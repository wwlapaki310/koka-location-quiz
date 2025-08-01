#!/usr/bin/env python3
"""
校歌データ収集プロジェクト メインランナー
Issue #8「大量データ収集プロジェクト」の実行統制スクリプト

使用方法:
python main.py --prefecture 東京都,神奈川県 --max-schools 20
python main.py --all-kanto --output-csv kanto_schools.csv
"""

import argparse
import logging
import sys
import time
from typing import List
from data_collector import SchoolDataCollector, SchoolData
from sheets_manager import GoogleSheetsManager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collection.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """コマンドライン引数解析"""
    parser = argparse.ArgumentParser(
        description='校歌データ収集ツール - Issue #8実行用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 特定都道府県の収集
  python main.py --prefecture 東京都,神奈川県,大阪府 --max-schools 10
  
  # 関東地方の一括収集
  python main.py --all-kanto --max-schools 50
  
  # 全国収集（時間がかかります）
  python main.py --all-japan --max-schools 20
  
  # スプレッドシート連携
  python main.py --prefecture 福岡県 --upload-sheets --max-schools 15
        """
    )
    
    # 地域選択オプション
    location_group = parser.add_mutually_exclusive_group(required=True)
    location_group.add_argument(
        '--prefecture', 
        type=str,
        help='収集対象都道府県をカンマ区切りで指定 (例: 東京都,神奈川県)'
    )
    location_group.add_argument(
        '--all-kanto', 
        action='store_true',
        help='関東地方の全都道府県を対象'
    )
    location_group.add_argument(
        '--all-kansai', 
        action='store_true',
        help='関西地方の全都道府県を対象'
    )
    location_group.add_argument(
        '--all-kyushu', 
        action='store_true',
        help='九州・沖縄地方の全都道府県を対象'
    )
    location_group.add_argument(
        '--all-japan', 
        action='store_true',
        help='全国すべてを対象（長時間実行）'
    )
    
    # 収集パラメータ
    parser.add_argument(
        '--max-schools', 
        type=int, 
        default=10,
        help='各都道府県の最大収集学校数 (デフォルト: 10)'
    )
    parser.add_argument(
        '--school-type', 
        type=str, 
        default='中学校',
        choices=['小学校', '中学校', '高等学校'],
        help='対象学校種別 (デフォルト: 中学校)'
    )
    parser.add_argument(
        '--delay', 
        type=float, 
        default=2.0,
        help='リクエスト間隔（秒）(デフォルト: 2.0秒)'
    )
    
    # 出力オプション
    parser.add_argument(
        '--output-csv', 
        type=str,
        help='CSV出力ファイル名（指定時のみCSV出力）'
    )
    parser.add_argument(
        '--upload-sheets', 
        action='store_true',
        help='Googleスプレッドシートにアップロード'
    )
    
    # その他オプション
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='実際には収集せず、処理対象を表示のみ'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='詳細ログ出力'
    )
    
    return parser.parse_args()

def get_prefecture_list(args) -> List[str]:
    """引数から都道府県リストを生成"""
    if args.prefecture:
        return [p.strip() for p in args.prefecture.split(',')]
    elif args.all_kanto:
        return ['東京都', '神奈川県', '埼玉県', '千葉県', '茨城県', '栃木県', '群馬県']
    elif args.all_kansai:
        return ['大阪府', '京都府', '兵庫県', '奈良県', '和歌山県', '滋賀県']
    elif args.all_kyushu:
        return ['福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県']
    elif args.all_japan:
        return [
            '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
            '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
            '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
            '岐阜県', '静岡県', '愛知県', '三重県',
            '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
            '鳥取県', '島根県', '岡山県', '広島県', '山口県',
            '徳島県', '香川県', '愛媛県', '高知県',
            '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
        ]
    else:
        return []

def print_collection_plan(prefectures: List[str], args):
    """収集計画の表示"""
    print(\"\\n\" + \"=\"*60)
    print(\"🏫 校歌データ収集計画 (Issue #8)\")
    print(\"=\"*60)
    print(f\"対象都道府県: {len(prefectures)}県\")
    for i, pref in enumerate(prefectures, 1):
        print(f\"  {i:2d}. {pref}\")
    print(f\"\\n学校種別: {args.school_type}\")
    print(f\"各県最大収集数: {args.max_schools}校\")
    print(f\"推定最大収集数: {len(prefectures) * args.max_schools}校\")
    print(f\"リクエスト間隔: {args.delay}秒\")
    
    # 推定所要時間
    estimated_time = len(prefectures) * args.max_schools * args.delay / 60
    print(f\"推定所要時間: {estimated_time:.1f}分\")
    
    if args.upload_sheets:
        print(\"📊 Googleスプレッドシート連携: 有効\")
    if args.output_csv:
        print(f\"📁 CSV出力: {args.output_csv}\")
    
    print(\"=\"*60 + \"\\n\")

def collect_prefecture_data(collector: SchoolDataCollector, prefecture: str, args) -> List[SchoolData]:
    \"\"\"都道府県単位のデータ収集\"\"\"\n    logger.info(f\"🏫 {prefecture}の{args.school_type}データ収集開始\")\n    \n    try:\n        # 学校検索\n        school_urls = collector.search_schools_by_prefecture(prefecture, args.school_type)\n        \n        if not school_urls:\n            logger.warning(f\"{prefecture}で学校が見つかりませんでした\")\n            return []\n        \n        logger.info(f\"{prefecture}: {len(school_urls)}校の候補を発見\")\n        \n        # データ収集\n        collected_schools = []\n        max_schools = min(len(school_urls), args.max_schools)\n        \n        for i, url in enumerate(school_urls[:max_schools]):\n            logger.info(f\"[{i+1}/{max_schools}] 収集中: {url}\")\n            \n            school_data = collector.extract_school_info(url)\n            if school_data:\n                collected_schools.append(school_data)\n                logger.info(f\"✅ 成功: {school_data.school_name}\")\n            else:\n                logger.warning(f\"❌ 失敗: {url}\")\n            \n            # レート制限\n            if i < max_schools - 1:  # 最後以外\n                time.sleep(args.delay)\n        \n        logger.info(f\"🎯 {prefecture}完了: {len(collected_schools)}/{max_schools}校収集\")\n        return collected_schools\n        \n    except Exception as e:\n        logger.error(f\"❌ {prefecture}でエラー発生: {e}\")\n        return []\n\ndef main():\n    \"\"\"メイン実行\"\"\"\n    args = parse_arguments()\n    \n    # ログレベル設定\n    if args.verbose:\n        logging.getLogger().setLevel(logging.DEBUG)\n    \n    # 収集対象都道府県の決定\n    prefectures = get_prefecture_list(args)\n    if not prefectures:\n        logger.error(\"収集対象都道府県が指定されていません\")\n        sys.exit(1)\n    \n    # 収集計画表示\n    print_collection_plan(prefectures, args)\n    \n    # Dry Run\n    if args.dry_run:\n        print(\"🔍 Dry Run モード: 実際の収集は行いません\")\n        return\n    \n    # 実行確認\n    if len(prefectures) > 5 and not args.all_japan:\n        confirm = input(\"\\n上記の計画で実行しますか? (y/N): \")\n        if confirm.lower() != 'y':\n            print(\"実行をキャンセルしました\")\n            return\n    \n    # データ収集実行\n    logger.info(\"📥 データ収集開始\")\n    start_time = time.time()\n    \n    collector = SchoolDataCollector()\n    all_schools = []\n    \n    for i, prefecture in enumerate(prefectures, 1):\n        logger.info(f\"\\n[{i}/{len(prefectures)}] === {prefecture} ===\")\n        \n        prefecture_schools = collect_prefecture_data(collector, prefecture, args)\n        all_schools.extend(prefecture_schools)\n        \n        logger.info(f\"{prefecture} 累計: {len(all_schools)}校\")\n        \n        # 県間の待機\n        if i < len(prefectures):\n            logger.info(f\"次の県まで{args.delay}秒待機...\")\n            time.sleep(args.delay)\n    \n    # 収集結果サマリー\n    end_time = time.time()\n    elapsed_time = end_time - start_time\n    \n    print(\"\\n\" + \"=\"*60)\n    print(\"📊 収集結果サマリー\")\n    print(\"=\"*60)\n    print(f\"総収集学校数: {len(all_schools)}校\")\n    print(f\"実行時間: {elapsed_time/60:.1f}分\")\n    \n    if all_schools:\n        # 都道府県別内訳\n        pref_counts = {}\n        for school in all_schools:\n            pref = school.prefecture\n            pref_counts[pref] = pref_counts.get(pref, 0) + 1\n        \n        print(\"\\n都道府県別内訳:\")\n        for pref, count in sorted(pref_counts.items()):\n            print(f\"  {pref}: {count}校\")\n        \n        # CSV出力\n        if args.output_csv:\n            collector.save_to_csv(all_schools, args.output_csv)\n            print(f\"\\n📁 CSV出力: {args.output_csv}\")\n        \n        # Googleスプレッドシート連携\n        if args.upload_sheets:\n            logger.info(\"📊 Googleスプレッドシートに登録中...\")\n            sheets_manager = GoogleSheetsManager()\n            \n            if sheets_manager.setup_spreadsheet():\n                if sheets_manager.add_school_data(all_schools):\n                    print(\"✅ Googleスプレッドシート登録完了\")\n                    \n                    # 品質レポート表示\n                    report = sheets_manager.generate_quality_report()\n                    if report:\n                        print(f\"\\n📈 品質レポート:\")\n                        print(f\"  A級データ: {report['quality_distribution']['A']}件\")\n                        print(f\"  B級データ: {report['quality_distribution']['B']}件\")\n                        print(f\"  C級データ: {report['quality_distribution']['C']}件\")\n                else:\n                    print(\"❌ スプレッドシート登録に失敗しました\")\n            else:\n                print(\"❌ スプレッドシート初期化に失敗しました\")\n    \n    else:\n        print(\"⚠️  収集できたデータがありません\")\n        logger.warning(\"設定や接続を確認してください\")\n    \n    print(\"\\n✅ 処理完了\")\n    print(\"=\"*60)\n\nif __name__ == \"__main__\":\n    try:\n        main()\n    except KeyboardInterrupt:\n        print(\"\\n\\n⚠️  ユーザーによって中断されました\")\n        sys.exit(1)\n    except Exception as e:\n        logger.error(f\"予期しないエラー: {e}\")\n        sys.exit(1)\n
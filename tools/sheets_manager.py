#!/usr/bin/env python3
"""
Googleスプレッドシート連携ツール
- データ収集結果のスプレッドシート自動登録
- 進捗管理ダッシュボード更新
- 品質チェック結果の反映

Requirements:
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib gspread
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from data_collector import SchoolData

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """Googleスプレッドシート管理クラス"""
    
    def __init__(self, credentials_file: str = "credentials.json", config_file: str = "sheets_config.json"):
        """
        初期化
        Args:
            credentials_file: Google Service Account認証情報
            config_file: スプレッドシート設定ファイル
        """
        self.config = self._load_config(config_file)
        self.gc = self._authenticate(credentials_file)
        self.workbook = None
        
    def _load_config(self, config_file: str) -> Dict:
        """設定ファイル読み込み"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"設定ファイル {config_file} が見つかりません。サンプル設定を作成します。")
            sample_config = {
                "spreadsheet_id": "YOUR_SPREADSHEET_ID_HERE",
                "sheets": {
                    "master": "学校マスター",
                    "songs": "校歌データ", 
                    "progress": "進捗管理",
                    "quality": "品質チェック",
                    "copyright": "著作権情報"
                },
                "master_headers": [
                    "ID", "学校名", "学校種別", "設置者", "都道府県", "市区町村", "住所",
                    "緯度", "経度", "校歌タイトル", "校歌全文", "マスク済み歌詞",
                    "作詞者", "作曲者", "制定年", "難易度", "ヒント1_地方", "ヒント2_地域",
                    "ヒント3_特徴", "設立年", "備考", "データソース", "収集日",
                    "収集者", "品質チェック", "著作権状況"
                ]
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            return sample_config
    
    def _authenticate(self, credentials_file: str) -> gspread.Client:
        """Google認証"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                credentials_file, scopes=scope
            )
            
            return gspread.authorize(credentials)
        except FileNotFoundError:
            logger.error(f"認証情報ファイル {credentials_file} が見つかりません。")
            logger.info("Google Cloud Consoleでサービスアカウントを作成し、認証情報をダウンロードしてください。")
            raise
    
    def setup_spreadsheet(self) -> bool:
        """スプレッドシートの初期設定"""
        try:
            spreadsheet_id = self.config["spreadsheet_id"]
            if spreadsheet_id == "YOUR_SPREADSHEET_ID_HERE":
                logger.error("spreadsheet_idが設定されていません。設定ファイルを確認してください。")
                return False
            
            self.workbook = self.gc.open_by_key(spreadsheet_id)
            logger.info(f"スプレッドシート '{self.workbook.title}' に接続しました")
            
            # 各シートの作成・設定
            self._setup_master_sheet()
            self._setup_progress_sheet()
            self._setup_quality_sheet()
            self._setup_copyright_sheet()
            
            return True
            
        except Exception as e:
            logger.error(f"スプレッドシート設定エラー: {e}")
            return False
    
    def _setup_master_sheet(self):
        """学校マスターシートの設定"""
        sheet_name = self.config["sheets"]["master"]
        
        try:
            sheet = self.workbook.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            sheet = self.workbook.add_worksheet(title=sheet_name, rows=1000, cols=26)
            logger.info(f"シート '{sheet_name}' を作成しました")
        
        # ヘッダー設定
        headers = self.config["master_headers"]
        sheet.update('A1', [headers])
        
        # フォーマット設定
        self._format_header_row(sheet, len(headers))
        
        logger.info(f"マスターシート '{sheet_name}' の設定完了")
    
    def _setup_progress_sheet(self):
        """進捗管理シートの設定"""
        sheet_name = self.config["sheets"]["progress"]
        
        try:
            sheet = self.workbook.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            sheet = self.workbook.add_worksheet(title=sheet_name, rows=100, cols=10)
        
        # 進捗管理ヘッダー
        progress_headers = [
            "都道府県", "目標件数", "収集済み件数", "進捗率(%)", 
            "品質A級", "品質B級", "品質C級", "最終更新日", "担当者", "備考"
        ]
        sheet.update('A1', [progress_headers])
        
        # 都道府県データの初期化
        prefectures_data = self._get_initial_prefecture_data()
        if prefectures_data:
            sheet.update('A2', prefectures_data)
        
        self._format_header_row(sheet, len(progress_headers))
        logger.info(f"進捗管理シート '{sheet_name}' の設定完了")
    
    def _setup_quality_sheet(self):
        """品質チェックシートの設定"""
        sheet_name = self.config["sheets"]["quality"]
        
        try:
            sheet = self.workbook.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            sheet = self.workbook.add_worksheet(title=sheet_name, rows=1000, cols=8)
        
        quality_headers = [
            "学校ID", "学校名", "品質レベル", "チェック項目", 
            "チェック結果", "コメント", "チェック日", "チェック者"
        ]
        sheet.update('A1', [quality_headers])
        self._format_header_row(sheet, len(quality_headers))
        
        logger.info(f"品質チェックシート '{sheet_name}' の設定完了")
    
    def _setup_copyright_sheet(self):
        """著作権情報シートの設定"""
        sheet_name = self.config["sheets"]["copyright"]
        
        try:
            sheet = self.workbook.worksheet(sheet_name)
        except gspread.WorksheetNotFound:
            sheet = self.workbook.add_worksheet(title=sheet_name, rows=1000, cols=10)
        
        copyright_headers = [
            "学校ID", "学校名", "作詞者", "作曲者", "制定年",
            "著作権状況", "使用許可", "権利者", "確認日", "備考"
        ]
        sheet.update('A1', [copyright_headers])
        self._format_header_row(sheet, len(copyright_headers))
        
        logger.info(f"著作権情報シート '{sheet_name}' の設定完了")
    
    def _format_header_row(self, sheet, col_count: int):
        """ヘッダー行のフォーマット設定"""
        try:
            # ヘッダー行の背景色とフォント設定
            header_range = f'A1:{chr(64 + col_count)}1'
            sheet.format(header_range, {
                "backgroundColor": {"red": 0.8, "green": 0.8, "blue": 0.8},
                "textFormat": {"bold": True},
                "horizontalAlignment": "CENTER"
            })
        except Exception as e:
            logger.warning(f"ヘッダーフォーマット設定エラー: {e}")
    
    def _get_initial_prefecture_data(self) -> List[List]:
        """都道府県別目標データの初期値"""
        # Issue #8 で定義された目標配分
        prefecture_goals = [
            ["北海道", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["青森県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["岩手県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["宮城県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["秋田県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["山形県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["福島県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["茨城県", 25, 0, 0, 0, 0, 0, "", "", ""],
            ["栃木県", 20, 0, 0, 0, 0, 0, "", "", ""],
            ["群馬県", 20, 0, 0, 0, 0, 0, "", "", ""],
            ["埼玉県", 40, 0, 0, 0, 0, 0, "", "", ""],
            ["千葉県", 35, 0, 0, 0, 0, 0, "", "", ""],
            ["東京都", 70, 0, 0, 0, 0, 0, "", "", ""],
            ["神奈川県", 60, 0, 0, 0, 0, 0, "", "", ""],
            ["新潟県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["富山県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["石川県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["福井県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["山梨県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["長野県", 20, 0, 0, 0, 0, 0, "", "", ""],
            ["岐阜県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["静岡県", 25, 0, 0, 0, 0, 0, "", "", ""],
            ["愛知県", 40, 0, 0, 0, 0, 0, "", "", ""],
            ["三重県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["滋賀県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["京都府", 25, 0, 0, 0, 0, 0, "", "", ""],
            ["大阪府", 50, 0, 0, 0, 0, 0, "", "", ""],
            ["兵庫県", 35, 0, 0, 0, 0, 0, "", "", ""],
            ["奈良県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["和歌山県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["鳥取県", 8, 0, 0, 0, 0, 0, "", "", ""],
            ["島根県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["岡山県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["広島県", 20, 0, 0, 0, 0, 0, "", "", ""],
            ["山口県", 12, 0, 0, 0, 0, 0, "", "", ""],
            ["徳島県", 8, 0, 0, 0, 0, 0, "", "", ""],
            ["香川県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["愛媛県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["高知県", 10, 0, 0, 0, 0, 0, "", "", ""],
            ["福岡県", 50, 0, 0, 0, 0, 0, "", "", ""],
            ["佐賀県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["長崎県", 20, 0, 0, 0, 0, 0, "", "", ""],
            ["熊本県", 25, 0, 0, 0, 0, 0, "", "", ""],
            ["大分県", 20, 0, 0, 0, 0, 0, "", "", ""],
            ["宮崎県", 15, 0, 0, 0, 0, 0, "", "", ""],
            ["鹿児島県", 25, 0, 0, 0, 0, 0, "", "", ""],
            ["沖縄県", 30, 0, 0, 0, 0, 0, "", "", ""]
        ]
        return prefecture_goals
    
    def add_school_data(self, schools: List[SchoolData]) -> bool:
        """学校データをスプレッドシートに追加"""
        if not self.workbook:
            logger.error("スプレッドシートが初期化されていません")
            return False
        
        try:
            master_sheet = self.workbook.worksheet(self.config["sheets"]["master"])
            
            # 既存データの行数を取得
            existing_data = master_sheet.get_all_values()
            next_row = len(existing_data) + 1
            
            # 学校データを行形式に変換
            new_rows = []
            for i, school in enumerate(schools):
                row_data = self._school_to_row(school, next_row + i - 1)
                new_rows.append(row_data)
            
            # バッチ更新
            if new_rows:
                range_to_update = f'A{next_row}:Z{next_row + len(new_rows) - 1}'
                master_sheet.update(range_to_update, new_rows)
                logger.info(f"{len(new_rows)}件の学校データを追加しました")
            
            # 進捗管理シートの更新
            self.update_progress()
            
            return True
            
        except Exception as e:
            logger.error(f"データ追加エラー: {e}")
            return False
    
    def _school_to_row(self, school: SchoolData, row_id: int) -> List:
        """SchoolDataを行データに変換"""
        return [
            row_id,  # ID
            school.school_name,
            school.school_type,
            school.establishment_type,
            school.prefecture,
            school.city,
            school.address,
            school.latitude,
            school.longitude,
            school.song_title,
            school.full_lyrics,
            school.masked_lyrics,
            school.lyricist,
            school.composer,
            school.composed_year,
            school.difficulty,
            school.hint_prefecture,
            school.hint_region,
            school.hint_landmark,
            school.established_year,
            school.notes,
            school.data_source,
            school.collection_date,
            "自動収集",  # 収集者
            school.quality_check,
            school.copyright_status
        ]
    
    def update_progress(self) -> bool:
        """進捗管理シートの更新"""
        try:
            master_sheet = self.workbook.worksheet(self.config["sheets"]["master"])
            progress_sheet = self.workbook.worksheet(self.config["sheets"]["progress"])
            
            # マスターデータから都道府県別集計
            all_data = master_sheet.get_all_records()
            
            prefecture_stats = {}
            for row in all_data:
                pref = row.get('都道府県', '')
                if pref:
                    if pref not in prefecture_stats:
                        prefecture_stats[pref] = {'total': 0, 'A': 0, 'B': 0, 'C': 0}\n                    \n                    prefecture_stats[pref]['total'] += 1\n                    quality = row.get('品質チェック', 'PENDING')\n                    if quality == 'A':\n                        prefecture_stats[pref]['A'] += 1\n                    elif quality == 'B':\n                        prefecture_stats[pref]['B'] += 1\n                    elif quality == 'C':\n                        prefecture_stats[pref]['C'] += 1\n            \n            # 進捗シートの更新\n            progress_data = progress_sheet.get_all_records()\n            update_rows = []\n            \n            for i, row in enumerate(progress_data):\n                pref = row['都道府県']\n                target = row.get('目標件数', 0)\n                \n                if pref in prefecture_stats:\n                    current = prefecture_stats[pref]['total']\n                    progress_rate = (current / target * 100) if target > 0 else 0\n                    \n                    update_row = [\n                        pref,\n                        target,\n                        current,\n                        f\"{progress_rate:.1f}\",\n                        prefecture_stats[pref]['A'],\n                        prefecture_stats[pref]['B'],\n                        prefecture_stats[pref]['C'],\n                        datetime.now().strftime(\"%Y-%m-%d\"),\n                        \"自動更新\",\n                        \"\"\n                    ]\n                    update_rows.append(update_row)\n                else:\n                    # データがない場合はそのまま\n                    update_rows.append([row[key] for key in row.keys()])\n            \n            # バッチ更新\n            if update_rows:\n                progress_sheet.update('A2', update_rows)\n                logger.info(\"進捗データを更新しました\")\n            \n            return True\n            \n        except Exception as e:\n            logger.error(f\"進捗更新エラー: {e}\")\n            return False\n    \n    def generate_quality_report(self) -> Dict:\n        \"\"\"品質レポートの生成\"\"\"\n        try:\n            master_sheet = self.workbook.worksheet(self.config[\"sheets\"][\"master\"])\n            all_data = master_sheet.get_all_records()\n            \n            total_schools = len(all_data)\n            quality_counts = {'A': 0, 'B': 0, 'C': 0, 'PENDING': 0}\n            \n            for row in all_data:\n                quality = row.get('品質チェック', 'PENDING')\n                if quality in quality_counts:\n                    quality_counts[quality] += 1\n                else:\n                    quality_counts['PENDING'] += 1\n            \n            report = {\n                'total_schools': total_schools,\n                'quality_distribution': quality_counts,\n                'quality_rate': {\n                    'A': (quality_counts['A'] / total_schools * 100) if total_schools > 0 else 0,\n                    'B': (quality_counts['B'] / total_schools * 100) if total_schools > 0 else 0,\n                    'C': (quality_counts['C'] / total_schools * 100) if total_schools > 0 else 0\n                },\n                'generated_at': datetime.now().isoformat()\n            }\n            \n            logger.info(f\"品質レポート生成完了: 総数{total_schools}件\")\n            return report\n            \n        except Exception as e:\n            logger.error(f\"品質レポート生成エラー: {e}\")\n            return {}\n    \n    def export_for_mvp(self, output_file: str = \"mvp_data.json\") -> bool:\n        \"\"\"MVP用データ形式でエクスポート\"\"\"\n        try:\n            master_sheet = self.workbook.worksheet(self.config[\"sheets\"][\"master\"])\n            all_data = master_sheet.get_all_records()\n            \n            mvp_data = []\n            for i, row in enumerate(all_data):\n                if row.get('品質チェック') in ['A', 'B']:  # 高品質データのみ\n                    mvp_school = {\n                        \"id\": i + 1,\n                        \"schoolName\": row.get('学校名', ''),\n                        \"prefecture\": row.get('都道府県', ''),\n                        \"city\": row.get('市区町村', ''),\n                        \"address\": row.get('住所', ''),\n                        \"coordinates\": {\n                            \"lat\": float(row.get('緯度', 0)) if row.get('緯度') else 0,\n                            \"lng\": float(row.get('経度', 0)) if row.get('経度') else 0\n                        },\n                        \"songTitle\": row.get('校歌タイトル', '校歌'),\n                        \"lyrics\": row.get('校歌全文', ''),\n                        \"maskedLyrics\": row.get('マスク済み歌詞', ''),\n                        \"difficulty\": row.get('難易度', 'medium'),\n                        \"notes\": row.get('備考', ''),\n                        \"hints\": {\n                            \"prefecture\": row.get('ヒント1_地方', ''),\n                            \"region\": row.get('ヒント2_地域', ''),\n                            \"landmark\": row.get('ヒント3_特徴', '')\n                        }\n                    }\n                    \n                    # 座標と歌詞が揃っているもののみ\n                    if (mvp_school[\"coordinates\"][\"lat\"] != 0 and \n                        mvp_school[\"coordinates\"][\"lng\"] != 0 and\n                        mvp_school[\"lyrics\"].strip()):\n                        mvp_data.append(mvp_school)\n            \n            # JSON出力\n            with open(output_file, 'w', encoding='utf-8') as f:\n                json.dump(mvp_data, f, indent=2, ensure_ascii=False)\n            \n            logger.info(f\"MVP用データを {output_file} に出力しました（{len(mvp_data)}件）\")\n            return True\n            \n        except Exception as e:\n            logger.error(f\"MVP用データ出力エラー: {e}\")\n            return False\n\ndef main():\n    \"\"\"メイン実行\"\"\"\n    sheets_manager = GoogleSheetsManager()\n    \n    # スプレッドシート初期設定\n    if sheets_manager.setup_spreadsheet():\n        logger.info(\"スプレッドシート設定完了\")\n        \n        # 品質レポート生成\n        report = sheets_manager.generate_quality_report()\n        if report:\n            print(\"=== 品質レポート ===\")\n            print(f\"総学校数: {report['total_schools']}\")\n            print(f\"品質A級: {report['quality_distribution']['A']}件 ({report['quality_rate']['A']:.1f}%)\")\n            print(f\"品質B級: {report['quality_distribution']['B']}件 ({report['quality_rate']['B']:.1f}%)\")\n            print(f\"品質C級: {report['quality_distribution']['C']}件 ({report['quality_rate']['C']:.1f}%)\")\n        \n        # MVP用データ出力\n        sheets_manager.export_for_mvp()\n    else:\n        logger.error(\"スプレッドシート設定に失敗しました\")\n\nif __name__ == \"__main__\":\n    main()\n
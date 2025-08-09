#!/usr/bin/env python3
"""
スプレッドシート簡易追加ツール
JSON/CSVファイルからGoogleスプレッドシートにデータを簡単追加

使用方法:
python quick_sheets_add.py --file data.json
python quick_sheets_add.py --file data.csv --format csv
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import csv
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any
import time

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickSheetsAdder:
    """シンプルなスプレッドシート追加ツール"""
    
    # 固定のスプレッドシートID
    SPREADSHEET_ID = "1ukF5ZhpwJkN21wHLTaTS13BYTk5puKPisdQ1fGR5BwE"
    SHEET_NAME = "学校マスター"
    
    # ヘッダー定義
    HEADERS = [
        "ID", "学校名", "都道府県", "市区町村", "住所",
        "緯度", "経度", "校歌タイトル", "校歌全文", "マスク済み歌詞",
        "作曲者", "作詞者", "難易度", "品質レベル", "品質スコア",
        "データソース", "収集日", "ヒント_都道府県", "ヒント_地域", "ヒント_特徴",
        "学校種別", "設置者", "設立年", "制定年", "備考", "著作権状況"
    ]
    
    def __init__(self, credentials_file: str = "credentials.json"):
        """初期化"""
        self.credentials_file = credentials_file
        self.gc = None
        self.sheet = None
        self.authenticate()
        
    def authenticate(self):
        """Google認証"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            
            self.gc = gspread.authorize(creds)
            logger.info("✅ Google認証成功")
            
            # スプレッドシート接続
            self.spreadsheet = self.gc.open_by_key(self.SPREADSHEET_ID)
            self.sheet = self.spreadsheet.worksheet(self.SHEET_NAME)
            logger.info(f"✅ スプレッドシート接続: {self.spreadsheet.title}")
            
        except FileNotFoundError:
            logger.error(f"❌ 認証ファイルが見つかりません: {self.credentials_file}")
            raise
        except Exception as e:
            logger.error(f"❌ 認証エラー: {e}")
            raise
    
    def ensure_headers(self):
        """ヘッダー確認・設定"""
        try:
            existing_headers = self.sheet.row_values(1)
            
            if not existing_headers or len(existing_headers) < len(self.HEADERS):
                logger.info("📋 ヘッダーを設定中...")
                self.sheet.update('A1', [self.HEADERS])
                
                # ヘッダーの書式設定
                self.sheet.format('A1:Z1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                    'textFormat': {
                        'bold': True,
                        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}
                    }
                })
                logger.info("✅ ヘッダー設定完了")
            else:
                logger.info("✅ ヘッダー確認済み")
                
        except Exception as e:
            logger.warning(f"⚠️ ヘッダー設定で問題発生: {e}")
    
    def get_next_id(self) -> int:
        """次のIDを取得"""
        try:
            all_values = self.sheet.get_all_values()
            if len(all_values) <= 1:  # ヘッダーのみ
                return 1
            
            # IDカラムから最大値を取得
            max_id = 0
            for row in all_values[1:]:  # ヘッダーをスキップ
                if row and row[0].strip():  # IDがある場合
                    try:
                        current_id = int(row[0])
                        max_id = max(max_id, current_id)
                    except ValueError:
                        continue
            
            return max_id + 1
            
        except Exception as e:
            logger.warning(f"⚠️ ID取得エラー: {e}")
            return 1
    
    def load_json_data(self, file_path: str) -> List[Dict]:
        """JSONファイル読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                logger.error(f"❌ 不正なJSONフォーマット: {type(data)}")
                return []
                
        except Exception as e:
            logger.error(f"❌ JSONファイル読み込みエラー: {e}")
            return []
    
    def load_csv_data(self, file_path: str) -> List[Dict]:
        """CSVファイル読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                return list(reader)
                
        except Exception as e:
            logger.error(f"❌ CSVファイル読み込みエラー: {e}")
            return []
    
    def convert_to_row(self, data: Dict, school_id: int) -> List[str]:
        """データを行形式に変換"""
        return [
            str(school_id),
            data.get('school_name', ''),
            data.get('prefecture', ''),
            data.get('city', ''),
            data.get('address', ''),
            str(data.get('latitude', '')),
            str(data.get('longitude', '')),
            data.get('song_title', '校歌'),
            data.get('full_lyrics', ''),
            data.get('masked_lyrics', ''),
            data.get('composer', ''),
            data.get('lyricist', ''),
            data.get('difficulty', ''),
            data.get('quality_level', ''),
            str(data.get('quality_score', '')),
            data.get('data_source', ''),
            data.get('collection_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('hints', {}).get('prefecture', ''),
            data.get('hints', {}).get('region', ''),
            data.get('hints', {}).get('landmark', ''),
            data.get('school_type', ''),
            data.get('establishment_type', ''),
            str(data.get('established_year', '')),
            str(data.get('composed_year', '')),
            data.get('notes', ''),
            data.get('copyright_status', '')
        ]
    
    def add_data_batch(self, data_list: List[Dict], batch_size: int = 10) -> bool:
        """データ一括追加"""
        if not data_list:
            logger.warning("⚠️ 追加するデータがありません")
            return False
        
        logger.info(f"📤 {len(data_list)}件のデータを追加中...")
        
        # ヘッダー確認
        self.ensure_headers()
        
        # 次のIDを取得
        next_id = self.get_next_id()
        logger.info(f"📊 開始ID: {next_id}")
        
        success_count = 0
        total_batches = (len(data_list) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(data_list))
            batch_data = data_list[start_idx:end_idx]
            
            try:
                # バッチデータを行形式に変換
                rows = []
                for i, item in enumerate(batch_data):
                    school_id = next_id + start_idx + i
                    row = self.convert_to_row(item, school_id)
                    rows.append(row)
                
                # スプレッドシートに追加
                self.sheet.append_rows(rows)
                success_count += len(rows)
                
                logger.info(f"✅ バッチ {batch_num + 1}/{total_batches}: {len(rows)}件追加完了")
                
                # API制限対策（少し待機）
                if batch_num < total_batches - 1:  # 最後のバッチでない場合
                    time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ バッチ {batch_num + 1} 追加エラー: {e}")
                # エラーが発生しても継続
                continue
        
        logger.info(f"🎉 追加完了: {success_count}/{len(data_list)}件")
        return success_count > 0
    
    def add_single_data(self, data: Dict) -> bool:
        """単体データ追加"""
        try:
            # ヘッダー確認
            self.ensure_headers()
            
            # 次のIDを取得
            next_id = self.get_next_id()
            
            # データを行形式に変換
            row = self.convert_to_row(data, next_id)
            
            # スプレッドシートに追加
            self.sheet.append_row(row)
            
            school_name = data.get('school_name', 'Unknown')
            logger.info(f"✅ 追加完了: {school_name} (ID: {next_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ データ追加エラー: {e}")
            return False
    
    def get_current_count(self) -> int:
        """現在のデータ件数"""
        try:
            all_values = self.sheet.get_all_values()
            count = max(0, len(all_values) - 1)  # ヘッダーを除く
            logger.info(f"📊 現在のデータ件数: {count}校")
            return count
        except Exception as e:
            logger.error(f"❌ 件数取得エラー: {e}")
            return 0

def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description='スプレッドシート簡易追加ツール')
    parser.add_argument('--file', required=True, help='追加するデータファイル (JSON/CSV)')
    parser.add_argument('--format', choices=['json', 'csv'], default='json', help='ファイル形式')
    parser.add_argument('--batch-size', type=int, default=10, help='バッチサイズ')
    parser.add_argument('--credentials', default='credentials.json', help='認証ファイル')
    
    args = parser.parse_args()
    
    print("📊 スプレッドシート簡易追加ツール")
    print("=" * 50)
    
    try:
        # ツール初期化
        adder = QuickSheetsAdder(args.credentials)
        
        # 現在の件数確認
        current_count = adder.get_current_count()
        
        # データ読み込み
        if args.format == 'json':
            data_list = adder.load_json_data(args.file)
        else:
            data_list = adder.load_csv_data(args.file)
        
        if not data_list:
            print("❌ データが読み込めませんでした")
            return 1
        
        print(f"📁 読み込みデータ: {len(data_list)}件")
        
        # データ追加実行
        success = adder.add_data_batch(data_list, args.batch_size)
        
        if success:
            # 最終件数確認
            final_count = adder.get_current_count()
            added_count = final_count - current_count
            
            print(f"\n🎉 追加完了!")
            print(f"📊 追加前: {current_count}校")
            print(f"📊 追加後: {final_count}校")
            print(f"📈 追加数: {added_count}校")
            print(f"🔗 スプレッドシート: https://docs.google.com/spreadsheets/d/{adder.SPREADSHEET_ID}")
            return 0
        else:
            print("❌ データ追加に失敗しました")
            return 1
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return 1

if __name__ == "__main__":
    exit(main())

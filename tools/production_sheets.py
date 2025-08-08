#!/usr/bin/env python3
"""
Googleスプレッドシート連携ツール
指定されたスプレッドシートにデータを投入・管理
"""

import gspread
from google.oauth2.service_account import Credentials
import json
import pandas as pd
from datetime import datetime
import logging

class ProductionSheetsManager:
    """本番用Googleスプレッドシート管理"""
    
    def __init__(self, config_file="config.json.production"):
        self.load_config(config_file)
        self.setup_credentials()
        self.connect_spreadsheet()
        
    def load_config(self, config_file):
        """設定読み込み"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.sheet_id = self.config['google_sheets_id']
        self.credentials_file = self.config['google_sheets_credentials_file']
        self.spreadsheet_config = self.config['spreadsheet_config']
        
        print(f"✅ 設定読み込み完了")
        print(f"📊 スプレッドシートID: {self.sheet_id}")
        
    def setup_credentials(self):
        """認証設定"""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        try:
            self.creds = Credentials.from_service_account_file(
                self.credentials_file, scopes=scopes
            )
            self.gc = gspread.authorize(self.creds)
            print("✅ Google認証完了")
        except Exception as e:
            print(f"❌ 認証エラー: {e}")
            print("📋 credentials.jsonを正しく配置してください")
            raise
    
    def connect_spreadsheet(self):
        """スプレッドシート接続"""
        try:
            self.spreadsheet = self.gc.open_by_key(self.sheet_id)
            print(f"✅ スプレッドシート接続成功: {self.spreadsheet.title}")
            self.setup_sheets()
        except Exception as e:
            print(f"❌ スプレッドシート接続エラー: {e}")
            print(f"📋 スプレッドシートID確認: {self.sheet_id}")
            print("📋 共有設定でサービスアカウントに編集権限を付与してください")
            raise
    
    def setup_sheets(self):
        """必要なシートを設定"""
        sheet_names = [
            self.spreadsheet_config['main_sheet_name'],
            self.spreadsheet_config['progress_sheet_name'],
            self.spreadsheet_config['quality_sheet_name'],
            self.spreadsheet_config['prefecture_sheet_name']
        ]
        
        existing_sheets = [ws.title for ws in self.spreadsheet.worksheets()]
        
        for sheet_name in sheet_names:
            if sheet_name not in existing_sheets:
                print(f"📋 シート作成中: {sheet_name}")
                self.spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=26)
            else:
                print(f"✅ 既存シート確認: {sheet_name}")
        
        # メインシートの参照
        self.main_sheet = self.spreadsheet.worksheet(
            self.spreadsheet_config['main_sheet_name']
        )
        
        # ヘッダー設定
        self.setup_headers()
    
    def setup_headers(self):
        """ヘッダー行設定"""
        headers = [
            "ID", "学校名", "都道府県", "市区町村", "住所",
            "緯度", "経度", "校歌タイトル", "校歌全文", "マスク済み歌詞",
            "作曲者", "作詞者", "難易度", "品質レベル", "品質スコア",
            "データソース", "収集日", "ヒント_都道府県", "ヒント_地域", "ヒント_特徴"
        ]
        
        # 既存のヘッダーチェック
        try:
            existing_headers = self.main_sheet.row_values(1)
            if not existing_headers or existing_headers != headers:
                print("📋 ヘッダー行を設定中...")
                self.main_sheet.clear()
                self.main_sheet.append_row(headers)
                
                # ヘッダーの書式設定
                self.main_sheet.format('A1:T1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                    'textFormat': {
                        'bold': True,
                        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}
                    }
                })
                print("✅ ヘッダー設定完了")
            else:
                print("✅ ヘッダー確認済み")
        except Exception as e:
            print(f"⚠️ ヘッダー設定エラー: {e}")
    
    def add_school_data(self, school_data):
        """学校データ追加（単体）"""
        try:
            row_data = [
                school_data.get('id', ''),
                school_data.get('school_name', ''),
                school_data.get('prefecture', ''),
                school_data.get('city', ''),
                school_data.get('address', ''),
                school_data.get('latitude', ''),
                school_data.get('longitude', ''),
                school_data.get('song_title', '校歌'),
                school_data.get('full_lyrics', ''),
                school_data.get('masked_lyrics', ''),
                school_data.get('composer', ''),
                school_data.get('lyricist', ''),
                school_data.get('difficulty', ''),
                school_data.get('quality_level', ''),
                school_data.get('quality_score', ''),
                school_data.get('data_source', ''),
                school_data.get('collection_date', ''),
                school_data.get('hints', {}).get('prefecture', ''),
                school_data.get('hints', {}).get('region', ''),
                school_data.get('hints', {}).get('landmark', '')
            ]
            
            self.main_sheet.append_row(row_data)
            print(f"✅ 追加完了: {school_data.get('school_name', 'Unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ データ追加エラー: {e}")
            return False
    
    def add_schools_batch(self, schools_data, batch_size=20):
        """学校データ一括追加"""
        print(f"📤 {len(schools_data)}校のデータを一括追加中...")
        
        success_count = 0
        for i in range(0, len(schools_data), batch_size):
            batch = schools_data[i:i + batch_size]
            batch_rows = []
            
            for school in batch:
                row_data = [
                    school.get('id', ''),
                    school.get('school_name', ''),
                    school.get('prefecture', ''),
                    school.get('city', ''),
                    school.get('address', ''),
                    school.get('latitude', ''),
                    school.get('longitude', ''),
                    school.get('song_title', '校歌'),
                    school.get('full_lyrics', ''),
                    school.get('masked_lyrics', ''),
                    school.get('composer', ''),
                    school.get('lyricist', ''),
                    school.get('difficulty', ''),
                    school.get('quality_level', ''),
                    school.get('quality_score', ''),
                    school.get('data_source', ''),
                    school.get('collection_date', ''),
                    school.get('hints', {}).get('prefecture', ''),
                    school.get('hints', {}).get('region', ''),
                    school.get('hints', {}).get('landmark', '')
                ]
                batch_rows.append(row_data)
            
            try:
                # バッチでデータ追加
                start_row = len(self.main_sheet.get_all_values()) + 1
                end_row = start_row + len(batch_rows) - 1
                cell_range = f'A{start_row}:T{end_row}'
                
                self.main_sheet.update(cell_range, batch_rows)
                success_count += len(batch_rows)
                
                print(f"📤 バッチ {i//batch_size + 1}: {len(batch_rows)}校追加完了")
                
                # API制限対策
                import time
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ バッチ追加エラー: {e}")
        
        print(f"✅ 一括追加完了: {success_count}/{len(schools_data)}校")
        return success_count
    
    def update_progress_sheet(self, progress_data):
        """進捗管理シート更新"""
        try:
            progress_sheet = self.spreadsheet.worksheet(
                self.spreadsheet_config['progress_sheet_name']
            )
            
            # 進捗ヘッダー
            progress_headers = [
                "実行ID", "開始時刻", "ステータス", "対象地域",
                "目標数", "完了数", "成功数", "失敗数", "成功率%",
                "品質A", "品質B", "品質C", "品質D", "A+B率%",
                "実行時間", "予想完了", "最終更新"
            ]
            
            # ヘッダーがなければ設定
            existing_headers = progress_sheet.row_values(1) if progress_sheet.row_count > 0 else []
            if not existing_headers:
                progress_sheet.append_row(progress_headers)
            
            # 進捗データ追加
            elapsed = datetime.now() - datetime.fromisoformat(progress_data.get('start_time', datetime.now().isoformat()))
            success_rate = (progress_data.get('successful', 0) / max(progress_data.get('completed', 1), 1)) * 100
            quality_total = sum(progress_data.get('quality_stats', {}).values())
            ab_rate = ((progress_data.get('quality_stats', {}).get('A', 0) + 
                       progress_data.get('quality_stats', {}).get('B', 0)) / max(quality_total, 1)) * 100
            
            row_data = [
                progress_data.get('execution_id', ''),
                progress_data.get('start_time', ''),
                progress_data.get('status', ''),
                progress_data.get('current_prefecture', ''),
                progress_data.get('total_target', 0),
                progress_data.get('completed', 0),
                progress_data.get('successful', 0),
                progress_data.get('failed', 0),
                round(success_rate, 1),
                progress_data.get('quality_stats', {}).get('A', 0),
                progress_data.get('quality_stats', {}).get('B', 0),
                progress_data.get('quality_stats', {}).get('C', 0),
                progress_data.get('quality_stats', {}).get('D', 0),
                round(ab_rate, 1),
                str(elapsed).split('.')[0],
                progress_data.get('estimated_completion', ''),
                datetime.now().isoformat()
            ]
            
            progress_sheet.append_row(row_data)
            print("✅ 進捗シート更新完了")
            
        except Exception as e:
            print(f"❌ 進捗シート更新エラー: {e}")
    
    def get_current_data_count(self):
        """現在のデータ件数取得"""
        try:
            all_values = self.main_sheet.get_all_values()
            # ヘッダーを除いた行数
            data_count = len(all_values) - 1 if len(all_values) > 1 else 0
            print(f"📊 現在のデータ件数: {data_count}校")
            return data_count
        except Exception as e:
            print(f"❌ データ件数取得エラー: {e}")
            return 0
    
    def get_spreadsheet_info(self):
        """スプレッドシート情報表示"""
        try:
            print("\n📊 スプレッドシート情報")
            print("=" * 40)
            print(f"タイトル: {self.spreadsheet.title}")
            print(f"URL: {self.config['google_sheets_url']}")
            print(f"シート数: {len(self.spreadsheet.worksheets())}")
            
            for ws in self.spreadsheet.worksheets():
                row_count = len(ws.get_all_values())
                print(f"  - {ws.title}: {row_count}行")
            
            data_count = self.get_current_data_count()
            print(f"📈 学校データ: {data_count}校")
            print("=" * 40)
            
        except Exception as e:
            print(f"❌ 情報取得エラー: {e}")

def main():
    """メイン実行"""
    print("📊 Googleスプレッドシート連携ツール")
    print("=" * 50)
    
    try:
        # スプレッドシート管理インスタンス作成
        sheets_manager = ProductionSheetsManager()
        
        # スプレッドシート情報表示
        sheets_manager.get_spreadsheet_info()
        
        # テストデータ追加
        test_data = {
            'id': 1,
            'school_name': '新宿区立戸山中学校',
            'prefecture': '東京都',
            'city': '新宿区',
            'address': '東京都新宿区戸山3-20-1',
            'latitude': 35.7019,
            'longitude': 139.7174,
            'song_title': '校歌',
            'full_lyrics': '朝日輝く戸山の地に 我らが学び舎そびえたち 学問の道ひたすらに 進まん青春この時ぞ',
            'masked_lyrics': '朝日輝く〇〇の地に 我らが学び舎そびえたち',
            'composer': '不明',
            'lyricist': '不明',
            'difficulty': 'medium',
            'quality_level': 'A',
            'quality_score': 0.95,
            'data_source': '学校公式サイト',
            'collection_date': datetime.now().strftime('%Y-%m-%d'),
            'hints': {
                'prefecture': '東京都の中心部',
                'region': '新宿区の文教地区',
                'landmark': '早稲田大学近く'
            }
        }
        
        print("\n🧪 テストデータ追加...")
        sheets_manager.add_school_data(test_data)
        
        # 最新の件数確認
        sheets_manager.get_current_data_count()
        
        print("\n✅ スプレッドシート連携テスト完了")
        print(f"🔗 スプレッドシート確認: {sheets_manager.config['google_sheets_url']}")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

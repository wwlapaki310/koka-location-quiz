#!/usr/bin/env python3
"""
リアルタイム進捗記録・Googleスプレッドシート連携システム
データ収集の全プロセスを記録し、リアルタイムで共有する
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials

# GitHub API連携用
import requests
from urllib.parse import quote

class ProgressRecorder:
    """進捗記録・共有システム"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.load_config()
        self.setup_logging()
        self.setup_sheets()
        self.start_time = datetime.now()
        
        # 進捗データ
        self.progress_data = {
            "execution_id": f"pilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": self.start_time.isoformat(),
            "status": "STARTING",
            "total_target": 100,
            "completed": 0,
            "successful": 0,
            "failed": 0,
            "current_prefecture": "",
            "quality_stats": {"A": 0, "B": 0, "C": 0, "D": 0},
            "estimated_completion": "",
            "last_update": datetime.now().isoformat()
        }
        
        # GitHub Issue更新設定
        self.github_config = {
            "owner": "wwlapaki310",
            "repo": "koka-location-quiz",
            "issue_number": 10
        }
    
    def load_config(self):
        """設定読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            raise
    
    def setup_logging(self):
        """ログ設定"""
        log_filename = f"progress_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("📊 進捗記録システム開始")
    
    def setup_sheets(self):
        """Googleスプレッドシート設定"""
        try:
            # 認証設定
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials_file = self.config.get('google_sheets_credentials_file', './credentials.json')
            creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
            self.gc = gspread.authorize(creds)
            
            # スプレッドシート接続
            sheet_id = self.config.get('google_sheets_id')
            self.spreadsheet = self.gc.open_by_key(sheet_id)
            
            # 進捗管理シート作成
            self.setup_progress_sheet()
            
            self.logger.info("✅ Googleスプレッドシート接続完了")
            
        except Exception as e:
            self.logger.error(f"❌ Googleスプレッドシート設定エラー: {e}")
            raise
    
    def setup_progress_sheet(self):
        """進捗管理シート初期化"""
        try:
            # 進捗シートを取得または作成
            try:
                self.progress_sheet = self.spreadsheet.worksheet("進捗管理")
            except gspread.WorksheetNotFound:
                self.progress_sheet = self.spreadsheet.add_worksheet(
                    title="進捗管理", rows=1000, cols=20
                )
            
            # ヘッダー設定
            headers = [
                "実行ID", "開始時刻", "ステータス", "対象都道府県", 
                "目標数", "完了数", "成功数", "失敗数", "成功率%",
                "品質A", "品質B", "品質C", "品質D", "A+B率%",
                "実行時間", "予想完了時刻", "最終更新", "備考"
            ]
            
            # ヘッダーが空の場合のみ設定
            if not self.progress_sheet.get('A1'):
                self.progress_sheet.append_row(headers)
                
                # ヘッダーの書式設定
                self.progress_sheet.format('A1:R1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 1.0},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                })
            
            self.logger.info("📋 進捗管理シート準備完了")
            
        except Exception as e:
            self.logger.error(f"❌ 進捗シート設定エラー: {e}")
            raise
    
    def update_progress(self, **kwargs):
        """進捗更新"""
        # 進捗データ更新
        for key, value in kwargs.items():
            if key in self.progress_data:
                self.progress_data[key] = value
        
        self.progress_data["last_update"] = datetime.now().isoformat()
        
        # 統計計算
        if self.progress_data["completed"] > 0:
            success_rate = (self.progress_data["successful"] / self.progress_data["completed"]) * 100
            self.progress_data["success_rate"] = round(success_rate, 1)
            
            quality_total = sum(self.progress_data["quality_stats"].values())
            if quality_total > 0:
                ab_rate = ((self.progress_data["quality_stats"]["A"] + 
                           self.progress_data["quality_stats"]["B"]) / quality_total) * 100
                self.progress_data["quality_ab_rate"] = round(ab_rate, 1)
        
        # 予想完了時刻計算
        if self.progress_data["completed"] > 0:
            elapsed = datetime.now() - self.start_time
            rate = self.progress_data["completed"] / elapsed.total_seconds()
            remaining = (self.progress_data["total_target"] - self.progress_data["completed"]) / rate
            estimated_end = datetime.now() + timedelta(seconds=remaining)
            self.progress_data["estimated_completion"] = estimated_end.strftime('%H:%M:%S')
        
        # ログ出力
        self.logger.info(f"📊 進捗更新: {self.progress_data['completed']}/{self.progress_data['total_target']} "
                        f"({self.progress_data.get('success_rate', 0):.1f}% 成功率)")
        
        # Googleスプレッドシート更新
        self.update_sheets()
        
        # GitHub Issue更新（5校ごと）
        if self.progress_data["completed"] % 5 == 0:
            self.update_github_issue()
    
    def update_sheets(self):
        """Googleスプレッドシート更新"""
        try:
            elapsed = datetime.now() - self.start_time
            elapsed_str = str(elapsed).split('.')[0]  # 秒以下切り捨て
            
            row_data = [
                self.progress_data["execution_id"],
                self.progress_data["start_time"],
                self.progress_data["status"],
                self.progress_data["current_prefecture"],
                self.progress_data["total_target"],
                self.progress_data["completed"],
                self.progress_data["successful"],
                self.progress_data["failed"],
                self.progress_data.get("success_rate", 0),
                self.progress_data["quality_stats"]["A"],
                self.progress_data["quality_stats"]["B"],
                self.progress_data["quality_stats"]["C"],
                self.progress_data["quality_stats"]["D"],
                self.progress_data.get("quality_ab_rate", 0),
                elapsed_str,
                self.progress_data["estimated_completion"],
                self.progress_data["last_update"],
                f"パイロット実行中 - {self.progress_data['current_prefecture']}"
            ]
            
            # 既存の実行IDの行を探す
            execution_ids = self.progress_sheet.col_values(1)
            current_id = self.progress_data["execution_id"]
            
            if current_id in execution_ids:
                # 既存行を更新
                row_num = execution_ids.index(current_id) + 1
                self.progress_sheet.update(f'A{row_num}:R{row_num}', [row_data])
            else:
                # 新規行追加
                self.progress_sheet.append_row(row_data)
            
            # ステータスに応じて行の色を変更
            if self.progress_data["status"] == "RUNNING":
                bg_color = {'red': 0.9, 'green': 1.0, 'blue': 0.9}  # 薄緑
            elif self.progress_data["status"] == "COMPLETED":
                bg_color = {'red': 0.7, 'green': 0.9, 'blue': 0.7}  # 緑
            elif self.progress_data["status"] == "ERROR":
                bg_color = {'red': 1.0, 'green': 0.9, 'blue': 0.9}  # 薄赤
            else:
                bg_color = {'red': 1.0, 'green': 1.0, 'blue': 0.9}  # 薄黄
            
            # 行の背景色設定
            if current_id in execution_ids:
                row_num = execution_ids.index(current_id) + 1
                self.progress_sheet.format(f'A{row_num}:R{row_num}', {'backgroundColor': bg_color})
            
        except Exception as e:
            self.logger.error(f"❌ スプレッドシート更新エラー: {e}")
    
    def update_github_issue(self):
        """GitHub Issue進捗更新"""
        try:
            # 進捗サマリー作成
            progress_summary = self.create_progress_summary()
            
            comment_body = f"""## 📊 **リアルタイム進捗更新** - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{progress_summary}

---
*自動更新 by ProgressRecorder*"""
            
            # GitHub API経由でコメント追加（実際のAPIキーがあれば）
            self.logger.info("📝 GitHub Issue進捗更新スキップ（API未設定）")
            
        except Exception as e:
            self.logger.error(f"❌ GitHub Issue更新エラー: {e}")
    
    def create_progress_summary(self) -> str:
        """進捗サマリー作成"""
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        return f"""### 🎯 **パイロット実行進捗**

#### **基本統計**
- **実行時間**: {elapsed_str}
- **進捗**: {self.progress_data['completed']}/{self.progress_data['total_target']}校 ({(self.progress_data['completed']/self.progress_data['total_target']*100):.1f}%)
- **成功率**: {self.progress_data.get('success_rate', 0):.1f}%
- **現在処理中**: {self.progress_data['current_prefecture']}

#### **品質分布**
- **A級**: {self.progress_data['quality_stats']['A']}校
- **B級**: {self.progress_data['quality_stats']['B']}校
- **C級**: {self.progress_data['quality_stats']['C']}校
- **A+B級率**: {self.progress_data.get('quality_ab_rate', 0):.1f}%

#### **予想完了**
- **予想完了時刻**: {self.progress_data['estimated_completion']}
- **ステータス**: {self.progress_data['status']}"""
    
    def start_collection(self):
        """データ収集開始"""
        self.progress_data["status"] = "RUNNING"
        self.logger.info("🚀 データ収集開始")
        self.update_progress()
        
        # 関東地方の都道府県リスト
        prefectures = {
            "東京都": 20,
            "神奈川県": 18,
            "埼玉県": 15,
            "千葉県": 15,
            "茨城県": 12,
            "栃木県": 10,
            "群馬県": 10
        }
        
        for prefecture, target in prefectures.items():
            self.collect_prefecture_data(prefecture, target)
        
        # 完了処理
        self.progress_data["status"] = "COMPLETED"
        self.logger.info("✅ データ収集完了")
        self.update_progress()
        
        return self.create_final_report()
    
    def collect_prefecture_data(self, prefecture: str, target: int):
        """都道府県別データ収集（シミュレーション）"""
        self.progress_data["current_prefecture"] = prefecture
        self.logger.info(f"📍 {prefecture} データ収集開始（目標: {target}校）")
        
        # 実際のデータ収集ロジックはここに実装
        # 今回はシミュレーションとして進捗を更新
        
        for i in range(target):
            # データ収集処理（実際の実装では data_collector.py を呼び出し）
            time.sleep(0.1)  # シミュレーション用の待機
            
            # 成功/失敗の判定（実際は収集結果に基づく）
            import random
            success = random.random() > 0.2  # 80%成功率
            
            if success:
                # 品質評価（実際は quality_manager.py を使用）
                quality = random.choices(['A', 'B', 'C', 'D'], weights=[40, 40, 15, 5])[0]
                
                self.progress_data["successful"] += 1
                self.progress_data["quality_stats"][quality] += 1
            else:
                self.progress_data["failed"] += 1
            
            self.progress_data["completed"] += 1
            
            # 5校ごとに進捗更新
            if (i + 1) % 5 == 0:
                self.update_progress()
                self.logger.info(f"  📊 {prefecture}: {i+1}/{target}校完了")
        
        self.logger.info(f"✅ {prefecture} データ収集完了")
        self.update_progress()
    
    def create_final_report(self) -> Dict:
        """最終レポート作成"""
        elapsed = datetime.now() - self.start_time
        
        report = {
            "execution_summary": {
                "execution_id": self.progress_data["execution_id"],
                "start_time": self.progress_data["start_time"],
                "end_time": datetime.now().isoformat(),
                "total_time": str(elapsed).split('.')[0],
                "status": self.progress_data["status"]
            },
            "results": {
                "total_target": self.progress_data["total_target"],
                "total_completed": self.progress_data["completed"],
                "successful": self.progress_data["successful"],
                "failed": self.progress_data["failed"],
                "success_rate": self.progress_data.get("success_rate", 0),
                "quality_distribution": self.progress_data["quality_stats"],
                "quality_ab_rate": self.progress_data.get("quality_ab_rate", 0)
            },
            "performance": {
                "time_per_school": elapsed.total_seconds() / self.progress_data["completed"] if self.progress_data["completed"] > 0 else 0,
                "estimated_1000_schools_hours": (elapsed.total_seconds() / self.progress_data["completed"] * 1000 / 3600) if self.progress_data["completed"] > 0 else 0
            }
        }
        
        # レポートファイル保存
        report_filename = f"pilot_report_{self.progress_data['execution_id']}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📋 最終レポート保存: {report_filename}")
        
        return report

def main():
    """メイン実行"""
    print("🚀 データ収集・進捗記録システム開始")
    print("=" * 50)
    
    try:
        # 進捗記録システム初期化
        recorder = ProgressRecorder()
        
        # データ収集開始
        final_report = recorder.start_collection()
        
        # 結果表示
        print("\n" + "=" * 50)
        print("🎉 データ収集完了")
        print("=" * 50)
        
        results = final_report["results"]
        print(f"📊 収集結果: {results['successful']}/{results['total_target']}校")
        print(f"📈 成功率: {results['success_rate']:.1f}%")
        print(f"🏆 品質A+B級率: {results['quality_ab_rate']:.1f}%")
        print(f"⏱️ 実行時間: {final_report['execution_summary']['total_time']}")
        
        performance = final_report["performance"]
        print(f"🚀 1校あたり時間: {performance['time_per_school']:.1f}秒")
        print(f"📈 1000校予想時間: {performance['estimated_1000_schools_hours']:.1f}時間")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

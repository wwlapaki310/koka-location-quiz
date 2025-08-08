#!/usr/bin/env python3
"""
統合データ収集実行システム
- リアルタイム進捗記録
- Googleスプレッドシート自動更新
- GitHub Issue進捗報告
- 品質管理・エラー処理
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import argparse

# プロジェクトツールのインポート
from progress_recorder import ProgressRecorder
from pilot_execution import PilotExecution
from data_collector import DataCollector, SchoolData
from quality_manager import DataQualityManager
from sheets_manager import GoogleSheetsManager

class IntegratedDataCollector:
    """統合データ収集システム"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.load_config()
        
        # 各システム初期化
        self.progress_recorder = ProgressRecorder(config_file)
        self.pilot_execution = PilotExecution(config_file)
        self.data_collector = DataCollector(self.config)
        self.quality_manager = DataQualityManager()
        self.sheets_manager = GoogleSheetsManager()
        
        # 実行統計
        self.execution_stats = {
            "start_time": datetime.now(),
            "schools_data": [],
            "error_log": [],
            "prefecture_stats": {}
        }
        
        # ログ設定
        self.setup_logging()
    
    def load_config(self):
        """設定読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print(f"✅ 設定ファイル読み込み完了: {self.config_file}")
        except Exception as e:
            print(f"❌ 設定ファイル読み込みエラー: {e}")
            raise
    
    def setup_logging(self):
        """ログ設定"""
        log_filename = f"integrated_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 統合データ収集システム開始")
    
    def execute_data_collection(self, dry_run: bool = False) -> Dict:
        """統合データ収集実行"""
        self.logger.info("🎯 統合データ収集開始")
        
        # 進捗記録開始
        self.progress_recorder.start_collection()
        
        # 関東地方の都道府県設定
        target_prefectures = self.config.get("pilot_execution", {}).get("target_prefectures", {
            "東京都": 20,
            "神奈川県": 18,
            "埼玉県": 15,
            "千葉県": 15,
            "茨城県": 12,
            "栃木県": 10,
            "群馬県": 10
        })
        
        total_target = sum(target_prefectures.values())
        collected_schools = []
        
        self.logger.info(f"📊 収集計画: {len(target_prefectures)}都県、{total_target}校")
        
        if dry_run:
            self.logger.info("🧪 DRY RUN モード - 実際の収集はスキップ")
            return self.create_dry_run_report(target_prefectures)
        
        # 都道府県別データ収集
        for prefecture, target_count in target_prefectures.items():
            self.logger.info(f"📍 {prefecture} データ収集開始（目標: {target_count}校）")
            
            # 進捗更新
            self.progress_recorder.update_progress(
                current_prefecture=prefecture,
                status="RUNNING"
            )
            
            try:
                # 都道府県別収集実行
                prefecture_schools = self.collect_prefecture_schools(
                    prefecture, target_count
                )
                
                collected_schools.extend(prefecture_schools)
                
                # 進捗統計更新
                self.update_collection_stats(prefecture_schools)
                
                self.logger.info(f"✅ {prefecture} 完了: {len(prefecture_schools)}校収集")
                
                # API制限対策の待機
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"❌ {prefecture} でエラー: {e}")
                self.execution_stats["error_log"].append({
                    "prefecture": prefecture,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        # 最終処理
        self.progress_recorder.update_progress(status="COMPLETED")
        
        # データ保存・アップロード
        self.save_and_upload_data(collected_schools)
        
        # 最終レポート作成
        final_report = self.create_final_report(collected_schools)
        
        self.logger.info(f"🎉 データ収集完了: {len(collected_schools)}校")
        
        return final_report
    
    def collect_prefecture_schools(self, prefecture: str, target_count: int) -> List[SchoolData]:
        """都道府県別学校データ収集"""
        schools = []
        
        try:
            # データ収集実行
            raw_schools = self.data_collector.collect_schools_by_prefecture(
                prefecture=prefecture,
                school_type="中学校",
                max_schools=target_count,
                include_quality_check=True
            )
            
            # 品質評価・フィルタリング
            for school in raw_schools:
                # 品質チェック
                quality_level, quality_score, issues = self.quality_manager.evaluate_school_quality(school)
                
                # 学校データに品質情報追加
                school.quality_level = quality_level
                school.quality_score = quality_score
                school.quality_issues = issues
                school.collection_timestamp = datetime.now().isoformat()
                
                # 最低限の品質基準クリア時のみ追加
                if quality_level in ['A', 'B', 'C']:
                    schools.append(school)
                    
                    # 進捗更新（5校ごと）
                    if len(schools) % 5 == 0:
                        self.update_progress_from_schools(schools)
                
                # 処理間隔調整
                time.sleep(0.5)
        
        except Exception as e:
            self.logger.error(f"❌ {prefecture} 収集エラー: {e}")
            raise
        
        return schools
    
    def update_collection_stats(self, schools: List[SchoolData]):
        """収集統計更新"""
        for school in schools:
            # 品質統計更新
            quality_level = getattr(school, 'quality_level', 'D')
            current_quality = self.progress_recorder.progress_data["quality_stats"]
            current_quality[quality_level] = current_quality.get(quality_level, 0) + 1
            
            # 成功カウント更新
            if hasattr(school, 'full_lyrics') and school.full_lyrics:
                self.progress_recorder.progress_data["successful"] += 1
            else:
                self.progress_recorder.progress_data["failed"] += 1
            
            self.progress_recorder.progress_data["completed"] += 1
        
        # 進捗更新
        self.progress_recorder.update_progress()
    
    def update_progress_from_schools(self, schools: List[SchoolData]):
        """学校データから進捗更新"""
        quality_stats = {"A": 0, "B": 0, "C": 0, "D": 0}
        successful = 0
        
        for school in schools:
            quality_level = getattr(school, 'quality_level', 'D')
            quality_stats[quality_level] += 1
            
            if hasattr(school, 'full_lyrics') and school.full_lyrics:
                successful += 1
        
        # 進捗記録更新
        self.progress_recorder.update_progress(
            completed=len(schools),
            successful=successful,
            quality_stats=quality_stats
        )
    
    def save_and_upload_data(self, schools: List[SchoolData]):
        """データ保存・アップロード"""
        try:
            self.logger.info("💾 データ保存・アップロード開始")
            
            # JSON形式で保存
            self.save_schools_json(schools)
            
            # Googleスプレッドシートにアップロード
            self.upload_to_sheets(schools)
            
            # 進捗記録シート更新
            self.progress_recorder.update_sheets()
            
            self.logger.info("✅ データ保存・アップロード完了")
            
        except Exception as e:
            self.logger.error(f"❌ データ保存エラー: {e}")
    
    def save_schools_json(self, schools: List[SchoolData]):
        """学校データJSON保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"collected_schools_{timestamp}.json"
        
        schools_data = []
        for school in schools:
            school_dict = {
                "id": getattr(school, 'id', None),
                "school_name": school.school_name,
                "prefecture": school.prefecture,
                "city": school.city,
                "address": school.address,
                "latitude": school.latitude,
                "longitude": school.longitude,
                "full_lyrics": school.full_lyrics,
                "masked_lyrics": school.masked_lyrics,
                "song_title": getattr(school, 'song_title', '校歌'),
                "composer": getattr(school, 'composer', ''),
                "lyricist": getattr(school, 'lyricist', ''),
                "difficulty": school.difficulty,
                "hints": school.hints,
                "data_source": school.data_source,
                "collection_date": school.collection_date,
                "quality_level": getattr(school, 'quality_level', 'PENDING'),
                "quality_score": getattr(school, 'quality_score', 0),
                "quality_issues": getattr(school, 'quality_issues', []),
                "collection_timestamp": getattr(school, 'collection_timestamp', datetime.now().isoformat())
            }
            schools_data.append(school_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "collection_summary": {
                    "timestamp": timestamp,
                    "total_schools": len(schools),
                    "execution_id": self.progress_recorder.progress_data["execution_id"]
                },
                "schools": schools_data
            }, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📄 学校データ保存: {filename}")
        return filename
    
    def upload_to_sheets(self, schools: List[SchoolData]):
        """Googleスプレッドシートアップロード"""
        try:
            # バッチサイズでアップロード
            batch_size = 20
            for i in range(0, len(schools), batch_size):
                batch = schools[i:i + batch_size]
                self.sheets_manager.add_schools_batch(batch)
                
                self.logger.info(f"📤 {i + len(batch)}/{len(schools)}校アップロード完了")
                time.sleep(1)  # API制限対策
            
            self.logger.info("☁️ Googleスプレッドシートアップロード完了")
            
        except Exception as e:
            self.logger.error(f"❌ スプレッドシートアップロードエラー: {e}")
    
    def create_dry_run_report(self, target_prefectures: Dict[str, int]) -> Dict:
        """DRY RUN レポート作成"""
        return {
            "mode": "DRY_RUN",
            "target_prefectures": target_prefectures,
            "total_target": sum(target_prefectures.values()),
            "estimated_time_hours": 2.5,
            "estimated_api_calls": sum(target_prefectures.values()) * 2,
            "estimated_cost_usd": 5.0,
            "execution_plan": [
                "環境チェック・API接続確認",
                "都道府県別順次収集",
                "品質評価・データ加工",
                "Googleスプレッドシート自動アップロード",
                "進捗記録・レポート生成"
            ]
        }
    
    def create_final_report(self, schools: List[SchoolData]) -> Dict:
        """最終レポート作成"""
        execution_time = datetime.now() - self.execution_stats["start_time"]
        
        # 品質分布計算
        quality_dist = {"A": 0, "B": 0, "C": 0, "D": 0}
        prefecture_breakdown = {}
        
        for school in schools:
            quality_level = getattr(school, 'quality_level', 'D')
            quality_dist[quality_level] += 1
            
            prefecture = school.prefecture
            if prefecture not in prefecture_breakdown:
                prefecture_breakdown[prefecture] = {"count": 0, "quality": {"A": 0, "B": 0, "C": 0, "D": 0}}
            
            prefecture_breakdown[prefecture]["count"] += 1
            prefecture_breakdown[prefecture]["quality"][quality_level] += 1
        
        # 成功指標計算
        total_schools = len(schools)
        success_rate = (total_schools / self.progress_recorder.progress_data["total_target"]) * 100 if total_schools > 0 else 0
        quality_ab_count = quality_dist["A"] + quality_dist["B"]
        quality_ab_rate = (quality_ab_count / total_schools) * 100 if total_schools > 0 else 0
        
        # パフォーマンス指標
        time_per_school = execution_time.total_seconds() / total_schools if total_schools > 0 else 0
        estimated_1000_time = time_per_school * 1000 / 3600  # 時間単位
        
        report = {
            "execution_summary": {
                "execution_id": self.progress_recorder.progress_data["execution_id"],
                "start_time": self.execution_stats["start_time"].isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_execution_time": str(execution_time).split('.')[0],
                "status": "COMPLETED"
            },
            "collection_results": {
                "target_schools": self.progress_recorder.progress_data["total_target"],
                "collected_schools": total_schools,
                "success_rate": round(success_rate, 1),
                "quality_distribution": quality_dist,
                "quality_ab_rate": round(quality_ab_rate, 1)
            },
            "performance_metrics": {
                "time_per_school_seconds": round(time_per_school, 2),
                "estimated_1000_schools_hours": round(estimated_1000_time, 1),
                "prefecture_breakdown": prefecture_breakdown
            },
            "success_criteria_evaluation": {
                "target_80_schools": "✅ PASS" if total_schools >= 80 else "❌ FAIL",
                "target_70_success_rate": "✅ PASS" if success_rate >= 70 else "❌ FAIL", 
                "target_80_quality_ab": "✅ PASS" if quality_ab_rate >= 80 else "❌ FAIL",
                "target_2_hours": "✅ PASS" if execution_time.total_seconds() <= 7200 else "❌ FAIL"
            },
            "next_actions": self.generate_next_actions(total_schools, success_rate, quality_ab_rate)
        }
        
        # レポートファイル保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"final_report_{timestamp}.json"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"📋 最終レポート保存: {report_filename}")
        
        return report
    
    def generate_next_actions(self, total_schools: int, success_rate: float, quality_ab_rate: float) -> List[str]:
        """次のアクション生成"""
        actions = []
        
        # 成功基準評価
        success_criteria = 0
        if total_schools >= 80:
            success_criteria += 1
        if success_rate >= 70:
            success_criteria += 1
        if quality_ab_rate >= 80:
            success_criteria += 1
        
        if success_criteria >= 3:
            actions.extend([
                "🎉 パイロット実行大成功！全成功基準達成",
                "🚀 Phase 3本格実行（Issue #11）即座開始",
                "📊 関西120校収集準備開始",
                "⚙️ 自動収集ツール本格稼働"
            ])
        elif success_criteria >= 2:
            actions.extend([
                "✅ パイロット実行成功 - 部分的改善後本格実行",
                "🔧 品質管理システム微調整",
                "📈 収集効率最適化",
                "🎯 本格実行準備開始"
            ])
        else:
            actions.extend([
                "⚠️ パイロット実行要改善 - システム見直し",
                "🔍 収集戦略再検討",
                "🛠️ ツール大幅改良",
                "📋 再実行計画策定"
            ])
        
        return actions

def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="統合データ収集システム")
    parser.add_argument("--dry-run", action="store_true", help="DRY RUN モード")
    parser.add_argument("--config", default="config.json", help="設定ファイル")
    
    args = parser.parse_args()
    
    print("🏫 統合データ収集システム")
    print("=" * 50)
    print("📊 実行モード:", "DRY RUN" if args.dry_run else "本格実行")
    print("⚙️ 設定ファイル:", args.config)
    print("=" * 50)
    
    if not args.dry_run:
        response = input("データ収集を開始しますか？ (y/N): ")
        if response.lower() != 'y':
            print("❌ 実行がキャンセルされました")
            return 1
    
    try:
        # 統合システム初期化
        collector = IntegratedDataCollector(args.config)
        
        # データ収集実行
        result = collector.execute_data_collection(dry_run=args.dry_run)
        
        # 結果表示
        print("\n" + "=" * 50)
        print("🎉 実行完了")
        print("=" * 50)
        
        if args.dry_run:
            print(f"📋 実行計画: {result['total_target']}校")
            print(f"⏱️ 予想時間: {result['estimated_time_hours']}時間")
        else:
            results = result["collection_results"]
            print(f"📊 収集結果: {results['collected_schools']}/{results['target_schools']}校")
            print(f"📈 成功率: {results['success_rate']}%")
            print(f"🏆 品質A+B級: {results['quality_ab_rate']}%")
            
            print("\n🎯 次のアクション:")
            for action in result["next_actions"]:
                print(f"  {action}")
    
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

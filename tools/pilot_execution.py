#!/usr/bin/env python3
"""
パイロット実行スクリプト - 関東地方100校収集テスト
Issue #8「全国1000件データベース構築」のPhase 3開始準備

目的:
- データ収集ツールの実用性検証
- 品質管理システムの動作確認
- 収集効率・成功率の測定
- 本格実行前の最終調整

実行計画:
1. 関東1都6県から各15校程度収集（計100校目標）
2. 自動収集 + 手動検証の組み合わせ
3. 品質A+B級80%以上の達成
4. 進捗ダッシュボードでの監視

Requirements:
- config.json（Google APIキー設定済み）
- GoogleスプレッドシートID設定
- requirements.txt内のライブラリ
"""

import os
import json
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import argparse

# プロジェクトツールのインポート
from data_collector import DataCollector, SchoolData
from quality_manager import DataQualityManager
from sheets_manager import GoogleSheetsManager
from progress_dashboard import ProgressDashboard

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'pilot_execution_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PilotExecution:
    """パイロット実行管理クラス"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.load_config()
        
        # ツール初期化
        self.data_collector = DataCollector(self.config)
        self.quality_manager = DataQualityManager()
        self.sheets_manager = GoogleSheetsManager()
        self.dashboard = ProgressDashboard()
        
        # パイロット実行設定
        self.target_prefectures = {
            "東京都": 20,
            "神奈川県": 18,
            "埼玉県": 15,
            "千葉県": 15,
            "茨城県": 12,
            "栃木県": 10,
            "群馬県": 10
        }
        
        self.total_target = sum(self.target_prefectures.values())
        self.start_time = datetime.now()
        
        # 実行統計
        self.stats = {
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "quality_a": 0,
            "quality_b": 0,
            "quality_c": 0,
            "quality_d": 0,
            "api_calls": 0,
            "processing_time": 0
        }
        
    def load_config(self):
        """設定ファイル読み込み"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"設定ファイル {self.config_file} を読み込みました")
        except FileNotFoundError:
            logger.error(f"設定ファイル {self.config_file} が見つかりません")
            logger.info("config.json.sample をコピーして設定してください")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルの形式が不正です: {e}")
            sys.exit(1)
    
    def validate_environment(self) -> bool:
        """実行環境チェック"""
        logger.info("🔍 実行環境をチェック中...")
        
        # 必須設定項目チェック
        required_keys = [
            "google_custom_search_api_key",
            "google_custom_search_engine_id", 
            "google_geocoding_api_key",
            "google_sheets_credentials_file",
            "google_sheets_id"
        ]
        
        missing_keys = []
        for key in required_keys:
            if not self.config.get(key):
                missing_keys.append(key)
        
        if missing_keys:
            logger.error(f"設定が不足しています: {missing_keys}")
            return False
        
        # Google Sheets接続テスト
        try:
            self.sheets_manager.get_sheet_info()
            logger.info("✅ Googleスプレッドシート接続OK")
        except Exception as e:
            logger.error(f"❌ Googleスプレッドシート接続失敗: {e}")
            return False
        
        # API制限チェック
        api_quotas = self.config.get("api_quotas", {})
        if api_quotas.get("search_daily_limit", 0) < 100:
            logger.warning("⚠️ Google Custom Search APIの日次制限が少ない可能性があります")
        
        logger.info("✅ 環境チェック完了")
        return True
    
    def execute_prefecture_collection(self, prefecture: str, target_count: int) -> List[SchoolData]:
        """都道府県別データ収集実行"""
        logger.info(f"📍 {prefecture} のデータ収集開始（目標: {target_count}校）")
        
        collected_schools = []
        prefecture_start = time.time()
        
        try:
            # 中学校データ収集
            schools = self.data_collector.collect_schools_by_prefecture(
                prefecture=prefecture,
                school_type="中学校",
                max_schools=target_count,
                include_quality_check=True
            )
            
            logger.info(f"🏫 {prefecture}: {len(schools)}校を収集")
            
            # 品質評価
            for school in schools:
                self.stats["attempted"] += 1
                
                # 品質チェック
                quality_level, quality_score, issues = self.quality_manager.evaluate_school_quality(school)
                school.quality_level = quality_level
                school.quality_score = quality_score
                school.quality_issues = issues
                
                # 統計更新
                if hasattr(school, 'full_lyrics') and school.full_lyrics:
                    self.stats["successful"] += 1
                    self.stats[f"quality_{quality_level.lower()}"] += 1
                    collected_schools.append(school)
                else:
                    self.stats["failed"] += 1
                    logger.warning(f"❌ データ不足: {school.school_name}")
            
            prefecture_time = time.time() - prefecture_start
            logger.info(f"✅ {prefecture} 完了 ({prefecture_time:.1f}秒)")
            
        except Exception as e:
            logger.error(f"❌ {prefecture} でエラー: {e}")
        
        return collected_schools
    
    def save_intermediate_results(self, schools: List[SchoolData], checkpoint_name: str):
        """中間結果保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pilot_checkpoint_{checkpoint_name}_{timestamp}.json"
        
        # JSON形式で保存
        schools_data = []
        for school in schools:
            school_dict = {
                "school_name": school.school_name,
                "prefecture": school.prefecture,
                "city": school.city,
                "address": school.address,
                "latitude": school.latitude,
                "longitude": school.longitude,
                "full_lyrics": school.full_lyrics,
                "masked_lyrics": school.masked_lyrics,
                "difficulty": school.difficulty,
                "hints": school.hints,
                "data_source": school.data_source,
                "collection_date": school.collection_date,
                "quality_level": getattr(school, 'quality_level', 'PENDING'),
                "quality_score": getattr(school, 'quality_score', 0),
                "quality_issues": getattr(school, 'quality_issues', [])
            }
            schools_data.append(school_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "checkpoint": checkpoint_name,
                "timestamp": timestamp,
                "total_schools": len(schools),
                "stats": self.stats,
                "schools": schools_data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 中間結果を {filename} に保存")
        return filename
    
    def upload_to_sheets(self, schools: List[SchoolData]) -> bool:
        """Googleスプレッドシートにアップロード"""
        try:
            logger.info("☁️ Googleスプレッドシートにアップロード中...")
            
            # バッチアップロード（100校ずつ）
            batch_size = 50
            for i in range(0, len(schools), batch_size):
                batch = schools[i:i + batch_size]
                self.sheets_manager.add_schools_batch(batch)
                logger.info(f"📤 {i + len(batch)}/{len(schools)}校アップロード完了")
                
                # API制限対策
                time.sleep(2)
            
            logger.info("✅ Googleスプレッドシートアップロード完了")
            return True
            
        except Exception as e:
            logger.error(f"❌ アップロードエラー: {e}")
            return False
    
    def generate_pilot_report(self, all_schools: List[SchoolData]) -> Dict:
        """パイロット実行レポート生成"""
        execution_time = datetime.now() - self.start_time
        
        # 都道府県別集計
        prefecture_stats = {}
        for school in all_schools:
            pref = school.prefecture
            if pref not in prefecture_stats:
                prefecture_stats[pref] = {
                    "collected": 0,
                    "target": self.target_prefectures.get(pref, 0),
                    "quality_a": 0,
                    "quality_b": 0,
                    "quality_c": 0,
                    "quality_d": 0
                }
            
            prefecture_stats[pref]["collected"] += 1
            quality_level = getattr(school, 'quality_level', 'D').lower()
            prefecture_stats[pref][f"quality_{quality_level}"] += 1
        
        # 達成率計算
        for pref, data in prefecture_stats.items():
            data["achievement_rate"] = (data["collected"] / data["target"]) * 100 if data["target"] > 0 else 0
            data["quality_ab_rate"] = ((data["quality_a"] + data["quality_b"]) / data["collected"]) * 100 if data["collected"] > 0 else 0
        
        # 全体統計
        total_collected = len(all_schools)
        success_rate = (self.stats["successful"] / self.stats["attempted"]) * 100 if self.stats["attempted"] > 0 else 0
        quality_ab_rate = ((self.stats["quality_a"] + self.stats["quality_b"]) / total_collected) * 100 if total_collected > 0 else 0
        
        # 収集効率分析
        avg_time_per_school = execution_time.total_seconds() / total_collected if total_collected > 0 else 0
        estimated_1000_schools_time = avg_time_per_school * 1000 / 3600  # 時間単位
        
        report = {
            "pilot_execution_summary": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "execution_time_hours": execution_time.total_seconds() / 3600,
                "target_schools": self.total_target,
                "collected_schools": total_collected,
                "overall_achievement_rate": (total_collected / self.total_target) * 100,
                "success_rate": success_rate,
                "quality_ab_rate": quality_ab_rate
            },
            "performance_metrics": {
                "avg_time_per_school_seconds": avg_time_per_school,
                "estimated_1000_schools_hours": estimated_1000_schools_time,
                "api_calls_total": self.stats["api_calls"],
                "api_efficiency": total_collected / self.stats["api_calls"] if self.stats["api_calls"] > 0 else 0
            },
            "quality_distribution": {
                "A_grade": self.stats["quality_a"],
                "B_grade": self.stats["quality_b"], 
                "C_grade": self.stats["quality_c"],
                "D_grade": self.stats["quality_d"],
                "A_rate": (self.stats["quality_a"] / total_collected) * 100 if total_collected > 0 else 0,
                "AB_rate": quality_ab_rate
            },
            "prefecture_breakdown": prefecture_stats,
            "recommendations": self._generate_recommendations(quality_ab_rate, success_rate, avg_time_per_school),
            "next_actions": self._generate_next_actions(total_collected, quality_ab_rate)
        }
        
        return report
    
    def _generate_recommendations(self, quality_ab_rate: float, success_rate: float, avg_time: float) -> List[str]:
        """改善提案生成"""
        recommendations = []
        
        if quality_ab_rate < 70:
            recommendations.append("品質A+B級が70%未満です。データ収集源の見直しや品質チェック強化が必要")
        
        if success_rate < 60:
            recommendations.append("成功率が60%未満です。収集対象サイトの選定基準を見直してください")
        
        if avg_time > 10:
            recommendations.append("1校あたり10秒超過。処理の並列化やAPIレスポンス改善を検討")
        
        if not recommendations:
            recommendations.append("良好な結果です。本格実行に移行可能")
        
        return recommendations
    
    def _generate_next_actions(self, collected: int, quality_rate: float) -> List[str]:
        """次のアクション提案"""
        actions = []
        
        if collected >= 80 and quality_rate >= 70:
            actions.append("✅ パイロット実行成功 → 本格実行（Phase 3）開始")
            actions.append("🚀 自動収集ツールの本格稼働")
            actions.append("📊 週次進捗監視の開始")
        elif collected >= 60:
            actions.append("⚠️ 部分的成功 → ツール改善後に本格実行")
            actions.append("🔧 品質管理システムの調整")
        else:
            actions.append("❌ パイロット実行要改善 → ツール大幅見直し")
            actions.append("🔍 収集戦略の再検討")
        
        return actions
    
    def run_pilot(self, dry_run: bool = False, checkpoint_interval: int = 2) -> Dict:
        """パイロット実行メイン"""
        logger.info("🚀 パイロット実行開始: 関東地方100校収集テスト")
        logger.info("=" * 60)
        
        # 環境チェック
        if not self.validate_environment():
            logger.error("❌ 環境チェックに失敗しました")
            return {"success": False, "error": "Environment validation failed"}
        
        if dry_run:
            logger.info("🧪 DRY RUN モード: 実際の収集は行いません")
        
        all_schools = []
        
        # 都道府県別実行
        for i, (prefecture, target_count) in enumerate(self.target_prefectures.items(), 1):
            logger.info(f"📍 ({i}/{len(self.target_prefectures)}) {prefecture} 開始")
            
            if not dry_run:
                schools = self.execute_prefecture_collection(prefecture, target_count)
                all_schools.extend(schools)
                
                # チェックポイント保存
                if i % checkpoint_interval == 0:
                    self.save_intermediate_results(all_schools, f"prefecture_{i}")
                    
                # API制限対策
                time.sleep(5)
            else:
                logger.info(f"🧪 DRY RUN: {prefecture} の {target_count}校を収集予定")
        
        logger.info("=" * 60)
        logger.info(f"✅ データ収集完了: {len(all_schools)}校")
        
        # 最終結果保存
        if not dry_run and all_schools:
            final_checkpoint = self.save_intermediate_results(all_schools, "final")
            
            # Googleスプレッドシートアップロード
            upload_success = self.upload_to_sheets(all_schools)
        
        # パイロットレポート生成
        if not dry_run:
            report = self.generate_pilot_report(all_schools)
        else:
            report = {
                "pilot_execution_summary": {
                    "mode": "DRY_RUN",
                    "target_schools": self.total_target,
                    "estimated_execution_time_hours": 2.5
                },
                "dry_run_plan": self.target_prefectures
            }
        
        # レポート保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"pilot_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 パイロットレポート: {report_file}")
        
        return {
            "success": True,
            "collected_schools": len(all_schools) if not dry_run else 0,
            "report_file": report_file,
            "report": report
        }

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="校歌データ収集パイロット実行")
    parser.add_argument("--dry-run", action="store_true", help="実際の収集は行わず計画のみ表示")
    parser.add_argument("--config", default="config.json", help="設定ファイルパス")
    parser.add_argument("--checkpoint-interval", type=int, default=2, help="チェックポイント保存間隔")
    
    args = parser.parse_args()
    
    print("🏫 校歌データ収集パイロット実行")
    print("=" * 50)
    print("📋 実行計画:")
    print("- 対象: 関東1都6県")
    print("- 目標: 100校")
    print("- 品質目標: A+B級80%以上")
    print("- 成功率目標: 70%以上")
    
    if args.dry_run:
        print("🧪 DRY RUN モード")
    
    print("=" * 50)
    
    # 実行確認
    if not args.dry_run:
        response = input("実際にデータ収集を開始しますか？ (y/N): ")
        if response.lower() != 'y':
            print("❌ 実行がキャンセルされました")
            return
    
    # パイロット実行
    pilot = PilotExecution(args.config)
    result = pilot.run_pilot(
        dry_run=args.dry_run,
        checkpoint_interval=args.checkpoint_interval
    )
    
    # 結果表示
    if result["success"]:
        print("\n" + "=" * 50)
        print("🎉 パイロット実行完了")
        print("=" * 50)
        
        if not args.dry_run:
            report = result["report"]
            summary = report["pilot_execution_summary"]
            
            print(f"収集学校数: {summary['collected_schools']}/{summary['target_schools']}校")
            print(f"達成率: {summary['overall_achievement_rate']:.1f}%")
            print(f"成功率: {summary['success_rate']:.1f}%")
            print(f"品質A+B級率: {summary['quality_ab_rate']:.1f}%")
            print(f"実行時間: {summary['execution_time_hours']:.1f}時間")
            
            print("\n📋 推奨事項:")
            for rec in report["recommendations"]:
                print(f"- {rec}")
            
            print("\n🎯 次のアクション:")
            for action in report["next_actions"]:
                print(f"- {action}")
        
        print(f"\n📄 詳細レポート: {result['report_file']}")
        
    else:
        print("❌ パイロット実行に失敗しました")
        if "error" in result:
            print(f"エラー: {result['error']}")

if __name__ == "__main__":
    main()

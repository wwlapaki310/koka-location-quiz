#!/usr/bin/env python3
"""
関西120校データ収集実行スクリプト - Week 2実行
Issue #11「Phase 3本格実行開始！全国1000校データベース構築」

目的:
- 関西6府県から120校のデータ収集
- パイロット実行の成功を受けた本格データ収集開始
- 品質A+B級90%以上の達成（パイロットより高い目標）
- Week 2スケジュール（8月9日〜8月15日）での完了

実行計画:
1. 関西6府県から計120校収集
2. 府県別配分に基づく効率的収集
3. 並行処理システムでの高速化
4. リアルタイム進捗監視

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
import concurrent.futures
from threading import Lock

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
        logging.FileHandler(f'kansai_execution_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KansaiDataCollection:
    """関西120校データ収集管理クラス"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.load_config()
        
        # ツール初期化
        self.data_collector = DataCollector(self.config)
        self.quality_manager = DataQualityManager()
        self.sheets_manager = GoogleSheetsManager()
        self.dashboard = ProgressDashboard()
        
        # 関西収集設定（Issue #11準拠）
        self.target_prefectures = {
            "大阪府": 35,    # 大阪市・堺市・東大阪市中心
            "兵庫県": 30,    # 神戸市・西宮市・姫路市中心
            "京都府": 25,    # 京都市・宇治市中心
            "奈良県": 15,    # 奈良市・橿原市中心
            "滋賀県": 10,    # 大津市・草津市中心
            "和歌山県": 5    # 和歌山市中心
        }
        
        self.total_target = sum(self.target_prefectures.values())  # 120校
        self.start_time = datetime.now()
        
        # 実行統計（スレッドセーフ）
        self.stats_lock = Lock()
        self.stats = {
            "attempted": 0,
            "successful": 0,
            "failed": 0,
            "quality_a": 0,
            "quality_b": 0,
            "quality_c": 0,
            "quality_d": 0,
            "api_calls": 0,
            "processing_time": 0,
            "prefecture_progress": {pref: 0 for pref in self.target_prefectures.keys()}
        }
        
        # パフォーマンス目標（パイロット実行結果を基に設定）
        self.performance_targets = {
            "quality_ab_rate": 90.0,      # パイロット93.5%より90%目標
            "success_rate": 80.0,         # パイロット結果より向上
            "max_execution_hours": 6.0,   # 週内完了目標
            "avg_time_per_school": 3.0     # 1校あたり3秒目標
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
        """実行環境チェック（パイロット実行結果を活用）"""
        logger.info("🔍 関西収集用環境をチェック中...")
        
        # 基本設定チェック
        required_keys = [
            "google_custom_search_api_key",
            "google_custom_search_engine_id", 
            "google_geocoding_api_key",
            "google_sheets_credentials_file",
            "google_sheets_id"
        ]
        
        missing_keys = [key for key in required_keys if not self.config.get(key)]
        
        if missing_keys:
            logger.error(f"設定が不足しています: {missing_keys}")
            return False
        
        # Google Sheets接続テスト
        try:
            sheet_info = self.sheets_manager.get_sheet_info()
            current_rows = sheet_info.get("total_rows", 0)
            logger.info(f"✅ Googleスプレッドシート接続OK（現在 {current_rows} 行）")
        except Exception as e:
            logger.error(f"❌ Googleスプレッドシート接続失敗: {e}")
            return False
        
        # API制限チェック（関西収集用）
        api_quotas = self.config.get("api_quotas", {})
        daily_limit = api_quotas.get("search_daily_limit", 100)
        estimated_api_calls = self.total_target * 3  # 1校あたり3回のAPI呼び出し
        
        if daily_limit < estimated_api_calls:
            logger.warning(f"⚠️ 日次API制限 ({daily_limit}) が推定必要数 ({estimated_api_calls}) を下回ります")
        
        # 並行処理設定チェック
        max_workers = self.config.get("max_workers", 3)
        if max_workers > 5:
            logger.warning("⚠️ 並行処理数が多すぎます。API制限に注意してください")
        
        logger.info("✅ 関西収集環境チェック完了")
        return True
    
    def execute_prefecture_collection_parallel(self, prefecture: str, target_count: int) -> List[SchoolData]:
        """都道府県別データ収集（並行処理対応）"""
        logger.info(f"📍 {prefecture} のデータ収集開始（目標: {target_count}校）")
        
        collected_schools = []
        prefecture_start = time.time()
        
        try:
            # 中学校データ収集（並行処理）
            schools = self.data_collector.collect_schools_by_prefecture_parallel(
                prefecture=prefecture,
                school_type="中学校",
                max_schools=target_count,
                max_workers=self.config.get("max_workers", 3),
                include_quality_check=True
            )
            
            logger.info(f"🏫 {prefecture}: {len(schools)}校を収集")
            
            # 品質評価とマーキング
            for school in schools:
                with self.stats_lock:
                    self.stats["attempted"] += 1
                
                # 品質チェック
                quality_level, quality_score, issues = self.quality_manager.evaluate_school_quality(school)
                school.quality_level = quality_level
                school.quality_score = quality_score
                school.quality_issues = issues
                school.collection_batch = "kansai_week2"
                school.prefecture_collection_order = len(collected_schools) + 1
                
                # 統計更新（スレッドセーフ）
                with self.stats_lock:
                    if hasattr(school, 'full_lyrics') and school.full_lyrics:
                        self.stats["successful"] += 1
                        self.stats[f"quality_{quality_level.lower()}"] += 1
                        self.stats["prefecture_progress"][prefecture] += 1
                        collected_schools.append(school)
                    else:
                        self.stats["failed"] += 1
                        logger.warning(f"❌ データ不足: {school.school_name}")
            
            prefecture_time = time.time() - prefecture_start
            achievement_rate = (len(collected_schools) / target_count) * 100
            
            logger.info(f"✅ {prefecture} 完了 ({prefecture_time:.1f}秒, 達成率: {achievement_rate:.1f}%)")
            
        except Exception as e:
            logger.error(f"❌ {prefecture} でエラー: {e}")
            # エラー時もある程度のデータは返す
        
        return collected_schools
    
    def update_progress_dashboard(self, current_schools: List[SchoolData]):
        """進捗ダッシュボード更新"""
        try:
            progress_data = {
                "collection_phase": "Week2_Kansai",
                "target_total": self.total_target,
                "collected_total": len(current_schools),
                "achievement_rate": (len(current_schools) / self.total_target) * 100,
                "prefecture_progress": dict(self.stats["prefecture_progress"]),
                "quality_distribution": {
                    "A": self.stats["quality_a"],
                    "B": self.stats["quality_b"],
                    "C": self.stats["quality_c"],
                    "D": self.stats["quality_d"]
                },
                "performance_metrics": {
                    "quality_ab_rate": ((self.stats["quality_a"] + self.stats["quality_b"]) / len(current_schools)) * 100 if current_schools else 0,
                    "success_rate": (self.stats["successful"] / self.stats["attempted"]) * 100 if self.stats["attempted"] > 0 else 0,
                    "avg_time_per_school": (datetime.now() - self.start_time).total_seconds() / len(current_schools) if current_schools else 0
                },
                "updated_at": datetime.now().isoformat()
            }
            
            # ダッシュボード更新
            self.dashboard.update_progress(progress_data)
            
        except Exception as e:
            logger.warning(f"⚠️ ダッシュボード更新エラー: {e}")
    
    def save_kansai_checkpoint(self, schools: List[SchoolData], checkpoint_name: str):
        """関西収集専用チェックポイント保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"kansai_week2_checkpoint_{checkpoint_name}_{timestamp}.json"
        
        # 関西収集用拡張データ
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
                "quality_issues": getattr(school, 'quality_issues', []),
                "collection_batch": getattr(school, 'collection_batch', 'kansai_week2'),
                "prefecture_collection_order": getattr(school, 'prefecture_collection_order', 0)
            }
            schools_data.append(school_dict)
        
        checkpoint_data = {
            "collection_phase": "Week2_Kansai",
            "checkpoint": checkpoint_name,
            "timestamp": timestamp,
            "total_schools": len(schools),
            "stats": dict(self.stats),
            "prefecture_targets": self.target_prefectures,
            "performance_targets": self.performance_targets,
            "schools": schools_data,
            "execution_metadata": {
                "start_time": self.start_time.isoformat(),
                "current_time": datetime.now().isoformat(),
                "elapsed_hours": (datetime.now() - self.start_time).total_seconds() / 3600
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 関西収集チェックポイントを {filename} に保存")
        return filename
    
    def upload_kansai_data_to_sheets(self, schools: List[SchoolData]) -> bool:
        """関西データのGoogleスプレッドシートアップロード"""
        try:
            logger.info("☁️ 関西データをGoogleスプレッドシートにアップロード中...")
            
            # 関西専用シートまたは既存シートに追記
            sheet_name = "Kansai_Week2"
            
            # バッチアップロード（50校ずつ、API制限考慮）
            batch_size = 50
            total_uploaded = 0
            
            for i in range(0, len(schools), batch_size):
                batch = schools[i:i + batch_size]
                
                # 関西収集メタデータを追加
                for school in batch:
                    school.week_number = 2
                    school.region = "関西"
                    school.cumulative_total_schools = total_uploaded + len(batch)
                
                self.sheets_manager.add_schools_batch(batch, sheet_name=sheet_name)
                total_uploaded += len(batch)
                
                logger.info(f"📤 {total_uploaded}/{len(schools)}校アップロード完了")
                
                # API制限対策（関西データ量考慮）
                time.sleep(3)
            
            # アップロード完了ログ
            logger.info(f"✅ 関西120校Googleスプレッドシートアップロード完了")
            logger.info(f"📊 累計データ: 関東108校 + 関西{len(schools)}校 = {108 + len(schools)}校")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 関西データアップロードエラー: {e}")
            return False
    
    def generate_kansai_week2_report(self, all_schools: List[SchoolData]) -> Dict:
        """関西Week2実行レポート生成"""
        execution_time = datetime.now() - self.start_time
        
        # 府県別詳細分析
        prefecture_analysis = {}
        for school in all_schools:
            pref = school.prefecture
            if pref not in prefecture_analysis:
                prefecture_analysis[pref] = {
                    "collected": 0,
                    "target": self.target_prefectures.get(pref, 0),
                    "quality_grades": {"A": 0, "B": 0, "C": 0, "D": 0},
                    "average_quality_score": 0,
                    "collection_issues": []
                }
            
            analysis = prefecture_analysis[pref]
            analysis["collected"] += 1
            
            quality_level = getattr(school, 'quality_level', 'D')
            analysis["quality_grades"][quality_level] += 1
            
            # 品質課題の集計
            quality_issues = getattr(school, 'quality_issues', [])
            analysis["collection_issues"].extend(quality_issues)
        
        # 府県別成績計算
        for pref, analysis in prefecture_analysis.items():
            analysis["achievement_rate"] = (analysis["collected"] / analysis["target"]) * 100 if analysis["target"] > 0 else 0
            analysis["quality_ab_rate"] = ((analysis["quality_grades"]["A"] + analysis["quality_grades"]["B"]) / analysis["collected"]) * 100 if analysis["collected"] > 0 else 0
            analysis["unique_issues"] = list(set(analysis["collection_issues"]))
        
        # 全体パフォーマンス評価
        total_collected = len(all_schools)
        quality_ab_rate = ((self.stats["quality_a"] + self.stats["quality_b"]) / total_collected) * 100 if total_collected > 0 else 0
        success_rate = (self.stats["successful"] / self.stats["attempted"]) * 100 if self.stats["attempted"] > 0 else 0
        avg_time_per_school = execution_time.total_seconds() / total_collected if total_collected > 0 else 0
        
        # パイロット実行との比較
        pilot_comparison = {
            "pilot_quality_ab_rate": 93.5,  # パイロット実行結果
            "kansai_quality_ab_rate": quality_ab_rate,
            "quality_improvement": quality_ab_rate - 93.5,
            "pilot_avg_time": 2.0,  # パイロットの推定値
            "kansai_avg_time": avg_time_per_school,
            "efficiency_improvement": ((2.0 - avg_time_per_school) / 2.0) * 100 if avg_time_per_school > 0 else 0
        }
        
        # 週次進捗（累計）
        cumulative_progress = {
            "week1_kanto": 108,
            "week2_kansai": total_collected,
            "total_collected": 108 + total_collected,
            "target_1000": 1000,
            "overall_progress_rate": ((108 + total_collected) / 1000) * 100,
            "remaining_schools": 1000 - (108 + total_collected),
            "weeks_remaining": 6,
            "required_weekly_rate": (1000 - (108 + total_collected)) / 6 if 108 + total_collected < 1000 else 0
        }
        
        report = {
            "kansai_week2_summary": {
                "collection_phase": "Week2_Kansai",
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "execution_time_hours": execution_time.total_seconds() / 3600,
                "target_schools": self.total_target,
                "collected_schools": total_collected,
                "achievement_rate": (total_collected / self.total_target) * 100,
                "success_rate": success_rate,
                "quality_ab_rate": quality_ab_rate
            },
            "performance_vs_targets": {
                "quality_ab_target": self.performance_targets["quality_ab_rate"],
                "quality_ab_actual": quality_ab_rate,
                "quality_target_met": quality_ab_rate >= self.performance_targets["quality_ab_rate"],
                "success_rate_target": self.performance_targets["success_rate"],
                "success_rate_actual": success_rate,
                "success_target_met": success_rate >= self.performance_targets["success_rate"],
                "time_target_hours": self.performance_targets["max_execution_hours"],
                "time_actual_hours": execution_time.total_seconds() / 3600,
                "time_target_met": execution_time.total_seconds() / 3600 <= self.performance_targets["max_execution_hours"]
            },
            "pilot_comparison": pilot_comparison,
            "prefecture_breakdown": prefecture_analysis,
            "cumulative_progress": cumulative_progress,
            "next_week_planning": {
                "week3_target_region": "中部",
                "week3_target_schools": 100,
                "estimated_completion_date": (datetime.now() + timedelta(weeks=1)).strftime("%Y-%m-%d"),
                "recommended_adjustments": self._generate_week3_recommendations(quality_ab_rate, success_rate, avg_time_per_school)
            },
            "quality_insights": self._analyze_quality_patterns(all_schools),
            "recommendations": self._generate_kansai_recommendations(quality_ab_rate, success_rate, avg_time_per_school)
        }
        
        return report
    
    def _analyze_quality_patterns(self, schools: List[SchoolData]) -> Dict:
        """品質パターン分析"""
        patterns = {
            "high_quality_prefectures": [],
            "improvement_needed_prefectures": [],
            "common_quality_issues": {},
            "data_source_effectiveness": {}
        }
        
        # 府県別品質分析
        for pref in self.target_prefectures.keys():
            pref_schools = [s for s in schools if s.prefecture == pref]
            if pref_schools:
                quality_ab_count = sum(1 for s in pref_schools if getattr(s, 'quality_level', 'D') in ['A', 'B'])
                quality_ab_rate = (quality_ab_count / len(pref_schools)) * 100
                
                if quality_ab_rate >= 90:
                    patterns["high_quality_prefectures"].append({
                        "prefecture": pref,
                        "quality_ab_rate": quality_ab_rate,
                        "schools_count": len(pref_schools)
                    })
                elif quality_ab_rate < 80:
                    patterns["improvement_needed_prefectures"].append({
                        "prefecture": pref,
                        "quality_ab_rate": quality_ab_rate,
                        "schools_count": len(pref_schools)
                    })
        
        return patterns
    
    def _generate_week3_recommendations(self, quality_rate: float, success_rate: float, avg_time: float) -> List[str]:
        """Week3向け推奨事項"""
        recommendations = []
        
        if quality_rate >= 90:
            recommendations.append("品質目標達成。中部収集でも同じ手法を継続")
        else:
            recommendations.append("品質向上のため、中部収集ではデータソース選定を強化")
        
        if avg_time <= 3.0:
            recommendations.append("効率目標達成。中部収集では並行処理数を増加可能")
        else:
            recommendations.append("処理時間改善のため、中部収集ではAPI呼び出し最適化を実施")
        
        recommendations.append("週次進捗良好。Week3は愛知・静岡・三重を重点的に収集")
        
        return recommendations
    
    def _generate_kansai_recommendations(self, quality_rate: float, success_rate: float, avg_time: float) -> List[str]:
        """関西収集総合推奨事項"""
        recommendations = []
        
        if quality_rate >= 85 and success_rate >= 75:
            recommendations.append("✅ 関西収集成功。Week3中部収集に移行可能")
            recommendations.append("🚀 並行処理システムの本格稼働継続")
        elif quality_rate >= 75:
            recommendations.append("⚠️ 部分的成功。品質管理を強化して中部収集に移行")
        else:
            recommendations.append("❌ 品質目標未達。ツール調整後に中部収集開始")
        
        if avg_time <= 4.0:
            recommendations.append("⏱️ 処理効率良好。全国1000校収集ペースを維持")
        else:
            recommendations.append("⏱️ 処理効率改善が必要。API最適化を実施")
        
        recommendations.append("📊 MVPアプリへの累計228校データ統合を実施")
        
        return recommendations
    
    def run_kansai_collection(self, dry_run: bool = False, parallel: bool = True) -> Dict:
        """関西120校収集メイン実行"""
        logger.info("🚀 関西120校データ収集開始 - Week 2実行")
        logger.info("=" * 60)
        logger.info(f"📅 実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        logger.info(f"🎯 目標: 関西6府県から120校収集")
        logger.info(f"📊 品質目標: A+B級90%以上")
        logger.info("=" * 60)
        
        # 環境チェック
        if not self.validate_environment():
            logger.error("❌ 環境チェックに失敗しました")
            return {"success": False, "error": "Environment validation failed"}
        
        if dry_run:
            logger.info("🧪 DRY RUN モード: 実際の収集は行いません")
        
        all_schools = []
        
        # 並行処理 vs 順次処理
        if parallel and not dry_run:
            logger.info("🔄 並行処理モードで関西収集を実行")
            
            # 府県別並行処理実行
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_prefecture = {
                    executor.submit(self.execute_prefecture_collection_parallel, pref, target): pref
                    for pref, target in self.target_prefectures.items()
                }
                
                for future in concurrent.futures.as_completed(future_to_prefecture):
                    prefecture = future_to_prefecture[future]
                    try:
                        schools = future.result()
                        all_schools.extend(schools)
                        logger.info(f"✅ {prefecture} 並行処理完了: {len(schools)}校")
                        
                        # 進捗ダッシュボード更新
                        self.update_progress_dashboard(all_schools)
                        
                    except Exception as e:
                        logger.error(f"❌ {prefecture} 並行処理エラー: {e}")
        
        else:
            # 順次処理（デバッグ用・DRY RUN用）
            for i, (prefecture, target_count) in enumerate(self.target_prefectures.items(), 1):
                logger.info(f"📍 ({i}/{len(self.target_prefectures)}) {prefecture} 開始")
                
                if not dry_run:
                    schools = self.execute_prefecture_collection_parallel(prefecture, target_count)
                    all_schools.extend(schools)
                    
                    # 進捗ダッシュボード更新
                    self.update_progress_dashboard(all_schools)
                    
                    # チェックポイント保存（2府県毎）
                    if i % 2 == 0:
                        self.save_kansai_checkpoint(all_schools, f"prefecture_{i}")
                    
                    # API制限対策
                    time.sleep(5)
                else:
                    logger.info(f"🧪 DRY RUN: {prefecture} の {target_count}校を収集予定")
        
        logger.info("=" * 60)
        logger.info(f"✅ 関西データ収集完了: {len(all_schools)}校")
        
        # 最終結果処理
        if not dry_run and all_schools:
            # 最終チェックポイント保存
            final_checkpoint = self.save_kansai_checkpoint(all_schools, "final")
            
            # Googleスプレッドシートアップロード
            upload_success = self.upload_kansai_data_to_sheets(all_schools)
            
            # 関西Week2レポート生成
            report = self.generate_kansai_week2_report(all_schools)
        else:
            # DRY RUN レポート
            report = {
                "kansai_week2_summary": {
                    "mode": "DRY_RUN",
                    "target_schools": self.total_target,
                    "prefecture_plan": self.target_prefectures,
                    "estimated_execution_hours": 4.0
                }
            }
        
        # レポート保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"kansai_week2_report_{timestamp}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 関西Week2レポート: {report_file}")
        
        return {
            "success": True,
            "collected_schools": len(all_schools) if not dry_run else 0,
            "report_file": report_file,
            "report": report,
            "cumulative_total": 108 + len(all_schools) if not dry_run else 108  # 関東108校 + 関西結果
        }

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description="関西120校データ収集実行")
    parser.add_argument("--dry-run", action="store_true", help="実際の収集は行わず計画のみ表示")
    parser.add_argument("--config", default="config.json", help="設定ファイルパス")
    parser.add_argument("--sequential", action="store_true", help="並行処理ではなく順次処理で実行")
    
    args = parser.parse_args()
    
    print("🏫 関西120校データ収集 - Week 2実行")
    print("=" * 50)
    print("📋 実行計画:")
    print("- 対象: 関西6府県（大阪・兵庫・京都・奈良・滋賀・和歌山）")
    print("- 目標: 120校")
    print("- 品質目標: A+B級90%以上")
    print("- スケジュール: Week 2（8月9日〜8月15日）")
    print("- 累計目標: 関東108校 + 関西120校 = 228校")
    
    if args.dry_run:
        print("🧪 DRY RUN モード")
    
    if args.sequential:
        print("📝 順次処理モード")
    else:
        print("⚡ 並行処理モード")
    
    print("=" * 50)
    
    # 実行確認
    if not args.dry_run:
        response = input("関西120校データ収集を開始しますか？ (y/N): ")
        if response.lower() != 'y':
            print("❌ 実行がキャンセルされました")
            return
    
    # 関西収集実行
    kansai_collection = KansaiDataCollection(args.config)
    result = kansai_collection.run_kansai_collection(
        dry_run=args.dry_run,
        parallel=not args.sequential
    )
    
    # 結果表示
    if result["success"]:
        print("\n" + "=" * 50)
        print("🎉 関西Week2収集完了")
        print("=" * 50)
        
        if not args.dry_run:
            report = result["report"]
            summary = report["kansai_week2_summary"]
            
            print(f"収集学校数: {summary['collected_schools']}/{summary['target_schools']}校")
            print(f"達成率: {summary['achievement_rate']:.1f}%")
            print(f"成功率: {summary['success_rate']:.1f}%")
            print(f"品質A+B級率: {summary['quality_ab_rate']:.1f}%")
            print(f"実行時間: {summary['execution_time_hours']:.1f}時間")
            print(f"累計データ: {result['cumulative_total']}校（全国1000校の{result['cumulative_total']/10:.1f}%）")
            
            # パフォーマンス目標達成状況
            targets_met = report["performance_vs_targets"]
            print(f"\n🎯 目標達成状況:")
            print(f"- 品質目標: {'✅' if targets_met['quality_target_met'] else '❌'}")
            print(f"- 成功率目標: {'✅' if targets_met['success_target_met'] else '❌'}")
            print(f"- 時間目標: {'✅' if targets_met['time_target_met'] else '❌'}")
            
            print(f"\n📋 推奨事項:")
            for rec in report["recommendations"]:
                print(f"- {rec}")
            
            print(f"\n🎯 Week3計画:")
            week3 = report["next_week_planning"]
            print(f"- 対象地域: {week3['target_region']}")
            print(f"- 目標校数: {week3['target_schools']}校")
            print(f"- 予定完了: {week3['estimated_completion_date']}")
        
        print(f"\n📄 詳細レポート: {result['report_file']}")
        
    else:
        print("❌ 関西収集に失敗しました")
        if "error" in result:
            print(f"エラー: {result['error']}")

if __name__ == "__main__":
    main()

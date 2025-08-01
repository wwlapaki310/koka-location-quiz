#!/usr/bin/env python3
"""
校歌データ収集 進捗監視ダッシュボード
Issue #8「全国1000件データベース構築」の進捗可視化

機能:
- 都道府県別収集進捗の可視化
- 品質レベル分布の分析
- 日次/週次進捗グラフ
- KPI達成状況モニタリング
- 遅延アラート機能

Requirements:
pip install -r requirements.txt
"""

import json
import csv
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass
import logging

from sheets_manager import GoogleSheetsManager
from quality_manager import DataQualityManager
from data_collector import SchoolData

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ProgressTarget:
    """都道府県別目標数"""
    prefecture: str
    target_count: int
    priority: int  # 1=最高優先
    region: str

@dataclass
class DailyProgress:
    """日別進捗"""
    date: str
    new_schools: int
    total_schools: int
    quality_a_count: int
    quality_b_count: int
    quality_c_count: int
    quality_d_count: int

@dataclass
class WeeklyKPI:
    """週次KPI"""
    week_start: str
    target_schools: int
    actual_schools: int
    achievement_rate: float
    quality_a_rate: float
    copyright_clear_rate: float

class ProgressDashboard:
    """進捗監視ダッシュボード"""
    
    def __init__(self):
        self.sheets_manager = GoogleSheetsManager()
        self.quality_manager = DataQualityManager()
        
        # Issue #8準拠の地域別目標設定
        self.targets = [
            # 関東（最優先）
            ProgressTarget("東京都", 60, 1, "関東"),
            ProgressTarget("神奈川県", 50, 1, "関東"),
            ProgressTarget("埼玉県", 40, 1, "関東"),
            ProgressTarget("千葉県", 35, 1, "関東"),
            ProgressTarget("茨城県", 25, 1, "関東"),
            ProgressTarget("栃木県", 20, 1, "関東"),
            ProgressTarget("群馬県", 20, 1, "関東"),
            
            # 関西（第2優先）
            ProgressTarget("大阪府", 45, 2, "関西"),
            ProgressTarget("兵庫県", 35, 2, "関西"),
            ProgressTarget("京都府", 30, 2, "関西"),
            ProgressTarget("奈良県", 25, 2, "関西"),
            ProgressTarget("滋賀県", 20, 2, "関西"),
            ProgressTarget("和歌山県", 15, 2, "関西"),
            
            # 九州・沖縄（第3優先）
            ProgressTarget("福岡県", 40, 3, "九州・沖縄"),
            ProgressTarget("熊本県", 25, 3, "九州・沖縄"),
            ProgressTarget("鹿児島県", 25, 3, "九州・沖縄"),
            ProgressTarget("長崎県", 20, 3, "九州・沖縄"),
            ProgressTarget("大分県", 20, 3, "九州・沖縄"),
            ProgressTarget("宮崎県", 18, 3, "九州・沖縄"),
            ProgressTarget("佐賀県", 15, 3, "九州・沖縄"),
            ProgressTarget("沖縄県", 12, 3, "九州・沖縄"),
            ProgressTarget("愛媛県", 15, 3, "九州・沖縄"),
            ProgressTarget("高知県", 10, 3, "九州・沖縄"),
            
            # 中部（第4優先）
            ProgressTarget("愛知県", 40, 4, "中部"),
            ProgressTarget("静岡県", 25, 4, "中部"),
            ProgressTarget("長野県", 20, 4, "中部"),
            ProgressTarget("新潟県", 20, 4, "中部"),
            ProgressTarget("岐阜県", 15, 4, "中部"),
            ProgressTarget("石川県", 12, 4, "中部"),
            ProgressTarget("富山県", 10, 4, "中部"),
            ProgressTarget("福井県", 8, 4, "中部"),
            
            # 北海道・東北（第5優先）
            ProgressTarget("北海道", 30, 5, "北海道・東北"),
            ProgressTarget("宮城県", 20, 5, "北海道・東北"),
            ProgressTarget("福島県", 15, 5, "北海道・東北"),
            ProgressTarget("青森県", 12, 5, "北海道・東北"),
            ProgressTarget("岩手県", 12, 5, "北海道・東北"),
            ProgressTarget("山形県", 8, 5, "北海道・東北"),
            ProgressTarget("秋田県", 8, 5, "北海道・東北"),
            
            # 中国・四国（第6優先）
            ProgressTarget("広島県", 20, 6, "中国・四国"),
            ProgressTarget("岡山県", 18, 6, "中国・四国"),
            ProgressTarget("山口県", 15, 6, "中国・四国"),
            ProgressTarget("香川県", 12, 6, "中国・四国"),
            ProgressTarget("徳島県", 10, 6, "中国・四国"),
            ProgressTarget("島根県", 8, 6, "中国・四国"),
            ProgressTarget("鳥取県", 7, 6, "中国・四国"),
            ProgressTarget("山梨県", 10, 6, "中国・四国")
        ]
        
        # 8週間の週次目標設定
        self.weekly_targets = [125, 125, 125, 125, 125, 125, 125, 125]  # 毎週125校ペース
        
        self.total_target = sum(target.target_count for target in self.targets)  # 1000校
        
    def load_current_data(self) -> List[SchoolData]:
        """現在収集済みデータの読み込み"""
        try:
            # Googleスプレッドシートから読み込み
            data = self.sheets_manager.export_to_csv("current_schools.csv")
            
            schools = []
            if os.path.exists("current_schools.csv"):
                df = pd.read_csv("current_schools.csv")
                for _, row in df.iterrows():
                    school = SchoolData(
                        school_name=row.get('school_name', ''),
                        prefecture=row.get('prefecture', ''),
                        city=row.get('city', ''),
                        address=row.get('address', ''),
                        latitude=row.get('latitude'),
                        longitude=row.get('longitude'),
                        full_lyrics=row.get('full_lyrics', ''),
                        data_source=row.get('data_source', ''),
                        collection_date=row.get('collection_date', ''),
                        quality_check=row.get('quality_check', 'PENDING')
                    )
                    schools.append(school)
                    
            logger.info(f"現在のデータ: {len(schools)}校")
            return schools
            
        except Exception as e:
            logger.warning(f"データ読み込みエラー: {e}")
            return []
    
    def calculate_prefecture_progress(self, schools: List[SchoolData]) -> Dict[str, Dict]:
        """都道府県別進捗計算"""
        progress = {}
        
        # 都道府県別集計
        prefecture_counts = {}
        for school in schools:
            pref = school.prefecture
            if pref not in prefecture_counts:
                prefecture_counts[pref] = 0
            prefecture_counts[pref] += 1
        
        # 目標との比較
        for target in self.targets:
            current_count = prefecture_counts.get(target.prefecture, 0)
            achievement_rate = (current_count / target.target_count) * 100
            
            progress[target.prefecture] = {
                "current": current_count,
                "target": target.target_count,
                "achievement_rate": achievement_rate,
                "region": target.region,
                "priority": target.priority,
                "status": self._get_status(achievement_rate)
            }
        
        return progress
    
    def _get_status(self, achievement_rate: float) -> str:
        """進捗状況判定"""
        if achievement_rate >= 100:
            return "完了"
        elif achievement_rate >= 80:
            return "順調"
        elif achievement_rate >= 60:
            return "要注意"
        elif achievement_rate >= 40:
            return "遅延"
        else:
            return "重大遅延"
    
    def calculate_quality_distribution(self, schools: List[SchoolData]) -> Dict[str, int]:
        """品質分布計算"""
        quality_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "PENDING": 0}
        
        for school in schools:
            quality_level, _, _ = self.quality_manager.evaluate_school_quality(school)
            quality_counts[quality_level] = quality_counts.get(quality_level, 0) + 1
        
        return quality_counts
    
    def generate_daily_progress_report(self, schools: List[SchoolData]) -> Dict:
        """日次進捗レポート生成"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 今日追加された学校数
        today_schools = [s for s in schools if s.collection_date == today]
        
        # 品質分布
        quality_dist = self.calculate_quality_distribution(schools)
        
        # 都道府県別進捗
        prefecture_progress = self.calculate_prefecture_progress(schools)
        
        report = {
            "date": today,
            "total_schools": len(schools),
            "today_added": len(today_schools),
            "target_achievement": (len(schools) / self.total_target) * 100,
            "quality_distribution": quality_dist,
            "prefecture_progress": prefecture_progress,
            "kpi_status": self._calculate_kpi_status(schools, prefecture_progress)
        }
        
        return report
    
    def _calculate_kpi_status(self, schools: List[SchoolData], prefecture_progress: Dict) -> Dict:
        """KPI達成状況計算"""
        total_schools = len(schools)
        quality_dist = self.calculate_quality_distribution(schools)
        
        # A級データ率
        quality_a_rate = (quality_dist["A"] / total_schools * 100) if total_schools > 0 else 0
        
        # 47都道府県カバー率
        covered_prefectures = len([p for p, data in prefecture_progress.items() if data["current"] > 0])
        coverage_rate = (covered_prefectures / 47) * 100
        
        # 著作権クリア率（仮想的な計算）
        copyright_clear_count = sum(1 for s in schools if "パブリックドメイン" in getattr(s, 'copyright_status', ''))
        copyright_clear_rate = (copyright_clear_count / total_schools * 100) if total_schools > 0 else 0
        
        return {
            "total_progress": (total_schools / self.total_target) * 100,
            "quality_a_rate": quality_a_rate,
            "coverage_rate": coverage_rate,
            "copyright_clear_rate": copyright_clear_rate,
            "target_kpis": {
                "total_schools": "1000件",
                "quality_a_target": "50%以上",
                "coverage_target": "100% (47都道府県)",
                "copyright_target": "80%以上"
            }
        }
    
    def create_progress_visualization(self, schools: List[SchoolData]):
        """進捗可視化グラフ作成"""
        plt.style.use('seaborn-v0_8')
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. 都道府県別進捗
        prefecture_progress = self.calculate_prefecture_progress(schools)
        prefs = list(prefecture_progress.keys())[:15]  # 上位15都道府県
        achievements = [prefecture_progress[p]["achievement_rate"] for p in prefs]
        
        bars = ax1.barh(prefs, achievements)
        ax1.set_xlabel('達成率 (%)')
        ax1.set_title('都道府県別進捗（上位15）')
        ax1.axvline(x=100, color='red', linestyle='--', alpha=0.7)
        
        # 色分け
        for i, bar in enumerate(bars):
            if achievements[i] >= 100:
                bar.set_color('green')
            elif achievements[i] >= 80:
                bar.set_color('blue')
            elif achievements[i] >= 60:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        # 2. 品質分布
        quality_dist = self.calculate_quality_distribution(schools)
        qualities = list(quality_dist.keys())
        counts = list(quality_dist.values())
        
        colors = ['green', 'blue', 'orange', 'red', 'gray']
        ax2.pie(counts, labels=qualities, colors=colors, autopct='%1.1f%%')
        ax2.set_title('品質レベル分布')
        
        # 3. 地域別進捗
        region_progress = {}
        for target in self.targets:
            region = target.region
            if region not in region_progress:
                region_progress[region] = {"current": 0, "target": 0}
            
            current = prefecture_progress[target.prefecture]["current"]
            region_progress[region]["current"] += current
            region_progress[region]["target"] += target.target_count
        
        regions = list(region_progress.keys())
        region_achievements = [
            (region_progress[r]["current"] / region_progress[r]["target"]) * 100 
            for r in regions
        ]
        
        ax3.bar(regions, region_achievements)
        ax3.set_ylabel('達成率 (%)')
        ax3.set_title('地域別進捗')
        ax3.tick_params(axis='x', rotation=45)
        ax3.axhline(y=100, color='red', linestyle='--', alpha=0.7)
        
        # 4. 週次進捗予測
        weeks = list(range(1, 9))
        current_week = min(8, (len(schools) // 125) + 1)
        actual_progress = [min(len(schools), week * 125) for week in weeks]
        target_progress = [week * 125 for week in weeks]
        
        ax4.plot(weeks, target_progress, 'r--', label='目標', linewidth=2)
        ax4.plot(weeks[:current_week], actual_progress[:current_week], 'b-', label='実績', linewidth=2)
        ax4.fill_between(weeks, target_progress, alpha=0.3, color='red')
        ax4.set_xlabel('週')
        ax4.set_ylabel('累計学校数')
        ax4.set_title('8週間進捗予測')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"progress_dashboard_{timestamp}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        logger.info(f"進捗グラフを {filename} に保存")
        
        return filename
    
    def generate_weekly_report(self, schools: List[SchoolData]) -> Dict:
        """週次レポート生成"""
        # 現在の週を計算
        current_week = min(8, len(schools) // 125 + 1)
        
        # 週次進捗
        weekly_progress = []
        for week in range(1, min(current_week + 1, 9)):
            week_schools = len([s for s in schools if s.collection_date]) # 簡易実装
            target = self.weekly_targets[week - 1] if week <= len(self.weekly_targets) else 125
            
            weekly_progress.append({
                "week": week,
                "target": target,
                "actual": min(len(schools), week * 125) - (week - 1) * 125,
                "cumulative_actual": min(len(schools), week * 125),
                "cumulative_target": week * 125
            })
        
        # アラート検出
        alerts = []
        
        # 進捗遅延チェック
        if len(schools) < current_week * 125 * 0.8:  # 80%未満
            alerts.append({
                "type": "DELAY",
                "severity": "HIGH",
                "message": f"進捗が目標の80%を下回っています (現在: {len(schools)}校, 目標: {current_week * 125}校)"
            })
        
        # 品質アラート
        quality_dist = self.calculate_quality_distribution(schools)
        a_rate = (quality_dist["A"] / len(schools) * 100) if len(schools) > 0 else 0
        if a_rate < 40:  # A級データが40%未満
            alerts.append({
                "type": "QUALITY",
                "severity": "MEDIUM", 
                "message": f"A級データが少なすぎます (現在: {a_rate:.1f}%, 目標: 50%以上)"
            })
        
        return {
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "current_week": current_week,
            "weekly_progress": weekly_progress,
            "alerts": alerts,
            "next_week_target": self.weekly_targets[current_week] if current_week < len(self.weekly_targets) else 125
        }
    
    def save_dashboard_report(self, schools: List[SchoolData], output_file: str = None):
        """ダッシュボードレポート保存"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"dashboard_report_{timestamp}.json"
        
        # 各種レポート生成
        daily_report = self.generate_daily_progress_report(schools)
        weekly_report = self.generate_weekly_report(schools)
        
        # 統合レポート
        dashboard_report = {
            "generated_at": datetime.now().isoformat(),
            "total_schools": len(schools),
            "target_schools": self.total_target,
            "overall_progress": (len(schools) / self.total_target) * 100,
            "daily_report": daily_report,
            "weekly_report": weekly_report,
            "data_summary": {
                "total_prefectures": len(set(s.prefecture for s in schools)),
                "quality_distribution": self.calculate_quality_distribution(schools),
                "prefecture_progress": self.calculate_prefecture_progress(schools)
            }
        }
        
        # 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dashboard_report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"ダッシュボードレポートを {output_file} に保存")
        
        # 可視化も生成
        viz_file = self.create_progress_visualization(schools)
        
        return {
            "report_file": output_file,
            "visualization_file": viz_file,
            "summary": dashboard_report["data_summary"]
        }

def main():
    """メイン実行"""
    print("📊 校歌データ収集 進捗監視ダッシュボード")
    print("=" * 50)
    
    dashboard = ProgressDashboard()
    
    # 現在のデータ読み込み
    print("📥 現在のデータを読み込み中...")
    schools = dashboard.load_current_data()
    
    if not schools:
        print("⚠️  データが見つかりません。サンプルデータで実行します。")
        # サンプルデータ生成（テスト用）
        from datetime import datetime, timedelta
        schools = []
        for i in range(50):  # 50校のサンプル
            school = SchoolData(
                school_name=f"サンプル中学校{i+1}",
                prefecture=["東京都", "神奈川県", "大阪府", "愛知県", "福岡県"][i % 5],
                city=f"サンプル市{i+1}",
                address=f"サンプル住所{i+1}",
                latitude=35.0 + (i * 0.1),
                longitude=135.0 + (i * 0.1),
                full_lyrics=f"サンプル校歌{i+1}",
                data_source="サンプル",
                collection_date=(datetime.now() - timedelta(days=i%7)).strftime("%Y-%m-%d"),
                quality_check=["A", "B", "C", "D"][i % 4]
            )
            schools.append(school)
    
    print(f"✅ {len(schools)}校のデータを読み込みました")
    
    # ダッシュボードレポート生成
    print("📊 ダッシュボードレポートを生成中...")
    result = dashboard.save_dashboard_report(schools)
    
    # 結果表示
    print("\n" + "=" * 50)
    print("📋 進捗サマリー")
    print("=" * 50)
    
    total_progress = (len(schools) / dashboard.total_target) * 100
    print(f"全体進捗: {len(schools)}/{dashboard.total_target}校 ({total_progress:.1f}%)")
    
    # 品質分布
    quality_dist = result["summary"]["quality_distribution"]
    print(f"品質分布: A級{quality_dist.get('A', 0)}校, B級{quality_dist.get('B', 0)}校, C級{quality_dist.get('C', 0)}校, D級{quality_dist.get('D', 0)}校")
    
    # 都道府県数
    print(f"カバー都道府県: {result['summary']['total_prefectures']}/47")
    
    print(f"\n📄 詳細レポート: {result['report_file']}")
    print(f"📈 可視化グラフ: {result['visualization_file']}")
    
    print("\n🎯 次のアクション:")
    if total_progress < 50:
        print("- 自動収集ツールの本格稼働")
        print("- 優先都道府県（関東・関西）への集中")
    elif total_progress < 80:
        print("- 手動収集体制の強化")
        print("- 品質A級データの向上")
    else:
        print("- 最終品質チェック")
        print("- データ統合・整理")

if __name__ == "__main__":
    main()

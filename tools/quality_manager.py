#!/usr/bin/env python3
"""
校歌データ品質管理・検証ツール
- 収集データの品質レベル判定
- 重複検出・排除
- データ妥当性チェック
- 著作権状況の判定支援

Requirements:
pip install -r requirements.txt
"""

import re
import csv
import json
import logging
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd
from collections import Counter

from data_collector import SchoolData

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class QualityCheck:
    """品質チェック結果"""
    school_id: str
    school_name: str
    check_type: str
    result: str  # PASS, FAIL, WARNING
    score: float  # 0.0-1.0
    comment: str
    checked_at: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class DataQualityManager:
    """データ品質管理クラス"""
    
    def __init__(self):
        self.quality_thresholds = {
            'A': 0.9,  # 90%以上
            'B': 0.7,  # 70%以上
            'C': 0.5   # 50%以上
        }
        
        # 著作権フリー作詞者・作曲者（1953年以前没）のサンプル
        self.public_domain_creators = {
            '文部省', '文部省唱歌', '作者不詳', '不詳',
            '伊沢修二', '上真行', '奥好義', '里見義'
        }
    
    def evaluate_school_quality(self, school: SchoolData) -> Tuple[str, float, List[QualityCheck]]:
        """
        学校データの品質評価
        Returns:
            (品質レベル, スコア, チェック結果リスト)
        """
        checks = []
        total_score = 0.0
        max_possible_score = 0.0
        
        # 必須項目チェック
        required_check = self._check_required_fields(school)
        checks.append(required_check)
        total_score += required_check.score * 3  # 重要度3倍
        max_possible_score += 3.0
        
        # 座標妥当性チェック
        coords_check = self._check_coordinates(school)
        checks.append(coords_check)
        total_score += coords_check.score * 2  # 重要度2倍
        max_possible_score += 2.0
        
        # 歌詞品質チェック
        lyrics_check = self._check_lyrics_quality(school)
        checks.append(lyrics_check)
        total_score += lyrics_check.score * 2
        max_possible_score += 2.0
        
        # ヒント品質チェック
        hints_check = self._check_hints_quality(school)
        checks.append(hints_check)
        total_score += hints_check.score
        max_possible_score += 1.0
        
        # 著作権状況チェック
        copyright_check = self._check_copyright_status(school)
        checks.append(copyright_check)
        total_score += copyright_check.score
        max_possible_score += 1.0
        
        # 最終スコア計算
        final_score = total_score / max_possible_score if max_possible_score > 0 else 0.0
        
        # 品質レベル判定
        if final_score >= self.quality_thresholds['A']:
            quality_level = 'A'
        elif final_score >= self.quality_thresholds['B']:
            quality_level = 'B'
        elif final_score >= self.quality_thresholds['C']:
            quality_level = 'C'
        else:
            quality_level = 'D'
        
        return quality_level, final_score, checks
    
    def _check_required_fields(self, school: SchoolData) -> QualityCheck:
        """必須項目チェック"""
        required_fields = [
            ('school_name', '学校名'),
            ('prefecture', '都道府県'),
            ('city', '市区町村'),
            ('address', '住所'),
            ('full_lyrics', '校歌全文')
        ]
        
        missing_fields = []
        for field, display_name in required_fields:
            value = getattr(school, field, None)
            if not value or (isinstance(value, str) and not value.strip()):
                missing_fields.append(display_name)
        
        score = (len(required_fields) - len(missing_fields)) / len(required_fields)
        
        if not missing_fields:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="必須項目",
                result="PASS",
                score=score,
                comment="すべての必須項目が入力されています"
            )
        else:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="必須項目",
                result="FAIL" if len(missing_fields) > 2 else "WARNING",
                score=score,
                comment=f"不足項目: {', '.join(missing_fields)}"
            )
    
    def _check_coordinates(self, school: SchoolData) -> QualityCheck:
        """座標妥当性チェック"""
        lat = school.latitude
        lng = school.longitude
        
        # 座標が存在するか
        if lat is None or lng is None:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="座標妥当性",
                result="FAIL",
                score=0.0,
                comment="座標が設定されていません"
            )
        
        # 日本の範囲内か（概算）
        if not (24.0 <= lat <= 46.0 and 123.0 <= lng <= 146.0):
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="座標妥当性",
                result="FAIL",
                score=0.2,
                comment=f"座標が日本の範囲外です ({lat}, {lng})"
            )
        
        # 都道府県と座標の整合性チェック（簡易版）
        prefecture_ranges = {
            '北海道': (42.0, 46.0, 139.0, 146.0),
            '東京都': (35.5, 36.0, 139.0, 140.0),
            '大阪府': (34.2, 35.0, 135.0, 136.0),
            '沖縄県': (24.0, 27.0, 123.0, 132.0)
        }
        
        pref_range = prefecture_ranges.get(school.prefecture)
        if pref_range:
            lat_min, lat_max, lng_min, lng_max = pref_range
            if not (lat_min <= lat <= lat_max and lng_min <= lng <= lng_max):
                return QualityCheck(
                    school_id=str(school.school_name),
                    school_name=school.school_name,
                    check_type="座標妥当性",
                    result="WARNING",
                    score=0.7,
                    comment=f"座標と都道府県の位置が一致しない可能性があります"
                )
        
        return QualityCheck(
            school_id=str(school.school_name),
            school_name=school.school_name,
            check_type="座標妥当性",
            result="PASS",
            score=1.0,
            comment="座標は適切な範囲内です"
        )
    
    def _check_lyrics_quality(self, school: SchoolData) -> QualityCheck:
        """歌詞品質チェック"""
        lyrics = school.full_lyrics
        
        if not lyrics or not lyrics.strip():
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="歌詞品質",
                result="FAIL",
                score=0.0,
                comment="歌詞が入力されていません"
            )
        
        # 文字数チェック
        if len(lyrics) < 50:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="歌詞品質",
                result="WARNING",
                score=0.5,
                comment=f"歌詞が短すぎます ({len(lyrics)}文字)"
            )
        
        # 校歌らしいキーワードの存在チェック
        school_song_keywords = [
            '学び', '青春', '希望', '未来', '夢', '友', '我ら', 'われら',
            '輝く', '風', '空', '海', '山', '川', '丘', '緑', '光'
        ]
        
        keyword_count = sum(1 for keyword in school_song_keywords if keyword in lyrics)
        keyword_score = min(keyword_count / 3, 1.0)  # 3個以上で満点
        
        # マスク済み歌詞の品質チェック
        masked_lyrics = school.masked_lyrics
        has_masked = masked_lyrics and '〇〇' in masked_lyrics
        mask_score = 1.0 if has_masked else 0.5
        
        total_score = (keyword_score + mask_score) / 2
        
        comments = []
        if keyword_count < 2:
            comments.append("校歌らしいキーワードが少ない")
        if not has_masked:
            comments.append("マスク済み歌詞が適切でない")
        
        result = "PASS" if total_score >= 0.8 else "WARNING" if total_score >= 0.5 else "FAIL"
        comment = "; ".join(comments) if comments else "歌詞品質は良好です"
        
        return QualityCheck(
            school_id=str(school.school_name),
            school_name=school.school_name,
            check_type="歌詞品質",
            result=result,
            score=total_score,
            comment=comment
        )
    
    def _check_hints_quality(self, school: SchoolData) -> QualityCheck:
        """ヒント品質チェック"""
        hints = school.hints
        
        if not hints:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="ヒント品質",
                result="FAIL",
                score=0.0,
                comment="ヒント情報が設定されていません"
            )
        
        hint_scores = []
        comments = []
        
        # 都道府県ヒント
        if hints.prefecture and len(hints.prefecture) > 5:
            hint_scores.append(1.0)
        else:
            hint_scores.append(0.0)
            comments.append("都道府県ヒントが不十分")
        
        # 地域ヒント
        if hints.region and len(hints.region) > 5:
            hint_scores.append(1.0)
        else:
            hint_scores.append(0.0)
            comments.append("地域ヒントが不十分")
        
        # 地理的特徴ヒント
        if hints.landmark and len(hints.landmark) > 5:
            hint_scores.append(1.0)
        else:
            hint_scores.append(0.0)
            comments.append("特徴ヒントが不十分")
        
        total_score = sum(hint_scores) / len(hint_scores)
        result = "PASS" if total_score >= 0.8 else "WARNING" if total_score >= 0.5 else "FAIL"
        comment = "; ".join(comments) if comments else "ヒント品質は良好です"
        
        return QualityCheck(
            school_id=str(school.school_name),
            school_name=school.school_name,
            check_type="ヒント品質",
            result=result,
            score=total_score,
            comment=comment
        )
    
    def _check_copyright_status(self, school: SchoolData) -> QualityCheck:
        """著作権状況チェック"""
        composer = school.composer or ""
        lyricist = school.lyricist or ""
        composed_year = school.composed_year
        
        # パブリックドメイン判定
        is_public_domain = False
        pd_reason = []
        
        # 作者不詳・文部省等
        if (composer in self.public_domain_creators or 
            lyricist in self.public_domain_creators):
            is_public_domain = True
            pd_reason.append("作者がパブリックドメイン")
        
        # 1953年以前制定（概算）
        if composed_year and composed_year <= 1953:
            is_public_domain = True
            pd_reason.append(f"制定年が古い ({composed_year}年)")
        
        if is_public_domain:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="著作権状況",
                result="PASS",
                score=1.0,
                comment=f"パブリックドメインの可能性が高い: {', '.join(pd_reason)}"
            )
        elif not composer and not lyricist:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="著作権状況",
                result="WARNING",
                score=0.5,
                comment="作詞者・作曲者情報が不明"
            )
        else:
            return QualityCheck(
                school_id=str(school.school_name),
                school_name=school.school_name,
                check_type="著作権状況",
                result="WARNING",
                score=0.3,
                comment="著作権調査が必要"
            )
    
    def detect_duplicates(self, schools: List[SchoolData]) -> List[Tuple[SchoolData, SchoolData, str]]:
        """重複検出"""
        duplicates = []
        
        # 学校名での重複チェック
        name_groups = {}
        for school in schools:
            name_key = self._normalize_school_name(school.school_name)
            if name_key not in name_groups:
                name_groups[name_key] = []
            name_groups[name_key].append(school)
        
        for name_key, group in name_groups.items():
            if len(group) > 1:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        duplicates.append((group[i], group[j], "学校名重複"))
        
        # 座標での重複チェック（100m以内）
        for i in range(len(schools)):
            for j in range(i + 1, len(schools)):
                school1, school2 = schools[i], schools[j]
                if (school1.latitude and school2.latitude and
                    school1.longitude and school2.longitude):
                    
                    distance = self._calculate_distance(
                        school1.latitude, school1.longitude,
                        school2.latitude, school2.longitude
                    )
                    
                    if distance < 0.1:  # 100m以内
                        duplicates.append((school1, school2, f"座標近接 ({distance:.0f}m)"))
        
        return duplicates
    
    def _normalize_school_name(self, name: str) -> str:
        """学校名正規化"""
        # 設置者表記を除去
        normalized = re.sub(r'^[^立]*立', '', name)
        # 学校種別を除去
        normalized = re.sub(r'(小学校|中学校|高等学校|高校)$', '', normalized)
        return normalized.strip()
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """2点間の距離計算（km）"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # 地球の半径（km）
        
        lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def generate_quality_report(self, schools: List[SchoolData]) -> Dict:
        """品質レポート生成"""
        if not schools:
            return {"error": "データが空です"}
        
        report = {
            "summary": {
                "total_schools": len(schools),
                "generated_at": datetime.now().isoformat()
            },
            "quality_distribution": {"A": 0, "B": 0, "C": 0, "D": 0},
            "average_score": 0.0,
            "check_results": [],
            "duplicates": [],
            "recommendations": []
        }
        
        total_score = 0.0
        all_checks = []
        
        # 各学校の品質評価
        for school in schools:
            quality_level, score, checks = self.evaluate_school_quality(school)
            
            report["quality_distribution"][quality_level] += 1
            total_score += score
            all_checks.extend(checks)
        
        report["average_score"] = total_score / len(schools)
        report["check_results"] = [asdict(check) for check in all_checks]
        
        # 重複検出
        duplicates = self.detect_duplicates(schools)
        report["duplicates"] = [
            {
                "school1": dup[0].school_name,
                "school2": dup[1].school_name,
                "reason": dup[2]
            }
            for dup in duplicates
        ]
        
        # 改善提案
        failed_checks = [check for check in all_checks if check.result == "FAIL"]
        warning_checks = [check for check in all_checks if check.result == "WARNING"]
        
        if failed_checks:
            report["recommendations"].append(f"重大な問題: {len(failed_checks)}件の修正が必要")
        if warning_checks:
            report["recommendations"].append(f"軽微な問題: {len(warning_checks)}件の改善を推奨")
        if duplicates:
            report["recommendations"].append(f"重複データ: {len(duplicates)}組の確認が必要")
        
        return report
    
    def save_quality_report(self, schools: List[SchoolData], output_file: str):
        """品質レポートをファイル保存"""
        report = self.generate_quality_report(schools)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"品質レポートを {output_file} に保存しました")
        return report

def main():
    """メイン実行"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python quality_manager.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # CSVファイル読み込み
    schools = []
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
        for _, row in df.iterrows():
            school = SchoolData(
                school_name=row.get('school_name', ''),
                school_type=row.get('school_type', '中学校'),
                establishment_type=row.get('establishment_type', '公立'),
                prefecture=row.get('prefecture', ''),
                city=row.get('city', ''),
                address=row.get('address', ''),
                latitude=row.get('latitude'),
                longitude=row.get('longitude'),
                full_lyrics=row.get('full_lyrics', ''),
                masked_lyrics=row.get('masked_lyrics', ''),
                composer=row.get('composer', ''),
                lyricist=row.get('lyricist', ''),
                composed_year=row.get('composed_year'),
                hint_prefecture=row.get('hint_prefecture', ''),
                hint_region=row.get('hint_region', ''),
                hint_landmark=row.get('hint_landmark', '')
            )
            schools.append(school)
        
        logger.info(f"{len(schools)}校のデータを読み込みました")
        
    except Exception as e:
        logger.error(f"CSVファイル読み込みエラー: {e}")
        sys.exit(1)
    
    # 品質管理実行
    quality_manager = DataQualityManager()
    
    # レポート生成
    report = quality_manager.generate_quality_report(schools)
    
    # 結果表示
    print("\n" + "="*60)
    print("📊 データ品質レポート")
    print("="*60)
    print(f"総学校数: {report['summary']['total_schools']}")
    print(f"平均品質スコア: {report['average_score']:.2f}")
    print("\n品質分布:")
    for level, count in report['quality_distribution'].items():
        percentage = count / report['summary']['total_schools'] * 100
        print(f"  {level}級: {count}校 ({percentage:.1f}%)")
    
    if report['duplicates']:
        print(f"\n⚠️  重複候補: {len(report['duplicates'])}組")
        for dup in report['duplicates'][:5]:  # 最初の5組のみ表示
            print(f"  - {dup['school1']} vs {dup['school2']} ({dup['reason']})")
    
    if report['recommendations']:
        print("\n💡 改善提案:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    # ファイル保存
    quality_manager.save_quality_report(schools, f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    print("\n✅ 品質レポートを保存しました")

if __name__ == "__main__":
    main()

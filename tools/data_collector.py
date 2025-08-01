#!/usr/bin/env python3
"""
校歌データ収集ツール
- 学校公式サイトからの校歌情報自動収集
- Google Geocoding APIによる座標取得
- Googleスプレッドシートへの自動登録

Requirements:
pip install requests beautifulsoup4 google-api-python-client google-auth-httplib2 google-auth-oauthlib
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import csv

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SchoolData:
    """学校データ構造"""
    school_name: str
    school_type: str  # 小学校/中学校/高等学校
    establishment_type: str  # 国立/公立/私立
    prefecture: str
    city: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    song_title: Optional[str] = None
    full_lyrics: Optional[str] = None
    masked_lyrics: Optional[str] = None
    composer: Optional[str] = None
    lyricist: Optional[str] = None
    composed_year: Optional[int] = None
    difficulty: str = "medium"
    hint_prefecture: Optional[str] = None
    hint_region: Optional[str] = None
    hint_landmark: Optional[str] = None
    established_year: Optional[int] = None
    notes: Optional[str] = None
    data_source: Optional[str] = None
    collection_date: str = datetime.now().strftime("%Y-%m-%d")
    quality_check: str = "PENDING"
    copyright_status: str = "UNKNOWN"

class SchoolDataCollector:
    """校歌データ収集メインクラス"""
    
    def __init__(self, config_file: str = "config.json"):
        """
        初期化
        Args:
            config_file: 設定ファイルパス（Google API Key等）
        """
        self.config = self._load_config(config_file)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def _load_config(self, config_file: str) -> Dict:
        """設定ファイル読み込み"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"設定ファイル {config_file} が見つかりません。サンプル設定を作成します。")
            sample_config = {
                "google_api_key": "YOUR_GOOGLE_API_KEY_HERE",
                "google_search_engine_id": "YOUR_CUSTOM_SEARCH_ENGINE_ID",
                "delay_seconds": 1,
                "max_schools_per_prefecture": 50
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(sample_config, f, indent=2, ensure_ascii=False)
            return sample_config
    
    def search_schools_by_prefecture(self, prefecture: str, school_type: str = "中学校") -> List[str]:
        """
        都道府県別学校検索
        Args:
            prefecture: 都道府県名
            school_type: 学校種別
        Returns:
            学校サイトURLリスト
        """
        search_query = f"{prefecture} {school_type} site:*.jp 校歌"
        
        try:
            # Google Custom Search API使用
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.config.get('google_api_key'),
                'cx': self.config.get('google_search_engine_id'),
                'q': search_query,
                'num': 10
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                results = response.json()
                urls = [item['link'] for item in results.get('items', [])]
                logger.info(f"{prefecture}の{school_type}を{len(urls)}件発見")
                return urls
            else:
                logger.error(f"検索APIエラー: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"学校検索エラー: {e}")
            return []
    
    def extract_school_info(self, url: str) -> Optional[SchoolData]:
        """
        学校サイトから情報抽出
        Args:
            url: 学校サイトURL
        Returns:
            SchoolData or None
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 基本情報抽出
            school_data = SchoolData(
                school_name=self._extract_school_name(soup, url),
                school_type="中学校",  # 検索条件から推定
                establishment_type="公立",  # デフォルト、後で判定
                prefecture="",
                city="",
                address="",
                data_source=url
            )
            
            # 校歌情報抽出
            lyrics_info = self._extract_lyrics(soup)
            if lyrics_info:
                school_data.full_lyrics = lyrics_info.get('lyrics')
                school_data.song_title = lyrics_info.get('title', '校歌')
                school_data.composer = lyrics_info.get('composer')
                school_data.lyricist = lyrics_info.get('lyricist')
            
            # 住所情報抽出
            address_info = self._extract_address(soup)
            if address_info:
                school_data.address = address_info.get('address', '')
                school_data.prefecture = address_info.get('prefecture', '')
                school_data.city = address_info.get('city', '')
            
            # 座標取得
            if school_data.address:
                coords = self._get_coordinates(school_data.address)
                if coords:
                    school_data.latitude, school_data.longitude = coords
            
            # マスク済み歌詞生成
            if school_data.full_lyrics:
                school_data.masked_lyrics = self._create_masked_lyrics(
                    school_data.full_lyrics, school_data.school_name
                )
            
            # ヒント生成
            school_data.hint_prefecture = self._generate_prefecture_hint(school_data.prefecture)
            school_data.hint_region = self._generate_region_hint(school_data.prefecture, school_data.city)
            school_data.hint_landmark = self._generate_landmark_hint(school_data.address)
            
            logger.info(f"学校情報抽出完了: {school_data.school_name}")
            return school_data
            
        except Exception as e:
            logger.error(f"情報抽出エラー ({url}): {e}")
            return None
    
    def _extract_school_name(self, soup: BeautifulSoup, url: str) -> str:
        """学校名抽出"""
        # title タグから抽出
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()
            # 「○○中学校」のパターンを抽出
            match = re.search(r'([^｜]*?(?:小学校|中学校|高等学校|高校))', title_text)
            if match:
                return match.group(1).strip()
        
        # h1 タグから抽出
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.get_text().strip()
            match = re.search(r'([^｜]*?(?:小学校|中学校|高等学校|高校))', h1_text)
            if match:
                return match.group(1).strip()
        
        # URLから学校名を推測
        match = re.search(r'/([^/]*(?:小学校|中学校|高等学校|高校|school))', url)
        if match:
            return match.group(1)
        
        return "不明"
    
    def _extract_lyrics(self, soup: BeautifulSoup) -> Optional[Dict]:
        """校歌歌詞抽出"""
        lyrics_keywords = ["校歌", "こうか", "school song", "歌詞"]
        
        for keyword in lyrics_keywords:
            # キーワードを含むテキストブロックを検索
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            
            for element in elements:
                parent = element.parent
                if parent:
                    # 周辺のテキストから歌詞を抽出
                    lyrics_text = self._extract_lyrics_from_element(parent)
                    if lyrics_text and len(lyrics_text) > 50:  # 十分な長さがある場合
                        return {
                            'lyrics': lyrics_text,
                            'title': '校歌',
                            'composer': self._extract_composer(parent),
                            'lyricist': self._extract_lyricist(parent)
                        }
        
        return None
    
    def _extract_lyrics_from_element(self, element) -> Optional[str]:
        """要素から歌詞テキスト抽出"""
        try:
            # 要素とその兄弟要素からテキストを収集
            text_parts = []
            
            # 現在の要素
            if element.get_text():
                text_parts.append(element.get_text().strip())
            
            # 次の兄弟要素たち
            for sibling in element.find_next_siblings():
                sibling_text = sibling.get_text().strip()
                if sibling_text and len(sibling_text) > 10:
                    text_parts.append(sibling_text)
                if len(text_parts) > 5:  # 適当な長さで切る
                    break
            
            full_text = '\n'.join(text_parts)
            
            # 歌詞らしいテキストかチェック
            if self._is_lyrics_text(full_text):
                return full_text
            
            return None
            
        except Exception as e:
            logger.debug(f"歌詞抽出エラー: {e}")
            return None
    
    def _is_lyrics_text(self, text: str) -> bool:
        """テキストが歌詞かどうか判定"""
        # 歌詞に特徴的なキーワード
        lyrics_indicators = [
            "青春", "学び", "希望", "未来", "夢", "友", "我ら",
            "輝く", "風", "空", "海", "山", "川", "丘"
        ]
        
        # 行数チェック（歌詞は複数行）
        lines = text.split('\n')
        if len(lines) < 3:
            return False
        
        # キーワードの含有率
        keyword_count = sum(1 for keyword in lyrics_indicators if keyword in text)
        return keyword_count >= 2
    
    def _extract_composer(self, element) -> Optional[str]:
        """作曲者抽出"""
        text = element.get_text()
        match = re.search(r'作曲[：:\s]*([^\s\n]+)', text)
        return match.group(1) if match else None
    
    def _extract_lyricist(self, element) -> Optional[str]:
        """作詞者抽出"""
        text = element.get_text()
        match = re.search(r'作詞[：:\s]*([^\s\n]+)', text)
        return match.group(1) if match else None
    
    def _extract_address(self, soup: BeautifulSoup) -> Optional[Dict]:
        """住所情報抽出"""
        address_patterns = [
            r'〒\d{3}-\d{4}\s*(.+)',
            r'住所[：:\s]*(.+)',
            r'所在地[：:\s]*(.+)',
        ]
        
        text = soup.get_text()
        for pattern in address_patterns:
            match = re.search(pattern, text)
            if match:
                address = match.group(1).strip()
                return self._parse_address(address)
        
        return None
    
    def _parse_address(self, address: str) -> Dict:
        """住所文字列を都道府県・市区町村に分解"""
        prefecture_match = re.match(r'([^都道府県]*[都道府県])', address)
        prefecture = prefecture_match.group(1) if prefecture_match else ""
        
        city_match = re.search(r'[都道府県]([^区市町村]*[区市町村])', address)
        city = city_match.group(1) if city_match else ""
        
        return {
            'address': address,
            'prefecture': prefecture,
            'city': city
        }
    
    def _get_coordinates(self, address: str) -> Optional[Tuple[float, float]]:
        """Google Geocoding APIで座標取得"""
        if not self.config.get('google_api_key'):
            return None
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'address': address,
                'key': self.config['google_api_key']
            }
            
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['results']:
                    location = data['results'][0]['geometry']['location']
                    return location['lat'], location['lng']
            
        except Exception as e:
            logger.error(f"座標取得エラー: {e}")
        
        return None
    
    def _create_masked_lyrics(self, lyrics: str, school_name: str) -> str:
        """マスク済み歌詞生成"""
        masked = lyrics
        
        # 学校名をマスク
        school_name_clean = re.sub(r'[都道府県市区町村立]', '', school_name)
        school_name_clean = re.sub(r'[小中高等学校]', '', school_name_clean)
        if school_name_clean:
            masked = masked.replace(school_name_clean, "〇〇")
        
        # 地名のマスク（簡易版）
        place_patterns = [
            r'[東西南北]京',
            r'[都道府県][名]',
            r'[川山海丘][名]'
        ]
        
        for pattern in place_patterns:
            masked = re.sub(pattern, "〇〇", masked)
        
        return masked
    
    def _generate_prefecture_hint(self, prefecture: str) -> str:
        """都道府県ヒント生成"""
        region_map = {
            '北海道': '日本最北の大地',
            '青森県': '本州最北端、りんごの名産地',
            '岩手県': '広大な面積を持つ東北の県',
            '宮城県': '仙台がある東北の中心県',
            '秋田県': '米どころで有名な日本海側の県',
            '山形県': 'さくらんぼの生産量日本一',
            '福島県': '会津、中通り、浜通りの3地域',
            '茨城県': '関東地方北部、納豆で有名',
            '栃木県': '日光東照宮がある関東の県',
            '群馬県': '草津温泉で有名な内陸県',
            '埼玉県': '東京の北に隣接する関東の県',
            '千葉県': '東京湾に面した関東の県',
            '東京都': '日本の首都',
            '神奈川県': '横浜・川崎がある関東の県',
            # 他の都道府県も追加...
        }
        
        return region_map.get(prefecture, f"{prefecture}地方")
    
    def _generate_region_hint(self, prefecture: str, city: str) -> str:
        """地域ヒント生成"""
        return f"{prefecture}の{city}地域"
    
    def _generate_landmark_hint(self, address: str) -> str:
        """地理的特徴ヒント生成"""
        landmarks = []
        if '海' in address or '浜' in address:
            landmarks.append('海に近い')
        if '山' in address or '丘' in address:
            landmarks.append('高台にある')
        if '川' in address:
            landmarks.append('川沿いの')
        if '駅' in address:
            landmarks.append('駅に近い')
        
        return '、'.join(landmarks) + '地域' if landmarks else '住宅地'
    
    def save_to_csv(self, schools: List[SchoolData], filename: str = "school_data.csv"):
        """CSVファイルに保存"""
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'school_name', 'school_type', 'establishment_type',
                'prefecture', 'city', 'address', 'latitude', 'longitude',
                'song_title', 'full_lyrics', 'masked_lyrics',
                'composer', 'lyricist', 'composed_year', 'difficulty',
                'hint_prefecture', 'hint_region', 'hint_landmark',
                'established_year', 'notes', 'data_source',
                'collection_date', 'quality_check', 'copyright_status'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for school in schools:
                writer.writerow({
                    field: getattr(school, field) for field in fieldnames
                })
        
        logger.info(f"データを {filename} に保存しました（{len(schools)}件）")

def main():
    """メイン実行"""
    collector = SchoolDataCollector()
    
    # 都道府県別収集（関東優先）
    prefectures = ["東京都", "神奈川県", "埼玉県", "千葉県", "茨城県", "栃木県", "群馬県"]
    
    all_schools = []
    
    for prefecture in prefectures:
        logger.info(f"=== {prefecture} の中学校を収集開始 ===")
        
        # 学校検索
        school_urls = collector.search_schools_by_prefecture(prefecture, "中学校")
        
        for url in school_urls[:10]:  # 1県あたり最大10校
            logger.info(f"収集中: {url}")
            school_data = collector.extract_school_info(url)
            
            if school_data:
                all_schools.append(school_data)
                logger.info(f"成功: {school_data.school_name}")
            
            # レート制限
            time.sleep(collector.config.get('delay_seconds', 1))
        
        logger.info(f"{prefecture} 完了: {len([s for s in all_schools if s.prefecture == prefecture])}校")
    
    # 結果保存
    if all_schools:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        collector.save_to_csv(all_schools, f"school_data_{timestamp}.csv")
        logger.info(f"合計 {len(all_schools)} 校のデータを収集しました")
    else:
        logger.warning("データが収集できませんでした")

if __name__ == "__main__":
    main()

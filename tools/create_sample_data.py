#!/usr/bin/env python3
"""
スプレッドシート追加用サンプルデータ生成ツール
"""

import json
from datetime import datetime

def create_sample_data():
    """関西地方のサンプルデータを作成"""
    sample_schools = [
        {
            "school_name": "大阪市立天王寺中学校",
            "prefecture": "大阪府",
            "city": "大阪市天王寺区",
            "address": "大阪府大阪市天王寺区筆ヶ崎町2-5",
            "latitude": 34.6638,
            "longitude": 135.5191,
            "song_title": "校歌",
            "full_lyrics": "天王寺の丘に立ちて 学びの園を仰ぎ見れば 希望の光さしそいて 我等青春歌いゆく",
            "masked_lyrics": "〇〇〇の丘に立ちて 学びの園を仰ぎ見れば",
            "composer": "田中作曲",
            "lyricist": "佐藤作詞",
            "difficulty": "medium",
            "quality_level": "A",
            "quality_score": 0.95,
            "data_source": "学校公式サイト",
            "collection_date": datetime.now().strftime('%Y-%m-%d'),
            "hints": {
                "prefecture": "関西地方の中心都市",
                "region": "大阪市内の文教地区",
                "landmark": "天王寺駅近く"
            },
            "school_type": "中学校",
            "establishment_type": "公立",
            "established_year": 1947,
            "composed_year": 1950,
            "notes": "大阪市内の伝統校",
            "copyright_status": "パブリックドメイン"
        },
        {
            "school_name": "京都府立洛北高等学校",
            "prefecture": "京都府",
            "city": "京都市左京区",
            "address": "京都府京都市左京区下鴨梅ノ木町59",
            "latitude": 35.0532,
            "longitude": 135.7664,
            "song_title": "校歌",
            "full_lyrics": "比叡の山を仰ぎ見て 鴨川清き流れのほとり 文化の光ここに集い 我等が母校洛北校",
            "masked_lyrics": "〇〇の山を仰ぎ見て 〇〇清き流れのほとり",
            "composer": "山田作曲",
            "lyricist": "田中作詞",
            "difficulty": "medium",
            "quality_level": "A",
            "quality_score": 0.92,
            "data_source": "学校公式サイト",
            "collection_date": datetime.now().strftime('%Y-%m-%d'),
            "hints": {
                "prefecture": "古都として有名",
                "region": "京都市北部の文教地区",
                "landmark": "比叡山の麓"
            },
            "school_type": "高等学校",
            "establishment_type": "公立",
            "established_year": 1902,
            "composed_year": 1955,
            "notes": "京都府内有数の進学校",
            "copyright_status": "パブリックドメイン"
        },
        {
            "school_name": "兵庫県立神戸高等学校",
            "prefecture": "兵庫県",
            "city": "神戸市灘区",
            "address": "兵庫県神戸市灘区城の下通1-5-1",
            "latitude": 34.7267,
            "longitude": 135.2425,
            "song_title": "校歌",
            "full_lyrics": "六甲颪に響く声 港神戸の学び舎に 真理を求め進みゆく 我等神戸高校生",
            "masked_lyrics": "〇〇颪に響く声 港〇〇の学び舎に",
            "composer": "神戸作曲",
            "lyricist": "港作詞",
            "difficulty": "easy",
            "quality_level": "B",
            "quality_score": 0.88,
            "data_source": "学校公式サイト",
            "collection_date": datetime.now().strftime('%Y-%m-%d'),
            "hints": {
                "prefecture": "本州と四国を結ぶ地域",
                "region": "国際港湾都市",
                "landmark": "六甲山系の麓"
            },
            "school_type": "高等学校",
            "establishment_type": "公立",
            "established_year": 1896,
            "composed_year": 1948,
            "notes": "兵庫県内トップ校",
            "copyright_status": "パブリックドメイン"
        }
    ]
    
    return sample_schools

def main():
    """サンプルデータ生成・保存"""
    print("📝 関西サンプルデータ生成中...")
    
    sample_data = create_sample_data()
    
    # JSONファイルに保存
    with open('sample_kansai_data.json', 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ サンプルデータ生成完了: {len(sample_data)}校")
    print("📁 ファイル: sample_kansai_data.json")
    print("\n使用方法:")
    print("python quick_sheets_add.py --file sample_kansai_data.json")

if __name__ == "__main__":
    main()

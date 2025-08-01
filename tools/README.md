# 校歌データ収集ツール

## 概要

全国の学校公式サイトから校歌情報を自動収集し、構造化データとして保存するツールです。Issue #8「大量データ収集プロジェクト」の一環として開発されました。

## 主な機能

- 🔍 **都道府県別学校検索**: Google Custom Search APIを使用
- 📖 **校歌情報自動抽出**: 学校サイトから歌詞・作詞者・作曲者を抽出
- 🗺️ **座標取得**: Google Geocoding APIで学校の緯度経度を取得
- 🎭 **マスク済み歌詞生成**: ゲーム用に学校名・地名をマスク
- 💡 **ヒント自動生成**: 都道府県・地域・地理的特徴のヒントを作成
- 📊 **CSV出力**: Googleスプレッドシート連携対応
- ✅ **品質管理**: 収集データの妥当性チェック

## セットアップ

### 1. 依存関係インストール

```bash
pip install requests beautifulsoup4 google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 2. Google API設定

#### Google Cloud Console設定
1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクト作成
2. 以下のAPIを有効化：
   - Custom Search API
   - Geocoding API
3. APIキーを作成

#### Google Custom Search設定
1. [Google Custom Search](https://cse.google.com/) でカスタム検索エンジン作成
2. 検索対象を「ウェブ全体」に設定
3. 検索エンジンIDをメモ

### 3. 設定ファイル作成

```bash
cp config.json.sample config.json
```

`config.json` を編集してAPIキーを設定：

```json
{
  "google_api_key": "YOUR_ACTUAL_API_KEY",
  "google_search_engine_id": "YOUR_ACTUAL_SEARCH_ENGINE_ID",
  "delay_seconds": 2,
  "max_schools_per_prefecture": 50
}
```

## 使い方

### 基本実行

```bash
python data_collector.py
```

### 都道府県指定実行

```python
from data_collector import SchoolDataCollector

collector = SchoolDataCollector()

# 特定の都道府県のみ収集
prefectures = ["東京都", "神奈川県", "大阪府"]
for prefecture in prefectures:
    schools = collector.collect_prefecture_data(prefecture)
    collector.save_to_csv(schools, f"{prefecture}_schools.csv")
```

### 収集戦略（Issue #8準拠）

#### Phase 1: 関東優先（250件目標）
```bash
# 関東地方の中学校を集中収集
python data_collector.py --prefecture 東京都,神奈川県,埼玉県,千葉県,茨城県,栃木県,群馬県 --school-type 中学校
```

#### Phase 2: 関西・九州（400件追加）
```bash
# 関西・九州地方の収集
python data_collector.py --prefecture 大阪府,京都府,兵庫県,奈良県,和歌山県,滋賀県,福岡県,佐賀県,長崎県,熊本県,大分県,宮崎県,鹿児島県,沖縄県
```

## データ構造

### 出力CSV形式

| 列名 | 説明 | 例 |
|------|------|-----|
| school_name | 学校名 | "東京都立戸山高等学校" |
| prefecture | 都道府県 | "東京都" |
| city | 市区町村 | "新宿区" |
| address | 住所 | "戸山3-19-1" |
| latitude | 緯度 | 35.7019 |
| longitude | 経度 | 139.7174 |
| full_lyrics | 校歌全文 | "朝日輝く戸山の丘に..." |
| masked_lyrics | マスク済み歌詞 | "朝日輝く〇〇の丘に..." |
| hint_prefecture | 都道府県ヒント | "関東地方の中心都市" |
| hint_region | 地域ヒント | "山手線内側の文教地区" |
| hint_landmark | 地理的特徴ヒント | "早稲田大学に近い高台" |

### データ品質レベル

- **A級（完全）**: 全項目が揃っている
- **B級（良好）**: 必須項目+α
- **C級（最低限）**: 学校名・所在地・歌詞のみ

## 進捗管理

### 都道府県別目標（Issue #8準拠）

| 地域 | 都道府県 | 目標件数 | 優先度 |
|------|----------|----------|--------|
| 関東 | 東京,神奈川,埼玉,千葉,茨城,栃木,群馬 | 250件 | P1 |
| 関西 | 大阪,京都,兵庫,奈良,和歌山,滋賀 | 200件 | P1 |
| 九州・沖縄 | 福岡,佐賀,長崎,熊本,大分,宮崎,鹿児島,沖縄 | 200件 | P2 |
| 中部 | 愛知,静岡,岐阜,三重,長野,山梨,新潟,富山,石川,福井 | 150件 | P2 |
| 北海道・東北 | 北海道,青森,岩手,宮城,秋田,山形,福島 | 100件 | P3 |
| 中国・四国 | 広島,岡山,山口,鳥取,島根,愛媛,香川,徳島,高知 | 100件 | P3 |

### 週次KPI

- **Week 1**: ツール開発完了、パイロット100件
- **Week 2-3**: 関東地方250件達成
- **Week 4-5**: 関西・九州400件追加（累計650件）
- **Week 6-7**: 残り地域350件追加（累計1000件）
- **Week 8**: 品質チェック・データ統合

## 品質管理

### 自動品質チェック

```python
# 品質チェック実行
from data_collector import SchoolDataCollector

collector = SchoolDataCollector()
schools = collector.load_from_csv("school_data.csv")

# 品質レポート生成
quality_report = collector.generate_quality_report(schools)
print(quality_report)
```

### 手動確認項目

1. **歌詞の正確性**: サンプリング検査
2. **座標の妥当性**: 地図上での位置確認
3. **重複排除**: 学校名・住所での重複チェック
4. **著作権状況**: パブリックドメイン判定

## トラブルシューティング

### よくある問題

#### APIクォータ超過
```
Error 429: API quota exceeded
```
**解決策**: `delay_seconds` を増やすか、複数のAPIキーを使用

#### 座標取得失敗
```
Error: Geocoding failed for address
```
**解決策**: 住所の表記を確認し、手動で座標を補完

#### 校歌情報が見つからない
```
Warning: No lyrics found on page
```
**解決策**: 手動収集に切り替えるか、別のデータソースを検討

## 開発・拡張

### カスタム抽出ルール追加

```python
# 特定学校向けのカスタム抽出ルール
def extract_custom_lyrics(self, soup, school_name):
    if "○○中学校" in school_name:
        # 特定学校用の抽出ロジック
        return custom_extraction_logic(soup)
    return None
```

### 新しいデータソース追加

```python
class WikipediaCollector(SchoolDataCollector):
    def extract_from_wikipedia(self, school_name):
        # Wikipedia からの情報抽出
        pass
```

## 貢献・フィードバック

- バグ報告: GitHubのIssues
- 機能要望: Issue #8へのコメント
- プルリクエスト: 歓迎します

## ライセンス・注意事項

### 著作権への配慮
- 収集データの利用前に著作権状況を確認
- パブリックドメイン楽曲を優先的に使用
- 商用利用時は適切な権利処理を実施

### レート制限遵守
- robots.txt の遵守
- 適切な間隔でのリクエスト実行
- サーバーへの負荷配慮

---

**関連Issue**: #8 (大量データ収集プロジェクト), #9 (基盤構築)  
**最終更新**: 2025年8月1日  
**作成者**: koka-location-quiz開発チーム

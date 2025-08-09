# スプレッドシート簡易追加ツール

**関西120校収集（Week 2）支援ツール**

## 🎯 概要

JSONファイルからGoogleスプレッドシートに学校データを簡単に追加するツールです。
既存のツールで追加が途中で止まる問題を解決するために作成されました。

## 📊 対象スプレッドシート

**校歌データ収集**: https://docs.google.com/spreadsheets/d/1ukF5ZhpwJkN21wHLTaTS13BYTk5puKPisdQ1fGR5BwE

## 🛠️ セットアップ

### 1. 依存関係インストール
```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

### 2. Google認証設定
1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. Google Sheets API と Google Drive API を有効化
3. サービスアカウント作成
4. 認証情報（JSON）をダウンロード
5. `tools/credentials.json` として保存
6. スプレッドシートにサービスアカウントのメールアドレスを編集者として共有

### 3. 実行権限付与
```bash
chmod +x tools/quick_add.sh
```

## 🚀 使用方法

### 基本的な使用方法

```bash
cd tools

# JSONファイルから追加
python3 quick_sheets_add.py --file your_data.json

# CSVファイルから追加
python3 quick_sheets_add.py --file your_data.csv --format csv

# バッチサイズ指定
python3 quick_sheets_add.py --file your_data.json --batch-size 20
```

### シェルスクリプトで簡単実行

```bash
cd tools

# サンプルデータでテスト
./quick_add.sh --sample

# データファイル指定
./quick_add.sh your_data.json

# CSVファイル指定
./quick_add.sh your_data.csv --format csv
```

## 📝 データ形式

### JSON形式例
```json
[
  {
    "school_name": "大阪市立天王寺中学校",
    "prefecture": "大阪府",
    "city": "大阪市天王寺区",
    "address": "大阪府大阪市天王寺区筆ヶ崎町2-5",
    "latitude": 34.6638,
    "longitude": 135.5191,
    "song_title": "校歌",
    "full_lyrics": "天王寺の丘に立ちて...",
    "masked_lyrics": "〇〇〇の丘に立ちて...",
    "composer": "田中作曲",
    "lyricist": "佐藤作詞",
    "difficulty": "medium",
    "quality_level": "A",
    "quality_score": 0.95,
    "data_source": "学校公式サイト",
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
  }
]
```

### 必須フィールド
- `school_name`: 学校名
- `prefecture`: 都道府県
- `city`: 市区町村

### オプションフィールド
- `address`: 住所
- `latitude`, `longitude`: 座標
- `song_title`: 校歌タイトル
- `full_lyrics`: 校歌全文
- `masked_lyrics`: マスク済み歌詞
- `composer`, `lyricist`: 作曲者・作詞者
- `difficulty`: 難易度 (easy/medium/hard)
- `quality_level`: 品質レベル (A/B/C/D)
- `quality_score`: 品質スコア (0.0-1.0)
- `data_source`: データソース
- `hints`: ヒント情報
- その他フィールド

## 🔧 ツール一覧

### quick_sheets_add.py
メインの追加ツール
- JSONファイルからスプレッドシートに追加
- エラーハンドリング強化
- バッチ処理でAPI制限回避

### create_sample_data.py
サンプルデータ生成ツール
- 関西地方のサンプルデータ作成
- テスト用データとして使用

### quick_add.sh
実行用シェルスクリプト
- 簡単なコマンドでデータ追加
- サンプルデータでのテスト実行

## 📊 Week 2関西収集での使用例

```bash
# 1. サンプルデータでテスト
./quick_add.sh --sample

# 2. 関西データファイルがある場合
./quick_add.sh kansai_120_schools.json

# 3. 大阪府データのみ追加
./quick_add.sh osaka_schools.json
```

## ⚠️ 注意事項

### API制限対策
- バッチサイズ: 10件ずつ処理（デフォルト）
- バッチ間隔: 2秒の待機時間
- エラー時の継続処理

### データ重複防止
- 自動的に次のIDを取得
- 既存データとの重複チェックは手動確認

### エラー対処
1. **認証エラー**: credentials.json の配置確認
2. **権限エラー**: スプレッドシートの共有設定確認
3. **API制限**: バッチサイズを小さくする
4. **ネットワークエラー**: 再実行

## 📈 進捗確認

追加後のデータ確認:
1. スプレッドシート画面で件数確認
2. 最新データの品質確認
3. 都道府県別の分布確認

## 🎯 Week 2目標

- **関西120校**: 大阪・京都・兵庫・奈良・滋賀・和歌山
- **品質目標**: A+B級90%以上
- **完了期限**: 8月15日（Week 2終了）
- **累計目標**: 228校（関東108校 + 関西120校）

## 🔗 関連リンク

- **スプレッドシート**: https://docs.google.com/spreadsheets/d/1ukF5ZhpwJkN21wHLTaTS13BYTk5puKPisdQ1fGR5BwE
- **GitHub Issues**: https://github.com/wwlapaki310/koka-location-quiz/issues/11
- **Project README**: ../README.md

---

**作成日**: 2025年8月9日  
**Phase 3 Week 2**: 関西120校収集支援ツール

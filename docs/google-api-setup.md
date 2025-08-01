# Google API設定ガイド

## 📋 概要

パイロット実行に必要なGoogle APIの設定手順です。

## 🔧 必要なAPI

1. **Google Custom Search API** - 学校サイト検索用
2. **Google Geocoding API** - 住所から座標取得用
3. **Google Sheets API** - データ保存用

## 📝 設定手順

### 1. Google Cloud Console設定

#### 1.1 プロジェクト作成
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
   - プロジェクト名: `koka-location-quiz` 
   - 課金を有効化（無料枠内で十分）

#### 1.2 API有効化
以下のAPIを有効化：
```
- Custom Search API
- Geocoding API  
- Google Sheets API
```

手順：
1. APIとサービス → ライブラリ
2. 各APIを検索して有効化

#### 1.3 APIキー作成
1. APIとサービス → 認証情報
2. 認証情報を作成 → APIキー
3. キーを制限（推奨）：
   - アプリケーションの制限: HTTPリファラー
   - API制限: Custom Search API, Geocoding API

### 2. Google Custom Search設定

#### 2.1 カスタム検索エンジン作成
1. [Google Custom Search](https://cse.google.com/) にアクセス
2. 新しい検索エンジンを追加
3. 設定：
   - 検索するサイト: `ウェブ全体を検索`
   - 言語: 日本語
   - 地域: 日本

#### 2.2 検索エンジンID取得
1. 作成した検索エンジンの設定
2. 基本タブで検索エンジンIDをコピー

### 3. Google Sheets設定

#### 3.1 サービスアカウント作成
1. Google Cloud Console → APIとサービス → 認証情報
2. 認証情報を作成 → サービスアカウント
3. サービスアカウント名: `koka-data-collector`
4. JSONキーをダウンロード

#### 3.2 スプレッドシート作成・共有
1. [Google Sheets](https://sheets.google.com/) で新しいシートを作成
2. タイトル: `校歌データ収集 - パイロット実行`
3. サービスアカウントのメールアドレスと共有（編集権限）
4. スプレッドシートIDをメモ（URLの `/d/` と `/edit` の間）

## ⚙️ 設定ファイル作成

### config.json作成

```bash
cd tools
cp config.json.sample config.json
```

`config.json` を編集：

```json
{
  "google_custom_search_api_key": "YOUR_API_KEY_HERE",
  "google_custom_search_engine_id": "YOUR_SEARCH_ENGINE_ID",
  "google_geocoding_api_key": "YOUR_API_KEY_HERE", 
  "google_sheets_credentials_file": "./credentials.json",
  "google_sheets_id": "YOUR_SPREADSHEET_ID",
  "delay_seconds": 2,
  "max_schools_per_prefecture": 50,
  "quality_threshold": 0.7,
  "retry_attempts": 3,
  "api_quotas": {
    "search_daily_limit": 100,
    "geocoding_daily_limit": 2500
  }
}
```

### credentials.json配置

ダウンロードしたサービスアカウントのJSONファイルを `tools/credentials.json` として保存

## 🧪 テスト実行

### 環境テスト
```bash
cd tools
python3 -c "
import json
with open('config.json') as f:
    config = json.load(f)
print('✅ Config file loaded')
print(f'Search Engine ID: {config.get(\"google_custom_search_engine_id\", \"Missing\")}')
print(f'Credentials file: {config.get(\"google_sheets_credentials_file\", \"Missing\")}')
"
```

### DRY RUN実行
```bash
python3 pilot_execution.py --dry-run
```

## 📊 API制限・コスト

### Custom Search API
- 無料枠: 100クエリ/日
- 有料: $5/1000クエリ
- パイロット実行: 約50-100クエリ予想

### Geocoding API  
- 無料枠: 2,500リクエスト/日
- 有料: $2-5/1000リクエスト
- パイロット実行: 約100リクエスト予想

### Sheets API
- 無料枠: 100リクエスト/100秒/ユーザー
- パイロット実行: 制限内で十分

## 🚨 トラブルシューティング

### よくあるエラー

#### API_KEY_INVALID
```
Error: API_KEY_INVALID
```
**解決策**: APIキーの確認、API有効化の確認

#### RATE_LIMIT_EXCEEDED  
```
Error: RATE_LIMIT_EXCEEDED
```
**解決策**: `delay_seconds` を増加（3-5秒）

#### SHEETS_ACCESS_DENIED
```
Error: SHEETS_ACCESS_DENIED  
```
**解決策**: サービスアカウントとの共有確認

## ✅ 準備完了チェックリスト

- [ ] Google Cloud Console プロジェクト作成
- [ ] Custom Search API, Geocoding API, Sheets API 有効化
- [ ] APIキー作成・制限設定
- [ ] カスタム検索エンジン作成
- [ ] サービスアカウント作成・JSONダウンロード
- [ ] Googleスプレッドシート作成・共有
- [ ] `config.json` 設定完了
- [ ] `credentials.json` 配置完了
- [ ] DRY RUNテスト成功

## 🎯 次のステップ

準備完了後：
1. `python3 pilot_execution.py --dry-run` で計画確認
2. `python3 pilot_execution.py` で本格実行開始
3. 進捗監視・結果分析

---

**関連**: Issue #10 (パイロット実行), Issue #8 (大量データ収集)  
**更新**: 2025年8月2日

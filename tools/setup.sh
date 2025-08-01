#!/bin/bash
# 校歌データ収集ツール セットアップスクリプト
# Issue #8「大量データ収集プロジェクト」環境構築用

set -e  # エラーで停止

echo "🏫 校歌データ収集ツール セットアップ開始"
echo "=================================================="

# Python バージョンチェック
echo "📍 Python バージョンチェック..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8以上が必要です。現在のバージョン: $python_version"
    exit 1
fi

echo "✅ Python $python_version が利用可能です"

# 仮想環境作成
echo "📍 Python仮想環境の作成..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 仮想環境を作成しました"
else
    echo "⚠️  仮想環境は既に存在します"
fi

# 仮想環境有効化
echo "📍 仮想環境の有効化..."
source venv/bin/activate

# pip アップグレード
echo "📍 pip のアップグレード..."
pip install --upgrade pip

# 依存関係インストール
echo "📍 依存関係のインストール..."
pip install -r requirements.txt

echo "✅ 依存関係のインストール完了"

# 設定ファイルの準備
echo "📍 設定ファイルの準備..."

# Google API設定
if [ ! -f "config.json" ]; then
    cp config.json.sample config.json
    echo "✅ config.json を作成しました (サンプルから)"
    echo "⚠️  Google API キー等の設定が必要です"
else
    echo "⚠️  config.json は既に存在します"
fi

# Googleスプレッドシート設定
if [ ! -f "sheets_config.json" ]; then
    cat > sheets_config.json << EOF
{
  "spreadsheet_id": "YOUR_SPREADSHEET_ID_HERE",
  "sheets": {
    "master": "学校マスター",
    "songs": "校歌データ",
    "progress": "進捗管理",
    "quality": "品質チェック",
    "copyright": "著作権情報"
  },
  "master_headers": [
    "ID", "学校名", "学校種別", "設置者", "都道府県", "市区町村", "住所",
    "緯度", "経度", "校歌タイトル", "校歌全文", "マスク済み歌詞",
    "作詞者", "作曲者", "制定年", "難易度", "ヒント1_地方", "ヒント2_地域",
    "ヒント3_特徴", "設立年", "備考", "データソース", "収集日",
    "収集者", "品質チェック", "著作権状況"
  ]
}
EOF
    echo "✅ sheets_config.json を作成しました"
else
    echo "⚠️  sheets_config.json は既に存在します"
fi

# ディレクトリ作成
echo "📍 作業ディレクトリの作成..."
mkdir -p data
mkdir -p logs
mkdir -p reports

echo "✅ ディレクトリを作成しました"

# 実行権限設定
echo "📍 実行権限の設定..."
chmod +x main.py
chmod +x data_collector.py
chmod +x sheets_manager.py
chmod +x quality_manager.py

# テスト実行
echo "📍 動作テスト..."
python3 -c "
import sys
sys.path.append('.')
try:
    from data_collector import SchoolDataCollector
    from sheets_manager import GoogleSheetsManager
    from quality_manager import DataQualityManager
    print('✅ 全モジュールのインポートに成功しました')
except ImportError as e:
    print(f'❌ インポートエラー: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ 動作テスト成功"
else
    echo "❌ 動作テスト失敗"
    exit 1
fi

echo ""
echo "=================================================="
echo "🎉 セットアップ完了！"
echo "=================================================="
echo ""
echo "📋 次のステップ:"
echo "1. Google Cloud Console でAPIを有効化"
echo "   - Custom Search API"
echo "   - Geocoding API"
echo ""
echo "2. config.json を編集してAPIキーを設定"
echo "   - google_api_key: Google API キー"
echo "   - google_search_engine_id: カスタム検索エンジンID"
echo ""
echo "3. (オプション) Google スプレッドシート連携"
echo "   - サービスアカウント認証情報 (credentials.json) を配置"
echo "   - sheets_config.json でスプレッドシートIDを設定"
echo ""
echo "4. パイロット実行"
echo "   ./main.py --prefecture 東京都 --max-schools 3 --dry-run"
echo ""
echo "📚 詳細な使用方法: README.md を参照"
echo ""

# 設定チェックリスト表示
echo "⚡ 設定チェックリスト:"
echo "[ ] Google API キー設定済み"
echo "[ ] カスタム検索エンジンID設定済み"
echo "[ ] (オプション) Google スプレッドシート認証設定済み"
echo "[ ] パイロット実行テスト完了"
echo ""
echo "全項目完了後、本格的なデータ収集を開始できます。"

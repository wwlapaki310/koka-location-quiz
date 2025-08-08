#!/bin/bash

# 校歌データ収集開始スクリプト
# Usage: ./start_collection.sh [dry-run]

echo "🏫 校歌データ収集 - 1000件データベース構築開始"
echo "=================================================="

# 作業ディレクトリ移動
cd "$(dirname "$0")"

# 引数チェック
DRY_RUN=""
if [ "$1" = "dry-run" ]; then
    DRY_RUN="--dry-run"
    echo "🧪 DRY RUN モード"
fi

echo "📅 実行日時: $(date)"
echo "📂 作業ディレクトリ: $(pwd)"

# 1. 環境チェック
echo ""
echo "🔍 Step 1: 環境チェック"
echo "------------------------"

if [ ! -f "config.json" ]; then
    if [ -f "config.json.complete.sample" ]; then
        echo "⚠️  config.json が見つかりません"
        echo "📋 config.json.complete.sample をコピーして設定してください："
        echo ""
        echo "   cp config.json.complete.sample config.json"
        echo "   # config.json を編集してAPIキーを設定"
        echo ""
        exit 1
    else
        echo "❌ 設定ファイルが見つかりません"
        exit 1
    fi
fi

if [ ! -f "credentials.json" ]; then
    echo "⚠️  credentials.json が見つかりません"
    echo "📋 Google Sheets API のサービスアカウントファイルを配置してください"
    echo "   参考: docs/google-api-setup.md"
    echo ""
    if [ -z "$DRY_RUN" ]; then
        exit 1
    fi
fi

# Python環境チェック
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 が見つかりません"
    exit 1
fi

echo "✅ 基本環境OK"

# 2. 依存関係チェック
echo ""
echo "📦 Step 2: 依存関係チェック"
echo "----------------------------"

if [ ! -f "requirements.txt" ]; then
    echo "⚠️  requirements.txt が見つかりません"
else
    echo "📋 必要なライブラリを確認中..."
    # 主要ライブラリのチェック
    python3 -c "
import sys
required = ['requests', 'beautifulsoup4', 'google-api-python-client', 'gspread']
missing = []
for lib in required:
    try:
        __import__(lib.replace('-', '_'))
    except ImportError:
        missing.append(lib)

if missing:
    print(f'⚠️  不足ライブラリ: {missing}')
    print('📥 インストール実行: pip3 install -r requirements.txt')
    sys.exit(1)
else:
    print('✅ 必要ライブラリ全て利用可能')
" || exit 1
fi

# 3. 設定ファイル検証
echo ""
echo "⚙️  Step 3: 設定ファイル検証"
echo "----------------------------"

python3 -c "
import json
import sys

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    required_keys = [
        'google_custom_search_api_key',
        'google_custom_search_engine_id',
        'google_geocoding_api_key',
        'google_sheets_credentials_file',
        'google_sheets_id'
    ]
    
    missing = []
    placeholder_values = ['YOUR_API_KEY_HERE', 'YOUR_SEARCH_ENGINE_ID', 'YOUR_SPREADSHEET_ID']
    
    for key in required_keys:
        if key not in config:
            missing.append(key)
        elif config[key] in placeholder_values:
            missing.append(f'{key} (プレースホルダー値)')
    
    if missing:
        print(f'❌ 設定不足: {missing}')
        print('📋 config.json を正しく設定してください')
        print('   参考: docs/google-api-setup.md')
        sys.exit(1)
    else:
        print('✅ 設定ファイル検証完了')
        
except Exception as e:
    print(f'❌ 設定ファイルエラー: {e}')
    sys.exit(1)
" || exit 1

# 4. パイロット実行
echo ""
echo "🚀 Step 4: パイロット実行開始"
echo "------------------------------"

if [ -n "$DRY_RUN" ]; then
    echo "🧪 実行計画の確認："
    python3 pilot_execution.py $DRY_RUN
else
    echo "📊 実際のデータ収集を開始します"
    echo ""
    echo "📍 収集対象:"
    echo "   - 関東1都6県: 100校"
    echo "   - 品質目標: A+B級80%以上"
    echo "   - 実行時間目標: 2時間以内"
    echo ""
    
    read -p "データ収集を開始しますか？ (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🎯 パイロット実行開始..."
        
        # ログファイル準備
        LOG_FILE="pilot_execution_$(date +%Y%m%d_%H%M%S).log"
        
        # 実行時間計測
        START_TIME=$(date +%s)
        
        # パイロット実行
        python3 pilot_execution.py 2>&1 | tee "$LOG_FILE"
        PILOT_RESULT=$?
        
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        echo ""
        echo "⏱️  実行時間: $((DURATION / 60))分$((DURATION % 60))秒"
        echo "📄 ログファイル: $LOG_FILE"
        
        if [ $PILOT_RESULT -eq 0 ]; then
            echo "✅ パイロット実行完了"
            echo ""
            echo "🎯 次のステップ:"
            echo "   1. レポートファイルの確認"
            echo "   2. Googleスプレッドシートの結果確認"
            echo "   3. 品質評価・成功判定"
            echo "   4. 本格実行(Issue #11)への移行判定"
        else
            echo "❌ パイロット実行でエラーが発生しました"
            echo "📋 ログファイルを確認してください: $LOG_FILE"
        fi
    else
        echo "❌ 実行がキャンセルされました"
    fi
fi

echo ""
echo "=================================================="
echo "📚 参考資料:"
echo "   - Google API設定: docs/google-api-setup.md"
echo "   - プロジェクト状況: docs/PROJECT_STATUS.md"
echo "   - Issue #10: パイロット実行"
echo "   - Issue #11: Phase 3本格実行"
echo "=================================================="

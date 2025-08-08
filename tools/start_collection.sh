#!/bin/bash

# 🚀 校歌データ収集実行スクリプト - リアルタイム進捗記録対応
# Usage: ./start_collection.sh [dry-run|collect|monitor]

echo "🏫 校歌データ収集 - 1000件データベース構築システム"
echo "==========================================================="

# 作業ディレクトリ移動
cd "$(dirname "$0")"

# 実行モード判定
MODE="collect"
if [ "$1" = "dry-run" ]; then
    MODE="dry-run"
elif [ "$1" = "monitor" ]; then
    MODE="monitor"
elif [ "$1" = "collect" ]; then
    MODE="collect"
fi

echo "📅 実行日時: $(date)"
echo "📂 作業ディレクトリ: $(pwd)"
echo "🎯 実行モード: $MODE"

# 1. 環境チェック
echo ""
echo "🔍 Step 1: 環境チェック"
echo "------------------------"

# 設定ファイルチェック
if [ ! -f "config.json" ]; then
    if [ -f "config.json.complete.sample" ]; then
        echo "⚠️  config.json が見つかりません"
        echo "📋 テンプレートから作成します..."
        cp config.json.complete.sample config.json
        echo "✅ config.json を作成しました"
        echo "⚠️  APIキーを設定してから再実行してください"
        echo ""
        echo "   編集必要項目:"
        echo "   - google_custom_search_api_key"
        echo "   - google_custom_search_engine_id"
        echo "   - google_geocoding_api_key"
        echo "   - google_sheets_id"
        echo ""
        exit 1
    else
        echo "❌ 設定ファイルテンプレートが見つかりません"
        exit 1
    fi
fi

# 認証ファイルチェック
if [ ! -f "credentials.json" ] && [ "$MODE" != "dry-run" ]; then
    echo "⚠️  credentials.json が見つかりません"
    echo "📋 Google Sheets APIのサービスアカウントファイルを配置してください"
    echo "   参考: docs/google-api-setup.md"
    exit 1
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

python3 -c "
import sys
required = ['requests', 'beautifulsoup4', 'google-api-python-client', 'gspread', 'google-auth']
missing = []
for lib in required:
    try:
        if lib == 'google-api-python-client':
            __import__('googleapiclient')
        elif lib == 'google-auth':
            __import__('google.auth')
        else:
            __import__(lib.replace('-', '_'))
    except ImportError:
        missing.append(lib)

if missing:
    print(f'⚠️  不足ライブラリ: {missing}')
    print('📥 自動インストールを実行します...')
    import subprocess
    for lib in missing:
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib])
            print(f'✅ {lib} インストール完了')
        except:
            print(f'❌ {lib} インストール失敗')
            sys.exit(1)
else:
    print('✅ 必要ライブラリ全て利用可能')
" || exit 1

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
        elif config.get(key) in placeholder_values:
            missing.append(f'{key} (プレースホルダー値)')
    
    if missing and '$MODE' != 'dry-run':
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

# 4. 実行モード別処理
echo ""
echo "🚀 Step 4: 実行開始"
echo "--------------------"

case $MODE in
    "dry-run")
        echo "🧪 DRY RUN モード: 実行計画を確認します"
        echo ""
        python3 integrated_collector.py --dry-run
        echo ""
        echo "📋 DRY RUN 完了"
        echo "✅ 実際の収集を開始する場合: ./start_collection.sh collect"
        ;;
        
    "monitor")
        echo "📊 監視モード: 進捗をリアルタイム表示します"
        echo ""
        
        # 進捗監視ダッシュボード起動
        echo "🎯 進捗ダッシュボード起動中..."
        python3 progress_dashboard.py &
        DASHBOARD_PID=$!
        
        echo "📊 進捗記録システム監視中..."
        python3 progress_recorder.py &
        RECORDER_PID=$!
        
        echo ""
        echo "✅ 監視システム起動完了"
        echo "📊 進捗確認: Googleスプレッドシートをチェック"
        echo "🔄 停止する場合: Ctrl+C"
        
        # 監視継続
        trap "kill $DASHBOARD_PID $RECORDER_PID 2>/dev/null; exit" INT
        wait
        ;;
        
    "collect")
        echo "🎯 データ収集開始準備"
        echo ""
        echo "📍 収集対象:"
        echo "   - 関東1都6県: 100校"
        echo "   - 品質目標: A+B級80%以上"
        echo "   - 実行時間目標: 2時間以内"
        echo "   - リアルタイム進捗記録: ON"
        echo "   - Googleスプレッドシート連携: ON"
        echo ""
        
        read -p "🚀 データ収集を開始しますか？ (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🎯 統合データ収集システム開始..."
            echo "📊 リアルタイム進捗記録を開始します"
            
            # ログファイル準備
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            LOG_FILE="data_collection_${TIMESTAMP}.log"
            
            # 実行時間計測
            START_TIME=$(date +%s)
            
            echo "⏱️  開始時刻: $(date)"
            echo "📄 ログファイル: $LOG_FILE"
            echo ""
            
            # 統合データ収集実行
            python3 integrated_collector.py --config config.json 2>&1 | tee "$LOG_FILE"
            COLLECTION_RESULT=$?
            
            END_TIME=$(date +%s)
            DURATION=$((END_TIME - START_TIME))
            
            echo ""
            echo "========================================"
            echo "⏱️  実行時間: $((DURATION / 60))分$((DURATION % 60))秒"
            echo "📄 ログファイル: $LOG_FILE"
            
            if [ $COLLECTION_RESULT -eq 0 ]; then
                echo "🎉 データ収集完了！"
                echo ""
                echo "📊 結果確認:"
                echo "   1. 最終レポートファイル確認"
                echo "   2. Googleスプレッドシート確認"
                echo "   3. GitHub Issue #10 進捗確認"
                echo ""
                echo "🎯 次のステップ:"
                echo "   - 成功基準達成時: Issue #11 本格実行開始"
                echo "   - 改善必要時: ツール調整・再実行"
                echo ""
                echo "🔍 詳細分析: python3 progress_dashboard.py --report"
            else
                echo "❌ データ収集でエラーが発生しました"
                echo ""
                echo "🔍 トラブルシューティング:"
                echo "   1. ログファイル確認: $LOG_FILE"
                echo "   2. API制限・認証エラーの確認"
                echo "   3. 設定ファイル再確認"
                echo "   4. DRY RUN での動作確認"
                echo ""
                echo "🔄 再実行: ./start_collection.sh collect"
            fi
        else
            echo "❌ データ収集がキャンセルされました"
        fi
        ;;
        
    *)
        echo "❌ 不正な実行モード: $MODE"
        echo ""
        echo "📋 使用方法:"
        echo "   ./start_collection.sh dry-run   # 実行計画確認"
        echo "   ./start_collection.sh collect   # データ収集実行"
        echo "   ./start_collection.sh monitor   # 進捗監視"
        exit 1
        ;;
esac

echo ""
echo "==========================================================="
echo "📚 参考資料・関連リンク:"
echo "   - Google API設定: docs/google-api-setup.md"
echo "   - プロジェクト状況: docs/PROJECT_STATUS.md"
echo "   - Issue #10: パイロット実行"
echo "   - Issue #11: Phase 3本格実行"
echo "   - 進捗確認: Googleスプレッドシート"
echo "==========================================================="

exit 0

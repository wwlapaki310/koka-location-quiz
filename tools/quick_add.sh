#!/bin/bash
# スプレッドシート簡易追加実行スクリプト

echo "📊 スプレッドシート簡易追加ツール"
echo "=================================="

# 必要なファイル確認
if [ ! -f "credentials.json" ]; then
    echo "❌ credentials.json が見つかりません"
    echo "📋 Google Cloud Console でサービスアカウントを作成し、認証情報をダウンロードしてください"
    exit 1
fi

# 引数確認
if [ $# -eq 0 ]; then
    echo "📝 使用方法:"
    echo "  ./quick_add.sh [データファイル] [オプション]"
    echo ""
    echo "📁 例:"
    echo "  ./quick_add.sh sample_kansai_data.json"
    echo "  ./quick_add.sh data.csv --format csv"
    echo ""
    echo "🧪 サンプルデータでテスト実行:"
    echo "  ./quick_add.sh --sample"
    exit 0
fi

# サンプルデータ生成・実行
if [ "$1" = "--sample" ]; then
    echo "🧪 サンプルデータを生成中..."
    python3 create_sample_data.py
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "📤 サンプルデータをスプレッドシートに追加中..."
        python3 quick_sheets_add.py --file sample_kansai_data.json
    else
        echo "❌ サンプルデータ生成に失敗しました"
        exit 1
    fi
else
    # 通常実行
    DATA_FILE="$1"
    shift
    
    if [ ! -f "$DATA_FILE" ]; then
        echo "❌ データファイルが見つかりません: $DATA_FILE"
        exit 1
    fi
    
    echo "📤 データをスプレッドシートに追加中..."
    echo "📁 ファイル: $DATA_FILE"
    
    python3 quick_sheets_add.py --file "$DATA_FILE" "$@"
fi

# 実行結果確認
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 スプレッドシート追加完了!"
    echo "🔗 確認: https://docs.google.com/spreadsheets/d/1ukF5ZhpwJkN21wHLTaTS13BYTk5puKPisdQ1fGR5BwE"
else
    echo "❌ スプレッドシート追加に失敗しました"
    exit 1
fi

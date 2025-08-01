# 開発ガイド

## 🏗️ プロジェクト構造（予定）

```
koka-location-quiz/
├── frontend/                 # フロントエンドアプリケーション
│   ├── src/
│   │   ├── components/       # Reactコンポーネント
│   │   ├── pages/           # Next.jsページ
│   │   ├── hooks/           # カスタムフック
│   │   ├── utils/           # ユーティリティ関数
│   │   ├── types/           # TypeScript型定義
│   │   └── styles/          # スタイル定義
│   ├── public/              # 静的ファイル
│   └── package.json
├── backend/                  # バックエンドAPI
│   ├── src/
│   │   ├── controllers/     # APIコントローラー
│   │   ├── models/          # データモデル
│   │   ├── services/        # ビジネスロジック
│   │   ├── utils/           # ユーティリティ
│   │   └── types/           # 型定義
│   ├── migrations/          # データベースマイグレーション
│   └── package.json
├── data/                     # データ関連
│   ├── raw/                 # 生データ
│   ├── processed/           # 処理済みデータ
│   ├── scripts/             # データ処理スクリプト
│   └── README.md
├── docs/                     # ドキュメント
├── tests/                    # テストファイル
└── tools/                    # 開発ツール
```

## 🔧 開発環境セットアップ

### 必要な環境
- Node.js 18.x以上
- npm 9.x以上
- PostgreSQL 14.x以上（本格開発時）
- Git

### 初期セットアップ（Phase 1完了後）
```bash
# リポジトリクローン
git clone https://github.com/wwlapaki310/koka-location-quiz.git
cd koka-location-quiz

# 依存関係インストール
npm run install:all

# 環境変数設定
cp .env.example .env.local
# .env.localを編集

# データベースセットアップ
npm run db:setup

# 開発サーバー起動
npm run dev
```

### 開発コマンド
```bash
# 全体
npm run dev              # 開発サーバー起動
npm run build            # プロダクションビルド
npm run test             # テスト実行
npm run lint             # リント実行
npm run format           # コード整形

# フロントエンド
npm run dev:frontend     # フロントエンド開発サーバー
npm run build:frontend   # フロントエンドビルド
npm run test:frontend    # フロントエンドテスト

# バックエンド
npm run dev:backend      # バックエンド開発サーバー
npm run build:backend    # バックエンドビルド
npm run test:backend     # バックエンドテスト

# データベース
npm run db:migrate       # マイグレーション実行
npm run db:seed          # シードデータ投入
npm run db:reset         # データベースリセット
```

## 📊 データ管理

### データ収集フロー
1. **生データ収集**: 各種ソースからの校歌データ取得
2. **データクレンジング**: 重複除去、形式統一
3. **品質チェック**: 歌詞・学校情報の正確性確認
4. **データベース投入**: 構造化データとしてDB格納

### データスキーマ
```sql
-- 学校マスター
CREATE TABLE schools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type school_type NOT NULL, -- 'public', 'private', 'national'
    prefecture VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    established_year INTEGER,
    website_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 校歌マスター
CREATE TABLE school_songs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_id UUID REFERENCES schools(id),
    title VARCHAR(255),
    lyrics TEXT NOT NULL,
    composer VARCHAR(255),
    lyricist VARCHAR(255),
    composed_year INTEGER,
    difficulty difficulty_level, -- 'easy', 'medium', 'hard'
    copyright_status VARCHAR(50), -- 'public_domain', 'permission_required', 'unknown'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- クイズ問題
CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    song_id UUID REFERENCES school_songs(id),
    masked_lyrics TEXT NOT NULL, -- 学校名等をマスクした歌詞
    correct_school_id UUID REFERENCES schools(id),
    difficulty difficulty_level,
    region VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🎮 ゲームロジック

### 問題生成アルゴリズム
1. **ユーザー設定取得**: 難易度、地域、問題数
2. **候補絞り込み**: 条件に合う校歌をフィルタリング
3. **選択肢生成**: 正解校を含む4択を作成
4. **歌詞マスキング**: 学校名・地名の適切な隠蔽

### スコア計算
```typescript
interface ScoreCalculation {
  baseScore: number;        // 基本点数（難易度による）
  timeBonus: number;        // 時間ボーナス
  streakBonus: number;      // 連続正解ボーナス
  difficultyMultiplier: number; // 難易度倍率
}

function calculateScore(params: ScoreCalculation): number {
  return (params.baseScore + params.timeBonus + params.streakBonus) 
         * params.difficultyMultiplier;
}
```

## 🗺️ 地図機能

### 地図ライブラリ比較

| 機能 | Google Maps | Leaflet + OSM | MapBox |
|------|-------------|---------------|--------|
| 費用 | 有料（クレジット制） | 無料 | 有料 |
| カスタマイズ | 制限あり | 高い自由度 | 高い自由度 |
| 日本地図品質 | 最高 | 良好 | 良好 |
| モバイル対応 | 優秀 | 良好 | 優秀 |
| 開発難易度 | 簡単 | 中程度 | 中程度 |

### 地図データ要件
- 都道府県境界データ
- 市区町村境界データ
- 学校位置データ（緯度経度）
- 地理的特徴データ（山、川、海等）

## 🧪 テスト戦略

### テストピラミッド
```
     E2E Tests (少数・重要フロー)
       ↗              ↖
  Integration Tests (API・DB連携)
    ↗                      ↖
Unit Tests (コンポーネント・関数)
```

### テストカテゴリ

#### Unit Tests
- コンポーネントの描画テスト
- ユーティリティ関数の動作テスト
- データ変換ロジックのテスト

#### Integration Tests
- API エンドポイントテスト
- データベースクエリテスト
- 外部サービス連携テスト

#### E2E Tests
- ユーザー登録〜ゲームプレイフロー
- スコア記録・ランキング表示
- レスポンシブデザイン確認

## 🚀 デプロイメント

### 開発環境
- **フロントエンド**: Vercel Preview
- **バックエンド**: Railway Development
- **データベース**: PostgreSQL on Railway

### 本番環境
- **フロントエンド**: Vercel Production
- **バックエンド**: Railway Production
- **データベース**: PostgreSQL on Railway（専用インスタンス）
- **CDN**: Vercel Edge Network
- **監視**: Vercel Analytics + Sentry

### CI/CD パイプライン
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run tests
        run: npm test
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Build
        run: npm run build
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
```

## 🔒 セキュリティ

### 認証・認可
- JWT トークンベース認証
- OAuth 2.0（Google、Twitter等）
- パスワードハッシュ化（bcrypt）

### データ保護
- HTTPS通信の強制
- SQLインジェクション対策
- XSS対策（Content Security Policy）
- CORS設定

### プライバシー
- 個人情報の最小収集
- データ匿名化
- Cookie同意バナー
- GDPR準拠（将来的）

---

**注意**: このドキュメントはPhase 1（技術選定）完了後に詳細化されます。
# 校歌場所当てクイズ MVP

校歌の歌詞から学校の場所を推測するクイズゲームのMVP（最小機能版）です。

## 🎯 機能

- 5問のクイズに挑戦
- 校歌の歌詞を表示（学校名は〇〇でマスク）
- 4択形式で学校を推測
- 正解・不正解のフィードバック
- スコア表示
- レスポンシブデザイン

## 🚀 開発・実行

### 必要な環境
- Node.js 18.x以上
- npm

### セットアップ
```bash
# 依存関係をインストール
npm install

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview
```

## 🛠️ 技術スタック

- **React 18** - UI フレームワーク
- **TypeScript** - 型安全性
- **Vite** - 高速ビルドツール
- **Tailwind CSS** - スタイリング
- **Lucide React** - アイコン

## 📋 データ構造

現在はサンプルデータをハードコードしていますが、将来的にはGoogleスプレッドシートと連携予定です。

```typescript
interface SchoolData {
  id: number;
  schoolName: string;
  prefecture: string;
  city: string;
  address: string;
  songTitle: string;
  lyrics: string;
  maskedLyrics: string;
  difficulty: 'easy' | 'medium' | 'hard';
  notes: string;
}
```

## 📊 サンプルデータ

現在5校のサンプルデータを収録：
- 東京都立新宿高等学校
- 大阪府立北野高等学校
- 福岡県立修猷館高等学校
- 愛知県立旭丘高等学校
- 神奈川県立横浜翠嵐高等学校

## 🔄 次期機能

- [ ] Google Sheets API連携
- [ ] 地図表示機能
- [ ] 難易度選択
- [ ] 問題数選択
- [ ] 都道府県フィルター
- [ ] ランキング機能

## 📝 デプロイ

Vercelにデプロイ可能：

1. GitHubリポジトリをVercelと連携
2. ビルドコマンド: `npm run build`
3. 出力ディレクトリ: `dist`

## 🎨 デザイン

- モバイルファーストのレスポンシブデザイン
- 親しみやすいカラーパレット
- 直感的なUI/UX
- アクセシビリティ配慮

---

**プロジェクト全体**: [koka-location-quiz](https://github.com/wwlapaki310/koka-location-quiz)
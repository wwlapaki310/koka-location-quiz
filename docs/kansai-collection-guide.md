# 関西120校収集実行ガイド - Week 2

## 📋 実行概要

**期間**: 2025年8月9日〜8月15日  
**目標**: 関西6府県から120校データ収集  
**累計**: 関東108校 + 関西120校 = 228校  
**品質目標**: A+B級90%以上

## 🎯 収集計画

### 府県別目標配分
| 府県 | 目標数 | 重点都市 | 優先度 |
|------|--------|----------|--------|
| 大阪府 | 35校 | 大阪市・堺市・東大阪市 | P1 |
| 兵庫県 | 30校 | 神戸市・西宮市・姫路市 | P1 |
| 京都府 | 25校 | 京都市・宇治市 | P1 |
| 奈良県 | 15校 | 奈良市・橿原市 | P2 |
| 滋賀県 | 10校 | 大津市・草津市 | P2 |
| 和歌山県 | 5校 | 和歌山市 | P2 |
| **合計** | **120校** | - | - |

## ⚙️ 実行前準備

### 1. 環境設定確認

```bash
cd tools

# 設定ファイル確認
ls -la config.json
cat config.json.sample  # 設定項目参考

# 依存関係確認
pip install -r requirements.txt

# Google API設定確認
python -c "import json; print('Config OK' if json.load(open('config.json')).get('google_custom_search_api_key') else 'API Key Missing')"
```

### 2. Googleスプレッドシート準備

```bash
# スプレッドシート接続テスト
python sheets_manager.py --test-connection

# 既存データ確認（関東108校の存在確認）
python sheets_manager.py --show-stats
```

### 3. DRY RUN実行（必須）

```bash
# 実行計画確認
python kansai_collection.py --dry-run

# 期待される出力：
# 🧪 DRY RUN: 大阪府 の 35校を収集予定
# 🧪 DRY RUN: 兵庫県 の 30校を収集予定
# ...
# 📋 推定実行時間: 4.0時間
```

## 🚀 本格実行

### Step 1: 関西収集開始

```bash
# 並行処理モード（推奨）
python kansai_collection.py

# または順次処理モード（デバッグ用）
python kansai_collection.py --sequential
```

### Step 2: 実行中監視

別ターミナルで進捗監視：

```bash
# 進捗ダッシュボード起動
python progress_dashboard.py --region 関西

# ログ確認
tail -f kansai_execution_$(date +%Y%m%d).log

# 中間結果確認
ls -la kansai_week2_checkpoint_*.json
```

### Step 3: 品質チェック

```bash
# 品質レポート生成
python quality_manager.py --analyze kansai_week2_checkpoint_final_*.json

# 期待される品質分布：
# A級: 50-60%
# B級: 30-40%
# C級: 5-10%
# D級: 0-5%
```

## 📊 成功基準

### 必須達成項目
- [x] **収集数**: 120校以上（100%達成）
- [x] **品質**: A+B級90%以上
- [x] **成功率**: 80%以上
- [x] **実行時間**: 週内完了（6時間以内）

### 推奨達成項目
- [x] **府県バランス**: 各府県目標の80%以上達成
- [x] **データ品質**: A級60%以上
- [x] **処理効率**: 1校あたり3秒以内
- [x] **API効率**: エラー率5%以下

## 🛠️ トラブルシューティング

### よくある問題と対処法

#### 1. API制限エラー
```
Error 429: API quota exceeded
```
**対処法**:
```bash
# 設定ファイルで遅延を増加
vim config.json
# "delay_seconds": 3 → 5

# または1日待機して翌日実行
```

#### 2. スプレッドシートエラー
```
Error: Sheets API authentication failed
```
**対処法**:
```bash
# 認証ファイル再設定
cp path/to/credentials.json tools/
python sheets_manager.py --reauth
```

#### 3. 品質低下
```
Warning: Quality A+B rate below 85%
```
**対処法**:
```bash
# データソース拡張
python kansai_collection.py --additional-sources

# 手動検証併用
python quality_manager.py --manual-review
```

#### 4. 処理速度低下
```
Warning: Average time per school > 5 seconds
```
**対処法**:
```bash
# 並行処理数調整
python kansai_collection.py --max-workers 2

# ネットワーク状況確認
ping google.com
```

## 📈 実行後処理

### 1. 結果確認

```bash
# 最終レポート確認
cat kansai_week2_report_*.json

# 主要指標確認
grep -E "(collected_schools|achievement_rate|quality_ab_rate)" kansai_week2_report_*.json
```

### 2. データ統合

```bash
# MVPアプリ用データ生成
python data_converter.py --kansai-to-mvp kansai_week2_checkpoint_final_*.json

# 統合データ確認
python -c "
import json
data = json.load(open('mvp/src/data/schoolData.json'))
print(f'Total schools: {len(data)}')
print(f'Kansai schools: {len([s for s in data if s[\"prefecture\"] in [\"大阪府\", \"兵庫県\", \"京都府\", \"奈良県\", \"滋賀県\", \"和歌山県\"]])}')
"
```

### 3. Week 3準備

```bash
# Week 3計画生成
python week3_planner.py --based-on kansai_week2_report_*.json

# 中部収集スクリプト準備
cp kansai_collection.py chubu_collection.py
# 対象地域を中部に変更して調整
```

## 📋 実行チェックリスト

### 実行前（必須）
- [ ] Google API設定完了
- [ ] config.json設定確認
- [ ] DRY RUN実行・結果確認
- [ ] Googleスプレッドシート接続確認
- [ ] 関東108校データ存在確認

### 実行中（推奨）
- [ ] 進捗ダッシュボード監視
- [ ] ログファイル定期確認
- [ ] 中間チェックポイント保存確認
- [ ] API制限状況監視

### 実行後（必須）
- [ ] 120校収集確認
- [ ] 品質A+B級90%確認
- [ ] Googleスプレッドシートアップロード確認
- [ ] MVPアプリデータ統合
- [ ] Week 3計画策定

## 🎯 期待される成果

### データ成果物
- **収集データ**: 関西120校の校歌・位置・品質情報
- **品質レポート**: 府県別品質分析
- **実行レポート**: パフォーマンス分析・改善提案
- **統合データ**: MVPアプリ用228校データ

### プロジェクト成果
- **進捗**: 全国1000校の22.8%完了
- **品質**: パイロット実行レベル維持・向上
- **効率**: 並行処理システム実用化
- **ノウハウ**: Week 3以降への知見蓄積

## 📞 問題発生時の連絡先

- **技術的問題**: Issue #11へコメント
- **API制限問題**: Google Cloud Consoleで確認
- **データ品質問題**: quality_manager.py で詳細分析
- **スケジュール遅延**: Week 3計画の調整検討

---

**最終更新**: 2025年8月2日  
**担当**: データ収集チーム  
**関連Issue**: #11 (Phase 3本格実行開始)

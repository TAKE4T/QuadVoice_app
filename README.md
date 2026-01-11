# QuadVoice API (MVP Skeleton)

This repository contains a FastAPI-based backend that follows the PRD in `rd.md`. It now wires Supabase/pgvector persistence, LangGraph風ワークフロー、Anthropicバックエンド（任意）を組み合わせたMVP実装です。Supabaseの認証情報が無い場合はインメモリにフォールバックします。

## Quick start

1. Copy `.env` values:
   ```bash
   cp env.example .env
   ```
2. Start Postgres with pgvector (optional if Supabase is remote):
   ```bash
   docker compose up -d
   ```
3. Install dependencies and run the API:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

### Supabase接続
- `.env` に `SUPABASE_URL` と `SUPABASE_SERVICE_KEY` を設定してください（サービスロールキー推奨）。
- `Identity_Docs`, `Platform_Styles`, `Projects` テーブルを PRD に合わせて作成してください。`embedding` カラムは `vector(1536)` を推奨。
- 環境変数が無い場合はログに警告を出しつつインメモリで動作します。

## API surface

- `POST /api/v1/ingest/identity` — Markdown複数と `doc_type` (`skill|goal|knowledge`) を受け取り、埋め込みを付与し Supabase (あれば) に保存。
- `POST /api/v1/ingest/style` — Markdownと `platform` (`qiita|zenn|note|owned`) を受け取り、簡易スタイル抽出して Supabase 保存。
- `POST /api/v1/generate` — `{"theme": "..."}` でプロジェクトを作成し、LangGraph風ワークフロー＋Anthropic（キーがあれば）で4媒体ドラフトを生成し保存。
- `GET /api/v1/generate/{project_id}` — 生成結果とイベントを取得。
- `WS /api/v1/ws/generate/{project_id}` — 進捗イベントと完了データをリアルタイム送信（同時にプロジェクトも更新）。

## Next steps (per PRD)

- Supabase Auth を組み込み、ユーザー単位のスコープを強制する。
- LangGraph で分岐/並列を増やし、Claudeのプロンプトを媒体別に最適化する。
- 既存記事スタイル抽出をLLM化し、ベクトル検索とFew-shotを組み合わせる。
- SSE/WS をバックグラウンドジョブと連携し、長時間処理でも途切れないようにする。

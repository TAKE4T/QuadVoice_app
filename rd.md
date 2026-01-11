# 🚀 プロダクト要件定義書 (PRD): CodeName "QuadVoice"

## 1. プロダクト概要

### コンセプト
**「ひとつのテーマ、4つの人格」**
ユーザーの「思想（スキル・目標・知識）」を核（Core）とし、LangGraphワークフローを通じてQiita、Zenn、note、オウンドメディアという4つの異なる文脈（Context）へ最適化された記事を同時生成する、適応型コンテンツ生成プラットフォーム。

### バリュープロポジション
1.  **Context-Aware**: 単なる要約やリライトではなく、各プラットフォームの「文化・作法」に則った構成変換。
2.  **Identity-Preservation**: ユーザー固有の思想（スキルセット、目標、知識体系）をRAGとSystem Promptに組み込み、AI臭さを排除した「本人らしい」文章生成。
3.  **Visualized Workflow**: LangGraphによる生成プロセスの透明化と、リアルタイムな進捗可視化。

---

## 2. システムアーキテクチャ詳細

フロントエンドとバックエンドを分離し、リアルタイム性と拡張性を担保する構成とする。

### 2.1 全体構成図
```mermaid
graph TD
    User[User Browser] -->|HTTPS| Vercel[Vercel Edge Network]
    Vercel -->|Static Assets| CDN
    Vercel -->|SSR/API Routes| NextJS[Next.js App Router]
    
    subgraph "Backend Infrastructure (Railway/Render recommended for Python)"
        NextJS -->|REST/WebSocket| FastAPI[FastAPI Server]
        FastAPI -->|State Management| LangGraph[LangGraph Engine]
        LangGraph -->|LLM Inference| Claude[Anthropic API (Claude 3.5 Sonnet)]
        
        subgraph "Data Layer (Supabase)"
            LangGraph -->|Vector Search| PgVector[pgvector]
            FastAPI -->|CRUD| Postgres[PostgreSQL]
        end
    end
```

### 2.2 技術スタック選定

| カテゴリ | 技術 | 選定理由 |
| :--- | :--- | :--- |
| **Frontend** | **Next.js 14 (App Router)** | Vercelとの親和性、Server Actions、React Server Componentsによるパフォーマンス最適化。 |
| **Styling** | **Tailwind CSS + shadcn/ui** | デザイン工数削減とカスタマイズ性の両立。take4ht氏のデザイナー領域を活かせる。 |
| **Backend** | **FastAPI (Python 3.11+)** | LangGraph/LangChainエコシステムとの直接統合に必須。非同期処理に強い。 |
| **Orchestration** | **LangGraph** | 循環的なワークフロー、状態保持、条件分岐をコードで定義可能。 |
| **LLM** | **Anthropic Claude 3.5 Sonnet** | 日本語の流暢さ、長文脈理解(Context Window)、コード生成能力において現状最適解。 |
| **Database** | **Supabase (PostgreSQL)** | RDBとVector Store (pgvector) を単一インスタンスで管理可能。Auth機能も利用可。 |
| **Deploy** | **Vercel (FE) + Railway (BE)** | Next.jsはVercel、Pythonバックエンドは永続プロセスが必要なためRailway推奨。 |

---

## 3. 機能要件 (Functional Requirements)

### 3.1 ユーザー思想学習 (Identity Layer)
*   **Markdown Ingestion**: 以下の3種のMDファイルをパースし、EmbeddingしてVector Storeへ格納。
    *   `skill_map.md` (技術スタック、得意領域)
    *   `goal_map.md` (発信の目的、ブランディング方針)
    *   `knowledge_map.md` (用語集、独自の定義、過去の知見)
*   **Context Injection**: 記事生成時、関連する思想チャンクを検索し、System Promptに注入。

### 3.2 記事構成学習 (Style Layer)
*   **Structure Learning**: ユーザーがアップロードした過去記事/構成案(`qiita_structure.md`等)から、以下の要素を抽出・構造化してDB保存。
    *   見出し構成パターン
    *   口調・文体（「だ・である」「です・ます」）
    *   コードブロックの頻度
    *   導入と結びの定型
*   **Feedback Loop**: 生成結果に対するユーザー修正版MDを再アップロードすることで、スタイル定義を更新（Version管理）。

### 3.3 ワークフロー生成 (Generation Layer)
LangGraphを用いて以下のStateを遷移させる。

1.  **Intent Analysis Node**: 入力テーマと思想マップを照合し、記事の「コア・メッセージ」を定義。
2.  **Angle Planning Node**: 4媒体ごとの切り口（Angle）を策定。
    *   *Qiita*: How-to, 実装詳細, エラー解決
    *   *Zenn*: 概念理解, 知見共有, 技術書的アプローチ
    *   *note*: ポエム, 背景ストーリー, マネジメント視点
    *   *Owned*: SEO, CV誘導, 権威性
3.  **Drafting Node (Parallel)**: 定義された切り口に基づき、4並列で本文生成。
4.  **Refinement Node**: プラットフォーム固有の記法（ZennのMessage記法など）やMarkdown構文の正規化。

### 3.4 UI/UX (Interaction Layer)
*   **Real-time Progress**: WebSocket/SSEを用い、LangGraphのノード遷移（「現在：Zennの構成案を作成中...」）をUIに進捗バーとして表示。
*   **Multi-View Preview**: タブ切り替えによるMarkdownプレビュー（Syntax Highlighting付き）。
*   **Export**: 個別ダウンロードおよび一括ZIPダウンロード機能。

---

## 4. データモデル設計 (Schema)

### Users Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `email` | String | Gmail |
| `created_at` | Timestamptz | |

### Identity_Docs Table (Vector Store)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `type` | Enum | skill/goal/knowledge |
| `content` | Text | MDの生テキスト |
| `embedding` | Vector(1536) | ベクトルデータ |

### Platform_Styles Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `platform` | Enum | qiita/zenn/note/owned |
| `rules` | JSONB | 抽出されたルール（口調、構成テンプレート等） |
| `version` | Integer | 学習バージョン |

### Projects Table
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `theme` | String | 入力テーマ |
| `status` | Enum | processing/completed/failed |
| `result_json` | JSONB | 生成された4記事のMDデータ |

---

## 5. API インターフェース定義

### `POST /api/v1/ingest/identity`
*   **Input**: Markdown Files (Multipart)
*   **Process**: Parse -> Chunk -> Embed -> Save to Supabase
*   **Output**: Success status

### `POST /api/v1/ingest/style`
*   **Input**: Platform, Markdown File
*   **Process**: Extract Style Rules (via LLM) -> Save JSON to DB
*   **Output**: Extracted Rules Summary

### `POST /api/v1/generate` (WebSocket推奨だがRESTの場合)
*   **Input**: `theme` (String)
*   **Process**: Trigger LangGraph Workflow
*   **Output**: `project_id`

### `WS /ws/generate/{project_id}`
*   **Stream**: Workflow events (Node change, Token stream)

---

## 6. 開発フェーズ (MVP Roadmap)

### Phase 1: Skeleton (Week 1-2)
*   Next.js + FastAPI + Supabaseの環境構築。
*   LangGraphの最小構成（入力→Claude→出力）の実装。
*   認証周り（Supabase Auth）の実装。

### Phase 2: Core Logic (Week 3-4)
*   pgvectorを用いたRAG（思想注入）の実装。
*   4媒体別のプロンプトエンジニアリングとLangGraph分岐の実装。
*   MDファイルアップロードと解析処理の実装。

### Phase 3: UI Integration (Week 5)
*   リアルタイム進捗表示の実装。
*   Markdownプレビューワーの実装。
*   ダウンロード機能の実装。

---

## 7. 差別化と品質担保への注記

*   **「学習」の定義**: ファインチューニングではなく、**「RAG（検索拡張生成）による文脈注入」** と **「Few-shot Prompting（構成例の提示）」** の組み合わせとする。これが最もコストパフォーマンスが良く、最新モデルへの追従も容易である。
*   **トークンコスト管理**: 入力テキスト量が増えるため、LangGraphの各ノードで渡すコンテキストを厳選（不要な知識マップはフィルタリングする）ロジックを挟むこと。

---

**Next Action:**
この仕様に基づき、まずは `docker-compose.yml` (ローカル開発用DB) と `requirements.txt` (FastAPI/LangGraph依存関係) の作成から開始することを推奨する。
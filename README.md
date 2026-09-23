# roadmap-sh-fastapi

FastAPI の学習リポジトリ。教材は `docs/`、本編アプリは `app/`、
roadmap.sh のプロジェクト成果物は `projects/`。

## 到達点

TODO API を作り、次がすべて満たせる状態にする。

1. CRUD 4種が curl で動く
2. 不正入力で 422 が返る
3. SQLAlchemy 2.0（ORM）経由で Docker 上の MySQL に永続化され、Alembic でスキーマを
   変更できる。1対多のリレーションを辿れ、N+1 が起きていることに気づける
4. 未認証で 401、他人のリソースに 403 が返る
5. CORS が通り、全リクエストがログに残る
6. pytest が全ケース green になる
7. ruff / mypy / pytest がコミット時に自動で回り、すべて通る
8. Zed からブレークポイントを張り、実行中のリクエストを止めて変数を覗ける
9. 上の力で roadmap.sh のプロジェクト3件を自力で完成できる
10. `/openapi.json` を jq で読んで構造を説明でき、Swagger UI から認証付きで
    エンドポイントを実行できる

## 使い方

教材はモード制で、1回に1つずつ生成する。

```
docs/_prompt.md を読んで、M0 を実行して
```

以降は `M1: P1 ステップ1`、フェーズ末に `M2: P1`、
プロジェクト回は `MP: PJ1`。詳細は `docs/_prompt.md` §1。

## 進捗

| Ph | 内容 | 状態 | プロジェクト |
|---|---|---|---|
| P1a | 品質ゲート + FastAPI 基礎（ルーティング / Pydantic） | **P1-1 完了**（5ステップ中1） | — |
| P1b | OpenAPI と Swagger UI の読み方 / DI / デバッガ | 未着手 | — |
| P2 | 環境と設定（Docker MySQL / pydantic-settings） | 未着手 | — |
| P3 | ORM で永続化（SQLAlchemy 2.0 / Alembic） | 未着手 | — |
| P4 | 認証・認可（OAuth2 + JWT）+ リレーションと N+1 | 未着手 | PJ1 |
| P5 | ミドルウェア層（CORS / ログ / 例外） | 未着手 | — |
| P6 | テスト（pytest / TestClient） | 未着手 | PJ2 |
| 総仕上げ | — | 未着手 | PJ3 |

**次の一手**: `M1: P1 ステップ2`（最小のエンドポイント `GET /health`）

教材は `docs/p1a-basics.md`。

## メモ

- 学習計画は `docs/00-plan.md`、Python 文法の逆引きは `docs/90-python-index.md`
- ブランクページ再現は**翌日**にやる
- ステップごとにコミットする
- エラーが出たら 15 分は自分で粘ってから聞く

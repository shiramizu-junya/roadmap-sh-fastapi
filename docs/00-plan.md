# M0 — 学習計画（FastAPI 実践型教材）

> このファイルは **学習計画のみ**。本編（コードと解説）は `docs/p1-*.md` 以降に、M1 で1ステップずつ書く。

**検証環境**（以降すべての `✅ 検証済み` ラベルはこの環境を指す）

| 項目 | 値 | 確認方法 |
| --- | --- | --- |
| OS | macOS (darwin 25.6.0 / arm64) | — |
| Python | 3.12.13（uv 管理） | `uv run python -V` |
| uv | 0.10.9 | `uv --version` |
| FastAPI | 0.141.1 | 下記 N-2 の確認コマンド |
| Pydantic | 2.13.5 | 同上 |
| Starlette | 1.6.0 | 同上 |
| Docker Engine | 29.6.1 | `docker info --format '{{.ServerVersion}}'` |
| Docker Compose | v5.2.0 | `docker compose version` |
| MySQL | 8.x（P2 で `compose.yaml` から取得） | P2-1 で確認 |

---

## 1. 到達点の確認 — どの条件がどこで満たされるか

| # | 達成条件 | 満たされるステップ | 検証手段 |
| --- | --- | --- | --- |
| (1) | CRUD 4種が `curl` で動く | **P1-5** 終了時（メモリ上）／ **P3-4** 終了時（MySQL 永続化） | `curl -X POST/GET/PUT/DELETE` の実レスポンス |
| (2) | 不正入力で 422 が返る | **P1-4** | `curl` で型違反を送り、`loc` / `type` / `msg` を読む |
| (3) | Docker 上の MySQL に永続化され、Alembic でスキーマを変更できる | **P3-5** | `docker compose ps` が healthy ／ `alembic upgrade head` 後に `SHOW COLUMNS` ／ `alembic downgrade -1` で戻る |
| (4) | 未認証で 401、他人のリソースに 403 | **P4-4**（401）／ **P4-5**（403） | トークン無しで `curl` → 401 ／ 他ユーザーの TODO を叩く → 403 |
| (5) | CORS が通り、全リクエストがログに残る | **P5-1**（CORS）／ **P5-2**（ログ） | `curl -X OPTIONS` でプリフライト応答 ／ 標準出力のログ行 |
| (6) | pytest が全ケース green | **P6-4** | `uv run pytest -q` |

> 条件 (1) は2回満たす。P1 では「メモリ上の list」で動かし、P3 で中身を MySQL に差し替える。**外から見た振る舞いを変えずに内部を入れ替える**ことが P3 の主題なので、P1 で書いた `curl` がそのまま回帰テストになる。

---

## 2. 環境準備

アプリはローカル（Python 3.12 / uv）、DB のみ Docker Compose。ここでは **P1 を始められる状態**までを作る。MySQL の起動は P2-1 で行う。

### 2-1. uv プロジェクトを作る

```bash
# プロジェクトのルートで実行
uv init --python 3.12     # pyproject.toml / .python-version / main.py / README.md を生成
rm main.py                # 本教材は app/ パッケージ構成にするため、雛形の単一ファイルは消す
uv add "fastapi[standard]"  # FastAPI 本体 + uvicorn + httpx + pydantic-settings などの標準セットを追加
```

✅ 検証済み: Python 3.12.13 / uv 0.10.9（`pyproject.toml`・`uv.lock`・`.venv/` が生成されることを確認）

| コマンド | 役割 |
| --- | --- |
| `uv init --python 3.12` | プロジェクト定義（`pyproject.toml`）と使う Python のバージョン固定（`.python-version`）を作る。`npm init` + `.nvmrc` に相当 |
| `uv add "fastapi[standard]"` | 依存を `pyproject.toml` に追記し、`.venv/` に入れ、`uv.lock` に正確なバージョンを刻む。`npm install` が `package.json` と `package-lock.json` を同時に更新するのと同じ |
| `uv run <cmd>` | `.venv/` を有効化した状態で `<cmd>` を実行する。`source .venv/bin/activate` を毎回書かずに済む |

> 🧩 **周辺注**: `[standard]` は FastAPI の**オプション依存グループ**。本体だけでは開発サーバも HTTP クライアントも入らないため、本教材では最初から `[standard]` を入れる。
> 根拠: https://fastapi.tiangolo.com/#installation

### 2-2. 入ったバージョンを確認する

```bash
uv run python -c "
import sys, fastapi, pydantic, starlette
print('python  ', sys.version.split()[0])
print('fastapi ', fastapi.__version__)
print('pydantic', pydantic.VERSION)
print('starlette', starlette.__version__)
"
```

✅ 検証済み: 実際の出力

```
python   3.12.13
fastapi  0.141.1
pydantic 2.13.5
starlette 1.6.0
```

> **なぜ Starlette と Pydantic のバージョンも見るのか**: FastAPI は自前で HTTP を処理していない。ルーティング・ミドルウェア・`Request` / `Response` は **Starlette**、型の検証とシリアライズは **Pydantic** の仕事。エラーメッセージもこの2つの名前で出る。仕組み解剖では毎回「どのライブラリの責務か」を書くので、最初にこの3層を見ておく。

### 2-3. `.gitignore` を置く

```gitignore
# .gitignore
.venv/
__pycache__/
*.py[cod]
.env        # P2 で作る。DB のパスワードを含むためコミットしない
.DS_Store
```

✅ 検証済み: `git status --short` に `.venv/` と `__pycache__/` が現れないことを確認

> `uv init` は空のディレクトリなら `.gitignore` も作るが、**既に `.git` があるリポジトリでは作らない**。本リポジトリは後者だったため手動で置いた。

### 2-4. Docker が使えることを確認する

```bash
docker info --format '{{.ServerVersion}}'   # デーモンが動いているか（動いていなければここでエラー）
docker compose version                      # compose v2 系のサブコマンドが使えるか
docker run --rm hello-world                 # 実際にコンテナを1つ起動して捨てられるか
```

✅ 検証済み: 出力は順に `29.6.1` / `Docker Compose version v5.2.0` / `Hello from Docker!`

| コマンド | 役割 |
| --- | --- |
| `docker info` | Docker Desktop（デーモン）が起動しているかの判定。**未起動なら `Cannot connect to the Docker daemon` が出る** |
| `docker compose version` | `compose.yaml` を扱うのは `docker compose`（v2、サブコマンド）。古い `docker-compose`（v1、別バイナリ）ではない |
| `docker run --rm hello-world` | イメージの pull と起動が通ることの最小確認。`--rm` は終了時にコンテナを捨てる指定 |

> 🔓 **教材用の簡略化**: ここでは Docker を「MySQL を用意する手段」としてだけ使う。アプリ自身のコンテナ化（`Dockerfile`）は本教材の範囲外で、M3 の「カバーしていないこと」に回す。
> **本番では**: アプリもイメージにして同じ成果物をどの環境にも配る。
> 根拠: https://docs.docker.com/language/python/containerize/

### 2-5. この時点での到達状態

- `uv run python -c "import fastapi"` がエラーなく通る
- `docker run --rm hello-world` が通る
- まだ `app/` も `compose.yaml` も存在しない（P1-1 と P2-1 で作る）

---

## 3. 完成時のディレクトリ構成（P6 終了時点）

先に全体像を示す。各ステップは**この図のどこを埋めているか**を毎回明示する。

```text
roadmap-sh-fastapi/
├── pyproject.toml              # 依存の宣言（P1-1 以降、各フェーズで uv add が追記）
├── uv.lock                     # 依存の正確なバージョン
├── .python-version             # 3.12
├── .gitignore
├── README.md                   # uv init が生成
├── .env                        # DB 接続情報・JWT 秘密鍵（コミットしない）  [P2-2]
├── .env.example                # キー名だけのテンプレート（コミットする）    [P2-2]
├── compose.yaml                # MySQL 8.x のみ定義                        [P2-1]
├── alembic.ini                 # Alembic の設定                            [P3-2]
├── alembic/
│   ├── env.py                  # target_metadata にモデルを繋ぐ            [P3-2]
│   ├── script.py.mako
│   └── versions/
│       ├── xxxx_create_todos.py        [P3-2]
│       ├── xxxx_create_users.py        [P4-1]
│       └── xxxx_add_due_date.py        [P3-5]
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI() の生成・ルータ登録・ミドルウェア [P1-1 → P5-3]
│   ├── config.py               # pydantic-settings の Settings             [P2-2]
│   ├── database.py             # engine / SessionLocal / Base              [P3-1]
│   ├── dependencies.py         # get_db / get_current_user                 [P3-1, P4-3]
│   ├── security.py             # パスワードハッシュ・JWT の生成と検証      [P4-1, P4-2]
│   ├── models/                 # ★ DB のテーブル定義（SQLAlchemy）
│   │   ├── __init__.py
│   │   ├── todo.py                     [P3-2]
│   │   └── user.py                     [P4-1]
│   ├── schemas/                # ★ API の入出力の形（Pydantic）
│   │   ├── __init__.py
│   │   ├── todo.py                     [P1-3, P3-3]
│   │   ├── user.py                     [P4-1]
│   │   └── token.py                    [P4-2]
│   ├── crud/                   # DB 操作をハンドラから切り離す
│   │   ├── __init__.py
│   │   ├── todo.py                     [P3-4]
│   │   └── user.py                     [P4-1]
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── todos.py                    [P1-6]
│   │   ├── users.py                    [P4-1]
│   │   └── auth.py                     [P4-2]
│   └── exceptions.py           # 例外ハンドラの一元化                      [P5-3]
├── tests/
│   ├── conftest.py             # fixture・依存差し替え・テスト用DB          [P6-1 → P6-3]
│   ├── test_health.py                  [P6-1]
│   ├── test_todos.py                   [P6-2]
│   └── test_auth.py                    [P6-4]
└── docs/
    ├── 00-plan.md              # このファイル
    ├── p1-basics.md            # P1 の全ステップ + フェーズ末パック
    ├── p2-environment.md
    ├── p3-persistence.md
    ├── p4-auth.md
    ├── p5-middleware.md
    ├── p6-testing.md
    └── 99-wrapup.md            # M3
```

⚠️ 未実行（これは P6 終了時の**予定図**であり、現時点で存在するのは `pyproject.toml` / `uv.lock` / `.python-version` / `.gitignore` / `README.md` / `docs/00-plan.md` のみ。検証手順: 各ステップ末で `find . -not -path './.venv/*' -not -path './.git/*' -type f | sort` を実行し、この図との差分を確認する）

**`models/` と `schemas/` を最初から分けている理由**: P3 の主題が「テーブルの形」と「API の形」を別物として扱うことだから。同じ `Todo` でも、DB には `hashed_password` のような外に出してはいけない列があり、API には DB に無い計算済みフィールドがある。1クラスに兼ねさせると、この差が表現できない。

> 🔄 **素材からの変更**: 公式チュートリアルは単一ファイル + SQLite + SQLModel。本教材は `app/` パッケージ分割 + Docker 上の MySQL + SQLAlchemy 2.0 に置き換えた。理由は、P4 で複数ルータが同じ依存を共有し、P6 でテスト用に DB を差し替えるため。単一ファイルではこの2つが表現できない。
> 根拠: https://fastapi.tiangolo.com/tutorial/bigger-applications/

---

## 4. フェーズ別ステップ一覧

**粒度のルール**: 1ステップの FastAPI 側初出は最大3つ。Python 注・周辺注は数に含めない。

### P1 — FastAPI 基礎（データはメモリ上）／ 6ステップ

| # | タイトル | 作るもの | 初出（FastAPI） | 重要度 |
| --- | --- | --- | --- | --- |
| P1-1 | 最小のエンドポイント | `GET /health` が `{"status":"ok"}` と 200 を返す | `FastAPI()`, `@app.get()`, `fastapi dev` | 🔴 |
| P1-2 | 一覧と単体取得 | `GET /todos` と `GET /todos/{todo_id}`（メモリ上の list） | パスパラメータ宣言, `Annotated[... , Query()]`, `HTTPException` | 🔴 |
| P1-3 | 作成とレスポンスの形 | `POST /todos` が 201 で作成済み TODO を返す | `BaseModel`（ボディ判定）, 戻り値アノテーション（レスポンスモデル）, `status_code=201` | 🔴 |
| P1-4 | 検証を締めて 422 を読む | `title` の長さ制約・独自ルールで 422 | `Field()`, `field_validator`, 422 ボディの `loc`/`type`/`msg` | 🔴 |
| P1-5 | 更新と削除（CRUD 完成） | `PUT /todos/{id}` と `DELETE /todos/{id}`（204） | `@app.put` / `@app.delete`, `status.HTTP_204_NO_CONTENT`, `Response` | 🔴 |
| P1-6 | ルータ分割と依存性注入 | `app/routers/todos.py` に分離し、共通処理を注入 | `APIRouter`, `include_router`, `Depends()` | 🔴 |

**この並びの理由**: 「読む（GET）→ 書く（POST）→ 検証を効かせる → 残りの動詞 → 構造化」。検証（P1-4）を作成（P1-3）の直後に置くのは、**422 が返る条件を自分で作ってから 422 のボディを読む**ほうが、エラーの形が記憶に残るため。

### P2 — 環境と設定 ／ 3ステップ

| # | タイトル | 作るもの | 初出（FastAPI） | 重要度 |
| --- | --- | --- | --- | --- |
| P2-1 | Docker Compose で MySQL を起動する | `compose.yaml`（MySQL 8.x のみ）が healthy になる | なし（周辺: `healthcheck`, `volumes`, `environment`） | ⚪ |
| P2-2 | 設定をコードから追い出す | `app/config.py` の `Settings` と `.env` / `.env.example` | `BaseSettings`, `SettingsConfigDict`, `Depends(get_settings)` | 🔴 |
| P2-3 | 起動時に DB 接続を確かめる | `lifespan` で接続を試し、`GET /health/db` を返す | `lifespan`, `app.state`, 503 の返し方 | 🟡 |

**P2 を P3 より前に置く理由**: DB 接続情報（ホスト・ユーザー・パスワード）はコードに直書きできない。永続化を先にやると、接続文字列をハードコードしてから設定管理に書き直すことになる。**一度書いたコードを書き直させない**ための順序。

**P2 で必ず 🔓 を付ける箇所**（§4.8）: DB 認証情報の置き場所 ／ root ユーザー利用 ／ `volumes` によるデータ永続化の有無 ／ 本番で managed DB を選ぶ選択肢。

### P3 — 永続化 ／ 5ステップ

| # | タイトル | 作るもの | 初出（FastAPI） | 重要度 |
| --- | --- | --- | --- | --- |
| P3-1 | 同期で統一する／セッションの寿命 | `app/database.py` の engine・`SessionLocal`、`get_db` 依存 | `def` ハンドラとスレッドプール（§4.7 をここで1回だけ）, `yield` 依存の後処理タイミング | 🔴 |
| P3-2 | モデル定義と最初のマイグレーション | `app/models/todo.py` と `alembic/`、`todos` テーブル | なし（周辺: `DeclarativeBase`, `Mapped`, `alembic upgrade head`） | 🔴 |
| P3-3 | モデルとスキーマを分ける | `app/schemas/todo.py` を ORM オブジェクトから作れるようにする | `ConfigDict(from_attributes=True)`, レスポンスモデルによる ORM→JSON 変換 | 🔴 |
| P3-4 | CRUD をメモリから DB に差し替える | `app/crud/todo.py`、P1 の `curl` が全部そのまま通る | `Session` とトランザクション境界（commit / rollback の位置） | 🔴 |
| P3-5 | スキーマ変更を安全に当てる | `due_date` 列を追加し、`downgrade -1` で戻せる | なし（周辺: `revision --autogenerate`, `downgrade`, `VARCHAR` 長さ必須） | 🟡 |

**P3-1 を最初に置く理由**: `def` と `async def` の選択（§4.7）と `Session` の寿命は、以降すべてのハンドラの書き方を決めてしまう。**モデルを書く前に器の設計を確定させる**。

### P4 — 認証・認可 ／ 5ステップ

| # | タイトル | 作るもの | 初出（FastAPI） | 重要度 |
| --- | --- | --- | --- | --- |
| P4-1 | ユーザーとパスワードハッシュ | `users` テーブル、`POST /users` で登録 | なし（周辺: bcrypt。FastAPI 側は P1-3 の再利用） | 🔴 |
| P4-2 | トークンを発行する | `POST /token` がアクセストークンを返す | `OAuth2PasswordRequestForm`, フォーム形式のボディ判定, JWT の `sub` / `exp` | 🔴 |
| P4-3 | トークンを検証して現在のユーザーを得る | `get_current_user` 依存 | `OAuth2PasswordBearer`, 依存の入れ子, 401 と `WWW-Authenticate` ヘッダ | 🔴 |
| P4-4 | エンドポイントを保護する（401） | TODO 系すべてを認証必須にする | `Annotated[User, Depends(get_current_user)]`, ルータ単位の `dependencies=[...]` | 🔴 |
| P4-5 | 認可 — 他人のリソースに 403 | `owner_id` で所有者を判定し 403 | 403 と 404 の使い分け, 認証と認可の依存を分ける設計 | 🔴 |

**P4-4 と P4-5 を分ける理由**: 「誰か（認証）」と「その人が触ってよいか（認可）」は別の判断で、依存も別にすべき。1ステップにまとめると `get_current_user` の中で所有者チェックまでやる設計になり、リソースごとにルールが違う場合に破綻する。

**P4 で必ず 🔓 を付ける箇所**（§4.8）: 秘密鍵の管理 ／ トークン有効期限 ／ リフレッシュトークンの有無 ／ ハッシュアルゴリズムとコスト ／ HTTPS 前提 ／ ログに出さないもの。
この5ステップは **(b) 根拠URL を他より厳しく適用する**（JWT は RFC 7519、パスワード保存は OWASP）。

### P5 — ミドルウェア層 ／ 3ステップ

| # | タイトル | 作るもの | 初出（FastAPI） | 重要度 |
| --- | --- | --- | --- | --- |
| P5-1 | CORS を通す | ブラウザの別オリジンから叩けるようにする | `CORSMiddleware`, `add_middleware`, プリフライト（`OPTIONS`）の扱い | 🔴 |
| P5-2 | 全リクエストをログに残す | メソッド・パス・ステータス・所要時間・リクエストID | `@app.middleware("http")`, `Request` / `call_next`, ミドルウェアの実行順 | 🟡 |
| P5-3 | 例外ハンドラを一元化する | 422 とアプリ独自例外のレスポンス形式を揃える | `@app.exception_handler`, `RequestValidationError`, `JSONResponse` | 🟡 |

**P5 で必ず 🔓 を付ける箇所**（§4.8）: `allow_origins` にワイルドカードを使っていないか ／ ログに個人情報やトークンを出していないか。

### P6 — テスト ／ 4ステップ

| # | タイトル | 作るもの | 初出（FastAPI） | 重要度 |
| --- | --- | --- | --- | --- |
| P6-1 | pytest と TestClient | `tests/test_health.py` が green | `TestClient`, pytest の fixture, `uv add --dev` | 🔴 |
| P6-2 | 依存を差し替える | DB 依存を偽物に置き換えて CRUD をテスト | `app.dependency_overrides` | 🔴 |
| P6-3 | テスト用 DB を分離する | 本番用スキーマを汚さずに実 DB でテスト | `conftest.py` の fixture スコープ, トランザクションのロールバック | 🟡 |
| P6-4 | 認証付きエンドポイントのテスト | 401 / 403 / 正常系を網羅して全ケース green | 認証依存の上書き, `@pytest.mark.parametrize` | 🟡 |

**P6-2 と P6-3 を分ける理由**: 依存差し替え（速いが本物の SQL を検証しない）と実 DB（遅いが本物）の**両方**を持っておくのが実務の形。片方だけ教えると、もう片方が必要になったときに設計を作り直すことになる。

### ステップ数の総計

| Ph | ステップ数 | 目安 | 判定 |
| --- | --- | --- | --- |
| P1 | 6 | 5〜6 | 範囲内 |
| P2 | 3 | 3 | 範囲内 |
| P3 | 5 | 5 | 範囲内 |
| P4 | 5 | 4〜5 | 範囲内 |
| P5 | 3 | 3 | 範囲内 |
| P6 | 4 | 3〜4 | 範囲内 |
| 合計 | **26** | — | どのフェーズも7ステップを超えないため、分割提案は不要 |

M2（フェーズ末パック）は各フェーズの末尾で計6回、M3（締め）は最後に1回。呼び出し総数は 26 + 6 + 1 = 33 回。

---

## 5. 範囲外の予告

`【範囲の外枠】` の5つの目次と、上の26ステップを突き合わせた差分。**ここでは項目名だけ**を挙げる。理由と一次情報URLは M3 で表にする。

### FastAPI（https://fastapi.tiangolo.com/learn/）

WebSocket ／ `BackgroundTasks` ／ 静的ファイル配信と `Jinja2Templates` ／ `StreamingResponse` / `FileResponse` などのカスタムレスポンス ／ OAuth2 スコープによる細かい権限分け ／ サブアプリケーションのマウント ／ リバースプロキシ配下での運用（`root_path`）／ GraphQL ／ WSGI アプリの同居 ／ OpenAPI 定義のカスタマイズ

### Pydantic（https://docs.pydantic.dev/latest/）

シリアライズのカスタマイズ（`field_serializer` / `model_serializer`）／ ジェネリックモデル ／ 判別可能ユニオン ／ `model_validator`（フィールド横断の検証）／ Pydantic dataclasses ／ JSON Schema の手動調整 ／ カスタム型と `Annotated` の高度な使い方

### Starlette（https://www.starlette.io/）

ASGI プロトコルそのものの仕様 ／ `Route` / `Mount` を直接使う低レベルルーティング ／ `GZipMiddleware` / `TrustedHostMiddleware` / `SessionMiddleware` ／ `BackgroundTask`（Starlette 側）／ ピュア ASGI ミドルウェアの書き方

### SQLAlchemy 2.0（https://docs.sqlalchemy.org/en/20/）

`relationship()` とリレーション（1対多・多対多）／ 遅延ロード戦略と N+1 問題 ／ Core（`select()` 直書き）と ORM の使い分け ／ コネクションプールのチューニング ／ **非同期エンジン（`AsyncSession`）** ／ ハイブリッドプロパティ ／ イベントフック

### Alembic（https://alembic.sqlalchemy.org/en/latest/）

ブランチとマージ ／ オフラインモード（SQL スクリプト出力）／ バッチ操作 ／ 複数データベースの同時管理 ／ 自動生成のカスタマイズ（`compare_type` など）

### 目次に無いが明示的に範囲外とするもの（§8.2 により M3 で必ず扱う）

1. **非同期 DB アクセス** — 本教材は同期ドライバで統一する（§4.7）
2. **アプリ側のコンテナ化** — Docker は MySQL を用意する手段としてのみ使う
3. **CI**（GitHub Actions などでの自動テスト実行）

---

## 6. 次のアクション

```text
M1: P1 ステップ1
```

⚠️ 未実行（これは実行するコマンドではなく、次に私へ渡す**モード呼び出し**）

で本編を開始する。出力先は `docs/p1-basics.md`。

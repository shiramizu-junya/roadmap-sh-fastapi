# P1 — FastAPI 基礎（データはメモリ上）

---

## P1-1: 最小のエンドポイント

**作るもの**: `GET /health` が 200 と `{"status":"ok"}` を返す
**重要度**: 🔴 毎日使う — `FastAPI()` とパスオペレーションデコレータは、どのエンドポイントを書くときも必ず最初に書く2行だから
**前ステップとの接続**: 最初のステップ。M0 の環境準備（`uv add "fastapi[standard]"` まで）が済んでいる前提

### 1-0. このステップの初出トークン

**FastAPI**: `FastAPI()` / `@app.get()` / `fastapi dev`（3）
**Python**: `from ... import` / `def` / dict リテラル
**周辺**: なし

### 1-1. コード

初出（登場回数1回目）なので**完成コード全文**を出す。ファイルは2つ。

**① `app/__init__.py`** — 中身は空でよい。

**② `app/main.py`** — 全文

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health():
    # 死活確認。アプリが起動してリクエストを処理できることだけを返す
    return {"status": "ok"}
```

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Starlette 1.6.0
（このコードで `uv run fastapi dev app/main.py` を起動し、`curl -i http://127.0.0.1:8000/health` が `HTTP/1.1 200 OK` + `{"status":"ok"}` を返すことを確認済み）

| 行 | 何をしているか |
| --- | --- |
| `from fastapi import FastAPI` | `FastAPI` クラスだけを取り込む |
| `app = FastAPI()` | アプリ本体を1個作る。**この時点で経路は0本** |
| `@app.get("/health")` | 直下の関数を「`GET /health` の担当」として `app` に登録する |
| `def health():` | ハンドラ本体。引数なし |
| `return {"status": "ok"}` | dict を返す。JSON への変換は FastAPI がやる |

起動コマンド（`app/` と同じ階層で実行する）:

```bash
uv run fastapi dev app/main.py
```

✅ 検証済み: `Server started at http://127.0.0.1:8000` と表示され、127.0.0.1:8000 で LISTEN することを確認

### 1-2. 🔬 仕組み解剖

#### (a) `app = FastAPI()`

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `FastAPI()` | アプリケーションインスタンス | `FastAPI` は Starlette の `Starlette` クラスを継承したサブクラス。生成時に、空のルーティングテーブル（`app.router`）・既定の例外ハンドラ・OpenAPI スキーマの器を持った **ASGI アプリ**が1個できる |

- **いつ評価されるか**: `app/main.py` が import された瞬間、つまり**サーバ起動時に1回だけ**。リクエストごとではない
- **どのライブラリの責務か**: クラス定義と OpenAPI 生成は FastAPI、ASGI アプリとしての実体とルーティングは Starlette
- **失敗したらどうなるか**: この行で失敗するのは引数の型が不正な場合などで、**起動時に例外を出してプロセスが終わる**。リクエストは1本も受け付けない。つまり「起動したのにエラー」と「起動すらしない」は別の層の問題

**既知スタックとの対応**: Express の `const app = express()` に近い。違いは、`FastAPI()` が同時に **OpenAPI スキーマの器**を持つこと（Express にはこれが無く、`swagger-jsdoc` などを別に足す）。React に対応物なし。

**なぜこの設計なのか**: アプリをモジュールレベルの変数として置くことで、起動側は `app.main:app` という**文字列**だけを頼りに実体を取りに行ける。設定ファイルでアプリを組み立てて返す方式もあるが、文字列1本のほうが `fastapi dev` / `uvicorn` / `gunicorn` / テストコードのどこからでも同じ書き方で参照できる。

#### (b) `@app.get("/health")`

**正式名称**: **パスオペレーションデコレータ**（path operation decorator）。`/health` が *path*、`get` が *operation*。

**実行時に何が起きるか** — 2つの時点に分けて読む。

- **起動時（import 時）**: まず `app.get("/health")` が呼ばれてデコレータ関数が返り、それが直下の `health` 関数を引数にして呼ばれる。その中で FastAPI は
  1. `health` の**関数シグネチャを読み取り**（引数・型アノテーション・戻り値アノテーション）、
  2. そこからパラメータ仕様とレスポンス仕様を組み立て、
  3. `APIRoute` オブジェクトを作って `app.router.routes` に**追加**する。
  この間、**`health()` 自体は1度も呼ばれない**
- **リクエスト時**: Starlette が `app.router.routes` を**登録順に**走査し、パスとメソッドが一致した最初の `APIRoute` を選ぶ。一致したら FastAPI が引数を組み立てて `health()` を呼び、戻り値を JSON にして返す

- **どのライブラリの責務か**: 経路の**登録**と関数シグネチャの解釈は FastAPI、経路の**探索**と ASGI の受け渡しは Starlette、引数の検証は Pydantic（このステップは引数が無いので出番なし）
- **失敗したらどうなるか**: どの経路にも一致しなければ Starlette が **404** `{"detail":"Not Found"}`。パスは一致するがメソッドが違えば **405** `{"detail":"Method Not Allowed"}`。どちらも `health()` は呼ばれない

**既知スタックとの対応**: Express の `app.get('/health', handler)` と登録の形はほぼ同じ。**決定的な違いは、FastAPI が登録時に関数のシグネチャを読んで仕様を先に確定させる点**。Express はハンドラの中身を一切見ないので、入出力の仕様はコメントか別ファイルに書くしかない。React に対応物なし。

**なぜこの設計なのか**: 「経路の宣言」と「処理の実装」を1箇所に置くため。ルーティング表を別ファイルに持つ方式（Django の `urls.py` など）は全経路の一覧性が高い代わりに、経路と関数の対応がコードの2箇所に分かれて片方だけ直す事故が起きる。FastAPI は一覧性のほうを捨て、それを `/docs`（OpenAPI から自動生成される画面）で埋め合わせている。

> 💡補足（`@` そのものについて / §4.3 の例外）: `@f` を関数定義の直前に書くと、`def g(): ...` の定義後に `g = f(g)` が実行される。つまり**デコレータは「関数を受け取って何かする関数」**にすぎず、特別な構文糖でしかない。FastAPI の場合、`app.get("/health")` の戻り値が「関数を受け取り、ルートに登録して、その関数をそのまま返す」関数になっている。**元の関数は書き換えられていない**ので、`health()` は普通の Python 関数として直接呼ぶこともテストすることもできる。

#### (c) `fastapi dev app/main.py`

**正式名称**: FastAPI CLI の開発サーバ。指定ファイルから `app` を探して import 文字列（ここでは `app.main:app`）を解決し、**uvicorn を自動リロード有効で起動**する。ファイル変更の監視は watchfiles が行い、変更のたびにプロセスを再起動する。

- **失敗したらどうなるか**: ポートが埋まっていれば `ERROR: [Errno 48] Address already in use` を出して**終了コード 3** で落ちる（サーバは起動しない）

**既知スタックとの対応**: `vite dev` / `next dev` と同じ位置づけ。**本番用は別コマンド `fastapi run`** である点も同じ（`vite build` + `vite preview` の関係に近い）。

**なぜこの設計なのか**: リロード監視は開発中だけ必要なコストなので、開発と本番でコマンドを分けている。
根拠: https://fastapi.tiangolo.com/fastapi-cli/

### 1-3. 🐍 Python注 ／ 🧩 周辺注

> 🐍 **Python注**: `from fastapi import FastAPI` は「`fastapi` の中の `FastAPI` だけを取り込む」。TS の `import { FastAPI } from "fastapi"` と同じ。

> 🐍 **Python注**: `def` は関数定義。`:` の後、**インデントされた範囲**が中身（`{}` を使わない）。

> 🐍 **Python注**: `{"status": "ok"}` は dict リテラル。JS のオブジェクトリテラルと見た目は同じだが、**キーも `"` で囲む**（`{status: "ok"}` は書けない）。

> 🧩 **周辺注**: このステップでは Docker / MySQL / Alembic を使わない。

### 1-4. 解説 — なぜこう設計するか

**なぜ単一ファイルではなく `app/` パッケージから始めるのか。** 公式チュートリアルは `main.py` 1枚で始める。本教材が最初から `app/` を切るのは、P1-6 でルータを分割し、P3 で `app.database`、P6 で `tests/` から `app.main` を import するときに、**パッケージの形を後から変えると import パスが全部壊れる**ため。`app/__init__.py` は「このディレクトリはパッケージだ」という印で、これがあることで `app.main:app` という点区切りの参照が成立する。

**なぜ `async def` ではなく `def` なのか。** FastAPI は両方書ける。ここでは外部を何も待たない処理なので `def` にしている。判断基準は「好み」ではなく「そのハンドラが何を待つか」で、この選択が実際に効いてくるのは DB を触り始める P3 から。

> ⏭️ **後で回収**: `def` と `async def` の使い分け（および同期 I/O を `async def` に入れると何が壊れるか）は **P3-1** で仕組み解剖として扱う。今は「外部を待たない処理は `def` でよい」とだけ理解して進む。

> ⏭️ **後で回収**: dict を返すと JSON になる変換の詳細（および戻り値の型を宣言して出力の形を絞る方法）は **P1-3** で扱う。

> 🧠 **FastAPI の考え方**: 「起動時に宣言を読んで仕様を組み立てる」段階と、「リクエストごとに組み立て済みの仕様で処理する」段階は別物。エラーがどちらで出たのかを見分けられると、原因の半分は絞れる。

### 1-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: 死活確認は **DB など外部依存を触らない**形で1本持つ。コンテナオーケストレータの liveness probe はこれを定期的に叩き、失敗が続くとコンテナを再起動する。DB 断でアプリまで再起動されると復旧が遅れるため、依存を含む確認は別経路に分ける（本教材では P2-3 の `/health/db`）。
> 根拠: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

> ⚠️ **アンチパターン**: `fastapi dev` を本番で使わない。`--reload` 相当のファイル監視が常駐し、プロセス構成も開発向けに最適化されている。本番は `fastapi run` を使う。
> 根拠: https://fastapi.tiangolo.com/deployment/manually/

### 1-6. 🔮 予測 → 動作確認

**先に予想を書いてから叩く**（紙でもメモでもよい）。

1. `GET /healthz`（綴り違い）を叩くと、ステータスコードは何か。`health()` 関数は呼ばれるか。**どのライブラリ**がそのレスポンスを作るか
2. `POST /health` を叩くと何が返るか。404 か、それとも別のコードか
3. `http://127.0.0.1:8000/docs` を開くと何が表示されるか。その内容は**誰が**作ったか

---

**別ターミナルで実行する**（サーバは起動したままにしておく）。

```bash
curl -i http://127.0.0.1:8000/health
```

✅ 検証済み: 実際の出力

```http
HTTP/1.1 200 OK
date: Sun, 20 Sep 2026 05:08:51 GMT
server: uvicorn
content-length: 15
content-type: application/json

{"status":"ok"}
```

`server: uvicorn` と `content-type: application/json` に注目する。**どちらも自分では書いていない。** 前者は ASGI サーバが、後者は dict を JSON に変換した FastAPI が付けている。

```bash
curl -i http://127.0.0.1:8000/healthz     # 綴り違い
curl -i -X POST http://127.0.0.1:8000/health
```

⚠️ 未実行（上の2本は自分で確認すること）。期待される結果:

| リクエスト | 期待 | 理由 |
| --- | --- | --- |
| `GET /healthz` | `404` `{"detail":"Not Found"}` | どの `APIRoute` にも一致せず、**Starlette** が既定の 404 を返す。`health()` は呼ばれない |
| `POST /health` | `405` `{"detail":"Method Not Allowed"}` | パスは一致するがメソッドが違う。404 ではない点が重要 |

ブラウザで `http://127.0.0.1:8000/docs` を開く。

⚠️ 未実行（自分で確認すること）。期待される結果: `GET /health` が1件だけ並んだ Swagger UI が出る。**この画面は手で書いていない** — 1-2(b) の「起動時に関数シグネチャを読んで仕様を組み立てる」処理の副産物として、`/openapi.json` が生成され、それを Swagger UI が描画している。`curl http://127.0.0.1:8000/openapi.json` で元データも見られる。

### 1-7. ✅ 想起チェック

**Q1.** `@app.get("/health")` が実行されるのはいつか。そのとき `health()` は呼ばれるか。

<details><summary>答え</summary>

`app/main.py` が import された瞬間（＝サーバ起動時）に1回だけ実行される。そのとき FastAPI は `health` の**シグネチャを読んで `APIRoute` を作り、ルーティングテーブルに追加する**だけで、`health()` 自体は呼ばれない。`health()` が呼ばれるのは、実際に `GET /health` のリクエストが来てパスとメソッドが一致したとき。
</details>

**Q2.** `GET /healthz` の 404 を返しているのは FastAPI か Starlette か。そう言える理由は。

<details><summary>答え</summary>

**Starlette**。経路の探索（`app.router.routes` の走査）は Starlette の責務で、どれにも一致しなければ Starlette の既定の 404 ハンドラが `{"detail":"Not Found"}` を返す。FastAPI の出番は「一致した後」に引数を組み立てて関数を呼ぶところから。
</details>

**Q3.** `FastAPI()` は `app.py` の中で何回評価されるか。リクエストが 100 本来たら何回になるか。

<details><summary>答え</summary>

どちらも **1回**。モジュールの import 時に1回だけ評価され、以降は同じインスタンスが使い回される。リクエスト数とは無関係。この「起動時1回」と「リクエストごと」の区別は、P2 の設定読み込みと P3 の DB セッションでそのまま効いてくる。
</details>

### 1-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `FastAPI()` | 1-2(a) で仕組み解剖 |
| `@app.get()` | 1-2(b) で仕組み解剖 |
| `fastapi dev` | 1-2(c) で仕組み解剖 |
| `@`（デコレータ構文そのもの） | 1-2(b) の 💡補足 で厚く扱った（§4.3 の例外5つに該当） |
| `from ... import` | 1-3 で Python注 |
| `def` | 1-3 で Python注 |
| dict リテラル | 1-3 で Python注 |
| `def` と `async def` の使い分け | ⏭️ **P3-1** で回収（今は「外部を待たない処理は `def`」とだけ理解） |
| dict → JSON の変換 / 戻り値の型宣言 | ⏭️ **P1-3** で回収 |

---

## P1-2: 一覧と単体取得

**作るもの**: `GET /todos`（絞り込み・件数上限つき）と `GET /todos/{todo_id}`（無ければ 404）。データはメモリ上の list
**重要度**: 🔴 毎日使う — URL から値を受け取る2系統（パス／クエリ）と、エラーを返す手段は、どの API でも最初に必要になるから
**前ステップとの接続**: P1-1 の `GET /health` に、**引数を受け取るエンドポイント**を2本足す。`app/main.py` に追記する

### 2-0. このステップの初出トークン

**FastAPI**: パスパラメータ宣言 / `Annotated[..., Query()]` / `HTTPException`（3）
**Python**: `Annotated` / `list[dict]`・`bool | None` / リスト内包表記 / `raise` / スライス `[:n]`
**周辺**: なし

### 2-1. コード

3つとも初出（登場回数1回目）なので**完成コード全文**。`app/main.py` を**丸ごとこの内容に置き換える**（P1-1 の `health` も含まれている）。

```python
# app/main.py
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

# メモリ上の仮データ。P3 で MySQL に置き換える
_todos: list[dict] = [
    {"id": 1, "title": "牛乳を買う", "done": False},
    {"id": 2, "title": "docs を書く", "done": True},
    {"id": 3, "title": "散歩する", "done": False},
]


@app.get("/health")
def health():
    # 死活確認。アプリが起動してリクエストを処理できることだけを返す
    return {"status": "ok"}


@app.get("/todos")
def list_todos(
    done: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items = [t for t in _todos if done is None or t["done"] == done]
    return items[:limit]


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    for todo in _todos:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")
```

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Starlette 1.6.0
（このコードを `TestClient` で 10 パターン叩き、2-6 に載せた出力をすべて実測で確認した）

| 行 | 何をしているか |
| --- | --- |
| `_todos: list[dict] = [...]` | 仮のデータ置き場。**モジュール読み込み時に1回だけ**作られ、以降すべてのリクエストが同じ list を見る |
| `done: Annotated[bool \| None, Query()] = None` | クエリパラメータ。省略可（既定 `None` = 絞り込まない） |
| `limit: Annotated[int, Query(ge=1, le=100)] = 20` | クエリパラメータ。1〜100 の範囲検証つき、既定 20 |
| `@app.get("/todos/{todo_id}")` + `todo_id: int` | パステンプレートの `{todo_id}` と**同名の引数**が対応する |
| `raise HTTPException(...)` | `return` ではなく `raise`。処理を中断してエラーレスポンスにする |

### 2-2. 🔬 仕組み解剖

#### (a) 引数の分類規則 — FastAPI は「どこから来た値か」をどう決めるか

このステップの本質は個々の書き方ではなく、**FastAPI が関数の引数を3種類に振り分ける規則**にある。起動時に、引数を1つずつ次の順で判定する。

| 判定 | 分類 | 例 |
| --- | --- | --- |
| 1. 引数名がパステンプレート `{...}` に**ある** | **パスパラメータ** | `todo_id` |
| 2. 名前が無く、型が単純型（`int` / `str` / `bool` / `float` など） | **クエリパラメータ** | `done`, `limit` |
| 3. 名前が無く、型が Pydantic モデル | リクエストボディ（P1-3） | — |

- **いつ評価されるか**: この振り分けは**起動時（デコレータ評価時）に1回**。リクエストごとには、確定済みの仕様に従って値を詰めるだけ
- **どのライブラリの責務か**: 振り分けは FastAPI、URL からの値の切り出しは Starlette、型変換と検証は Pydantic

**この規則が事故になる形**（実測）: パステンプレートを `{todo_id}` と書いたのに引数名を `id` にすると、**起動時エラーにはならない**。規則1に当たらず規則2に落ちるので、`id` が**クエリパラメータ**として扱われ、パスの値は無視される。

```
GET /todos/5       -> 422 {"detail":[{"type":"missing","loc":["query","id"],...}]}
GET /todos/5?id=7  -> 200 {"id": 7}
```

✅ 検証済み: FastAPI 0.141.1（上の2行は実測出力）

`loc` の先頭が `"path"` ではなく **`"query"`** になっているのが手がかり。**422 が出たら `loc` の第1要素を必ず見る** — 値がどこから来る想定になっているかが分かる。

#### (b) `todo_id: int` — パスパラメータ

**正式名称**: パスパラメータ（path parameter）。

**実行時に何が起きるか**: Starlette が URL からセグメント（`/todos/2` なら `"2"`）を**文字列として**切り出す。FastAPI がそれを Pydantic に渡し、宣言された `int` へ変換させる。変換できれば `todo_id=2` として関数を呼び、できなければ**関数を呼ばずに 422** を返す。

- **失敗したらどうなるか**: `/todos/abc` → `422`、`{"type":"int_parsing","loc":["path","todo_id"],...}`

**既知スタックとの対応**: Express の `req.params.todo_id` は**常に string** で、`Number()` と `isNaN()` チェックを自分で書く。FastAPI は**型宣言がそのまま変換器と検証器を兼ねる**ので、関数の中に入った時点で `int` であることが保証されている。React に対応物なし。

**なぜこの設計なのか**: 「URL から来た値は文字列」という事実を、境界の1箇所（宣言）で吸収してしまうため。手で変換すると、変換忘れ・エラー時のレスポンス形式のばらつきが全エンドポイントに散る。

#### (c) `Annotated[int, Query(ge=1, le=100)] = 20` — クエリパラメータ

**正式名称**: クエリパラメータ + `Query()` による追加バリデーション。`Annotated` は Python 標準の「型にメタデータを添える」仕組みで、FastAPI 固有の機能ではない。

**実行時に何が起きるか**: 起動時に FastAPI が `Annotated` の中身を覗き、`Query(...)` を見つけて検証ルール（`ge` / `le`）を Pydantic のフィールド定義に組み込む。リクエスト時は、クエリ文字列の `limit=2` を `int` に変換し、範囲を検査してから関数へ渡す。`= 20` は**素の Python のデフォルト引数**なので、省略時は 20 が入る。

- **失敗したらどうなるか**: `?limit=0` → `422`、`{"type":"greater_than_equal","loc":["query","limit"],"ctx":{"ge":1}}`

**既知スタックとの対応**: NestJS の `@Query('limit') limit: number` に近い。ただし NestJS はデコレータで**引数の外側**から指定するのに対し、`Annotated` は**型そのものに**メタデータを畳み込む。zod の `.min(1).max(100)` は検証内容としては同じだが、スキーマを別に書く点が違う。

**なぜ `Annotated` で書くのか**: 古い書き方 `limit: int = Query(20, ge=1)` も動くが、こちらは**デフォルト値の置き場所が `Query()` の中**になり、`= Query(...)` が Python から見たデフォルト引数になってしまう。つまり `list_todos()` を普通の関数として直接呼ぶと、`limit` に `Query` オブジェクトが入る。`Annotated` 形式ならデフォルトは `= 20` のまま素の値なので、**関数がただの Python 関数のままでいられる**（P6 のテストで効く）。
根拠: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/

#### (d) `raise HTTPException(status_code=404, detail="Todo not found")`

**正式名称**: `fastapi.HTTPException`。Starlette の同名クラスを継承し、レスポンスヘッダを指定できるよう拡張したもの。

**実行時に何が起きるか**: 普通の Python 例外として送出され、ハンドラの実行はその場で中断する。Starlette に既定登録されている例外ハンドラがこれを捕まえ、`{"detail": <detail>}` という JSON を指定ステータスで返す。

- **どのライブラリの責務か**: 例外クラスの提供は FastAPI、捕捉とレスポンス化は Starlette の例外ミドルウェア
- **失敗したらどうなるか**: `HTTPException` 以外の例外が漏れると 500 になり、ボディは `Internal Server Error`（detail は出ない）

**既知スタックとの対応**: NestJS の `throw new NotFoundException()` がほぼ同型。Express の `res.status(404).json(...)` とは**発想が違う** — あちらは「レスポンスを書いて return する」、FastAPI は「例外を投げて中断する」。

**なぜ `return` ではなく `raise` なのか**: 深くネストした場所からでも、途中の関数に「エラーを上へ返す」責務を持たせずに中断できるため。P1-6 以降の依存関数（`Depends`）はハンドラの**前**に走るので、そこから 401 や 404 を返すには例外である必要がある。エラー形式を後から変えたくなったら、ハンドラ側を触らず例外ハンドラだけ差し替えればよい（P5-3 でやる）。
根拠: https://fastapi.tiangolo.com/tutorial/handling-errors/

### 2-3. 🐍 Python注 ／ 🧩 周辺注

> 🐍 **Python注**: `bool | None` は「bool か None」。TS の `boolean | null` と同じ。`list[dict]` は「dict の配列」で TS の `Record<string, any>[]` に相当。

> 🐍 **Python注**: `raise` は例外を投げる。TS の `throw` と同じ。

> 🐍 **Python注**: `items[:limit]` はスライス。先頭から `limit` 件を取り出す。JS の `items.slice(0, limit)` と同じで、**元の list は変わらない**。

> 🐍 **Python注（§4.3 の例外: リスト内包表記）**: `[t for t in _todos if 条件]` は「`_todos` の各要素 `t` のうち条件を満たすものを集めて新しい list にする」。JS の `_todos.filter(t => 条件)` に対応するが、Python では `map` / `filter` よりこちらが標準的な書き方。`[式 for 変数 in 元 if 条件]` の順で、**取り出す式が先頭**に来る点だけ覚えればよい。

> 🧩 **周辺注**: このステップでも Docker / MySQL / Alembic は使わない。

### 2-4. 解説 — なぜこう設計するか

**`done` と `limit` をパスではなくクエリにした理由**。パスは「リソースの identity（どれか）」、クエリは「その見せ方（絞り込み・並び・件数）」を表す。`/todos/done/false` のようにパスに詰めると、絞り込み条件が増えるたびに URL の形が変わり、条件の組み合わせが爆発する。クエリなら独立して足せる。

**`limit` に既定値 20 と上限 100 を置いた理由**。件数上限の無い一覧 API は、データが増えたときに**アプリではなく DB が先に落ちる**。上限は後から足すと既存クライアントの挙動が変わるので、最初から入れておく。

> ⏭️ **後で回収**: 戻り値が list や dict のまま（出力の形を宣言していない）なので、内部のフィールドがそのまま外に出る。**P1-3** でレスポンスモデルを宣言して絞り込む。

> 🧠 **FastAPI の考え方**: 引数の「名前」と「型」だけで、値がどこから来てどう検証されるかが決まる。だから **422 が出たら `loc` を読む** — FastAPI が自分の宣言をどう解釈したかが、そこに書いてある。

### 2-5. 🏢 実務メモ ／ ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> 🏢 **実務メモ**: 一覧系エンドポイントには、最初から件数上限を宣言で強制する。クライアント任せにすると、`?limit=1000000` 一発でメモリと DB を食い潰せる API になる（OWASP API Security Top 10 の «Unrestricted Resource Consumption»）。
> 根拠: https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/

> ⚠️ **アンチパターン**: 固定パスを可変パスより**後に**登録する。Starlette は `app.router.routes` を**登録順**に走査して最初に一致したものを使うため、`/todos/{todo_id}` の後に `/todos/search` を足すと `search` が `todo_id` として解釈され、`422 {"type":"int_parsing","loc":["path","todo_id"],"input":"search"}` になる（✅ 実測）。**固定パスを先に書く**。
> 根拠: https://fastapi.tiangolo.com/tutorial/path-params/

> 🔓 **教材用の簡略化**: データをモジュールレベルの list `_todos` に置いている。これは**プロセスに紐づく状態**なので、`fastapi run --workers 4` のように複数ワーカーで動かすと**ワーカーごとに別の `_todos`** ができ、書き込んだ内容が次のリクエストで消えたように見える。
> **本番では**: 状態はプロセスの外（DB など）に置く。本教材では P3 で MySQL に移す。
> 根拠: https://fastapi.tiangolo.com/deployment/server-workers/

### 2-6. 🔮 予測 → 動作確認

**先に予想を書いてから叩く。**

1. `GET /todos?done=maybe` のステータスコードは何か。`list_todos()` は呼ばれるか。`loc` には何が入るか
2. `GET /todos/999`（存在しない id）と `GET /todos/abc`（型違い）は、**どちらも 4xx だが同じコードか**。違うなら、その差はどの層で生じるか
3. `GET /todos/search` は何を返すか

---

サーバを起動した状態で、別ターミネルから叩く。

```bash
curl -s http://127.0.0.1:8000/todos | python3 -m json.tool
curl -s "http://127.0.0.1:8000/todos?done=false" | python3 -m json.tool
curl -s "http://127.0.0.1:8000/todos?limit=2" | python3 -m json.tool
```

✅ 検証済み: 実際の結果（`python3 -m json.tool` は JSON を整形するだけの標準ツール）

| リクエスト | ステータス | 返る件数 |
| --- | --- | --- |
| `/todos` | 200 | 3件（全部） |
| `/todos?done=false` | 200 | 2件（id 1, 3） |
| `/todos?done=true` | 200 | 1件（id 2） |
| `/todos?limit=2` | 200 | 2件（id 1, 2） |

```bash
curl -s -i "http://127.0.0.1:8000/todos?limit=0"
curl -s -i "http://127.0.0.1:8000/todos?done=maybe"
```

✅ 検証済み: どちらも `422 Unprocessable Content`。ボディは以下（整形済み）

```json
{"detail":[{"type":"greater_than_equal","loc":["query","limit"],
            "msg":"Input should be greater than or equal to 1","input":"0","ctx":{"ge":1}}]}
```

```json
{"detail":[{"type":"bool_parsing","loc":["query","done"],
            "msg":"Input should be a valid boolean, unable to interpret input","input":"maybe"}]}
```

```bash
curl -s -i http://127.0.0.1:8000/todos/2
curl -s -i http://127.0.0.1:8000/todos/999
curl -s -i http://127.0.0.1:8000/todos/abc
curl -s -i http://127.0.0.1:8000/todos/search
```

✅ 検証済み: 実際の結果

| リクエスト | ステータス | ボディ | 誰が返したか |
| --- | --- | --- | --- |
| `/todos/2` | 200 | `{"id":2,"title":"docs を書く","done":true}` | ハンドラ |
| `/todos/999` | **404** | `{"detail":"Todo not found"}` | ハンドラが `raise` → Starlette の例外ハンドラ |
| `/todos/abc` | **422** | `{"detail":[{"type":"int_parsing","loc":["path","todo_id"],...}]}` | **ハンドラは呼ばれず** Pydantic の検証で弾かれた |
| `/todos/search` | **422** | 同上（`"input":"search"`） | 同上。2-5 のアンチパターン |

**404 と 422 の差が要点**。422 は「**リクエストの形が仕様に合っていない**」（ハンドラに到達すらしない）、404 は「形は正しいが**その資源が無い**」（ハンドラが判断して投げた）。前者は Pydantic、後者は自分のコードの責務。

### 2-7. ✅ 想起チェック

**Q1.** `@app.get("/todos/{todo_id}")` と書いたまま、引数名を `todo_id` から `id` に変えた。起動は成功するか。`GET /todos/5` は何を返すか。

<details><summary>答え</summary>

**起動は成功する**（ここが罠）。引数名 `id` はパステンプレートに無いので分類規則の1に当たらず、規則2に落ちて**クエリパラメータ**として扱われる。結果、`GET /todos/5` は「必須のクエリ `id` が無い」として `422 {"type":"missing","loc":["query","id"]}` を返し、`GET /todos/5?id=7` なら 200 で `{"id":7}` が返る（パスの `5` は無視される）。**`loc` が `"query"` になっていたら、この取り違えを疑う。**
</details>

**Q2.** `limit` の範囲検証（`ge=1`）はいつ設定され、いつ実行されるか。

<details><summary>答え</summary>

**設定は起動時**（デコレータ評価時に `Annotated` の中の `Query(ge=1, le=100)` が読まれ、Pydantic のフィールド定義に組み込まれる）。**実行はリクエストごと**。この「宣言を読む段階」と「宣言を使う段階」の分離は P1-1 の `@app.get()` と同じ構造で、以降も繰り返し出てくる。
</details>

**Q3.** `HTTPException` を `raise` ではなく `return` したらどうなるか。

<details><summary>答え</summary>

例外は送出されないので、Starlette の例外ハンドラは動かない。`HTTPException` オブジェクトそのものを戻り値として JSON 化しようとするため、404 にはならず、シリアライズに失敗して **500** になる。`HTTPException` は「返すもの」ではなく「投げるもの」。
</details>

### 2-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| パスパラメータ宣言（`{todo_id}` + `todo_id: int`） | 2-2(a)(b) で仕組み解剖 |
| `Annotated[..., Query()]` | 2-2(a)(c) で仕組み解剖 |
| `HTTPException` | 2-2(d) で仕組み解剖 |
| `Annotated` / `bool \| None` / `list[dict]`（型アノテーション） | 2-2(c) と 2-3 で扱った（§4.3 の例外に該当するため `Annotated` は仕組み解剖側で厚く） |
| リスト内包表記 | 2-3 で Python注（§4.3 の例外5つに該当するため4行使用） |
| `raise` | 2-3 で Python注 |
| スライス `[:n]` | 2-3 で Python注 |
| 出力の形の宣言（レスポンスモデル） | ⏭️ **P1-3** で回収（2-4 で宣言済み） |
| `def` と `async def` の使い分け | ⏭️ **P3-1** で回収（P1-1 から継続） |

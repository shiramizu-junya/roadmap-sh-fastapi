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

---

## P1-3: 作成とレスポンスの形

**作るもの**: `POST /todos` が 201 で作成済み TODO を返す。返す形は型で宣言する
**重要度**: 🔴 毎日使う — 入力の形と出力の形を別々に宣言するのは、FastAPI で API を書く基本姿勢だから
**前ステップとの接続**: P1-2 の「引数の分類規則」の**規則3（Pydantic モデル → リクエストボディ）**を埋める。`app/main.py` に追記する

### 3-0. このステップの初出トークン

**FastAPI**: `BaseModel`（ボディ判定）/ `response_model`（レスポンスモデル）/ `status_code=201`（3）
**Python**: `class` / クラス属性の型アノテーション
**周辺**: なし

### 3-1. コード

3つとも初出なので**完成コード全文**。`app/main.py` を丸ごとこの内容に置き換える。

```python
# app/main.py
from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()


class TodoCreate(BaseModel):
    """クライアントから受け取る形。id はサーバが決めるので含めない"""
    title: str
    done: bool = False


class TodoRead(BaseModel):
    """クライアントに返す形。内部フィールドは含めない"""
    id: int
    title: str
    done: bool


# メモリ上の仮データ。internal_note は「外に出してはいけない内部情報」の見本
_todos: list[dict] = [
    {"id": 1, "title": "牛乳を買う", "done": False, "internal_note": "社内メモ1"},
    {"id": 2, "title": "docs を書く", "done": True, "internal_note": "社内メモ2"},
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


@app.post("/todos", response_model=TodoRead, status_code=201)
def create_todo(todo: TodoCreate) -> Any:
    new_id = max([t["id"] for t in _todos], default=0) + 1
    record = todo.model_dump()
    record["id"] = new_id
    record["internal_note"] = "内部メモ（APIには出さない）"
    _todos.append(record)
    return record


@app.get("/todos/{todo_id}")
def get_todo(todo_id: int):
    for todo in _todos:
        if todo["id"] == todo_id:
            return todo
    raise HTTPException(status_code=404, detail="Todo not found")
```

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Pydantic 2.13.5
（`TestClient` で7パターンと OpenAPI スキーマを実測。結果は 3-6）

| 行 | 何をしているか |
| --- | --- |
| `class TodoCreate(BaseModel)` | **入力**の形。`id` を持たないのが要点 |
| `done: bool = False` | 省略可。既定 `False` |
| `class TodoRead(BaseModel)` | **出力**の形。`internal_note` を持たないのが要点 |
| `@app.post(..., status_code=201)` | 成功時の既定ステータスを 200 から 201 に変える |
| `todo: TodoCreate` | 分類規則3 に当たり、**リクエストボディ**と判定される |
| `response_model=TodoRead` | 戻り値をこの形で作り直してから返す（`-> TodoRead` と等価。使い分けは 3-2(b)） |
| `-> Any` | ハンドラは dict を返す、という**型チェッカ向けの宣言**。FastAPI の挙動には影響しない |
| `record = todo.model_dump()` | Pydantic モデルを dict に変換する |

> 🔄 **素材からの変更**: 公式は1つのモデルを入出力で使い回す例から始める。本教材は最初から `TodoCreate` / `TodoRead` を分ける。P3 で DB モデルが加わったとき、「テーブルの形・入力の形・出力の形」の3つが必要になり、後から分けると全エンドポイントを書き直すことになるため。

### 3-2. 🔬 仕組み解剖

#### (a) `todo: TodoCreate` — リクエストボディ

**正式名称**: リクエストボディ（request body）。宣言は P1-2 の分類規則そのもので、**規則3（Pydantic モデル型 → ボディ）**に当たる。

**実行時に何が起きるか**

- **起動時**: FastAPI が `TodoCreate` を見て「これは Pydantic モデルだからボディだ」と判定し、同時に**そのクラスから JSON Schema を生成**して OpenAPI に登録する
- **リクエスト時**: Starlette が受信したバイト列を JSON としてパースし、Pydantic が `TodoCreate` として検証・変換する。成功したら `TodoCreate` の**インスタンス**が `todo` に入って関数が呼ばれる

- **どのライブラリの責務か**: ボディ判定は FastAPI、受信は Starlette、検証と変換は Pydantic
- **失敗したらどうなるか**: **関数は呼ばれず** 422。`loc` の先頭は `"body"` になる

```
{"title": 123} -> 422 {"type":"string_type","loc":["body","title"],"msg":"Input should be a valid string"}
```

Pydantic v2 は `int` を `str` に**黙って変換しない**。TS で `123` を `string` として受け取れないのと同じ厳しさが、実行時に効く。

**既知スタックとの対応**: zod の `schema.parse(req.body)` をハンドラの手前に自動で挟んだ状態。違いは、**スキーマを別に書くのではなくクラス定義がそのままスキーマになる**こと。React に対応物なし。

**なぜクラスで書くのか**: 型・検証・OpenAPI 定義・エディタ補完が1つの定義から出るため。スキーマとクラスを別に書くと必ずズレる。
根拠: https://fastapi.tiangolo.com/tutorial/body/

#### (b) `response_model=TodoRead` — レスポンスモデル

**この教材で最も重要な宣言**。出口の形の宣言は「ドキュメント」ではなく**実行される仕様**になる。

**書き方が2つある。まずそこから。**

| 書き方 | 使う場面 |
| --- | --- |
| `def create_todo(...) -> TodoRead:` | ハンドラが**本当に `TodoRead` を返す**とき。こちらが基本形 |
| `@app.post(..., response_model=TodoRead)` | **宣言した型とは違うもの**（dict や DB オブジェクト）を返すとき |

本教材は dict（`record`）を返すので**後者**を使う。前者で書くと、型チェッカが「dict を返しているのに `TodoRead` と宣言している」と正しく指摘する。FastAPI 公式もこの場合は `response_model` を使うよう案内している。

```
line 66: Type "dict[str, Any]" is not assignable to return type "TodoRead"
```

✅ 検証済み: Pyright 1.1 系での実測。`response_model=` + `-> Any` にすると指摘が消え、**レスポンスも OpenAPI も同一**であることを確認した

`-> Any` は「何を返すか型では縛らない」という型チェッカ向けの宣言で、FastAPI の挙動には影響しない。両方書いた場合は **`response_model` が優先される**。
根拠: https://fastapi.tiangolo.com/tutorial/response-model/

**実行時に何が起きるか**

- **起動時**: FastAPI が `response_model` を読み、`TodoRead` をレスポンスモデルとして登録する。OpenAPI の 201 応答に `$ref: TodoRead` が入る
- **リクエスト時**: ハンドラの戻り値を**そのまま返さない**。`TodoRead` として一度作り直し（検証し）、その結果を JSON にする。**`TodoRead` に無いフィールドは落ちる**

実測での対比がすべてを語る。同じ `_todos` の要素を返しているのに、

```
POST /todos  ->  {"id":3,"title":"牛乳を買う","done":false}                      ← internal_note が無い
GET  /todos  ->  [{"id":1,...,"internal_note":"社内メモ1"}, ...]                 ← 漏れている
```

差は出口の形を宣言したかどうかだけ。`GET /todos` にはまだ宣言していないので、内部フィールドがそのまま外に出ている。

- **どのライブラリの責務か**: 登録は FastAPI、作り直しは Pydantic
- **失敗したらどうなるか**: 戻り値が `TodoRead` として成立しない場合（必須フィールドが欠けているなど）、**500** になる。422 ではない。422 は「クライアントの入力が悪い」、500 は「サーバの出力が仕様違反」

OpenAPI 上の差も実測で見える。

```
POST /todos の 201: {"schema": {"$ref": "#/components/schemas/TodoRead"}}
GET  /todos の 200: {"schema": {}}                                        ← 空
```

**既知スタックとの対応**: 対応物なし。Express も NestJS（`class-transformer` を足さない限り）も、戻り値を宣言しても実行時には何もしない。「返す形を宣言したら本当にその形に絞られる」のは TS 側には無い挙動。

**なぜこの設計なのか**: 出力の漏洩は**書き忘れでは気づけない**種類の事故だから。「余分なフィールドを消す」コードを各ハンドラに書く方式だと、新しい内部フィールドを1つ足した瞬間に全エンドポイントが漏洩候補になる。出口の形を宣言しておけば、**足したフィールドは既定で外に出ない**。
根拠: https://fastapi.tiangolo.com/tutorial/response-model/

#### (c) `status_code=201`

**正式名称**: パスオペレーションデコレータの `status_code` 引数。**成功時の既定**ステータスを指定する（`HTTPException` で投げたエラーには影響しない）。

- **いつ評価されるか**: 起動時に1回。`APIRoute` に保持される
- **なぜ 201 か**: `POST` が**新しいリソースを作った**ことを表すため。200 だと「処理は成功した」以上の情報が無く、作成されたのかどうかをクライアントがボディから推測することになる
  根拠: https://www.rfc-editor.org/rfc/rfc9110（201 Created の定義）

**既知スタックとの対応**: Express の `res.status(201)` と結果は同じだが、**書く場所が違う**。Express は処理の中（実行時の命令）、FastAPI は宣言の中（起動時の仕様）。だから `/docs` にも自動で反映される。

### 3-3. 🐍 Python注 ／ 🧩 周辺注

> 🐍 **Python注**: `class TodoCreate(BaseModel):` はクラス定義。括弧の中は**継承元**で、TS の `class TodoCreate extends BaseModel` と同じ。

> 🐍 **Python注**: クラス直下の `title: str` は「型を宣言しただけの属性」。値を書かなければ**必須**、`done: bool = False` のように書けば**既定値つき**になる。

> 🐍 **Python注**: `"""..."""` はドキュメント文字列。クラスや関数の直下に置くと説明として扱われる（コメント `#` と違い、実行時にも値として残る）。

> 🧩 **周辺注**: このステップでも Docker / MySQL / Alembic は使わない。

### 3-4. 解説 — なぜこう設計するか

**なぜ `TodoCreate` に `id` を入れないのか。** `id` はサーバが決める値で、クライアントが指定してよい値ではない。モデルに無いフィールドは**黙って捨てられる**ので、`{"title":"z","id":999}` を送っても `id` は無視され、サーバが採番した値になる（実測: `id` は 6 になった）。

これは偶然の親切ではなく、**入力モデルを絞ることが防御になる**という設計。もし1つのモデルを入出力で使い回して `id` を含めていたら、クライアントが他人の `id` を上書きできる余地が生まれる。

**なぜ入力と出力でクラスを2つに分けるのか。** 同じ TODO でも、入口では `id` が不要で、出口では `id` が必要、そして `internal_note` はどちらにも出てはいけない。**3種類の「形」が必要**で、1クラスでは表現できない。P3 でここに「DB のテーブルの形」が加わる。

> ⏭️ **後で回収**: `GET /todos` と `GET /todos/{todo_id}` にはまだ戻り値の型を書いていないので `internal_note` が漏れたままになっている。**P3-3** で `TodoRead` を全エンドポイントに適用する（DB のオブジェクトから Pydantic モデルを作る話と同時にやるほうが自然なため）。

> 🧠 **FastAPI の考え方**: 型宣言は「入口の検査」と「出口の検査」の両方になる。入口を絞ると**受け取ってはいけない値**が、出口を絞ると**返してはいけない値**が、どちらも既定で止まる。

### 3-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: 入力モデルには「クライアントが決めてよい項目」だけを置く。`id` / `created_at` / `owner_id` / `is_admin` のようなサーバ側が決める項目を入力モデルに含めると、リクエストで上書きできてしまう（OWASP API Security Top 10 の «Broken Object Property Level Authorization»、いわゆる mass assignment）。P4 で `owner_id` を扱うときに実際に効いてくる。
> 根拠: https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/

> ⚠️ **アンチパターン**: 1つのモデルを入力と出力で使い回す。最初は短く書けるが、`hashed_password` のような「DB には要るが返してはいけない」列が1つ増えた瞬間に破綻する。**出力モデルを別に持っていれば、列を足しても既定で外に出ない。**
> 根拠: https://fastapi.tiangolo.com/tutorial/response-model/

### 3-6. 🔮 予測 → 動作確認

**先に予想を書いてから叩く。**

1. `{"title":"z","id":999}` を POST したら、返ってくる `id` は何か。422 になるか
2. モデルに無いフィールド `{"title":"y","extra":"余分"}` を送ったら 422 か、それとも通るか
3. `{"title":123}` は通るか。Python では `str(123)` ができるが、Pydantic はどうするか

---

```bash
curl -i -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"牛乳を買う"}'
```

✅ 検証済み: `201 Created`、ボディは以下

```json
{"id":3,"title":"牛乳を買う","done":false}
```

**`internal_note` が入っていない**。ハンドラは `record`（`internal_note` を含む dict）を返しているのに、`response_model=TodoRead` が出口で落としている。

```bash
curl -s -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d '{}'
curl -s -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d '{"title":123}'
curl -s -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d '{"title":"y","extra":"余分"}'
curl -s -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d '{"title":"z","id":999}'
```

✅ 検証済み: 実際の結果

| 送ったボディ | 結果 | 何が起きたか |
| --- | --- | --- |
| `{}` | **422** `{"type":"missing","loc":["body","title"]}` | 必須が無い。`loc` が `"body"` |
| `{"title":123}` | **422** `{"type":"string_type","loc":["body","title"]}` | **数値を文字列に変換しない** |
| `{"title":"y","extra":"余分"}` | **201** `{"id":5,"title":"y","done":false}` | 余分なフィールドは**黙って無視**（エラーにはしない） |
| `{"title":"z","id":999}` | **201** `{"id":6,...}` | `id` も無視され、**サーバの採番が勝つ** |

最後の2つが重要。**Pydantic は「足りない」は怒るが「余分」は黙って捨てる**（既定の挙動）。これが 3-5 の mass assignment 対策の実体。

```bash
curl -s http://127.0.0.1:8000/todos?limit=3
```

✅ 検証済み: `internal_note` がそのまま返る

```json
[{"id":1,"title":"牛乳を買う","done":false,"internal_note":"社内メモ1"}, ...]
```

**同じデータなのに POST では消え、GET では出る。** 差はレスポンスモデルを宣言したかどうかだけ。これが P3-3 で回収する宿題になる。

ブラウザで `http://127.0.0.1:8000/docs` を開く。`POST /todos` には Example Value とスキーマが出るが、`GET /todos` の応答は空のまま。

✅ 検証済み: OpenAPI 定義の実測

```
POST /todos の 201: {"schema": {"$ref": "#/components/schemas/TodoRead"}}
GET  /todos の 200: {"schema": {}}
```

### 3-7. ✅ 想起チェック

**Q1.** ハンドラは `internal_note` を含む dict を返している。なぜレスポンスに出ないのか。落としているのは誰か。

<details><summary>答え</summary>

`response_model=TodoRead` があるため、FastAPI は戻り値をそのまま返さず、**`TodoRead` として作り直してから** JSON にする。`TodoRead` に `internal_note` フィールドが無いので落ちる。作り直しているのは **Pydantic**（登録したのは FastAPI）。`GET /todos` はレスポンスモデルを宣言していないので、この工程が無く、dict がそのまま出る。
</details>

**Q2.** `{"title":"z","id":999}` が 422 にならないのはなぜか。「余分なフィールドはエラー」にしたい場合は何が必要か。

<details><summary>答え</summary>

Pydantic の既定は「知らないフィールドは無視」。必須が欠けていれば怒るが、余分は黙って捨てる。結果として `id` はクライアントから指定できず、サーバの採番が使われる（mass assignment の防御になっている）。

エラーにしたい場合はモデル側の設定で「余分を禁止」に変えられる。ただし既定のままでも**値が通ることはない**ので、この教材では既定を使う。
</details>

**Q3.** `response_model=TodoRead` と宣言したのに、ハンドラが `{"title": "x"}`（`id` 無し）を返したらどうなるか。ステータスコードは。

<details><summary>答え</summary>

`TodoRead` は `id` を必須にしているので、出口の作り直しに失敗する。これはクライアントの入力の問題ではなく**サーバが仕様どおりに返せていない**状態なので、**500** になる（422 ではない）。入口の失敗は 422、出口の失敗は 500、と覚える。
</details>

### 3-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `BaseModel`（ボディ判定） | 3-2(a) で仕組み解剖 |
| `response_model`（レスポンスモデル） | 3-2(b) で仕組み解剖（`-> TodoRead` 形式との使い分けを含む） |
| `status_code=201` | 3-2(c) で仕組み解剖 |
| `.model_dump()` | 3-2(a) の範囲内で扱った（Pydantic モデル → dict の変換） |
| `class` / 継承 | 3-3 で Python注 |
| クラス属性の型アノテーション | 3-3 で Python注 |
| ドキュメント文字列 `"""..."""` | 3-3 で Python注 |
| dict → JSON の変換 / 出力の形の宣言 | ✅ **本ステップで回収**（P1-1・P1-2 からの宿題） |
| `GET` 系へのレスポンスモデル適用 | ⏭️ **P3-3** で回収（3-4 で宣言済み） |
| `def` と `async def` の使い分け | ⏭️ **P3-1** で回収（P1-1 から継続） |

---

## P1-4: 検証を締めて 422 を読む

**作るもの**: `title` に長さ制限と「空白だけは禁止」の独自ルールを入れ、422 のボディを読めるようにする
**重要度**: 🔴 毎日使う — 入力検証はどの API でも必ず書く。そして **422 を読めないと詰まる時間が最も長い**
**前ステップとの接続**: P1-3 の `TodoCreate` に制約を足す。`app/main.py` の `TodoCreate` だけを書き換える

### 4-0. このステップの初出トークン

**FastAPI**: `Field()` / `field_validator` / 422 ボディの構造（`type` / `loc` / `msg` / `ctx` / `input`）（3）
**Python**: `@classmethod` / `.strip()` / `if not x`
**周辺**: なし

### 4-1. コード

初出なので完成形を出す。**変更は `TodoCreate` と import 行だけ**（他のエンドポイントはそのまま）。

```python
# app/main.py — 差分（import 行と TodoCreate のみ）
from pydantic import BaseModel, Field, field_validator


class TodoCreate(BaseModel):
    """クライアントから受け取る形。id はサーバが決めるので含めない"""

    title: str = Field(min_length=1, max_length=100)
    done: bool = False

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("空白だけのタイトルは登録できません")
        return trimmed
```

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Pydantic 2.13.5
（`TestClient` で5パターン + OpenAPI スキーマ + デコレータ順序の挙動を実測。結果は 4-6）

| 行 | 何をしているか |
| --- | --- |
| `Field(min_length=1, max_length=100)` | 型だけでは表せない**制約**を足す。`str` であることは型が、長さは `Field` が担当 |
| `@field_validator("title")` | `title` を検証する関数をこのモデルに登録する |
| `trimmed = value.strip()` | 前後の空白を落とす |
| `raise ValueError(...)` | 検証失敗。**`HTTPException` ではない**（後述） |
| `return trimmed` | **検証器は値を書き換えて返せる**。以降はこの値が使われる |

### 4-2. 🔬 仕組み解剖

#### (a) `Field(min_length=1, max_length=100)`

**正式名称**: Pydantic のフィールド制約（field constraints）。

**実行時に何が起きるか**

- **起動時**: `TodoCreate` のクラス定義が評価されるときに Pydantic が制約を読み取り、検証器（Rust 実装のコア）を組み立てる。同時に **JSON Schema にも反映**される
- **リクエスト時**: 組み立て済みの検証器が値を検査する。毎回ルールを解釈し直すわけではない

OpenAPI への反映は実測で見える。

```json
"title": { "type": "string", "maxLength": 100, "minLength": 1, "title": "Title" }
```

- **どのライブラリの責務か**: 完全に Pydantic。FastAPI はモデルを渡しているだけ
- **失敗したらどうなるか**: 422。`type` は `string_too_short` / `string_too_long` になり、**`ctx` に違反した閾値が入る**

**既知スタックとの対応**: zod の `z.string().min(1).max(100)` と同じ役割。違いは、zod がスキーマを別に書くのに対し、`Field` は**クラス属性のデフォルト値の位置**に書くこと。

**なぜ型と別に書くのか**: 「文字列であること」は型の話、「1〜100文字であること」は値の話で、レイヤが違うため。`Annotated[str, Field(min_length=1)]` と書くこともでき、意味は同じ。P1-2 の `Query()` と同じ構造だと気づけば見通しがよくなる。
根拠: https://docs.pydantic.dev/latest/concepts/fields/

#### (b) `@field_validator("title")`

**正式名称**: フィールドバリデータ。`Field` の宣言的な制約では表せないルールを、関数で書くための仕組み。

**実行時に何が起きるか** — **実行順序が重要**。

1. まず**型変換**（`str` か？）
2. 次に **`Field` の制約**（長さは足りるか？）
3. 最後に **`field_validator`**（独自ルール）

実測でこの順序が確認できる。`""`（空文字）を送ると `Field` の `min_length` で止まり、**独自バリデータには到達しない**。

```
{"title":""}    -> type: "string_too_short"   ← Field で止まった
{"title":"   "} -> type: "value_error"        ← Field は通過し、独自バリデータで止まった
```

- **どのライブラリの責務か**: Pydantic
- **失敗したらどうなるか**: `ValueError` を投げると 422 になり、`type` は `value_error`、`msg` は **`"Value error, "` が前置された**自分のメッセージになる

```json
{"type":"value_error","loc":["body","title"],
 "msg":"Value error, 空白だけのタイトルは登録できません","input":"   "}
```

**なぜ `HTTPException` ではなく `ValueError` を投げるのか**: このクラスは FastAPI 専用ではなく、**ただの Pydantic モデル**だから。HTTP を知らない層に HTTP の例外を持ち込むと、CLI やバッチから同じモデルを使えなくなる。`ValueError` を投げておけば、HTTP に変換するかどうかは外側（FastAPI）が決められる。

**値を書き換えられる点**: `return trimmed` により、`"  牛乳を買う  "` は `"牛乳を買う"` として保存される（実測で確認）。検証器は「検査」だけでなく「正規化」の場所でもある。
根拠: https://docs.pydantic.dev/latest/concepts/validators/

#### (c) 422 のボディを読む

**正式名称**: `422 Unprocessable Content`。「構文は正しいが、内容が処理できない」を表す。
根拠: https://www.rfc-editor.org/rfc/rfc9110#name-422-unprocessable-content

`detail` は**常にリスト**で、**エラーは1件ずつではなくまとめて返る**（実測: 2箇所間違えると2件入る）。

| キー | 意味 | 読み方 |
| --- | --- | --- |
| `type` | エラーの種類 | `string_too_short` / `bool_parsing` / `value_error` など。**機械判定はここを見る** |
| `loc` | 場所 | `["body","title"]`。**第1要素が `body` / `query` / `path` のどれか**を最初に見る（P1-2 参照） |
| `msg` | 人間向けの説明 | UI にそのまま出す用途には向かない（英語＋`Value error, ` の前置） |
| `ctx` | 文脈 | 違反した閾値（`{"min_length":1}` など）。**エラーメッセージを自前で組み立てるならここ** |
| `input` | 実際に来た値 | デバッグ用。**ログに出すと個人情報が載る**点に注意 |

- **どのライブラリの責務か**: このボディを組み立てるのは Pydantic、HTTP レスポンスにするのは FastAPI（`RequestValidationError` のハンドラ）

**なぜ最初のエラーで打ち切らないのか**: フォームを1項目ずつ直させるのは UX として悪いため。全部まとめて返せば、クライアントは一度に全項目へ印を付けられる。

### 4-3. 🐍 Python注 ／ 🧩 周辺注

> 🐍 **Python注**: `@classmethod` は「インスタンスではなくクラス自身を第1引数（`cls`）で受け取る関数」にする指定。Pydantic v2 では**省略しても動く**が、型チェッカが誤検知するため付けるのが推奨。

> 🐍 **Python注**: `value.strip()` は前後の空白（改行・タブ含む）を落とした**新しい文字列**を返す。JS の `String.prototype.trim()` と同じ。

> 🐍 **Python注**: `if not trimmed:` は「空文字なら真」。Python では空文字・空list・`0`・`None` が偽として扱われる（JS の falsy とほぼ同じだが、`"0"` は真）。

> 🧩 **周辺注**: このステップでも Docker / MySQL / Alembic は使わない。

### 4-4. 解説 — なぜこう設計するか

**`Field` と `field_validator` の使い分け。** 宣言で書けるものは `Field` に寄せる。理由は2つあり、(1) OpenAPI に反映されるのでクライアントが事前に知れる、(2) Rust 実装の検証器が使われるため速い。`field_validator` は「宣言では表せないもの」専用と考える。

今回の「空白だけ禁止」は、`min_length=1` では表せない（`"   "` は3文字なので通ってしまう）。だから関数が要る。

**正規化を検証器でやる理由。** `"  牛乳  "` と `"牛乳"` を別物として保存すると、後から「重複チェックが効かない」「検索に引っかからない」という形で壊れる。**入口で形を揃える**のが最も安い。P3 で DB に入れるようになると、揃っていないデータは修正コストが跳ね上がる。

> 🧠 **FastAPI の考え方**: 検証器は「関所」ではなく「入口の整形工場」。弾くだけでなく、通す値の形も整えて奥へ渡す。

### 4-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: `422` のボディをそのままクライアントに見せない。`msg` は英語で、`input` には**送られてきた生の値がそのまま入る**。パスワードや個人情報を含むフィールドで検証が落ちると、それがレスポンスとログの両方に出る。表示用のメッセージは `type` と `ctx` から自前で組み立て、`input` は落とす。P5-3 で例外ハンドラを一元化するときに実装する。
> 根拠: https://fastapi.tiangolo.com/tutorial/handling-errors/

> ⚠️ **アンチパターン**: `@classmethod` を `@field_validator` の**上**に書く。エラーにも警告にもならず、**バリデータが静かに無視される**。

```python
@classmethod            # ← 上下が逆
@field_validator("title")
def up(cls, v: str) -> str: return v.upper()
```

✅ 検証済み: 正しい順序では `"abc"` → `"ABC"` になるが、逆順では `"abc"` のまま（例外は出ない）。
デコレータは**下から順に適用される**ため、`field_validator` が登録する前に `classmethod` が包んでしまう。
根拠: https://docs.pydantic.dev/latest/concepts/validators/

### 4-6. 🔮 予測 → 動作確認

**先に予想を書いてから叩く。**

1. `{"title":""}` と `{"title":"   "}` は**同じ `type`** の 422 になるか。違うなら、なぜ違うか
2. `{"title":"  牛乳を買う  "}` は 422 か 201 か。201 なら、保存される `title` は何か
3. `{"title":"","done":"maybe"}` のように2箇所間違えたら、返るエラーは何件か

---

```bash
curl -s -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" -d '{"title":"  牛乳を買う  "}'
```

✅ 検証済み: `201`、**前後の空白が落ちている**

```json
{"id":2,"title":"牛乳を買う","done":false}
```

```bash
curl -s -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d '{"title":""}'
curl -s -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d '{"title":"   "}'
```

✅ 検証済み: **どちらも 422 だが `type` が違う**

| 送った値 | `type` | 誰が止めたか |
| --- | --- | --- |
| `""` | `string_too_short`（`ctx: {"min_length":1}`） | **`Field`**。独自バリデータには届いていない |
| `"   "` | `value_error`（`msg: "Value error, 空白だけの…"`） | **`field_validator`**。`Field` は通過した |

同じ「空っぽ」でも**止まる場所が違う**。検証は「型 → `Field` → `field_validator`」の順に走り、**手前で落ちたら奥は実行されない**。

```bash
curl -s -X POST http://127.0.0.1:8000/todos \
  -H "Content-Type: application/json" -d '{"title":"","done":"maybe"}'
```

✅ 検証済み: **2件**まとめて返る

```json
{"detail":[
  {"type":"string_too_short","loc":["body","title"],"ctx":{"min_length":1}},
  {"type":"bool_parsing","loc":["body","done"],"input":"maybe"}
]}
```

ブラウザで `/docs` を開くと、`TodoCreate` の `title` に `minLength: 1` / `maxLength: 100` が表示される。

✅ 検証済み: OpenAPI 実測

```json
"title": { "type": "string", "maxLength": 100, "minLength": 1, "title": "Title" }
```

**`Field` の制約は仕様として外に出るが、`field_validator` のルールは出ない**（関数の中身は機械には読めないため）。独自ルールを増やすほど、ドキュメントに載らない仕様が増える点は意識しておく。

### 4-7. ✅ 想起チェック

**Q1.** `{"title":""}` が独自バリデータに届かないのはなぜか。

<details><summary>答え</summary>

検証は「型変換 → `Field` の制約 → `field_validator`」の順に走り、**手前で失敗したら奥は実行されない**。`""` は `min_length=1` に違反するので `Field` の段階で止まり、`type` は `string_too_short` になる。`"   "` は3文字なので `Field` を通過し、独自バリデータまで届いて `value_error` になる。
</details>

**Q2.** バリデータで `HTTPException(status_code=422, ...)` を投げないのはなぜか。

<details><summary>答え</summary>

`TodoCreate` は FastAPI 専用のクラスではなく**ただの Pydantic モデル**で、HTTP を知らない層だから。`ValueError` を投げておけば、HTTP に変換するかどうかは外側の FastAPI が決められ、同じモデルを CLI やバッチ処理からも使える。層をまたぐ依存を作らない、という設計判断。
</details>

**Q3.** 422 のボディのうち、クライアントに表示するメッセージを組み立てるのに使うべきキーはどれか。使ってはいけないキーは。

<details><summary>答え</summary>

使うのは **`type` と `ctx`**（`type` で種類を判定し、`ctx` の閾値を埋め込む）。`loc` でどの項目かを特定する。

避けるのは **`msg` と `input`**。`msg` は英語で `"Value error, "` の前置が付く。`input` には**送られてきた生の値**が入るので、パスワードなどが検証に落ちるとそのまま露出する。
</details>

### 4-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `Field()` | 4-2(a) で仕組み解剖 |
| `field_validator` | 4-2(b) で仕組み解剖 |
| 422 ボディの構造（`type`/`loc`/`msg`/`ctx`/`input`） | 4-2(c) で仕組み解剖 |
| `@classmethod` | 4-3 で Python注（+ 4-5 で順序のアンチパターン） |
| `.strip()` | 4-3 で Python注 |
| `if not x`（真偽の扱い） | 4-3 で Python注 |
| 422 の表示用整形 / `input` を落とす | ⏭️ **P5-3** で回収（例外ハンドラの一元化として実装） |
| `GET` 系へのレスポンスモデル適用 | ⏭️ **P3-3** で回収（P1-3 から継続） |
| `def` と `async def` の使い分け | ⏭️ **P3-1** で回収（P1-1 から継続） |

---

## P1-5: 更新と削除（CRUD 完成）

**作るもの**: `PUT /todos/{todo_id}` と `DELETE /todos/{todo_id}`（204）。これで達成条件 (1) の CRUD 4種が揃う
**重要度**: 🔴 毎日使う — 残り2つの動詞と、「本文を返さない応答」の書き方はどの API にも出る
**前ステップとの接続**: P1-4 までで作成・一覧・取得ができている。`app/main.py` に `TodoUpdate` と2本のエンドポイントを足す

### 5-0. このステップの初出トークン

**FastAPI**: `@app.put` / `@app.delete` / `status` モジュールの定数 / 204 と本文なしレスポンス（3）
**Python**: 継承による共通化 / `list.remove()` / 値を返さない `return`
**周辺**: なし

### 5-1. コード

初出なので完成形。**追加は import 行・`TodoUpdate`・エンドポイント2本**（既存部分は変更なし）。

```python
# app/main.py — 追加分
from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator


class TodoBase(BaseModel):
    """入力の共通部分。title の制約と検証はここに1回だけ書く"""

    title: str = Field(min_length=1, max_length=100)

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("空白だけのタイトルは登録できません")
        return trimmed


class TodoCreate(TodoBase):
    """POST 用。done は省略できる"""

    done: bool = False


class TodoUpdate(TodoBase):
    """PUT 用。全置換なので done も必須にする"""

    done: bool


@app.put("/todos/{todo_id}", response_model=TodoRead)
def update_todo(todo_id: int, todo: TodoUpdate) -> Any:
    for record in _todos:
        if record["id"] == todo_id:
            record["title"] = todo.title
            record["done"] = todo.done
            return record
    raise HTTPException(status_code=404, detail="Todo not found")


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: int) -> None:
    for record in _todos:
        if record["id"] == todo_id:
            _todos.remove(record)
            return
    raise HTTPException(status_code=404, detail="Todo not found")
```

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Pydantic 2.13.5
（`TestClient` で6パターン + OpenAPI を実測。ボディはバイト列のまま確認した。結果は 5-6）

| 行 | 何をしているか |
| --- | --- |
| `class TodoUpdate(TodoBase)` | `TodoBase` を継承。`title` の制約と検証器は**そのまま受け継ぐ** |
| `done: bool` | 親の `done: bool = False` を**必須に上書き**する |
| `def update_todo(todo_id: int, todo: TodoUpdate)` | パスパラメータとボディを**同時に**受け取る |
| `status.HTTP_204_NO_CONTENT` | 数値 `204` と同じだが、名前で意味が読める |
| `-> None` | 返すものが無い。FastAPI は本文を書かない |
| `_todos.remove(record)` | list から要素を取り除く |

### 5-2. 🔬 仕組み解剖

#### (a) `@app.put` / `@app.delete` — 引数の分類は同じ規則で動く

**正式名称**: パスオペレーションデコレータ。`get` / `post` / `put` / `delete` / `patch` などが同じ形で用意されている（P1-1 の仕組み解剖参照）。

注目すべきは `update_todo` の引数が**2種類混ざっている**こと。

```python
def update_todo(todo_id: int, todo: TodoUpdate) -> Any:
```

P1-2 で立てた分類規則がそのまま効く。

| 引数 | 規則 | 分類 |
| --- | --- | --- |
| `todo_id` | 1（名前がパステンプレートにある） | パスパラメータ |
| `todo` | 3（型が Pydantic モデル） | リクエストボディ |

**新しい規則は何も足されていない。** メソッドが増えても引数の読み方は1つ。これが P1-2 で個別の書き方ではなく「規則」として説明した理由。

- **いつ評価されるか**: 起動時に1回（分類の確定）
- **失敗したらどうなるか**: `/todos/abc` なら `loc:["path","todo_id"]`、ボディが不正なら `loc:["body",...]` の 422

#### (b) `TodoBase` — 共通部分を親に置き、差分だけを子に書く

Pydantic モデルは普通のクラスなので継承できる。**`Field` の制約も `field_validator` も自動的に引き継がれる。**

実測: `PUT /todos/1` に `{"title":"   ","done":false}` を送ると、`TodoBase` に書いた検証器が動く。

```json
{"type":"value_error","loc":["body","title"],"msg":"Value error, 空白だけのタイトルは登録できません"}
```

`TodoUpdate` には検証器を1行も書いていないのに効いている。

**3つのクラスの関係**

```
TodoBase   … title（制約と検証）        ← 入力に共通
 ├ TodoCreate … + done: bool = False    ← POST。省略可
 └ TodoUpdate … + done: bool            ← PUT。必須
```

`done` の扱いだけが違い、その違いがクラス構造にそのまま出ている。実測:

```
POST {"title":"x"}  (done 省略) -> 201  （既定 False が入る）
PUT  {"title":"x"}  (done 省略) -> 422 {"type":"missing","loc":["body","done"]}
```

**なぜ更新では必須にするのか**: `PUT` は**リソース全体の置き換え**だから。省略を許して既定値 `False` を入れると、`done: true` の TODO に `{"title":"買い物"}` を送っただけで完了状態が消える。「送らなかった項目は変えない」という挙動が欲しい場合は `PUT` ではなく `PATCH` を使う。
根拠: https://www.rfc-editor.org/rfc/rfc9110#name-put

**なぜ `TodoUpdate(TodoCreate)` として `done` を上書きしないのか**

一見、親を `TodoCreate` にして `done: bool` と書き直すほうが短い。実行時はそれでも動く。
だが**型チェッカがエラーを出す**。

```
"done" overrides a field of the same name but is missing a default value
```

✅ 検証済み: Pyright 1.1 系での実測。Pydantic モデルはデータクラス相当として扱われ、
「既定値のあるフィールドの既定値を継承で剥がす」ことが規則違反と判定される
（Pydantic の `__init__` はキーワード専用なので実害は無く、だから実行時は動く）。

共通部分を親に切り出せば**上書き自体が無くなる**ので、この問題は起きない。
警告を抑えるためではなく、**「何が共通で何が違うのか」がクラス構造に現れる**のが本来の利点。
根拠: https://docs.pydantic.dev/latest/concepts/models/#model-inheritance

> ⏭️ **後で回収**: 部分更新（`PATCH`）はこの教材では作らない。必要な考え方（「未指定」と「null を指定」の区別）は **M3 のカバーしていないこと**で扱う。

#### (c) `status.HTTP_204_NO_CONTENT` と本文なしレスポンス

**正式名称**: `fastapi.status`。HTTP ステータスコードの定数を集めたモジュール（実体は Starlette のもの）。`status.HTTP_204_NO_CONTENT` は `204` そのもので、動作は変わらない。

**なぜ定数を使うのか**: `204` という数字を見て「No Content」と即座に読める人は多いが、`422` や `409` になると怪しくなる。**エディタの補完が効く**点も大きい。

**204 のとき実行時に何が起きるか**

- 戻り値アノテーションが `-> None` で、ハンドラが値を返さない（`return` のみ）
- FastAPI は**本文を1バイトも書かない**

実測（バイト列のまま確認）:

```
DELETE /todos/2 -> 204
  raw body: b''
  headers: content-length ヘッダが無い
```

比較用に、404 のときは本文がある。

```
DELETE /todos/2 (2回目) -> 404
  raw body: b'{"detail":"Todo not found"}'
  content-length: 27
```

- **どのライブラリの責務か**: 204 の扱いは Starlette のレスポンス生成、判断は FastAPI
- **失敗したらどうなるか**: 204 を指定したハンドラが**値を返してしまう**と、本文のあるレスポンスを作ろうとして矛盾する。`-> None` を書いておくと、型の上でも返せないことが明示される

OpenAPI にも「本文なし」として出る。実測:

```json
"204": { "description": "Successful Response" }      ← content キーが無い
```

**既知スタックとの対応**: Express の `res.sendStatus(204)` に相当。違いは、FastAPI 側は**宣言（デコレータ引数）で決まる**ので `/docs` にも自動で反映されること。
根拠: https://www.rfc-editor.org/rfc/rfc9110#name-204-no-content

### 5-3. 🐍 Python注 ／ 🧩 周辺注

> 🐍 **Python注**: `class TodoCreate(TodoBase):` は継承。親の属性をすべて受け継ぎ、子で書いた分が足される。TS の `extends` と同じ。

> 🐍 **Python注**: `_todos.remove(record)` は list から**最初に一致した要素**を取り除く。JS の `arr.splice(arr.indexOf(x), 1)` に相当。

> 🐍 **Python注**: 値を書かない `return` は「ここで関数を終える」の意味で、`None` を返したのと同じ。

> 🧩 **周辺注**: このステップでも Docker / MySQL / Alembic は使わない。

### 5-4. 解説 — なぜこう設計するか

**ループ中に list を変更している点について。** `delete_todo` は `for` で回しながら `remove` しているが、**`return` で即座に抜けるので安全**。抜けずに回し続けると、要素が詰まってインデックスがずれ、次の要素を飛ばす。「消したら抜ける」を守ること。

**404 を返すか 204 を返すか。** 存在しない TODO への `DELETE` は、2回目以降 404 になる（実測）。「`DELETE` は冪等（idempotent）なのに 404 なのは矛盾では」と思うかもしれないが、冪等性が保証するのは**サーバの状態**であって**ステータスコード**ではない。何度呼んでも「その TODO が無い」状態は同じなので、冪等性は満たしている。
根拠: https://www.rfc-editor.org/rfc/rfc9110#name-idempotent-methods

> 🧠 **FastAPI の考え方**: メソッドが増えても読み方は増えない。`get` が `put` になっても、引数の分類規則も検証の走り方も同じ。**覚える規則を増やさない**のが FastAPI の一貫した設計。

### 5-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: `204 No Content` のレスポンスに本文を入れてはいけない。仕様上「本文を含まない」と定義されており、入れた場合の挙動はプロキシやクライアントによって割れる（無視される／接続が壊れる）。「削除しました」というメッセージを返したいなら 204 ではなく 200 を選ぶ。
> 根拠: https://www.rfc-editor.org/rfc/rfc9110#name-204-no-content

> ⚠️ **アンチパターン**: `PUT` の入力モデルで項目を省略可にする。`{"title":"買い物"}` だけを送れてしまうと、既存の `done: true` が既定値の `False` で上書きされ、**送っていない項目が勝手に変わる**。`PUT` は全置換なので入力も全項目必須にし、部分更新が要るなら `PATCH` を別に用意する。
> 根拠: https://www.rfc-editor.org/rfc/rfc9110#name-put

### 5-6. 🔮 予測 → 動作確認

**先に予想を書いてから叩く。**

1. `TodoUpdate` には検証器を1行も書いていない。`{"title":"   ","done":false}` を PUT したらどうなるか
2. `{"title":"x"}`（`done` を省略）を PUT したら 200 か 422 か
3. `DELETE` が成功したときのレスポンス本文は何バイトか。2回続けて削除したら2回目は何が返るか

---

```bash
curl -s -X PUT http://127.0.0.1:8000/todos/1 \
  -H "Content-Type: application/json" -d '{"title":"牛乳と卵","done":true}'
```

✅ 検証済み: `200`、`internal_note` は落ちている（`response_model=TodoRead` が効いている）

```json
{"id":1,"title":"牛乳と卵","done":true}
```

```bash
curl -s -X PUT http://127.0.0.1:8000/todos/1 -H "Content-Type: application/json" -d '{"title":"x"}'
curl -s -X PUT http://127.0.0.1:8000/todos/1 -H "Content-Type: application/json" -d '{"title":"   ","done":false}'
curl -s -X PUT http://127.0.0.1:8000/todos/999 -H "Content-Type: application/json" -d '{"title":"y","done":false}'
```

✅ 検証済み: 実際の結果

| 送ったもの | 結果 | 何が起きたか |
| --- | --- | --- |
| `{"title":"x"}` | **422** `{"type":"missing","loc":["body","done"]}` | 親の `= False` を**上書きして必須にした**効果 |
| `{"title":"   ","done":false}` | **422** `{"type":"value_error",...}` | `TodoCreate` の検証器が**継承されている** |
| `/todos/999` | **404** `{"detail":"Todo not found"}` | ボディは正しいので 422 ではない |

```bash
curl -s -i -X DELETE http://127.0.0.1:8000/todos/2
curl -s -i -X DELETE http://127.0.0.1:8000/todos/2
```

✅ 検証済み: 1回目と2回目で明確に違う

| 回 | ステータス | 本文 | ヘッダ |
| --- | --- | --- | --- |
| 1回目 | **204** | `b''`（0バイト） | `content-length` が**無い** |
| 2回目 | **404** | `b'{"detail":"Todo not found"}'` | `content-length: 27` |

`-> None` と `status_code=204` の組み合わせで、FastAPI は**本文を1バイトも書かない**。

これで CRUD 4種が揃った。**達成条件 (1) の前半（メモリ上で動く）がここで満たされる。**

```bash
curl -s -X POST http://127.0.0.1:8000/todos -H "Content-Type: application/json" -d '{"title":"新規"}'   # C
curl -s http://127.0.0.1:8000/todos                                                                     # R
curl -s -X PUT http://127.0.0.1:8000/todos/1 -H "Content-Type: application/json" -d '{"title":"更新","done":true}'  # U
curl -s -i -X DELETE http://127.0.0.1:8000/todos/1                                                      # D
```

### 5-7. ✅ 想起チェック

**Q1.** `TodoUpdate` に `field_validator` を1行も書いていないのに、空白だけの `title` が弾かれるのはなぜか。

<details><summary>答え</summary>

`TodoUpdate` は `TodoBase` を**継承**しているため。Pydantic モデルは普通の Python クラスなので、`Field` の制約（`min_length` / `max_length`）も `field_validator` で登録した検証器も、そのまま受け継がれる。子で足したのは `done` だけ。
</details>

**Q2.** `TodoUpdate` で `done: bool` を必須にしているのはなぜか。省略可にすると何が起きるか。

<details><summary>答え</summary>

`PUT` が**全置換**だから。省略可（既定 `False`）にすると `{"title":"買い物"}` だけの PUT が通ってしまい、`done: true` だった TODO が `False` で上書きされる。**送っていない項目が勝手に変わる**という事故になる。`TodoCreate` 側が省略可なのは、作成時には「まだ完了していない」が自然な既定だから。
</details>

**Q3.** `DELETE` を2回呼ぶと 204 → 404 と変わる。これは「`DELETE` は冪等」に反しないか。

<details><summary>答え</summary>

反しない。冪等性が保証するのは**サーバの状態**であって、返るステータスコードではない。何回呼んでも「その TODO が存在しない」という状態は同じなので、冪等性は満たしている。
</details>

### 5-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `@app.put` / `@app.delete` | 5-2(a) で仕組み解剖（P1-1 の `@app.get` と同じ機構であることを確認） |
| `response_model=` の再登場 | P1-3 の 3-2(b) 参照（`-> Any` との組み合わせも同じ） |
| `status` モジュールの定数 | 5-2(c) で仕組み解剖 |
| 204 と本文なしレスポンス（`-> None`） | 5-2(c) で仕組み解剖 |
| 継承による共通化（`TodoBase`） | 5-2(b) で仕組み解剖 + 5-3 で Python注 |
| `list.remove()` | 5-3 で Python注 |
| 値を返さない `return` | 5-3 で Python注 |
| **達成条件 (1) CRUD 4種** | ✅ **本ステップで達成**（メモリ上。P3-4 で MySQL 版を再達成） |
| `PATCH` による部分更新 | ⏭️ **M3 のカバーしていないこと**で扱う（5-2(b) で宣言済み） |
| `GET` 系へのレスポンスモデル適用 | ⏭️ **P3-3** で回収（P1-3 から継続） |
| 422 の表示用整形 | ⏭️ **P5-3** で回収（P1-4 から継続） |
| `def` と `async def` の使い分け | ⏭️ **P3-1** で回収（P1-1 から継続） |

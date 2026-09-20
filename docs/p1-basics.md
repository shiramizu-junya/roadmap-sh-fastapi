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

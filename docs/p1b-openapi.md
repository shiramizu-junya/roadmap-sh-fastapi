# P1b — 生成物を読めるようになる

P1a では**宣言を書いた**。P1b では、その宣言から FastAPI が**何を生成したか**を読み、
残りの CRUD・ファイル分割・デバッガまで進む。

| # | タイトル |
| --- | --- |
| P1-6 | 生成された仕様書を読む |
| P1-7 | 残りの CRUD と 404 |
| P1-8 | ルーター分割と依存性注入 |
| P1-9 | Zed からブレークポイントで止める |
| P1-10 | 欄をまたぐ条件を書く（v11 で追加） |

---

## P1-6: 生成された仕様書を読む

**作るもの**: `/openapi.json` を `jq` で読み、**書いたコードの1行1行が仕様書のどこに現れているか**を対応づける。コードは `tags=` / `summary=` / docstring を足すだけ
**重要度**: 🔴 毎日使う — 仕様書はフロントエンドや他チームとの**約束そのもの**で、コードを変えるたびに「約束がどう変わったか」を確かめることになるため
**前ステップとの接続**: P1-2 から「仕様書が勝手に生えている」とだけ言って先送りしてきた（2-6b / 3-6b / 4-6b / 5-6b）。**入口の形（P1-4）と出口の形（P1-5）がそろった**ので、ここでまとめて読む

### 6-0. このステップの初出トークン

| 系統 | トークン |
| --- | --- |
| **FastAPI** | `GET /openapi.json`（と `/docs` / `/redoc`）/ `components.schemas` と `$ref` / `tags=` / `summary=`（3つ = 上限） |
| **Python** | `"""..."""`（docstring） |
| **【道具】** | `jq` の読み方（`.キー` / `."/todos"` / `keys` / `\|` / `-c` / `-r`） |
| **周辺** | — |

> `jq` は P1-5 で「整形する道具」として出しただけだった。今回は**主役の道具**なので、周辺注ではなく 6-2b で読み方をまとめて扱う。

---

### 6-1. コード

**今回のコード変更は小さい。** 主役は 6-6 の「読む」ほう。

#### 要件

1. 3つのエンドポイントに **`tags=`** を付ける。`/health` は `"health"`、`/todos` の2つは `"todos"`
2. 3つに **`summary=`** で日本語の短い説明を付ける
3. `create_todo` に **docstring**（関数の説明文）を書く。複数行で、箇条書きを1つ以上含める
4. ruff / mypy が通る

#### 骨組み: `app/main.py`（変わる部分だけ）

```python
@app.get("/health")  # TODO: tags と summary
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/todos", status_code=201)  # TODO: tags と summary
def create_todo(todo: TodoCreate) -> TodoRead:
    # TODO: ここに docstring（関数の最初の行に置く）
    new_todo = TodoRead(id=len(todos) + 1, title=todo.title, done=todo.done)
    todos.append(new_todo)
    return new_todo


@app.get("/todos")  # TODO: tags と summary
def list_todos() -> list[TodoRead]:
    return todos
```

<details><summary>完成形（自分で書いてから開く）</summary>

`app/main.py`（全文）

```python
from fastapi import FastAPI

from app.schemas.todo import TodoCreate, TodoRead

app = FastAPI()

todos: list[TodoRead] = []


@app.get("/health", tags=["health"], summary="死活確認")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/todos", status_code=201, tags=["todos"], summary="TODO を1件作る")
def create_todo(todo: TodoCreate) -> TodoRead:
    """
    タイトルを受け取り、ID を振って保存する。

    - 知らない欄を送ると 422
    - 成功すると 201
    """
    new_todo = TodoRead(id=len(todos) + 1, title=todo.title, done=todo.done)
    todos.append(new_todo)
    return new_todo


@app.get("/todos", tags=["todos"], summary="TODO の一覧")
def list_todos() -> list[TodoRead]:
    return todos
```

</details>

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Pydantic 2.13.5 / jq 1.8.2。
完成形を別の場所にコピーして `ruff check` = `All checks passed!`、`ruff format --check` = `4 files already formatted`、
`mypy` = `Success: no issues found in 4 source files`。`jq` の出力はすべて 6-6 に実物を貼った。

> 💡 **補足**: 6-6 の Q1〜Q3 は、**コードを変える前**（P1-5 の状態）でも同じ結果になる。先に読んで、最後に `tags=` を足して差分を見る（6-6b）順番でもよい。

---

### 6-1b. 📊 図解

#### (a) 4つの名前は、それぞれどこにいるか

```mermaid
sequenceDiagram
    participant B as ブラウザ
    participant SW as Swagger UI（/docs の画面）
    participant F as FastAPI
    participant H as create_todo()

    B->>F: GET /docs
    F-->>B: 画面の骨組み（HTML）だけ
    SW->>F: GET /openapi.json
    F->>F: 初回だけ仕様書を組み立てて覚えておく
    F-->>SW: OpenAPI スキーマ（JSON）
    SW->>SW: JSON を読んで画面を描く
    SW->>F: Try it out → POST /todos {"title":""}
    F--xSW: 422（create_todo は呼ばれない）
    Note over H: Try it out は本物のリクエスト
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**Swagger UI は FastAPI の一部ではなく、ブラウザで動く「JSON を絵にする道具」。**
`/docs` が返すのは空っぽの画面で、中身は**ブラウザが改めて `/openapi.json` を取りに行って**描いている。
だから「コードを直したのに画面が変わらない」ときは、**まず `/openapi.json` を `jq` で見る**。JSON が変わっていなければコード側（あるいはサーバの再起動）、JSON が変わっていれば画面側（ブラウザの再読み込み）の問題、と切り分けられる。

#### (b) `$ref` は「実体はあっち」という矢印

```mermaid
flowchart LR
    subgraph paths["paths./todos.post"]
        RB["requestBody"]
        R201["responses.201"]
        R422["responses.422"]
    end
    subgraph schemas["components.schemas"]
        TC["TodoCreate"]
        TR["TodoRead"]
        HVE["HTTPValidationError"]
        VE["ValidationError"]
    end
    RB -->|"$ref"| TC
    R201 -->|"$ref"| TR
    R422 -->|"$ref"| HVE
    HVE -->|"$ref"| VE
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**`paths` の中には形の実体が無い。** 全部が `components.schemas` を指す矢印になっている。
`TodoRead` は `POST` の 201 からも `GET` の 200 からも指されているが、**実体は1か所**。
右下の `HTTPValidationError → ValidationError` は、**あなたが書いていないのに FastAPI が足した**もの（422 の形）。

---

### 6-2a. 🔤 入口の2行

#### 🔤 `GET /openapi.json`
**読み方**: 「オープン・エーピーアイ・ドット・ジェイソン」
**要するに**: **この API の取扱説明書を、機械が読める形で1枚にしたもの**。書いたコードから自動で作られる。

#### 🔤 `components.schemas` と `$ref`
**読み方**: 「コンポーネンツ・ドット・スキーマズ」「ダラー・レフ」（レフは reference の略）
**要するに**: `components.schemas` は**データの形の見本帳**。`$ref` は「**形は見本帳の何ページ目を見て**」という付箋。

#### 🔤 `tags=["todos"]` / `summary="..."`
**読み方**: 「タグズ・イコール…」「サマリー・イコール…」
**要するに**: 取扱説明書の**章分け**と、各ページの**見出し**。動きは何も変わらない。

---

### 6-2b. 🧰 【道具】`jq` の読み方（このステップで使う分だけ）

`jq` は **JSON を上から順にたどって、欲しいところだけ取り出す**道具。書き方はフォルダをたどるのに近い。

| 書き方 | 意味 | 例 |
| --- | --- | --- |
| `.` | 全体（そのまま整形して出す） | `jq .` |
| `.キー` | そのキーの中へ入る | `.info` → `{"title":"FastAPI","version":"0.1.0"}` |
| `.a.b` | 続けて入る | `.info.title` → `"FastAPI"` |
| `."/todos"` | **記号を含むキーは `""` で囲む** | `.paths."/todos"` |
| `keys` | 中にあるキーの**名前だけ**を並べる | `.paths \| keys` → `["/health","/todos"]` |
| `\|` | 左の結果を右に渡す（シェルのパイプと同じ考え方） | `.paths \| keys` |
| `-c` | 1行に詰めて出す（Compact） | `jq -c .info` |
| `-r` | 文字列の `""` を外して出す（Raw） | `jq -r .info.title` → `FastAPI` |

**いちばん転ぶところ**: `/` や `$` を含むキーを `""` で囲み忘れる。実際のエラーはこうなる。

```
$ jq '.paths./todos' openapi.json
jq: error: syntax error, unexpected '/', expecting FORMAT or QQSTRING_START or '[' at <top-level>, line 1, column 8:
    .paths./todos
           ^

$ jq '...schema.$ref' openapi.json
jq: error: syntax error, unexpected BINDING, expecting FORMAT or QQSTRING_START or '[' ...
```

✅ 検証済み: jq 1.8.2 で実際に出した出力。

`$ref` の `$` は、jq の中では「変数」の印なので、`."$ref"` と囲まないと別物として読まれる。
**`QQSTRING_START`（= `"` が来るはずだった）と言われたら、囲み忘れ**と覚えておく。

> 💡 コマンド全体は `'...'`（シングルクォート）で囲む。こうすると、中の `"` と `$` をシェルが勝手に解釈しない。

---

### 6-2. 🔬 仕組み解剖

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `GET /openapi.json` | OpenAPI スキーマ | `FastAPI()` を作った時点で、この経路が**自動で経路表に入っている**。**最初に叩かれたとき**に、経路表と各経路の型・デコレータの引数をすべて読んで JSON を組み立て、`app.openapi_schema` に**覚えておく**。2回目からは覚えたものを返すだけ |
| `components.schemas` / `$ref` | 再利用される形の定義 / 参照 | Pydantic がモデルごとに **JSON Schema**（JSON の形を書くための別の決まり）を作り、FastAPI がそれを `components.schemas` に1つずつ並べる。使う場所には実体ではなく `{"$ref": "#/components/schemas/名前"}` を置く |
| `tags=` / `summary=` / docstring | パスオペレーションのメタデータ | 起動時にデコレータが受け取り、経路表の行にメモとして付くだけ。**リクエストの処理には一切使われない**。`summary=` を省くと関数名から作られ（`create_todo` → `"Create Todo"`）、docstring は `description` になる |

**いつ評価されるか**: 型やデコレータの引数を読むのは起動時。JSON に組み立てるのは**最初に `/openapi.json` が叩かれたとき**（以後は使い回し。`--reload` で再起動すれば作り直される）。

**どの道具の責務か**: モデル1つぶんの形（`properties` / `required` / `minLength`）は **Pydantic** が JSON Schema として作る。
それを `paths` と組み合わせて1枚にまとめ、422 の形を足すのが **FastAPI**。画面に描くのは **Swagger UI / ReDoc**（ブラウザ側）。

**失敗したらどうなるか**: 読む側の失敗は無い。怖いのは**書いてあることと実際が違う**ほう。6-4 のなぜなぜ③で扱う。

#### 用語を分ける（§4.14）

| 呼び名 | 何を指すか | どこにあるか |
| --- | --- | --- |
| **OpenAPI** | API の仕様書を書くための**決まりそのもの**（昔は Swagger Specification と呼ばれていた） | 仕様の文書 |
| **OpenAPI スキーマ** | その決まりに従って FastAPI が**生成した JSON** | `GET /openapi.json` |
| **Swagger UI** | その JSON を読んで**画面に描き、試し打ちもできる道具** | `GET /docs` |
| **ReDoc** | 同じ JSON を**読み物の見た目**で描く道具（試し打ちは無い） | `GET /redoc` |

**「Swagger を見て」は、この4つのどれかが曖昧。** この教材では必ず4つの名前で呼び分ける。
根拠: https://fastapi.tiangolo.com/tutorial/first-steps/#openapi ／ https://swagger.io/specification/

#### コードの1行が、スキーマのどこに出るか

| コード | スキーマ上の場所と値 |
| --- | --- |
| `@app.post("/todos")` | `paths."/todos".post` |
| 関数名 `create_todo` | `operationId: "create_todo_todos_post"`（関数名 + パス + メソッド） |
| `todo: TodoCreate` | `requestBody` → `$ref: TodoCreate`、`"required": true` |
| `Field(min_length=1, max_length=200)` | `TodoCreate.properties.title` の `"minLength": 1` / `"maxLength": 200` |
| `done: bool = False` | `"default": false`、そして `required` に**入らない** |
| `extra="forbid"` | `"additionalProperties": false` |
| `status_code=201` | `responses."201"`（200 は**消える**） |
| `-> TodoRead` | `responses."201"` → `$ref: TodoRead` |
| （書いていない） | `responses."422"` → `$ref: HTTPValidationError` |
| `-> list[TodoRead]` | `"type": "array"`、`"items"` → `$ref: TodoRead` |
| `-> dict[str, str]` | `"type": "object"`、`"additionalProperties": {"type": "string"}` |

**P1a で書いた宣言は、ほぼ全部ここに出ている。** 6-6 で1つずつ `jq` で確かめる。

---

### 6-3. 🐍 Python解説

#### 🐍 `"""..."""`（docstring）

```python
def create_todo(todo: TodoCreate) -> TodoRead:
    """
    タイトルを受け取り、ID を振って保存する。

    - 知らない欄を送ると 422
    """
```

**読み方**: 「トリプル・クォート」。中身は「ドックストリング」（documentation string の略）

**たとえ**: 関数に付ける**取扱説明の貼り紙**。`#` のメモは Python が捨ててしまうが、こちらは**関数に貼り付いたまま残る**。

**正確には**:
- `"""` で始めて `"""` で閉じると、**改行を含む文字列**を書ける（`"..."` は1行だけ）
- その文字列を**関数の中身の一番最初**に置くと、特別に **docstring** として扱われ、関数にくっついて保存される。2行目以降に置くと、ただの捨てられる文字列になる
- **FastAPI はこれを読んで、仕様書の `description` にする**。字下げは自動で取り除かれ、Markdown（`- ` の箇条書きなど）としても解釈される
- `#` のコメントとの使い分け: `#` は**コードを読む人**へのメモ、docstring は**関数を使う人**への説明

**TS なら**: 関数の上に書く `/** ... */`（JSDoc）が近い。違いは**置く場所が関数の中**であることと、**実行中のプログラムから読める**こと（JSDoc はコンパイル後には残らない）。

> 💡 あなたがブランクページ再現で `"""Health check endpoint"""` と書いていたのが、まさにこれ。
> `/health` に付けていれば、`paths."/health".get.description` に `"Health check endpoint"` が出る。

---

### 6-3a. 🐍 Python の道具立て ／ 6-3b. 🧩 周辺注

このステップでは該当なし（`jq` は 6-2b で扱った）。

---

### 6-4. 解説 — なぜこう設計するか

#### 🪜 なぜなぜ: なぜ仕様書を手で書かず、コードから作るのか

**なぜ① `/openapi.json` の中身は、どこから来ているのか**
→ **起動時に経路表に登録されたもの全部**から。デコレータの引数（`status_code=` / `tags=`）、引数の型（`TodoCreate`）、戻り値の型（`TodoRead`）を、FastAPI が最初の `/openapi.json` のときにまとめて読み、1枚の JSON に組み立てる。
**あなたは仕様書を1行も書いていない**のに、`minLength` まで入っていたのはそのため。

**なぜ② 仕様書を別に手で書く（`openapi.yaml` を用意する）のでは、なぜだめなのか**
→ **2か所に書いたものは、いつか必ずズレる**から（P1-2 の なぜなぜ② と同じ理屈）。
`max_length` を 200 から 100 に変えたのに `openapi.yaml` を直し忘れると、フロントエンドは古い約束のまま作り続ける。
コードから作れば、**仕様書は実装の写し**になり、ズレようがない。P1-3 のなぜなぜ② で「宣言だから機械に読める」と書いたのは、ここに繋がっている。
根拠: https://fastapi.tiangolo.com/features/#automatic-docs

**なぜ③ では、コードから作る方式は何を失うのか** 🤔 まず自分で考える

<details><summary>答え</summary>

2つ失う。

**1. 宣言していないことは、仕様書に出ない。**
「実装の写し」と言ったが、正確には**宣言の写し**。宣言の外で起きることは写らない。

- P1-5 の 5-6 Q3 で起こした **500** は、`responses` のどこにも無い（6-6 の Q3 で確かめる）
- 次の P1-7 で `HTTPException(404)` を投げるようにしても、**投げるだけでは 404 は仕様書に出ない**

→ **手当て**（§4.2.1 ルール6）: **P1-7** で `responses=` を使い、「このエンドポイントは 404 も返す」と**宣言として**書き足す。
仕様書に出したいことは、**型かデコレータの引数で宣言する**。これが FastAPI で仕様書を正しく保つための唯一の方法。

**2. 「先に仕様書を決めてから作る」進め方がしにくい。**
フロントエンドと先に約束だけを決めて、並行して作りたい場面がある（**スキーマファースト**と呼ばれる進め方）。
コードから作る方式では、**コードを書くまで仕様書が存在しない**。

→ **この教材では手当てしない。** 仕様書から Python のコードを生成する道具はあるが、FastAPI の中心的な使い方から外れる。
代わりに、**中身が空のエンドポイント（型だけ書いて `...`）を先に作って仕様書を渡す**、という逃げ方はできる。
</details>

> 🧠 **FastAPI の考え方**: 仕様書は「書くもの」ではなく「**宣言から出てくるもの**」。
> だから仕様書に載せたいことは、**コメントではなく宣言として書く**。宣言していないことは、仕様書にとって存在しない。

---

### 6-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: `tags=` は**リソース単位**（`todos` / `users`）で付ける。Swagger UI はタグごとにエンドポイントをまとめて表示し、
> OpenAPI スキーマからクライアントのコードを自動生成する道具の多くも、**タグ単位でファイルやクラスを分ける**。
> 根拠: https://fastapi.tiangolo.com/advanced/generate-clients/#generate-a-typescript-client-with-tags

> ⚠️ **アンチパターン**: 仕様書に載せたい条件を、**docstring にだけ**書く（「title は 200 文字まで」と説明文に書いて、`max_length=200` を書かない）。
> docstring は人間が読む説明で、**検証もされず、機械も読めない**。条件は `Field()` に、説明は docstring に、と分ける。
> 根拠: https://fastapi.tiangolo.com/tutorial/path-operation-configuration/#description-from-docstring

---

### 6-6. 🔮 予測 → 動作確認

**先に予想してから実行する。**

1. `/openapi.json` の一番上の階層には、キーがいくつあるか。`TodoCreate` の `required` には何が入っているか
2. `POST /todos` の `responses` のキーは何か。**P1-5 の 5-6 Q3 で起こした 500 は入っているか**
3. `components.schemas` には、いくつの形が載っているか。**自分で書いていないもの**はあるか

サーバを起動しておく。

```bash
uv run uvicorn app.main:app --port 8000 --reload
```

<details><summary>実行と結果</summary>

**1 の答え: 4つ。`required` は `["title"]` だけ**

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq 'keys'
```
```json
["components", "info", "openapi", "paths"]
```

上から順に読む（§4.14）。

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq -c '{openapi, info}'
curl -s http://127.0.0.1:8000/openapi.json | jq -c '.paths | keys'
```
```
{"openapi":"3.1.0","info":{"title":"FastAPI","version":"0.1.0"}}
["/health","/todos"]
```

- `openapi`: 準拠している OpenAPI の版。FastAPI が決める
- `info`: API の名前と版。`FastAPI()` に何も渡していないので既定値のまま（この教材では変えない）
- `paths`: P1-3 で作った `/items/` は、**消したので載っていない**

`TodoCreate` の中身:

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq '.components.schemas.TodoCreate'
```
```json
{
  "properties": {
    "title": { "type": "string", "maxLength": 200, "minLength": 1, "title": "Title" },
    "done": { "type": "boolean", "title": "Done", "default": false }
  },
  "additionalProperties": false,
  "type": "object",
  "required": ["title"],
  "title": "TodoCreate"
}
```

（読みやすさのため、`properties` の中だけ1行に詰めて貼った）

**`done` は `= False` があるので `required` に入らない。** P1-4 の「既定値があれば任意」が、そのまま仕様書に写っている。
`extra="forbid"` は `"additionalProperties": false` になった。**仕様書を読むだけで、フロントエンドは「余計な欄を送ると弾かれる」と分かる。**

**2 の答え: `["201", "422"]`。500 は入っていない**

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq '.paths."/todos".post.responses | keys'
```
```json
["201", "422"]
```

- `201`: `status_code=201` を書いたので、既定の `200` が**置き換わった**
- `422`: **書いていないのに入っている**。ボディを受け取る以上、形が合わないことがありうるので、FastAPI が自動で足す
- **500 は無い。** P1-5 で実際に 500 を返せたのに、仕様書には一言も書かれていない。**宣言の外で起きたことは写らない**（6-4 のなぜなぜ③）

`$ref` をたどってみる。

```bash
curl -s http://127.0.0.1:8000/openapi.json \
  | jq -r '.paths."/todos".post.requestBody.content."application/json".schema."$ref"'
```
```
#/components/schemas/TodoCreate
```

**この文字列は、そのまま jq の道順になっている。** `#` が「この JSON の一番上」、`/` が「中へ入る」。

```
#/components/schemas/TodoCreate
 → jq '.components.schemas.TodoCreate'
```

**3 の答え: 4つ。そのうち2つは自分で書いていない**

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq -c '.components.schemas | keys'
```
```json
["HTTPValidationError","TodoCreate","TodoRead","ValidationError"]
```

`TodoCreate` と `TodoRead` はあなたのクラス。**`HTTPValidationError` と `ValidationError` は FastAPI が足した 422 の形**。

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq -c '.components.schemas.ValidationError.required'
```
```json
["loc","msg","type"]
```

**P1-3 から読んできた 422 の `loc` / `msg` / `type` は、ここで「必ずある欄」として約束されていた。** `input` と `ctx` は `required` に入っていない（無いこともある）。

**おまけ: 戻り値の型も写っている**

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq -c '.paths."/todos".get.responses."200".content."application/json".schema'
```
```json
{"items":{"$ref":"#/components/schemas/TodoRead"},"type":"array","title":"Response List Todos Todos Get"}
```

`-> list[TodoRead]` が「`TodoRead` を並べた配列」として書かれている。
</details>

✅ 検証済み（上の出力はすべて実行して取得。`TodoCreate` の出力だけ、`properties` の中を1行に詰めて貼った）。

#### Swagger UI / ReDoc で見る — 🧑 読者が検証

**Swagger UI の画面操作は生成側では実行できない**ので、手順と判定基準を書く（§4.6(c)）。

1. ブラウザで `http://127.0.0.1:8000/docs` を開く
2. **`health` と `todos` の2つの見出しに分かれている**ことを確かめる（`tags=` を付けた後。付ける前は `default` 1つにまとまっている）
3. `POST /todos` を開き、見出しの横に **`TODO を1件作る`**（`summary=`）、その下に **docstring の箇条書き**が出ていることを確かめる
4. **Try it out** → Request body を `{"title": ""}` に書き換える → **Execute**
5. **判定基準**: Responses の **Server response** に `422` と、`"loc": ["body", "title"]` を含むボディが出る。
   その上の **Curl** 欄に、実際に送ったコマンドが出ている（自分で書いた `curl` と見比べる）
6. 同じ手順で `{"title": "牛乳を買う"}` を送り、**`201`** と `"id"` を含むボディが返ることを確かめる
7. 画面の一番下の **Schemas** に、`TodoCreate` / `TodoRead` / `HTTPValidationError` / `ValidationError` の4つが並んでいることを確かめる（6-6 の Q3 と同じもの）
8. `http://127.0.0.1:8000/redoc` も開き、**同じ内容が、試し打ちボタンの無い読み物の形**で出ることを確かめる

**スクリーンショット**: 手順5で 422 が返った状態の、**Responses の Server response の部分**（ステータス `422` とボディが両方入る範囲）を撮り、
`docs/images/p1-6-swagger-try-it-out-422.png` に保存する。

![Swagger UI の Try it out で空のタイトルを送り、422 と loc が返った画面](images/p1-6-swagger-try-it-out-422.png)

> ⚠️ **Try it out は本物のリクエスト**。手順6で作った TODO は、`GET /todos` にも本当に増えている。

---

### 6-6b. 🧾 OpenAPI スキーマの差分

**今回からは毎回、コードの変更で仕様書がどう変わったかを見る**（§4.14）。
`tags=` / `summary=` / docstring を足す前と後で、`POST /todos` の見出しまわりを比べる。

```bash
curl -s http://127.0.0.1:8000/openapi.json \
  | jq '.paths."/todos".post | {tags, summary, description, operationId}'
```

**足す前（P1-5 の状態）**
```json
{ "tags": null, "summary": "Create Todo", "description": null, "operationId": "create_todo_todos_post" }
```

**足した後**
```json
{
  "tags": ["todos"],
  "summary": "TODO を1件作る",
  "description": "タイトルを受け取り、ID を振って保存する。\n\n- 知らない欄を送ると 422\n- 成功すると 201",
  "operationId": "create_todo_todos_post"
}
```

✅ 検証済み（「足す前」は1行に詰めて貼った）。

- `summary` は、書かなければ**関数名から自動で作られていた**（`create_todo` → `Create Todo`）
- `description` は docstring から。**先頭の字下げは取り除かれている**
- `operationId` は**変わらない**。関数名とパスとメソッドから作られるので、`summary=` とは無関係
- `null` と出ているのは「そのキーが**無い**」という意味（jq が無いキーを `null` として見せている）

**変わったのは見出しまわりだけで、`requestBody` と `responses` は1文字も変わっていない。** `tags=` と `summary=` は**動きを変えない**ことが、差分からも分かる。

---

### 6-7. ✅ 想起チェック

1. OpenAPI / OpenAPI スキーマ / Swagger UI / ReDoc を、それぞれ1行で区別せよ
2. `"$ref": "#/components/schemas/TodoRead"` を `jq` で開くには、どう書くか
3. `TodoCreate` の `required` に `done` が入っていないのはなぜか
4. `POST /todos` は 500 を返しうるのに、`responses` に 500 が無いのはなぜか
5. 「コードを直したのに Swagger UI が変わらない」とき、最初に何を確かめるか

<details><summary>答え</summary>

1. **OpenAPI** = 仕様書の書き方の決まり ／ **OpenAPI スキーマ** = FastAPI が作った JSON（`/openapi.json`）／
   **Swagger UI** = その JSON を画面にして試し打ちできる道具（`/docs`）／ **ReDoc** = 同じ JSON を読み物にする道具（`/redoc`）
2. `jq '.components.schemas.TodoRead'`。`#` が一番上、`/` が「中へ入る」
3. **`= False` という既定値があるから。** 既定値があれば任意、という P1-4 の規則がそのまま写っている
4. **仕様書は宣言の写しで、500 はどこにも宣言していないから。** 出したいなら `responses=` で宣言する（P1-7）
5. **`/openapi.json` を `jq` で見る。** JSON が古ければサーバ側（再起動されているか）、JSON が新しければブラウザ側（再読み込み）
</details>

---

### 6-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `GET /openapi.json`（と `/docs` / `/redoc`） | 6-2a / 6-2 で仕組み解剖（初回に組み立てて覚える）/ 用語の表 / 6-6 / 🧑 Swagger UI の手順 |
| `components.schemas` と `$ref` | 6-2a / 6-1b(b) の図 / 6-6 の Q1〜Q3 で実物をたどる |
| `tags=` / `summary=` | 6-2a / 6-2 / 6-5 実務メモ / 6-6b で差分 |
| `"""..."""`（docstring） | 6-3 で Python解説 / 6-6b で `description` になるのを確認 |
| `jq` の読み方 | 6-2b（実際のエラー出力つき）/ **P1-5 の ⏭️「jq の書き方は P1-6」を回収** |
| 以前の ⏭️ | **P1-2 の `/docs`、P1-3 の `parameters`、P1-4 の `requestBody` と `minLength`、P1-5 の `["201","422"]` を 6-6 でまとめて回収** |
| 宣言していないものは出ない | 6-4 なぜなぜ③ / 6-6 Q2 / ⏭️ **P1-7 の `responses=` で回収** |

> P1-3 の 3-6b で予告した `parameters`（`"in": "path"` / `"in": "query"`）は、`/items/` を P1-4 で消したので**今の仕様書には無い**。
> P1-7 で `GET /todos/{todo_id}` を作ると、`"in": "path"` として再び現れる。そこで確かめる。

**未回収: 0件**（`⏭️` 宣言は2件、どちらも P1-7 で回収）

---

### 6-9. 📌 進捗の更新

`README.md` の進捗表 P1b を「**P1-6 完了**（5ステップ中1。v11 で P1-10 が増えた）」、次の一手を `M1: P1 ステップ7` に更新した。

**次のステップ**: P1-7「残りの CRUD と 404」。`GET /todos/{todo_id}` / `PUT` / `DELETE` を足し、見つからないときに **404** を返す。
**404 を返すだけでは仕様書に出ない**ことを 6-6b の差分で確かめ、`responses=` で宣言して出す。
P1-5 の 🔓 で予告した「`DELETE` の後に `id` が重なる」も、ここで予測問題として踏む。

---

## P1-7: 残りの CRUD と 404

**作るもの**: `GET /todos/{todo_id}` / `PUT /todos/{todo_id}` / `DELETE /todos/{todo_id}` を足し、**無い ID には 404** を返す。そのうえで 404 を**仕様書にも載せる**
**重要度**: 🔴 毎日使う — 「1件取る・直す・消す」と「無ければ 404」は、どの API にも必ずある形のため
**前ステップとの接続**: P1-6 の なぜなぜ③ で「**宣言していないことは仕様書に出ない**」と書いた。その実物をここで作り、`responses=` で直す。P1-5 の 🔓 で予告した **ID の重なり**もここで踏む

### 7-0. このステップの初出トークン

| 系統 | トークン |
| --- | --- |
| **FastAPI** | `HTTPException` / `status` 定数（`status.HTTP_404_NOT_FOUND` など）/ `responses=`（3つ = 上限） |
| **Python** | `for ... in ...:` / `if ...:` / `==` / `raise` / 途中の `return` / `todo.title = ...`（欄への代入）/ `.remove()` / `-> None` / `from itertools import count` と `next()` |
| **【道具】** | —（該当なし） |
| **周辺** | — |

> `@app.put` と `@app.delete` は、`@app.post` の**メソッド違い**なので初出に数えない（P1-4 の 4-2 と同じ仕組み）。

---

### 7-1. コード（段階1: まず動かす）

**2段階で書く。** 段階1では「404 を投げるだけ」「ID の振り方は今のまま」で動かし、7-6 で**その問題を2つ踏んでから**段階2で直す。

#### 要件（段階1）

1. `find_todo(todo_id)` という**普通の関数**（`@` の貼り紙なし）を作る。リストから ID が一致する TODO を探して返し、**無ければ 404 を投げる**
2. `GET /todos/{todo_id}`: 1件返す
3. `PUT /todos/{todo_id}`: ボディは `TodoCreate`。**`title` と `done` を丸ごと置き換えて**、置き換えた後の TODO を返す
4. `DELETE /todos/{todo_id}`: 消して **204**（ボディ無し）を返す
5. 3つとも、無い ID なら **404**、ボディは `{"detail": "TODO が見つかりません"}`
6. ステータス番号は**数字で書かず** `status.HTTP_201_CREATED` のような定数で書く（既存の `201` も置き換える）
7. `id` の振り方（`len(todos) + 1`）は**まだ変えない**

#### 骨組み: `app/main.py`（足す部分だけ）

```python
from fastapi import FastAPI, HTTPException, status


def find_todo(todo_id: int) -> TodoRead:
    # TODO: todos を1件ずつ見て、id が一致したらそれを返す
    # TODO: 最後まで見つからなければ 404 の HTTPException を raise する
    ...


@app.get("/todos/{todo_id}")  # TODO: tags / summary
def read_todo(todo_id: int) -> TodoRead:
    ...


@app.put("/todos/{todo_id}")  # TODO: tags / summary
def update_todo(todo_id: int, body: TodoCreate) -> TodoRead:
    # TODO: find_todo で取ってきて、title と done を body の値で書き換えて返す
    ...


@app.delete("/todos/{todo_id}")  # TODO: 204 / tags / summary
def delete_todo(todo_id: int) -> None:
    # TODO: find_todo で取ってきて、リストから取り除く（return は書かない）
    ...
```

<details><summary>段階1の完成形（自分で書いてから開く）</summary>

`app/main.py`（全文）

```python
from fastapi import FastAPI, HTTPException, status

from app.schemas.todo import TodoCreate, TodoRead

app = FastAPI()

todos: list[TodoRead] = []


def find_todo(todo_id: int) -> TodoRead:
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TODO が見つかりません")


@app.get("/health", tags=["health"], summary="死活確認")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/todos",
    status_code=status.HTTP_201_CREATED,
    tags=["todos"],
    summary="TODO を1件作る",
)
def create_todo(todo: TodoCreate) -> TodoRead:
    new_todo = TodoRead(id=len(todos) + 1, title=todo.title, done=todo.done)
    todos.append(new_todo)
    return new_todo


@app.get("/todos", tags=["todos"], summary="TODO 一覧を取得")
def list_todos() -> list[TodoRead]:
    return todos


@app.get("/todos/{todo_id}", tags=["todos"], summary="TODO を1件取得")
def read_todo(todo_id: int) -> TodoRead:
    return find_todo(todo_id)


@app.put("/todos/{todo_id}", tags=["todos"], summary="TODO を丸ごと置き換える")
def update_todo(todo_id: int, body: TodoCreate) -> TodoRead:
    todo = find_todo(todo_id)
    todo.title = body.title
    todo.done = body.done
    return todo


@app.delete(
    "/todos/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["todos"],
    summary="TODO を削除する",
)
def delete_todo(todo_id: int) -> None:
    todo = find_todo(todo_id)
    todos.remove(todo)
```

（`create_todo` の docstring は紙幅のため省いた。残しておいてよい）

</details>

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Pydantic 2.13.5 / jq 1.8.2。
段階1・段階2の完成形をそれぞれ別の場所にコピーして `ruff check` / `ruff format --check` / `mypy` がすべて通ることを確認。実レスポンスは 7-6。

---

### 7-1b. 📊 図解

#### (a) `raise` は、呼んだ関数を飛び越えて FastAPI まで届く

```mermaid
sequenceDiagram
    participant C as curl
    participant F as FastAPI
    participant H as read_todo()
    participant FT as find_todo()

    C->>F: GET /todos/99
    F->>H: todo_id=99 で呼ぶ
    H->>FT: find_todo(99)
    FT->>FT: 全部見たが無い
    FT--xF: raise HTTPException(404)
    Note over H: return まで進まない
    F--xC: 404 {"detail": "TODO が見つかりません"}
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**`find_todo` から投げた 404 は、`read_todo` の中を素通りして FastAPI まで届く。** `read_todo` の `return` は実行されない。
`read_todo` の側に「見つからなかったら…」という `if` が1行も無いのは、このため。

#### (b) `len(todos) + 1` で番号を振ると、なぜ重なるのか

```mermaid
flowchart LR
    A["3件ある<br/>id 1, 2, 3"]
    B["id 1 を削除<br/>残り id 2, 3"]
    C["次の番号は<br/>len 2 + 1 = 3"]
    D["id 3 が2件"]
    E["GET /todos/3 は<br/>先に見つかった方だけ"]
    A --> B --> C --> D --> E
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**「件数 + 1」は、消さないうちだけ「最後の番号 + 1」と一致する。** 消した瞬間にずれる。7-6 の Q3 で実際に起こす。

---

### 7-2a. 🔤 入口の2行

#### 🔤 `raise HTTPException(status_code=404, detail="...")`
**読み方**: 「レイズ・エイチティーティーピー・エクセプション、ステータスコード…、ディテール…」
**要するに**: **「この話はここで打ち切り。お客さんにはこの番号とこの一言を返して」**と、途中から店長に伝える非常ボタン。

#### 🔤 `status.HTTP_404_NOT_FOUND`
**読み方**: 「ステータス・ドット・エイチティーティーピー・よんまるよん・ノット・ファウンド」
**要するに**: **番号に名札を付けたもの**。中身はただの `404` だが、読んだだけで意味が分かる。

#### 🔤 `responses={404: {"description": "..."}}`
**読み方**: 「レスポンシズ・イコール…」
**要するに**: 取扱説明書に「**こういう失敗の返事もあります**」と書き足す欄。動きは変えない。

---

### 7-2. 🔬 仕組み解剖

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `raise HTTPException(...)` | HTTP エラーの例外 | 投げた瞬間に、その関数も**呼び出し元の関数も**途中で止まる。FastAPI（正確には Starlette の例外の受け口）が受け取り、`{"detail": ...}` の JSON と指定の番号に変える。**`detail` は文字列そのまま**（422 の `detail` は配列だった。読み分ける） |
| `status.HTTP_404_NOT_FOUND` | ステータスコードの定数 | 中身は整数の `404`。**実行時の違いは一切無い**。違いは**読みやすさ**と**エディタの補完**。⚠️ ただし打ち間違い（`HTTP_404_NOT_FUOND`）は **ruff も mypy も止めない**（下の注） |
| `responses={...}` | 追加のレスポンス | **起動時に**デコレータが受け取り、仕様書の `responses` に1行足すだけ。**404 を返す動き自体は `raise` が作っている**。`responses=` を書かなくても 404 は返るし、書いても `raise` が無ければ返らない |

**いつ評価されるか**: `responses=` と `status_code=` は起動時。`raise` はリクエストごと（見つからなかったときだけ）。

> ⚠️ **定数の打ち間違いは、実行されるまで見つからない**（実際に試して確認した）
> `status` の中身は Starlette が用意していて、**古い名前でも動くようにする仕組み**（名前を受け取って整数を返す関数）を持っている。
> そのため mypy には「`status.` の後ろには**どんな名前でも**整数がある」ように見え、`HTTP_404_NOT_FUOND` も通してしまう。
> 実行すると `AttributeError: module 'starlette.status' has no attribute 'HTTP_404_NOT_FUOND'` になる。
> - **デコレータの中**（`status_code=...`）で打ち間違えた → **起動時に**落ちるので、すぐ気づく
> - **`raise` の中**で打ち間違えた → **404 になるはずのリクエストが来たときに初めて**落ち、しかも **500** になる
>
> 後者は、正常系しか試していないと気づけない。**失敗の道も1回は叩く**（7-6 がまさにそれ）。P6 のテストで 404 のケースを書くのは、これを自動で見つけるため。

**どの道具の責務か**: 例外を投げるのは**あなたのコード**、受け取って JSON に変えるのは **Starlette / FastAPI**、仕様書に書くのは **`responses=` を読んだ FastAPI**。
**動き（`raise`）と宣言（`responses=`）が別の場所にある**のが、このステップの要点。

**失敗したらどうなるか**: 3つを区別する。

| リクエスト | 番号 | どこで決まったか |
| --- | --- | --- |
| `GET /todos/99` | **404** `{"detail":"TODO が見つかりません"}` | あなたの `raise` |
| `GET /todos/abc` | **422** `loc: ["path","todo_id"]` | 入口の門（ハンドラは呼ばれない。P1-3 と同じ） |
| `PUT /todos`（ID 無し） | **405** | 経路表（パスはあるがメソッドが違う。P1-2 と同じ） |

**既知スタックとの対応**: Express の `res.status(404).json({...}); return;` が近い。
違いは、Express では**呼んだ関数の中からは返せない**（`res` を渡すか、戻り値で知らせて呼び出し元で分岐する）のに対し、
`raise` は**何段下の関数からでも**一気に FastAPI まで届くこと。NestJS の `throw new NotFoundException()` は、ほぼ同じ考え方。

---

### 7-3. 🐍 Python解説

#### 🐍 `for todo in todos:`

**読み方**: 「フォー・トゥードゥー・イン・トゥードゥーズ」

**たとえ**: ファイルに綴じた用紙を、**上から1枚ずつめくって見る**。いまめくっている1枚を `todo` と呼ぶ。

**正確には**:
- `for 名前 in 入れ物:` = 入れ物の中身を**先頭から1つずつ**取り出し、そのたびに字下げされた範囲を実行する
- `todo` という名前は**ここで初めて作られる**。1周ごとに、次の中身を指すように付け替わる
- 最後まで見終わると、`for` の下（字下げが戻った行）に進む
- 行末の `:` と字下げは `def` / `class` と同じ（P1-2 の 2-3）

**TS なら**: `for (const todo of todos) { ... }`。**`of` ではなく `in`**、`()` と `{}` が無く字下げで範囲を表す。
⚠️ TS の `for...in` はキー（添え字）を回すが、**Python の `for...in` は中身そのもの**を回す。名前が同じで意味が違うので注意。

#### 🐍 `if todo.id == todo_id:`

**読み方**: 「イフ・トゥードゥー・ドット・アイディー・イコールイコール・トゥードゥー・アイディー」

**たとえ**: 「**もし番号が一致したら**、下の作業をする」。一致しなければ飛ばす。

**正確には**:
- `if 条件:` = 条件が成り立つときだけ、字下げされた範囲を実行する
- `==` = 左右が**同じ値か**を調べる。`=`（名前を付ける）とは別物。`if todo.id = todo_id:` と書くと**文法エラー**で起動しない
- TS の `===` にあたる。Python には `===` は無く、`==` が「型も含めて同じか」を見る（`1 == "1"` は `False`）

**TS なら**: `if (todo.id === todoId) { ... }`。`()` と `{}` が無い。

#### 🐍 途中の `return` と、最後の `raise`

```python
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(...)
```

**正確には**:
- `return` は**その場で関数を終わらせる**（P1-2 の 2-3）。`for` の途中でも、見つかった時点で抜ける
- だから `raise` の行に来るのは、**最後まで見て一度も `return` しなかったとき**だけ
- `raise 例外` = **例外（「もう続けられない」という知らせ）を投げる**。投げた瞬間に関数が止まり、呼んだ側の関数も止まり、**受け取る人がいるところまで**一気に戻る。FastAPI では、受け取るのは FastAPI 自身

**TS なら**: `raise` は `throw`。`HTTPException(...)` の前に `new` は付けない（P1-5 の 5-3）。

#### 🐍 `todo.title = body.title`（欄への代入）

**正確には**: P1-5 の `todo.title` は**欄を読む**だった。左側に置いて `=` を付けると、**欄の中身を書き換える**。
`find_todo` が返したのは**リストに入っているのと同じ1枚**（コピーではない）なので、書き換えればリストの中身も変わっている。TS のオブジェクトと同じ。

⚠️ **Pydantic は、この代入では検証しない**（既定の設定）。`todo.title = ""` と書いても通ってしまう。
ここでは `body` が入口の門を通った後なので安全だが、「代入でも検証されている」と思い込まない。

#### 🐍 `todos.remove(todo)` と `-> None`

**正確には**:
- `.remove(x)` = リストから **x と同じものを1つ**取り除く（`append` の逆）。リストそのものが変わる
- `-> None` = 「**何も返さない**」関数の印。`return` を書かないと、関数は自動で `None` を返す
- FastAPI は `status_code=204` と `None` の組み合わせで、**ボディの無い**レスポンスを返す

**TS なら**: `.remove` に直接の対応物は無い（`splice(indexOf(x), 1)`）。`-> None` は `: void`。

#### 🐍 `from itertools import count` / `next(todo_ids)`（段階2で使う）

**読み方**: 「フロム・イターツールズ・インポート・カウント」「ネクスト」

**たとえ**: 銀行の**番号札の発券機**。ボタンを押すたびに 1, 2, 3, ... と1枚ずつ出てくる。**前の人が帰っても、番号は戻らない**。

**正確には**:
- `count(1)` = 1 から始まる番号を**1つずつ出せる**ものを作る。まだ番号は出ていない
- `next(x)` = x から**次の1つ**を取り出す。`count` に対して呼ぶたびに、1, 2, 3, ... と増える
- `itertools` は Python に**最初から付いている**部品箱（`uv add` は要らない）

**TS なら**: 対応物なし（ジェネレータ関数 `function*` で自作すれば近いものは作れる）。単に `let nextId = 1; nextId++` と書くのが一番近い。
Python で同じことを関数の中から書き換えるには別の文法（`global`）が要るので、ここでは発券機を使う。

---

### 7-3a. 🐍 Python の道具立て ／ 7-3b. 🧩 周辺注

このステップでは該当なし。

---

### 7-4. 解説 — なぜこう設計するか

#### 🪜 なぜなぜ: なぜ 404 は `return` せずに `raise` するのか

**なぜ① `find_todo` の中で `raise` すると、なぜ `read_todo` を飛び越えて 404 になるのか**
→ 例外は**受け取る人がいるところまで、呼び出しの道を逆向きに一気に戻る**（Python の言語の決まり）。
`read_todo` にも `find_todo` にも受け取る仕組みが無いので素通りし、その外側で待っている **FastAPI（Starlette）の例外の受け口**に届く。
受け口は `HTTPException` を見ると、中の `status_code` と `detail` から JSON のレスポンスを作る。
根拠: https://fastapi.tiangolo.com/tutorial/handling-errors/#use-httpexception

**なぜ② `return` で「404 です」と返すのでは、なぜだめなのか**
→ **`return` は呼んだ関数にしか届かない**から。`find_todo` が「404 です」と `return` すると、受け取るのは `read_todo` で、
`read_todo` / `update_todo` / `delete_todo` の3か所すべてに「404 が返ってきたら…」という `if` が要る。
さらに `find_todo` の戻り値の型が「`TodoRead` か、404 か」になり、**`-> TodoRead` と書けなくなる**（mypy が使う側に毎回の確認を求める）。
`raise` なら、**戻り値の型は「見つかった場合」だけを表し**、見つからない場合は別の道で FastAPI に直接届く。

**なぜ③ では、`raise` で飛ばす方式は何を失うのか** 🤔 まず自分で考える

<details><summary>答え</summary>

**「この関数は 404 を投げるかもしれない」が、どこにも書かれない。**
`def find_todo(todo_id: int) -> TodoRead:` を見ても、404 の可能性は読み取れない。mypy も知らない。
そして**仕様書にも出ない**（7-6 の Q2 で確かめる）。P1-6 の なぜなぜ③ で挙げた「宣言していないことは仕様書に出ない」の典型。

**手当て**（§4.2.1 ルール6）

| 失うもの | 手当て | 扱う場所 |
| --- | --- | --- |
| 仕様書に出ない | `responses=` で**宣言として**書き足す | **このステップの段階2** |
| 投げる場所が散らばる | 例外ハンドラで、例外 → レスポンスの変換を**1か所**にまとめる | **P5-3** |
| 関数の型に出ない | **この教材では手当てしない。** Python の型には「投げうる例外」を書く欄が無い（言語の設計）。関数名（`find_...` / `get_or_404` など）と docstring で伝えるのが慣習 |

</details>

> 🧠 **FastAPI の考え方**: **動きは `raise`、約束は `responses=`。** 別々に書くので、片方だけ直すとズレる。
> 404 を投げるコードを足したら、同じ PR で `responses=` も足す。

---

### 7-5. 🏢 実務メモ ／ ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> 🏢 **実務メモ**: ステータス番号は `status.HTTP_404_NOT_FOUND` のような**定数で書く**。中身は同じ整数だが、
> 読んだだけで意味が分かり、エディタが候補を出してくれる。FastAPI の公式もこの書き方を「名前を覚えるための近道」として紹介している。
> （打ち間違いは静的チェックでは見つからない。7-2 の注）
> 根拠: https://fastapi.tiangolo.com/tutorial/response-status-code/#shortcut-to-remember-the-names

> ⚠️ **アンチパターン**: 見つからないときに **200 と `null`** を返す。クライアントは「成功して中身が空」と「そもそも無い」を区別できない。
> HTTP の仕様は、対象が見つからないことを 404 で表すと定めている。
> 根拠: https://www.rfc-editor.org/rfc/rfc9110#name-404-not-found

> 🔓 **教材用の簡略化**: 段階2の発券機（`count`）は**サーバを再起動すると 1 に戻る**。リストも消えるので今は困らないが、
> データだけが残る仕組み（DB）にすると番号が重なる。
> **本番では**: 番号は DB に振らせる（**P3** の自動採番）。
> 根拠: https://dev.mysql.com/doc/refman/8.0/en/example-auto-increment.html

---

### 7-6. 🔮 予測 → 動作確認（段階1のコードで）

**先に予想してから実行する。**

1. `done: true` にした TODO に、`PUT` で `{"title":"..."}` だけを送ると、`done` はどうなるか
2. `GET /todos/{todo_id}` の `responses` のキーは何か。**404 は入っているか**
3. 3件作り、`id` 1 を消してから1件作る。**新しい TODO の `id` は何か**。その後 `GET /todos/3` は何を返すか

サーバを起動し、3件作っておく。

```bash
uv run uvicorn app.main:app --port 8000 --reload
```
```bash
for t in 牛乳 卵 パン; do
  curl -sS -X POST http://127.0.0.1:8000/todos \
    -H 'Content-Type: application/json' -d "{\"title\":\"$t\"}" | jq -c
done
```
```
{"id":1,"title":"牛乳","done":false}
{"id":2,"title":"卵","done":false}
{"id":3,"title":"パン","done":false}
```

（`for ... in ...; do ...; done` はシェルの繰り返し。Python の `for` と考え方は同じ。`-d` の中で `$t` を使うため、外側を `"` で囲んでいる）

<details><summary>実行と結果</summary>

**まず 404 / 422 / 405 の3つを見分ける**

```bash
curl -sS -w '%{stderr}%{http_code}\n' http://127.0.0.1:8000/todos/99 | jq -c
curl -sS -w '%{stderr}%{http_code}\n' http://127.0.0.1:8000/todos/abc | jq -c
curl -sS -w '%{stderr}%{http_code}\n' -X PUT http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' -d '{"title":"x"}' | jq -c
```
```
404
{"detail":"TODO が見つかりません"}
422
{"detail":[{"type":"int_parsing","loc":["path","todo_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"abc"}]}
405
{"detail":"Method Not Allowed"}
```

**`detail` の形が違う。** 404 は**文字列**（あなたが `detail=` に書いたもの）、422 は**配列**（Pydantic の失敗の一覧）。
クライアント側でエラーを表示するときは、この2つを読み分ける必要がある（揃えたくなったら **P5-3**）。

**1 の答え: `false` に戻る**

```bash
curl -sS -X PUT http://127.0.0.1:8000/todos/2 \
  -H 'Content-Type: application/json' -d '{"title":"卵を2パック","done":true}' | jq -c
curl -sS -X PUT http://127.0.0.1:8000/todos/2 \
  -H 'Content-Type: application/json' -d '{"title":"卵を3パック"}' | jq -c
```
```
{"id":2,"title":"卵を2パック","done":true}
{"id":2,"title":"卵を3パック","done":false}
```

ボディは `TodoCreate` なので、`done` を送らなければ**既定値の `false`** が入り、それで**丸ごと置き換え**られた。
これが PUT の意味（**送った内容で置き換える**）。一部だけ直したいなら PATCH という別のメソッドを使うのが普通だが、この教材では扱わない。
根拠: https://www.rfc-editor.org/rfc/rfc9110#name-put

**2 の答え: `["200", "422"]`。404 は入っていない**

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq -c '.paths."/todos/{todo_id}".get.responses | keys'
```
```json
["200","422"]
```

**さっき実際に 404 を返したのに、仕様書には無い。** `raise` は動きであって宣言ではないから（7-4 のなぜなぜ③）。

**3 の答え: 新しい TODO も `id: 3`。`GET /todos/3` は古いほうを返す**

```bash
curl -sS -w '%{stderr}%{http_code}\n' -X DELETE http://127.0.0.1:8000/todos/1 | jq -c
curl -sS -X POST http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' -d '{"title":"りんご"}' | jq -c
curl -sS http://127.0.0.1:8000/todos | jq -c
curl -sS http://127.0.0.1:8000/todos/3 | jq -c
```
```
204
{"id":3,"title":"りんご","done":false}
[{"id":2,"title":"卵を3パック","done":false},{"id":3,"title":"パン","done":false},{"id":3,"title":"りんご","done":false}]
{"id":3,"title":"パン","done":false}
```

- `DELETE` は `204` だけが出て、**JSON は何も出ない**（ボディが空なので `jq` は何もせずに終わる）
- `id: 3` が**2件**ある。残り2件なので `len(todos) + 1 = 3`
- `GET /todos/3` は `find_todo` が**先に見つけたほう**（パン）を返す。**りんごには、もう ID で届かない**
- 同じ `DELETE /todos/1` をもう一度送ると `404`（もう無いので）
</details>

✅ 検証済み（上の出力はすべて段階1のコードを実行して取得）。

### 7-6a. 段階2: 見つけた2つの問題を直す

#### 要件（段階2）

1. 3つのエンドポイントに `responses=` で **404 を宣言**する（説明文は「指定した ID の TODO が無い」）
2. `id` を**発券機**（`itertools.count`）で振り、**消しても番号が戻らない**ようにする

<details><summary>段階2の完成形（変わる部分だけ）</summary>

```python
from itertools import count

from fastapi import FastAPI, HTTPException, status

from app.schemas.todo import TodoCreate, TodoRead

app = FastAPI()

todos: list[TodoRead] = []
# 1, 2, 3, ... と番号を1枚ずつ出す発券機。消しても番号は戻らない
todo_ids = count(1)

# （find_todo と /health は段階1のまま）


@app.post(
    "/todos",
    status_code=status.HTTP_201_CREATED,
    tags=["todos"],
    summary="TODO を1件作る",
)
def create_todo(todo: TodoCreate) -> TodoRead:
    new_todo = TodoRead(id=next(todo_ids), title=todo.title, done=todo.done)
    todos.append(new_todo)
    return new_todo


@app.get(
    "/todos/{todo_id}",
    tags=["todos"],
    summary="TODO を1件取得",
    responses={status.HTTP_404_NOT_FOUND: {"description": "指定した ID の TODO が無い"}},
)
def read_todo(todo_id: int) -> TodoRead:
    return find_todo(todo_id)
```

`update_todo` と `delete_todo` にも、同じ `responses=...` の1行を足す。

</details>

✅ 検証済み: 段階2で同じ手順を踏むと、`id` 1 を消した後の新しい TODO は **`id: 4`**、さらに `id` 4 を消した後は **`id: 5`**。重ならない。

> ⚠️ **やりがち**: 3か所に同じ `responses=` を書くのが嫌で、辞書を変数に入れて使い回すと、**mypy が止める**。
> ```
> app/main.py:45: error: Argument "responses" to "get" of "FastAPI" has incompatible type "dict[int, dict[str, str]]"; expected "dict[int | str, dict[str, Any]] | None"  [arg-type]
> ```
> ✅ 検証済み（実際に出した出力）。
> 変数に入れると、mypy が中身から**狭い型**（`dict[int, dict[str, str]]`）を決めてしまい、FastAPI が求める**広い型**と合わなくなる。
> デコレータの中に直接書けば、mypy は「FastAPI が求める型として」中身を読むので通る。
> **今は3か所に書く。** 同じものを何度も書く問題は、次の **P1-8**（ルーターにまとめる回）で `APIRouter` 側にまとめて片付く。

---

### 7-6b. 🧾 OpenAPI スキーマの差分

`responses=` を足す前（段階1）と後（段階2）で、`/todos/{todo_id}` の3つのメソッドの `responses` を比べる。

```bash
curl -s http://127.0.0.1:8000/openapi.json \
  | jq -c '.paths."/todos/{todo_id}" | map_values(.responses | keys)'
```

**段階1**
```json
{"get":["200","422"],"put":["200","422"],"delete":["204","422"]}
```

**段階2**
```json
{"get":["200","404","422"],"put":["200","404","422"],"delete":["204","404","422"]}
```

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq -c '.paths."/todos/{todo_id}".get.responses."404"'
```
```json
{"description":"指定した ID の TODO が無い"}
```

✅ 検証済み（段階1・段階2のそれぞれで実行して取得。`map_values` は「各キーの中身に同じ処理をする」jq の書き方で、3メソッドを1行で比べるために使った）。

- **動き（404 を返すこと）は段階1から変わっていない。変わったのは仕様書だけ。**
- `404` には `description` しか無く、**ボディの形（`content`）が無い**。`{"detail": "..."}` という形までは宣言していないため。
  形まで載せる書き方（`responses={404: {"model": ...}}`）もあるが、この教材では扱わない
- P1-6 の 3-6b で予告した `parameters` が戻ってきた:

```bash
curl -s http://127.0.0.1:8000/openapi.json | jq -c '.paths."/todos/{todo_id}".get.parameters'
```
```json
[{"name":"todo_id","in":"path","required":true,"schema":{"type":"integer","title":"Todo Id"}}]
```

`"in": "path"` と `"type": "integer"`。P1-3 で書いた「パスにある名前の引数 → path、`int` → integer」が、そのまま写っている。

---

### 7-7. ✅ 想起チェック

1. `find_todo` の中で `raise` した 404 は、`read_todo` のどの行を実行せずに FastAPI に届くか
2. 404 の `detail` と 422 の `detail` は、形がどう違うか
3. `responses=` を書かずに 404 を返すと何が起きるか。`responses=` だけ書いて `raise` しないと何が起きるか
4. `len(todos) + 1` で番号を振ると、どういう手順で重なるか
5. `PUT` で `done` を送らないと `false` に戻るのはなぜか

<details><summary>答え</summary>

1. **`return find_todo(todo_id)` の `return`**。`find_todo` が戻ってこないので、`read_todo` はそこで止まる
2. **404 は文字列**（`detail=` に書いたもの）、**422 は配列**（Pydantic の失敗の一覧で、各要素に `loc` / `msg` / `type`）
3. 前者: **404 は返るが仕様書に載らない**。後者: **仕様書に 404 と書いてあるのに、実際には返らない**。どちらも「約束と動きのズレ」
4. 3件作る（1, 2, 3）→ 1 を消す（残り 2 件）→ `2 + 1 = 3` → **3 が2件**
5. **ボディが `TodoCreate` で、`done` の既定値が `False` だから。** PUT は送った内容で丸ごと置き換える
</details>

---

### 7-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `HTTPException` | 7-2a / 7-2 で仕組み解剖 / 7-1b(a) の図 / 7-4 なぜなぜ（代償の手当ては段階2・**P5-3**） |
| `status` 定数 | 7-2a / 7-2（打ち間違いが静的チェックを抜ける注つき）/ 7-5 実務メモ |
| `responses=` | 7-2a / 7-2 / 7-6a / 7-6b で差分（**P1-6 の ⏭️「P1-7 の `responses=` で回収」を回収**） |
| `for` / `if` / `==` / 途中の `return` / `raise` | 7-3 で Python解説 |
| 欄への代入 / `.remove()` / `-> None` | 7-3 で Python解説（代入は検証されない注意つき） |
| `itertools.count` / `next()` | 7-3 で Python解説 / 7-6a で使用 |
| ID の重なり | 7-1b(b) / 7-6 の Q3 で実際に踏み、7-6a で修正（**P1-5 の 🔓 を回収**） |
| `parameters`（`"in": "path"`） | 7-6b（**P1-3 の 3-6b、P1-6 の 6-8 の予告を回収**） |
| 同じ `responses=` を3回書く | ⏭️ **P1-8** で `APIRouter` にまとめる |

**未回収: 0件**（`⏭️` 宣言は2件: P1-8 / P5-3）

---

### 7-9. 📌 進捗の更新

`README.md` の進捗表 P1b を「**P1-7 完了**（5ステップ中2）」、次の一手を `M1: P1 ステップ8` に更新した。

**次のステップ**: P1-8「ルーター分割と依存性注入」。`/todos` の5つを `app/routers/todos.py` に移し、`app/main.py` を薄くする。
**`__init__.py` と import がここで本番**（壊れたときの読み方も）。`find_todo` を**依存（`Depends()`）**に変え、ハンドラの引数で受け取る形にする。
3回書いた `responses=` と `tags=` は `APIRouter` 側にまとめる。最後に `app.routes` で経路の一覧を確かめる（P1-2 の なぜなぜ③ の2つ目の手当て）。

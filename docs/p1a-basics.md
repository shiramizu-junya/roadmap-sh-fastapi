# P1a — 品質ゲートと FastAPI 基礎

`docs/_prompt.md` §6（M1）の出力。1ステップずつ追記していく。

---

## P1-1: 品質ゲートを先に立てる

**作るもの**: `git commit` したときに ruff と mypy が自動で走り、**通らなければコミットが止まる**状態
**重要度**: 🔴 毎日使う — この後の全ステップが「この2つを通ったコードしか載せない」前提で書かれるため（§4.6）
**前ステップとの接続**: 最初のステップ。**Python のコードはまだ1行も書かない**

### 1-0. このステップの初出トークン

| 系統 | トークン |
| --- | --- |
| **FastAPI** | —（このステップでは出ない） |
| **Python** | —（`.py` ファイルをまだ作らないため） |
| **【道具】** | `uv run` と `.venv`（§4.3.1-1） |
| **開発ツール** | `pyproject.toml` / `ruff` / `mypy` / `pre-commit` |
| **周辺** | — |

> 最初のステップに FastAPI が1つも出ないのは意図的。**後から入れると、それまでに書いたコードを一斉に直すことになる**（§2.4）。

---

### 1-1. コード

#### (1) `pyproject.toml` — **末尾に追記**（既存の `[project]` と `[dependency-groups]` はそのまま）

```toml
[tool.ruff]
# 1行の長さの上限。ruff format がこの幅で折り返す
line-length = 100
# 3.12 として解釈する（古い書き方を「古い」と判定できるようになる）
target-version = "py312"

[tool.ruff.lint]
# E: 書き方の統一 / F: 実際のバグ / I: import の並び順
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.12"
# 型の付いていない関数定義を許さない（P1 の段階ではこれだけ）
disallow_untyped_defs = true
```

**なぜこの4項目だけなのか**（設定名を並べるだけにしない。§4.12-14）

| 設定 | 何のために足すか |
| --- | --- |
| `line-length = 100` | 既定は 88。3つの引数に型を書くと 88 はすぐ超える。**折り返しが増えると差分が読みにくくなる**ので少し広げた |
| `target-version = "py312"` | これが無いと ruff は「どの版として読むか」を推測する。3.12 と伝えると、古い書き方の指摘が正確になる |
| `select = ["E", "F", "I"]` | 既定は `F` と `E` の一部だけ。**`I`（import の並び）を足すのが主目的**。並び順が人によって違うと、中身を変えていないのに差分が出る |
| `disallow_untyped_defs` | **P1 の段階ではこれだけ。** 関数に型を書く習慣をつけるのが狙い。P3 と P6 で段階的に締める（§2.4） |

> ⏭️ **後で回収**: mypy を `strict = true` にするのは **P6-4**。いきなり strict にすると、動かない設定として外されて終わるため。今は「関数に型を書く」だけを強制する。

#### (2) `.pre-commit-config.yaml` — **新規作成・全文**（リポジトリのルート）

```yaml
# コミットのたびに何を走らせるかの一覧
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff (lint) — バグと書き方を見る
        entry: uv run ruff check --fix
        language: system
        types_or: [python, pyi]
        require_serial: true

      - id: ruff-format
        name: ruff (format) — 見た目を揃える
        entry: uv run ruff format
        language: system
        types_or: [python, pyi]
        require_serial: true

      - id: mypy
        name: mypy — 型が合っているか見る
        entry: uv run mypy
        language: system
        types_or: [python, pyi]
        require_serial: true
```

#### (3) フックを仕掛ける

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

✅ 検証済み: macOS / uv 0.12.17 / Python 3.12.13 / ruff 0.16.8 / mypy 2.3.1 / pre-commit 4.6.2。
`--all-files` の実際の出力は **1-6** に貼った。

---

### 1-1b. 📊 図解

#### (a) 誰が何を持っているか

```mermaid
flowchart TB
    subgraph you["あなたが書くもの"]
        PP["pyproject.toml<br/>どう直すかの基準"]
        PC[".pre-commit-config.yaml<br/>いつ何を走らせるか"]
    end
    subgraph tools["道具"]
        UV["uv<br/>.venv と依存の管理"]
        RF["ruff<br/>書き方とバグ"]
        MY["mypy<br/>型"]
    end
    GIT["git commit"]
    PP --> RF
    PP --> MY
    PC --> GIT
    GIT --> RF
    GIT --> MY
    UV -.実行環境を渡す.-> RF
    UV -.実行環境を渡す.-> MY
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**読みどころは、設定ファイルが2つに分かれていること。** `pyproject.toml` は「**どう直すか**」の基準、
`.pre-commit-config.yaml` は「**いつ走らせるか**」。片方だけでは動かない。
`pre-commit install` でコミットが止まったのに `.pre-commit-config.yaml` が無かったのは、
**入れ物だけ置いて中身が空**だったから。

#### (b) `git commit` を叩いたとき、中で何が起きるか

```mermaid
sequenceDiagram
    participant Y as あなた
    participant G as git
    participant P as pre-commit
    participant R as ruff
    participant M as mypy

    Y->>G: git commit
    G->>P: .git/hooks/pre-commit を起動
    P->>R: 変更された .py を渡す
    P->>M: 同じファイルを渡す
    alt すべて通った
        P-->>G: 終了コード 0
        G-->>Y: コミットができる
    else どれかが落ちた
        P--xG: 終了コード 1
        G--xY: コミットは作られない
    end
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**`--x` の側（下）が、このステップで作っているもの。** 成功経路だけなら、フックを入れる意味がない。

---

### 1-2a. 🔤 入口の2行

#### 🔤 `pyproject.toml`
**読み方**: 「パイプロジェクト・トムル」
**要するに**: このプロジェクトの**身分証と設定をまとめた1枚の紙**。名前・必要な部品・道具の設定が全部ここに書いてある。

#### 🔤 `uv`
**読み方**: 「ユー・ブイ」
**要するに**: **部品の買い出し係**。必要なものを取ってきて、このプロジェクト専用の箱（`.venv`）に入れる。

#### 🔤 `ruff`
**読み方**: 「ラフ」
**要するに**: **書き方の見張り番**。間違い探しと、見た目の揃え直しを両方やる。

#### 🔤 `mypy`
**読み方**: 「マイ・パイ」
**要するに**: **型の見張り番**。「数を入れる約束の場所に文字を入れていないか」を、動かす前に調べる。

#### 🔤 `pre-commit`
**読み方**: 「プリ・コミット」
**要するに**: **コミットの直前に見張り番を呼ぶ係**。呼ぶ相手は `.pre-commit-config.yaml` に書いておく。

---

### 1-2. 🔬 仕組み解剖

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `[tool.ruff]` | TOML のテーブル（セクション） | **ruff を起動した瞬間に**読まれる。`pyproject.toml` は複数の道具の設定を同居させる場所で、`[tool.<道具名>]` が各道具の取り分。ruff は `[tool.ruff]` しか見ず、mypy は `[tool.mypy]` しか見ない |
| `repo: local` | pre-commit のリポジトリ指定 | フックの**取得元**。`local` は「取ってこない。この環境にあるものを使う」の意味。起動のたびに `entry` のコマンドをそのまま実行する |
| `language: system` | フックの実行環境の指定 | pre-commit が**専用の環境を作らず**、いまの PATH でコマンドを実行する。`uv run` を書いているので、結果として**このプロジェクトの `.venv`** が使われる |
| `types_or: [python, pyi]` | ファイル種別のフィルタ | pre-commit が渡すファイルを `.py` / `.pyi` に絞る。**該当が0件ならフックは実行されず `Skipped`** になる（1-6 の実出力を参照） |
| `pre-commit install` | フックのインストール | `.git/hooks/pre-commit` に**起動用のスクリプトを1枚置く**。中身は「pre-commit を呼べ」だけで、**何を走らせるかは書かれていない** |

**いつ評価されるか**: `pyproject.toml` は各道具の**起動時**。`.pre-commit-config.yaml` は**コミットのたび**。

**どの道具の責務か**: 並び順の修正は ruff、型は mypy、**呼ぶタイミングだけが pre-commit**、`.venv` の用意は uv。
pre-commit 自身は lint も型チェックもしない。

**失敗したらどうなるか**: どれか1つでも終了コードが 0 以外なら、git は**コミットを作らずに中断する**。
`--fix` で自動修正できた場合も、**ファイルを書き換えた時点で失敗扱い**になる（1-6 の Q3）。

---

### 1-3. 🐍 Python解説

**このステップでは Python の文法は1つも出てこない。** 書いたのは TOML と YAML だけ。
Python の文法は **P1-2** の `app/main.py` から始まる。

---

### 1-3a. 🐍 Python の道具立て: `uv run` と `.venv`（§4.3.1-1）

**現象**: `python main.py` と打つと、入れたはずの FastAPI が「無い」と言われる。

```
ModuleNotFoundError: No module named 'fastapi'
```

**なぜそうなるか**

Python は**1台のパソコンに何個でも入る**。そして**入っている Python ごとに、持っている部品が違う**。

- あなたのパソコン全体の Python は **3.14.3**（`python3 --version` で確認済み）
- このプロジェクトの Python は **3.12.13**。`.venv/` という箱の中にいる

`uv add fastapi` で入れた FastAPI は、**`.venv/` の中の 3.12.13 にだけ**入っている。
`python main.py` と打つと、パソコン全体の 3.14.3 が動いてしまうので、「そんな部品は無い」になる。

**たとえ**: `.venv/` は**このプロジェクト専用の道具箱**。`uv run` は「**その道具箱を開けてから実行して**」という指示。
道具箱を開けずに作業を始めると、道具が見つからない。

**どう直すか**: 頭に `uv run` を付ける。これだけ。

```bash
uv run python main.py     # ← .venv の中の Python 3.12.13 が動く
uv run ruff check         # ← .venv の中の ruff が動く
uv run pytest             # ← P6 でも同じ
```

> **`source .venv/bin/activate` は覚えなくていい。** 昔ながらの「道具箱を開けっぱなしにする」やり方で、
> 今でも動くが、**開けたことを忘れて別のプロジェクトで作業すると事故る**。`uv run` は毎回その場で開けて閉じるので、忘れようがない。

**TS で言えば**: `.venv/` が `node_modules/`、`uv run` が `npx` にあたる。
違いは、Node は `node_modules/` を**自動で探しに行く**が、**Python は探しに行かない**こと。だから明示的に `uv run` が要る。

⚠️ **この教材では、Python がらみのコマンドは全部 `uv run` から始まる。** 例外はない。

---

### 1-3b. 🧩 周辺注

なし（Docker / MySQL はこのステップでは出ない。P2-1 から）。

---

### 1-4. 解説 — なぜこう設計するか

#### 🪜 なぜなぜ: なぜ「手で実行する」ではなく、git に仕掛けるのか

**なぜ① そもそも `git commit` のときに、なぜ勝手にコマンドが走るのか**
→ git には**フック**という仕組みがあり、`.git/hooks/pre-commit` という名前の実行ファイルが置いてあると、
コミットを作る直前に必ずそれを起動する。**終了コードが 0 以外ならコミットを中断する**。
`pre-commit install` がやったのは、このファイルを1枚置くことだけ。

**なぜ② なぜ git に任せるのか。自分で `ruff check` を打てばいいのでは**
→ **人間は忘れるから**、ではない（それもあるが本質ではない）。本質は**いつ止めるか**。
手で打つ場合、止まるのは「打ったとき」。CI に任せる場合、止まるのは「push した後」。
**コミットの時点で止めれば、壊れたコードがそもそも歴史に残らない。**
後から「このコミットは lint が通っていない」と分かっても、履歴は書き換えられない。

**なぜ③ では、フックを入れると何を失うのか** 🤔 まず自分で考える

<details><summary>答え</summary>

3つ失う。

1. **速さ。** コミットのたびに数秒待つ。ファイル数が増えるほど伸びる
2. **逃げ道が生まれる。** 急いでいるときに `git commit --no-verify` で飛ばせてしまう。
   飛ばしたことは**コミットには残らない**ので、後から分からない
3. **環境差が事故になる。** `language: system` はこの環境の道具をそのまま使うので、
   道具の版が違う人と一緒に作業すると、**自分の環境だけ落ちる／自分の環境だけ通る**が起きうる

3 は実際には `uv.lock` が版を固定しているので、**`uv run` 経由なら揃う**。
これが「`uv run` を必ず頭に付ける」ルールのもう1つの理由。

**ここから先は git 自体の設計思想の領域**（フックはあくまでローカルの仕組みで、強制力は持たせない）なので、ここで止める。
根拠: https://git-scm.com/docs/githooks
</details>

> 🧠 **考え方**: 品質ゲートは「いい行いをする道具」ではなく「**悪い状態を歴史に残さない関所**」。
> だから**一番最初**に立てる。後から立てると、関所の後ろに既に壊れたものが溜まっている。

---

### 1-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: フックの書き方には「配布元から取ってくる（`repo: https://...`）」やり方もあるが、
> ここでは **`repo: local` + `language: system`** にした。理由は **mypy がプロジェクトの `.venv` を見る必要がある**から。
> 取ってくる方式だと mypy は隔離された別の環境で動き、**FastAPI や SQLAlchemy の型が見えず**、P3 以降で誤検知が出る。
> 根拠: https://pre-commit.com/#repository-local-hooks

> ⚠️ **アンチパターン**: `git commit --no-verify` を常用する。
> 1回使うぶんには逃げ道として正しいが、常用すると**フックが入っていないのと同じ**になる。
> しかも「飛ばした」記録がコミットに残らないので、後から追えない。
> 根拠: https://git-scm.com/docs/git-commit#Documentation/git-commit.txt---no-verify

---

### 1-6. 🔮 予測 → 動作確認

**先に予想してから実行する。**

1. `.py` ファイルが1つも無い状態で `pre-commit run --all-files` を叩くと、3つのフックはどうなるか
2. 型の無い関数を書いてコミットしようとすると、**3つのうちどれが**止めるか。コミットは作られるか
3. 未使用 import のように **ruff が自動で直せる**問題のとき、コミットは成功するか失敗するか

<details><summary>1 の実行と結果</summary>

```bash
uv run pre-commit run --all-files
```

```
ruff (lint) — バグと書き方を見る.....................(no files to check)Skipped
ruff (format) — 見た目を揃える.......................(no files to check)Skipped
mypy — 型が合っているか見る..........................(no files to check)Skipped
→ 終了コード: 0
```

✅ 検証済み。**`Skipped` であって `Passed` ではない。** `types_or` で `.py` に絞っているので、
対象0件なら**そもそも起動しない**。「通った」のではなく「見ていない」。
</details>

<details><summary>2・3 の実行と結果</summary>

わざと壊れたファイルを作る。

```bash
cat > _scratch_bad.py <<'PY'
import sys
import os


def add(a, b):
    return a + b
PY
git add _scratch_bad.py
uv run pre-commit run --files _scratch_bad.py
```

```
ruff (lint) — バグと書き方を見る.........................................Failed
- hook id: ruff-check
- files were modified by this hook
Found 2 errors (2 fixed, 0 remaining).

ruff (format) — 見た目を揃える...........................................Failed
- hook id: ruff-format
- files were modified by this hook
1 file reformatted

mypy — 型が合っているか見る..............................................Failed
- hook id: mypy
- exit code: 1
_scratch_bad.py:1: error: Function is missing a type annotation  [no-untyped-def]

→ 終了コード: 1
```

✅ 検証済み。**3つとも落ちた。コミットは作られない。**

**3 の答えが要点**: ruff は未使用 import を**自動で直した**（`2 fixed`）のに、**Failed になっている**。
`files were modified by this hook` — 直したこと自体が失敗扱い。
**理由**: 直った後のファイルは、あなたが `git add` した内容と違う。
勝手に書き換えたものを黙ってコミットしたら、**あなたが見ていないコードが履歴に入る**。
だから一度止めて、「直したので、確認して `git add` し直してください」と促している。

後片付け:

```bash
git restore --staged _scratch_bad.py && rm _scratch_bad.py
```

> 💡 **補足**: mypy は既定で結果をキャッシュする（incremental mode）。
> 他の道具が同じファイルを書き換えた直後などに、結果が実態と合わないことがある。
> **おかしいと思ったら `rm -rf .mypy_cache` して再実行する。**
> 根拠: https://mypy.readthedocs.io/en/stable/command_line.html#incremental-mode
</details>

---

### 1-6b. 🧾 OpenAPI スキーマの差分

**対象外。** OpenAPI スキーマを読むのは **P1-6** から（§4.14）。ここではまだアプリが存在しない。

---

### 1-7. ✅ 想起チェック

1. `pyproject.toml` と `.pre-commit-config.yaml` は、それぞれ何を決めているか
2. `pre-commit install` を実行したのに `.pre-commit-config.yaml` が無いと、何が起きるか
3. `uv run` を付け忘れると、なぜ `ModuleNotFoundError` になるのか
4. ruff が問題を**自動で直した**とき、コミットは成功するか

<details><summary>答え</summary>

1. `pyproject.toml` = **どう直すか**の基準（ruff / mypy の設定）。`.pre-commit-config.yaml` = **いつ何を走らせるか**。
2. `git commit` が必ず失敗する。`No .pre-commit-config.yaml file was found`。
   フックは**入れ物**で、中身は設定ファイルにしかないため。
3. `uv run` 無しではパソコン全体の Python（3.14.3）が動く。FastAPI は `.venv` の中の 3.12.13 にしか入っていないため。
4. **失敗する。** 直した結果はあなたが `git add` した内容と違うので、一度止めて確認させる。
   `git add` し直してもう一度コミットすれば通る。
</details>

---

### 1-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `pyproject.toml` | 1-2a で入口の2行 / 1-2 で仕組み解剖 |
| `ruff` | 1-2a で入口の2行 / 1-1 で設定の各項目 |
| `mypy` | 1-2a で入口の2行 / ⏭️ `strict = true` は **P6-4** で回収 |
| `pre-commit` | 1-2a で入口の2行 / 1-2 で仕組み解剖 |
| `uv run` と `.venv` | **1-3a で道具立て**（§4.3.1-1） |
| `repo: local` / `language: system` | 1-2 で仕組み解剖 / 1-5 で実務メモ |
| `types_or` | 1-2 で仕組み解剖 / 1-6 の Q1 で実挙動を確認 |

**未回収: 0件**（`⏭️` 宣言した `strict = true` のみ P6-4 に持ち越し）

---

### 1-9. 📌 進捗の更新

`README.md` の進捗表 P1a を「P1-1 完了」、次の一手を `M1: P1 ステップ2` に更新した。

**次のステップ**: P1-2「最小のエンドポイント」。`GET /health` が 200 を返すところまで作り、
**初めて Python の文法が出てくる**（`def` / デコレータ `@` / 型アノテーション）。

---

## P1-2: 最小のエンドポイント

**作るもの**: `GET /health` を叩くと `{"status":"ok"}` が 200 で返るサーバ
**重要度**: 🔴 毎日使う — `@app.get()` と型アノテーションは、この先**すべてのエンドポイントの入口**になるため
**前ステップとの接続**: P1-1 で立てた品質ゲートを、**初めて実際の Python コードに通す**

### 2-0. このステップの初出トークン

| 系統 | トークン |
| --- | --- |
| **FastAPI** | `FastAPI()` / `@app.get()` / `uvicorn app.main:app`（3つ = 上限） |
| **Python** | `from ... import ...` / `=`（代入）/ `@`（デコレータ）/ `def` / `->` / `dict[str, str]` / 行末の `:` / 字下げ / `return` / `{...}`（辞書） |
| **【道具】** | トレースバックの読み方（§4.3.1-3）/ インデントエラー（§4.3.1-4） |
| **周辺** | — |

> Python が一気に増えるが、**FastAPI 側は3つに抑えてある**（§4.5）。
> 文法が多いのは、Python のファイルを初めて書くから。ステップを割る理由にはしない（§6.3）。

---

### 2-1. コード

#### (1) `app/__init__.py` — **新規作成・中身は空**

```bash
mkdir -p app
touch app/__init__.py
```

空のファイルを1つ置く。**なぜ空のファイルが要るのか**は 2-3a で扱う。

#### (2) `app/main.py` — **新規作成・全文**

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

**たった8行（空行込み）。** この8行に、Python の文法が10個入っている。1つずつ 2-3 で潰す。

#### (3) 起動する

```bash
uv run uvicorn app.main:app --port 8000
```

開発中はファイルを保存するたびに再起動してほしいので、こちらを使う。

```bash
uv run uvicorn app.main:app --port 8000 --reload
```

> ⚠️ **P1-9（デバッガ）では `--reload` を外す。** リローダーは**子プロセス**でアプリを動かすため、
> 親に接続したデバッガではブレークポイントが止まらない。**用途で2つ使い分ける**（§2.5）。

✅ 検証済み: macOS / Python 3.12.13 / FastAPI 0.141.1 / uvicorn 0.53.0 / ruff 0.16.8 / mypy 2.3.1。
`uv run ruff check app/` = `All checks passed!`、`uv run mypy app/` = `Success: no issues found in 2 source files`。
実レスポンスは 2-6 に貼った。

---

### 2-1b. 📊 図解

#### (a) uvicorn と FastAPI と Starlette は何が違うのか

新しく3つ名前が出たので、先に役割を分ける（§4.13）。

```mermaid
flowchart TB
    NET["ネットワーク<br/>TCP:8000"]
    subgraph srv["サーバ（あなたは書かない）"]
        UVI["uvicorn<br/>HTTP を解釈して受け渡す"]
    end
    subgraph fw["フレームワーク（あなたは書かない）"]
        STA["Starlette<br/>経路表を引く・応答を組む"]
        FAS["FastAPI<br/>型を読む・検証する・仕様書を作る"]
    end
    MINE["app/main.py<br/>あなたが書く8行"]
    NET --> UVI
    UVI --> STA
    STA --> FAS
    FAS --> MINE
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**読みどころは、あなたが書くのが一番奥の1枚だけということ。** 手前の3つは全部もらいもの。
`uvicorn app.main:app` というコマンドは、**この鎖を外から内へ繋ぐ指示**になっている。

#### (b) `curl` を叩いてから返るまで（失敗する道も描く）

```mermaid
sequenceDiagram
    participant C as curl
    participant U as uvicorn
    participant S as Starlette
    participant H as health()

    C->>U: GET /health
    U->>S: 経路表を引く
    alt /health が登録されている
        S->>H: 呼ぶ
        H-->>S: {"status": "ok"}
        S-->>C: 200 + JSON
    else 登録されていない（例 /helth）
        S--xC: 404 Not Found
    end
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**`/helth` の側では、矢印が `health()` まで届いていない。** 打ち間違えたとき、
あなたの関数は**呼ばれてすらいない**。「関数の中を直しても直らない」のはこのため（2-6 の Q1）。

---

### 2-2a. 🔤 入口の2行

#### 🔤 `FastAPI()`
**読み方**: 「ファストエーピーアイ、かっこ」
**要するに**: アプリ本体を1つ作る。**これから作るお店の、建物そのもの**。

#### 🔤 `@app.get("/health")`
**読み方**: 「アット・アップ・ドット・ゲット、かっこ、スラッシュ・ヘルス」
**要するに**: **「この住所に GET で来たら、下の関数を呼んでね」という貼り紙**。

#### 🔤 `uvicorn app.main:app`
**読み方**: 「ユビコーン、アップ・ドット・メイン、コロン、アップ」
**要するに**: 「`app` フォルダの `main.py` の中にある `app` という名前のものを動かして」という指示。

---

### 2-2. 🔬 仕組み解剖

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `FastAPI()` | アプリケーションインスタンスの生成 | **ファイルが読み込まれた瞬間**に1回だけ動く。中身が空の**経路表**を持ったアプリが1つできる。Starlette のアプリを継承しているので、この時点で ASGI アプリとして完成している |
| `@app.get("/health")` | パスオペレーションデコレータ | **起動時に1回**動く。`health` 関数を受け取り、`("GET", "/health") → health` を経路表に**登録**して、関数をそのまま返す。ついでに `-> dict[str, str]` を読み、OpenAPI スキーマの下書きも作る。**リクエストのたびに動くのではない** |
| `uvicorn app.main:app` | ASGI サーバの起動コマンド | `:` の**左が読み込むファイル**（`app/main.py`）、**右が変数名**（`app`）。uvicorn は HTTP を解釈して ASGI という形に直し、その `app` に渡す |

**いつ評価されるか**: 3つとも**起動時**。リクエストのたびに動くのは、登録された `health()` だけ。

**どの道具の責務か**: HTTP の解釈は uvicorn、経路表の照合は Starlette、型を読んで仕様書を作るのが FastAPI。
**あなたの関数が受け取るのは、全部済んだ後の状態**。

**失敗したらどうなるか**

| 失敗 | 結果 |
| --- | --- |
| 登録していないパス（`/helth`） | **404** `{"detail":"Not Found"}`。関数は呼ばれない |
| 登録はあるがメソッド違い（`POST /health`） | **405** Method Not Allowed |
| ファイルに構文エラー | **起動そのものが失敗**（終了コード 1）。2-3a を参照 |

**既知スタックとの対応**: Express の `app.get("/health", handler)` に近い。
違いは、**ハンドラを引数で渡さず、関数の真上に貼る**こと。理由は 2-4 で掘る。

---

### 2-3. 🐍 Python解説

初めての Python ファイルなので、8行を**1つ残らず**潰す。

#### 🐍 `from fastapi import FastAPI`

**読み方**: 「フロム・ファストエーピーアイ、インポート・ファストエーピーアイ」

**たとえ**: **道具箱から、使う道具を1つだけ出して机に置く**こと。
「`fastapi` という箱の中から、`FastAPI` という道具を出して使えるようにして」。

**正確には**:
- `from <どこから> import <なにを>` の形。左が箱（モジュール／パッケージ）、右が取り出すもの
- 小文字の `fastapi` が**ライブラリ名**、大文字の `FastAPI` が**その中のクラス名**。**別物**
- 取り出すと、そのファイルの中で `FastAPI` という名前で呼べるようになる

**TS なら**: `import { FastAPI } from "fastapi";` とほぼ同じ。`{}` が無く、順番が逆（`from` が先）。

#### 🐍 `app = FastAPI()`

**読み方**: 「アップ・イコール・ファストエーピーアイ、かっこ」

**たとえ**: **道具を実際に使って、モノを1つ作り、名札を付ける**。`app` が名札。

**正確には**:
- `=` は**代入**。右で作ったものに、左の名前を付ける。数学の「等しい」ではない
- `FastAPI()` の**末尾の `()` が「実行しろ」の合図**。付けないとモノは作られず、設計図のまま
- Python に**変数宣言のキーワードは無い**（`let` / `const` / `var` にあたるものが無い）。いきなり名前を書く

**TS なら**: `const app = new FastAPI();`
違いは2つ。**`const` にあたる語が無い**ことと、**`new` が要らない**こと（`()` だけでモノができる）。

> ⚠️ **`app` という名前は2か所で一致していないといけない。** ここで付けた名札と、
> 起動コマンド `uvicorn app.main:app` の**右側の `app`** は同じもの。名前を変えるなら両方変える。

#### 🐍 `@app.get("/health")` — デコレータ（§4.3 の「特に丁寧に扱う」）

**読み方**: 「アット」。この `@` で始まる書き方を**デコレータ**と呼ぶ。

**たとえ**: **関数に貼る付箋**。関数そのものは変えず、上から1枚貼って「この関数はこういう扱いにして」と伝える。

**正確には**: `@X` を関数の真上に書くと、**その関数が定義された直後に `X(その関数)` が自動で実行される**。つまり下の2つは同じ意味。

```python
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
def health() -> dict[str, str]:
    return {"status": "ok"}

health = app.get("/health")(health)   # ← デコレータはこれの短縮形
```

**2段階ある**のがつまずきどころ。`app.get("/health")` がまず実行されて**関数を受け取る関数**が返り、
それに `health` が渡される。だから `("/health")` の括弧が必要になる。

**いつ動くか**: **起動時に1回だけ**。リクエストのたびではない。ここが最大の勘違いポイント。

**TS なら**: 実験段階のデコレータ（`@Component` など）が近い。Angular や NestJS を触ったことがあれば同じ感覚。
触ったことがなければ「**関数を定義した直後に、その関数を引数にして呼ばれる仕掛け**」と覚えれば足りる。

#### 🐍 `def health() -> dict[str, str]:`

**読み方**: 「デフ・ヘルス、かっこかっこ、アロー、ディクト・ストリング・ストリング、コロン」

**たとえ**: **自動販売機の説明書き**。`def` が「この機械の名前」、`()` が「入れるものは無し」、
`-> dict[str, str]` が「出てくるものの形」、末尾の `:` が「ここから下が中身です」の合図。

**正確には**:
- `def` = 関数を定義する語。**この行の下の、字下げされた範囲**が中身
- `()` が空 = **引数なし**。P1-3 からここに引数が入る
- `->` = 戻り値の**型アノテーション**。矢印の右が「返ってくるものの型」
- `dict[str, str]` = 「**鍵が文字列、値も文字列の辞書**」。`[]` の中が中身の型
- **行末の `:` は必須**。`def` / `if` / `for` / `class` すべてに要る。忘れると構文エラー

**TS なら**: `function health(): Record<string, string> { ... }`
違いは3つ。戻り値の型が `:` ではなく **`->`**、`{}` が無く**字下げが範囲を決める**、そして `Record` ではなく `dict`。

> 🔴 **この `->` が、この教材の中心。** FastAPI はこの型を**飾りではなく実行時の仕様**として読む。
> P1-5 で `-> TodoRead` と書くと、**モデルに無いフィールドが自動で落ちる**ようになる。今はまだ効果が見えない。

#### 🐍 `return {"status": "ok"}`

**読み方**: 「リターン、なみかっこ、スターテス、コロン、オーケー」

**たとえ**: **自動販売機から商品が出てくる**ところ。`{...}` は**ラベル付きの引き出し**。

**正確には**:
- `return` = 関数の答えを返して、そこで関数を終える
- `{"鍵": "値"}` = **辞書**（dict）。鍵で値を取り出す入れ物
- FastAPI は、返ってきた辞書を**自動で JSON に変換**して返す。`json.dumps` を書く必要はない

**TS なら**: `return { status: "ok" };`
違いは1つ。**鍵をクォートで囲む必要がある**（`{"status": ...}`）。JS のように裸で書けない。

#### 🐍 字下げ（インデント）

**正確には**: Python は `{}` を使わず、**字下げそのものがブロックの範囲**を表す。
**半角スペース4つ**で統一する（ruff が自動で直すので、自分で数えなくてよい）。

**TS なら**: `{}` の役割を、空白が担っていると思えばよい。**見た目の整形ではなく、文法そのもの**。

---

### 2-3a. 🐍 Python の道具立て

#### (1) なぜ空の `app/__init__.py` が要るのか（§4.3.1-2 の予告）

**たとえ**: フォルダに貼る「**ここは Python の部品置き場です**」という札。

**正確には**: `__init__.py`（「ダンダー・イニット」と読む）があると、そのフォルダは
**パッケージ**として扱われ、`app.main` のような `.` 区切りの名前で呼べるようになる。
`uvicorn app.main:app` の `app.main` が、まさにこの呼び方。

> ⏭️ **後で回収**: import を本格的に使うのは **P1-8**（`app/routers/todos.py` に分割する回）。
> 今は「フォルダを Python の部品置き場だと宣言する札」とだけ理解して進む。

#### (2) トレースバックの読み方（§4.3.1-3）— **下から読む**

字下げを忘れて起動すると、こうなる。

```
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 995, in exec_module
  File "<frozen importlib._bootstrap_external>", line 1133, in get_code
  File "<frozen importlib._bootstrap_external>", line 1063, in source_to_code
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "/Users/.../roadmap-sh-fastapi/app/main.py", line 8
    return {"status": "ok"}
    ^^^^^^
IndentationError: expected an indented block after function definition on line 7
```

✅ 検証済み（実際に出した出力）。

**読む順番はこう。**

| 順 | どこを見るか | 何が分かるか |
| --- | --- | --- |
| **1** | **一番下の行** | **何が起きたか**。`IndentationError` = 字下げの問題 |
| **2** | その上の `File "..." line 8` | **どこで起きたか**。自分のファイルの8行目 |
| **3** | `^^^^^^` | **その行のどこか** |
| 4 | さらに上 | そこに至る道のり。**ほとんど読まなくていい** |

**上の10行は全部 `<frozen importlib._bootstrap>`**、つまり Python 自身の内部。
**あなたのファイル名が出てくる行までは、読み飛ばしてよい。**

> 🧠 **考え方**: トレースバックは「**下が結論、上が経緯**」。新聞と逆で、**最後の行から読む**。
> 慣れるまでは「自分のファイル名が出ている一番下の行」を探すだけでいい。

**TS との違い**: JS のスタックトレースは**エラーメッセージが先頭**に出る。Python は**最後**。上下が逆。

#### (3) インデントエラー（§4.3.1-4）

**現象**: 上の `IndentationError`。**起動そのものが失敗**し、サーバは立たない（終了コード 1）。

**どう直すか**: 字下げを入れる。ただし**その前に ruff が教えてくれる**。

```
invalid-syntax: Expected an indented block after function definition
 --> app/main.py:8:1
  |
6 | @app.get("/health")
7 | def health() -> dict[str, str]:
8 | return {"status": "ok"}
  | ^^^^^^
```

✅ 検証済み。**P1-1 で品質ゲートを先に立てた効果がここで出る。**
起動して10行のトレースバックを読むより、`uv run ruff check app/` のほうが速い。

> ⚠️ **タブと半角スペースを混ぜない。** 見た目が同じでも Python には別物で、`TabError` になる。
> エディタの設定を「タブをスペースに変換」にしておけば起きない。

#### (4) `uv run python app/main.py` では起動しない

```bash
uv run python app/main.py
# 終了コード: 0 ← エラーも出ず、サーバも立たない
```

✅ 検証済み。**エラーが出ないぶん、かえって厄介。**

**なぜか**: `app/main.py` がやっているのは「アプリを**作って** `app` という名札を付ける」ところまで。
**待ち受ける処理は1行も書いていない**。だからファイルを最後まで実行して、何事もなく終わる。

待ち受けるのは uvicorn の仕事。だから `uv run uvicorn app.main:app` と、**uvicorn 側から呼ぶ**。

---

### 2-3b. 🧩 周辺注

なし（Docker / MySQL は P2-1 から）。

---

### 2-4. 解説 — なぜこう設計するか

#### 🔄 素材からの変更: 公式は `async def`、本教材は `def`

【入力素材】の公式チュートリアルは、**最初の例から `async def`** で書かれている。本教材は `def` を使う。

> ⏭️ **後で回収**: 理由は **P3-1** で仕組み解剖として扱う。
> ごく短く言うと、このプロジェクトは**同期の DB ドライバ**で統一するため（§4.7）。
> `def` で書くと Starlette が別スレッドで実行してくれるので、DB 待ちでサーバ全体が止まらない。
>
> **公式を読んで `async def` を見ても、自分が間違えたわけではない。** どちらも動く。選択が違うだけ。

#### 🪜 なぜなぜ: なぜ関数の**真上**に貼るのか

**なぜ① `@app.get("/health")` と書くだけで、なぜ経路が繋がるのか**
→ デコレータは**起動時に実行される**。`app.get("/health")` が「関数を受け取る関数」を返し、
それが `health` を受け取って、`("GET", "/health") → health` という**対応表の1行**をアプリの中に書き込む。
リクエストが来たとき Starlette はこの表を引くだけ。**繋ぐ作業は、起動時にもう終わっている。**

**なぜ② なぜ設定ファイルに経路をまとめないのか。そのほうが一覧できるのでは**
→ **経路と処理が離れると、片方だけ直す事故が起きるから。** URL を変えたのに設定側を直し忘れる、
関数を消したのに経路が残る、といった食い違いは、2か所に分かれている限り必ず起きる。
真上に貼ってあれば、**関数を消せば経路も一緒に消える**。近くにあるものは、一緒に直る。

**なぜ③ では、真上に貼る方式は何を失うのか** 🤔 まず自分で考える

<details><summary>答え</summary>

3つ失う。

1. **一覧性。** 「この API に経路がいくつあるか」は、**ファイルを読み込んでみるまで分からない**。
   経路表が埋まるのは、デコレータが実行された後だから。設定ファイル方式なら1枚見れば済む。
   → ただし**手当てが2つある**（§4.2.1 ルール6）。

   | 手当て | やり方 | 扱うステップ |
   | --- | --- | --- |
   | 起動して見る | `/openapi.json` を `jq` で読む | **P1-6** |
   | 起動せずに見る | `app.routes` を読む（import だけで経路表は埋まる） | **P1-8** |

   「静的に読めない代わりに、**読み込みさえすれば正確な一覧が出る**」という取り引き。
   ドキュメントと実装がズレないのは、一覧が実装そのものから出ているため。
2. **順序の制御。** 経路が登録される順番は、**ファイルが読み込まれる順番**に縛られる。
   `/users/me` と `/users/{id}` のように**衝突しうる経路**では、書いた順が結果を変える（P1-3 で実際に踏む）。
3. **経路の動的な差し替え。** 起動後に経路を増やしたり消したりする道は、実質的に用意されていない。

> 3 は失ったというより**捨てた**もの。「宣言がそのまま仕様である」を優先した結果で、
> これは §4.14 の OpenAPI スキーマ生成とも一体になっている。
> 根拠: https://fastapi.tiangolo.com/tutorial/first-steps/
</details>

> 🧠 **FastAPI の考え方**: 宣言は**その場に書く**。経路も型も、離れた設定ファイルではなく
> **使う場所の真上**に置く。すると「直し忘れ」という失敗の種類そのものが消える。

---

### 2-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: `--reload` は**開発専用**。ファイル変更を監視するために別プロセスを動かし続けるので、
> 本番では使わない。公式も本番での使用を想定していないと明記している。
> 根拠: https://www.uvicorn.org/settings/

> ⚠️ **アンチパターン**: `app/main.py` の末尾に `uvicorn.run(...)` を書いて `python app/main.py` で起動する。
> 動くが、**アプリの定義ファイルが起動方法まで抱え込む**。起動の仕方（ポート・ワーカー数・リロード）は
> 環境ごとに変わるもので、アプリ本体に埋め込むと差し替えられなくなる。**起動はコマンド側に置く。**
> 根拠: https://fastapi.tiangolo.com/deployment/manually/

---

### 2-6. 🔮 予測 → 動作確認

**先に予想してから実行する。**

1. `/helth` と打ち間違えたら、何が返るか。**`health()` 関数は呼ばれるか**
2. `POST /health` を叩いたら、404 か、別の何かか
3. 字下げを忘れたとき、失敗するのは**起動時か、リクエストが来たときか**

<details><summary>実行と結果</summary>

サーバを起動しておく。

```bash
uv run uvicorn app.main:app --port 8000
```

**1 と 2**

```bash
curl -sS -i http://127.0.0.1:8000/health
```
```
HTTP/1.1 200 OK
server: uvicorn
content-type: application/json

{"status":"ok"}
```

```bash
curl -sS -i http://127.0.0.1:8000/helth
```
```
HTTP/1.1 404 Not Found
content-type: application/json

{"detail":"Not Found"}
```

```bash
curl -sS -i -X POST http://127.0.0.1:8000/health
```
```
HTTP/1.1 405 Method Not Allowed
content-type: application/json
```

✅ 検証済み。

**1 の答え**: `health()` は**呼ばれない**。経路表に `/helth` が無いので、Starlette が照合の時点で打ち切る。
**関数の中をいくら直しても直らない**のはこのため（2-1b の図を参照）。

**2 の答え**: 404 ではなく **405**。パスは存在するが**メソッドが違う**ことを、経路表は区別している。
「404 が返らない＝パスは合っている」と読めるので、切り分けに使える。

**3 の答え**: **起動時**。Python はファイルを読み込む時点で構文を検査するので、
リクエストを待たずに落ちる（終了コード 1）。実際の出力は 2-3a(2) に貼った。
</details>

---

### 2-6b. 🧾 OpenAPI スキーマの差分

**まだ対象外**（差分を出し始めるのは P1-6 から。§4.14）。

ただし `/docs` は**この時点で既に見られる**。

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/docs
# 200
```

✅ 検証済み。

> ⏭️ **後で回収**: `/docs`・`/redoc`・`/openapi.json` の**違いと読み方**は **P1-6**。
> 今は「`@app.get` と `-> dict[str, str]` を書いただけで、仕様書が勝手に生えている」とだけ確認して進む。

---

### 2-7. ✅ 想起チェック

1. `@app.get("/health")` はいつ実行されるか。リクエストのたびか、起動時に1回か
2. `uvicorn app.main:app` の `:` の左と右は、それぞれ何を指すか
3. `->` の右に書いたものは、何に使われるか
4. `uv run python app/main.py` を叩くと何が起きるか。なぜか
5. トレースバックは、どこから読むか

<details><summary>答え</summary>

1. **起動時に1回だけ。** 経路表に `("GET", "/health") → health` を登録して終わり。
   リクエストのたびに動くのは `health()` 本体。
2. **左が読み込むファイル**（`app/main.py`）、**右がその中の変数名**（`app = FastAPI()` で付けた名札）。
3. **戻り値の型アノテーション。** 今は mypy が見るだけだが、P1-5 以降は FastAPI が
   **レスポンスの形の宣言**として実行時に使う（モデルに無いフィールドが落ちる）。
4. **何も起きずに終了コード 0 で終わる。** ファイルにはアプリを作る処理しかなく、
   待ち受ける処理が無いため。待ち受けは uvicorn の仕事。
5. **一番下から。** 下が結論（エラーの種類）、その上が場所。上のほうの `<frozen importlib...>` は
   Python 内部なので読み飛ばす。**自分のファイル名が出る行**を探す。
</details>

---

### 2-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `FastAPI()` | 2-2a で入口の2行 / 2-2 で仕組み解剖 |
| `@app.get()` | 2-2a / 2-2 で仕組み解剖 / 2-4 で なぜなぜ3段（代償の手当ては ⏭️ **P1-6 / P1-8** で回収） |
| `uvicorn app.main:app` | 2-2a / 2-2 で仕組み解剖（`:` の左右）/ 2-3a(4) |
| `from ... import ...` | 2-3 で Python解説 |
| `=`（代入） | 2-3 で Python解説（`const` も `new` も無い） |
| `@`（デコレータ） | 2-3 で Python解説（§4.3「特に丁寧に扱う」該当。展開形も併記） |
| `def` / 行末の `:` / 字下げ | 2-3 で Python解説 |
| `->` / `dict[str, str]` | 2-3 で Python解説 / ⏭️ **実行時の効果は P1-5 で回収** |
| `return` / `{...}`（辞書） | 2-3 で Python解説 |
| `app/__init__.py` | 2-3a(1) で道具立て / ⏭️ **import 本番は P1-8 で回収** |
| トレースバックの読み方 | **2-3a(2) で道具立て**（実出力つき） |
| インデントエラー | **2-3a(3) で道具立て**（実出力つき） |
| `async def` との差 | 2-4 で 🔄 素材からの変更 / ⏭️ **P3-1 で回収** |
| `/docs` | 2-6b で存在だけ確認 / ⏭️ **P1-6 で回収** |

**未回収: 0件**（`⏭️` 宣言は4件、すべて回収先を明示）

---

### 2-9. 📌 進捗の更新

`README.md` の進捗表 P1a を「P1-2 完了」、次の一手を `M1: P1 ステップ3` に更新した。

**次のステップ**: P1-3「パスとクエリの受け取り」。`GET /items/{id}?q=` で**引数を受け取る**。
ここで初めて `()` の中身が埋まり、**型を書くだけで文字列が数値に変換される**ところを見る。
2-4 の なぜなぜ③ で触れた「**経路の順番が結果を変える**」も、ここで実際に踏む。

---

## P1-3: パスとクエリの受け取り

**作るもの**: `GET /items/{item_id}?q=` が**型どおりに変換**され、変換できなければ 422 を返す
**重要度**: 🔴 毎日使う — 引数の受け取り方は、この先すべてのエンドポイントの入口になるため
**前ステップとの接続**: P1-2 で**空だった `()`** に、初めて中身が入る

### 3-0. このステップの初出トークン

| 系統 | トークン |
| --- | --- |
| **FastAPI** | パスパラメータ宣言（`{item_id}` と `item_id: int`）/ `Query()` / **422 の自動応答**（3つ = 上限） |
| **Python** | `Annotated` / `|`（ユニオン型）/ `None` / 既定値つき引数 / 引数の複数行書き |
| **【道具】** | —（該当なし） |
| **周辺** | — |

---

### 3-1. コード

#### `app/main.py` — **全文**（`/items/{item_id}` を追加）

```python
from typing import Annotated

from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items/{item_id}")
def read_item(
    item_id: int,
    q: Annotated[str | None, Query(max_length=20)] = None,
) -> dict[str, int | str | None]:
    return {"item_id": item_id, "q": q}
```

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / uvicorn 0.53.0。
`uv run ruff check app/` = `All checks passed!`、`uv run mypy app/` = `Success`。実レスポンスは 3-6。

> 💡 **補足**: `/items/` は**練習用**のエンドポイント。P1-4 で `/todos` を作り始めたら**削除する**。
> ここで TODO を使わないのは、まだ**データを置く場所が無い**（メモリ上のリストは P1-4 から）ため。

> 🔄 **素材からの変更**: 公式チュートリアルは `Annotated` を使う形を推奨しており、本教材もそれに合わせた。
> ただし**ネット上の記事の多くは `q: str = Query(default=None, max_length=20)` という古い形**で書かれている。
> **どちらも動き、生成される OpenAPI も完全に同一**（実際に両方で生成して比較し、一致を確認した）。
> 見かけても間違いではない。新しく書くときは `Annotated` を使う。
> 根拠: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/

---

### 3-1b. 📊 図解

#### (a) 型を書くと、リクエストが来たとき何が起きるか

```mermaid
sequenceDiagram
    participant C as curl
    participant S as Starlette
    participant F as FastAPI
    participant H as read_item()

    C->>S: GET /items/abc
    S->>F: 経路は一致。item_id="abc"（文字列）
    F->>F: int に変換を試みる
    alt 変換できた
        F->>H: item_id=42（整数）で呼ぶ
        H-->>C: 200 + JSON
    else 変換できない
        F--xC: 422 + loc / type / msg
    end
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**読みどころは、URL から来る値が最初は必ず「文字列」であること。** HTTP に整数という概念は無い。
`item_id: int` と書くことで、**FastAPI が文字列 → 整数の変換を引き受ける**。
失敗した側の矢印は `read_item()` に**届いていない**。

#### (b) 経路表は上から順に照合される

```mermaid
flowchart TB
    REQ["GET /items/special"]
    R1{"1番目<br/>/items/{item_id}<br/>に一致する？"}
    R2{"2番目<br/>/items/special<br/>に一致する？"}
    CONV["item_id に 'special' を<br/>int で変換"]
    ERR["422<br/>到達すらしない"]
    OK["200"]
    REQ --> R1
    R1 -->|"一致する（何でも入る）"| CONV
    CONV --> ERR
    R1 -.->|一致しなければ| R2
    R2 --> OK
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**`{item_id}` は「何でも一致する」ので、先に書くと後ろが永久に届かない。**
点線のルートには入れない。これが P1-2 の なぜなぜ③ で挙げた「**順序の制御**」という代償の実物（3-6 の Q3）。

---

### 3-2a. 🔤 入口の2行

#### 🔤 `@app.get("/items/{item_id}")`
**読み方**: 「スラッシュ・アイテムズ・スラッシュ、なみかっこ・アイテム・アイディー」
**要するに**: **住所の一部を穴あきにした貼り紙**。`{}` の場所に何が来ても受け取り、その中身に名前を付ける。

#### 🔤 `Query(max_length=20)`
**読み方**: 「クエリ、マックス・レングス・イコール・にじゅう」
**要するに**: **`?` の後ろから来る値への注文票**。「最大20文字まで」のような条件をここに書く。

---

### 3-2. 🔬 仕組み解剖

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `{item_id}` + `item_id: int` | パスパラメータ | **起動時**に「パスの `{}` と同じ名前の引数」を突き合わせ、変換器を用意する。**リクエストごと**に、URL から切り出した**文字列**を `int` に変換して渡す。`{}` の中と引数名が**一致していないと起動時にエラー**になる |
| `q: Annotated[str | None, Query(...)] = None` | クエリパラメータ | **パスに無い名前の引数は、自動でクエリ扱い**になる。`Query()` は「注文票」で、`max_length` などの条件をここに書く。既定値があるので**省略可能**、無ければ必須になる |
| 422 の自動応答 | RequestValidationError → 422 | 変換や条件チェックに失敗すると、**ハンドラを呼ばずに**422 を返す。ボディは `detail` の配列で、各要素に `type` / `loc` / `msg` / `input` が入る |

**いつ評価されるか**: 型の読み取りと変換器の用意は**起動時**。変換と検証は**リクエストごと**。

**どの道具の責務か**: 経路の照合は Starlette、**型の変換と検証は Pydantic**、その結果を 422 に組み立てるのが FastAPI。

**失敗したらどうなるか**: 下の3つは**全部 422**で、`loc` の1つ目が違う。

| 失敗 | `type` | `loc` |
| --- | --- | --- |
| `/items/abc` | `int_parsing` | `["path", "item_id"]` |
| `?q=`（21文字） | `string_too_long` | `["query", "q"]` |
| （P1-4 で出る）ボディの型違い | — | `["body", ...]` |

**`loc` の1つ目が「どこで起きたか」を指している。** path / query / body の3つを見分けるのが、422 を読む第一歩。

**既知スタックとの対応**: Express の `req.params.id`（常に文字列。自分で `Number()` する）と、
zod の `z.coerce.number()` を**足したもの**が近い。違いは、**変換と検証を関数の外に出している**こと。

---

### 3-3. 🐍 Python解説

#### 🐍 `str | None`（ユニオン型）

**読み方**: 「ストリング・または・ノン」。`|` は「パイプ」または「バーティカルバー」。

**たとえ**: **「文字列が入っているか、空っぽか、そのどちらか」**という札。

**正確には**:
- `A | B` = 「A か B のどちらか」を表す型。**型の世界での「または」**
- `None` は「値が無い」ことを表す**専用の値**。0 でも空文字でもない
- `str | None` は「文字列が来るか、何も来ないか」

**TS なら**: `string | null` とほぼ同じ。**記号まで同じ**。違いは `null` が `None` になること。

> JSON に変換されると `None` は `null` になる。3-6 で `{"item_id":42,"q":null}` が返るのはこのため。

#### 🐍 `= None`（既定値つき引数）

**読み方**: 「イコール・ノン」

**たとえ**: **注文票の「未記入なら、こう扱う」欄**。

**正確には**:
- 引数に `= 値` を付けると、呼ぶ側が省略したときその値になる
- **FastAPI では、これが「省略可能かどうか」の判定に直結する。** 既定値があれば任意、無ければ必須
- 既定値つきの引数は、既定値の無い引数**より後ろ**に書く（Python の決まり）

**TS なら**: `function f(q: string | null = null)` と同じ。

#### 🐍 `Annotated[str | None, Query(max_length=20)]`

**読み方**: 「アノテイテッド、ストリング・または・ノン、カンマ、クエリ、マックスレングス・にじゅう」

**たとえ**: **荷物に札を2枚貼る**。1枚目が「中身は何か」（`str | None`）、2枚目が「取り扱いの注意」（`Query(max_length=20)`）。

**正確には**:
- `Annotated[型, 追加の情報...]` の形。**1つ目が本当の型**で、2つ目以降は**おまけの情報**
- Python 自身は2つ目以降を**無視する**。読むのは、読みたい道具（ここでは FastAPI）だけ
- だから **mypy は `str | None` としてだけ見る**。`Query(...)` は型チェックに影響しない

**なぜこんな回りくどい形なのか**: 型と「その型への注文」を**1か所にまとめられる**から。
古い形（`q: str | None = Query(default=None)`）だと、**既定値を書く場所が `Query()` に奪われて**しまい、
「省略時は何になるのか」が読みにくかった。`Annotated` なら `= None` が素直に右端に残る。

**TS なら**: **対応物なし。** TS には「型に注釈を貼って、実行時に別のライブラリが読む」仕組みが無い
（デコレータ + `reflect-metadata` が近いが、言語標準ではない）。

#### 🐍 引数を複数行に分ける

```python
def read_item(
    item_id: int,
    q: Annotated[str | None, Query(max_length=20)] = None,
) -> dict[str, int | str | None]:
```

**正確には**: `(` の後ろで改行すると、`)` まで1行として扱われる。
**最後の引数の後ろにもカンマを付ける**（末尾カンマ）のが慣習で、ruff format が自動で付ける。
引数を1つ足したときに**差分が1行で済む**ため。

**TS なら**: 同じことができる。末尾カンマの理由も同じ。

#### 🐍 `dict[str, int | str | None]`

**正確には**: 「鍵は文字列、値は**整数か文字列か空っぽ**の辞書」。
`{"item_id": 42, "q": "hello"}` の値が2種類あるので、`|` で並べている。

> ⏭️ **後で回収**: 戻り値をこうやって手で書くのは**今回が最後**。
> P1-5 で **Pydantic モデル**を戻り値にすると、この宣言がもっと正確で短くなる。

---

### 3-3a. 🐍 Python の道具立て ／ 3-3b. 🧩 周辺注

このステップでは該当なし。

---

### 3-4. 解説 — なぜこう設計するか

#### 🪜 なぜなぜ: なぜ型を書くだけで変換され、失敗が 422 になるのか

**なぜ① `item_id: int` と書いただけで、なぜ文字列が整数になるのか**
→ **URL から来る値は、必ず文字列**。HTTP に整数という型は無く、`/items/42` の `42` はただの2文字。
FastAPI は**起動時**に引数の型を読み、「この引数は `int` に直してから渡す」という変換器を用意しておく。
リクエストごとに Pydantic がその変換を実行する。

**なぜ② なぜハンドラの中で `int(item_id)` を書かせないのか**
→ 3つ困るから。(1) **全ハンドラに同じ `try / except` が並ぶ**。(2) 失敗時に返す形が
**書いた人ごとにバラバラ**になり、クライアントが対応できない。(3) 何よりも、
**仕様書に出ない**。ハンドラの中の `int()` は外から見えないが、`item_id: int` は
OpenAPI スキーマに `"type": "integer"` として現れる。**宣言だから機械に読める。**

**なぜ③ では、この「宣言でしか書けない」方式は何を失うのか** 🤔 まず自分で考える

<details><summary>答え</summary>

3つ失う。**そして3つとも、この教材の中で手当てがある**（§4.2.1 ルール6）。

| 失うもの | 具体的に | 手当て |
| --- | --- | --- |
| **型で表せない条件が書けない** | 「`start` は `end` より前」のような**2つの値をまたぐ**条件は、1つの引数の型では表せない | **P1-4** の `Field()` と、モデル単位の検証で一部を回収 |
| **エラーメッセージを自由にできない** | `"Input should be a valid integer"` は Pydantic の文面。日本語にしたい、独自コードを付けたい、が直接はできない | **P5-3** の例外ハンドラ一元化で、422 の形ごと作り替える |
| **宣言できる範囲に設計が縛られる** | 「この条件のときだけ別の形を受ける」が書きにくい | **手当てしない。** 宣言主義を選んだ以上の当然の帰結で、避けるなら FastAPI を使う意味が薄れる |

3つ目を正直に「手当てしない」と書けるのが、この方式の強さでもある。
**何ができないかがはっきりしている**ほうが、設計の判断はしやすい。
根拠: https://fastapi.tiangolo.com/tutorial/path-params/
</details>

> 🧠 **FastAPI の考え方**: 変換と検証は**関数の外**でやる。
> ハンドラが動き始めた時点で、**引数はもう正しい**という前提に立てる。
> だからハンドラの中に「値が変かどうか」を調べるコードが要らなくなる。

---

### 3-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: パスパラメータには**必ず型を付ける**。`item_id` と型なしで書くと**文字列のまま**渡り、
> `/items/abc` も 200 で通ってしまう。**422 が返らないエンドポイントは、型を付け忘れている**と疑う。
> 根拠: https://fastapi.tiangolo.com/tutorial/path-params/

> ⚠️ **アンチパターン**: `/items/{item_id}` を書いた**後ろ**に `/items/special` のような固定パスを書く。
> `{}` は何にでも一致するので、後ろの固定パスには**永久に到達しない**。
> **固定パスは、穴あきパスより先に書く。**
> 根拠: https://fastapi.tiangolo.com/tutorial/path-params/#order-matters

---

### 3-6. 🔮 予測 → 動作確認

**先に予想してから実行する。**

1. `/items/abc` を叩くと、**404 か 422 か**。`read_item()` は呼ばれるか
2. `?q=` に21文字を渡すと、何が返るか。`loc` はどうなるか
3. `/items/special` という固定パスを `{item_id}` の**後ろ**に足すと、`/items/special` は **200 / 404 / 422** のどれか

<details><summary>実行と結果</summary>

```bash
uv run uvicorn app.main:app --port 8000 --reload
```

**正常系**

```bash
curl -sS http://127.0.0.1:8000/items/42
curl -sS "http://127.0.0.1:8000/items/42?q=hello"
```
```
{"item_id":42,"q":null}
{"item_id":42,"q":"hello"}
```

`q` を省略すると `None` になり、JSON では `null` として出る。

**1 の答え: 422**（404 ではない）

```bash
curl -sS http://127.0.0.1:8000/items/abc
```
```json
{"detail":[{"type":"int_parsing","loc":["path","item_id"],
"msg":"Input should be a valid integer, unable to parse string as an integer","input":"abc"}]}
```

**経路としては一致している**（`/items/` の後ろに何かある）ので 404 にはならない。
一致した後の**変換で落ちて 422**。`read_item()` は**呼ばれていない**。

**2 の答え: 422、`loc` は `["query","q"]`**

```bash
curl -sS "http://127.0.0.1:8000/items/42?q=123456789012345678901"
```
```json
{"detail":[{"type":"string_too_long","loc":["query","q"],
"msg":"String should have at most 20 characters","input":"123456789012345678901",
"ctx":{"max_length":20}}]}
```

**`loc` の1つ目が `path` から `query` に変わっている。** どこで落ちたかが、ここで分かる。

**3 の答え: 422**（200 でも 404 でもない）

`{item_id}` の後ろに置いた場合:
```json
{"detail":[{"type":"int_parsing","loc":["path","item_id"],
"msg":"Input should be a valid integer, unable to parse string as an integer","input":"special"}]}
```

**`"input":"special"`** が出ている。`/items/{item_id}` が先に一致してしまい、
`"special"` を整数に変換しようとして落ちている。`read_special()` には**到達すらしていない**。

固定パスを**先に**書き直すと:
```
GET /items/special → {"item_id":"special"}  status=200
GET /items/42      → {"item_id":42,"q":null} status=200
```

両方通る。**順番だけが違い、コードは1文字も変えていない。**
</details>

✅ 検証済み（上の出力はすべて実行して取得）。

---

### 3-6b. 🧾 OpenAPI スキーマの差分

**まだ対象外**（差分を出し始めるのは P1-6 から。§4.14）。

> ⏭️ **後で回収**: いま追加した `item_id` と `q` が、仕様書の `parameters` に
> `"in": "path"` / `"in": "query"` としてどう現れるかは **P1-6** で読む。
> `max_length=20` も `"maxLength": 20` として出ている。

---

### 3-7. ✅ 想起チェック

1. `/items/abc` が 404 ではなく 422 になるのはなぜか
2. 422 のボディの `loc` の1つ目には、何が入るか。種類を3つ
3. `q` を必須にするには、どこをどう変えるか
4. `Annotated[str | None, Query(max_length=20)]` の1つ目と2つ目は、それぞれ誰が読むか
5. 固定パスと穴あきパスは、どちらを先に書くか。なぜか

<details><summary>答え</summary>

1. **経路の照合には成功しているから。** `/items/` の後ろに値はある。落ちたのは**その後の型変換**。
   404 は「経路が無い」、422 は「経路はあるが中身が不正」。
2. **`path` / `query` / `body`**（body は P1-4 から）。**どこで落ちたか**を指す。
3. **`= None` を消す。** 既定値が無くなると必須になる。型も `str` にする。
4. **1つ目（`str | None`）は Python と mypy。2つ目（`Query(...)`）は FastAPI だけ。**
   Python 自身は2つ目を無視する。
5. **固定パスが先。** `{}` は何にでも一致するので、先に書くと後ろの固定パスに永久に到達しない。
</details>

---

### 3-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| パスパラメータ（`{item_id}` + `item_id: int`） | 3-2a で入口の2行 / 3-2 で仕組み解剖 / 3-6 の Q1 で実挙動 |
| `Query()` | 3-2a / 3-2 で仕組み解剖 / 3-6 の Q2 で実挙動 |
| 422 の自動応答 | 3-2 で仕組み解剖（`loc` の3種類）/ ⏭️ **ボディの 422 は P1-4**、**形の作り替えは P5-3** で回収 |
| `Annotated` | 3-3 で Python解説（なぜこの形かも含む） |
| `|`（ユニオン型） | 3-3 で Python解説（TS の `\|` と同じ記号） |
| `None` | 3-3 で Python解説（JSON では `null`） |
| 既定値つき引数（`= None`） | 3-3 で Python解説（**省略可能かの判定に直結**） |
| 引数の複数行書き・末尾カンマ | 3-3 で Python解説 |
| `dict[str, int | str | None]` | 3-3 で Python解説 / ⏭️ **P1-5 で Pydantic モデルに置き換える** |
| 経路の順序 | 3-1b(b) の図 / 3-5 のアンチパターン / 3-6 の Q3（**P1-2 なぜなぜ③ の代償を回収**） |

**未回収: 0件**（`⏭️` 宣言は3件、すべて回収先を明示）

---

### 3-9. 📌 進捗の更新

`README.md` の進捗表 P1a を「P1-3 完了」、次の一手を `M1: P1 ステップ4` に更新した。

**次のステップ**: P1-4「リクエストボディと 422」。`POST /todos` を作り、**Pydantic モデル**で
ボディを受け取る。`loc` の3つ目 `body` がここで出る。`/items/` は役目を終えるので**削除する**。

---

## P1-4: リクエストボディと 422

**作るもの**: `POST /todos` が JSON のボディを **Pydantic モデル**で受け取り、形が違えば 422 を返す
**重要度**: 🔴 毎日使う — データを「送って作る」エンドポイントは、すべてこの形で入口を作るため
**前ステップとの接続**: P1-3 の `loc` の3種類のうち、最後の **`body`** がここで出る。練習用の `/items/` は**削除する**

### 4-0. このステップの初出トークン

| 系統 | トークン |
| --- | --- |
| **FastAPI** | `@app.post()` / `BaseModel` を引数に書く（**ボディ判定**）/ `Field()`（3つ = 上限） |
| **Python** | `class`（クラスの定義）/ `(BaseModel)`（継承）/ クラスの中の `名前: 型` / `bool` と `True` / `False` / `list[...]` と `[]` / `.append()` / `#`（コメント）/ `.` 区切りの import |
| **【道具】** | —（該当なし） |
| **周辺** | — |

> 422 の自動応答は **P1-3 で既出**（今回はその `body` 版）。`Annotated` も2度目なので1行の復習で済ませる。

---

### 4-1. コード

#### (1) `app/schemas/__init__.py` — **新規作成・中身は空**

```bash
mkdir -p app/schemas
touch app/schemas/__init__.py
```

P1-2 の `app/__init__.py` と同じ札（2-3a(1) 参照）。`app/schemas/` も部品置き場にする。

#### (2) `app/schemas/todo.py` — **新規作成・全文**

```python
from typing import Annotated

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    done: bool = False
```

#### (3) `app/main.py` — **全文**（`/items/` を削除し、`/todos` を追加）

```python
from fastapi import FastAPI

from app.schemas.todo import TodoCreate

app = FastAPI()

# 教材用の置き場所。サーバを止めると消える（P3 で MySQL に置き換える）
todos: list[TodoCreate] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/todos")
def create_todo(todo: TodoCreate) -> TodoCreate:
    todos.append(todo)
    return todo


@app.get("/todos")
def list_todos() -> list[TodoCreate]:
    return todos
```

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Pydantic 2.13.5 / uvicorn 0.53.0。
`uv run ruff check app/` = `All checks passed!`、`uv run ruff format --check app/` = `4 files already formatted`、
`uv run mypy app/` = `Success: no issues found in 4 source files`。実レスポンスは 4-6。

> 💡 **補足**: `GET /todos` は**確認用**に足した。422 のとき「ハンドラが本当に呼ばれていないか」を、
> **リストに増えていないこと**で確かめるため（4-6 の Q1）。

> 💡 **補足**: 戻り値の `-> TodoCreate` は、今は「受け取ったものをそのまま返す」ための仮の形。
> **ID が無い**のが気になるはずで、それが P1-5 の主題（`TodoCreate` と `TodoRead` を分ける）。

---

### 4-1b. 📊 図解

#### (a) 誰が何を持っているか（Pydantic が初めて表に出る回・§4.13）

```mermaid
flowchart LR
    subgraph fa["FastAPI の仕事"]
        SORT["引数を振り分ける<br/>path / query / body"]
        ERR["失敗を 422 に組み立てる"]
    end
    subgraph pd["Pydantic の仕事"]
        MODEL["TodoCreate<br/>形の設計図"]
        CHECK["JSON を検証して<br/>TodoCreate に詰める"]
    end
    SORT -->|"body の中身を渡す"| CHECK
    MODEL -.->|"設計図を読む"| CHECK
    CHECK -->|"全部の失敗をまとめて返す"| ERR
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**あなたが書くのは `TodoCreate`（設計図）だけ。** 検証を動かすのは Pydantic、
それを HTTP の 422 に変えるのは FastAPI。**Pydantic 自身は HTTP を知らない**（P2-2 では設定ファイルの検証にも使う）。

#### (b) 失敗したとき、どこまで届くか

```mermaid
sequenceDiagram
    participant C as curl
    participant F as FastAPI
    participant P as Pydantic
    participant H as create_todo()
    participant L as todos リスト

    C->>F: POST /todos {"title": 123}
    F->>P: body を TodoCreate として検証
    alt 形が合う
        P-->>F: TodoCreate の実物
        F->>H: todo=... で呼ぶ
        H->>L: append
        H-->>C: 200 + JSON
    else 形が合わない
        P--xF: 失敗の一覧
        F--xC: 422 + loc ["body", "title"]
        Note over H,L: 呼ばれない。リストも増えない
    end
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**失敗した側の矢印は、`create_todo()` にも `todos` にも届かない。** これを 4-6 で実際に確かめる。

---

### 4-2a. 🔤 入口の2行

#### 🔤 `@app.post("/todos")`
**読み方**: 「アット・アップ・ドット・ポスト、スラッシュ・トゥードゥーズ」
**要するに**: `@app.get` の**「送ってきたものを受け取る」版**の貼り紙。中身を持ったお届け物を受け付ける窓口。

#### 🔤 `class TodoCreate(BaseModel):`
**読み方**: 「クラス・トゥードゥー・クリエイト、ベース・モデル」
**要するに**: **申込用紙のひな形**。「タイトル欄は必須、完了欄は空なら『いいえ』」と、用紙の書き方を決めたもの。

#### 🔤 `Field(min_length=1, max_length=200)`
**読み方**: 「フィールド、ミン・レングス・イコール・いち、マックス・レングス・イコール・にひゃく」
**要するに**: 用紙の**1つの欄への注文**。「1文字以上、200文字まで」。P1-3 の `Query()` の、用紙の欄版。

---

### 4-2. 🔬 仕組み解剖

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `@app.post("/todos")` | パスオペレーションデコレータ（POST） | `@app.get` と同じく**起動時に**経路表へ `("POST", "/todos") → create_todo` を1行書く。同じ `/todos` でも **GET とは別の行**になる |
| `todo: TodoCreate` | リクエストボディ | **起動時**、FastAPI は引数の型が `BaseModel` の仲間だと見て「これはボディ」と判定する（図は 4-4）。**リクエストごと**に、ボディを JSON として読み、Pydantic に `TodoCreate` として検証させ、**できあがった実物**を `todo` に渡す |
| `Field(min_length=1, max_length=200)` | フィールドの制約 | 型（`str`）に加えて、長さの条件を**設計図に書き込む**。検証は Pydantic が行う。`Annotated` の2枚目の札なので、**mypy は見ない**（P1-3 の 3-3 参照） |

**いつ評価されるか**: `class TodoCreate` が読み込まれた時点（起動時）で、Pydantic が**検証の手順を組み立てて**持っておく。
リクエストごとに走るのは、その手順を実行する部分だけ。

**どの道具の責務か**: ボディを読んで引数に振り分けるのは FastAPI、**形を検証して詰めるのは Pydantic**（図 4-1b(a)）。

**失敗したらどうなるか**: 全部 422。`loc` の1つ目が **`body`** になり、2つ目に**どの欄か**が入る。

| 失敗 | `type` | `loc` |
| --- | --- | --- |
| `title` が無い | `missing` | `["body", "title"]` |
| `title` が数値 | `string_type` | `["body", "title"]` |
| `title` が空文字 | `string_too_short` | `["body", "title"]` |
| JSON が壊れている | `json_invalid` | `["body", 13]`（**13文字目**で壊れた） |

**既知スタックとの対応**: zod の `TodoCreate.parse(req.body)` を、**ハンドラの手前に自動で挟んだ**形。
違いは2つ。(1) 失敗時に**自分で `res.status(422)` を書かなくてよい**。(2) zod のスキーマは TS の型と別に書くが、
Pydantic のクラスは**型そのもの**なので、mypy が `todo.title` を `str` として扱える。

---

### 4-3. 🐍 Python解説

#### 🐍 `class TodoCreate(BaseModel):`（クラスの定義と継承）

**読み方**: 「クラス／トゥードゥー・クリエイト／かっこ ベース・モデル／コロン」

**たとえ**: **申込用紙のひな形**を作っている。
`class` が「これからひな形を作ります」、`TodoCreate` がひな形の名前。
`(BaseModel)` は「**Pydantic が用意した基本の用紙を下敷きにします**」。
下敷きのおかげで、「欄が埋まっているか調べる」「JSON にする」といった**用紙としての機能が最初から全部ついてくる**。
行末の `:` から下（字下げされた範囲）が、この用紙にどんな欄があるかの一覧。

**正確には**:
- `class 名前:` = **クラス**（ひな形）を定義する合図。字下げされた範囲がクラスの中身。`def` と同じく行末の `:` が要る
- `class 名前(親):` = `()` の中のクラスを**引き継ぐ**（これを**継承**と呼ぶ）。親が持つ機能を、子がそのまま使える
- ひな形から作った1枚1枚を**インスタンス**（実物）と呼ぶ。`todo` 引数に入ってくるのは、Pydantic が作った `TodoCreate` の実物
- クラス名は**単語の頭を大文字**でつなぐのが Python の慣習（`TodoCreate`）。関数名は小文字と `_`（`create_todo`）

**TS なら**: `class TodoCreate extends BaseModel { ... }` が形としては近い。
違いは2つ。**`extends` の代わりに `()`**、そして **`{}` の代わりに字下げ**。

⚠️ **`(BaseModel)` を書き忘れると**、ただのクラスになる。FastAPI はボディと判定できず、起動時にエラーになる。

#### 🐍 クラスの中の `title: 型` と `done: bool = False`

```python
    title: Annotated[str, Field(min_length=1, max_length=200)]
    done: bool = False
```

**読み方**: 「タイトル コロン アノテイテッド…」「ダン コロン ブール イコール フォルス」

**たとえ**: 用紙の**欄**。`title` は「タイトル欄。文字で、1〜200文字」、
`done` は「完了欄。はい／いいえ。**書かなければ『いいえ』**」。

**正確には**:
- クラスの中に `名前: 型` と書くと、それが**欄（フィールド）**になる。**`=` が無い欄は必須**、`= 値` がある欄は省略できて、省略時はその値になる
- これは P1-3 の「既定値つき引数」（3-3）と**同じ規則**。既定値があれば任意、無ければ必須
- 普通の Python のクラスでは `名前: 型` は「型のメモ」にすぎないが、**`BaseModel` を継承したクラスでは、Pydantic がこのメモを読んで検証の規則にする**

**TS なら**: `{ title: string; done?: boolean }` が近い。
ただし TS の `?` は「無いかもしれない」で終わるのに対し、`= False` は「**無ければ False を入れる**」。
受け取った後の `todo.done` は必ず `True` か `False` で、**「無い」状態は残らない**。

#### 🐍 `bool` と `True` / `False`

**読み方**: 「ブール」「トゥルー」「フォルス」

**たとえ**: **はい／いいえ**の2択だけが入る欄。

**正確には**:
- `bool` = 真偽値（はい・いいえ）の型。入る値は `True` と `False` の**2つだけ**
- **先頭が大文字**。`true` と書くと「そんな名前は無い」とエラーになる
- JSON に変換されると `true` / `false`（小文字）になる。4-6 の出力で `"done":false` と出るのはこのため

**TS なら**: `boolean` と `true` / `false`。**大文字小文字だけが違う**。

#### 🐍 `Annotated[str, Field(...)]`（2度目）

**`Annotated[型, 札]` は1枚目が本当の型、2枚目は読みたい道具だけが読む札。P1-3 の 3-3 参照。**
ここでは2枚目を読むのが FastAPI ではなく **Pydantic** になっただけ。

#### 🐍 `#`（コメント）

**読み方**: 「シャープ」（「ハッシュ」とも）

**正確には**: `#` から行末までは**Python が読まない**。人間向けのメモ。
TS の `//` と同じ。**複数行用の `/* */` は無い**ので、行ごとに `#` を付ける。

#### 🐍 `todos: list[TodoCreate] = []`

**読み方**: 「トゥードゥーズ コロン リスト・トゥードゥー・クリエイト イコール かくかっこ」

**たとえ**: **申込用紙を綴じていくファイル**。`[]` は「まだ1枚も綴じていない空のファイル」。

**正確には**:
- `list` = **順番つきで並べておく入れ物**（リスト）。`[]` が空のリスト、`[a, b]` が2つ入ったリスト
- `list[TodoCreate]` = 「中身は `TodoCreate` だけ」という型。`dict[str, str]`（P1-2）と同じく、`[]` の中が中身の型
- `変数名: 型 = 値` = 変数に**型を書いてから**代入する形。関数の引数と同じ書き方を、ふつうの変数にも使える
- この行は**関数の外**に書いてあるので、ファイルが読み込まれたとき（起動時）に**1回だけ**実行される。
  だからリクエストをまたいで**同じリストが使い回され**、前のリクエストで入れたものが次のリクエストでも見える

**TS なら**: `const todos: TodoCreate[] = [];`。**型の書き方が `TodoCreate[]` ではなく `list[TodoCreate]`**。

#### 🐍 `todos.append(todo)`

**読み方**: 「トゥードゥーズ・ドット・アペンド」

**たとえ**: ファイルの**一番後ろに1枚綴じる**。

**正確には**:
- `.` = 「その物が持っている機能を使う」印。`todos.append` は「`todos` というリストが持つ `append` という機能」
- `append(x)` = リストの**末尾に x を1つ足す**。**リストそのものが書き換わる**（新しいリストは作らない）

**TS なら**: `todos.push(todo)`。名前が `push` ではなく `append`。

#### 🐍 `from app.schemas.todo import TodoCreate`（`.` 区切りの import）

**読み方**: 「フロム・アップ・ドット・スキーマズ・ドット・トゥードゥー・インポート・トゥードゥー・クリエイト」

**正確には**: `.` は**フォルダの区切り**。`app.schemas.todo` は `app/schemas/todo.py` を指す。
途中のフォルダ（`app/`、`app/schemas/`）に `__init__.py` が要るのは P1-2 の 2-3a(1) のとおり。

> ⏭️ **後で回収**: import が**壊れたときの読み方と直し方**は P1-8（ファイルを本格的に分ける回）。

---

### 4-3a. 🐍 Python の道具立て ／ 4-3b. 🧩 周辺注

このステップでは該当なし。

---

### 4-4. 解説 — なぜこう設計するか

#### 🏛 設計パターン: 入口で弾く

**① 問題 — ボディを `dict` で受けて、ハンドラの中で調べると**

```python
# ❌ 問題を見せるための書き方（本編では使わない）
@app.post("/todos")
def create_todo(body: dict[str, object]) -> dict[str, object]:
    title = body.get("title")
    if title is None:
        return {"error": "title がありません"}
    if not isinstance(title, str):
        return {"error": "title は文字列にしてください"}
    return body
```

> このコードは**読めなくてよい**（書くことも無い）。`if` は「もし〜なら」、`isinstance` は「〜の種類か調べる」とだけ。

```
POST {}                              → {"error":"title がありません"}           [200]
POST {"title":123,"done":"maybe"}    → {"error":"title は文字列にしてください"} [200]
POST {"title":"ok","done":"maybe"}   → {"title":"ok","done":"maybe"}          [200]
```

✅ 検証済み: 上のコードを別ファイルで起動し、`curl` で取得（ruff / mypy も通過）。

困りごとが**3つ同時に**出ている。

1. **エラーなのに 200。** 自分で 422 を書き忘れると、クライアントは成功と区別できない
2. **最初の1つで止まる。** 2か所間違っていても、1つ直して送り直すまで2つ目が分からない
3. **調べ忘れが素通りする。** `done` のチェックを書かなかったので `"maybe"` がそのまま保存された。
   しかもこの `if` は **`PUT /todos/{id}` にも同じものが要る**（P1-7）

**② 解 — 形をクラスに書き、引数の型にする**

4-1 の `TodoCreate` がそれ。4-6 で見るとおり、3つとも消える（422 になる／**全部の失敗が一度に返る**／書いた欄は必ず調べられる）。

**③ 名前** — これには **「入口で弾く」（バリデーション境界）** という名前が付いている。
**外から来たデータは、中に入る門の1か所で調べ、門の内側では「もう正しい」と信じて書く**、という考え方。

**④ たとえ** — 会場の**受付**。入口で招待状を1回確かめれば、中の各部屋で毎回確かめなくていい。

**⑤ 使わない判断** — **データベースを見ないと分からない条件**（「同じタイトルが既にあるか」「その ID が存在するか」）は、
入口の設計図には書けない。これはハンドラの中で調べて、404 や 409 を返す（**P1-7** の `HTTPException`）。
**形の検査は入口、中身の事情の検査は中**、と分ける。

#### 🪜 なぜなぜ: なぜ型が `BaseModel` だと「ボディ」になるのか

**なぜ① `todo: TodoCreate` と書いただけで、なぜボディから読まれるのか**
→ FastAPI は**起動時に**引数を1つずつ見て、置き場所を決めている。

```mermaid
flowchart TB
    ARG["引数1つ"]
    Q1{"パスの {} に<br/>同じ名前がある？"}
    Q2{"int / str / bool など<br/>1つの値の型？"}
    Q3{"BaseModel の仲間？"}
    PATH["path"]
    QUERY["query"]
    BODY["body"]
    ARG --> Q1
    Q1 -->|はい| PATH
    Q1 -->|いいえ| Q2
    Q2 -->|はい| QUERY
    Q2 -->|いいえ| Q3
    Q3 -->|はい| BODY
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

この3つの規則は公式に明記されている。P1-3 の `item_id`（パスに名前がある）と `q`（1つの値）も、同じ規則で振り分けられていた。
根拠: https://fastapi.tiangolo.com/tutorial/body/#request-body-path-query-parameters

**なぜ② なぜ `Body()` のような印を毎回書かせず、型で決めるのか**
→ **欄が何個もある「まとまり」は、URL に自然に載らない**から。`?title=a&done=false` はまだしも、
入れ子や配列を URL に詰めると読めなくなる。**まとまりを表す型なら、置き場所はボディしかありえない**ので、
印を書かせるのは同じことを2回言わせるだけになる。よくある形は**型だけで決まり**、印（`Query()` など）は**例外を書くとき**に使う。

**なぜ③ では、型で自動的に決まる方式は何を失うのか** 🤔 まず自分で考える

<details><summary>答え</summary>

**「どこから読まれるか」がコードに書かれていない**。規則を知らない人には見えない。
典型的な事故が `list[str]` で、「1つの値」ではないので、`Query()` を付け忘れると**クエリではなくボディ**と判定される。

```
@app.post("/x")
def x(tags: list[str]) -> list[str]: ...
→ OpenAPI 上: parameters なし / requestBody あり
```

✅ 検証済み: FastAPI 0.141.1 で `app.openapi()` を読んで確認。
根拠: https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#query-parameter-list-multiple-values

**手当て**（§4.2.1 ルール6）: 振り分けの**結果は OpenAPI スキーマに必ず出る**。
`parameters` に `"in": "query"` で並ぶか、`requestBody` に入るか。**P1-6** で `/openapi.json` を読めるようになれば、
「どこから読まれるつもりか」を**起動して1秒で確認**できる。
コードに書かない代わりに、**生成物を見れば正確に分かる**という取り引き（P1-2 なぜなぜ③ の「一覧性」と同じ形）。
</details>

> 🧠 **FastAPI の考え方**: 外から来るデータの**形**は、クラスで1回だけ書く。
> ハンドラの1行目に来た時点で `todo` は**必ず正しい形**をしている。だから中身の処理だけを書けばいい。

---

### 4-5. 🏢 実務メモ ／ ⚠️ アンチパターン ／ 🔓 教材用の簡略化

> 🏢 **実務メモ**: 文字列の欄には**最大の長さを必ず付ける**。付けないと、1MB のタイトルも「正しい文字列」として通り、
> そのまま保存や処理に回る。長さの上限は、入力チェックの基本項目として挙げられている。
> 根拠: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html

> ⚠️ **アンチパターン**: ボディを `dict` で受け取る（4-4 の ① の形）。検証が消えるだけでなく、
> **OpenAPI スキーマにも形が出ない**。Pydantic モデルで受ければ、検証と仕様書の両方が同じ1か所から作られる。
> 根拠: https://fastapi.tiangolo.com/tutorial/body/#results

> 🔓 **教材用の簡略化**: TODO を**関数の外のリスト**に置いている。サーバを止めると消え、
> サーバを複数の**プロセス**（同時に動く別々のプログラム）で動かすと、**それぞれが別のリストを持つ**。
> **本番では**: データベースに置く（**P3** で MySQL に置き換える）。
> 根拠: https://fastapi.tiangolo.com/deployment/concepts/#memory-per-process

---

### 4-6. 🔮 予測 → 動作確認

**先に予想してから実行する。**

1. `{"title": 123}` を送ると何が返るか。その後 `GET /todos` の件数は増えているか
2. `{"title": 123, "done": "maybe"}` のように**2か所**間違えると、エラーはいくつ返るか
3. 次の2つは 200 か 422 か。(a) `{"title":"a","done":"true"}`（`true` が**文字列**）(b) `{"title":"b","priority":5}`（**設計図に無い欄**）

<details><summary>実行と結果</summary>

```bash
uv run uvicorn app.main:app --port 8000 --reload
```

**正常系**

```bash
curl -sS -X POST http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' -d '{"title":"牛乳を買う"}'
```
```
{"title":"牛乳を買う","done":false}
```

`done` を送っていないのに `false` が入っている。`= False` の既定値。

**1 の答え: 422。リストは増えない**

```json
{"detail":[{"type":"string_type","loc":["body","title"],
"msg":"Input should be a valid string","input":123}]}
```

**`loc` の1つ目が `body`**。P1-3 の `path` / `query` と並べて3種類そろった。
`123` を `"123"` に**直してはくれない**（数値から文字列への変換は Pydantic が許していない）。

**2 の答え: 2つ。まとめて返る**

```json
{"detail":[
 {"type":"string_type","loc":["body","title"],"msg":"Input should be a valid string","input":123},
 {"type":"bool_parsing","loc":["body","done"],
  "msg":"Input should be a valid boolean, unable to interpret input","input":"maybe"}]}
```

4-4 の ① の手書き版は1つ目で止まっていた。**Pydantic は全部の欄を調べてから、失敗を一覧で返す**。
根拠: https://pydantic.dev/docs/validation/latest/concepts/models/#validating-data

**3 の答え: どちらも 200**

```
(a) {"title":"a","done":true}
(b) {"title":"b","done":false}
```

(a) は文字列の `"true"` が**本物の `true` に変換**された。`bool` の欄は `"yes"` / `"on"` / `"1"` なども受け付ける
（`"maybe"` は受け付けない）。(b) の `priority` は**黙って捨てられた**。どちらも Pydantic の既定の振る舞い。
根拠: https://pydantic.dev/docs/validation/latest/concepts/conversion_table/ ／
https://pydantic.dev/docs/validation/latest/concepts/models/#extra-data

**最後に、リストの中身**

```bash
curl -sS http://127.0.0.1:8000/todos
```
```
[{"title":"牛乳を買う","done":false},{"title":"a","done":true},{"title":"b","done":false}]
```

**200 を返した3件だけが入っている。** 422 になったリクエストは、`create_todo()` の `append` まで**届いていない**（4-1b(b) の図のとおり）。

**`/items/` を消したことの確認**

```bash
curl -sS http://127.0.0.1:8000/items/1
```
```
{"detail":"Not Found"}
```
</details>

✅ 検証済み（上の出力はすべて実行して取得）。

> ⏭️ **後で回収**: 3(b) の「知らない欄を黙って捨てる」を**422 にしたい**ときは、`model_config` で設定を変える。**P1-5** で扱う。

---

### 4-6b. 🧾 OpenAPI スキーマの差分

**まだ対象外**（差分を出し始めるのは P1-6 から。§4.14）。

> ⏭️ **後で回収**: `TodoCreate` は仕様書の `components.schemas` に1項目として載り、
> `POST /todos` の `requestBody` からは `{"$ref": "#/components/schemas/TodoCreate"}` という**矢印**で指される。
> `min_length=1` は `"minLength": 1` として出ている。読み方は **P1-6**。

---

### 4-7. ✅ 想起チェック

1. `def f(todo: TodoCreate)` の `todo` がボディと判定されるのは、いつか。何を見て決めているか
2. 422 のとき `create_todo()` が呼ばれていないことを、このステップではどうやって確かめたか
3. `done: bool = False` の `= False` を消すと、何が変わるか
4. 手書きの `if` で検証するやり方に比べて、困りごとが3つ消えた。何と何と何か
5. 「同じタイトルが既にある」を 422 と同じ入口で弾けないのはなぜか

<details><summary>答え</summary>

1. **起動時。** 引数の型が `BaseModel` の仲間かどうかを見ている（パスに名前がある → path、1つの値 → query、`BaseModel` → body）。
2. **`GET /todos` の件数。** 422 になった送信はリストに増えていなかった。
3. **`done` が必須になる。** 送らないと `missing` で 422。既定値の有無が「省略できるか」を決める（P1-3 と同じ規則）。
4. **失敗なのに 200 になる**（→ 必ず 422）／**最初の1つで止まる**（→ 全部まとめて返る）／**調べ忘れが素通りする**（→ 書いた欄は必ず調べられる）。
5. **データベースを見ないと分からない**から。入口で調べられるのは「形」だけ。中身の事情はハンドラの中で調べる（P1-7）。
</details>

---

### 4-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| `@app.post()` | 4-2a で入口の2行 / 4-2 で仕組み解剖（GET とは経路表の別の行） |
| `BaseModel`（ボディ判定） | 4-2a / 4-2 で仕組み解剖 / 4-4 で なぜなぜ3段（代償の手当ては ⏭️ **P1-6** で回収） |
| `Field()` | 4-2a / 4-2 で仕組み解剖 / 4-5 の実務メモ |
| 422 の自動応答（`body` 版） | 4-2 の失敗表 / 4-6 で実挙動（**P1-3 の ⏭️「ボディの 422 は P1-4」を回収**） |
| `class` / 継承 `(BaseModel)` | 4-3 で Python解説 |
| クラスの中の `名前: 型` / 既定値 | 4-3 で Python解説（必須と任意の規則） |
| `bool` / `True` / `False` | 4-3 で Python解説（先頭が大文字） |
| `Annotated`（2度目） | 4-3 で1行復習 |
| `#`（コメント） | 4-3 で Python解説 |
| `list[...]` / `[]` / 関数の外の変数 | 4-3 で Python解説（起動時に1回だけ作られる） |
| `.append()` / `.` | 4-3 で Python解説 |
| `.` 区切りの import | 4-3 で Python解説 / ⏭️ **壊れたときの直し方は P1-8** |
| 🏛 入口で弾く | 4-4 で 問題 → 解 → 名前 → たとえ → 使わない判断 |
| 知らない欄を捨てる振る舞い | 4-6 の Q3 / ⏭️ **P1-5 の `model_config` で回収** |
| `/items/` の削除 | 4-1 / 4-6 で 404 を確認（**P1-3 の 💡補足を回収**） |

**未回収: 0件**（`⏭️` 宣言は4件、すべて回収先を明示）

---

### 4-9. 📌 進捗の更新

`README.md` の進捗表 P1a を「P1-4 完了」、次の一手を `M1: P1 ステップ5` に更新した。

**次のステップ**: P1-5「返す形を宣言する」。いまの `-> TodoCreate` には **ID が無い**。
受け取る形（`TodoCreate`）と返す形（`TodoRead`）を**別のクラスに分け**、作成成功を **201** で返す。
4-6 で見た「知らない欄を黙って捨てる」を `model_config` で変えるのもここ。

---

## P1-5: 返す形を宣言する

**作るもの**: `POST /todos` が **ID 付きの `TodoRead`** を **201** で返す。知らない欄を送られたら 422 で弾く
**重要度**: 🔴 毎日使う — 「受け取る形」と「返す形」を分けるのは、この先すべての作成・取得エンドポイントの基本形になるため
**前ステップとの接続**: P1-4 の `-> TodoCreate` には **ID が無かった**。4-6 の Q3(b) で見た「知らない欄を黙って捨てる」もここで変える

### 5-0. このステップの初出トークン

| 系統 | トークン |
| --- | --- |
| **FastAPI** | 返す形の宣言（戻り値の型 / `response_model`）/ `status_code=201` / `model_config`（3つ = 上限） |
| **Python** | クラスを呼んで実物を作る `TodoRead(...)` / 名前付きで渡す引数 `id=...` / `len()` / `todo.title`（欄を読む `.`）/ クラスの中の `名前 = 値`（`:` 無し） |
| **【道具】** | —（該当なし） |
| **周辺** | `jq` / `curl -w '%{stderr}%{http_code}\n'` |

> 💡 **このステップから、コードは自分で書く。** 5-1 には**要件と骨組み（`# TODO:` の穴）**だけを置き、
> 完成形は `<details>` に入れた。`_prompt.md` §6.1 では新しい概念の初回は完成コードを全文出すことになっているが、
> **学習者の希望で骨組みにした**（解説は全文を前提に書いてある）。

---

### 5-1. コード

#### 要件

1. `app/schemas/todo.py` に **`TodoRead`** を足す。欄は `id`（整数）/ `title`（文字列）/ `done`（真偽値）。**3つとも必須**
2. `TodoCreate` は**設計図に無い欄を 422 で弾く**ようにする
3. `POST /todos` は、成功したら **201** で `TodoRead` を返す。`id` は **1 から順に**振る
4. `todos` リストと `GET /todos` も `TodoRead` に揃える
5. ruff / mypy が通る（コミットすれば pre-commit が確かめる）

#### 骨組み: `app/schemas/todo.py`

```python
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    # TODO: 設計図に無い欄を 422 にする設定を1行（ConfigDict を使う）

    title: Annotated[str, Field(min_length=1, max_length=200)]
    done: bool = False


class TodoRead(BaseModel):
    # TODO: id / title / done の3つの欄。どれも既定値なし
    ...
```

#### 骨組み: `app/main.py`（変わる部分だけ）

```python
from app.schemas.todo import TodoCreate, TodoRead

todos: list[TodoRead] = []


@app.post("/todos")  # TODO: 成功時のステータスを 201 にする
def create_todo(todo: TodoCreate) -> TodoRead:
    # TODO: id を振って TodoRead の実物を作り、リストに足して返す
    ...


@app.get("/todos")
def list_todos() -> list[TodoRead]:
    return todos
```

> `...`（ドット3つ）は「**ここはまだ空**」という印で、Python が文法として許している置き場所。穴を埋めたら消す。

<details><summary>完成形（自分で書いてから開く）</summary>

`app/schemas/todo.py`

```python
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)]
    done: bool = False


class TodoRead(BaseModel):
    id: int
    title: str
    done: bool
```

`app/main.py`（全文）

```python
from fastapi import FastAPI

from app.schemas.todo import TodoCreate, TodoRead

app = FastAPI()

todos: list[TodoRead] = []


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate) -> TodoRead:
    new_todo = TodoRead(id=len(todos) + 1, title=todo.title, done=todo.done)
    todos.append(new_todo)
    return new_todo


@app.get("/todos")
def list_todos() -> list[TodoRead]:
    return todos
```

</details>

✅ 検証済み: Python 3.12.13 / FastAPI 0.141.1 / Pydantic 2.13.5 / jq 1.8.2。
完成形を別の場所にコピーして `ruff check` = `All checks passed!`、`ruff format --check` = `4 files already formatted`、
`mypy` = `Success: no issues found in 4 source files`。実レスポンスは 5-6。

> 🔓 **教材用の簡略化**: `id` を `len(todos) + 1` で振っている。**削除が無いうちしか正しくない**
> （3件のうち1件を消すと、次に振る `id` が既存と重なる）。
> **本番では**: データベースに振らせる（**P3** の自動採番）。
> ⏭️ **P1-7** で `DELETE` を足すときに、この重なりを予測問題として実際に踏む。
> 根拠: https://dev.mysql.com/doc/refman/8.0/en/example-auto-increment.html

---

### 5-1b. 📊 図解

#### (a) 入口の門と出口の門

```mermaid
flowchart LR
    C["curl"]
    subgraph in["入口の門 TodoCreate"]
        IN{"形は合う？<br/>知らない欄は無い？"}
    end
    H["create_todo()<br/>id を振る"]
    subgraph out["出口の門 TodoRead"]
        OUT{"形は合う？"}
    end
    E422["422<br/>loc: body<br/>送った側の間違い"]
    E500["500<br/>loc: response<br/>サーバ側の間違い"]
    OK["201 + TodoRead"]
    C --> IN
    IN -->|はい| H
    IN -->|いいえ| E422
    H --> OUT
    OUT -->|はい| OK
    OUT -->|いいえ| E500
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**門は2つある。** P1-4 までは入口しか見ていなかった。
入口で落ちるのは**送った人の間違い**なので 422、出口で落ちるのは**あなたのコードの間違い**なので **500**。
同じ「形が合わない」でも、**誰の責任か**で番号が変わる（5-6 の Q3 で実際に起こす）。

#### (b) 1回の作成で、誰が何をするか

```mermaid
sequenceDiagram
    participant C as curl
    participant F as FastAPI
    participant P as Pydantic
    participant H as create_todo()

    C->>F: POST /todos {"title":"牛乳を買う"}
    F->>P: TodoCreate として検証
    P-->>F: TodoCreate の実物
    F->>H: todo=... で呼ぶ
    H->>H: TodoRead(id=1, ...) を作る
    H-->>F: TodoRead の実物
    F->>P: TodoRead として検証し JSON に直す
    P-->>F: {"id":1,"title":"牛乳を買う","done":false}
    F-->>C: 201 + JSON
```

✅ 描画確認済み: mermaid 12.0.0 でパース通過。

**Pydantic は2回呼ばれている。** 1回目は入ってくるときの検証、2回目は出ていくときの検証と JSON への変換。
2回目はハンドラの**後ろ**で動くので、`return` した後に FastAPI の中で起きる。

---

### 5-2a. 🔤 入口の2行

#### 🔤 `-> TodoRead`（返す形の宣言）／ `response_model=TodoRead`
**読み方**: 「アロー・トゥードゥー・リード」／「レスポンス・モデル・イコール・トゥードゥー・リード」
**要するに**: **出口の門に貼る「持ち出してよいもの一覧」**。一覧に無いものは門で取り上げられる。

#### 🔤 `status_code=201`
**読み方**: 「ステータス・コード・イコール・にひゃくいち」
**要するに**: **うまくいったときに返す番号**を、貼り紙に書いておく。201 は「新しく作りました」。

#### 🔤 `model_config = ConfigDict(extra="forbid")`
**読み方**: 「モデル・コンフィグ・イコール・コンフィグ・ディクト、エクストラ・イコール・フォービッド」
**要するに**: 用紙のひな形全体への**注意書き**。「**書く欄の無いことを書いてきたら受け付けない**」。

---

### 5-2. 🔬 仕組み解剖

| 部品 | 正式名称 | 実行時に何が起きるか |
| --- | --- | --- |
| `-> TodoRead` | 戻り値の型によるレスポンスモデル | **起動時**、FastAPI は戻り値の型を読んで**レスポンスモデル**にする。**リクエストごと**に、ハンドラが返したものを `TodoRead` として検証し、**`TodoRead` に無い欄を落としてから** JSON にする。合わなければ **500** |
| `response_model=TodoRead` | レスポンスモデル（デコレータ側） | 上と同じことをデコレータ側に書く形。**両方あれば `response_model` が勝つ**。戻り値の型と実際に返すものが違うとき（辞書を返すなど）に使う（5-6 の Q3） |
| `status_code=201` | レスポンスのステータスコード | 成功したときの番号を**起動時に**決めておく。**関数の引数ではなくデコレータの引数**。失敗時（422 など）には効かない |
| `model_config = ConfigDict(extra="forbid")` | モデルの設定 | **クラスが読み込まれた時点で** Pydantic が検証手順に組み込む。知らない欄があると `extra_forbidden` で落ちる。既定は `"ignore"`（黙って捨てる。4-6 の Q3(b)） |

**いつ評価されるか**: 4つとも**起動時に**読まれて検証の手順に組み込まれる。リクエストごとに走るのは、その実行だけ。

**どの道具の責務か**: 出口の検証と「無い欄を落とす」は **Pydantic**、それを呼ぶ順番と 201 / 500 を決めるのは **FastAPI**、
`extra="forbid"` は **Pydantic の設定**（FastAPI は関係しない）。

**失敗したらどうなるか**

| 失敗 | 番号 | どこに出るか |
| --- | --- | --- |
| 知らない欄を送った | **422**（`extra_forbidden`、`loc: ["body", "priority"]`） | レスポンスのボディ |
| 返す形が `TodoRead` に合わない | **500**（中身は `Internal Server Error` という文字だけ） | **サーバのターミナル**に `ResponseValidationError` と `loc: ('response', 'id')` |

**500 のとき、詳細はクライアントに返らない。** サーバ内部の事情を外に見せないため。原因は**サーバのログを読む**（P1-2 のトレースバックの読み方がここで効く）。

**既知スタックとの対応**: tRPC の `.output(zodSchema)` が近い。返す値を zod で検証し、**スキーマに無いキーを落とす**（zod の `.parse()` は既定で未知のキーを取り除く）。
違いは、FastAPI では**戻り値の型を書けば自動でそうなる**こと。Express には対応物なし（`res.json()` は渡したものを全部出す）。
根拠: https://fastapi.tiangolo.com/tutorial/response-model/#response-model-priority

---

### 5-3. 🐍 Python解説

#### 🐍 `TodoRead(id=..., title=..., done=...)`（クラスを呼んで実物を作る）

**読み方**: 「トゥードゥー・リード、アイディー・イコール…、タイトル・イコール…、ダン・イコール…」

**たとえ**: **ひな形の用紙に記入して、1枚の本物の書類にする**。
P1-4 では Pydantic が記入してくれた（ボディから `TodoCreate` を作った）。今回は**あなたが自分で記入する**。

**正確には**:
- クラスの名前の後ろに `()` を付けると、そのクラスの**実物（インスタンス）**が1つできる。関数を呼ぶのと同じ形
- `BaseModel` を継承したクラスでは、**このときも検証が走る**。`TodoRead(id="abc", ...)` なら、その場でエラーになる
- **`new` は書かない。** TS の `new TodoRead(...)` の `new` にあたる語は Python に無い

**TS なら**: `new TodoRead({ id: 1, title: "a", done: false })` に近い。**`new` が無い**のと、`{}` で包まず**直接並べる**のが違い。

#### 🐍 `id=len(todos) + 1`（名前付きで渡す引数）

**読み方**: 「アイディー・イコール・レン・トゥードゥーズ・プラス・いち」

**たとえ**: 用紙に**欄の名前を指さしながら**書き込む。「ID 欄はこれ、タイトル欄はこれ」。

**正確には**:
- `名前=値` の形で渡すと、**順番ではなく名前で**どの引数かが決まる。`Field(min_length=1)` や `Query(max_length=20)` も同じ形だった
- **`=` の左右に空白を入れない**のが慣習（`id=1`）。ふつうの代入 `x = 1` とは見た目で区別する。ruff format もそう揃える
- `len(x)` = x の**中に入っている数**を返す。空のリストなら `0`。だから1件目は `0 + 1 = 1`
- `len` は `from` で取り出さなくても**最初から使える**（Python に組み込まれている）

**TS なら**: 引数の名前指定は**対応物なし**（TS はオブジェクトを1つ渡して `{ id, title }` と分ける）。`len(todos)` は `todos.length`。

#### 🐍 `todo.title`（欄を読む `.`）

**正確には**: P1-4 の `todos.append` の `.` は「機能を使う」だったが、`()` が付かなければ**中の値を読む**。
`todo.title` は「`todo` の `title` 欄の値」。TS の `todo.title` と**まったく同じ**。
mypy は `todo` が `TodoCreate` だと知っているので、`todo.titel` と打ち間違えると**実行前に**教えてくれる。

#### 🐍 `model_config = ConfigDict(...)`（クラスの中の、`:` の無い行）

**読み方**: 「モデル・コンフィグ・イコール…」

**たとえ**: 用紙のひな形に**欄を足しているのではなく**、ひな形の**余白に注意書きを書いている**。

**正確には**:
- P1-4 で見たとおり、`BaseModel` の中の **`名前: 型`（`:` がある行）は欄**になる
- **`名前 = 値`（`:` が無い行）は欄にならない。** ただの値としてクラスに置かれる
- Pydantic は **`model_config` という名前だけ**を「設定」として特別に読む。**名前を1文字でも変えると、ただの値になって効かない**
- `ConfigDict(extra="forbid")` は設定を入れる入れ物を作っている。`extra` に入れられるのは `"ignore"`（既定）/ `"allow"` / `"forbid"`

**TS なら**: **対応物なし。** TS のクラスでは `:` の有無でこのような区別はしない。
「決まった名前の値を、ライブラリが設定として読む」という約束ごとは、Python のライブラリでよく使われる形。

#### 🐍 `...`（ドット3つ）

**正確には**: 骨組みの中身を**まだ書いていない**ことを示す置き場所。Python は字下げされた範囲が空だと文法エラーにするので、
「空です」と書く代わりに置く。**穴を埋めたら消す**。

---

### 5-3a. 🐍 Python の道具立て

このステップでは該当なし。

### 5-3b. 🧩 周辺注

> 🧩 **周辺注**: `jq` は **JSON を読みやすく並べ直す道具**。`curl ... | jq` で整形され、`| jq '.detail[] | {loc, input}'` のように**一部だけ取り出す**こともできる。
> 詳しい書き方は **P1-6**（`/openapi.json` を読む回）。**JSON でないもの**を渡すと `jq: parse error` になる（5-6 の Q3）。

> 🧩 **周辺注**: `curl -w '%{stderr}%{http_code}\n'` は、**ステータス番号だけを画面の別の出口（標準エラー）に出す**指定。
> ボディだけが `jq` に流れるので、番号と整形済み JSON を**同時に**見られる。`-i` はヘッダがボディに混ざり `jq` が読めなくなる。

---

### 5-4. 解説 — なぜこう設計するか

#### 🪜 なぜなぜ: なぜ受け取る形と返す形を別のクラスに分けるのか

**なぜ① `TodoCreate` を返すだけではだめなのか。何が足りないのか**
→ **`id` はサーバが決めるもの**だから。受け取るときには無く、返すときには要る。
1つのクラスで両方をやろうとすると、`id` を「あってもなくてもよい」にするしかない。
すると**クライアントが `id` を送ってきたときに受け付けてしまう**。5-6 の Q2 で、`{"id":999,...}` が 422 になるのを確かめる。

**なぜ② なぜ「返す形」まで型で決めるのか。返したいものを返せばよいのでは**
→ **返す側の失敗は、気づかないまま外に漏れる**から。
P3 で表の行をそのまま返すようになると、行には `hashed_password`（P4）のような**外に出してはいけない欄**が入ってくる。
返す形を宣言しておけば、**`TodoRead` に無い欄は出口で必ず落ちる**（5-6 の Q3 で実際に確かめる）。
「出してはいけないものを毎回消す」ではなく、「**出してよいものだけを並べる**」ほうが、書き忘れたときに安全な側に倒れる。
根拠: https://fastapi.tiangolo.com/tutorial/response-model/#return-type-and-data-filtering

**なぜ③ では、クラスを分けると何を払うのか** 🤔 まず自分で考える

<details><summary>答え</summary>

**同じ欄を2回書くことになる。** `title` と `done` は `TodoCreate` にも `TodoRead` にもある。
片方の `title` だけ `max_length` を変えて、もう片方を直し忘れる、という**ズレの種**が生まれる。

**手当て**（§4.2.1 ルール6）: 共通の欄を**親クラスにまとめて継承する**方法がある（`class TodoBase(BaseModel)` に `title` と `done` を置き、
`TodoCreate(TodoBase)` / `TodoRead(TodoBase)` とする）。公式もこの形を「重複を減らす」方法として示している。
根拠: https://fastapi.tiangolo.com/tutorial/extra-models/#reduce-duplication

**ただし今はやらない。** 欄が2つのうちは、継承でまとめるより**並べて書いたほうが読める**（どの欄があるかが1か所で見える）。
**P3-4**（表のモデルとスキーマを分ける回）で、`TodoRead` に欄が増えたときにもう一度判断する。
「重複を消す」は無料ではなく、**読むときに親クラスまで見に行く手間**と引き換えになる。
</details>

> 🧠 **FastAPI の考え方**: 門は**入口と出口の2つ**。入口は「受け付けてよいもの」、出口は「持ち出してよいもの」を宣言する。
> 入口で落ちれば 422（相手の間違い）、出口で落ちれば 500（自分の間違い）。

---

### 5-5. 🏢 実務メモ ／ ⚠️ アンチパターン

> 🏢 **実務メモ**: 作成が成功したら **201**。200 でも動くが、201 なら「**新しい何かができた**」ことが番号だけで伝わる。
> HTTP の仕様でも、POST で新しいものを作った場合は 201 を返すと定めている。
> 根拠: https://www.rfc-editor.org/rfc/rfc9110#name-post

> ⚠️ **アンチパターン**: 返す形を宣言せず、`-> dict[str, object]` で辞書をそのまま返す。
> 辞書に入っているものが**全部**外に出る（5-6 の Q3 の `/leak`）。**出口の門が無い状態**。
> 根拠: https://fastapi.tiangolo.com/tutorial/response-model/#fastapi-data-filtering

---

### 5-6. 🔮 予測 → 動作確認

**先に予想してから実行する。**

1. 1件作ると、ステータス番号と `id` は何になるか
2. 4-6 の Q3(b) と同じ `{"title":"b","priority":5}` は、今回は通るか。`{"id":999,"title":"c"}` はどうか
3. **（実験）** 下の3つのエンドポイントを `app/main.py` に**一時的に**足す。それぞれ何が返るか

```python
@app.get("/leak")
def leak() -> dict[str, object]:
    return {"id": 1, "title": "a", "done": False, "internal_note": "外に出したくない"}


@app.get("/filtered", response_model=TodoRead)
def filtered() -> dict[str, object]:
    return {"id": 1, "title": "a", "done": False, "internal_note": "外に出したくない"}


@app.get("/broken", response_model=TodoRead)
def broken() -> dict[str, object]:
    return {"title": "a", "done": False}
```

✅ 検証済み: この3つを足した状態で ruff / mypy が通る（`-> dict[str, object]` と書いているので、mypy は辞書を返しても怒らない）。

<details><summary>実行と結果</summary>

```bash
uv run uvicorn app.main:app --port 8000 --reload
```

**1 の答え: 201、`id` は 1**

```bash
curl -sS -w '%{stderr}%{http_code}\n' -X POST http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' -d '{"title":"牛乳を買う"}' | jq
```
```
201
{
  "id": 1,
  "title": "牛乳を買う",
  "done": false
}
```

もう1件作ると `"id": 2`。`GET /todos` の結果も `TodoRead` の形になる。

```bash
curl -sS http://127.0.0.1:8000/todos | jq -c
```
```
[{"id":1,"title":"牛乳を買う","done":false},{"id":2,"title":"卵","done":true}]
```

（`jq -c` は1要素1行に詰めて出す指定）

**2 の答え: どちらも 422**

```bash
curl -sS -w '%{stderr}%{http_code}\n' -X POST http://127.0.0.1:8000/todos \
  -H 'Content-Type: application/json' -d '{"title":"b","priority":5}' | jq
```
```
422
{
  "detail": [
    {
      "type": "extra_forbidden",
      "loc": [
        "body",
        "priority"
      ],
      "msg": "Extra inputs are not permitted",
      "input": 5
    }
  ]
}
```

P1-4 では黙って捨てられていたものが、**`extra_forbidden` で弾かれた**。
`{"id":999,"title":"c"}` も同じく `"loc": ["body", "id"]` で 422。**`id` は `TodoCreate` の欄ではない**ので、
クライアントが ID を選ぶことはできない（5-4 の なぜなぜ①）。

**3 の答え**

```bash
curl -sS -w '%{stderr}%{http_code}\n' http://127.0.0.1:8000/leak | jq -c
curl -sS -w '%{stderr}%{http_code}\n' http://127.0.0.1:8000/filtered | jq -c
curl -sS -w '%{stderr}%{http_code}\n' http://127.0.0.1:8000/broken | jq -c
```
```
200
{"id":1,"title":"a","done":false,"internal_note":"外に出したくない"}
200
{"id":1,"title":"a","done":false}
500
jq: parse error: Invalid numeric literal at line 1, column 9
```

- **`/leak`**: 門が無いので、`internal_note` まで**全部出た**
- **`/filtered`**: 返したものは同じ辞書なのに、`internal_note` が**消えた**。`response_model` の門で落ちた
- **`/broken`**: **500**。そして `jq` が壊れた。ボディが JSON ではないから。`-i` を付けて生のまま見る

```bash
curl -sS -i http://127.0.0.1:8000/broken
```
```
HTTP/1.1 500 Internal Server Error
content-type: text/plain; charset=utf-8

Internal Server Error
```

**クライアントには理由が返らない。** 理由は**サーバのターミナル**に出ている。**下から読む**（P1-2 の 2-3a(2)）。

```
fastapi.exceptions.ResponseValidationError: 1 validation error:
  {'type': 'missing', 'loc': ('response', 'id'), 'msg': 'Field required', 'input': {'title': 'a', 'done': False}}

  File ".../app/main.py", line 37, in broken
    GET /broken
```

**`loc` の1つ目が `response`**。path / query / body に続く**4つ目**で、「**返す側**の `id` が無い」と言っている。
最後の `File` の行が**あなたのファイルの `broken` 関数**（の貼り紙の行）を指している。

**確かめ終わったら、3つのエンドポイントは消す。**
</details>

✅ 検証済み（上の出力はすべて実行して取得。行番号 `line 37` は完成形の末尾に3つを足した場合で、`@app.get("/broken", ...)` の行を指す。足した位置によって変わる）。

---

### 5-6b. 🧾 OpenAPI スキーマの差分

**まだ対象外**（差分を出し始めるのは次の P1-6 から。§4.14）。

> ⏭️ **後で回収**: `POST /todos` の返り値の一覧は、今 `["201", "422"]` になっている（200 が消えて 201 に置き換わった）。
> `201` の中身は `{"$ref": "#/components/schemas/TodoRead"}`。**入口の形と出口の形の両方がそろった**ので、
> P1-6 で `/openapi.json` を `jq` で読む準備ができた。

---

### 5-7. ✅ 想起チェック

1. `-> TodoRead` と `response_model=TodoRead` を両方書いたら、FastAPI はどちらを使うか。`response_model` が要るのはどんなときか
2. 入口で形が合わないと 422、出口で合わないと 500。番号が違うのはなぜか
3. `model_config = ConfigDict(extra="forbid")` を `config = ConfigDict(extra="forbid")` と書いたら、どうなるか
4. `status_code=201` は、なぜ関数の引数ではなくデコレータに書くのか
5. 500 のとき、原因はどこで読むか

<details><summary>答え</summary>

1. **`response_model` が勝つ。** 実際に返すもの（辞書など）と、外に見せたい形が違うときに使う。
   戻り値の型は mypy のため、`response_model` は FastAPI のため、と役割を分けられる。
2. **誰の間違いかが違うから。** 入口は送った人の間違い（4xx）、出口はサーバのコードの間違い（5xx）。
3. **ただの値になり、設定として効かない。** Pydantic が設定として読むのは `model_config` という名前だけ。知らない欄はまた黙って捨てられる。
4. **ステータス番号はリクエストの中身ではなく、エンドポイントの性質だから。** 引数はリクエストから受け取るもの（path / query / body）の置き場所で、
   デコレータは「この窓口はこういう窓口」という宣言の置き場所。
5. **サーバのターミナル。** クライアントには `Internal Server Error` しか返らない。トレースバックを下から読み、`loc` が `response` で始まるかを見る。
</details>

---

### 5-8. 初出トークンの回収確認

| トークン | 扱い |
| --- | --- |
| 返す形の宣言（`-> TodoRead` / `response_model`） | 5-2a / 5-2 で仕組み解剖（優先順位）/ 5-4 なぜなぜ② / 5-6 の Q3 で実挙動（**P1-2 の ⏭️「実行時の効果は P1-5」を回収**） |
| `status_code=201` | 5-2a / 5-2 で仕組み解剖 / 5-5 の実務メモ / 5-6 の Q1 |
| `model_config` | 5-2a / 5-2 / 5-3 / 5-6 の Q2（**P1-4 の ⏭️「知らない欄を捨てる」を回収**） |
| クラスを呼んで実物を作る | 5-3 で Python解説（`new` が無い） |
| 名前付きの引数 / `len()` | 5-3 で Python解説 |
| `todo.title`（欄を読む `.`） | 5-3 で Python解説 |
| クラスの中の `名前 = 値` | 5-3 で Python解説（`:` の有無で欄か設定かが変わる） |
| `...` | 5-3 で Python解説 |
| `jq` / `curl -w '%{stderr}...'` | 5-3b で周辺注 / ⏭️ **`jq` の書き方は P1-6** |
| `dict[str, int \| str \| None]` の置き換え | 5-1 で `TodoRead` を戻り値にした（**P1-3 の ⏭️ を回収**） |
| `id` の重なり（🔓） | ⏭️ **P1-7 で DELETE を足すときに踏む** / 本番の手当ては **P3** |

**未回収: 0件**（`⏭️` 宣言は3件、すべて回収先を明示）

---

### 5-9. 📌 進捗の更新

`README.md` の進捗表 P1a を「**P1-5 完了（P1a 完了）**」、次の一手を `M2: P1a`（フェーズ末パック）に更新した。

**次のステップ**: **P1a のフェーズ末パック**（`M2: P1a`）。`app/main.py` と `app/schemas/todo.py` を**白紙から再現**し（翌日にやるのが推奨）、
宿題 Lv1〜Lv3 を解く。その後 P1b に入り、**P1-6「生成された仕様書を読む」**で、ここまで宣言してきた形が
`/openapi.json` にどう現れているかを `jq` で読む。

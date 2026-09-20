# デバッグ環境（Zed + iTerm2）

サーバは **iTerm2 で起動**し、Zed は**そこに接続（attach）する**。
Zed 側からサーバを起動しないので、ログは iTerm2 でそのまま読める。

設定ファイルは `.zed/debug.json`。

---

## 1. 準備（最初の1回だけ）

```bash
uv add --dev debugpy
```

✅ 検証済み: Zed 1.20.2 は自前の debugpy 1.8.21 を持っているが、それは **Zed が起動したプロセス用**。
iTerm2 から `uv run` で起動する場合はプロジェクトの `.venv` に必要なので、開発依存として入れる。

> 🧩 **周辺注**: `--dev` を付けると `pyproject.toml` の `[dependency-groups] dev` に入る。本番インストール時には含まれない。

---

## 2. iTerm2 でサーバを起動する

```bash
uv run python -m debugpy --listen 127.0.0.1:5678 \
  -m uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  --reload --reload-dir app
```

✅ 検証済み: Python 3.12.13 / uvicorn 0.53.0 / debugpy 1.8.21
（検証時は Zed 同梱の 1.8.21 を `PYTHONPATH` 経由で使用。プロジェクトには `uv add --dev` で 1.8.22 を導入済み）

| 部分 | 役割 |
| --- | --- |
| `python -m debugpy --listen 127.0.0.1:5678` | デバッガの受け口を 5678 番で開く。**アプリの 8000 番とは別ポート** |
| `-m uvicorn app.main:app` | その配下で `python -m uvicorn` を動かす |
| `--reload --reload-dir app` | `app/` 配下の変更だけを監視して自動再起動する |

起動すると `docs/` や `.md` を編集しても再起動しない。監視対象を `app/` に絞っているため。

### 起動直後のコードを止めたいとき

`@app.get()` の評価や `FastAPI()` の生成（= import 時に1回だけ走る処理）にブレークポイントを置く場合は、
`--wait-for-client` を足す。Zed が接続するまでサーバが起動を待つ。

```bash
uv run python -m debugpy --listen 127.0.0.1:5678 --wait-for-client \
  -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

⚠️ 未実行（自分で確認すること）。P1-1 の「起動時に `APIRoute` が登録される」を実物で確かめるときに使う。
このときは `--reload` を外す（リロードのたびに接続待ちで止まってしまうため）。

---

## 3. Zed から接続する

1. 止めたい行の**行番号の左**（ガター）をクリック → 赤丸が付く
2. `F4` でデバッグパネルを開く
3. **「FastAPI に接続 (iTerm2)」** を選んで実行
4. 別ターミナルで `curl http://127.0.0.1:8000/todos/2` などを叩く → 赤丸の行で止まる

⚠️ 未実行（Zed の画面操作のため、実機確認は各自）

---

## 4. 設定の意味

`.zed/debug.json` のキーのうち、意図があるもの。

| キー | 値 | 理由 |
| --- | --- | --- |
| `"request"` | `"attach"` | サーバは iTerm2 が持つ。Zed は繋ぐだけ |
| `"connect"` | `127.0.0.1:5678` | `--listen` で開いたポート |
| `"justMyCode"` | **`false`** | FastAPI / Starlette / Pydantic の内部にステップインできる。教材の「🔬 仕組み解剖」を実物で検証するため |
| `"subProcess"` | `true` | `--reload` の**子プロセス**にデバッガを注入する。これが無いと再起動後に止まらない |

### `--reload` してもブレークポイントが効く理由

uvicorn の `--reload` は「監視する親」と「実際に動く子」に分かれる。
`subProcess: true` により、**リロードで作り直された子プロセスにもデバッガが注入される**。

✅ 検証済み: リロードを挟んで子プロセスを観測した実測ログ

```
INFO:  Started reloader process [95460] using WatchFiles
[PROBE] pid=95468 ppid=95460 debugger_modules=['pydevd', '_pydevd_bundle']
WARNING: WatchFiles detected changes ... Reloading...
[PROBE] pid=95498 ppid=95460 debugger_modules=['pydevd', '_pydevd_bundle']
```

生まれ直した子（95498）にも `pydevd` が載っている。
また **5678 番は親が握り続ける**ので、リロードのたびに Zed を繋ぎ直す必要はない。

✅ 検証済み: リロード前後で `lsof -iTCP:5678` が同一 PID のまま LISTEN していることを確認

---

## 5. 注意点

### autosave（1秒）とリロードの相性

`~/.config/zed/settings.json` で `"autosave": { "after_delay": { "milliseconds": 1000 } }` が有効。
**ブレークポイントで止めている最中に `app/` 配下を編集すると、1秒後に保存 → リロード → 止まっていたプロセスごと消える。**

- 軽い確認なら `--reload` のままでよい（`--reload-dir app` で誤爆は減らしてある）
- 腰を据えて追うときは `--reload` を外して起動する

### ポートが埋まっているとき

```
ERROR: [Errno 48] Address already in use
```

`fastapi dev` が生きたままのことが多い。確認と停止:

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

✅ 検証済み: FastAPI CLI は起動できないと終了コード 3 で落ちる

---

## 6. 実行 SQL を見る（P3 以降）

SQLAlchemy が発行した SQL は `sqlalchemy.engine` ロガーに流れる。

| 方法 | 書き方 | 出るもの |
| --- | --- | --- |
| `echo=True` | `create_engine(url, echo=True)` | 実行 SQL とバインドパラメータ |
| `echo="debug"` | `create_engine(url, echo="debug")` | 上に加えて結果の行も |
| logging 直指定 | `logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)` | `echo=True` と同じ（`echo` は内部でこれをしている） |

**本教材では環境変数で切り替える形にする**（P2-2 の `Settings` に足して P3-1 で使う）。

```python
# app/config.py    [P2-2]
class Settings(BaseSettings):
    database_url: str
    sql_echo: bool = False
```

```python
# app/database.py  [P3-1]
engine = create_engine(settings.database_url, echo=settings.sql_echo)
```

```bash
# .env（開発機のみ）
SQL_ECHO=true
```

⚠️ 未実行（P3-1 で実際に書いて検証する）

> 🔓 **教材用の簡略化**: `echo=True` は SQL とともに**バインド値**も出す。メールアドレスやトークンがそのままログに載るため、開発機限定にする。
> **本番では**: 既定で無効にし、必要なときだけ一時的に有効化する。
> 根拠: https://docs.sqlalchemy.org/en/20/core/engines.html#configuring-logging

### デバッガと組み合わせる

ブレークポイントで止めた状態で、デバッグコンソールからバインド値を埋めた SQL を出せる。

```python
print(stmt.compile(engine, compile_kwargs={"literal_binds": True}))
```

⚠️ 未実行（P3 以降で使う）。N+1 の調査（P3 の宿題 Lv3）ではログを数えるよりこちらが速い。

from typing import Annotated

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
    return {"status": "ok"}


@app.get("/todos")
def list_todos(
    done: Annotated[bool | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    items = [t for t in _todos if done is None or t["done"] == done]
    return items[:limit]


@app.post("/todos", status_code=201)
def create_todo(todo: TodoCreate) -> TodoRead:
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

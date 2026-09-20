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

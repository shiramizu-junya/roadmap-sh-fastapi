from typing import Annotated, Any

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

app = FastAPI()


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
    """POST 用。id はサーバが決めるので含めない。done は省略できる"""

    done: bool = False


class TodoUpdate(TodoBase):
    """PUT 用。全置換なので done も必須にする"""

    done: bool


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
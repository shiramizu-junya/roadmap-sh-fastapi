from itertools import count

from fastapi import FastAPI, HTTPException, status

from app.schemas.todo import TodoCreate, TodoRead

app = FastAPI()

todos: list[TodoRead] = []

# 1, 2, 3, ... と番号を1枚ずつ出す発券機。消しても番号は戻らない
todo_ids = count(1)


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
    new_todo = TodoRead(id=next(todo_ids), title=todo.title, done=todo.done)
    todos.append(new_todo)
    return new_todo


@app.get("/todos", tags=["todos"], summary="TODO 一覧を取得")
def list_todos() -> list[TodoRead]:
    return todos


@app.get(
    "/todos/{todo_id}",
    tags=["todos"],
    summary="TODO を1件取得",
    responses={status.HTTP_404_NOT_FOUND: {"description": "指定した ID の TODO が無い"}},
)
def read_todo(todo_id: int) -> TodoRead:
    return find_todo(todo_id)


@app.put(
    "/todos/{todo_id}",
    tags=["todos"],
    summary="TODO を丸ごと置き換える",
    responses={status.HTTP_404_NOT_FOUND: {"description": "指定した ID の TODO が無い"}},
)
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
    responses={status.HTTP_404_NOT_FOUND: {"description": "指定した ID の TODO が無い"}},
)
def delete_todo(todo_id: int) -> None:
    todo = find_todo(todo_id)
    todos.remove(todo)

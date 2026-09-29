from fastapi import APIRouter, status

from app.dependencies import TodoDep
from app.schemas.todo import TodoCreate, TodoRead
from app.store import todo_ids, todos

router = APIRouter(prefix="/todos", tags=["todos"])

NOT_FOUND: dict[int | str, dict[str, str]] = {
    status.HTTP_404_NOT_FOUND: {"description": "指定した ID の TODO が無い"},
}


@router.post("", status_code=status.HTTP_201_CREATED, summary="TODO を1件作る")
def create_todo(todo: TodoCreate) -> TodoRead:
    new_todo = TodoRead(id=next(todo_ids), title=todo.title, done=todo.done)
    todos.append(new_todo)
    return new_todo


@router.get("", summary="TODO 一覧を取得")
def list_todos() -> list[TodoRead]:
    return todos


@router.get("/{todo_id}", summary="TODO を1件取得", responses=NOT_FOUND)
def read_todo(todo: TodoDep) -> TodoRead:
    return todo


@router.put("/{todo_id}", summary="TODO を丸ごと置き換える", responses=NOT_FOUND)
def update_todo(todo: TodoDep, body: TodoCreate) -> TodoRead:
    todo.title = body.title
    todo.done = body.done
    return todo


@router.delete(
    "/{todo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="TODO を削除する",
    responses=NOT_FOUND,
)
def delete_todo(todo: TodoDep) -> None:
    todos.remove(todo)

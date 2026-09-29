from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.schemas.todo import TodoRead
from app.store import todos


def get_todo(todo_id: int) -> TodoRead:
    for todo in todos:
        if todo.id == todo_id:
            return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TODO が見つかりません")


# 「パスの todo_id で探した TODO」を受け取る、という宣言に名前を付けたもの
TodoDep = Annotated[TodoRead, Depends(get_todo)]

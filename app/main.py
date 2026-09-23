from fastapi import FastAPI

from app.schemas.todo import TodoCreate

app = FastAPI()

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

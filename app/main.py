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

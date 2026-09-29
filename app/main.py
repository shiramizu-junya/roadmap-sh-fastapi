from fastapi import FastAPI

from app.routers import todos

app = FastAPI()


@app.get("/health", tags=["health"], summary="死活確認")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(todos.router)

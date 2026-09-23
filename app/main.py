from typing import Annotated

from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/items/{item_id}")
def read_item(
    item_id: int,
    q: Annotated[str | None, Query(max_length=20)] = None,
) -> dict[str, int | str | None]:
    return {"item_id": item_id, "q": q}

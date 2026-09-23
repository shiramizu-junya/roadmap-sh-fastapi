from typing import Annotated

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    done: bool = False

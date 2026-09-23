from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Annotated[str, Field(min_length=1, max_length=200)]
    done: bool = False


class TodoRead(BaseModel):
    id: int
    title: str
    done: bool

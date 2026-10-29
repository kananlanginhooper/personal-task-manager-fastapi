"""Shared bits for request and response models: camelCase JSON, UTC timestamps written with a trailing Z."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer
from pydantic.alias_generators import to_camel

# The database stores naive UTC; the API has always sent it as ISO 8601 with a trailing Z.
UtcDatetime = Annotated[datetime, PlainSerializer(lambda v: v.isoformat() + "Z", return_type=str)]


class CamelModel(BaseModel):
    """snake_case in Python, camelCase on the wire; builds from ORM rows."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class DoneIn(CamelModel):
    done: bool


class ReasonIn(CamelModel):
    reason: str | None = None

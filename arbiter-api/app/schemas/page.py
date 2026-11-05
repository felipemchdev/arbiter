from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """One page of a list endpoint, with the total row count for pagination."""

    items: list[T]
    total: int
    limit: int
    offset: int

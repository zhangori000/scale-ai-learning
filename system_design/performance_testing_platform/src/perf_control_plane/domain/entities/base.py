from __future__ import annotations

from typing import Any, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict

T = TypeVar("T", bound="BaseModel")


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )

    @classmethod
    def from_model(cls: type[T], value: Any) -> T:
        return cls.model_validate(value)

    def to_dict(self, *, exclude_none: bool = False) -> dict[str, Any]:
        return self.model_dump(exclude_none=exclude_none)

from typing import Annotated

from pydantic import Field
from typing_extensions import TypeAlias

__all__ = (
    "OptionalStr",
    "OptionalInt",
    "OptionalBool",
)

OptionalStr: TypeAlias = Annotated[str | None, Field(default=None)]
"""Type alias for optional string fields with default None value."""
OptionalInt: TypeAlias = Annotated[int | None, Field(default=None)]
"""Type alias for optional integer fields with default None value."""
OptionalBool: TypeAlias = Annotated[bool | None, Field(default=None)]
"""Type alias for optional boolean fields with default None value."""

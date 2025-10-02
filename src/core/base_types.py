from typing import Annotated

from pydantic import Field
from typing_extensions import TypeAlias

OptionalStr: TypeAlias = Annotated[str | None, Field(default=None)]
OptionalInt: TypeAlias = Annotated[int | None, Field(default=None)]
OptionalBool: TypeAlias = Annotated[bool | None, Field(default=None)]

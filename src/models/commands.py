from pydantic import BaseModel
from typing import Literal, Union, Annotated
from pydantic import Field, TypeAdapter


class StartProbeCommand(BaseModel):
    type: Literal["start_probe"]


class StopProbeCommand(BaseModel):
    type: Literal["stop_probe"]


Command = Annotated[
    Union[StartProbeCommand, StopProbeCommand], Field(discriminator="type")
]

command_adapter = TypeAdapter(Command)

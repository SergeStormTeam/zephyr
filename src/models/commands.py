from pydantic import BaseModel
from typing import Literal, Union, Annotated
from pydantic import Field, TypeAdapter


class StartProbeCommand(BaseModel):
    type: Literal["start_probe"]


class StopProbeCommand(BaseModel):
    type: Literal["stop_probe"]


class SetProbeMode(BaseModel):
    type: Literal["probe_mode"]
    mode: Literal["test", "drive", "field"]


Command = Annotated[
    Union[StartProbeCommand, StopProbeCommand, SetProbeMode],
    Field(discriminator="type"),
]

command_adapter: TypeAdapter = TypeAdapter(Command)

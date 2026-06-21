from abc import ABC, abstractmethod
from app.context import AppContext


class BaseSensor(ABC):
    def __init__(self, ctx: AppContext):
        self.sensor_name = ""
        self.ctx: AppContext = ctx
        self.active: bool = False

    def start(self):
        self._connect()
        self.active = True

    def stop(self):
        self._disconnect()
        self.active = False

    @abstractmethod
    def _connect(self) -> None:
        pass

    @abstractmethod
    def _disconnect(self) -> None:
        pass

    @abstractmethod
    def update(self) -> Exception | None:
        pass

    @abstractmethod
    def read(self) -> dict[str, float]:
        pass

    def is_active(self) -> bool:
        return self.active

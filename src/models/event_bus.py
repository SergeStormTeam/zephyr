from queue import Queue
# from enum import Enum

# class Event(Enum):
#     PROBE_READING = "probe_reading"
#     SESSION_UPDATE = "session_update"
#     SENSOR_STATUS_UPDATE =
#     DASHBOARD_NOTIFICATION = "dashboard_notification"


class EventBus:
    """
    Custom Pub/Sub implementation

    Attributes:
        event_loop (asyncio.AbstractEventLoop): The running asyncio loop to be used throughout the application

        server_connected (bool): Is the backup server connected?
        server_update: (asyncio.Event): Event that fires whenever a reading is taken for the server to update

        laptop_connected (bool): Is the local laptop connected?
        server_update: (asyncio.Event): Event that fires whenever a reading is taken for the laptop to update

        latest_reading (ProbeData): The most recent reading from the probe, None if none has been taken yet
        thread_shutdown (threading.Event): The multi-thread event that fires to start shutting down the application gracefully

    Methods:

    """

    def __init__(self) -> None:
        self.subscribers: dict[str, list[Queue]] = {}

    def subscribe(self, event: str):
        queue: Queue = Queue()
        self.subscribers.setdefault(event, []).append(queue)
        return queue

    def publish(self, event: str, data):
        for subscriber in self.subscribers.get(event, []):
            subscriber.put(data)

    def unsubscribe(self, event: str, queue: Queue):
        if event not in self.subscribers:
            return

        try:
            self.subscribers[event].remove(queue)
        except ValueError:
            pass

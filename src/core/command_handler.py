from fastapi import WebSocket, WebSocketDisconnect
from app.context import CurrentContext as ctx
from queue import Empty

from services import sensor_reader
import asyncio
import logging

logger: logging.Logger = logging.getLogger(__name__)

async def manage_connection(websocket: WebSocket) -> None:

    probe_data_update = ctx.event_bus.subscribe("probe_data_update")
    sensor_update = ctx.event_bus.subscribe("sensor_status_update")

    try:
        if ctx.latest_reading:
            await websocket.send_json(
                data={
                    "type": "init",
                    "sensors": sensor_reader.get_sensor_status(ctx),
                    "probe_data": ctx.latest_reading.json_data(),
                }
            )
        else:
            await websocket.send_json(
                data={
                    "type": "init",
                    "sensors": sensor_reader.get_sensor_status(ctx),
                }
            )

        while not ctx.thread_shutdown.is_set():
            try:
                new_data: dict[str, float] = probe_data_update.get_nowait()
                await websocket.send_json(data={"type": "probe_data", "data": new_data})
            except Empty:
                pass

            try:
                new_sensor_status: dict[str, float] = sensor_update.get_nowait()
                await websocket.send_json(
                    data={"type": "sensor_update", "data": new_sensor_status}
                )
            except Empty:
                pass
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"Failed to continue websocket connection! {e}")
    finally:
        ctx.event_bus.unsubscribe("probe_data_update", probe_data_update)
        ctx.event_bus.unsubscribe("sensor_status_update", sensor_update)

    return

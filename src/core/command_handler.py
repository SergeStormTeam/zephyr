from fastapi import WebSocket, WebSocketDisconnect
from app.context import CurrentContext as ctx
from queue import Empty

from services import sensor_reader
import asyncio
import logging
from models import commands
from core import lifecycle

logger: logging.Logger = logging.getLogger(__name__)


async def receive_commands(websocket: WebSocket) -> None:
    try:
        while True:
            new_data = await websocket.receive_json()
            try:
                command = commands.command_adapter.validate_python(new_data)
            except Exception as e:
                logger.warning(f"Invalid command received: {e}")
                await websocket.send_json({"type": "command_error", "detail": str(e)})
                continue

            match command:
                case commands.StartProbeCommand():
                    valid: bool = lifecycle.start_session(ctx)
                    if valid:
                        await websocket.send_json(
                            {"type": "start_probe", "id": ctx.session_id}
                        )
                        continue

                    await websocket.send_json({"type": "start_probe_error"})
                    continue
                case commands.StopProbeCommand():
                    valid: bool = lifecycle.stop_session(ctx)
                    if valid:
                        await websocket.send_json({"type": "stop_probe"})
                        continue

                    await websocket.send_json({"type": "stop_probe_error"})
                    continue

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"Failed to continue websocket connection! {e}")


async def send_data(websocket: WebSocket) -> None:

    probe_data_update = ctx.event_bus.subscribe("probe_data_update")
    sensor_update = ctx.event_bus.subscribe("sensor_status_update")

    try:
        await websocket.send_json(
            data={"type": "session_state", "state": ctx.session_active}
        )

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

        while True:
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


async def hook_websocket(websocket: WebSocket) -> None:
    await asyncio.gather(send_data(websocket), receive_commands(websocket))

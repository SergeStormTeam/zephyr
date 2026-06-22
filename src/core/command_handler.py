from fastapi import WebSocket, WebSocketDisconnect
from app.context import CurrentContext as ctx
from queue import Empty

import asyncio
import logging
from models import commands
from core import lifecycle

logger: logging.Logger = logging.getLogger(__name__)


async def handle_command(websocket: WebSocket, command):
    match command:
        case commands.StartProbeCommand():
            await websocket.send_json(
                {
                    "type": "notification",
                    "data": {"text": "Attempting to start a probe session"},
                }
            )

            valid: bool = lifecycle.start_session(ctx)
            if valid:
                await websocket.send_json(
                    {"type": "start_probe", "data": {"id": ctx.session_id}}
                )
                return

            await websocket.send_json(
                {
                    "type": "notification",
                    "data": {
                        "text": "Unable to start a new session!",
                        "desc": "Check if a session is already active!",
                    },
                }
            )
            return
        case commands.StopProbeCommand():
            await websocket.send_json(
                {
                    "type": "notification",
                    "data": {"text": "Attempting to end the current probe session!"},
                }
            )

            valid: bool = lifecycle.stop_session(ctx)
            if valid:
                await websocket.send_json({"type": "stop_probe"})
                return

            await websocket.send_json(
                {
                    "type": "notification",
                    "data": {
                        "text": "Unable to end the current session!",
                        "desc": "Check if there is no session active!",
                    },
                }
            )
            return

        case commands.SetProbeMode():
            ctx.probe_mode = command.mode
            await websocket.send_json(
                data={
                    "type": "notification",
                    "data": {"text": f"Updated Probe Mode to {ctx.probe_mode}!"},
                }
            )


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

            await handle_command(websocket, command)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"Failed to continue websocket connection! {e}")


async def send_data(websocket: WebSocket) -> None:

    notification_update = ctx.event_bus.subscribe("notification")
    session_update = ctx.event_bus.subscribe("session_update")
    probe_data_update = ctx.event_bus.subscribe("probe_data_update")
    sensor_update = ctx.event_bus.subscribe("sensor_status_update")

    try:
        await websocket.send_json(
            data={
                "type": "session_update",
                "data": {"session": ctx.session_active, "id": ctx.session_id},
            }
        )

        if ctx.latest_reading:
            await websocket.send_json(
                data={
                    "type": "probe_data",
                    "probe_data": ctx.latest_reading.json(get_timestamp=True),
                }
            )

        while True:
            try:
                new_state: dict[str, bool] = session_update.get_nowait()
                await websocket.send_json(
                    data={"type": "session_update", "data": new_state}
                )
            except Empty:
                pass

            try:
                new_noti: str = notification_update.get_nowait()
                await websocket.send_json(
                    data={"type": "notification", "data": new_noti}
                )
            except Empty:
                pass

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
        ctx.event_bus.unsubscribe("session_update", session_update)
        ctx.event_bus.unsubscribe("notification", notification_update)
    return


async def hook_websocket(websocket: WebSocket) -> None:
    await asyncio.gather(send_data(websocket), receive_commands(websocket))

from fastapi import WebSocket, WebSocketDisconnect
from app.context import CurrentContext as ctx
from queue import Empty


async def manage_connection(websocket: WebSocket) -> None:

    new_data = ctx.event_bus.subscribe("probe_data")

    try:
        while not ctx.thread_shutdown.is_set() and websocket:
            try:
                probe_data: dict[str, float] = new_data.get_nowait()
                await websocket.send_json(
                    data={"type": "probe_data", "data": probe_data}
                )
            except Empty:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        ctx.event_bus.unsubscribe("probe_data", new_data)

    return

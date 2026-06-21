import asyncio
import logging
import websockets
import json

from db import database
from app.config import (
    SERVER_API_KEY,
    SERVER_WS_URL,
    WEBSOCKET_RECONNECT_DEBOUNCE,
    LAPTOP_WS_URL,
)

from app.context import AppContext

from models.probe_data import ProbeData

logger: logging.Logger = logging.getLogger(__name__)


async def initalize_laptop_connection(ctx: AppContext):
    """
    Initialize the connection the websocket
    """

    if not SERVER_API_KEY:
        return

    if not LAPTOP_WS_URL:
        return

    headers: dict[str, str] = {
        "Authorization": f"Bearer {SERVER_API_KEY}",
    }

    while not ctx.thread_shutdown.is_set():
        try:
            async with websockets.connect(
                LAPTOP_WS_URL,
                ping_interval=20,
                ping_timeout=10,
                additional_headers=headers,
            ) as client:
                ctx.laptop_connected = True
                database.log_event("WEBSOCKET CONNECTED!", logging.INFO)

                while not ctx.thread_shutdown.is_set():
                    await ctx.laptop_update.wait()
                    ctx.laptop_update.clear()

                    reading: ProbeData | None = ctx.latest_reading
                    if not reading:
                        continue

                    data: dict[str, float | None] = {
                        "timestamp": reading.timestamp,
                        "temperature": reading.temperature,
                        "co2": reading.co2,
                        "humidity": reading.humidity,
                        "precipitation": reading.precipitation,
                        "pressure": reading.pressure,
                        "voc": reading.voc,
                        "wind_speed": reading.wind_speed,
                    }

                    await client.send(json.dumps(data))
        except Exception as e:
            if ctx.laptop_connected:
                logger.warning(f"LAPTOP WEBSOCKET DISCONNECTED! {e}")
                database.log_event(
                    f"LAPTOP WEBSOCKET DISCONNECTED! {e}", logging.WARNING
                )
        finally:
            ctx.laptop_connected = False

        if ctx.thread_shutdown.is_set():
            break

        await asyncio.sleep(WEBSOCKET_RECONNECT_DEBOUNCE)


async def initialize_server_connection(ctx: AppContext):
    """
    Initialize the connection the websocket
    """

    if not SERVER_API_KEY:
        return

    if not SERVER_WS_URL:
        return

    headers: dict[str, str] = {
        "Authorization": f"Bearer {SERVER_API_KEY}",
    }

    while not ctx.thread_shutdown.is_set():
        try:
            async with websockets.connect(
                SERVER_WS_URL,
                ping_interval=20,
                ping_timeout=10,
                additional_headers=headers,
            ) as client:
                ctx.server_connected = True
                database.log_event("WEBSOCKET CONNECTED!", logging.INFO)

                while not ctx.thread_shutdown.is_set():
                    await ctx.server_update.wait()
                    ctx.server_update.clear()

                    reading: ProbeData | None = ctx.latest_reading
                    if not reading:
                        continue

                    data: dict[str, float | None] = {
                        "timestamp": reading.timestamp,
                        "temperature": reading.temperature,
                        "co2": reading.co2,
                        "humidity": reading.humidity,
                        "precipitation": reading.precipitation,
                        "pressure": reading.pressure,
                        "voc": reading.voc,
                        "wind_speed": reading.wind_speed,
                    }

                    await client.send(json.dumps(data))
        except Exception as e:
            if ctx.server_connected:
                logger.warning(f"SERVER WEBSOCKET DISCONNECTED! {e}")
                database.log_event(
                    f"SERVER WEBSOCKET DISCONNECTED! {e}", logging.WARNING
                )
        finally:
            ctx.server_connected = False

        if ctx.thread_shutdown.is_set():
            break

        await asyncio.sleep(WEBSOCKET_RECONNECT_DEBOUNCE)


async def main(ctx):

    await asyncio.gather(initialize_server_connection(ctx))


def run_websocket_loops(ctx: AppContext):
    asyncio.run(main(ctx))

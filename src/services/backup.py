import asyncio
import logging
import httpx
import sqlite3

from typing import Any
from db import database
from app.config import (
    SERVER_API_KEY,
    HTTP_URL,
    DATABASE_BACKUP_DEBOUNCE,
    BASE_DIR,
    DATABASE_FILENAME,
)
from app.context import AppContext

logger: logging.Logger = logging.getLogger(__name__)


async def backup_data(ctx: AppContext):
    """
    Attempts to connect to the server for data export
    """
    if SERVER_API_KEY in (None, ""):
        return

    if HTTP_URL in (None, ""):
        return

    headers: dict[str, str] = {
        "Authorization": f"Bearer {SERVER_API_KEY}",
        "Content-Type": "application/json",
    }

    db: sqlite3.Connection = sqlite3.connect(
        f"{BASE_DIR}/data/{DATABASE_FILENAME}", timeout=30.0
    )

    db.row_factory = sqlite3.Row
    cursor: sqlite3.Cursor = db.cursor()

    backup_complete: bool = False
    try:
        while (not ctx.thread_shutdown.is_set()) or (not backup_complete):
            async with httpx.AsyncClient(headers=headers) as client:
                event_rows: list[Any] = database.fetch_unsent_events(cursor)
                data_rows: list[Any] = database.fetch_unsent_data(cursor)

                if (not event_rows) and (not data_rows):
                    backup_complete = True
                    await asyncio.sleep(DATABASE_BACKUP_DEBOUNCE)
                    continue

                backup_complete = False
                event_rows_json = [dict(r) for r in event_rows]
                data_rows_json = [dict(r) for r in data_rows]

                try:
                    resp = await client.post(
                        HTTP_URL,
                        json={"events": event_rows_json, "data": data_rows_json},
                    )
                    resp.raise_for_status()

                    ack = resp.json()
                    database.update_sent_data(
                        cursor, [row["id"] for row in ack["data"]]
                    )
                    database.update_sent_events(
                        cursor, [row["id"] for row in ack["events"]]
                    )
                    db.commit()

                except Exception as e:
                    logger.exception("FAILED TO BACKUP")
                    database.log_event(f"FAILED TO BACKUP! {e}", logging.WARNING)
                    db.rollback()
                await asyncio.sleep(DATABASE_BACKUP_DEBOUNCE)
    except Exception as e:
        database.log_event(f"FAILED TO CONNECT FOR BACKUP! {e}", logging.WARNING)


def run_backup_loop(ctx: AppContext):
    asyncio.run(backup_data(ctx))

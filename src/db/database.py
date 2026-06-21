import sqlite3
import logging
import os
import queue

from app.config import (
    BASE_DIR,
    DATABASE_FILENAME,
    DATABASE_QUEUE_MAX_SIZE,
    DATABASE_UPLOAD_BATCH_SIZE,
)
from app.context import AppContext

from models.probe_data import ProbeData
from models.probe_event import ProbeEvent

from typing import Any

logger: logging.Logger = logging.getLogger(__name__)
database_queue: queue.Queue = queue.Queue(maxsize=DATABASE_QUEUE_MAX_SIZE)


def log_event(message: str, level: int) -> None:
    """
    Adds a log event into the queue to be written.

    Arguments:
        message (str): The message to be written to the database, ex: Sensor Failed!
        level (LogSeverity): The severity of the event, advised to use loggings. Levels
    """

    new_entry: ProbeEvent = ProbeEvent(message=message, severity=level)

    database_queue.put(new_entry)


def log_sensor_data(data_entry: ProbeData) -> None:
    """
    Adds a sensor data event into the queue to be written.

    Arguments:
        data_entry (ProbeData): The data entry to be written to the database
    """

    database_queue.put(data_entry)


def process_sensor_data(ctx: AppContext, cursor: sqlite3.Cursor, d: ProbeData) -> None:
    """
    Parses data from the sensor to be written to the porbe_data database.

    Arguments:
        cursor (sqlite3.Cursor): The SQLite cursor to use
        d (ProbeData): The data to be written to the database
    """
    cursor.execute(
        """
    INSERT INTO data (id, timestamp, session_id, sequence, temperature, humidity, pressure, voc, wind_speed, co2, precipitation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            d.record_id,
            d.timestamp,
            ctx.session_id,
            d.sequence,
            d.temperature,
            d.humidity,
            d.pressure,
            d.voc,
            d.wind_speed,
            d.co2,
            d.precipitation,
        ),
    )


def process_log_event(ctx: AppContext, cursor: sqlite3.Cursor, d: ProbeEvent) -> None:
    """
    Parses data from the sensor to be written to the events database.

    Arguments:
        cursor (sqlite3.Cursor): The SQLite cursor to use
        d (ProbeEvent): The data to be written to the database
    """
    cursor.execute(
        """
    INSERT INTO events (id, timestamp, session_id,  message, severity)
    VALUES (?, ?, ?, ?, ?)
    """,
        (d.record_id, d.timestamp, ctx.session_id, d.message, d.severity),
    )


def fetch_unsent_events(cursor: sqlite3.Cursor) -> list:
    """
    Grabs all of the unsent rows of events to be uploaded, maxing out at 100 rows

    Arguments:
        cursor (sqlite3.Cursor): The SQLite cursor to use

    Returns:
        list: The list of rows to be uploaded
    """

    cursor.execute(
        """
        SELECT id, timestamp, session_id, message, severity
        FROM events
        WHERE sent = 0
        LIMIT ?;
    """,
        (DATABASE_UPLOAD_BATCH_SIZE,),
    )

    rows: list[Any] = cursor.fetchall()

    return rows


def fetch_unsent_data(cursor: sqlite3.Cursor) -> list:
    """
    Grabs all of the unsent rows of probe data to be uploaded, maxing out at 100 rows

    Arguments:
        cursor (sqlite3.Cursor): The SQLite cursor to use

    Returns:
        list: The list of rows to be uploaded
    """

    cursor.execute(
        """
        SELECT id, timestamp, session_id, sequence,
            temperature, humidity, pressure, voc,
            wind_speed, co2, precipitation
            FROM data
            WHERE sent = 0
            LIMIT ?;
    """,
        (DATABASE_UPLOAD_BATCH_SIZE,),
    )

    rows: list[Any] = cursor.fetchall()

    return rows


def update_sent_events(
    cursor: sqlite3.Cursor, sent_rows: list[dict[str, str | int]]
) -> None:
    """
    Updates the rows of data from the server acknowledgment

    Arguments:
        cursor (sqlite3.Cursor): The SQLite cursor to use
        sent_rows (list[dict[str, str | int]]): The rows that were updated
    """
    cursor.execute(
        f"UPDATE events SET sent = 1 WHERE id IN ({','.join('?' * len(sent_rows))})",
        sent_rows,
    )

    return


def update_sent_data(
    cursor: sqlite3.Cursor, sent_rows: list[dict[str, str | int]]
) -> None:
    """
    Updates the rows of data from the server acknowledgment

    Arguments:
        cursor (sqlite3.Cursor): The SQLite cursor to use
        sent_rows (list[dict[str, str | int]]): The rows that were updated
    """
    cursor.execute(
        f"UPDATE data SET sent = 1 WHERE id IN ({','.join('?' * len(sent_rows))})",  # Ahh yes this works for some reason!
        sent_rows,
    )

    return


def create_new_connection() -> tuple[sqlite3.Connection, sqlite3.Cursor]:
    """
    Creates a new DB and Cursor connection to use

    Returns:
        sqlite3.Connection: The connection object (the database)
        sqlite3.Cursor: The cursor object (the cursor)
    """

    db: sqlite3.Connection = sqlite3.connect(
        f"{BASE_DIR}/data/{DATABASE_FILENAME}", timeout=30.0
    )
    cursor: sqlite3.Cursor = db.cursor()

    return db, cursor


def initialize_database() -> None:
    """
    Attempts to initalize the SQLite database, creating necessary tables if they do not exist
    """

    logger.info("Attempting to Load Database!")

    try:
        data_dir = f"{BASE_DIR}/data"
        os.makedirs(data_dir, exist_ok=True)

        db: sqlite3.Connection = sqlite3.connect(
            f"{BASE_DIR}/data/{DATABASE_FILENAME}", timeout=30.0
        )
        cursor: sqlite3.Cursor = db.cursor()

        cursor.execute("PRAGMA journal_mode=WAL")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,

                session_id TEXT NOT NULL,
                sequence INTEGER NOT NULL,


                temperature REAL,
                humidity REAL,
                pressure REAL,
                voc REAL,
                wind_speed REAL,
                co2 REAL,
                precipitation REAL,

                sent INTEGER DEFAULT 0,

                UNIQUE(session_id, sequence)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_unsent ON data (sent) WHERE sent = 0;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                timestamp REAL NOT NULL,

                session_id TEXT NOT NULL,

                message TEXT NOT NULL,
                severity INTEGER NOT NULL,

                sent INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_unsent ON events (sent) WHERE sent = 0;
        """)

        db.commit()
        db.close()
    except sqlite3.OperationalError as e:
        logger.critical("DB init failed (operational): %s", e)
        raise
    except sqlite3.DatabaseError as e:
        logger.critical("DB init failed (corrupt or invalid): %s", e)
        raise
    except RuntimeError as e:
        logger.critical("DB init failed: %s", e)
        raise

    logger.info("Successfully loaded the database!")


def update_database_loop(ctx: AppContext):
    """
    Running loop for the database writing thread
    """

    loop_database: sqlite3.Connection = sqlite3.connect(
        f"{BASE_DIR}/data/{DATABASE_FILENAME}", timeout=30.0
    )
    cursor: sqlite3.Cursor = loop_database.cursor()

    try:
        while True:
            try:
                new_entry: ProbeData | ProbeEvent = database_queue.get(timeout=1)
            except queue.Empty:
                if ctx.thread_shutdown.is_set():
                    logger.info("Shutdown detected and queue empty, exiting.")
                    break
                continue

            try:
                if isinstance(new_entry, ProbeEvent):
                    process_log_event(ctx, cursor, new_entry)
                elif isinstance(new_entry, ProbeData):
                    process_sensor_data(ctx, cursor, new_entry)
                else:
                    logger.warning(f"Unknown entry in the queue! {new_entry}")
            except Exception as e:
                logger.exception(
                    f"Failed to process entry, reverting! {new_entry} with error {e}"
                )
                loop_database.rollback()
            else:
                loop_database.commit()
    finally:
        loop_database.commit()
        loop_database.close()

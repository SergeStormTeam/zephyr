import logging
import sys

from fastapi import FastAPI
from core import lifecycle

from app.context import CurrentContext
from api import endpoints

from db import database
from services import sensor_reader

from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger: logging.Logger = logging.getLogger(__name__)


@asynccontextmanager
async def runtime(app: FastAPI):
    database.initialize_database()
    sensor_reader.initalize_sensors(ctx=CurrentContext)

    logger.info("Importing API endpoints!")
    app.include_router(endpoints.router, prefix="/api")

    logger.info("Finished setting up the application!")

    lifecycle.start_session(CurrentContext)

    yield

    lifecycle.stop_session(CurrentContext)


app: FastAPI = FastAPI(docs_url="/swag", lifespan=runtime)

app.include_router(endpoints.router, prefix="/api")

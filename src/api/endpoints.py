from fastapi import WebSocket, APIRouter
from core import command_handler

import logging

router: APIRouter = APIRouter()
logger: logging.Logger = logging.getLogger(__name__)


@router.websocket("/dashboard")
async def dashboard(websocket: WebSocket) -> None:
    """ """
    await websocket.accept()
    await command_handler.hook_websocket(websocket)

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlmodel import Session

from .db import get_session
from .security.auth import get_user_from_token

router = APIRouter()


@router.websocket("/ws/game")
async def websocket_endpoint(
    ws: WebSocket,
    room: str,
    token: str,
    session: Session = Depends(get_session),
) -> None:
    """Echo WebSocket endpoint that requires JWT auth and a room."""
    try:
        get_user_from_token(token, session)
    except ValueError:
        await ws.close(code=1008)
        return
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            await ws.send_text(data)
    except WebSocketDisconnect:
        pass

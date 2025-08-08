from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .ws import router as ws_router
from .api import users, auth
from .db import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(users.router)
app.include_router(auth.router)
app.include_router(ws_router)

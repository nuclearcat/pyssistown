from fastapi import FastAPI

from .ws import router as ws_router

app = FastAPI()

@app.get("/")
async def read_root() -> dict[str, str]:
    return {"status": "ok"}

app.include_router(ws_router)

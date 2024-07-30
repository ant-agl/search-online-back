from fastapi import FastAPI
from starlette.responses import RedirectResponse, JSONResponse

from app.settings import settings

app = FastAPI(
    **settings.app_config,
)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok"}, status_code=200)

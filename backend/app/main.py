"""FastAPI entry point. Run from the project root with the documented command."""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.api.routes import router
from backend.app.api.india import router as india_router
from backend.app.models.database import initialize


@asynccontextmanager
async def lifespan(app:FastAPI):
    initialize()
    yield


app=FastAPI(title="Emergency Relief DAA API",version="1.0.0",
    description="Academic decision-support prototype; local planning data with optional live Indian weather context.",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(router,prefix="/api")
app.include_router(india_router, prefix="/api")

dist=Path(__file__).resolve().parents[2]/"frontend"/"dist"
if dist.exists():
    app.mount("/",StaticFiles(directory=dist,html=True),name="web")

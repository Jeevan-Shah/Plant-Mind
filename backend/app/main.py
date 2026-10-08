"""PlantMind FastAPI application entry point.

Run:  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import routes_analyses, routes_chat, routes_knowledge, routes_meta, routes_plants
from .config import UPLOAD_DIR
from .database import Base, SessionLocal, engine
from . import models  # noqa: F401  (register models on the Base metadata)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables and seed the demo knowledge base + demo plants if empty.
    Base.metadata.create_all(engine)
    from backend.seed import seed_all
    with SessionLocal() as session:
        seed_all(session)
    yield


app = FastAPI(
    title='PlantMind API',
    version='1.0.0',
    description='Explainable AI plant-care system: Knowledge Graph + GraphRAG '
                '+ Computer Vision + LLM/fallback reasoning.',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    # The Android app's WebView origin is https://localhost and, in the browser
    # dev setup, http://localhost:5173 — allow any origin. This is a LAN demo
    # app and uses no cookies, so credentials are not needed.
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(routes_plants.router)
app.include_router(routes_analyses.router)
app.include_router(routes_chat.router)
app.include_router(routes_knowledge.router)
app.include_router(routes_meta.router)

app.mount('/uploads', StaticFiles(directory=str(UPLOAD_DIR)), name='uploads')


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception):
    return JSONResponse(status_code=500, content={'detail': f'Internal error: {exc}'})


@app.get('/')
def root():
    return {
        'name': 'PlantMind API',
        'version': '1.0.0',
        'docs': '/docs',
        'health': '/api/health',
    }

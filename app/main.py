"""
VoiCal FastAPI application — provides REST API and database initialization.

NOTE: The primary server entry point is server.py (Flask + SocketIO).
This module is imported by server.py to initialize the database at startup.
Do NOT run this file directly as a standalone server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}

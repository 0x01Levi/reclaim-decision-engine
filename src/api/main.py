from fastapi import FastAPI
from typing import Dict, Any

from ..config import load_config


config = load_config()

app = FastAPI(
    title="RECLAIM - Intelligent Revenue Recovery",
    description="AI-assisted revenue-recovery decision system for merchants",
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "version": "0.1.0",
        "environment": config.environment,
    }


@app.get("/")
async def root() -> Dict[str, Any]:
    return {
        "name": "RECLAIM",
        "description": "Intelligent Revenue Recovery System",
        "version": "0.1.0",
        "docs": "/docs",
    }
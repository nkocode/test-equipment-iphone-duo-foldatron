"""Headless Pi 3B entry point; bind locally unless explicitly configured."""

import os

import uvicorn

from .api import create_app

uvicorn.run(
    create_app(),
    host=os.getenv("FOLDATRON_C_BIND", "127.0.0.1"),
    port=int(os.getenv("FOLDATRON_C_PORT", "8001")),
    workers=1,
)

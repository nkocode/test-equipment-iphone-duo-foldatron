"""Run locally by default; LAN TLS settings are installation choices."""

import os

import uvicorn

from .api import create_app

if __name__ == "__main__":
    uvicorn.run(
        create_app(),
        host=os.getenv("FOLDBENCH_HOST", "127.0.0.1"),
        port=int(os.getenv("FOLDBENCH_HTTP_PORT", "8000")),
        workers=1,
        ssl_certfile=os.getenv("FOLDBENCH_TLS_CERT"),
        ssl_keyfile=os.getenv("FOLDBENCH_TLS_KEY"),
    )

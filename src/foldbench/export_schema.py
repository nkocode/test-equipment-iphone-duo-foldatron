"""Export exactly the schema served by the FastAPI application."""

import json
from pathlib import Path

from .api import create_app
from .revc.export_schema import main as revc_schema
from .settings import Settings

if __name__ == "__main__":
    revc_schema()
    schema = create_app(Settings()).openapi()
    Path("openapi.json").write_text(json.dumps(schema, indent=2) + "\n")

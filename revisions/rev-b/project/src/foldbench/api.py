"""Authenticated REST interface and machine-generated OpenAPI contract."""

import csv
import io
import secrets
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.security import APIKeyHeader

from .controller import Conflict, Controller
from .models import (
    Action,
    Calibration,
    Error,
    Event,
    Inspection,
    Jog,
    Recipe,
    Run,
    Sample,
    Status,
    Telemetry,
)
from .settings import Settings


def create_app(settings=None, driver=None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        if len(settings.api_key) < 32 or settings.api_key.startswith(
            "REPLACE"
        ):
            raise RuntimeError("FOLDBENCH_API_KEY must contain 32+ characters")
        controller = Controller(settings, driver)
        app.state.controller = controller
        try:
            yield
        finally:
            controller.close()

    app = FastAPI(
        title="FoldBench iPhone Duo Endurance Tester",
        version="1.0.0",
        description=(
            "Single-station Pi controller. Simulation is the default. "
            "Angles are calibrated motor-derived estimates; endpoints have "
            "independent switches. API stop is not a physical emergency stop. "
            "All /v1 operations require X-API-Key. Run one process/worker."
        ),
        lifespan=lifespan,
        responses={
            401: {"model": Error, "description": "Missing or invalid API key"},
            409: {"model": Error, "description": "State or safety conflict"},
            404: {"model": Error, "description": "Run not found"},
            503: {"model": Error, "description": "Telemetry unavailable"},
        },
    )
    scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

    def authorize(key: Annotated[str | None, Depends(scheme)]):
        if not key or not secrets.compare_digest(key, settings.api_key):
            raise HTTPException(401, "Missing or invalid API key")

    auth = [Depends(authorize)]

    def controller():
        return app.state.controller

    def call(name, *args):
        try:
            return controller().call(name, *args)
        except Conflict as exc:
            raise HTTPException(409, str(exc)) from exc

    def get_run(run_id):
        ctl = controller()
        with ctl.lock:
            if ctl.run and ctl.run.id == run_id:
                return ctl.run.model_copy(deep=True)
            found = ctl.store.get(run_id)
        if not found:
            raise HTTPException(404, "Run not found")
        return found

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """HTTP liveness only; use /v1/status for readiness and faults."""
        return {"service": "foldbench", "status": "alive"}

    @app.get("/v1/status", dependencies=auth, tags=["system"])
    def status() -> Status:
        return controller().snapshot()

    @app.get("/v1/calibration", dependencies=auth, tags=["system"])
    def calibration() -> Calibration:
        """Read local installation limits; remote widening is not supported."""
        return settings.calibration

    @app.get("/v1/telemetry", dependencies=auth, tags=["system"])
    def telemetry() -> Telemetry:
        sample = controller().snapshot().telemetry
        if sample is None:
            raise HTTPException(503, "No valid telemetry; inspect status")
        return sample

    @app.post("/v1/stop", dependencies=auth, status_code=202, tags=["control"])
    def stop_all() -> Action:
        """Request latched protective stop, including jogs; poll status.

        This acknowledgement is NOT proof of stopped motion. Use the physical
        emergency stop for immediate independent removal of actuator power.
        """
        controller().emergency_stop()
        return Action(detail="Protective stop requested; poll /v1/status")

    @app.post("/v1/reset", dependencies=auth, tags=["control"])
    def reset() -> Action:
        """Clear a resolved fault without enabling torque or resuming."""
        return call("reset")

    @app.post("/v1/jogs", dependencies=auth, status_code=202, tags=["control"])
    def jog(body: Jog) -> Action:
        """Move to one commissioned endpoint at 5 deg/s; idle state only."""
        return call("jog", body.target)

    @app.post("/v1/runs", dependencies=auth, status_code=201, tags=["runs"])
    def start_run(
        body: Recipe,
        idempotency_key: Annotated[
            str, Header(min_length=8, max_length=128, pattern=r"^[\w.-]+$")
        ],
    ) -> Run:
        """Start one run. Reusing the same key/body returns the same run."""
        return call("start", body, idempotency_key)

    @app.get("/v1/runs", dependencies=auth, tags=["runs"])
    def list_runs(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[Run]:
        with controller().lock:
            return controller().store.runs(limit, offset)

    @app.get("/v1/runs/{run_id}", dependencies=auth, tags=["runs"])
    def read_run(run_id: str) -> Run:
        return get_run(run_id)

    @app.post("/v1/runs/{run_id}/pause", dependencies=auth, tags=["runs"])
    def pause_run(run_id: str) -> Action:
        """Pause at the next verified full cycle, leaving the phone open."""
        get_run(run_id)
        return call("pause", run_id)

    @app.post("/v1/runs/{run_id}/resume", dependencies=auth, tags=["runs"])
    def resume_run(run_id: str) -> Run:
        get_run(run_id)
        return call("resume", run_id)

    @app.post("/v1/runs/{run_id}/stop", dependencies=auth, tags=["runs"])
    def stop_run(run_id: str) -> Run:
        """Disable torque and end this run. A partial cycle is not counted."""
        get_run(run_id)
        return call("stop", run_id)

    @app.post(
        "/v1/runs/{run_id}/inspections", dependencies=auth, tags=["runs"]
    )
    def inspect_run(run_id: str, body: Inspection) -> Run:
        """Record human display/touch/fixture inspection while paused."""
        get_run(run_id)
        return call("inspect", run_id, body)

    @app.get("/v1/runs/{run_id}/samples", dependencies=auth, tags=["results"])
    def samples(
        run_id: str,
        after: int = Query(0, ge=0),
        limit: int = Query(1000, ge=1, le=10_000),
    ) -> list[Sample]:
        """1 Hz plus endpoint samples; continue with last seq as after."""
        get_run(run_id)
        with controller().lock:
            return controller().store.samples(run_id, after, limit)

    @app.get("/v1/runs/{run_id}/events", dependencies=auth, tags=["results"])
    def events(
        run_id: str,
        after: int = Query(0, ge=0),
        limit: int = Query(1000, ge=1, le=10_000),
    ) -> list[Event]:
        get_run(run_id)
        with controller().lock:
            return controller().store.events(run_id, after, limit)

    @app.get(
        "/v1/runs/{run_id}/samples.csv",
        dependencies=auth,
        tags=["results"],
        response_class=Response,
        responses={
            200: {
                "content": {"text/csv": {"schema": {"type": "string"}}},
                "description": "One page of samples; X-Next-After cursor",
            }
        },
    )
    def export_csv(
        run_id: str,
        after: int = Query(0, ge=0),
        limit: int = Query(1000, ge=1, le=10_000),
    ):
        rows = samples(run_id, after, limit)
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer, fieldnames=["seq", *Telemetry.model_fields]
        )
        writer.writeheader()
        writer.writerows(rows)
        cursor = rows[-1]["seq"] if rows else after
        return Response(
            buffer.getvalue(),
            media_type="text/csv",
            headers={"X-Next-After": str(cursor)},
        )

    return app

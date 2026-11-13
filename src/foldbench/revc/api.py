"""Authenticated Rev C REST API; hardware is owned by a single worker."""

import csv
import io
import secrets
from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from fastapi.security import APIKeyHeader

from .controller import Conflict, Controller
from .models import (
    Action,
    Commissioning,
    Inspection,
    Jog,
    Recipe,
    Run,
    Settings,
    SimulationFault,
    Status,
    Telemetry,
)


def create_app(settings=None, driver=None):
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app):
        if len(settings.api_key) < 32 or settings.api_key.startswith(
            "REPLACE"
        ):
            raise RuntimeError("FOLDATRON_C_API_KEY requires 32+ characters")
        controller = Controller(settings, driver)
        app.state.controller = controller
        try:
            yield
        finally:
            controller.close()

    app = FastAPI(
        title="foldatron Rev C",
        version="0.3.0",
        description=(
            "Catalog-component folding bench. Simulation is default. "
            "Use one worker. Hardware requires a local commissioning record. "
            "Opening is an endpoint-calibrated motor estimate, not direct "
            "phone-angle or torque measurement. API stop is not the physical "
            "E-stop. Vacuum release and safety reset are physical operations."
        ),
        lifespan=lifespan,
    )
    scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

    def authorize(key: Annotated[str | None, Depends(scheme)]):
        if not key or not secrets.compare_digest(key, settings.api_key):
            raise HTTPException(401, "Missing or invalid API key")

    auth = [Depends(authorize)]

    def controller():
        return app.state.controller

    def call(method, *args):
        ctl = controller()
        with ctl.lock:
            try:
                return getattr(ctl, method)(*args)
            except Conflict as exc:
                raise HTTPException(409, str(exc)) from exc
            except Exception as exc:
                ctl.trip(f"Control operation failed: {exc}")
                raise HTTPException(503, str(exc)) from exc

    def get_run(run_id):
        ctl = controller()
        with ctl.lock:
            found = ctl.store.get(run_id)
        if found is None:
            raise HTTPException(404, "Run not found")
        return found

    @app.get("/health", tags=["system"])
    def health() -> dict[str, str]:
        """HTTP liveness only; does not indicate equipment readiness."""
        return {"service": "foldatron", "revision": "C", "status": "alive"}

    @app.get("/v1/status", dependencies=auth, tags=["system"])
    def status() -> Status:
        return controller().snapshot()

    @app.get("/v1/commissioning", dependencies=auth, tags=["system"])
    def commissioning() -> Commissioning:
        """Read local limits; no network route can release or widen them."""
        return settings.calibration

    @app.get("/v1/telemetry", dependencies=auth, tags=["system"])
    def telemetry() -> Telemetry:
        snapshot = controller().snapshot()
        if snapshot.telemetry is None or snapshot.telemetry_age_s > 0.5:
            raise HTTPException(503, "Fresh telemetry unavailable")
        return snapshot.telemetry

    @app.post("/v1/stop", dependencies=auth, status_code=202, tags=["control"])
    def stop() -> Action:
        """Latch a stop request without waiting for the hardware lock.

        Poll status to confirm. Physical E-stop independently removes power.
        Vacuum is retained; the API does not vent the cups.
        """
        controller().stop_requested.set()
        return Action(detail="Stop requested; poll status for confirmation")

    @app.post("/v1/reset", dependencies=auth, tags=["control"])
    def reset() -> Action:
        """Verify resolved conditions, clear software fault, never resume."""
        call("reset")
        return Action(detail="Software fault reset; no motion commanded")

    @app.post("/v1/jogs", dependencies=auth, status_code=202, tags=["control"])
    def jog(body: Jog) -> Action:
        call("jog", body)
        return Action(detail="Bounded jog requested")

    @app.post("/v1/runs", dependencies=auth, status_code=201, tags=["runs"])
    def start(
        body: Recipe,
        idempotency_key: Annotated[
            str, Header(min_length=8, max_length=128, pattern=r"^[\w.-]+$")
        ],
    ) -> Run:
        return call("start", body, idempotency_key)

    @app.get("/v1/runs", dependencies=auth, tags=["runs"])
    def runs(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[Run]:
        ctl = controller()
        with ctl.lock:
            return ctl.store.runs(limit, offset)

    @app.get("/v1/runs/{run_id}", dependencies=auth, tags=["runs"])
    def run(run_id: str) -> Run:
        return get_run(run_id)

    @app.post("/v1/runs/{run_id}/{action}", dependencies=auth, tags=["runs"])
    def run_action(
        run_id: str, action: Literal["pause", "resume", "stop"]
    ) -> Run:
        """Pause at the next open endpoint after a full cycle.

        Stop ends the run immediately without counting a partial cycle.
        Resume is valid only for a healthy paused run at the open endpoint.
        """
        get_run(run_id)
        return call("run_action", run_id, action)

    @app.post(
        "/v1/runs/{run_id}/inspections/record",
        dependencies=auth,
        tags=["results"],
    )
    def inspection(run_id: str, body: Inspection) -> Action:
        ctl = controller()
        with ctl.lock:
            record = get_run(run_id)
            if record.state == "running":
                raise HTTPException(409, "Pause or stop before inspection")
            ctl.store.record(run_id, "inspection", body.model_dump())
            if not body.passed and ctl.run and ctl.run.id == run_id:
                ctl.trip("Human inspection failed")
        return Action(detail="Inspection recorded")

    @app.get(
        "/v1/runs/{run_id}/records/{kind}",
        dependencies=auth,
        tags=["results"],
    )
    def records(
        run_id: str,
        kind: Literal["sample", "event", "inspection"],
        after: int = Query(0, ge=0),
        limit: int = Query(1000, ge=1, le=10000),
    ) -> list[dict]:
        get_run(run_id)
        ctl = controller()
        with ctl.lock:
            return ctl.store.records(run_id, kind, after, limit)

    @app.get(
        "/v1/runs/{run_id}/samples.csv",
        dependencies=auth,
        tags=["results"],
        response_class=Response,
        responses={200: {"content": {"text/csv": {}}}},
    )
    def csv_export(
        run_id: str,
        after: int = Query(0, ge=0),
        limit: int = Query(1000, ge=1, le=10000),
    ):
        rows = records(run_id, "sample", after, limit)
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "seq",
                "recorded_at",
                *Telemetry.model_fields,
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
        cursor = rows[-1]["seq"] if rows else after
        return Response(
            buffer.getvalue(),
            media_type="text/csv",
            headers={
                "X-Next-After": str(cursor),
            },
        )

    if settings.mode == "simulation":

        @app.post(
            "/v1/simulation/fault", dependencies=auth, tags=["simulation"]
        )
        def inject(body: SimulationFault) -> Action:
            """Only registered in simulation mode; cannot alter live inputs."""
            ctl = controller()
            with ctl.lock:
                ctl.driver.fault = body.fault
            return Action(detail=f"Simulation fault set to {body.fault}")

    return app

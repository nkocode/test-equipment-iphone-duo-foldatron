"""Real FastAPI lifespan and HTTP contract checks for Rev C."""

import time

from fastapi.testclient import TestClient

from foldbench.revc.api import create_app
from foldbench.revc.models import Settings

KEY = "test-only-key-0123456789-0123456789"


def test_api_auth_idempotency_and_simulation_fault(tmp_path):
    app = create_app(Settings(api_key=KEY, data_dir=tmp_path, tick_s=0.01))
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/v1/status").status_code == 401
        headers = {"X-API-Key": KEY, "Idempotency-Key": "api-test-key"}
        for _ in range(100):
            state = client.get("/v1/status", headers=headers).json()
            if state["telemetry"]:
                break
            time.sleep(0.01)
        body = {"sample_id": "API surrogate"}
        first = client.post("/v1/runs", json=body, headers=headers)
        assert first.status_code == 201
        duplicate = client.post("/v1/runs", json=body, headers=headers)
        assert duplicate.json()["id"] == first.json()["id"]
        injected = client.post(
            "/v1/simulation/fault", json={"fault": "vacuum"}, headers=headers
        )
        assert injected.status_code == 200
        for _ in range(100):
            state = client.get("/v1/status", headers=headers).json()
            if state["state"] == "faulted":
                break
            time.sleep(0.01)
        assert state["state"] == "faulted"
        assert state["run"]["completed_cycles"] == 0
        run_id = first.json()["id"]
        csv = client.get(f"/v1/runs/{run_id}/samples.csv", headers=headers)
        assert csv.status_code == 200
        assert "X-Next-After" in csv.headers


def test_hardware_schema_has_no_fault_injection_route():
    schema = create_app(Settings(mode="hardware")).openapi()
    assert "/v1/simulation/fault" not in schema["paths"]
    assert "/v1/reset" in schema["paths"]
    assert "APIKeyHeader" in schema["components"]["securitySchemes"]

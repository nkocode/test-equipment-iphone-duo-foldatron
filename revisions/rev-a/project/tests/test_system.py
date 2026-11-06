"""Observable behavior, durable counting, fault paths, and API contracts."""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from foldbench.api import create_app
from foldbench.controller import Conflict, Controller
from foldbench.hardware import HardwareFault, Simulator, read_probe
from foldbench.models import Calibration, Recipe
from foldbench.settings import Settings

KEY = "test-credential-" * 4
HEADERS = {"X-API-Key": KEY}


def wait_for(predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        time.sleep(0.01)
    raise AssertionError("Expected state did not arrive")


@pytest.fixture
def setup(tmp_path):
    settings = Settings(
        data_dir=tmp_path, api_key=KEY, simulation_speed=2000, tick_s=0.01
    )
    driver = Simulator(settings)
    app = create_app(settings, driver)
    with TestClient(app) as client:
        wait_for(lambda: app.state.controller.snapshot().telemetry)
        client.headers.update(HEADERS)
        yield client, app.state.controller, driver


def start(client, key="unique-test-key", **changes):
    body = {"specimen": "Duo-test", "cycles": 1, "dwell_s": 0.25}
    body.update(changes)
    response = client.post(
        "/v1/runs", json=body, headers={"Idempotency-Key": key}
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_auth_validation_and_schema(setup):
    client, _, _ = setup
    assert client.get("/health").status_code == 200
    assert (
        client.get("/v1/status", headers={"X-API-Key": "wrong"}).status_code
        == 401
    )
    invalid = client.post(
        "/v1/runs",
        json={"specimen": "x", "cycles": -1},
        headers={"Idempotency-Key": "valid-key"},
    )
    assert invalid.status_code == 422
    assert client.post("/v1/runs", json={"specimen": "x"}).status_code == 422
    spec = client.get("/openapi.json").json()
    assert spec["openapi"].startswith("3.1")
    assert spec["components"]["securitySchemes"]["APIKeyHeader"]["name"] == (
        "X-API-Key"
    )
    for path, methods in spec["paths"].items():
        if path.startswith("/v1/"):
            for operation in methods.values():
                assert operation["security"] == [{"APIKeyHeader": []}]


def test_complete_count_samples_and_csv(setup):
    client, ctl, _ = setup
    run_id = start(client, cycles=2)
    wait_for(lambda: ctl.snapshot().active_run.state == "completed")
    run = client.get(f"/v1/runs/{run_id}").json()
    assert run["completed_cycles"] == 2
    assert run["mode"] == "simulation"
    rows = client.get(f"/v1/runs/{run_id}/samples?limit=1").json()
    assert len(rows) == 1
    csv = client.get(f"/v1/runs/{run_id}/samples.csv?limit=1")
    assert csv.status_code == 200
    assert csv.headers["x-next-after"] == str(rows[0]["seq"])
    assert "simulation" in csv.text
    later = client.get(
        f"/v1/runs/{run_id}/samples?after={rows[0]['seq']}"
    ).json()
    assert all(row["seq"] > rows[0]["seq"] for row in later)


def test_idempotency_and_one_owner(setup):
    client, _, _ = setup
    run_id = start(client, cycles=100)
    assert start(client, cycles=100) == run_id
    response = client.post(
        "/v1/runs",
        json={"specimen": "different"},
        headers={"Idempotency-Key": "unique-test-key"},
    )
    assert response.status_code == 409
    response = client.post(
        "/v1/runs",
        json={"specimen": "other"},
        headers={"Idempotency-Key": "different-key"},
    )
    assert response.status_code == 409


def test_concurrent_starts_have_exactly_one_winner(setup):
    _, ctl, _ = setup
    recipe = Recipe(specimen="concurrency", cycles=100)

    def attempt(number):
        try:
            return ctl.call("start", recipe, f"concurrent-{number}").id
        except Conflict:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(attempt, range(4)))
    assert len([result for result in results if result]) == 1


def test_protective_stop_latches_and_never_counts_partial(setup):
    client, ctl, driver = setup
    driver.jammed = True
    run_id = start(client, cycles=10)
    response = client.post("/v1/stop")
    assert response.status_code == 202
    wait_for(lambda: ctl.snapshot().state == "faulted")
    assert not driver.enabled
    assert client.get(f"/v1/runs/{run_id}").json()["completed_cycles"] == 0
    assert (
        client.post("/v1/jogs", json={"target": "closed"}).status_code == 409
    )
    assert client.post("/v1/reset").status_code == 200
    assert not driver.enabled


@pytest.mark.parametrize("fault", ["permit", "temperature", "overcurrent"])
def test_faults_disable_motion(setup, fault):
    client, ctl, driver = setup
    start(client, cycles=100)
    if fault == "permit":
        driver.permit = False
    elif fault == "temperature":
        driver.case_c = 50
    else:
        driver.current_ma = 400
    wait_for(lambda: ctl.snapshot().state == "faulted")
    assert not driver.enabled
    assert client.post("/v1/reset").status_code == 409


def test_inspection_gate_and_resume(setup):
    client, ctl, _ = setup
    run_id = start(client, cycles=2, inspection_every=1)
    wait_for(lambda: ctl.snapshot().state == "paused")
    assert ctl.snapshot().active_run.completed_cycles == 1
    assert client.post(f"/v1/runs/{run_id}/resume").status_code == 409
    response = client.post(
        f"/v1/runs/{run_id}/inspections",
        json={"result": "pass", "notes": "Screen and fixture checked"},
    )
    assert response.status_code == 200
    assert client.post(f"/v1/runs/{run_id}/resume").status_code == 200
    wait_for(lambda: ctl.snapshot().active_run.state == "completed")
    assert ctl.snapshot().active_run.completed_cycles == 2


def test_failed_inspection_is_terminal(setup):
    client, ctl, driver = setup
    run_id = start(client, cycles=2, inspection_every=1)
    wait_for(lambda: ctl.snapshot().state == "paused")
    client.post(
        f"/v1/runs/{run_id}/inspections",
        json={"result": "fail", "notes": "Display line visible"},
    )
    assert ctl.snapshot().state == "faulted"
    assert not driver.enabled


def test_manual_pause_stop_and_jog(setup):
    client, ctl, driver = setup
    run_id = start(client, cycles=10)
    assert client.post(f"/v1/runs/{run_id}/pause").status_code == 200
    wait_for(lambda: ctl.snapshot().state == "paused")
    assert not driver.enabled
    assert ctl.snapshot().active_run.completed_cycles == 1
    assert client.post(f"/v1/runs/{run_id}/stop").status_code == 200
    assert (
        client.post("/v1/jogs", json={"target": "closed"}).status_code == 202
    )
    wait_for(lambda: ctl.snapshot().state == "idle")
    assert driver.read().closed_sensor
    assert not driver.enabled


def test_endpoint_disagreement_and_timeout(setup):
    client, ctl, driver = setup
    run_id = start(client, cycles=100)
    driver.jammed = True
    with ctl.lock:
        ctl.run.phase = "closing"
        ctl._move("closed", 15)
        ctl.deadline = time.monotonic() - 1
    wait_for(lambda: ctl.snapshot().state == "faulted")
    assert ctl.snapshot().active_run.completed_cycles == 0
    assert "timed out" in client.get(f"/v1/runs/{run_id}").json()["fault"]


def test_stuck_endpoint_sensor_faults(setup):
    client, ctl, driver = setup
    read = driver.read

    def stuck():
        sample = read()
        sample.closed_sensor = True
        return sample

    driver.read = stuck
    wait_for(lambda: ctl.snapshot().state == "faulted")
    assert client.post("/v1/reset").status_code == 409


def test_restart_marks_run_interrupted(tmp_path):
    from foldbench.models import Run
    from foldbench.storage import Store, utc_now

    store = Store(tmp_path / "foldbench.sqlite3")
    run = Run(
        id="crashed-run",
        mode="simulation",
        state="running",
        phase="opening",
        completed_cycles=17,
        recipe=Recipe(specimen="Duo"),
        calibration=Calibration(),
        started_at=utc_now(),
        updated_at=utc_now(),
    )
    store.save(run)
    store.close()
    ctl = Controller(Settings(data_dir=tmp_path))
    try:
        record = ctl.store.get("crashed-run")
        assert record.state == "interrupted"
        assert record.completed_cycles == 17
        assert ctl.snapshot().active_run is None
    finally:
        ctl.close()


def test_process_lock(setup):
    _, ctl, _ = setup
    with pytest.raises(RuntimeError, match="Another controller"):
        Controller(ctl.settings)


def test_limits_and_unknown_fields(setup):
    client, _, _ = setup
    assert (
        client.post(
            "/v1/runs",
            json={"specimen": "Duo", "current_limit_ma": 300},
            headers={"Idempotency-Key": "limits-key"},
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/v1/runs",
            json={"specimen": "Duo", "disable_safety": True},
            headers={"Idempotency-Key": "limits-key"},
        ).status_code
        == 422
    )


def test_missing_key_rejects_startup(tmp_path):
    with pytest.raises(RuntimeError, match="32"):
        with TestClient(create_app(Settings(data_dir=tmp_path))):
            pass


def test_probe_crc_and_range(tmp_path):
    probe = tmp_path / "w1_slave"
    probe.write_text("00 crc=00 YES\n00 t=25375\n")
    assert read_probe(probe) == 25.375
    probe.write_text("00 crc=00 NO\n00 t=25375\n")
    with pytest.raises(HardwareFault):
        read_probe(probe)
    probe.write_text("00 crc=00 YES\n00 t=85000\n")
    with pytest.raises(HardwareFault):
        read_probe(probe)


def test_database_failure_stops_motion(setup, monkeypatch):
    client, ctl, driver = setup
    start(client, cycles=100)

    def fail(*args):
        raise OSError("disk write failed")

    monkeypatch.setattr(ctl.store, "sample", fail)
    with ctl.lock:
        ctl.last_sample = 0
    wait_for(lambda: ctl.snapshot().state == "faulted")
    assert not driver.enabled

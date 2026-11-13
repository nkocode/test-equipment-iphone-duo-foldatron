"""Motion/fault behavior without pretending to test physical equipment."""

import time

import pytest

from foldbench.revc.controller import Conflict, Controller
from foldbench.revc.drivers import MICROSTEP_DEG, Simulator
from foldbench.revc.models import Commissioning, Recipe, Settings


@pytest.fixture
def controller(tmp_path):
    settings = Settings(data_dir=tmp_path)
    settings.calibration.segment_deg = 0.5
    simulator = Simulator(settings)
    ctl = Controller(settings, simulator, start_worker=False)
    ctl.tick()
    try:
        yield ctl
    finally:
        ctl.close()


def finish_segment(ctl):
    ctl.driver.position = ctl.driver.target
    ctl.driver.last = time.monotonic()
    if ctl.dwell_until is not None:
        ctl.dwell_until = 0
    ctl.tick()


def test_full_cycle_counted_only_after_return_open(controller):
    ctl = controller
    ctl.start(Recipe(sample_id="surrogate"), "cycle-key")
    for _ in range(2000):
        finish_segment(ctl)
        if ctl.state == "idle":
            break
        if ctl.phase == "close":
            assert ctl.run.completed_cycles == 0
    assert ctl.run.state == "completed"
    assert ctl.run.completed_cycles == 1
    assert ctl.telemetry.stage_steps == ctl.cal.open_steps
    previous = ctl.cal.open_steps
    for target, speed in ctl.driver.moves:
        assert abs(target - previous) * MICROSTEP_DEG <= 0.500001
        assert speed <= ctl.cal.max_speed_deg_s
        previous = target


@pytest.mark.parametrize(
    "fault",
    [
        "vacuum",
        "permit",
        "temperature",
        "communication",
    ],
)
def test_fault_stops_and_requires_deliberate_reset(controller, fault):
    ctl = controller
    ctl.start(Recipe(sample_id="surrogate"), "fault-key")
    ctl.tick()
    ctl.driver.fault = fault
    ctl.tick()
    assert ctl.state == "faulted"
    assert ctl.run.state == "faulted"
    assert ctl.run.completed_cycles == 0
    assert ctl.driver.target == ctl.driver.position
    if fault == "communication":
        assert ctl.telemetry is None
    ctl.driver.fault = "none"
    ctl.tick()
    assert ctl.state == "faulted"
    ctl.reset()
    assert ctl.state == "idle"
    assert ctl.run.state == "faulted"


def test_pending_stop_prevents_motion(controller):
    ctl = controller
    ctl.stop_requested.set()
    with pytest.raises(Conflict, match="pending"):
        ctl.start(Recipe(sample_id="surrogate"), "stop-key")
    ctl.tick()
    assert ctl.state == "faulted"
    assert not ctl.driver.moves


def test_idempotency_and_stale_data(controller):
    ctl = controller
    recipe = Recipe(sample_id="surrogate")
    first = ctl.start(recipe, "same-key")
    assert ctl.start(recipe, "same-key").id == first.id
    with pytest.raises(Conflict, match="different recipe"):
        ctl.start(Recipe(sample_id="other"), "same-key")
    ctl.trip("Test end")
    ctl.reset()
    ctl.last_sample = time.monotonic() - 1
    with pytest.raises(Conflict, match="stale"):
        ctl.start(recipe, "new-key-1")


def test_segment_timeout_and_short_stop(controller):
    ctl = controller
    ctl.start(Recipe(sample_id="surrogate"), "short-key")
    ctl.tick()
    ctl.driver.stop()
    ctl.tick()
    assert ctl.state == "faulted"
    assert "short" in ctl.fault


def test_restart_does_not_resume(tmp_path):
    settings = Settings(data_dir=tmp_path)
    ctl = Controller(settings, start_worker=False)
    ctl.tick()
    run = ctl.start(Recipe(sample_id="surrogate"), "restart-key")
    # Simulate an abrupt process exit: leave the running row in storage.
    ctl.driver.close()
    ctl.store.close()
    ctl.process_lock.close()
    restarted = Controller(settings, start_worker=False)
    try:
        saved = restarted.store.get(run.id)
        assert saved.state == "faulted"
        assert restarted.state == "idle"
        assert restarted.run is None
        assert not restarted.driver.moves
    finally:
        restarted.close()


def test_pause_completes_current_cycle_then_resume(controller):
    ctl = controller
    ctl.start(Recipe(sample_id="surrogate", cycles=2), "pause-key")
    ctl.run_action(ctl.run.id, "pause")
    for _ in range(2000):
        finish_segment(ctl)
        if ctl.state == "paused":
            break
    assert ctl.state == "paused"
    assert ctl.run.completed_cycles == 1
    assert ctl.telemetry.stage_steps == ctl.cal.open_steps
    ctl.run_action(ctl.run.id, "resume")
    assert ctl.state == "running"
    assert ctl.phase == "close"


def test_commissioning_cannot_be_released_by_boolean_only():
    with pytest.raises(ValueError, match="shop traveler"):
        Commissioning(released=True)


def test_process_ownership(controller):
    with pytest.raises(RuntimeError, match="Another Rev C"):
        Controller(controller.settings, start_worker=False)

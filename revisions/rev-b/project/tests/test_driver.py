"""Verify bus safety ordering against a deterministic register fake."""

import pytest

from foldbench.hardware import Dynamixel, HardwareFault
from foldbench.models import Calibration, Recipe


def fake_driver():
    driver = object.__new__(Dynamixel)
    driver.cal = Calibration(commissioned=True, record_id="bench-test")
    registers = {132: 1800, 6: 45}
    writes = []

    def write(address, size, value):
        writes.append((address, size, value))
        registers[address] = value

    driver._write = write
    driver._read = lambda address, size: registers.get(address, 0)
    driver.inputs = type("Inputs", (), {"read": lambda self: (1, 0, 0)})()
    return driver, registers, writes


def test_torque_enable_after_current_profile_and_hold_target():
    driver, registers, writes = fake_driver()
    driver.prepare(Recipe(specimen="dummy"))
    assert writes[0] == (64, 1, 0)
    assert writes[-1] == (64, 1, 1)
    assert registers[11] == 5
    assert registers[98] == 25
    assert registers[102] == int(150 / 2.69)
    assert registers[116] == 1800
    assert 0 < registers[112] <= 15 / (0.229 * 6)
    assert registers[108] > 0


def test_uncommissioned_and_out_of_range_never_enable():
    driver, registers, writes = fake_driver()
    driver.cal.commissioned = False
    with pytest.raises(HardwareFault):
        driver.prepare(Recipe(specimen="dummy"))
    assert not writes
    driver.cal.commissioned = True
    registers[132] = 50
    with pytest.raises(HardwareFault):
        driver.prepare(Recipe(specimen="dummy"))
    assert (64, 1, 1) not in writes


def test_register_error_is_never_ignored():
    driver, _, _ = fake_driver()
    with pytest.raises(HardwareFault):
        driver._check(-3001, 0)
    with pytest.raises(HardwareFault):
        driver._check(0, 128)


def test_illegal_goal_is_not_written():
    driver, _, writes = fake_driver()
    with pytest.raises(HardwareFault):
        driver.move(9999)
    assert not writes


@pytest.mark.parametrize("permit", [True, False])
def test_uncoupled_index_limits_and_final_disable(monkeypatch, permit):
    from foldbench import probe

    registers = {0: 1020, 6: 45, 132: 1800}
    writes = []

    class Packet:
        def __getattr__(self, name):
            if name.startswith("read"):
                return lambda port, servo, address: (
                    registers.get(address, 0),
                    0,
                    0,
                )

            def write(port, servo, address, value):
                writes.append((address, value))
                registers[address] = value
                if address == 116:
                    registers[132] = value
                return 0, 0

            return write

    class Inputs:
        def __init__(self, *args):
            pass

        def read(self):
            return permit, False, False

        def close(self):
            pass

    monkeypatch.setattr(probe, "GpioInputs", Inputs)
    if permit:
        probe.index_uncoupled(None, Packet(), 1024, "fake")
        assert registers[102] == 18
        assert registers[112] == 3
        assert registers[132] == 1024
        assert (64, 1) in writes
    else:
        with pytest.raises(RuntimeError, match="permit"):
            probe.index_uncoupled(None, Packet(), 1024, "fake")
        assert (64, 1) not in writes
    assert writes[-1] == (64, 0)

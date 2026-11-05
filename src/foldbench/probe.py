"""Read motor identity/position with torque off; service must be stopped."""

import argparse
import json
import time

from dynamixel_sdk import PacketHandler, PortHandler

from .hardware import GpioInputs


def index_uncoupled(port, packet, target, gpio_chip):
    """Low-current local setup only; requires disconnected drive coupling."""
    inputs = GpioInputs(gpio_chip, (17, 27, 22))

    def write(address, size, value):
        method = getattr(packet, f"write{size}ByteTxRx")
        result, error = method(port, 1, address, value)
        if result or error:
            raise RuntimeError(f"Index write failed: {result}/{error}")

    def read(address, size):
        value, result, error = getattr(packet, f"read{size}ByteTxRx")(
            port, 1, address
        )
        if result or error:
            raise RuntimeError(f"Index read failed: {result}/{error}")
        return value

    try:
        if read(0, 2) != 1020 or read(6, 1) < 38:
            raise RuntimeError("Expected XM430-W350, firmware 38+")
        if not inputs.read()[0]:
            raise RuntimeError("Guard/safety permit is not enabled")
        for address, size, value in (
            (64, 1, 0),
            (10, 1, 0),
            (11, 1, 5),
            (20, 4, 0),
            (38, 2, 18),
            (63, 1, 61),
            (98, 1, 0),
            (102, 2, 18),
            (108, 4, 1),
            (112, 4, 3),
        ):
            write(address, size, value)
        current = read(132, 4)
        if not 0 <= current <= 4095:
            raise RuntimeError("Power-cycle uncoupled motor before indexing")
        write(116, 4, current)
        write(98, 1, 25)
        write(64, 1, 1)
        write(116, 4, target)
        deadline = time.monotonic() + 110
        stable = None
        while time.monotonic() < deadline:
            if not inputs.read()[0] or read(70, 1) or read(146, 1) >= 50:
                raise RuntimeError("Index safety/temperature/device fault")
            if read(98, 1) == 255:
                raise RuntimeError("Index watchdog fault")
            if abs(read(132, 4) - target) <= 8:
                stable = stable or time.monotonic()
                if time.monotonic() - stable >= 0.3:
                    return
            else:
                stable = None
            time.sleep(0.05)
        raise RuntimeError("Index timed out; torque disabled")
    finally:
        try:
            write(64, 1, 0)
        finally:
            inputs.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True)
    parser.add_argument("--index-tick", type=int)
    parser.add_argument("--uncoupled", action="store_true")
    parser.add_argument("--gpio-chip", default="/dev/gpiochip0")
    args = parser.parse_args()
    if args.index_tick is not None and (
        not args.uncoupled or not 256 <= args.index_tick <= 3839
    ):
        parser.error("Index requires --uncoupled and tick 256-3839")
    port = PortHandler(args.port)
    packet = PacketHandler(2.0)
    port.setBaudRate(57600)
    try:
        port.ser.exclusive = True
        port.ser.write_timeout = 0.2
        port.getCurrentTime = lambda: time.monotonic() * 1000
        result, error = packet.write1ByteTxRx(port, 1, 64, 0)
        if result or error:
            raise RuntimeError(f"Torque-off failed: {result}/{error}")
        if args.index_tick is not None:
            index_uncoupled(port, packet, args.index_tick, args.gpio_chip)
        output = {}
        for name, address, size in (
            ("model", 0, 2),
            ("firmware", 6, 1),
            ("tick", 132, 4),
            ("current_raw", 126, 2),
            ("motor_c", 146, 1),
        ):
            method = getattr(packet, f"read{size}ByteTxRx")
            value, result, error = method(port, 1, address)
            if result or error:
                raise RuntimeError(f"Read failed: {result}/{error}")
            output[name] = value
        print(json.dumps(output, indent=2))
    finally:
        port.closePort()


if __name__ == "__main__":
    main()

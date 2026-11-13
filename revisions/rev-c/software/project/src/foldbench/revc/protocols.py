"""Strict, bounded transactions for the Rev C purchased controllers.

Protocol sources and register assumptions are recorded in
revisions/rev-c/software/protocols.md. No third-party serial dependency.
"""

import fcntl
import os
import select
import struct
import termios
import time
from dataclasses import dataclass


class CommunicationError(RuntimeError):
    """A response cannot be used as fresh equipment state."""


class SerialPort:
    """POSIX 8N1 serial port with exclusive process ownership and deadlines."""

    def __init__(self, path, baud=9600, timeout=0.25):
        self.timeout = timeout
        self.baud = baud
        self.fd = os.open(path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            attrs = termios.tcgetattr(self.fd)
            attrs[0] = attrs[1] = attrs[3] = 0
            attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
            attrs[4] = attrs[5] = getattr(termios, f"B{baud}")
            attrs[6][termios.VMIN] = 0
            attrs[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, attrs)
            termios.tcflush(self.fd, termios.TCIOFLUSH)
        except BaseException:
            os.close(self.fd)
            raise

    def begin(self, payload):
        # Includes RTU silent interval, also harmless for the ASCII port.
        time.sleep(max(0.004, 40 / self.baud))
        termios.tcflush(self.fd, termios.TCIFLUSH)
        deadline = time.monotonic() + self.timeout
        view = memoryview(payload)
        while view:
            remaining = deadline - time.monotonic()
            if (
                remaining <= 0
                or not select.select([], [self.fd], [], remaining)[1]
            ):
                raise CommunicationError("Serial write deadline")
            count = os.write(self.fd, view)
            if not count:
                raise CommunicationError("Serial disconnected")
            view = view[count:]
        return deadline

    def read(self, count, deadline):
        result = bytearray()
        while len(result) < count:
            remaining = deadline - time.monotonic()
            if (
                remaining <= 0
                or not select.select([self.fd], [], [], remaining)[0]
            ):
                raise CommunicationError("Serial response deadline")
            chunk = os.read(self.fd, count - len(result))
            if not chunk:
                raise CommunicationError("Serial disconnected")
            result.extend(chunk)
        return bytes(result)

    def line(self, deadline):
        result = bytearray()
        while len(result) < 256:
            result.extend(self.read(1, deadline))
            if result.endswith(b"\n"):
                return bytes(result)
        raise CommunicationError("Oversize ASCII response")

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


def crc16(data):
    """Modbus RTU CRC, transmitted low byte first."""
    value = 0xFFFF
    for byte in data:
        value ^= byte
        for _ in range(8):
            value = (value >> 1) ^ (0xA001 if value & 1 else 0)
    return value


def rtu_frame(body):
    return body + struct.pack("<H", crc16(body))


def decode_rtu(frame, address, function, byte_count):
    if len(frame) < 5 or crc16(frame[:-2]) != int.from_bytes(
        frame[-2:], "little"
    ):
        raise CommunicationError("Modbus length or CRC error")
    if frame[0] != address:
        raise CommunicationError("Modbus wrong device")
    if frame[1] == function | 0x80:
        raise CommunicationError(f"Modbus exception {frame[2]}")
    if frame[1] != function or frame[2] != byte_count:
        raise CommunicationError("Modbus function or byte-count mismatch")
    if len(frame) != byte_count + 5:
        raise CommunicationError("Modbus trailing or missing bytes")
    return frame[3:-2]


class Modbus:
    """Read-only bus: no remote reset, coil write or configuration write."""

    def __init__(self, port):
        self.port = port

    def read(self, device, function, start, count):
        if not 1 <= device <= 247 or function not in (1, 2, 3, 4):
            raise ValueError("Read requires an individual Modbus address")
        if not 0 <= start <= 65535 or not 1 <= count <= 125:
            raise ValueError("Invalid register span")
        size = (count + 7) // 8 if function in (1, 2) else count * 2
        request = rtu_frame(
            struct.pack(">BBHH", device, function, start, count)
        )
        deadline = self.port.begin(request)
        header = self.port.read(3, deadline)
        length = 2 if header[1] & 0x80 else header[2] + 2
        if length > 252:
            raise CommunicationError("Oversize Modbus reply")
        frame = header + self.port.read(length, deadline)
        return decode_rtu(frame, device, function, size)

    def registers(self, device, start, count, function=3):
        data = self.read(device, function, start, count)
        return struct.unpack(f">{count}H", data)


def ascii_frame(body, header="/"):
    raw = body.encode("ascii")
    return header.encode() + raw + f":{-sum(raw) & 255:02X}\r\n".encode()


@dataclass(frozen=True)
class ZaberReply:
    status: str
    warning: str
    data: str


def decode_zaber(raw, device, axis, message_id):
    try:
        line = raw.decode("ascii").strip()
        body, checksum = line.rsplit(":", 1)
        if (
            len(checksum) != 2
            or (sum(body[1:].encode("ascii")) + int(checksum, 16)) & 255
        ):
            raise ValueError("Checksum mismatch")
        fields = body[1:].split(maxsplit=6)
        if not body.startswith("@") or len(fields) != 7:
            raise ValueError("Not a reply")
        if [int(v) for v in fields[:3]] != [device, axis, message_id]:
            raise ValueError("Reply address, axis or ID mismatch")
        if fields[3] != "OK" or fields[4] not in {"IDLE", "BUSY"}:
            raise ValueError(f"Rejected command: {fields[3:]}")
        return ZaberReply(fields[4], fields[5], fields[6])
    except (ValueError, UnicodeError) as exc:
        raise CommunicationError(f"Invalid Zaber reply: {exc}") from exc


class Zaber:
    def __init__(self, port, address=1):
        if not 1 <= address <= 99:
            raise ValueError("Individual Zaber address required")
        self.port = port
        self.address = address
        self.message_id = 0

    def command(self, command, axis=1, allow_warning=False):
        self.message_id = (self.message_id + 1) % 100
        body = f"{self.address} {axis} {self.message_id} {command}"
        deadline = self.port.begin(ascii_frame(body))
        response = decode_zaber(
            self.port.line(deadline), self.address, axis, self.message_id
        )
        if response.warning != "--" and not allow_warning:
            raise CommunicationError(f"Zaber warning {response.warning}")
        return response

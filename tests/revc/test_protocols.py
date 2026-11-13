"""Wire-level acceptance/rejection cases, using published protocol examples."""

import pytest

from foldbench.revc.drivers import decode_temperature
from foldbench.revc.protocols import (
    CommunicationError,
    Modbus,
    ascii_frame,
    crc16,
    decode_rtu,
    decode_zaber,
    rtu_frame,
)


def test_vendor_crc_and_zaber_checksum_examples():
    assert rtu_frame(bytes.fromhex("01 02 00 00 00 08")) == bytes.fromhex(
        "01 02 00 00 00 08 79 CC"
    )
    assert ascii_frame("01 tools echo") == b"/01 tools echo:8F\r\n"
    assert crc16(b"123456789") == 0x4B37


@pytest.mark.parametrize(
    "bad",
    [
        bytes.fromhex("01 02 01 00 A1 89"),
        rtu_frame(bytes.fromhex("02 02 01 00")),
        rtu_frame(bytes.fromhex("01 03 01 00")),
        rtu_frame(bytes.fromhex("01 02 02 00 00")),
        rtu_frame(bytes.fromhex("01 82 02")),
        b"",
        b"\x01\x02",
    ],
)
def test_invalid_rtu_is_never_accepted(bad):
    with pytest.raises(CommunicationError):
        decode_rtu(bad, 1, 2, 1)


def test_valid_rtu_bits():
    assert decode_rtu(rtu_frame(b"\x01\x02\x01\x1f"), 1, 2, 1) == b"\x1f"


@pytest.mark.parametrize(
    "body",
    [
        "02 1 07 OK IDLE -- 42",
        "01 0 07 OK IDLE -- 42",
        "01 1 06 OK IDLE -- 42",
        "01 1 07 RJ IDLE -- BADCOMMAND",
        "01 1 07 OK UNKNOWN -- 42",
        "01 1 07 OK IDLE",
    ],
)
def test_zaber_rejects_wrong_scope_stale_id_and_rejection(body):
    with pytest.raises(CommunicationError):
        decode_zaber(ascii_frame(body, "@"), 1, 1, 7)


def test_zaber_requires_checksum_and_preserves_warning():
    with pytest.raises(CommunicationError):
        decode_zaber(b"@01 1 07 OK IDLE -- 42\r\n", 1, 1, 7)
    reply = decode_zaber(ascii_frame("01 1 07 OK BUSY FS 42", "@"), 1, 1, 7)
    assert (reply.status, reply.warning, reply.data) == ("BUSY", "FS", "42")


@pytest.mark.parametrize("raw, expected", [(235, 23.5), (65526, -1.0), (0, 0)])
def test_type_k_engineering_tenths(raw, expected):
    assert decode_temperature(raw) == expected


@pytest.mark.parametrize("raw", [0x7FFF, 0x8000, 2000, 65000])
def test_open_wire_and_implausible_temperature_fail(raw):
    with pytest.raises(CommunicationError):
        decode_temperature(raw)


class Port:
    def __init__(self, response):
        self.response = response
        self.written = None

    def begin(self, payload):
        self.written = payload
        return 1

    def read(self, count, deadline):
        result, self.response = self.response[:count], self.response[count:]
        if len(result) != count:
            raise CommunicationError("Test timeout")
        return result


def test_modbus_exception_and_read_only_addressing():
    bus = Modbus(Port(rtu_frame(bytes.fromhex("02 84 02"))))
    with pytest.raises(CommunicationError, match="exception"):
        bus.read(2, 4, 0, 2)
    with pytest.raises(ValueError):
        bus.read(0, 4, 0, 2)
    with pytest.raises(ValueError):
        bus.read(2, 5, 0, 1)

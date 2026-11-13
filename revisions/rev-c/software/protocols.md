# Rev C protocol and installation contract

The installable code is `src/foldbench/revc/`. The original `foldbench` entry
point remains the Rev B actuator implementation. Use `python -m foldbench.revc`
for Rev C. No additional production package is required.

## Hardware identities and ports

- Zaber X-RSW60A-E03, individual address 1, ASCII, 115200 baud, 8N1.
  Record its serial number and exact firmware response in the local traveler.
  Use the manufacturer's USB/RS232 cable, not a TTL UART cable.
- Waveshare 26244: RS485 address 1, 9600 baud, 8N1; normal output mode.
- ICP DAS M-7018R: RS485 address 2, 9600 baud, 8N1. Require the R model
  and shop-verified open-thermocouple behavior. Record both raw firmware words.
- Identify adapters with `/dev/serial/by-id/`; do not rely on ttyUSB numbering.
  One process owns each port and the data directory. Use one Uvicorn worker.

The host uses POSIX `termios`, bounded serial reads and exclusive file locks.
A serial timeout, wrong address, wrong function, invalid length, checksum
failure or rejected stage command invalidates the acquisition. Transactions
are not retried into motion. The API is not a real-time or safety controller.

## Zaber setup

With the fixture empty, use Zaber Launcher to establish the reference and
verify direction. The service never issues home, renumber, system reset or
warning-clear commands. Set `comm.checksum=1`, `comm.alert=0`, and leave
`resolution=64`. Record `driver.current.run`, `driver.current.hold` and
`accel` after load/stop qualification. These settings are checked on connection
and reset. Current settings are motor-phase settings, **not measured hinge
torque**. No API route changes the commissioning record.

The driver uses checksummed commands with message IDs and verifies the reply
address, axis and ID. Only warning-free IDLE/BUSY replies are accepted for
normal operation. A stop may be attempted even when a warning is present.
Position uses 0.000234375 degree/microstep. Speed conversion is
`floor(degrees_per_second * 1.6384 / microstep_degrees)`.

Each move is at most the local segment limit (default 0.25 degree, absolute
software cap 0.5 degree). The next segment requires another complete
acquisition and a verified stopped position. This limits a last commanded
movement after host failure; it does **not** provide a safety-rated watchdog
or remove retained worm-drive load. The hardware E-stop/guard circuit must
remove stage supply independently. Keep vacuum energized on protective stop.

## Read-only Modbus map

Wire addresses below are zero-based. The manual's 4xxxx/3xxxx/0xxxx labels
are one-based references, not literal numbers to place on the wire.

| Module | Function | Wire start / count | Meaning |
|---|---:|---|---|
| Waveshare | 02 | 0 / 8 bits | Bit 0 = terminal DI1 permit; bits 1..4 = DI2..DI5 cup vacuum; bits 5..7 reserved |
| M-7018R | 04 | 0 / 2 words | CH0 phone case and CH1 ambient temperature |
| M-7018R | 03 | 480 / 2 words | Firmware identity, compare with commissioning record |
| M-7018R | 03 | 482 / 2 words | Model identity: 0x1822, 0x0070 |
| M-7018R | 03 | 486 / 1 word | Type K code 0x0F |
| M-7018R | 03 | 489 / 1 word | Enabled channel mask 0x03 |
| M-7018R | 01 | 267 / 2 bits | CJC enabled and engineering format; both 1 |
| M-7018R | 01 | 272 / 1 bit | Read-to-clear power-up flag; later reboot latches a fault |

Configure the thermocouple module with the vendor utility before connecting
the service. In engineering mode, Type K values are **signed tenths of a
Celsius degree**; 235 means 23.5 C. CJC's separate 0.01 C scale must not be
applied to channel readings. Reject 0x7FFF and 0x8000 and values outside the
bench plausibility range. Disconnect each probe during commissioning and
record the actual fault response and latency; do not infer wire detection
from plausible room-temperature values. Sensor detachment from the phone
cannot be detected by open-wire diagnostics and requires inspection.

## Source documents

- [Zaber ASCII protocol](https://www.zaber.com/protocol-manual?protocol=ASCII):
  message framing, checksums, IDs, physical-unit conversion and settings.
- [X-RSW-E manual](https://www.zaber.com/manuals/X-RSW-E): model-specific
  electrical and motion requirements.
- [Waveshare 26244 wiki](https://www.waveshare.com/wiki/Modbus_RTU_IO_8CH):
  input function 02, address 0, eight bits; hardware wiring and normal mode.
- [ICP DAS mapping, v1.18](https://www.icpdas.com/web/product/download/io_and_unit/rs-485/document/manual/7000/M-7000_address_mapping_table.pdf),
  pages 37–38: M-7018/R register map.
- [ICP DAS comprehensive manual](https://www.icpdas.com/web/product/download/io_and_unit/rs-485/document/manual/7000/I-7000_M-7000_Comprehensive-Manual_en.pdf),
  Type K engineering example and range tables.

No real hardware was connected during software development. Protocol unit
vectors and simulated fault tests are supplied; commissioning remains a
physical acceptance activity.

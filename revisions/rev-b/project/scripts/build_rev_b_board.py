"""Define and check the interface board against original Adafruit copper."""

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware/rev-b"
ROWS = dict(
    zip(
        "ABCDEFGHIJ",
        [-13.97, -11.43, -8.89, -6.35, -3.81, 3.81, 6.35, 8.89, 11.43, 13.97],
    )
)
ROWS.update(P=19.05, N=21.59)
COMPONENTS = [
    ("U1", "LITEON LTV-817-C DIP4", ["E10", "E11", "F11", "F10"]),
    ("R1", "2k / 1% / 1W", ["D5", "D10"]),
    ("D1", "Vishay 1N4148; cathode first", ["C10", "C11"]),
    ("R2", "10k / 1% / 1W", ["J11", "J16"]),
    ("R3", "1k / 1% / 1W", ["G11", "G20"]),
    ("R4", "1.8k / 1% / 1W", ["J22", "J27"]),
    ("R5", "2.7k / 1% / 1W", ["F27", "F17"]),
    ("R6", "1.8k / 1% / 1W", ["I24", "I29"]),
    ("R7", "2.7k / 1% / 1W", ["H29", "H19"]),
    ("R8", "4.7k / 1% / 1W", ["I21", "I15"]),
]
# R4 and R6 share a row but their bodies/leads must not overlap.
# Move R6 to row B of the otherwise unused lower bank, linking its ends.
COMPONENTS[7] = ("R6", "1.8k / 1% / 1W", ["B24", "B29"])
JUMPERS = [
    ("W1", "I16", "N16"),
    ("W2", "J10", "P10"),
    ("W3", "J17", "N17"),
    ("W4", "J19", "N19"),
    ("W5", "J15", "P15"),
    ("W6", "F24", "E24"),
    ("W7", "F29", "E29"),
]
EXTERNAL = [
    ("A5", "K2:34 permit +24V", "PERMIT24"),
    ("A11", "X1:11A 0V24", "RETURN24"),
    ("P30", "Pi physical pin1 / 3.3V", "3V3"),
    ("N30", "Pi physical pin6 / GND", "GND"),
    ("A25", "Pi physical pin2 / 5V", "5V"),
    ("B25", "Open switch COM", "5V"),
    ("C25", "Closed switch COM", "5V"),
    ("I22", "Open switch NO", "OPEN_NO"),
    ("J24", "Closed switch NO", "CLOSED_NO"),
    ("J20", "Pi physical pin11 / BCM17 permit", "PERMIT_GPIO"),
    ("I27", "Pi physical pin13 / BCM27 open", "OPEN_GPIO"),
    ("J29", "Pi physical pin15 / BCM22 closed", "CLOSED_GPIO"),
    ("F21", "Pi physical pin7 / BCM4 data", "ONEWIRE"),
    ("G21", "Case probe data", "ONEWIRE"),
    ("H21", "Ambient probe data", "ONEWIRE"),
    ("P24", "Case probe VDD", "3V3"),
    ("P25", "Ambient probe VDD", "3V3"),
    ("N24", "Case probe GND", "GND"),
    ("N25", "Ambient probe GND", "GND"),
]


def position(hole):
    """Component-side view; columns increase left to right."""
    return round(-36.83 + (int(hole[1:]) - 1) * 2.54, 2), ROWS[hole[0]]


def main():
    path = DATA / "vendor/adafruit-permaproto-half.brd"
    root = ET.parse(path).getroot()
    copper = {}
    for signal in root.findall(".//signals/signal"):
        for via in signal.findall("via"):
            xy = tuple(round(float(via.attrib[k]), 2) for k in ("x", "y"))
            copper[xy] = signal.attrib["name"]
    parent = {net: net for net in copper.values()}

    def find(net):
        while parent[net] != net:
            net = parent[net]
        return net

    def net(hole):
        return find(copper[position(hole)])

    occupied = []
    for _, _, pins in COMPONENTS:
        occupied.extend(pins)
    for _, a, b in JUMPERS:
        occupied.extend([a, b])
        parent[net(b)] = net(a)
    occupied.extend(hole for hole, _, _ in EXTERNAL)
    assert len(occupied) == len(set(occupied)), "Two leads in one hole"
    for hole in occupied:
        assert position(hole) in copper, hole
    expected = {
        "PERMIT24": ["A5", "D5"],
        "RETURN24": ["A11", "E11", "C11"],
        "LED_ANODE": ["D10", "E10", "C10"],
        "3V3": ["F10", "I15", "P30", "P24", "P25"],
        "GND": ["J16", "F17", "H19", "N30", "N24", "N25"],
        "EMITTER": ["F11", "J11", "G11"],
        "PERMIT_GPIO": ["G20", "J20"],
        "5V": ["A25", "B25", "C25"],
        "OPEN_NO": ["J22", "I22"],
        "OPEN_GPIO": ["I27", "F27", "J27"],
        "CLOSED_NO": ["J24", "B24"],
        "CLOSED_GPIO": ["B29", "H29", "J29"],
        "ONEWIRE": ["I21", "F21", "G21", "H21"],
    }
    groups = {}
    for name, holes in expected.items():
        assert len({net(h) for h in holes}) == 1, name
        groups[name] = net(holes[0])
    assert len(groups) == len(set(groups.values())), "Unintended net short"
    for hole, _, name in EXTERNAL:
        assert net(hole) == groups[name], hole
    # Resistive corner calculations, independently bounded at 1%.
    low = 5 * 2673 / (1818 + 2673)
    high = 5.25 * 2727 / (1782 + 2727)
    current = 5 / (1818 + 2727)
    assert 2.9 < low < high < 3.3
    assert current >= 0.001
    board = {
        "id": "E-BOARD-01",
        "base": "Adafruit 1609",
        "original_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "outline_mm": [81.28, 50.8],
        "mounting": {"hole_diameter_mm": 3.2, "pitch_mm": 73.66},
        "rows_mm": ROWS,
        "components": [
            dict(ref=r, value=v, holes=p) for r, v, p in COMPONENTS
        ],
        "jumpers": [dict(ref=r, holes=[a, b]) for r, a, b in JUMPERS],
        "external": [
            dict(hole=h, connection=c, net=n) for h, c, n in EXTERNAL
        ],
        "continuity_groups": expected,
        "checks": {
            "original_copper_groups": len(parent),
            "distinct_circuit_nets": len(groups),
            "occupied_holes": len(occupied),
            "no_duplicate_holes": True,
            "no_unintended_copper_shorts": True,
            "endpoint_gpio_min_v": low,
            "endpoint_gpio_max_v": high,
            "endpoint_contact_min_a": current,
        },
        "limits": "Connectivity only; not solder, EMC, thermal, "
        "insulation certification or physical commissioning.",
    }
    (DATA / "controller-board.json").write_text(
        json.dumps(board, indent=2) + "\n"
    )
    print(
        f"PASS board: {len(occupied)} unique holes, "
        f"{len(groups)} distinct nets against original copper"
    )


if __name__ == "__main__":
    main()

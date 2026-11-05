# Bill of materials - one FoldBench station

USD planning allowances, 2026-11-04. Verify quotes, interfaces and availability before ordering. Phone, taxes, shipping, machine-shop labor and workshop machinery are excluded. Fastener quantities include spares.

**Station parts: $2,510.00.** Tools if not owned: $415.00. Optional observation/charging: $115.00. Add a 25% station-parts contingency ($627.50) for a planning total of $3,137.50 before tools, optional items and labor.

## Control - $143.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| C01 | 1 | Raspberry Pi 5: 4 GB; 64-bit Raspberry Pi OS | 70.00 | 70.00 | [Vendor/reference](https://www.raspberrypi.com/products/raspberry-pi-5/) |
| C02 | 1 | Pi 27 W USB-C supply: Official supply; regional mains plug | 15.00 | 15.00 | [Vendor/reference](https://www.raspberrypi.com/products/27w-power-supply/) |
| C03 | 1 | Active cooler and vented case: Pi 5 compatible; outside moving envelope | 25.00 | 25.00 | [Vendor/reference](https://www.raspberrypi.com/products/raspberry-pi-5/) |
| C04 | 1 | 64 GB high-endurance microSD: Genuine industrial/high-endurance card; retain backup image | 25.00 | 25.00 | Authorized memory distributor |
| C05 | 1 | Ethernet cable: Cat6, 2 m | 8.00 | 8.00 | Electrical distributor |

## Drive - $904.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| D01 | 1 | XM430-W350-T actuator: ROBOTIS TTL variant; firmware 38+; ID 1; 57600 baud | 330.00 | 330.00 | [Vendor/reference](https://en.robotis.com/shop_en/item.php?it_id=902-0124-000) |
| D02 | 1 | U2D2: ROBOTIS USB to TTL/RS-485 interface; use TTL | 50.00 | 50.00 | [Vendor/reference](https://emanual.robotis.com/docs/en/parts/interface/u2d2/) |
| D03 | 1 | U2D2 power hub board set: 12 V motor power distribution; keyed 3-pin TTL cables | 25.00 | 25.00 | [Vendor/reference](https://www.robotis.us/row-l-u2d2/) |
| D04 | 1 | X430 horn/bracket set: Compatible metal horn, motor bracket and vendor screws; verify package contents | 35.00 | 35.00 | [Vendor/reference](https://en.robotis.com/shop_en/item.php?it_id=902-0124-000) |
| D05 | 1 | USB cable: Pi USB-A to U2D2 connector, 0.5 m; match delivered interface | 8.00 | 8.00 | ROBOTIS or cable distributor |
| D06 | 2 | DYNAMIXEL TTL cable: 3-pin keyed X-series, 200-300 mm, match delivered hub | 8.00 | 16.00 | [Vendor/reference](https://en.robotis.com/shop_en/item.php?it_id=902-0124-000) |
| D07 | 1 | Slip-Ease EAS12 configured clutch: Request EAS12-6MM-6MM; horizontal; vendor-confirmed bidirectional 0.20-0.50 N m setting; quote required | 220.00 | 220.00 | [Vendor/reference](https://www.dynatect.de/en/product/slip-ease-slip-clutches/) |
| D08 | 2 | 6 mm bearing pillow block: Ball bearing; split shaft support; rated >=50 N radial; vendor mounting drawing | 20.00 | 40.00 | Bearing supplier; select matched pair |
| D09 | 1 | 6 mm ground shaft stock: 300 mm stock cut into front/rear stubs and input link; no shaft through phone | 20.00 | 20.00 | Shaft supplier; lengths matched to clutch/support layout |
| D10 | 6 | 6 mm split shaft collar: Two per support plus input/assembly retention as needed | 5.00 | 30.00 | Shaft supplier |
| D11 | 2 | 6 mm split-clamp arm hub: Bolt-on flange, >=1 N m rating; match M03 arms | 15.00 | 30.00 | Mechanical distributor |
| D12 | 2 | MGN7 linear guide with carriage: 100 mm rail; two matched rails; limited to +/-6 mm working float | 30.00 | 60.00 | Linear motion supplier; inspect free movement |
| D13 | 1 | Adjustable friction damper: Rotary/hinge damper, bidirectional; qualify gravity settling; no claimed safety rating | 40.00 | 40.00 | Mechanical supplier; select from measured fixture inertia |

## Structure - $334.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| M01 | 1 | Base plate: 6061-T6 500 x 400 x 8 mm; drawing M01 | 100.00 | 100.00 | Metal supplier / machine shop |
| M02 | 1 | Fabricated plate stock set: All M02-M07 and M09-M13 parts in design table; machining labor excluded | 130.00 | 130.00 | Machine shop; dimension/slot schedule in guide |
| M03 | 8 | Phone shoe blank: Acetal 20 x 15 x 8 mm; machine actual phone contours; M08 | 4.00 | 32.00 | Plastics supplier / machine shop |
| M04 | 1 | Silicone pad sheet: 200 x 200 x 1 mm, Shore A 30-40; removable adhesive if compatible | 15.00 | 15.00 | Industrial silicone supplier |
| M05 | 1 | Compliant mount kit: 4 M4 shoulder screws, spacers, 8 silicone bushings, retaining washers; +/-2 mm travel | 25.00 | 25.00 | Mechanical distributor |
| M06 | 2 | Adjustable mechanical stop: M6 screw, locknut, polyurethane bumper and M10 bracket | 8.00 | 16.00 | Mechanical distributor |
| M07 | 4 | Rubber foot: M6 mounting, >=5 kg rating each | 4.00 | 16.00 | Mechanical distributor |

## Guard - $315.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| G01 | 1 | 2020 aluminum extrusion frame: 4 x 560, 4 x 460, 4 x 360 mm plus base outriggers; 6 m stock allowance | 90.00 | 90.00 | Extrusion supplier; same slot series throughout |
| G02 | 24 | 2020 corner bracket: Matching M5 T-nuts and screws included | 2.50 | 60.00 | Extrusion supplier |
| G03 | 1 | Polycarbonate panel set: Five 4 mm panels to M14 dimensions; allow cutting waste | 120.00 | 120.00 | Plastics supplier |
| G04 | 1 | Door hardware set: 2 hinges, handle, latch, 24 panel clips and captive fasteners | 45.00 | 45.00 | Extrusion supplier |

## Electrical - $627.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| E01 | 1 | Enclosed 12 V DC supply: 5 A, SELV, listed brick, regional AC cord; matching locking DC inlet | 35.00 | 35.00 | Authorized power supply distributor |
| E02 | 1 | Enclosed 24 V DC supply: 1 A or greater, SELV, listed brick and regional AC cord | 30.00 | 30.00 | Authorized power supply distributor |
| E03 | 1 | PNOZ X3 774310: 24 V AC/DC safety relay; use B1/B2 for DC supply | 300.00 | 300.00 | [Vendor/reference](https://www.pilz.com/en-INT/eshop/product/774310) |
| E04 | 1 | Emergency-stop assembly: 40 mm red mushroom/yellow background, twist release, 2 direct-opening NC contacts, 22 mm panel | 45.00 | 45.00 | Safety-component distributor; certified contact assembly |
| E05 | 1 | OMRON D4NS-1BF guard switch: 2 NC direct-opening, tongue operated; matching PG13.5 gland | 60.00 | 60.00 | [Vendor/reference](https://industrial.omron.co.uk/en/products/D4NS-1BF) |
| E06 | 1 | OMRON D4DS-K2 actuator key: Match switch and chosen door entry direction; captive mounting | 15.00 | 15.00 | [Vendor/reference](https://www.ia.omron.com/products/family/1465/dimension.html) |
| E07 | 1 | Reset pushbutton: Momentary NO, 22 mm, blue label; physical monitored reset only | 12.00 | 12.00 | Industrial controls distributor |
| E08 | 1 | DC disconnect: 2 pole, rated >=24 V DC 5 A; isolate low-voltage equipment for service | 15.00 | 15.00 | Electrical distributor |
| E09 | 1 | Fuse/holder kit: 3 A fast DC F1, 0.5 A DC F2, covered holders plus 2 spares each; verify inrush and relay coordination | 20.00 | 20.00 | Electrical distributor |
| E10 | 1 | Covered electrical enclosure: 300 x 250 x 150 mm nominal; mounting plate; outside guard sweep | 60.00 | 60.00 | Electrical enclosure supplier |
| E11 | 1 | DIN/terminal kit: 300 mm DIN rail, end stops, 20 terminals, 10 jumpers, labels | 35.00 | 35.00 | Electrical distributor |

## Sensing - $52.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| S01 | 2 | OMRON D2F-01L endpoint switch: Gold-contact low-load SPDT; use COM/NO; adjustable output-side cams | 5.00 | 10.00 | [Vendor/reference](https://components.omron.com/sg-en/faq/switches/FAQE20005) |
| S02 | 2 | DS18B20 probe: Genuine 3-wire powered probe; 3.3 V; one case and one ambient | 10.00 | 20.00 | Authorized semiconductor/sensor distributor |
| S03 | 1 | Isolated permit board parts: LTV-817C, 2 kohm 0.5 W, 1N4148, 3 x 10 kohm, 3 x 1 kohm, 4.7 kohm, covered perfboard and terminals | 12.00 | 12.00 | Electronics distributor; verify optocoupler pinout |
| S04 | 1 | Probe attachment kit: Thin removable thermal tape, cable anchors, ambient standoff | 10.00 | 10.00 | Electronics distributor |

## Wiring - $75.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| W01 | 1 | 18 AWG wire: Red/black, 3 m each, stranded, appropriately rated insulation | 15.00 | 15.00 | Electrical distributor |
| W02 | 1 | Signal/safety wire set: 22 AWG 4-core 5 m; 24-26 AWG twisted pair 5 m | 20.00 | 20.00 | Electrical distributor |
| W03 | 1 | Terminations and strain relief: 100 ferrules, 8 glands, 20 heat-shrink pieces, 20 tie bases, 50 ties | 25.00 | 25.00 | Electrical distributor |
| W04 | 1 | Pi header breakout: 40-pin cable/breakout with screw terminals and standoffs | 15.00 | 15.00 | Electronics distributor |

## Fasteners - $60.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| F01 | 1 | M3 kit: 40 M3x8, 20 M3x12, 40 washers, 40 locknuts | 10.00 | 10.00 | Fastener distributor |
| F02 | 1 | M4 kit: 40 M4x10, 20 M4x16, 80 washers, 40 locknuts | 12.00 | 12.00 | Fastener distributor |
| F03 | 1 | M5/M6 kit: 40 M5x10/T-nuts, 20 M6x16, 40 M6 washers, 20 M6 locknuts | 18.00 | 18.00 | Fastener distributor |
| F04 | 1 | Consumables: Low-strength threadlocker, witness paint, 0.1/0.2/0.5 mm shims | 20.00 | 20.00 | Industrial supplier |

## Tools - $415.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| T01 | 1 | Digital caliper and angle gauge: 0.1 mm fit measurement; angle resolution <=0.5 degrees | 70.00 | 70.00 | Metrology supplier |
| T02 | 1 | Force gauge and 100 mm arm: 0-20 N, resolution <=0.1 N; documented calibration; custom arm | 180.00 | 180.00 | Metrology supplier; verify accuracy for acceptance |
| T03 | 1 | Multimeter: DC voltage, continuity, adequate probe insulation | 40.00 | 40.00 | Authorized instrument distributor |
| T04 | 1 | Assembly tools: Hex keys, low-range torque screwdriver, drill/taps/deburr tool access | 100.00 | 100.00 | Workshop allowance; machine tools excluded |
| T05 | 1 | Two-leaf phone dummy: Match measured envelope and hinge path sufficiently for clearance trials | 25.00 | 25.00 | Fabricate; no claim to reproduce phone hinge torque |

## Optional - $115.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| O01 | 1 | Observation camera and mount: USB UVC camera for external recording; no camera control in delivered API | 70.00 | 70.00 | Camera supplier |
| O02 | 1 | Phone charger/cable: Genuine compatible charger; strain relief; charging is separate qualified test condition | 45.00 | 45.00 | Apple / authorized distributor |

## Software - $0.00

| ID | Qty | Item / specification | Unit USD | Ext. USD | Source |
| --- | ---: | --- | ---: | ---: | --- |
| SW01 | 1 | Python control stack: FastAPI, Uvicorn, dynamixel-sdk; Pipenv lock; OS and Python 3.12 | 0.00 | 0.00 | Delivered source; no paid license allowance |

# FoldBench / iPhone Duo

Revision A - prototype engineering package - 4 November 2026

## 1. What is being built

A single-station, guarded benchtop folding-endurance tester. A Raspberry Pi runs Python/FastAPI and commands a smart servo through USB. One phone half is supported in a stationary cradle; the other is carried by a rotating, floating cradle. The machine records verified open-close-open cycles, motor current, temperatures, faults and operator inspections.

This is an original design inspired by CNET's machine, not a reverse-engineered copy or a claim to reproduce its test method. The supplied Python software is executable and simulator-tested. The mechanics, wiring, Pi GPIO integration, stopping time, continuous-duty capability and phone fit have not been physically validated. Treat this package as a prototype for fabrication and commissioning, not a certified unattended test machine.

### Video observations versus design decisions

The linked 60-second CNET clip shows an aluminum-framed mechanism repeatedly opening and closing a phone, a moving cradle/linkage, cables, a red stop button and a displayed cycle counter. The caption identifies the phone as iPhone Duo and describes continuous operation. The clip does not establish a motor model, torque, speed profile, hinge trajectory, sensor architecture or dimensioned drawings. Those details below are our design choices. Playback and several mechanism views were inspected; no audio transcript was available.

Apple lists the Duo at 164.6 x 117.8 x 5.2 mm open, 84.1 x 117.8 x 11.3 mm closed, and 254 g. These are exterior envelopes, not a fixture drawing. Measure the actual phone's camera protrusion, half-body widths, buttons, port location, edge radii, hinge migration and usable contact patches before machining the phone-contact shoes. [S1, S2]

### Prototype operating contract

| Parameter | Revision A choice |
| --- | --- |
| Specimen | One iPhone Duo, case removed; USB-port half stationary |
| Base / outer guard envelope | 500 x 400 mm / approximately 600 x 500 x 400 mm |
| Motion | One motor, 1:1 shaft drive, horizontal hinge axis, floating moving cradle |
| Angle convention | 0 degrees closed, 180 degrees open |
| Initial test span | 5-175 degrees; partial-fold screening, explicitly recorded |
| Full closure | Only after phone-specific fit and force qualification; use measured angles/ticks |
| Speed | 1-30 degrees/s request range; initial installation ceiling 15 degrees/s |
| Endpoint dwell | 0.25-60 seconds; default 1 second |
| Current | Default ceiling 150 mA; commissioning range 20-350 mA |
| Mechanical torque limiter | Initially 0.20 N m; adjust only from measured baseline, maximum design target 0.50 N m |
| Sampling | Nominal 20 Hz control loop; stored 1 Hz plus confirmed endpoint samples |
| Cycle definition | Confirmed open, then closed, then open; stable endpoint evidence for 150 ms |
| Persistence | SQLite FULL synchronous commits; one commit per counted cycle |
| Restart | No automatic motion or run resumption |
| Inspection pause | Every 1,000 cycles by default; operator must record pass to resume |
| Phone / ambient / motor limits | Initial case 40 C, ambient 10-30 C, motor 55 C |

These limits are conservative starting choices, not measured safe limits for the Duo. Motor current is not calibrated hinge torque. A case sensor does not measure internal battery temperature. A completed run means the requested mechanical cycling finished; it does not mean the phone passed functional testing.

Ignoring acceleration, the default 170-degree span gives a cycle time of 2 x 170 / 15 + 2 x 1 = 24.7 seconds, or at most about 3,500 cycles/day. Acceleration, verification and inspections reduce throughput. Do not compare this directly with CNET's cycle totals or convert cycles into years of normal use.

## 2. Architecture and interlocks

The Pi has its own 27 W supply and remains powered after an emergency stop. An enclosed 12 V, 5 A supply feeds the motor through a fused safety-relay output path. A separate enclosed 24 V supply feeds the safety relay. No exposed mains wiring is required inside the machine.

Use a Pilz PNOZ X3 774310 with a two-contact emergency stop and a two-contact tongue-operated guard switch. Both safety channels must open when either device is operated. Use monitored physical reset, outside the guard. Route the motor's positive supply through two safety output contacts in series. This removes motor power independently of Python, Linux and network availability. The third safety output drives an isolated Pi status input. The exact relay input wiring must follow the manufacturer's dual-channel, cross-short-detection diagram; it must be checked against the supplied revision before energizing. No safety performance level is claimed for the assembled prototype. [S5]

Normal API stop disables torque. API protective stop latches a fault. Neither guarantees an immediate physical stop. Power removal can allow the cradle to settle under gravity: retain the phone mechanically, damp the moving cradle, and measure the worst-case coast/fall motion during commissioning. Place the guard switch so motion stops before a hand can reach the swept volume; use a locking guard if the measured time does not permit this.

The actuator bus watchdog stops motion after loss of command traffic; it can retain holding torque and is not the emergency-stop circuit. Mode 5 provides current-based position control but does not enforce the servo's min/max position registers. Independent adjustable fixture stops and the slip clutch are therefore essential. [S3]

## 3. Mechanical layout

Use the supplied layout SVG and parametric OpenSCAD source as design references. The source models the assembly envelope and provides flat stock/slot templates. Vendor bearing, horn, slide and motor mounting patterns must be taken from the parts actually delivered and transfer-drilled into the slotted adapter plates. The model is not a collision-certified or tolerance-validated production assembly.

Coordinate system: origin at the center of the base's top surface. X is left/right across the phone, Y follows the phone hinge, Z is upward. The nominal phone hinge axis is X=0, Z=140 mm. The phone height runs from Y=-58.9 to +58.9 mm. The stationary half is at negative X; the moving half is at positive X when open. The front of the machine is negative Y.

### The hinge must remain unobstructed

Use two separate 6 mm stub shafts, one in front of and one behind the phone. Do not install a continuous shaft through the phone hinge. Front/rear support centers are Y=-95 and +95 mm. The front stub projects toward the motor; the rear stub is an idler. Bearings and drive components stay outside Y=+/-70 mm. A U-shaped rotating yoke joins the two stubs through two radial arms and an outer crossbar at X=115 mm. This leaves the phone hinge space empty.

Each half is supported from its exterior back, with soft shoes on suitable metal-frame areas. Nothing presses on the flexible display, hinge gap, buttons, camera glass or USB connector. The moving plate rides on two radial linear guides, allowing +/-6 mm translation; compliant shoe mounts allow approximately +/-2 mm tangential movement. The phone's real hinge determines the path. It must not be forced to behave like a perfect pin hinge.

### Fabricated parts and dimensions

All dimensions in mm. General noncritical dimensions +/-0.5; hole locations +/-0.2; bearing fits and shaft sizes to the purchased bearing specification. Deburr all edges, minimum 0.5 edge break. Phone-adjacent corners radius at least 2. Use 6061-T6 aluminum for structural plates; acetal for shoe bodies; 1 mm silicone pads, approximately Shore A 30-40, for replaceable contact surfaces.

| Drawing ID | Qty | Stock and operations |
| --- | --- | --- |
| M01 base | 1 | 500 x 400 x 8 aluminum; mounting grid holes 6.6 diameter on 25 mm grid in center 350 x 250 area; four foot holes at 20 mm from corners |
| M02 bearing towers | 2 | 100 x 180 x 8 aluminum, 100 x 50 x 6 angle feet; slotted bearing adapter permits Z=130-150; tower feet permit X +/-10 and Y +/-15 |
| M03 yoke radial arms | 2 | 125 x 25 x 6 aluminum; 6 mm split-clamp hub at inner end; crossbar holes at X=115, two M4 fixings per joint |
| M04 yoke outer crossbar | 1 | 190 x 25 x 6 aluminum; bridges arms at Y +/-95; keep outside phone edge |
| M05 moving backplate | 1 | 100 x 135 x 4 aluminum; four 4.5 x 20 adjustment slots; attach to slide carriages, not rigidly to yoke |
| M06 fixed backplate | 1 | 100 x 135 x 4 aluminum; camera clearance pocket located from actual phone; four 4.5 x 20 adjustment slots |
| M07 fixed cradle risers | 2 | 100 x 125 x 6 aluminum vertical plates plus 100 x 40 x 6 feet; final height shimmed to phone exterior back |
| M08 shoe bodies | 8 | Acetal blanks 20 x 15 x 8; slot 4.5 x 10; machine contact contour after specimen measurement; four shoes per half |
| M09 motor shelf | 1 | 100 x 100 x 6 aluminum on two 100 mm slotted angles; position motor axis coaxial with front shaft at Z=140 |
| M10 stop/sensor mounts | 4 | 40 x 25 x 3 aluminum angles; slotted base holes 4.5 x 15; two for stops and two for switches |
| M11 horn-to-shaft adapter | 1 | 30 diameter x 10 aluminum hub; 6 H7 bore with split clamp; horn fixing pattern matched to supplied ROBOTIS horn; no invented spline dimensions |
| M12 guide carrier brackets | 2 | 100 x 25 x 4 aluminum; slotted holes for the two MGN7 guide rails; attach across yoke arms behind moving plate |
| M13 switch cams | 2 | 20 x 15 x 3 acetal; bolt to moving cradle/yoke output side of clutch; adjustable trigger angle |
| M14 guard panels | 5 | 4 mm polycarbonate: front/rear 560 x 360 (2), sides 460 x 360 (2), top 560 x 460 (1); mounting overlaps adjusted to frame |

The fixed plate's back surface orientation and camera cutout differ between phone halves; do not make mirror-image contact shoes without checking the specimen. Use pads on the rigid perimeter only. The clamp restraint must resist a 10 N tangential pull without crushing or changing the manual hinge feel. If that cannot be achieved on a non-screen contact patch, redesign the shoes rather than tightening them further.

The free carriage travel must remain at least 2 mm from either mechanical travel limit at every angle. End stops act on the yoke, not the phone. For the initial 5-175-degree trial, set stops approximately 1 degree outside the software endpoints, still within the specimen's freely moving range. For a full-range test, the stops must be established from actual safe closure/opening and must never force negative opening or overextension.

### Drive sizing and limitations

At an assumed moving phone-half mass of 0.127 kg and center radius 0.042 m, gravity contributes about 0.052 N m. A 0.15 kg lightweight moving fixture at radius 0.05 m adds about 0.074 N m. Together these are roughly 0.126 N m before hinge friction, acceleration and imbalance. Weigh the finished fixture and measure the real force. This estimate is why an unqualified low-current setting may stall.

The XM430 has ample peak torque, but peak/stall torque is not a continuous-duty rating. Do not use its full rating on a phone. Set the friction clutch above the measured normal folding torque with a small documented margin and below the established specimen/fixture limit, never above this prototype's 0.50 N m design ceiling. At a 60 mm lever, 0.20 N m corresponds to 3.33 N tangential force. If baseline folding requires more than the available protective range, stop and revise the fixture or counterbalance; do not override limits.

For the clutch, specify Dynatect Polyclutch EAS12, shaft-to-shaft, 6 mm input/output bores (configured request EAS12-6MM-6MM). Obtain a vendor quote confirming bidirectional low-speed oscillation and adjustment around 0.20-0.50 N m. This is a configured item, not a confirmed in-stock SKU. Its published nominal envelope is 19.05 diameter x 31.75 long; our design uses a horizontal axis as required by the installation instructions. Require supplier confirmation of low-end adjustment and breakaway torque before ordering. [S6]

## 4. Bill of materials

The complete line-item bill is supplied as BOM.json and BOM.md, including stock, fasteners, wiring, software, calibration tools and optional observation equipment. Quantities are for one station. Prices are planning allowances in USD, not supplier quotations. The phone, taxes, shipping, professional fabrication labor and a suitable test-room fire response arrangement are excluded. The clutch configuration and phone shoes require final fit/quote confirmation.

Use equivalent parts only if the interfaces, electrical ratings, failure behavior and mounting requirements are rechecked. Do not substitute an unisolated hobby relay board for the safety relay, or a 5 V logic connection for a 3.3 V Pi input.

## 5. Electrical connections

### Power and relay output netlist

| Net | Connection |
| --- | --- |
| P1 | Pi official 27 W USB-C supply directly to Pi; independent of motor stop circuit |
| P2 | Enclosed 12 V 5 A supply + -> DC disconnect -> 3 A fast fuse F1 -> safety relay 13 |
| P3 | Relay 14 -> relay 23; relay 24 -> U2D2 power-hub +12 V input |
| P4 | 12 V supply negative -> hub motor ground; use ROBOTIS keyed cables to servo |
| P5 | Pi USB -> U2D2; U2D2 TTL 3-pin port -> hub -> XM430-W350-T; do not use the RS-485 port |
| P6 | Enclosed 24 V 1 A supply + -> 0.5 A fuse F2 -> PNOZ B1; 24 V negative -> B2 |
| P7 | 24 V fused + -> relay 33; relay 34 -> 2.0 kohm 0.5 W resistor -> optocoupler LED anode; cathode -> 24 V negative |
| P8 | Optocoupler collector -> Pi 3.3 V; emitter -> GPIO17 node; 10 kohm from node to Pi ground; 1 kohm series from node to GPIO17 header pin |
| P9 | Pi GPIO inputs use Pi ground only; no 24 V conductor connects directly to any Pi pin |

Use an LTV-817C or equivalent optocoupler with documented CTR at the chosen current; its LED receives approximately 11 mA from the 24 V status circuit. Confirm GPIO high is above 2.0 V and below 3.3 V. Check the selected part's pinout. Add a reverse-protection diode across the optocoupler LED. The 33-34 circuit is status only. Power-cut testing at the actual motor terminals is still required.

Use the manufacturer's two-channel E-stop/safety-gate circuit with cross-short detection and monitored reset. Put the two E-stop NC contacts and the corresponding guard NC contacts in their separate channels. For PNOZ X3 DC supply use B1/B2, not an assumed A1/A2 connection. Monitored reset uses S33/S34; leave automatic-start S13/S14 unlinked. Preserve or remove the delivered S11/S12 link only as the selected vendor diagram specifies. The manual's schematic, rather than a guessed text pin mapping, is the authority for the input circuit. Check fault masking in the series-connected devices and validate each device independently. [S5]

### Pi header table (BCM numbering)

| Signal | BCM line | Physical header pin | Connection |
| --- | --- | --- | --- |
| Safety permit | 17 | 11 | Isolated active-high status from P8 |
| Open endpoint | 27 | 13 | Gold-contact switch NO to 3.3 V; 10 kohm pulldown; 1 kohm series to Pi |
| Closed endpoint | 22 | 15 | Same circuit as open switch |
| 1-Wire data | 4 | 7 | Both DS18B20 data wires; one 4.7 kohm pullup to 3.3 V |
| 3.3 V | - | 1 | Probe supply and input circuit supply only |
| Ground | - | 6 | Probe/input ground |

Use three-wire powered temperature probes, not parasite power. Identify their actual 28-* serial numbers. Attach the case probe using thin removable thermal tape to the stationary half's exterior frame/back, away from the camera, not to the folding display. Place the ambient probe in shaded, freely circulating air near the phone. The case probe must remain attached through all folds; its loss of thermal contact is not automatically detectable from a valid digital reading.

Use 18 AWG for 12 V distribution, 22 AWG for safety wiring, 24-26 AWG twisted pairs for short signal runs. Use ferrules, numbered terminals, strain relief and covered connections. Keep signal wiring away from the clutch/shaft and motor cabling. The USB charging cable, if used, goes to the stationary phone half with a loose strain-relieved loop. Continuous charging is a separate test condition: initially run uncharged and periodically inspect the battery/phone. A case-temperature stop does not certify battery safety.

## 6. Assembly sequence

1. Inventory all BOM lines. Print the drawings at labeled scale only when explicitly shown; the overview is not a drilling template. Verify vendor dimensions and clutch configuration before cutting adapter parts.
2. Machine and deburr the base, towers, yoke, plate blanks and slotted brackets. Bolt on the four feet. Support the wider guard frame on fixed outriggers from the base plate. Assemble the base frame square; measure diagonals within 1 mm. Do not install the phone.
3. Mount the bearing towers at Y=+/-95. Use a temporary straight alignment rod through the two bearing bores to align them at X=0, Z=140 within 0.2 mm. Remove this rod: it must never be present with the phone installed.
4. Install the two short stub shafts, radial yoke arms and outer crossbar. Use two shaft collars per support to restrain axial motion. Verify the empty yoke rotates without binding. A shaft must not project into the phone envelope.
5. Mount the motor on its slotted shelf outside the front support. Connect the verified horn adapter, short input shaft and slip clutch. Align the clutch axes within 0.1 mm as an assembly target. No phone loads should be carried by the servo output bearing alone. Tighten hub screws to the hub supplier's value; apply witness marks.
6. Mount the two radial rails and moving plate. Confirm +/-6 mm available travel, soft retention at travel extremes, and no loose ball carriage. Fit the four compliant shoe mounts. Adjust float without appreciable preload on a dummy phone.
7. Build the fixed cradle and align the two phone backing planes using a two-leaf dummy of the measured phone envelope. Include camera/connector relief before any real-phone fit. Ensure the yoke and brackets clear both halves over the entire arc.
8. Fit adjustable stops and the two endpoint switches. Switch cams must be on the output side of the clutch. Initial switching should occur close to the calibrated endpoint, never throughout a large part of the stroke. Fit locknuts and witness marks.
9. Assemble the polycarbonate guard and front door. Fit the captive tongue switch and E-stop/reset panel. Leave at least 25 mm clearance between guard and every moving part. Avoid openings through which fingers can reach the mechanism; assess ventilation slots and cable entries for reach-through.
10. Install the low-voltage electrical enclosure, DIN rail, relay, fuses, DC disconnect, terminal blocks and isolated input board. Connect exactly as the netlist and vendor relay diagram require. Label the 12 V, 24 V and 3.3 V domains distinctly.
11. Fit the Pi, cooler and storage outside the motion envelope. Connect USB and probes; route all wires clear of stops, rails and pinch points. Check continuity and polarity before connecting power supplies.
12. With the servo disconnected, test guard and E-stop operation using a meter at the hub output. Confirm physical reset is required after each interruption, that holding reset cannot defeat the intended monitored behavior, and that reset never commands motor motion.

## 7. Commissioning and calibration

Record results in the supplied commissioning checklist. Never set `commissioned=true` based solely on the example file. The API cannot remotely widen installation limits.

### A. Verify electronics with motor uncoupled

Set servo ID 1, Protocol 2, 57600 baud. These are the expected XM430 settings. Stop the service and use `pipenv run python -m foldbench.probe --port /dev/serial/by-id/...` to read identity and position with torque disabled. The probe utility does not command movement. Verify model 1020 and firmware at least 38. If ID/baud differs, restore the documented configuration using the vendor's setup procedure before connecting the application. The application does not scan or broadcast to unknown actuators.

First set up an empty mechanism. With the motor mechanically disconnected, set the yoke at the chosen closed angle against an angle gauge. Select an encoder region at least 256 counts from rollover, with room for about 2,000 counts of positive movement. The supplied Python setup command can index the mechanically uncoupled motor: append `--index-tick 1024 --uncoupled --gpio-chip /dev/gpiochip0` to the probe command, using the verified GPIO chip. This enables a roughly 48 mA, 4-degree/s setup move only while the guard/safety permit is healthy, then disables torque. The flag is an operator declaration: the software cannot verify that the coupling and phone are absent. Never use this command on a coupled mechanism. Record the observed tick, reconnect the clutch without moving either side, and use angle-span x 4096/360 for the preliminary open-tick calculation. Check positive motor direction opens the phone; reverse mechanical orientation if necessary, since this implementation expects open_tick > closed_tick.

The Python operational controller and uncoupled indexing utility are supplied. A servo with a nondefault ID/baud may require vendor recovery before use. No handset-control software is required. No claim is made that iOS exposes display health, touch health or internal battery temperature through this REST API.

### B. Empty mechanism and dummy qualification

1. Verify GPIO chip identity from `/sys/bus/gpio/devices/gpiochip*/label`. Select the chip that owns the header BCM lines. Chip numbers differ between Pi/kernel versions. The driver uses the Linux GPIO v1 character ABI; if the kernel disables this ABI, stop and adapt/test the driver before use.
2. Enable the `w1-gpio` overlay on BCM4 in the Pi boot configuration. Verify two distinct probes produce CRC-valid readings. Identify case versus ambient by gently warming one and record the serial mapping.
3. Verify inputs at the API or with a meter: healthy permit high, each endpoint high only at its own position, open wires low. Both endpoints must never be high together.
4. Inspect all hard stops, guard wiring, clutch alignment and dummy clearance. Create an EMPTY-FIXTURE commissioning record and a temporary calibration file for dummy-only testing, with 5 degrees/s and the lowest current capable of moving the empty fixture. Do not reuse this record for a phone test.
5. Run single endpoint jogs with the guard closed, no phone, and a hand at the E-stop. Check measured direction and travel. Operate E-stop and open the guard independently during motion. Measure stopping time and distance, including gravity settling; record the worst value and verify access is prevented until motion stops.
6. Disconnect USB during movement. The bus watchdog must trip, and reconnect must not resume. The resulting watchdog fault requires inspection and a motor power cycle before reset. Stop the Pi process and cut Pi power separately; verify no automatic restart.
7. Jam the dummy gently with a calibrated restraint, not fingers. Verify clutch slips below its qualified torque, endpoint timeout faults, the count does not increase, and power interruption releases drive. Test a disconnected endpoint wire and each disconnected temperature probe.
8. Run 100 dummy cycles, recheck alignment and clamp marks, then run 1,000 dummy cycles while checking motor temperature, rails, cable wear and counts. Reconcile the machine count against an independent tally/video sample.

### C. Phone-specific qualification

Measure the actual Duo and complete its shoes. Support the phone with torque off and clutch disengaged. Move it by hand over the entire intended range; there must be no forced translation, clamp movement, screen contact or cable tug. Record natural open/closed angles and the radial slide excursion at 0, 45, 90, 135 and 180 degrees where physically reachable.

Measure the peak folding force gently at a known lever radius, in both directions and at several angles. Include empty-fixture gravity/friction separately. Set the clutch using a force gauge on a 100 mm arm: torque in N m = force in N x 0.100. Test clockwise and counterclockwise breakaway repeatedly; require repeatability within the documented acceptance band, initially +/-10%. Lock and mark the adjuster.

Set current only high enough to complete the stroke with margin below the measured mechanical protection threshold. The firmware current scale is not a torque calibration. Record the relationship from actual measurements. If the phone cannot move within the 350 mA / 0.50 N m ceiling, revise the mechanics; do not silently raise it.

Start with 5-175-degree partial folds at 5 degrees/s, 2-second dwells, one cycle. Inspect the phone, pads and cable. Repeat ten cycles, then 100. Only after these pass may the phone-specific `commissioned=true` record authorize routine runs. Full 0-180-degree operation needs a new measurement/stop/switch setup and recorded calibration; use whatever real angles the phone freely reaches, not forced mathematical endpoints.

### D. Run acceptance and result interpretation

Record baseline photographs, serial identifier, iOS version, battery state, charge state, room temperature, fixture revision and pre-existing damage. At each scheduled pause inspect display uniformity, crease, touch response, frame, hinge feel, clamp witness marks and USB cable. Record pass/fail and notes through the API. The software cannot judge these automatically. A fail ends the run in a fault state; a pass permits, but does not initiate, resume.

Power loss can occur after a physical cycle but before its database commit. The persisted count is a confirmed lower bound and may omit that last cycle. Partial strokes are deliberately uncounted. Do not merge counts across interrupted/replaced specimens without an explicit analysis record.

## 8. Maintenance and unattended operation boundary

Before each run: operate E-stop and guard, inspect fasteners/pads/cable, check probe attachment, disk space and serial/time settings. After each 1,000 cycles initially: check clutch setting, witness marks and rails; set the later interval from measured wear. Lubricate only the rail/bearing locations specified by their manufacturers. Keep lubricant away from the clutch and phone. Recommission after changing shoes, clutch, firmware, servo, stops, sensors or safety wiring.

Revision A is intended for supervised endurance testing. A 24/7 unattended release needs physical validation under the intended room conditions, independent battery/thermal incident provisions, long-duration component qualification, a completed machine risk assessment and confirmed stopping performance. The video demonstrates an operating aim, not evidence that this newly designed machine is ready for that service.

## 9. Software and API behavior

See README.md and docs/API.md for installation and requests. FastAPI serves interactive documentation at `/docs`, the live schema at `/openapi.json`, and the same exported schema in openapi.json. All operational endpoints require `X-API-Key`. Start requests also require `Idempotency-Key`; retries return the original run and changing the body with the same key is rejected.

Only one run or jog may own the mechanism. A dedicated worker serializes hardware commands. Temperature conversion runs independently so it cannot block bus-watchdog servicing. The process locks its data directory and exclusively opens the serial port. Do not use Uvicorn reload, multiple workers or multiple services with different data directories on the same station.

Results include the exact recipe and commissioning snapshot, simulated/physical mode, phase, confirmed cycles, timestamps and fault. Samples include motor-derived angle, signed current, motor/case/ambient temperatures, supply voltage and endpoint/permit states. Samples and events use bounded pagination; CSV export returns an `X-Next-After` cursor. The software does not auto-delete test data. It stops a running test when free space falls below 100 MiB.

If torque-off cannot be confirmed, the controller reports that explicitly and stops background bus polling so it cannot keep feeding the watchdog. Use the physical E-stop. Any API stop acknowledgement means the request was accepted, not that a safety-rated stop was proven.

## 10. Sources and evidence

Sources checked 4 November 2026. Component pricing in the BOM is an estimate independent of source-listed retail prices.

- S1: CNET video/post: https://x.com/CNET/status/2114060888109928499
- S2: Apple Duo exterior dimensions: https://www.apple.com/iphone-duo/specs/
- S3: ROBOTIS XM430-W350 control table, operating modes and watchdog: https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/
- S4: ROBOTIS U2D2 connections: https://emanual.robotis.com/docs/en/parts/interface/u2d2/
- S5: Pilz PNOZ X3 manual, especially wiring and preparation pages 11-14: https://www.pilz.com/download/open/PNOZ_X3_Operating_Manual_20547-EN-10.pdf
- S6: Dynatect Slip-Ease specifications and horizontal installation: https://www.dynatect.de/en/product/slip-ease-slip-clutches/
- S7: Raspberry Pi power guidance: https://www.raspberrypi.com/documentation/computers/getting-started.html
- S8: OMRON D4NS guard switch: https://industrial.omron.co.uk/en/products/D4NS-1BF
- S9: FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- S10: FastAPI API key security: https://fastapi.tiangolo.com/reference/security/
- S11: DYNAMIXEL Python SDK: https://github.com/ROBOTIS-GIT/DynamixelSDK

Software tests and generated schema were checked locally. No Pi, servo, phone or fabricated mechanism was connected during this work. Physical verification remains the commissioning work described above.

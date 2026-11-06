# foldatron Rev B engineering package

**Development review, not a fabrication release.** This replaces the Rev A
2020 frame and schematic fixture geometry with a 1010 structure and a
CadQuery/OpenCascade assembly. It does not make the earlier prototype a
physically validated machine.

Start with the [drawing book](../../docs/rev-b/Foldatron-Rev-B-drawing-book.pdf)
and the separate [assembly traveler](../../docs/rev-b/Foldatron-Rev-B-assembly-traveler.pdf).
The traveler has an ordered operation sequence and spaces for measurements
and inspection signatures. Follow its release holds before the affected work.

## What is supplied

- `cad/foldatron-rev-b.step`: named solid-model development assembly, mm.
- `cad/B*.step`: 34 custom parts with corresponding drawing sheets.
- `cad/B*.dxf`: selected sections 0.5 mm above the bottom face, with DXF
  units explicitly millimetres. This preserves holes below top counterbores.
  DXF is not a complete machining instruction: counterbores, thread depths,
  tolerances and other side operations are in the drawing book.
- `cad/fasteners/`: 17 standard-derived ISO4762 screw envelopes. These are
  project-generated models, not original Bossard CAD or screw manufacturing files.
- `bom.csv` / `bom.json`: purchased parts, individual fastener lengths and
  custom drawings; unresolved electrical items remain visibly on hold.
- `source-register.json`: manufacturer URLs, local-file availability,
  provenance, SHA-256 hashes and licensing scope.
- `vendor-cad-checks.json`: original connector import/topology results.
- `custom-parts.json`: machining features and dimensions used to generate
  both the CAD and drawings.
- `verification.json`: CAD validity, sampled motion clearance and qualified
  mass information. This is computer evidence, not hardware acceptance.
- `assembly-operations.json`: editable assembly-traveler source.

## Decisions and corrections

1. **1010 means 25.4 mm square 80/20.** Four 660.4 mm, eight 508 mm and two
   609.6 mm members total 7,924.8 mm before saw waste. Use 10-series imperial
   hardware, not metric 2020 fittings. All 28 brackets are placed in CAD.
2. **The base is supported.** Two crossmembers support a 500 x 460 x 8 mm
   plate. Recessed fastener seats preserve the intended 3393 screw stack.
3. **Bearings have defined interfaces.** NSK 626 seats are 19 H7, with
   retaining plates, separate inner-race spacers and ground 6 mm shafts.
4. **The yoke is counterbalanced.** Steel weights have independent X/Z
   adjustment. Their final settings depend on the measured dummy/phone and
   wiring; balance must be measured across the whole operating sweep.
5. **The guide interfaces follow the catalogue.** MGN7C mounting is 12 x 8 mm,
   not a generic square pattern. M2 x 6 through the 4 mm plate leaves 2 mm
   engagement against a published 2.5 mm limit. The current catalogue's
   torque table has a conflicting pitch notation; confirm the purchased
   block thread before ordering screws. Maximum block length is modeled.
6. **The motor mount follows the manufacturer drawing.** Case side mounting
   is 12 x 24 mm; the horn bolt circle is 16 mm. Case and horn screw-depth
   limits are explicitly checked.
7. **Angular stops act after the clutch.** A shaft-mounted cam meets two
   adjustable soft-tipped stop screws. Normal cycles stop short of them.
8. **The generic damper is not retained by assumption.** The investigated
   ACE unit is only 0.020 N m and has a stated 50,000-cycle reference life.
   It is not credited with holding the yoke or providing a safety function.
9. **The front guard is tool-removable.** The current issue does not pretend
   to include a validated hinge assembly. The cabinet stands independently
   on the workbench, rather than hanging from an undefined frame bracket.
10. **Two safety relays are proposed.** E-stop and guard have separate
    dual-channel inputs and separate monitored-reset buttons. The reviewed
    terminal diagram is in E-001; final component selection and physical
    acceptance are still P4. Existing software signal polarity is preserved.

11. **The endpoint circuit uses the published microload range.** COM must
    measure 5.00-5.25 V, with 1.8k/2.7k 1% dividers to the Pi. The earlier
    3.3 V/10k circuit is superseded. Do not energize an old circuit from this
    package without checking E-002 and E-005 through E-008.
12. **The interface PCB has a hole-by-hole assembly schedule.** Its 55
    occupied holes and 13 separate nets were checked against the original
    Adafruit EAGLE copper. That check does not validate soldering or hardware.

## Remaining release work

| Hold | Required evidence | Owner / permitted work |
| --- | --- | --- |
| P1 | Measure the actual iPhone Duo; design contact inserts and restraint; verify hinge path and dummy fit | The user directed the shop to measure the phone before machining inserts. No published or guessed phone envelope is a substitute. |
| P2 | Configured Dynatect drawing, exact 6 mm bores, insertion depths, set-screw location, stable low-torque slip; guide block thread confirmation | Obtain supplier configuration data before final shaft flats and clutch purchase. B122 center-bolt clearance must be checked. |
| P3 | Fit-check interlock/key and endpoint mounts, output-side cam actuation, guard access test | B125-B130 define the sensor mounts and cams. Physical actuation, insertion and access tests remain required. |
| P4 | Fit-check E-003/E-009 cabinet layout; qualify selected fuses; finish board mounting/cover, probe housing and locking harness; physical stop/reset/thermal tests | Electrical engineer and shop finish the wiring package and sign measured acceptance. |

The full bench cannot yet be assembled solely from this issue: P1-P4 are real
remaining design work, not optional inspection notes. In particular, the
electrical-completion BOM row is not a purchasable kit. The previous $2,510
planning allowance is not a current quotation for Rev B. Do not place a full
procurement order from it.

## Provenance and reuse

Original downloaded vendor references are kept in ignored `vendor/` and in
the local handoff archive. They retain their manufacturers' copyrights;
the repository MIT license does not cover them. The Pi STEP archive includes
its own MIT license. The Adafruit board grid/placement is CC BY-SA3.0; see
[third-party notices](THIRD-PARTY-NOTICES.md). Other vendor files are internal reference copies, not
relicensed project assets. Public GitHub contains the source URLs and hashes,
project-generated CAD and drawings, and appropriately attributed renders.

80/20's original CAD download requires a PartCommunity account. The present
1010 model has the actual outside/mating envelope but only illustrative slot
reliefs; do not use its volume for extrusion mass or manufacture profile
tooling from it. The manufacturer linear mass is used for stock planning.
The ROBOTIS legacy STEP links returned HTML and were discarded. The actuator,
rails, bearings, collars and enclosure are reconstructed interface models.

Both original Neutrik files import into OpenCascade. The NC4FD-LX original
fails the CAD kernel's overall validity check; it is retained unchanged as
a vendor reference and rendered for recognition. Use its dimensioned PDF
and a physical fit check for the panel interface, not a claim that all its
internal solids are valid. See `vendor-cad-checks.json`.

## Rebuild

CadQuery 2.6.1 and svglib are development-only tools. They are not Raspberry
Pi runtime dependencies. On the Pi install production dependencies with
`pipenv sync`, without `--dev`. A desktop graphics context is needed for the
VTK image-rendering step; the macOS renderer cannot create that context in
some restricted background environments.

```sh
pipenv sync --dev
pipenv run python scripts/fetch_rev_b_sources.py
pipenv run python scripts/build_rev_b_cad.py
pipenv run python scripts/build_rev_b_board.py
pipenv run python scripts/build_rev_b_catalog.py
pipenv run python scripts/build_rev_b_docs.py
pipenv run python scripts/render_rev_b_assembly_views.py
pipenv run python scripts/build_rev_b_docs.py
pipenv run python scripts/check_rev_b_package.py
```

Inspect rendered pages after rebuilding. Source download failures are reported
and do not become silently substituted files. The original Rev A manuals and
interactive viewer remain available as history; they do not represent Rev B.

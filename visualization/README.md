# foldatron / Rev B CAD motion study

Open `index.html` in a current browser with WebGL 2. This single file includes
all geometry, styling and Three.js; rendering needs no server, internet,
account or API key. Drawing and procurement links open GitHub and need internet.

## Explore the bench

- Orbit by dragging; zoom by scrolling or pinching. Five camera presets show
  the complete 1010 bench, mechanism cutaway, endpoints, guard interlock and plan.
- **Motion:** run a 5–175° opening study, set travel speed and endpoint dwell,
  change playback to 1×/2×/4×, and watch cycle count and a 60-second angle trace.
  Pause freezes simulated time and position. Hidden tabs pause advancement.
- **Simulated inputs:** remove the front guard or press the emergency stop.
  Motion halts immediately and the permit latches off. Restore both inputs,
  reset the permit, then explicitly start again. This is a virtual state machine,
  not a prediction of real stopping distance or safety performance.
- **Fit study:** move the radial carriage ±5.7 mm manually. The actual phone
  hinge path remains unmeasured; the shop must measure it before making inserts.
- **Parts:** search 122 CAD instances by part ID or name. Focus an individual
  component, isolate its assembly, inspect material/source/release status, and
  open its custom STEP file or the procurement register.
- **Assembly:** follow all 20 current traveler operations, including part lists,
  instructions and inspection holds. Geometry appears cumulatively by assembly
  operation. Operations 1–2 show the whole model for inventory/drawing review;
  operations after mechanical assembly cover inspection and commissioning.
- **Display:** show/hide panels, reference specimen and datums; separate ten
  assemblies for inspection. Folding is disabled while exploded or in assembly
  mode. Explosion offsets are a presentation arrangement, not removal paths.
- Reset restores the initial mechanism view, recipe, inputs and display layers.

## Geometry and engineering boundaries

The mesh is tessellated directly from `scripts/build_rev_b_cad.py`, the same
CadQuery solids used for the Rev B drawings and STEP assembly: 122 instances,
157,610 triangles, 0.15 mm tessellation tolerance and 0.15 rad angular tolerance.
Machined holes and pockets are actual cut geometry. The 1010 frame is
660.4 × 558.8 × 558.8 mm; the base is 500 × 460 × 8 mm and the hinge axis is
140 mm above the base datum. Coordinates map design (X, Y, Z) to display
(X, Z, −Y). Stored source hashes detect a stale CAD/BOM/traveler export.

Custom parts use the project CAD. Purchased parts use the documented interface
envelopes in that CAD, **not vendor-certified detailed solids**. The reference
phone is not measured Apple geometry. Individual fasteners, wiring, sensors'
internal mechanisms and cabinet internals are not fully modeled. Materials and
lighting aid inspection; rendered colors are not procurement specifications.

The yoke, shafts, output cam, guides and moving phone half rotate about the
output axis. The motor horn/adapter follows the nominal 1:1 drive. Radial offset
moves the float plate, guide blocks and reference moving phone half together.
It does not solve contact or the phone's real hinge trajectory. The front guard
and actuator-key mount withdraw together when the guard input is selected.

The motion study uses a 120 Hz maximum integration step, an **assumed 60°/s²
acceleration/deceleration ramp**, and the chosen travel speed (default 15°/s)
and dwell (default 1 s). A cycle counts after closed and open dwells complete.
Endpoint indicators use nominal thresholds ≤5.5° and ≥174.5°, not cam/contact
collision detection. Playback changes the virtual clock, not commanded speed.
There is no stress, force, motor-current, clutch-slip, gravity, inertia,
backlash, collision, fatigue or hardware-telemetry model.

The displayed 6.665 mm minimum moving Z comes from the existing CAD study
sampled every 5° over 0–180°. It excludes the phone, wiring, screw heads and
switch deflection. Carriage-offset positions are not collision-checked. This
does not establish a safe clearance throughout continuous motion.

P1–P4 release holds remain: phone metrology/contact inserts, configured clutch
interfaces, physical sensor/guard acceptance, and electrical completion/machine
acceptance. Refer to `hardware/rev-b/README.md`. No real machine or phone was
tested. The viewer never connects to or sends commands to the Raspberry Pi;
the Python API simulator and hardware commissioning lockouts are unchanged.

## Rebuild and check

Use the existing Pipenv environment with CadQuery, Node.js 22+ and npm.
Three.js remains the only viewer production dependency; esbuild is the
development bundler. This revision adds no dependencies.

```sh
pipenv sync --dev
pipenv run python scripts/export_rev_b_viewer.py
cd visualization
npm ci
npm run check
npm run build
```

`src/rev-b-model.json` contains the CAD mesh and source metadata.
`src/model.js` creates the display transforms and materials; `src/simulation.js`
contains the independent motion state machine. `src/app.js` connects controls
and rendering. `build.mjs` bundles everything into the checked-in `index.html`.
Three.js attribution is in `THIRD_PARTY_NOTICES.md`.

The ten built-in Node tests cover motion limits, speed, dwells, cycle counting,
pause, both latched inputs, reset/start behavior, presentation changes during
a fault, playback timing, angle conventions, mesh integrity and source hashes.
Browser acceptance checks are recorded in `VERIFICATION.md`.

## Design references

The explorable presentation was inspired by Michael Raspuzzi's
[Lab Automation in 3D](https://github.com/michaelraspuzzi/labautomationin3d) and
[article](https://michaelsmemos.substack.com/p/i-gave-claude-my-x-bookmarks-and).
No reference code, models or artwork were copied.

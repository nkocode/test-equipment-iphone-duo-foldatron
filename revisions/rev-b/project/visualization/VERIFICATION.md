# Rev B viewer verification — 2026-11-06

## Automated checks

- Ten Node tests pass: motion bounds, speed and dwells; complete-cycle counting;
  pause; guard and emergency-stop latches; both-input restoration; explicit
  restart; fault persistence during presentation changes; playback timing;
  opening/axis convention; current source hashes and mesh validity.
- Export contains 122 instances and all 20 traveler operations. Base bounds
  agree with 500 × 460 mm. Output cam rotates; endpoint switches remain fixed.
- Existing Python suite: 25 passed. Ruff passed. OpenAPI regeneration produced
  no schema changes. The existing Starlette/httpx deprecation warning remains.
- Offline build completes with the locked, existing dependencies.

## Browser acceptance

Reviewed in the in-app Chromium browser at 1337 × 1174 and 390 × 844.
These are software/display checks, not physical machine acceptance.

| Check | Observed result |
| --- | --- |
| Default render | Rev B geometry, machined holes, dimensions and cutaway visible |
| Folding at 4× | Closing/opening movement, cycle count and angle history advance |
| Pause | Displayed angle and simulated time stop advancing |
| Guard input while running | Motion stops; Run disabled; removing the fault input alone does not restore Run |
| Emergency-stop input | Fault remains latched after input is released |
| Permit reset | Returns Ready without restarting; explicit Run resumes motion |
| Radial float | Control reaches +5.7 mm and pauses playback |
| Part lookup | B125 resolves to endpoint cam, POM-C material and correct STEP link |
| Assembly isolation | Only the selected endpoint assembly remains; heading names that assembly |
| Assembly traveler | All 20 selections return the corresponding operation title and text |
| Assembly render | Lower rectangle at operation 3; cam and slotted mounts at operation 14 |
| Exploded view | Assemblies separate at 60%; folding controls disabled |
| Guard removal view | Front panel/key withdraw from fixed switch mount; reset restores default |
| Reset | Restores recipe, angle, mode, camera, inputs, layers and part selection |
| Mobile | Page width equals 390 px viewport; controls and part lookup remain usable |
| Console | No warnings or errors reported during final browser review |

## Remaining engineering work

This viewer uses the existing development-review geometry and preserves P1–P4.
It does not resolve supplier interfaces, phone metrology, continuous collision
clearance, real stopping behavior or electrical acceptance. The simulated
sensor states are nominal angle thresholds. See the viewer README and Rev B
release table for exact limits.

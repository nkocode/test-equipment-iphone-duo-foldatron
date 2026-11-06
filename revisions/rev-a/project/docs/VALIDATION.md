# Validation evidence and limits

Date: 4 November 2026. Execution host: local macOS, Python 3.12.14, Pipenv-managed environment. No physical Raspberry Pi, servo or phone was connected.

## Passed locally

- 25 automated tests: authenticated API access; request bounds; generated security schema; durable complete-cycle count; CSV/JSON pagination; idempotent retries; exclusive run ownership; concurrent starts; latched stop; no partial-cycle increment; permit/temperature/current faults; inspection pass/resume and fail termination; manual pause/stop; endpoint jog; jam timeout; stuck sensor; crash recovery; process lock; missing-key rejection; probe CRC/range; database failure; servo register write ordering; commissioned-limit checks; communication errors; rejected illegal goals; uncoupled index current/speed limits, permit gating and final torque disable.
- Ruff style/import/error checks, configured for PEP 8-compatible 79-character lines.
- A real local Uvicorn HTTP run: authenticated POST, status polling, completed simulated cycle, saved run result and exact equality between live and exported OpenAPI schemas.
- Dependency resolution and installation through Pipenv; committed-to-deliverable lockfile records package versions and hashes.
- Source-layout migration: `src/foldbench` installed through Pipenv in editable mode, with no pytest import-path override; wheel and source distributions built, and wheel import/API schema checked from outside the checkout.
- Assembly and wiring SVGs rendered for visual inspection. OpenSCAD source supplied as an envelope/plate-template model; no OpenSCAD executable was available for mesh rendering or collision verification.

The test runner reports one upstream Starlette warning about future httpx test-client deprecation. It does not prevent the current tests from passing. The delivered dependencies remain locked; review this warning when upgrading them.

## Not established by these checks

GPIO operation on the selected Pi/kernel, 1-Wire timing with actual probes, DYNAMIXEL serial behavior under real electrical faults, actual clutch torque, alignment, phone clearance, stopping distance, fixture wear, cycle-counter accuracy under physical slip, hardware temperature thresholds, continuous-duty endurance, safety-circuit performance and handset functional health remain unverified. Driver register tests use a fake transport and cannot validate actuator behavior.

The setup indexing utility must be exercised only with the motor mechanically uncoupled and no phone. Its physical effect is unverified. The software's local commissioning record is a lockout mechanism, not proof that an engineer performed the checks.

See COMMISSIONING.md for the physical evidence required before phone trials. No deployment was made to a Raspberry Pi, and the temporary HTTP smoke-test process was stopped after verification.

# foldatron Rev C - purchased-component redesign

**C-0.3 development review. Not released for procurement, assembly or powered
phone testing.** Full natural closure remains required. The actual phone is
measured by the shop; the CAD phone leaves are explicitly illustrative.

This revision uses purchased 1010 extrusion, a Thorlabs breadboard and mounting
parts, a Zaber rotary stage, a factory plain Del-Tron XY stage and four Festo
outside-surface vacuum contacts. No custom machining, drilled adapters,
printed structural parts or custom circuit boards are specified. Supplier
cuts and standard factory configurations are permitted.

The current delivery prioritizes mechanical review and the public viewer.
Further software implementation and hardware integration are deferred. Existing
software work is preserved below; it is not physically commissioned.

## Current materials

- [Technical drawing book](docs/Foldatron-Rev-C-drawing-book.pdf)
- [Separate illustrated assembly manual](docs/Foldatron-Rev-C-assembly-manual.pdf)
- [Interactive whole-bench and fixture viewer](visualization/index.html)
- [Bench STEP](hardware/cad/bench-development.step)
- [Fixture STEP](hardware/cad/fixture-development.step)
- [Purchased parts and explicit holds](hardware/assembly-parts.tsv)
- [Fastener schedule](docs/fastener-schedule.md)
- [Point-to-point electrical installation](docs/electrical-installation.md)
- [Pneumatic circuit and hose schedule](docs/pneumatic-installation.md)
- [Phone measurement traveler](docs/phone-measurement-traveler.md)
- [Design release and physical qualification register](docs/release-register.json)
- [Vendor source URLs, file sizes and hashes](hardware/sources.json)
- [Raspberry Pi installation and operation](software/README.md)
- [Hardware OpenAPI](software/openapi-hardware.json)
- [Simulation OpenAPI](software/openapi-simulation.json)

The 83-component bench model and 27-component fixture are more detailed than
the C-0.2 structure study, but they omit several required mounts, fasteners
and hose routes. The parts table identifies selections, candidates and open
order codes; it is not presented as a complete purchase BOM. Eleven design
holds remain in the release register, independently of physical commissioning.
The earlier C-0.2 PDF is retained as a superseded development record.

## Software and revision ownership

The maintained Python package uses the repository's `src/foldbench/revc/`
source layout. Use `python -m foldbench.revc`; the older `foldbench` entry
point still operates the earlier actuator architecture. A self-contained
runtime source copy is provided under `software/project/`, with its lock,
tests and license, so this revision can be obtained independently.

The default is simulation. Hardware enablement requires a local commissioning
record and verifies device identities and configuration. The API provides
runs, jogs, pause/resume/stop, telemetry, inspections and durable results.
It does not remotely reset the safety controller, vent cups, change local
commissioning limits or prove physical stop performance. The public gallery
hosts documentation and a browser motion study, not the equipment API.

Rev A and Rev B remain byte-exact snapshots in their adjacent revision folders.

## Rebuild and inspect

Use the existing Pipenv development environment on a workstation. Runtime
installation on the Pi does not require CAD or PDF development dependencies.

```sh
pipenv sync --dev
pipenv run python revisions/rev-c/scripts/fetch_sources.py
pipenv run python revisions/rev-c/scripts/build_fixture.py
pipenv run python revisions/rev-c/scripts/build_bench.py
pipenv run python revisions/rev-c/scripts/build_assembly_views.py
pipenv run python revisions/rev-c/scripts/check_guard.py
pipenv run python revisions/rev-c/scripts/check_fixture_sweep.py --step 15
pipenv run python revisions/rev-c/scripts/build_handoff.py
node revisions/rev-c/visualization/build.mjs
pipenv run lint
pipenv run test
pipenv run schema
pipenv run python revisions/rev-c/scripts/package_review.py
```

The viewer uses the already-approved Three.js and existing workstation build
tooling in `visualization/node_modules`. No new production dependency was
added for Rev C. Fetching vendor files can fail if a supplier changes its
URLs or bytes; the script fails instead of accepting a changed drawing.
Vendor originals remain in the ignored `hardware/vendor/` cache. Their URLs
and hashes travel with the repository; this does not grant a redistribution
license. Reconstructed geometry is labeled separately from original CAD.

# foldatron / FoldBench - iPhone Duo endurance tester

**Revision library:** [Rev A — original concept](revisions/rev-a/),
[Rev B — drawing CAD and motion study](revisions/rev-b/), and
[Rev C — catalog-only redesign](revisions/rev-c/).
Rev A and Rev B are complete frozen source snapshots with file hashes.
The [revision gallery](https://foldatron-evolution.nathanota.chatgpt.site)
provides separate revision pages, with the preserved Rev A/Rev B interactive
viewers and downloadable Rev C engineering checkpoints.

**Latest Rev C checkpoint: C-0.2.** Full natural closure is required; edge
clamps are rejected. The [14-sheet drawing review](revisions/rev-c/docs/Foldatron-Rev-C-structure-and-interface-review.pdf)
and [phone measurement traveler](revisions/rev-c/docs/phone-measurement-traveler.md)
record the purchased-part direction and remaining release gates. This is
not yet a complete assembly package or a working Rev C hardware driver.

An original prototype inspired by CNET's Fold-A-Phone video. Includes hardware design, a complete procurement/fabrication BOM, assembly and commissioning instructions, Python Raspberry Pi controller, FastAPI REST API, generated OpenAPI 3.1 specification and automated tests.

foldatron is the repository name; `foldbench` is the Python package and service name. The project is licensed under the existing [MIT license](LICENSE).

**Default mode is simulation. Hardware has not been physically validated.** The design is for supervised commissioning and testing; read the guide before fabrication or connecting an actuator. A mechanically completed run is not an automatic phone-function pass.

Start the current mechanical review with the [Rev B engineering package](hardware/rev-b/README.md), its [CAD drawing book](docs/rev-b/Foldatron-Rev-B-drawing-book.pdf), and separate [assembly traveler](docs/rev-b/Foldatron-Rev-B-assembly-traveler.pdf). Rev B uses 1010 one-inch extrusion, dimensioned custom STEP parts, DXF profiles, individual fastener lengths and a hashed vendor-source register. P1-P4 still prevent a complete fabrication/commissioning release; the shop will measure the actual phone before machining inserts. The earlier [illustrated manual](docs/Foldatron-illustrated-assembly-manual.pdf), and envelope model describe Rev A and are retained as history.

## Interactive 3D explorer

The explorer now uses the **Rev B drawing CAD**: 122 instances across ten assemblies, with machined holes, bearing seats, guide carriages, endpoint cam and guard mounts.

Download and open [visualization/index.html](visualization/index.html) in a browser. The single-file viewer works offline and includes orbit/zoom, part selection and STEP links, a 5–175° motion study, adjustable speed/dwell, cycle history, latched simulated guard/E-stop inputs, radial carriage adjustment, an exploded view and the current 20-operation assembly traveler. It is a kinematic visualization, not a physics simulation or live machine interface. See the [viewer guide](visualization/README.md) for scope and rebuilding.

## Files

- `docs/DESIGN_AND_ASSEMBLY.md`: design rationale, dimensions, wiring and assembly.
- `hardware/BOM.md` and `hardware/BOM.json`: quantities, specifications, allowances, procurement links.
- `hardware/layout.svg`: dimensioned assembly overview.
- `hardware/wiring.svg`: power and signal architecture.
- `hardware/foldbench.scad`: parametric assembly envelope and plate templates.
- `hardware/calibration.example.json`: uncommissioned installation limits.
- `docs/COMMISSIONING.md`: physical acceptance checklist.
- `docs/API.md`: endpoint behavior, error semantics and pagination.
- `openapi.json`: schema generated directly from the application.
- `src/foldbench/`: installable Python application, real servo/GPIO/probe driver and simulator.
- `deploy/`: service and environment examples for a Raspberry Pi.
- `tests/`: simulation/API and register-level driver tests.
- `scripts/`: BOM/manual generation, live HTTP check, wheel check and ZIP packaging.
- [Printable manual](docs/FoldBench-design-and-assembly.pdf): design, BOM, assembly and operation in one document.
- [Illustrated assembly companion](docs/Foldatron-illustrated-assembly-manual.pdf): 36-page step-by-step bench construction and commissioning booklet.
- [Assembly source and editable SVGs](docs/assembly/README.md): illustrated operations, part register, wire schedule and manufacturer references.

## Source layout

Application modules live under `src/foldbench/`, with package metadata in `pyproject.toml`. Pipenv installs this local package in editable mode. Tests exercise the installed package; they do not add the checkout or `src` to Python's import path. The same `python -m foldbench` command works outside the repository once installed. Tests, documentation, hardware files and deployment examples remain outside the Python import package.

Rev B is the current engineering review package. Its 1010 frame, fixture,
sensor mounts and corrected endpoint wiring supersede the corresponding
Rev A illustrations. The interactive viewer uses the same Rev B geometry.
See [the Rev B release boundary](hardware/rev-b/README.md) before purchasing
or fabricating; phone metrology and supplier/physical acceptance are open.

## Run the simulator

Use Python 3.12 and Pipenv. Runtime dependencies remain FastAPI, Uvicorn and the ROBOTIS SDK, with their transitive dependencies. Packaging, test and document-generation tools are development-only. Versions and hashes are in Pipfile.lock. No GPIO package is required: the real driver uses Linux's GPIO character-device ABI.

From this directory:

```sh
PIPENV_VENV_IN_PROJECT=1 pipenv sync --dev
export FOLDBENCH_API_KEY="$(pipenv run python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export FOLDBENCH_MODE=simulation
pipenv run test
pipenv run serve
```

Open http://127.0.0.1:8000/docs and authorize with your generated `X-API-Key`. Use `GET /v1/status`, then `POST /v1/runs` with a unique `Idempotency-Key` and a body such as `{"specimen":"Duo-demo","cycles":3,"dwell_s":1}`. Default real-time simulation takes roughly 75 seconds for three cycles. Inspect the run, samples and CSV through the documentation UI. Stop the server with Ctrl-C.

`GET /health` is liveness only. Readiness and faults are in `/v1/status`. The API is intentionally bound to localhost by default. For remote access, use an SSH tunnel, or set a specific private LAN bind address with TLS configured. Keep the API off the public internet. There is no deployment to your Pi in this delivery: no Pi connection was supplied.

## Raspberry Pi installation

Use Pi 5, 4 GB, active cooling, official 27 W supply, 64-bit Raspberry Pi OS, a high-endurance card or SSD, and Python 3.12. Install Pipenv with the OS package manager or your existing tool manager. If the OS supplies a different Python version, install 3.12 before syncing this locked environment, or deliberately re-lock and re-test for the chosen version.

Copy the application to `/opt/foldbench`, create the `foldbench` service account, create `/var/lib/foldbench` owned by it, and build the virtual environment there with Pipenv. Grant that account access to `dialout` and `gpio`, not unrestricted root access. Confirm the serial port's persistent `/dev/serial/by-id/` name and GPIO chip/header mapping. Enable 1-Wire on GPIO4 and record both probe serial numbers.

Copy the environment example to `/etc/foldbench.env`, set a unique key, actual device paths, and the absolute calibration path. Restrict the file to root and the service group. Use the supplied systemd unit after completing the physical checks. Run exactly one worker and no reload mode. A failed service restart never resumes an old test.

The hardware driver expects XM430-W350-T ID 1 at 57600 baud, protocol 2, firmware 38+. It requires independent endpoint switches, safety-permit input and both temperature probes. Missing hardware causes a fault; the program never silently substitutes simulation.

## Validation

Run `pipenv run test`, `pipenv run lint`, and `pipenv run schema`. Compare a regenerated `openapi.json` with the distributed copy after API changes. Review `docs/VALIDATION.md` for the checks performed and the physical checks still outstanding.

`pipenv run package` builds a wheel and source archive. `pipenv run python scripts/check_wheel.py` verifies that the wheel imports and builds the API schema outside the source checkout. `pipenv run smoke` starts a temporary localhost server, completes a simulated cycle, checks the schema and shuts down. GitHub Actions runs these checks on pushes and pull requests.

## Rebuild design deliverables

Edit `hardware/BOM.json`, then run `pipenv run bom` to update totals and the readable table. Run `pipenv run manual` to rebuild the PDF from the repository documentation and `docs/assets/` images. The generator uses fonts distributed with ReportLab and has no machine-specific font paths. If an SVG changes, regenerate its matching PNG in `docs/assets/` using `rsvg-convert` or another SVG renderer before rebuilding the manual, then visually review the PDF.

`pipenv run bundle` creates `artifacts/FoldBench-complete-package.zip` from Git-tracked files, including the PDF. Stage new files before bundling. GitHub's **Code > Download ZIP** also provides the complete repository. Virtual environments, credentials, test databases, caches and generated distribution archives are excluded from version control.

`pipenv run assembly-manual` rebuilds the separate illustrated assembly PDF, Markdown instructions and SVG drawings from `docs/assembly/steps.json` and `scripts/build_assembly_guide.py`. It uses the existing development dependencies. Review all rendered pages after changes; the generator checks text/table space, not mechanical fit or electrical correctness.

The code logs motor-derived angle and current as observations, not calibrated hinge torque or display-health measurements. Complete the commissioning checklist with an empty rig and dummy before testing the phone.

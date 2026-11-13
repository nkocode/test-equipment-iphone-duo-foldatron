# Rev C Raspberry Pi service

Use a Raspberry Pi 3B headless. Its USB and Ethernet interfaces are sufficient
for this supervisory workload; deterministic stops belong to the independent
wired controller. A Pi 5 is optional, not required. The 3B's 1 GB RAM is not
intended to build CAD or run the browser renderer. Build drawings on a workstation.
Use a supported 64-bit Linux image and Python 3.12 or later. The original Pi
models with ARMv6 CPUs are not the deployment target of this environment.

From the repository root, install the locked runtime with Pipenv. CAD and PDF
packages are development dependencies and are not needed on the Pi.

```sh
pipenv sync
export FOLDATRON_C_API_KEY="$(pipenv run python -c 'import secrets; print(secrets.token_urlsafe(32))')"
pipenv run python -m foldbench.revc
# In another terminal, retain the same API key:
curl -H "X-API-Key: $FOLDATRON_C_API_KEY" http://127.0.0.1:8001/v1/status
# Export both current contracts without connecting equipment:
pipenv run python -m foldbench.revc.export_schema
```

The default is simulation, loopback port 8001. Interactive API documentation
is at `/docs`, schema at `/openapi.json`. Saved hardware and simulation
OpenAPI specifications are included here. All `/v1` routes require the key;
`/health` is only process liveness. Do not put the key in the repository or URL.
Use a trusted local network or authenticated tunnel for remote access; do not
publish the equipment API on the public revision-gallery site.

## Operation

1. Read status and the local commissioning record. Check telemetry freshness,
   hardwired permit, all four cup permissives and phone temperature.
2. Start a run with `POST /v1/runs`, a `sample_id`, cycle count, speed and dwell,
   and an `Idempotency-Key` header. Repeating the same key/body returns the
   original run. Changing the body with the same key returns a conflict.
3. A cycle is counted after a completed close/open pair. A partial cycle on a
   fault, stop or reboot is not counted. Pause finishes the current full cycle
   and leaves the fixture open. Resume requires an explicit request.
4. `/v1/stop` latches a protective-stop request without waiting for the serial
   lock. Its 202 response is an acknowledgment, not proof that motion stopped.
   Poll status. Use the physical E-stop when independent power removal is needed.
5. After a fault, restore physical conditions and reset the hardwired controller
   locally. `/v1/reset` verifies healthy stationary state and clears only the
   software fault. The interrupted run stays ended.
6. Results are stored in SQLite with durable run, sample, event and inspection
   records. Download paginated records or CSV; continue with `X-Next-After`.
   A process restart faults unfinished runs and never resumes them.

Simulation exposes `/v1/simulation/fault` for vacuum, permit, temperature and
communication faults. That route is absent from the hardware app and schema.
The simulated phone is a surrogate, and the 3D viewer is separate from this API.

## Hardware enablement

Copy `commissioning.example.json` to a local protected location, complete the
shop traveler and record the measured endpoints, approved speed/current,
serial identities and acceptance evidence. The example is deliberately
unreleased. Setting `released=true` alone is rejected. No remote API can edit
these values. The application cannot authenticate a human's recorded physical
test results; ownership and review of this file are the shop's responsibility.

Set `FOLDATRON_C_MODE=hardware`, `FOLDATRON_C_COMMISSIONING` to that file,
`FOLDATRON_C_STAGE_PORT` and `FOLDATRON_C_IO_PORT` to stable adapter paths,
and `FOLDATRON_C_DATA` to a writable persistent directory. Permit the service
account to use those serial devices. Configure vendor devices exactly as
[protocols.md](protocols.md) specifies, with the phone removed during setup.

The supplied systemd unit uses one worker, an environment file, a restart delay
and a private writable data directory. Install only after simulation and empty
fixture acceptance. A service restart does not clear the physical stop circuit.

## Limits of the measurements

Opening angle is normalized between the commissioned motor endpoints. It is
not a direct phone-angle measurement. This version does not measure hinge
force or torque. Vacuum inputs report threshold states, not analog pressure.
An unpowered worm drive may retain force. Vacuum leakage can eventually release
a phone despite check valves. The shop must validate retention, allowable loads,
hose drag, full closure and safe recovery with a representative sacrificial unit.

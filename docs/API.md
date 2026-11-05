# REST API contract

Base URL: `http://127.0.0.1:8000` by default. Use HTTPS or an SSH tunnel for remote clients. API key header: `X-API-Key`. Only health, interactive documentation and schema are public; they expose no run data or control actions.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | /health | Process liveness, not equipment readiness |
| GET | /v1/status | Controller state, last/current run, last valid telemetry |
| GET | /v1/calibration | Read-only installation/commissioning limits |
| GET | /v1/telemetry | Latest observation; 503 when unavailable |
| POST | /v1/runs | Start a validated recipe; requires Idempotency-Key |
| GET | /v1/runs | Paginated history, limit and offset |
| GET | /v1/runs/{id} | Run state, recipe, calibration, confirmed count |
| POST | /v1/runs/{id}/pause | Request pause at the next completed cycle |
| POST | /v1/runs/{id}/resume | Resume a paused, inspected run |
| POST | /v1/runs/{id}/stop | End the active run and disable torque |
| POST | /v1/runs/{id}/inspections | Record pass/fail and notes while paused |
| POST | /v1/jogs | Move to a commissioned open/closed endpoint at 5 deg/s |
| POST | /v1/stop | Latched protective-stop request, including jogs |
| POST | /v1/reset | Acknowledge a resolved fault; no motion |
| GET | /v1/runs/{id}/samples | Sample page, after sequence and limit |
| GET | /v1/runs/{id}/samples.csv | CSV page, X-Next-After response cursor |
| GET | /v1/runs/{id}/events | Event/inspection page, after sequence and limit |
| GET | /openapi.json | Generated OpenAPI 3.1 specification |
| GET | /docs | Interactive API documentation |

## Start recipe

Required field: `specimen` (1-100 characters). Optional fields: `cycles` (integer 1-10,000,000; default 100), `speed_deg_s` (1-30; default 15), `dwell_s` (0.25-60; default 1), `current_limit_ma` (20-350; default 150), `inspection_every` (1-10,000; default 1,000). Local calibrated limits can be tighter and take precedence. Unknown fields and nonfinite numeric values are rejected.

The start request's `Idempotency-Key` must be 8-128 letters/digits/underscores/dots/hyphens. Use a new UUID for a deliberately new run. Repeating the same key and recipe returns the same run, including after restart; changing the recipe with that key returns 409. Never retry an uncertain start with a new key until reading status/history.

The run begins by confirming the open endpoint; that initial opening is not a cycle. A cycle is counted only after a subsequent confirmed closed endpoint and return to open. Each endpoint requires both a motor encoder tolerance and its independent switch, stable for 150 ms. Both switches high, or a switch active far from its calibrated encoder position, faults the run. Mode is always explicitly `simulation` or `hardware` in records.

## State semantics

Controller states: idle, running, paused, jogging, faulted. Historical run states: running, paused, completed, stopped, faulted, interrupted. `active_run` in status contains the most recent run, including its terminal state, so it can be inspected after completion. Check controller state to determine ownership/readiness.

A pause request completes the current cycle and then removes torque. Automatic inspection pauses require a `pass` record before resume. A `fail` inspection faults the run. Resume reestablishes open position before beginning the next cycle; it does not increment a partial cycle. A terminal stopped/faulted/interrupted run cannot be resumed; start a new run after inspection and any required reset.

`POST /v1/stop` returns 202 immediately after requesting a latched stop. Poll status for the actual outcome. It is not an emergency-stop device. If a bus or controller call hangs, use the physical E-stop. A bus-watchdog fault requires inspecting the mechanism and cycling motor power before reset. Hardware reset does not bypass guard, temperature, position or other readiness checks.

## Records and export

Samples are normally stored once per second plus endpoint observations; timestamps are UTC. Motor current is signed mA, angle is estimated from the motor encoder and local calibration, and temperatures are Celsius. Endpoint sensors verify position at endpoints only. Motor angle can diverge from phone angle between endpoints if the clutch slips or a clamp moves.

For complete JSON/CSV export, request pages until an empty page: `limit` defaults to 1,000, maximum 10,000; the next `after` is the last returned `seq`, or CSV's `X-Next-After`. CSV repeats its header per page. Sequence numbers are database-global, so gaps within a run are normal. Downloading during a run produces an evolving dataset; finish/stop first for a stable export. Results remain local in SQLite; no cloud upload is performed.

A crash after physical motion but before a confirmed-cycle commit may undercount the last cycle. On startup, all previously running/paused records are marked interrupted and retain their committed count. Backup the database with SQLite's backup facility, not a bare copy of a live database that omits its WAL.

## HTTP responses

200: read/control result. 201: created or idempotently replayed start. 202: asynchronous stop/jog request accepted. 401: missing/incorrect key. 404: unknown run. 409: ownership, calibration, safety state or controller conflict. 422: invalid input. 503: no valid telemetry. Detailed schemas and response models are in openapi.json. Do not interpret HTTP 200/201/202 alone as a mechanical pass or proof of zero motion.

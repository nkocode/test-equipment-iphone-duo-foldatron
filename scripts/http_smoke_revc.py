"""Exercise Rev C over a real localhost socket, including crash recovery."""

import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    key = secrets.token_urlsafe(32)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    with tempfile.TemporaryDirectory(prefix="foldatron-revc-http-") as data:
        env = dict(os.environ, FOLDATRON_C_API_KEY=key,
                   FOLDATRON_C_DATA=data, FOLDATRON_C_MODE="simulation",
                   FOLDATRON_C_PORT=str(port))

        def launch():
            return subprocess.Popen(
                [sys.executable, "-m", "foldbench.revc"], env=env, cwd=data,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

        def request(path, body=None, authenticated=True, idem=None):
            headers = {"Content-Type": "application/json"}
            if authenticated:
                headers["X-API-Key"] = key
            if idem:
                headers["Idempotency-Key"] = idem
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}", headers=headers,
                data=None if body is None else json.dumps(body).encode(),
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.load(response)

        def ready(process):
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Rev C service exited before readiness")
                try:
                    if request("/v1/status")["telemetry"] is not None:
                        return
                except (OSError, urllib.error.URLError):
                    pass
                time.sleep(0.05)
            raise TimeoutError("No fresh startup telemetry")

        process = launch()
        try:
            ready(process)
            assert request("/health", authenticated=False)["revision"] == "C"
            try:
                request("/v1/status", authenticated=False)
            except urllib.error.HTTPError as error:
                assert error.code == 401
            else:
                raise AssertionError("Unauthenticated state read succeeded")
            body = {"sample_id": "live-http-surrogate", "cycles": 1}
            first = request("/v1/runs", body, idem="live-http-c")
            again = request("/v1/runs", body, idem="live-http-c")
            assert again["id"] == first["id"]
            assert request("/openapi.json") == json.loads(
                (ROOT / "revisions/rev-c/software/"
                 "openapi-simulation.json").read_text())
            process.kill()
            process.wait(timeout=10)
            process = launch()
            ready(process)
            run = request("/v1/runs/" + first["id"])
            assert run["state"] == "faulted", run
            assert run["completed_cycles"] == 0, run
            state = request("/v1/status")
            assert state["telemetry"]["moving"] is False
            print("PASS: real HTTP auth, idempotency, schema and crash "
                  "recovery; no automatic resumption or partial cycle count")
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()

"""Live localhost test; no physical hardware and no persistent secrets."""

import json
import os
import secrets
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
    with tempfile.TemporaryDirectory(prefix="foldbench-smoke-") as data:
        env = dict(
            os.environ,
            FOLDBENCH_API_KEY=key,
            FOLDBENCH_DATA=data,
            FOLDBENCH_MODE="simulation",
            FOLDBENCH_HTTP_PORT="8087",
        )
        process = subprocess.Popen(
            [sys.executable, "-m", "foldbench"],
            env=env,
            cwd=data,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        def request(path, body=None, headers=None):
            request_headers = {
                "X-API-Key": key,
                "Content-Type": "application/json",
            }
            request_headers.update(headers or {})
            req = urllib.request.Request(
                "http://127.0.0.1:8087" + path,
                data=None if body is None else json.dumps(body).encode(),
                headers=request_headers,
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                return json.load(response)

        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("HTTP server exited before readiness")
                try:
                    request("/health")
                    break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.1)
            run = request(
                "/v1/runs",
                {"specimen": "HTTP-smoke", "cycles": 1, "dwell_s": 0.25},
                {"Idempotency-Key": "live-http-smoke"},
            )
            deadline = time.monotonic() + 40
            while time.monotonic() < deadline:
                result = request("/v1/runs/" + run["id"])
                if result["state"] == "completed":
                    break
                time.sleep(0.25)
            assert result["state"] == "completed", result
            assert result["completed_cycles"] == 1
            assert request("/openapi.json") == json.loads(
                (ROOT / "openapi.json").read_text()
            )
            print(
                "PASS: Live HTTP authenticated start, polling, completed "
                "cycle, persisted result and exported schema match"
            )
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()

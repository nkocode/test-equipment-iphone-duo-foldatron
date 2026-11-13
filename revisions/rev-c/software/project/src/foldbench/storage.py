"""Durable records; each confirmed cycle commits before the next stroke."""

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .models import Run, Telemetry


def utc_now():
    return datetime.now(UTC).isoformat()


class Store:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript(
            "CREATE TABLE IF NOT EXISTS runs "
            "(id TEXT PRIMARY KEY, body TEXT NOT NULL);"
            "CREATE TABLE IF NOT EXISTS samples "
            "(seq INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id TEXT NOT NULL, body TEXT NOT NULL);"
            "CREATE INDEX IF NOT EXISTS sample_run ON samples(run_id, seq);"
            "CREATE TABLE IF NOT EXISTS events "
            "(seq INTEGER PRIMARY KEY AUTOINCREMENT, "
            "run_id TEXT, at TEXT NOT NULL, kind TEXT NOT NULL, body TEXT);"
            "CREATE TABLE IF NOT EXISTS requests "
            "(key TEXT PRIMARY KEY, run_id TEXT NOT NULL, recipe TEXT);"
        )
        self.db.commit()

    def recover(self):
        rows = self.db.execute("SELECT body FROM runs").fetchall()
        for (body,) in rows:
            run = Run.model_validate_json(body)
            if run.state in {"running", "paused"}:
                run.state = "interrupted"
                run.phase = "requires_inspection"
                run.fault = "Service restarted; no automatic resumption"
                self.save(run)
                self.event(run.id, "restart_interrupted", {})

    def save(self, run: Run):
        run.updated_at = utc_now()
        self.db.execute(
            "INSERT OR REPLACE INTO runs VALUES (?, ?)",
            (run.id, run.model_dump_json()),
        )
        self.db.commit()

    def create_run(self, run, key):
        with self.db:
            self.db.execute(
                "INSERT INTO runs VALUES (?, ?)",
                (run.id, run.model_dump_json()),
            )
            self.db.execute(
                "INSERT INTO requests VALUES (?, ?, ?)",
                (key, run.id, run.recipe.model_dump_json()),
            )

    def request(self, key):
        return self.db.execute(
            "SELECT run_id, recipe FROM requests WHERE key=?", (key,)
        ).fetchone()

    def get(self, run_id):
        row = self.db.execute(
            "SELECT body FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
        return Run.model_validate_json(row[0]) if row else None

    def runs(self, limit=100, offset=0):
        rows = self.db.execute(
            "SELECT body FROM runs ORDER BY rowid DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [Run.model_validate_json(row[0]) for row in rows]

    def sample(self, run_id: str, telemetry: Telemetry):
        self.db.execute(
            "INSERT INTO samples(run_id, body) VALUES (?, ?)",
            (run_id, telemetry.model_dump_json()),
        )
        self.db.commit()

    def samples(self, run_id: str, after: int, limit: int):
        return [
            {"seq": seq, **json.loads(body)}
            for seq, body in self.db.execute(
                "SELECT seq, body FROM samples WHERE run_id=? AND seq>? "
                "ORDER BY seq LIMIT ?",
                (run_id, after, limit),
            )
        ]

    def event(self, run_id, kind, body):
        self.db.execute(
            "INSERT INTO events(run_id, at, kind, body) VALUES (?, ?, ?, ?)",
            (run_id, utc_now(), kind, json.dumps(body)),
        )
        self.db.commit()

    def events(self, run_id, after=0, limit=1000):
        return [
            {"seq": seq, "at": at, "kind": kind, "body": json.loads(body)}
            for seq, at, kind, body in self.db.execute(
                "SELECT seq, at, kind, body FROM events "
                "WHERE run_id=? AND seq>? ORDER BY seq LIMIT ?",
                (run_id, after, limit),
            )
        ]

    def close(self):
        self.db.close()

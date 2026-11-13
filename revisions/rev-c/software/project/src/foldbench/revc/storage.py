"""Durable run, event and sample journal, owned by the controller lock."""

import json
import sqlite3
import time

from .models import Run


class Store:
    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, idem TEXT UNIQUE, body TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS records (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT, kind TEXT NOT NULL, body TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS records_run ON records(run_id, seq);
        """)
        for row in self.db.execute("SELECT id, body FROM runs").fetchall():
            run = Run.model_validate_json(row[1])
            if run.state in {"running", "paused"}:
                run.state = "faulted"
                run.ended_at = time.time()
                run.detail = "Process restarted; no automatic resumption"
                self.save(run)
                self.record(run.id, "event", {"detail": run.detail})

    def save(self, run, idem=None):
        if idem:
            self.db.execute(
                "INSERT INTO runs VALUES (?, ?, ?)",
                (run.id, idem, run.model_dump_json()),
            )
        else:
            self.db.execute(
                "UPDATE runs SET body=? WHERE id=?",
                (run.model_dump_json(), run.id),
            )
        self.db.commit()

    def get(self, run_id):
        row = self.db.execute(
            "SELECT body FROM runs WHERE id=?", (run_id,)
        ).fetchone()
        return Run.model_validate_json(row[0]) if row else None

    def by_key(self, key):
        row = self.db.execute(
            "SELECT body FROM runs WHERE idem=?", (key,)
        ).fetchone()
        return Run.model_validate_json(row[0]) if row else None

    def runs(self, limit, offset):
        return [
            Run.model_validate_json(row[0])
            for row in self.db.execute(
                "SELECT body FROM runs ORDER BY rowid DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        ]

    def record(self, run_id, kind, body):
        payload = {"recorded_at": time.time(), **body}
        self.db.execute(
            "INSERT INTO records(run_id, kind, body) VALUES (?, ?, ?)",
            (run_id, kind, json.dumps(payload)),
        )
        self.db.commit()

    def records(self, run_id, kind, after, limit):
        rows = self.db.execute(
            "SELECT seq, body FROM records WHERE run_id=? AND kind=? "
            "AND seq>? ORDER BY seq LIMIT ?",
            (run_id, kind, after, limit),
        )
        return [{"seq": row[0], **json.loads(row[1])} for row in rows]

    def close(self):
        self.db.close()

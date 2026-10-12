"""SQLite storage for endpoints and historical check results."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "monitor.db"


def connect(db_path=None):
    connection = sqlite3.connect(str(db_path or DB_PATH), timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path=None):
    with connect(db_path) as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS endpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            method TEXT NOT NULL DEFAULT 'GET',
            expected_status INTEGER NOT NULL DEFAULT 200,
            contains_text TEXT NOT NULL DEFAULT '',
            enabled INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint_id INTEGER NOT NULL REFERENCES endpoints(id) ON DELETE CASCADE,
            checked_at TEXT NOT NULL,
            status_code INTEGER,
            response_ms REAL NOT NULL,
            healthy INTEGER NOT NULL,
            error TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_results_endpoint_time
        ON results(endpoint_id, checked_at);
        """)


def list_endpoints(db_path=None):
    with connect(db_path) as con:
        return [dict(r) for r in con.execute("SELECT * FROM endpoints ORDER BY name")]


def add_endpoint(name, url, method="GET", expected_status=200, contains_text="", db_path=None):
    from .checker import validate_url
    url = validate_url(url)
    if not name.strip():
        raise ValueError("Name is required")
    if method not in ("GET", "HEAD"):
        raise ValueError("Only GET and HEAD are supported")
    if not 100 <= int(expected_status) <= 599:
        raise ValueError("HTTP status must be between 100 and 599")
    with connect(db_path) as con:
        cur = con.execute("INSERT INTO endpoints(name,url,method,expected_status,contains_text) VALUES(?,?,?,?,?)",
                          (name.strip(), url, method, int(expected_status), contains_text))
        return cur.lastrowid


def update_endpoint(endpoint_id, name, url, method, expected_status, contains_text, enabled, db_path=None):
    from .checker import validate_url
    url = validate_url(url)
    if not name.strip() or method not in ("GET", "HEAD") or not 100 <= int(expected_status) <= 599:
        raise ValueError("Invalid endpoint settings")
    with connect(db_path) as con:
        con.execute("UPDATE endpoints SET name=?,url=?,method=?,expected_status=?,contains_text=?,enabled=? WHERE id=?",
                    (name.strip(),url,method,int(expected_status),contains_text,int(enabled),endpoint_id))


def delete_endpoint(endpoint_id, db_path=None):
    with connect(db_path) as con:
        con.execute("DELETE FROM endpoints WHERE id=?", (endpoint_id,))


def save_result(result, db_path=None):
    with connect(db_path) as con:
        con.execute("INSERT INTO results(endpoint_id,checked_at,status_code,response_ms,healthy,error) VALUES(?,?,?,?,?,?)",
                    tuple(result[k] for k in ("endpoint_id","checked_at","status_code","response_ms","healthy","error")))


def list_results(limit=2000, db_path=None):
    with connect(db_path) as con:
        return [dict(r) for r in con.execute("""
            SELECT r.*, e.name, e.url FROM results r JOIN endpoints e ON e.id=r.endpoint_id
            ORDER BY r.checked_at DESC, r.id DESC LIMIT ?""", (int(limit),))]

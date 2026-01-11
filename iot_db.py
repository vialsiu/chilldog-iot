import os
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

DB_PATH = os.getenv("AUTH_DB_PATH", "/var/www/FlaskApp/FlaskApp/chilldog.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_iot_tables():
    with get_conn() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ts INTEGER NOT NULL,
            temp REAL,
            humidity REAL,
            fan_on INTEGER NOT NULL,
            on_temp REAL,
            off_temp REAL,
            energy_enabled INTEGER,
            energy_timeout_sec INTEGER,
            no_motion_for_sec INTEGER,
            mode TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sensor_status_device_ts
        ON sensor_status(device_id, ts)
        """)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS fan_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ts INTEGER NOT NULL,
            event TEXT NOT NULL,
            temp REAL,
            humidity REAL,
            mode TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_fan_events_device_ts
        ON fan_events(device_id, ts)
        """)
        conn.commit()

def get_last_fan_on(device_id: str) -> Optional[bool]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT fan_on FROM sensor_status WHERE device_id=? ORDER BY ts DESC LIMIT 1",
            (device_id,),
        ).fetchone()
        if not row:
            return None
        return bool(row["fan_on"])

def insert_status_and_maybe_event(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    device_id = str(payload.get("deviceId") or payload.get("device_id") or "pi-001")
    ts = int(payload.get("ts") or 0)

    temp = payload.get("temp", payload.get("temperature"))
    humidity = payload.get("humidity")

    fan_on = payload.get("fanOn", payload.get("fan_on"))
    fan_on = bool(fan_on)

    on_temp = payload.get("onTemp")
    off_temp = payload.get("offTemp")
    energy_enabled = payload.get("energySaverEnabled")
    energy_timeout = payload.get("energySaverTimeoutSec")
    no_motion = payload.get("noMotionForSec")
    mode = payload.get("mode")

    prev = get_last_fan_on(device_id)

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sensor_status
            (device_id, ts, temp, humidity, fan_on, on_temp, off_temp,
             energy_enabled, energy_timeout_sec, no_motion_for_sec, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                device_id,
                ts,
                None if temp is None else float(temp),
                None if humidity is None else float(humidity),
                1 if fan_on else 0,
                None if on_temp is None else float(on_temp),
                None if off_temp is None else float(off_temp),
                None if energy_enabled is None else (1 if bool(energy_enabled) else 0),
                None if energy_timeout is None else int(energy_timeout),
                None if no_motion is None else int(no_motion),
                None if mode is None else str(mode),
            ),
        )

        event = None
        if prev is None:
            event = None
        elif prev != fan_on:
            event = "FAN_ON" if fan_on else "FAN_OFF"
            conn.execute(
                """
                INSERT INTO fan_events (device_id, ts, event, temp, humidity, mode)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    ts,
                    event,
                    None if temp is None else float(temp),
                    None if humidity is None else float(humidity),
                    None if mode is None else str(mode),
                ),
            )

        conn.commit()

    return True, event

def fetch_fan_events(device_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, device_id, ts, event, temp, humidity, mode, created_at
            FROM fan_events
            WHERE device_id=?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (device_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

from typing import Any, Dict, List, Optional, Tuple
from .db_mysql import db


def init_iot_tables():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS sensor_status (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                device_id VARCHAR(64) NOT NULL,
                ts BIGINT NOT NULL,
                temp DOUBLE NULL,
                humidity DOUBLE NULL,
                fan_on TINYINT(1) NOT NULL,
                on_temp DOUBLE NULL,
                off_temp DOUBLE NULL,
                energy_enabled TINYINT(1) NULL,
                energy_timeout_sec INT NULL,
                no_motion_for_sec INT NULL,
                mode VARCHAR(64) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_sensor_status_user_device_ts (user_id, device_id, ts),
                CONSTRAINT fk_sensor_user
                    FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB;
            """)

            cur.execute("""
            CREATE TABLE IF NOT EXISTS fan_events (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                device_id VARCHAR(64) NOT NULL,
                ts BIGINT NOT NULL,
                event VARCHAR(16) NOT NULL,
                temp DOUBLE NULL,
                humidity DOUBLE NULL,
                mode VARCHAR(64) NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_fan_events_user_device_ts (user_id, device_id, ts),
                CONSTRAINT fk_events_user
                    FOREIGN KEY (user_id) REFERENCES users(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB;
            """)


def get_last_fan_on(user_id: int, device_id: str) -> Optional[bool]:
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fan_on
                FROM sensor_status
                WHERE user_id=%s AND device_id=%s
                ORDER BY ts DESC
                LIMIT 1
                """,
                (user_id, device_id),
            )
            row = cur.fetchone()
            return None if not row else bool(row["fan_on"])


def insert_status_and_maybe_event(
    user_id: int,
    payload: Dict[str, Any],
) -> Tuple[bool, Optional[str]]:
    device_id = str(payload.get("deviceId") or payload.get("device_id") or "pi-001")
    ts = int(payload.get("ts") or 0)

    temp = payload.get("temp", payload.get("temperature"))
    humidity = payload.get("humidity")
    fan_on = bool(payload.get("fanOn", payload.get("fan_on")))

    on_temp = payload.get("onTemp")
    off_temp = payload.get("offTemp")
    energy_enabled = payload.get("energySaverEnabled")
    energy_timeout = payload.get("energySaverTimeoutSec")
    no_motion = payload.get("noMotionForSec")
    mode = payload.get("mode")

    prev = get_last_fan_on(user_id, device_id)
    event = None

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sensor_status
                (user_id, device_id, ts, temp, humidity, fan_on, on_temp, off_temp,
                 energy_enabled, energy_timeout_sec, no_motion_for_sec, mode)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
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

            if prev is not None and prev != fan_on:
                event = "FAN_ON" if fan_on else "FAN_OFF"
                cur.execute(
                    """
                    INSERT INTO fan_events
                    (user_id, device_id, ts, event, temp, humidity, mode)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        device_id,
                        ts,
                        event,
                        None if temp is None else float(temp),
                        None if humidity is None else float(humidity),
                        None if mode is None else str(mode),
                    ),
                )

    return True, event


def fetch_fan_events(
    user_id: int,
    device_id: str,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    limit = max(1, min(int(limit), 200))
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    id,
                    user_id,
                    device_id,
                    ts,
                    event,
                    temp,
                    humidity,
                    mode,
                    created_at
                FROM fan_events
                WHERE user_id=%s AND device_id=%s
                ORDER BY ts DESC
                LIMIT %s
                """,
                (user_id, device_id, limit),
            )
            return cur.fetchall()


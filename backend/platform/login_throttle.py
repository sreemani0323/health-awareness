"""Progressive login throttling and brute-force mitigation for HealthAware.

Implements multi-tiered, worker-safe throttling:
1. Per (username, ip) pair: After 5 failed attempts, progressively throttles that IP/username
   pair for 5 minutes (300 seconds). Legitimate users on other IPs are not blocked.
2. Global per-username ceiling: After 10 failed attempts across all IPs, imposes a temporary
   15-minute (900 seconds) cooling window to protect account integrity.
3. Administrator / CLI reset: Administrators can immediately clear throttles for any account,
   preventing permanent Denial-of-Service (DoS) lockouts.
4. Concurrency safety: Utilizes SQLite in WAL mode with busy timeouts to coordinate reliably
   across multiple Gunicorn worker processes and application restarts without paid Redis dependencies.
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Configurable thresholds
PAIR_THRESHOLD = 5          # Failures before (username, ip) throttling kicks in
PAIR_LOCKOUT_SECONDS = 300  # 5 minutes
USER_THRESHOLD = 10         # Global failures across all IPs before account cooling
USER_LOCKOUT_SECONDS = 900  # 15 minutes
RESET_WINDOW_SECONDS = 900  # Failures older than 15 min expire automatically


def _get_db_path() -> str:
    override = os.environ.get("LOGIN_THROTTLE_DB_PATH")
    if override:
        return override
    # Default to local_db directory
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_db_dir = os.path.join(os.path.dirname(base_dir), "local_db")
    os.makedirs(local_db_dir, exist_ok=True)
    return os.path.join(local_db_dir, "login_throttles.sqlite3")


class LoginThrottleManager:
    """Manages failure counters and progressive throttling."""

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path or _get_db_path()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS throttle_pairs (
                    pair_key TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    last_failed_at REAL NOT NULL,
                    locked_until REAL NOT NULL DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS throttle_users (
                    username TEXT PRIMARY KEY,
                    failed_count INTEGER NOT NULL DEFAULT 0,
                    last_failed_at REAL NOT NULL,
                    locked_until REAL NOT NULL DEFAULT 0
                )
            """)
            conn.commit()

    @staticmethod
    def _make_pair_key(username: str, ip: str) -> str:
        return f"{username.strip().lower()}::{ip.strip()}"

    def is_throttled(self, username: str, ip: str) -> Tuple[bool, int, str]:
        """Checks if a login attempt for (username, ip) is currently throttled.

        Returns:
            (is_throttled: bool, retry_after_seconds: int, reason: str)
        """
        now = time.time()
        u_clean = username.strip().lower()
        ip_clean = ip.strip() or "127.0.0.1"
        pair_key = self._make_pair_key(u_clean, ip_clean)

        try:
            with self._get_conn() as conn:
                # 1. Check (username, ip) pair lockout
                row = conn.execute(
                    "SELECT locked_until FROM throttle_pairs WHERE pair_key = ?",
                    (pair_key,),
                ).fetchone()
                if row and row["locked_until"] > now:
                    retry_after = int(row["locked_until"] - now) + 1
                    return True, retry_after, "pair_lockout"

                # 2. Check global username lockout
                user_row = conn.execute(
                    "SELECT locked_until FROM throttle_users WHERE username = ?",
                    (u_clean,),
                ).fetchone()
                if user_row and user_row["locked_until"] > now:
                    retry_after = int(user_row["locked_until"] - now) + 1
                    return True, retry_after, "user_lockout"

            return False, 0, ""
        except Exception as exc:
            logger.error("Failed to check login throttle: %s", exc)
            return False, 0, ""

    def record_failure(self, username: str, ip: str) -> None:
        """Records an authentication failure and calculates progressive lockouts."""
        now = time.time()
        u_clean = username.strip().lower()
        ip_clean = ip.strip() or "127.0.0.1"
        pair_key = self._make_pair_key(u_clean, ip_clean)

        try:
            with self._get_conn() as conn:
                # --- A. Update pair record ---
                row = conn.execute(
                    "SELECT failed_count, last_failed_at FROM throttle_pairs WHERE pair_key = ?",
                    (pair_key,),
                ).fetchone()

                if row is None or (now - row["last_failed_at"]) > RESET_WINDOW_SECONDS:
                    new_pair_count = 1
                else:
                    new_pair_count = row["failed_count"] + 1

                locked_until = 0.0
                if new_pair_count >= PAIR_THRESHOLD:
                    # Calculate progressive lockout: 5 mins + 2 mins per subsequent attempt, capped at 30 mins
                    extra_attempts = new_pair_count - PAIR_THRESHOLD
                    lock_duration = min(PAIR_LOCKOUT_SECONDS + (extra_attempts * 120), 1800)
                    locked_until = now + lock_duration

                conn.execute(
                    """
                    INSERT INTO throttle_pairs (pair_key, username, ip_address, failed_count, last_failed_at, locked_until)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pair_key) DO UPDATE SET
                        failed_count = excluded.failed_count,
                        last_failed_at = excluded.last_failed_at,
                        locked_until = excluded.locked_until
                    """,
                    (pair_key, u_clean, ip_clean, new_pair_count, now, locked_until),
                )

                # --- B. Update global username record ---
                user_row = conn.execute(
                    "SELECT failed_count, last_failed_at FROM throttle_users WHERE username = ?",
                    (u_clean,),
                ).fetchone()

                if user_row is None or (now - user_row["last_failed_at"]) > RESET_WINDOW_SECONDS:
                    new_user_count = 1
                else:
                    new_user_count = user_row["failed_count"] + 1

                user_locked_until = 0.0
                if new_user_count >= USER_THRESHOLD:
                    user_locked_until = now + USER_LOCKOUT_SECONDS

                conn.execute(
                    """
                    INSERT INTO throttle_users (username, failed_count, last_failed_at, locked_until)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(username) DO UPDATE SET
                        failed_count = excluded.failed_count,
                        last_failed_at = excluded.last_failed_at,
                        locked_until = excluded.locked_until
                    """,
                    (u_clean, new_user_count, now, user_locked_until),
                )

                conn.commit()
        except Exception as exc:
            logger.error("Failed to record login failure: %s", exc)

    def record_success(self, username: str, ip: str) -> None:
        """Clears failed attempt counters upon successful authentication."""
        u_clean = username.strip().lower()
        ip_clean = ip.strip() or "127.0.0.1"
        pair_key = self._make_pair_key(u_clean, ip_clean)

        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM throttle_pairs WHERE pair_key = ?", (pair_key,))
                conn.execute("DELETE FROM throttle_users WHERE username = ?", (u_clean,))
                conn.commit()
        except Exception as exc:
            logger.error("Failed to reset throttle on login success: %s", exc)

    def admin_reset_throttle(self, username: str) -> bool:
        """Administratively unlocks a username and removes all recorded failures."""
        u_clean = username.strip().lower()
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM throttle_pairs WHERE username = ?", (u_clean,))
                conn.execute("DELETE FROM throttle_users WHERE username = ?", (u_clean,))
                conn.commit()
            return True
        except Exception as exc:
            logger.error("Failed to admin-reset throttle for user '%s': %s", username, exc)
            return False

    def clear_all(self) -> None:
        """Wipes all throttle records (used in test isolation)."""
        try:
            with self._get_conn() as conn:
                conn.execute("DELETE FROM throttle_pairs")
                conn.execute("DELETE FROM throttle_users")
                conn.commit()
        except Exception as exc:
            logger.error("Failed to clear throttles: %s", exc)


# Singleton process-wide instance
_default_throttle_manager: Optional[LoginThrottleManager] = None


def get_login_throttle_manager() -> LoginThrottleManager:
    global _default_throttle_manager
    if _default_throttle_manager is None:
        _default_throttle_manager = LoginThrottleManager()
    return _default_throttle_manager

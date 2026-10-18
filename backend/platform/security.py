"""Password hashing and verification utilities conforming to OWASP guidance.

Implements PBKDF2-HMAC-SHA256 with 600,000 iterations (OWASP recommendation),
unique 16-byte cryptographic salts, and support for transparent hash upgrades
from legacy schemes upon successful authentication.

Scheme format:
    pbkdf2:sha256:<iterations>$<salt_hex>$<hash_hex>
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from typing import Tuple

DEFAULT_PBKDF2_ITERATIONS = int(os.environ.get("PBKDF2_ITERATIONS", "600000"))
SALT_BYTE_LEN = 16


def hash_password(password: str, iterations: int | None = None) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256.

    Args:
        password: The plaintext password.
        iterations: Number of hash iterations. Defaults to DEFAULT_PBKDF2_ITERATIONS.

    Returns:
        Formatted string: pbkdf2:sha256:<iterations>$<salt_hex>$<hash_hex>
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")

    iters = iterations if iterations is not None else DEFAULT_PBKDF2_ITERATIONS
    salt = secrets.token_bytes(SALT_BYTE_LEN)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
    return f"pbkdf2:sha256:{iters}${salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a plaintext password against a stored hash.

    Supports:
    1. Modern versioned PBKDF2: pbkdf2:sha256:<iters>$<salt_hex>$<hash_hex>
    2. Legacy un-salted SHA-256 (64 hex characters) from initial prototypes.

    Returns:
        True if the password matches, False otherwise.
    """
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False
    if not password or not stored_hash:
        return False

    # 1. Versioned PBKDF2
    if stored_hash.startswith("pbkdf2:sha256:"):
        try:
            prefix, salt_hex, key_hex = stored_hash.split("$")
            iters_str = prefix.split(":")[-1]
            iters = int(iters_str)
            salt = bytes.fromhex(salt_hex)
            computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters).hex()
            return hmac.compare_digest(computed, key_hex)
        except (ValueError, TypeError):
            return False

    # 2. Legacy single-round SHA-256 (backward compatibility)
    if len(stored_hash) == 64 and "$" not in stored_hash:
        try:
            computed = hashlib.sha256(password.encode("utf-8")).hexdigest()
            return hmac.compare_digest(computed, stored_hash)
        except Exception:
            return False

    return False


def needs_rehash(stored_hash: str, target_iterations: int | None = None) -> bool:
    """Determine if a stored hash should be upgraded to the current standard.

    Returns True if:
    - The hash uses the legacy single-round SHA-256 scheme.
    - The hash uses PBKDF2 but with fewer iterations than the target (default 600,000).
    """
    if not isinstance(stored_hash, str) or not stored_hash:
        return True

    target = target_iterations if target_iterations is not None else DEFAULT_PBKDF2_ITERATIONS

    # Legacy SHA-256 needs immediate upgrade
    if len(stored_hash) == 64 and "$" not in stored_hash:
        return True

    if stored_hash.startswith("pbkdf2:sha256:"):
        try:
            prefix, _, _ = stored_hash.split("$")
            iters = int(prefix.split(":")[-1])
            return iters < target
        except Exception:
            return True

    return True

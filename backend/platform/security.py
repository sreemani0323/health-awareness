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


# ---------------------------------------------------------------------------
# TOTP Secret Encryption at Rest & Recovery Code Utilities
# ---------------------------------------------------------------------------

import base64
from cryptography.fernet import Fernet


def _get_mfa_fernet() -> Fernet:
    """Returns a Fernet cipher instance for TOTP secret encryption at rest.

    Key hierarchy:
    1. Dedicated MFA_ENCRYPTION_KEY environment variable.
    2. Cryptographically derived key from FLASK_SECRET_KEY / SECRET_KEY using HMAC domain separation.
    3. Non-production / local test fallback default.
    """
    mfa_key = os.environ.get("MFA_ENCRYPTION_KEY", "").strip()

    if mfa_key:
        raw_key = mfa_key
    else:
        flask_secret = (
            os.environ.get("FLASK_SECRET_KEY", "").strip()
            or os.environ.get("SECRET_KEY", "").strip()
        )
        if flask_secret:
            raw_key = hmac.new(
                b"healthaware-mfa-derivation-salt-v1",
                flask_secret.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        else:
            raw_key = "healthaware-default-mfa-encryption-key-32b"

    key_32 = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(key_32))


def encrypt_totp_secret(secret: str) -> str:
    """Encrypts a plaintext base32 TOTP secret for storage at rest."""
    if not secret or not isinstance(secret, str):
        raise ValueError("Secret must be a non-empty string.")
    fernet = _get_mfa_fernet()
    return fernet.encrypt(secret.encode("utf-8")).decode("utf-8")


def decrypt_totp_secret(ciphertext: str) -> str:
    """Decrypts an encrypted TOTP secret from storage."""
    if not ciphertext or not isinstance(ciphertext, str):
        raise ValueError("Ciphertext must be a non-empty string.")
    fernet = _get_mfa_fernet()
    return fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def generate_recovery_codes(count: int = 8) -> list[str]:
    """Generates human-readable, high-entropy emergency recovery codes.
    
    Format: XXXX-XXXX using an unambiguous uppercase alphanumeric character set.
    """
    charset = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"  # Excludes 0, O, 1, I
    codes = []
    for _ in range(count):
        part1 = "".join(secrets.choice(charset) for _ in range(4))
        part2 = "".join(secrets.choice(charset) for _ in range(4))
        codes.append(f"{part1}-{part2}")
    return codes


def hash_recovery_code(code: str) -> str:
    """Normalizes and hashes an emergency recovery code with SHA-256."""
    clean = code.strip().upper().replace(" ", "").replace("-", "")
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()


def verify_recovery_code(candidate: str, hashed_code: str) -> bool:
    """Constant-time verification of a recovery code candidate against its stored hash."""
    clean = candidate.strip().upper().replace(" ", "").replace("-", "")
    computed = hashlib.sha256(clean.encode("utf-8")).hexdigest()
    return hmac.compare_digest(computed, hashed_code)


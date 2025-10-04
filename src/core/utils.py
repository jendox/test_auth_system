import datetime
import hashlib
from datetime import UTC, timedelta

__all__ = (
    "get_iat_exp_timestamps",
    "get_sha256hash",
)


def get_iat_exp_timestamps(delta: timedelta = timedelta(seconds=0)) -> tuple[int, int]:
    """
    Generate issued-at (iat) and expiration (exp) timestamps.

    Args:
        delta: Time duration to add to current time for expiration

    Returns:
        Tuple of (issued_at_timestamp, expiration_timestamp) as integers
    """
    iat = datetime.datetime.now(UTC)
    exp = iat + delta
    return int(iat.timestamp()), int(exp.timestamp())


def get_sha256hash(secret: str) -> str:
    """
    Generate SHA-256 hash of a string.

    Args:
        secret: String to hash

    Returns:
        Hexadecimal representation of the SHA-256 hash
    """
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()

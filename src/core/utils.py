import datetime
import hashlib
from datetime import UTC, timedelta


def get_iat_exp_timestamps(delta: timedelta = timedelta(seconds=0)) -> tuple[int, int]:
    iat = datetime.datetime.now(UTC)
    exp = iat + delta
    return int(iat.timestamp()), int(exp.timestamp())


def get_sha256hash(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()

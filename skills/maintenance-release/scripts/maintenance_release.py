"""Maintenance and release helpers."""

import hashlib
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int


def parse_semver(text: str) -> SemVer:
    parts = text.split(".")
    if len(parts) != 3:
        raise ValueError("semantic version must have major.minor.patch")
    return SemVer(*(int(part) for part in parts))


def calibration_checksum(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def compatible_runtime(required: SemVer, actual: SemVer) -> bool:
    return actual.major == required.major and (actual.minor, actual.patch) >= (required.minor, required.patch)


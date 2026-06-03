import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from maintenance_release import calibration_checksum, compatible_runtime, parse_semver


def test_parse_semver():
    v = parse_semver("1.2.3")
    assert (v.major, v.minor, v.patch) == (1, 2, 3)


def test_parse_semver_rejects_invalid():
    with pytest.raises(ValueError):
        parse_semver("1.2")


def test_checksum_is_order_stable():
    assert calibration_checksum({"a": 1, "b": 2}) == calibration_checksum({"b": 2, "a": 1})


def test_compatible_runtime():
    assert compatible_runtime(parse_semver("1.2.0"), parse_semver("1.3.0"))
    assert not compatible_runtime(parse_semver("1.2.0"), parse_semver("2.0.0"))


import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.mujoco_tennis_world_builder.scripts.world_builder import (
    generate_tennis_world,
    verify_world,
    COURT_STANDARDS,
    BALL_STANDARDS,
)


def test_world_builder_tennis():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = generate_tennis_world(tmp, sport_type="tennis")
        assert os.path.exists(xml_path)
        ok, info = verify_world(xml_path)
        assert ok, f"Verification failed: {info}"
        print(f"PASS: Tennis world builder - {info}")


def test_world_builder_badminton():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = generate_tennis_world(tmp, sport_type="badminton")
        assert os.path.exists(xml_path)
        ok, info = verify_world(xml_path)
        assert ok, f"Verification failed: {info}"
        print(f"PASS: Badminton world builder - {info}")


if __name__ == "__main__":
    test_world_builder_tennis()
    test_world_builder_badminton()
    print("\nAll world builder tests PASSED!")

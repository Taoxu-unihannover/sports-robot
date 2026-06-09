import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.world_builder import generate_tennis_world, verify_world


def test_generate_tennis_world(tmp_path):
    xml_path = generate_tennis_world(str(tmp_path), sport_type="tennis")
    assert os.path.exists(xml_path), f"XML file not found: {xml_path}"
    ok, info = verify_world(xml_path)
    assert ok, f"World verification failed: {info}"
    print(f"PASS: Tennis world generated and verified - {info}")


def test_generate_badminton_world(tmp_path):
    xml_path = generate_tennis_world(str(tmp_path), sport_type="badminton")
    assert os.path.exists(xml_path), f"XML file not found: {xml_path}"
    ok, info = verify_world(xml_path)
    assert ok, f"World verification failed: {info}"
    print(f"PASS: Badminton world generated and verified - {info}")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_generate_tennis_world(tmp)
        tmp2 = os.path.join(tmp, "badminton")
        test_generate_badminton_world(tmp2)

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from skill_policy import Skill, SkillLibrary, blend_actions


def test_selects_matching_side():
    lib = SkillLibrary()
    lib.add(Skill("forehand", 0.1, "right"))
    lib.add(Skill("backhand", 0.1, "left"))
    assert lib.select({"side": "right", "workspace_margin": 0.2}).name == "forehand"


def test_rejects_low_margin():
    lib = SkillLibrary()
    lib.add(Skill("attack", 0.5, "right"))
    assert lib.select({"side": "right", "workspace_margin": 0.1}) is None


def test_blend_actions():
    assert blend_actions({"x": 0}, {"x": 10}, 0.25)["x"] == 2.5


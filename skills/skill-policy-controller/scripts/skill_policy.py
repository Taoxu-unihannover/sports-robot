"""Skill library and simple policy router for ball games."""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Skill:
    name: str
    required_margin: float
    preferred_side: str
    priority: int = 0

    def score(self, context: Dict) -> float:
        margin = float(context.get("workspace_margin", 0.0))
        if margin < self.required_margin:
            return -1e9
        side_bonus = 1.0 if context.get("side") == self.preferred_side else 0.0
        urgency = float(context.get("urgency", 0.0))
        return self.priority + side_bonus + 0.2 * margin + 0.5 * urgency


class SkillLibrary:
    def __init__(self):
        self.skills: List[Skill] = []

    def add(self, skill: Skill):
        self.skills.append(skill)

    def select(self, context: Dict) -> Optional[Skill]:
        if not self.skills:
            return None
        scored = [(skill.score(context), skill) for skill in self.skills]
        score, skill = max(scored, key=lambda item: item[0])
        return skill if score > -1e8 else None


def blend_actions(action_a: Dict[str, float], action_b: Dict[str, float], alpha: float) -> Dict[str, float]:
    alpha = max(0.0, min(1.0, alpha))
    keys = set(action_a) | set(action_b)
    return {k: (1 - alpha) * action_a.get(k, 0.0) + alpha * action_b.get(k, 0.0) for k in keys}


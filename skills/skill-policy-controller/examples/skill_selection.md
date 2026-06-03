# 技能策略控制示例

```python
from skill_policy import SkillLibrary, Skill

library = SkillLibrary()
library.add(Skill("forehand", required_margin=0.1, preferred_side="right"))
selected = library.select({"side": "right", "workspace_margin": 0.3})
```

该 skill 用于把连续控制问题拆成可复用技能：正手、反手、接球、退让、恢复等。


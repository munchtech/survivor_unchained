"""Local trial of the Warden's C03 clips (never committed: the timeline is cinematics').
python cine_try3.py on|off"""
import sys
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\godot\data\cinematics\c03.json"
s = open(p, encoding="utf-8").read()
pairs = [('{"do": "anim", "actor": "warden", "clip": "Fixing_Kneeling", "from": 0.8, "speed": 0.25, "blend": 0.9}',
          '{"do": "anim", "actor": "warden", "clip": "folk/m_kneel_lamp", "from": 0, "speed": 1, "blend": 0.6}'),
         ('{"at": 1.1, "do": "lamp", "actor": "warden", "lit": false, "glow": 0.0, "over": 0.4},',
          '{"do": "anim", "actor": "warden", "clip": "folk/m_lamp_down", "from": 0, "speed": 1, "blend": 0.3},\n        {"at": 1.1, "do": "lamp", "actor": "warden", "lit": false, "glow": 0.0, "over": 0.4},'),
         ('{"do": "anim", "actor": "warden", "clip": "Death01", "from": 0.4, "speed": 0.45, "blend": 0.5}',
          '{"do": "anim", "actor": "warden", "clip": "folk/m_fold_forward", "from": 0, "speed": 1, "blend": 0.2}')]
for a, b in pairs:
    if sys.argv[1] == "on":
        assert s.count(a) == 1, a
        s = s.replace(a, b)
    else:
        s = s.replace(b, a)
open(p, "w", encoding="utf-8", newline="").write(s)
print(sys.argv[1])

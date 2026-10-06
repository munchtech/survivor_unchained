"""Local trial of the Warden's clips in C02 (never committed: the timeline is cinematics').
python cine_try.py on|off"""
import sys
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7dd95d00c4a6a017\godot\data\cinematics\c02.json"
s = open(p, encoding="utf-8").read()
pairs = [('{"do": "anim", "actor": "warden", "clip": "LayToIdle", "from": 0, "speed": 0.45, "blend": 0}',
          '{"do": "anim", "actor": "warden", "clip": "folk/m_rise_stiff", "from": 0, "speed": 1, "blend": 0}'),
         ('{"do": "anim", "actor": "warden", "clip": "Idle_Torch", "speed": 0.4, "blend": 0.4, "from": 0.4}',
          '{"do": "anim", "actor": "warden", "clip": "folk/m_bend_lift", "speed": 1, "blend": 0.4, "from": 0}')]
for a, b in pairs:
    if sys.argv[1] == "on":
        s = s.replace(a, b)
    else:
        s = s.replace(b, a)
open(p, "w", encoding="utf-8", newline="").write(s)
print(sys.argv[1])

# Boss unwedge lead (coordinator #14, 15 Nov)

## Top block (read first)
- Worktree C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af0dfb5a9bf5ba20b, branch boss-unwedge (from integration ced27dbf1). Not pushed yet.
- Bug: Roost seed 16 deft bot, Red Hand wedged ~(64.1,-89.6) inside Boss camp `wall` boxes, 9054 life, 25 min timeout.
- State: starting (reproduce).
- Next in order: 1 reproduce + trace cause; 2 fix in godot/logic/Sim (foes never end a step in solid; displaced to nearest walkable) + tests (seed 16; wall push from each side); 3 tables seeds 1-50 and 51-100 (no timeouts; deft>=95, human 80-90, standing 0); 4 full suite; report-only: standing 96% vs Red Hand, heavy-mark gaps Roost, Bladestorm share.
- Cost so far: none.

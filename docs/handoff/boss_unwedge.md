# Boss unwedge lead (coordinator #14, 15 Nov)

## Top block (read first)
- DONE: branch boss-unwedge (from integration ced27dbf1, nothing newer on origin), suite 2832/0/11, tables in scratch_coord14u	_s1.md, t_s51.md (boss alone boss_s1.md). Only the report to main is left.
- Cause: not a push. The Red Hand (radius 1.1) jams between two Boss-camp wall corners 2.0 m apart ((63.5,-88.5) and (63.5,-90.5)); the 1 m nav grid sends every foe through, the resolver stops it politely at the door; nothing reached him, 25-min timeout.
- Fix: CollisionWorld.FoeWallCap 0.95 (foes meet walls at no more than that), squeeze/Unwedge for pinches, Battle.KeepOutOfSolid after each foe's Ai step; harness MAP_FOE=from,to (minutes).

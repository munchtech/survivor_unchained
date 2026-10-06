#!/usr/bin/env bash
# The night won in ember with the way out's band; Moonbrand near her and at range; the firepot's
# burst (and its burning ground's ticks); the Hollow's fed fires taking, guttering and going out,
# and Greymuzzle's breath in "His age".
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ad059388f00c19f9f
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py won2 --quick warden --tier 2 --zone arena --people dead --time night --minute 29.9 --won --on boss --seconds 4
python sweep.py e2 moonbrand firepot
python sweep.py e2far moonbrand --dist 6 --spread 8 --count 12 --every 0.12
python shot.py hollow2 --quick warden --night hollow --stage 3 --lit 9 --lab --on boss --seconds 0.3 --every 0.6 --count 28
echo done

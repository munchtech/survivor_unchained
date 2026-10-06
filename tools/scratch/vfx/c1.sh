#!/usr/bin/env bash
# The new lead's first look: elites capped (Iron Palms, Hallowed Ground on 8 elite risen); the
# Legendary's foot by night and day; the night won and the chests' columns; Moonbrand and Firepot as
# they are; the Hollow's boss with its deadfalls lit ("His age", a fed fire).
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ad059388f00c19f9f
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python sweep.py e1 iron_palms hallowed_ring --count 8 --every 0.2
python shot.py lf_tiers_night --quick warden --tier 2 --lab --zone arena --people dead --time night --loot-tiers --loot-at 3 --seconds 6 --count 1
python shot.py lf_tiers_day --quick warden --tier 2 --lab --zone verge --time day --loot-tiers --loot-at 3 --seconds 6 --count 1
python shot.py won --quick warden --tier 2 --zone arena --people dead --time night --minute 29.9 --won --on boss --seconds 4
python shot.py chest --quick warden --tier 2 --lab --zone arena --people dead --time night --chest 1,3,5! --chest-at 2 --seconds 2.05 --every 0.12 --count 14
python sweep.py e1 moonbrand firepot
python shot.py hollow --quick warden --night hollow --stage 3 --lit --lab --on boss --seconds 40
echo done

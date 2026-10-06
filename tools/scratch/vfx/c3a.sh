#!/usr/bin/env bash
# Rechecks (the night won's pool, the way out's band, the fed fire as a line of flame, the old wolf's
# breath, Moonbrand's trail), then the unions and the first evolutions, for grading.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ad059388f00c19f9f
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
python shot.py won3 --quick warden --tier 2 --zone arena --people dead --time night --minute 29.9 --won --on boss --seconds 4
python shot.py hollow3 --quick warden --night hollow --stage 3 --lit 9 --lab --on boss --seconds 0.3 --every 0.6 --count 28
python sweep.py e3far moonbrand --dist 6 --spread 8 --count 12 --every 0.12
python sweep.py u1 frostfire_comet:4 the_tempest:4 rotwood:4 butchers_wheel:4 hail_of_steel:4 dawns_judgement:4 barrow_host:4 soul_lantern:4 starfall:4 --count 12 --every 0.15
python sweep.py v1 oathblade:4@oathkeeper oathblade:4@graveedge cleaver:4@whirlwind cleaver:4@bonesplitter axe_gyre:4@gyrestorm axe_gyre:4@reavers_wheel iron_palms:4@temple_breaker iron_palms:4@thunder_palm reaving_arc:4@rend_and_mend reaving_arc:4@harrowing volley:4@arrowfall volley:4@predators_volley knifestorm:4@steel_flurry knifestorm:4@thousand_cuts gale_chakram:4@razorgale gale_chakram:4@hailwheel judgement_disc:4@reckoning judgement_disc:4@aegis_wheel firepot:4@powder_keg firepot:4@wildfire --count 12 --every 0.15
echo done

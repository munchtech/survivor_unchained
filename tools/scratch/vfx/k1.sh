#!/usr/bin/env bash
# Skills lead a560452c, batch 1: the evolutions redrawn (no hoops, no white bars), Moonfall and
# Frostfire after their fixes, burning ground as fires in it, the way out late in a won night, the
# warm struck flash, and Iron Palms and Firepot taped again after the volume fix.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a560452c597415545
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
mkdir -p snd
for sk in "iron_palms reaver" "firepot stalker"; do
  set -- $sk
  python shot.py snd2_$1 --quick $2 --zone arena --people dead --time night --tier 2 --lab --give $1:4 --horde 60,4:risen! --dist 3 --spread 9 --seconds 5 --count 1 --wav "C:\\Users\\munch\\AppData\\Local\\Temp\\claude\\C--Users-munch-Desktop-wowsurvivors\\f1b9be14-0826-4f47-8004-f1d371f2c6a3\\scratchpad\\vfx\\snd\\k1_$1.wav"
done
python sweep.py k1 reaving_arc:4@rend_and_mend reaving_arc:4@harrowing reaving_arc:4 hoarfrost:4@winter_ward hoarfrost:4@absolute_zero hoarfrost:4 spirit_herd:4@wild_hunt arcweb:4@skybreak rimeshard:4@glacier_spear verdant_lance:4@sunlance moonbrand:4@moonfall frostfire_comet:4 firepot:4 --count 12 --every 0.15
# The struck flash: a volley into the pale dead, a frame every two ticks.
python shot.py k1_flash --quick stalker --zone arena --people dead --time night --tier 2 --lab --give volley:4 --horde 70,8:risen! --dist 3 --spread 9 --seconds 3 --every 0.034 --count 10
# The way out late in a won night, at its full strength and breathing.
python shot.py k1_won --quick warden --tier 2 --zone arena --people dead --time night --minute 29.9 --won --seconds 7 --every 1.5 --count 3
echo done

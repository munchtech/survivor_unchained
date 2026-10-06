#!/usr/bin/env bash
# Each skill's own voice, on tape (--wav) for spectrograms; Frostfire Comet's frost again.
cd "$(dirname "$0")"
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-ad059388f00c19f9f
(cd "$WT/godot" && dotnet build 2>&1 | grep -E " error |Build succeeded" | head -3)
mkdir -p snd
for sk in "volley stalker" "moonbrand arcanist" "firepot stalker" "thunderhead arcanist" "gale_chakram stalker" "iron_palms reaver" "grave_tether reaver" "arcweb arcanist"; do
  set -- $sk
  python shot.py snd_$1 --quick $2 --zone arena --people dead --time night --tier 2 --lab --give $1:4 --horde 60,4:risen! --dist 3 --spread 9 --seconds 5 --count 1 --wav "C:\\Users\\munch\\AppData\\Local\\Temp\\claude\\C--Users-munch-Desktop-wowsurvivors\\f1b9be14-0826-4f47-8004-f1d371f2c6a3\\scratchpad\\vfx\\snd\\$1.wav"
done
python sweep.py u3 frostfire_comet:4 reaving_arc:4@rend_and_mend reaving_arc:4@harrowing axe_gyre:4@gyrestorm judgement_disc:4@aegis_wheel moonbrand:4@moonfall thunderhead:4@thunderclap --count 12 --every 0.15
python shot.py won5 --quick warden --tier 2 --zone arena --people dead --time night --minute 29.9 --won --seconds 7 --count 1
echo done

#!/usr/bin/env bash
# Upgrade session 2, judge round 3 (the last): 4.7.2 only at the new glow numbers (x3 / x2); the 4.5.1 side is round 2's clips
# (godot/.shots/r2_g45) and the numbers run's s12d (moves12_g45s2): nothing since then changes the 4.5.1 picture (all of it is
# behind Engine46 / Aa.Active). Pairs in godot/.shots/godot47up/judge3/ (a = 4.5.1, b = 4.7.2). Through tools/quiet.py.
WT=/c/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a73cef575840655d2
G47=/c/Users/munch/Desktop/Godot_v4.7.2-stable_mono_win64/Godot_v4.7.2-stable_mono_win64_console.exe
O=$WT/godot/.shots/godot47up; L=$O/round3.log; cd $WT
dotnet build godot/SurvivorUnchained.csproj > $O/r3_build47.log 2>&1; echo "build 4.7.2: $(grep -c 'error CS' $O/r3_build47.log) errors" > $L
GODOT="$G47" MOVES_OUT=r3_g47 TURN_LABEL="godot47-up2: round 3 4.7.2" python tools/motion/move_baseline.py s01,s11,s10a,s12d > $O/r3_47.out 2>&1
for spec in s01:0.5,3.0 s11:2.15 s10a:2.1; do IFS=: read tk secs <<< "$spec"
  python tools/scratch/godot47/compare.py godot/.shots/r2_g45/$tk/clip.mp4 godot/.shots/r3_g47/$tk/clip.mp4 $O/judge3/$tk $secs >> $L 2>&1
done
python tools/scratch/godot47/halo.py $O/judge3/s01/a_0.5.png $O/judge3/s01/b_0.5.png >> $L 2>&1
python - >> $L 2>&1 <<'PY'
# s12d is not frame-matched across engines (the pack drifts before S0), so the pair is by event: each engine's own first
# two of her hits landing on a foe (ticks.csv ev "Hit"), 3 and 7 frames after the tick. Clip second = t_shot + 0.5.
import csv, os, cv2
O = "godot/.shots/godot47up/judge3/s12d"; os.makedirs(O, exist_ok=True)
for side, d in (("a", "godot/.shots/moves12_g45s2/s12d"), ("b", "godot/.shots/r3_g47/s12d")):
    hits = [float(r["t_shot"]) for r in csv.DictReader(open(d + "/ticks.csv")) if "Hit" in r["ev"].split("|")]
    picks = [hits[0]] + [h for h in hits if h > hits[0] + 0.4][:1]
    c = cv2.VideoCapture(d + "/clip.mp4")
    for i, h in enumerate(picks, 1):
        for j, off in enumerate((3, 7), 1):
            c.set(cv2.CAP_PROP_POS_FRAMES, round((h + 0.5) * 60) + off); ok, f = c.read()
            cv2.imwrite(f"{O}/{side}_hit{i}_{j}.png", f)
    print("s12d", side, "her hits land at shot seconds", [round(h, 3) for h in hits[:6]], "picked", picks)
PY
echo "done $(grep -c 'exit 0' $O/r3_47.out) takes ok" >> $L

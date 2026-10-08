#!/bin/bash
# Which part of the render draws the Warden's blue sparkles: the same clip and frames under
# each switch, one Godot turn, then a count of isolated blue pixels per variant.
#   bash bisect.sh <outfit> <clip> <tag> "<variant>" ...   (a variant: "NAME=1 NAME2=0" or "base")
O="$1"; CLIP="$2"; TAG="$3"; shift 3
WT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"  # (this worktree)
L="${OSCR:?set OSCR, the outfits scratch folder}/legal"
OUT="$L/$TAG"; mkdir -p "$OUT"
T="python /c/Users/munch/Desktop/survivorsunchained/tools/turn.py"
N="outfits lead: render bisect ($TAG)"
G=/c/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe
python "$WT/tools/legal/motioncheck/make_motioncheck.py" "$OUT/motioncheck.gd" >/dev/null || exit 1
until $T take godot "$N" --wait 60 >/dev/null 2>&1; do :; done
cd $WT/godot
k=0
for v in "$@"; do
  k=$((k+1)); vv="$v"; [ "$v" = "base" ] && vv=""
  env FOV=38 OUTFIT="$O" HAIR=ponytail SPREAD=1 FRAMES=10 VIEWS="${VIEWS:-chest:0,1.45,1.3,1.30:35}" FOLLOW=1 $vv \
    timeout 300 "$G" --path . --resolution 960x540 --fixed-fps 60 -s "$OUT/motioncheck.gd" -- "her/$CLIP" "$OUT/v${k}_${CLIP}.png" \
    </dev/null >"$OUT/log_v$k.txt" 2>&1
done
$T give godot "$N" >/dev/null
cd "$OUT"
python - "$@" <<'PY'
import glob, sys
import numpy as np
from PIL import Image
for k, v in enumerate(sys.argv[1:], 1):
    n = 0
    fs = sorted(glob.glob('v%d_*_[0-9][0-9].png' % k))
    for f in fs:
        a = np.asarray(Image.open(f).convert('RGB')).astype(int)
        b = a[..., 2] - 0.5 * (a[..., 0] + a[..., 1])
        p = np.pad(b, 1, mode='edge')
        nb = np.max(np.stack([p[1 + dy:p.shape[0] - 1 + dy, 1 + dx:p.shape[1] - 1 + dx]
                              for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]), 0)
        n += int(((b > 60) & (b - nb > 45)).sum())
    print('%-40s %3d isolated blue pixels in %d frames' % (v, n, len(fs)))
PY
echo BISECTDONE

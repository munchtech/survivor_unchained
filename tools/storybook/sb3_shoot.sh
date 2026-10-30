#!/usr/bin/env bash
# Storybook 3: one round of SB00's ink section (56-89.5 s by default), wired, imported and shot.
#
#   bash tools/storybook/sb3_shoot.sh <round>        e.g. r2
#   FROM=0 TO=56 TIMES="0.5 1.5 2.3" bash tools/storybook/sb3_shoot.sh r7a   (another span: env FROM, TO, TIMES)
#
# Re-runs sb_wire_ink.py (ink_picks.json + the plates' layers.json -> sb00.json and the art),
# builds the C#, imports, then with the godot turn held (taken and given back here):
#   - 14 frames at 1920x1080 at the storybook times below
#   - the FROM-TO capture with sound (voice-over on: --vo on) as an mp4
#   - the contact sheet (each frame half size, 4 a row, labelled) and a half copy of it
# into tools/storybook/out/sb3_frames/<round>/. Any failure stops the run with a message.
set -euo pipefail

ROUND="${1:?usage: sb3_shoot.sh <round>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
G="${G:-C:/Users/munch/Desktop/Godot_v4.5.1-stable_mono_win64/Godot_v4.5.1-stable_mono_win64_console.exe}"
TURN="C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
TURN_NAME="storybook3: shoot $ROUND"
OUT="$ROOT/tools/storybook/out/sb3_frames/$ROUND"
read -r -a TIMES <<< "${TIMES:-57.5 59 63 66 69.5 72 75.5 78 80.5 82.2 84 86 88 89.2}"
FROM="${FROM:-56}"
TO="${TO:-89.5}"
END="$(python -c "import json; print(json.load(open(r'$(cygpath -m "$ROOT")/godot/data/storybook/sb00.json', encoding='utf-8'))['end'])")"
# a span that stops before the end: the scripted skip ends the run at TO (the mp4 is cut to TO - FROM either way)
SKIP=()
if python -c "import sys; sys.exit(0 if float('$TO') < float('$END') - 0.01 else 1)"; then SKIP=(--sb-skip-at "$TO"); fi
DUR="$(python -c "print(float('$TO') - float('$FROM'))")"

die() { echo "sb3_shoot: FAILED: $*" >&2; exit 1; }
[ -x "$G" ] || [ -f "$G" ] || die "no Godot at $G"
FF="$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" || die "no ffmpeg (imageio_ffmpeg)"
mkdir -p "$OUT"

echo "== wire"
python "$HERE/sb_wire_ink.py" || die "sb_wire_ink.py"

echo "== build"
dotnet build "$ROOT/godot/SurvivorUnchained.csproj" -v q -nologo >"$OUT/build.log" 2>&1 || { tail -30 "$OUT/build.log" >&2; die "dotnet build (log: $OUT/build.log)"; }

held=0
give() { if [ "$held" = 1 ]; then python "$TURN" give godot "$TURN_NAME" || true; held=0; fi; }
trap give EXIT
echo "== turn"
# --stale-ok: SB00 draws only the storybook plates, never her art or clips.
python "$TURN" take godot "$TURN_NAME" --wait 60 --stale-ok || die "no godot turn"
held=1

echo "== import"
"$G" --headless --path "$ROOT/godot" --import >"$OUT/import.log" 2>&1 || { tail -30 "$OUT/import.log" >&2; die "import (log: $OUT/import.log)"; }

echo "== frames"
SHOTS="$ROOT/godot/.shots"
mkdir -p "$SHOTS"
names=()
for t in "${TIMES[@]}"; do
  n="$(printf 'sb_sb00_%.2f.png' "$t")"
  names+=("$n")
  rm -f "$SHOTS/$n" "$OUT/$n"
done
list="$(IFS=,; echo "${TIMES[*]}")"
"$G" --path "$ROOT/godot" --resolution 1920x1080 --fixed-fps 30 -- --storybook sb00 --sb-shots "$list" --sb-from "$FROM" \
  >"$OUT/frames.log" 2>&1 || { tail -30 "$OUT/frames.log" >&2; die "frames run (log: $OUT/frames.log)"; }
for n in "${names[@]}"; do
  [ -f "$SHOTS/$n" ] || die "frame $n not written (log: $OUT/frames.log)"
  mv "$SHOTS/$n" "$OUT/$n"
done

echo "== capture"
AVI="$OUT/sb00_${ROUND}_${FROM}-${TO}.avi"
MP4="$OUT/sb00_${ROUND}_${FROM}-${TO}.mp4"
rm -f "$AVI" "$MP4"
"$G" --path "$ROOT/godot" --resolution 1920x1080 --write-movie "$AVI" --fixed-fps 30 -- --storybook sb00 --sb-from "$FROM" "${SKIP[@]}" --vo on \
  >"$OUT/capture.log" 2>&1 || { tail -30 "$OUT/capture.log" >&2; die "capture run (log: $OUT/capture.log)"; }
[ -s "$AVI" ] || die "capture not written (log: $OUT/capture.log)"
give

"$FF" -y -loglevel error -i "$AVI" -t "$DUR" -c:v libx264 -crf 16 -pix_fmt yuv420p -c:a aac -b:a 192k "$MP4" || die "ffmpeg"
rm -f "$AVI"

echo "== sheet"
files=()
for n in "${names[@]}"; do files+=("$OUT/$n"); done
python "$HERE/sheet.py" "$OUT/sheet_${ROUND}.jpg" 960 4 "${files[@]}" || die "sheet"
python "C:/Users/munch/Desktop/survivorsunchained/tools/half.py" "$OUT/sheet_${ROUND}.jpg" >/dev/null || die "half sheet"

echo "== done: $OUT"
grep -h '^voice \|storybook:' "$OUT/capture.log" || true
echo "frames: ${#names[@]}; capture: $MP4; sheet: $OUT/sheet_${ROUND}.jpg (+ _half)"

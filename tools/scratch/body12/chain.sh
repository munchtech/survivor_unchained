#!/usr/bin/env bash
# G3 chain (Body 12, 25 Oct 2026): install a new heroine body with every outfit, armor piece, tuck, cover and LOD.
#
#   bash chain.sh <body.glb> <out dir> [--install] [--stages s0,s1,...] [--post-steps <file>]
#
# Everything is built in <out>/stage, a shadow copy of the worktree's tools/ and godot/art/{people,armor,outfit}
# (the tools find their repo root from their own path, so they write into the stage, never into W). W changes only
# with --install (stage s9), which copies the install set into W and lists what is left (Godot reimport, skeleton
# dump, clip pack: the coordinator packs heroine.res / heroine_clips.json in main after the merge).
#
# Stages (default all but s9):
#   s0  preflight: hashes, disk, W clean, the stage copied, the export skeleton put in place
#   s1  outfit export (Blender turn): TWIST_CHAIN=1 NAPE=0 heroine_outfits.py on BLEND, every outfit + --body
#   s2  art post on the stage (heroine_body_post steps 1-5 and 7; NOT 7b axilla_fold / 7c shoulder_psd: the new body
#       carries its own shoulder shapes, and the old ones were stripped from its base): BASE = the body after it
#   s3  FOLLOW: outfits, hair and armor follow BASE -> BODY (rest moves, the helper bones' weights, the shoulder
#       shapes; tuck/cover records re-keyed and the new points' records filled). Runs $FOLLOW_CMD; NOT BUILT YET
#       (blocker 1): without it the chain goes on and measures the unfollowed art
#   s4  body swap: BODY copied in as people/heroine.glb, then every integration post-step in --post-steps
#   s5  armor pieces (Blender turn): build.py --all on BLEND (SRC), cover.py
#   s6  LODs: heroine_lod.py on the stage art
#   s7  numbers: g3meas.py (rest moves, follow zone, stale tuck) + wearcheck stage vs W's art (baseline)
#   s9  --install: copy the install set into W
set -u
BODY=$(cygpath -m "$1"); OUT=$(cygpath -m "$2"); shift 2
INSTALL=0; STAGES=s0,s1,s2,s3,s4,s5,s6,s7; POSTS=""
while [ $# -gt 0 ]; do case "$1" in
  --install) INSTALL=1; STAGES="${STAGES},s9";;
  --stages) STAGES=$2; shift;;
  --post-steps) POSTS=$(cygpath -m "$2"); shift;;
esac; shift; done
W=${W:-C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/armor-7}
MAIN=C:/Users/munch/Desktop/survivorsunchained
BL=${BL:-C:/Users/munch/Tools/blender-4.5.14-windows-x64/blender.exe}
BLEND=${BLEND:-C:/Users/munch/Desktop/survivorsunchained_inputs/armor_src/heroine_built_armScl3uf.blend}
# the export skeleton: the game skeleton of a TWIST_CHAIN export (twist_02-04, no scap/shoulder helpers). With the
# tracked one (84 bones) heroine_rig._game_skeleton finds no match and DROPS elbow_point_l/r and the glove fit.
SKEL_EXPORT=${SKEL_EXPORT:-C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8322a60-4855-4605-8c6c-f2390411a0ff/scratchpad/body5/a2/skel_new/heroine_skeleton.json}
BODY_BASE_REF=${BODY_BASE_REF:-C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8322a60-4855-4605-8c6c-f2390411a0ff/scratchpad/body5/fold/base/heroine.glb}
# the game skeleton for wearcheck (skin.py): scap included; the 8 shoulder helpers are in no dump yet (blocker 2)
SKEL_GAME=${SKEL_GAME:-C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8322a60-4855-4605-8c6c-f2390411a0ff/scratchpad/body6/s1/heroine_skeleton.json}
HERE=$(cd "$(dirname "$0")" && pwd -W 2>/dev/null || pwd)
ST=$OUT/stage; ART=$ST/godot/art/people; EXP=$OUT/exp; LOG=$OUT/logs
TURN="python $MAIN/tools/turn.py"
FOLLOW_CMD=${FOLLOW_CMD:-"python $ST/tools/assets/body_follow_post.py"}
WC_CLIPS=${WC_CLIPS:-idle_warden,idle_warden_town,run_warden,sword_heavy,sword_fore,idle_reaver,run_reaver_axes,axe_heavy,idle_arcanist,run_arcanist_wand,cast_flick,idle_stalker,run_stalker,crossbow_shoot,daggers_heavy,cast_raise,flask_drink,leap,reaver_show,warden_show,stalker_show,catch_breath}
export ANIM_OUT=${ANIM_OUT:-$MAIN/tools/anim/out}
mkdir -p "$OUT" "$LOG"
has() { case ",$STAGES," in *",$1,"*) return 0;; esac; return 1; }
say() { echo "G3 $*" | tee -a "$OUT/numbers.txt"; }
die() { say "STOP: $*"; exit 1; }
cd "$W" || die "no worktree $W"

if has s0; then
  [ -f "$BODY" ] || die "no body $BODY"; [ -f "$BLEND" ] || die "no blend $BLEND"
  say "s0 body $(sha1sum "$BODY" | cut -c1-8) blend $(basename "$BLEND") W $(git -C "$W" rev-parse --short HEAD)"
  FREE=$(df -BG /c | awk 'NR==2{gsub("G","",$4); print $4}'); [ "$FREE" -ge 50 ] || die "C: has ${FREE} GB free (< 50): sweep first"
  D=$(git -C "$W" status --porcelain -- godot/art tools | grep -v '\.uid$\|\.import$' | grep -v '^?? tools/assets/arm_graft/g2a/' | head -3)
  [ -z "$D" ] || say "s0 WARNING W has edits under godot/art or tools: $D"
  rm -rf "$ST"; mkdir -p "$ST/godot/art"
  # (tools without the scratch; the art the install touches, plus hair and textures the tools read)
  ( cd "$W" && tar --exclude=tools/scratch --exclude='__pycache__' --exclude=tools/anim/out -cf - tools ) | ( cd "$ST" && tar -xf - )
  for d in people armor outfit; do cp -r "$W/godot/art/$d" "$ST/godot/art/$d"; done
  cp "$SKEL_EXPORT" "$ST/tools/anim/data/heroine_skeleton.json"
  say "s0 stage $ST ($(du -sh "$ST" | cut -f1)), export skeleton $(python -c "import json;print(len(json.load(open(r'$SKEL_EXPORT'))['bones']))") bones"
fi

if has s1; then
  rm -rf "$EXP"; mkdir -p "$EXP"
  $TURN take blender "body12 g3: outfit export" --wait 3600 | tail -1
  ( cd "$ST" && TWIST_CHAIN=1 NAPE=0 "$BL" -b "$BLEND" --python tools/assets/heroine_outfits.py -- "$EXP/x" --body "$EXP/heroine.glb" ) > "$LOG/s1_export.log" 2>&1
  RC=$?; $TURN give blender "body12 g3: outfit export" | tail -1
  cp "$W/tools/assets/heroine_neck_graft.npz" "$ST/tools/assets/heroine_neck_graft.npz"   # (the build rewrites it)
  [ $RC -eq 0 ] && [ -f "$EXP/heroine.glb" ] || die "s1 export failed ($RC): $LOG/s1_export.log"
  grep -E "^RIG correctives|RIGID:|BODY |Traceback" "$LOG/s1_export.log" | head -8
  for f in "$EXP"/heroine_outfit_*.gltf "$EXP"/heroine_outfit_*.bin "$EXP"/heroine.glb "$EXP"/armor_index.json; do cp "$f" "$ART/"; done
  rm -rf "$ART/armor_tuck"; cp -r "$EXP/armor_tuck" "$ART/armor_tuck"
  say "s1 exported: $(ls "$EXP"/heroine_outfit_*.gltf | wc -l) outfits, $(ls "$EXP/armor_tuck" | wc -l) tuck records; elbow_point on the body: $(python "$HERE/g3meas.py" targets "$EXP/heroine.glb" | grep -c elbow_point)"
fi

if has s2; then
  ( cd "$ST" && python - "$ART" ) > "$LOG/s2_post.log" 2>&1 <<'EOF' || die "s2 art post failed: $LOG/s2_post.log"
import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "tools", "assets"))
import heroine_body_post as hbp
# (every step of the body post, as integration has it, but 7b/7c: the new body brings its own shoulder shapes,
# and the export's old ones would land on the outfits as follows of shapes the body no longer has)
SKIP = ("axilla_fold_post.py", "shoulder_psd_post.py", "heroine_lod.py")
_run = hbp.run
def run(*a):
    if os.path.basename(a[0]) in SKIP:
        print("G3 skipped", os.path.basename(a[0])); return
    _run(*a)
hbp.run = run
hbp.main([sys.argv[1], "--no-lod"])
print("MARKS", sorted(hbp.marks(os.path.join(sys.argv[1], "heroine.glb"))))
EOF
  cp "$ART/heroine.glb" "$OUT/base.glb"
  say "s2 base $(sha1sum "$OUT/base.glb" | cut -c1-8); $(grep MARKS "$LOG/s2_post.log")"
  python "$HERE/g3meas.py" same "$OUT/base.glb" "$BODY_BASE_REF" 2>/dev/null | tee -a "$OUT/numbers.txt"
fi

if has s3; then
  F=$(echo $FOLLOW_CMD | awk '{print $2}')
  if [ -f "$F" ]; then
    $FOLLOW_CMD "$OUT/base.glb" "$BODY" "$ST/godot/art" > "$LOG/s3_follow.log" 2>&1 || die "s3 follow failed: $LOG/s3_follow.log"
    say "s3 followed: $(grep -E '^FOLLOW' "$LOG/s3_follow.log" | tr '\n' ';')"
  else
    say "s3 BLOCKER 1: $F not built: the outfits/armor DON'T follow the body's post-chain (numbers below are unfollowed)"
  fi
fi

if has s4; then
  cp "$BODY" "$ART/heroine.glb"
  if [ -n "$POSTS" ]; then
    # one step a line: a command; {glb} = the stage heroine.glb, {art} = the stage people dir, {tools} = the stage tools
    while IFS= read -r L; do
      case "$L" in ''|'#'*) continue;; esac
      C=${L//\{glb\}/$ART/heroine.glb}; C=${C//\{art\}/$ART}; C=${C//\{tools\}/$ST/tools}
      say "s4 post-step: $C"; ( cd "$ST" && eval "$C" ) >> "$LOG/s4_posts.log" 2>&1 || die "s4 post-step failed: $L"
    done < "$POSTS"
  fi
  say "s4 body in: $(sha1sum "$ART/heroine.glb" | cut -c1-8); marks $(python "$HERE/g3meas.py" marks "$ART/heroine.glb")"
fi

if has s5; then
  $TURN take blender "body12 g3: armor build" --wait 3600 | tail -1
  ( cd "$ST" && SRC="$BLEND" TWIST_CHAIN=1 python tools/armor/build.py --all ) > "$LOG/s5_armor.log" 2>&1; RC=$?
  $TURN give blender "body12 g3: armor build" | tail -1
  grep -E "ADORN .*FAILED|REFUSED|through her skin|Traceback" "$LOG/s5_armor.log" | head -12 | sed 's/^/G3 s5 /' | tee -a "$OUT/numbers.txt"
  ( cd "$ST" && python tools/armor/cover.py ) > "$LOG/s5_cover.log" 2>&1 || say "s5 cover.py failed"
  say "s5 armor exit $RC"
fi

if has s6; then
  ( cd "$ST" && python tools/assets/heroine_lod.py "$ART" ) > "$LOG/s6_lod.log" 2>&1 || say "s6 LOD failed: $LOG/s6_lod.log"
  grep -iE "^LOD|triangles|tris" "$LOG/s6_lod.log" | tail -12 | sed 's/^/G3 s6 /' | tee -a "$OUT/numbers.txt"
fi

if has s7; then
  python "$HERE/g3meas.py" zone "$OUT/base.glb" "$ART/heroine.glb" "$ST/godot/art" | tee -a "$OUT/numbers.txt"
  [ -d "$OUT/wc_base" ] || ( WC_ART=$W/godot/art ANIM_PEOPLE=$W/godot/art/people python "$W/tools/armor/wearcheck.py" --clips "$WC_CLIPS" --out "$OUT/wc_base" ) > "$LOG/s7_wc_base.log" 2>&1
  cp "$SKEL_GAME" "$ST/tools/anim/data/heroine_skeleton.json"
  ( cd "$ST" && WC_ART=$ST/godot/art ANIM_PEOPLE=$ART python tools/armor/wearcheck.py --clips "$WC_CLIPS" --out "$OUT/wc" ) > "$LOG/s7_wc.log" 2>&1 || say "s7 wearcheck failed: $LOG/s7_wc.log"
  python "$HERE/g3meas.py" wc "$OUT/wc_base" "$OUT/wc" | tee -a "$OUT/numbers.txt"
fi

if has s9 && [ $INSTALL -eq 1 ]; then
  P=godot/art/people; A=godot/art/armor
  for f in heroine.glb armor_index.json heroine_outfit_{warden,arcanist,ranger,reaver}.{gltf,bin} heroine_outfit_{warden,arcanist,ranger,reaver}_lod.{gltf,bin}; do cp "$ART/$f" "$W/$P/$f"; done
  for d in armor_tuck armor_cover; do cp "$ART/$d"/*.bin "$W/$P/$d/"; cp "$ST/$A/$d"/*.bin "$W/$A/$d/"; done
  cp "$ST/$A"/*.gltf "$ST/$A"/*.bin "$ST/$A"/*.sockets.json "$ST/$A/armor_index.json" "$W/$A/"
  for f in "$ART"/head_tex/*; do cmp -s "$f" "$W/$P/head_tex/$(basename "$f")" || cp "$f" "$W/$P/head_tex/"; done
  for f in "$ST"/godot/art/outfit/*; do cmp -s "$f" "$W/godot/art/outfit/$(basename "$f")" || cp "$f" "$W/godot/art/outfit/"; done
  say "s9 installed into W: $(git -C "$W" status --porcelain -- godot/art | grep -v '\.uid$' | wc -l) files changed"
  say "s9 LEFT: Godot reimport; dump the skeleton (anim_skeleton.gd -> tools/anim/data/heroine_skeleton.json, 100 bones);"
  say "s9 LEFT: pack heroine.res/heroine_clips.json locally (ARM_CHAIN rest tracks), NOT committed; dotnet test; commit"
fi
say "done: $STAGES"

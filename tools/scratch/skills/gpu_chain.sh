#!/usr/bin/env bash
# After the tell sounds: the skills' sprites (Krea), then the twelve clips (LTX), a clip retried once if it fails.
OUT=/c/Users/munch/Desktop/survivorsunchained/tools/comfy/out
TASK="/c/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/tasks/b5f3idx6w.output"
until grep -q "sfx exit" "$TASK"; do sleep 15; done
echo "sounds done: $(grep 'sfx exit' "$TASK")"
python tools/comfy/fx_sprites.py make && echo "sprites made"
for c in frost_spikes holy_ring blood_scythe moon_burst ice_shatter poison_cloud bramble_burst gold_flare fireball_impact dust_chop shadow_wisps leaf_burst; do
  for try in 1 2; do
    rm -rf "$OUT/clips/_$c"
    if python tools/comfy/fx_clips.py "$OUT/clips" "$c"; then echo "clip $c made"; break; else echo "clip $c failed (try $try)"; sleep 30; fi
  done
done
curl -s -X POST -H 'Content-Type: application/json' -d '{"unload_models": true, "free_memory": true}' http://127.0.0.1:8188/free >/dev/null && echo "freed"

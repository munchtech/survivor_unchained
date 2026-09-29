# Survivor Unchained: the Godot test slice

A night fight in the Verge, rebuilt in Godot 4.5 (C#, Forward+ renderer) to
compare with the three.js game before deciding on an engine. It uses the web
game's own assets and the Verge as the web game builds it:

- `assets` links to `../public/assets` (the Quaternius people, kits, weapons;
  Godot imports them in place, KTX2 textures included);
- `data/verge` is the zone exported from the running web game by
  `tools/godot/export_zone.mjs` (the ground's heights and paint, where every
  tree, rock and prop stands, the lights);
- `art/ground` is the same photoscanned Poly Haven ground, stacked into
  texture arrays by `tools/godot/ground_atlas.py`.

## Running it

    tools/godot/setup.sh                 # Godot 4.5.1 .NET, .NET 8, software Vulkan
    tools/godot/run.sh                   # play (WASD), in a window if you have one
    tools/godot/run.sh --fixed-fps 10 -- --shot fight --seconds 1.5
                                         # headless: a screenshot in godot/.shots/

Slice options go after `--`: `--shot NAME --seconds S [--every T --count N]`
(screenshots, `src/Shots.cs`), `--at X,Z` (where to stand), `--still` (the
place without the fight), `--risen N`, `--start N`, `--grass R`, `--pitch`,
`--dist`. Headless runs use Mesa's software Vulkan: seconds per frame, so
keep shots short; on a real GPU it runs in real time.

## What is where

- `src/Slice.cs` puts it together: the zone, night, the fire, the fight.
- `src/World/`: the zone data, ground (`shaders/terrain.gdshader`, the web
  game's terrain shader ported), flora and props, grass
  (`shaders/grass.gdshader`), the campfire (GPU particles).
- `src/Actors/`: people from Quaternius parts on one skeleton, with the
  Universal Animation Libraries (`People.cs`); weapons normalised to one grip
  (`Arms.cs`, the web game's `arms.ts`); the survivor (an AnimationTree: the
  swing on the upper body over the run); the Risen.
- `src/Fight.cs`: the fight (autopilot for screenshots), hitstop, shake, the
  follow camera; `src/Fx/Hits.cs`: blood, decals, numbers, the blade's arc.

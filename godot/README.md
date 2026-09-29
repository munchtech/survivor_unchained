# Survivor Unchained in Godot

The game, being ported from the web build (three.js) to Godot 4.5 (C#,
Forward+ renderer). The web game keeps working until the port reaches
parity. The port uses the web game's own assets and its zones as the web
game builds them:

- `assets` links to `../public/assets` (the Quaternius people, kits, weapons;
  Godot imports them in place, KTX2 textures included);
- `data/zones/<id>` is each zone exported from the running web game by
  `tools/godot/export_zone.mjs` (the ground's heights and paint, where every
  tree, rock and prop stands, the lights, the water, the colliders, and the
  landmarks as one glTF); `data/content` is the game's content as JSON
  (`tools/godot/export_content.mjs`);
- `art/ground` is the photoscanned Poly Haven ground, stacked into texture
  arrays by `tools/godot/ground_atlas.py`.

## Running it

    tools/godot/setup.sh                 # Godot 4.5.1 .NET, .NET 8, software Vulkan
    tools/godot/run.sh                   # play, in a window if you have one
    tools/godot/run.sh --fixed-fps 30 -- --quick warden --zone verge --time night --auto --shot verge --seconds 8
                                         # headless: a screenshot in godot/.shots/
    cd godot/tests && dotnet test        # the game's logic, without a screen

Until the title and creation screens are ported, the game starts a journey
straight away. Options go after `--`:

- `--quick warden|reaver|arcanist|stalker`: a new survivor of that calling
  (with `--name`, `--bg`, `--weapon`, `--blessing`);
- `--zone lowford|waystation|verge`: where to start (past the prologue, which
  then counts as done), `--time day|night|dusk|dawn`, `--at X,Z`;
- `--continue`: the last journey saved (saves are in Godot's user folder);
- `--auto`: a crude player drives (`src/Game/Autopilot.cs`); `--auto idle`
  only takes the level-up cards;
- `--shot NAME --seconds S [--every T --count N]`: screenshots
  (`src/Shots.cs`).

Keys: WASD to move, Space to dash, Q for the calling's skill, E to use or
talk, R to drink a draught, 1-4 to pick a card or an answer (X rerolls the
cards, B then a number banishes one), Escape to pause.

Headless runs use Mesa's software Vulkan: seconds per frame, so keep shots
short; on a real GPU it runs in real time.

The first slice (a night fight by the Verge's Hunters' Blind, the zone
viewer) is still here: `tools/godot/run.sh res://scenes/slice.tscn -- --zone
waystation --time night --shot town` (options in `src/Slice.cs`). To set a
Godot shot beside the web game's: `node tools/godot/web_shot.mjs` (the web
game at the same place and hour; needs the dev server), then
`python3 tools/godot/compare.py web.png godot.png out.jpg`.

## What is where

- `logic/`: the game without a screen, in plain C# (it builds into the game
  and into the tests): `Core` (json, noise, random), `Sim` (the fight: battle,
  creatures' minds, weapons, collision, stats, the level-up draft), `Rpg`
  (the character, items, callings), `Content` (weapons, blessings,
  creatures), `World` (the world's state and memory, rules, dialogue, quests,
  saves, the zones' exported data) and `Play` (the journey, the zones'
  runtimes: the prologue, the Waystation and its townsfolk, the Verge).
  Zone runtimes reach the game through `IZoneHost` and the view through
  `IZoneLook`, so the tests run them end to end with fakes (`tests/FakeHost.cs`).
- `src/Game/`: `Game.cs` (the host: zones, travel, saves, the prompt, the
  fall, conversations, the draft), `WorldScene.cs` (a zone and its fight,
  stepped at 60 Hz, with hitstop; what a runtime reaches into), the follow
  camera, the controls (keys, mouse and pad as named actions), the autopilot.
- `src/World/`: a zone stood up from its data: the ground
  (`shaders/terrain.gdshader`), flora and props (`shaders/kit.gdshader`),
  grass, water, fires, the landmarks, the lights, the sky and grade
  (`Atmosphere.cs`).
- `src/Actors/`: people from Quaternius parts on one skeleton with the
  Universal Animation Libraries (`People.cs`), weapons in hand (`Arms.cs`),
  the survivor (`PlayerView.cs`: an AnimationTree, the swing on the upper
  body over the run), people in the world (`PersonView.cs`), the crowd
  (`CrowdView.cs`; each creature's look in `Visuals.cs`), the Ford-Warden
  (`BossViews.cs`).
- `src/Fx/`: the fight made visible (`BattleFx.cs`: sparks, marks on the
  ground, what is in the air and on the ground, lights), blood and numbers
  (`Hits.cs`), the colours of each school (`Palette.cs`).
- `src/Ui/`: the HUD, the draft and the conversation panel (`GameHud.cs`),
  names and words over heads (`Voices.cs`).

Stand-ins still to be replaced: the wolves and boars (shapes, until the real
creatures), the KayKit props (a torch, a bucket, a grave marker), and the
shop, storeroom, map, journal and menus (with the rest of the interface).

Fonts: Cinzel and Alegreya Sans (SIL Open Font License, `art/fonts`), as the
web game uses them.

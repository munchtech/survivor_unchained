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

The game opens on its title (a stranger by a fire on the Low Ford road).
Options go after `--`:

- `--new`: straight to making a survivor;
- `--quick warden|reaver|arcanist|stalker`: a new survivor of that calling,
  no title (with `--name`, `--bg`, `--weapon`, `--blessing`);
- `--zone lowford|waystation|verge`: where to start (past the prologue, which
  then counts as done), `--time day|night|dusk|dawn`, `--at X,Z`;
- `--continue`: the last journey saved (saves are in Godot's user folder);
- `--auto`: a crude player drives (`src/Game/Autopilot.cs`), from the title
  on; `--auto idle` only takes the level-up cards;
- `--open inventory|character|journal|map|pause|rest|stash|shop:ID|chapter|all`,
  `--open talk:ID`, `--open draft`: a screen, a conversation or the level-up
  draft opened a moment in (`--every T` between several); `--bare` hides the
  world, for quick pictures of the interface;
- `--shot NAME --seconds S [--every T --count N]`: screenshots
  (`src/Shots.cs`);
- `--log S`: a line every S seconds (the fight, the zone, the sound);
- `--wav PATH`: no speakers; the game's sound is written to a WAV on exit
  (with `--fixed-fps 60` it is exactly as long as the run); `--sound`: sound
  even in a headless run (for timing the mixer against Godot's dummy driver).

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
- `src/Ui/`: the look shared by every screen (`Style.cs`, the icons in
  `Glyphs.cs`), the HUD (`GameHud.cs`), the level-up draft and the
  conversation panel (`Panels.cs`), the screens over the game (`Overlay.cs`;
  the pack, a shop, the storeroom in `Pack.cs`, the self and the journal in
  `Book.cs`, `MapScreen.cs`, the pause menu, settings, controls, a night's
  rest and the chapter's end in `Menus.cs`), the title and making a survivor
  (`Front.cs`), a person drawn live in a frame (`Portrait.cs`), names and
  words over heads (`Voices.cs`).
- `src/Audio/`: the web game's sound, still made without a single sample:
  `Synth.cs` (tones, filtered noise and FM bells, four buses into one dark
  room and a compressor, mixed on its own thread into Godot's audio streams,
  keeping a little sound queued and more when the machine stalls),
  `Sfx.cs` (every sound the game makes), `Ambience.cs` (wind, leaves, water,
  a town, a fire, the blight's hum, crickets; birds, owls, the smith),
  `Music.cs` (the score, composed as it plays) and `SoundBridge.cs` (what
  happens, turned into all of that).

Stand-ins still to be replaced: the wolves and boars (shapes, until the real
creatures), the KayKit props (a torch, a bucket, a grave marker), and the
items' pictures (icons for now).

## Desktop builds

    tools/godot/setup.sh --templates     # once: Godot's export templates
    tools/godot/export.sh [windows|linux|macos|all]

Builds land in `release/godot/<platform>/` (a `.pck` beside the executable
and a `data_SurvivorUnchained_*` folder of .NET assemblies; ship the folder
whole). The presets are in `export_presets.cfg`. The macOS build is
ad-hoc signed, not notarised: on a Mac, right-click and Open the first time
(or `xattr -cr "Survivor Unchained.app"`).

Fonts: Cinzel, Alegreya and Alegreya Sans (SIL Open Font License,
`art/fonts`), as the web game uses them.

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
- `--icons [a,b]`: the items photographed afresh (all, or those named), then
  quit (they are kept in the user folder's `icons/`; `--icons-fresh` retakes
  them as the game starts);
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
  Universal Animation Libraries (`People.cs`: the body hidden under the
  clothes, a woman's figure from two shape keys, skin tone, cloth dyed by
  `shaders/person.gdshader`), weapons in hand (`Arms.cs`), the survivor
  (`PlayerView.cs`: an AnimationTree, the swing on the upper body over the
  run), people in the world (`PersonView.cs`), the beasts (`Beasts.cs`:
  modelled, rigged and animated wolves, boars and lamplings from
  `art/beasts`, the moves their clips lack composed over their poses, a
  lampling's hat and lamp made in code and worn on its head), the crowd
  (`CrowdView.cs`; each creature's look in `Visuals.cs`), the Ford-Warden
  (`BossViews.cs`).
- The crowd is vertex animation (`Vat.cs`, `shaders/vat.gdshader`): each
  kind of creature is played through its clips once and every vertex's pose
  written into two textures; a kind is then one MultiMesh, however many
  there are (people slimmed to about 4,000 vertices with meshoptimizer
  first). Bakes are kept in Godot's user folder (`vat/`) between runs;
  `--vat-fresh` bakes again, and bump `Vat.Version` when what a bake holds
  changes. `--horde 40:wolf,20:risen` puts a crowd round the survivor,
  `--drops` one of everything that lies on the ground (embers of three
  worths, gold, a draught, a lodestone, gear, a chest), and `--cam D`
  brings the camera in, for pictures and timing.
- `src/Fx/`: the fight made visible (`BattleFx.cs`: sparks, marks on the
  ground, what is in the air and on the ground, lights; its particles drawn
  from Kenney's CC0 sprites, `Sprites.cs`, art/fx: puffs of smoke, glints,
  spattered earth, bursts of fire, rune circles on hallowed ground), blood (`Gore.cs`:
  sprays, pools that spread and dry, a burst body's pieces thrown, bleeding
  where they land, sinking), sprays, numbers and blade arcs (`Hits.cs`), the
  colours of each school (`Palette.cs`).
- `src/Ui/`: the look shared by every screen (`Style.cs`, the icons in
  `Glyphs.cs`), the items' pictures (`ItemPhotos.cs`: each item photographed
  once in a little studio of its own, lit by a studio HDRI, and kept; what is
  photographed is in `ItemModels.cs`: the weapons in hand, and the rest made
  in code with `src/World/Shapes.cs`, turned, swept, cut out and draped), the HUD (`GameHud.cs`), the level-up draft and the
  conversation panel (`Panels.cs`), the screens over the game (`Overlay.cs`;
  the pack, a shop, the storeroom in `Pack.cs`, the self and the journal in
  `Book.cs`, `MapScreen.cs`, the pause menu, settings, controls, a night's
  rest and the chapter's end in `Menus.cs`), the title and making a survivor
  (`Front.cs`), a person drawn live in a frame (`Portrait.cs`), names and
  words over heads (`Voices.cs`).
- `src/Audio/`: the web game's sound, made on the spot, with recordings laid
  under it where a real thing sounds best: `Synth.cs` (tones, filtered noise,
  FM bells and recorded takes, four buses into one dark room and a
  compressor, mixed on its own thread into Godot's audio streams, keeping a
  little sound queued and more when the machine stalls), `Recordings.cs`
  (art/sound, Kenney's CC0 packs: blows, bodies falling, footsteps by
  ground, coins, doors, pages, the interface's clicks; CC0 field recordings
  from OpenGameArt: a river, a fire, crickets, birdsong, an anvil),
  `Sfx.cs` (every sound the game makes), `Ambience.cs` (recorded water,
  fire, crickets and birds, each looped and played wide; made wind, leaves,
  a town and the blight's hum; owls, creaking boughs, the smith),
  `Music.cs` (the score, composed as it plays) and `SoundBridge.cs` (what
  happens, turned into all of that).

The web game's KayKit props (graves, a crypt, ruins, fences, lamp posts, the
Lowford gate, the farm's mills) come through the export tagged (each a node
`kk-PACK-NAME-N` in `landmarks.glb`, its size in `data/zones/kaykit.json`) and
are replaced where they stand (`src/World/Pieces.cs`): by a piece of the
world's kits where one fits, otherwise made in code to the same size in
photographed stone, wood and earth (`art/materials`, Poly Haven, CC0;
`src/World/Made.cs`). `--icons kk:halloween/crypt` photographs one alone,
`--icons kit:props/Torch_Metal` a kit piece. The KayKit packs themselves do
not load in Godot (they are meshopt-compressed).

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

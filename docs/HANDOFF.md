# Handoff: picking up Survivor Unchained

Notes for a new Claude Code session (or anyone) carrying the work on from
the cloud sessions that built the Godot game so far. Those sessions ran
without a GPU and could only render a frame every 10–15 seconds; on a
machine with a real GPU, run the game in a window and iterate on visuals
in real time.

## Repo
- munchtech/survivor_unchained, branch `claude/vigilant-galileo-l6jqyx`.
  Work on this branch, commit and push as you go; no PR unless asked.
- The real game is the Godot 4.5.1 (.NET/C#) project in `godot/`. The repo
  root (`src/`, `public/`, Vite and Three.js) is the older web build it was
  ported from. `godot/assets` links to `public/assets`.
- Read `README.md` and `godot/README.md` first: running, every
  command-line option, the code map and the asset tools.

## Setup
- Godot 4.5.1 .NET and the .NET 8 SDK. Open `godot/project.godot` and
  press F5, or build with `dotnet build godot/SurvivorUnchained.csproj`.
- Tests: `cd godot/tests && dotnet test` (all pass). `StoryLint.cs` reads the
  story whole (unreachable nodes, journal lines never earned, facts asked
  about but never set, items wanted but never obtainable, pronoun drift):
  keep it green when writing content. Voices: `docs/VOICES.md`; the
  story's secrets and where it goes: `docs/STORY_BIBLE.md`.
- On Windows, `godot/assets` may arrive as a tiny text file instead of a
  symlink: clone with `-c core.symlinks=true` (Developer Mode on), or
  delete it and copy `public/assets` into its place.
- `tools/godot/run.sh` is the Linux headless runner the cloud sessions
  used; elsewhere run Godot directly: `<godot> --path godot -- <options>`.
- The Blender pipelines in `tools/assets/*.py` need `pip install bpy==4.2.0`
  (Python 3.11 venv), or run them with Blender itself.
- Game options go after `--`:
  - `--quick warden|reaver|arcanist|stalker`
  - `--sex female --figure 1.2 --skin deep --palette dusk`
  - `--zone lowford|waystation|verge|arena --time day|night`
  - `--people pack|dead|lamplings|kerchiefs`
  - `--art ID --cast T`, `--auto`, `--open inventory|character|journal|...`
  - `--shot NAME --seconds S` (screenshots land in `godot/.shots/`)

## The game as designed (all implemented)
- **Two halves.** By day the story: no ember, character XP, enemy packs
  placed in the world, learned skills. At night the ember arenas: start at
  ember 1, a great blessing at the start and another at 15 minutes, a boss
  at 30 minutes, and endless play after the win.
- **The prologue night (Lowford) has ember**, which wears off at dawn:
  that is how the mechanic is introduced. At night, ember scars in the
  Verge pull you into arenas. All four story beats are night arenas.
- **Skills.** A skill seen burning in an arena is "discovered" and can be
  learned by day, from tomes or from your calling (one every third level).
  Each needs an attribute: Wits for spells, Resolve for holy and nature,
  Might for melee, Finesse for thrown and shot. Day skill slots open at
  levels 1, 4 and 8.
- **Zones:** Lowford (prologue), the Waystation (town hub), the Verge (a
  wood). **Callings:** warden, reaver, arcanist, stalker.
- **The Wayfinder's table** offers arenas, each with a tier, the people
  who hold it, and oaths (map conditions).
- **Combat:** dash as a skill, movement abilities, starting blessings.
- **Code:** `godot/logic/` is pure C# logic (`Sim/Battle.cs`, `Arena/`,
  `Play/Journey.cs`, `Play/Zones/*`, `Rpg/`, `Content/`, `Maps/`);
  `godot/src/` is the Godot view (`Actors/People.cs`, `Fx/BattleFx.cs`,
  `Ui/`, `Game/Game.cs`, `Audio/`). Shaders in `godot/shaders/`, content
  JSON in `godot/data/content/`, xUnit tests in `godot/tests/`.

## The woman survivor's body (most recent work)
- `tools/assets/woman_body.py` builds it from the owner's ComfyUI figure,
  producing `godot/art/people/woman.glb` and `woman_mask.png`.
- `People.Woman` draws it with `shaders/woman_skin.gdshader`: through the
  mask (red skin, green hair, blue suit) the shader tones her skin, colours
  her hair and dyes her suit in the calling's colours. A "Figure" shape key
  drives the creation slider. `Loadouts.HerBody = "woman"`.
- Fixed recently: she was back to front on her skeleton, and her hands
  were remade (palm down, natural size, fingers laid like the skeleton's,
  joints placed per finger) to cure "hot dog fingers".
- **Never checked in a real window:** the title screen (sitting by the
  fire), character creation, holding weapons such as the staff, a fight.
- **Known leftovers:** her jab fist only half closes; her little finger is
  short.
- **Checking a model:** a small GDScript scene that plays the game's clips
  (`res://assets/people/UAL1.glb`, `UAL2.glb`) on `woman.glb` beside
  `res://assets/people/Superhero_Female_FullBody.gltf` and saves
  side-by-side screenshots is the quickest check of any model change.

## The brief
Take the game to release-candidate quality ("Diablo 5 RC" good) in every
respect. Priorities:
- the epicness of the Ember and Blade skills: VFX, impact, sound, hit feel;
- dialogue, choices and their outcomes;
- graphics;
- the day-story / night-arena structure.

Full control: build tools, download software and assets, restructure
whatever needs it. Take your time.

Where the last session left off:
- **Graphics backlog:** moonlit nights and colour grade (half done);
  combat VFX (slash arcs, hit glints, impacts); spell effects and a more
  living world.
- **From recent screenshots:** the arena ground reads flat and muddy from
  the top-down camera; skills have little visual punch; nights are very
  dark.

## How to work
- Start by playing through: title, creation, prologue, Waystation, Verge,
  an arena. Note what falls short of the bar, then make a prioritised task
  list before any big change.
- Check every visual change by running the game; run `dotnet test` before
  each commit.
- **Assets:** prefer CC0 (Quaternius, Kenney, Poly Haven). CC-BY is fine
  with credit in `public/assets/CREDITS.md` and in the in-game credits
  (`godot/src/Ui/Front.cs`). Check every licence before using an asset.
- **Secrets:** never commit or print API tokens. Pass them through
  environment variables (e.g. `SKETCHFAB_TOKEN`) and ask the owner to set
  them.
- **Style:** match the codebase. Comments are short prose in British
  spelling ("colour") that say why. Keep the READMEs and credits current.

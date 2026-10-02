# Survivor Unchained

A persistent, emergent ARPG built on Survivors-style automated combat, in a
stylized dark-fantasy world rendered with Three.js. This is the **beta
vertical slice**: one night on the Low Ford road, one town, one wood outside
it, two deep questlines with many ways through them, two mysteries left
open, and a world that remembers what you did.

```
npm install
npm run dev        # http://localhost:5173
npm test           # content integrity, questline scenarios, combat sim
npm run build      # typecheck + production build
```

## Playing

| | Keyboard and mouse | Pad |
|---|---|---|
| Move | WASD / arrows | left stick |
| Dash | Space / Shift | A |
| Art in hand | Q / right mouse | X |
| Arts (which, rank, facets) | K | Menu |
| Draught | R | Y |
| Interact, talk | E / F | B |
| Pack · Self · Journal · Map | I (Tab) · C · J · M | View · then Menu |
| Level-up draft | 1–4 to pick, X reroll, B banish | D-pad and A, X, Y |
| Pause (save, sound, graphics, controls) | Esc / P | Menu |

The full list is under Controls, on the title and in the pause menu, where
any gameplay key can be moved (click it, press the new one; Defaults undoes).

Skills (weapons) fire on their own. You choose where to stand, when to
dash, which skill to take or rank up each time the ember rises (anyone can
take any skill; a calling leans a little toward its own style), what each
skill evolves into at rank 8, and, out of combat, what to say and to whom.
The game has two halves, the day's and the night's. The story is walked
and talked through by day: the ember sleeps, the survivor fights with what
they carry (their gear's skills, the art in hand, the dash) and every fight
teaches them (character levels). The ember burns only in the dark. The
first night, on the Low Ford road, is where you learn it: the dead leave
its stones, it rises, you choose skills and blessings, and at dawn it goes
out and everything it built goes with it. After that the night belongs to
the **ember arenas**: at the story's turns, and where danger is marked, the
survivor is pulled into one, seen from higher and further out, the ember
starting again from nothing, a horde that thickens by the minute, cards
coming often. At the half hour what
rules the horde comes; kill it and the fight is won. The arena goes on
after that, harder by the minute, for as long as you care to see how far
your build goes: leave by the way out that opens where the boss fell, or
fall (fallen after the win, it is still won). The cards stay in the arena;
what comes out is experience for the time survived, gold and gear, the
skills discovered (to be learned in the world) and how the story goes on.
Lose a story fight and the story goes on without the win; the Wayfinder's
table lets you take it again, and offers arenas of its own.

Blessings are the night's too. A great blessing is chosen as an arena
begins (and at the prologue's first ember) and another at its fifteenth minute, from all twelve, whoever the
survivor is; each has three ranks, and the second may deepen the first.
Build-shaped blessings come at ember levels 4, 10, 18, 28, 40 and on, on top
of that level's skill (a milestone may deepen a great blessing held).

## On the desktop

The game is a desktop game first: an Electron window around the build, so
it runs full-screen with the full-size (4K and 2K) textures.

| | |
|---|---|
| `npm run desktop` | Build, then play in the desktop window |
| `npm run desktop:dev` | The window around the dev server (`npm run dev` running) |
| `npm run dist` | Linux release in `release/` (tarball; AppImage where its tools run) |
| `npm run dist:win` | Windows zip (from any OS); `dist:win-installer` builds the installer on Windows |
| `npm run dist:mac` | macOS disk image (on a Mac) |

The Desktop builds workflow (Actions tab, run by hand) builds the Windows
installer, the macOS image and the Linux AppImage on their own systems.
F11 or Alt+Enter toggles full-screen; Settings remembers a window or
full-screen; saves live in the app's own data folder. As root (containers),
Electron needs `--no-sandbox`.

## What is in the slice

- **Character creation**: name, look (the calling's colours repainting
  armour and cloth, a dyed cloak or none, skin, hair, headgear), archetype
  (Warden, Reaver, Arcanist, Stalker), starting weapon, the art in hand, and
  a background (hunter, scholar, devout or outcast). Backgrounds are
  knowledge: they open dialogue options, routes and readings of the world
  that other survivors never see.
- **The Low Ford** (tutorial): wake by a dying fire, learn ember, hold a
  broken Watch-post, find a barrow and a knight who guards it, and relight
  the lamps to break the Ford-Warden's ward. Grimtunnel steals its heart.
- **The Waystation** (hub): the inn and its stash, a tavern, the smithy,
  merchants, the shrine, a notice board, homes, the square, a garden
  nobody visits, the Watch, and gates east and north. Twelve residents with
  places, routines, barks, opinions of each other, shops and memories.
- **The Beast Problem**: the wolves are sick, not bold. Kill them for the
  bounty, lie about it, find the dead wolf and the green stream, have Wenna
  test the water, walk into the Hollow and speak with Greymuzzle, run with
  the Pack, talk the diggers' foreman into moving his outflow, break the
  pump, blow it up, or do nothing and watch the wolves come to the gate.
- **The Missing Caravan**: Harlan's nephew is in a Kerchief cage. Follow
  the ruts, read the toll ledger, find the clerk who sent them the wrong way, break into Pell's
  warehouse by key or by night, bluff Redcowl out of his own camp, show him
  who sold him out, buy the prisoners, fight for them, return the cargo,
  sell it, or keep it.
- **Thornhollow Verge** (the outside zone): reactive factions (the Pack,
  the Kerchiefs, the Dig) whose disposition you set by what you know and
  do; a director that surges; named nemeses; the stream, the Roost, the
  Dig, the Hollow (a den in the rock, beds of flattened grass, bones), a
  Moon Grove behind burnable brambles (moonflowers, a pale tree, a ring of
  standing stones round a shrine). Elites drop gear rolled where it falls;
  the light over it says how good it is.
- **Breadcrumbs**: the Sealed Vault (a black door, a sigil fragment,
  bootprints going in and not out) and the Thing Below (tremors, a pit, and
  something enormous at the bottom of it).
- **Death as content**: your body keeps half your gold where you fell; the
  thing that killed you takes one of your things and a name, and waits for
  you (put it down and you get that very thing back). You wake at the shrine, wounded, and Chid has something to say.
- **Persistence**: every save holds the character, the world, where you
  stand and the ember build you carry; saves migrate forward, never vanish.
- **The map**: each zone drawn by hand from itself (hill shading, contours,
  ink trees, footprints of every house), fog where you have not walked,
  places named once found.
- **A town that notices**: people keep routines and move with their
  troubles (Harlan watches the east gate while the caravan is missing);
  nameless townsfolk run errands between the stalls, the well, the board
  and their doors, children chase each other round the square, a watchman
  walks the rounds by torchlight, and what they mutter as you pass is what
  the town thinks of what you did; the
  notice board changes as the world does, and each morning's report says
  who heard what about you overnight. People quote your deeds back to you,
  size up your calling, notice when you have become dangerous, and keep
  the promises the text makes (Maeca's rule at the Hollow, a promise to
  Greymuzzle); one of them, Maeca, can be more than a friend. Intimate
  scenes cut away unless the settings ask for them in full.
- **The journal**: what each person has on their mind, how they feel about
  you in words, what the world remembers, and where you stand with the
  Watch, the Coyle Company, the Kerchiefs, the Pack and the Dig.
- **The chapter's end**: when both questlines are settled, Vonnra reads your
  fortune (it is your own story, read back), and the chapter closes on a
  page worked out from the world: what was done, what is still waiting, who
  remembers you and why.

## How the world works

Content never touches state directly. It asks questions (`Cond`) and makes
changes (`Effect`) as plain data (`src/world/logic.ts`): quests, dialogue,
zone scripts, shops and the daily simulation all speak that language, which
is what lets one quest have six solutions without six code paths, and what
the journal, the tests and the chapter's end read back.

- **History and gossip**: deeds are history events with witnesses and
  reactions; each night news travels one step along who-talks-to-whom
  (`src/content/rules.ts`), so a lie told to Holloway comes back to him when
  the world contradicts it.
- **Clocks**: rules run every dawn: the wolves escalate, the prisoners do not
  wait forever, a cured stream heals over days, the Dig digs deeper.
- **Dispositions**: in the Verge, factions are hostile, neutral or allied
  depending on what you know, wear and have done; nothing neutral is ever
  hurt by accident, so a peace holds until you break it on purpose.

## Look and sound

Dark fantasy. People are Quaternius's Universal Base Characters, outfits
and animation libraries (CC0), with a woman's figure shaped offline
(`tools/assets/figure.py`) and crowd figures baked from the same people. In
the Godot game a woman survivor has a body of her own, a figure made in
ComfyUI for the game, rigged to the same skeleton so every clip plays on her
(`tools/assets/woman_body.py`, fitted from donizaki's anime base, CC BY,
`tools/assets/anime_female.py`); her hair and close-fitting suit are her
own, the suit dyed the calling's colours. Weapons are CC BY models from Sketchfab (credited in the game and in
`public/assets/CREDITS.md`). Houses are put together from Quaternius's
Medieval Village MegaKit on its 2 m grid (`src/world/zones/houses.ts`), with
the Fantasy Props and Stylized Nature kits (CC0), each material weathered in
its shader to suit a darker world; what the kits lack (the town's well) is
modelled for the game in Blender, in the kits' own sheets (`tools/models/`). Trees, bushes and stone are the nature
kit's, instanced by the thousand in culled cells, the foliage recoloured for
autumn and blight and the stone mossed (`src/render/scatter.ts`). The
people's and the kits' 2K and 4K sheets ship as KTX2 (Basis UASTC,
`tools/assets/ktx2.py`), transcoded to BC7 or ASTC on load: full resolution
at a quarter of the video memory of decoded images; older props
are KayKit (CC0, Kay Lousberg); with ground photoscanned by Poly Haven (CC0: meadow, forest floor, dirt, mud, setts, rock, burnt earth, blended by height, `tools/assets/ground.py`), generated grass, water and sky; N8AO, bloom, AgX and
a grade pass; VAT crowds and GPU particles for the hordes. Trees between the
camera and the survivor thin out; streams meander and know how deep they
are. Sound is procedural, with no samples: a score composed as it plays
(pads, a wandering melody, drums as thick as the fight), ambience beds that
follow the place and the hour, and effects for everything that happens.

## Code map

| | |
|---|---|
| `src/sim/` | Headless 60 Hz combat: battle, weapons, AI, stats, level-up drafts |
| `src/rpg/` | Character, items, gear |
| `src/world/` | Logic DSL, dialogue runner, daily simulation, saves, paths |
| `src/content/` | Archetypes, items, enemies, NPCs, quests, dialogue, rules, shops |
| `src/game/` | The game controller, zone runtimes, actors, audio and HUD bridges |
| `src/world/zones/` | Zone builds: terrain, props, water, lights |
| `src/render/` | Renderer, atmosphere, terrain, flora, water, crowds, effects |
| `src/audio/` | Sound engine, effects, ambience, music |
| `src/ui/` | Preact interface: HUD, overlays, screens |
| `docs/BETA_DESIGN.md` | The design bible the slice is built against |

## Tools

All expect `npm run dev` running.

| | |
|---|---|
| `node tools/shot.mjs "<query>" name [ms] [w h]` | Screenshot (software WebGL); `EVAL=` runs code first |
| `node tools/play.mjs "quick=warden&auto" name secs` | Autopilot through the prologue |
| `node tools/verge.mjs [hollow roost dig death]` | Drive the Verge routes and check the world's answer |
| `node tools/saveload.mjs` | Save mid-expedition, reload, continue, compare |
| `node tools/newgame.mjs [calling] [--continue]` | A new player's first hour, clicked: title, creation, prologue, town, Continue, out the gate |
| `node tools/monkey.mjs [zone] [steps] [seed]` | Random keys and clicks, checking nothing ever gets stuck |
| `node tools/console.mjs` | Every warning and error in the console, zone by zone, day and night |
| `node tools/flow.mjs` | Toll, both roads out of town and back, a night at the inn |
| `node tools/field.mjs [--fresh]` | Balance: a survivor who played the prologue, in the Verge by day and night, playing or idle |
| `node tools/folk.mjs [day\|night]` | The townsfolk: lanes checked against colliders, three minutes of errands, anyone stuck |
| `node tools/frames.mjs "<query>" name [frames] [fps] [setup]` | A run of frames stepped in game time, as a contact sheet: for judging motion |
| `node tools/probe.mjs "<query>" "<expression>"` | Load the game somewhere and print what an expression gives there |
| `node tools/reach.mjs [zone] [day\|night]` | Every door, person, clue and way in, checked for a walkable route from where you stand (and a map of it) |
| `node tools/leaks.mjs [rounds]` | Back and forth between the zones: GPU geometries and textures must not climb |
| `node tools/hitch.mjs [zone] [quality]` | Walk into each place and time the frame it comes alive on: shader programs compiled and creatures baked there (should be none: `WorldScene.warm` does it behind the fade; play tools print any `mid-play` warning) |
| `node tools/leakhunt.mjs [geo\|tex] [rounds]` | When leaks.mjs climbs: what is alive after each round, by kind, and which kind keeps growing |
| `node tools/tour.mjs verge [day\|night]` | One picture per landmark of a zone, empty of people |
| `node tools/looks.mjs [calling...]` | Every colour, cloak, skin and hair option of creation, photographed |
| `node tools/drafts.mjs [calling] [levels]` | A run of level-up drafts, photographed, taking a skill each time |
| `node tools/ui.mjs [w h] [screen...]` | Every overlay (shops, stash, pack, self, journal, map, rest, pause, talk) at one size |
| `node tools/listen.mjs "<query>" name secs` | Record the mix as a spectrogram with loudness |
| `python3 tools/assets/people.py [.packs]` | Gather the people from the unpacked Quaternius packs (textures to WebP) |
| `python tools/assets/figure.py` | Then shape the women (bust and hips morph targets; needs numpy) |
| `<bpy venv>/bin/python tools/assets/anime_female.py <blend> <gltf> <textures> godot/art/people/anime_female.glb` | Rig the woman survivor's own body to the Quaternius skeleton: joints to her body, arms to its T, hands fitted and weighted (`anime_hands.py`) |
| `<bpy venv>/bin/python tools/assets/anime_hair.py <her glb> <gltf> <hair dir> godot/art/people` | Then fit the women's hairstyles to her scalp (`her_<style>.glb`) |
| `<bpy venv>/bin/python tools/assets/woman_body.py <figure.glb> godot/art/people/anime_female.glb godot/art/people/woman.glb` | The woman survivor's body from a sculpted, painted figure (one T-posed mesh, e.g. from ComfyUI): rigged by landmarks to the anime body's skeleton, her hands laid palm down at a woman's size with each finger's joints in it, brought down to 32k faces (the hands kept finer), paint and fine shape baked, a mask of skin, hair and suit (`woman_mask.png`), weights through a watertight copy, a Figure shape key |
| `python3 tools/assets/env.py [.packs]` | Gather the world's kits (village, props, nature) with their bounds |
| `python3 tools/assets/ground.py` | The ground's photoscanned materials from Poly Haven (CC0), packed into KTX2 arrays (needs `toktx`) |
| `python3 tools/assets/ktx2.py [--keep]` | Then compress every sheet to KTX2 (UASTC, mipmapped; needs `toktx` from KTX-Software) |
| `<bpy venv>/bin/python tools/models/well.py` | Build one of the game's own models in headless Blender (`pip install bpy`, 4.2 LTS), painted with the village kit's sheets (`tools/models/kitmodel.py`) |
| `node tools/assets/sketchfab.mjs search\|get ...` | Find and fetch CC0/CC BY models, writing their credit (`SKETCHFAB_TOKEN`) |

`NO_HMR=1 npm run dev` serves without hot reload, so a long tool run
survives edits to the source. Useful URLs: `?quick=warden&bg=hunter&zone=verge&at=-60,-80` (start
anywhere as anyone), `?screen=create`, `?dev=zone&zone=verge&x=..&z=..`,
`?dev=sandbox`, `?dev=combat`, `?dev=icons`, `?dev=gallery`, `?dev=people&view=1`
(people, `&spec=`/`&arms=`/`&boss=idle`), `?dev=armory` (weapons), `?dev=env&kit=village` (a kit's pieces, labelled; `kit=custom` for the game's own), `?dev=house` (houses), `&flora=gen` (the generated trees, to compare), `&quality=low`.

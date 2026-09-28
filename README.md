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

| | |
|---|---|
| Move | WASD / arrows / left stick |
| Dash | Space / Shift |
| Ability | Q / right mouse |
| Interact, talk | E / F |
| Pack · Self · Journal · Map | I (Tab) · C · J · M |
| Level-up draft | 1–4 to pick, X reroll, B banish |
| Pause (save, sound) | Esc / P |

Skills (weapons) fire on their own. You choose where to stand, when to
dash, which skill to take or rank up each time the ember rises (anyone can
take any skill; a calling leans a little toward its own style), what each
skill evolves into at rank 8, and, out of combat, what to say and to whom.
Blessings are milestones: one chosen at creation and given at the start of
every expedition, and one more every 85 ember levels, on top of that
level's skill.

## What is in the slice

- **Character creation**: name, look (the calling's colours repainting
  armour and cloth, a dyed cloak or none, skin, hair, headgear), archetype
  (Warden, Reaver, Arcanist, Stalker), starting weapon, ability, a boon, and
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
  who heard what about you overnight.
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

Stylized dark fantasy: KayKit characters and props (CC0, Kay Lousberg) with
generated terrain, vegetation, water and sky; N8AO, bloom, AgX and
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
| `node tools/flow.mjs` | Toll, both roads out of town and back, a night at the inn |
| `node tools/field.mjs [--fresh]` | Balance: a survivor who played the prologue, in the Verge by day and night, playing or idle |
| `node tools/folk.mjs [day\|night]` | The townsfolk: lanes checked against colliders, three minutes of errands, anyone stuck |
| `node tools/leaks.mjs [rounds]` | Back and forth between the zones: GPU geometries and textures must not climb |
| `node tools/tour.mjs verge [day\|night]` | One picture per landmark of a zone, empty of people |
| `node tools/looks.mjs [calling...]` | Every colour, cloak, skin and hair option of creation, photographed |
| `node tools/drafts.mjs [calling] [levels]` | A run of level-up drafts, photographed, taking a skill each time |
| `node tools/ui.mjs [w h] [screen...]` | Every overlay (shops, stash, pack, self, journal, map, rest, pause, talk) at one size |
| `node tools/listen.mjs "<query>" name secs` | Record the mix as a spectrogram with loudness |

Useful URLs: `?quick=warden&bg=hunter&zone=verge&at=-60,-80` (start
anywhere as anyone), `?screen=create`, `?dev=zone&zone=verge&x=..&z=..`,
`?dev=sandbox`, `?dev=combat`, `?dev=icons`, `?dev=gallery`, `&quality=low`.

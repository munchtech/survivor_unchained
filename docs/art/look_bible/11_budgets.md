# 11. Budgets: per frame, per tier, per asset

What the Prologue may spend, so the tutorial environment lead, the story characters lead and the armor-and-weapons pipeline lead build to numbers, not to taste. The boards (pages 1a-1j) say how each thing looks; this page says what it may cost. "Page 2" on the boards means this page (page 11).

**The owner's rule (18 October):** "more realistic - but stylized enough to make sense on saving graphics lag", and "very few things need to be as detailed as our heroine - infact they should be less - we will cut corners with smart clever tricks that still look good". Tier 1 (her, her spells, her animation, later the bosses) gets full detail; tier 2 (the open world, story NPCs) looks good on a budget; tier 3 (fodder) is cheap.

## Where the numbers come from

- **Measured** on the owner's machine (RTX 5080), 18 October, HEAD `cff7b440`: `C:\Users\munch\Desktop\survivorsunchained_inputs\look_bible_perf\summary.md` (per-case tables and per-20-s windows; raw `*.csv`, `*.json`, `*.log` beside it). Cases: the Low Ford at 1440p high (`lf_hi`, the autopilot's Prologue run, which reached the Barrow and no further), the same at 1080p medium (`lf_med`), a 45-s Low Ford view (`lf_base45`) with one part switched off per case (`lf_off_*`), the town (`hub_*`) the same way, and the title (`title_hi`).
- **Caveats:** a Debug C# build (2026-10-17 23:17), and a day-old import cache with 10 stale models. Frame times run well over the GPU's (the run's first window: 10.0 ms frames against 4.9 ms GPU, 2.7 ms render CPU and 1.8 ms of game logic in `lf_hi.log`). That gap is not art and isn't explained yet, so GPU numbers are the ones that count here; the first perf run on the new kit is a Release build and checks the gap.
- **What each part costs** is the base case minus that part's off case. Shadow draws sit inside each part's delta.

### What the Low Ford spends today (1440p high, `lf_base45`: 4.96 ms GPU, 438 draws, 2,435 shadow draws, 4.78M primitives)

| Part | GPU ms | Draws | Shadow draws | Primitives |
|---|---|---|---|---|
| Grass | 1.05 | 4 | 0 | 2.55M |
| Trees and flora | 0.97 | 169 | 714 | 0.36M |
| Lamp shadows | 0.65 | 4 | 1,495 | 0.09M |
| Crowd (NPCs, the risen) | 0.15 | 135 | 1,095 | 0.39M |
| FX | 0.24 | 57 | 428 | 0.19M |
| Sun shadows | 0.19 | 0 | 935 | 0.05M |
| Her | re-run (disturbed) | 33 | 63 | 1.45M |
| Props | under 0.05 ms | 20 | 30 | 0.09M |
| Landmarks | 0.07 | 10 | 60 | 0.08M |
| Volumetric fog | re-run (disturbed) | - | - | - |

**The town** (`hub_hi`: 3.97 ms GPU, 492 draws, 1,686 shadow draws, all of them the sun's): grass 0.99 ms, her 0.51 ms, props 266 draws and 935 shadow draws, lamps 0.24 ms. **The title** (`title_hi`) is the heaviest screen: 11.3 ms GPU, 33.1 ms p99, 1,512 draws, 6.3M primitives.

**The Prologue run by window** (`lf_hi`, 20-s windows): GPU 4.6-5.0 ms average in the quiet windows, but **6.0-10.1 ms at 70-170 s: late Rising, Road, Ambush and Post, the road's heaviest fighting (kills 60 to 286; the log's fx time triples, 0.10 to 0.31-0.35 ms)**, with frame p99 up to 42 ms, draws 443-481 in the 70-190 s windows (`lf_med` reaches 480) and primitives averaging 5.02-5.21M from 130 s on, peaking at 5.40M. The run never reached ToFord, Boss, Dawn or Exit (it sits at the Barrow from 190 to 310 s): the Warden, dawn and the gate are unmeasured. That peak isn't split by part yet (the off cases are on the static view); the tutorial environment lead's first perf run splits it (the Warden, her spells, the risen, fx) before anything is cut to fit.

**Lessons:** Grass and trees are the biggest world costs. Shadows are the draw-call problem: lamp shadows alone are 1,495 of 2,435 shadow draws for 0.65 ms, and the crowd and fx cast 1,523 shadow draws that the player never reads. Two cases ran disturbed (`lf_off_her`, p99 13.5 ms, and `lf_off_volfog`, p99 11.5 ms, both slower than the base's 5.5 ms), so her cost at the Low Ford and the fog's cost are not measured; both are re-run (disturbed). In town her measured cost is 0.51 ms (`hub_off_her`).

## Per frame (the targets)

| Target | Owner's 5080, 1440p high | Min-spec, 1080p medium |
|---|---|---|
| GPU, average per 20-s window | at most 6 ms | at most 4.5 ms on the 5080 (estimate: the 60 fps line on an RTX 3060 / 4060 class card, about a quarter of a 5080 by the cards' benchmark ratio, roughly 8.7k against 32k in Time Spy) |
| GPU, p99 per 20-s window | at most 10 ms | at most 7 ms on the 5080 (estimate, same basis) |
| Draws per frame | at most 450 | the same |
| Shadow draws per frame | at most 1,200 | at most 1,000 |
| Primitives per frame | at most 5M | at most 4M |
| Frame time, p99 per window (Release) | at most 16.7 ms | the same |
| Render CPU | at most 3 ms | the same |
| Game logic | at most 2 ms | the same |
| Hitches | none over 33 ms outside loads | the same |
| UI draws | at most 300 (today 486-583, uncounted) | the same |
| Video memory | at most 3 GB | at most 2.5 GB (8 GB cards) |
| Texture memory by tier | her at most 400 MB, world 1.2 GB, NPCs and fodder 300 MB, FX and UI 200 MB | the same (today 1.66 GB at medium against the 2.5 GB cap) |
| The title screen | at most 6 ms GPU, at most 450 draws | at most 5 ms |

Today against these: the Low Ford's quiet windows meet the GPU target and the road's heaviest fighting (70-170 s) doesn't (above); the Warden fight, dawn and the gate are unmeasured. In the run, draws (443-481) and primitives (5.02-5.21M average from 130 s, peak 5.40M) fail; in the static view draws are 438 at the Low Ford (pass) and 492 in town (fail), and primitives are 4.78M (pass narrowly, with grass more than half). Shadow draws (2,435 and 1,686) fail: 2x at the Low Ford, 1.4x in town. Video memory (2.4 GB) passes; the title (11.3 ms, 1,512 draws) fails. At 1080p medium the Low Ford runs 4.0 ms average and 8.2 ms p99 (`lf_med`): over the 7 ms p99 line. The CPU side is not met: frames take 10.0 ms against 4.9 ms of GPU in the run's first window, and the log has hitches of 152, 180 and 209 ms (fx, draft, auto) at 21-22 s.

### The split of the 6 ms (planning numbers; each lead keeps its part)

| Part | GPU ms | Draws | Shadow draws | Today |
|---|---|---|---|---|
| Her (dressed, play LOD) | 0.3 | 40 until the equip-time merge lands, then 20 | 80, then 40 | hub 0.51 ms (`hub_off_her`); Low Ford re-run (disturbed), 33 draws |
| Her spells (typical) | 0.5 | 40 | 0 | in fx; the big screen-clear spells' peaks are the Flare lead's |
| Terrain, road and decals | 0.8 | 40 | 0 | not measured (add an `lf_off_terrain` case) |
| Grass | 1.0 | 10 | 0 | 1.05 ms |
| Trees, bushes, rocks | 0.8 | 80 | 420 | 0.97 ms, 169, 714 |
| Water | 0.5 | 5 | 0 | - |
| Buildings, castle, props | 0.6 | 130 | 640 | town props 266, 935 |
| NPCs and crowds | 0.4 | 60 | 60 (story NPCs only) | 0.15 ms, 135, 1,095 |
| Post, sky, fog (lights' shadow draws counted on the casters) | 1.0 | 15 | 0 | sun 0.19 ms, lamps 0.65 ms; post not split yet (measure it) |
| **Total** | **5.9** | **420** | **1,200** | |

Every shadow draw is the sun's or the one shadowed lamp's; each caster's count includes both. The armor-and-weapons pipeline lead owns the equip-time merge that takes her from 40 draws to 20 (today HerWear adds each piece's meshes, and the 11 October merge is a post-export step per outfit). Trees and crowds use one MultiMesh per LOD per cell (Godot picks the LOD per MultiMesh, not per instance), and those draws are counted in their lines.

The 0.1 ms and 30 draws left over are headroom, not anyone's. The boards' own cost lines are gates on the way: 1e's and 1f's "shadow draws at or below 2,246" and 1e's alone "primitives at or below 4.9M" mean no worse than today when the new kit first lands; this page's 1,200 and 5M are the launch line. 1f's "at most 1.0 ms over today's ground (or page 2's number)" takes page 11's number: terrain, road and decals at most 0.8 ms in all, with the scatter inside the trees-and-rocks line; 1c's fog and mist (at most 0.5 ms) and 1d's ford (at most 0.5 ms) sit inside the post and water lines. A part over its line borrows only with the environment lead's say-so, written in its owner's handoff.

## Per asset

Triangles are at LOD0 (the close-up and cinematics) unless named. "Play" is the gameplay LOD the play camera draws. Draws are per pass. Materials are per asset.

### Tier 1: her, her weapons, later the bosses

| Asset | Triangles | Textures | Materials | Draws | Shadows |
|---|---|---|---|---|---|
| Her body (head, eyes, brows, lashes, teeth) | as built (93.6k) | 4096 body and head; the rest at most 2048 | as built (7) | 7 | the shadow LOD |
| Hair: braid (default), ponytail, pixie | as built (braid 101.5k, ponytail 129.3k, pixie 93.3k) | the strands sheet, 4096 x 2048 | at most 4 | at most 4 | the shadow LOD |
| Armor, large slot piece (top, bottom, skirt, cloak) | at most 30k, 20k typical | at most 2048, 1024 px/m | at most 2 | at most 2 | the shadow LOD |
| Armor, paired piece, both sides (gloves, bracers, greaves, boots, pauldrons, legwear) | 15-20k | at most 2048 | at most 2 | at most 2 | the shadow LOD |
| Armor, small piece (belt, collar) | at most 8k | at most 1024 | at most 2 | at most 2 | the shadow LOD |
| Armor, head | at most 15k | at most 2048 | at most 2 | at most 2 | the shadow LOD |
| **Her dressed** (body, hair, every worn piece) | **at most 350k (300k typical)** at LOD0; play LOD at most 25%; shadow LOD at most 10% | - | - | at most 40 at LOD0 and in play until the equip-time merge lands; **at most 20 in play after it** (worn pieces merged by material) | 80 shadow draws over 4 cascades until the merge, then 40 |
| Weapon | at most 15k | at most 2048 | at most 2 | at most 2 | yes |
| Boss (later) | 150k LOD0, 40k play, 10k shadow | at most 4096 | at most 4 | at most 8 | the shadow LOD |

**Armor lead 2's provisional budget is confirmed** (sent at `bd4bac70`; armor.md's "Budgets" line): large slot at most 30k (20k typical), pairs 15-20k, small 8k, at most 2 materials and 2 draws a piece, gameplay LOD at most 25%, shadow LOD at most 10%. Skirt, cloak, head and legwear are this page's additions to armor.md's Budgets line, sent to the armor lead. The plate top meets it (round 2 `cddee5d5`: 18.6k, 2 draws; round 3 `067d2bf0`: play LOD 23%, shadow LOD 8.9%). Two rules go with it:
1. **The dressed cap binds, not the sum of slot caps.** Per hair, the heaviest built style in each slot, after culling, is at most 350k. A new piece that breaks this fails its own build. In the Prologue, check the four callings' sets (the build can't try every player-mixed combination). Every visual slot at its typical number is about 216k of pieces; with the body (93.6k) and the ponytail (129.3k) that is about 439k. So the build removes the body's faces under worn pieces and an inner piece's faces wholly covered by an outer one (the plan the owner approved on 11 October: "all those ideas seem worthwhile!"), and a look still over 350k fails the build. A typical look (top, bottom, belt, gloves, bracers, boots, pauldrons with the braid) is about 313k before culling.
2. **Mixed looks draw LOD0 in play until per-piece LODs land** (armor.md item 7). Measure a mixed look in the playable Prologue build, at the ford fight, against the 0.3 ms line above.

Full detail always shows at the title, in creation, in conversations, close-ups and cinematics (the owner, 11 October: "we worked very hard on these models so they show there no matter what"). The play LOD is judged so she looks the same at the play camera. Today's outfits (Warden 942k, Ranger 653k, Arcanist 485k, Reaver 420k, before her body and hair) are rebuilt into slot parts to this budget (page 12).

### Tier 2: the open world and the story NPCs

| Asset | Triangles | Textures | Materials | Draws | Shadows | LODs |
|---|---|---|---|---|---|---|
| Story NPC (body, clothes, hair and beard cards) | at most 40k | one 2048 atlas plus the hair cards | at most 2 | at most 2 | yes (story NPCs only) | LOD past about 10 m |
| Story NPC with a close-up (C02 s4, C04 B sB4a) | at most 55k | a third material, its own 2048 head map | at most 3 | at most 3 | yes (story NPCs only) | LOD past about 10 m |
| Crowd and background NPC | at most 15k, 5k in play | the shared atlas | 1 | VAT MultiMesh, one per type | none: a blob decal | as fodder |
| Broadleaf tree | 8k | the species' bark and leaf sheets, at most 2048 | 2 | 2 per type per cell (MultiMesh) | a shadow-only LOD at most 1k | 3 LODs, an impostor past about 60 m |
| Spruce | 6k | as above | 2 | as above | as above | as above |
| Bush | 2k | the species' sheet | 1-2 | MultiMesh | none | 2 LODs |
| Grass clump | at most 150 | the grass sheet | 1 | MultiMesh, visibility-range fade | none | fade |
| Rock | 3k (outcrop 8k) | a shared rock set, 1024-2048 | 1 | MultiMesh where repeated | yes, its LOD1 | 2 LODs |
| Building, merged | at most 25k | two trim sheets (2048) shared by the kit | at most 3 | at most 3 | one shadow-only proxy, at most 2k | 2 LODs |
| The far castle | one mesh, at most 30k | the stone trim sheet | 1 | 1 | none | - |
| Prop | 1.5k (carts and stalls 4k) | the shared prop atlas | 1 | MultiMesh where repeated | only 0.5 m and taller | 2 LODs over 1k |
| Lamp or torch | 1.5k | the prop atlas | 1 + the flame | 2 | no shadow; one shadowed light per frame (two in a cinematic) | - |
| Terrain | one heightfield per zone | at most 4 layers per pixel (today a 7-layer array) | 1 | as few as the clipmap needs | receives only | - |
| Water | one material, flow-mapped | normals and foam at most 1024 | 1 | at most 5 | none | - |

### Tier 3: fodder

| Asset | Triangles | Textures | Materials | Draws | Shadows |
|---|---|---|---|---|---|
| Fodder (the risen, the drowned) | at most 8k LOD0, 2k in play | the shared atlas, 256 px/m | 1 | VAT MultiMesh, one per type | none: a blob decal |

### Textures, all tiers

- Texel density: tier 1 1024 px/m; tier 2 512 px/m where the close-up or a cinematic shows it, 256 px/m where only the play camera does; tier 3 256 px/m.
- 4096 only for tier-1 bodies and faces (and the hair strands sheet). Everything compressed (VRAM-compressed in the import; normal maps as RG).
- Texture memory by tier at medium: her at most 400 MB, world 1.2 GB, NPCs and fodder 300 MB, FX and UI 200 MB. Today is 1.66 GB against the 2.5 GB cap, with three leads adding at once, so each lead keeps to its tier's number.
- A story NPC whose face fills a close-up gets its own 2048 head map: one 2048 atlas at 512 px/m puts only about 128 px across such a face, which is the toy look board 1i forbids.
- Shared sheets over unique maps: one prop atlas, two building trim sheets, one rock set, one sheet per tree species.

## DONE means

- Each new asset's row passes this page: its triangles, materials, draws and shadows, measured by its owner on the built file (a runner's number, not an estimate).
- A perf run (Release build, the owner's 5080) over the whole Prologue meets the per-frame targets in every 20-s window: at 1440p high and at 1080p medium, and the run's log reaches stage=Exit.
- One measured run on a real 3060 / 4060-class card holds 60 fps in every window (the min-spec numbers above are estimates until then).
- The title screen meets its line.

Owners: the tutorial environment lead (the world's parts and the per-frame run); the armor-and-weapons pipeline lead (her pieces, dressed and mixed looks); the story characters lead (story NPCs, crowds and fodder); rendering (shadows, LODs, impostors, the title); Flare (her spells' peaks, when unpaused); the armor-and-weapons pipeline lead also owns the equip-time merge.

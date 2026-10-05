# Handoff: skills look and feel

For the next skills lead. Read `docs/team/README.md` first, then this page, then
`docs/team/skills.md` (status, grades, the exact next step). Branch:
`worktree-agent-a94ac6b67f1279213` (pushed; not yet merged into the integration branch).

## The owner's words

- "leveling up all our skills. revisiting ones we already made if they don't match our perfection
  standard, moving on to others if they do. theres many we never got to. leverage our gpu as always
  to create amazing effects and be careful of crop/squaring issues we had early on"
- "I don't want to polish, I want to create perfection." "Do we have soul?" AAA, never settle. Judge
  at full resolution: the owner caught square edges in thumbnails that others had dismissed.

## The brief

You own how every skill looks, sounds and feels in play: arts, auto-attacks, evolutions, blessings,
the callings' own moves, her rise, and (combat's list) the enemy's own verbs. Each skill must read at
a glance in a horde, keep one colour and shape language per school, land every hit with a flash,
hit-stop, sound and mark, and grow with rank and evolution. No effect may show its sprite's square or
be cut off at its frame's edge. Combat owns mechanics and numbers: propose, never change them. Send
the main session before/after sheets of full-resolution frames from play for each batch. Commit and
push your branch at milestones; the main session merges it. Run `dotnet test` before every commit.

## Done this session (all pushed: c2b16600, f519680d)

- **The main session's three findings, fixed and seen** in the packed crowd:
  - numbers (`Hits.Numbers.cs`): 4 new a frame, 12 on screen, none over one still rising, the
    weightiest first; no exceptions (in a crowd of the small dead every blow is "heavy");
  - Hoarfrost no longer whites the crowd;
  - glare round her: lights fade within 4 m of her unless lit where she stands (`Flash`);
    `flipbook.gdshader` clears its smoke (alpha) over her as well as its light; a champion's fall
    is Blast radius 1.3 (about 3 m across); the disc's body, sun and arcs held down within 3 m.
- **The rise** (`BattleFx.Rise.cs`, `Ev.Rise` in `Events.cs`, emitted in `Battle.HurtPlayer`):
  - the cold (ice spikes, frost glints, cold breath), the world slowed 1.1 s (`Game.cs`), haptics;
  - Cold, Then Not: `shaders/fire_ring.gdshader` on one flat square (gradient noise in rings and
    spokes, wrapping round so no seam; tongues out past the front, a char band with embers behind
    it), a `smoulder` mark (Krea, `marks.py`), embers off the wall where it stops;
  - Not Yet: a watch-lamp sprite over her and the painted dial (`art/fx/fb/watch_dial.*`, a
    one-frame flipbook) held at the waist, turning back, a ribbon hand wound back three hours;
  - the grace ring; `Sfx.Rise` (glassy breath, a heartbeat, then a fire rush or a deep bell);
  - `--fall-at T` (dev): a killing blow at T, for pictures (give `+from_the_ashes` for the ember).
- **Enemy looks seen** (`dig4`, `kerch3`, `dead3`, `pack3`): hostile marks scaled to 0.28 (boss 0.5);
  the Dig's cream rings are gone at 0.38 (0.28 unseen). Rallies, summons and slams read.
- Her dash is one ribbon streak plus a little dust. The dry dead's bone dust is grey, 4 a told kill.
- **Experience's status look** (frozen and burning bodies) is judged by them and committed on their
  branch (`worktree-agent-ab406cf9ddd22b03b@a3d42f7d`); my frames agree (frozen a clear win).

## Next, in order

1. See the hostile marks at 0.28 on the Dig (`dig5`) and the dash streak close.
2. Gale Chakram (grade 2: two pale rings read as handcuffs): `python tools/comfy/fx_sprites.py cut
   gale_ring=tools/comfy/out/fx_sprites/gale_ring_1_1_0.png wind_swirl=tools/comfy/out/fx_sprites/wind_swirl_2_2_0.png`,
   import, then in `Flight` draw `Body(at, ..., "gale_ring", ...)` spun fast over a dark steel ring,
   with `wind_swirl` behind it. (The four-blade candidates are set aside in `scratchpad/vfx/rejected/`.)
3. `gpu_horn.sh` when 11 GB of RAM is free; add `tell_horn` to `sounds.json`. No leftover war horn
   job was in ComfyUI's queue.
4. Cinderfall's blast blooms cream round her (and the coal in flight is a cream pill); Umbral Bolt
   and Moonbrand read as grey smoke (shadow_wisps tinted grey); the crit `sparks` burst is white
   at her feet. Then Firepot, Iron Palms, Grave Tether, Gravecall, Spirit Herd, Thornbloom,
   Blightfield; evolutions, unions, the arts, sound per skill; combat's asks (a fed deadfall, the
   cold's band, the pale-blue "His age" ring).
5. The rise could be richer still: filmed flame (an LTX "ring of fire spreading on the ground from
   above" clip) over the shader's band; the fire's front is a band of orange more than tongues at
   full resolution.

## Decisions (why)

- **Nothing lights her but her own moments** (lights near her fade; effects cleared over her).
- **A crowd is told by its first few**: numbers, deaths, dust, flashes, falls.
- **Hues below AgX's knee** (cream past about 2). Fire's hot is (1.05, 0.5, 0.08).
- **What must be seen over a packed crowd is held in the air**: a ground decal under seventy
  bodies was invisible (the dial).
- **Fire from above is a field**: upright flame sprites read as torches, flat ones as streaks.
- **No four-armed turning blades** (they read as a hooked cross).
- **Hostile marks near the ground's lit value**, hatched, never solid.

## Failures, and why

- **Flames as sprites** (three tries): upright `fire_loop` read as torches, flat ones as sparse
  streaks; the shader ring fixed it.
- **The dial as a ground decal**: hidden under the crowd.
- **The rise's first look lit the crowd cream**: a chest flash with a 12 m range. Lights near the
  crowd must be low and short.
- **Batch 11 lost frames**: disk C: fell under 2 GB and Godot wrote truncated PNGs. Check
  `Get-PSDrive C` before a long batch; `grid.py` fails on a truncated frame.
- **Krea skips a name it has made**: `krea.t2i_many` returns an existing file; move old candidates
  aside before remaking one.

## Gotchas

- Import after every merge and after adding textures (`--headless --path godot --import`; an
  incremental one takes a minute or two). New textures get their sibling's import settings with
  `scratchpad/vfx/import_like.py` (VRAM compressed, mipmapped), or Godot imports them lossless with
  no mips.
- `comfy_stat.py free` now frees only when the queue is empty (freeing under another lead's job makes
  it reload). The face and UI leads use ComfyUI a lot; RAM is often 3 to 8 GB free.
- `shot.py`, `sweep.py`, `shots.py`, `gpu_horn.sh`, `install_fb.py` point at this worktree;
  `shots.py` also reads the previous lead's frames (`a63cd93...`) as "before" (`a9`, `s6`, `s7`).
  `grid.py OUT COLS W,H[,DX,DY] globs` makes full-resolution crops.
- `Shots.Want("rise", t)` saves frames at real seconds after a rise (`rise_ember_rise_N.png`).
- Shader `TIME` is engine time (not slowed); `BattleFx.time` is the fight's.
- `Color * float` scales alpha too; use `new Color(r*k, g*k, b*k, a)` where alpha matters.
- Don't `dotnet build` the game while a capture runs; compile-check with `-o scratchpad/vfx/buildcheck`.

## Collaborators

- **Main session**: merges; sent the sheets listed below.
- **Experience director** (`ab406cf9ddd22b03b`): owns `vat.gdshaderinc` (status and struck looks).
- **Combat** (`a708da2c97bf85c95`): told of `Ev.Rise` and the delay proposal.
- **Arena art** (`a26767f7f9955cb56`): given the Dig crop.
- **Performance** (`a7145e18b3eb78294`): Blades is one MultiMesh; tell them before touching `Ribbons.cs`.

## Sheets (in `scratchpad/vfx/`)

`ba_a9_1.png`, `ba_s6_1.png`, `ba_s6_2.png` (the previous lead's); `ba_r1.png`, `ba_r2.png` (the three
findings, before and after); `rise_ember_sheet.png`, `rise_ember_whole.png`, `rise_notyet_sheet.png`;
`st_cmp.png` (status read); `dig_crop_for_arena.png`; `z_disc.png`.

## Files to read first

1. `docs/team/skills.md`
2. `godot/src/Fx/BattleFx.Rise.cs`, `BattleFx.Skills.cs`, `BattleFx.Enemies.cs`, `Hits.Numbers.cs`
3. `godot/src/Fx/BattleFx.cs` (Handle, Flash, Blast, the telegraph handler)
4. `godot/shaders/fire_ring.gdshader`, `flipbook.gdshader`, `hero_clear.gdshaderinc`, `blade.gdshader`
5. `tools/comfy/marks.py`, `fx_sprites.py`, `fx_clips.py`, `flipbook.py`
6. `scratchpad/vfx/shot.py`, `sweep.py`, `grid.py`, `ba.py`, `batch13.sh`

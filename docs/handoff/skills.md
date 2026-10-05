# Handoff: skills look and feel

For the next skills lead. Read `docs/team/README.md` first, then this page, then
`docs/team/skills.md` (status, grades, the exact next step). Branch:
`worktree-agent-a63cd93fc73d5ed79`, merged into the integration branch at 0e6f2e8b.

## The owner's words

- "leveling up all our skills. revisiting ones we already made if they don't match our perfection
  standard, moving on to others if they do. theres many we never got to. leverage our gpu as always
  to create amazing effects and be careful of crop/squaring issues we had early on"
- "I don't want to polish, I want to create perfection." "Do we have soul?" AAA, never settle. Judge
  at full resolution: the owner caught square edges in thumbnails that others had dismissed.

## The brief

You own how every skill looks, sounds and feels in play: arts, auto-attacks, evolutions, blessings,
the callings' own moves, and (combat's list) the enemy's own verbs. Each skill must:
- read at a glance in a horde;
- keep one colour and shape language per school;
- land every hit with a flash, hit-stop, sound and mark;
- grow with rank and evolution.

No effect may ever show its sprite's square or be cut off at its frame's edge. Combat owns mechanics
and numbers: propose changes, never make them. For each batch, send the main session a before/after
sheet of full-resolution frames from play.

## Done (all pushed and merged)

- **The nine starting weapons, Hoarfrost and Dawnpulse are remade and judged at full resolution**, in
  a packed crowd and in the 9–14 m showcase. Grades are on the status page.
  - **Blades** (Oathblade, Cleaver, Reaving Arc) use `shaders/blade.gdshader` and `src/Fx/Blades.cs`, one
    MultiMesh: a crescent with a white edge leading, a streaked smear behind, tattering away, and its
    own dark bed. Blades set it up per art in `Swing` (`BattleFx.Skills.cs`).
  - **Bodies in flight:**
    - motes weave with a short tail and spark dust;
    - the Disc is a gold ring with spin arcs and a painted sawblade face;
    - Rimeshard is a cut six-sided ice lance (`IceLance`, `crystal.gdshader` with facets);
    - arrows are an arrow mesh (`Arrow`);
    - Cinderfall has a painted coal;
    - the umbral bolt has a ring of violet flame;
    - Moonbrand is a crescent;
    - Arcweb is a forking blue bolt with a glow;
    - Verdant Lance has a heart, a haze and twisting vines;
    - Thunderhead has a glow round its bolt.
  - **Crowd restraint** (the "cream blobs"):
    - six kill bursts a frame (`killBudget`); steel kills throw grit, not light;
    - flashes share their light (`Flash`);
    - champions falling together are told by the first (`lastFall`);
    - no filmed burst per mote, shard or disc hit;
    - sparks and filmed bursts keep her clear (`hero_clear` in `spark.gdshader` and `flipbook.gdshader`).
  - **Damage numbers** (`src/Fx/Hits.Numbers.cs`), to the experience director's S-13 rule:
    - hits sum per target per 0.25 s beat;
    - at most 8 new numbers a frame, crits first, then the biggest;
    - a hit over 20% of the target's health is one size bigger;
    - none within 1.5 m of her;
    - damage over time is summed in its school's colour.
  - **Grounds and telegraphs:**
    - the fills are premultiplied (`Premul`), so a turning fill can't glow as a square;
    - burning ground is fire in its cracks;
    - Hallowed's edge is thinner and its runes are at 0.18;
    - hostile discs and lanes are hatched (front edge plus about 30%), never solid;
    - "blocked" is said once per 0.35 s.
- **Enemy looks, built but NOT yet seen in play** (`src/Fx/BattleFx.Enemies.cs`):
  - rallies in the people's colour (they were white-gold bands, which the arena lead called "lampling discs");
  - summoning circles (the painted rune ring) with the ground breaking as the kin rise;
  - slams that throw stone and roll dust;
  - haste lines and ward glints;
  - `bolt_bone` and `frost_orb` in flight.
- **GPU work:**
  - Krea (`tools/comfy/fx_sprites.py`): 10 sprites cut into `art/fx/sprites.png`, all passing the
    edge-light rule: sun_disc, dawn_sigil, frost_star, rune_ring, umbral, ward_disc, crescent,
    ember_coal, wisp, blood_drop. Candidates are in the worktree's `tools/comfy/out/fx_sprites/`.
  - LTX (`tools/comfy/fx_clips.py`): 12 clips, in the main checkout's `tools/comfy/out/clips/`. Six
    are in use: holy_ring, moon_burst, gold_flare, shadow_wisps, bramble_burst and leaf_burst. Five
    were refused by `flipbook.py`'s edge check or set aside as poor: fireball_impact (sparks run off the
    clip), dust_chop (a post in frame), ice_shatter (a white ball), poison_cloud (too dense for the zone
    rule) and frost_spikes (fills the frame). blood_scythe is unused too.
  - **Tell takes:** tell_whistle ×2 and a second tell_fuse, now `art/sound/tell_*`. They are counted in
    `sounds.json`. **No one has listened to any tell take** (whistle, fuse, howl, drum). The owner should.
    By analysis, the whistle is tonal at about 1.1 kHz and the fuse is broadband hiss.

## In progress, and next (in order)

1. **batch10**: run `bash scratchpad/vfx/batch10.sh` with no other game open. It shoots the Dig
   (lamplings, seed 739), the Kerchiefs, the dead and the Pack at minute 25, plus `s7` (Gale Chakram,
   Umbral Bolt, Moonbrand, Reaving Arc, Thunderhead).
   - Judge the enemy looks.
   - Judge the lamplings on the Dig's clay against the arena lead's rule: each disc's core no more than
     the clay's lit value plus about 1 stop.
   - Judge the blade smear on dark ground (toned down, not yet seen).
   - Send the arena lead (a26767f7f9955cb56) the Dig crop.
   - It was stopped mid-run for the owner's pause. Its first three runs (dig2, kerch2, dead2) were
     shot before the last code change, so reshoot them.
2. **gpu_horn**: run `bash scratchpad/vfx/gpu_horn.sh`. It makes `tell_horn` (the dead's tell, which
   combat moved from the drum; the prompt is in `sfx_clips.py`) and waits for 11 GB of free RAM first.
   - I interrupted it for the pause. Check ComfyUI's queue for a leftover "war horn" prompt.
   - Free ComfyUI after.
   - Add `tell_horn` to `sounds.json` with its count, and commit the `.wav` and `.import` files.
   - `Sfx.Tell` falls back to a made sound until then.
3. Send the main session the newer sheets together with the batch10 results: `scratchpad/vfx/ba_a9_1.png`
   (numbers summed, frozen tint) and `ba_s6_1.png` and `ba_s6_2.png` (the second batch).
4. Champion Sign marks (`logic/Content/Signs.cs`: each Sign has a tint and glow on the body; is a
   mark at the feet wanted?).
5. See and judge, still at the "before" grades: Firepot, Iron Palms, Grave Tether, Gravecall, Spirit
   Herd, Thornbloom, Blightfield.
6. Evolutions and unions, the arts, the callings' own moves, and sound per skill.

## Decisions (why)

- **Hues below the tone curve's knee.** AgX turns coloured light over about 2 to cream, so bodies and
  smears sit near 1, and only thin edges and cores go white. Dark grounds raise the exposure, so hold
  smears lower still.
- **A crowd is told by its first few.** Deaths, champion falls, flashes and numbers are all budgeted
  per frame: many small effects summed into a wash.
- **Dark beds, in the same pass where possible** (premultiplied: alpha darkens, colour adds). This is
  what makes light read over the pale risen.
- **Danger keeps its own language:** amber blow, violet ground, hatched and never solid. A people's
  colour is for what is theirs and not yet a blow. Never use her red or the dead's grey.
- **Per skill, not per school.** Real shapes where a flat picture fails (ice, arrows). Painted
  sprites and filmed clips are always cut through the edge checks.
- **Frozen and burning bodies are the experience director's** (`vat.gdshaderinc`). Ask; don't edit.

## Failures, and why

- **Each sheet looked fine at a glance and wasn't.** Cream blobs, centre blooms and carpets of numbers
  only showed in packed crowds at full resolution. The main session caught three of them. Judge the
  packed crowd (`sweep.py` defaults) as well as the showcase.
- **A shader constant named `RIM` clashed** with `hero_clear.gdshaderinc`'s include. The shader
  failed silently in the game, and only the console showed it. `shot.py` now prints `SHADER` lines.
- **The first LTX tries cut off at the frame's edge.** `flipbook.py` refuses them. Use `--start`,
  `--end` and `--pad` to keep the part that stays inside, or set the clip aside. Never force it.
- **After a merge, the arena came out as banded gradients**, because the new textures weren't imported.

## Gotchas

- **Import after every merge, before you shoot:** run Godot's `--path godot --headless --import`
  (about 15 to 25 minutes). It rewrites many `.import` files with VRAM formats. Commit only your own
  files. Don't restore the rest mid-session, or the next import redoes them all.
- **Worktree setup:**
  - `godot/assets` arrives as a 16-byte file: make it a junction to `public/assets` and set
    skip-worktree;
  - copy a sibling worktree's `godot/.godot` with robocopy, without `mono`.
- **Line endings:** `BattleFx.cs` is LF now. `Scars.cs`, `spark.gdshader` and `flipbook.gdshader` are
  CRLF; edit them by script, keeping CRLF. The isolation guard refuses complex shell one-liners: put
  edits in small Python scripts in the scratchpad (see `scratchpad/vfx/edit_*.py`).
- **Don't `dotnet build` the game while a capture runs.** Compile-check with
  `-o scratchpad/vfx/buildcheck` instead.
- **LTX needs RAM.** It died at 2 GB free (Windows error 1450). The chain scripts wait for 11 GB.
- **ComfyUI is shared.** Delete only your own queue items, matched by prompt text. Free it with
  `POST /free` (`comfy_stat.py free`); interrupt with `POST /interrupt`.
- **Tools** in `scratchpad/vfx/` (the session scratchpad):
  - `shot.py` and `sweep.py`: capture runs;
  - `strip.py`, `ba.py`, `best.py`, `find.py`: full-resolution crops and before/after sheets; they read
    the predecessor's `before_*` and `show1_*` frames from `agent-a8bafe3cd8a229639/godot/.shots`;
  - `clipsheet.py`: views a clip;
  - `install_fb.py`: cuts and installs an atlas;
  - `comfy_stat.py`: shows the queue, RAM and VRAM, and frees ComfyUI;
  - `batch10.sh`, `gpu_horn.sh`: the next two runs.
- **Repro flags** (from the experience director):
  - the Barrow Lord's Rise: `--zone arena --people dead --tier 2 --minute 29.85 --give
    "oathblade:8,seeking_motes:8,cinderfall:8,arcweb:7,knifestorm:7,hallowed_ring:7,+might:3" --auto --on boss --until 170`;
  - the Kerchiefs' lobs: `--zone arena --people kerchiefs --tier 2 --minute 25 --give
    "oathblade:6,seeking_motes:5,cinderfall:5,arcweb:4" --auto --seconds 5 --every 5 --count 12`.

## Collaborators

- **Experience director** (ad1f5623590e09883): set the hit, zone and number rules (S-13). Owns frozen and
  burning in `vat.gdshaderinc`. Will judge Hallowed and the telegraphs in a minute-25 run.
- **Arena art** (a26767f7f9955cb56): raising the ground brightness, the Dig's clay most. They're owed
  the Dig crop.
- **Performance** (a7145e18b3eb78294): made Ribbons' Buffer write in place. Blades is one MultiMesh,
  at most 48 instances. Tell them before you touch `Ribbons.cs`.
- **Combat** (a1d4562f44c7f6feb): mechanics, and its enemy-looks list. Telegraphs carry `Faction`.
- **UI art and the face lead** both use ComfyUI.

## Files to read first

1. `docs/team/skills.md`
2. `godot/src/Fx/BattleFx.Skills.cs`, `BattleFx.Enemies.cs`, `Blades.cs`, `Hits.Numbers.cs`
3. `godot/src/Fx/BattleFx.cs` (Handle, Blast, Flash, Ground, the telegraph handler)
4. `godot/shaders/blade.gdshader`, `crystal.gdshader`, `hero_clear.gdshaderinc`
5. `tools/comfy/flipbook.py`, `fx_sprites.py`, `fx_clips.py`, `sfx_clips.py`
6. `scratchpad/vfx/batch10.sh`, `gpu_horn.sh`, `shot.py`, `sweep.py`, `ba.py`

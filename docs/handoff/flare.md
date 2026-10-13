# Handoff: the Flares (look, sound and feel)

Read `docs/team/README.md`, `RESUME.md` (top block), `OWNER_NOTES.md` (13 October), then this page, then
`docs/design/FLARE_LOOK.md` §0-§2 and §4 (grammar, sound, the slice: Burns Twice, beat sheet, "done", judge checklist).
Branch `flare-1`. Worktree `.claude/worktrees/agent-af0782e2e3f51bc1f` (`godot/assets` is a junction to its own
`public/assets`). Coordinator: 59a43b82. Numbers are classes' (a63a34b9e5a45d1bf); her clip is animation's
(aaf7f8cdd03812ebd; placeholder `cast_raise` then `cast_bolt` until they message).

## The owner's words
"super epic flare animations. like beyond anything we've done yet"; "an 'oh shit' button ... a 'clear the whole room'
button"; "pushing a flare should always do something visible"; "flares should be unique" (no spell's art or sound,
no Kenney sprites); "sounds that feel awesome, feel good. intangibles".

## State (successor 2 stopped here)
- **Wired and seen.** BattleFx owns `FlareFx Flare` (Ev.Flare, ByFlare kills to `Flare.Kill`, ByFlare hits tally only
  champions/bosses while `Quiet`; ordinary numbers hidden in the Quiet too). WorldScene: world at `Flare.WorldRate`,
  her clock through `b.FlareLead` while `Frozen`, `Player.Update(dt*HerRate)` while frozen or in a Flare hitstop,
  `Watch`/`Tick`, staff found once per figure (`arm:mage_staff`). CrowdView `FlareDeath` (1 held, -1 shattered).
  Game: Rumble to Haptics, `HudDim` to `GameHud.FlareDim`, Motion setting, `Night`. `Cue` is still a no-op: sound is next.
- **Test switches:** `--flare burns_twice[+burns.black_ice|+burns.more_embers|+burns.called_down|+!banked]` (meter full),
  `--flare-hp F` (0.2 = the clutch), `--cast T`, `--clean` (no loot beams, hints or title cards). The director calls
  `Shots.Want` at every beat (`NAME_ready`, `b1_press` ... `c3_ret3`, `c4_ret6`). Arenas run at night only: "by day"
  is the story camera (`--zone verge --time day`).
- **Scripts (scratch, backed up in `survivorsunchained_inputs/scratch_59a43b82/flare/`):** `batch.sh TAG [args]`
  takes the godot turn, imports and shoots arena night / (arena day: skip with `NO_AD=1`) / Verge night / Verge day,
  250 packed, cast at 6 s, to `godot/.shots/TAG_*`; `sheet.py OUT W COLS png[@x0,y0,x1,y1]...` makes labelled sheets.
  Never `python -` (it hung and wrote 100 MB twice).
- **Seen:** `t5_sheet.jpg` (latest; rows arena night, Verge night, Verge day; beats ready, hold, frost +0.1/+0.3,
  embers, last+5f, return +1/+3 s). `t1_sheet.jpg` is the first, unfixed look. Logged: struck down 232-242 of 250,
  standing in reach after 0-20: the clear is delivered by the numbers.
- **Timing (real s from the press):** frost 0.67 (as the sheet), first ember lands ~1.2, last ~2.0 (sheet 1.42): twelve
  2-frame hitstops add ~0.37 s, and the fall is now 0.26 s at 80 m/s (was 0.14 at 110) so the bodies it kills stand
  ~0.26 s after the logic's blow. Judge in motion; if it reads late, ask classes for an aim event ~0.2 s ahead.

## Honest critique of t5 (start here)
1. The last BOOM now has a field-wide light (20, range 1.3 x reach), 32 billows and a shock ring of frost dust and
   shards, and reads at the arena camera; at the story camera it's still just a bigger fireball. No shake in stills.
2. Each ember now reads from the top: a bright short ground light (12, range 10) and a crater (black pit, glowing lip).
3. Frost by day is darker (glaze x0.6, spec 0.22) but the frame still reads grey: most of it is glazed bodies, not
   ground. Next: body glaze darker and less opaque by day; measure the frame against §1.6 (mean <= 1.5x pre-press).
4. Steam columns now rise from each crater but read as straight, even contrails: give them turbulence (sideways
   wander, varied lean and width) and fewer per column by day, where they read pale.
5. Her key pose isn't a poster: ~40 px at the arena camera, placeholder clip. Waits on animation.
6. Shards still read as white paper flakes up close; frozen bodies as grey ghosts.
7. A thin red vertical needle sits ~3 m below her in the arena after the frost (not loot: `--clean` hides drops):
   find it (her aim mark, a lamp?) before the judge.
8. "Survivors staggered back" needs a knockback on the BOOM from the logic: ask classes (don't change numbers).

## Next, in order
1. Fix 3, 4, 7 above in one pass; reshoot with `NO_AD=1 batch.sh t6 --clean`; one sheet.
2. Sound (§2.2, §2.3): `Audio/Sfx.Flare.cs` from `Cue(name, at, k)`: catch, confirm, inhale (+ the gap at the Hold's
   last 0.1 s), frost, ember_fall, ember_land, ember_last (four layers, valley echo), boom, steam; the duck (world
   -12 dB, music -9 dB). Synth.cs or offline numpy, logged as ours (or CC0, logged). Owner records a bronze bell and
   ice later. Measure with `--wav`; the owner listens.
3. Luminance (§1.6) from a 60 fps run (`--every 0.0166 --count N` from the press) and the Spend's frame time.
4. Fresh `su-lead-max` judge, FOREGROUND, `Context budget: 150k`, §4.4's checklist, one face, sheets plus numbers.
5. 60 fps captures for the owner (`--write-movie`) through the coordinator. Then the remaining "done" cases: empty
   field, clutch, boss in reach, the three lamps, banked.

## Gotchas
- First `--import` after new files may segfault; the batch's import runs once per batch. Import churn under
  `godot/art/**/*.import` stays uncommitted: `git checkout -- godot/art` before committing (but commit new `.import`
  files for new art, as `art/fx/flare/*.import`).
- Give the godot turn back by its name: `turn.py give godot "<the name you took it with>"`.
- Onboarding plus this pass cost ~250k; the images were the bulk. One sheet per pass, crops only where needed.

# Audio (H3 sound): handoff

## Start here (3 November, lead 2: H3 done)
MR READY audio-h3@532d6a41b (suite 1480 passed, 0 failed; the commit on top only writes this line)

**H3's fixed list is done.** The owner's exit is still to come: a night with headphones, "it sounds like a game". The listening sheet is `C:\Users\munch\Desktop\survivorsunchained_inputs\audio_h3\README.md`: 20 moments, before and after through the same mixer. Numbers table: `docs/team/audio.md` "Numbers". The owner list: `docs/team/audio.md` "For the owner".

**Lead 2 did:**
- Merged integration and combat-h1.
- Wired H1's telegraphs: each windup is cut to its mark's duration (`Clip.Len`).
- Made SoundHooks.cs byte-identical to seams-h4's.
- Added zone beds (`Ambience.SetZone`; `bed.verge.day`, `bed.lowford`, `bed.waystation`, `bed.arena`, `bed.title`).
- Kept takes for `ui_open` and `lamp_lit_big` and wired them.
- Regenerated six weak families with sharper prompts. Five improved; `lamp_out` kept its first prompt.
- Added master makeup (+5 dB): fights now sit at -20 LUFS.
- Fixed the moment recipes, plus two game bugs:
  - A table boss's arrival rang `stinger.danger`: ArenaRun now sets the boss bar before the announcement.
  - The crowd limit could drop a boss's kill sound.
- Added test-only flags: `--bosskill T`, and the `--lamps-moves` moves `go@ID` and `putout`.

**Credits:** 368 spent this pass; about 31,650 left of 40,000 (resets ~6 Nov).

**If the owner's night finds more:**
1. Music is the synth score: `docs/team/audio.md` "Music" is the next pass.
2. `lamps.light_notable` is wired but no tape reaches it (every notable is behind a road gate).
3. m11 got only the pull. Setting SU_TELLS to a telegraphs.json with one kind's weight forces that kind.
4. Story nights and maps may announce a boss before its bar, as ArenaRun did. Not checked.

## Lead 1 -> successor (3 November; superseded by the section above)
Worktree `C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\audio-h3`, branch `audio-h3` (junction `godot/assets` -> own `public/assets`; follow README's junction rule before any merge). Report to main (coordinator b6ad7e4e), short. Read `docs/team/hook/H3_sound.md` (the fixed list), `docs/team/audio.md` (what the app can do, numbers, the owner list, the Music section main asked for), then this.

**Done:** 1 the bank as data (sounds.json, 71 events, SoundBank.cs, stereo takes, buses and ducks from data, `--nobank`, `--soundlog`, stems, compressor+limiter in `Synth.Mix`); 2 the generation tool (`tools/audio/gen.py`, prompts in `prompts.json`, 64 families, CLAP + onset ranking, provenance in `docs/legal/audio_generated.md`); 3 the palette's takes are ALL generated (batches 1 and 2) and most are wired as events (`tools/audio/events.py` is the table; run it to rewrite sounds.json's events); 4 the owner list started in audio.md. Captures: `survivorsunchained_inputs\audio_h3\before\` (all 16, but m01/m02/m04_sunder/m05 re-taken with the new limiter; RE-TAKE THE REST of before with `--nobank` so before and after share the limiter), `after1\` (4 moments, batch 1 only).

**Credits:** Starter plan, 32,021 left of 40,000 (resets ~6 Nov); reserve 15,000 (main: keep it). About 10 credits per generated second; a 30 s bed costs 300.

**Next, in order:**
1. **Merge `combat-h1`** for the Ev.Telegraph fields (H1 a11423fe1c6149251: fields 6870e414b, kit 44381f2c2; `Tell` in ring|charge|pull|closing, `Phase` Warn|Land, `Boss`, `Caught`; windups in data/content/telegraphs.json: ring 2.0, charge 1.1, pull 1.6, closing 1.6 s; a pull's outer band has Tell null: no sound). Then in `SoundBridge.Events` add `case Ev.Telegraph t when t.Tell != null: Sfx.Telegraph(t.Tell, t.Phase == TellPhase.Land, t.Boss, At(t.X, t.Z));` (`Sfx.Telegraph` exists in `Sfx.Cue.cs`; events `telegraph.<kind>.<windup|land>[.boss]` are in the table). `tg_closing_windup` takes are 3.7 s against a 1.6 s windup: regenerate at 1.6 s (or give the layer a fade) so it ends when the blow lands.
2. **H4's hooks** (a572bf4e1d106c432, branch seams-h4): they add `godot/src/Audio/SoundHooks.cs` with the same one line as ours (identical: merges clean) and call `SoundHooks.Play("ui.way_out" | "ui.skill_ready" | "cine.to_play")`. Ours already sets `SoundHooks.Cue = id => Sfx.Cue(id)` and the three events exist. Nothing to do unless their file differs.
3. **Zone beds** (not wired: the takes exist, `bed_verge_day`, `bed_lowford_night`, `bed_waystation`, `bed_deepshaw_night` (zone `arena`), `bed_title`, stereo, seamless loops at -28 LUFS). Give `Ambience` a zone bed: from `SoundBridge`'s per-frame state (zone, time), look up event `bed.<zone>.<day|night>` then `bed.<zone>`, play its take as a wide `TakeBed` (stereo support is in), crossfade over ~2 s on change, under the existing per-key beds (keep the synth wind etc. at lower weight or drop them where the bed covers them: decide by the ambience stem's LUFS, target about -36). Title: find where the title screen sets its music mood and start `bed.title` there. Add the events to `events.py`. A su-worker can do this from this paragraph.
4. **Fix the 0-take families:** `ui_open`, `lamp_lit_big` (the oneshot onset/duration rules dropped all: set `"max_onsets": 4` and loosen by trying `kind: "long"`, then `gen.py process <f>`, free); then add `ui.open`, `lamps.light_notable` events. Consider regenerating the weak ones in audio.md's owner list once with a sharper prompt (a new prompt = a new cache key) before leaving them to the owner.
5. **Calibrate the mix:** fights are about -25 LUFS; bring them to about -20 (bus `sfx` level or `master` level in sounds.json, then re-tape m01/m02), check the ui and flare buses sit above the fight, ambience about 15 dB under the fight. Numbers only: no model judges sound.
6. **The listening sheet:** `python tools/audio/moments.py run --all --tag after` and `--tag before --nobank` (both on the final build; ~25 min each; hand to a su-runner), then `python tools/audio/moments.py sheet` -> `survivorsunchained_inputs\audio_h3\README.md`. Moment flags TODO: m06 (the draft may not open: check `--open draft`), m07 (lamps lit/put out don't fire: find the lamps-demo/--lamps-moves recipe), m08 (no boss id fired: use a boss that exists in the arena, e.g. `--people dead --boss boss_dead`, and check `stinger.boss` / `kill.boss` in its soundlog). Add a telegraph moment once H1 is merged (an H1 recipe that makes rings/charges in a night).
7. Full `dotnet test` (1467 green at the last run), commit, push, "MR READY audio-h3@<commit>" to main, with the sheet's path and the numbers table.

**Gotchas:** new wavs need a Godot import (`gen.py process` runs it; else `gen.py import`) or the game logs "Failed loading resource"; `Where` default has Near 0 (use `near: 1` for UI/non-placed events); `SoundBank.Has` logs every id in a fallback chain, so soundlog counts double for chains; the CLAP model is cached by HF (1.2 GB, CPU only).

# Sound (lane F, the den's sound from the owner's files): handoff

## TOP BLOCK (state file; keep current)
Lane F lead (su-lead-sonnet, 250k), worktree `.claude\worktrees\agent-a38a6b090f1256466`, branch `demo-sound` (reset onto integration `claude/vigilant-galileo-l6jqyx@867525d49` at start: the worktree was made from the stub `main`; brief: `tools/scratch/coordinator/briefs/demo_15nov/F_sound.md`).
Owner's words (16 Nov 2026): "please give me a list of sounds needed for this demo (abilities, monsters and their abilities, whatever) so I can do something on my own while you work on things"; "I put a bunch in that folder, all are elevenlabs no attribution needed". Source folder `C:\Users\munch\Desktop\survivorsunchained_inputs\sounds_demo\` (56 wav, all 16-bit stereo 48 kHz).

FINDINGS (verified 16 Nov):
- Bank = `godot/art/sound/<family>_<n>.wav` + `.wav.import` (both tracked) + `art/sound/sounds.json` (family -> take count); events in `godot/data/content/sounds.json` (layers: take, gain, pitch, stereo...).
- `Recordings.Load` loads EVERY family into float arrays at start (a 120 s stereo music track = about 63 MB of floats: make music lazy or keep it out of that load).
- `Music.cs` IS a synth score (Mood enum; SoundBridge.Update picks the mood: Boss when `s.Boss`). "No music" = no recorded music; recorded tracks must silence the synth (Music.Set(Silence)) in the den.
- Zone beds: `Ambience.SetZone(id)` with `bed.<zone>[.day|night]` via SoundBridge (`zone.Id`); `bed.den` needs the den's zone id (find it).
- Den = DungeonGen `Hollow` ("hollow", den look), boss "boss_pack" in `logic/Play/Bosses/ArenaBosses.cs` (PackMother: Drive via Signature+B.Tell("charge"), Hamstring Cone label, Howl channel 8 s, Enter(phase), "The last of the Pack" Ring, Shake, Lunge Chain).
- Pits: `DungeonDress.FloorDecals.cs` DenPits(ctx) (centroid, radius) from `ZoneData.HoleField`.
- Foe moments in the sim: bite = contact in `Ai.cs` ~line 454 (HurtPlayer + Anim=Attack); lunge/charge windup = `Ai.Run(...)` (Telegraph with Id = enemy id, Tell null); notice = `b.Rouse(e)`/first target; hurt = Ev.Hit (Target, Def, Amount, MaxHp); death = Ev.Kill (Def, Family).
- Her: Ev.Slash(Art, Cut), Ev.Cast(Heavy), Ev.Leap(Phase Takeoff/Land), Ev.Dash, Ev.PerfectDodge, Ev.Swap (stance), Sfx.Heartbeat exists.
- Plan: add `Ev.Voice` (Def, Moment, X, Z) from the sim for bite/lunge/notice and `Ev.Sound` ids for Pack-Mother moves; the SoundBridge turns them into `voice.<kind>.<moment>` events with limits. Enemy pool fields are reset at ~Battle.cs:2122 (add any new field there).
- Disk: C: 27 GB free after checkout (guard 20): NO full Godot import.

STEP 1 DONE `383235995` (demo_ingest.py, table `tools/sound/demo_ingest_table.md`, 54 takes in 40 families: den_ambience, den_pits, den_pack_far, music_den_explore|boss|falls, voice_<wolf|wolfb|boar|yearling|packmother>_<notice|bite|lunge|hurt|death|arrival|drive|hamstring|moonhowl|phase|call>, her_grunt|leap|land|dodge|perfect|stance|heartbeat; seams all pass; 44.1 kHz 16-bit, mono for world takes, stereo loops/music/boss calls; levelled by mono-mix LUFS to the nearest banked neighbour).

DESIGN DECIDED (implement in this order, commit each):
 a) Godot-free `src/Audio/DenSound.cs` (add to godot/tests/Tests.csproj like LeadRule.cs): def->voice kind map (wolf->wolf, wolf_blighted->wolfb, boar->boar, lt_pack->yearling, boss_pack->packmother), VoiceLimiter (max voices at once, per-kind cooldown per moment, nearest first), her-grunt chance+cooldown. Numbers picked from a 5-wolf fight log (tests/den sim), written in docs/team/den_sound_events.md.
 b) Sim: `Ev.Voice{Def,Moment,X,Z}` emitted at bite (Ai.cs contact ~454), lunge windup (Ai.Run), notice (new Enemy.Noticed, reset at Battle.cs ~2122); `Ev.Sound` ids from PackMother (drive/hamstring/howl/phase/call/lunge) in ArenaBosses.cs.
 c) sounds.json events: bed.den, den.pits, den.pack_far, music.den.explore|boss|falls, voice.<kind>.<moment>, her.* (grunt, leap, land, dodge, perfect, stance, heartbeat as existing id `heartbeat`, `dodge`, `dodge.perfect`), boss: voice.packmother.* ; common wolf bite borrows voice_wolfb_bite pitched 0.9.
 d) Engine: SoundState gets the dungeon theme as zone id "den" (Game.cs ~1789, MapRun.IsDungeon + map.Dungeon.Def.Theme) so `bed.den` is found by the existing SetZone path; Synth.Bed gets a Bus field (music beds on the music bus: ducks apply); Recordings lazy for `music_*` families (not in the eager load; mono mix = left); recorded music TakeBed pair with crossfade; synth Music.Set(Silence) in the den; pits = emitters (positions from DenPits via a Godot-free list on ZoneData) with distance fall-off, loop bed per nearest 2 pits; pack_far one-shots before first fight, never during one.
 e) Proof: no Godot import (C: ~22 GB free, guard 20): sim-driven den bot in tests logs voice events through the real limiter (counts, peaks) + an offline mixer replica in tools/sound/ (Python) for master peak; say plainly that no Godot run was done.
 f) Owner's listen list + not-supplied list in docs/team/den_sound_events.md; provenance rows docs/team/provenance.md; PIPELINE.md row.
STATE: 1 DONE; 2-7 NOT STARTED (a-f above is the order).
NEXT IN ORDER: (b) sim events, then (a), (c), (d), (e), (f).

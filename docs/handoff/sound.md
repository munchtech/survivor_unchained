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

PLAN (fixed list 1-7 of the brief) STATE: 1 ingest NOT STARTED; 2 bed/pits/distance pack NOT STARTED; 3 music NOT STARTED; 4 voices NOT STARTED; 5 Pack-Mother NOT STARTED; 6 her NOT STARTED; 7 proof/tables/owner list NOT STARTED.
NEXT IN ORDER: step 1 `tools/sound/demo_ingest.py`.

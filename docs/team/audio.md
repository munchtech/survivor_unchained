# Audio: status (H3 sound, the first audio lead)

Branch `audio-h3`. Brief: `docs/team/hook/H3_sound.md`. Handoff: `docs/handoff/audio.md`.

## What the app can now do
- **Give any event a sound from a line of data:** `godot/data/content/sounds.json` (buses, ducks, foe materials, events -> layers of recorded takes with gain, pitch spread, gain jitter, delay, gate, falloff, stereo). Every Sfx recipe asks the bank first; the synth plays only where an event has no takes. The table is edited in `tools/audio/events.py` (one line per event) or by hand. Every id a recipe can ask for: `godot/data/content/sounds_ids.txt`.
- **Make a sound family from a line of prompt data:** `tools/audio/gen.py make <family>` (ElevenLabs sound generation on the owner's account, cached by prompt hash, logged in `tools/audio/gen_log.jsonl` and `docs/legal/audio_generated.md`), trimmed, normalized, and ranked by CLAP text-audio match and onset count (no one can hear, so the machine picks the takes that best match their brief; the owner's ears judge the result).
- **Record any moment of the game as sound:** `tools/audio/moments.py run <names> --tag <t> [--nobank]` writes master + per-bus stems + the ids fired (`--soundlog`) + loudness numbers to `survivorsunchained_inputs\audio_h3\<t>\`. `--nobank` is the synth-only BEFORE.
- **Measure:** the master compressor, a makeup gain (`buses.master.makeup`, dB) and a -1 dBFS limiter run inside the mixer, so a tape is what the speakers get. `tools/audio/measure.py` gives peak, true peak, LUFS, short-term max.
- **Give each zone its recorded room:** `bed.<zone>.<day|night>`, then `bed.<zone>` (`bed.title` on the title) in sounds.json; `Ambience.SetZone` loops the take, crossfades over about 2 s, and halves the made wide beds under it.
- **End a windup on its blow:** H1's `Ev.Telegraph` plays `telegraph.<kind>.<windup|land>[.boss]`; a windup is cut to the mark's own duration with a short fade (`Clip.Len`, `SoundBank.Play(len:)`), whatever the take's length or pitch.

## Numbers (game tapes, master; the listening sheet `C:\Users\munch\Desktop\survivorsunchained_inputs\audio_h3\README.md`)
BEFORE (old synth through today's mixer) and AFTER (the bank), integrated LUFS / peak dBFS:

| moment | before | after | | moment | before | after |
|---|---|---|---|---|---|---|
| m01 bandits | -21.3 / -1.0 | -20.3 / -1.0 | | m06 draft pick | -25.2 / -13.4 | -24.1 / -8.8 |
| m02 dead horde | -21.3 / -1.0 | -19.9 / -1.0 | | m07 lamps | -27.1 / -13.3 | -25.8 / -9.6 |
| m03 dash | -23.4 / -2.6 | -21.9 / -2.0 | | m08 boss | -20.2 / -1.0 | -17.9 / -1.0 |
| m04 sunder | -22.3 / -1.0 | -20.0 / -1.0 | | m09 won | -24.2 / -8.6 | -22.9 / -5.9 |
| m04 groundbreaker | -22.7 / -1.0 | -21.8 / -1.0 | | m09 fell | -23.5 / -7.9 | -22.8 / -1.3 |
| m04 rebuke | -22.9 / -1.0 | -22.7 / -1.0 | | m10 Low Ford night | -25.1 / -12.0 | -25.0 / -10.5 |
| m04 watch bell | -22.9 / -1.0 | -20.1 / -1.8 | | m10 Deep Shaw night | -25.6 / -13.9 | -25.0 / -8.3 |
| m05 Long Cut | -21.6 / -1.0 | -19.0 / -1.0 | | m10 Waystation | -25.6 / -11.6 | -24.8 / -6.0 |
| m06 embers, level-up | -22.0 / -1.0 | -20.0 / -1.0 | | m10 Verge day | -24.1 / -10.1 | -24.2 / -7.8 |
| m11 telegraphs | -23.6 / -2.1 | -22.0 / -2.2 | | m12 title | -25.7 / -13.5 | -24.8 / -10.7 |

AFTER stems (pre-master): sfx -18 to -25 in fights, music -29 to -31 (boss -23.5), ambience -35 to -40 (about 17 dB under a fight), the Flare -17.9 over the fight's sfx -22.1, ui -24 where it fires densely. Fights sit at the -20 target with makeup 5 dB.

## For the owner (sounds generation could not get right; one line each: what, length, character, a reference in words)
- `lamp_out` (weak match after two prompts): a lamp put out; 0.5 s; a soft breath and a wick's hiss; like blowing out a candle up close.
- Kept on a loosened rule or a second prompt (the machine's match is now good; replace any that miss by ear): `ui_open` (a worn diary opening, 0.4 s), `lamp_lit_big` (a forge-like flare in a brass lantern, 1.2 s), `heal_glow` (warmth spreading, tiny chimes, 0.8 s), `result_fell` (one far funeral bell over a drone, 4 s), `tg_pull_land` (air slammed out of a room, 0.7 s), `spawn_rise` (the risen clawing up, 1 s), `crowdfall` (a crowd dropping at once, 1 s).

## Music (not in H3's list: the next pass, the owner decides)
Today every note is made by `godot/src/Audio/Music.cs` (moods: day, night, town, danger, boss, story; a generative synth score in D). It is likely half of "kinda stink". The route I'd take:
- **Tracks as data:** a `music` block in `sounds.json`: mood -> stems (an ambient bed, a percussion layer, a lead) as looping oggs at one tempo and key (D, the Flare's home note), crossfaded by the mood and the fight's heat that `Music.cs` already computes; stingers (boss, triumph, fell) as one-shots that land on the bar. Long tracks play through a Godot `AudioStreamPlayer` on a Music bus under the same ducks, not through the sample mixer.
- **What the game needs:** the title (2-3 min loop, the hymn's melody, sparse); the town / the Waystation (3 min loop, warm, small ensemble); the night, three intensities layered (calm, pressed, overrun: 2-3 min loops, the same tempo); the boss (2 min loop, percussion forward); stingers already generated as effects above (boss arrival, won, fell) would move here.
- **Source:** the owner's Suno hymn as the title and the melodic seed; ElevenLabs' music model on the owner's account for the loops (it can be asked for stems and a tempo), or the owner composes; no CC0 music library would be one game with the hymn.

## Decisions
- Takes are mono for anything placed in the world (the mixer pans them); stereo for her Flare, the boss, results, beds.
- Footsteps keep Kenney's CC0 grounds with her armor jingle laid on top; the ember pickup keeps its musical ladder with a spark under it (synth "under").
- 15,000 credits stay in reserve for the owner's voice work (gen.py refuses below it).

# Audio: status (H3 sound, the first audio lead)

Branch `audio-h3`. Brief: `docs/team/hook/H3_sound.md`. Handoff: `docs/handoff/audio.md`.

## What the app can now do
- **Give any event a sound from a line of data:** `godot/data/content/sounds.json` (buses, ducks, foe materials, events -> layers of recorded takes with gain, pitch spread, gain jitter, delay, gate, falloff, stereo). Every Sfx recipe asks the bank first; the synth plays only where an event has no takes. The table is edited in `tools/audio/events.py` (one line per event) or by hand. Every id a recipe can ask for: `godot/data/content/sounds_ids.txt`.
- **Make a sound family from a line of prompt data:** `tools/audio/gen.py make <family>` (ElevenLabs sound generation on the owner's account, cached by prompt hash, logged in `tools/audio/gen_log.jsonl` and `docs/legal/audio_generated.md`), trimmed, normalized, and ranked by CLAP text-audio match and onset count (no one can hear, so the machine picks the takes that best match their brief; the owner's ears judge the result).
- **Record any moment of the game as sound:** `tools/audio/moments.py run <names> --tag <t> [--nobank]` writes master + per-bus stems + the ids fired (`--soundlog`) + loudness numbers to `survivorsunchained_inputs\audio_h3\<t>\`. `--nobank` is the synth-only BEFORE.
- **Measure:** the master compressor and a -1 dBFS limiter now run inside the mixer, so a tape is what the speakers get. `tools/audio/measure.py` gives peak, true peak, LUFS, short-term max.

## Numbers (game tapes, master)
BEFORE with the old mix peaked at 0.0 dBFS (clipping) in every fight. With the limiter: peaks -2.5 to -5 dBFS, integrated -24 to -26 LUFS in fights (sfx stem -21 to -25), ambience -36 to -41, music -29 to -31. Target for the next pass: fights about -20 LUFS integrated, true peak <= -1.

## For the owner (sounds generation could not get right; one line each: what, length, character, a reference in words)
- `ui_open` (0 takes kept): a book or journal opening for every screen; 0.4 s; soft leather creak and one paper rustle, intimate; like opening a worn diary.
- `lamp_lit_big` (0 kept): a notable lamp lit on the Lamps screen; 1.2 s; a deep warm whoosh of flame catching in a brass lantern with a ringing metal body; like a forge flaring.
- `lamp_out` (weak match): a lamp put out; 0.5 s; a soft breath and a wick's hiss; like blowing out a candle up close.
- `heal_glow` (weak match): her healing; 0.8 s; a warm soft swell with a few tiny chimes, no tune; like warmth spreading through the chest.
- `result_fell` (weak match): the night lost; 3-4 s; one low mournful drone and a single deep drum, fading; like a funeral bell heard far off.
- `tg_pull_land` (weak match): a vortex's blow at its heart; 0.7 s; an inward suck then a hard crack; like air slammed out of a room.
- `spawn_rise`, `crowdfall` (weak matches): the risen clawing up (1 s, dirt tearing, bones creaking, a rasp) and a crowd dropping at once (1 s, a cascade of thuds).

## Music (not in H3's list: the next pass, the owner decides)
Today every note is made by `godot/src/Audio/Music.cs` (moods: day, night, town, danger, boss, story; a generative synth score in D). It is likely half of "kinda stink". The route I'd take:
- **Tracks as data:** a `music` block in `sounds.json`: mood -> stems (an ambient bed, a percussion layer, a lead) as looping oggs at one tempo and key (D, the Flare's home note), crossfaded by the mood and the fight's heat that `Music.cs` already computes; stingers (boss, triumph, fell) as one-shots that land on the bar. Long tracks play through a Godot `AudioStreamPlayer` on a Music bus under the same ducks, not through the sample mixer.
- **What the game needs:** the title (2-3 min loop, the hymn's melody, sparse); the town / the Waystation (3 min loop, warm, small ensemble); the night, three intensities layered (calm, pressed, overrun: 2-3 min loops, the same tempo); the boss (2 min loop, percussion forward); stingers already generated as effects above (boss arrival, won, fell) would move here.
- **Source:** the owner's Suno hymn as the title and the melodic seed; ElevenLabs' music model on the owner's account for the loops (it can be asked for stems and a tempo), or the owner composes; no CC0 music library would be one game with the hymn.

## Decisions
- Takes are mono for anything placed in the world (the mixer pans them); stereo for her Flare, the boss, results, beds.
- Footsteps keep Kenney's CC0 grounds with her armor jingle laid on top; the ember pickup keeps its musical ladder with a spark under it (synth "under").
- 15,000 credits stay in reserve for the owner's voice work (gen.py refuses below it).

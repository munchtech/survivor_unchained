# Voice shoot-out: the same five hard lines, every way we can make them

For the owner to judge by ear. Each file is one method's best take of one
line (best by the measures below, out of three or four), put through the
same mix: the scene's room, de-essing, light compression, loudness for the
line's volume. Nothing in this folder is in the game. File names are
`<line>__<method>.ogg`.

## The lines

| Line | Who | What it tests |
|---|---|---|
| `1_angry` | Holloway, `liar` | Fury held one notch down; a pause on "So."; the swear landing hard and quiet |
| `2_intimate` | Sella, `free` | Close, unsure, a nervous laugh; a professional dropping her patter |
| `3_wry` | Rook, `runs` | Dry wit building to a laugh on the out-breath |
| `4_grief` | Brannoc, `nell_ditch` | A man who has just learned his daughter is dead |
| `5_shout` | Redcowl, `trick` | Bellowed orders in sudden alarm |

## The methods

Each part's voice was designed (VoxCPM2 voice design from a written
description, auditioned and chosen by measurement: `docs/VO_CAST.md`).
Methods that clone use that voice; the others say so.

| Method | What it is | Licence to ship |
|---|---|---|
| `kokoro` | Kokoro-82M's stock British voices. Clean, in accent, not acted, and not our people: the yardstick for a read | Apache 2.0 |
| `vox_cont` | VoxCPM2 carrying on from a take of the cast voice (the pipeline as first built). Keeps the person; delivery follows the reference take | Apache 2.0 |
| `vox_style` | VoxCPM2 cloning the cast voice with the line's direction as a style instruction | Apache 2.0 |
| `vox_design` | VoxCPM2 voice design per line: the part's description plus how this line is played. The most acted VoxCPM2 mode, but each take is a slightly different person | Apache 2.0 |
| `vox_design-vc` | `vox_design`'s performance turned into the cast voice by Seed-VC (speech model, 22 kHz): the performance keeps its timing and stress, the timbre becomes the part's | Apache 2.0 + GPL-3.0 tool |
| `vox_design-vcf0` | The same through Seed-VC's 44 kHz model, which also follows the performance's pitch | Apache 2.0 + GPL-3.0 tool |
| `chatterbox` | Chatterbox (Resemble AI) cloning the cast voice, exaggeration set from the direction | MIT |
| `indextts` | IndexTTS-2.5 cloning the cast voice, emotion from an eight-number vector | bilibili licence (free under 100M users) |
| `dia` | Dia 1.6B with non-verbal cues ("(sighs)", "(laughs)") and the cast voice as audio prompt; three lines only (very slow here) | Apache 2.0 |
| `orpheus` | Orpheus 3B's stock American voices with emotive tags: a performance, not our voice | Apache 2.0 (Llama base) |
| `orpheus-vc`, `orpheus-vcf0` | Orpheus's performance turned into the cast voice by Seed-VC (the accent stays American) | as above |
| `f5` | F5-TTS cloning the cast voice | weights CC BY-NC: comparison only, cannot ship |

Not run here: Higgs Audio v2 (needs about 24 GB of VRAM), VibeVoice 7B
(too large; the 1.5B was not set up in time), CosyVoice 3 (its Windows
install needs pynini), Fish/OpenAudio S1 (non-commercial weights), and a
human performance converted the same way (the route this pack points to;
see below).

## How the takes were measured

I cannot listen, so every take is measured for the tells of generated
speech (`tools/vo/tells.py`, with Whisper's word timings), beside the usual
checks (the words, the accent, naturalness, the speaker against the cast
voice):

- **Flat prosody**: pitch spread, and how far each word's pitch moves from
  its neighbours.
- **Even pacing**: how much the speed changes from phrase to phrase. People
  rush and hold back; a reader keeps a metronome.
- **Even stress**: how much louder the strong words are than the weak.
  Everything stressed alike is a reader's tell.
- **No breath**: breaths and mouth sounds between phrases.
- **Sheen**: harmonics-to-noise, and how tonal the 4 to 8 kHz band is.
- **Dead air**: the longest silence.

"Moves like a person" folds the first four into one number (each capped so
no one measure can win it). It is a guide to where to listen first, not a
verdict: only an ear can say whether a take sounds made.

<!-- RESULTS -->

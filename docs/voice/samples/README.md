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

## Results

`listen.html` in this folder (open it in a browser) plays every file, line
by line, best guess first; the same page is published, private to the
owner, at https://claude.ai/artifact/T1Bns481cT4bLCAqB6Sipx. Every number
is in `metrics.json`. Across the
five lines, by method (accent "heard right" is the share of the accent
model's vote for the part's own accent; 1 is certain):

| Method | Lines | Words right | Accent heard right | Same voice as cast | Naturalness (UTMOS) | Moves like a person | Pace changes | Stress spread dB | Breaths |
|---|---|---|---|---|---|---|---|---|---|
| dia-vc | 3 | 3/3 | 0.33 | 0.77 | 2.96 | 4.16 | 0.29 | 3.5 | 2.7 |
| dia-vcf0 | 3 | 3/3 | 0.00 | 0.65 | 2.84 | 3.80 | 0.25 | 3.5 | 2.3 |
| orpheus-vcf0 | 5 | 5/5 | 0.19 | 0.63 | 2.86 | 3.06 | 0.13 | 3.8 | 0.6 |
| orpheus | 5 | 5/5 | 0.20 | 0.14 | 4.13 | 2.99 | 0.11 | 4.3 | 0.6 |
| chatterbox | 5 | 5/5 | 0.35 | 0.74 | 3.78 | 2.85 | 0.12 | 3.5 | 0.6 |
| vox_style | 5 | 5/5 | 0.46 | 0.74 | 3.33 | 2.84 | 0.15 | 2.7 | 0.6 |
| orpheus-vc | 5 | 5/5 | 0.03 | 0.69 | 2.81 | 2.82 | 0.07 | 3.6 | 0.4 |
| vox_cont | 5 | 5/5 | 0.59 | 0.81 | 3.48 | 2.81 | 0.11 | 4.0 | 0.2 |
| vox_design | 5 | 5/5 | 0.60 | 0.19 | 3.19 | 2.79 | 0.09 | 3.6 | 0.0 |
| vox_design-vc | 5 | 5/5 | 0.40 | 0.73 | 3.00 | 2.74 | 0.12 | 3.2 | 0.4 |
| dia | 3 | 3/3 | 0.33 | 0.25 | 2.79 | 2.68 | 0.09 | 3.0 | 0.3 |
| vox_design-vcf0 | 5 | 5/5 | 0.42 | 0.74 | 2.69 | 2.65 | 0.05 | 3.6 | 0.4 |
| indextts | 5 | 4/5 | 0.00 | 0.66 | 2.93 | 2.30 | 0.12 | 2.6 | 0.2 |
| f5 | 5 | 5/5 | 0.78 | 0.80 | 3.18 | 2.16 | 0.00 | 3.7 | 0.2 |
| kokoro | 5 | 5/5 | 0.80 | 0.11 | 4.21 | 1.66 | 0.05 | 2.5 | 0.2 |

"Words right" forgives a near-spelling, so a few slips pass it: listen
for "Weave the heavy stuff" (Orpheus, `5_shout`) and "Calloway" and
"Cal's" for Holloway and Pell (Orpheus, `3_wry`).

### What the numbers say

- **Acting first, then converting the voice moves most like a person.**
  Dia's performances turned into the cast voice (`dia-vc`) change pace
  from phrase to phrase about as much as people do (0.29) and breathe
  (2.7 breaths a line); nothing that reads the line directly in the cast
  voice comes close (0.11 to 0.15). The route works: the performance's
  timing and breath survive the conversion.
- **But the performer here is American, so the accent goes.** Dia and
  Orpheus were trained on American speech; converted, they keep their
  American vowels in our people's voices (accent heard right 0.0 to 0.3),
  and conversion costs clarity (naturalness about 2.9 against 3.5 to 4.2).
  VoxCPM2 acting in an English accent (`vox_design`) keeps the accent but
  moves no more than a reader once converted.
- **Of what keeps both the accent and the person**, `vox_cont` (the first
  pipeline) and `vox_style` (the same model, direction as a style note) are
  the strongest, and Chatterbox is close; each has one good line (Sella's
  `2_intimate` in `vox_cont`, 4.55, the best English-voiced take in the
  pack; Brannoc's grief in `chatterbox`). Their pace is still a reader's.
- **The shout fails everywhere.** No model bellows; Redcowl's Scots, which
  his cast voice has, is lost by every method. Kokoro's stock British
  reader is clean and dead, as expected, and F5 (which cannot ship) is the
  most even of all.
- **Nothing scores like a person on every count.** The best take of each
  line is the best of what this machine can make, not a human performance.

### Listen first

1. `2_intimate__vox_cont.ogg`: the best English take; Sella in her own voice.
2. `1_angry__dia-vc.ogg` against `1_angry__vox_cont.ogg`: the performance
   route against the reader, the same words and the same voice.
3. `3_wry__dia-vc.ogg` and `3_wry__vox_design.ogg`: Rook's laugh, acted.
4. `4_grief__chatterbox.ogg`: Brannoc.
5. `5_shout__orpheus.ogg` and `5_shout__vox_cont.ogg`: how far the shout is
   from a shout.

The question for the ear is not which is best, but whether any of them
would pass as a person in the game. My answer, from the numbers, is no:
the generated lines that move like people lose the accent, and the ones
that keep the accent move like readers. Nothing has shipped into the game,
and nothing will until a take passes your ear.

## Round two, and the decision

A second round (October 2026) tried Voicebox's engines (Qwen3-TTS,
Chatterbox, Chatterbox Turbo with tags, LuxTTS, TADA), Maya1 (voices
designed from a sentence, with emotion tags), Dia2 and VibeVoice. It was
stopped part-way when the owner chose the route, so its takes are not in
this pack. What it showed before it stopped:

- **Maya1's performance converted into the cast voice** was the first take
  heard as English (1.0) that also moves like a person (pace change 0.22,
  two breaths, words right), at some cost in clarity (naturalness 3.45).
- **Maya1 on its own and Voicebox's Qwen3** are British and clean
  (naturalness 4.3 to 4.4), and still read like readers (pace 0.04 to 0.12).
- **Chatterbox Turbo** stopped the take at a tag in mid-line.

None of it reaches a movie actor. **The decision (the owner's): final voices
are made in ElevenLabs, one character at a time, directed by packets in
`docs/voice/elevenlabs/`. Every line meanwhile has a local placeholder,
Maya1 converted into the cast voice, marked as a placeholder until its
final replaces it.**

## If none of these is good enough

They may not be: the bar is a human performance, and every file here is
generated. The routes that get there, cheapest first:

1. **One actor's performance, the cast's voices** (performance-driven
   voice conversion). A versatile British character actor (or one woman
   and one man) records every line as a guide performance, in the accents,
   with the direction in the scripts (`python tools/vo/script.py <part>`
   prints each part's lines with their direction). Seed-VC (already set up
   here, `--method perform` in `tools/vo/produce.py` takes any performance)
   turns each line into its part's designed voice. The timing, stress,
   breath and accent are a person's; only the timbre is converted. About
   100 finished minutes for Act 1, roughly 8 to 12 studio hours: at the
   Equity indie minimum (£200 an hour, the first hour £400) about £2,500 to
   £4,000 with a studio, more with a director. The actor must agree in
   writing to the conversion (Equity's AI guidance).
2. **A paid generator with acting control**: ElevenLabs v3 (or the newer
   v4) with audio tags ([whispers], [sighs], [laughs], [shouting]) and
   Voice Design, which does Scots, Irish and Welsh, which nothing local
   here does. Act 1 is about 100,000 characters; with three takes a line,
   about 300,000 credits: one month of the Pro plan ($99, 600,000 credits,
   commercial rights included). Still synthetic, but the best-acted
   synthetic speech available; worth one evening's test on these same five
   lines before deciding.
3. **A human cast**: the principals (narrator, Vonnra, Rook, Brannoc,
   Holloway, Chid, Maeca, Rav, Redcowl, Sella) by actors, the passers-by
   and barks by two or three actors doubling. At Equity indie rates, about
   £10,000 to £15,000 for Act 1 with studio and direction. The only route
   that is certain to have soul.

The game is ready for any of them: line ids and hashes, the scripts with
direction, the mix, the index the game reads, and the tests that keep it
honest are the same whoever makes the takes.

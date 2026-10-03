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

<!-- METHODS -->

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

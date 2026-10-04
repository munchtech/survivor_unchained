# The Red Hand: ElevenLabs packet

Voice id in the game: `red_hand`. 1 takes to record (13 characters; about 39 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

A Kerchief enforcer in his forties, one of Ashford's old levy, with a low, flat, hard west-of-Scotland voice. He never raises it: he is collecting a debt, not threatening. Few words to strangers, and those flat.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The Red Hand`. Never describe a voice as sounding like a real person.

```
Native English (British, Scottish). Male, 40s. Studio quality. Persona: a debt collector. A Kerchief enforcer in his forties, one of Ashford's old levy, with a low, flat, hard west-of-Scotland voice. He never raises it: he is collecting a debt, not threatening. Few words to strangers, and those flat. Thick Scottish accent. No reverb or effects.
```

Preview text:

```
Toll's due. Same as last month, and the month before. Put it in the hand and walk on.
```

In the Voice Library instead: search for *hard west-of-Scotland Scots*, *male*, *40*, and listen for this: A Kerchief enforcer in his forties, one of Ashford's old levy, with a low, flat, hard west-of-Scotland voice. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/cbark.9515915472c5.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice red_hand
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## In a fight

### 1. `cbark.9515915472c5.wav`

*Where:* godot/logic/Play/Bosses/ArenaBosses.cs

```
"Toll's due."
```
Subtitle: "Toll's due."


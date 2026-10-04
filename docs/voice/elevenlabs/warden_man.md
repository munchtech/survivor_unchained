# The Ford-Warden, the man under him: ElevenLabs packet

Voice id in the game: `warden_man`. 1 take to record (14 characters; about 42 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**The Ford-Warden.** The Order's keeper of the Low Ford, older than the Watch. Speaks rarely, in capitals and orders: the dead are told to rise, the living to lie down, nobody to cross. Sings the Order's evening call under the water. His last line is in another voice: the tired man under him, asking if it is morning. *Casting:* a very low bass with no age and no accent that belongs to the valley now, a long cave reverb with water in it; the last line a plain man of sixty, dry, no reverb.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The Ford-Warden, the man under him`. Never describe a voice as sounding like a real person.

```
Native English (British). Male, 60s. Studio quality. Persona: a tired old soldier. A plain, tired man of sixty, an old soldier of a religious order, speaking quietly and close with a dry, worn, slightly hoarse baritone. English, the regional accent worn almost away. No boom, no grandeur: an ordinary man who has been very tired for a very long time. No reverb or effects.
```

Preview text:

```
Is it morning? I kept the lamps. Someone has to keep the lamps, or nobody knows where the water is.
```

In the Voice Library instead: search for *plain English, the accent worn almost away*, *male*, *60*, and listen for this: A plain, tired man of sixty, an old soldier of a religious order, speaking quietly and close with a dry, worn, slightly hoarse baritone. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_heart_goes_down.morning.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice warden_man
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: heart goes down

### 1. `dlg.cin_heart_goes_down.morning.0.wav`

*The same words are also* `cbark.f7a2a69e2307.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_heart_goes_down/morning#0
*Played:* tired, lost; doing: the man under the Warden asks the lamp; pace: slow; volume: quiet.
*Note:* Not the giant's voice: a plain, tired man of sixty, the accent worn off, no boom. Quiet enough that the subtitle is the only certain thing.
*Length:* the cut is timed to it: 1.2–1.6 s, first sound to last word.

```
[tired, lost, quietly] Is it morning?
```
Subtitle: Is it morning?


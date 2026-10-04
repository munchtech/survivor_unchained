# The dead Watchman: ElevenLabs packet

Voice id in the game: `watchman`. 1 takes to record (45 characters; about 135 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Nell, Wat, Corran.** The dead. They never speak; they are spoken of. (The one place the dead are heard is the bottom of the stair, C43, where the Morrow's voices are only names, and Nell's is one word: "Da".) Nell is "Mine." to her father and "Brannoc's girl" to the town. Corran speaks only in his belt-book, three lines in a hand that worsens.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The dead Watchman`. Never describe a voice as sounding like a real person.

```
Native English (British, northern English). Male, 60s. Studio quality. Persona: a dead northern soldier. An old dead soldier speaking in a dry, rasping, hollow whisper with a northern English accent, slow and broken. Thick northern English accent. No reverb or effects.
```

Preview text:

```
It shatters its own lamps when it charges. Make it charge.
```

In the Voice Library instead: search for *northern English*, *male*, *60*, and listen for this: An old dead soldier speaking in a dry, rasping, hollow whisper with a northern English accent, slow and broken.. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/say.b81f9a1e8df8.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice watchman
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Scenes: Prologue

### 1. `say.b81f9a1e8df8.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* dry, broken, dead; doing: the watchman's warning; pace: slow; volume: hushed.

```
[dry, broken, dead, whispers] It broke its own lamps, coming for me. Twice.
```
Subtitle: It broke its own lamps, coming for me. Twice.


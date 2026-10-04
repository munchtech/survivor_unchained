# The bones: ElevenLabs packet

Voice id in the game: `bones`. 1 takes to record (37 characters; about 111 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

An ancient skeleton speaking in a dry, hollow, rasping whisper, very slow and very quiet.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The bones`. Never describe a voice as sounding like a real person.

```
Native English (British, British). Male, ageless, not human. Studio quality. Persona: male voice with british accent. An ancient skeleton speaking in a dry, hollow, rasping whisper, very slow and very quiet. No reverb or effects.
```

Preview text:

```
It was never locked from the outside.
```

In the Voice Library instead: search for *neutral*, *male*, *ageless*, and listen for this: An ancient skeleton speaking in a dry, hollow, rasping whisper, very slow and very quiet.. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/say.4c984565e1f9.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice bones
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Scenes: Verge

### 1. `say.4c984565e1f9.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* ancient, dry; doing: the dead speak; pace: very slow; volume: hushed.

```
[ancient, dry, whispers] It was never locked from the outside.
```
Subtitle: It was never locked from the outside.


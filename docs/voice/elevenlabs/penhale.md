# Penhale, Tam's Pa: ElevenLabs packet

Voice id in the game: `penhale`. 1 take to record (39 characters; about 117 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

**Hold 1 of these** (marked HOLD below, with why); the rest can be recorded now.

## Who they are

A Somerset hill farmer in his forties with a loud, rough, chesty voice and a broad West Country accent. Profane, furious and alive; grateful only by accident.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Penhale, Tam's Pa`. Never describe a voice as sounding like a real person.

```
Native English (British, Somerset, West Country). Male, 40s. Studio quality. Persona: a West Country farmer. A Somerset hill farmer in his forties with a loud, rough, chesty voice and a broad West Country accent. Profane, furious and alive; grateful only by accident. Broad Somerset, West Country accent. No reverb or effects.
```

Preview text:

```
My father ploughed that. And his. And you took your bloody time, the lot of you!
```

In the Voice Library instead: search for *Somerset (West Country)*, *male*, *40*, and listen for this: A Somerset hill farmer in his forties with a loud, rough, chesty voice and a broad West Country accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.scene_count_right.pa.0.p1.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice penhale
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Scene_count_right

### 1. `dlg.scene_count_right.pa.0.p1.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_count_right/pa#0; part 2 of 2: narrator: On his back in the mud, he gets up on one elbow and bawls down the hole. / **penhale: And you took your bloody time, Captain!**

```
And you took your bloody time, Captain!
```
Subtitle: And you took your bloody time, Captain!


# The Legion's dead, behind the door: ElevenLabs packet

Voice id in the game: `barrow_lord`. 4 takes to record (24 characters; about 72 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**The Barrow Lord** (the Seventh Legion). Speaks only the old empire's tongue, one word at a time, like orders given a thousand times ("Nondum", "Redi"). Translated in the subtitles only for a survivor who can read it. *Casting:* a dry, enormous whisper, close to the ear.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The Legion's dead, behind the door`. Never describe a voice as sounding like a real person.

```
Native English (British, British). Male, ageless, not human. Studio quality. Persona: male voice with british accent. An ancient dead soldier speaking from deep inside a stone tomb, a very low, hollow, dry voice like wind in a crypt, slow and final, each word heavy. No reverb or effects.
```

Preview text:

```
Not yet. Go back. The road is shut, and it is kept.
```

In the Voice Library instead: search for *old Latin, inhuman*, *male*, *ageless*, and listen for this: An ancient dead soldier speaking from deep inside a stone tomb, a very low, hollow, dry voice like wind in a crypt, slow and final, each word heavy.. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_behind_the_door.nondum.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice barrow_lord
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: behind the door

### 1. `dlg.cin_behind_the_door.nondum.0.wav`

*Where:* dialogue.json cin_behind_the_door/nondum#0
*Played:* ancient, final; doing: not yet; pace: very slow; volume: quiet.
*Note:* Latin: NON-dum. The narrator does not translate aloud; the subtitle does.

```
[ancient, final, quietly] Nondum.
```
Subtitle: Nondum.

### 2. `dlg.cin_behind_the_door.nondum.1.wav`

*Where:* dialogue.json cin_behind_the_door/nondum#1
*Played:* ancient, final; doing: not yet; pace: very slow; volume: quiet.

```
[ancient, final, quietly] Nondum.
```
Subtitle: Nondum.

### 3. `dlg.cin_behind_the_door.redi.0.wav`

*Where:* dialogue.json cin_behind_the_door/redi#0
*Played:* ancient, final; doing: go back; pace: very slow; volume: quiet.
*Note:* Latin: RED-ee.

```
[ancient, final, quietly] Redi.
```
Subtitle: Redi.

### 4. `dlg.cin_behind_the_door.redi.1.wav`

*Where:* dialogue.json cin_behind_the_door/redi#1
*Played:* ancient, final; doing: go back; pace: very slow; volume: quiet.

```
[ancient, final, quietly] Redi.
```
Subtitle: Redi.


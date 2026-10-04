# A Watchwoman: ElevenLabs packet

Voice id in the game: `guard_f`. 9 takes to record (406 characters; about 1,218 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**The Waystation's watchmen.** Tired men with colds; they say to each other what they always say and watch the survivor too long after.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU A Watchwoman`. Never describe a voice as sounding like a real person.

```
Native English (British, northern English). Female, 30s. Studio quality. Persona: a northern town guardswoman. A tough town guardswoman in her thirties with a firm, low, gruff voice and a flat northern English accent. Curt and unimpressed. Thick northern English accent. No reverb or effects.
```

Preview text:

```
Gates are shut till dawn. Walk on, traveller, and keep that blade sheathed.
```

In the Voice Library instead: search for *northern English*, *female*, *30*, and listen for this: A tough town guardswoman in her thirties with a firm, low, gruff voice and a flat northern English accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/folk.71.f.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice guard_f
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Passers-by

### 1. `folk.71.f.wav`

*Where:* folk.json lines[71]
*Played:* curt; pace: measured; volume: level.

```
[curt] All quiet. Keep it that way.
```
Subtitle: All quiet. Keep it that way.

### 2. `folk.72.f.wav`

*Where:* folk.json lines[72]
*Played:* curt; pace: measured; volume: level.

```
[curt] Gates are shut till dawn.
```
Subtitle: Gates are shut till dawn.

### 3. `folk.73.f.wav`

*Where:* folk.json lines[73]
*Played:* curt; pace: measured; volume: level.

```
[curt] Walk on, traveller.
```
Subtitle: Walk on, traveller.

### 4. `folk.74.f.wav`

*Where:* folk.json lines[74]
*Played:* rough; pace: measured; volume: level.

```
[rough] Piss off home. It's past curfew.
```
Subtitle: Piss off home. It's past curfew.

### 5. `folk.75.f.wav`

*Where:* folk.json lines[75]
*Played:* threatening; pace: measured; volume: level.

```
[threatening] Keep that blade sheathed or I'll sheathe it for you.
```
Subtitle: Keep that blade sheathed or I'll sheathe it for you.

### 6. `folk.76.f.wav`

*Where:* folk.json lines[76]
*Played:* tired; pace: measured; volume: level.

```
[tired] Captain's doubled the gate. Wolves.
```
Subtitle: Captain's doubled the gate. Wolves.

### 7. `folk.81.f.wav`

*Where:* folk.json lines[81]
*Played:* uneasy; pace: measured; volume: level.

```
[uneasy] Captain says to let you be. Captain says it like he's not sure.
```
Subtitle: Captain says to let you be. Captain says it like he's not sure.

### 8. `folk.94.f.wav`

*Where:* folk.json lines[94]
*Played:* rough threat; pace: measured; volume: level.

```
[rough threat] Indoors, before I find a reason. I'm good at finding reasons.
```
Subtitle: Indoors, before I find a reason. I'm good at finding reasons.

### 9. `folk.106.f.wav`

*Where:* folk.json lines[106]
*Played:* uneasy; pace: measured; volume: level.

```
[uneasy] Captain's had a letter with a silver seal. Hasn't said a word since. Not that he says many.
```
Subtitle: Captain's had a letter with a silver seal. Hasn't said a word since. Not that he says many.


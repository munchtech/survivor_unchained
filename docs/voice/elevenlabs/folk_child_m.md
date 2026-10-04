# A town boy: ElevenLabs packet

Voice id in the game: `folk_child_m`. 7 takes to record (205 characters; about 615 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

An eight-year-old boy from the north of England with a high, bright child's voice and a northern accent. Cheeky, loud and excited.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU A town boy`. Never describe a voice as sounding like a real person.

```
Native English (British, northern English). Male, a child of about 8. Studio quality. Persona: an eight-year-old boy with british accent from the north. An eight-year-old boy from the north of England with a high, bright child's voice and a northern accent. Cheeky, loud and excited. Broad northern English accent. No reverb or effects.
```

Preview text:

```
Show us your sword! Go on! Did you kill a wolf? A big one?
```

In the Voice Library instead: search for *northern English*, *male*, *ageless*, and listen for this: An eight-year-old boy from the north of England with a high, bright child's voice and a northern accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/folk.65.m.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice folk_child_m
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Passers-by

### 1. `folk.65.m.wav`

*Where:* folk.json lines[65]
*Played:* excited, child; pace: measured; volume: level.

```
[excited, child] Are you a knight?
```
Subtitle: Are you a knight?

### 2. `folk.66.m.wav`

*Where:* folk.json lines[66]
*Played:* playful, child; pace: measured; volume: level.

```
[playful, child] Tag! You're it!
```
Subtitle: Tag! You're it!

### 3. `folk.67.m.wav`

*Where:* folk.json lines[67]
*Played:* shy, child; pace: measured; volume: level.

```
[shy, child] Mum says not to talk to you.
```
Subtitle: Mum says not to talk to you.

### 4. `folk.68.m.wav`

*Where:* folk.json lines[68]
*Played:* eager, child; pace: measured; volume: level.

```
[eager, child] Show us your sword! Go on!
```
Subtitle: Show us your sword! Go on!

### 5. `folk.69.m.wav`

*Where:* folk.json lines[69]
*Played:* awed, child; pace: measured; volume: level.

```
[awed, child] Did you kill a wolf? A big one?
```
Subtitle: Did you kill a wolf? A big one?

### 6. `folk.70.m.wav`

*Where:* folk.json lines[70]
*Played:* awed, child; pace: measured; volume: level.

```
[awed, child] Is it true you've got a wolf for a friend?
```
Subtitle: Is it true you've got a wolf for a friend?

### 7. `folk.83.m.wav`

*Where:* folk.json lines[83]
*Played:* awed, child; pace: measured; volume: level.

```
[awed, child] Are you a lady knight? Are there lady knights?
```
Subtitle: Are you a lady knight? Are there lady knights?


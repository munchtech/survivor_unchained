# Grimtunnel: ElevenLabs packet

Voice id in the game: `grimtunnel`. 10 takes to record (518 characters; about 1,554 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

**Hold 3 of these** (marked HOLD below) until the story editor's review of section 17 is back; the rest can be recorded now.

## Who they are

**Grimtunnel** (Boss of the Dig). Oily, gleeful, possessive: "Nobody's!", "surface-meat", "downstairs" for the deep. Under the greed, faith: he is carrying a god its heart, and when anything touches that he goes toad-still and very nearly bows, then covers it with a grin. He believes the thing below will be grateful, and says so. *Casting:* Snib's family, bigger, lower, a cackle, a cave reverb that gets wetter as he goes down.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Grimtunnel`. Never describe a voice as sounding like a real person.

```
Native English (British, London). Male, ageless, not human. Studio quality. Persona: male voice with a rough london accent. A big, gleeful goblin boss with a gravelly, oily, low voice and a rough London accent, cackling and greedy, savouring every word. Thick London accent. No reverb or effects.
```

Preview text:

```
Oho! What's this, then? Nobody's, is it? Nobody's! Finders keepers, surface-meat.
```

In the Voice Library instead: search for *goblinish London*, *male*, *ageless*, and listen for this: A big, gleeful goblin boss with a gravelly, oily, low voice and a rough London accent, cackling and greedy, savouring every word.. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_heart_goes_down.nobodys.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice grimtunnel
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: heart goes down

### 1. `dlg.cin_heart_goes_down.nobodys.0.wav`

*Where:* dialogue.json cin_heart_goes_down/nobodys#0
*Played:* gleeful greed; doing: Grimtunnel finds the heart; pace: quick; volume: raised.
*Note:* Cackling delight.

```
[gleeful greed, loudly] Ooh, still lit! Nobody's, is it? Nobody's!
```
Subtitle: Ooh, still lit! Nobody's, is it? Nobody's!

### 2. `dlg.cin_heart_goes_down.downstairs.0.wav`

*Where:* dialogue.json cin_heart_goes_down/downstairs#0
*Played:* sly, sniffing; doing: Grimtunnel smells you; pace: slow; volume: quiet.
*Note:* A sniff; creepy and pleased.

```
[sly, sniffing, quietly] ...You smell like downstairs.
```
Subtitle: ...You smell like downstairs.

### 3. `dlg.cin_heart_goes_down.grateful.0.p0.wav`

*Where:* dialogue.json cin_heart_goes_down/grateful#0; part 1 of 3: **grimtunnel: Finders keepers, surface-m—** / narrator: a sniff / grimtunnel: ...Downstairs'll be ever so grateful.
*Played:* gloating, then reverent; doing: he takes it down; pace: measured; volume: level.
*Note:* Cut off by his own sniff; then oily reverence.

```
[gloating, then reverent] Finders keepers, surface-m—
```
Subtitle: Finders keepers, surface-m—

### 4. `dlg.cin_heart_goes_down.grateful.0.p2.wav`

*Where:* dialogue.json cin_heart_goes_down/grateful#0; part 3 of 3: grimtunnel: Finders keepers, surface-m— / narrator: a sniff / **grimtunnel: ...Downstairs'll be ever so grateful.**
*Played:* gloating, then reverent; doing: he takes it down; pace: measured; volume: level.
*Note:* Cut off by his own sniff; then oily reverence.

```
[gloating, then reverent] ...Downstairs'll be ever so grateful.
```
Subtitle: ...Downstairs'll be ever so grateful.

## Cinematic: dig boils over

### 5. `dlg.cin_dig_boils_over.pump.0.wav`

*Where:* dialogue.json cin_dig_boils_over/pump#0
*Played:* furious, then gleeful; doing: Grimtunnel's pump; pace: quick; volume: shout.
*Note:* 'PUMP' stressed. Then oily calm: 'Downstairs is PATIENT.'

```
[furious, then gleeful, shouting] Surface-meat! You broke my PUMP. ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.
```
Subtitle: Surface-meat! You broke my PUMP. ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.

### 6. `dlg.cin_dig_boils_over.pump.1.wav`

*Where:* dialogue.json cin_dig_boils_over/pump#1
*Played:* furious, then gleeful; doing: Grimtunnel's lads; pace: quick; volume: shout.
*Note:* As pump.0.

```
[furious, then gleeful, shouting] Surface-meat! Killing my lads, are we? ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.
```
Subtitle: Surface-meat! Killing my lads, are we? ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.

### 7. `dlg.cin_dig_boils_over.quiet.0.wav`

*Where:* dialogue.json cin_dig_boils_over/quiet#0
*Played:* delighted, unnerving; doing: he told it about you; pace: quick; volume: raised.
*Note:* 'QUIET' stressed, giddy.

```
[delighted, unnerving, loudly] I told it about you! It went ever so QUIET!
```
Subtitle: I told it about you! It went ever so QUIET!

## In a fight

### 8. `cbark.676eeb4cf137.wav`  HOLD

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* gleeful; doing: finds an unclaimed lamp; pace: quick; volume: raised.
*Note:* Delighted, goblinish.

```
[gleeful, loudly] Ooh, still lit! Nobody's, is it? Nobody's!
```
Subtitle: Ooh, still lit! Nobody's, is it? Nobody's!

### 9. `cbark.ca65f966df2d.wav`  HOLD

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* sly, sniffing; doing: smells you; pace: slow; volume: level.
*Note:* Close and pleased.

```
[sly, sniffing] ...You smell like downstairs.
```
Subtitle: ...You smell like downstairs.

### 10. `cbark.d6a6b3a4b868.wav`  HOLD

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* gleeful; doing: steals and runs; pace: quick; volume: level.
*Note:* Cut off mid-word, a sniff, then smug: delighted, never beaten.

```
[gleeful] Finders keepers, surface-m— [sniffs] ...Downstairs'll be ever so grateful.
```
Subtitle: Finders keepers, surface-m— ...Downstairs'll be ever so grateful.


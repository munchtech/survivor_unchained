# Grimtunnel: ElevenLabs packet

Voice id in the game: `grimtunnel`. 7 takes to record (442 characters; about 1,326 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Grimtunnel** (Boss of the Dig). Oily, gleeful, possessive: "Nobody's!", "surface-meat" (never finished at the survivor once he has smelled downstairs on her in C03: "surface-m—"), "downstairs" for the deep. Under the greed, faith: he is carrying a god its heart, and when anything touches that he goes toad-still and very nearly bows, then covers it with a grin. He believes the thing below will be grateful, and says so. *Casting:* Snib's family, bigger, lower, a cackle, a cave reverb that gets wetter as he goes down.

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

*The same words are also* `cbark.676eeb4cf137.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_heart_goes_down/nobodys#0
*Played:* gleeful greed; doing: Grimtunnel finds the heart; pace: quick; volume: raised.
*Note:* Cackling delight.

```
[gleeful greed, loudly] Ooh, still lit! Nobody's, is it? Nobody's!
```
Subtitle: Ooh, still lit! Nobody's, is it? Nobody's!

### 2. `dlg.cin_heart_goes_down.downstairs.0.wav`

*The same words are also* `cbark.ca65f966df2d.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_heart_goes_down/downstairs#0
*Played:* sly, sniffing; doing: Grimtunnel smells you; pace: slow; volume: quiet.
*Note:* A sniff; creepy and pleased.

```
[sly, sniffing, quietly] ...You smell like downstairs.
```
Subtitle: ...You smell like downstairs.

### 3. `dlg.cin_heart_goes_down.grateful.0.wav`

*The same words are also* `cbark.d6a6b3a4b868.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_heart_goes_down/grateful#0
*Played:* gloating, then reverent; doing: he takes it down; pace: measured; volume: level.
*Note:* Cut off by his own sniff; then oily reverence.

```
[gloating, then reverent] Finders keepers, surface-m— [sniffs] ...Downstairs'll be ever so grateful.
```
Subtitle: Finders keepers, surface-m— ...Downstairs'll be ever so grateful.

## Cinematic: dig boils over

### 4. `dlg.cin_dig_boils_over.pump.0.wav`

*Where:* dialogue.json cin_dig_boils_over/pump#0
*Played:* furious, then gleeful; doing: Grimtunnel's pump; pace: quick; volume: shout.
*Note:* 'PUMP' stressed. Then oily calm: 'Downstairs is PATIENT.'

```
[furious, then gleeful, shouting] Surface-m— ...You broke my PUMP. ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.
```
Subtitle: Surface-m— ...You broke my PUMP. ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.

### 5. `dlg.cin_dig_boils_over.pump.1.wav`

*Where:* dialogue.json cin_dig_boils_over/pump#1
*Played:* furious, then gleeful; doing: Grimtunnel's lads; pace: quick; volume: shout.
*Note:* As pump.0.

```
[furious, then gleeful, shouting] Surface-m— ...Killing my lads, are we? ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.
```
Subtitle: Surface-m— ...Killing my lads, are we? ...Doesn't matter. Downstairs doesn't mind. Downstairs is PATIENT.

### 6. `dlg.cin_dig_boils_over.quiet.0.wav`

*Where:* dialogue.json cin_dig_boils_over/quiet#0
*Played:* delighted, unnerving; doing: he told it about you; pace: quick; volume: raised.
*Note:* 'QUIET' stressed, giddy.

```
[delighted, unnerving, loudly] I told it about you! It went ever so QUIET!
```
Subtitle: I told it about you! It went ever so QUIET!

## In a fight

### 7. `cbark.9fbae2a7c31b.wav`

*Where:* godot/logic/Play/Bosses/ArenaBosses.cs

```
"Ha! Keep upstairs, surface-m— you! I'm wanted DOWNSTAIRS!"
```
Subtitle: "Ha! Keep upstairs, surface-m— you! I'm wanted DOWNSTAIRS!"


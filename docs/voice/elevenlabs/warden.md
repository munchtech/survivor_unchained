# The Ford-Warden: ElevenLabs packet

Voice id in the game: `warden`. 6 takes to record (164 characters; about 492 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**The Ford-Warden.** The Order's keeper of the Low Ford, older than the Watch. Speaks rarely, in capitals and orders: the dead are told to rise, the living to lie down, nobody to cross. Sings the Order's evening call under the water. His last line is in another voice: the tired man under him, asking if it is morning. *Casting:* a very low bass with no age and no accent that belongs to the valley now, a long cave reverb with water in it; the last line a plain man of sixty, dry, no reverb.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The Ford-Warden`. Never describe a voice as sounding like a real person.

```
Native English (British). Male, ageless, not human. Studio quality. Persona: Ancient monster character. An enormous, ancient being with a vast, booming, very deep bass voice, slow and terrible, speaking like a tolling bell. No reverb or effects.
```

Preview text:

```
None cross after dark.
```

In the Voice Library instead: search for *inhuman*, *male*, *ageless*, and listen for this: An enormous, ancient being with a vast, booming, very deep bass voice, slow and terrible, speaking like a tolling bell.. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_none_cross.call.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice warden
```

## The effect

Record every take dry, with no effect or reverb: the game adds it. For every line, it slows it by a quarter (lower and larger), lays a voice an octave down under it, and puts it in a cave with water in it. For the lines that say so, it does the same, and hears it through the river: the top gone, the surface moving over it. So read a little quicker than he should finally sound.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: none cross

### 1. `dlg.cin_none_cross.call.0.wav`

*Where:* dialogue.json cin_none_cross/call#0
*Played:* a slow dirge; doing: the Order's evening call, heard through water; pace: very slow; volume: quiet.
*Note:* Sung low, as a dirge: two phrases of about three seconds with a short breath between; the second trails off as he rises.
*Length:* the cut is timed to 6.4–7.6 s (two phrases of about 3.0 s with 0.8 s between, the second trailing off) once the effect has slowed it, so read it in 5.1–6.1 s, first sound to last word.

```
[a slow dirge, quietly] [singing, under the water] Lamps are lit... stay where they reach...
```
Subtitle: Lamps are lit... stay where they reach...

### 2. `dlg.cin_none_cross.lie_down.0.wav`

*The same words are also* `cbark.d918c7cc3d98.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_none_cross/lie_down#0
*Played:* quiet, gentle; doing: the Order's word for the dead, said over a grave; pace: very slow; volume: quiet.
*Note:* Not a threat: said to her as you would say it over a grave.
*Length:* the cut is timed to 1.0–1.4 s once the effect has slowed it, so read it in 0.8–1.1 s, first sound to last word.

```
[quiet, gentle, quietly] Lie down.
```
Subtitle: Lie down.

### 3. `dlg.cin_none_cross.none.0.wav`

*Where:* dialogue.json cin_none_cross/none#0
*Played:* tired, final; doing: the ford's rule, not a threat; pace: slow; volume: quiet.
*Note:* Every word set down like a stone; no louder than 'Lie down.' The capitals are the subtitle's, not the performance's.
*Length:* the cut is timed to 2.6–3.4 s once the effect has slowed it, so read it in 2.1–2.7 s, first sound to last word.

```
[tired, final, quietly] None… Cross… After dark.
```
Subtitle: NONE. CROSS. AFTER DARK.

## In a fight

### 4. `cbark.345352a478c0.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* vast, commanding; doing: the Warden raises the drowned; pace: slow; volume: shout.
*Note:* A tolling command, enormous and slow. Each word a bell.

```
[vast, commanding, shouting] RISE, YOU WHO DROWNED HERE.
```
Subtitle: RISE, YOU WHO DROWNED HERE.

### 5. `cbark.db6c2c28509f.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* eerie, distant; doing: the Warden's call; pace: slow; volume: hushed.
*Note:* Drawn out, from under the water.

```
[eerie, distant, whispers] Lamps are lit... stay where they reach...
```
Subtitle: Lamps are lit... stay where they reach...

### 6. `cbark.a5b5efc70a27.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* vast, final; doing: the Warden's law; pace: slow; volume: shout.
*Note:* Each word a bell stroke.

```
[vast, final, shouting] NONE CROSS AFTER DARK.
```
Subtitle: NONE CROSS AFTER DARK.


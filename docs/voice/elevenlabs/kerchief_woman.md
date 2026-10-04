# A Kerchief woman: ElevenLabs packet

Voice id in the game: `kerchief_woman`. 1 takes to record (11 characters; about 33 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**The Kerchiefs.** Scots like their chief, rougher; few words to strangers, and those flat.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU A Kerchief woman`. Never describe a voice as sounding like a real person.

```
Native English (British, Scottish). Female, 40s. Studio quality. Persona: a hard refugee. A hard, weary woman in her forties with a rough Scottish accent, one of a camp of hungry refugees, low and blunt. Thick Scottish accent. No reverb or effects.
```

Preview text:

```
Them first. The bairns eat, then the old ones, then us. That's how it's done here.
```

In the Voice Library instead: search for *hard Scots*, *female*, *40*, and listen for this: A hard, weary woman in her forties with a rough Scottish accent, one of a camp of hungry refugees, low and blunt.. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_forty_one_mouths.them_first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice kerchief_woman
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: forty one mouths

### 1. `dlg.cin_forty_one_mouths.them_first.0.wav`

*The same words are also* `say.3bf0d0b0d0da.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_forty_one_mouths/them_first#0
*Played:* hard, weary; doing: the children eat first; pace: measured; volume: level.

```
[hard, weary] Them first.
```
Subtitle: Them first.


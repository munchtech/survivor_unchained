# The babbling lampling: ElevenLabs packet

Voice id in the game: `lampling`. 2 takes to record (421 characters; about 1,263 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**The babbling lampling.** Repetition, broken grammar, the same three facts in a different order. *Casting:* whispered, dry, close.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The babbling lampling`. Never describe a voice as sounding like a real person.

```
Native English (British). Male, ageless, not human. Studio quality. Persona: Small creature character. A small, frightened creature whispering in a dry, rasping, close whisper, repeating itself, half mad with fear. No reverb or effects.
```

Preview text:

```
Down there. Under the one that is dead. There is another. There is always another.
```

In the Voice Library instead: search for *goblinish*, *male*, *ageless*, and listen for this: A small, frightened creature whispering in a dry, rasping, close whisper, repeating itself, half mad with fear.. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.survivor.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice lampling
```

## Saying the names

The text to paste already respells these; keep the respelling: Grimtunnel as *Grim-tunnel*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: the survivor

### 1. `dlg.survivor.first.0.wav`

*Where:* dialogue.json survivor/first#0
*Played:* terrified babble; doing: a lampling broken by what he saw; pace: quick; volume: hushed.
*Note:* A dry, close whisper, rocking. 'MOVED' a hissed burst. Repeats 'Grimtunnel says' like a prayer he no longer believes.

```
[terrified babble, whispers] It moved. The dark moved. We dug, and we dug, and it MOVED. The others went down to see. Grim-tunnel says it is ours now. Grim-tunnel says it is hungry. Grim-tunnel brought it a heart.
```
Subtitle: It moved. The dark moved. We dug, and we dug, and it MOVED. The others went down to see. Grimtunnel says it is ours now. Grimtunnel says it is hungry. Grimtunnel brought it a heart.

### 2. `dlg.survivor.what.0.wav`

*Where:* dialogue.json survivor/what#0
*Played:* hollow terror; doing: what is down there; pace: measured; volume: hushed.
*Note:* Whispered. 'There is always another.' 'Still lit. Still lit.' haunted. Then a frantic pleading whisper: take the map.

```
[hollow terror, whispers] Down there. Under the one that is dead. There is another. There is always another. Kell went down to see. Kell's lamp came back up on its own, still lit. Still lit. Take the map, take it, I do not want to know where the tunnels go any more.
```
Subtitle: Down there. Under the one that is dead. There is another. There is always another. Kell went down to see. Kell's lamp came back up on its own, still lit. Still lit. Take the map, take it, I do not want to know where the tunnels go any more.


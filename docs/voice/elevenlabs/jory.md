# Jory Coyle: ElevenLabs packet

Voice id in the game: `jory`. 15 takes to record (884 characters; about 2,652 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Jory Coyle.** Seventeen and shaken: short sentences, "Uncle", the cage in every other thing he says without saying "cage". *Casting:* Bristol, like Harlan, quiet.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Jory Coyle`. Never describe a voice as sounding like a real person.

```
Native English (British, Bristol). Male, a child of about 17. Studio quality. Persona: a seventeen-year-old Bristol boy. A seventeen-year-old boy from Bristol in the West Country of England, with a young, quiet, unsteady tenor voice and a soft Bristolian accent. Shaken, speaking in short sentences. Thick Bristol accent. No reverb or effects.
```

Preview text:

```
I'm all right. I'm all right. Uncle keeps asking. I keep saying. It was the dark that was the worst of it.
```

In the Voice Library instead: search for *Bristol*, *male*, *10*, and listen for this: A seventeen-year-old boy from Bristol in the West Country of England, with a young, quiet, unsteady tenor voice and a soft Bristolian accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/say.1a1877c48374.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice jory
```

## Saying the names

The text to paste already respells these; keep the respelling: Thornhollow as *Thorn-hollow*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Scenes: Verge

### 1. `say.1a1877c48374.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* panic, hope; doing: Jory asks for his uncle; pace: quick; volume: level.

```
[panic, hope] Jory. Jory Coyle. Is my uncle... Is he...
```
Subtitle: Jory. Jory Coyle. Is my uncle... Is he...

## Conversations: Jory

### 2. `dlg.jory.first.0.wav`

*Where:* dialogue.json jory/first#0
*Played:* shaken gratitude; doing: thanks his rescuer; pace: quick; volume: quiet.
*Wants:* someone to believe it wasn't wolves
*Note:* Short sentences, unsteady. 'I— thank you.' A small laugh-sob about Uncle. Then urgent, quiet: the clerk in violet. 'And they were waiting.' a shiver.

```
[shaken gratitude, quietly] You're the one with the bar. I— thank you. Uncle Harlan hasn't stopped crying. It wasn't wolves, you know. A toll clerk met us on the road, in Vonnra's violet, and said the Old Road was shut at the Waystation and sent us down the forest track. And they were waiting.
```
Subtitle: You're the one with the bar. I— thank you. Uncle Harlan hasn't stopped crying. It wasn't wolves, you know. A toll clerk met us on the road, in Vonnra's violet, and said the Old Road was shut at the Waystation and sent us down the forest track. And they were waiting.

### 3. `dlg.jory.hub.0.p0.wav`

*Where:* dialogue.json jory/hub#0; part 1 of 3: **jory: I'm all right.** / narrator: He isn't. / jory: Uncle's counting crates that aren't there.
*Played:* brittle; doing: he's not all right; pace: slow; volume: quiet.
*Note:* 'I'm all right.' Narrator: he isn't. Bitter about Uncle.

```
[brittle, quietly] I'm all right.
```
Subtitle: I'm all right.

### 4. `dlg.jory.hub.0.p2.wav`

*Where:* dialogue.json jory/hub#0; part 3 of 3: jory: I'm all right. / narrator: He isn't. / **jory: Uncle's counting crates that aren't there.**
*Played:* brittle; doing: he's not all right; pace: slow; volume: quiet.
*Note:* 'I'm all right.' Narrator: he isn't. Bitter about Uncle.

```
[brittle, quietly] Uncle's counting crates that aren't there.
```
Subtitle: Uncle's counting crates that aren't there.

### 5. `dlg.jory.hub.1.wav`

*Where:* dialogue.json jory/hub#1
*Played:* weary, shaken; doing: still shaken; pace: measured; volume: quiet.
*Note:* Flat, tired repetition.

```
[weary, shaken, quietly] I'm all right. I keep saying that. Uncle keeps asking.
```
Subtitle: I'm all right. I keep saying that. Uncle keeps asking.

### 6. `dlg.jory.crates.0.wav`

*Where:* dialogue.json jory/crates#0
*Played:* nervous, curious; doing: what was he carrying; pace: measured; volume: quiet.
*Note:* A list. A boy's bravado on 'every rut'. A pause; quietly frightened question.

```
[nervous, curious, quietly] Salt. Cloth. Iron. And six we weren't to open, Uncle said, and not to take over ruts. I took them over every rut in Thorn-hollow. Nothing happened. ...What was in them?
```
Subtitle: Salt. Cloth. Iron. And six we weren't to open, Uncle said, and not to take over ruts. I took them over every rut in Thornhollow. Nothing happened. ...What was in them?

### 7. `dlg.jory.truth.0.p1.wav`

*Where:* dialogue.json jory/truth#0; part 2 of 4: narrator: He laughs, once, as if you've told him a joke he didn't get. / **jory: Every rut in Thornhollow. I took them over every rut.** / narrator: He stops laughing. / jory: ...Uncle knew. Didn't he. He told me salt.
*Played:* shock, then betrayal; doing: learns the truth; pace: slow; volume: quiet.
*Note:* Narrator: one laugh. Numb repetition. Narrator: he stops laughing. '...Uncle knew.' Hurt. 'He told me salt.' breaking.

```
[shock, then betrayal, quietly] Every rut in Thorn-hollow. I took them over every rut.
```
Subtitle: Every rut in Thornhollow. I took them over every rut.

### 8. `dlg.jory.truth.0.p3.wav`

*Where:* dialogue.json jory/truth#0; part 4 of 4: narrator: He laughs, once, as if you've told him a joke he didn't get. / jory: Every rut in Thornhollow. I took them over every rut. / narrator: He stops laughing. / **jory: ...Uncle knew. Didn't he. He told me salt.**
*Played:* shock, then betrayal; doing: learns the truth; pace: slow; volume: quiet.
*Note:* Narrator: one laugh. Numb repetition. Narrator: he stops laughing. '...Uncle knew.' Hurt. 'He told me salt.' breaking.

```
[shock, then betrayal, quietly] ...Uncle knew. Didn't he. He told me salt.
```
Subtitle: ...Uncle knew. Didn't he. He told me salt.

### 9. `dlg.jory.truth_knew.0.p1.wav`

*Where:* dialogue.json jory/truth_knew#0; part 2 of 2: narrator: He nods. He keeps nodding. / **jory: Right. Right. ...Thank you. I think. I'll know when I've stopped feeling sick.**
*Played:* numb, sick; doing: accepts it; pace: slow; volume: quiet.
*Note:* Narrator for the nodding. 'Right. Right.' Then the family line, sick and honest.

```
[numb, sick, quietly] Right. Right. ...Thank you. I think. I'll know when I've stopped feeling sick.
```
Subtitle: Right. Right. ...Thank you. I think. I'll know when I've stopped feeling sick.

### 10. `dlg.jory.truth_ask.0.p0.wav`

*Where:* dialogue.json jory/truth_ask#0; part 1 of 3: **jory: I will.** / narrator: He doesn't move. / jory: I will.
*Played:* frozen resolve; doing: he will ask; pace: slow; volume: quiet.
*Note:* 'I will.' Narrator: he doesn't move. 'I will.' smaller.

```
[frozen resolve, quietly] I will.
```
Subtitle: I will.

### 11. `dlg.jory.truth_ask.0.p2.wav`

*Where:* dialogue.json jory/truth_ask#0; part 3 of 3: jory: I will. / narrator: He doesn't move. / **jory: I will.**
*Played:* frozen resolve; doing: he will ask; pace: slow; volume: quiet.
*Note:* 'I will.' Narrator: he doesn't move. 'I will.' smaller.

```
[frozen resolve, quietly] I will.
```
Subtitle: I will.

### 12. `dlg.jory.salt.0.p1.wav`

*Where:* dialogue.json jory/salt#0; part 2 of 2: narrator: He nods, and it goes out of his face at once, the way it goes out of a child's. / **jory: Salt. Right. ...Thanks.**
*Played:* relief, deflation; doing: believes the lie; pace: slow; volume: quiet.
*Note:* Narrator: it goes out of his face. 'Salt. Right.' relieved and young. 'Thanks.'

```
[relief, deflation, quietly] Salt. Right. ...Thanks.
```
Subtitle: Salt. Right. ...Thanks.

## Said in passing

### 13. `bark.jory.day.0.wav`

*Where:* npcs.json jory.barks[0]
*Played:* shaken; pace: measured; volume: quiet.

```
[shaken, quietly] I thought I'd die in there.
```
Subtitle: I thought I'd die in there.

### 14. `bark.jory.day.1.wav`

*Where:* npcs.json jory.barks[1]
*Played:* wry, tired; pace: measured; volume: quiet.

```
[wry, tired, quietly] Uncle keeps hugging me. It's a lot.
```
Subtitle: Uncle keeps hugging me. It's a lot.

### 15. `bark.jory.day.2.wav`

*Where:* npcs.json jory.barks[2]
*Played:* haunted; pace: slow; volume: quiet.
*Note:* 'Was.' alone, chilling.

```
[haunted, quietly] There were four of us. Were.
```
Subtitle: There were four of us. Were.


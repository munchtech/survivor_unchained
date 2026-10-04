# Tam: ElevenLabs packet

Voice id in the game: `tam`. 19 takes to record (1,814 characters; about 5,442 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Tam** (farm boy). Nine. Run-on sentences joined with "and"; "Pa says"; the exact thing he saw, in order, with the wrong word for the important part. Earnest. Repeats a swear word he has overheard and is pleased about it. Never sarcastic. *Casting:* a young adult voice lightly pitched up, or very short lines.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Tam`. Never describe a voice as sounding like a real person.

```
Native English (British, Somerset, West Country). Male, a child of about 9. Studio quality. Persona: a nine-year-old boy with british accent from the West Country. A nine-year-old farm boy from Somerset in the West Country of England, with a light, high child's voice and a soft rural West Country accent. Earnest and breathless, his words tumbling out one after another. Thick Somerset, West Country accent. No reverb or effects.
```

Preview text:

```
Pa says stay in town, so I stayed in town. But I saw them, I did. Three wolves, down by the green water, and they drank and they fell down.
```

In the Voice Library instead: search for *Somerset (West Country)*, *male*, *ageless*, and listen for this: A nine-year-old farm boy from Somerset in the West Country of England, with a light, high child's voice and a soft rural West Country accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.tam.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice tam
```

## Saying the names

The text to paste already respells these; keep the respelling: Penhale's as *Pen-hale's*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Tam

### 1. `dlg.tam.first.0.wav`

*Where:* dialogue.json tam/first#0
*Played:* earnest, desperate to be believed; doing: tells what he saw; pace: quick; volume: level.
*Wants:* one grown-up to believe him
*Note:* A child's voice, rushing. 'Three of them.' 'Nobody believes me.' sulky. A pause; small and hopeful: 'You believe me?'

```
[earnest, desperate to be believed] They drank from the stream and they fell down. Three of them. Nobody believes me. ...You believe me?
```
Subtitle: They drank from the stream and they fell down. Three of them. Nobody believes me. ...You believe me?

### 2. `dlg.tam.story.0.wav`

*Where:* dialogue.json tam/story#0
*Played:* earnest, breathless; doing: the whole story; pace: quick; volume: level.
*Note:* Run-on, joined with 'and', the exact details in order. 'like Gran's' matter-of-fact. 'Pa says stay in town. I stayed in town.' proud of obeying.

```
[earnest, breathless] Down by the green water, past the old fence where Pa lost the goat. Three wolves. They drank and they lay down and they didn't get up, and their eyes went all milky like Gran's. And the water smells like the chapel lamps. Pa says stay in town. I stayed in town.
```
Subtitle: Down by the green water, past the old fence where Pa lost the goat. Three wolves. They drank and they lay down and they didn't get up, and their eyes went all milky like Gran's. And the water smells like the chapel lamps. Pa says stay in town. I stayed in town.

### 3. `dlg.tam.farm.0.wav`

*Where:* dialogue.json tam/farm#0
*Played:* earnest, worried; doing: the farm; pace: quick; volume: level.
*Note:* Proud 'Penhale's, that's us.' Quoting Pa gruffly. 'But these ones aren't right.' worried.

```
[earnest, worried] Out past the Old Road, where the wood starts. Pen-hale's, that's us. Pa won't leave it. He says wolves is wolves and a farm's a farm. But these ones aren't right.
```
Subtitle: Out past the Old Road, where the wood starts. Penhale's, that's us. Pa won't leave it. He says wolves is wolves and a farm's a farm. But these ones aren't right.

### 4. `dlg.tam.again.0.wav`

*Where:* dialogue.json tam/again#0
*Played:* frightened; doing: wolves at the gate; pace: measured; volume: quiet.
*Note:* Small and scared. 'Not ever, maybe.' trailing.

```
[frightened, quietly] They came right up to the gate. I heard them. Pa says we're not going home. Not ever, maybe.
```
Subtitle: They came right up to the gate. I heard them. Pa says we're not going home. Not ever, maybe.

### 5. `dlg.tam.again.1.wav`

*Where:* dialogue.json tam/again#1
*Played:* indignant, relieved; doing: Pa was hurt; pace: quick; volume: raised.
*Note:* Relief on the arm. Then furious child: 'I SAID it was wolves. Weeks ago.'

```
[indignant, relieved, loudly] Pa's at Wenna's. She says he'll keep the arm. The Watch says it was wolves. I SAID it was wolves. Weeks ago.
```
Subtitle: Pa's at Wenna's. She says he'll keep the arm. The Watch says it was wolves. I SAID it was wolves. Weeks ago.

### 6. `dlg.tam.again.2.wav`

*Where:* dialogue.json tam/again#2
*Played:* excited, thrilled; doing: the hens and Pa's bad word; pace: quick; volume: raised.
*Note:* Breathless outrage about the hens. Thrilled by the bad word. 'He was smiling, though.'

```
[excited, thrilled, loudly] The wolves broke our door and ate all the hens. All of them. Pa says he'd have been in the hens' place if not for you, and then he called you a bad word. He was smiling, though.
```
Subtitle: The wolves broke our door and ate all the hens. All of them. Pa says he'd have been in the hens' place if not for you, and then he called you a bad word. He was smiling, though.

### 7. `dlg.tam.again.3.wav`

*Where:* dialogue.json tam/again#3
*Played:* frightened, small; doing: Pa didn't come home; pace: slow; volume: quiet.
*Note:* Very quiet. 'He always comes in.' a child trying not to cry.

```
[frightened, small, quietly] Pa didn't come in last night. He always comes in.
```
Subtitle: Pa didn't come in last night. He always comes in.

### 8. `dlg.tam.again.4.wav`

*Where:* dialogue.json tam/again#4
*Played:* hopeful; doing: any news; pace: measured; volume: level.

```
[hopeful] Did you find out what's wrong with them?
```
Subtitle: Did you find out what's wrong with them?

### 9. `dlg.tam.happy.0.wav`

*Where:* dialogue.json tam/happy#0
*Played:* overjoyed; doing: the water's clear; pace: quick; volume: raised.
*Note:* Bouncing. 'Did you do it?' in awe.

```
[overjoyed, loudly] The water's clear! Pa says I can go home! Pa says you did it. Did you do it?
```
Subtitle: The water's clear! Pa says I can go home! Pa says you did it. Did you do it?

### 10. `dlg.tam.cb_killed_greymuzzle.0.wav`

*Where:* dialogue.json tam/cb_killed_greymuzzle#0
*Played:* uncertain, sad; doing: the big grey one; pace: measured; volume: quiet.
*Note:* Awed question; then quieter, sad: was he sick too?

```
[uncertain, sad, quietly] Did you kill the big grey one? ...Was he sick too?
```
Subtitle: Did you kill the big grey one? ...Was he sick too?

### 11. `dlg.tam.cb_grey2.0.wav`

*Where:* dialogue.json tam/cb_grey2#0
*Played:* trying to understand; doing: accepts it; pace: slow; volume: quiet.
*Note:* 'Oh.' Repeating Pa. 'Pa says a lot of things.' a child's doubt.

```
[trying to understand, quietly] Oh. ...Pa says you have to, sometimes. Pa says a lot of things.
```
Subtitle: Oh. ...Pa says you have to, sometimes. Pa says a lot of things.

### 12. `dlg.tam.t_tam.0.wav`

*Where:* dialogue.json tam/t_tam#0
*Played:* wistful, cheerful; doing: Clover the goat; pace: measured; volume: level.
*Note:* Fond. The hat said with delight. 'I think she's happy.' hopeful.

```
[wistful, cheerful] No. Her name was Clover and she ate a whole hat once. Pa says the wolves got her. I think she ran off to be a wild goat. I think she's happy.
```
Subtitle: No. Her name was Clover and she ate a whole hat once. Pa says the wolves got her. I think she ran off to be a wild goat. I think she's happy.

### 13. `dlg.tam.tock.0.wav`

*Where:* dialogue.json tam/tock#0
*Played:* earnest, spooked; doing: the knocking; pace: quick; volume: quiet.
*Note:* One long breathless run-on. 'Tock, and then tock' imitated softly. Quoting Pa sleepily. 'but it kept knocking.' quiet and spooked.

```
[earnest, spooked, quietly] The ground knocks. At night. Tock, and then tock, under the floor, like somebody wanting to come in, and Pa says it's moles, and I said moles don't knock, and he said go to sleep Tam, so I did, but it kept knocking.
```
Subtitle: The ground knocks. At night. Tock, and then tock, under the floor, like somebody wanting to come in, and Pa says it's moles, and I said moles don't knock, and he said go to sleep Tam, so I did, but it kept knocking.

## Said in passing

### 14. `bark.tam.day.0.wav`

*Where:* npcs.json tam.barks[0]
*Played:* earnest; pace: quick; volume: level.

```
[earnest] Pa says stay in town.
```
Subtitle: Pa says stay in town.

### 15. `bark.tam.said.0.wav`

*Where:* npcs.json tam.said[0]
*Played:* earnest; doing: what he saw; pace: quick; volume: level.
*Note:* A boy insisting.

```
[earnest] They drank from the stream and fell down.
```
Subtitle: They drank from the stream and fell down.

### 16. `bark.tam.said.1.wav`

*Where:* npcs.json tam.said[1]
*Played:* aggrieved; doing: nobody believed him; pace: quick; volume: level.
*Note:* Hurt pride.

```
[aggrieved] I told the Watch. The Watch laughed.
```
Subtitle: I told the Watch. The Watch laughed.

### 17. `bark.tam.said.2.wav`

*Where:* npcs.json tam.said[2]
*Played:* triumphant; doing: he was right; pace: quick; volume: raised.
*Note:* 'and I was.' a boy's triumph.

```
[triumphant, loudly] The stream's clear and Pa says I was right, and I was.
```
Subtitle: The stream's clear and Pa says I was right, and I was.

### 18. `bark.tam.said.3.wav`

*Where:* npcs.json tam.said[3]
*Played:* troubled; doing: the wolves were all killed; pace: measured; volume: level.
*Note:* Upset, not sure he's allowed to be.

```
[troubled] Somebody killed all the wolves. Even the ones that were only sick.
```
Subtitle: Somebody killed all the wolves. Even the ones that were only sick.

### 19. `bark.tam.said.4.wav`

*Where:* npcs.json tam.said[4]
*Played:* spooked, earnest; doing: knocking under the barn; pace: quick; volume: level.
*Note:* 'We've got no pipes.' the point he's sure of.

```
[spooked, earnest] Still knocking under our floor. Pa's stopped saying it's moles.
```
Subtitle: Still knocking under our floor. Pa's stopped saying it's moles.


# Ysolde Marrow, the Wayfinder: ElevenLabs packet

Voice id in the game: `ysolde`. 26 takes to record (3,142 characters; about 9,426 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Ysolde Marrow** (the Wayfinder). Brisk, bookish, gallows humour; talks about the dead as entries in a margin; contractions. Precise about maps, vague about who buys her notes. *Casting:* 50s, Edinburgh.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Ysolde Marrow, the Wayfinder`. Never describe a voice as sounding like a real person.

```
Native English (British, Edinburgh Scottish). Female, 50s. Studio quality. Persona: an Edinburgh cartographer. A woman in her fifties, a cartographer from Edinburgh in Scotland, with a crisp, educated Edinburgh Scottish accent. Brisk, bookish and dry, with a gallows sense of humour. Broad Edinburgh Scottish accent. No reverb or effects.
```

Preview text:

```
Maps! Places the road forgets. Some of them it forgot on purpose. Read the oaths in the margins before you go; they are not decoration.
```

In the Voice Library instead: search for *Edinburgh*, *female*, *50*, and listen for this: A woman in her fifties, a cartographer from Edinburgh in Scotland, with a crisp, educated Edinburgh Scottish accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.wayfinder.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice ysolde
```

## Saying the names

The text to paste already respells these; keep the respelling: Ysolde as *Ee-zolda*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: the Wayfinder

### 1. `dlg.wayfinder.first.0.wav`

*Where:* dialogue.json wayfinder/first#0
*Played:* brisk, dry, bookish; doing: sells her maps; pace: brisk; volume: level.
*Wants:* a customer who'll come back
*Hides:* she sells the names of those who come back, to feed her brother in his cage
*Note:* Brisk Edinburgh. 'Most only ever buy the one.' dry, a cartographer's sales line, no relish. 'barrows' a touch faster, no weight: it's her brother's. The last two sentences drier and darker.

```
[brisk, dry, bookish] You've the look of someone who'll want a second map… Good. Most only ever buy the one. [inhales] I'm Ee-zolda Marrow, and I draw maps of the places the road forgets: woods that eat their own paths, barrows that open after dark, ravines the Kerchiefs think are theirs… Each one sworn under an oath. Each one ruled by something that won't want you there.
```
Subtitle: You've the look of someone who'll want a second map. Good. Most only ever buy the one. I'm Ysolde Marrow, and I draw maps of the places the road forgets: woods that eat their own paths, barrows that open after dark, ravines the Kerchiefs think are theirs. Each one sworn under an oath. Each one ruled by something that won't want you there.

### 2. `dlg.wayfinder.hub.0.wav`

*Where:* dialogue.json wayfinder/hub#0
*Played:* pleased, brisk; doing: welcomes you back; pace: brisk; volume: level.
*Note:* A beat where the name would be. Approving.

```
[pleased, brisk] Back from the edges, and in one piece. The places you took are quieter for it. I've new ones.
```
Subtitle: Back from the edges, and in one piece. The places you took are quieter for it. I've new ones.

### 3. `dlg.wayfinder.hub.1.wav`

*Where:* dialogue.json wayfinder/hub#1
*Played:* brisk; doing: sells maps; pace: brisk; volume: level.
*Note:* A beat where the name would be.

```
[brisk] Maps. Places the road forgets. Pick one.
```
Subtitle: Maps. Places the road forgets. Pick one.

### 4. `dlg.wayfinder.oaths.0.wav`

*Where:* dialogue.json wayfinder/oaths#0
*Played:* precise, dry; doing: explains the oaths; pace: measured; volume: level.
*Note:* A cartographer's precision. 'Those are the choices.' dry gallows humour.

```
[precise, dry] Every map is sworn under something, written in the margin: the Long Winter, the Blight, Iron, a shorter light. The place keeps its oath, and so will you, whether you read it or not. A cold place pays out in things that keep the cold off. Go in dressed for it, or come out dressed for it. Those are the choices.
```
Subtitle: Every map is sworn under something, written in the margin: the Long Winter, the Blight, Iron, a shorter light. The place keeps its oath, and so will you, whether you read it or not. A cold place pays out in things that keep the cold off. Go in dressed for it, or come out dressed for it. Those are the choices.

### 5. `dlg.wayfinder.places.0.wav`

*Where:* dialogue.json wayfinder/places#0
*Played:* matter-of-fact, gallows humour; doing: what happens in there; pace: brisk; volume: level.
*Note:* Rules laid out briskly. 'I sell them fewer maps.' deadpan.

```
[matter-of-fact, gallows humour] Half an hour, give or take, and it only gets worse. The ember in you starts from nothing in there, same as every night. Last the half hour and whatever rules the place comes out to see who's been killing its people. Kill it and the way out opens where it fell. Stay past that if you like. Some do. I sell them fewer maps.
```
Subtitle: Half an hour, give or take, and it only gets worse. The ember in you starts from nothing in there, same as every night. Last the half hour and whatever rules the place comes out to see who's been killing its people. Kill it and the way out opens where it fell. Stay past that if you like. Some do. I sell them fewer maps.

### 6. `dlg.wayfinder.drawn.0.wav`

*Where:* dialogue.json wayfinder/drawn#0
*Played:* bookish, a shadow; doing: who draws the maps; pace: measured; volume: level.
*Note:* Plain trade. The dead drawn 'from where their light went out' quieter, almost tender.

```
[bookish, a shadow] People like you. They walk in, and some of them walk out, and I buy what they remember before the drink takes it. The ones who don't walk out, I draw from where their light went out. You can see it from the road, if you know how to look.
```
Subtitle: People like you. They walk in, and some of them walk out, and I buy what they remember before the drink takes it. The ones who don't walk out, I draw from where their light went out. You can see it from the road, if you know how to look.

### 7. `dlg.wayfinder.notes.0.wav`

*Where:* dialogue.json wayfinder/notes#0
*Played:* evasive, then uneasy honesty; doing: who buys her notes; pace: measured; volume: quiet.
*Note:* Vague list, a little too light. Pause. Then lower, almost a warning: 'So has he.'

```
[evasive, then uneasy honesty, quietly] Collectors. Scholars. A gentleman in the north who likes silver ink and doesn't haggle. I don't ask, and the maps get drawn. ...You come back more often than most, you know. I've noticed. So has he.
```
Subtitle: Collectors. Scholars. A gentleman in the north who likes silver ink and doesn't haggle. I don't ask, and the maps get drawn. ...You come back more often than most, you know. I've noticed. So has he.

### 8. `dlg.wayfinder.cb_nemesis_slain.0.wav`

*Where:* dialogue.json wayfinder/cb_nemesis_slain#0
*Played:* delighted, dry; doing: a good story; pace: brisk; volume: level.
*Note:* Pleased; a writer's relish.

```
[delighted, dry] You went back for whatever killed you, and took your things off it. That's going in a margin. People like reading about that.
```
Subtitle: You went back for whatever killed you, and took your things off it. That's going in a margin. People like reading about that.

### 9. `dlg.wayfinder.cb_opened_vault.0.wav`

*Where:* dialogue.json wayfinder/cb_opened_vault#0
*Played:* uneasy, dry; doing: doesn't want to know; pace: measured; volume: quiet.
*Note:* Dry, with real fear under 'that far down'.

```
[uneasy, dry, quietly] You've been under the black door. Don't tell me what's on the stair; I'd only have to draw it, and I don't draw that far down.
```
Subtitle: You've been under the black door. Don't tell me what's on the stair; I'd only have to draw it, and I don't draw that far down.

### 10. `dlg.wayfinder.say_calling.0.wav`

*Where:* dialogue.json wayfinder/say_calling#0
*Played:* dry advice; doing: reads a warden; pace: measured; volume: level.

```
[dry advice] A warden. You'll hold a clearing longer than most. Mind you don't hold it after it's stopped being worth holding.
```
Subtitle: A warden. You'll hold a clearing longer than most. Mind you don't hold it after it's stopped being worth holding.

### 11. `dlg.wayfinder.say_calling.1.wav`

*Where:* dialogue.json wayfinder/say_calling#1
*Played:* gallows humour; doing: reads a reaver; pace: measured; volume: level.

```
[gallows humour] A reaver. You'll go in at the front and come out the back. The maps don't care which, but I do; I sell more of them to the living.
```
Subtitle: A reaver. You'll go in at the front and come out the back. The maps don't care which, but I do; I sell more of them to the living.

### 12. `dlg.wayfinder.say_calling.2.wav`

*Where:* dialogue.json wayfinder/say_calling#2
*Played:* dry, ominous; doing: reads an arcanist; pace: measured; volume: level.
*Note:* 'I've a margin for people like you.' dry and ominous.

```
[dry, ominous] An arcanist. You'll burn brighter than most in there, and faster. I've a margin for people like you.
```
Subtitle: An arcanist. You'll burn brighter than most in there, and faster. I've a margin for people like you.

### 13. `dlg.wayfinder.say_calling.3.wav`

*The same words are also* `dlg.wayfinder.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json wayfinder/say_calling#3
*Played:* conspiratorial; doing: reads a stalker; pace: measured; volume: level.
*Note:* Pointing at the map. A joke at the reavers.

```
[conspiratorial] A stalker. You'll want the maps with cover. Here, and here. Don't tell the reavers; they'll only stand in it.
```
Subtitle: A stalker. You'll want the maps with cover. Here, and here. Don't tell the reavers; they'll only stand in it.

### 14. `dlg.wayfinder.t_wayfinder.0.wav`

*Where:* dialogue.json wayfinder/t_wayfinder#0
*Played:* quiet grief, dry; doing: her brother; pace: slow; volume: quiet.
*Note:* 'Once.' The facts, plain. 'My brother didn't.' steady. 'I still can't get the corners right.' dry, and it hurts.

```
[quiet grief, dry, quietly] Once. A barrow in the Morrow hills, twelve years back. I came out. My brother didn't. I've drawn it eleven times since and I still can't get the corners right.
```
Subtitle: Once. A barrow in the Morrow hills, twelve years back. I came out. My brother didn't. I've drawn it eleven times since and I still can't get the corners right.

### 15. `dlg.wayfinder.margin.0.p0.wav`

*Where:* dialogue.json wayfinder/margin#0; part 1 of 3: **ysolde: Who came back, from where, how long they lasted, what they carried out. Name first; I'm a …** / narrator: She dips her pen. / ysolde: Speaking of which. How do I put you down?
*Played:* brisk, practised; doing: asks your name for the margin; pace: brisk; volume: level.
*Wants:* your name
*Hides:* where it goes
*Note:* Light because practised. 'put you down' means write, and also the other thing: she never hears the second meaning. Narrator: the pen.

```
[brisk, practised] Who came back, from where, how long they lasted, what they carried out… Name first… I'm a tidy woman.
```
Subtitle: Who came back, from where, how long they lasted, what they carried out. Name first; I'm a tidy woman.

### 16. `dlg.wayfinder.margin.0.p2.wav`

*Where:* dialogue.json wayfinder/margin#0; part 3 of 3: ysolde: Who came back, from where, how long they lasted, what they carried out. Name first; I'm a … / narrator: She dips her pen. / **ysolde: Speaking of which. How do I put you down?**
*Played:* brisk, practised; doing: asks your name for the margin; pace: brisk; volume: level.
*Wants:* your name
*Hides:* where it goes
*Note:* Light because practised. 'put you down' means write, and also the other thing: she never hears the second meaning. Narrator: the pen.

```
[brisk, practised] Speaking of which… How do I put you down?
```
Subtitle: Speaking of which. How do I put you down?

### 17. `dlg.wayfinder.margin_name.0.p1.wav`

*Where:* dialogue.json wayfinder/margin_name#0; part 2 of 2: narrator: She writes it, blots it, and blows on it. / **ysolde: There. Now you're in the margins for good.**
*Played:* satisfied; doing: writes your name; pace: measured; volume: level.
*Note:* Narrator for the writing and blotting. 'There.' A little ceremony in the last line.

```
[satisfied] There. Now you're in the margins for good.
```
Subtitle: There. Now you're in the margins for good.

### 18. `dlg.wayfinder.margin_nobody.0.p0.wav`

*Where:* dialogue.json wayfinder/margin_nobody#0; part 1 of 3: **ysolde: Nobody.** / narrator: She writes it without blinking. / ysolde: You'd be surprised how often Nobody comes back. More than most.
*Played:* deadpan; doing: writes Nobody; pace: measured; volume: level.
*Note:* On audio the capital N vanishes: give the second 'Nobody' the same name-shape and weight she gave it as she wrote it, with a tiny beat before it; then 'More than most' lands the joke. Deadpan, no chill added.

```
[deadpan] Nobody.
```
Subtitle: Nobody.

### 19. `dlg.wayfinder.margin_nobody.0.p2.wav`

*Where:* dialogue.json wayfinder/margin_nobody#0; part 3 of 3: ysolde: Nobody. / narrator: She writes it without blinking. / **ysolde: You'd be surprised how often Nobody comes back. More than most.**
*Played:* deadpan; doing: writes Nobody; pace: measured; volume: level.
*Note:* On audio the capital N vanishes: give the second 'Nobody' the same name-shape and weight she gave it as she wrote it, with a tiny beat before it; then 'More than most' lands the joke. Deadpan, no chill added.

```
[deadpan] You'd be surprised how often… Nobody comes back… More than most.
```
Subtitle: You'd be surprised how often Nobody comes back. More than most.

### 20. `dlg.wayfinder.margin_lark.0.p1.wav`

*Where:* dialogue.json wayfinder/margin_lark#0; part 2 of 2: narrator: She looks at you over the pen for a moment, then writes. / **ysolde: Lark. You look like a Lark. Larks get up early and make a great deal of noise about it.**
*Played:* dry, quick; doing: names you Lark; pace: measured; volume: level.
*Hides:* by making a name up she chooses not to sell you: a kindness she won't own
*Note:* Edinburgh dry and quick, not fond teasing. The kindness is in the choice, not the voice.

```
[dry, quick] Lark… You look like a Lark. Larks get up early… and make a great deal of noise about it.
```
Subtitle: Lark. You look like a Lark. Larks get up early and make a great deal of noise about it.

## Said in passing

### 21. `bark.wayfinder.day.0.wav`

*Where:* npcs.json wayfinder.barks[0]
*Played:* hawking; pace: brisk; volume: raised.

```
[hawking, loudly] Maps! Places the road forgets. Some of them it forgot on purpose.
```
Subtitle: Maps! Places the road forgets. Some of them it forgot on purpose.

### 22. `bark.wayfinder.day.1.wav`

*Where:* npcs.json wayfinder.barks[1]
*Played:* dry; pace: measured; volume: level.

```
[dry] Every map on this table was drawn by someone who came back. Not always all of them.
```
Subtitle: Every map on this table was drawn by someone who came back. Not always all of them.

### 23. `bark.wayfinder.day.2.wav`

*Where:* npcs.json wayfinder.barks[2]
*Played:* dry; pace: measured; volume: level.

```
[dry] Read the oaths in the margins before you go. They are not decoration.
```
Subtitle: Read the oaths in the margins before you go. They are not decoration.

### 24. `bark.wayfinder.day.3.wav`

*Where:* npcs.json wayfinder.barks[3]
*Played:* dry; pace: measured; volume: level.

```
[dry] Half an hour in there and the thing that owns it comes to see who's making the noise.
```
Subtitle: Half an hour in there and the thing that owns it comes to see who's making the noise.

### 25. `bark.wayfinder.night.0.wav`

*Where:* npcs.json wayfinder.nightBarks[0]
*Played:* gallows humour; pace: measured; volume: level.

```
[gallows humour] The ink is still wet on this one. So is the blood.
```
Subtitle: The ink is still wet on this one. So is the blood.

### 26. `bark.wayfinder.night.1.wav`

*Where:* npcs.json wayfinder.nightBarks[1]
*Played:* dry; pace: measured; volume: level.

```
[dry] Night maps cost the same. They just feel dearer.
```
Subtitle: Night maps cost the same. They just feel dearer.


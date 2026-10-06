# Old Wenna: ElevenLabs packet

Voice id in the game: `wenna`. 34 takes to record (4,069 characters; about 12,207 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Old Wenna** (herbalist). Brisk, cracked, impatient; lists of plants and symptoms; interrupts herself with a dash when she gets interested, and speeds up. Calls everyone "child". Very rude, very kind. Never admits to being frightened, and never names the fever year's dead. *Casting:* 70s, Somerset.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Old Wenna`. Never describe a voice as sounding like a real person.

```
Native English (British, Somerset, West Country). Female, 70s. Studio quality. Persona: a West Country village herbalist. An old woman in her seventies, a village herbalist from Somerset in the West Country of England, with a broad rural West Country accent and a rolled 'r'. A thin, cracked, creaky old voice, brisk and impatient, speeding up when she gets interested. Rude but kind. Broad Somerset, West Country accent. No reverb or effects.
```

Preview text:

```
Sit, child, and stop bleeding on my floor. Comfrey for the bruise, yarrow for the cut, and willow bark for the rest of you, and don't pull that face at me.
```

In the Voice Library instead: search for *Somerset (West Country)*, *female*, *70*, and listen for this: An old woman in her seventies, a village herbalist from Somerset in the West Country of England, with a broad rural West Country accent and a rolled 'r'. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.wenna.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice wenna
```

## Saying the names

The text to paste already respells these; keep the respelling: Grimtunnel as *Grim-tunnel*, Thornhollow as *Thorn-hollow*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Wenna

### 1. `dlg.wenna.first.0.wav`

*Where:* dialogue.json wenna/first#0
*Played:* brisk, rude, curious; doing: pegs a scholar; pace: brisk; volume: level.
*Note:* Rapid appraisal. Scornful on 'catalogue it'. 'What d'you want?' snappish.

```
[brisk, rude, curious] A Cloister lens, and a Cloister squint. Scholar? Then don't touch anything, you'll only want to catalogue it. I'm Wenna. What d'you want?
```
Subtitle: A Cloister lens, and a Cloister squint. Scholar? Then don't touch anything, you'll only want to catalogue it. I'm Wenna. What d'you want?

### 2. `dlg.wenna.first.1.wav`

*Where:* dialogue.json wenna/first#1
*Played:* irritable, brisk; doing: keeps you off her things; pace: quick; volume: raised.
*Note:* Snapping at your hands: 'Don't touch that. Or that. Or—' then resigned 'yes, that too.' Dry wit on 'a few that don't'.

```
[irritable, brisk, loudly] Don't touch that. Or that. Or— yes, that too. I'm Wenna. I make things that stop you dying, and a few that don't. What d'you want?
```
Subtitle: Don't touch that. Or that. Or— yes, that too. I'm Wenna. I make things that stop you dying, and a few that don't. What d'you want?

### 3. `dlg.wenna.hub.0.wav`

*Where:* dialogue.json wenna/hub#0
*Played:* triumphant delight; doing: the stream is clean; pace: quick; volume: raised.
*Note:* Bossy and flustered with joy. 'Clean.' repeated, softer, relieved.

```
[triumphant delight, loudly] You! Sit. No, don't sit, you'll squash the feverfew. The stream's clean, child. Clean.
```
Subtitle: You! Sit. No, don't sit, you'll squash the feverfew. The stream's clean, child. Clean.

### 4. `dlg.wenna.hub.1.wav`

*Where:* dialogue.json wenna/hub#1
*Played:* impatient; doing: busy; pace: brisk; volume: level.
*Note:* Snappish.

```
[impatient] Well? I've roots on the boil.
```
Subtitle: Well? I've roots on the boil.

### 5. `dlg.wenna.animals.0.wav`

*Where:* dialogue.json wenna/animals#0
*Played:* troubled, then businesslike; doing: the water's wrong; pace: measured; volume: level.
*Note:* 'Never.' emphatic. Tasting memory: metal, and smoke. Then brisk orders.

```
[troubled, then businesslike] The animals were never like this. Never. And the water's tasted wrong all year: metal, and smoke. Bring me some from the Thorn-hollow stream, above the blight if you can, below it if you must, and I'll tell you what's in it.
```
Subtitle: The animals were never like this. Never. And the water's tasted wrong all year: metal, and smoke. Bring me some from the Thornhollow stream, above the blight if you can, below it if you must, and I'll tell you what's in it.

### 6. `dlg.wenna.tamsays.0.wav`

*Where:* dialogue.json wenna/tamsays#0
*Played:* sharp, then uneasy; doing: takes Tam seriously; pace: measured; volume: level.
*Note:* Fond scorn for the boy, then sharp logic, speeding up: 'drank.' A pause; then quieter, admitting she's been afraid: 'telling myself I was old.'

```
[sharp, then uneasy] Tam. Course Tam saw it; nobody watches the ground like a boy with nothing to do. Drank and fell down. Not fought, not starved: drank. ...Bring me that water. A bottle, from where he saw them. I've been smelling metal in the well for a month and telling myself I was old.
```
Subtitle: Tam. Course Tam saw it; nobody watches the ground like a boy with nothing to do. Drank and fell down. Not fought, not starved: drank. ...Bring me that water. A bottle, from where he saw them. I've been smelling metal in the well for a month and telling myself I was old.

### 7. `dlg.wenna.analyse.0.wav`

*Where:* dialogue.json wenna/analyse#0
*Played:* absorbed, then alarmed; doing: identifies the poison; pace: quick; volume: level.
*Note:* Interrupts herself with interest, speeding up. 'Ember.' certain. Grim certainty on the last two sentences.

```
[absorbed, then alarmed] Green water, and— what's this? From a pipe? Ember. Ember slurry: the dust of the stones, cooked and watered down. Rots the belly of anything that drinks it. And nobody spills this much by accident. Someone upstream's getting rid of it.
```
Subtitle: Green water, and— what's this? From a pipe? Ember. Ember slurry: the dust of the stones, cooked and watered down. Rots the belly of anything that drinks it. And nobody spills this much by accident. Someone upstream's getting rid of it.

### 8. `dlg.wenna.analyse.1.wav`

*Where:* dialogue.json wenna/analyse#1
*Played:* absorbed, grim; doing: identifies the poison; pace: measured; volume: level.
*Note:* Three sense words, sniffing. Then lecturing, quick. Grim on 'Someone upstream's getting rid of it.'

```
[absorbed, grim] Green. Warm. Smells like a chapel lamp. Ember slurry, child: the dust of the stones, cooked and watered. Rots the belly of anything that drinks it. Nobody spills this much by accident. Someone upstream's getting rid of it.
```
Subtitle: Green. Warm. Smells like a chapel lamp. Ember slurry, child: the dust of the stones, cooked and watered. Rots the belly of anything that drinks it. Nobody spills this much by accident. Someone upstream's getting rid of it.

### 9. `dlg.wenna.analyse_arcana.0.wav`

*Where:* dialogue.json wenna/analyse_arcana#0
*Played:* approving, absorbed; doing: works it out with you; pace: quick; volume: level.
*Note:* Grudging approval; excited as the precipitate falls. The deduction rattled off.

```
[approving, absorbed] You know your salts. Yes, precipitate it, there, and— ember. Slurry, and fresh. Look at the grain: it's been through a pump. Nobody pumps ember but the lamplings, and the lamplings answer to Grim-tunnel.
```
Subtitle: You know your salts. Yes, precipitate it, there, and— ember. Slurry, and fresh. Look at the grain: it's been through a pump. Nobody pumps ember but the lamplings, and the lamplings answer to Grimtunnel.

### 10. `dlg.wenna.who.0.wav`

*Where:* dialogue.json wenna/who#0
*Played:* sharp, warning; doing: tells you who and how to stay safe; pace: brisk; volume: level.
*Note:* Rhetorical questions, sharp. Then the warning slower, motherly and fierce: 'Especially not if it's clear.'

```
[sharp, warning] Who digs? Who burns ember by the barrow-load? The lamplings. Find where it goes into the water and you'll find their pipe. Take an antidote or two, and don't drink anything out there. Not even if it's clear. Especially not if it's clear.
```
Subtitle: Who digs? Who burns ember by the barrow-load? The lamplings. Find where it goes into the water and you'll find their pipe. Take an antidote or two, and don't drink anything out there. Not even if it's clear. Especially not if it's clear.

### 11. `dlg.wenna.root.0.wav`

*Where:* dialogue.json wenna/root#0
*Played:* pleased, brisk; doing: takes the bitterroot; pace: brisk; volume: level.
*Note:* Gruff pleasure at fat roots.

```
[pleased, brisk] Good. Fat ones, too. Here. Come back with more; I'm always short.
```
Subtitle: Good. Fat ones, too. Here. Come back with more; I'm always short.

### 12. `dlg.wenna.mask.0.wav`

*Where:* dialogue.json wenna/mask#0
*Played:* proud, then rueful; doing: gives you the mask; pace: measured; volume: level.
*Note:* Pride in her work. 'Take it.' abrupt; 'I'm too old...' rueful, honest.

```
[proud, then rueful] My blightward. I made it the fever year. Stuff the beak with bitterroot and you can walk through air that'd drop a horse. You cleaned my stream, child. Take it. ...Something down there's still cooking, and I'm too old to go where it's needed.
```
Subtitle: My blightward. I made it the fever year. Stuff the beak with bitterroot and you can walk through air that'd drop a horse. You cleaned my stream, child. Take it. ...Something down there's still cooking, and I'm too old to go where it's needed.

### 13. `dlg.wenna.mask.1.wav`

*Where:* dialogue.json wenna/mask#1
*Played:* brisk, matter-of-fact; doing: gives you her plague mask; pace: measured; volume: level.
*Hides:* what the fever year cost her
*Note:* A herbwife's practical pride in the bitterroot. 'Take it.' an order. 'I'm too old to go where it's needed.' plain, no self-pity.

```
[brisk, matter-of-fact] My blightward. I made it the fever year. Stuff the beak with bitterroot and you can walk through air that'd drop a horse… Take it. I'm too old to go where it's needed.
```
Subtitle: My blightward. I made it the fever year. Stuff the beak with bitterroot and you can walk through air that'd drop a horse. Take it. I'm too old to go where it's needed.

### 14. `dlg.wenna.fever.0.wav`

*Where:* dialogue.json wenna/fever#0
*Played:* haunted, brusque; doing: remembers the fever year; pace: slow; volume: quiet.
*Wants:* not to remember
*Note:* The brisk voice drops. 'coughing green' vivid. 'Same smell exactly.' quiet, chilling. Then a hard change of subject: 'I've roots on the boil.'

```
[haunted, brusque, quietly] The year after Ashford went into the ground. Coughing green, then the sweats, then the— well. "Gone to the Morrow," they say up here, like it's a walk. They died, child. Same smell as your bottle. Same smell exactly. ...I've roots on the boil.
```
Subtitle: The year after Ashford went into the ground. Coughing green, then the sweats, then the— well. "Gone to the Morrow," they say up here, like it's a walk. They died, child. Same smell as your bottle. Same smell exactly. ...I've roots on the boil.

### 15. `dlg.wenna.cb_sold_dig.0.wav`

*Where:* dialogue.json wenna/cb_sold_dig#0
*Played:* disgusted, spiteful; doing: you sold out the stream; pace: measured; volume: level.
*Note:* Cold accounting. Hurt in 'I tested that water for you, child.' Then spite with relish: 'and I'll enjoy it.'

```
[disgusted, spiteful] You sold it. The stream, the Pack, all of it, to Pell, for forty. I tested that water for you, child. ...I'll still sell you an antidote. I'll charge you double, and I'll enjoy it.
```
Subtitle: You sold it. The stream, the Pack, all of it, to Pell, for forty. I tested that water for you, child. ...I'll still sell you an antidote. I'll charge you double, and I'll enjoy it.

### 16. `dlg.wenna.cb_broke_pump.0.wav`

*Where:* dialogue.json wenna/cb_broke_pump#0
*Played:* pleased, stubborn; doing: the pump is stopped; pace: brisk; volume: level.
*Note:* Sniffing. 'Don't argue; I can.' stubborn.

```
[pleased, stubborn] You stopped their pump. I can smell the difference already. Don't argue; I can.
```
Subtitle: You stopped their pump. I can smell the difference already. Don't argue; I can.

### 17. `dlg.wenna.cb_shrine_lit.0.wav`

*Where:* dialogue.json wenna/cb_shrine_lit#0
*Played:* dry amusement; doing: Chid's joy; pace: measured; volume: level.
*Note:* Fond scorn.

```
[dry amusement] Chid's lamp's lit. He came to tell me with his shoes on the wrong feet.
```
Subtitle: Chid's lamp's lit. He came to tell me with his shoes on the wrong feet.

### 18. `dlg.wenna.say_calling.0.wav`

*Where:* dialogue.json wenna/say_calling#0
*Played:* scolding; doing: your diet; pace: brisk; volume: level.
*Note:* Rapid scolding; 'I can see your gums' triumphant.

```
[scolding] Steel all over and not a scrap of sense in your diet. When did you last eat a green thing? Don't lie; I can see your gums.
```
Subtitle: Steel all over and not a scrap of sense in your diet. When did you last eat a green thing? Don't lie; I can see your gums.

### 19. `dlg.wenna.say_calling.1.wav`

*Where:* dialogue.json wenna/say_calling#1
*Played:* professional scorn, impatient; doing: your shoulder; pace: quick; volume: level.
*Note:* Interrupts herself; gives up: 'Fine. Limp, then.'

```
[professional scorn, impatient] You've had that shoulder put back by somebody who didn't know what they were doing. Twice. Sit, I'll— no, you won't sit. Fine. Limp, then.
```
Subtitle: You've had that shoulder put back by somebody who didn't know what they were doing. Twice. Sit, I'll— no, you won't sit. Fine. Limp, then.

### 20. `dlg.wenna.say_calling.2.wav`

*Where:* dialogue.json wenna/say_calling#2
*Played:* irritable; doing: no fire near the racks; pace: brisk; volume: level.
*Note:* Comic grievance about the funeral smell.

```
[irritable] Your hands smell of hot iron, child, and you've not been near a forge. I don't want to know. Comfrey, twice a day, and keep them off my drying racks.
```
Subtitle: Your hands smell of hot iron, child, and you've not been near a forge. I don't want to know. Comfrey, twice a day, and keep them off my drying racks.

### 21. `dlg.wenna.say_calling.3.wav`

*The same words are also* `dlg.wenna.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json wenna/say_calling#3
*Played:* bossy care; doing: feeds you; pace: brisk; volume: level.
*Note:* 'Don't ask what it is.' brisk.

```
[bossy care] You're the sort that eats standing up. It shows in the skin. Here. Chew this. Don't ask what it is.
```
Subtitle: You're the sort that eats standing up. It shows in the skin. Here. Chew this. Don't ask what it is.

### 22. `dlg.wenna.say_woman.0.wav`

*Where:* dialogue.json wenna/say_woman#0
*Played:* frank, kind; doing: a woman's medicine; pace: measured; volume: quiet.
*Note:* Low and matter-of-fact, woman to woman; dry about Chid.

```
[frank, kind, quietly] If you're ever carrying, child, there's a tea for keeping it and a tea for not. I don't ask which, and I don't tell Chid.
```
Subtitle: If you're ever carrying, child, there's a tea for keeping it and a tea for not. I don't ask which, and I don't tell Chid.

### 23. `dlg.wenna.t_wenna.0.wav`

*Where:* dialogue.json wenna/t_wenna#0
*Played:* wry, unsentimental; doing: her husbands; pace: measured; volume: level.
*Note:* A cackle in it. 'lost one at cards' deadpan. The last sentence comic grudge with real loss underneath.

```
[wry, unsentimental] Three husbands. Buried two, lost one at cards. The one I lost at cards was the best of them, and I've never forgiven the man who won him.
```
Subtitle: Three husbands. Buried two, lost one at cards. The one I lost at cards was the best of them, and I've never forgiven the man who won him.

### 24. `dlg.wenna.tallow.0.wav`

*Where:* dialogue.json wenna/tallow#0
*Played:* tart, dry; doing: her candles are honest; pace: measured; volume: level.
*Note:* Somerset bluntness. 'Fat was a pig.' as plain fact, a dry relish.

```
[tart, dry] I burn fat, child… Fat's honest. Fat was a pig.
```
Subtitle: I burn fat, child. Fat's honest. Fat was a pig.

## Said in passing

### 25. `bark.wenna.day.0.wav`

*Where:* npcs.json wenna.barks[0]
*Played:* irritable; pace: brisk; volume: level.

```
[irritable] Bitterroot, bitterroot. Always need more.
```
Subtitle: Bitterroot, bitterroot. Always need more.

### 26. `bark.wenna.night.0.wav`

*Where:* npcs.json wenna.nightBarks[0]
*Played:* tired, cross; pace: measured; volume: quiet.

```
[tired, cross, quietly] Moon's up. Good for picking. Bad for knees.
```
Subtitle: Moon's up. Good for picking. Bad for knees.

### 27. `bark.wenna.night.1.wav`

*Where:* npcs.json wenna.nightBarks[1]
*Played:* tired, cross; pace: measured; volume: quiet.

```
[tired, cross, quietly] Mind the nettles in the dark.
```
Subtitle: Mind the nettles in the dark.

### 28. `bark.wenna.night.2.wav`

*Where:* npcs.json wenna.nightBarks[2]
*Played:* tired, cross; pace: measured; volume: quiet.

```
[tired, cross, quietly] Night air's full of things. Some of them are herbs.
```
Subtitle: Night air's full of things. Some of them are herbs.

### 29. `bark.wenna.night.3.wav`

*Where:* npcs.json wenna.nightBarks[3]
*Played:* tired, cross; pace: measured; volume: quiet.

```
[tired, cross, quietly] Nightshade's out. So are the idiots.
```
Subtitle: Nightshade's out. So are the idiots.

### 30. `bark.wenna.said.0.wav`

*Where:* npcs.json wenna.said[0]
*Played:* uneasy; doing: the animals are wrong; pace: measured; volume: level.
*Note:* 'Never.' a herbwife's certainty.

```
[uneasy] The animals were never like this. Never.
```
Subtitle: The animals were never like this. Never.

### 31. `bark.wenna.said.1.wav`

*Where:* npcs.json wenna.said[1]
*Played:* suspicious; doing: the water; pace: measured; volume: level.
*Note:* Tart, sure of herself.

```
[suspicious] The water tastes wrong this year.
```
Subtitle: The water tastes wrong this year.

### 32. `bark.wenna.said.2.wav`

*Where:* npcs.json wenna.said[2]
*Played:* delighted; doing: the water is sweet again; pace: measured; volume: raised.
*Note:* 'Sweet!' a cackle of pleasure.

```
[delighted, loudly] Water's sweet again. I'd forgotten it could be.
```
Subtitle: Water's sweet again. I'd forgotten it could be.

### 33. `bark.wenna.said.3.wav`

*Where:* npcs.json wenna.said[3]
*Played:* bitter, dry; doing: clean water, no wolves; pace: slow; volume: level.
*Note:* Dry and sad.

```
[bitter, dry] Clean water, and nothing left in the wood to drink it.
```
Subtitle: Clean water, and nothing left in the wood to drink it.

### 34. `bark.wenna.said.4.wav`

*Where:* npcs.json wenna.said[4]

```
Hot stone on you, child. Last I smelled that was the fever year.
```
Subtitle: Hot stone on you, child. Last I smelled that was the fever year.


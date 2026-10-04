# Rav Cutwell: ElevenLabs packet

Voice id in the game: `rav`. 52 takes to record (5,351 characters; about 16,053 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Rav Cutwell** (the Crooked Flagon). Gravel and cant; a doctor's frankness about bodies ("drop your trousers or don't"); a half-drunk music in the rhythm; "pal". Funny about everything except his brother, whom he never names (once: "Dunstan", the day he hears Redcowl is dead). Never sentimental, never says no to a drink (once: "No. ...No, I'll keep this one.", the morning after his night with the survivor, `rav.sober`, Act 2). No oaths from anyone's scripture: when something is unbearable he reaches for his mother ("Oh, Mam."), as his brother does. *Casting:* 50s, Glaswegian, wry; the bedside calm under the cant.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Rav Cutwell`. Never describe a voice as sounding like a real person.

```
Native English (British, Glaswegian). Male, 50s. Studio quality. Persona: a Glasgow tavern doctor. A fifty-four-year-old tavern doctor from Glasgow in Scotland, with a gravelly, wry baritone and a strong Glaswegian Scottish accent. Half-drunk music in his rhythm, funny and frank, with a calm bedside steadiness underneath. Broad Glaswegian accent. No reverb or effects.
```

Preview text:

```
Sit down, pal, and drop your trousers or don't. I've seen worse, and I've sewn worse, and I've drunk to forget the both of them.
```

In the Voice Library instead: search for *Glaswegian*, *male*, *50*, and listen for this: A fifty-four-year-old tavern doctor from Glasgow in Scotland, with a gravelly, wry baritone and a strong Glaswegian Scottish accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.rav.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice rav
```

## Saying the names

The text to paste already respells these; keep the respelling: McBreathless as *Mac-Breathless*, Redcowl as *Red-cowl*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Rav

### 1. `dlg.rav.first.0.wav`

*Where:* dialogue.json rav/first#0
*Played:* wry delight; doing: recognises a fellow outlaw; pace: measured; volume: level.
*Wants:* a drinking companion
*Note:* Half-drunk music. 'Well, well.' amused. The parrot joke dry. Three names, each funnier; 'McBreathless' with relish.

```
[wry delight] Well, well. Somebody who knows how to wear a kerchief without looking like a parrot. Sit. I'm Rav Cutwell. Doctor Cutwell, if you're bleeding. Doctor Mac-Breathless, if you're the Watch.
```
Subtitle: Well, well. Somebody who knows how to wear a kerchief without looking like a parrot. Sit. I'm Rav Cutwell. Doctor Cutwell, if you're bleeding. Doctor McBreathless, if you're the Watch.

### 2. `dlg.rav.first.1.wav`

*Where:* dialogue.json rav/first#1
*Played:* amused warning; doing: a Kerchief colour in daylight; pace: measured; volume: level.
*Note:* Dry amusement; 'Sit, before Holloway sees you.' low and quick.

```
[amused warning] Red cloth, walking into my tavern in daylight. Brave, or somebody gave it you for a joke. Rav. Sit, before Holloway sees you.
```
Subtitle: Red cloth, walking into my tavern in daylight. Brave, or somebody gave it you for a joke. Rav. Sit, before Holloway sees you.

### 3. `dlg.rav.first.2.wav`

*Where:* dialogue.json rav/first#2
*Played:* grumpy, then wry; doing: introduces himself; pace: measured; volume: level.
*Note:* Grumbling 'You're in my light.' Pause. Gives up: 'Oh, sit, then.' Self-mocking résumé. 'Ask me which paid better.' a wink.

```
[grumpy, then wry] You're in my light. ...Oh, sit, then. Rav. I was a doctor, then I was a Kerchief, and now I'm a doctor who drinks here. Ask me which paid better.
```
Subtitle: You're in my light. ...Oh, sit, then. Rav. I was a doctor, then I was a Kerchief, and now I'm a doctor who drinks here. Ask me which paid better.

### 4. `dlg.rav.hub.0.wav`

*Where:* dialogue.json rav/hub#0
*Played:* warm, easy; doing: a friend; pace: measured; volume: level.
*Note:* 'Pal.' warm.

```
[warm, easy] Pal. Pull up a stool.
```
Subtitle: Pal. Pull up a stool.

### 5. `dlg.rav.hub.1.wav`

*Where:* dialogue.json rav/hub#1
*Played:* wry, bawdy; doing: night at the Flagon; pace: measured; volume: level.
*Note:* Dry jokes; 'I checked.' deadpan. The Sella line bawdy and fond.

```
[wry, bawdy] Night surgery's double. Night drinking's the same price; I checked. And if you're here for Sella, she's busy: you can hear the bed from the cellar.
```
Subtitle: Night surgery's double. Night drinking's the same price; I checked. And if you're here for Sella, she's busy: you can hear the bed from the cellar.

### 6. `dlg.rav.hub.2.wav`

*Where:* dialogue.json rav/hub#2
*Played:* wry; doing: what'll it be; pace: measured; volume: level.
*Note:* 'and worth it' dry.

```
[wry] What'll it be? Advice is free, and worth it.
```
Subtitle: What'll it be? Advice is free, and worth it.

### 7. `dlg.rav.kerchiefs.0.wav`

*Where:* dialogue.json rav/kerchiefs#0
*Played:* wry, knowing; doing: explains the Kerchiefs; pace: measured; volume: level.
*Note:* A man describing family without saying so. Practical advice with gallows humour at the end.

```
[wry, knowing] Red-cowl runs them. He'd rather talk than bleed, and he'd rather you bled than he talked. Their camp's in the ravine off the Old Road: the Roost. Wear red, walk slow, keep your hands empty, and you might get to say hello before they shoot you.
```
Subtitle: Redcowl runs them. He'd rather talk than bleed, and he'd rather you bled than he talked. Their camp's in the ravine off the Old Road: the Roost. Wear red, walk slow, keep your hands empty, and you might get to say hello before they shoot you.

### 8. `dlg.rav.clerk.0.wav`

*Where:* dialogue.json rav/clerk#0
*Played:* conspiratorial, then uneasy; doing: tells you about Jessop; pace: measured; volume: quiet.
*Note:* Pub gossip, then 'Between us' lower. Fond scorn: 'like a boy with a frog'. A pause; uneasy: 'Not seen him since.'

```
[conspiratorial, then uneasy, quietly] A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. Jessop, his name is; Vonnra's. He'd "done somebody a favour": told Coyle's teamsters the road was shut and sent them down the forest track. Between us, he'd also a key he shouldn't have. Pell's warehouse. Showed it me like a boy with a frog. ...Not seen him since. He wasn't the type to buy rounds, either.
```
Subtitle: A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. Jessop, his name is; Vonnra's. He'd "done somebody a favour": told Coyle's teamsters the road was shut and sent them down the forest track. Between us, he'd also a key he shouldn't have. Pell's warehouse. Showed it me like a boy with a frog. ...Not seen him since. He wasn't the type to buy rounds, either.

### 9. `dlg.rav.clerk.1.wav`

*Where:* dialogue.json rav/clerk#1
*Played:* conspiratorial, then uneasy; doing: tells you about Jessop; pace: measured; volume: quiet.
*Note:* Pub gossip. 'Draw your own lines, pal.' A pause; slow realisation on 'now I think of it.'

```
[conspiratorial, then uneasy, quietly] A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. Jessop, his name is; Vonnra's. He'd "done somebody a favour": told Coyle's teamsters the road was shut and sent them down the forest track. Draw your own lines, pal. ...Not seen him since, now I think of it.
```
Subtitle: A toll clerk bought the room a round the night the caravan vanished. Clerks don't buy rounds. Jessop, his name is; Vonnra's. He'd "done somebody a favour": told Coyle's teamsters the road was shut and sent them down the forest track. Draw your own lines, pal. ...Not seen him since, now I think of it.

### 10. `dlg.rav.fence.0.wav`

*Where:* dialogue.json rav/fence#0
*Played:* amused, worldly; doing: offers to fence the box; pace: measured; volume: quiet.
*Note:* 'Oh, dear.' amused. Business. The last sentence a grim little truth.

```
[amused, worldly, quietly] Coyle's strongbox. Oh, dear. Aye, I know a man. A hundred and fifty, and nobody asks where it came from. At first. People always find out in the end; it's the only law in this valley that gets kept.
```
Subtitle: Coyle's strongbox. Oh, dear. Aye, I know a man. A hundred and fifty, and nobody asks where it came from. At first. People always find out in the end; it's the only law in this valley that gets kept.

### 11. `dlg.rav.roost.0.wav`

*Where:* dialogue.json rav/roost#0
*Played:* conspiratorial, wry; doing: your way into the Roost; pace: measured; volume: quiet.
*Note:* Instructions with relish. The password quoted with a grin. 'I was never here.' deadpan.

```
[conspiratorial, wry, quietly] Alive, and talking? Wear this, walk in the front, and say "Red-cowl owes Rav a leg." He'll laugh. If he laughs, you're in. If he doesn't laugh, I was never here.
```
Subtitle: Alive, and talking? Wear this, walk in the front, and say "Redcowl owes Rav a leg." He'll laugh. If he laughs, you're in. If he doesn't laugh, I was never here.

### 12. `dlg.rav.redcowl.0.wav`

*Where:* dialogue.json rav/redcowl#0
*Played:* fond grievance, then closing; doing: knows Redcowl; pace: measured; volume: level.
*Note:* A pub story about the leg, laughing at himself. A pause; the door shuts: 'Don't ask me the rest.' gentle but final.

```
[fond grievance, then closing] Know him? I sewed his leg back on with a sail-needle and a bottle of something blue, and he's never once said thank you. That's the leg he owes me. ...Don't ask me the rest. I'm a doctor; I don't do family histories.
```
Subtitle: Know him? I sewed his leg back on with a sail-needle and a bottle of something blue, and he's never once said thank you. That's the leg he owes me. ...Don't ask me the rest. I'm a doctor; I don't do family histories.

### 13. `dlg.rav.cb_tricked_redcowl.0.wav`

*Where:* dialogue.json rav/cb_tricked_redcowl#0
*Played:* gleeful delight; doing: you made Redcowl run; pace: quick; volume: raised.
*Note:* 'RAN' stressed with joy. Laughing. Buying the round.

```
[gleeful delight, loudly] You told Red-cowl the Watch was coming, and he RAN. I've waited my whole life to see that man run. Sit. This one's on me, and so's the next.
```
Subtitle: You told Redcowl the Watch was coming, and he RAN. I've waited my whole life to see that man run. Sit. This one's on me, and so's the next.

### 14. `dlg.rav.cb_killed_redcowl.0.p1.wav`

*Where:* dialogue.json rav/cb_killed_redcowl#0; part 2 of 4: narrator: He doesn't look up. / **rav: You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated…** / narrator: He drinks. / rav: No. He'd have said it was the job. It was always the job, with him. Get out of my light fo…
*Played:* grief, held with a drink; doing: his brother is dead; pace: slow; volume: quiet.
*Wants:* to be left alone
*Note:* Narrator: he doesn't look up. 'You killed him.' flat. Pause. 'Dunstan.' the one time he says it; barely there. Mother's idea, a wet laugh. Narrator: he drinks. Then defending his brother. 'I'll be a doctor again tomorrow.' trying to be wry, failing.

```
[grief, held with a drink, quietly] You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated it.
```
Subtitle: You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated it.

### 15. `dlg.rav.cb_killed_redcowl.0.p3.wav`

*Where:* dialogue.json rav/cb_killed_redcowl#0; part 4 of 4: narrator: He doesn't look up. / rav: You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated… / narrator: He drinks. / **rav: No. He'd have said it was the job. It was always the job, with him. Get out of my light fo…**
*Played:* grief, held with a drink; doing: his brother is dead; pace: slow; volume: quiet.
*Wants:* to be left alone
*Note:* Narrator: he doesn't look up. 'You killed him.' flat. Pause. 'Dunstan.' the one time he says it; barely there. Mother's idea, a wet laugh. Narrator: he drinks. Then defending his brother. 'I'll be a doctor again tomorrow.' trying to be wry, failing.

```
[grief, held with a drink, quietly] No. He'd have said it was the job. It was always the job, with him. Get out of my light for a bit, pal. Come back tomorrow. I'll be a doctor again tomorrow.
```
Subtitle: No. He'd have said it was the job. It was always the job, with him. Get out of my light for a bit, pal. Come back tomorrow. I'll be a doctor again tomorrow.

### 16. `dlg.rav.cb_burned_roost.0.wav`

*Where:* dialogue.json rav/cb_burned_roost#0
*Played:* dread, then bitter; doing: the Roost burned; pace: slow; volume: quiet.
*Note:* Reporting. Pause. Convincing himself: 'He'll have got out. He always gets out.' Then bitter and quiet: 'The ones in the cages didn't.'

```
[dread, then bitter, quietly] The Roost burned. With the cages full, they're saying. ...He'll have got out. He always gets out. The ones in the cages didn't.
```
Subtitle: The Roost burned. With the cages full, they're saying. ...He'll have got out. He always gets out. The ones in the cages didn't.

### 17. `dlg.rav.cb_exposed_pell.0.wav`

*Where:* dialogue.json rav/cb_exposed_pell#0
*Played:* merry; doing: Pell in irons; pace: quick; volume: raised.
*Note:* Toast. Self-mocking joke.

```
[merry, loudly] Pell in irons! I'll drink to that. I'll drink to anything, but I'll drink to that twice.
```
Subtitle: Pell in irons! I'll drink to that. I'll drink to anything, but I'll drink to that twice.

### 18. `dlg.rav.say_calling.0.wav`

*Where:* dialogue.json rav/say_calling#0
*Played:* clinical wit; doing: reads your body; pace: measured; volume: level.
*Note:* A doctor's eye; dry advice about Holloway.

```
[clinical wit] Shield arm's longer than the other. Comes of holding a door shut. Holloway'd love you, pal; don't let him.
```
Subtitle: Shield arm's longer than the other. Comes of holding a door shut. Holloway'd love you, pal; don't let him.

### 19. `dlg.rav.say_calling.1.wav`

*Where:* dialogue.json rav/say_calling#1
*Played:* clinical wit; doing: reads your knuckles; pace: measured; volume: level.
*Note:* Deadpan.

```
[clinical wit] You've broken a few noses. Your knuckles are a medical history.
```
Subtitle: You've broken a few noses. Your knuckles are a medical history.

### 20. `dlg.rav.say_calling.2.wav`

*Where:* dialogue.json rav/say_calling#2
*Played:* clinical wit; doing: reads your fingertips; pace: measured; volume: level.
*Note:* 'but you won't.' dry.

```
[clinical wit] Spell-scorched fingertips. You'll want goose fat for that. And to stop doing it, but you won't.
```
Subtitle: Spell-scorched fingertips. You'll want goose fat for that. And to stop doing it, but you won't.

### 21. `dlg.rav.say_calling.3.wav`

*The same words are also* `dlg.rav.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json rav/say_calling#3
*Played:* sharp, curious; doing: spots an old habit; pace: measured; volume: quiet.
*Note:* Suddenly sober and interested: 'Who taught you?'

```
[sharp, curious, quietly] You counted the doors when you sat down. Old Kerchief habit. Who taught you?
```
Subtitle: You counted the doors when you sat down. Old Kerchief habit. Who taught you?

### 22. `dlg.rav.say_sella.0.wav`

*Where:* dialogue.json rav/say_sella#0
*Played:* conspiratorial; doing: a tip; pace: measured; volume: quiet.
*Note:* 'Notice.' a wink.

```
[conspiratorial, quietly] A word to the wise: Sella charges ladies the gentleman's rate, to see if they'll notice. Notice.
```
Subtitle: A word to the wise: Sella charges ladies the gentleman's rate, to see if they'll notice. Notice.

### 23. `dlg.rav.say_sella.1.wav`

*Where:* dialogue.json rav/say_sella#1
*Played:* bawdy, dry; doing: a joke about Sella; pace: measured; volume: quiet.
*Note:* 'She just says it slower.' deadpan.

```
[bawdy, dry, quietly] A word to the wise: Sella's charging the gentleman's rate this week. It's the same as the lady's rate. She just says it slower.
```
Subtitle: A word to the wise: Sella's charging the gentleman's rate this week. It's the same as the lady's rate. She just says it slower.

### 24. `dlg.rav.t_rav.0.wav`

*Where:* dialogue.json rav/t_rav#0
*Played:* wry, rueful; doing: why he left; pace: measured; volume: level.
*Note:* A list growing worse; the teeth man grotesque and funny. 'and I have a fifth.' resigned.

```
[wry, rueful] Every night, round the fourth cup. Then I remember the latrines, and the lice, and the man who sharpened his teeth for a joke and then couldn't stop, and I have a fifth.
```
Subtitle: Every night, round the fourth cup. Then I remember the latrines, and the lice, and the man who sharpened his teeth for a joke and then couldn't stop, and I have a fifth.

### 25. `dlg.rav.pain.0.wav`

*Where:* dialogue.json rav/pain#0
*Played:* flirtatious, wry; doing: a doctor's offer; pace: measured; volume: quiet.
*Note:* Mock propriety. 'Largely professionally.' a twinkle. The anaesthetic joke dry.

```
[flirtatious, wry, quietly] Where? ...No, don't point, pal, we're in company. Come round the back after closing and I'll take a look. Largely professionally. Bring a bottle; it's an anaesthetic for one of us.
```
Subtitle: Where? ...No, don't point, pal, we're in company. Come round the back after closing and I'll take a look. Largely professionally. Bring a bottle; it's an anaesthetic for one of us.

### 26. `dlg.rav.leg_held.0.p1.wav`

*Where:* dialogue.json rav/leg_held#0; part 2 of 4: narrator: He puts the cup down, very carefully, as if it were full. / **rav: ...Did he.** / narrator: A long time. / rav: Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow.
*Played:* grief held with care; doing: his brother's last words; pace: slow; volume: quiet.
*Note:* Narrator: the cup set down. '...Did he.' A long time. Professional pride as armour: 'I'm a good doctor.' cracking. Kind dismissal.

```
[grief held with care, quietly] ...Did he.
```
Subtitle: ...Did he.

### 27. `dlg.rav.leg_held.0.p3.wav`

*Where:* dialogue.json rav/leg_held#0; part 4 of 4: narrator: He puts the cup down, very carefully, as if it were full. / rav: ...Did he. / narrator: A long time. / **rav: Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow.**
*Played:* grief held with care; doing: his brother's last words; pace: slow; volume: quiet.
*Note:* Narrator: the cup set down. '...Did he.' A long time. Professional pride as armour: 'I'm a good doctor.' cracking. Kind dismissal.

```
[grief held with care, quietly] Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow.
```
Subtitle: Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow.

### 28. `dlg.rav.back_room_look.0.p0.wav`

*Where:* dialogue.json rav/back_room_look#0; part 1 of 7: **rav: You came.** / narrator: He looks faintly alarmed about it. / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / rav: You're cold, pal. Cold as a cellar step. / narrator: He frowns at your wrist, then lets it go. / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* flirty, then troubled; doing: he examines you; pace: measured; volume: quiet.
*Note:* Alarmed 'You came.' Doctor's orders, joking. Narrator through the exam. 'Cold as a cellar step.' quiet and worried. The last lines a joke covering real alarm.

```
[flirty, then troubled, quietly] You came.
```
Subtitle: You came.

### 29. `dlg.rav.back_room_look.0.p2.wav`

*Where:* dialogue.json rav/back_room_look#0; part 3 of 7: rav: You came. / narrator: He looks faintly alarmed about it. / **rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical.** / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / rav: You're cold, pal. Cold as a cellar step. / narrator: He frowns at your wrist, then lets it go. / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* flirty, then troubled; doing: he examines you; pace: measured; volume: quiet.
*Note:* Alarmed 'You came.' Doctor's orders, joking. Narrator through the exam. 'Cold as a cellar step.' quiet and worried. The last lines a joke covering real alarm.

```
[flirty, then troubled, quietly] Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical.
```
Subtitle: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical.

### 30. `dlg.rav.back_room_look.0.p4.wav`

*Where:* dialogue.json rav/back_room_look#0; part 5 of 7: rav: You came. / narrator: He looks faintly alarmed about it. / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / **rav: You're cold, pal. Cold as a cellar step.** / narrator: He frowns at your wrist, then lets it go. / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* flirty, then troubled; doing: he examines you; pace: measured; volume: quiet.
*Note:* Alarmed 'You came.' Doctor's orders, joking. Narrator through the exam. 'Cold as a cellar step.' quiet and worried. The last lines a joke covering real alarm.

```
[flirty, then troubled, quietly] You're cold, pal. Cold as a cellar step.
```
Subtitle: You're cold, pal. Cold as a cellar step.

### 31. `dlg.rav.back_room_look.0.p6.wav`

*Where:* dialogue.json rav/back_room_look#0; part 7 of 7: rav: You came. / narrator: He looks faintly alarmed about it. / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / rav: You're cold, pal. Cold as a cellar step. / narrator: He frowns at your wrist, then lets it go. / **rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…**
*Played:* flirty, then troubled; doing: he examines you; pace: measured; volume: quiet.
*Note:* Alarmed 'You came.' Doctor's orders, joking. Narrator through the exam. 'Cold as a cellar step.' quiet and worried. The last lines a joke covering real alarm.

```
[flirty, then troubled, quietly] ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong with them. Have a drink, before I find something.
```
Subtitle: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong with them. Have a drink, before I find something.

### 32. `dlg.rav.back_room_drink.0.p0.wav`

*Where:* dialogue.json rav/back_room_drink#0; part 1 of 3: **rav: For one of us.** / narrator: He drinks his, then looks at yours. / rav: Both of us, evidently. ...Go home, pal. You've got a job up the Old Road, and I've got a b…
*Played:* rueful, fond; doing: sends you home; pace: measured; volume: quiet.
*Note:* Dry about the cups. The last sentence a soft confession.

```
[rueful, fond, quietly] For one of us.
```
Subtitle: For one of us.

### 33. `dlg.rav.back_room_drink.0.p2.wav`

*Where:* dialogue.json rav/back_room_drink#0; part 3 of 3: rav: For one of us. / narrator: He drinks his, then looks at yours. / **rav: Both of us, evidently. ...Go home, pal. You've got a job up the Old Road, and I've got a b…**
*Played:* rueful, fond; doing: sends you home; pace: measured; volume: quiet.
*Note:* Dry about the cups. The last sentence a soft confession.

```
[rueful, fond, quietly] Both of us, evidently. ...Go home, pal. You've got a job up the Old Road, and I've got a bad habit of liking folk who've jobs up the Old Road.
```
Subtitle: Both of us, evidently. ...Go home, pal. You've got a job up the Old Road, and I've got a bad habit of liking folk who've jobs up the Old Road.

### 34. `dlg.rav.back_room_kiss.0.p1.wav`

*Where:* dialogue.json rav/back_room_kiss#0; part 2 of 4: narrator: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. … / **rav: Not yet, pal. Not three cups down, and not while you're still needing things off me: keys,…** / narrator: He picks up his cup. / rav: Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's t…
*Played:* tender, careful; doing: not yet; pace: slow; volume: quiet.
*Note:* Narrator through the kiss and the hand. 'Not yet, pal.' gentle. His reasons plain. 'I'm always here.' rueful; the worrying part dry.

```
[tender, careful, quietly] Not yet, pal. Not three cups down, and not while you're still needing things off me: keys, ways in, who's who up the Old Road.
```
Subtitle: Not yet, pal. Not three cups down, and not while you're still needing things off me: keys, ways in, who's who up the Old Road.

### 35. `dlg.rav.back_room_kiss.0.p3.wav`

*Where:* dialogue.json rav/back_room_kiss#0; part 4 of 4: narrator: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. … / rav: Not yet, pal. Not three cups down, and not while you're still needing things off me: keys,… / narrator: He picks up his cup. / **rav: Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's t…**
*Played:* tender, careful; doing: not yet; pace: slow; volume: quiet.
*Note:* Narrator through the kiss and the hand. 'Not yet, pal.' gentle. His reasons plain. 'I'm always here.' rueful; the worrying part dry.

```
[tender, careful, quietly] Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's the other worrying part.
```
Subtitle: Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's the other worrying part.

### 36. `dlg.rav.back_room_end.0.p0.wav`

*Where:* dialogue.json rav/back_room_end#0; part 1 of 3: **rav: "Doctor."** / narrator: He snorts. / rav: Get out of my surgery.
*Played:* mock-offended, fond; doing: shoos you out; pace: measured; volume: level.
*Note:* Narrator: the snort. Grumbling affection.

```
[mock-offended, fond] "Doctor."
```
Subtitle: "Doctor."

### 37. `dlg.rav.back_room_end.0.p2.wav`

*Where:* dialogue.json rav/back_room_end#0; part 3 of 3: rav: "Doctor." / narrator: He snorts. / **rav: Get out of my surgery.**
*Played:* mock-offended, fond; doing: shoos you out; pace: measured; volume: level.
*Note:* Narrator: the snort. Grumbling affection.

```
[mock-offended, fond] Get out of my surgery.
```
Subtitle: Get out of my surgery.

### 38. `dlg.rav.came_back.0.p1.wav`

*Where:* dialogue.json rav/came_back#0; part 2 of 4: narrator: He's at his table. He's sober, or near it. He's shaved. / **rav: You came back.** / narrator: He looks at you for a long time. / rav: Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. .…
*Played:* sober, raw, steady; doing: you came back after Dunstan; pace: slow; volume: quiet.
*Note:* Narrator: sober, shaved. 'You came back.' Long look. Dry about Rook's. Then plain: no talk of it. 'I'm a doctor today.' steadying himself.

```
[sober, raw, steady, quietly] You came back.
```
Subtitle: You came back.

### 39. `dlg.rav.came_back.0.p3.wav`

*Where:* dialogue.json rav/came_back#0; part 4 of 4: narrator: He's at his table. He's sober, or near it. He's shaved. / rav: You came back. / narrator: He looks at you for a long time. / **rav: Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. .…**
*Played:* sober, raw, steady; doing: you came back after Dunstan; pace: slow; volume: quiet.
*Note:* Narrator: sober, shaved. 'You came back.' Long look. Dry about Rook's. Then plain: no talk of it. 'I'm a doctor today.' steadying himself.

```
[sober, raw, steady, quietly] Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. ...Sit. I'll not talk about it if you don't. I'm a doctor today. What's wrong with you?
```
Subtitle: Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. ...Sit. I'll not talk about it if you don't. I'm a doctor today. What's wrong with you?

### 40. `dlg.rav.came_back_sit.0.wav`

*Where:* dialogue.json rav/came_back_sit#0
*Played:* gruff acceptance; doing: sit; pace: slow; volume: quiet.
*Note:* Narrator: the breath. 'Aye. Well.'

```
[gruff acceptance, quietly] [a breath out through his nose] Aye. Well. Sit, then.
```
Subtitle: Aye. Well. Sit, then.

### 41. `dlg.rav.came_back_sorry.0.wav`

*Where:* dialogue.json rav/came_back_sorry#0
*Played:* grief, firm; doing: don't apologise; pace: slow; volume: quiet.
*Note:* Firm and kind. 'I'll not be able to hear it twice.' near breaking.

```
[grief, firm, quietly] No. You're not, and you shouldn't be; he'd have said it was the job. Don't say it again, pal. I'll not be able to hear it twice.
```
Subtitle: No. You're not, and you shouldn't be; he'd have said it was the job. Don't say it again, pal. I'll not be able to hear it twice.

## Said in passing

### 42. `bark.rav.day.0.wav`

*Where:* npcs.json rav.barks[0]
*Played:* wry; pace: measured; volume: level.

```
[wry] I'm a doctor. Don't make me prove it.
```
Subtitle: I'm a doctor. Don't make me prove it.

### 43. `bark.rav.day.1.wav`

*Where:* npcs.json rav.barks[1]
*Played:* wry; pace: measured; volume: level.

```
[wry] Red cloth's a hard habit to break.
```
Subtitle: Red cloth's a hard habit to break.

### 44. `bark.rav.day.2.wav`

*Where:* npcs.json rav.barks[2]
*Played:* wry; pace: measured; volume: level.

```
[wry] Buy me a drink and I'll tell you a lie worth hearing.
```
Subtitle: Buy me a drink and I'll tell you a lie worth hearing.

### 45. `bark.rav.day.3.wav`

*Where:* npcs.json rav.barks[3]
*Played:* wry; pace: measured; volume: level.

```
[wry] Drop your trousers or don't. The leeches aren't fussy.
```
Subtitle: Drop your trousers or don't. The leeches aren't fussy.

### 46. `bark.rav.day.4.wav`

*Where:* npcs.json rav.barks[4]
*Played:* wry; pace: measured; volume: level.

```
[wry] Half my patients die. The other half pay.
```
Subtitle: Half my patients die. The other half pay.

### 47. `bark.rav.day.5.wav`

*Where:* npcs.json rav.barks[5]
*Played:* wry; pace: measured; volume: level.

```
[wry] Pox, piles, a pike-wound or a broken heart: I've a cure for three of them and a drink for the fourth.
```
Subtitle: Pox, piles, a pike-wound or a broken heart: I've a cure for three of them and a drink for the fourth.

### 48. `bark.rav.night.0.wav`

*Where:* npcs.json rav.nightBarks[0]
*Played:* merry; pace: measured; volume: level.

```
[merry] Night surgery's double. Night anything's double.
```
Subtitle: Night surgery's double. Night anything's double.

### 49. `bark.rav.night.1.wav`

*Where:* npcs.json rav.nightBarks[1]
*Played:* merry; pace: measured; volume: level.

```
[merry] The best stories come after the third cup.
```
Subtitle: The best stories come after the third cup.

### 50. `bark.rav.night.2.wav`

*Where:* npcs.json rav.nightBarks[2]
*Played:* merry; pace: measured; volume: level.

```
[merry] Pull up a stool. Mind the blood.
```
Subtitle: Pull up a stool. Mind the blood.

### 51. `bark.rav.night.3.wav`

*Where:* npcs.json rav.nightBarks[3]
*Played:* merry; pace: measured; volume: level.

```
[merry] Last orders were an hour ago. I'm the only one who heard them.
```
Subtitle: Last orders were an hour ago. I'm the only one who heard them.

### 52. `bark.rav.said.0.wav`

*Where:* npcs.json rav.said[0]
*Played:* grief, sudden; doing: his mother; pace: slow; volume: quiet.
*Note:* Two words escaping him; barely voiced.

```
[grief, sudden, quietly] Man owed me a leg, pal. Bad debt, now.
```
Subtitle: Man owed me a leg, pal. Bad debt, now.


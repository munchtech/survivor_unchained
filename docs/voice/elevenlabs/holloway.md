# Captain Holloway: ElevenLabs packet

Voice id in the game: `holloway`. 64 takes to record (7,712 characters; about 23,136 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Captain Holloway** (the Watch). A quartermaster who was made a captain: numbers, lists, what things cost ("eleven men, four can hold a spear the right way round"). Clipped, tired, contractions, anger held one notch below the surface. Says "proof", never "evidence". Never says sorry; the nearest he gets is paying for something. Goes very quiet whenever Ashford or Maeca comes up. *Casting:* 45, Lancashire flattened by the army; hoarse from shouting.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Captain Holloway`. Never describe a voice as sounding like a real person.

```
Native English (British, Lancashire). Male, 40s. Studio quality. Persona: a tired northern English army captain. A tired forty-five-year-old soldier from Lancashire in the north of England, an army quartermaster made captain. A hoarse, worn baritone, rough from years of shouting orders, with a flat northern English accent. Clipped and weary, anger held just below the surface. Thick Lancashire accent. No reverb or effects.
```

Preview text:

```
Eleven men, and four of them can hold a spear the right way round. I've a wall to keep, a road to keep, and a town that thinks both keep themselves.
```

In the Voice Library instead: search for *Lancashire, flattened by the army*, *male*, *40*, and listen for this: A tired forty-five-year-old soldier from Lancashire in the north of England, an army quartermaster made captain. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.holloway.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice holloway
```

## Saying the names

The text to paste already respells these; keep the respelling: Greymuzzle as *Grey-muzzle*, Maeca as *Mayka*, Redcowl as *Red-cowl*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Holloway

### 1. `dlg.holloway.first.0.wav`

*Where:* dialogue.json holloway/first#0
*Played:* hostile, contemptuous; doing: warns a Kerchief-looking stranger off; pace: measured; volume: level.
*Wants:* the red rag off you
*Note:* Hard and clipped. Threat flat, not shouted. Name and rank at the end tired and bitter: 'what's left of'.

```
[hostile, contemptuous] You came up the Low Ford road in Kerchief red. Either you're one of them or you're a fool, and I've no room in the cells for either. Take that rag off in my town, or I'll take it off you. Holloway. Captain of what's left of the Watch.
```
Subtitle: You came up the Low Ford road in Kerchief red. Either you're one of them or you're a fool, and I've no room in the cells for either. Take that rag off in my town, or I'll take it off you. Holloway. Captain of what's left of the Watch.

### 2. `dlg.holloway.first.1.wav`

*Where:* dialogue.json holloway/first#1
*Played:* grudging respect, weary; doing: acknowledges the Warden's death; pace: measured; volume: level.
*Wants:* you useful and not trouble
*Note:* Grudging. 'I'd thank you, but...' dry and tired. Name and rank flat.

```
[grudging respect, weary] You're the one who put the Ford-Warden down. The Watch kept those lamps, once. I'd thank you, but thanks don't feed eleven men. Holloway. Captain of what's left of the Watch.
```
Subtitle: You're the one who put the Ford-Warden down. The Watch kept those lamps, once. I'd thank you, but thanks don't feed eleven men. Holloway. Captain of what's left of the Watch.

### 3. `dlg.holloway.first.2.wav`

*Where:* dialogue.json holloway/first#2
*Played:* wary, tired; doing: sizes up a stranger; pace: measured; volume: level.
*Wants:* no trouble in his town
*Note:* 'At night.' its own suspicious beat. Clipped and hoarse.

```
[wary, tired] You came up the Low Ford road. At night. Either you're very good or very lucky, and I've no use for either kind of trouble in my town. Holloway. Captain of the Watch.
```
Subtitle: You came up the Low Ford road. At night. Either you're very good or very lucky, and I've no use for either kind of trouble in my town. Holloway. Captain of the Watch.

### 4. `dlg.holloway.hub.0.wav`

*Where:* dialogue.json holloway/hub#0
*Played:* grudging, rueful; doing: admits he was wrong; pace: measured; volume: quiet.
*Note:* An effort to say. 'Don't tell anyone I said so.' gruff, nearly a smile.

```
[grudging, rueful, quietly] The water's clean and the wolves are back in the deep wood. I was wrong about them. Don't tell anyone I said so.
```
Subtitle: The water's clean and the wolves are back in the deep wood. I was wrong about them. Don't tell anyone I said so.

### 5. `dlg.holloway.hub.1.wav`

*Where:* dialogue.json holloway/hub#1
*Played:* grief held down; doing: a man of his was killed; pace: slow; volume: quiet.
*Wants:* not to show it
*Note:* Quartermaster's list for a dead man. 'by the bad leg' barely steady. 'I'd give a month's pay to hear him hum.' cracks just slightly. Then forced back to business: 'Five a pelt, still. What do you want?'

```
[grief held down, quietly] You heard. Aldo. Wife at Low Kiln, a bad knee, and a habit of humming on the wall that I told him twice to stop. They took him off it by the bad leg. I'd give a month's pay to hear him hum. Five a pelt, still. What do you want?
```
Subtitle: You heard. Aldo. Wife at Low Kiln, a bad knee, and a habit of humming on the wall that I told him twice to stop. They took him off it by the bad leg. I'd give a month's pay to hear him hum. Five a pelt, still. What do you want?

### 6. `dlg.holloway.hub.2.p1.wav`

*Where:* dialogue.json holloway/hub#2; part 2 of 2: narrator: A letter lies open under his lamp, a silver seal broken on it. He turns it face down when … / **holloway: What.**
*Played:* guarded, curt; doing: hides the letter; pace: slow; volume: quiet.
*Note:* Narrator reads the business with the letter. 'What.' flat and closed.

```
[guarded, curt, quietly] What.
```
Subtitle: What.

### 7. `dlg.holloway.hub.3.wav`

*Where:* dialogue.json holloway/hub#3
*Played:* cold distrust; doing: watches you; pace: measured; volume: quiet.
*Note:* Low and hard.

```
[cold distrust, quietly] You. Keep your hands where I can see them.
```
Subtitle: You. Keep your hands where I can see them.

### 8. `dlg.holloway.hub.4.p1.wav`

*Where:* dialogue.json holloway/hub#4; part 2 of 2: narrator: He straightens when you come in, and then looks annoyed that he did. / **holloway: You. What is it?**
*Played:* grudging respect, annoyed; doing: greets someone formidable; pace: measured; volume: level.
*Note:* Curt; annoyed with himself.

```
[grudging respect, annoyed] You. What is it?
```
Subtitle: You. What is it?

### 9. `dlg.holloway.hub.5.wav`

*Where:* dialogue.json holloway/hub#5
*Played:* dry, wary; doing: your reputation precedes you; pace: measured; volume: level.
*Note:* Dry warning.

```
[dry, wary] They say you've put down more things than the fever year. Try not to put any down in my square.
```
Subtitle: They say you've put down more things than the fever year. Try not to put any down in my square.

### 10. `dlg.holloway.hub.6.wav`

*Where:* dialogue.json holloway/hub#6
*Played:* bitter irony; doing: the slaughter's cost; pace: measured; volume: quiet.
*Note:* Not proud. The Maeca line hurts more than he lets on.

```
[bitter irony, quietly] The road's quiet. I paid for every pelt of it. You know how quiet? Maeca's stopped coming in to argue with me.
```
Subtitle: The road's quiet. I paid for every pelt of it. You know how quiet? Maeca's stopped coming in to argue with me.

### 11. `dlg.holloway.hub.7.wav`

*Where:* dialogue.json holloway/hub#7
*Played:* frustrated, grudging; doing: the bounty isn't working; pace: measured; volume: level.
*Note:* Exasperated. 'and I hate that' with feeling.

```
[frustrated, grudging] I pay for a pelt and two more wolves come down the road. I'm starting to think Maeca's right, and I hate that. What is it?
```
Subtitle: I pay for a pelt and two more wolves come down the road. I'm starting to think Maeca's right, and I hate that. What is it?

### 12. `dlg.holloway.hub.8.wav`

*Where:* dialogue.json holloway/hub#8
*Played:* impatient, tired; doing: busy; pace: brisk; volume: level.
*Note:* Clipped.

```
[impatient, tired] Make it quick. I've a gate to count.
```
Subtitle: Make it quick. I've a gate to count.

### 13. `dlg.holloway.wolves.0.wav`

*Where:* dialogue.json holloway/wolves#0
*Played:* terse, practical; doing: explains the bounty; pace: measured; volume: level.
*Wants:* proof, not stories
*Note:* A quartermaster's numbers. 'Bring me proof and I'll pay. Bring me stories and I won't.' as a rule. The eleven-men line bitter and dry.

```
[terse, practical] They're bolder. Two nights ago they came right up to the east gate. Five a pelt, fifty for the old grey one they call Grey-muzzle. Bring me proof and I'll pay. Bring me stories and I won't. I've eleven men and four of them can hold a spear the right way round; I'm not spending them on stories.
```
Subtitle: They're bolder. Two nights ago they came right up to the east gate. Five a pelt, fifty for the old grey one they call Greymuzzle. Bring me proof and I'll pay. Bring me stories and I won't. I've eleven men and four of them can hold a spear the right way round; I'm not spending them on stories.

### 14. `dlg.holloway.maeca.0.wav`

*Where:* dialogue.json holloway/maeca#0
*Played:* grudging respect, guilt; doing: speaks of Maeca; pace: slow; volume: quiet.
*Note:* Fair-minded first sentence. Then much quieter, after a pause: what she never got. Guilt he won't name.

```
[grudging respect, guilt, quietly] Maeca's right more often than I'd like. She's earned that. ...She's earned a lot of things she never got.
```
Subtitle: Maeca's right more often than I'd like. She's earned that. ...She's earned a lot of things she never got.

### 15. `dlg.holloway.ashford.0.wav`

*Where:* dialogue.json holloway/ashford#0
*Played:* guilt, shutting down; doing: almost confesses; pace: slow; volume: quiet.
*Wants:* to stop talking
*Note:* 'Boots, for a start.' heavy. Bitter pride on 'I was good at it.' Then the door slams: 'That's all you're getting.' 'Something else?' brusque.

```
[guilt, shutting down, quietly] Boots, for a start. I counted boots for the Ashford garrison, once, and I was good at it. That's all you're getting. Something else?
```
Subtitle: Boots, for a start. I counted boots for the Ashford garrison, once, and I was good at it. That's all you're getting. Something else?

### 16. `dlg.holloway.bounty.0.wav`

*Where:* dialogue.json holloway/bounty#0
*Played:* grim satisfaction; doing: pays for Greymuzzle; pace: measured; volume: level.
*Note:* Almost respectful of the old devil. Thanks offered plainly.

```
[grim satisfaction] That's his fang. That's the old devil himself. Fifty, as promised, and my thanks with it.
```
Subtitle: That's his fang. That's the old devil himself. Fifty, as promised, and my thanks with it.

### 17. `dlg.holloway.bounty.1.wav`

*Where:* dialogue.json holloway/bounty#1
*Played:* businesslike; doing: counts pelts; pace: brisk; volume: level.
*Note:* Already counting.

```
[businesslike] Pelts. Good. Let me count them.
```
Subtitle: Pelts. Good. Let me count them.

### 18. `dlg.holloway.liar.0.wav`

*Where:* dialogue.json holloway/liar#0
*Played:* cold fury; doing: confronts your lie; pace: slow; volume: level.
*Wants:* his gold's worth, and the truth
*Hides:* he has been paying for something himself for ten years; some of the anger is at himself for trusting you
*Note:* Quiet anger one notch below the surface; he never raises his voice and swears rarely, so when he does it lands. Mock-quote 'dealt with'. 'So.' then the swear lands hard and low, not shouted.

```
[cold fury] Dealt with. That's what you said. I paid you thirty of the Watch's gold for "dealt with", and this morning I had a drover bleeding on my gate. So. Tell me why you shouldn't spend the night in the fucking cells.
```
Subtitle: Dealt with. That's what you said. I paid you thirty of the Watch's gold for "dealt with", and this morning I had a drover bleeding on my gate. So. Tell me why you shouldn't spend the night in the fucking cells.

### 19. `dlg.holloway.repaid.0.wav`

*Where:* dialogue.json holloway/repaid#0
*Played:* dry, grudging; doing: accepts repayment; pace: measured; volume: level.
*Note:* Dry wit; 'I've written both halves down' a quartermaster's threat.

```
[dry, grudging] A liar who pays his debts. Rarer than wolves, that. I've written both halves down.
```
Subtitle: A liar who pays his debts. Rarer than wolves, that. I've written both halves down.

### 20. `dlg.holloway.argued.0.wav`

*Where:* dialogue.json holloway/argued#0
*Played:* thinking, grudging; doing: accepts your argument; pace: slow; volume: level.
*Note:* Turning it over. 'bucket against a flood' tired. Deal offered gruffly.

```
[thinking, grudging] ...New ones. From a sick wood. Then the pelts buy me nothing, and you're telling me the bounty's a bucket against a flood. Find me the hole in the bucket and we'll call it square.
```
Subtitle: ...New ones. From a sick wood. Then the pelts buy me nothing, and you're telling me the bounty's a bucket against a flood. Find me the hole in the bucket and we'll call it square.

### 21. `dlg.holloway.defied.0.wav`

*Where:* dialogue.json holloway/defied#0
*Played:* contempt, threat; doing: throws you out; pace: measured; volume: raised.
*Note:* 'Out of my sight.' sharp. The threat cold and almost pleasant at the end.

```
[contempt, threat, loudly] Out of my sight. And if I see you near my gate with a blade out, you'll find out how the cells feel on a cold night, and how the cell-rats feel about fresh meat.
```
Subtitle: Out of my sight. And if I see you near my gate with a blade out, you'll find out how the cells feel on a cold night, and how the cell-rats feel about fresh meat.

### 22. `dlg.holloway.caravan.0.wav`

*Where:* dialogue.json holloway/caravan#0
*Played:* certain, suspicious; doing: the caravan left the road; pace: measured; volume: level.
*Note:* Facts in order. 'lied' hard.

```
[certain, suspicious] Coyle's wagons never reached my gate. The Old Road was open all day; I had men on it dawn to dusk. Whatever happened to them happened off the road, and whoever told them otherwise lied.
```
Subtitle: Coyle's wagons never reached my gate. The Old Road was open all day; I had men on it dawn to dusk. Whatever happened to them happened off the road, and whoever told them otherwise lied.

### 23. `dlg.holloway.caravan2.0.wav`

*Where:* dialogue.json holloway/caravan2#0
*Played:* grim, uneasy; doing: someone in town is guilty; pace: measured; volume: quiet.
*Note:* Quiet. 'I don't like a single name on it.' troubled.

```
[grim, uneasy, quietly] Somebody who knew they were coming, what they carried and which clerk could be bought. That's a short list in a town this size, and I don't like a single name on it.
```
Subtitle: Somebody who knew they were coming, what they carried and which clerk could be bought. That's a short list in a town this size, and I don't like a single name on it.

### 24. `dlg.holloway.sick.0.wav`

*Where:* dialogue.json holloway/sick#0
*Played:* gruff, then open; doing: listens; pace: measured; volume: level.
*Note:* Dismissive first line; after the pause, open and tired: he'd rather fix the cause.

```
[gruff, then open] Sick or bold, they bite the same. ...But if you're right, and you can show me what's sickening them, I'd rather fix the cause than pay for pelts till I'm old.
```
Subtitle: Sick or bold, they bite the same. ...But if you're right, and you can show me what's sickening them, I'd rather fix the cause than pay for pelts till I'm old.

### 25. `dlg.holloway.cause.0.wav`

*Where:* dialogue.json holloway/cause#0
*Played:* angry disgust, resolve; doing: ends the bounty; pace: measured; volume: level.
*Note:* 'Of course it's the lamplings.' disgust. Firm: no paying men to kill sick dogs.

```
[angry disgust, resolve] The lamplings. Of course it's the lamplings. Then I'm done paying for pelts: I'll not pay men to put down sick dogs. Deal with the pump. I'll keep watching the road.
```
Subtitle: The lamplings. Of course it's the lamplings. Then I'm done paying for pelts: I'll not pay men to put down sick dogs. Deal with the pump. I'll keep watching the road.

### 26. `dlg.holloway.cause.1.wav`

*Where:* dialogue.json holloway/cause#1
*Played:* angry disgust, resolve; doing: agrees to stop the bounty; pace: measured; volume: level.
*Note:* 'Of course it's the lamplings.' disgust. Practical deal.

```
[angry disgust, resolve] The lamplings. Of course it's the lamplings. Deal with the pump and I'll stop paying for pelts. I won't stop watching the road.
```
Subtitle: The lamplings. Of course it's the lamplings. Deal with the pump and I'll stop paying for pelts. I won't stop watching the road.

### 27. `dlg.holloway.lie.0.wav`

*Where:* dialogue.json holloway/lie#0
*Played:* doubtful, dry; doing: pays for your claim; pace: measured; volume: level.
*Note:* Not convinced. The last sentence a warning.

```
[doubtful, dry] Dealt with. The road's been quiet today, I'll grant you that. Thirty for the trouble. And if I've wolves at my gate tomorrow night, we'll talk again.
```
Subtitle: Dealt with. The road's been quiet today, I'll grant you that. Thirty for the trouble. And if I've wolves at my gate tomorrow night, we'll talk again.

### 28. `dlg.holloway.expose.0.wav`

*Where:* dialogue.json holloway/expose#0
*Played:* grim triumph, then dry; doing: Pell is caught; pace: measured; volume: level.
*Note:* Reading the ledger aloud, building. Contempt and relish on 'you careful, greedy little man'. The fee line dry: 'Once.'

```
[grim triumph, then dry] Payments to "R.": Red-cowl. And to Jessop, at Vonnra's toll. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. ...And the strongbox you sold, we'll call that a fee for services. Once.
```
Subtitle: Payments to "R.": Redcowl. And to Jessop, at Vonnra's toll. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. ...And the strongbox you sold, we'll call that a fee for services. Once.

### 29. `dlg.holloway.expose.1.wav`

*Where:* dialogue.json holloway/expose#1
*Played:* grim triumph, then gratitude; doing: Pell is caught; pace: measured; volume: level.
*Note:* Reading the ledger, building. Contempt on 'careful, greedy little man'. Then awkward, sincere thanks; 'I've not much to pay you with' rueful.

```
[grim triumph, then gratitude] Payments to "R.": Red-cowl. And to Jessop, at Vonnra's toll. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. The Watch owes you. I don't say that lightly; I've not much to pay you with.
```
Subtitle: Payments to "R.": Redcowl. And to Jessop, at Vonnra's toll. On the night. Pell Varrow, you careful, greedy little man. My lads'll have him in irons before dark. The Watch owes you. I don't say that lightly; I've not much to pay you with.

### 30. `dlg.holloway.arrest.0.wav`

*Where:* dialogue.json holloway/arrest#0
*Played:* stern, official; doing: fines you; pace: measured; volume: level.
*Note:* A captain's sentence; flat terms.

```
[stern, official] You sold the Coyle cargo to a fence. Everyone in the Waystation knows it, and so do I. A hundred gold to the Watch and we'll say no more about it. Or you can leave my town.
```
Subtitle: You sold the Coyle cargo to a fence. Everyone in the Waystation knows it, and so do I. A hundred gold to the Watch and we'll say no more about it. Or you can leave my town.

### 31. `dlg.holloway.cb_killed_greymuzzle.0.wav`

*Where:* dialogue.json holloway/cb_killed_greymuzzle#0
*Played:* troubled, judging; doing: you killed the wolf anyway; pace: slow; volume: quiet.
*Note:* Puzzled and uneasy, not angry.

```
[troubled, judging, quietly] I hear you put the old grey one down. I'd stopped paying for it. You did it anyway. I'm trying to work out what that makes you.
```
Subtitle: I hear you put the old grey one down. I'd stopped paying for it. You did it anyway. I'm trying to work out what that makes you.

### 32. `dlg.holloway.cb_killed_greymuzzle.1.wav`

*Where:* dialogue.json holloway/cb_killed_greymuzzle#1
*Played:* dry, then wistful; doing: the old wolf is dead; pace: measured; volume: quiet.
*Note:* Dry joke about Maeca. After the pause, unexpectedly reflective: odd, missing a thing you hated.

```
[dry, then wistful, quietly] Greymuzzle's dead, they tell me. Mayka won't speak to me for a month and I've slept better for it already. ...Twenty years that wolf's had the run of this valley. Odd, missing a thing you hated.
```
Subtitle: Greymuzzle's dead, they tell me. Maeca won't speak to me for a month and I've slept better for it already. ...Twenty years that wolf's had the run of this valley. Odd, missing a thing you hated.

### 33. `dlg.holloway.cb_burned_roost.0.wav`

*Where:* dialogue.json holloway/cb_burned_roost#0
*Played:* cold anger; doing: he knows you burned it; pace: slow; volume: quiet.
*Note:* Each clause measured and cold. 'and I'd like you to know that I know that' quiet and precise.

```
[cold anger, quietly] The Roost burned with the cages full. I've hanged men for less. I can't prove you lit it, and you know I can't, and I'd like you to know that I know that.
```
Subtitle: The Roost burned with the cages full. I've hanged men for less. I can't prove you lit it, and you know I can't, and I'd like you to know that I know that.

### 34. `dlg.holloway.cb_freed_teamsters.0.wav`

*Where:* dialogue.json holloway/cb_freed_teamsters#0
*Played:* grudging gratitude; doing: thanks you, gruffly; pace: measured; volume: level.
*Note:* Relief in 'and alive'. The joke at his own expense dry.

```
[grudging gratitude] Three teamsters walked in through my gate, thin as rakes and alive. You did what eleven Watchmen couldn't. Don't let it go to your head; eleven Watchmen can't do much.
```
Subtitle: Three teamsters walked in through my gate, thin as rakes and alive. You did what eleven Watchmen couldn't. Don't let it go to your head; eleven Watchmen can't do much.

### 35. `dlg.holloway.cb_tricked_redcowl.0.wav`

*Where:* dialogue.json holloway/cb_tricked_redcowl#0
*Played:* dry amusement; doing: your trick used his name; pace: measured; volume: level.
*Note:* Deadpan 'The Watch was in bed.' The last three sentences a man talking himself round.

```
[dry amusement] Somebody told Red-cowl the Watch was coming, and he ran. The Watch was in bed. ...I'd ask you not to use my name in vain. But it worked. Did it work? It worked.
```
Subtitle: Somebody told Redcowl the Watch was coming, and he ran. The Watch was in bed. ...I'd ask you not to use my name in vain. But it worked. Did it work? It worked.

### 36. `dlg.holloway.cb_opened_vault.0.wav`

*Where:* dialogue.json holloway/cb_opened_vault#0
*Played:* weary gravity; doing: you broke an old oath; pace: slow; volume: quiet.
*Note:* Solemn, then too tired to care. 'What's down there?' genuinely wanting to know.

```
[weary gravity, quietly] You went through the black door. The Watch was founded on the promise that nobody would. My predecessors would've hanged you for it. I'm too tired. What's down there?
```
Subtitle: You went through the black door. The Watch was founded on the promise that nobody would. My predecessors would've hanged you for it. I'm too tired. What's down there?

### 37. `dlg.holloway.cb_vault2.0.wav`

*Where:* dialogue.json holloway/cb_vault2#0
*Played:* weary resignation; doing: doesn't want to know; pace: measured; volume: quiet.
*Note:* Flat 'Course it is.'

```
[weary resignation, quietly] Course it is. Keep it to yourself. I've enough to count.
```
Subtitle: Course it is. Keep it to yourself. I've enough to count.

### 38. `dlg.holloway.cb_nemesis_slain.0.wav`

*Where:* dialogue.json holloway/cb_nemesis_slain#0
*Played:* grudging admiration; doing: you went back; pace: measured; volume: level.
*Note:* Dry, impressed.

```
[grudging admiration] Heard you went back for whatever killed you and took your things off it. I've known men who wouldn't go back for their own boots.
```
Subtitle: Heard you went back for whatever killed you and took your things off it. I've known men who wouldn't go back for their own boots.

### 39. `dlg.holloway.cb_core_stolen.0.wav`

*Where:* dialogue.json holloway/cb_core_stolen#0
*Played:* suspicious, weary; doing: the heart was taken; pace: measured; volume: quiet.
*Note:* Pointed; doesn't want the answer.

```
[suspicious, weary, quietly] They say a lampling walked off with the Warden's heart while you stood there. Don't tell me why you let it. I've a feeling I'd not like either answer.
```
Subtitle: They say a lampling walked off with the Warden's heart while you stood there. Don't tell me why you let it. I've a feeling I'd not like either answer.

### 40. `dlg.holloway.say_calling.0.wav`

*Where:* dialogue.json holloway/say_calling#0
*Played:* curious, then rueful; doing: sees a soldier; pace: measured; volume: level.
*Note:* Interested for a moment; 'I can't afford you either way' rueful.

```
[curious, then rueful] You stand like Watch. Who trained you? ...Never mind. I can't afford you either way.
```
Subtitle: You stand like Watch. Who trained you? ...Never mind. I can't afford you either way.

### 41. `dlg.holloway.say_calling.1.wav`

*Where:* dialogue.json holloway/say_calling#1
*Played:* wary; doing: a warning; pace: measured; volume: level.
*Note:* Plain, a little menacing.

```
[wary] I've seen men built like you on both sides of a gate. Make sure I always know which side you're on.
```
Subtitle: I've seen men built like you on both sides of a gate. Make sure I always know which side you're on.

### 42. `dlg.holloway.say_calling.2.wav`

*Where:* dialogue.json holloway/say_calling#2
*Played:* dry exasperation; doing: no magic in town; pace: measured; volume: level.
*Note:* Dry anecdote; firm order.

```
[dry exasperation] Spark-thrower. The last one we had set the barracks roof alight trying to light a pipe. Do your tricks outside my walls.
```
Subtitle: Spark-thrower. The last one we had set the barracks roof alight trying to light a pipe. Do your tricks outside my walls.

### 43. `dlg.holloway.say_calling.3.wav`

*The same words are also* `dlg.holloway.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json holloway/say_calling#3
*Played:* dry recognition; doing: sees a fellow watcher; pace: measured; volume: level.
*Note:* Almost a joke between equals.

```
[dry recognition] You count the ways out when you walk into a room. So do I. One of us should be paid for it.
```
Subtitle: You count the ways out when you walk into a room. So do I. One of us should be paid for it.

### 44. `dlg.holloway.say_woman.0.wav`

*Where:* dialogue.json holloway/say_woman#0
*Played:* dry, grim; doing: won't patronise you; pace: measured; volume: level.
*Note:* Starts the old line, stops himself. 'it's no place.' flat and honest.

```
[dry, grim] I'd tell you it's no place for a woman out there. The last three people I said that to were men, and they're dead. So I'll say: it's no place.
```
Subtitle: I'd tell you it's no place for a woman out there. The last three people I said that to were men, and they're dead. So I'll say: it's no place.

### 45. `dlg.holloway.t_holloway.0.wav`

*Where:* dialogue.json holloway/t_holloway#0
*Played:* tired, wry; doing: what he wants; pace: measured; volume: quiet.
*Note:* A list delivered like an inventory, tired and longing. 'In that order.' dry. The dog line sheepish.

```
[tired, wry, quietly] A posting with walls somebody else has to count. A dog. Eight hours' sleep in one go. In that order. ...Don't tell the men about the dog.
```
Subtitle: A posting with walls somebody else has to count. A dog. Eight hours' sleep in one go. In that order. ...Don't tell the men about the dog.

### 46. `dlg.holloway.ledger_early.0.p1.wav`

*Where:* dialogue.json holloway/ledger_early#0; part 2 of 4: narrator: He reads it standing up. Then he sits down and reads it again. / **holloway: Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's cler…** / narrator: He shuts it. / holloway: Don't tell me where you got it. If you tell me, I have to do something about it.
*Played:* shocked, then careful; doing: the ledger is damning; pace: slow; volume: quiet.
*Wants:* not to be made to act yet
*Note:* Narrator for the reading. Then reading the entries, quieter as he understands. Firm and low on 'Don't tell me where you got it.'

```
[shocked, then careful, quietly] Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's clerk at the toll. And that's the night Harlan Coyle's wagons went off the Old Road and didn't come back.
```
Subtitle: Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's clerk at the toll. And that's the night Harlan Coyle's wagons went off the Old Road and didn't come back.

### 47. `dlg.holloway.ledger_early.0.p3.wav`

*Where:* dialogue.json holloway/ledger_early#0; part 4 of 4: narrator: He reads it standing up. Then he sits down and reads it again. / holloway: Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's cler… / narrator: He shuts it. / **holloway: Don't tell me where you got it. If you tell me, I have to do something about it.**
*Played:* shocked, then careful; doing: the ledger is damning; pace: slow; volume: quiet.
*Wants:* not to be made to act yet
*Note:* Narrator for the reading. Then reading the entries, quieter as he understands. Firm and low on 'Don't tell me where you got it.'

```
[shocked, then careful, quietly] Don't tell me where you got it. If you tell me, I have to do something about it.
```
Subtitle: Don't tell me where you got it. If you tell me, I have to do something about it.

### 48. `dlg.holloway.ledger_early2.0.wav`

*Where:* dialogue.json holloway/ledger_early2#0
*Played:* frustrated, careful; doing: needs more proof; pace: measured; volume: level.
*Note:* Dry about thieves and letters. Proof, not evidence. 'Keep it somewhere I can't see it.' low.

```
[frustrated, careful] Could be anyone. There's more thieves in this valley than letters to go round. Find me who "R." is, and what Pell bought for forty, and I'll put him in irons myself. Until then it's a book with numbers in, and Pell's got a man in Low Kiln who loves numbers. ...Keep it somewhere I can't see it.
```
Subtitle: Could be anyone. There's more thieves in this valley than letters to go round. Find me who "R." is, and what Pell bought for forty, and I'll put him in irons myself. Until then it's a book with numbers in, and Pell's got a man in Low Kiln who loves numbers. ...Keep it somewhere I can't see it.

### 49. `dlg.holloway.post.0.p1.wav`

*Where:* dialogue.json holloway/post#0; part 2 of 2: narrator: He says nothing for long enough that you think he hasn't heard. / **holloway: Grey beard, proud of it? Bad hip? ...Corran. He had that post before I had this one. I wro…**
*Played:* shock, guilt; doing: his old comrade is dead; pace: slow; volume: quiet.
*Note:* Narrator holds the silence. Then quiet questions he knows the answers to. 'Corran.' on its own. The deserter lines in self-disgust.

```
[shock, guilt, quietly] Grey beard, proud of it? Bad hip? ...Corran. He had that post before I had this one. I wrote him down as a deserter in the spring. Him and his runner, Dannet. Dannet never came up the road, so I wrote him down too.
```
Subtitle: Grey beard, proud of it? Bad hip? ...Corran. He had that post before I had this one. I wrote him down as a deserter in the spring. Him and his runner, Dannet. Dannet never came up the road, so I wrote him down too.

### 50. `dlg.holloway.post2.0.p0.wav`

*Where:* dialogue.json holloway/post2#0; part 1 of 3: **holloway: Not by us. We've not had oil for those lamps since my first winter, and nobody's asked me …** / narrator: He writes something down, and crosses it out. / holloway: So somebody had oil. And a reason. ...I'll send two men down with a cart. I owe Corran a h…
*Played:* grim realisation, guilt; doing: someone lit the lamps; pace: slow; volume: quiet.
*Note:* Thinking it through. Narrator for the writing. 'So somebody had oil. And a reason.' cold. The apology line heavy.

```
[grim realisation, guilt, quietly] Not by us. We've not had oil for those lamps since my first winter, and nobody's asked me for any.
```
Subtitle: Not by us. We've not had oil for those lamps since my first winter, and nobody's asked me for any.

### 51. `dlg.holloway.post2.0.p2.wav`

*Where:* dialogue.json holloway/post2#0; part 3 of 3: holloway: Not by us. We've not had oil for those lamps since my first winter, and nobody's asked me … / narrator: He writes something down, and crosses it out. / **holloway: So somebody had oil. And a reason. ...I'll send two men down with a cart. I owe Corran a h…**
*Played:* grim realisation, guilt; doing: someone lit the lamps; pace: slow; volume: quiet.
*Note:* Thinking it through. Narrator for the writing. 'So somebody had oil. And a reason.' cold. The apology line heavy.

```
[grim realisation, guilt, quietly] So somebody had oil. And a reason. ...I'll send two men down with a cart. I owe Corran a hole in the ground, and an apology he can't hear.
```
Subtitle: So somebody had oil. And a reason. ...I'll send two men down with a cart. I owe Corran a hole in the ground, and an apology he can't hear.

### 52. `dlg.holloway.letter.0.p0.wav`

*Where:* dialogue.json holloway/letter#0; part 1 of 3: **holloway: Mine. From the north, about the north.** / narrator: The cup doesn't move. / holloway: Read your own post, if anybody writes to you.
*Played:* closed, curt; doing: won't discuss the letter; pace: measured; volume: quiet.
*Note:* 'Mine.' hard. Narrator: the cup doesn't move. Brusque dismissal.

```
[closed, curt, quietly] Mine. From the north, about the north.
```
Subtitle: Mine. From the north, about the north.

### 53. `dlg.holloway.letter.0.p2.wav`

*Where:* dialogue.json holloway/letter#0; part 3 of 3: holloway: Mine. From the north, about the north. / narrator: The cup doesn't move. / **holloway: Read your own post, if anybody writes to you.**
*Played:* closed, curt; doing: won't discuss the letter; pace: measured; volume: quiet.
*Note:* 'Mine.' hard. Narrator: the cup doesn't move. Brusque dismissal.

```
[closed, curt, quietly] Read your own post, if anybody writes to you.
```
Subtitle: Read your own post, if anybody writes to you.

## Said in passing

### 54. `bark.holloway.day.0.wav`

*Where:* npcs.json holloway.barks[0]
*Played:* curt; pace: brisk; volume: level.

```
[curt] Keep to the road, and keep your blade where I can see it.
```
Subtitle: Keep to the road, and keep your blade where I can see it.

### 55. `bark.holloway.day.1.wav`

*Where:* npcs.json holloway.barks[1]
*Played:* curt; pace: brisk; volume: level.

```
[curt] Three caravans this month. Three.
```
Subtitle: Three caravans this month. Three.

### 56. `bark.holloway.night.0.wav`

*Where:* npcs.json holloway.nightBarks[0]
*Played:* tired; pace: measured; volume: quiet.

```
[tired, quietly] Curfew's not law. Yet.
```
Subtitle: Curfew's not law. Yet.

### 57. `bark.holloway.night.1.wav`

*Where:* npcs.json holloway.nightBarks[1]
*Played:* tired; pace: measured; volume: quiet.

```
[tired, quietly] Two on the walls, one on each gate. It's not enough.
```
Subtitle: Two on the walls, one on each gate. It's not enough.

### 58. `bark.holloway.night.2.wav`

*Where:* npcs.json holloway.nightBarks[2]
*Played:* tired; pace: measured; volume: quiet.

```
[tired, quietly] Go to bed, traveller.
```
Subtitle: Go to bed, traveller.

### 59. `bark.holloway.night.3.wav`

*Where:* npcs.json holloway.nightBarks[3]
*Played:* tired; pace: measured; volume: quiet.

```
[tired, quietly] Every night I bury somebody's son. Go home.
```
Subtitle: Every night I bury somebody's son. Go home.

### 60. `bark.holloway.night.4.wav`

*Where:* npcs.json holloway.nightBarks[4]
*Played:* tired; pace: measured; volume: quiet.

```
[tired, quietly] Quiet on the wall. I hate it quiet.
```
Subtitle: Quiet on the wall. I hate it quiet.

### 61. `bark.holloway.said.0.wav`

*Where:* npcs.json holloway.said[0]
*Played:* businesslike; doing: the pelt bounty; pace: measured; volume: level.
*Note:* A notice read aloud by a man who wrote it.

```
[businesslike] Five a pelt. Fifty for the old grey one.
```
Subtitle: Five a pelt. Fifty for the old grey one.

### 62. `bark.holloway.said.1.wav`

*Where:* npcs.json holloway.said[1]
*Played:* dry relief; doing: the bounty's done; pace: measured; volume: level.
*Note:* A tired half-smile in it.

```
[dry relief] Pelt book's closed. I'll not miss writing in it.
```
Subtitle: Pelt book's closed. I'll not miss writing in it.

### 63. `bark.holloway.said.2.wav`

*Where:* npcs.json holloway.said[2]
*Played:* grim, private; doing: Corran buried; pace: slow; volume: quiet.
*Hides:* the debt is his own
*Note:* To himself. 'That's one debt paid.' flat.

```
[grim, private, quietly] Corran's in the ground. That's one debt paid.
```
Subtitle: Corran's in the ground. That's one debt paid.

### 64. `bark.holloway.said.3.wav`

*Where:* npcs.json holloway.said[3]
*Played:* weary, grateful; doing: one caravan came home; pace: measured; volume: level.
*Note:* 'One.' heavy; 'I'll take it.' accepting.

```
[weary, grateful] One caravan home. I'll take it.
```
Subtitle: One caravan home. I'll take it.


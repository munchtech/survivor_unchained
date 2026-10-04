# Harlan Coyle: ElevenLabs packet

Voice id in the game: `harlan`. 63 takes to record (7,217 characters; about 21,651 credits at three tries a line). Status: **final** (the story lead, 2026-10-04): record it.

## Who they are

**Harlan Coyle** (the Coyle Company). A salesman's patter with a crack in it: lists of goods, prices, "friend". Over-explains, then stops dead. Breaks on "Jory". Never names the buyer of the B.E. crates, and changes the subject a beat too fast when anyone tries. *Casting:* 55, Bristol merchant, warm and cracking.

*Wants:* Jory home, and the Company alive. *Hides:* the Company has sold the Dig its blasting ember for two years, through Pell's books and the Kerchiefs' road; he put Jory on the road with six crates he knew were bound for the hole. His grief is real and so is his guilt, and every 'Jory' carries both. His sister died in the fever year, of the ember sickness, and he sells the stuff anyway; he has never let himself see that, so never play the irony.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Harlan Coyle`. Never describe a voice as sounding like a real person.

```
Native English (British, Bristol). Male, 50s. Studio quality. Persona: a Bristol merchant. A fifty-five-year-old merchant from Bristol in the West Country of England, with a warm, rounded Bristolian accent. A friendly salesman's baritone, quick patter, warm and generous, with a crack of grief that breaks through when he stops talking. Broad Bristol accent. No reverb or effects.
```

Preview text:

```
Coyle Company, friend: salt, iron and Morrow cloth, nails, good wool and better rope, at the fairest prices between here and the coast. Ask anyone. Well. Ask most people.
```

In the Voice Library instead: search for *Bristol*, *male*, *50*, and listen for this: A fifty-five-year-old merchant from Bristol in the West Country of England, with a warm, rounded Bristolian accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.harlan.first.0.p0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice harlan
```

## Saying the names

The text to paste already respells these; keep the respelling: Thornhollow as *Thorn-hollow*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Harlan

### 1. `dlg.harlan.first.0.p0.wav`

*Where:* dialogue.json harlan/first#0; part 1 of 3: **harlan: You. Jory says it was you at the cage with the bar in your hands, and he's told it four ti…** / narrator: He takes your hand in both of his. / harlan: Harlan Coyle, of the Coyle Company. Any other day I'd have said that first.
*Played:* overflowing gratitude; doing: meets Jory's rescuer; pace: quick; volume: level.
*Wants:* to thank you properly
*Note:* Delighted, laughing at Jory's retelling. Narrator: he takes your hand. Then a little embarrassed formality: 'Any other day I'd have said that first.'

```
[overflowing gratitude] You. Jory says it was you at the cage with the bar in your hands, and he's told it four times since breakfast, and it gets better every time.
```
Subtitle: You. Jory says it was you at the cage with the bar in your hands, and he's told it four times since breakfast, and it gets better every time.

### 2. `dlg.harlan.first.0.p2.wav`

*Where:* dialogue.json harlan/first#0; part 3 of 3: harlan: You. Jory says it was you at the cage with the bar in your hands, and he's told it four ti… / narrator: He takes your hand in both of his. / **harlan: Harlan Coyle, of the Coyle Company. Any other day I'd have said that first.**
*Played:* overflowing gratitude; doing: meets Jory's rescuer; pace: quick; volume: level.
*Wants:* to thank you properly
*Note:* Delighted, laughing at Jory's retelling. Narrator: he takes your hand. Then a little embarrassed formality: 'Any other day I'd have said that first.'

```
[overflowing gratitude] Harlan Coyle, of the Coyle Company. Any other day I'd have said that first.
```
Subtitle: Harlan Coyle, of the Coyle Company. Any other day I'd have said that first.

### 3. `dlg.harlan.first.1.p1.wav`

*Where:* dialogue.json harlan/first#1; part 2 of 2: narrator: The shutters are half closed, and he doesn't get up. / **harlan: Harlan Coyle. You'll have heard. Everyone's heard. ...Buy something, or don't.**
*Played:* hollow grief; doing: Jory is dead; pace: slow; volume: quiet.
*Note:* Narrator: the shutters, he doesn't get up. His name said without the patter. 'Everyone's heard.' A pause. 'Buy something, or don't.' empty.

```
[hollow grief, quietly] Harlan Coyle. You'll have heard. Everyone's heard. ...Buy something, or don't.
```
Subtitle: Harlan Coyle. You'll have heard. Everyone's heard. ...Buy something, or don't.

### 4. `dlg.harlan.first.2.p0.wav`

*Where:* dialogue.json harlan/first#2; part 1 of 3: **harlan: That's my seal. That's—** / narrator: He's round the counter before you can blink, hands out, and then he doesn't touch it. / harlan: Where did you get that? Where was it? Where's the boy that was driving it?
*Played:* shock, desperate hope; doing: his strongbox, and Jory?; pace: quick; volume: raised.
*Wants:* news of Jory
*Note:* Breaks off on 'That's—'. Narrator for the rush round the counter. Then questions tumbling, rising, the last one cracking: the boy.

```
[shock, desperate hope, loudly] That's my seal. That's—
```
Subtitle: That's my seal. That's—

### 5. `dlg.harlan.first.2.p2.wav`

*Where:* dialogue.json harlan/first#2; part 3 of 3: harlan: That's my seal. That's— / narrator: He's round the counter before you can blink, hands out, and then he doesn't touch it. / **harlan: Where did you get that? Where was it? Where's the boy that was driving it?**
*Played:* shock, desperate hope; doing: his strongbox, and Jory?; pace: quick; volume: raised.
*Wants:* news of Jory
*Note:* Breaks off on 'That's—'. Narrator for the rush round the counter. Then questions tumbling, rising, the last one cracking: the boy.

```
[shock, desperate hope, loudly] Where did you get that? Where was it? Where's the boy that was driving it?
```
Subtitle: Where did you get that? Where was it? Where's the boy that was driving it?

### 6. `dlg.harlan.first.3.wav`

*Where:* dialogue.json harlan/first#3
*Played:* patter cracking into hope; doing: you've been in the Verge; pace: quick; volume: level.
*Wants:* news
*Note:* Salesman's opener by habit, then he smells the Verge and the patter drops. 'Tell me you've seen something.' pleading.

```
[patter cracking into hope] Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth. You've the Verge on your boots, friend; I can smell it from here. My wagons are out there somewhere. Three of them, and a boy called Jory driving the first. Tell me you've seen something.
```
Subtitle: Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth. You've the Verge on your boots, friend; I can smell it from here. My wagons are out there somewhere. Three of them, and a boy called Jory driving the first. Tell me you've seen something.

### 7. `dlg.harlan.first.4.wav`

*Where:* dialogue.json harlan/first#4
*Played:* patter, then cracking; doing: his missing nephew; pace: measured; volume: level.
*Wants:* news of Jory
*Note:* Warm Bristol patter on the goods. Slower on Jory. 'He's never been a week late in his life.' breaks. Pause. 'Forgive me. I say that to everyone.' embarrassed.

```
[patter, then cracking] Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory driving the first. A week, near enough. He's never been a week late in his life. ...Forgive me. I say that to everyone.
```
Subtitle: Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory driving the first. A week, near enough. He's never been a week late in his life. ...Forgive me. I say that to everyone.

### 8. `dlg.harlan.first.5.wav`

*Where:* dialogue.json harlan/first#5
*Played:* patter, then cracking; doing: his missing nephew; pace: measured; volume: level.
*Wants:* news of Jory
*Note:* As first.4: patter, then the crack on 'He's never six days late.'

```
[patter, then cracking] Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory driving the first. Six days. He's never six days late. ...Forgive me. I say that to everyone.
```
Subtitle: Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory driving the first. Six days. He's never six days late. ...Forgive me. I say that to everyone.

### 9. `dlg.harlan.first.6.wav`

*Where:* dialogue.json harlan/first#6
*Played:* patter, then cracking; doing: his missing nephew; pace: measured; volume: level.
*Wants:* news of Jory
*Note:* As first.4: patter, then the crack on 'He's never five days late.'

```
[patter, then cracking] Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory driving the first. Five days. He's never five days late. ...Forgive me. I say that to everyone.
```
Subtitle: Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You'll have seen my notice. Three wagons, and a boy called Jory driving the first. Five days. He's never five days late. ...Forgive me. I say that to everyone.

### 10. `dlg.harlan.first.7.wav`

*Where:* dialogue.json harlan/first#7
*Played:* patter, hope, then cracking; doing: asks if you saw the wagons; pace: measured; volume: level.
*Wants:* news of Jory
*Note:* Patter; a spark of hope on 'You came up the south road?', answered by himself: 'No. No, of course you didn't.' 'Four days.' a crack.

```
[patter, hope, then cracking] Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You came up the south road? Then you didn't pass three wagons and a boy called Jory. No. No, of course you didn't. Forgive me. Four days. He's never four days late.
```
Subtitle: Harlan Coyle, of the Coyle Company: salt, iron and Morrow cloth, the best on the Old Road. You came up the south road? Then you didn't pass three wagons and a boy called Jory. No. No, of course you didn't. Forgive me. Four days. He's never four days late.

### 11. `dlg.harlan.hub.0.wav`

*Where:* dialogue.json harlan/hub#0
*Played:* joyful, fond; doing: Jory is home; pace: brisk; volume: level.
*Note:* Laughing fondness on 'Pretending!'. Warm 'friend'.

```
[joyful, fond] Jory's round the back, pretending to count crates. Pretending! What can I do for you, friend?
```
Subtitle: Jory's round the back, pretending to count crates. Pretending! What can I do for you, friend?

### 12. `dlg.harlan.hub.1.wav`

*Where:* dialogue.json harlan/hub#1
*Played:* numb grief; doing: Jory is dead; pace: slow; volume: quiet.
*Note:* 'I heard. I heard.' 'They were fed' is Holloway's comfort, and it isn't one. The cold, plainly. The brick is where he breaks. Then hollow kindness.

```
[numb grief, quietly] I heard. I heard. ...They were fed, Holloway says. It was the cold that did it, in those cages, at night. Jory never could get warm of a night. I used to put a hot brick in his bed. You needn't say anything. What do you want?
```
Subtitle: I heard. I heard. ...They were fed, Holloway says. It was the cold that did it, in those cages, at night. Jory never could get warm of a night. I used to put a hot brick in his bed. You needn't say anything. What do you want?

### 13. `dlg.harlan.hub.2.p1.wav`

*Where:* dialogue.json harlan/hub#2; part 2 of 2: narrator: He doesn't get up. / **harlan: Three days of watching that road. I stopped. Somebody has to keep the stock, I told myself…**
*Played:* despair; doing: he's stopped watching; pace: slow; volume: quiet.
*Note:* Narrator: he doesn't get up. Tired self-justification. 'Any word? No. There never is.' answers himself.

```
[despair, quietly] Three days of watching that road. I stopped. Somebody has to keep the stock, I told myself. Any word? No. There never is.
```
Subtitle: Three days of watching that road. I stopped. Somebody has to keep the stock, I told myself. Any word? No. There never is.

### 14. `dlg.harlan.hub.3.p1.wav`

*Where:* dialogue.json harlan/hub#3; part 2 of 2: narrator: He keeps his eyes on the bend in the Old Road while he talks. / **harlan: I keep thinking the lead wagon'll come round there, Jory shouting that he got lost. Any wo…**
*Played:* aching hope; doing: watching the road; pace: measured; volume: quiet.
*Note:* Narrator: eyes on the bend. A fond imagined picture. 'Any word?' quiet.

```
[aching hope, quietly] I keep thinking the lead wagon'll come round there, Jory shouting that he got lost. Any word?
```
Subtitle: I keep thinking the lead wagon'll come round there, Jory shouting that he got lost. Any word?

### 15. `dlg.harlan.hub.4.wav`

*Where:* dialogue.json harlan/hub#4
*Played:* anxious; doing: any news; pace: quick; volume: level.
*Note:* Eager, anxious.

```
[anxious] Any word? Anything at all?
```
Subtitle: Any word? Anything at all?

### 16. `dlg.harlan.what.0.wav`

*Where:* dialogue.json harlan/what#0
*Played:* angry, desperate; doing: offers a reward; pace: quick; volume: level.
*Wants:* Jory home
*Note:* Bitter about the wolves. Businesslike rewards; then the patter drops: 'The boy, I'll pay what you ask.' raw.

```
[angry, desperate] The wolves, that's what. Three caravans this month. A hundred gold to whoever brings Jory home, and another hundred for my goods. Price the salt however you like. The boy, I'll pay what you ask.
```
Subtitle: The wolves, that's what. Three caravans this month. A hundred gold to whoever brings Jory home, and another hundred for my goods. Price the salt however you like. The boy, I'll pay what you ask.

### 17. `dlg.harlan.route.0.wav`

*Where:* dialogue.json harlan/route#0
*Played:* anxious, precise; doing: where the wagons were; pace: measured; volume: level.
*Note:* Facts he has repeated too often. 'Nobody saw them.' deflated.

```
[anxious, precise] The east road. The Old Road, through Thorn-hollow. They should've come through Vonnra's gate at dusk, a week ago now. Holloway had men on the road. Nobody saw them.
```
Subtitle: The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, a week ago now. Holloway had men on the road. Nobody saw them.

### 18. `dlg.harlan.route.1.wav`

*Where:* dialogue.json harlan/route#1
*Played:* anxious, precise; doing: where the wagons were; pace: measured; volume: level.
*Note:* As route.0.

```
[anxious, precise] The east road. The Old Road, through Thorn-hollow. They should've come through Vonnra's gate at dusk, six days back. Holloway had men on the road. Nobody saw them.
```
Subtitle: The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, six days back. Holloway had men on the road. Nobody saw them.

### 19. `dlg.harlan.route.2.wav`

*Where:* dialogue.json harlan/route#2
*Played:* anxious, precise; doing: where the wagons were; pace: measured; volume: level.
*Note:* As route.0.

```
[anxious, precise] The east road. The Old Road, through Thorn-hollow. They should've come through Vonnra's gate at dusk, five days back. Holloway had men on the road. Nobody saw them.
```
Subtitle: The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, five days back. Holloway had men on the road. Nobody saw them.

### 20. `dlg.harlan.route.3.wav`

*Where:* dialogue.json harlan/route#3
*Played:* anxious, precise; doing: where the wagons were; pace: measured; volume: level.
*Note:* As route.0.

```
[anxious, precise] The east road. The Old Road, through Thorn-hollow. They should've come through Vonnra's gate at dusk, four days back. Holloway had men on the road. Nobody saw them.
```
Subtitle: The east road. The Old Road, through Thornhollow. They should've come through Vonnra's gate at dusk, four days back. Holloway had men on the road. Nobody saw them.

### 21. `dlg.harlan.notwolves.0.wav`

*Where:* dialogue.json harlan/notwolves#0
*Played:* shock, then pleading; doing: someone took them; pace: quick; volume: level.
*Hides:* who would want those crates stopped
*Note:* Stunned 'Driven...?'. Breaks off 'Who—'. Then begging: 'Please.' 'Who—' is him starting to guess, and not daring to.

```
[shock, then pleading] Driven...? Wolves don't drive wagons. Who— no. Find out who. Please.
```
Subtitle: Driven...? Wolves don't drive wagons. Who— no. Find out who. Please.

### 22. `dlg.harlan.jory.0.wav`

*Where:* dialogue.json harlan/jory#0
*Played:* overwhelming joy; doing: Jory is alive; pace: quick; volume: raised.
*Note:* 'Alive. Alive!' the second almost a sob. Fumbling coins. Overflowing generosity. 'Don't tell anyone.' laughing.

```
[overwhelming joy, loudly] Alive. Alive! I— here. A hundred, as I said, and that's the least of it. Whatever you need that I can sell you, you pay cost. Cost! Don't tell anyone.
```
Subtitle: Alive. Alive! I— here. A hundred, as I said, and that's the least of it. Whatever you need that I can sell you, you pay cost. Cost! Don't tell anyone.

### 23. `dlg.harlan.box.0.wav`

*Where:* dialogue.json harlan/box#0
*Played:* grateful amazement; doing: you returned the box; pace: quick; volume: level.
*Note:* Honest wonder at honesty. Thanks doubled.

```
[grateful amazement] The strongbox! Unopened. You could've walked off with this and I'd never have known. A hundred gold, and my thanks. And my thanks again.
```
Subtitle: The strongbox! Unopened. You could've walked off with this and I'd never have known. A hundred gold, and my thanks. And my thanks again.

### 24. `dlg.harlan.pell.0.wav`

*Where:* dialogue.json harlan/pell#0
*Played:* betrayed fury; doing: Pell did it; pace: quick; volume: raised.
*Hides:* Pell keeps the books for the Dig trade, and could hang him with them. The fury is on top; the fear is under it, unplayed
*Note:* 'Pell. Pell!' disbelief then fury. Bitter on 'as a friend'. Hot determination at the end.

```
[betrayed fury, loudly] Pell. Pell! We shook hands on this square at midsummer; he offered to buy me out, as a friend. Give me that. Holloway will see it if I have to nail it to his door.
```
Subtitle: Pell. Pell! We shook hands on this square at midsummer; he offered to buy me out, as a friend. Give me that. Holloway will see it if I have to nail it to his door.

### 25. `dlg.harlan.be.0.wav`

*Where:* dialogue.json harlan/be#0
*Played:* guilty, evasive; doing: admits the crates; pace: slow; volume: quiet.
*Wants:* to say as little as possible
*Hides:* the buyer is the Dig, and he has known for two years
*Note:* A long hesitation. 'Six crates.' Justifying himself. 'B.E. Blasting ember.' said like spelling a guilt. Last sentence a weak joke.

```
[guilty, evasive, quietly] ...Six crates. For a buyer I won't name. Paid in advance, in gold, which is why I asked no questions. B. E. Blasting ember. Somebody out there wants to dig a very big hole.
```
Subtitle: ...Six crates. For a buyer I won't name. Paid in advance, in gold, which is why I asked no questions. B. E. Blasting ember. Somebody out there wants to dig a very big hole.

### 26. `dlg.harlan.g.0.wav`

*Where:* dialogue.json harlan/g#0
*Played:* evasive patter; doing: won't name the buyer; pace: quick; volume: level.
*Hides:* the buyer is the Dig, and he has known for two years
*Note:* Too-quick salesman's joke. Changes the subject a beat too fast: 'Is there anything else?'

```
[evasive patter] A customer. Customers have initials, friend; it's how you tell them from friends. Is there anything else? Only I've stock to count.
```
Subtitle: A customer. Customers have initials, friend; it's how you tell them from friends. Is there anything else? Only I've stock to count.

### 27. `dlg.harlan.knew.0.wav`

*Where:* dialogue.json harlan/knew#0
*Played:* protective, then guilt; doing: Jory didn't know; pace: slow; volume: quiet.
*Note:* Fond scorn for Jory. Repeats 'He didn't know.' quieter. Then the confession, barely said: 'I did.'

```
[protective, then guilt, quietly] Jory? Jory knows salt from sugar on a good day. He didn't know. ...He didn't know. I did.
```
Subtitle: Jory? Jory knows salt from sugar on a good day. He didn't know. ...He didn't know. I did.

### 28. `dlg.harlan.betrayed.0.p0.wav`

*Where:* dialogue.json harlan/betrayed#0; part 1 of 3: **harlan: You brought him home. Then you sold my strongbox to a fence for the price of a good horse.** / narrator: He counts a hundred onto the counter, coin by coin, and doesn't push it towards you. / harlan: For the boy. I said I would. Take it, and get away from my stall.
*Played:* hurt, cold dignity; doing: pays you anyway, and sends you off; pace: slow; volume: quiet.
*Note:* First sentence warm with memory; the second cold. Narrator: the coins counted. 'For the boy. I said I would.' dignity. Cold dismissal.

```
[hurt, cold dignity, quietly] You brought him home. Then you sold my strongbox to a fence for the price of a good horse.
```
Subtitle: You brought him home. Then you sold my strongbox to a fence for the price of a good horse.

### 29. `dlg.harlan.betrayed.0.p2.wav`

*Where:* dialogue.json harlan/betrayed#0; part 3 of 3: harlan: You brought him home. Then you sold my strongbox to a fence for the price of a good horse. / narrator: He counts a hundred onto the counter, coin by coin, and doesn't push it towards you. / **harlan: For the boy. I said I would. Take it, and get away from my stall.**
*Played:* hurt, cold dignity; doing: pays you anyway, and sends you off; pace: slow; volume: quiet.
*Note:* First sentence warm with memory; the second cold. Narrator: the coins counted. 'For the boy. I said I would.' dignity. Cold dismissal.

```
[hurt, cold dignity, quietly] For the boy. I said I would. Take it, and get away from my stall.
```
Subtitle: For the boy. I said I would. Take it, and get away from my stall.

### 30. `dlg.harlan.betrayed.1.wav`

*Where:* dialogue.json harlan/betrayed#1
*Played:* cold contempt; doing: you stole the box; pace: slow; volume: quiet.
*Note:* Flat and hurt.

```
[cold contempt, quietly] You. You found it, and you kept it. Get away from my stall.
```
Subtitle: You. You found it, and you kept it. Get away from my stall.

### 31. `dlg.harlan.ash.0.wav`

*Where:* dialogue.json harlan/ash#0
*Played:* devastated; doing: the Roost burned; pace: slow; volume: quiet.
*Note:* Asks, dreading. Stops himself. 'Don't come to the funeral. There's nothing to bury.' breaking.

```
[devastated, quietly] They said there was screaming. Was there screaming? ...They said you could smell it from the wall. No. Don't tell me. Just don't come to my stall again. Don't come to the funeral. There's nothing to bury.
```
Subtitle: They said there was screaming. Was there screaming? ...They said you could smell it from the wall. No. Don't tell me. Just don't come to my stall again. Don't come to the funeral. There's nothing to bury.

### 32. `dlg.harlan.cb_exposed_pell.0.wav`

*Where:* dialogue.json harlan/cb_exposed_pell#0
*Played:* sick betrayal, gratitude; doing: Pell exposed; pace: slow; volume: quiet.
*Note:* Bitter memory of the wine. Pause. 'Thank you. I think. I'll know when I've stopped feeling sick.' the family line, honest and queasy.

```
[sick betrayal, gratitude, quietly] Holloway showed me Pell's book. Payments to "R.", on the night. I sat at that man's table at midsummer and let him pour my wine. ...Thank you. I think. I'll know when I've stopped feeling sick.
```
Subtitle: Holloway showed me Pell's book. Payments to "R.", on the night. I sat at that man's table at midsummer and let him pour my wine. ...Thank you. I think. I'll know when I've stopped feeling sick.

### 33. `dlg.harlan.cb_sold_dig.0.wav`

*Where:* dialogue.json harlan/cb_sold_dig#0
*Played:* wry, complicit; doing: you sold the secret; pace: measured; volume: level.
*Note:* A long beat. 'Well.' Then a rueful confession dressed as agreement.

```
[wry, complicit] Word is you sold Pell what the Dig was doing to the stream, and he sold it on. ...Well. I've sold worse, to worse. Don't look at me like that, friend; I'm agreeing with you.
```
Subtitle: Word is you sold Pell what the Dig was doing to the stream, and he sold it on. ...Well. I've sold worse, to worse. Don't look at me like that, friend; I'm agreeing with you.

### 34. `dlg.harlan.cb_killed_greymuzzle.0.wav`

*Where:* dialogue.json harlan/cb_killed_greymuzzle#0
*Played:* hard, unrepentant; doing: the wolf is dead; pace: measured; volume: level.
*Note:* Fair-minded, then hard: 'I'll not pretend to weep.'

```
[hard, unrepentant] They say the old grey wolf's dead. It wasn't wolves that took my wagons, I know that now. But it was wolves on that road every other night, and I'll not pretend to weep.
```
Subtitle: They say the old grey wolf's dead. It wasn't wolves that took my wagons, I know that now. But it was wolves on that road every other night, and I'll not pretend to weep.

### 35. `dlg.harlan.say_calling.0.wav`

*Where:* dialogue.json harlan/say_calling#0
*Played:* warm, catching on grief; doing: offers work; pace: measured; volume: level.
*Note:* Salesman's warmth; catches on 'if Jory—' and corrects himself.

```
[warm, catching on grief] You've the look of a caravan guard. Good ones are rarer than salt, friend. When this is over, if Jory— when this is over, come and see me about work.
```
Subtitle: You've the look of a caravan guard. Good ones are rarer than salt, friend. When this is over, if Jory— when this is over, come and see me about work.

### 36. `dlg.harlan.say_calling.1.wav`

*Where:* dialogue.json harlan/say_calling#1
*Played:* grim; doing: wants vengeance; pace: measured; volume: level.
*Note:* Hard edge under the warmth.

```
[grim] Big. Good. If you find the men who took my wagons, I'll not ask you to be gentle.
```
Subtitle: Big. Good. If you find the men who took my wagons, I'll not ask you to be gentle.

### 37. `dlg.harlan.say_calling.2.wav`

*Where:* dialogue.json harlan/say_calling#2
*Played:* jovial, then sharp; doing: sizes up a mage; pace: quick; volume: level.
*Note:* Salesman's banter; a bitter edge on 'Then what's it for?'

```
[jovial, then sharp] A mage! There's a thing I've never sold. Can it find a lost wagon? No? Then what's it for?
```
Subtitle: A mage! There's a thing I've never sold. Can it find a lost wagon? No? Then what's it for?

### 38. `dlg.harlan.say_calling.3.wav`

*The same words are also* `dlg.harlan.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json harlan/say_calling#3
*Played:* wistful, apologetic; doing: reminded of Jory; pace: measured; volume: quiet.
*Note:* The association slips out. Apology.

```
[wistful, apologetic, quietly] You've quiet feet. My nephew's somewhere quiet. ...Forgive me. Everything makes me think of him.
```
Subtitle: You've quiet feet. My nephew's somewhere quiet. ...Forgive me. Everything makes me think of him.

### 39. `dlg.harlan.jory_now.0.p0.wav`

*Where:* dialogue.json harlan/jory_now#0; part 1 of 3: **harlan: He asked me what was in the crates. I told him salt.** / narrator: He looks at his hands. / harlan: He didn't believe me. First time in his life. ...That's the worst of it, friend. He always…
*Played:* shame; doing: Jory doesn't believe him now; pace: slow; volume: quiet.
*Note:* Narrator: he looks at his hands. 'First time in his life.' A pause. 'He always did.' broken past tense.

```
[shame, quietly] He asked me what was in the crates. I told him salt.
```
Subtitle: He asked me what was in the crates. I told him salt.

### 40. `dlg.harlan.jory_now.0.p2.wav`

*Where:* dialogue.json harlan/jory_now#0; part 3 of 3: harlan: He asked me what was in the crates. I told him salt. / narrator: He looks at his hands. / **harlan: He didn't believe me. First time in his life. ...That's the worst of it, friend. He always…**
*Played:* shame; doing: Jory doesn't believe him now; pace: slow; volume: quiet.
*Note:* Narrator: he looks at his hands. 'First time in his life.' A pause. 'He always did.' broken past tense.

```
[shame, quietly] He didn't believe me. First time in his life. ...That's the worst of it, friend. He always did.
```
Subtitle: He didn't believe me. First time in his life. ...That's the worst of it, friend. He always did.

### 41. `dlg.harlan.jory_now.1.wav`

*Where:* dialogue.json harlan/jory_now#1
*Played:* fond, guilty; doing: Jory trusts him; pace: measured; volume: quiet.
*Note:* Fond list. Then guilt: 'He believed me; he always does.' The last line self-hatred, quiet.

```
[fond, guilty, quietly] Sleeps with the lamp lit. Eats like a horse. Asked me last night what was in the crates. I told him salt. He believed me; he always does. ...That's the worst of it, friend. He always does.
```
Subtitle: Sleeps with the lamp lit. Eats like a horse. Asked me last night what was in the crates. I told him salt. He believed me; he always does. ...That's the worst of it, friend. He always does.

### 42. `dlg.harlan.t_harlan.0.wav`

*Where:* dialogue.json harlan/t_harlan#0
*Played:* tender memory; doing: how Jory came to him; pace: slow; volume: quiet.
*Hides:* his sister died in the fever year, of the ember sickness, and he sells the stuff anyway; he has never let himself see it, so never play the irony
*Note:* Sad on his sister. A laugh in the voice for 'Do you have a horse?'. 'He named all of them wrong.' fond, wet-eyed.

```
[tender memory, quietly] His mother was my sister. She went with the fever year, and he came to me at eight with a bundle and a cough, and the first thing he ever said to me was "Do you have a horse?" ...I had six. He named all of them wrong.
```
Subtitle: His mother was my sister. She went with the fever year, and he came to me at eight with a bundle and a cough, and the first thing he ever said to me was "Do you have a horse?" ...I had six. He named all of them wrong.

### 43. `dlg.harlan.roost.0.p1.wav`

*Where:* dialogue.json harlan/roost#0; part 2 of 6: narrator: He sits down, which you haven't seen him do. / **harlan: Three. In cages.** / narrator: He's counting something on his fingers, and he stops. / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / narrator: He stops that too. / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* shaken, desperate; doing: Jory may be caged; pace: slow; volume: quiet.
*Wants:* Jory out
*Note:* Narrator: he sits. 'Three. In cages.' numb. Narrator: counting, stops. The description of Jory loving and frightened; narrator: he stops. Then fierce: 'Get him out.'

```
[shaken, desperate, quietly] Three. In cages.
```
Subtitle: Three. In cages.

### 44. `dlg.harlan.roost.0.p3.wav`

*Where:* dialogue.json harlan/roost#0; part 4 of 6: narrator: He sits down, which you haven't seen him do. / harlan: Three. In cages. / narrator: He's counting something on his fingers, and he stops. / **harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him—** / narrator: He stops that too. / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* shaken, desperate; doing: Jory may be caged; pace: slow; volume: quiet.
*Wants:* Jory out
*Note:* Narrator: he sits. 'Three. In cages.' numb. Narrator: counting, stops. The description of Jory loving and frightened; narrator: he stops. Then fierce: 'Get him out.'

```
[shaken, desperate, quietly] Is one of them young? Fair, freckled, a mouth on him that'll get him—
```
Subtitle: Is one of them young? Fair, freckled, a mouth on him that'll get him—

### 45. `dlg.harlan.roost.0.p5.wav`

*Where:* dialogue.json harlan/roost#0; part 6 of 6: narrator: He sits down, which you haven't seen him do. / harlan: Three. In cages. / narrator: He's counting something on his fingers, and he stops. / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / narrator: He stops that too. / **harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.**
*Played:* shaken, desperate; doing: Jory may be caged; pace: slow; volume: quiet.
*Wants:* Jory out
*Note:* Narrator: he sits. 'Three. In cages.' numb. Narrator: counting, stops. The description of Jory loving and frightened; narrator: he stops. Then fierce: 'Get him out.'

```
[shaken, desperate, quietly] Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
```
Subtitle: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.

### 46. `dlg.harlan.ledger_early.0.p1.wav`

*Where:* dialogue.json harlan/ledger_early#0; part 2 of 4: narrator: He reads, and his finger stops on a line. / **harlan: That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's…** / narrator: He looks up. / harlan: For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holl…
*Played:* shock, fury restrained; doing: the ledger shows the night; pace: measured; volume: quiet.
*Note:* Narrator: his finger stops. 'That's the night.' twice, the second hollow. Reading. Narrator: he looks up. Questions. Then pleading; the last line a frightening honesty. 'If I knew, I'd do something I'd hang for.' plain, a man stating a fact about himself.

```
[shock, fury restrained, quietly] That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's Vonnra's clerk. "For the road."
```
Subtitle: That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's Vonnra's clerk. "For the road."

### 47. `dlg.harlan.ledger_early.0.p3.wav`

*Where:* dialogue.json harlan/ledger_early#0; part 4 of 4: narrator: He reads, and his finger stops on a line. / harlan: That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's… / narrator: He looks up. / **harlan: For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holl…**
*Played:* shock, fury restrained; doing: the ledger shows the night; pace: measured; volume: quiet.
*Note:* Narrator: his finger stops. 'That's the night.' twice, the second hollow. Reading. Narrator: he looks up. Questions. Then pleading; the last line a frightening honesty. 'If I knew, I'd do something I'd hang for.' plain, a man stating a fact about himself.

```
[shock, fury restrained, quietly] For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holloway, not to me. If I knew, I'd do something I'd hang for.
```
Subtitle: For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holloway, not to me. If I knew, I'd do something I'd hang for.

### 48. `dlg.harlan.crates.0.p1.wav`

*Where:* dialogue.json harlan/crates#0; part 2 of 4: narrator: His face does what it does whenever anyone says those two letters. / **harlan: ...Are they. With the bandit.** / narrator: He's already reaching for paper. / harlan: Thank you, friend. Leave that with me. Paid for is paid for.
*Played:* uneasy, then too brisk; doing: the crates; pace: measured; volume: quiet.
*Wants:* the crates delivered, because the Dig has paid
*Hides:* that he means to send them on
*Note:* Narrator for his face. '...Are they.' Narrator: reaching for paper. Thanks a beat too quick. 'Paid for is paid for.' businesslike cover.

```
[uneasy, then too brisk, quietly] ...Are they. With the bandit.
```
Subtitle: ...Are they. With the bandit.

### 49. `dlg.harlan.crates.0.p3.wav`

*Where:* dialogue.json harlan/crates#0; part 4 of 4: narrator: His face does what it does whenever anyone says those two letters. / harlan: ...Are they. With the bandit. / narrator: He's already reaching for paper. / **harlan: Thank you, friend. Leave that with me. Paid for is paid for.**
*Played:* uneasy, then too brisk; doing: the crates; pace: measured; volume: quiet.
*Wants:* the crates delivered, because the Dig has paid
*Hides:* that he means to send them on
*Note:* Narrator for his face. '...Are they.' Narrator: reaching for paper. Thanks a beat too quick. 'Paid for is paid for.' businesslike cover.

```
[uneasy, then too brisk, quietly] Thank you, friend. Leave that with me. Paid for is paid for.
```
Subtitle: Thank you, friend. Leave that with me. Paid for is paid for.

### 50. `dlg.harlan.be_dig.0.p1.wav`

*Where:* dialogue.json harlan/be_dig#0; part 2 of 2: narrator: He takes a long time to answer. / **harlan: I sell salt to people who salt things. I sell iron to people who hit things. I don't ask t…**
*Played:* defensive guilt; doing: justifies selling to the Dig; pace: slow; volume: quiet.
*Hides:* the buyer is the Dig, and he has known for two years
*Note:* Narrator: a long time. A salesman's creed, recited. Then the subject changes a beat too fast.

```
[defensive guilt, quietly] I sell salt to people who salt things. I sell iron to people who hit things. I don't ask the salt what it's for, friend. ...Is there anything else? Only I've stock to count.
```
Subtitle: I sell salt to people who salt things. I sell iron to people who hit things. I don't ask the salt what it's for, friend. ...Is there anything else? Only I've stock to count.

### 51. `dlg.harlan.cb_jory_knows.0.p1.wav`

*Where:* dialogue.json harlan/cb_jory_knows#0; part 2 of 2: narrator: He doesn't say good morning. / **harlan: He knows. You told him. ...I'd have told him myself. One day. When it didn't matter any mo…**
*Played:* hurt, ashamed; doing: you told Jory; pace: slow; volume: quiet.
*Note:* Narrator: no good morning. 'He knows. You told him.' flat. Then a weak excuse, ashamed.

```
[hurt, ashamed, quietly] He knows. You told him. ...I'd have told him myself. One day. When it didn't matter any more.
```
Subtitle: He knows. You told him. ...I'd have told him myself. One day. When it didn't matter any more.

## Said in passing

### 52. `bark.harlan.day.0.wav`

*Where:* npcs.json harlan.barks[0]
*Played:* patter; pace: brisk; volume: raised.

```
[patter, loudly] Salt and iron, friend. Good honest salt.
```
Subtitle: Salt and iron, friend. Good honest salt.

### 53. `bark.harlan.night.0.wav`

*Where:* npcs.json harlan.nightBarks[0]
*Played:* tired; pace: measured; volume: quiet.

```
[tired, quietly] I keep the books by candlelight. Helps me not think.
```
Subtitle: I keep the books by candlelight. Helps me not think.

### 54. `bark.harlan.said.0.wav`

*Where:* npcs.json harlan.said[0]
*Played:* worried; doing: Jory is late; pace: measured; volume: level.
*Note:* Trying to sound unworried and failing.

```
[worried] Late. Jory's never late.
```
Subtitle: Late. Jory's never late.

### 55. `bark.harlan.said.1.wav`

*Where:* npcs.json harlan.said[1]
*Played:* merchant's patter; doing: trade; pace: brisk; volume: level.
*Note:* Habit, a shopkeeper's call.

```
[merchant's patter] Salt, iron, cloth. Whatever you need, when the wagons come.
```
Subtitle: Salt, iron, cloth. Whatever you need, when the wagons come.

### 56. `bark.harlan.said.2.wav`

*Where:* npcs.json harlan.said[2]
*Played:* suspicious, bitter; doing: someone knows about the caravan; pace: measured; volume: quiet.
*Note:* Muttered.

```
[suspicious, bitter, quietly] Somebody knows something.
```
Subtitle: Somebody knows something.

### 57. `bark.harlan.said.3.wav`

*Where:* npcs.json harlan.said[3]
*Played:* haunted; doing: every wagon might be Jory's; pace: slow; volume: quiet.
*Note:* To himself.

```
[haunted, quietly] Every wagon on that road's his, in the dark.
```
Subtitle: Every wagon on that road's his, in the dark.

### 58. `bark.harlan.said.4.wav`

*Where:* npcs.json harlan.said[4]
*Played:* exhausted, stubborn; doing: he won't sleep; pace: slow; volume: quiet.
*Note:* 'Won't.' a small defiance.

```
[exhausted, stubborn, quietly] Can't sleep. Won't.
```
Subtitle: Can't sleep. Won't.

### 59. `bark.harlan.said.5.wav`

*Where:* npcs.json harlan.said[5]
*Played:* grief, fond; doing: Jory and the dark; pace: slow; volume: quiet.
*Note:* Fond memory with the fear under it.

```
[grief, fond, quietly] Jory hated the dark. Hated it. Slept with a candle till he was fourteen.
```
Subtitle: Jory hated the dark. Hated it. Slept with a candle till he was fourteen.

### 60. `bark.harlan.said.6.wav`

*Where:* npcs.json harlan.said[6]
*Played:* relief, tender; doing: Jory is home; pace: measured; volume: quiet.
*Note:* 'I keep going to look.' a happy confession.

```
[relief, tender, quietly] Jory's asleep in Rook's good room. I keep going to look.
```
Subtitle: Jory's asleep in Rook's good room. I keep going to look.

### 61. `bark.harlan.said.7.wav`

*Where:* npcs.json harlan.said[7]
*Played:* quiet, wry; doing: the lamp; pace: measured; volume: quiet.
*Note:* 'So do I, now.' a small admission.

```
[quiet, wry, quietly] He sleeps with the lamp lit. So do I, now.
```
Subtitle: He sleeps with the lamp lit. So do I, now.

### 62. `bark.harlan.said.8.wav`

*Where:* npcs.json harlan.said[8]
*Played:* grief; doing: the sign that won't be made; pace: slow; volume: quiet.
*Note:* He breaks off on the second 'Coyle and'; the cut is the line.

```
[grief, quietly] Coyle and Nephew, the new sign was going to say. Coyle and—
```
Subtitle: Coyle and Nephew, the new sign was going to say. Coyle and—

### 63. `bark.harlan.said.9.wav`

*Where:* npcs.json harlan.said[9]
*Played:* amused, proud; doing: Jory calls him Mister Coyle; pace: measured; volume: level.
*Note:* Mock outrage, delighted underneath.

```
[amused, proud] Mister Coyle, he calls me. In my own shop.
```
Subtitle: Mister Coyle, he calls me. In my own shop.


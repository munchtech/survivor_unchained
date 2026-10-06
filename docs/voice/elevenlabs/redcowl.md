# Redcowl: ElevenLabs packet

Voice id in the game: `redcowl`. 45 takes to record (4,339 characters; about 13,017 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Redcowl** (the Kerchiefs). A big chest voice that laughs before it threatens ("Ha! HA."), and goes cold on a turn. "Lad" or "lass" as the survivor is (write both variants), "my lot". Talks about feeding people the way other chiefs talk about gold. Never says please; never says the name Ashford, and never lets anyone else say it twice. *Casting:* 40s, hard Scots.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Redcowl`. Never describe a voice as sounding like a real person.

```
Native English (British, Scottish). Male, 40s. Studio quality. Persona: a bandit chief. A big, burly bandit chief in his forties with a deep, booming chest voice and a hard, broad Scottish accent. He laughs loud and easy, then turns cold and dangerous in the same breath. Commanding and rough. Broad Scottish accent. No reverb or effects.
```

Preview text:

```
Ha! Look at the colours on you. You're standing in my Roost, and my lot are hungry, and nobody here has ever been hungry for long. Talk.
```

In the Voice Library instead: search for *hard Scots*, *male*, *40*, and listen for this: A big, burly bandit chief in his forties with a deep, booming chest voice and a hard, broad Scottish accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_raid_on_the_roost.bairns.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice redcowl
```

## Saying the names

The text to paste already respells these; keep the respelling: Redcowl as *Red-cowl*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: raid on the roost

### 1. `dlg.cin_raid_on_the_roost.bairns.0.wav`

*Where:* dialogue.json cin_raid_on_the_roost/bairns#0
*Played:* laughing menace; doing: you came at night; pace: measured; volume: raised.
*Note:* 'Ha! HA.' then cold: the bairns. 'Mind where you swing.' a grim joke.

```
[laughing menace, loudly] Ha! HA. At night, lass. With my bairns asleep behind me. ...Mind where you swing.
```
Subtitle: Ha! HA. At night, lass. With my bairns asleep behind me. ...Mind where you swing.

### 2. `dlg.cin_raid_on_the_roost.bairns.1.wav`

*Where:* dialogue.json cin_raid_on_the_roost/bairns#1
*Played:* laughing menace; doing: you came at night; pace: measured; volume: raised.
*Note:* As bairns.0.

```
[laughing menace, loudly] Ha! HA. At night, lad. With my bairns asleep behind me. ...Mind where you swing.
```
Subtitle: Ha! HA. At night, lad. With my bairns asleep behind me. ...Mind where you swing.

### 3. `dlg.cin_raid_on_the_roost.last.0.wav`

*Where:* dialogue.json cin_raid_on_the_roost/last#0
*Played:* dying, bitter amusement; doing: he says Ashford; pace: slow; volume: quiet.
*Note:* Breath failing. Narrator: a laugh. 'Now we've both said it.'

```
[dying, bitter amusement, quietly] ...Ashford. [laughs] There. Now we've both said it.
```
Subtitle: ...Ashford. There. Now we've both said it.

### 4. `dlg.cin_raid_on_the_roost.last.1.wav`

*Where:* dialogue.json cin_raid_on_the_roost/last#1
*Played:* dying, tender; doing: a message for Rav; pace: very slow; volume: hushed.
*Note:* Barely voiced; the leg held.

```
[dying, tender, whispers] Tell the saw-bones... the leg held.
```
Subtitle: Tell the saw-bones... the leg held.

### 5. `dlg.cin_raid_on_the_roost.spared.0.wav`

*Where:* dialogue.json cin_raid_on_the_roost/spared#0

```
[a laugh, and it costs him] Ha! ...You said a word in my camp once, and I let you. Now you've let me. That's us square, lass. ...Near enough.
```
Subtitle: Ha! ...You said a word in my camp once, and I let you. Now you've let me. That's us square, lass. ...Near enough.

### 6. `dlg.cin_raid_on_the_roost.spared.1.wav`

*Where:* dialogue.json cin_raid_on_the_roost/spared#1

```
[a laugh, and it costs him] Ha! ...You said a word in my camp once, and I let you. Now you've let me. That's us square, lad. ...Near enough.
```
Subtitle: Ha! ...You said a word in my camp once, and I let you. Now you've let me. That's us square, lad. ...Near enough.

### 7. `dlg.cin_raid_on_the_roost.spared.2.wav`

*Where:* dialogue.json cin_raid_on_the_roost/spared#2

```
[a laugh, and it costs him] Ha! ...You minded where you swung. That's two I owe, then, lass. The saw-bones a leg, and you the rest of me.
```
Subtitle: Ha! ...You minded where you swung. That's two I owe, then, lass. The saw-bones a leg, and you the rest of me.

### 8. `dlg.cin_raid_on_the_roost.spared.3.wav`

*Where:* dialogue.json cin_raid_on_the_roost/spared#3

```
[a laugh, and it costs him] Ha! ...You minded where you swung. That's two I owe, then, lad. The saw-bones a leg, and you the rest of me.
```
Subtitle: Ha! ...You minded where you swung. That's two I owe, then, lad. The saw-bones a leg, and you the rest of me.

### 9. `dlg.cin_raid_on_the_roost.flit.0.wav`

*Where:* dialogue.json cin_raid_on_the_roost/flit#0

```
[cold, to her] We'll be off your road by light. [to the camp, the big voice back] Up, my lot! Boots on! We're flitting!
```
Subtitle: We'll be off your road by light. Up, my lot! Boots on! We're flitting!

## Conversations: Redcowl

### 10. `dlg.redcowl.first.0.p1.wav`

*Where:* dialogue.json redcowl/first#0; part 2 of 2: narrator: Every crossbow in the camp is on you, and nobody's laughing. / **redcowl: You're the one who's been putting my lads in the ground. Redcowl. Talk, and talk slow.**
*Played:* cold menace; doing: faces the killer of his men; pace: slow; volume: level.
*Wants:* a reason not to kill you
*Note:* Narrator: every crossbow, nobody laughing. No laugh in him either; big voice held low and cold. 'Talk, and talk slow.' a promise.

```
[cold menace] You're the one who's been putting my lads in the ground. Red-cowl. Talk, and talk slow.
```
Subtitle: You're the one who's been putting my lads in the ground. Redcowl. Talk, and talk slow.

### 11. `dlg.redcowl.first.1.wav`

*Where:* dialogue.json redcowl/first#1
*Played:* amused suspicion; doing: sizes up the red-wearer; pace: measured; volume: level.
*Note:* Big, amused. 'daft' Scots. Then cold on 'You're standing in my Roost. Talk.'

```
[amused suspicion] Look at the colours on you. You're not one of mine, and you're not daft enough to be one of Holloway's. Red-cowl. You're standing in my Roost. Talk.
```
Subtitle: Look at the colours on you. You're not one of mine, and you're not daft enough to be one of Holloway's. Redcowl. You're standing in my Roost. Talk.

### 12. `dlg.redcowl.first.2.wav`

*Where:* dialogue.json redcowl/first#2
*Played:* wary humour, threat; doing: warns a mage; pace: measured; volume: level.
*Note:* A laugh in the story about the tent; the order to talk hard.

```
[wary humour, threat] Keep your hands where I can see them, and keep them cold. I've bairns asleep in this camp, and they've had enough fire for one life. Red-cowl. You're in my camp. Talk.
```
Subtitle: Keep your hands where I can see them, and keep them cold. I've bairns asleep in this camp, and they've had enough fire for one life. Redcowl. You're in my camp. Talk.

### 13. `dlg.redcowl.first.3.wav`

*Where:* dialogue.json redcowl/first#3
*Played:* boisterous, then warning; doing: admires a big fighter; pace: measured; volume: raised.
*Note:* 'Ha!' booming. Admiring. The warning lands with a grin. Then cold: 'Talk.'

```
[boisterous, then warning, loudly] Ha! Look at the size of you. I've a dozen lads would follow you for the fun of it; don't make me find out which dozen. Red-cowl. You're in my camp. Talk.
```
Subtitle: Ha! Look at the size of you. I've a dozen lads would follow you for the fun of it; don't make me find out which dozen. Redcowl. You're in my camp. Talk.

### 14. `dlg.redcowl.first.4.wav`

*Where:* dialogue.json redcowl/first#4
*Played:* rough humour, protective threat; doing: a woman in his camp; pace: measured; volume: level.
*Note:* Coarse joke about his lads. A hard edge on 'where I've told them'. Then 'Talk.'

```
[rough humour, protective threat] Red-cowl. You're standing in my camp, which means my sentries are drunk or you're interesting. Which is it?
```
Subtitle: Redcowl. You're standing in my camp, which means my sentries are drunk or you're interesting. Which is it?

### 15. `dlg.redcowl.hub.0.wav`

*Where:* dialogue.json redcowl/hub#0
*Played:* gruff amusement; doing: still here; pace: measured; volume: level.
*Note:* 'Ha.' short.

```
[gruff amusement] Still here? Ha. Talk, then.
```
Subtitle: Still here? Ha. Talk, then.

### 16. `dlg.redcowl.who.0.wav`

*Where:* dialogue.json redcowl/who#0
*Played:* pride, then bitterness, then cover; doing: his people; pace: measured; volume: level.
*Note:* 'Mine.' proud. Then bitter, slower, about the Watch counting boots. Catches himself: a big laugh, 'Listen to me.' Then hard: 'Talk.'

```
[pride, then bitterness, then cover] Mine. Forty-one mouths, and a dozen of them can hold a blade. The rest are what's left when a town goes into the ground and the Watch writes it down and goes home. ...Ha! Listen to me. Talk or bleed, I said. Talk.
```
Subtitle: Mine. Forty-one mouths, and a dozen of them can hold a blade. The rest are what's left when a town goes into the ground and the Watch writes it down and goes home. ...Ha! Listen to me. Talk or bleed, I said. Talk.

### 17. `dlg.redcowl.rav.0.wav`

*Where:* dialogue.json redcowl/rav#0
*Played:* roaring laughter, then business; doing: the password works; pace: measured; volume: raised.
*Note:* 'Ha! HA.' a real belly laugh. Fond grumble about Rav. Then a grin: 'So: talk.'

```
[roaring laughter, then business, loudly] Ha! HA. That old saw-bones. He does too, and he knows it. All right. Rav's friends get to talk before they get shot. So: talk.
```
Subtitle: Ha! HA. That old saw-bones. He does too, and he knows it. All right. Rav's friends get to talk before they get shot. So: talk.

### 18. `dlg.redcowl.goods.0.wav`

*Where:* dialogue.json redcowl/goods#0
*Played:* businesslike, cheerful; doing: names his price; pace: measured; volume: level.
*Note:* A bandit's merchant; a joke about the teamsters' appetite.

```
[businesslike, cheerful] The wagons are salvage, and salvage is mine. You want the strongbox, you buy it. A hundred gold and I'll throw in the teamsters, since they eat more than they're worth.
```
Subtitle: The wagons are salvage, and salvage is mine. You want the strongbox, you buy it. A hundred gold and I'll throw in the teamsters, since they eat more than they're worth.

### 19. `dlg.redcowl.deal.0.wav`

*Where:* dialogue.json redcowl/deal#0
*Played:* satisfied, then warning; doing: deal done; pace: measured; volume: level.
*Note:* 'Pleasure.' Directions. 'And' then a beat where the name would be: the warning lowered.

```
[satisfied, then warning] Pleasure. Box is by the tents; the teamsters are in the cages. Open them yourself; my lads won't stop you. And if Holloway asks, you've never seen my face.
```
Subtitle: Pleasure. Box is by the tents; the teamsters are in the cages. Open them yourself; my lads won't stop you. And if Holloway asks, you've never seen my face.

### 20. `dlg.redcowl.favour.0.wav`

*Where:* dialogue.json redcowl/favour#0
*Played:* grudging; doing: a favour for a favour; pace: measured; volume: level.
*Note:* 'Is it, now.' sceptical. Admits the howling. 'Fine.' 'for a friend' with a grin.

```
[grudging] Is it, now. The howling's been keeping my lot up nights, I'll admit. ...Fine. The teamsters, for the favour. The box you still pay for. Fifty, for a friend.
```
Subtitle: Is it, now. The howling's been keeping my lot up nights, I'll admit. ...Fine. The teamsters, for the favour. The box you still pay for. Fifty, for a friend.

### 21. `dlg.redcowl.prisoners.0.wav`

*Where:* dialogue.json redcowl/prisoners#0
*Played:* dry, mocking; doing: names the price; pace: measured; volume: level.
*Note:* Mock-complaint about their praying.

```
[dry, mocking] The teamsters? They eat my food and pray a great deal. Fifty for their keep and they're yours.
```
Subtitle: The teamsters? They eat my food and pray a great deal. Fifty for their keep and they're yours.

### 22. `dlg.redcowl.released.0.wav`

*Where:* dialogue.json redcowl/released#0
*Played:* amused; doing: go ahead; pace: measured; volume: level.
*Note:* 'he bites' a joke.

```
[amused] Cages are over there. Mind the one on the end; he bites.
```
Subtitle: Cages are over there. Mind the one on the end; he bites.

### 23. `dlg.redcowl.pell.0.wav`

*Where:* dialogue.json redcowl/pell#0
*Played:* rising fury; doing: Pell sold him out; pace: quick; volume: raised.
*Note:* Snatching the book. Reading, building. 'After!' a roar. Cuts himself off mid-insult. Then cold resolve: business in the Waystation.

```
[rising fury, loudly] ...Give me that. "R., for the Coyle job." And to the clerk. And— "tell Holloway where they camp, after." After! Varrow, you soft-handed little— Take your wagons. Take your teamsters. I've business in the Waystation.
```
Subtitle: ...Give me that. "R., for the Coyle job." And to the clerk. And— "tell Holloway where they camp, after." After! Varrow, you soft-handed little— Take your wagons. Take your teamsters. I've business in the Waystation.

### 24. `dlg.redcowl.trick.0.p0.wav`

*Where:* dialogue.json redcowl/trick#0; part 1 of 3: **redcowl: The Watch. Holloway hasn't got the men to—** / narrator: A whistle from the ridge. The whole camp stops. / redcowl: —PACK IT UP! PACK IT UP! Leave the heavy stuff!
*Played:* scorn, then panic; doing: the Watch is coming; pace: quick; volume: shout.
*Note:* Scornful start, cut off by the narrator: the whistle, the camp stops. Then bellowing orders: 'PACK IT UP! PACK IT UP!'

```
[scorn, then panic, shouting] The Watch. Holloway hasn't got the men to—
```
Subtitle: The Watch. Holloway hasn't got the men to—

### 25. `dlg.redcowl.trick.0.p2.wav`

*Where:* dialogue.json redcowl/trick#0; part 3 of 3: redcowl: The Watch. Holloway hasn't got the men to— / narrator: A whistle from the ridge. The whole camp stops. / **redcowl: —PACK IT UP! PACK IT UP! Leave the heavy stuff!**
*Played:* scorn, then panic; doing: the Watch is coming; pace: quick; volume: shout.
*Note:* Scornful start, cut off by the narrator: the whistle, the camp stops. Then bellowing orders: 'PACK IT UP! PACK IT UP!'

```
[scorn, then panic, shouting] —PACK IT UP! PACK IT UP! Leave the heavy stuff!
```
Subtitle: —PACK IT UP! PACK IT UP! Leave the heavy stuff!

### 26. `dlg.redcowl.cages.0.wav`

*Where:* dialogue.json redcowl/cages#0
*Played:* hard logic, then hurt; doing: why the cages; pace: measured; volume: level.
*Note:* A hard man's arithmetic. 'worth-nothings' bitter, 'lass'. A pause; then defensive, almost wounded: 'I feed them before I feed my own.'

```
[hard logic, then hurt] Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. I've buried enough worth-nothings for one life, lass. ...Ask them if they're hungry.
```
Subtitle: Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. I've buried enough worth-nothings for one life, lass. ...Ask them if they're hungry.

### 27. `dlg.redcowl.cages.1.wav`

*Where:* dialogue.json redcowl/cages#1
*Played:* hard logic, then hurt; doing: why the cages; pace: measured; volume: level.
*Note:* As cages.0, with 'lad'.

```
[hard logic, then hurt] Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. I've buried enough worth-nothings for one life, lad. ...Ask them if they're hungry.
```
Subtitle: Because a man in a cage is worth something to somebody, and a man in a ditch is worth nothing to anybody. I've buried enough worth-nothings for one life, lad. ...Ask them if they're hungry.

### 28. `dlg.redcowl.wagons.0.wav`

*Where:* dialogue.json redcowl/wagons#0
*Played:* mocking; doing: salvage; pace: measured; volume: level.
*Note:* 'Ha!' Mockery of Coyle's painted boards. 'The road knows now.' a grin.

```
[mocking] Ha! Salvage, is what they are. Some merchant up at the Waystation painted his name on every board of them, so the road'd know who to thank. Coyle. The road knows now. ...You'll be wanting them. Everyone does, once they've seen them.
```
Subtitle: Ha! Salvage, is what they are. Some merchant up at the Waystation painted his name on every board of them, so the road'd know who to thank. Coyle. The road knows now. ...You'll be wanting them. Everyone does, once they've seen them.

### 29. `dlg.redcowl.crates.0.wav`

*Where:* dialogue.json redcowl/crates#0
*Played:* comic, uneasy; doing: the crates; pace: measured; volume: level.
*Note:* A camp story, comic, with real fear under it: 'listened to it think about it.'

```
[comic, uneasy] Salvage. Heavy salvage. My lads were using them for seats, till one of them dropped one and we all stood very still and listened to it think about it.
```
Subtitle: Salvage. Heavy salvage. My lads were using them for seats, till one of them dropped one and we all stood very still and listened to it think about it.

### 30. `dlg.redcowl.crates_dig.0.p1.wav`

*Where:* dialogue.json redcowl/crates_dig#0; part 2 of 4: narrator: He doesn't laugh. / **redcowl: The hill.** / narrator: He looks north-east, past the ravine wall, at nothing you can see. / redcowl: The one that's been knocking at night. ...How deep are they going?
*Played:* sudden gravity; doing: the crates are for the hill; pace: slow; volume: quiet.
*Note:* Narrator: he doesn't laugh, he looks north-east. 'The hill.' quiet. 'The one that's been knocking at night.' A pause. The question low and serious.

```
[sudden gravity, quietly] The hill.
```
Subtitle: The hill.

### 31. `dlg.redcowl.crates_dig.0.p3.wav`

*Where:* dialogue.json redcowl/crates_dig#0; part 4 of 4: narrator: He doesn't laugh. / redcowl: The hill. / narrator: He looks north-east, past the ravine wall, at nothing you can see. / **redcowl: The one that's been knocking at night. ...How deep are they going?**
*Played:* sudden gravity; doing: the crates are for the hill; pace: slow; volume: quiet.
*Note:* Narrator: he doesn't laugh, he looks north-east. 'The hill.' quiet. 'The one that's been knocking at night.' A pause. The question low and serious.

```
[sudden gravity, quietly] The one that's been knocking at night. ...How deep are they going?
```
Subtitle: The one that's been knocking at night. ...How deep are they going?

### 32. `dlg.redcowl.crates_keep.0.p0.wav`

*Where:* dialogue.json redcowl/crates_keep#0; part 1 of 3: **redcowl: Then nobody's having them. Not the hole in the hill. Not Holloway. Not your merchant, and …** / narrator: A laugh, but not the big one. / redcowl: Guarding crates. My mother'd laugh herself sick.
*Played:* grim resolve, rueful; doing: he'll guard them; pace: measured; volume: level.
*Note:* A list of refusals, each harder. 'They stay with me.' Narrator: a smaller laugh. 'My mother'd laugh herself sick.' wry, a little sad.

```
[grim resolve, rueful] Then nobody's having them. Not the hole in the hill. Not Holloway. Not your merchant, and not the soft-handed little man that sold them twice. They stay with me.
```
Subtitle: Then nobody's having them. Not the hole in the hill. Not Holloway. Not your merchant, and not the soft-handed little man that sold them twice. They stay with me.

### 33. `dlg.redcowl.crates_keep.0.p2.wav`

*Where:* dialogue.json redcowl/crates_keep#0; part 3 of 3: redcowl: Then nobody's having them. Not the hole in the hill. Not Holloway. Not your merchant, and … / narrator: A laugh, but not the big one. / **redcowl: Guarding crates. My mother'd laugh herself sick.**
*Played:* grim resolve, rueful; doing: he'll guard them; pace: measured; volume: level.
*Note:* A list of refusals, each harder. 'They stay with me.' Narrator: a smaller laugh. 'My mother'd laugh herself sick.' wry, a little sad.

```
[grim resolve, rueful] Guarding crates. My mother'd laugh herself sick.
```
Subtitle: Guarding crates. My mother'd laugh herself sick.

### 34. `dlg.redcowl.crates_charge.0.p1.wav`

*Where:* dialogue.json redcowl/crates_charge#0; part 2 of 2: narrator: He looks at you a long while. Then he whistles, and a lad brings one over, walking like he… / **redcowl: Take it. Put it where it'll do the most harm to the right people. And run.**
*Played:* grave trust; doing: gives you a charge; pace: slow; volume: quiet.
*Note:* Narrator for the long look, the whistle, the lad. Low instruction. 'And' then a beat where the name would be. 'run.' plain.

```
[grave trust, quietly] Take it. Put it where it'll do the most harm to the right people. And run.
```
Subtitle: Take it. Put it where it'll do the most harm to the right people. And run.

### 35. `dlg.redcowl.birds.0.p0.wav`

*The same words are also* `dlg.redcowl.birds.1.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json redcowl/birds#0; part 1 of 3: **redcowl: Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober.** / narrator: The laugh stops. / redcowl: Birds don't have names, lass. Not in my camp.
*Played:* jovial, then cold; doing: won't name the informer; pace: measured; volume: level.
*Note:* Fond riddle about the little bird (his brother). Narrator: the laugh stops. Cold and final, 'lass'.

```
[jovial, then cold] Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober.
```
Subtitle: Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober.

### 36. `dlg.redcowl.birds.0.p2.wav`

*Where:* dialogue.json redcowl/birds#0; part 3 of 3: redcowl: Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober. / narrator: The laugh stops. / **redcowl: Birds don't have names, lass. Not in my camp.**
*Played:* jovial, then cold; doing: won't name the informer; pace: measured; volume: level.
*Note:* Fond riddle about the little bird (his brother). Narrator: the laugh stops. Cold and final, 'lass'.

```
[jovial, then cold] Birds don't have names, lass. Not in my camp.
```
Subtitle: Birds don't have names, lass. Not in my camp.

### 37. `dlg.redcowl.birds.1.p2.wav`

*Where:* dialogue.json redcowl/birds#1; part 3 of 3: redcowl: Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober. / narrator: The laugh stops. / **redcowl: Birds don't have names, lad. Not in my camp.**
*Played:* jovial, then cold; doing: won't name the informer; pace: measured; volume: level.
*Note:* As birds.0, with 'lad'.

```
[jovial, then cold] Birds don't have names, lad. Not in my camp.
```
Subtitle: Birds don't have names, lad. Not in my camp.

### 38. `dlg.redcowl.ashford.0.p1.wav`

*Where:* dialogue.json redcowl/ashford#0; part 2 of 2: narrator: The laugh goes out of him like a lamp. / **redcowl: Don't. You get to say that once in my camp. You've said it.**
*Played:* cold, dangerous grief; doing: never say that name; pace: slow; volume: quiet.
*Note:* Narrator: the laugh goes out of him. 'Don't.' Narrator: quiet. The warning, very quiet and very dangerous.

```
[cold, dangerous grief, quietly] Don't. [quietly] You get to say that once in my camp. You've said it.
```
Subtitle: Don't. You get to say that once in my camp. You've said it.

### 39. `dlg.redcowl.pell_given.0.p0.wav`

*Where:* dialogue.json redcowl/pell_given#0; part 1 of 3: **redcowl: Ha! Somebody who knows where the rats sleep.** / narrator: He's already shouting for boots. / redcowl: Go home. Stay off the square tonight.
*Played:* gleeful vengeance; doing: now he knows where Pell sleeps; pace: quick; volume: raised.
*Note:* 'Ha!' Narrator: shouting for boots. A beat where the name would be. A half-friendly warning.

```
[gleeful vengeance, loudly] Ha! Somebody who knows where the rats sleep.
```
Subtitle: Ha! Somebody who knows where the rats sleep.

### 40. `dlg.redcowl.pell_given.0.p2.wav`

*Where:* dialogue.json redcowl/pell_given#0; part 3 of 3: redcowl: Ha! Somebody who knows where the rats sleep. / narrator: He's already shouting for boots. / **redcowl: Go home. Stay off the square tonight.**
*Played:* gleeful vengeance; doing: now he knows where Pell sleeps; pace: quick; volume: raised.
*Note:* 'Ha!' Narrator: shouting for boots. A beat where the name would be. A half-friendly warning.

```
[gleeful vengeance, loudly] Go home. Stay off the square tonight.
```
Subtitle: Go home. Stay off the square tonight.

### 41. `dlg.redcowl.pell_hunt.0.wav`

*Where:* dialogue.json redcowl/pell_hunt#0
*Played:* cold certainty; doing: he'll find Pell; pace: measured; volume: level.
*Note:* Low and sure; contempt for ink.

```
[cold certainty] I'll find him. Men like Varrow leave a smell of ink wherever they go.
```
Subtitle: I'll find him. Men like Varrow leave a smell of ink wherever they go.

## Said in passing

### 42. `bark.redcowl.day.0.wav`

*Where:* npcs.json redcowl.barks[0]
*Played:* gruff; pace: measured; volume: level.

```
[gruff] Keep walking.
```
Subtitle: Keep walking.

### 43. `bark.redcowl.day.1.wav`

*Where:* npcs.json redcowl.barks[1]
*Played:* gruff; pace: measured; volume: level.

```
[gruff] Salvage is salvage.
```
Subtitle: Salvage is salvage.

### 44. `bark.redcowl.day.2.wav`

*Where:* npcs.json redcowl.barks[2]
*Played:* threat; pace: measured; volume: level.

```
[threat] Talk or bleed. Your choice.
```
Subtitle: Talk or bleed. Your choice.

### 45. `bark.redcowl.day.3.wav`

*Where:* npcs.json redcowl.barks[3]
*Played:* dark humour; pace: measured; volume: level.
*Note:* A grisly story told with a grin.

```
[dark humour] Last man who lied to me, I nailed his tongue to a cart and let the horse decide.
```
Subtitle: Last man who lied to me, I nailed his tongue to a cart and let the horse decide.


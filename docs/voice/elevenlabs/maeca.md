# Maeca Barefoot: ElevenLabs packet

Voice id in the game: `maeca`. 74 takes to record (5,330 characters; about 15,990 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

**Hold 74 of these** (marked HOLD below) until the story editor's review of section 17 is back; the rest can be recorded now.

## Who they are

**Maeca Barefoot** (the Ashford Garrison). Few words, all of them about ground, tracks, weather and animals. Level, quiet, present tense. Calls the wolves "the Pack" or "them", never "beasts" or "monsters". Contempt is quiet and final. Never raises her voice; never talks about Ashford except in three words or fewer. *Casting:* 30s, Welsh borders, a hunter's half-voice with a hard edge.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Maeca Barefoot`. Never describe a voice as sounding like a real person.

```
Native English (British, Welsh). Female, 30s. Studio quality. Persona: a hunter. A woman in her thirties, a hunter from the Welsh borders, with a soft lilting Welsh-English accent. A low, quiet, level half-voice with a hard edge, like someone used to not being heard in a wood. Few words, calm and steady, never raised. Thick Welsh accent. No reverb or effects.
```

Preview text:

```
Tracks by the stream, three days old. They drank, and they lay down where they drank. The Pack doesn't do that. Something in the water does.
```

In the Voice Library instead: search for *Welsh borders*, *female*, *30*, and listen for this: A woman in her thirties, a hunter from the Welsh borders, with a soft lilting Welsh-English accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.maeca.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice maeca
```

## Saying the names

The text to paste already respells these; keep the respelling: Greymuzzle as *Grey-muzzle*, Maeca as *Mayka*, Thornhollow as *Thorn-hollow*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Maeca

### 1. `dlg.maeca.first.0.wav`  HOLD

*Where:* dialogue.json maeca/first#0
*Played:* quiet recognition; doing: finds a fellow hunter; pace: measured; volume: quiet.
*Wants:* someone who reads ground the way she does
*Hides:* the Pack are hers
*Note:* Level, a hunter's half-voice. 'Hunter?' barely a question: she is confirming what she has read, no surprise. 'They're running.' plain and certain. 'before you ask' dry, said a thousand times, not a joke she enjoys.

```
[quiet recognition, quietly] You walk like someone who's followed a thing to its den… Hunter?… Then you've seen it too, out there. They're not hunting… They're running. [inhales] Mayka… Barefoot, before you ask.
```
Subtitle: You walk like someone who's followed a thing to its den. Hunter? Then you've seen it too, out there. They're not hunting. They're running. Maeca. Barefoot, before you ask.

### 2. `dlg.maeca.first.1.wav`  HOLD

*Where:* dialogue.json maeca/first#1
*Played:* cold contempt; doing: you wear wolves; pace: measured; volume: quiet.
*Wants:* you out of her Hollow
*Hides:* those were her Pack
*Note:* Quiet and final. 'and so can they' a fact, which is what makes it the threat. 'What do you want?' drops, no question lift.

```
[cold contempt, quietly] That cloak's made of wolves. I can smell it from here… and so can they. Mayka Barefoot. What do you want?
```
Subtitle: That cloak's made of wolves. I can smell it from here, and so can they. Maeca Barefoot. What do you want?

### 3. `dlg.maeca.first.2.wav`  HOLD

*Where:* dialogue.json maeca/first#2
*Played:* weary contempt; doing: dismisses another bounty-hunter; pace: measured; volume: quiet.
*Wants:* to be taken seriously about the cause
*Hides:* she is all that is left of the Ashford garrison
*Note:* Flat contempt for the bounty; the rule about the problem said plainly. 'before you ask' dry, said a thousand times.

```
[weary contempt, quietly] Another blade for Holloway's bounty?… The Pack aren't the problem. They're what the problem looks like from the road. [inhales] Mayka… Barefoot, before you ask.
```
Subtitle: Another blade for Holloway's bounty? The Pack aren't the problem. They're what the problem looks like from the road. Maeca. Barefoot, before you ask.

### 4. `dlg.maeca.hub.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/hub#0; part 2 of 2: narrator: She doesn't look up from her cup. / **maeca: It's late. Say it.**
*Played:* tired, terse; doing: late night; pace: slow; volume: quiet.
*Note:* Narrator for the cup. 'Say it.' curt.

```
[tired, terse, quietly] It's late. Say it.
```
Subtitle: It's late. Say it.

### 5. `dlg.maeca.hub.1.wav`  HOLD

*Where:* dialogue.json maeca/hub#1
*Played:* level, warmer; doing: respect; pace: measured; volume: quiet.
*Note:* Calls you hunter as a compliment.

```
[level, warmer, quietly] Hunter. What have you found?
```
Subtitle: Hunter. What have you found?

### 6. `dlg.maeca.hub.2.wav`  HOLD

*Where:* dialogue.json maeca/hub#2
*Played:* flat; doing: acknowledges you; pace: measured; volume: quiet.

```
[flat, quietly] You again. What is it?
```
Subtitle: You again. What is it?

### 7. `dlg.maeca.driving.0.wav`  HOLD

*Where:* dialogue.json maeca/driving#0
*Played:* focused, concerned; doing: explains the Pack's trouble; pace: measured; volume: quiet.
*Note:* Ground and animals, present tense. A little heat on 'more than a hundred pelts'. Tam's line with quiet sympathy.

```
[focused, concerned, quietly] Something in the deep wood. The deer are thin, the Pack's thinner, and the old alpha, Grey-muzzle, has brought them closer to people than he ever would. Find out why and you'll have done more than a hundred pelts. Ask Tam, by the well. He's seen something, and nobody believes a child.
```
Subtitle: Something in the deep wood. The deer are thin, the Pack's thinner, and the old alpha, Greymuzzle, has brought them closer to people than he ever would. Find out why and you'll have done more than a hundred pelts. Ask Tam, by the well. He's seen something, and nobody believes a child.

### 8. `dlg.maeca.tracks.0.wav`  HOLD

*Where:* dialogue.json maeca/tracks#0
*Played:* surprised respect; doing: you read the tracks; pace: measured; volume: quiet.
*Note:* Genuine surprise on 'You saw that?'. Then clinical. 'So. Not bold. Sick.' a verdict.

```
[surprised respect, quietly] You saw that? Nobody sees that. Dragging, yes. Weak in the hindquarters, like a dog that's eaten what it shouldn't. So. Not bold. Sick.
```
Subtitle: You saw that? Nobody sees that. Dragging, yes. Weak in the hindquarters, like a dog that's eaten what it shouldn't. So. Not bold. Sick.

### 9. `dlg.maeca.truth.0.wav`  HOLD

*Where:* dialogue.json maeca/truth#0
*Played:* quiet anger, then hope; doing: the Dig is poisoning them; pace: measured; volume: quiet.
*Note:* Contempt for the diggers. 'Days, maybe.' hopeful, guarded.

```
[quiet anger, then hope, quietly] Grimtunnel's diggers. Should've known; every bad thing under Thorn-hollow has a lamp in its hand. Stop that pump and the Pack'll come back to itself. Days, maybe. It'll happen.
```
Subtitle: Grimtunnel's diggers. Should've known; every bad thing under Thornhollow has a lamp in its hand. Stop that pump and the Pack'll come back to itself. Days, maybe. It'll happen.

### 10. `dlg.maeca.speak.0.wav`  HOLD

*Where:* dialogue.json maeca/speak#0
*Played:* serious, careful; doing: how to approach Greymuzzle; pace: slow; volume: quiet.
*Note:* Instructions, each a rule. A dry edge on 'If he decides wrong, well. Run then.'

```
[serious, careful, quietly] Not with words. But Greymuzzle's old and he isn't stupid. Go into the Hollow with no wolf blood on you, none since you last slept. Don't wear their skins. And don't run. He'll decide what you are. If he decides wrong, well. Run then.
```
Subtitle: Not with words. But Greymuzzle's old and he isn't stupid. Go into the Hollow with no wolf blood on you, none since you last slept. Don't wear their skins. And don't run. He'll decide what you are. If he decides wrong, well. Run then.

### 11. `dlg.maeca.where.0.wav`  HOLD

*Where:* dialogue.json maeca/where#0
*Played:* dry; doing: where to find her; pace: measured; volume: quiet.
*Note:* Plain directions; dry humour on 'fool enough' and 'Rav's piss'.

```
[dry, quietly] The Hunters' Blind, out past the wreck on the Old Road, most days. I watch the Hollow from there. You'll know it by the smoke; I'm the only one fool enough to light a fire in that wood. Nights, I'm here, drinking Rav's piss.
```
Subtitle: The Hunters' Blind, out past the wreck on the Old Road, most days. I watch the Hollow from there. You'll know it by the smoke; I'm the only one fool enough to light a fire in that wood. Nights, I'm here, drinking Rav's piss.

### 12. `dlg.maeca.barefoot.0.wav`  HOLD

*Where:* dialogue.json maeca/barefoot#0
*Played:* flat, guarded; doing: why she's barefoot; pace: slow; volume: quiet.
*Note:* Short and hard. 'They never came.' heavy. 'I prefer it now.' a door closing.

```
[flat, guarded, quietly] Boots were signed for. They never came. You learn to hear the ground through your feet. I prefer it now.
```
Subtitle: Boots were signed for. They never came. You learn to hear the ground through your feet. I prefer it now.

### 13. `dlg.maeca.signed.0.wav`  HOLD

*Where:* dialogue.json maeca/signed#0
*Played:* cold, suspicious; doing: won't say; pace: slow; volume: quiet.
*Note:* Contempt in 'a good hand'. Then suspicion turned on you.

```
[cold, suspicious, quietly] Somebody with a good hand and a ledger. ...You ask a lot of questions for a stranger.
```
Subtitle: Somebody with a good hand and a ledger. ...You ask a lot of questions for a stranger.

### 14. `dlg.maeca.thanks.0.wav`  HOLD

*Where:* dialogue.json maeca/thanks#0
*Played:* moved, unaccustomed; doing: thanks you; pace: slow; volume: quiet.
*Wants:* you to know what it means
*Note:* Reporting the Hollow, steady. Then the confession, quieter. A long pause. 'Thank you.' barely said; she never says it.

```
[moved, unaccustomed, quietly] The Hollow's quiet. The Pack's eating again: deer, not travellers. I've been a hunter all my life, and I've never once saved anything. ...Thank you.
```
Subtitle: The Hollow's quiet. The Pack's eating again: deer, not travellers. I've been a hunter all my life, and I've never once saved anything. ...Thank you.

### 15. `dlg.maeca.cold.0.wav`  HOLD

*Where:* dialogue.json maeca/cold#0
*Played:* contempt, hurt; doing: you killed the Pack; pace: slow; volume: quiet.
*Note:* Ice. The last line bitter and quiet.

```
[contempt, hurt, quietly] You emptied the Hollow. I heard. I hope Holloway's gold keeps you warm.
```
Subtitle: You emptied the Hollow. I heard. I hope Holloway's gold keeps you warm.

### 16. `dlg.maeca.gone.0.wav`  HOLD

*Where:* dialogue.json maeca/gone#0
*Played:* betrayal, fury held down; doing: you killed Greymuzzle; pace: slow; volume: quiet.
*Note:* Each fragment its own blow. The voice never rises; the hurt is in the stillness. 'Get out of my light' through her teeth.

```
[betrayal, fury held down, quietly] You went to his house. In the dark. After I told you what he was to me. Get out of my light, and don't come to the Blind again.
```
Subtitle: You went to his house. In the dark. After I told you what he was to me. Get out of my light, and don't come to the Blind again.

### 17. `dlg.maeca.gone.1.wav`  HOLD

*Where:* dialogue.json maeca/gone#1
*Played:* cold fury; doing: you killed Greymuzzle; pace: slow; volume: quiet.
*Note:* Each fragment its own blow, never raised.

```
[cold fury, quietly] You went to his house. In the dark. Get out of my light.
```
Subtitle: You went to his house. In the dark. Get out of my light.

### 18. `dlg.maeca.cb_burned_roost.0.wav`  HOLD

*Where:* dialogue.json maeca/cb_burned_roost#0
*Played:* cold, haunted; doing: you burned people; pace: slow; volume: quiet.
*Note:* Flat and quiet. 'I was at Ashford.' three words, final.

```
[cold, haunted, quietly] You burned the Roost with them still in the cages. I know what fire does in a ravine. I was at Ashford.
```
Subtitle: You burned the Roost with them still in the cages. I know what fire does in a ravine. I was at Ashford.

### 19. `dlg.maeca.say_calling.0.wav`  HOLD

*Where:* dialogue.json maeca/say_calling#0
*Played:* practical; doing: advice; pace: measured; volume: quiet.
*Note:* Hunter's instruction.

```
[practical, quietly] A shield. Good. Don't raise it in the Hollow. To a wolf a raised arm's a raised arm.
```
Subtitle: A shield. Good. Don't raise it in the Hollow. To a wolf a raised arm's a raised arm.

### 20. `dlg.maeca.say_calling.1.wav`  HOLD

*Where:* dialogue.json maeca/say_calling#1
*Played:* practical; doing: advice; pace: measured; volume: quiet.
*Note:* Hunter's instruction.

```
[practical, quietly] Leave the big blade at the Blind if you go near the Hollow. They can smell iron that's been used.
```
Subtitle: Leave the big blade at the Blind if you go near the Hollow. They can smell iron that's been used.

### 21. `dlg.maeca.say_calling.2.wav`  HOLD

*Where:* dialogue.json maeca/say_calling#2
*Played:* practical, grave; doing: advice; pace: measured; volume: quiet.
*Note:* 'Fire's the one thing they all remember.' with a shadow of Ashford.

```
[practical, grave, quietly] Whatever it is you burn with, don't burn it in the Hollow. Fire's the one thing they all remember.
```
Subtitle: Whatever it is you burn with, don't burn it in the Hollow. Fire's the one thing they all remember.

### 22. `dlg.maeca.say_calling.3.wav`  HOLD

*Where:* dialogue.json maeca/say_calling#3
*Played:* approving, dry; doing: notices your quiet feet; pace: measured; volume: quiet.
*Note:* A rare half-smile on 'Pity about the boots.'

```
[approving, dry, quietly] You move like you've done this. Quiet feet. ...Pity about the boots.
```
Subtitle: You move like you've done this. Quiet feet. ...Pity about the boots.

### 23. `dlg.maeca.say_calling.4.wav`  HOLD

*Where:* dialogue.json maeca/say_calling#4
*Played:* approving, dry; doing: notices your quiet feet; pace: measured; volume: quiet.
*Note:* A rare half-smile on 'Pity about the boots.'

```
[approving, dry, quietly] You move like you've done this. Quiet feet. ...Pity about the boots.
```
Subtitle: You move like you've done this. Quiet feet. ...Pity about the boots.

### 24. `dlg.maeca.invite.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/invite#0; part 2 of 2: narrator: She finishes her cup and stands. / **maeca: I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can…**
*Played:* understated invitation; doing: asks you to the Blind; pace: slow; volume: quiet.
*Wants:* company she can trust
*Note:* Plain and low, no flirtation. 'Most can't.' dry, a challenge.

```
[understated invitation, quietly] I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can't.
```
Subtitle: I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can't.

### 25. `dlg.maeca.blind_morning.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/blind_morning#0; part 2 of 2: narrator: Grey light. She's already up, barefoot in the frost, listening. / **maeca: Go on, then. The wood's awake, and so's Holloway, and he'll count us both.**
*Played:* quiet warmth, dry; doing: morning after; pace: measured; volume: quiet.
*Note:* Narrator for the frost. Then softer than usual; dry joke on Holloway counting.

```
[quiet warmth, dry, quietly] Go on, then. The wood's awake, and so's Holloway, and he'll count us both.
```
Subtitle: Go on, then. The wood's awake, and so's Holloway, and he'll count us both.

### 26. `dlg.maeca.blind_morning.1.p1.wav`  HOLD

*Where:* dialogue.json maeca/blind_morning#1; part 2 of 2: narrator: Grey light. She's already up, barefoot in the frost, listening to the wood. / **maeca: The Pack found me, after Ashford. Three days in a cave mouth with the garrison dead round …**
*Played:* confession, raw but steady; doing: tells you why she never hunts wolves; pace: slow; volume: quiet.
*Wants:* you to know, and not to pity her
*Note:* Narrator for the frost. The story told plainly, present tense feel. 'Kept everything off.' near breaking. A pause. 'That's all of why.' firm. 'Don't make it a story.' a plea disguised as an order.

```
[confession, raw but steady, quietly] The Pack found me, after Ashford. Three days in a cave mouth with the garrison dead round me, and the old grey one came and lay down across the way in. Kept the cold off. Kept everything off. ...That's why. That's all of why. Don't make it a story.
```
Subtitle: The Pack found me, after Ashford. Three days in a cave mouth with the garrison dead round me, and the old grey one came and lay down across the way in. Kept the cold off. Kept everything off. ...That's why. That's all of why. Don't make it a story.

### 27. `dlg.maeca.cb_broke_promise.0.wav`  HOLD

*Where:* dialogue.json maeca/cb_broke_promise#0
*Played:* cold contempt, grief; doing: you betrayed the Pack; pace: slow; volume: quiet.
*Note:* Three plain statements, cold. Pause. The last line quiet and final.

```
[cold contempt, grief, quietly] You knelt to him. You held out your hand and he let you in. Then you killed his. ...I've nothing to say to you that I'd want to have said.
```
Subtitle: You knelt to him. You held out your hand and he let you in. Then you killed his. ...I've nothing to say to you that I'd want to have said.

### 28. `dlg.maeca.t_maeca.0.wav`  HOLD

*Where:* dialogue.json maeca/t_maeca#0
*Played:* dry, grim; doing: what she hunted; pace: measured; volume: quiet.
*Note:* Deadpan; a grim joke about men on paths.

```
[dry, grim, quietly] Men, for the garrison. Deer, for me. Men are easier. They keep to paths and they talk while they walk.
```
Subtitle: Men, for the garrison. Deer, for me. Men are easier. They keep to paths and they talk while they walk.

### 29. `dlg.maeca.kerchiefs.0.p0.wav`  HOLD

*Where:* dialogue.json maeca/kerchiefs#0; part 1 of 3: **maeca: Some.** / narrator: She drinks, and looks at the cup instead of you. / maeca: Fed some of them, once. Buried more. ...Ask me about wolves.
*Played:* guarded grief; doing: won't talk about them; pace: slow; volume: quiet.
*Note:* 'Some.' Narrator for the cup. 'Fed some of them, once. Buried more.' heavy. 'Ask me about wolves.' a closing door.

```
[guarded grief, quietly] Some.
```
Subtitle: Some.

### 30. `dlg.maeca.kerchiefs.0.p2.wav`  HOLD

*Where:* dialogue.json maeca/kerchiefs#0; part 3 of 3: maeca: Some. / narrator: She drinks, and looks at the cup instead of you. / **maeca: Fed some of them, once. Buried more. ...Ask me about wolves.**
*Played:* guarded grief; doing: won't talk about them; pace: slow; volume: quiet.
*Note:* 'Some.' Narrator for the cup. 'Fed some of them, once. Buried more.' heavy. 'Ask me about wolves.' a closing door.

```
[guarded grief, quietly] Fed some of them, once. Buried more. ...Ask me about wolves.
```
Subtitle: Fed some of them, once. Buried more. ...Ask me about wolves.

### 31. `dlg.maeca.cb_knelt.0.p0.wav`  HOLD

*Where:* dialogue.json maeca/cb_knelt#0; part 1 of 3: **maeca: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge.** / narrator: She looks at your knees. / maeca: He let you. ...He doesn't let me, and he's known me ten years.
*Played:* quiet wonder, a little jealous; doing: she saw you kneel to Greymuzzle; pace: slow; volume: quiet.
*Note:* Narrator for the look at your knees. 'He let you.' amazed. The last sentence hurt, plain.

```
[quiet wonder, a little jealous, quietly] You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge.
```
Subtitle: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge.

### 32. `dlg.maeca.cb_knelt.0.p2.wav`  HOLD

*Where:* dialogue.json maeca/cb_knelt#0; part 3 of 3: maeca: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge. / narrator: She looks at your knees. / **maeca: He let you. ...He doesn't let me, and he's known me ten years.**
*Played:* quiet wonder, a little jealous; doing: she saw you kneel to Greymuzzle; pace: slow; volume: quiet.
*Note:* Narrator for the look at your knees. 'He let you.' amazed. The last sentence hurt, plain.

```
[quiet wonder, a little jealous, quietly] He let you. ...He doesn't let me, and he's known me ten years.
```
Subtitle: He let you. ...He doesn't let me, and he's known me ten years.

### 33. `dlg.maeca.blood.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/blood#0; part 2 of 2: narrator: At the edge of the Hollow she stops, and sniffs, once, and turns round. / **maeca: Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night ta…**
*Played:* flat warning, then kind; doing: you smell of wolf blood; pace: measured; volume: quiet.
*Note:* Narrator: she stops and sniffs. Curt orders. 'It took it off me.' quiet, a confession.

```
[flat warning, then kind, quietly] Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night takes it off. It took it off me.
```
Subtitle: Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night takes it off. It took it off me.

### 34. `dlg.maeca.blind_walk.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/blind_walk#0; part 2 of 3: narrator: She goes out by the east gate without a lamp, and you follow her along the Old Road past t… / **maeca: Him. And the bitch with the white foot.** / narrator: She walks on.
*Played:* hushed, attentive; doing: the walk to the Blind; pace: slow; volume: quiet.
*Note:* Narrator plain and starlit; a beat before 'and is answered'. Maeca just above a breath, naming neighbours by their voices. Narrator plain: the narrator never shows a feeling.

```
[hushed, attentive, quietly] Him… And the bitch with the white foot.
```
Subtitle: Him. And the bitch with the white foot.

### 35. `dlg.maeca.blind_ask.0.wav`  HOLD

*Where:* dialogue.json maeca/blind_ask#0
*Played:* dry, guarded; doing: terms for the night; pace: measured; volume: quiet.
*Note:* Deadpan; almost a smile.

```
[dry, guarded, quietly] If you're going to talk after, don't.
```
Subtitle: If you're going to talk after, don't.

### 36. `dlg.maeca.blind_leave.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/blind_leave#0; part 2 of 2: narrator: She nods at the fire. / **maeca: Mind the frost on the Old Road. It's worse by the wreck.**
*Played:* practical tenderness; doing: sends you off safe; pace: measured; volume: quiet.
*Note:* Care disguised as a road report.

```
[practical tenderness, quietly] Mind the frost on the Old Road. It's worse by the wreck.
```
Subtitle: Mind the frost on the Old Road. It's worse by the wreck.

### 37. `dlg.maeca.watch_morning.0.p0.wav`  HOLD

*Where:* dialogue.json maeca/watch_morning#0; part 1 of 3: **maeca: You kept quiet.** / narrator: She stands, and stretches, and looks at the Hollow, not you. / maeca: Most can't.
*Played:* approving, dry; doing: you kept the watch; pace: slow; volume: quiet.
*Note:* Narrator for the stretch. 'Most can't.' a small compliment.

```
[approving, dry, quietly] You kept quiet.
```
Subtitle: You kept quiet.

### 38. `dlg.maeca.watch_morning.0.p2.wav`  HOLD

*Where:* dialogue.json maeca/watch_morning#0; part 3 of 3: maeca: You kept quiet. / narrator: She stands, and stretches, and looks at the Hollow, not you. / **maeca: Most can't.**
*Played:* approving, dry; doing: you kept the watch; pace: slow; volume: quiet.
*Note:* Narrator for the stretch. 'Most can't.' a small compliment.

```
[approving, dry, quietly] Most can't.
```
Subtitle: Most can't.

### 39. `dlg.maeca.blind_dark.1.p1.wav`  HOLD

*Where:* dialogue.json maeca/blind_dark#1; part 2 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / **maeca: They don't do that. Not for me. Not for anyone.** / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* hushed, careful; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[hushed, careful, whispers] They don't do that… Not for me. Not for anyone.
```
Subtitle: They don't do that. Not for me. Not for anyone.

### 40. `dlg.maeca.blind_dark.1.p3.wav`  HOLD

*Where:* dialogue.json maeca/blind_dark#1; part 4 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / **maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a…** / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* hushed, careful; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[hushed, careful, whispers] You walk quiet. You came into my Hollow and knelt to him, and he let you… You never talk about before.
```
Subtitle: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk about before.

### 41. `dlg.maeca.blind_dark.1.p5.wav`  HOLD

*Where:* dialogue.json maeca/blind_dark#1; part 6 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / **maeca: What were you?**
*Played:* hushed, careful; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[hushed, careful, whispers] [long pause] What were you?
```
Subtitle: What were you?

### 42. `dlg.maeca.blind_dark.2.p1.wav`  HOLD

*Where:* dialogue.json maeca/blind_dark#2; part 2 of 4: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / **maeca: You walk quiet. You never talk about before.** / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* hushed, careful; doing: she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences
*Note:* As blind_dark.1 without the Pack. 'What were you?' careful, no stress on 'were', after a real count of about three seconds.

```
[hushed, careful, whispers] You walk quiet. You never talk about before.
```
Subtitle: You walk quiet. You never talk about before.

### 43. `dlg.maeca.blind_dark.2.p3.wav`  HOLD

*Where:* dialogue.json maeca/blind_dark#2; part 4 of 4: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: You walk quiet. You never talk about before. / narrator: Against your chest you feel her lips move, without a sound. / **maeca: What were you?**
*Played:* hushed, careful; doing: she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences
*Note:* As blind_dark.1 without the Pack. 'What were you?' careful, no stress on 'were', after a real count of about three seconds.

```
[hushed, careful, whispers] [long pause] What were you?
```
Subtitle: What were you?

### 44. `dlg.maeca.told_true.0.p0.wav`  HOLD

*Where:* dialogue.json maeca/told_true#0; part 1 of 3: **maeca: Thought so. You put your feet down like you're asking the ground first.** / narrator: She almost smiles. / maeca: I'd have liked you, then. Probably would have shot you for poaching.
*Played:* warm, wry; doing: you were a hunter; pace: measured; volume: quiet.
*Note:* Narrator: she almost smiles. The poaching joke fond.

```
[warm, wry, quietly] Thought so. You put your feet down like you're asking the ground first.
```
Subtitle: Thought so. You put your feet down like you're asking the ground first.

### 45. `dlg.maeca.told_true.0.p2.wav`  HOLD

*Where:* dialogue.json maeca/told_true#0; part 3 of 3: maeca: Thought so. You put your feet down like you're asking the ground first. / narrator: She almost smiles. / **maeca: I'd have liked you, then. Probably would have shot you for poaching.**
*Played:* warm, wry; doing: you were a hunter; pace: measured; volume: quiet.
*Note:* Narrator: she almost smiles. The poaching joke fond.

```
[warm, wry, quietly] I'd have liked you, then. Probably would have shot you for poaching.
```
Subtitle: I'd have liked you, then. Probably would have shot you for poaching.

### 46. `dlg.maeca.told_true.1.p0.wav`  HOLD

*Where:* dialogue.json maeca/told_true#1; part 1 of 3: **maeca: Letters.** / narrator: She thinks about it. / maeca: Tracks for people who sit still. ...Read me something, one day. Not now.
*Played:* curious, soft; doing: you were a scholar; pace: slow; volume: quiet.
*Note:* Thinking. 'Read me something, one day.' shy, then 'Not now.' quick.

```
[curious, soft, quietly] Letters.
```
Subtitle: Letters.

### 47. `dlg.maeca.told_true.1.p2.wav`  HOLD

*Where:* dialogue.json maeca/told_true#1; part 3 of 3: maeca: Letters. / narrator: She thinks about it. / **maeca: Tracks for people who sit still. ...Read me something, one day. Not now.**
*Played:* curious, soft; doing: you were a scholar; pace: slow; volume: quiet.
*Note:* Thinking. 'Read me something, one day.' shy, then 'Not now.' quick.

```
[curious, soft, quietly] Tracks for people who sit still. ...Read me something, one day. Not now.
```
Subtitle: Tracks for people who sit still. ...Read me something, one day. Not now.

### 48. `dlg.maeca.told_true.2.wav`  HOLD

*Where:* dialogue.json maeca/told_true#2
*Played:* respect; doing: you walked away; pace: measured; volume: quiet.
*Note:* Plain respect, with Ashford under it.

```
[respect, quietly] Walking away's a skill. Most never learn it. They stay till it's too late, out of pride.
```
Subtitle: Walking away's a skill. Most never learn it. They stay till it's too late, out of pride.

### 49. `dlg.maeca.told_true.3.p0.wav`  HOLD

*Where:* dialogue.json maeca/told_true#3; part 1 of 3: **maeca: Lamps. Nobody coming.** / narrator: A long breath. / maeca: I held a cave mouth three days for nobody coming. We'd have got on.
*Played:* kinship, grief; doing: you lit lamps for nobody; pace: slow; volume: quiet.
*Note:* Narrator: a long breath. The cave mouth line very quiet. 'We'd have got on.' tender.

```
[kinship, grief, quietly] Lamps. Nobody coming.
```
Subtitle: Lamps. Nobody coming.

### 50. `dlg.maeca.told_true.3.p2.wav`  HOLD

*Where:* dialogue.json maeca/told_true#3; part 3 of 3: maeca: Lamps. Nobody coming. / narrator: A long breath. / **maeca: I held a cave mouth three days for nobody coming. We'd have got on.**
*Played:* kinship, grief; doing: you lit lamps for nobody; pace: slow; volume: quiet.
*Note:* Narrator: a long breath. The cave mouth line very quiet. 'We'd have got on.' tender.

```
[kinship, grief, quietly] I held a cave mouth three days for nobody coming. We'd have got on.
```
Subtitle: I held a cave mouth three days for nobody coming. We'd have got on.

### 51. `dlg.maeca.told_little.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/told_little#0; part 2 of 4: narrator: She doesn't push. / **maeca: All right.** / narrator: And it is. / maeca: ...Keep it, then. I keep mine.
*Played:* accepting; doing: she doesn't push; pace: slow; volume: quiet.
*Note:* Narrator around her. 'I keep mine.' kind.

```
[accepting, quietly] All right.
```
Subtitle: All right.

### 52. `dlg.maeca.told_little.0.p3.wav`  HOLD

*Where:* dialogue.json maeca/told_little#0; part 4 of 4: narrator: She doesn't push. / maeca: All right. / narrator: And it is. / **maeca: ...Keep it, then. I keep mine.**
*Played:* accepting; doing: she doesn't push; pace: slow; volume: quiet.
*Note:* Narrator around her. 'I keep mine.' kind.

```
[accepting, quietly] ...Keep it, then. I keep mine.
```
Subtitle: ...Keep it, then. I keep mine.

### 53. `dlg.maeca.blind3_morning.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/blind3_morning#0; part 2 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / **maeca: Your heart's going like a hare's.** / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* tender, frightened, hiding it; doing: she heard your heart change; pace: slow; volume: hushed.
*Note:* Narrator: grey light, her head on your chest. Close and still: the hare and the bear. 'I counted between.' A pause where the name would be. Narrator: she goes out. 'Go on. Holloway'll count us.' steadier.

```
[tender, frightened, hiding it, whispers] Your heart's going like a hare's.
```
Subtitle: Your heart's going like a hare's.

### 54. `dlg.maeca.blind3_morning.0.p3.wav`  HOLD

*Where:* dialogue.json maeca/blind3_morning#0; part 4 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / **maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot…** / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* tender, frightened, hiding it; doing: she heard your heart change; pace: slow; volume: hushed.
*Note:* Narrator: grey light, her head on your chest. Close and still: the hare and the bear. 'I counted between.' A pause where the name would be. Narrator: she goes out. 'Go on. Holloway'll count us.' steadier.

```
[tender, frightened, hiding it, whispers] All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot of things to see if they'd live.
```
Subtitle: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot of things to see if they'd live.

### 55. `dlg.maeca.blind3_morning.0.p5.wav`  HOLD

*Where:* dialogue.json maeca/blind3_morning#0; part 6 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / **maeca: Go on. Holloway'll count us.**
*Played:* tender, frightened, hiding it; doing: she heard your heart change; pace: slow; volume: hushed.
*Note:* Narrator: grey light, her head on your chest. Close and still: the hare and the bear. 'I counted between.' A pause where the name would be. Narrator: she goes out. 'Go on. Holloway'll count us.' steadier.

```
[tender, frightened, hiding it, whispers] Go on. Holloway'll count us.
```
Subtitle: Go on. Holloway'll count us.

### 56. `dlg.maeca.blind3_m_no.0.p0.wav`  HOLD

*Where:* dialogue.json maeca/blind3_m_no#0; part 1 of 3: **maeca: No.** / narrator: Not unkind. / maeca: Don't make it a story. Not yet.
*Played:* gentle refusal; doing: not yet; pace: slow; volume: quiet.
*Note:* 'No.' Narrator: not unkind. Her old rule, softened.

```
[gentle refusal, quietly] No.
```
Subtitle: No.

### 57. `dlg.maeca.blind3_m_no.0.p2.wav`  HOLD

*Where:* dialogue.json maeca/blind3_m_no#0; part 3 of 3: maeca: No. / narrator: Not unkind. / **maeca: Don't make it a story. Not yet.**
*Played:* gentle refusal; doing: not yet; pace: slow; volume: quiet.
*Note:* 'No.' Narrator: not unkind. Her old rule, softened.

```
[gentle refusal, quietly] Don't make it a story. Not yet.
```
Subtitle: Don't make it a story. Not yet.

### 58. `dlg.maeca.say_sella.0.p0.wav`  HOLD

*Where:* dialogue.json maeca/say_sella#0; part 1 of 3: **maeca: You go up Sella's stairs.** / narrator: She doesn't look up from her cup. / maeca: Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind n…
*Played:* plain, exposed; doing: asks about Sella; pace: slow; volume: quiet.
*Note:* Narrator: the cup. Level. 'I mind not knowing.' honest and quiet.

```
[plain, exposed, quietly] You go up Sella's stairs.
```
Subtitle: You go up Sella's stairs.

### 59. `dlg.maeca.say_sella.0.p2.wav`  HOLD

*Where:* dialogue.json maeca/say_sella#0; part 3 of 3: maeca: You go up Sella's stairs. / narrator: She doesn't look up from her cup. / **maeca: Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind n…**
*Played:* plain, exposed; doing: asks about Sella; pace: slow; volume: quiet.
*Note:* Narrator: the cup. Level. 'I mind not knowing.' honest and quiet.

```
[plain, exposed, quietly] Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind not knowing.
```
Subtitle: Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind not knowing.

### 60. `dlg.maeca.say_sella.1.p0.wav`  HOLD

*Where:* dialogue.json maeca/say_sella#1; part 1 of 3: **maeca: You go up Sella's stairs. Rook talks.** / narrator: A shrug. / maeca: She's honest about what she charges. That's more than most.
*Played:* dry, fair; doing: Sella's honest; pace: measured; volume: quiet.
*Note:* Narrator: a shrug. Fair-minded.

```
[dry, fair, quietly] You go up Sella's stairs. Rook talks.
```
Subtitle: You go up Sella's stairs. Rook talks.

### 61. `dlg.maeca.say_sella.1.p2.wav`  HOLD

*Where:* dialogue.json maeca/say_sella#1; part 3 of 3: maeca: You go up Sella's stairs. Rook talks. / narrator: A shrug. / **maeca: She's honest about what she charges. That's more than most.**
*Played:* dry, fair; doing: Sella's honest; pace: measured; volume: quiet.
*Note:* Narrator: a shrug. Fair-minded.

```
[dry, fair, quietly] She's honest about what she charges. That's more than most.
```
Subtitle: She's honest about what she charges. That's more than most.

### 62. `dlg.maeca.say_sella_both.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/say_sella_both#0; part 2 of 2: narrator: A nod. / **maeca: Good. Now I know.**
*Played:* settled; doing: now she knows; pace: measured; volume: quiet.

```
[settled, quietly] Good. Now I know.
```
Subtitle: Good. Now I know.

### 63. `dlg.maeca.say_sella_you.0.p1.wav`  HOLD

*Where:* dialogue.json maeca/say_sella_you#0; part 2 of 2: narrator: She looks at you, long, the way she looks at a track that might be lying. / **maeca: We'll see.**
*Played:* wary hope; doing: we'll see; pace: slow; volume: quiet.
*Note:* Narrator for the long look. 'We'll see.' guarded.

```
[wary hope, quietly] We'll see.
```
Subtitle: We'll see.

### 64. `dlg.maeca.say_sella_dunno.0.wav`  HOLD

*Where:* dialogue.json maeca/say_sella_dunno#0
*Played:* dry acceptance; doing: an answer of sorts; pace: measured; volume: quiet.

```
[dry acceptance, quietly] That's an answer.
```
Subtitle: That's an answer.

## Said in passing

### 65. `bark.maeca.day.0.wav`  HOLD

*Where:* npcs.json maeca.barks[0]
*Played:* terse; pace: measured; volume: quiet.

```
[terse, quietly] Mind the east road after dark.
```
Subtitle: Mind the east road after dark.

### 66. `bark.maeca.night.0.wav`  HOLD

*Where:* npcs.json maeca.nightBarks[0]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] Hear that? No. Neither do I. That's what worries me.
```
Subtitle: Hear that? No. Neither do I. That's what worries me.

### 67. `bark.maeca.night.1.wav`  HOLD

*Where:* npcs.json maeca.nightBarks[1]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] One more, then I sleep.
```
Subtitle: One more, then I sleep.

### 68. `bark.maeca.said.0.wav`  HOLD

*Where:* npcs.json maeca.said[0]
*Played:* certain, quiet; doing: the wolves are running; pace: measured; volume: quiet.
*Note:* Half-voice, plain fact.

```
[certain, quiet, quietly] They're not hunting. They're running.
```
Subtitle: They're not hunting. They're running.

### 69. `bark.maeca.said.1.wav`  HOLD

*Where:* npcs.json maeca.said[1]
*Played:* uneasy, watchful; doing: the wood is wrong; pace: measured; volume: quiet.
*Note:* Listening while she says it.

```
[uneasy, watchful, quietly] Something's got the whole wood on edge.
```
Subtitle: Something's got the whole wood on edge.

### 70. `bark.maeca.said.2.wav`  HOLD

*Where:* npcs.json maeca.said[2]
*Played:* quiet, attentive; doing: the Pack tonight; pace: measured; volume: quiet.
*Note:* Neighbours, not beasts.

```
[quiet, attentive, quietly] The Pack's loud tonight.
```
Subtitle: The Pack's loud tonight.

### 71. `bark.maeca.said.3.wav`  HOLD

*Where:* npcs.json maeca.said[3]
*Played:* attentive, tender; doing: an old wolf coughing; pace: slow; volume: quiet.
*Note:* 'Listen.' almost a whisper.

```
[attentive, tender, quietly] Somewhere out there an old wolf's coughing. Listen.
```
Subtitle: Somewhere out there an old wolf's coughing. Listen.

### 72. `bark.maeca.said.4.wav`  HOLD

*Where:* npcs.json maeca.said[4]
*Played:* quiet satisfaction; doing: the Pack hunts again; pace: measured; volume: quiet.
*Note:* 'Deer.' a small, private pleasure.

```
[quiet satisfaction, quietly] Hear that? They're hunting again. Deer.
```
Subtitle: Hear that? They're hunting again. Deer.

### 73. `bark.maeca.said.5.wav`  HOLD

*Where:* npcs.json maeca.said[5]
*Played:* plain, protective; doing: the Pack lying up; pace: measured; volume: quiet.
*Note:* 'Leave them be.' quiet and final.

```
[plain, protective, quietly] The Pack's lying up by the east wall. Leave them be.
```
Subtitle: The Pack's lying up by the east wall. Leave them be.

### 74. `bark.maeca.said.6.wav`  HOLD

*Where:* npcs.json maeca.said[6]
*Played:* flat, hollow; doing: the Hollow is empty; pace: slow; volume: quiet.
*Note:* The second 'Nothing.' quieter. No tears in it.

```
[flat, hollow, quietly] Nothing calls in the Hollow now. Nothing.
```
Subtitle: Nothing calls in the Hollow now. Nothing.


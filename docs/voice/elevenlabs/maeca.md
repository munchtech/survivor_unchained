# Maeca: ElevenLabs packet

Voice id in the game: `maeca`. 87 takes to record (6,295 characters; about 18,885 credits at three tries a line). Status: **on hold**: the story rewrite changes most of her lines (docs/voice/RERECORD.md). Do not record any of it yet.

## Who they are

**Maeca** (the Ashford Garrison). Just Maeca: no other name. Few words, all of them about ground, tracks, weather and animals. Level, quiet, present tense. Calls the wolves "the Pack" or "them", never "beasts" or "monsters". Contempt is quiet and final. Never raises her voice; about Ashford she says three words, "The cave mouths.", and nothing else. Signature: "I track for the Watch, before you ask. Not wolves." Every kindness she does Holloway is true, and is a hunter waiting. *Casting:* 30s, Welsh borders, a hunter's half-voice with a hard edge.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Maeca`. Never describe a voice as sounding like a real person.

```
Native English (British, Welsh). Female, 30s. Studio quality. Persona: a hunter. A woman in her thirties, a hunter from the Welsh borders, with a soft lilting Welsh-English accent. A low, quiet, level half-voice with a hard edge, like someone used to not being heard in a wood. Few words, calm and steady, never raised. Broad Welsh accent. No reverb or effects.
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

### 1. `dlg.maeca.first.0.wav`

*Where:* dialogue.json maeca/first#0
*Played:* quiet recognition; doing: finds a fellow hunter; pace: measured; volume: quiet.
*Wants:* someone who reads ground the way she does
*Hides:* the Pack are hers
*Note:* Level, a hunter's half-voice. 'Hunter?' barely a question: she is confirming what she has read, no surprise. 'They're running.' plain and certain. 'before you ask' dry, said a thousand times, not a joke she enjoys.

```
[quiet recognition, quietly] You walk like someone who's followed a thing to its den… Hunter?… Then you've seen it too, out there. They're not hunting… They're running. [inhales] Mayka… I track for the Watch, before you ask… Not wolves.
```
Subtitle: You walk like someone who's followed a thing to its den. Hunter? Then you've seen it too, out there. They're not hunting. They're running. Maeca. I track for the Watch, before you ask. Not wolves.

### 2. `dlg.maeca.first.1.wav`

*Where:* dialogue.json maeca/first#1
*Played:* cold contempt; doing: you wear wolves; pace: measured; volume: quiet.
*Wants:* you out of her Hollow
*Hides:* those were her Pack
*Note:* Quiet and final. 'and so can they' a fact, which is what makes it the threat. 'What do you want?' drops, no question lift.

```
[cold contempt, quietly] That cloak's made of wolves. I can smell it from here… and so can they. Mayka. What do you want?
```
Subtitle: That cloak's made of wolves. I can smell it from here, and so can they. Maeca. What do you want?

### 3. `dlg.maeca.first.2.wav`

*Where:* dialogue.json maeca/first#2
*Played:* weary contempt; doing: dismisses another bounty-hunter; pace: measured; volume: quiet.
*Wants:* to be taken seriously about the cause
*Hides:* she is all that is left of the Ashford garrison
*Note:* Flat contempt for the bounty; the rule about the problem said plainly. 'before you ask' dry, said a thousand times.

```
[weary contempt, quietly] Another blade for Holloway's bounty?… The Pack aren't the problem. They're what the problem looks like from the road. [inhales] Mayka… I track for the Watch, before you ask… Not wolves.
```
Subtitle: Another blade for Holloway's bounty? The Pack aren't the problem. They're what the problem looks like from the road. Maeca. I track for the Watch, before you ask. Not wolves.

### 4. `dlg.maeca.hub.0.p1.wav`

*Where:* dialogue.json maeca/hub#0; part 2 of 2: narrator: She doesn't look up from her cup. / **maeca: It's late. Say it.**
*Played:* tired, terse; doing: late night; pace: slow; volume: quiet.
*Note:* Narrator for the cup. 'Say it.' curt.

```
[tired, terse, quietly] It's late. Say it.
```
Subtitle: It's late. Say it.

### 5. `dlg.maeca.hub.1.wav`

*Where:* dialogue.json maeca/hub#1
*Played:* level, warmer; doing: respect; pace: measured; volume: quiet.
*Note:* Calls you hunter as a compliment.

```
[level, warmer, quietly] Hunter. What have you found?
```
Subtitle: Hunter. What have you found?

### 6. `dlg.maeca.hub.2.wav`

*Where:* dialogue.json maeca/hub#2
*Played:* flat; doing: acknowledges you; pace: measured; volume: quiet.

```
[flat, quietly] You again. What is it?
```
Subtitle: You again. What is it?

### 7. `dlg.maeca.driving.0.wav`

*Where:* dialogue.json maeca/driving#0
*Played:* focused, concerned; doing: explains the Pack's trouble; pace: measured; volume: quiet.
*Note:* Ground and animals, present tense. A little heat on 'more than a hundred pelts'. Tam's line with quiet sympathy.

```
[focused, concerned, quietly] Something in the deep wood. The deer are thin, the Pack's thinner, and the old dog-wolf, Grey-muzzle, has brought them closer to people than he ever would. Find out why and you'll have done more than a hundred pelts. Ask Tam, by the well. He's seen something, and nobody believes a child.
```
Subtitle: Something in the deep wood. The deer are thin, the Pack's thinner, and the old dog-wolf, Greymuzzle, has brought them closer to people than he ever would. Find out why and you'll have done more than a hundred pelts. Ask Tam, by the well. He's seen something, and nobody believes a child.

### 8. `dlg.maeca.tracks.0.wav`

*Where:* dialogue.json maeca/tracks#0
*Played:* surprised respect; doing: you read the tracks; pace: measured; volume: quiet.
*Note:* Genuine surprise on 'You saw that?'. Then clinical. 'So. Not bold. Sick.' a verdict.

```
[surprised respect, quietly] You saw that? Nobody sees that. Dragging, yes. Weak in the hindquarters, like a dog that's eaten what it shouldn't. So. Not bold. Sick.
```
Subtitle: You saw that? Nobody sees that. Dragging, yes. Weak in the hindquarters, like a dog that's eaten what it shouldn't. So. Not bold. Sick.

### 9. `dlg.maeca.truth.0.wav`

*Where:* dialogue.json maeca/truth#0
*Played:* quiet anger, then hope; doing: the Dig is poisoning them; pace: measured; volume: quiet.
*Note:* Contempt for the diggers. 'Days, maybe.' hopeful, guarded.

```
[quiet anger, then hope, quietly] Grimtunnel's diggers. Should've known; every bad thing under Thorn-hollow has a lamp in its hand. Stop that pump and the Pack'll come back to itself. Days, maybe. It'll happen.
```
Subtitle: Grimtunnel's diggers. Should've known; every bad thing under Thornhollow has a lamp in its hand. Stop that pump and the Pack'll come back to itself. Days, maybe. It'll happen.

### 10. `dlg.maeca.speak.0.wav`

*Where:* dialogue.json maeca/speak#0
*Played:* serious, careful; doing: how to approach Greymuzzle; pace: slow; volume: quiet.
*Note:* Instructions, each a rule. A dry edge on 'If he decides wrong, well. Run then.'

```
[serious, careful, quietly] Not with words. But Greymuzzle's old and he isn't stupid. Go into the Hollow with no wolf blood on you, none since you last slept. Don't wear their skins. And don't run. He'll decide what you are. If he decides wrong, well. Run then.
```
Subtitle: Not with words. But Greymuzzle's old and he isn't stupid. Go into the Hollow with no wolf blood on you, none since you last slept. Don't wear their skins. And don't run. He'll decide what you are. If he decides wrong, well. Run then.

### 11. `dlg.maeca.where.0.wav`

*Where:* dialogue.json maeca/where#0
*Played:* dry; doing: where to find her; pace: measured; volume: quiet.
*Note:* Plain directions; dry humour on 'fool enough' and 'Rav's piss'.

```
[dry, quietly] The Hunters' Blind, out past the wreck on the Old Road, most days. I watch the Hollow from there. You'll know it by the smoke; I'm the only one fool enough to light a fire in that wood. Nights, I'm here, drinking Rav's piss, and then I walk the captain home.
```
Subtitle: The Hunters' Blind, out past the wreck on the Old Road, most days. I watch the Hollow from there. You'll know it by the smoke; I'm the only one fool enough to light a fire in that wood. Nights, I'm here, drinking Rav's piss, and then I walk the captain home.

### 12. `dlg.maeca.thanks.0.wav`

*Where:* dialogue.json maeca/thanks#0
*Played:* moved, unaccustomed; doing: thanks you; pace: slow; volume: quiet.
*Wants:* you to know what it means
*Note:* Reporting the Hollow, steady. Then the confession, quieter. A long pause. 'Thank you.' barely said; she never says it.

```
[moved, unaccustomed, quietly] The Hollow's quiet. The Pack's eating again: deer, not travellers. I've been a hunter all my life, and I've never once saved anything. ...Thank you.
```
Subtitle: The Hollow's quiet. The Pack's eating again: deer, not travellers. I've been a hunter all my life, and I've never once saved anything. ...Thank you.

### 13. `dlg.maeca.cold.0.wav`

*Where:* dialogue.json maeca/cold#0
*Played:* contempt, hurt; doing: you killed the Pack; pace: slow; volume: quiet.
*Note:* Ice. The last line bitter and quiet.

```
[contempt, hurt, quietly] You emptied the Hollow. I heard. I hope Holloway's gold keeps you warm.
```
Subtitle: You emptied the Hollow. I heard. I hope Holloway's gold keeps you warm.

### 14. `dlg.maeca.gone.0.wav`

*Where:* dialogue.json maeca/gone#0
*Played:* betrayal, fury held down; doing: you killed Greymuzzle; pace: slow; volume: quiet.
*Note:* Each fragment its own blow. The voice never rises; the hurt is in the stillness. 'Get out of my light' through her teeth.

```
[betrayal, fury held down, quietly] You went to his house. In the dark. After I told you what he was to me. Get out of my light, and don't come to the Blind again.
```
Subtitle: You went to his house. In the dark. After I told you what he was to me. Get out of my light, and don't come to the Blind again.

### 15. `dlg.maeca.gone.1.wav`

*Where:* dialogue.json maeca/gone#1
*Played:* cold fury; doing: you killed Greymuzzle; pace: slow; volume: quiet.
*Note:* Each fragment its own blow, never raised.

```
[cold fury, quietly] You went to his house. In the dark. Get out of my light.
```
Subtitle: You went to his house. In the dark. Get out of my light.

### 16. `dlg.maeca.cb_burned_roost.0.wav`

*Where:* dialogue.json maeca/cb_burned_roost#0
*Played:* cold, haunted; doing: you burned people; pace: slow; volume: quiet.
*Note:* Flat and quiet. 'I was at Ashford.' three words, final.

```
[cold, haunted, quietly] You burned the Roost with them still in the cages. I know what fire does in a ravine. I was at Ashford.
```
Subtitle: You burned the Roost with them still in the cages. I know what fire does in a ravine. I was at Ashford.

### 17. `dlg.maeca.say_calling.0.wav`

*Where:* dialogue.json maeca/say_calling#0
*Played:* practical; doing: advice; pace: measured; volume: quiet.
*Note:* Hunter's instruction.

```
[practical, quietly] A shield. Good. Don't raise it in the Hollow. To a wolf a raised arm's a raised arm.
```
Subtitle: A shield. Good. Don't raise it in the Hollow. To a wolf a raised arm's a raised arm.

### 18. `dlg.maeca.say_calling.1.wav`

*Where:* dialogue.json maeca/say_calling#1
*Played:* practical; doing: advice; pace: measured; volume: quiet.
*Note:* Hunter's instruction.

```
[practical, quietly] Leave the big blade at the Blind if you go near the Hollow. They can smell iron that's been used.
```
Subtitle: Leave the big blade at the Blind if you go near the Hollow. They can smell iron that's been used.

### 19. `dlg.maeca.say_calling.2.wav`

*Where:* dialogue.json maeca/say_calling#2
*Played:* practical, grave; doing: advice; pace: measured; volume: quiet.
*Note:* 'Fire's the one thing they all remember.' with a shadow of Ashford.

```
[practical, grave, quietly] Whatever it is you burn with, don't burn it in the Hollow. Fire's the one thing they all remember.
```
Subtitle: Whatever it is you burn with, don't burn it in the Hollow. Fire's the one thing they all remember.

### 20. `dlg.maeca.say_calling.3.wav`

*The same words are also* `dlg.maeca.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json maeca/say_calling#3
*Played:* approving, dry; doing: notices your quiet feet; pace: measured; volume: quiet.
*Note:* A rare half-smile on 'Pity about the boots.'

```
[approving, dry, quietly] You walk like you've done this. Heel last, weight back. ...Who taught you? Not the Watch. The Watch walks like a dropped tray.
```
Subtitle: You walk like you've done this. Heel last, weight back. ...Who taught you? Not the Watch. The Watch walks like a dropped tray.

### 21. `dlg.maeca.invite.0.p1.wav`

*Where:* dialogue.json maeca/invite#0; part 2 of 2: narrator: She finishes her cup and stands. / **maeca: I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can…**
*Played:* understated invitation; doing: asks you to the Blind; pace: slow; volume: quiet.
*Wants:* company she can trust
*Note:* Plain and low, no flirtation. 'Most can't.' dry, a challenge.

```
[understated invitation, quietly] I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can't.
```
Subtitle: I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can't.

### 22. `dlg.maeca.blind.0.p1.wav`

*Where:* dialogue.json maeca/blind#0; part 2 of 3: narrator: Off in the Hollow the Pack is loud, a long tangle of voices, and she stops with her hands … / **maeca: They're eating.** / narrator: She pulls you down onto the hides. Her hands are hard and careful, the way they are with a…

```
They're eating.
```
Subtitle: They're eating.

### 23. `dlg.maeca.blind_morning.0.p1.wav`

*Where:* dialogue.json maeca/blind_morning#0; part 2 of 2: narrator: Grey light. She's already up, barefoot in the frost, listening. / **maeca: Go on, then. The wood's awake, and so's Holloway, and he'll count us both.**
*Played:* quiet warmth, dry; doing: morning after; pace: measured; volume: quiet.
*Note:* Narrator for the frost. Then softer than usual; dry joke on Holloway counting.

```
[quiet warmth, dry, quietly] Go on, then. The wood's awake, and so's Holloway, and he'll count us both.
```
Subtitle: Go on, then. The wood's awake, and so's Holloway, and he'll count us both.

### 24. `dlg.maeca.blind_morning.1.p1.wav`

*Where:* dialogue.json maeca/blind_morning#1; part 2 of 2: narrator: Grey light. She's already up, barefoot in the frost, listening to the wood. / **maeca: The Pack found me, after Ashford. Three days, and then a cave mouth, and a lad I'd been fo…**
*Played:* confession, raw but steady; doing: tells you why she never hunts wolves; pace: slow; volume: quiet.
*Wants:* you to know, and not to pity her
*Note:* Narrator for the frost. The story told plainly, present tense feel. 'Kept everything off.' near breaking. A pause. 'That's all of why.' firm. 'Don't make it a story.' a plea disguised as an order.

```
[confession, raw but steady, quietly] The Pack found me, after Ashford. Three days, and then a cave mouth, and a lad I'd been fond of dying in it. The old grey one came and lay down across the way in. Kept the cold off. Kept everything off. ...That's why. That's all of why. Don't make it a story.
```
Subtitle: The Pack found me, after Ashford. Three days, and then a cave mouth, and a lad I'd been fond of dying in it. The old grey one came and lay down across the way in. Kept the cold off. Kept everything off. ...That's why. That's all of why. Don't make it a story.

### 25. `dlg.maeca.cb_broke_promise.0.wav`

*Where:* dialogue.json maeca/cb_broke_promise#0
*Played:* cold contempt, grief; doing: you betrayed the Pack; pace: slow; volume: quiet.
*Note:* Three plain statements, cold. Pause. The last line quiet and final.

```
[cold contempt, grief, quietly] You knelt to him. You held out your hand and he let you in. Then you killed his. ...I've nothing to say to you that I'd want to have said.
```
Subtitle: You knelt to him. You held out your hand and he let you in. Then you killed his. ...I've nothing to say to you that I'd want to have said.

### 26. `dlg.maeca.t_maeca.0.wav`

*Where:* dialogue.json maeca/t_maeca#0
*Played:* dry, grim; doing: what she hunted; pace: measured; volume: quiet.
*Note:* Deadpan; a grim joke about men on paths.

```
[dry, grim, quietly] Men, for the garrison. Deer, for me. Men are easier. They keep to paths and they talk while they walk.
```
Subtitle: Men, for the garrison. Deer, for me. Men are easier. They keep to paths and they talk while they walk.

### 27. `dlg.maeca.kerchiefs.0.p0.wav`

*Where:* dialogue.json maeca/kerchiefs#0; part 1 of 3: **maeca: Some.** / narrator: She drinks, and looks at the cup instead of you. / maeca: Fed some of them, once. Buried more. ...Ask me about wolves.
*Played:* guarded grief; doing: won't talk about them; pace: slow; volume: quiet.
*Note:* 'Some.' Narrator for the cup. 'Fed some of them, once. Buried more.' heavy. 'Ask me about wolves.' a closing door.

```
[guarded grief, quietly] Some.
```
Subtitle: Some.

### 28. `dlg.maeca.kerchiefs.0.p2.wav`

*Where:* dialogue.json maeca/kerchiefs#0; part 3 of 3: maeca: Some. / narrator: She drinks, and looks at the cup instead of you. / **maeca: Fed some of them, once. Buried more. ...Ask me about wolves.**
*Played:* guarded grief; doing: won't talk about them; pace: slow; volume: quiet.
*Note:* 'Some.' Narrator for the cup. 'Fed some of them, once. Buried more.' heavy. 'Ask me about wolves.' a closing door.

```
[guarded grief, quietly] Fed some of them, once. Buried more. ...Ask me about wolves.
```
Subtitle: Fed some of them, once. Buried more. ...Ask me about wolves.

### 29. `dlg.maeca.cb_knelt.0.p0.wav`

*Where:* dialogue.json maeca/cb_knelt#0; part 1 of 3: **maeca: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge.** / narrator: She looks at your knees. / maeca: He let you. ...He doesn't let me, and he's known me ten years.
*Played:* quiet wonder, a little jealous; doing: she saw you kneel to Greymuzzle; pace: slow; volume: quiet.
*Note:* Narrator for the look at your knees. 'He let you.' amazed. The last sentence hurt, plain.

```
[quiet wonder, a little jealous, quietly] You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge.
```
Subtitle: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge.

### 30. `dlg.maeca.cb_knelt.0.p2.wav`

*Where:* dialogue.json maeca/cb_knelt#0; part 3 of 3: maeca: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge. / narrator: She looks at your knees. / **maeca: He let you. ...He doesn't let me, and he's known me ten years.**
*Played:* quiet wonder, a little jealous; doing: she saw you kneel to Greymuzzle; pace: slow; volume: quiet.
*Note:* Narrator for the look at your knees. 'He let you.' amazed. The last sentence hurt, plain.

```
[quiet wonder, a little jealous, quietly] He let you. ...He doesn't let me, and he's known me ten years.
```
Subtitle: He let you. ...He doesn't let me, and he's known me ten years.

### 31. `dlg.maeca.blood.0.p1.wav`

*Where:* dialogue.json maeca/blood#0; part 2 of 2: narrator: At the edge of the Hollow she stops, and sniffs, once, and turns round. / **maeca: Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night ta…**
*Played:* flat warning, then kind; doing: you smell of wolf blood; pace: measured; volume: quiet.
*Note:* Narrator: she stops and sniffs. Curt orders. 'It took it off me.' quiet, a confession.

```
[flat warning, then kind, quietly] Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night takes it off. It took it off me.
```
Subtitle: Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night takes it off. It took it off me.

### 32. `dlg.maeca.blind_walk.0.p1.wav`

*Where:* dialogue.json maeca/blind_walk#0; part 2 of 3: narrator: She goes out by the east gate without a lamp, and you follow her along the Old Road past t… / **maeca: Him. And the bitch with the white foot.** / narrator: She walks on.
*Played:* plain; doing: the walk to the Blind; pace: slow; volume: quiet.
*Note:* Narrator plain and starlit; a beat before 'and is answered'. Maeca just above a breath, naming neighbours by their voices. Narrator plain: the narrator never shows a feeling.

```
[plain, quietly] Him… And the bitch with the white foot.
```
Subtitle: Him. And the bitch with the white foot.

### 33. `dlg.maeca.blind_ask.0.wav`

*Where:* dialogue.json maeca/blind_ask#0
*Played:* dry, guarded; doing: terms for the night; pace: measured; volume: quiet.
*Note:* Deadpan; almost a smile.

```
[dry, guarded, quietly] If you're going to talk after, don't.
```
Subtitle: If you're going to talk after, don't.

### 34. `dlg.maeca.blind_leave.0.p1.wav`

*Where:* dialogue.json maeca/blind_leave#0; part 2 of 2: narrator: She nods at the fire. / **maeca: Mind the frost on the Old Road. It's worse by the wreck.**
*Played:* practical tenderness; doing: sends you off safe; pace: measured; volume: quiet.
*Note:* Care disguised as a road report.

```
[practical tenderness, quietly] Mind the frost on the Old Road. It's worse by the wreck.
```
Subtitle: Mind the frost on the Old Road. It's worse by the wreck.

### 35. `dlg.maeca.watch_morning.0.p0.wav`

*Where:* dialogue.json maeca/watch_morning#0; part 1 of 3: **maeca: You kept quiet.** / narrator: She stands, and stretches, and looks at the Hollow, not you. / maeca: Most can't.
*Played:* approving, dry; doing: you kept the watch; pace: slow; volume: quiet.
*Note:* Narrator for the stretch. 'Most can't.' a small compliment.

```
[approving, dry, quietly] You kept quiet.
```
Subtitle: You kept quiet.

### 36. `dlg.maeca.watch_morning.0.p2.wav`

*Where:* dialogue.json maeca/watch_morning#0; part 3 of 3: maeca: You kept quiet. / narrator: She stands, and stretches, and looks at the Hollow, not you. / **maeca: Most can't.**
*Played:* approving, dry; doing: you kept the watch; pace: slow; volume: quiet.
*Note:* Narrator for the stretch. 'Most can't.' a small compliment.

```
[approving, dry, quietly] Most can't.
```
Subtitle: Most can't.

### 37. `dlg.maeca.blind_dark.1.p1.wav`

*Where:* dialogue.json maeca/blind_dark#1; part 2 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / **maeca: They don't do that. Not for me. Not for anyone.** / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* plain; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[plain, quietly] They don't do that… Not for me. Not for anyone.
```
Subtitle: They don't do that. Not for me. Not for anyone.

### 38. `dlg.maeca.blind_dark.1.p3.wav`

*Where:* dialogue.json maeca/blind_dark#1; part 4 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / **maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a…** / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* plain; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[plain, quietly] You walk quiet. You came into my Hollow and knelt to him, and he let you… You never talk about before.
```
Subtitle: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk about before.

### 39. `dlg.maeca.blind_dark.1.p5.wav`

*The same words are also* `dlg.maeca.blind_dark.2.p3.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json maeca/blind_dark#1; part 6 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / **maeca: What were you?**
*Played:* plain; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[plain, quietly] [long pause] What were you?
```
Subtitle: What were you?

### 40. `dlg.maeca.blind_dark.2.p1.wav`

*Where:* dialogue.json maeca/blind_dark#2; part 2 of 4: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / **maeca: You walk quiet. You never talk about before.** / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* plain; doing: she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences
*Note:* As blind_dark.1 without the Pack. 'What were you?' careful, no stress on 'were', after a real count of about three seconds.

```
[plain, quietly] You walk quiet. You never talk about before.
```
Subtitle: You walk quiet. You never talk about before.

### 41. `dlg.maeca.blind2_feet.0.p1.wav`

*Where:* dialogue.json maeca/blind2_feet#0; part 2 of 4: narrator: You take one in your hands. The sole is hard as boot leather, and scarred: old white lines… / **maeca: Your hands are colder than my feet.** / narrator: She doesn't take them back. / maeca: Hold them anyway. ...Nobody's held those.
*Played:* plain; doing: her scarred feet; pace: slow; volume: quiet.
*Note:* The scars described plainly; her words are hers.

```
[plain, quietly] Your hands are colder than my feet.
```
Subtitle: Your hands are colder than my feet.

### 42. `dlg.maeca.blind2_feet.0.p3.wav`

*Where:* dialogue.json maeca/blind2_feet#0; part 4 of 4: narrator: You take one in your hands. The sole is hard as boot leather, and scarred: old white lines… / maeca: Your hands are colder than my feet. / narrator: She doesn't take them back. / **maeca: Hold them anyway. ...Nobody's held those.**
*Played:* plain; doing: her scarred feet; pace: slow; volume: quiet.
*Note:* The scars described plainly; her words are hers.

```
[plain, quietly] Hold them anyway. ...Nobody's held those.
```
Subtitle: Hold them anyway. ...Nobody's held those.

### 43. `dlg.maeca.told_true.0.p0.wav`

*Where:* dialogue.json maeca/told_true#0; part 1 of 3: **maeca: Thought so. You put your feet down like you're asking the ground first.** / narrator: She almost smiles. / maeca: I'd have liked you, then. Probably would have shot you for poaching.
*Played:* warm, wry; doing: you were a hunter; pace: measured; volume: quiet.
*Note:* Narrator: she almost smiles. The poaching joke fond.

```
[warm, wry, quietly] Thought so. You put your feet down like you're asking the ground first.
```
Subtitle: Thought so. You put your feet down like you're asking the ground first.

### 44. `dlg.maeca.told_true.0.p2.wav`

*Where:* dialogue.json maeca/told_true#0; part 3 of 3: maeca: Thought so. You put your feet down like you're asking the ground first. / narrator: She almost smiles. / **maeca: I'd have liked you, then. Probably would have shot you for poaching.**
*Played:* warm, wry; doing: you were a hunter; pace: measured; volume: quiet.
*Note:* Narrator: she almost smiles. The poaching joke fond.

```
[warm, wry, quietly] I'd have liked you, then. Probably would have shot you for poaching.
```
Subtitle: I'd have liked you, then. Probably would have shot you for poaching.

### 45. `dlg.maeca.told_true.1.p0.wav`

*Where:* dialogue.json maeca/told_true#1; part 1 of 3: **maeca: Letters.** / narrator: She thinks about it. / maeca: Tracks for people who sit still. ...Read me something, one day. Not now.
*Played:* curious, soft; doing: you were a scholar; pace: slow; volume: quiet.
*Note:* Thinking. 'Read me something, one day.' shy, then 'Not now.' quick.

```
[curious, soft, quietly] Letters.
```
Subtitle: Letters.

### 46. `dlg.maeca.told_true.1.p2.wav`

*Where:* dialogue.json maeca/told_true#1; part 3 of 3: maeca: Letters. / narrator: She thinks about it. / **maeca: Tracks for people who sit still. ...Read me something, one day. Not now.**
*Played:* curious, soft; doing: you were a scholar; pace: slow; volume: quiet.
*Note:* Thinking. 'Read me something, one day.' shy, then 'Not now.' quick.

```
[curious, soft, quietly] Tracks for people who sit still. ...Read me something, one day. Not now.
```
Subtitle: Tracks for people who sit still. ...Read me something, one day. Not now.

### 47. `dlg.maeca.told_true.2.wav`

*Where:* dialogue.json maeca/told_true#2
*Played:* respect; doing: you walked away; pace: measured; volume: quiet.
*Note:* Plain respect, with Ashford under it.

```
[respect, quietly] Walking away's a skill. Most never learn it. They stay till it's too late, out of pride.
```
Subtitle: Walking away's a skill. Most never learn it. They stay till it's too late, out of pride.

### 48. `dlg.maeca.told_true.3.wav`

*Where:* dialogue.json maeca/told_true#3
*Played:* kinship, grief; doing: you lit lamps for nobody; pace: slow; volume: quiet.
*Note:* Narrator: a long breath. The cave mouth line very quiet. 'We'd have got on.' tender.

```
[kinship, grief, quietly] Lamps. Nobody coming. [a long breath] I held a cave mouth three days for nobody coming. We'd have got on.
```
Subtitle: Lamps. Nobody coming. I held a cave mouth three days for nobody coming. We'd have got on.

### 49. `dlg.maeca.told_little.0.p1.wav`

*Where:* dialogue.json maeca/told_little#0; part 2 of 4: narrator: She doesn't push. / **maeca: All right.** / narrator: And it is. / maeca: ...Keep it, then. I keep mine.
*Played:* accepting; doing: she doesn't push; pace: slow; volume: quiet.
*Note:* Narrator around her. 'I keep mine.' kind.

```
[accepting, quietly] All right.
```
Subtitle: All right.

### 50. `dlg.maeca.told_little.0.p3.wav`

*Where:* dialogue.json maeca/told_little#0; part 4 of 4: narrator: She doesn't push. / maeca: All right. / narrator: And it is. / **maeca: ...Keep it, then. I keep mine.**
*Played:* accepting; doing: she doesn't push; pace: slow; volume: quiet.
*Note:* Narrator around her. 'I keep mine.' kind.

```
[accepting, quietly] ...Keep it, then. I keep mine.
```
Subtitle: ...Keep it, then. I keep mine.

### 51. `dlg.maeca.blind3_morning.0.p1.wav`

*Where:* dialogue.json maeca/blind3_morning#0; part 2 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / **maeca: Your heart's going like a hare's.** / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* tender, frightened, hiding it; doing: she heard your heart change; pace: slow; volume: hushed.
*Note:* Narrator: grey light, her head on your chest. Close and still: the hare and the bear. 'I counted between.' A pause where the name would be. Narrator: she goes out. 'Go on. Holloway'll count us.' steadier.

```
[tender, frightened, hiding it, whispers] Your heart's going like a hare's.
```
Subtitle: Your heart's going like a hare's.

### 52. `dlg.maeca.blind3_morning.0.p3.wav`

*Where:* dialogue.json maeca/blind3_morning#0; part 4 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / **maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot…** / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* tender, frightened, hiding it; doing: she heard your heart change; pace: slow; volume: hushed.
*Note:* Narrator: grey light, her head on your chest. Close and still: the hare and the bear. 'I counted between.' A pause where the name would be. Narrator: she goes out. 'Go on. Holloway'll count us.' steadier.

```
[tender, frightened, hiding it, whispers] All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot of things to see if they'd live.
```
Subtitle: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot of things to see if they'd live.

### 53. `dlg.maeca.blind3_morning.0.p5.wav`

*Where:* dialogue.json maeca/blind3_morning#0; part 6 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / **maeca: Go on. Holloway'll count us.**
*Played:* tender, frightened, hiding it; doing: she heard your heart change; pace: slow; volume: hushed.
*Note:* Narrator: grey light, her head on your chest. Close and still: the hare and the bear. 'I counted between.' A pause where the name would be. Narrator: she goes out. 'Go on. Holloway'll count us.' steadier.

```
[tender, frightened, hiding it, whispers] Go on. Holloway'll count us.
```
Subtitle: Go on. Holloway'll count us.

### 54. `dlg.maeca.blind3_m_no.0.wav`

*Where:* dialogue.json maeca/blind3_m_no#0
*Played:* gentle refusal; doing: not yet; pace: slow; volume: quiet.
*Note:* 'No.' Narrator: not unkind. Her old rule, softened.

```
[gentle refusal, quietly] No. [not unkind] Don't make it a story. Not yet.
```
Subtitle: No. Don't make it a story. Not yet.

### 55. `dlg.maeca.say_sella.0.p0.wav`

*Where:* dialogue.json maeca/say_sella#0; part 1 of 3: **maeca: You go up Sella's stairs.** / narrator: She doesn't look up from her cup. / maeca: Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind n…
*Played:* plain, exposed; doing: asks about Sella; pace: slow; volume: quiet.
*Note:* Narrator: the cup. Level. 'I mind not knowing.' honest and quiet.

```
[plain, exposed, quietly] You go up Sella's stairs.
```
Subtitle: You go up Sella's stairs.

### 56. `dlg.maeca.say_sella.0.p2.wav`

*Where:* dialogue.json maeca/say_sella#0; part 3 of 3: maeca: You go up Sella's stairs. / narrator: She doesn't look up from her cup. / **maeca: Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind n…**
*Played:* plain, exposed; doing: asks about Sella; pace: slow; volume: quiet.
*Note:* Narrator: the cup. Level. 'I mind not knowing.' honest and quiet.

```
[plain, exposed, quietly] Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind not knowing.
```
Subtitle: Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind not knowing.

### 57. `dlg.maeca.say_sella.1.p0.wav`

*Where:* dialogue.json maeca/say_sella#1; part 1 of 3: **maeca: You go up Sella's stairs. Rook talks.** / narrator: A shrug. / maeca: She's honest about what she charges. That's more than most.
*Played:* dry, fair; doing: Sella's honest; pace: measured; volume: quiet.
*Note:* Narrator: a shrug. Fair-minded.

```
[dry, fair, quietly] You go up Sella's stairs. Rook talks.
```
Subtitle: You go up Sella's stairs. Rook talks.

### 58. `dlg.maeca.say_sella.1.p2.wav`

*Where:* dialogue.json maeca/say_sella#1; part 3 of 3: maeca: You go up Sella's stairs. Rook talks. / narrator: A shrug. / **maeca: She's honest about what she charges. That's more than most.**
*Played:* dry, fair; doing: Sella's honest; pace: measured; volume: quiet.
*Note:* Narrator: a shrug. Fair-minded.

```
[dry, fair, quietly] She's honest about what she charges. That's more than most.
```
Subtitle: She's honest about what she charges. That's more than most.

### 59. `dlg.maeca.say_sella_both.0.p1.wav`

*Where:* dialogue.json maeca/say_sella_both#0; part 2 of 2: narrator: A nod. / **maeca: Good. Now I know.**
*Played:* settled; doing: now she knows; pace: measured; volume: quiet.

```
[settled, quietly] Good. Now I know.
```
Subtitle: Good. Now I know.

### 60. `dlg.maeca.say_sella_you.0.p1.wav`

*Where:* dialogue.json maeca/say_sella_you#0; part 2 of 2: narrator: She looks at you, long, the way she looks at a track that might be lying. / **maeca: We'll see.**
*Played:* wary hope; doing: we'll see; pace: slow; volume: quiet.
*Note:* Narrator for the long look. 'We'll see.' guarded.

```
[wary hope, quietly] We'll see.
```
Subtitle: We'll see.

### 61. `dlg.maeca.say_sella_dunno.0.wav`

*Where:* dialogue.json maeca/say_sella_dunno#0
*Played:* dry acceptance; doing: an answer of sorts; pace: measured; volume: quiet.

```
[dry acceptance, quietly] That's an answer.
```
Subtitle: That's an answer.

### 62. `dlg.maeca.shed_fur_offer.0.wav`

*Where:* dialogue.json maeca/shed_fur_offer#0

```
They've been leaving fur on the thorn by the Blind. For you, I think. Give me an evening.
```
Subtitle: They've been leaving fur on the thorn by the Blind. For you, I think. Give me an evening.

### 63. `dlg.maeca.shed_fur_braid.0.p1.wav`

*Where:* dialogue.json maeca/shed_fur_braid#0; part 2 of 2: narrator: She sits with her back to the fire and braids it on her knee, grey and grey and white, the… / **maeca: Next to the skin. They'll know you in the dark.**

```
Next to the skin. They'll know you in the dark.
```
Subtitle: Next to the skin. They'll know you in the dark.

### 64. `dlg.maeca.fire.0.p1.wav`

*Where:* dialogue.json maeca/fire#0; part 2 of 2: narrator: She looks at you for a long time. / **maeca: If you're going in there with a blade, I'll not help you. ...Take fire, and feed it. They …**

```
If you're going in there with a blade, I'll not help you. ...Take fire, and feed it. They won't come near a fire that's fed. That's not for your sake. It's so they don't have to.
```
Subtitle: If you're going in there with a blade, I'll not help you. ...Take fire, and feed it. They won't come near a fire that's fed. That's not for your sake. It's so they don't have to.

### 65. `dlg.maeca.watch.0.p0.wav`

*Where:* dialogue.json maeca/watch#0; part 1 of 3: **maeca: Men. Deserters, mostly, and the ones the road loses. The Watch won't pay for it, so Hollow…** / narrator: She drinks. / maeca: I take it. Every week. ...He'd pay me double, if I let him. I don't let him.
*Played:* flat, a little proud; doing: says who pays her; pace: measured; volume: quiet.
*Wants:* nothing from you
*Hides:* every week she takes his money and buys his drink with it, and she is waiting
*Note:* Plain. 'I take it. Every week.' a fact, not a confession. 'I don't let him.' the only warmth, and it is not warmth.

```
[flat, a little proud, quietly] Men. Deserters, mostly, and the ones the road loses. The Watch won't pay for it, so Holloway does, out of his own pocket.
```
Subtitle: Men. Deserters, mostly, and the ones the road loses. The Watch won't pay for it, so Holloway does, out of his own pocket.

### 66. `dlg.maeca.watch.0.p2.wav`

*Where:* dialogue.json maeca/watch#0; part 3 of 3: maeca: Men. Deserters, mostly, and the ones the road loses. The Watch won't pay for it, so Hollow… / narrator: She drinks. / **maeca: I take it. Every week. ...He'd pay me double, if I let him. I don't let him.**
*Played:* flat, a little proud; doing: says who pays her; pace: measured; volume: quiet.
*Wants:* nothing from you
*Hides:* every week she takes his money and buys his drink with it, and she is waiting
*Note:* Plain. 'I take it. Every week.' a fact, not a confession. 'I don't let him.' the only warmth, and it is not warmth.

```
[flat, a little proud, quietly] I take it. Every week. ...He'd pay me double, if I let him. I don't let him.
```
Subtitle: I take it. Every week. ...He'd pay me double, if I let him. I don't let him.

### 67. `dlg.maeca.ashford.0.p1.wav`

*Where:* dialogue.json maeca/ashford#0; part 2 of 2: narrator: She doesn't look up from her cup. / **maeca: The cave mouths.**
*Played:* nothing; doing: closes the subject; pace: slow; volume: quiet.
*Wants:* the subject shut
*Hides:* she was on the ladder, the next hand up, number ninety-two
*Note:* Three words, to the cup. No weight on any of them. It is her post, and his report's lie.

```
[nothing, quietly] The cave mouths.
```
Subtitle: The cave mouths.

## Conversations: Scene_gate_dawn

### 68. `dlg.scene_gate_dawn.maeca.0.wav`

*Where:* dialogue.json scene_gate_dawn/maeca#0

```
[a nod at him] Waits up for you. [a beat] Somebody waits up for him.
```
Subtitle: Waits up for you. Somebody waits up for him.

### 69. `dlg.scene_gate_dawn.last.0.wav`

*Where:* dialogue.json scene_gate_dawn/last#0

```
That's your last.
```
Subtitle: That's your last.

## Conversations: Scene_did_he

### 70. `dlg.scene_did_he.well.0.p1.wav`

*Where:* dialogue.json scene_did_he/well#0; part 2 of 2: narrator: She's waiting for you at the well, which she never does. / **maeca: He talked to you. Last night. At the gate.**

```
He talked to you. Last night. At the gate.
```
Subtitle: He talked to you. Last night. At the gate.

### 71. `dlg.scene_did_he.did.0.wav`

*Where:* dialogue.json scene_did_he/did#0

```
...Did he.
```
Subtitle: ...Did he.

## Said in passing

### 72. `bark.maeca.day.0.wav`

*Where:* npcs.json maeca.barks[0]
*Played:* terse; pace: measured; volume: quiet.

```
[terse, quietly] Mind the east road after dark.
```
Subtitle: Mind the east road after dark.

### 73. `bark.maeca.night.0.wav`

*Where:* npcs.json maeca.nightBarks[0]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] Hear that? No. Neither do I. That's what worries me.
```
Subtitle: Hear that? No. Neither do I. That's what worries me.

### 74. `bark.maeca.night.1.wav`

*Where:* npcs.json maeca.nightBarks[1]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] One more, then I sleep.
```
Subtitle: One more, then I sleep.

### 75. `bark.maeca.said.0.wav`

*Where:* npcs.json maeca.said[0]
*Played:* certain, quiet; doing: the wolves are running; pace: measured; volume: quiet.
*Note:* Half-voice, plain fact.

```
[certain, quiet, quietly] They're not hunting. They're running.
```
Subtitle: They're not hunting. They're running.

### 76. `bark.maeca.said.1.wav`

*Where:* npcs.json maeca.said[1]
*Played:* uneasy, watchful; doing: the wood is wrong; pace: measured; volume: quiet.
*Note:* Listening while she says it.

```
[uneasy, watchful, quietly] Something's got the whole wood on edge.
```
Subtitle: Something's got the whole wood on edge.

### 77. `bark.maeca.said.2.wav`

*Where:* npcs.json maeca.said[2]
*Played:* quiet, attentive; doing: the Pack tonight; pace: measured; volume: quiet.
*Note:* Neighbours, not beasts.

```
[quiet, attentive, quietly] The Pack's loud tonight.
```
Subtitle: The Pack's loud tonight.

### 78. `bark.maeca.said.3.wav`

*Where:* npcs.json maeca.said[3]
*Played:* attentive, tender; doing: an old wolf coughing; pace: slow; volume: quiet.
*Note:* 'Listen.' almost a whisper.

```
[attentive, tender, quietly] Somewhere out there an old wolf's coughing. Listen.
```
Subtitle: Somewhere out there an old wolf's coughing. Listen.

### 79. `bark.maeca.said.4.wav`

*Where:* npcs.json maeca.said[4]
*Played:* quiet satisfaction; doing: the Pack hunts again; pace: measured; volume: quiet.
*Note:* 'Deer.' a small, private pleasure.

```
[quiet satisfaction, quietly] Hear that? They're hunting again. Deer.
```
Subtitle: Hear that? They're hunting again. Deer.

### 80. `bark.maeca.said.5.wav`

*Where:* npcs.json maeca.said[5]
*Played:* plain, protective; doing: the Pack lying up; pace: measured; volume: quiet.
*Note:* 'Leave them be.' quiet and final.

```
[plain, protective, quietly] The Pack's lying up by the east wall. Leave them be.
```
Subtitle: The Pack's lying up by the east wall. Leave them be.

### 81. `bark.maeca.said.6.wav`

*Where:* npcs.json maeca.said[6]
*Played:* flat, hollow; doing: the Hollow is empty; pace: slow; volume: quiet.
*Note:* The second 'Nothing.' quieter. No tears in it.

```
[flat, hollow, quietly] Nothing calls in the Hollow now.
```
Subtitle: Nothing calls in the Hollow now.

### 82. `bark.maeca.said.7.wav`

*Where:* npcs.json maeca.said[7]

```
Heard you out by the Hollow last night. From the Blind. How many?
```
Subtitle: Heard you out by the Hollow last night. From the Blind. How many?

### 83. `bark.maeca.said.8.wav`

*Where:* npcs.json maeca.said[8]

```
Mine don't run at fire. Whatever came at you last night wasn't mine.
```
Subtitle: Mine don't run at fire. Whatever came at you last night wasn't mine.

### 84. `bark.maeca.said.9.wav`

*Where:* npcs.json maeca.said[9]

```
There's no Pack left. I counted the pelts. So what were you killing?
```
Subtitle: There's no Pack left. I counted the pelts. So what were you killing?

### 85. `bark.maeca.said.10.wav`

*Where:* npcs.json maeca.said[10]

```
That's his. Wear it where I can't see it.
```
Subtitle: That's his. Wear it where I can't see it.

### 86. `bark.maeca.said.11.wav`

*Where:* npcs.json maeca.said[11]

```
Heard you go down in the Hollow. Heard them walk away after. They don't leave meat.
```
Subtitle: Heard you go down in the Hollow. Heard them walk away after. They don't leave meat.

### 87. `bark.maeca.said.12.wav`

*Where:* npcs.json maeca.said[12]

```
Heard you let the red one walk. ...Good.
```
Subtitle: Heard you let the red one walk. ...Good.


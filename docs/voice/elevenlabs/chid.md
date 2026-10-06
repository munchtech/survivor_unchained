# Chid: ElevenLabs packet

Voice id in the game: `chid`. 75 takes to record (8,438 characters; about 25,314 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

**Hold 2 of these** (marked HOLD below, with why); the rest can be recorded now.

## Who they are

**Chid** ("the Fool"). Light, breathless, delighted; exclamations; sentences that run on and double back. Theology in plain words, and now and then a line that is far older than he looks, which he does not notice saying. Never cynical; never says how old he is (once, in Act 3, and only if asked who else knew what the lamps were for, the plainest thing he ever says: "I go when the lamps are lit. I couldn't have stopped it. I didn't try. I wanted to see one get up."). *Casting:* sounds 30s, Irish- tinged; the voice catches on joy.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Chid`. Never describe a voice as sounding like a real person.

```
Native English (British, Irish). Male, 30s. Studio quality. Persona: a gentle priest. A man who sounds in his thirties, a gentle priest with a light, bright Irish accent. A light, breathless, delighted tenor that runs on and doubles back, catching with joy; kind, earnest and a little foolish. Light Irish accent. No reverb or effects.
```

Preview text:

```
Oh! A visitor. Hello! I'm Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. It used to work. It might again!
```

In the Voice Library instead: search for *Irish-tinged*, *male*, *30*, and listen for this: A man who sounds in his thirties, a gentle priest with a light, bright Irish accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_iron_marker.verse1.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice chid
```

## Saying the names

The text to paste already respells these; keep the respelling: Aumery as *Awmery*, Brannoc as *Brannock*, Maeca as *Mayka*, Vonnra as *Vonra*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: iron marker

### 1. `dlg.cin_iron_marker.verse1.0.wav`  HOLD: the owner's choice of how the hymn is sung (README)

*Where:* dialogue.json cin_iron_marker/verse1#0
*Played:* tender, out of tune; doing: Chid sings at Nell's grave; pace: slow; volume: quiet.
*Note:* Sung simply and not well; he can't sing and nobody minds.

```
[tender, out of tune, quietly] [singing] Lie down, lie down, the lamps are tended, / and all the dark is kept; / the morning lies a little under, / and it will wake you where you slept.
```
Subtitle: Lie down, lie down, the lamps are tended, / and all the dark is kept; / the morning lies a little under, / and it will wake you where you slept.

### 2. `dlg.cin_iron_marker.verse2.0.wav`  HOLD: the owner's choice of how the hymn is sung (README)

*Where:* dialogue.json cin_iron_marker/verse2#0
*Played:* tender, out of tune; doing: Chid sings at Nell's grave; pace: slow; volume: quiet.
*Note:* As verse1.

```
[tender, out of tune, quietly] [singing] Lie down, lie down, the road is ended, / your toll is paid and kept; / the dark is but the day not risen, / and it will wake you where you slept.
```
Subtitle: Lie down, lie down, the road is ended, / your toll is paid and kept; / the dark is but the day not risen, / and it will wake you where you slept.

## Conversations: Chid

### 3. `dlg.chid.first.0.wav`

*Where:* dialogue.json chid/first#0
*Played:* overjoyed surprise; doing: greets a fellow of his dead Order; pace: quick; volume: raised.
*Wants:* company, a lit Order lamp, family
*Hides:* what he is, how old, what the lamps burn
*Note:* The catch of joy on 'Lit!'. No rue on 'which is fair': he likes the name, and the laugh is delight on the out-breath. 'It used to work.' cheerful and practical, like a man reporting a broken pump; the sadness belongs to the listener. Chid is never cynical and never self-pitying.

```
[overjoyed surprise, loudly] Oh!… A lantern of the Order! [inhales] Lit! Oh, sit down, sit, sit. I'm Chid. They call me the Fool, which is fair. [laughs] This is the shrine of the Morning Light… It used to work.
```
Subtitle: Oh! A lantern of the Order! Lit! Oh, sit down, sit, sit. I'm Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. It used to work.

### 4. `dlg.chid.first.1.wav`

*Where:* dialogue.json chid/first#1
*Played:* delighted surprise; doing: greets a visitor; pace: quick; volume: level.
*Wants:* company
*Hides:* what he is, how old, what the lamps burn
*Note:* Bright 'Oh!'. He likes the name 'the Fool'; the laugh is delight. 'It used to work.' cheerful and practical.

```
[delighted surprise] Oh! A visitor… Hello! I'm Chid. They call me the Fool, which is fair. [laughs] This is the shrine of the Morning Light… It used to work.
```
Subtitle: Oh! A visitor. Hello! I'm Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. It used to work.

### 5. `dlg.chid.hub.0.wav`

*Where:* dialogue.json chid/hub#0
*Played:* giddy pride; doing: the shrine still burns; pace: quick; volume: level.
*Note:* Can't keep it in. Second 'Still burning.' softer, to himself, amazed.

```
[giddy pride] It's still burning! Every morning I check. Still burning.
```
Subtitle: It's still burning! Every morning I check. Still burning.

### 6. `dlg.chid.hub.1.wav`

*Where:* dialogue.json chid/hub#1
*Played:* cheerful, gently rueful; doing: welcomes you back; pace: measured; volume: level.
*Note:* Light joke at his own expense on 'I'm trying to be.'

```
[cheerful, gently rueful] Hello again! The light's patient. I'm trying to be.
```
Subtitle: Hello again! The light's patient. I'm trying to be.

### 7. `dlg.chid.woke.0.p0.wav`

*Where:* dialogue.json chid/woke#0; part 1 of 3: **chid: Up again.** / narrator: He has the kettle on already. / chid: The carter sends his regards. You'll be sore a day or two. Whatever did it has your things…
*Played:* relieved joy, then gentle worry; doing: you woke after dying; pace: quick then slower; volume: level.
*Wants:* you to rest and believe the flame saved you
*Note:* 'Good. Good!' overflowing. Awe and a catch on 'the flame... the flame kept you'. Quieter and serious for the warning; 'They always keep something' with old knowledge he doesn't notice.

```
[relieved joy, then gentle worry] Up again.
```
Subtitle: Up again.

### 8. `dlg.chid.woke.0.p2.wav`

*Where:* dialogue.json chid/woke#0; part 3 of 3: chid: Up again. / narrator: He has the kettle on already. / **chid: The carter sends his regards. You'll be sore a day or two. Whatever did it has your things…**
*Played:* relieved joy, then gentle worry; doing: you woke after dying; pace: quick then slower; volume: level.
*Wants:* you to rest and believe the flame saved you
*Note:* 'Good. Good!' overflowing. Awe and a catch on 'the flame... the flame kept you'. Quieter and serious for the warning; 'They always keep something' with old knowledge he doesn't notice.

```
[relieved joy, then gentle worry] The carter sends his regards. You'll be sore a day or two. Whatever did it has your things.
```
Subtitle: The carter sends his regards. You'll be sore a day or two. Whatever did it has your things.

### 9. `dlg.chid.woke.1.p0.wav`

*Where:* dialogue.json chid/woke#1; part 1 of 3: **chid: You're up. A carter brought you in.** / narrator: He isn't looking at you. / chid: ...Well. Someone did. You'll be sore a day or two, and whatever did this still has your th…
*Played:* relieved, flustered; doing: you woke after dying; pace: measured; volume: quiet.
*Wants:* you to rest
*Note:* Gentle; trails off on 'and... well.' with an embarrassed little laugh. Serious and quiet for the warning.

```
[relieved, flustered, quietly] You're up. A carter brought you in.
```
Subtitle: You're up. A carter brought you in.

### 10. `dlg.chid.woke.1.p2.wav`

*Where:* dialogue.json chid/woke#1; part 3 of 3: chid: You're up. A carter brought you in. / narrator: He isn't looking at you. / **chid: ...Well. Someone did. You'll be sore a day or two, and whatever did this still has your th…**
*Played:* relieved, flustered; doing: you woke after dying; pace: measured; volume: quiet.
*Wants:* you to rest
*Note:* Gentle; trails off on 'and... well.' with an embarrassed little laugh. Serious and quiet for the warning.

```
[relieved, flustered, quietly] ...Well. Someone did. You'll be sore a day or two, and whatever did this still has your things.
```
Subtitle: ...Well. Someone did. You'll be sore a day or two, and whatever did this still has your things.

### 11. `dlg.chid.woke.2.p0.wav`

*Where:* dialogue.json chid/woke#2; part 1 of 3: **chid: You're awake! A carter found you. The same carter, as it happens; he's starting to think y…** / narrator: He laughs, and stops. / chid: You'll be sore a day or two. Whatever did this is still out there. It'll have your things.
*Played:* cheerful, a shade less convinced; doing: you woke again (the second death); pace: quick; volume: level.
*Hides:* he carries you in himself, and what the flame costs
*Note:* The lie wears thin: brighter than he feels. The joke about the carter, then the narrator: he laughs, and stops. The rest practical.

```
[cheerful, a shade less convinced] You're awake! A carter found you. The same carter, as it happens; he's starting to think you're doing it on purpose. [laughs]
```
Subtitle: You're awake! A carter found you. The same carter, as it happens; he's starting to think you're doing it on purpose.

### 12. `dlg.chid.woke.2.p2.wav`

*Where:* dialogue.json chid/woke#2; part 3 of 3: chid: You're awake! A carter found you. The same carter, as it happens; he's starting to think y… / narrator: He laughs, and stops. / **chid: You'll be sore a day or two. Whatever did this is still out there. It'll have your things.**
*Played:* cheerful, a shade less convinced; doing: you woke again (the second death); pace: quick; volume: level.
*Hides:* he carries you in himself, and what the flame costs
*Note:* The lie wears thin: brighter than he feels. The joke about the carter, then the narrator: he laughs, and stops. The rest practical.

```
[cheerful, a shade less convinced] You'll be sore a day or two. Whatever did this is still out there. It'll have your things.
```
Subtitle: You'll be sore a day or two. Whatever did this is still out there. It'll have your things.

### 13. `dlg.chid.woke.3.wav`

*Where:* dialogue.json chid/woke#3
*Played:* relief, joy; doing: you woke at the shrine; pace: quick; volume: level.
*Hides:* what the flame costs
*Note:* Tumbling relief; a catch on 'The flame kept you.' 'I watched it.' quiet wonder. Then practical.

```
[relief, joy] You're awake! Good. Good! A carter found you on the Old Road and brought you here, and the flame..… The flame kept you. I watched it. [inhales] You'll be sore a day or two. Whatever did this to you is still out there. It'll have your things. They always keep something.
```
Subtitle: You're awake! Good. Good! A carter found you on the Old Road and brought you here, and the flame... The flame kept you. I watched it. You'll be sore a day or two. Whatever did this to you is still out there. It'll have your things. They always keep something.

### 14. `dlg.chid.woke.4.wav`

*Where:* dialogue.json chid/woke#4
*Played:* relieved, sheepish; doing: you woke after his prayer; pace: measured; volume: level.
*Note:* 'Oh, you're awake.' soft surprise. The prayer told shyly; 'well.' a little shrug. 'Here you are.' warm.

```
[relieved, sheepish] Oh, you're awake. A carter found you on the Old Road and brought you in, and I didn't know what else to do, so I prayed at the shrine and..… well. Here you are. You'll be sore a day or two. Whatever did this is still out there. It'll have your things.
```
Subtitle: Oh, you're awake. A carter found you on the Old Road and brought you in, and I didn't know what else to do, so I prayed at the shrine and... well. Here you are. You'll be sore a day or two. Whatever did this is still out there. It'll have your things.

### 15. `dlg.chid.where.0.wav`

*Where:* dialogue.json chid/where#0
*Played:* earnest concern; doing: tells you where you fell; pace: measured; volume: level.
*Note:* Storytelling; 'Be careful.' sincere. 'It knows your smell now.' quiet.

```
[earnest concern] In the Verge. The carter said there was a grave-mark where you lay, and your purse under it, and a beast standing over it that wouldn't let him near. Be careful. It knows your smell now.
```
Subtitle: In the Verge. The carter said there was a grave-mark where you lay, and your purse under it, and a beast standing over it that wouldn't let him near. Be careful. It knows your smell now.

### 16. `dlg.chid.before.0.wav`

*Where:* dialogue.json chid/before#0
*Played:* caught out, then tender; doing: admits you died and rose; pace: slow; volume: quiet.
*Wants:* not to frighten you
*Note:* 'Have I? Oh. Well.' flustered. Then quiet and plain: properly cold. A long pause; 'It's been a long time' much older than he sounds. 'Rest, now.' tender.

```
[caught out, then tender, quietly] Have I? Oh. Well. You were cold when they brought you in. Properly cold, the way the dead go cold. And then you weren't. ...It's been a long time since I saw anyone do that. I'd forgotten how it looks. Rest, now.
```
Subtitle: Have I? Oh. Well. You were cold when they brought you in. Properly cold, the way the dead go cold. And then you weren't. ...It's been a long time since I saw anyone do that. I'd forgotten how it looks. Rest, now.

### 17. `dlg.chid.shrine.0.wav`

*Where:* dialogue.json chid/shrine#0
*Played:* wistful, self-mocking; doing: explains the dead flame; pace: measured; volume: level.
*Note:* Sincere about the blessing; falters on 'trying'. Comic list building; 'That was a bad day.' rueful.

```
[wistful, self-mocking] The flame. It blessed people. Kept the dead lying down where you'd put them. It was never for seeing by, you know; it was for keeping company. Then the Order left and the flame went out, and I've been... trying. With prayers. And candles. And a bellows, once. That was a bad day.
```
Subtitle: The flame. It blessed people. Kept the dead lying down where you'd put them. It was never for seeing by, you know; it was for keeping company. Then the Order left and the flame went out, and I've been... trying. With prayers. And candles. And a bellows, once. That was a bad day.

### 18. `dlg.chid.lit.0.wav`

*Where:* dialogue.json chid/lit#0
*Played:* ecstatic joy; doing: the flame is lit again; pace: quick; volume: raised.
*Wants:* to tell the whole world
*Note:* Near tears with joy. 'WORKS' stressed. Voice cracks on 'Oh, thank you!'

```
[ecstatic joy, loudly] It WORKS. It works! I knew it worked. I said it worked! I have to tell Rook. I have to tell everyone. Thank you. Oh, thank you!
```
Subtitle: It WORKS. It works! I knew it worked. I said it worked! I have to tell Rook. I have to tell everyone. Thank you. Oh, thank you!

### 19. `dlg.chid.blessed.0.wav`

*Where:* dialogue.json chid/blessed#0
*Played:* warm, simple; doing: blesses you; pace: measured; volume: quiet.
*Note:* Gentle and fond, like tucking someone in.

```
[warm, simple, quietly] There. Go on, then, and be warm.
```
Subtitle: There. Go on, then, and be warm.

### 20. `dlg.chid.warden.0.wav`

*Where:* dialogue.json chid/warden#0
*Played:* thoughtful, faintly sad; doing: explains the Order's guardians; pace: measured; volume: level.
*Note:* 'which is a long time' slips out with a little laugh he shouldn't have. The last sentence quietly profound.

```
[thoughtful, faintly sad] The Order made it, I think. Before the Watch. Before me, certainly, which is a long time. Everything the Morning Light made was made to guard something. That's the trouble with guards: they outlast whatever they were guarding against, and then they guard against us.
```
Subtitle: The Order made it, I think. Before the Watch. Before me, certainly, which is a long time. Everything the Morning Light made was made to guard something. That's the trouble with guards: they outlast whatever they were guarding against, and then they guard against us.

### 21. `dlg.chid.vault.0.wav`

*Where:* dialogue.json chid/vault#0
*Played:* uneasy, hesitant; doing: what he knows of the door; pace: measured; volume: quiet.
*Note:* Short halting sentences. 'That, I think, is the answer.' quiet and pointed.

```
[uneasy, hesitant, quietly] The old empire did something there, before the Watch. I think the Watch was founded to keep it done. I don't know what. Vonra does. Vonra won't say. That, I think, is the answer.
```
Subtitle: The old empire did something there, before the Watch. I think the Watch was founded to keep it done. I don't know what. Vonnra does. Vonnra won't say. That, I think, is the answer.

### 22. `dlg.chid.below.0.wav`

*Where:* dialogue.json chid/below#0
*Played:* uneasy; doing: something digging; pace: measured; volume: quiet.
*Note:* The Order's saying recited, then a shiver: 'It sounds like a threat.'

```
[uneasy, quietly] Digging. Down. The Order used to say the dark's only light that hasn't been found yet. I never liked that one. It sounds like a threat.
```
Subtitle: Digging. Down. The Order used to say the dark's only light that hasn't been found yet. I never liked that one. It sounds like a threat.

### 23. `dlg.chid.long.0.wav`

*Where:* dialogue.json chid/long#0
*Played:* evasive, flustered; doing: dodges how old he is; pace: quick; volume: level.
*Note:* Cuts himself off at 'Since—'. Fond laugh on 'Terrible bread'. Hurried change of subject on 'Is that the time?'

```
[evasive, flustered] Oh, ages. Since— well. Rook's mother used to bring me bread. Lovely woman. Terrible bread. ...Is that the time? I should light a candle.
```
Subtitle: Oh, ages. Since— well. Rook's mother used to bring me bread. Lovely woman. Terrible bread. ...Is that the time? I should light a candle.

### 24. `dlg.chid.cb_opened_vault.0.wav`

*Where:* dialogue.json chid/cb_opened_vault#0
*Played:* excited dread; doing: you went through the door; pace: quick; volume: raised.
*Note:* Breathless; cuts himself off. Flip-flops: 'No, don't tell me. Yes, tell me. No.' comic and frightened.

```
[excited dread, loudly] You went through the door! You went through— what was on the stair? No, don't tell me. Yes, tell me. No.
```
Subtitle: You went through the door! You went through— what was on the stair? No, don't tell me. Yes, tell me. No.

### 25. `dlg.chid.cb_vault2.0.wav`

*Where:* dialogue.json chid/cb_vault2#0
*Played:* relieved, shaken; doing: the dead still guard the stair; pace: slow; volume: quiet.
*Note:* 'Good. Good, I think.' unsure. Then a nervous resolve on the candles.

```
[relieved, shaken, quietly] Then they're still keeping it. Good. Good, I think. ...I'm going to light every candle I've got.
```
Subtitle: Then they're still keeping it. Good. Good, I think. ...I'm going to light every candle I've got.

### 26. `dlg.chid.cb_core_stolen.0.wav`

*Where:* dialogue.json chid/cb_core_stolen#0
*Played:* dismay; doing: the Warden's heart was taken; pace: slow; volume: quiet.
*Note:* Quiet, the joy gone. 'Oh, dear. Oh, dear, dear.' genuinely frightened. The last line almost to himself.

```
[dismay, quietly] The Warden's heart. Rook says a lampling took it at the ford. ...Oh, dear. Oh, dear, dear. That was one of the old ones. They're not meant to be carried about.
```
Subtitle: The Warden's heart. Rook says a lampling took it at the ford. ...Oh, dear. Oh, dear, dear. That was one of the old ones. They're not meant to be carried about.

### 27. `dlg.chid.cb_nemesis_slain.0.wav`

*Where:* dialogue.json chid/cb_nemesis_slain#0
*Played:* excited fuss; doing: you got your things back; pace: quick; volume: raised.
*Note:* Answers his own question. Fussing: 'Not there. There.'

```
[excited fuss, loudly] You got your things back! From the thing! Was it horrible? It was horrible. Sit down. The good stool, the other one wobbles.
```
Subtitle: You got your things back! From the thing! Was it horrible? It was horrible. Sit down. The good stool, the other one wobbles.

### 28. `dlg.chid.say_calling.0.wav`

*Where:* dialogue.json chid/say_calling#0
*Played:* delighted; doing: admires your shield; pace: quick; volume: level.
*Note:* Wonder at the shield. Pause on '... dents.' then cheerful reassurance.

```
[delighted] A shield! The Order's knights carried shields with the morning painted on them. Yours has... dents. Dents are good. Dents mean it worked.
```
Subtitle: A shield! The Order's knights carried shields with the morning painted on them. Yours has... dents. Dents are good. Dents mean it worked.

### 29. `dlg.chid.say_calling.1.wav`

*Where:* dialogue.json chid/say_calling#1
*Played:* gentle, kind; doing: sees your anger; pace: measured; volume: quiet.
*Note:* Not a lecture. 'fire with manners' with a small smile.

```
[gentle, kind, quietly] There's a lot of anger in you. That's all right. The light doesn't mind anger. It's only fire with manners.
```
Subtitle: There's a lot of anger in you. That's all right. The light doesn't mind anger. It's only fire with manners.

### 30. `dlg.chid.say_calling.2.wav`

*Where:* dialogue.json chid/say_calling#2
*Played:* awed, then sheepish; doing: sees the ember in you; pace: measured; volume: quiet.
*Note:* Fascination; catches himself. 'I won't, but I'll try.' sheepish honesty.

```
[awed, then sheepish, quietly] You burn, don't you? Not like a candle. Like... oh. Like you. Sorry. I'll stop staring. I won't, but I'll try.
```
Subtitle: You burn, don't you? Not like a candle. Like... oh. Like you. Sorry. I'll stop staring. I won't, but I'll try.

### 31. `dlg.chid.say_calling.3.wav`

*The same words are also* `dlg.chid.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/say_calling#3
*Played:* startled, amused; doing: you crept in; pace: quick; volume: level.
*Note:* Startled first line; deadpan little joke about the spiders.

```
[startled, amused] You put your feet down like the floor's asleep and you don't want to wake it. The Order had a word for walking like that. I've forgotten it. It was a nice word.
```
Subtitle: You put your feet down like the floor's asleep and you don't want to wake it. The Order had a word for walking like that. I've forgotten it. It was a nice word.

### 32. `dlg.chid.names.0.wav`

*Where:* dialogue.json chid/names#0
*Played:* gentle, sorrowful; doing: warns you the dead forget; pace: slow; volume: quiet.
*Wants:* you to keep your names
*Note:* Tentative question. Long pause. Kind, grave and very old for 'It always takes the names first. Then the faces.' Then the apology, and a too-quick brightening: 'Sit, sit.'

```
[gentle, sorrowful, quietly] Can I ask you something? Your mother's name. ...No, don't tell me. You had to think. I saw you think. Write the names down, somewhere you'll find them. It always takes the names first. Then the faces. I'm sorry. I'll stop. Sit, sit.
```
Subtitle: Can I ask you something? Your mother's name. ...No, don't tell me. You had to think. I saw you think. Write the names down, somewhere you'll find them. It always takes the names first. Then the faces. I'm sorry. I'll stop. Sit, sit.

### 33. `dlg.chid.t_chid.0.wav`

*Where:* dialogue.json chid/t_chid#0
*Played:* fond nostalgia, then grief; doing: remembers the Order; pace: measured then slow; volume: level.
*Note:* 'Loud!' laughing. Warm memory of Brother Aumery. Then quiet: they're all gone. 'I keep not.' barely held.

```
[fond nostalgia, then grief] Loud! Everybody thinks priests are quiet. We sang at breakfast. Brother Awmery could sing bread warm. ...They're all gone now. I keep thinking I'll get used to that. I keep not.
```
Subtitle: Loud! Everybody thinks priests are quiet. We sang at breakfast. Brother Aumery could sing bread warm. ...They're all gone now. I keep thinking I'll get used to that. I keep not.

### 34. `dlg.chid.note.0.p0.wav`

*Where:* dialogue.json chid/note#0; part 1 of 5: **chid: Was there!** / narrator: He's suddenly very interested in a candle. / chid: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, wh… / narrator: He stops. / chid: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made…
*Played:* flustered evasion; doing: hides that he wrote the note; pace: quick; volume: level.
*Note:* Too-bright 'Was there!'. Babbling names; stops dead at 'Cormac, once, who—'. Then fond, quieter, almost giving himself away on 'in... well. Ages.'

```
[flustered evasion] Was there!
```
Subtitle: Was there!

### 35. `dlg.chid.note.0.p2.wav`

*Where:* dialogue.json chid/note#0; part 3 of 5: chid: Was there! / narrator: He's suddenly very interested in a candle. / **chid: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, wh…** / narrator: He stops. / chid: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made…
*Played:* flustered evasion; doing: hides that he wrote the note; pace: quick; volume: level.
*Note:* Too-bright 'Was there!'. Babbling names; stops dead at 'Cormac, once, who—'. Then fond, quieter, almost giving himself away on 'in... well. Ages.'

```
[flustered evasion] A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, who—
```
Subtitle: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, who—

### 36. `dlg.chid.note.0.p4.wav`

*Where:* dialogue.json chid/note#0; part 5 of 5: chid: Was there! / narrator: He's suddenly very interested in a candle. / chid: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, wh… / narrator: He stops. / **chid: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made…**
*Played:* flustered evasion; doing: hides that he wrote the note; pace: quick; volume: level.
*Note:* Too-bright 'Was there!'. Babbling names; stops dead at 'Cormac, once, who—'. Then fond, quieter, almost giving himself away on 'in... well. Ages.'

```
[flustered evasion] It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made a C like that in... well. Ages.
```
Subtitle: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made a C like that in... well. Ages.

### 37. `dlg.chid.cb_nell.0.p0.wav`

*Where:* dialogue.json chid/cb_nell#0; part 1 of 4: **chid: I sang it flat. I always have. There's always somebody who has the tune.** / narrator: He is quiet, which he never is. / chid: She was very light. ...Sit down a minute. / narrator: He moves up the bench, though there's nobody else on it.
*Played:* quiet grief, held; doing: after the burial he sang at; pace: slow; volume: quiet.
*Wants:* to look after the one who put her down
*Hides:* he knows what the irons are for; 'somebody' is Vonnra's alto
*Note:* Light and offhand on the singing; 'I always have' is older than he looks, and he doesn't notice saying it. Narrator plain; three seconds of silence. 'She was very light' barely voiced, one catch on 'light', no sob. 'By me.' quiet, almost asking.

```
[quiet grief, held, quietly] I sang it flat… I always have. [inhales] There's always somebody who has the tune.
```
Subtitle: I sang it flat. I always have. There's always somebody who has the tune.

### 38. `dlg.chid.cb_nell.0.p2.wav`

*The same words are also* `dlg.chid.cb_nell.1.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/cb_nell#0; part 3 of 4: chid: I sang it flat. I always have. There's always somebody who has the tune. / narrator: He is quiet, which he never is. / **chid: She was very light. ...Sit down a minute.** / narrator: He moves up the bench, though there's nobody else on it.
*Played:* quiet grief, held; doing: after the burial he sang at; pace: slow; volume: quiet.
*Wants:* to look after the one who put her down
*Hides:* he knows what the irons are for; 'somebody' is Vonnra's alto
*Note:* Light and offhand on the singing; 'I always have' is older than he looks, and he doesn't notice saying it. Narrator plain; three seconds of silence. 'She was very light' barely voiced, one catch on 'light', no sob. 'By me.' quiet, almost asking.

```
[quiet grief, held, quietly] She was very light. ...Sit down a minute.
```
Subtitle: She was very light. ...Sit down a minute.

### 39. `dlg.chid.cb_nell.1.p0.wav`

*Where:* dialogue.json chid/cb_nell#1; part 1 of 4: **chid: We buried Nell behind the shrine, next to old Ashe. Brannoc made the marker himself. Iron.…** / narrator: He is quiet, which he never is. / chid: She was very light. ...Sit down a minute. / narrator: He moves up the bench, though there's nobody else on it.
*Played:* quiet grief, held; doing: they buried Nell; pace: slow; volume: quiet.
*Wants:* to look after the one who put her down
*Hides:* he knows what the irons are for, and he was at the ford the night she got up
*Note:* 'Of course, iron' fond: the half-second before it holds the sting (iron is what drowned her), so don't play the irony. Narrator plain, no sorrow; then three seconds of silence. 'She was very light' barely voiced, one catch allowed on 'light', no sob. His ordinary self comes back on 'Not on the step'; under the care he is the one who needs the company, and 'By me.' is quiet, almost asking.

```
[quiet grief, held, quietly] We buried Nell behind the shrine, next to old Ashe… Brannock made the marker himself. Iron… Of course, iron.
```
Subtitle: We buried Nell behind the shrine, next to old Ashe. Brannoc made the marker himself. Iron. Of course, iron.

### 40. `dlg.chid.carter.0.p0.wav`

*Where:* dialogue.json chid/carter#0; part 1 of 3: **chid: ...You know, I never asked his name. I should ask his name. Next time.** / narrator: He puts a cup in your hands. / chid: Drink that. It's only hot water. There's nothing in it but hot.
*Played:* light, distracted; doing: the carter who keeps finding you; pace: measured; volume: quiet.
*Hides:* there is no carter, or none he can name
*Note:* Musing, light; he doesn't hear what he's saying. Narrator: the cup. Then fussing kindness; 'There's nothing in it but hot.' a small reassurance.

```
[light, distracted, quietly] ...You know, I never asked his name… I should ask his name. Next time.
```
Subtitle: ...You know, I never asked his name. I should ask his name. Next time.

### 41. `dlg.chid.carter.0.p2.wav`

*Where:* dialogue.json chid/carter#0; part 3 of 3: chid: ...You know, I never asked his name. I should ask his name. Next time. / narrator: He puts a cup in your hands. / **chid: Drink that. It's only hot water. There's nothing in it but hot.**
*Played:* light, distracted; doing: the carter who keeps finding you; pace: measured; volume: quiet.
*Hides:* there is no carter, or none he can name
*Note:* Musing, light; he doesn't hear what he's saying. Narrator: the cup. Then fussing kindness; 'There's nothing in it but hot.' a small reassurance.

```
[light, distracted, quietly] Drink that. It's only hot water… There's nothing in it but hot.
```
Subtitle: Drink that. It's only hot water. There's nothing in it but hot.

### 42. `dlg.chid.legion.0.wav`

*Where:* dialogue.json chid/legion#0

```
Soldiers! The Seventh, the Order's books called them. Very tidy, very old, very... thorough. Oh, and this is the part I liked: they never followed a man. Never. They followed the pole. A bronze hand on a pole, a standard, and wherever it went they went, and if it went down they stood about like a choir that's lost its place. ...I don't know why I'm telling you that. It's a very old book.
```
Subtitle: Soldiers! The Seventh, the Order's books called them. Very tidy, very old, very... thorough. Oh, and this is the part I liked: they never followed a man. Never. They followed the pole. A bronze hand on a pole, a standard, and wherever it went they went, and if it went down they stood about like a choir that's lost its place. ...I don't know why I'm telling you that. It's a very old book.

### 43. `dlg.chid.carried_chid.0.p0.wav`

*The same words are also* `dlg.chid.carried_chid.1.p0.wav`, `dlg.chid.carried_chid.2.p0.wav`, `dlg.chid.carried_chid.3.p0.wav`, `dlg.chid.carried_chid.4.p0.wav`, `dlg.chid.carried_chid.5.p0.wav`, `dlg.chid.carried_chid.6.p0.wav`, `dlg.chid.carried_chid.7.p0.wav`, `dlg.chid.carried_chid.8.p0.wav`, `dlg.chid.carried_chid.9.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/carried_chid#0; part 1 of 5: **chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and …** / narrator: He doesn't look at you. / chid: Somebody brought you in. A carter, I expect. / narrator: He has a small book in both hands, held the way you hold a bird. / chid: I was keeping this for you. It's only an old office, what the keepers said at night. There…

```
You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and that's all it's cost you: a night. They come round again; it's the one thing you can say for them.
```
Subtitle: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and that's all it's cost you: a night. They come round again; it's the one thing you can say for them.

### 44. `dlg.chid.carried_chid.0.p2.wav`

*The same words are also* `dlg.chid.carried_chid.9.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/carried_chid#0; part 3 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you in. A carter, I expect.** / narrator: He has a small book in both hands, held the way you hold a bird. / chid: I was keeping this for you. It's only an old office, what the keepers said at night. There…

```
Somebody brought you in. A carter, I expect.
```
Subtitle: Somebody brought you in. A carter, I expect.

### 45. `dlg.chid.carried_chid.0.p4.wav`

*Where:* dialogue.json chid/carried_chid#0; part 5 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / chid: Somebody brought you in. A carter, I expect. / narrator: He has a small book in both hands, held the way you hold a bird. / **chid: I was keeping this for you. It's only an old office, what the keepers said at night. There…**

```
I was keeping this for you. It's only an old office, what the keepers said at night. There's a bit at the end. ...Read it before you go out again. Please.
```
Subtitle: I was keeping this for you. It's only an old office, what the keepers said at night. There's a bit at the end. ...Read it before you go out again. Please.

### 46. `dlg.chid.carried_chid.1.p2.wav`

*Where:* dialogue.json chid/carried_chid#1; part 3 of 3: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you in off the Hollow road. A carter, I expect. ...Maeca was at the door …**

```
Somebody brought you in off the Hollow road. A carter, I expect. ...Mayka was at the door at first light, asking after you. She wouldn't come in. If anybody knows those wolves, it's Mayka.
```
Subtitle: Somebody brought you in off the Hollow road. A carter, I expect. ...Maeca was at the door at first light, asking after you. She wouldn't come in. If anybody knows those wolves, it's Maeca.

### 47. `dlg.chid.carried_chid.2.p2.wav`

*Where:* dialogue.json chid/carried_chid#2; part 3 of 3: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you in off the Hollow road. A carter, I expect. They get everywhere, cart…**

```
Somebody brought you in off the Hollow road. A carter, I expect. They get everywhere, carters.
```
Subtitle: Somebody brought you in off the Hollow road. A carter, I expect. They get everywhere, carters.

### 48. `dlg.chid.carried_chid.3.p2.wav`

*Where:* dialogue.json chid/carried_chid#3; part 3 of 3: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it …**

```
Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it was light. He sat with you a while and didn't say much, which isn't like him. He knows that camp, you know. He's stitched up half of it.
```
Subtitle: Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it was light. He sat with you a while and didn't say much, which isn't like him. He knows that camp, you know. He's stitched up half of it.

### 49. `dlg.chid.carried_chid.4.p2.wav`

*Where:* dialogue.json chid/carried_chid#4; part 3 of 3: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it …**

```
Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it was light. He sat with you a while and didn't say much, which isn't like him.
```
Subtitle: Somebody brought you down off the Roost road. A carter, I expect. ...Rav was in before it was light. He sat with you a while and didn't say much, which isn't like him.

### 50. `dlg.chid.carried_chid.5.p2.wav`

*Where:* dialogue.json chid/carried_chid#5; part 3 of 3: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you down off the Dig's hill. A carter, I expect. ...That old lamp of your…**

```
Somebody brought you down off the Dig's hill. A carter, I expect. ...That old lamp of yours was lit when you came in. I didn't light it. Those little fellows must have been very taken with it.
```
Subtitle: Somebody brought you down off the Dig's hill. A carter, I expect. ...That old lamp of yours was lit when you came in. I didn't light it. Those little fellows must have been very taken with it.

### 51. `dlg.chid.carried_chid.6.p2.wav`

*Where:* dialogue.json chid/carried_chid#6; part 3 of 3: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you down off the Dig's hill. A carter, I expect. I've put the kettle on.**

```
Somebody brought you down off the Dig's hill. A carter, I expect. I've put the kettle on.
```
Subtitle: Somebody brought you down off the Dig's hill. A carter, I expect. I've put the kettle on.

### 52. `dlg.chid.carried_chid.7.p2.wav`

*The same words are also* `dlg.chid.carried_chid.8.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/carried_chid#7; part 3 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / **chid: Somebody brought you in from the old door. A carter, I expect.** / narrator: He's quiet a moment, which isn't like him. / chid: I've read about the ones behind that door. In a very old book. Ask me, when you've eaten.

```
Somebody brought you in from the old door. A carter, I expect.
```
Subtitle: Somebody brought you in from the old door. A carter, I expect.

### 53. `dlg.chid.carried_chid.7.p4.wav`

*Where:* dialogue.json chid/carried_chid#7; part 5 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / chid: Somebody brought you in from the old door. A carter, I expect. / narrator: He's quiet a moment, which isn't like him. / **chid: I've read about the ones behind that door. In a very old book. Ask me, when you've eaten.**

```
I've read about the ones behind that door. In a very old book. Ask me, when you've eaten.
```
Subtitle: I've read about the ones behind that door. In a very old book. Ask me, when you've eaten.

### 54. `dlg.chid.carried_chid.8.p4.wav`

*Where:* dialogue.json chid/carried_chid#8; part 5 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / chid: Somebody brought you in from the old door. A carter, I expect. / narrator: He's quiet a moment, which isn't like him. / **chid: They followed the pole, you know. Always the pole.**

```
They followed the pole, you know. Always the pole.
```
Subtitle: They followed the pole, you know. Always the pole.

### 55. `dlg.chid.carried_who.0.p0.wav`

*Where:* dialogue.json chid/carried_who#0; part 1 of 3: **chid: Oh, somebody kind. There are more of them about at night than you'd think.** / narrator: He busies himself with the kettle. / chid: ...Eat something. The day's yours.

```
Oh, somebody kind. There are more of them about at night than you'd think.
```
Subtitle: Oh, somebody kind. There are more of them about at night than you'd think.

### 56. `dlg.chid.carried_who.0.p2.wav`

*Where:* dialogue.json chid/carried_who#0; part 3 of 3: chid: Oh, somebody kind. There are more of them about at night than you'd think. / narrator: He busies himself with the kettle. / **chid: ...Eat something. The day's yours.**

```
...Eat something. The day's yours.
```
Subtitle: ...Eat something. The day's yours.

### 57. `dlg.chid.office.0.p0.wav`

*Where:* dialogue.json chid/office#0; part 1 of 5: **chid: You've been up the Tower.** / narrator: He doesn't ask what she told you. He has a small book in both hands, held the way you hold… / chid: I want you to have this. It's only an old office: the watch-hours, what the keepers said a… / narrator: He opens it at the last page, and doesn't look at it. / chid: There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in …

```
You've been up the Tower.
```
Subtitle: You've been up the Tower.

### 58. `dlg.chid.office.0.p2.wav`

*Where:* dialogue.json chid/office#0; part 3 of 5: chid: You've been up the Tower. / narrator: He doesn't ask what she told you. He has a small book in both hands, held the way you hold… / **chid: I want you to have this. It's only an old office: the watch-hours, what the keepers said a…** / narrator: He opens it at the last page, and doesn't look at it. / chid: There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in …

```
I want you to have this. It's only an old office: the watch-hours, what the keepers said at night. Nobody's said them in a long while.
```
Subtitle: I want you to have this. It's only an old office: the watch-hours, what the keepers said at night. Nobody's said them in a long while.

### 59. `dlg.chid.office.0.p4.wav`

*Where:* dialogue.json chid/office#0; part 5 of 5: chid: You've been up the Tower. / narrator: He doesn't ask what she told you. He has a small book in both hands, held the way you hold… / chid: I want you to have this. It's only an old office: the watch-hours, what the keepers said a… / narrator: He opens it at the last page, and doesn't look at it. / **chid: There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in …**

```
There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in the dark.
```
Subtitle: There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in the dark.

### 60. `dlg.chid.office_end.0.p1.wav`

*Where:* dialogue.json chid/office_end#0; part 2 of 2: narrator: He puts his hand over yours, flat on the cover. / **chid: Not now, I said! ...It's the end of the watch. One keeper asks, and the other one answers,…**

```
Not now, I said! ...It's the end of the watch. One keeper asks, and the other one answers, so nobody has to sit up the whole night on their own. That's what an office is, really. Somebody answering.
```
Subtitle: Not now, I said! ...It's the end of the watch. One keeper asks, and the other one answers, so nobody has to sit up the whole night on their own. That's what an office is, really. Somebody answering.

### 61. `dlg.chid.office_who.0.wav`

*Where:* dialogue.json chid/office_who#0

```
Oh, a keeper. One of the old ones. Lovely hand, hasn't he? Nobody makes a C like that any more.
```
Subtitle: Oh, a keeper. One of the old ones. Lovely hand, hasn't he? Nobody makes a C like that any more.

### 62. `dlg.chid.names_write.0.p1.wav`

*Where:* dialogue.json chid/names_write#0; part 2 of 2: narrator: He watches you write it, and doesn't look at what. / **chid: Good. Keep it somewhere dry.**

```
Good. Keep it somewhere dry.
```
Subtitle: Good. Keep it somewhere dry.

## Said in passing

### 63. `bark.chid.day.0.wav`

*Where:* npcs.json chid.barks[0]
*Played:* wistful, cheerful; pace: measured; volume: level.

```
[wistful, cheerful] The light's patient. I'm trying to be.
```
Subtitle: The light's patient. I'm trying to be.

### 64. `bark.chid.day.1.wav`

*Where:* npcs.json chid.barks[1]
*Played:* gently rueful; pace: measured; volume: level.

```
[gently rueful] Morning comes. It always has. I should know.
```
Subtitle: Morning comes. It always has. I should know.

### 65. `bark.chid.night.0.wav`

*Where:* npcs.json chid.nightBarks[0]
*Played:* gentle hope; pace: slow; volume: quiet.

```
[gentle hope, quietly] Even in the dark, the morning's on its way.
```
Subtitle: Even in the dark, the morning's on its way.

### 66. `bark.chid.night.1.wav`

*Where:* npcs.json chid.nightBarks[1]
*Played:* kind; pace: slow; volume: quiet.

```
[kind, quietly] I leave a candle lit. Somebody might need it.
```
Subtitle: I leave a candle lit. Somebody might need it.

### 67. `bark.chid.night.2.wav`

*Where:* npcs.json chid.nightBarks[2]
*Played:* friendly, sleepless; pace: measured; volume: quiet.

```
[friendly, sleepless, quietly] Can't sleep either?
```
Subtitle: Can't sleep either?

### 68. `bark.chid.night.3.wav`

*Where:* npcs.json chid.nightBarks[3]
*Played:* reciting, then rueful; pace: slow; volume: quiet.
*Note:* The Order's saying, then a little laugh at the long night.

```
[reciting, then rueful, quietly] The dark's only the part of the day that hasn't happened yet. ...It's taking its time tonight.
```
Subtitle: The dark's only the part of the day that hasn't happened yet. ...It's taking its time tonight.

### 69. `bark.chid.said.0.wav`

*Where:* npcs.json chid.said[0]
*Played:* cheerful; doing: the shrine used to work; pace: measured; volume: level.
*Note:* Cheerful and practical, like a broken pump.

```
[cheerful] It used to work, you know. The shrine.
```
Subtitle: It used to work, you know. The shrine.

### 70. `bark.chid.said.1.wav`

*Where:* npcs.json chid.said[1]
*Played:* delighted; doing: the shrine works again; pace: quick; volume: raised.
*Note:* Bursting; 'I keep checking.' sheepish delight.

```
[delighted, loudly] It works! It works. I keep checking.
```
Subtitle: It works! It works. I keep checking.

### 71. `bark.chid.said.2.wav`

*Where:* npcs.json chid.said[2]
*Played:* bright, fond; doing: you're up; pace: quick; volume: level.
*Note:* 'Up's very good.' a little joke at himself.

```
[bright, fond] Up and about! Up's very good.
```
Subtitle: Up and about! Up's very good.

### 72. `bark.chid.said.3.wav`

*Where:* npcs.json chid.said[3]
*Played:* quiet, tender; doing: candles for Nell; pace: measured; volume: quiet.
*Note:* 'don't tell him.' a small conspiracy.

```
[quiet, tender, quietly] Two candles in for her. One's for Brannock. He'd only blow it out.
```
Subtitle: Two candles in for her. One's for Brannoc. He'd only blow it out.

### 73. `bark.chid.said.4.wav`

*Where:* npcs.json chid.said[4]

```
Oh, you're cold! Colder than usual, I mean. Come and sit by the flame.
```
Subtitle: Oh, you're cold! Colder than usual, I mean. Come and sit by the flame.

### 74. `bark.chid.said.5.wav`

*Where:* npcs.json chid.said[5]

```
Back again! You always are. Sit, sit; the flame likes company.
```
Subtitle: Back again! You always are. Sit, sit; the flame likes company.

### 75. `bark.chid.said.6.wav`

*Where:* npcs.json chid.said[6]

```
Out ever so long! The whole dark was up, like moths round a candle.
```
Subtitle: Out ever so long! The whole dark was up, like moths round a candle.


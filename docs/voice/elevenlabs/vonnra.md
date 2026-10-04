# Vonnra Ash-of-Morrow: ElevenLabs packet

Voice id in the game: `vonnra`. 103 takes to record (9,057 characters; about 27,171 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Vonnra Ash-of-Morrow** (toll-keeper, far seer). No contractions. Very still, long pauses, few questions. Talks of payment, of seeing, of what is "arranged". Never answers yes or no; never hurries; never says what she wants. Calls the survivor "traveller" until the fortune; if the survivor tells her there that she lit the lamps, she answers with their name, and uses it from then on. (Every such line puts the name alone at a pause, so it can be recorded as its own take and spliced; the subtitle always carries it. See `docs/cinematics/c09_fortune.md`, Lines.) That is the only answer she gives, until the bottom of the stair (Act 3, C43), where she breaks both halves of her rule once, if the survivor tells her what the Morrow is saying: "...No. I wanted the lamps to stay lit. That is all I ever wanted. I wanted it to be morning." Her "seeing" is what she has bought: say it as sight, and let the narrator notice where her eyes are. *Casting:* 60s, clipped and unplaceable (old empire), a low alto with a little air. The most important casting in the game. She is heard once before the player meets her, unnamed: the voice up the road at the waking (C01, speaker `far_voice`), "Come up, traveller. ...No charge, this once.", recorded far off and thinned by the cold. The fortune opens on the same words.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Vonnra Ash-of-Morrow`. Never describe a voice as sounding like a real person.

```
Native English (British, old-fashioned upper-class English). Female, 60s. Studio quality. Persona: an old aristocrat. A woman in her sixties with a low, smooth alto and a little air in the voice, and a clipped, old-fashioned, upper-class English accent that is hard to place. She speaks slowly and very still, with long pauses, never hurried, every word weighed. Calm, courteous and quietly unsettling. Crisp old-fashioned upper-class English. No reverb or effects.
```

Preview text:

```
The toll is the toll: five gold to pass east. I am Vonra. I see a great deal, traveller, and I say very little. You will find that is the arrangement.
```

In the Voice Library instead: search for *clipped, unplaceable old empire*, *female*, *60*, and listen for this: A woman in her sixties with a low, smooth alto and a little air in the voice, and a clipped, old-fashioned, upper-class English accent that is hard to place. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_drowned_fire.call.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice vonnra
```

## The effect

Record every take dry, with no effect or reverb: the game adds it. For the lines that say so, it puts it far up the road on a frosty night: the top lost to the cold air, thinner, with a little early reflection.

## Saying the names

The text to paste already respells these; keep the respelling: Legio Septima as *Leggio Septeema*, Vonnra as *Vonra*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: drowned fire

### 1. `dlg.cin_drowned_fire.call.0.wav`

*The same words are also* `say.bc92c07d79db.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_drowned_fire/call#0
*Played:* kindly, unhurried; doing: a toll-keeper waving a traveller through; pace: slow; volume: quiet.
*Wants:* the risen traveller up the road and into her town before dawn
*Hides:* that she made them
*Note:* Far off and thinned by the cold, never raised; the frost carries it, close as if at the shoulder. The pause before 'No charge' is her deciding to. The game adds the distance (the 'far' effect): record it dry and close.
*Length:* the cut is timed to it: 3.0–3.6 s (distant but every word clear; the outdoor tail after it is welcome), first sound to last word.

```
[kindly, unhurried, quietly] Come up, traveller… ...No charge, this once.
```
Subtitle: Come up, traveller. ...No charge, this once.

## Conversations: Vonnra

### 2. `dlg.vonnra.first.0.wav`

*Where:* dialogue.json vonnra/first#0
*Played:* cool, amused, still; doing: names the toll and sizes you up; pace: slow; volume: quiet.
*Wants:* to see what you are
*Note:* Very still. 'A reader.' a verdict. 'The toll is the toll' a ritual phrase. A faint dry amusement in the last sentence.

```
[cool, amused, still, quietly] A reader. You have the look. The toll is the toll: five gold to pass east. I am Vonra. I see a great deal and say very little. You, of all people, will find that frustrating.
```
Subtitle: A reader. You have the look. The toll is the toll: five gold to pass east. I am Vonnra. I see a great deal and say very little. You, of all people, will find that frustrating.

### 3. `dlg.vonnra.first.1.wav`

*Where:* dialogue.json vonnra/first#1
*Played:* quiet recognition, controlled; doing: the one she has waited for has come; pace: very slow; volume: quiet.
*Wants:* to hide how much this matters
*Note:* 'So.' long beat. 'The one from the ford.' as if confirming a delivery. The pause before '...Sooner than I had thought' is the most telling thing she does: almost to herself. Then back to ritual, perfectly level.

```
[quiet recognition, controlled, quietly] So. The one from the ford. ...Sooner than I had thought. The toll is the toll: five gold to pass east. I am Vonra. I see a great deal and say very little. You will find that is the arrangement.
```
Subtitle: So. The one from the ford. ...Sooner than I had thought. The toll is the toll: five gold to pass east. I am Vonnra. I see a great deal and say very little. You will find that is the arrangement.

### 4. `dlg.vonnra.first.2.wav`

*Where:* dialogue.json vonnra/first#2
*Played:* cool, faintly menacing; doing: names the toll; pace: slow; volume: quiet.
*Note:* The ritual phrase. 'and I remember your face' quietly menacing, unhurried.

```
[cool, faintly menacing, quietly] The toll is the toll. Five gold to pass east, or no gold and I remember your face. I am Vonra. I see a great deal and say very little. You will find that is the arrangement.
```
Subtitle: The toll is the toll. Five gold to pass east, or no gold and I remember your face. I am Vonnra. I see a great deal and say very little. You will find that is the arrangement.

### 5. `dlg.vonnra.hub.0.wav`

*Where:* dialogue.json vonnra/hub#0
*Played:* calm finality, a new intimacy; doing: uses your name now; pace: slow; volume: quiet.
*Note:* A beat where the name would be. Then as hub.1, but a degree warmer.
*The name:* her take of the survivor's name plays just before this one; start as if she had that moment said it.

```
[calm finality, a new intimacy, quietly] Your chapter is written. The next one is not. ...Payment, always.
```
Subtitle: Your chapter is written. The next one is not. ...Payment, always.

### 6. `dlg.vonnra.hub.1.wav`

*Where:* dialogue.json vonnra/hub#1
*Played:* calm finality; doing: the chapter is closed; pace: slow; volume: quiet.
*Note:* Each sentence its own weight. 'Payment, always.' her refrain, never varied in tone.

```
[calm finality, quietly] Your chapter is written. The next one is not. Payment, always.
```
Subtitle: Your chapter is written. The next one is not. Payment, always.

### 7. `dlg.vonnra.hub.2.p1.wav`

*Where:* dialogue.json vonnra/hub#2; part 2 of 2: narrator: Her lamp is lit, and she is looking south, toward the ford. / **vonnra: Traveller. The road was quiet tonight. It will not always be. Payment, always.**
*Played:* watchful, foreboding; doing: looking toward the ford; pace: slow; volume: quiet.
*Note:* Narrator for the lamp and the south. 'Traveller.' acknowledgement without turning. A quiet prophecy. 'Payment, always.'

```
[watchful, foreboding, quietly] Traveller. The road was quiet tonight. It will not always be. Payment, always.
```
Subtitle: Traveller. The road was quiet tonight. It will not always be. Payment, always.

### 8. `dlg.vonnra.hub.3.wav`

*Where:* dialogue.json vonnra/hub#3
*Played:* dry, businesslike; doing: comments on trade; pace: slow; volume: quiet.
*Note:* Dry observation. 'Payment, always.'

```
[dry, businesslike, quietly] Fewer wagons, fewer tolls. The Kerchiefs are bad for everyone's business but their own. Payment, always.
```
Subtitle: Fewer wagons, fewer tolls. The Kerchiefs are bad for everyone's business but their own. Payment, always.

### 9. `dlg.vonnra.hub.4.wav`

*The same words are also* `bark.vonnra.day.2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json vonnra/hub#4
*Played:* still; doing: her refrain; pace: slow; volume: quiet.
*Note:* Two words, perfectly level.

```
[still, quietly] Payment, always.
```
Subtitle: Payment, always.

### 10. `dlg.vonnra.paid.0.wav`

*Where:* dialogue.json vonnra/paid#0
*Played:* cool, ambiguous; doing: lets you pass; pace: slow; volume: quiet.
*Note:* 'Try to come back through it.' neither warning nor kindness; both.

```
[cool, ambiguous, quietly] The east gate is yours. Try to come back through it.
```
Subtitle: The east gate is yours. Try to come back through it.

### 11. `dlg.vonnra.ledger.0.wav`

*Where:* dialogue.json vonnra/ledger#0
*Played:* cool, transactional; doing: the ledger costs; pace: slow; volume: quiet.
*Note:* Plain terms.

```
[cool, transactional, quietly] Everything that passes my gate is written down. Reading it is not free.
```
Subtitle: Everything that passes my gate is written down. Reading it is not free.

### 12. `dlg.vonnra.ledger_read.0.wav`

*Where:* dialogue.json vonnra/ledger_read#0
*Played:* precise, unhelpful; doing: the caravan never came; pace: slow; volume: quiet.
*Note:* 'There.' Each sentence a fact laid down. No hint that she knows more.

```
[precise, unhelpful, quietly] There. The Coyle caravan did not pay my toll. It never came through my gate. Whatever happened to it happened before it reached me.
```
Subtitle: There. The Coyle caravan did not pay my toll. It never came through my gate. Whatever happened to it happened before it reached me.

### 13. `dlg.vonnra.vault.0.wav`

*Where:* dialogue.json vonnra/vault#0
*Played:* cold, absolute; doing: refuses; pace: slow; volume: quiet.
*Note:* 'Not for any price.' immovable. The second sentence almost gracious, which is worse.

```
[cold, absolute, quietly] Not for any price. That is the only thing I will ever say to you without charging for it.
```
Subtitle: Not for any price. That is the only thing I will ever say to you without charging for it.

### 14. `dlg.vonnra.arcana.0.wav`

*Where:* dialogue.json vonnra/arcana#0
*Played:* cool respect, warning; doing: you know the Legion's words; pace: slow; volume: quiet.
*Note:* Say 'Legio Septima' as LEG-ee-oh sep-TEE-mah, crisp and old. 'Ask me something cheaper.' dry.

```
[cool respect, warning, quietly] You do read. Then you know what Leggio Septeema means over a door, and you know better than to ask me what is behind it. Ask me something cheaper.
```
Subtitle: You do read. Then you know what Legio Septima means over a door, and you know better than to ask me what is behind it. Ask me something cheaper.

### 15. `dlg.vonnra.ford.0.wav`

*Where:* dialogue.json vonnra/ford#0
*Played:* hushed, deliberate; doing: tells you what she saw; pace: very slow; volume: quiet.
*Wants:* you to wonder, not to know
*Note:* Her 'seeing' as sight. 'A light going out at the crossing.' a long pause. 'And then, a little after, another one coming on.' 'It is not often the second thing happens.' almost tender, a secret. Pause. The fee line dry.

```
[hushed, deliberate, quietly] A light going out at the crossing. And then, a little after, another one coming on. It is not often the second thing happens. ...That would be five gold. This once, no charge.
```
Subtitle: A light going out at the crossing. And then, a little after, another one coming on. It is not often the second thing happens. ...That would be five gold. This once, no charge.

### 16. `dlg.vonnra.fortune.0.wav`

*Where:* dialogue.json vonnra/fortune#0
*Played:* calm command, a hidden eagerness; doing: begins the fortune; pace: slow; volume: quiet.
*Wants:* to read the result of her work
*Note:* Commands, unhurried. 'No, the other one' precise. 'I have been waiting to see how it came out.' the only hint of appetite in her voice. 'No charge, this once.' is the call's twin (C01): the same phrasing, close and quiet across a table, so a listener can find it.

```
[calm command, a hidden eagerness, quietly] Sit. Give me your hand. No, the other one: the one you burn with. No charge, this once. I have been waiting to see how it came out.
```
Subtitle: Sit. Give me your hand. No, the other one: the one you burn with. No charge, this once. I have been waiting to see how it came out.

### 17. `dlg.vonnra.fortune.1.wav`

*Where:* dialogue.json vonnra/fortune#1
*Played:* calm command, a hidden eagerness; doing: begins the fortune; pace: slow; volume: quiet.
*Note:* As fortune.0. 'No charge, this once.' is the call's twin (C01): the same phrasing, close and quiet across a table, so a listener can find it.

```
[calm command, a hidden eagerness, quietly] Sit. Give me your hand. No, the other one: the one you draw with. No charge, this once. I have been waiting to see how it came out.
```
Subtitle: Sit. Give me your hand. No, the other one: the one you draw with. No charge, this once. I have been waiting to see how it came out.

### 18. `dlg.vonnra.fortune.2.wav`

*Where:* dialogue.json vonnra/fortune#2
*Played:* expectant calm; doing: to read the result of her own work; pace: slow; volume: level.
*Wants:* to read the result of her own work
*Note:* Practical and exact about the hand. 'I have been waiting to see how it came out' is literal, and she lets it sound like ordinary curiosity. 'No charge, this once.' is the call's twin (C01): the same phrasing, close and quiet across a table, so a listener can find it.

```
[expectant calm] Sit. Give me your hand. No, the other one: the one you hold the blade with. No charge, this once. I have been waiting to see how it came out.
```
Subtitle: Sit. Give me your hand. No, the other one: the one you hold the blade with. No charge, this once. I have been waiting to see how it came out.

### 19. `dlg.vonnra.f_beasts.0.wav`

*Where:* dialogue.json vonnra/f_beasts#0
*Played:* cold judgement; doing: you broke faith with the Pack; pace: slow; volume: quiet.
*Note:* Seeing, as sight. 'So will I.' very quiet, final.

```
[cold judgement, quietly] I see an old wolf who let you into his house, and you, coming back to it with his children's blood on your hands. Whatever else you did about the wolves, he will remember that first. So will I.
```
Subtitle: I see an old wolf who let you into his house, and you, coming back to it with his children's blood on your hands. Whatever else you did about the wolves, he will remember that first. So will I.

### 20. `dlg.vonnra.f_beasts.1.wav`

*Where:* dialogue.json vonnra/f_beasts#1
*Played:* approving, grave; doing: you cured the wolves; pace: slow; volume: quiet.
*Note:* The images unhurried. The last sentence a quiet lesson, approving.

```
[approving, grave, quietly] I see water running clear. Wolves in the deep wood where they belong, and a hole in the hillside with no poison coming out of it. You went looking for the cause and not the culprit. Most people never learn the difference.
```
Subtitle: I see water running clear. Wolves in the deep wood where they belong, and a hole in the hillside with no poison coming out of it. You went looking for the cause and not the culprit. Most people never learn the difference.

### 21. `dlg.vonnra.f_beasts.2.wav`

*Where:* dialogue.json vonnra/f_beasts#2
*Played:* measured, warning; doing: you run with wolves; pace: slow; volume: quiet.
*Note:* A faint amusement at Holloway. 'Be careful what you have taught them to follow.' a warning.

```
[measured, warning, quietly] I see wolves running beside you, not at you. The old grey one lets you walk in front. Holloway sleeps with his sword across his knees now. Be careful what you have taught them to follow.
```
Subtitle: I see wolves running beside you, not at you. The old grey one lets you walk in front. Holloway sleeps with his sword across his knees now. Be careful what you have taught them to follow.

### 22. `dlg.vonnra.f_beasts.3.wav`

*Where:* dialogue.json vonnra/f_beasts#3
*Played:* cold, unsparing; doing: you slaughtered the Pack; pace: slow; volume: quiet.
*Note:* Flat images. The last sentence slow and pitiless.

```
[cold, unsparing, quietly] I see pelts. A great many pelts, and a grey one on top of the pile. The road is safe and the wood is quiet. Something that was sick got sicker, and then there was nothing left of it to be sick.
```
Subtitle: I see pelts. A great many pelts, and a grey one on top of the pile. The road is safe and the wood is quiet. Something that was sick got sicker, and then there was nothing left of it to be sick.

### 23. `dlg.vonnra.f_beasts.4.wav`

*Where:* dialogue.json vonnra/f_beasts#4
*Played:* cold irony; doing: you slaughtered the Pack; pace: slow; volume: quiet.
*Note:* 'Too quiet.' A pause before the simile.

```
[cold irony, quietly] I see a quiet wood. Too quiet. You made the road safe the way a fire makes a house warm.
```
Subtitle: I see a quiet wood. Too quiet. You made the road safe the way a fire makes a house warm.

### 24. `dlg.vonnra.f_beasts.5.wav`

*Where:* dialogue.json vonnra/f_beasts#5
*Played:* cool reproach; doing: you did nothing; pace: slow; volume: quiet.
*Note:* 'You were busy. The world was not.' two flat strokes.

```
[cool reproach, quietly] I see wolves at the east gate, and a man of the Watch who did not come home. You were busy. The world was not.
```
Subtitle: I see wolves at the east gate, and a man of the Watch who did not come home. You were busy. The world was not.

### 25. `dlg.vonnra.f_beasts.6.wav`

*Where:* dialogue.json vonnra/f_beasts#6
*Played:* dry, knowing; doing: you sold the cure; pace: slow; volume: quiet.
*Note:* 'Someone always is.' dry. The Wenna line pointed.

```
[dry, knowing, quietly] I see clean water, and a ledger with a new line in it. The wolves are saved and Pell Varrow owns a hole in the ground. You were paid; he was paid. Someone always is. Wenna has not forgiven you, and she is the one who notices.
```
Subtitle: I see clean water, and a ledger with a new line in it. The wolves are saved and Pell Varrow owns a hole in the ground. You were paid; he was paid. Someone always is. Wenna has not forgiven you, and she is the one who notices.

### 26. `dlg.vonnra.f_beasts.7.wav`

*Where:* dialogue.json vonnra/f_beasts#7
*Played:* veiled; doing: the wolves are unresolved; pace: slow; volume: quiet.

```
[veiled, quietly] The wolves, I see only dimly. Whatever you meant to do about them, you have not done it yet.
```
Subtitle: The wolves, I see only dimly. Whatever you meant to do about them, you have not done it yet.

### 27. `dlg.vonnra.f_caravan.0.wav`

*Where:* dialogue.json vonnra/f_caravan#0
*Played:* grave, watchful; doing: Jory knows; pace: slow; volume: quiet.
*Note:* Images; the last clause heavy with consequence.

```
[grave, watchful, quietly] I see a boy in a wagon, and his uncle sitting up beside him all night. The boy is not asleep. He knows what he carried now, and he is deciding what that makes his uncle.
```
Subtitle: I see a boy in a wagon, and his uncle sitting up beside him all night. The boy is not asleep. He knows what he carried now, and he is deciding what that makes his uncle.

### 28. `dlg.vonnra.f_caravan.1.wav`

*Where:* dialogue.json vonnra/f_caravan#1
*Played:* measured approval; doing: the caravan restored; pace: slow; volume: quiet.
*Note:* Warm images; the last sentence a cool compliment.

```
[measured approval, quietly] I see a boy asleep in a wagon, and his uncle sitting up beside him all night. Salt and iron back where they belong. The Coyle Company will say your name at every table it sits at.
```
Subtitle: I see a boy asleep in a wagon, and his uncle sitting up beside him all night. Salt and iron back where they belong. The Coyle Company will say your name at every table it sits at.

### 29. `dlg.vonnra.f_caravan.2.wav`

*Where:* dialogue.json vonnra/f_caravan#2
*Played:* dry warning; doing: you sold the box; pace: slow; volume: quiet.
*Note:* 'People always do.' quiet.

```
[dry warning, quietly] I see a boy come home, and a strongbox go the other way. Harlan will learn where it went. People always do.
```
Subtitle: I see a boy come home, and a strongbox go the other way. Harlan will learn where it went. People always do.

### 30. `dlg.vonnra.f_caravan.3.wav`

*Where:* dialogue.json vonnra/f_caravan#3
*Played:* measured; doing: the teamsters home; pace: slow; volume: quiet.

```
[measured, quietly] I see three teamsters walking home, thinner than when they left. What became of the rest of it is between you and the Kerchiefs.
```
Subtitle: I see three teamsters walking home, thinner than when they left. What became of the rest of it is between you and the Kerchiefs.

### 31. `dlg.vonnra.f_caravan.4.wav`

*Where:* dialogue.json vonnra/f_caravan#4
*Played:* cold, final; doing: the prisoners died; pace: very slow; volume: quiet.
*Note:* 'I see cages.' Pause. 'You know.' barely voiced.

```
[cold, final, quietly] I see cages. I will not tell you what is in them. You know.
```
Subtitle: I see cages. I will not tell you what is in them. You know.

### 32. `dlg.vonnra.f_caravan.5.wav`

*Where:* dialogue.json vonnra/f_caravan#5
*Played:* veiled; doing: unfinished; pace: slow; volume: quiet.
*Note:* 'Neither are you.' a quiet hook.

```
[veiled, quietly] The caravan: a cold trail, cold cages. It is not finished. Neither are you.
```
Subtitle: The caravan: a cold trail, cold cages. It is not finished. Neither are you.

### 33. `dlg.vonnra.f_pell.0.wav`

*Where:* dialogue.json vonnra/f_pell#0
*Played:* cold satisfaction; doing: Pell in a cage; pace: slow; volume: quiet.
*Note:* 'He is still counting.' A hint of pity, none of mercy.

```
[cold satisfaction, quietly] And Pell Varrow, in a cage that was built for someone else. You know which one. He is still counting. It is all he has left to do.
```
Subtitle: And Pell Varrow, in a cage that was built for someone else. You know which one. He is still counting. It is all he has left to do.

### 34. `dlg.vonnra.f_pell.1.wav`

*Where:* dialogue.json vonnra/f_pell#1
*Played:* dry, ominous; doing: Pell arrested; pace: slow; volume: quiet.
*Note:* Dry about his protests. 'They are not in this town.' ominous.

```
[dry, ominous, quietly] And Pell. Pell in irons, being walked to the cells, telling everyone who will listen that he has friends. He does. They are not in this town.
```
Subtitle: And Pell. Pell in irons, being walked to the cells, telling everyone who will listen that he has friends. He does. They are not in this town.

### 35. `dlg.vonnra.f_pell.2.wav`

*Where:* dialogue.json vonnra/f_pell#2
*Played:* cool warning; doing: you are in Pell's book; pace: slow; volume: quiet.

```
[cool warning, quietly] And a ledger, with your name in it, in Pell's small tidy hand. You were paid. So was everyone else in that book. I would keep an eye on all of them.
```
Subtitle: And a ledger, with your name in it, in Pell's small tidy hand. You were paid. So was everyone else in that book. I would keep an eye on all of them.

### 36. `dlg.vonnra.f_pell.3.wav`

*Where:* dialogue.json vonnra/f_pell#3
*Played:* measured warning; doing: Pell fled; pace: slow; volume: quiet.
*Note:* 'He took his books with him.' plain. 'You are in them.' quiet: the warning is in the last four words.

```
[measured warning, quietly] And an empty warehouse, and a man on a fast horse who will not stop until he is somewhere that has never heard of the Coyle Company. He took his books with him. You are in them.
```
Subtitle: And an empty warehouse, and a man on a fast horse who will not stop until he is somewhere that has never heard of the Coyle Company. He took his books with him. You are in them.

### 37. `dlg.vonnra.f_pell.4.wav`

*Where:* dialogue.json vonnra/f_pell#4
*Played:* ominous; doing: Pell is counting; pace: slow; volume: quiet.
*Note:* 'One day he will count you.' quiet.

```
[ominous, quietly] And Pell Varrow, counting. He is always counting. One day he will count you.
```
Subtitle: And Pell Varrow, counting. He is always counting. One day he will count you.

### 38. `dlg.vonnra.f_self.0.wav`

*Where:* dialogue.json vonnra/f_self#0
*Played:* intense, controlled curiosity; doing: you have died; pace: slow; volume: quiet.
*Wants:* to hide that she knows exactly what
*Note:* 'And you.' A beat. The middle sentence a wry understatement. 'I would very much like to know what.' a lie, smoothly told.

```
[intense, controlled curiosity, quietly] And you. You have already died on this road. Most people only get to do that the once. Something did not want you to stay down, and I would very much like to know what.
```
Subtitle: And you. You have already died on this road. Most people only get to do that the once. Something did not want you to stay down, and I would very much like to know what.

### 39. `dlg.vonnra.f_self.1.wav`

*Where:* dialogue.json vonnra/f_self#1
*Played:* dry; doing: you are wanted; pace: slow; volume: quiet.
*Note:* 'It is not flattering.' the driest line she has.

```
[dry, quietly] And you. The Watch has your description. It is not flattering.
```
Subtitle: And you. The Watch has your description. It is not flattering.

### 40. `dlg.vonnra.f_self.2.wav`

*Where:* dialogue.json vonnra/f_self#2
*Played:* dry, observant; doing: you smell of wolves; pace: slow; volume: quiet.

```
[dry, observant, quietly] And you, who smell of the Pack now. Dogs in the square will not bark at you. People will.
```
Subtitle: And you, who smell of the Pack now. Dogs in the square will not bark at you. People will.

### 41. `dlg.vonnra.f_self.3.wav`

*Where:* dialogue.json vonnra/f_self#3
*Played:* hushed significance; doing: the lamps lit for you; pace: very slow; volume: quiet.
*Note:* Her secret almost surfacing. 'and the lamps lit for you' too gentle. The last sentence a held breath.

```
[hushed significance, quietly] And you. You came up the Low Ford road at night, and the lamps lit for you. They have not done that for anyone in a long time.
```
Subtitle: And you. You came up the Low Ford road at night, and the lamps lit for you. They have not done that for anyone in a long time.

### 42. `dlg.vonnra.f_below.0.p0.wav`

*Where:* dialogue.json vonnra/f_below#0; part 1 of 2: **vonnra: Last. Under the Verge, something is turning over in its sleep, and under a farm past the O…** / narrator: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame …
*Played:* hushed dread; doing: the thing below; pace: very slow; volume: quiet.
*Note:* The deepest reading: slower and lower, never whispered (a whisper turns her breathy). Unhurried images; 'they think it will be grateful' with pity. The roof shivers, and she does not finish: trails off on the door, deliberately.

```
[hushed dread, quietly] Last. Under the Verge, something is turning over in its sleep, and under a farm past the Old Road, something is knocking to be let in. The little lamp-people are digging down to it with the Warden's heart in their arms, and they think it will be grateful. And the door in the hillside...
```
Subtitle: Last. Under the Verge, something is turning over in its sleep, and under a farm past the Old Road, something is knocking to be let in. The little lamp-people are digging down to it with the Warden's heart in their arms, and they think it will be grateful. And the door in the hillside...

### 43. `dlg.vonnra.f_below.1.p0.wav`

*Where:* dialogue.json vonnra/f_below#1; part 1 of 2: **vonnra: Last. Under the Verge, something is turning over in its sleep. The little lamp-people are …** / narrator: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame …
*Played:* hushed dread; doing: the thing below; pace: very slow; volume: quiet.
*Note:* The deepest reading: slower and lower, never whispered (a whisper turns her breathy). Unhurried images; 'they think it will be grateful' with pity. The roof shivers, and she does not finish: trails off on the door, deliberately.

```
[hushed dread, quietly] Last. Under the Verge, something is turning over in its sleep. The little lamp-people are digging down to it with the Warden's heart in their arms, and they think it will be grateful. And the door in the hillside...
```
Subtitle: Last. Under the Verge, something is turning over in its sleep. The little lamp-people are digging down to it with the Warden's heart in their arms, and they think it will be grateful. And the door in the hillside...

### 44. `dlg.vonnra.f_door.0.p0.wav`

*Where:* dialogue.json vonnra/f_door#0; part 1 of 2: **vonnra: The door in the hillside is listening, as I am. That is all I see for free.** / vonnra: The rest you will walk into yourself, and you will, because you are the kind that does.
*Played:* calm, intimate, inexorable; doing: closes the reading, using your name; pace: slow; volume: quiet.
*Note:* 'is listening, as I am' very quiet. A beat where the name would be. The last sentence certain, almost fond.
*The name:* the survivor's name (one of her name takes, at the end of this packet) is spliced in straight after this take, so end it leading into a name, not closing the sentence.

```
[calm, intimate, inexorable, quietly] The door in the hillside is listening, as I am. That is all I see for free,
```
Subtitle: The door in the hillside is listening, as I am. That is all I see for free.

### 45. `dlg.vonnra.f_door.0.p1.wav`

*Where:* dialogue.json vonnra/f_door#0; part 2 of 2: vonnra: The door in the hillside is listening, as I am. That is all I see for free. / **vonnra: The rest you will walk into yourself, and you will, because you are the kind that does.**
*Played:* calm, intimate, inexorable; doing: closes the reading, using your name; pace: slow; volume: quiet.
*Note:* 'is listening, as I am' very quiet. A beat where the name would be. The last sentence certain, almost fond.
*The name:* the survivor's name comes just before this take, in the pause; start as if she had just said it.

```
[calm, intimate, inexorable, quietly] The rest you will walk into yourself, and you will, because you are the kind that does.
```
Subtitle: The rest you will walk into yourself, and you will, because you are the kind that does.

### 46. `dlg.vonnra.f_door.1.wav`

*Where:* dialogue.json vonnra/f_door#1
*Played:* calm, inexorable; doing: closes the reading; pace: slow; volume: quiet.
*Note:* The last sentence certain, almost fond.

```
[calm, inexorable, quietly] The door is not for sale. That is all I see for free. The rest you will walk into yourself, and you will, because you are the kind that does.
```
Subtitle: The door is not for sale. That is all I see for free. The rest you will walk into yourself, and you will, because you are the kind that does.

### 47. `dlg.vonnra.cb_opened_vault.0.wav`

*Where:* dialogue.json vonnra/cb_opened_vault#0
*Played:* shaken, controlled; doing: you opened the door; pace: slow; volume: quiet.
*Note:* 'You opened it.' A long pause, the closest she comes to fear. Then sharp control: she would rather you stood. The question urgent under the calm.

```
[shaken, controlled, quietly] You opened it. ...Do not sit, traveller. I would rather you stood. What did you see on the stair?
```
Subtitle: You opened it. ...Do not sit, traveller. I would rather you stood. What did you see on the stair?

### 48. `dlg.vonnra.cb_vault2.0.wav`

*Where:* dialogue.json vonnra/cb_vault2#0
*Played:* relief hidden as finality; doing: the dead still hold; pace: slow; volume: quiet.
*Note:* 'Then it is still there.' Repeat 'that is all' exactly the same both times; the repetition is the tell.

```
[relief hidden as finality, quietly] Then it is still there. That is all. I will say it again, because it bears repeating: that is all.
```
Subtitle: Then it is still there. That is all. I will say it again, because it bears repeating: that is all.

### 49. `dlg.vonnra.cb_vault3.0.wav`

*Where:* dialogue.json vonnra/cb_vault3#0
*Played:* cool, menacing; doing: silence has a price; pace: slow; volume: quiet.
*Note:* 'Yours, for now.' cool. Then quiet menace. 'You will find I collect.' softly.

```
[cool, menacing, quietly] Yours, for now. Payment, always, traveller; even for silence. You will find I collect.
```
Subtitle: Yours, for now. Payment, always, traveller; even for silence. You will find I collect.

### 50. `dlg.vonnra.cb_core_stolen.0.wav`

*Where:* dialogue.json vonnra/cb_core_stolen#0
*Played:* cold, controlled anger; doing: the heart was lost; pace: very slow; volume: quiet.
*Note:* Each word placed. 'I am not angry.' A beat. 'I am arranging.' the coldest line in the act.

```
[cold, controlled anger, quietly] A heart went into the ground at the Low Ford, and you watched it go. I am not angry. I am arranging.
```
Subtitle: A heart went into the ground at the Low Ford, and you watched it go. I am not angry. I am arranging.

### 51. `dlg.vonnra.cb_exposed_pell.0.wav`

*Where:* dialogue.json vonnra/cb_exposed_pell#0
*Played:* dry, calculating; doing: Pell is caught; pace: slow; volume: quiet.
*Note:* Dry; the last sentence calculating, faintly threatening.

```
[dry, calculating, quietly] Pell Varrow in irons. He owed me a great deal. I shall have to find another way to be paid.
```
Subtitle: Pell Varrow in irons. He owed me a great deal. I shall have to find another way to be paid.

### 52. `dlg.vonnra.say_calling.0.wav`

*Where:* dialogue.json vonnra/say_calling#0
*Played:* gentle condescension; doing: reads a warden; pace: slow; volume: quiet.
*Note:* Three nouns, unhurried. 'It is a lovely belief.' kind and pitying.

```
[gentle condescension, quietly] Shields. Gates. Walls. You believe things can be kept out, traveller. It is a lovely belief.
```
Subtitle: Shields. Gates. Walls. You believe things can be kept out, traveller. It is a lovely belief.

### 53. `dlg.vonnra.say_calling.1.wav`

*Where:* dialogue.json vonnra/say_calling#1
*Played:* measured warning; doing: reads a reaver; pace: slow; volume: quiet.

```
[measured warning, quietly] You will break a great many things before the end. Try to choose them.
```
Subtitle: You will break a great many things before the end. Try to choose them.

### 54. `dlg.vonnra.say_calling.2.wav`

*Where:* dialogue.json vonnra/say_calling#2
*Played:* veiled warning; doing: reads an arcanist; pace: slow; volume: quiet.
*Note:* 'Some of them keep ledgers.' a real warning.

```
[veiled warning, quietly] You carry a fire you did not buy. Be careful whom you show it to. Some of them keep ledgers.
```
Subtitle: You carry a fire you did not buy. Be careful whom you show it to. Some of them keep ledgers.

### 55. `dlg.vonnra.say_calling.3.wav`

*The same words are also* `dlg.vonnra.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json vonnra/say_calling#3
*Played:* cool approval; doing: reads a stalker; pace: slow; volume: quiet.
*Note:* 'I noticed.' quiet.

```
[cool approval, quietly] You came to my window from the side the light does not reach. Few think to. I noticed.
```
Subtitle: You came to my window from the side the light does not reach. Few think to. I noticed.

### 56. `dlg.vonnra.coin.0.wav`

*Where:* dialogue.json vonnra/coin#0
*Played:* reverent, guarded; doing: the square coin; pace: slow; volume: quiet.
*Note:* Old-empire, square: fingering it. Lineage, quiet pride. 'something that cannot be bought twice' almost a confession. Pause. Then dry: 'Do not grow used to it.'

```
[reverent, guarded, quietly] Old-empire. Square. My grandmother's, and hers before. I have never spent it. One day I shall, and it will buy something that cannot be bought twice. ...That was free. Do not grow used to it.
```
Subtitle: Old-empire. Square. My grandmother's, and hers before. I have never spent it. One day I shall, and it will buy something that cannot be bought twice. ...That was free. Do not grow used to it.

### 57. `dlg.vonnra.risen.0.wav`

*Where:* dialogue.json vonnra/risen#0
*Played:* grave, knowing; doing: you came back from death; pace: slow; volume: quiet.
*Note:* 'You came back.' Long pause. Firm instructions. 'you will find out who holds the note' very quiet, very sure.

```
[grave, knowing, quietly] You came back. Most do not, the first time. ...Do not thank Chid. Do not thank anyone. Payment, always, traveller, and for that above all; you will find out who holds the note.
```
Subtitle: You came back. Most do not, the first time. ...Do not thank Chid. Do not thank anyone. Payment, always, traveller, and for that above all; you will find out who holds the note.

### 58. `dlg.vonnra.jessop.0.p0.wav`

*Where:* dialogue.json vonnra/jessop#0; part 1 of 3: **vonnra: Gone south. On the toll's business.** / narrator: She turns a page of the ledger that does not need turning. / vonnra: Clerks go south, traveller. It is the direction they fall in.
*Played:* smooth evasion; doing: covers for Jessop; pace: slow; volume: quiet.
*Note:* Unruffled. Narrator: the page that does not need turning. The last line a quiet, chilling aphorism.

```
[smooth evasion, quietly] Gone south. On the toll's business.
```
Subtitle: Gone south. On the toll's business.

### 59. `dlg.vonnra.jessop.0.p2.wav`

*Where:* dialogue.json vonnra/jessop#0; part 3 of 3: vonnra: Gone south. On the toll's business. / narrator: She turns a page of the ledger that does not need turning. / **vonnra: Clerks go south, traveller. It is the direction they fall in.**
*Played:* smooth evasion; doing: covers for Jessop; pace: slow; volume: quiet.
*Note:* Unruffled. Narrator: the page that does not need turning. The last line a quiet, chilling aphorism.

```
[smooth evasion, quietly] Clerks go south, traveller. It is the direction they fall in.
```
Subtitle: Clerks go south, traveller. It is the direction they fall in.

### 60. `dlg.vonnra.f_ember.0.wav`

*Where:* dialogue.json vonnra/f_ember#0
*Played:* curious, wary; doing: Redcowl keeps the crates; pace: slow; volume: quiet.
*Note:* 'I wonder for what.' genuinely interested, and wary.

```
[curious, wary, quietly] And six crates in a bandit's tent, guarded now by a man who knows what they are for. He will not sell them. He is saving them. I wonder for what.
```
Subtitle: And six crates in a bandit's tent, guarded now by a man who knows what they are for. He will not sell them. He is saving them. I wonder for what.

### 61. `dlg.vonnra.f_ember.1.wav`

*Where:* dialogue.json vonnra/f_ember#1
*Played:* cool distinction; doing: the crates go home; pace: slow; volume: quiet.
*Note:* 'That is honest. It is not the same thing as good.' a lesson.

```
[cool distinction, quietly] And six crates going home to a man who knows where they go next. You told him where to find what was his. That is honest. It is not the same thing as good.
```
Subtitle: And six crates going home to a man who knows where they go next. You told him where to find what was his. That is honest. It is not the same thing as good.

### 62. `dlg.vonnra.f_ember.2.wav`

*Where:* dialogue.json vonnra/f_ember#2
*Played:* cold approval; doing: the crates drowned; pace: slow; volume: quiet.
*Note:* 'where nothing will ever buy them' plain. 'That is the first thing you have thrown away that I approve of.' cold, and as near to a compliment as she comes.

```
[cold approval, quietly] And six crates at the bottom of a stream, where nothing will ever buy them. That is the first thing you have thrown away that I approve of.
```
Subtitle: And six crates at the bottom of a stream, where nothing will ever buy them. That is the first thing you have thrown away that I approve of.

### 63. `dlg.vonnra.f_ember.3.wav`

*Where:* dialogue.json vonnra/f_ember#3
*Played:* cold; doing: the crates burned; pace: slow; volume: quiet.
*Note:* 'Everyone did.' quiet.

```
[cold, quietly] And six crates that went up with the Roost. You will have heard it from the wall. Everyone did.
```
Subtitle: And six crates that went up with the Roost. You will have heard it from the wall. Everyone did.

### 64. `dlg.vonnra.f_ember.4.wav`

*Where:* dialogue.json vonnra/f_ember#4
*Played:* dry, knowing; doing: the crates sold on; pace: slow; volume: quiet.
*Note:* 'sold to whoever paid for them first' flat. 'I think you know who that was.' quiet: she does, and so do you.

```
[dry, knowing, quietly] And six crates gone down the south road with the rest of the cargo, sold to whoever paid for them first. I think you know who that was.
```
Subtitle: And six crates gone down the south road with the rest of the cargo, sold to whoever paid for them first. I think you know who that was.

### 65. `dlg.vonnra.f_ember.5.wav`

*Where:* dialogue.json vonnra/f_ember#5
*Played:* dark certainty; doing: to warn that the trade will finish itself; pace: slow; volume: level.
*Wants:* to warn that the trade will finish itself
*Note:* 'Someone always does' is a law she lives by. Neither threat nor regret; a ledger fact.

```
[dark certainty] And six crates still waiting in a ravine to go where they were paid to go. Someone will deliver them. Someone always does.
```
Subtitle: And six crates still waiting in a ravine to go where they were paid to go. Someone will deliver them. Someone always does.

### 66. `dlg.vonnra.f_ember.6.wav`

*Where:* dialogue.json vonnra/f_ember#6
*Played:* oblique warning; doing: to plant a question they have not asked; pace: slow; volume: quiet.
*Wants:* to plant a question they have not asked
*Note:* She knows what B.E. means and lets the letters hang unread. 'Someone always does' is quiet and certain.

```
[oblique warning, quietly] And six crates nobody opened, marked with two letters, waiting in a ravine to go where they were paid to go. Someone will deliver them. Someone always does.
```
Subtitle: And six crates nobody opened, marked with two letters, waiting in a ravine to go where they were paid to go. Someone will deliver them. Someone always does.

### 67. `dlg.vonnra.f_past.0.p0.wav`

*Where:* dialogue.json vonnra/f_past#0; part 1 of 2: **vonnra: And before the ford: a child following tracks through these woods, with a bow too big for …** / narrator: She is not looking at your palm.
*Played:* intimate, uncanny; doing: quotes what you said in Sella's bed; pace: slow; volume: quiet.
*Note:* She is reciting something bought, but makes it sound like sight. Narrator: she is not looking at your palm.

```
[intimate, uncanny, quietly] And before the ford: a child following tracks through these woods, with a bow too big for them.
```
Subtitle: And before the ford: a child following tracks through these woods, with a bow too big for them.

### 68. `dlg.vonnra.f_past.1.p0.wav`

*Where:* dialogue.json vonnra/f_past#1; part 1 of 2: **vonnra: And before the ford: four years in a cloister cellar among dead men's letters, and a lens …** / narrator: She is not looking at your palm.
*Played:* intimate, uncanny; doing: quotes what you said in Sella's bed; pace: slow; volume: quiet.
*Note:* As f_past.0.

```
[intimate, uncanny, quietly] And before the ford: four years in a cloister cellar among dead men's letters, and a lens you were not meant to leave with.
```
Subtitle: And before the ford: four years in a cloister cellar among dead men's letters, and a lens you were not meant to leave with.

### 69. `dlg.vonnra.f_past.2.p0.wav`

*Where:* dialogue.json vonnra/f_past#2; part 1 of 2: **vonnra: And before the ford: worse company than the Kerchiefs, and the trick of walking away from …** / narrator: She is not looking at your palm.
*Played:* intimate, uncanny; doing: quotes what you said in Sella's bed; pace: slow; volume: quiet.
*Note:* As f_past.0.

```
[intimate, uncanny, quietly] And before the ford: worse company than the Kerchiefs, and the trick of walking away from it.
```
Subtitle: And before the ford: worse company than the Kerchiefs, and the trick of walking away from it.

### 70. `dlg.vonnra.f_past.3.p0.wav`

*Where:* dialogue.json vonnra/f_past#3; part 1 of 2: **vonnra: And before the ford: chapel lamps that nobody came to see, and you, lighting them anyway.** / narrator: She is not looking at your palm.
*Played:* intimate, uncanny; doing: quotes what you said in Sella's bed; pace: slow; volume: quiet.
*Note:* As f_past.0.

```
[intimate, uncanny, quietly] And before the ford: chapel lamps that nobody came to see, and you, lighting them anyway.
```
Subtitle: And before the ford: chapel lamps that nobody came to see, and you, lighting them anyway.

### 71. `dlg.vonnra.f_past.4.wav`

*Where:* dialogue.json vonnra/f_past#4
*Played:* gentle, unsettling; doing: your past is lost; pace: slow; volume: quiet.
*Note:* 'Most do.' soft.

```
[gentle, unsettling, quietly] Of before the ford, I see very little. The water took it, or you left it on the far bank. Most do.
```
Subtitle: Of before the ford, I see very little. The water took it, or you left it on the far bank. Most do.

### 72. `dlg.vonnra.f_accuse.0.p1.wav`

*Where:* dialogue.json vonnra/f_accuse#0; part 2 of 3: narrator: For the first time she looks at your face and not at your hand. It goes on long enough tha… / **vonnra: ...Sit down.** / vonnra: I have not finished reading.
*Played:* listening very hard, caught for once; doing: accused, she answers with your name; pace: very slow; volume: quiet.
*Wants:* you to sit and hear the rest
*Note:* The narrator holds the long look. Not denial, not admission. A breath before 'Sit down' (she is alive, and it is cold). The name is spliced in at the pause, its own take in her voice: the only warmth anywhere in her part, and it should frighten. 'I have not finished reading.' quietly in command. Never 'traveller'.
*The name:* the survivor's name (one of her name takes, at the end of this packet) is spliced in straight after this take, so end it leading into a name, not closing the sentence.

```
[listening very hard, caught for once, quietly] [inhales] ...Sit down,
```
Subtitle: ...Sit down.

### 73. `dlg.vonnra.f_accuse.0.p2.wav`

*Where:* dialogue.json vonnra/f_accuse#0; part 3 of 3: narrator: For the first time she looks at your face and not at your hand. It goes on long enough tha… / vonnra: ...Sit down. / **vonnra: I have not finished reading.**
*Played:* listening very hard, caught for once; doing: accused, she answers with your name; pace: very slow; volume: quiet.
*Wants:* you to sit and hear the rest
*Note:* The narrator holds the long look. Not denial, not admission. A breath before 'Sit down' (she is alive, and it is cold). The name is spliced in at the pause, its own take in her voice: the only warmth anywhere in her part, and it should frighten. 'I have not finished reading.' quietly in command. Never 'traveller'.
*The name:* the survivor's name comes just before this take, in the pause; start as if she had just said it.

```
[listening very hard, caught for once, quietly] I have not finished reading.
```
Subtitle: I have not finished reading.

## The survivor's name

One take for each name the creation screen suggests. The game splices it into every line where she says the survivor's name (marked *The name* above); a name the player types that is not on this list leaves the pause empty. Keep each the same in tone, so it fits all of them.

### 74. `name.vonnra.Alder.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Alder.
```
Subtitle: Alder.

### 75. `name.vonnra.Bryony.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Bryony.
```
Subtitle: Bryony.

### 76. `name.vonnra.Cass.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Cass.
```
Subtitle: Cass.

### 77. `name.vonnra.Dace.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Dace.
```
Subtitle: Dace.

### 78. `name.vonnra.Edda.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Edda.
```
Subtitle: Edda.

### 79. `name.vonnra.Fen.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Fen.
```
Subtitle: Fen.

### 80. `name.vonnra.Garrow.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Garrow.
```
Subtitle: Garrow.

### 81. `name.vonnra.Hester.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Hester.
```
Subtitle: Hester.

### 82. `name.vonnra.Ilse.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Ilse.
```
Subtitle: Ilse.

### 83. `name.vonnra.Jessamy.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Jessamy.
```
Subtitle: Jessamy.

### 84. `name.vonnra.Kit.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Kit.
```
Subtitle: Kit.

### 85. `name.vonnra.Lorne.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Lorne.
```
Subtitle: Lorne.

### 86. `name.vonnra.Maren.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Maren.
```
Subtitle: Maren.

### 87. `name.vonnra.Nolly.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Nolly.
```
Subtitle: Nolly.

### 88. `name.vonnra.Orla.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Orla.
```
Subtitle: Orla.

### 89. `name.vonnra.Pim.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Pim.
```
Subtitle: Pim.

### 90. `name.vonnra.Quill.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Quill.
```
Subtitle: Quill.

### 91. `name.vonnra.Rhosyn.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Rhosyn.
```
Subtitle: Rhosyn.

### 92. `name.vonnra.Sabre.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Sabre.
```
Subtitle: Sabre.

### 93. `name.vonnra.Tegan.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Tegan.
```
Subtitle: Tegan.

### 94. `name.vonnra.Ulla.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Ulla.
```
Subtitle: Ulla.

### 95. `name.vonnra.Voss.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Voss.
```
Subtitle: Voss.

### 96. `name.vonnra.Wren.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Wren.
```
Subtitle: Wren.

### 97. `name.vonnra.Yarrow.wav`

*Where:* Front.cs Names (the creation screen)
*Played:* level, exact; doing: a name read from her ledger; pace: slow; volume: quiet.
*Note:* Level, exact, unhurried: a name read from her ledger. Not warm, but known, as if she has always had it; that is what frightens. The same take goes into the accusation ('Sit down, ...'), the door ('That is all I see for free, ...') and her greeting ever after ('... Your chapter is written.').

```
[level, exact, quietly] Yarrow.
```
Subtitle: Yarrow.

## Said in passing

### 98. `bark.vonnra.day.0.wav`

*Where:* npcs.json vonnra.barks[0]
*Played:* still; pace: slow; volume: quiet.

```
[still, quietly] The toll is the toll.
```
Subtitle: The toll is the toll.

### 99. `bark.vonnra.day.1.wav`

*Where:* npcs.json vonnra.barks[1]
*Played:* still; pace: slow; volume: quiet.

```
[still, quietly] I see a great deal. I say very little. You will find that is the arrangement.
```
Subtitle: I see a great deal. I say very little. You will find that is the arrangement.

### 100. `bark.vonnra.night.0.wav`

*Where:* npcs.json vonnra.nightBarks[0]
*Played:* still; pace: slow; volume: quiet.

```
[still, quietly] The toll does not sleep, and neither do I.
```
Subtitle: The toll does not sleep, and neither do I.

### 101. `bark.vonnra.night.1.wav`

*Where:* npcs.json vonnra.nightBarks[1]
*Played:* still; pace: slow; volume: quiet.

```
[still, quietly] The dark is also a customer.
```
Subtitle: The dark is also a customer.

### 102. `bark.vonnra.night.2.wav`

*Where:* npcs.json vonnra.nightBarks[2]
*Played:* still; pace: slow; volume: quiet.

```
[still, quietly] Payment, even now.
```
Subtitle: Payment, even now.

### 103. `bark.vonnra.night.3.wav`

*Where:* npcs.json vonnra.nightBarks[3]
*Played:* still; pace: slow; volume: quiet.

```
[still, quietly] The ford is quiet tonight. It will not stay quiet.
```
Subtitle: The ford is quiet tonight. It will not stay quiet.


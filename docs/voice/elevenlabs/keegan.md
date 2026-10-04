# Dame Keegan Orme: ElevenLabs packet

Voice id in the game: `keegan`. 44 takes to record (4,924 characters; about 14,772 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

**Hold 1 of these** (marked HOLD below, with why); the rest can be recorded now.

## Who they are

**Dame Keegan Orme** (the Argent Vigil, probationary). Over-articulated and earnest, a lecturer's projection; no contractions while she is on duty, and they slip out when she forgets herself (which is the joke, and later the tell). Cites the probationary handbook by chapter. Names rhetorical figures. Never admits the Vigil is gone; never says what chapter four is about. *Casting:* 20s, a woman, Oxbridge RP; comic but sincere.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Dame Keegan Orme`. Never describe a voice as sounding like a real person.

```
Native English (British, Received Pronunciation). Female, 20s. Studio quality. Persona: a young upper-class knight. A young woman in her early twenties, a probationary knight, with a clear, bright, projecting voice and a crisp, over-articulated upper-class English Received Pronunciation accent, like a keen young lecturer. Earnest, formal and sincere, a little comic in her seriousness. Crisp Received Pronunciation. No reverb or effects.
```

Preview text:

```
Dame Keegan Orme, of the Argent Vigil, probationary. The north road is closed by order of the Vigil, under chapter two of the handbook, and I am obliged to explain why at some length.
```

In the Voice Library instead: search for *Oxbridge RP*, *female*, *20*, and listen for this: A young woman in her early twenties, a probationary knight, with a clear, bright, projecting voice and a crisp, over-articulated upper-class English Received Pronunciation accent, like a keen young lecturer. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.keegan.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice keegan
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Keegan

### 1. `dlg.keegan.first.0.wav`

*Where:* dialogue.json keegan/first#0
*Played:* earnest bravado; doing: halts you at the north gate; pace: measured; volume: raised.
*Wants:* to be taken seriously
*Note:* 'Halt!' projected, a touch too loud. Full title, over-articulated. 'Probationary.' a reluctant honesty. 'It is a real title.' defensive.

```
[earnest bravado, loudly] Halt! None pass north. Dame Keegan Orme, of the Argent Vigil. Probationary. It is a real title.
```
Subtitle: Halt! None pass north. Dame Keegan Orme, of the Argent Vigil. Probationary. It is a real title.

### 2. `dlg.keegan.hub.0.wav`

*Where:* dialogue.json keegan/hub#0
*Played:* lecturing, disappointed; doing: checks your reading; pace: measured; volume: level.
*Note:* Schoolmistress; answers herself: 'No? I can tell.'

```
[lecturing, disappointed] You again. Have you read anything since we last spoke? No? I can tell.
```
Subtitle: You again. Have you read anything since we last spoke? No? I can tell.

### 3. `dlg.keegan.hub.1.wav`

*Where:* dialogue.json keegan/hub#1
*Played:* prim certainty; doing: you're not ready; pace: measured; volume: level.
*Note:* Crisp.

```
[prim certainty] Still not ready. I would know.
```
Subtitle: Still not ready. I would know.

### 4. `dlg.keegan.north.0.wav`

*Where:* dialogue.json keegan/north#0
*Played:* solemn, official; doing: refuses the north; pace: measured; volume: level.
*Note:* Grave. 'chapter four' with weight she tries not to show.

```
[solemn, official] Things you are not ready for. When you are, I will know. It is in the probationary handbook, chapter four.
```
Subtitle: Things you are not ready for. When you are, I will know. It is in the probationary handbook, chapter four.

### 5. `dlg.keegan.ch4.0.wav`

*Where:* dialogue.json keegan/ch4#0
*Played:* closed, uneasy; doing: won't say; pace: measured; volume: quiet.
*Note:* A shade too quick; a door shut.

```
[closed, uneasy, quietly] That is between me and chapter four.
```
Subtitle: That is between me and chapter four.

### 6. `dlg.keegan.prof.0.wav`

*Where:* dialogue.json keegan/prof#0
*Played:* proud, pedantic, comic; doing: explains her nickname; pace: measured; volume: level.
*Note:* Lecturer's delivery. Rueful about the children. 'That was litotes. You're welcome.' pleased with herself, enunciated.

```
[proud, pedantic, comic] I taught rhetoric at Saint Wend's before I took the oath, and somebody's mother found out. Now I am Professor to everyone under four feet tall. Rhetoric is not without its uses when telling people no. That was litotes. You're welcome.
```
Subtitle: I taught rhetoric at Saint Wend's before I took the oath, and somebody's mother found out. Now I am Professor to everyone under four feet tall. Rhetoric is not without its uses when telling people no. That was litotes. You're welcome.

### 7. `dlg.keegan.warden.0.wav`

*Where:* dialogue.json keegan/warden#0
*Played:* alarmed, then lecturing, then anxious; doing: the lamps kept the Warden asleep; pace: measured; volume: quiet.
*Wants:* you not to repeat it
*Note:* Sharp '...Who told you that?'. Lecture, gathering seriousness. 'somebody wanted it awake.' cold. Then anxious and small: 'Do not repeat that. I am probationary.'

```
[alarmed, then lecturing, then anxious, quietly] ...Who told you that? The Vigil kept those lamps before the Watch did. Before the Watch was the Watch. Oil. The lamps at the ford were to burn oil, and nothing else; it is in the handbook, with a drawing. Oil keeps it sleeping. Ember wakes it. If somebody lit them with ember, somebody wanted it awake. Do not repeat that. I am probationary.
```
Subtitle: ...Who told you that? The Vigil kept those lamps before the Watch did. Before the Watch was the Watch. Oil. The lamps at the ford were to burn oil, and nothing else; it is in the handbook, with a drawing. Oil keeps it sleeping. Ember wakes it. If somebody lit them with ember, somebody wanted it awake. Do not repeat that. I am probationary.

### 8. `dlg.keegan.who.0.wav`

*Where:* dialogue.json keegan/who#0
*Played:* pointed, suspicious; doing: turns it on you; pace: measured; volume: quiet.
*Note:* Reasoning aloud; 'you were there' a little accusing.

```
[pointed, suspicious, quietly] Someone who needed the ford closed. Someone who wanted a heart. You tell me; you were there.
```
Subtitle: Someone who needed the ford closed. Someone who wanted a heart. You tell me; you were there.

### 9. `dlg.keegan.ashe.0.wav`

*Where:* dialogue.json keegan/ashe#0
*Played:* reverent pride; doing: Captain Ashe; pace: measured; volume: level.
*Note:* Hero-worship. 'with one' quiet. Firm: why she says no.

```
[reverent pride] Know him? The Vigil buried him. He closed the north road with forty lamps and walked back through it with one. What he saw up there is why I am standing here telling you no. Were he here, he would tell you himself, once you were ready.
```
Subtitle: Know him? The Vigil buried him. He closed the north road with forty lamps and walked back through it with one. What he saw up there is why I am standing here telling you no. Were he here, he would tell you himself, once you were ready.

### 10. `dlg.keegan.vigil.0.wav`

*Where:* dialogue.json keegan/vigil#0
*Played:* brave face, then quiet doubt; doing: her absent order; pace: measured then slow; volume: level.
*Note:* Brisk official answer. A pause. The excuse runs on and gets smaller; 'being read by nobody' almost a whisper.

```
[brave face, then quiet doubt] At the chapterhouse, in the north. Keeping the vigil. I write every month. They are very busy. ...It is a long way, and the roads are bad, and I am sure the letters are simply waiting at a waystation somewhere, being read by nobody.
```
Subtitle: At the chapterhouse, in the north. Keeping the vigil. I write every month. They are very busy. ...It is a long way, and the roads are bad, and I am sure the letters are simply waiting at a waystation somewhere, being read by nobody.

### 11. `dlg.keegan.ready.0.wav`

*Where:* dialogue.json keegan/ready#0
*Played:* ominous, then flustered; doing: the signs; pace: measured; volume: level.
*Note:* Too honest: 'You would not like it if I saw them.' Then flustered backtracking, a weak joke about paperwork.

```
[ominous, then flustered] The handbook is very clear on the signs, and I am watching for them. You would not like it if I saw them. ...That came out wrong. I mean you would not like the paperwork.
```
Subtitle: The handbook is very clear on the signs, and I am watching for them. You would not like it if I saw them. ...That came out wrong. I mean you would not like the paperwork.

### 12. `dlg.keegan.cb_opened_vault.0.wav`

*Where:* dialogue.json keegan/cb_opened_vault#0
*Played:* dry, comic severity; doing: you opened the door; pace: measured; volume: level.
*Note:* Deadpan escalation: 'in several sizes'.

```
[dry, comic severity] You opened the black door. The handbook has a chapter on that. It is a short chapter. It is the word "don't", in several sizes.
```
Subtitle: You opened the black door. The handbook has a chapter on that. It is a short chapter. It is the word "don't", in several sizes.

### 13. `dlg.keegan.cb_core_stolen.0.wav`

*Where:* dialogue.json keegan/cb_core_stolen#0
*Played:* dismay, comic resolve; doing: the heart was taken; pace: measured; volume: level.
*Note:* Grave, then a pause, then escalating comic determination: 'In capitals.'

```
[dismay, comic resolve] The Warden's heart, taken at the ford. ...I am going to write to the chapterhouse. Again. Twice, perhaps. In capitals.
```
Subtitle: The Warden's heart, taken at the ford. ...I am going to write to the chapterhouse. Again. Twice, perhaps. In capitals.

### 14. `dlg.keegan.say_calling.0.wav`

*Where:* dialogue.json keegan/say_calling#0
*Played:* eager, then prim; doing: a fellow shield; pace: quick; volume: level.
*Note:* Delight, deflation, then gossip about the handbook's rudeness.

```
[eager, then prim] A fellow shield! Which order? None? A free lance. The handbook has a chapter on free lances. It is very rude about them.
```
Subtitle: A fellow shield! Which order? None? A free lance. The handbook has a chapter on free lances. It is very rude about them.

### 15. `dlg.keegan.say_calling.1.wav`

*Where:* dialogue.json keegan/say_calling#1
*Played:* polite alarm; doing: mind the gate; pace: measured; volume: level.
*Note:* Very polite, very worried.

```
[polite alarm] That is a great deal of weapon. Please do not swing it near the gate. The gate is older than both of us and considerably less forgiving.
```
Subtitle: That is a great deal of weapon. Please do not swing it near the gate. The gate is older than both of us and considerably less forgiving.

### 16. `dlg.keegan.say_calling.2.wav`

*Where:* dialogue.json keegan/say_calling#2
*Played:* slip, then cover; doing: nearly says too much; pace: quick; volume: level.
*Note:* Breaks off 'a ledger of—'. Over-cheerful cover: 'Good morning.' The last question too bright.

```
[slip, then cover] Arcanist. The Vigil kept a ledger of— never mind. Good morning. It is a good morning, is it not.
```
Subtitle: Arcanist. The Vigil kept a ledger of— never mind. Good morning. It is a good morning, is it not.

### 17. `dlg.keegan.say_calling.3.wav`

*The same words are also* `dlg.keegan.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json keegan/say_calling#3
*Played:* pride, then honest; doing: pretends she noticed you; pace: measured; volume: level.
*Note:* Prim claim; a pause; honest and small: 'I did not know.'

```
[pride, then honest] You have been standing there for some time. I knew. I was merely being polite. ...I did not know.
```
Subtitle: You have been standing there for some time. I knew. I was merely being polite. ...I did not know.

### 18. `dlg.keegan.dinner.0.wav`

*Where:* dialogue.json keegan/dinner#0
*Played:* flustered, tempted; doing: fraternisation; pace: quick; volume: level.
*Note:* Prim citation; caught lying; confession; the answer wobbles: 'very nearly no.' Hasty 'Good day.'

```
[flustered, tempted] Chapter eleven. Fraternisation. I have not read it. ...That is a lie. I have read it four times. The answer is no. The answer is very nearly no. Good day.
```
Subtitle: Chapter eleven. Fraternisation. I have not read it. ...That is a lie. I have read it four times. The answer is no. The answer is very nearly no. Good day.

### 19. `dlg.keegan.t_keegan.0.wav`

*Where:* dialogue.json keegan/t_keegan#0
*Played:* earnest longing, then comic; doing: what she wants; pace: measured; volume: level.
*Note:* Sincere and moving: 'without the bracket.' A pause; comic: the bath, the protest underlining.

```
[earnest longing, then comic] To be confirmed. To kneel, and have a knight I respect touch my shoulder with a sword and say "Dame Keegan" without the bracket. ...And a bath. The Vigil frowns on baths. Chapter nine. I have underlined it in protest.
```
Subtitle: To be confirmed. To kneel, and have a knight I respect touch my shoulder with a sword and say "Dame Keegan" without the bracket. ...And a bath. The Vigil frowns on baths. Chapter nine. I have underlined it in protest.

### 20. `dlg.keegan.say_risen.0.p0.wav`

*Where:* dialogue.json keegan/say_risen#0; part 1 of 3: **keegan: I am told you were carried into the shrine under a sheet.** / narrator: She looks at you very carefully, from your boots upwards, and back down. / keegan: You look well. You look extremely well. ...I've got to go and read something. I— I have to…
*Played:* dawning fear, composure cracking; doing: sees the sign; pace: measured then quick; volume: level.
*Wants:* to be wrong
*Note:* Narrator for the long look. 'You look well. You look extremely well.' too careful. Then the contraction slips: 'I've got to go' quick and frightened, catching herself 'I— I have to go'. A brittle 'Good day.'

```
[dawning fear, composure cracking] I am told you were carried into the shrine under a sheet.
```
Subtitle: I am told you were carried into the shrine under a sheet.

### 21. `dlg.keegan.say_risen.0.p2.wav`

*Where:* dialogue.json keegan/say_risen#0; part 3 of 3: keegan: I am told you were carried into the shrine under a sheet. / narrator: She looks at you very carefully, from your boots upwards, and back down. / **keegan: You look well. You look extremely well. ...I've got to go and read something. I— I have to…**
*Played:* dawning fear, composure cracking; doing: sees the sign; pace: measured then quick; volume: level.
*Wants:* to be wrong
*Note:* Narrator for the long look. 'You look well. You look extremely well.' too careful. Then the contraction slips: 'I've got to go' quick and frightened, catching herself 'I— I have to go'. A brittle 'Good day.'

```
[dawning fear, composure cracking] You look well. You look extremely well. ...I've got to go and read something. I— I have to go and read something. Good day.
```
Subtitle: You look well. You look extremely well. ...I've got to go and read something. I— I have to go and read something. Good day.

### 22. `dlg.keegan.supper.0.p0.wav`

*Where:* dialogue.json keegan/supper#0; part 1 of 3: **keegan: I have not. I am on watch.** / narrator: She looks at the bread in her hand, which she has evidently been holding for some time. / keegan: Chapter eleven, paragraph six permits "a meal taken in company for the purposes of morale"…
*Played:* flustered propriety, pleased; doing: invites you to supper, by the book; pace: measured; volume: level.
*Note:* 'I am on watch.' prim. Narrator: the bread. The citation proud; 'It does not say whose morale.' a slip of mischief. The stone warning earnest.

```
[flustered propriety, pleased] I have not. I am on watch.
```
Subtitle: I have not. I am on watch.

### 23. `dlg.keegan.supper.0.p2.wav`

*Where:* dialogue.json keegan/supper#0; part 3 of 3: keegan: I have not. I am on watch. / narrator: She looks at the bread in her hand, which she has evidently been holding for some time. / **keegan: Chapter eleven, paragraph six permits "a meal taken in company for the purposes of morale"…**
*Played:* flustered propriety, pleased; doing: invites you to supper, by the book; pace: measured; volume: level.
*Note:* 'I am on watch.' prim. Narrator: the bread. The citation proud; 'It does not say whose morale.' a slip of mischief. The stone warning earnest.

```
[flustered propriety, pleased] Chapter eleven, paragraph six permits "a meal taken in company for the purposes of morale". I have read it very carefully. It does not say whose morale. ...Sit. Not there; that stone is the one the gate was built on, and it is older than manners. Here.
```
Subtitle: Chapter eleven, paragraph six permits "a meal taken in company for the purposes of morale". I have read it very carefully. It does not say whose morale. ...Sit. Not there; that stone is the one the gate was built on, and it is older than manners. Here.

### 24. `dlg.keegan.supper_wends.0.p0.wav`

*Where:* dialogue.json keegan/supper_wends#0; part 1 of 3: **keegan: Rhetoric, to the sons and daughters of people who could afford it. I was very good. I was …** / narrator: She smiles at the road. / keegan: I taught them chiasmus. "The Vigil keeps the gate, and the gate keeps the Vigil." It has k…
*Played:* proud, then rueful; doing: her old life; pace: measured; volume: level.
*Note:* Lecturer's pride; the chiasmus recited. 'It has kept neither.' quiet. Narrator: she smiles at the road. Flustered about the joke; 'It's late.' a contraction slipping.

```
[proud, then rueful] Rhetoric, to the sons and daughters of people who could afford it. I was very good. I was the youngest lecturer they had ever had, and they told me so every morning, in case I forgot and became the oldest.
```
Subtitle: Rhetoric, to the sons and daughters of people who could afford it. I was very good. I was the youngest lecturer they had ever had, and they told me so every morning, in case I forgot and became the oldest.

### 25. `dlg.keegan.supper_wends.0.p2.wav`

*Where:* dialogue.json keegan/supper_wends#0; part 3 of 3: keegan: Rhetoric, to the sons and daughters of people who could afford it. I was very good. I was … / narrator: She smiles at the road. / **keegan: I taught them chiasmus. "The Vigil keeps the gate, and the gate keeps the Vigil." It has k…**
*Played:* proud, then rueful; doing: her old life; pace: measured; volume: level.
*Note:* Lecturer's pride; the chiasmus recited. 'It has kept neither.' quiet. Narrator: she smiles at the road. Flustered about the joke; 'It's late.' a contraction slipping.

```
[proud, then rueful] I taught them chiasmus. "The Vigil keeps the gate, and the gate keeps the Vigil." It has kept neither. ...That was a joke. It was not a good one. It's late.
```
Subtitle: I taught them chiasmus. "The Vigil keeps the gate, and the gate keeps the Vigil." It has kept neither. ...That was a joke. It was not a good one. It's late.

### 26. `dlg.keegan.supper_age.0.p0.wav`

*Where:* dialogue.json keegan/supper_age#0; part 1 of 3: **keegan: Twenty-six. The handbook says that is old for a probationer. The handbook says a great man…** / narrator: She looks at you sidelong. / keegan: How old are you? No. Do not answer. I should only write it down.
*Played:* dry, warming; doing: her age; pace: measured; volume: level.
*Note:* Narrator: sidelong. A joke at herself; the last line a smile.

```
[dry, warming] Twenty-six. The handbook says that is old for a probationer. The handbook says a great many things. Some of them are true.
```
Subtitle: Twenty-six. The handbook says that is old for a probationer. The handbook says a great many things. Some of them are true.

### 27. `dlg.keegan.supper_age.0.p2.wav`

*Where:* dialogue.json keegan/supper_age#0; part 3 of 3: keegan: Twenty-six. The handbook says that is old for a probationer. The handbook says a great man… / narrator: She looks at you sidelong. / **keegan: How old are you? No. Do not answer. I should only write it down.**
*Played:* dry, warming; doing: her age; pace: measured; volume: level.
*Note:* Narrator: sidelong. A joke at herself; the last line a smile.

```
[dry, warming] How old are you? No. Do not answer. I should only write it down.
```
Subtitle: How old are you? No. Do not answer. I should only write it down.

### 28. `dlg.keegan.supper_letters.0.p1.wav`

*Where:* dialogue.json keegan/supper_letters#0; part 2 of 2: narrator: She doesn't answer for so long that you think she won't. / **keegan: That is a possibility I have considered. I have considered it every month for two years, o…**
*Played:* composed hurt; doing: the letters don't come; pace: slow; volume: quiet.
*Note:* Narrator holds the silence. Very precise, very hurt. 'That was an example of correctio.' brittle. Thanks sincere. 'I am also not a fool.' quiet and firm.

```
[composed hurt, quietly] That is a possibility I have considered. [very precisely] I have considered it every month for two years, on the day the post does not come. I have written it down and crossed it out. That was an example of correctio. ...Thank you for saying it. Nobody else will. They think I am funny. I am funny. I am also not a fool.
```
Subtitle: That is a possibility I have considered. I have considered it every month for two years, on the day the post does not come. I have written it down and crossed it out. That was an example of correctio. ...Thank you for saying it. Nobody else will. They think I am funny. I am funny. I am also not a fool.

### 29. `dlg.keegan.supper_read.0.p1.wav`

*Where:* dialogue.json keegan/supper_read#0; part 2 of 4: narrator: She is very obviously delighted, and very obviously trying not to be. / **keegan: Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body b…** / narrator: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gat… / keegan: ...You did not fall asleep. Nobody has ever not fallen asleep.
*Played:* delight trying to hide; doing: she reads to you; pace: measured; volume: level.
*Note:* Narrator: delighted. The handbook quoted with relish; 'In protest.' Narrator for the reading. The last line amazed and shy.

```
[delight trying to hide] Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body being a lamp and not a garden." I have underlined "garden". In protest.
```
Subtitle: Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body being a lamp and not a garden." I have underlined "garden". In protest.

### 30. `dlg.keegan.supper_read.0.p3.wav`

*Where:* dialogue.json keegan/supper_read#0; part 4 of 4: narrator: She is very obviously delighted, and very obviously trying not to be. / keegan: Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body b… / narrator: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gat… / **keegan: ...You did not fall asleep. Nobody has ever not fallen asleep.**
*Played:* delight trying to hide; doing: she reads to you; pace: measured; volume: level.
*Note:* Narrator: delighted. The handbook quoted with relish; 'In protest.' Narrator for the reading. The last line amazed and shy.

```
[delight trying to hide] ...You did not fall asleep. Nobody has ever not fallen asleep.
```
Subtitle: ...You did not fall asleep. Nobody has ever not fallen asleep.

### 31. `dlg.keegan.supper_ch4.0.p1.wav`

*Where:* dialogue.json keegan/supper_ch4#0; part 2 of 3: narrator: She closes the book. / **keegan: No.** / narrator: She says it gently, and then she doesn't say anything else for a while, and her hand stays…
*Played:* gentle refusal; doing: not chapter four; pace: slow; volume: quiet.
*Note:* Narrator: the book closed. 'No.' gently. Narrator holds the quiet.

```
[gentle refusal, quietly] No.
```
Subtitle: No.

### 32. `dlg.keegan.supper_hand.0.p1.wav`

*Where:* dialogue.json keegan/supper_hand#0; part 2 of 4: narrator: You put your hand over hers on the stone. She lets it stay there for a count of three. / **keegan: I am on duty.** / narrator: She takes her hand back. Then, without looking, she puts it back, under yours, for another… / keegan: ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.
*Played:* shy, moved; doing: her hand; pace: slow; volume: quiet.
*Note:* Narrator for the hands. 'I am on duty.' unsteady. The rhetoric lesson a shield. 'Goodnight.' soft.

```
[shy, moved, quietly] I am on duty.
```
Subtitle: I am on duty.

### 33. `dlg.keegan.supper_hand.0.p3.wav`

*Where:* dialogue.json keegan/supper_hand#0; part 4 of 4: narrator: You put your hand over hers on the stone. She lets it stay there for a count of three. / keegan: I am on duty. / narrator: She takes her hand back. Then, without looking, she puts it back, under yours, for another… / **keegan: ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.**
*Played:* shy, moved; doing: her hand; pace: slow; volume: quiet.
*Note:* Narrator for the hands. 'I am on duty.' unsteady. The rhetoric lesson a shield. 'Goodnight.' soft.

```
[shy, moved, quietly] ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.
```
Subtitle: ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.

### 34. `dlg.keegan.supper_end.0.p0.wav`

*Where:* dialogue.json keegan/supper_end#0; part 1 of 3: **keegan: Goodnight.** / narrator: As you go: / keegan: It was good for morale. Mine. I checked.
*Played:* pleased, shy; doing: goodnight; pace: measured; volume: quiet.
*Note:* 'Goodnight.' Narrator: as you go. 'Mine. I checked.' delighted.

```
[pleased, shy, quietly] Goodnight.
```
Subtitle: Goodnight.

### 35. `dlg.keegan.supper_end.0.p2.wav`

*Where:* dialogue.json keegan/supper_end#0; part 3 of 3: keegan: Goodnight. / narrator: As you go: / **keegan: It was good for morale. Mine. I checked.**
*Played:* pleased, shy; doing: goodnight; pace: measured; volume: quiet.
*Note:* 'Goodnight.' Narrator: as you go. 'Mine. I checked.' delighted.

```
[pleased, shy, quietly] It was good for morale. Mine. I checked.
```
Subtitle: It was good for morale. Mine. I checked.

### 36. `dlg.keegan.vonnra.0.wav`  HOLD: the story lead's confirmation of Keegan's kenning

*Where:* dialogue.json keegan/vonnra#0

```
Ash-of-Morrow. A peculiar sort of surname: a kenning, almost. The ash of the morning; what is left when the morning has burned down. ...I have no opinion of her. Chapter two forbids opinions about civilians. I have several.
```
Subtitle: Ash-of-Morrow. A peculiar sort of surname: a kenning, almost. The ash of the morning; what is left when the morning has burned down. ...I have no opinion of her. Chapter two forbids opinions about civilians. I have several.

## Said in passing

### 37. `bark.keegan.day.0.wav`

*Where:* npcs.json keegan.barks[0]
*Played:* earnest; pace: measured; volume: raised.

```
[earnest, loudly] None pass north. Not yet.
```
Subtitle: None pass north. Not yet.

### 38. `bark.keegan.day.1.wav`

*Where:* npcs.json keegan.barks[1]
*Played:* earnest; pace: measured; volume: raised.

```
[earnest, loudly] You are not ready for what is beyond there.
```
Subtitle: You are not ready for what is beyond there.

### 39. `bark.keegan.day.2.wav`

*Where:* npcs.json keegan.barks[2]
*Played:* earnest; pace: measured; volume: raised.

```
[earnest, loudly] Probationary. It is a real title.
```
Subtitle: Probationary. It is a real title.

### 40. `bark.keegan.night.0.wav`

*Where:* npcs.json keegan.nightBarks[0]
*Played:* earnest, tired; pace: measured; volume: level.

```
[earnest, tired] Night watch. Probationary night watch.
```
Subtitle: Night watch. Probationary night watch.

### 41. `bark.keegan.night.1.wav`

*Where:* npcs.json keegan.nightBarks[1]
*Played:* earnest, tired; pace: measured; volume: level.

```
[earnest, tired] Something moved out there. Probably.
```
Subtitle: Something moved out there. Probably.

### 42. `bark.keegan.night.2.wav`

*Where:* npcs.json keegan.nightBarks[2]
*Played:* earnest, tired; pace: measured; volume: level.

```
[earnest, tired] Stand back from the gate, please.
```
Subtitle: Stand back from the gate, please.

### 43. `bark.keegan.night.3.wav`

*Where:* npcs.json keegan.nightBarks[3]
*Played:* earnest, tired; pace: measured; volume: level.

```
[earnest, tired] I am not frightened of the dark. I am merely monitoring it very closely.
```
Subtitle: I am not frightened of the dark. I am merely monitoring it very closely.

### 44. `bark.keegan.said.0.wav`

*Where:* npcs.json keegan.said[0]
*Played:* absorbed, then polite; doing: reading her book; pace: measured; volume: level.
*Note:* Muttering 'Chapter four' twice, then a startled, proper 'Good day.'

```
[absorbed, then polite] Chapter four. Chapter four. ...Good day.
```
Subtitle: Chapter four. Chapter four. ...Good day.


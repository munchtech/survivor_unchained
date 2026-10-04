# Pell Varrow: ElevenLabs packet

Voice id in the game: `pell`. 31 takes to record (3,605 characters; about 10,815 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Pell Varrow** (factor). Soft, precise, smiling; complete sentences with contractions; the vocabulary of ledgers ("terms", "considerations", "accounts"). Never raises his voice, never swears, never makes a threat that could be repeated to the Watch. When he is frightened he gets more polite. *Casting:* 40, precise London RP, a little nasal.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Pell Varrow`. Never describe a voice as sounding like a real person.

```
Native English (British, London). Male, 40s. Studio quality. Persona: a precise London factor. A forty-year-old London merchant's factor with a soft, precise, smooth tenor and a clipped upper-middle-class London accent, a little nasal. Smiling, polite and quietly calculating; every word chosen as if it will be written down. Broad London accent. No reverb or effects.
```

Preview text:

```
Terms, friend, are what we agree they are, and I always keep to mine. Consider it a courtesy. I find courtesy is very much cheaper than the alternative.
```

In the Voice Library instead: search for *precise London RP*, *male*, *40*, and listen for this: A forty-year-old London merchant's factor with a soft, precise, smooth tenor and a clipped upper-middle-class London accent, a little nasal. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.pell.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice pell
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Pell

### 1. `dlg.pell.first.0.wav`

*Where:* dialogue.json pell/first#0
*Played:* smooth, smiling, insincere sympathy; doing: introduces himself; pace: measured; volume: level.
*Wants:* your custom and your trust
*Note:* Precise and pleased with himself. The sympathy for Coyle practised: 'Terrible. Terrible.' the second a touch too relished.

```
[smooth, smiling, insincere sympathy] Pell Varrow. Factor. If it can be bought, stored or sold in the Waystation, it's been through my books at least once. Terrible business, Coyle's wagons. Terrible.
```
Subtitle: Pell Varrow. Factor. If it can be bought, stored or sold in the Waystation, it's been through my books at least once. Terrible business, Coyle's wagons. Terrible.

### 2. `dlg.pell.hub.0.p1.wav`

*Where:* dialogue.json pell/hub#0; part 2 of 2: narrator: He smiles a little too quickly. / **pell: Ah. You. What can I do for you today, specifically?**
*Played:* nervous politeness; doing: afraid of you; pace: quick; volume: level.
*Note:* Narrator: the smile too quick. Over-polite, a little high; 'specifically' crisp.

```
[nervous politeness] Ah. You. What can I do for you today, specifically?
```
Subtitle: Ah. You. What can I do for you today, specifically?

### 3. `dlg.pell.hub.1.wav`

*Where:* dialogue.json pell/hub#1
*Played:* dry wit; doing: greets you; pace: measured; volume: level.
*Note:* A smile in the voice on 'simply being seen with me'.

```
[dry wit] Good day. Buying, selling, or simply being seen with me?
```
Subtitle: Good day. Buying, selling, or simply being seen with me?

### 4. `dlg.pell.caravan.0.wav`

*Where:* dialogue.json pell/caravan#0
*Played:* smooth, faux concern, sly; doing: angles to buy Coyle out; pace: measured; volume: level.
*Note:* 'one hears' distancing. Faux sorrow. 'As a friend.' silky. The last sentence a little too knowing.

```
[smooth, faux concern, sly] The wolves, one hears. Such a shame for Harlan. Such a shame for the Company. I've offered to buy him out, of course. As a friend. Someone ought to own those wagons who knows what not to put in them.
```
Subtitle: The wolves, one hears. Such a shame for Harlan. Such a shame for the Company. I've offered to buy him out, of course. As a friend. Someone ought to own those wagons who knows what not to put in them.

### 5. `dlg.pell.smell.0.wav`

*Where:* dialogue.json pell/smell#0
*Played:* soft menace, then persuasion; doing: bribes you to look away; pace: measured; volume: quiet.
*Wants:* your silence bought
*Note:* A cold pause, then very quiet: 'Careful.' Leans in: 'Walk with me.' Reasonable, friendly, terms laid out like a contract. 'Only not do certain other things.' delicate.

```
[soft menace, then persuasion, quietly] ...Careful. That's the kind of thing that gets said once. Walk with me. You understand how things are done, I think. Coyle's finished; the only question is who picks up the pieces. Sixty gold now, and more later, to let the Kerchiefs keep what they have. You needn't do a thing. Only not do certain other things.
```
Subtitle: ...Careful. That's the kind of thing that gets said once. Walk with me. You understand how things are done, I think. Coyle's finished; the only question is who picks up the pieces. Sixty gold now, and more later, to let the Kerchiefs keep what they have. You needn't do a thing. Only not do certain other things.

### 6. `dlg.pell.confront.0.p0.wav`

*Where:* dialogue.json pell/confront#0; part 1 of 3: **pell: Where did you— the clerk. Of course.** / narrator: He studies your face, and something in his own unclenches. / pell: ...You don't know what you're holding, do you? How refreshing. Let's be civilised. There's…
*Played:* alarm, then relief, then smooth; doing: caught, then bargains; pace: quick then measured; volume: quiet.
*Note:* Breaks off 'Where did you—'. Narrator: he studies your face and relaxes. Relief, amused: 'How refreshing.' Then smooth bargaining.

```
[alarm, then relief, then smooth, quietly] Where did you— the clerk. Of course.
```
Subtitle: Where did you— the clerk. Of course.

### 7. `dlg.pell.confront.0.p2.wav`

*Where:* dialogue.json pell/confront#0; part 3 of 3: pell: Where did you— the clerk. Of course. / narrator: He studies your face, and something in his own unclenches. / **pell: ...You don't know what you're holding, do you? How refreshing. Let's be civilised. There's…**
*Played:* alarm, then relief, then smooth; doing: caught, then bargains; pace: quick then measured; volume: quiet.
*Note:* Breaks off 'Where did you—'. Narrator: he studies your face and relaxes. Relief, amused: 'How refreshing.' Then smooth bargaining.

```
[alarm, then relief, then smooth, quietly] ...You don't know what you're holding, do you? How refreshing. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire.
```
Subtitle: ...You don't know what you're holding, do you? How refreshing. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire.

### 8. `dlg.pell.confront.1.wav`

*Where:* dialogue.json pell/confront#1
*Played:* alarm, then smooth; doing: caught, then bargains; pace: quick then measured; volume: quiet.
*Note:* Breaks off 'Where did you—'. Recovers instantly into civility.

```
[alarm, then smooth, quietly] Where did you— the clerk. Of course. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire.
```
Subtitle: Where did you— the clerk. Of course. Let's be civilised. There's gold in this for you, a good deal of gold, if that book were to go in the fire.

### 9. `dlg.pell.why.0.wav`

*Where:* dialogue.json pell/why#0
*Played:* candid, rueful; doing: justifies himself; pace: measured; volume: quiet.
*Wants:* you to understand, without saying too much
*Note:* The mask slips a little: honest. A pause. 'I'm not a good man. I'm a careful one.' quiet and sincere for once.

```
[candid, rueful, quietly] It wasn't the salt I was paying for. Ask Harlan what else was on those wagons, and who for. Then ask yourself whether you'd rather it reached them or sat in a ravine with a dozen drunks. ...I'm not a good man. I'm a careful one. In this valley that's rarer.
```
Subtitle: It wasn't the salt I was paying for. Ask Harlan what else was on those wagons, and who for. Then ask yourself whether you'd rather it reached them or sat in a ravine with a dozen drunks. ...I'm not a good man. I'm a careful one. In this valley that's rarer.

### 10. `dlg.pell.bribe.0.wav`

*Where:* dialogue.json pell/bribe#0
*Played:* crisp; doing: names his price; pace: measured; volume: quiet.
*Note:* Terms.

```
[crisp, quietly] Eighty gold. And the book.
```
Subtitle: Eighty gold. And the book.

### 11. `dlg.pell.dig.0.wav`

*Where:* dialogue.json pell/dig#0
*Played:* interested, then gleeful; doing: sees a profit; pace: measured; volume: level.
*Note:* 'Is it? Go on.' Then delighted calculation; ledger words, 'consideration' savoured. 'Especially me.' a little giggle he can't help.

```
[interested, then gleeful] Is it? Go on. ...The Dig. Grimtunnel's little lamp-people, pumping their slurry into the stream. Oh, that is worth something. Not to Holloway: to the diggers. A pipe can be moved, for a consideration, and a consideration can be split. Forty gold, and the wolves stop dying. Everyone's happy. Especially me.
```
Subtitle: Is it? Go on. ...The Dig. Grimtunnel's little lamp-people, pumping their slurry into the stream. Oh, that is worth something. Not to Holloway: to the diggers. A pipe can be moved, for a consideration, and a consideration can be split. Forty gold, and the wolves stop dying. Everyone's happy. Especially me.

### 12. `dlg.pell.dig_done.0.wav`

*Where:* dialogue.json pell/dig_done#0
*Played:* smug; doing: deal done; pace: measured; volume: quiet.
*Note:* Conspiratorial on the weather.

```
[smug, quietly] A pleasure. Give it two days. And if anyone asks, you and I discussed the weather.
```
Subtitle: A pleasure. Give it two days. And if anyone asks, you and I discussed the weather.

### 13. `dlg.pell.books.0.wav`

*Where:* dialogue.json pell/books#0
*Played:* dismissive, then intense; doing: the ember going into the hill; pace: measured then slow; volume: quiet.
*Note:* Light list first. A pause. Then quieter and serious: the numbers frighten him. 'Nobody digs that deep for coal.' dead quiet.

```
[dismissive, then intense, quietly] Who doesn't? Lamp-oil, chapel candles, a little blasting for the quarrymen. All very ordinary. ...And then there's the hill. Do you know how much ember has gone into that hill this year? I do. I have the receipts. Nobody digs that deep for coal.
```
Subtitle: Who doesn't? Lamp-oil, chapel candles, a little blasting for the quarrymen. All very ordinary. ...And then there's the hill. Do you know how much ember has gone into that hill this year? I do. I have the receipts. Nobody digs that deep for coal.

### 14. `dlg.pell.books2.0.wav`

*Where:* dialogue.json pell/books2#0
*Played:* dry, uneasy; doing: doesn't know, and fears it; pace: measured; volume: quiet.
*Note:* Dry deflection, then 'it's expensive' with real unease.

```
[dry, uneasy, quietly] I'm a factor, not a priest. I only know what things cost. Whatever's down there, it's expensive.
```
Subtitle: I'm a factor, not a priest. I only know what things cost. Whatever's down there, it's expensive.

### 15. `dlg.pell.ally.0.wav`

*Where:* dialogue.json pell/ally#0
*Played:* smooth, discreet; doing: our deal stands; pace: measured; volume: quiet.

```
[smooth, discreet, quietly] Our arrangement stands. Discreetly, please.
```
Subtitle: Our arrangement stands. Discreetly, please.

### 16. `dlg.pell.cb_tricked_redcowl.0.wav`

*Where:* dialogue.json pell/cb_tricked_redcowl#0
*Played:* dry admiration, wary; doing: you moved the Kerchiefs; pace: measured; volume: level.
*Note:* Delicate pause before 'efficient'.

```
[dry admiration, wary] I hear the Kerchiefs left their camp in rather a hurry. On your word. How very... efficient.
```
Subtitle: I hear the Kerchiefs left their camp in rather a hurry. On your word. How very... efficient.

### 17. `dlg.pell.say_calling.0.wav`

*Where:* dialogue.json pell/say_calling#0
*Played:* appraising; doing: values your armour; pace: measured; volume: level.
*Note:* A merchant's appraisal.

```
[appraising] Armour like that costs more than most of this street. Whoever paid for it, I'd very much like to meet them.
```
Subtitle: Armour like that costs more than most of this street. Whoever paid for it, I'd very much like to meet them.

### 18. `dlg.pell.say_calling.1.wav`

*Where:* dialogue.json pell/say_calling#1
*Played:* dry, wry; doing: a joke about violence; pace: measured; volume: level.
*Note:* A thin smile.

```
[dry, wry] I do prefer to deal with people who could break my arm. It keeps the terms so simple.
```
Subtitle: I do prefer to deal with people who could break my arm. It keeps the terms so simple.

### 19. `dlg.pell.say_calling.2.wav`

*Where:* dialogue.json pell/say_calling#2
*Played:* dry amusement; doing: arcanists read labels; pace: measured; volume: level.
*Note:* Mock complaint.

```
[dry amusement] A scholar of the burning arts. Do you know, I've never once sold an arcanist anything at a profit? You people read the labels.
```
Subtitle: A scholar of the burning arts. Do you know, I've never once sold an arcanist anything at a profit? You people read the labels.

### 20. `dlg.pell.say_calling.3.wav`

*The same words are also* `dlg.pell.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json pell/say_calling#3
*Played:* cold unease; doing: you crept up; pace: measured; volume: quiet.
*Note:* The politeness thins. 'I'll remember it.' quietly.

```
[cold unease, quietly] You've been standing there longer than I noticed. I don't care for that. I'll remember it.
```
Subtitle: You've been standing there longer than I noticed. I don't care for that. I'll remember it.

### 21. `dlg.pell.say_woman.0.wav`

*Where:* dialogue.json pell/say_woman#0
*Played:* smooth flattery, condescending; doing: a merchant's theory; pace: measured; volume: level.
*Note:* Charming and slightly insufferable; pleased with his wit.

```
[smooth flattery, condescending] I find women drive the harder bargain. I've a theory it's because you're used to being underpaid. Do prove me right; it's so rare that I am wrong.
```
Subtitle: I find women drive the harder bargain. I've a theory it's because you're used to being underpaid. Do prove me right; it's so rare that I am wrong.

### 22. `dlg.pell.cb_bribed_snib.0.wav`

*Where:* dialogue.json pell/cb_bribed_snib#0
*Played:* dry, competitive; doing: you went around him; pace: measured; volume: level.
*Note:* 'Pumps do.' dry. Professional pique at the end.

```
[dry, competitive] I hear the Dig's pump broke. Pumps do. And I hear a very small foreman is forty gold richer. You might have come to me; I'd have done it for thirty-five, and kept it quieter.
```
Subtitle: I hear the Dig's pump broke. Pumps do. And I hear a very small foreman is forty gold richer. You might have come to me; I'd have done it for thirty-five, and kept it quieter.

### 23. `dlg.pell.t_pell.0.p0.wav`

*Where:* dialogue.json pell/t_pell#0; part 1 of 3: **pell: My sister kept the books in Ashford. I came up to collect them, after. There wasn't an Ash…** / narrator: He straightens a pen that was straight. / pell: She wrote to me the week before. The garrison's boots had come in short, and somebody had …
*Played:* grief behind precision; doing: why he counts; pace: slow; volume: quiet.
*Wants:* to be understood, once
*Note:* Plain, no smile. 'There wasn't an Ashford to collect them from.' level. Narrator: the pen. The boots told flatly; 'She thought it was funny.' fond. 'She had a dreadful sense of humour.' nearly breaks. Pause. The last line a creed.

```
[grief behind precision, quietly] My sister kept the books in Ashford. I came up to collect them, after. There wasn't an Ashford to collect them from.
```
Subtitle: My sister kept the books in Ashford. I came up to collect them, after. There wasn't an Ashford to collect them from.

### 24. `dlg.pell.t_pell.0.p2.wav`

*Where:* dialogue.json pell/t_pell#0; part 3 of 3: pell: My sister kept the books in Ashford. I came up to collect them, after. There wasn't an Ash… / narrator: He straightens a pen that was straight. / **pell: She wrote to me the week before. The garrison's boots had come in short, and somebody had …**
*Played:* grief behind precision; doing: why he counts; pace: slow; volume: quiet.
*Wants:* to be understood, once
*Note:* Plain, no smile. 'There wasn't an Ashford to collect them from.' level. Narrator: the pen. The boots told flatly; 'She thought it was funny.' fond. 'She had a dreadful sense of humour.' nearly breaks. Pause. The last line a creed.

```
[grief behind precision, quietly] She wrote to me the week before. The garrison's boots had come in short, and somebody had signed for them full. She thought it was funny. She had a dreadful sense of humour. ...So I count. Somebody ought to know what things cost.
```
Subtitle: She wrote to me the week before. The garrison's boots had come in short, and somebody had signed for them full. She thought it was funny. She had a dreadful sense of humour. ...So I count. Somebody ought to know what things cost.

## Said in passing

### 25. `bark.pell.day.0.wav`

*Where:* npcs.json pell.barks[0]
*Played:* smooth; pace: measured; volume: level.

```
[smooth] Everything has a price. Most things have two.
```
Subtitle: Everything has a price. Most things have two.

### 26. `bark.pell.day.1.wav`

*Where:* npcs.json pell.barks[1]
*Played:* smooth; pace: measured; volume: level.

```
[smooth] Terrible business, Coyle's caravan. Terrible.
```
Subtitle: Terrible business, Coyle's caravan. Terrible.

### 27. `bark.pell.day.2.wav`

*Where:* npcs.json pell.barks[2]
*Played:* smooth; pace: measured; volume: level.

```
[smooth] My warehouse is closed to the public.
```
Subtitle: My warehouse is closed to the public.

### 28. `bark.pell.night.0.wav`

*Where:* npcs.json pell.nightBarks[0]
*Played:* smooth; pace: measured; volume: quiet.

```
[smooth, quietly] Closed. Closed! Come back in daylight.
```
Subtitle: Closed. Closed! Come back in daylight.

### 29. `bark.pell.night.1.wav`

*Where:* npcs.json pell.nightBarks[1]
*Played:* smooth; pace: measured; volume: quiet.

```
[smooth, quietly] A man can't count in peace in this town.
```
Subtitle: A man can't count in peace in this town.

### 30. `bark.pell.night.2.wav`

*Where:* npcs.json pell.nightBarks[2]
*Played:* smooth; pace: measured; volume: quiet.

```
[smooth, quietly] Who's there?
```
Subtitle: Who's there?

### 31. `bark.pell.night.3.wav`

*Where:* npcs.json pell.nightBarks[3]
*Played:* smooth; pace: measured; volume: quiet.

```
[smooth, quietly] The numbers don't sleep. Why should I?
```
Subtitle: The numbers don't sleep. Why should I?


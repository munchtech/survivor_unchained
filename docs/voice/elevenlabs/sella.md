# Sella: ElevenLabs packet

Voice id in the game: `sella`. 95 takes to record (13,007 characters; about 39,021 credits at three tries a line). Status: **final** (the story lead, 2026-10-03): record it.

**52 takes are LOCKED FOR RECORDING** (marked below).

## Who they are

**Sella** (the blue room). Low, amused, intimate; heavy contractions; "love". Frank about sex and money and about which is which; never coy, never pitiful, never sorry for her work. Sells talk as well as company and says so. *Casting:* late 20s, softened Cockney; warmth that is also work. Adult, never breathy.

*Wants:* a house in the south with a door that locks from the inside, and somebody who knocks; until then, your custom, and to keep it work. *Hides:* she sells what's said upstairs, and Vonnra outbids everyone: every intimate scene has a buyer listening, until she stops (sella.free). Adult, frank, never breathy, never coy.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Sella`. Never describe a voice as sounding like a real person.

```
Native English (British, London). Female, 20s. Studio quality. Persona: a London courtesan. A woman in her late twenties from London with a soft, warm Cockney accent. A low, amused, intimate alto, relaxed and knowing, frank and unembarrassed, with warmth that is also a professional's. Never breathy. Light London accent. No reverb or effects.
```

Preview text:

```
Evening, love. The lamp's lit upstairs, if you're asking. Conversation's extra, mind; most people don't know they want it till they've had it.
```

In the Voice Library instead: search for *softened Cockney (London)*, *female*, *20*, and listen for this: A woman in her late twenties from London with a soft, warm Cockney accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.sella.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice sella
```

## Saying the names

The text to paste already respells these; keep the respelling: Maeca as *Mayka*, Redcowl as *Red-cowl*, Vonnra as *Vonra*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Sella

### 1. `dlg.sella.first.0.wav`

*Where:* dialogue.json sella/first#0
*Played:* amused, frank; doing: introduces herself to the town's new hero; pace: measured; volume: level.
*Wants:* your custom
*Note:* Low, amused, relaxed; the swear casual. Wry on the two halves of the tavern. 'Talk's free. The rest isn't.' her line, a smile in it.

```
[amused, frank] So you're the one who put the big dead bastard at the ford back in the ground. Half the tavern's been drinking to you and the other half's been drinking to them. I'm Sella. I keep the blue room at the top of Rook's stairs. Talk's free. The rest isn't.
```
Subtitle: So you're the one who put the big dead bastard at the ford back in the ground. Half the tavern's been drinking to you and the other half's been drinking to them. I'm Sella. I keep the blue room at the top of Rook's stairs. Talk's free. The rest isn't.

### 2. `dlg.sella.first.1.wav`

*Where:* dialogue.json sella/first#1
*Played:* amused, warm; doing: introduces herself; pace: measured; volume: level.
*Wants:* your custom
*Note:* Teasing on the ditches; 'love' warm. Her line at the end.

```
[amused, warm] You've the look of someone who's been sleeping in ditches, love. Sella. I keep the blue room at the top of Rook's stairs. Talk's free. The rest isn't.
```
Subtitle: You've the look of someone who's been sleeping in ditches, love. Sella. I keep the blue room at the top of Rook's stairs. Talk's free. The rest isn't.

### 3. `dlg.sella.hub.0.wav`

*Where:* dialogue.json sella/hub#0
*Played:* teasing, intimate; doing: the evening invitation; pace: measured; volume: quiet.
*Note:* Lower at night. Each 'asking' a step further into the tease.

```
[teasing, intimate, quietly] Evening. The lamp's lit upstairs, if you're asking. You look like you're asking. You look like you've been asking all day.
```
Subtitle: Evening. The lamp's lit upstairs, if you're asking. You look like you're asking. You look like you've been asking all day.

### 4. `dlg.sella.hub.1.wav`

*Where:* dialogue.json sella/hub#1
*Played:* amused; doing: welcomes you back; pace: measured; volume: level.
*Note:* Unbothered by gossip; business.

```
[amused] Back again. People'll talk. Let them; it's good for business.
```
Subtitle: Back again. People'll talk. Let them; it's good for business.

### 5. `dlg.sella.again.0.wav`

*Where:* dialogue.json sella/again#0
*Played:* teasing, fond; doing: glad to see you; pace: measured; volume: quiet.
*Note:* Mock jealousy; 'You'd have been robbed.' professional pride.

```
[teasing, fond, quietly] There you are. I was starting to think you'd found someone cheaper. You'd have been robbed.
```
Subtitle: There you are. I was starting to think you'd found someone cheaper. You'd have been robbed.

### 6. `dlg.sella.again.1.wav`

*Where:* dialogue.json sella/again#1
*Played:* teasing; doing: a joke at your expense; pace: measured; volume: level.
*Note:* A beat where the name would be. Dry, pleased.

```
[teasing] Still walking straight, I see. I'll take that as a compliment.
```
Subtitle: Still walking straight, I see. I'll take that as a compliment.

### 7. `dlg.sella.hear.0.wav`

*Where:* dialogue.json sella/hear#0
*Played:* gossipy, wry, then shrewd; doing: sells you Jessop's secret; pace: measured; volume: quiet.
*Note:* Worldly amusement at men. Jessop quoted with scorn. 'Charming.' dry. Then shrewd: he hasn't been back; 'You could set a clock by Jessop.' pointed.

```
[gossipy, wry, then shrewd, quietly] Men talk after. God, do they talk. There's a toll clerk, Jessop, been flush all month, paying me in new silver with the Varrow mark stamped on it. Last time he was pleased with himself: said he'd "sent some wagons down the wrong road" and got paid twice for it. Then he fell asleep on my arm. Charming. ...Not been up my stairs since, and he was a Tuesday man. You could set a clock by Jessop.
```
Subtitle: Men talk after. God, do they talk. There's a toll clerk, Jessop, been flush all month, paying me in new silver with the Varrow mark stamped on it. Last time he was pleased with himself: said he'd "sent some wagons down the wrong road" and got paid twice for it. Then he fell asleep on my arm. Charming. ...Not been up my stairs since, and he was a Tuesday man. You could set a clock by Jessop.

### 8. `dlg.sella.hear.1.wav`

*Where:* dialogue.json sella/hear#1
*Played:* dry, gossipy; doing: the town's news; pace: measured; volume: level.
*Note:* A list, each item drier. 'Same as ever.' bored.

```
[dry, gossipy] That the wolves are quiet, and Holloway's drinking more than he's paying. That Pell sleeps with his ledgers. That Harlan cries when he's had three. Same as ever.
```
Subtitle: That the wolves are quiet, and Holloway's drinking more than he's paying. That Pell sleeps with his ledgers. That Harlan cries when he's had three. Same as ever.

### 9. `dlg.sella.hear.2.wav`

*Where:* dialogue.json sella/hear#2
*Played:* dry, then a shadow; doing: the town's news; pace: measured; volume: level.
*Note:* Light swearing on Holloway. A little darker about the north road. 'Same as ever.'

```
[dry, then a shadow] That the wolves are sick and Holloway's a prick, and that nobody who goes up the north road comes back to tell me about it. Same as ever.
```
Subtitle: That the wolves are sick and Holloway's a prick, and that nobody who goes up the north road comes back to tell me about it. Same as ever.

### 10. `dlg.sella.rook.0.wav`

*Where:* dialogue.json sella/rook#0
*Played:* wry affection; doing: about Rook; pace: measured; volume: level.
*Note:* A list of Rook's virtues, fond. 'I've had worse mothers.' a joke with a bruise in it.

```
[wry affection] Rook minds everything. She also takes a third, keeps the drunks off the stairs, and once put a Kerchief through the front door for not paying. I've had worse landladies. I've had worse mothers.
```
Subtitle: Rook minds everything. She also takes a third, keeps the drunks off the stairs, and once put a Kerchief through the front door for not paying. I've had worse landladies. I've had worse mothers.

### 11. `dlg.sella.buyers.0.wav`

*Where:* dialogue.json sella/buyers#0
*Played:* frank, knowing; doing: who buys what she hears; pace: measured; volume: quiet.
*Note:* 'Clever.' approving. Brisk list of buyers. Vonnra said with respect and unease. A pause; then a promise with a hook: 'Nobody has. Yet.'

```
[frank, knowing, quietly] Clever. Everybody, love. Pell pays for what his rivals say. Holloway pays for what his men say. Vonra pays for all of it, more than anyone, and she's never once come up the stairs. Rook takes a third of everything. ...What you say up there's yours. Unless somebody outbids you. Nobody has. Yet.
```
Subtitle: Clever. Everybody, love. Pell pays for what his rivals say. Holloway pays for what his men say. Vonnra pays for all of it, more than anyone, and she's never once come up the stairs. Rook takes a third of everything. ...What you say up there's yours. Unless somebody outbids you. Nobody has. Yet.

### 12. `dlg.sella.price.0.wav`

*Where:* dialogue.json sella/price#0
*Played:* frank, warm, businesslike; doing: her terms; pace: measured; volume: quiet.
*Note:* Terms without coyness. Humour on the bath. The last two sentences sincere, a professional's care.

```
[frank, warm, businesslike, quietly] Fifteen gold, up front. For that you get the blue room, a bath that's warm at least to start with, and me, until morning. Anything you'd rather I didn't do, say so. Anything you'd rather I did, say that too.
```
Subtitle: Fifteen gold, up front. For that you get the blue room, a bath that's warm at least to start with, and me, until morning. Anything you'd rather I didn't do, say so. Anything you'd rather I did, say that too.

### 13. `dlg.sella.night.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/night#0
*Played:* low, slow; holding something down; doing: the night she stops working and can't let you see it; pace: slow; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. No laugh anywhere in this one. 'I'm not walking three steps for a bed; bring the quilt.' tired, fond. 'Easy. Easy, love.' the way you gentle a skittish horse; it's you she's gentling, and herself. 'Don't. ...Don't look at me.' close and soft, not a plea: she stops your look the way she'd stop a hand (the old 'Don't' take folds in here). 'I'm not getting dressed. Don't ask me why.' the last thing before sleep, plain, a door closing. The coins, counted twice in the morning, are the game's.

```
[low, slow, quietly] Water's gone cold. ...Leave it. I'm not walking three steps for a bed; bring the quilt. ...Easy. Easy, love. [long pause] ...Don't. ...Don't look at me. [long pause] ...I'm not getting dressed. Don't ask me why.
```
Subtitle: Water's gone cold. ...Leave it. I'm not walking three steps for a bed; bring the quilt. ...Easy. Easy, love. ...Don't. ...Don't look at me. ...I'm not getting dressed. Don't ask me why.

### 14. `dlg.sella.night.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/night#1
*Played:* easy; laughing, then losing the thread; doing: a regular's night that stops being work in the gaps; pace: slow; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. Starts on a real laugh: the bath has gone over the side (if the laugh comes out made, start on 'That's the floor, then.'). 'you great—' cut off by her own laugh. 'I'll tell you what I'm going to do, love, and then I'm going to do it.' her trade, low and wicked. Then 'First I'm going to— ...First.' she loses it, and the gaps are the scene: don't fill them, don't play them sad. Not coy and not shy: the patter simply isn't there tonight. 'You know. Come here.' softer than anything before it.

```
[easy, quietly] [laughs softly] That's the floor, then. ...Not with my shift, you great— give it here. ...Right. I'll tell you what I'm going to do, love, and then I'm going to do it. First I'm going to— ...First. [long pause] ...You know. Come here.
```
Subtitle: That's the floor, then. ...Not with my shift, you great— give it here. ...Right. I'll tell you what I'm going to do, love, and then I'm going to do it. First I'm going to— ...First. ...You know. Come here.

### 15. `dlg.sella.night.2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/night#2
*Played:* low, amused, unhurried; doing: the first night: makes it easy, and sells the quiet; pace: slow; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. She's good at this, likes it, and makes no secret of either. 'Was warm.' a smile you can hear. 'Come here. There.' the voice of someone arranging you. 'any hand of mine that's not welcome, you say' plain, a professional's courtesy, not a tease. 'Nobody's paying me to hurry.' sly: you're paying for the time. 'Listen.' and she listens. 'That's what the fifteen's for.' fond and businesslike at once: the money is part of the tenderness, not a cut against it. The coins in the morning are the game's.

```
[low, amused, unhurried, quietly] Bath's warm. Was warm. ...Leave it, love. Come here. There. Now, any hand of mine that's not welcome, you say, and I'll find it somewhere it is. ...That's it. Slow. Nobody's paying me to hurry. ...Listen. Can't hear the road from up here. Can't hear the river. That's what the fifteen's for.
```
Subtitle: Bath's warm. Was warm. ...Leave it, love. Come here. There. Now, any hand of mine that's not welcome, you say, and I'll find it somewhere it is. ...That's it. Slow. Nobody's paying me to hurry. ...Listen. Can't hear the road from up here. Can't hear the river. That's what the fifteen's for.

### 16. `dlg.sella.morning.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/morning#0
*Played:* fond, uneasy under it; doing: she noticed the body's hours; pace: measured; volume: quiet.
*Hides:* she knows who pays for a thing like this, and unless she has stopped selling you, Vonnra will have it by noon
*Note:* Morning in the room: close and quiet, not hushed. Sitting on the edge of the bed, her palm on your breastbone. The first time anyone says it (the bible's 'body's hours'). 'cold as the river all night' puzzled, half a joke she doesn't quite make; 'warm as toast' a shade too bright. '...Rook's got a word for that. It's not a nice word.' quieter, not looking at you, because she's already counting it: as near as she comes to warning you. 'Get up and eat something.' brisk care, and real.

```
[fond, uneasy under it, quietly] You were cold as the river all night, love. Like sleeping next to a stone. And now look at you: warm as toast. ...Rook's got a word for that. It's not a nice word. Get up and eat something.
```
Subtitle: You were cold as the river all night, love. Like sleeping next to a stone. And now look at you: warm as toast. ...Rook's got a word for that. It's not a nice word. Get up and eat something.

### 17. `dlg.sella.morning.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/morning#1
*Played:* fond, teasing; doing: you're a habit; pace: measured; volume: level.
*Note:* Rook's complaint relayed with relish; a brisk send-off with a dark joke.

```
[fond, teasing] You're getting to be a habit. I don't mind. Rook does; she says you're wearing out the stairs. Go on, the day's wasting, and somebody out there owes you money, or the other way round.
```
Subtitle: You're getting to be a habit. I don't mind. Rook does; she says you're wearing out the stairs. Go on, the day's wasting, and somebody out there owes you money, or the other way round.

### 18. `dlg.sella.morning.2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/morning#2
*Played:* teasing, fond; doing: you talk in your sleep; pace: measured; volume: quiet.
*Note:* 'You lose. Every time.' a grin.

```
[teasing, fond, quietly] Two nights. ...You make a noise in your sleep, you know. Like you're arguing with somebody. You lose. Every time.
```
Subtitle: Two nights. ...You make a noise in your sleep, you know. Like you're arguing with somebody. You lose. Every time.

### 19. `dlg.sella.morning.3.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/morning#3
*Played:* affectionate mischief; doing: to send them off without admitting she cares; pace: measured; volume: quiet.
*Wants:* to send them off without admitting she cares
*Note:* Morning-after banter, frank and funny. 'The pieces are what I like' is bawdy and also a real wish for them to come back alive.

```
[affectionate mischief, quietly] You snore, by the way. Not badly. Go on, then. Come back in one piece; the pieces are what I like.
```
Subtitle: You snore, by the way. Not badly. Go on, then. Come back in one piece; the pieces are what I like.

### 20. `dlg.sella.cb_tricked_redcowl.0.wav`

*Where:* dialogue.json sella/cb_tricked_redcowl#0
*Played:* admiring, flirtatious; doing: praises your lie; pace: measured; volume: level.
*Note:* 'You'd do well upstairs' a compliment between professionals.

```
[admiring, flirtatious] Heard you sent Red-cowl running with nothing but a lie and a straight face. You'd do well upstairs, love.
```
Subtitle: Heard you sent Redcowl running with nothing but a lie and a straight face. You'd do well upstairs, love.

### 21. `dlg.sella.cb_exposed_pell.0.wav`

*Where:* dialogue.json sella/cb_exposed_pell#0
*Played:* dry, unsentimental; doing: Pell's gone; pace: measured; volume: level.
*Note:* Deadpan.

```
[dry, unsentimental] Pell's in the cells. One less customer. I'll miss his money and not one other thing about him.
```
Subtitle: Pell's in the cells. One less customer. I'll miss his money and not one other thing about him.

### 22. `dlg.sella.cb_burned_roost.0.wav`

*Where:* dialogue.json sella/cb_burned_roost#0
*Played:* guarded, cool; doing: she's heard; pace: slow; volume: quiet.
*Note:* A pause. 'I don't judge' a professional reflex. 'But I heard.' cool and pointed.

```
[guarded, cool, quietly] They're saying you burned the Roost with folk still in it. ...I don't judge, love; it's bad for business. But I heard.
```
Subtitle: They're saying you burned the Roost with folk still in it. ...I don't judge, love; it's bad for business. But I heard.

### 23. `dlg.sella.cb_freed_teamsters.0.wav`

*Where:* dialogue.json sella/cb_freed_teamsters#0
*Played:* amused tenderness; doing: Jory's crush; pace: measured; volume: level.
*Note:* Laughing at Jory, kindly. 'Sweet.' 'he thinks you're a story.' gentle.

```
[amused tenderness] Jory Coyle came up the stairs to say thank you to somebody, and it wasn't me, and he went red as a radish. Sweet. Go easy on him; he thinks you're a story.
```
Subtitle: Jory Coyle came up the stairs to say thank you to somebody, and it wasn't me, and he went red as a radish. Sweet. Go easy on him; he thinks you're a story.

### 24. `dlg.sella.say_calling.0.wav`

*Where:* dialogue.json sella/say_calling#0
*Played:* teasing; doing: all that steel; pace: measured; volume: level.
*Note:* Dry, bawdy.

```
[teasing] All that steel. Takes an age to get off, I expect. I charge by the hour, love, not by the buckle.
```
Subtitle: All that steel. Takes an age to get off, I expect. I charge by the hour, love, not by the buckle.

### 25. `dlg.sella.say_calling.1.wav`

*Where:* dialogue.json sella/say_calling#1
*Played:* teasing; doing: big hands; pace: measured; volume: level.
*Note:* Dry, bawdy.

```
[teasing] Big hands. Be gentle with them upstairs, or you'll be paying for the furniture.
```
Subtitle: Big hands. Be gentle with them upstairs, or you'll be paying for the furniture.

### 26. `dlg.sella.say_calling.2.wav`  **RE-RECORD: the words changed**

*Where:* dialogue.json sella/say_calling#2
*Played:* startled, amused; doing: you're hot to the touch; pace: measured; volume: level.
*Note:* Puzzled, then laughing: 'You're a little bit on fire.'

```
[startled, amused] Something on you's smoldering, love. Are you on fire? You're a little bit on fire.
```
Subtitle: Something on you's smoldering, love. Are you on fire? You're a little bit on fire.

### 27. `dlg.sella.say_calling.3.wav`

*The same words are also* `dlg.sella.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/say_calling#3
*Played:* startled, then wry; doing: you crept up; pace: measured; volume: level.
*Note:* A real start, covered with a joke.

```
[startled, then wry] Nobody's looked at you once since you came in. Not once. I'd pay good money for that, love. Some nights I'd pay all of it.
```
Subtitle: Nobody's looked at you once since you came in. Not once. I'd pay good money for that, love. Some nights I'd pay all of it.

### 28. `dlg.sella.say_woman.0.wav`

*Where:* dialogue.json sella/say_woman#0
*Played:* warm, frank; doing: reassures a woman; pace: measured; volume: quiet.
*Note:* Easy and kind; the last sentence a little sad.

```
[warm, frank, quietly] Don't look so surprised, love. You're not the first woman up those stairs and you won't be the last. Half my regulars are lonelier than you.
```
Subtitle: Don't look so surprised, love. You're not the first woman up those stairs and you won't be the last. Half my regulars are lonelier than you.

### 29. `dlg.sella.say_maeca.0.wav`  **RE-RECORD: the words changed**

*Where:* dialogue.json sella/say_maeca#0
*Played:* delighted gossip; doing: Maeca's humming; pace: measured; volume: level.
*Note:* 'Maeca. Humming.' incredulous. Teasing professional jealousy.

```
[delighted gossip] Mayka came in this morning humming. Mayka. Humming. I've a professional interest, love: who's my competition?
```
Subtitle: Maeca came in this morning humming. Maeca. Humming. I've a professional interest, love: who's my competition?

### 30. `dlg.sella.t_sella.0.wav`

*Where:* dialogue.json sella/t_sella#0
*Played:* wistful, unguarded; doing: what she wants; pace: slow; volume: quiet.
*Note:* The patter drops. 'a door that locks from the inside' quiet. 'Just somebody who knocks.' the most honest thing she says.

```
[wistful, unguarded, quietly] A house in the south with a door that locks from the inside, and somebody who knocks. Man, woman, I'm not fussy. Just somebody who knocks.
```
Subtitle: A house in the south with a door that locks from the inside, and somebody who knocks. Man, woman, I'm not fussy. Just somebody who knocks.

### 31. `dlg.sella.free.0.wav`

*Where:* dialogue.json sella/free#0
*Played:* plain, then strained; doing: offers herself freely, which she has never done; pace: slow; volume: quiet.
*Wants:* you to stay without it turning into business or a fuss
*Hides:* her fear that it means something
*Note:* Not shy: she has never done this. 'Put your purse away.' brisk, a professional's habit; a beat; 'Tonight I'm not working.' plainly, as if it cost nothing. 'Don't look at me like that.' a small laugh at herself; 'Don't make it strange.' is where the strain shows.

```
[plain, then strained, quietly] Put your purse away… Tonight I'm not working. ...Don't look at me like that. [laughs] Don't make it strange.
```
Subtitle: Put your purse away. Tonight I'm not working. ...Don't look at me like that. Don't make it strange.

### 32. `dlg.sella.free_night.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_night#0
*Played:* unsure, low; laughing at herself, then very quiet; doing: her free night, with no act to do it in; pace: slow; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. Not her working voice at all: lower, less sure, the polish gone. 'Seven years, love, and I can't undo a lace.' half a laugh. 'Don't you laugh. Don't you dare—' and she's the one who goes: a real laugh she can't stop, muffled into your neck (if it isn't real, cut it and go straight to 'Wait.'). 'Wait. ...All right. All right.' barely voiced, the laugh gone somewhere else. Then a long time. 'You told me anyway.' into your shoulder, nearly asleep, wondering, and nothing else (the old take of it folds in here).

```
[unsure, low, quietly] My hands don't know what they're doing. ...Seven years, love, and I can't undo a lace. Don't you laugh. Don't you dare— [laughs helplessly, muffled] ...Wait. ...All right. All right. [long pause] ...You told me anyway.
```
Subtitle: My hands don't know what they're doing. ...Seven years, love, and I can't undo a lace. Don't you laugh. Don't you dare— ...Wait. ...All right. All right. ...You told me anyway.

### 33. `dlg.sella.free_night.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_night#1
*Played:* serious, unguarded; very quiet; doing: looks at you as if learning your face; pace: slow; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. No laugh and no performance: the voice she doesn't sell. 'No talking. I talk for money.' a rule, close and plain. 'Stay like that. Let me look.' slow; she is learning your face. 'I'm not making a joke of it. Don't you make one.' almost fierce, very low. '...Yes.' to herself as much as to you: a decision, never a moan. If no take of '...Yes.' sounds like a decision and not a breath, cut the word, from the text as well (the story lead's change): the line ends on 'Don't you make one.'

```
[serious, unguarded, quietly] No talking. I talk for money. ...Stay like that. Let me look. ...I'm not making a joke of it. Don't you make one. ...Yes.
```
Subtitle: No talking. I talk for money. ...Stay like that. Let me look. ...I'm not making a joke of it. Don't you make one. ...Yes.

### 34. `dlg.sella.free_morning.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_morning#0
*Played:* tender; then serious; doing: a warning out of love; pace: slow; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. She's still there when you wake, which is the point. The Rook joke soft. Then serious: the Vonnra warning, plain. 'It's the kindest thing I've said to anyone in a year.' nearly shy.

```
[tender, quietly] Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anything up here you'd not want Vonra to hear. I mean that kindly. It's the kindest thing I've said to anyone in a year.
```
Subtitle: Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anything up here you'd not want Vonnra to hear. I mean that kindly. It's the kindest thing I've said to anyone in a year.

### 35. `dlg.sella.past.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#0
*Played:* attentive, warm; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. She goes still when you start: she knows who buys what's said up here, and you know she knows. Chin on her fist, listening properly. Pictures it fondly; a little laugh at herself on the guess. 'You know where that goes, love. You know exactly where.' plain, not sorry. A silence; then 'Go on. Out.' a joke to end it.

```
[attentive, warm, quietly] A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that. ...You know where that goes, love. You know exactly where. [long pause] Go on. Out. Before I start charging you for the sentiment.
```
Subtitle: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that. ...You know where that goes, love. You know exactly where. Go on. Out. Before I start charging you for the sentiment.

### 36. `dlg.sella.past.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#1
*Played:* attentive, warm; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. As past.0: still when you start, chin on her fist. Teasing 'cloister rat', admiring. 'Good for you, love.' Then plain about where it goes, a silence, and the joke out.

```
[attentive, warm, quietly] A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love. ...You know where that goes, love. You know exactly where. [long pause] Go on. Out. Before I start charging you for the sentiment.
```
Subtitle: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love. ...You know where that goes, love. You know exactly where. Go on. Out. Before I start charging you for the sentiment.

### 37. `dlg.sella.past.2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#2
*Played:* attentive, conspiratorial; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. As past.0. A low laugh before 'Takes one to know one.' Then plain about where it goes, a silence, and the joke out.

```
[attentive, conspiratorial, quietly] Worse company than the Kerchiefs, and you walked away from it. [chuckles] Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactly where. [long pause] Go on. Out. Before I start charging you for the sentiment.
```
Subtitle: Worse company than the Kerchiefs, and you walked away from it. Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactly where. Go on. Out. Before I start charging you for the sentiment.

### 38. `dlg.sella.past.3.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#3
*Played:* moved; doing: listens to your past; pace: slow; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. As past.0. Quiet a moment before 'That's the saddest thing'; genuinely moved, soft, no pity. Then plain about where it goes, a silence, and the joke out.

```
[moved, quietly] Chapel lamps, with nobody to see them but you, and you lit them anyway. [short pause] That's the saddest thing anyone's told me up here, love, and they tell me some sad things. ...You know where that goes, love. You know exactly where. [long pause] Go on. Out. Before I start charging you for the sentiment.
```
Subtitle: Chapel lamps, with nobody to see them but you, and you lit them anyway. That's the saddest thing anyone's told me up here, love, and they tell me some sad things. ...You know where that goes, love. You know exactly where. Go on. Out. Before I start charging you for the sentiment.

### 39. `dlg.sella.past.4.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#4
*Played:* fond surprise; doing: to know them a little; pace: measured; volume: level.
*Wants:* to know them a little
*Note:* Morning in the room: close and quiet, not hushed. Chin on her fist, listening properly; she enjoys the picture of you young. 'I'd have guessed, but not that' warm and slightly puzzled. What is said here may be sold, and she knows it.

```
[fond surprise] A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that.
```
Subtitle: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that.

### 40. `dlg.sella.past.5.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#5
*Played:* admiring warmth; doing: to approve of their escape; pace: brisk; volume: quiet.
*Wants:* to approve of their escape
*Note:* Morning in the room: close and quiet, not hushed. Chin on her fist. A gentle tease ('cloister rat'), then 'Good for you, love' warmly meant: she knows about getting out.

```
[admiring warmth, quietly] A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love.
```
Subtitle: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love.

### 41. `dlg.sella.past.6.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#6
*Played:* kinship; doing: to share a secret back; pace: measured; volume: quiet.
*Wants:* to share a secret back
*Note:* Morning in the room: close and quiet, not hushed. Chin on her fist. Her low laugh before 'Takes one to know one', which hints at her own past, unexplained. 'Don't tell Rook' is a shared joke.

```
[kinship, quietly] Worse company than the Kerchiefs, and you walked away from it. [chuckles] Takes one to know one. Don't tell Rook.
```
Subtitle: Worse company than the Kerchiefs, and you walked away from it. Takes one to know one. Don't tell Rook.

### 42. `dlg.sella.past.7.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/past#7
*Played:* moved; doing: to honor what they told her; pace: slow; volume: quiet.
*Wants:* to honor what they told her
*Note:* Morning in the room: close and quiet, not hushed. Chin on her fist. Quiet a moment before the second sentence. 'Saddest thing' said without performance; the last clause keeps it from tipping into pity.

```
[moved, quietly] Chapel lamps, with nobody to see them but you, and you lit them anyway. [short pause] That's the saddest thing anyone's told me up here, love, and they tell me some sad things.
```
Subtitle: Chapel lamps, with nobody to see them but you, and you lit them anyway. That's the saddest thing anyone's told me up here, love, and they tell me some sad things.

### 43. `dlg.sella.sleeptalk.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/sleeptalk#0
*Played:* gentle, uneasy; doing: you said a name; pace: slow; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. Careful and kind; a one-shouldered shrug in the voice on 'Didn't catch it.' 'I don't think you did either.' gentle and unsettling.

```
[gentle, uneasy, quietly] You said a name. Over and over, like you'd got hold of it in the dark and didn't want to let go. Didn't catch it. I don't think you did either.
```
Subtitle: You said a name. Over and over, like you'd got hold of it in the dark and didn't want to let go. Didn't catch it. I don't think you did either.

### 44. `dlg.sella.stairs_say.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_say#0
*Played:* teasing; doing: you know the stairs; pace: measured; volume: quiet.

```
[teasing, quietly] You're getting good at my stairs, love. Careful. People'll think you live here.
```
Subtitle: You're getting good at my stairs, love. Careful. People'll think you live here.

### 45. `dlg.sella.stairs_say.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_say#1
*Played:* dry, wicked; doing: the creaking steps; pace: measured; volume: quiet.
*Note:* The wives joke deadpan.

```
[dry, wicked, quietly] Mind the fourth. And the ninth. Rook says they're for the drunks. I say they're for the wives.
```
Subtitle: Mind the fourth. And the ninth. Rook says they're for the drunks. I say they're for the wives.

### 46. `dlg.sella.stairs_say.2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_say#2
*Played:* warm, teasing; doing: the bath; pace: measured; volume: quiet.

```
[warm, teasing, quietly] In you go. Bath's run. It's warm, I promise. For a bit.
```
Subtitle: In you go. Bath's run. It's warm, I promise. For a bit.

### 47. `dlg.sella.stairs_room.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#0
*Played:* low, amused, at work; doing: again: the room, the water, you; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. 'Blue room again. Same jug, same quilt.' easy, a regular's welcome. '...Same me.' dry, half a laugh at herself, not sad. Then as the first time: brisk with the buckles, a short real laugh at the stuck one, 'A person.' meant.

```
[low, amused, at work, quietly] Blue room again. Same jug, same quilt. ...Same me. I've undone a few of these, love. [laughs softly] All that steel, and under it, look. A person.
```
Subtitle: Blue room again. Same jug, same quilt. ...Same me. I've undone a few of these, love. All that steel, and under it, look. A person.

### 48. `dlg.sella.stairs_room.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#1
*Played:* low, amused; then reading you; doing: again: your hands; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. 'Blue room again...' easy; '...Same me.' dry, not sad. Then slower over your hands, reading the scars; 'Gently, upstairs. I mean it. I like this jug.' a joke with a rule in it.

```
[low, amused, quietly] Blue room again. Same jug, same quilt. ...Same me. Give me your hands. ...The other one. ...Look at these knuckles. Gently, upstairs. I mean it. I like this jug.
```
Subtitle: Blue room again. Same jug, same quilt. ...Same me. Give me your hands. ...The other one. ...Look at these knuckles. Gently, upstairs. I mean it. I like this jug.

### 49. `dlg.sella.stairs_room.2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#2
*Played:* low, amused; then caught out; doing: again: you're cold; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. 'Blue room again...' easy; '...Same me.' dry. Then the breath through her teeth at your skin, and the joke over it: 'Pick one, love.'

```
[low, amused, quietly] Blue room again. Same jug, same quilt. ...Same me. [sharp inhale] Your hands are hot and the rest of you's a cellar floor. Pick one, love.
```
Subtitle: Blue room again. Same jug, same quilt. ...Same me. Your hands are hot and the rest of you's a cellar floor. Pick one, love.

### 50. `dlg.sella.stairs_room.3.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#3
*Played:* low, amused, teasing; doing: again: she gets her own back; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. 'Blue room again...' easy; '...Same me.' dry. Then at your ear from behind, wicked and soft; the laugh at your jump real or cut.

```
[low, amused, teasing, quietly] Blue room again. Same jug, same quilt. ...Same me. [whispers] There. Now you know what it's like. [laughs softly] You jumped.
```
Subtitle: Blue room again. Same jug, same quilt. ...Same me. There. Now you know what it's like. You jumped.

### 51. `dlg.sella.stairs_room.4.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#4
*Played:* low, amused, at work; doing: the first time: the room, the water, you; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. A professional's welcome, warm because warmth is the job and she's good at it. 'Everyone asks.' dry. 'Warm. Told you.' pleased with herself. 'I've undone a few of these, love.' brisk pride. The laugh is at the stuck buckle, short and real. 'All that steel, and under it, look. A person.' amused, and meaning it: a professional's line that happens to be true.

```
[low, amused, at work, quietly] It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. I've undone a few of these, love. [laughs softly] All that steel, and under it, look. A person.
```
Subtitle: It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. I've undone a few of these, love. All that steel, and under it, look. A person.

### 52. `dlg.sella.stairs_room.5.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#5
*Played:* low, amused; then reading you; doing: the first time: your hands; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. As the warden's welcome, then slower over your hands: '...The other one. ...Look at these knuckles.' she's reading the scars, not flirting. 'Gently, upstairs. I mean it. I like this jug.' a joke with a rule in it.

```
[low, amused, quietly] It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. Give me your hands. ...The other one. ...Look at these knuckles. Gently, upstairs. I mean it. I like this jug.
```
Subtitle: It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. Give me your hands. ...The other one. ...Look at these knuckles. Gently, upstairs. I mean it. I like this jug.

### 53. `dlg.sella.stairs_room.6.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#6
*Played:* low, amused; then caught out; doing: the first time: you're cold; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. As the warden's welcome; then she touches you and takes a breath through her teeth (the only sound she makes before the words). 'Your hands are hot and the rest of you's a cellar floor.' puzzled for one beat, then covered: 'Pick one, love.' light.

```
[low, amused, quietly] It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. [sharp inhale] Your hands are hot and the rest of you's a cellar floor. Pick one, love.
```
Subtitle: It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. Your hands are hot and the rest of you's a cellar floor. Pick one, love.

### 54. `dlg.sella.stairs_room.7.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_room#7
*Played:* low, amused, teasing; doing: the first time: she gets her own back; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. As the warden's welcome; then right at your ear, from behind: 'There. Now you know what it's like.' wicked and soft. The laugh is delight at your jump, real or cut; 'You jumped.' pleased.

```
[low, amused, teasing, quietly] It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. [whispers] There. Now you know what it's like. [laughs softly] You jumped.
```
Subtitle: It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. There. Now you know what it's like. You jumped.

### 55. `dlg.sella.stairs_rules.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_rules#0
*Played:* unsettled; then brisk to cover it; doing: she feels the cold in you and puts it away to work; pace: slow; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. In the bath, her hands on your arms. '...You're cold.' plain and close: a professional surprised for once. 'Not chilled, love. Cold.' exact, correcting herself. 'Under warm water.' almost to herself. The long quiet is real, no joke in it. Then 'Right. Rules.' back to work, and the last line warm and wicked, as if the quiet never happened.

```
[unsettled, quietly] ...You're cold. Not chilled, love. Cold. Under warm water. [long pause] ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder.
```
Subtitle: ...You're cold. Not chilled, love. Cold. Under warm water. ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder.

### 56. `dlg.sella.stairs_rules.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stairs_rules#1
*Played:* frank, wry; doing: her rules, the first night; pace: unhurried; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. Her house rules: patter she has said a hundred times and still enjoys. 'Anything you'd rather I didn't, say so.' plain, and meant. 'Anything you'd rather I did, say it louder;' low and wicked. 'Rook's walls are thin, but she's deaf in the left ear.' deadpan: the joke left for you to find.

```
[frank, wry, quietly] Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder; Rook's walls are thin, but she's deaf in the left ear.
```
Subtitle: Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder; Rook's walls are thin, but she's deaf in the left ear.

### 57. `dlg.sella.stop_paid.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/stop_paid#0
*Played:* easy, kind, businesslike; doing: you stop; she lets you go without a sulk or a question; pace: measured; volume: quiet.
*Note:* No hurt in it and no sell. She counts thirteen back into your palm (the coins are the game's, not the take's): leave a beat for them. 'Two for the water. That's Rook's rule, not mine.' a light apology. 'Either's all right, love.' meant.

```
[easy, kind, businesslike, quietly] Then I'll have the bath. It's paid for. [short pause] Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or you won't. Either's all right, love. Go on.
```
Subtitle: Then I'll have the bath. It's paid for. Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or you won't. Either's all right, love. Go on.

### 58. `dlg.sella.rest_night.0.p0.wav`

*Where:* dialogue.json sella/rest_night#0; part 1 of 3: **sella: Sleep.** / narrator: She looks at you as if you'd asked her to recite something in a foreign tongue. / sella: You've paid fifteen gold to sleep.
*Played:* baffled amusement; doing: you paid to sleep; pace: measured; volume: quiet.
*Note:* Narrator for the look. Incredulous.

```
[baffled amusement, quietly] Sleep.
```
Subtitle: Sleep.

### 59. `dlg.sella.rest_night.0.p2.wav`

*Where:* dialogue.json sella/rest_night#0; part 3 of 3: sella: Sleep. / narrator: She looks at you as if you'd asked her to recite something in a foreign tongue. / **sella: You've paid fifteen gold to sleep.**
*Played:* baffled amusement; doing: you paid to sleep; pace: measured; volume: quiet.
*Note:* Narrator for the look. Incredulous.

```
[baffled amusement, quietly] You've paid fifteen gold to sleep.
```
Subtitle: You've paid fifteen gold to sleep.

### 60. `dlg.sella.rest_night_paid.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/rest_night_paid#0
*Played:* baffled, amused; doing: you've paid her to sleep; pace: measured; volume: quiet.
*Note:* 'Sleep.' turned over as if it were a word in a foreign tongue: not mocking, genuinely thrown. Then the sum, flat, and delighted despite herself.

```
[baffled, amused, quietly] Sleep. ...You've paid fifteen gold to sleep.
```
Subtitle: Sleep. ...You've paid fifteen gold to sleep.

### 61. `dlg.sella.rest_bed.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/rest_bed#0
*Played:* bossy, wry; doing: lie down, then; pace: brisk; volume: quiet.
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. Rapid little orders, low, arranging you for sleep: bossy because it's easier than tender. 'No. Boots off; Rook'll have my hide.' quick. 'I'm not sitting up all night in a chair.' dry. 'I've done that for worse money.' drier, and true, and left there.

```
[bossy, wry, quietly] ...Lie down, then. No. Boots off; Rook'll have my hide. Shift over. I'm not sitting up all night in a chair. I've done that for worse money.
```
Subtitle: ...Lie down, then. No. Boots off; Rook'll have my hide. Shift over. I'm not sitting up all night in a chair. I've done that for worse money.

### 62. `dlg.sella.rest_dark.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/rest_dark#0
*Played:* chatty, low, drowsy; doing: talks you to sleep, then watches; pace: slow; volume: quiet.
*Hides:* she knows who pays for a thing like this, and Vonnra will have your cold by noon
*Note:* Dark room: low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. A laugh that sounds made is cut: leave it out. On top of the quilt, dressed, talking low the way you talk someone down: gossip, warm and a little wicked, already mid-story. 'him in his shirt— no.' stops herself, amused. 'And I said—' she sees you've gone, and the break is real. Then softer, nearly to herself: 'Go on, then. Sleep.' 'Somebody ought to watch you.' tender, with the thing she'll sell under it: never played as a threat.

```
[chatty, low, drowsy, quietly] ...and there's Rook at the top of the stairs with her cudgel, and him in his shirt— no. That one's for another night. ...There was a man from Low Kiln, wanted me to bark. Like a dog. And I said— [long pause] [softly] ...Go on, then. Sleep. Somebody ought to watch you.
```
Subtitle: ...and there's Rook at the top of the stairs with her cudgel, and him in his shirt— no. That one's for another night. ...There was a man from Low Kiln, wanted me to bark. Like a dog. And I said— ...Go on, then. Sleep. Somebody ought to watch you.

### 63. `dlg.sella.rest_morning.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/rest_morning#0
*Played:* unsettled; then fond; doing: you were cold all night; pace: slow; volume: quiet.
*Hides:* she knows who pays for a thing like this, and unless she has stopped selling you, Vonnra will have it by noon
*Note:* Morning in the room: close and quiet, not hushed. Her hand flat on your chest. Quiet wonder at the cold. Then warm and wry: 'Best money I ever made.' doubles (she'll be paid for it twice): play it as a joke and nothing more; the listener finds the rest.

```
[unsettled, quietly] You were cold as the river all night. Like lying next to a stone. And now look at you: warm as toast. ...Fifteen gold to lie awake next to a stone. Best money I ever made. Don't tell anyone.
```
Subtitle: You were cold as the river all night. Like lying next to a stone. And now look at you: warm as toast. ...Fifteen gold to lie awake next to a stone. Best money I ever made. Don't tell anyone.

### 64. `dlg.sella.rest_morning.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/rest_morning#1
*Played:* fond, teasing; doing: best money; pace: measured; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. Already dressed, and for once she doesn't count it. 'Rich and bored.' a grin.

```
[fond, teasing, quietly] Fifteen gold to watch you snore. Best money I ever made. Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.
```
Subtitle: Fifteen gold to watch you snore. Best money I ever made. Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.

### 65. `dlg.sella.door.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/door#0
*Played:* matter-of-fact, guarded; doing: the bolt and Rook; pace: measured; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. Doing up her boots on the bed, not looking up. Plain about danger; 'I'll not say which.' closed. 'Nothing in here's my door.' flat, and it costs her.

```
[matter-of-fact, guarded, quietly] That? It's Rook's. Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funny she's up those stairs before he's finished turning. I've needed her twice in seven years. Once for a drover. Once for one of the Watch, and I'll not say which. ...So, no. I've never shot it. It's not my door. Nothing in here's my door.
```
Subtitle: That? It's Rook's. Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funny she's up those stairs before he's finished turning. I've needed her twice in seven years. Once for a drover. Once for one of the Watch, and I'll not say which. ...So, no. I've never shot it. It's not my door. Nothing in here's my door.

### 66. `dlg.sella.door_years.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/door_years#0
*Played:* wry, warm; doing: her years; pace: measured; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. Self-mocking; the laugh low and short, before 'I'm twenty-nine'.

```
[wry, warm, quietly] Twenty-two, and sure I was cleverer than everyone in the valley. I was right about most of them. [chuckles] I'm twenty-nine, love, since you're doing sums. Seven years at the top of Rook's stairs, and I've only fallen down them twice.
```
Subtitle: Twenty-two, and sure I was cleverer than everyone in the valley. I was right about most of them. I'm twenty-nine, love, since you're doing sums. Seven years at the top of Rook's stairs, and I've only fallen down them twice.

### 67. `dlg.sella.door_south.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/door_south#0
*Played:* wistful, guarded; doing: the house in the south; pace: slow; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. Standing, checking her hair in the jug, not looking at you. 'And somebody who knocks.' quiet.

```
[wistful, guarded, quietly] I told you. A house in the south. A door that locks from the inside. [short pause] And somebody who knocks.
```
Subtitle: I told you. A house in the south. A door that locks from the inside. And somebody who knocks.

### 68. `dlg.sella.free_decline.0.p0.wav`

*Where:* dialogue.json sella/free_decline#0; part 1 of 5: **sella: Your loss, love. Literally; I'm worth a fortune.** / narrator: She means it lightly, and very nearly manages it. / sella: ...No, it's all right. It is. I'll not ask twice. I don't ask twice. / narrator: She pats your cheek, once, like a regular's. / sella: Go on. Rook's stew's still warm.
*Played:* hurt, covering lightly; doing: you said no; pace: measured; volume: quiet.
*Note:* 'Your loss, love. Literally; I'm worth a fortune.' a real joke, with a laugh. '...No, it's all right.' a beat, 'It is.': convincing herself. 'I don't ask twice.' is pride. Narrator: the pat. Brisk kindness.

```
[hurt, covering lightly, quietly] Your loss, love. Literally; I'm worth a fortune. [laughs]
```
Subtitle: Your loss, love. Literally; I'm worth a fortune.

### 69. `dlg.sella.free_decline.0.p2.wav`

*Where:* dialogue.json sella/free_decline#0; part 3 of 5: sella: Your loss, love. Literally; I'm worth a fortune. / narrator: She means it lightly, and very nearly manages it. / **sella: ...No, it's all right. It is. I'll not ask twice. I don't ask twice.** / narrator: She pats your cheek, once, like a regular's. / sella: Go on. Rook's stew's still warm.
*Played:* hurt, covering lightly; doing: you said no; pace: measured; volume: quiet.
*Note:* 'Your loss, love. Literally; I'm worth a fortune.' a real joke, with a laugh. '...No, it's all right.' a beat, 'It is.': convincing herself. 'I don't ask twice.' is pride. Narrator: the pat. Brisk kindness.

```
[hurt, covering lightly, quietly] ...No, it's all right… It is. I'll not ask twice. I don't ask twice.
```
Subtitle: ...No, it's all right. It is. I'll not ask twice. I don't ask twice.

### 70. `dlg.sella.free_decline.0.p4.wav`

*Where:* dialogue.json sella/free_decline#0; part 5 of 5: sella: Your loss, love. Literally; I'm worth a fortune. / narrator: She means it lightly, and very nearly manages it. / sella: ...No, it's all right. It is. I'll not ask twice. I don't ask twice. / narrator: She pats your cheek, once, like a regular's. / **sella: Go on. Rook's stew's still warm.**
*Played:* hurt, covering lightly; doing: you said no; pace: measured; volume: quiet.
*Note:* 'Your loss, love. Literally; I'm worth a fortune.' a real joke, with a laugh. '...No, it's all right.' a beat, 'It is.': convincing herself. 'I don't ask twice.' is pride. Narrator: the pat. Brisk kindness.

```
[hurt, covering lightly, quietly] Go on. Rook's stew's still warm.
```
Subtitle: Go on. Rook's stew's still warm.

### 71. `dlg.sella.free_ask.0.p1.wav`

*Where:* dialogue.json sella/free_ask#0; part 2 of 2: narrator: She looks at you for a long moment, as if you were a coin she was checking for clipping. / **sella: I said I'd not ask twice. I never said I'd not answer. ...Come on, then. Before I think be…**
*Played:* wary, then giving in; doing: you asked; pace: measured; volume: quiet.
*Note:* Narrator for the look. Wry logic. 'Come on.' twice, the second a little shaky.

```
[wary, then giving in, quietly] I said I'd not ask twice. I never said I'd not answer. ...Come on, then. Before I think better of it. I'm thinking better of it already. Come on.
```
Subtitle: I said I'd not ask twice. I never said I'd not answer. ...Come on, then. Before I think better of it. I'm thinking better of it already. Come on.

### 72. `dlg.sella.free_door.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_door#0
*Played:* unsure, honest, wondering; doing: nobody does that; pace: slow; volume: quiet.
*Note:* In the room, lamp up. 'Lamp stays up tonight.' the first thing, plain: she wants to see and be seen, and it isn't seduction. Then the wonder, quiet: 'Nobody does that.' and a beat. 'Nobody's ever done that.' lower.

```
[unsure, honest, wondering, quietly] Lamp stays up tonight. ...I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd hear it by morning. ...Nobody does that. Nobody's ever done that.
```
Subtitle: Lamp stays up tonight. ...I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd hear it by morning. ...Nobody does that. Nobody's ever done that.

### 73. `dlg.sella.free_door.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_door#1
*Played:* unsure, honest; doing: she doesn't know how to do this one; pace: slow; volume: quiet.
*Note:* 'Lamp stays up tonight.' plain, not seduction. 'I don't know how to do this one.' a real admission. '...That's a lie. I know how.' a half-laugh at herself. 'I don't know how to do it like this.' quiet, the truest thing she's said upstairs.

```
[unsure, honest, quietly] Lamp stays up tonight. ...I don't know how to do this one. ...That's a lie. I know how. I don't know how to do it like this.
```
Subtitle: Lamp stays up tonight. ...I don't know how to do this one. ...That's a lie. I know how. I don't know how to do it like this.

### 74. `dlg.sella.free_want.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_want#0
*Played:* steady, close to tears; refusing them; doing: says yes; pace: slow; volume: quiet.
*Note:* 'Ask me that again and I'll cry, and I don't cry, so don't.' quick, a warning with a laugh in the throat. A breath out. 'Yes. ...Yes.' the second firmer. 'There. Said it.' as if she'd lifted something heavy. 'Come here.' soft.

```
[steady, close to tears, quietly] Ask me that again and I'll cry, and I don't cry, so don't. [exhales] Yes. ...Yes. There. Said it. Come here.
```
Subtitle: Ask me that again and I'll cry, and I don't cry, so don't. Yes. ...Yes. There. Said it. Come here.

### 75. `dlg.sella.free_stop.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_stop#0
*Played:* relieved, and meaning it; doing: you stop; she's glad; pace: slow; volume: quiet.
*Note:* A breath out she's held since the stairs. 'All right.' twice, the second one sure. 'Sit with me, then. Just sit.' shy. 'Rook'd think we'd died.' a real smile.

```
[relieved, and meaning it, quietly] [exhales] All right. All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'd think we'd died.
```
Subtitle: All right. All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'd think we'd died.

### 76. `dlg.sella.free_sit.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_sit#0
*Played:* slow, private; doing: tells you the house in the south, for nothing; pace: slow; volume: quiet.
*Note:* Backs to the wall, sitting up together. She has never told it for nothing: each thing placed like furniture. 'Not blue; nothing in it blue.' a little fierce. A breath. 'And somebody who knocks.' the whole dream in it, and she can't stay there: 'Go on, then. Down you go.' brisk before it shows. 'Mind the fourth.' fond.

```
[slow, private, quietly] The house. In the south. ...Kitchen faces the sun. Green door. Not blue; nothing in it blue. [exhales] And somebody who knocks. ...Go on, then. Down you go. Mind the fourth.
```
Subtitle: The house. In the south. ...Kitchen faces the sun. Green door. Not blue; nothing in it blue. And somebody who knocks. ...Go on, then. Down you go. Mind the fourth.

### 77. `dlg.sella.free_sleep.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_sleep#0
*Played:* laughing, properly; doing: you want to sleep with her, only sleep; pace: measured; volume: quiet.
*Note:* The first real laugh tonight, out of her before she can make it pretty (real or cut). 'You and your sleeping.' fond. 'Yes. All right. Yes.' each softer.

```
[laughing, properly, quietly] [laughs] You and your sleeping. ...Yes. All right. Yes.
```
Subtitle: You and your sleeping. ...Yes. All right. Yes.

### 78. `dlg.sella.free_sleep_bed.0.p1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_sleep_bed#0; part 2 of 2: narrator: Behind the door, the bolt sticks halfway; nobody has ever shot it. Swearing, and a shoulde… / **sella: Shift over. Arm. ...Your arm, love, over. Like a blanket. There.**
*Played:* sleepy, practical, tender; doing: she sleeps, with your arm over her; pace: slow; volume: quiet.
*Note:* The narrator's aside is the bolt, heard from the stairs (one take with free_bolt's). Then Sella in the dark, low and close, nearly a whisper, never breathy. Each '...' is a real silence of two to four seconds. 'Shift over. Arm.' half asleep already, arranging you. 'Your arm, love, over. Like a blanket.' 'There.' content.

```
[sleepy, practical, tender, quietly] Shift over. Arm. ...Your arm, love, over. Like a blanket. There.
```
Subtitle: Shift over. Arm. ...Your arm, love, over. Like a blanket. There.

### 79. `dlg.sella.free_bolt.0.p1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_bolt#0; part 2 of 2: narrator: Behind the door, the bolt sticks halfway; nobody has ever shot it. Swearing, and a shoulde… / **sella: ...There.**
*Played:* barely voiced; doing: the bolt: the last thing she tells; pace: slow; volume: quiet.
*Note:* Her forehead against the door, her back to you; she has never shot it. The word is the decision: a breath out with a word in it, not a whisper.

```
[barely voiced, quietly] ...There.
```
Subtitle: ...There.

### 80. `dlg.sella.free_m_downstairs.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_m_downstairs#0
*Played:* wry; then honest; doing: go on; pace: measured; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. A laugh first, easy. The turn 'No. You wouldn't.' honest. 'That's the point, love.' fond.

```
[wry, quietly] [laughs] Downstairs Rook hears everything and charges nobody. You'd be better off with me. ...No. You wouldn't. That's the point, love. Go on.
```
Subtitle: Downstairs Rook hears everything and charges nobody. You'd be better off with me. ...No. You wouldn't. That's the point, love. Go on.

### 81. `dlg.sella.free_m_who.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_m_who#0
*Played:* honest, uncomfortable; doing: Vonnra pays; pace: slow; volume: quiet.
*Note:* Morning in the room: close and quiet, not hushed. She pulls the quilt up to her chin while she says it. Her honesty stumbling; a beat where the name would be. 'Don't make me practice before breakfast.' a joke to get out of the room.

```
[honest, uncomfortable, quietly] You know who. Everybody pays; she pays most. [short pause] I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don't know. That's the honest answer, and I'm out of practice at those. Don't make me practice before breakfast.
```
Subtitle: You know who. Everybody pays; she pays most. I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don't know. That's the honest answer, and I'm out of practice at those. Don't make me practice before breakfast.

### 82. `dlg.sella.free_m_kiss.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json sella/free_m_kiss#0
*Played:* smiling; doing: out, before she gets used to it; pace: measured; volume: quiet.
*Note:* Morning in the room. She lets you kiss her, then pushes you off by the face with the flat of her hand. 'Out. Before I get used to it.' close, smiling: the truth under the joke. The ninth step creaks behind you (the game's sound). '...I'm not watching you go.' called down after you from two steps down: pitched to carry, never raised; caught, and grinning about it. 'Go on.'

```
[smiling, quietly] Out. Before I get used to it. [long pause] [calling down softly, amused] ...I'm not watching you go. Go on.
```
Subtitle: Out. Before I get used to it. ...I'm not watching you go. Go on.

### 83. `dlg.sella.refuse_roost.0.p1.wav`

*Where:* dialogue.json sella/refuse_roost#0; part 2 of 4: narrator: At the top of the stairs she stops with her hand on the door. / **sella: They're saying you burned the Roost with folk still in it.** / narrator: She puts the coins back in your hand, all of them. / sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…
*Played:* cool, firm; doing: she won't work tonight; pace: slow; volume: quiet.
*Note:* Narrator at the door and the coins. Cool, not cruel. 'Come back when I can't.' quiet.

```
[cool, firm, quietly] They're saying you burned the Roost with folk still in it.
```
Subtitle: They're saying you burned the Roost with folk still in it.

### 84. `dlg.sella.refuse_roost.0.p3.wav`

*Where:* dialogue.json sella/refuse_roost#0; part 4 of 4: narrator: At the top of the stairs she stops with her hand on the door. / sella: They're saying you burned the Roost with folk still in it. / narrator: She puts the coins back in your hand, all of them. / **sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…**
*Played:* cool, firm; doing: she won't work tonight; pace: slow; volume: quiet.
*Note:* Narrator at the door and the coins. Cool, not cruel. 'Come back when I can't.' quiet.

```
[cool, firm, quietly] I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working with that in the room. ...Come back when I can't.
```
Subtitle: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working with that in the room. ...Come back when I can't.

### 85. `dlg.sella.say_keegan.0.wav`

*Where:* dialogue.json sella/say_keegan#0
*Played:* delighted gossip; doing: Keegan's list; pace: measured; volume: level.
*Note:* Teasing; 'the whole chapter' mock-doom.

```
[delighted gossip] The knight's been asking Rook what you like for breakfast. In full sentences, love. With a list. ...She's going to read you a chapter after. You know that. You'll have to sit through the whole chapter.
```
Subtitle: The knight's been asking Rook what you like for breakfast. In full sentences, love. With a list. ...She's going to read you a chapter after. You know that. You'll have to sit through the whole chapter.

### 86. `dlg.sella.say_rav.0.wav`

*Where:* dialogue.json sella/say_rav#0
*Played:* fond, frank; doing: be kind to Rav; pace: measured; volume: quiet.
*Note:* 'He's softer than he drinks.' gentle.

```
[fond, frank, quietly] You went round the back of the Flagon after closing. Rav's been up my stairs twice in seven years, and both times to lance something. Be kind to him. He's softer than he drinks.
```
Subtitle: You went round the back of the Flagon after closing. Rav's been up my stairs twice in seven years, and both times to lance something. Be kind to him. He's softer than he drinks.

## Said in passing

### 87. `bark.sella.day.0.wav`

*Where:* npcs.json sella.barks[0]
*Played:* amused; pace: measured; volume: level.

```
[amused] Buy a girl a drink? No? Buy yourself one, then. You look like you need it.
```
Subtitle: Buy a girl a drink? No? Buy yourself one, then. You look like you need it.

### 88. `bark.sella.day.1.wav`

*Where:* npcs.json sella.barks[1]
*Played:* amused; pace: measured; volume: level.

```
[amused] You've got road on you. I can smell it from here.
```
Subtitle: You've got road on you. I can smell it from here.

### 89. `bark.sella.day.2.wav`

*Where:* npcs.json sella.barks[2]
*Played:* amused; pace: measured; volume: level.

```
[amused] Rook's stew or my company. Only one of them's warm.
```
Subtitle: Rook's stew or my company. Only one of them's warm.

### 90. `bark.sella.night.0.wav`

*Where:* npcs.json sella.nightBarks[0]
*Played:* teasing; pace: measured; volume: quiet.

```
[teasing, quietly] Cold night to sleep alone, love.
```
Subtitle: Cold night to sleep alone, love.

### 91. `bark.sella.night.1.wav`

*Where:* npcs.json sella.nightBarks[1]
*Played:* teasing; pace: measured; volume: quiet.
*Note:* An invitation dressed as thrift.

```
[teasing, quietly] I've a bath going cold upstairs. Shame to waste it.
```
Subtitle: I've a bath going cold upstairs. Shame to waste it.

### 92. `bark.sella.night.2.wav`

*Where:* npcs.json sella.nightBarks[2]
*Played:* teasing; pace: measured; volume: quiet.

```
[teasing, quietly] The blue room's got a lamp lit. Guess who's in it.
```
Subtitle: The blue room's got a lamp lit. Guess who's in it.

### 93. `bark.sella.night.3.wav`

*Where:* npcs.json sella.nightBarks[3]
*Played:* teasing; pace: measured; volume: quiet.

```
[teasing, quietly] Rook's walls are thin and I'm not quiet. Fair warning.
```
Subtitle: Rook's walls are thin and I'm not quiet. Fair warning.

### 94. `bark.sella.said.0.wav`

*Where:* npcs.json sella.said[0]

```
Tell me about last night, love. I pay better than the Wayfinder.
```
Subtitle: Tell me about last night, love. I pay better than the Wayfinder.

### 95. `bark.sella.said.1.wav`

*Where:* npcs.json sella.said[1]

```
Back, and all your bits still on. Pity to waste them on sleep.
```
Subtitle: Back, and all your bits still on. Pity to waste them on sleep.


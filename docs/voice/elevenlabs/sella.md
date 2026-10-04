# Sella: ElevenLabs packet

Voice id in the game: `sella`. 95 takes to record (9,821 characters; about 29,463 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Sella** (the blue room). Low, amused, intimate; heavy contractions; "love". Frank about sex and money and about which is which; never coy, never pitiful, never sorry for her work. Sells talk as well as company and says so. *Casting:* late 20s, softened Cockney; warmth that is also work. Adult, never breathy.

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

### 13. `dlg.sella.night.1.p1.wav`

*Where:* dialogue.json sella/night#1; part 2 of 3: narrator: The water's gone cool by the time either of you notices, and she drags the quilt off the b… / **sella: Don't,** / narrator: and kisses you so you can't. After, you lie on the floor of the blue room with the lamp tu…
*Played:* plain; doing: a night with Sella; pace: slow; volume: quiet.
*Note:* Low and close, discreet; 'She is dressed, and counting.' plain. Her word is hers.

```
[plain, quietly] Don't,
```
Subtitle: Don't,

### 14. `dlg.sella.morning.0.p1.wav`

*Where:* dialogue.json sella/morning#0; part 2 of 2: narrator: She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone. / **sella: You were cold as the river all night, love. Like sleeping next to a stone. And now look at…**
*Played:* fond, teasing; doing: you're a habit; pace: measured; volume: level.
*Note:* Pleased. Rook's complaint relayed with relish. Brisk send-off with a dark joke.

```
[fond, teasing] You were cold as the river all night, love. Like sleeping next to a stone. And now look at you: warm as toast. ...Rook's got a word for that. It's not a nice word. Get up and eat something.
```
Subtitle: You were cold as the river all night, love. Like sleeping next to a stone. And now look at you: warm as toast. ...Rook's got a word for that. It's not a nice word. Get up and eat something.

### 15. `dlg.sella.morning.1.wav`

*Where:* dialogue.json sella/morning#1
*Played:* fond, teasing; doing: morning after; pace: measured; volume: quiet.
*Note:* 'Not badly.' kind. 'the pieces are what I like.' warm double meaning.

```
[fond, teasing, quietly] You're getting to be a habit. I don't mind. Rook does; she says you're wearing out the stairs. Go on, the day's wasting, and somebody out there owes you money, or the other way round.
```
Subtitle: You're getting to be a habit. I don't mind. Rook does; she says you're wearing out the stairs. Go on, the day's wasting, and somebody out there owes you money, or the other way round.

### 16. `dlg.sella.morning.2.wav`

*Where:* dialogue.json sella/morning#2
*Played:* teasing, fond; doing: you talk in your sleep; pace: measured; volume: quiet.
*Note:* 'You lose. Every time.' a grin.

```
[teasing, fond, quietly] Two nights. ...You make a noise in your sleep, you know. Like you're arguing with somebody. You lose. Every time.
```
Subtitle: Two nights. ...You make a noise in your sleep, you know. Like you're arguing with somebody. You lose. Every time.

### 17. `dlg.sella.morning.3.wav`

*Where:* dialogue.json sella/morning#3
*Played:* affectionate mischief; doing: to send them off without admitting she cares; pace: measured; volume: quiet.
*Wants:* to send them off without admitting she cares
*Note:* Morning-after banter, frank and funny. 'The pieces are what I like' is bawdy and also a real wish for them to come back alive.

```
[affectionate mischief, quietly] You snore, by the way. Not badly. Go on, then. Come back in one piece; the pieces are what I like.
```
Subtitle: You snore, by the way. Not badly. Go on, then. Come back in one piece; the pieces are what I like.

### 18. `dlg.sella.cb_tricked_redcowl.0.wav`

*Where:* dialogue.json sella/cb_tricked_redcowl#0
*Played:* admiring, flirtatious; doing: praises your lie; pace: measured; volume: level.
*Note:* 'You'd do well upstairs' a compliment between professionals.

```
[admiring, flirtatious] Heard you sent Red-cowl running with nothing but a lie and a straight face. You'd do well upstairs, love.
```
Subtitle: Heard you sent Redcowl running with nothing but a lie and a straight face. You'd do well upstairs, love.

### 19. `dlg.sella.cb_exposed_pell.0.wav`

*Where:* dialogue.json sella/cb_exposed_pell#0
*Played:* dry, unsentimental; doing: Pell's gone; pace: measured; volume: level.
*Note:* Deadpan.

```
[dry, unsentimental] Pell's in the cells. One less customer. I'll miss his money and not one other thing about him.
```
Subtitle: Pell's in the cells. One less customer. I'll miss his money and not one other thing about him.

### 20. `dlg.sella.cb_burned_roost.0.wav`

*Where:* dialogue.json sella/cb_burned_roost#0
*Played:* guarded, cool; doing: she's heard; pace: slow; volume: quiet.
*Note:* A pause. 'I don't judge' a professional reflex. 'But I heard.' cool and pointed.

```
[guarded, cool, quietly] They're saying you burned the Roost with folk still in it. ...I don't judge, love; it's bad for business. But I heard.
```
Subtitle: They're saying you burned the Roost with folk still in it. ...I don't judge, love; it's bad for business. But I heard.

### 21. `dlg.sella.cb_freed_teamsters.0.wav`

*Where:* dialogue.json sella/cb_freed_teamsters#0
*Played:* amused tenderness; doing: Jory's crush; pace: measured; volume: level.
*Note:* Laughing at Jory, kindly. 'Sweet.' 'he thinks you're a story.' gentle.

```
[amused tenderness] Jory Coyle came up the stairs to say thank you to somebody, and it wasn't me, and he went red as a radish. Sweet. Go easy on him; he thinks you're a story.
```
Subtitle: Jory Coyle came up the stairs to say thank you to somebody, and it wasn't me, and he went red as a radish. Sweet. Go easy on him; he thinks you're a story.

### 22. `dlg.sella.say_calling.0.wav`

*Where:* dialogue.json sella/say_calling#0
*Played:* teasing; doing: all that steel; pace: measured; volume: level.
*Note:* Dry, bawdy.

```
[teasing] All that steel. Takes an age to get off, I expect. I charge by the hour, love, not by the buckle.
```
Subtitle: All that steel. Takes an age to get off, I expect. I charge by the hour, love, not by the buckle.

### 23. `dlg.sella.say_calling.1.wav`

*Where:* dialogue.json sella/say_calling#1
*Played:* teasing; doing: big hands; pace: measured; volume: level.
*Note:* Dry, bawdy.

```
[teasing] Big hands. Be gentle with them upstairs, or you'll be paying for the furniture.
```
Subtitle: Big hands. Be gentle with them upstairs, or you'll be paying for the furniture.

### 24. `dlg.sella.say_calling.2.wav`

*Where:* dialogue.json sella/say_calling#2
*Played:* startled, amused; doing: you're hot to the touch; pace: measured; volume: level.
*Note:* Puzzled, then laughing: 'You're a little bit on fire.'

```
[startled, amused] Your hands are warm. Not in a nice way. Are you on fire? Your hands are a little bit on fire.
```
Subtitle: Your hands are warm. Not in a nice way. Are you on fire? Your hands are a little bit on fire.

### 25. `dlg.sella.say_calling.3.wav`

*The same words are also* `dlg.sella.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/say_calling#3
*Played:* startled, then wry; doing: you crept up; pace: measured; volume: level.
*Note:* A real start, covered with a joke.

```
[startled, then wry] You came up behind me without a sound. Do that upstairs and you'll get a candlestick in the ear.
```
Subtitle: You came up behind me without a sound. Do that upstairs and you'll get a candlestick in the ear.

### 26. `dlg.sella.say_woman.0.wav`

*Where:* dialogue.json sella/say_woman#0
*Played:* warm, frank; doing: reassures a woman; pace: measured; volume: quiet.
*Note:* Easy and kind; the last sentence a little sad.

```
[warm, frank, quietly] Don't look so surprised, love. You're not the first woman up those stairs and you won't be the last. Half my regulars are lonelier than you.
```
Subtitle: Don't look so surprised, love. You're not the first woman up those stairs and you won't be the last. Half my regulars are lonelier than you.

### 27. `dlg.sella.say_maeca.0.wav`

*Where:* dialogue.json sella/say_maeca#0
*Played:* delighted gossip; doing: Maeca's humming; pace: measured; volume: level.
*Note:* 'Maeca. Humming.' incredulous. Teasing professional jealousy.

```
[delighted gossip] Mayka Barefoot came in this morning humming. Mayka. Humming. I've a professional interest, love: who's my competition?
```
Subtitle: Maeca Barefoot came in this morning humming. Maeca. Humming. I've a professional interest, love: who's my competition?

### 28. `dlg.sella.t_sella.0.wav`

*Where:* dialogue.json sella/t_sella#0
*Played:* wistful, unguarded; doing: what she wants; pace: slow; volume: quiet.
*Note:* The patter drops. 'a door that locks from the inside' quiet. 'Just somebody who knocks.' the most honest thing she says.

```
[wistful, unguarded, quietly] A house in the south with a door that locks from the inside, and somebody who knocks. Man, woman, I'm not fussy. Just somebody who knocks.
```
Subtitle: A house in the south with a door that locks from the inside, and somebody who knocks. Man, woman, I'm not fussy. Just somebody who knocks.

### 29. `dlg.sella.free.0.wav`

*Where:* dialogue.json sella/free#0
*Played:* plain, then strained; doing: offers herself freely, which she has never done; pace: slow; volume: quiet.
*Wants:* you to stay without it turning into business or a fuss
*Hides:* her fear that it means something
*Note:* Not shy: she has never done this. 'Put your purse away.' brisk, a professional's habit; a beat; 'Tonight I'm not working.' plainly, as if it cost nothing. 'Don't look at me like that.' a small laugh at herself; 'Don't make it strange.' is where the strain shows.

```
[plain, then strained, quietly] Put your purse away… Tonight I'm not working. ...Don't look at me like that. [laughs] Don't make it strange.
```
Subtitle: Put your purse away. Tonight I'm not working. ...Don't look at me like that. Don't make it strange.

### 30. `dlg.sella.free_night.1.p1.wav`

*Where:* dialogue.json sella/free_night#1; part 2 of 3: narrator: She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undre… / **sella: You told me anyway,** / narrator: and nothing else, and then she sleeps.
*Played:* plain; doing: a night Sella gives; pace: slow; volume: quiet.
*Note:* The narrator's, hushed and unhurried: the one night that isn't work, so no patter. Narrator plain: the narrator never shows a feeling. Her four words are hers, said into your shoulder.

```
[plain, quietly] You told me anyway,
```
Subtitle: You told me anyway,

### 31. `dlg.sella.free_morning.0.p1.wav`

*Where:* dialogue.json sella/free_morning#0; part 2 of 2: narrator: She's still there when you wake, which she never is. / **sella: Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anythi…**
*Played:* tender, then serious; doing: a warning out of love; pace: slow; volume: quiet.
*Note:* Narrator: she's still there. A joke about Rook, soft. Then serious: the Vonnra warning. 'It's the kindest thing I've said to anyone in a year.' nearly shy.

```
[tender, then serious, quietly] Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anything up here you'd not want Vonra to hear. I mean that kindly. It's the kindest thing I've said to anyone in a year.
```
Subtitle: Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anything up here you'd not want Vonnra to hear. I mean that kindly. It's the kindest thing I've said to anyone in a year.

### 32. `dlg.sella.past.0.p1.wav`

*Where:* dialogue.json sella/past#0; part 2 of 4: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / **sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. …** / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* attentive, warm; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Narrator for her listening. Pictures it fondly. A little laugh at herself on the guess.

```
[attentive, warm, quietly] A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that. ...You know where that goes, love. You know exactly where.
```
Subtitle: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that. ...You know where that goes, love. You know exactly where.

### 33. `dlg.sella.past.0.p3.wav`

*The same words are also* `dlg.sella.past.1.p3.wav`, `dlg.sella.past.2.p5.wav`, `dlg.sella.past.3.p5.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#0; part 4 of 4: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. … / narrator: She doesn't say anything else for a while. Then: / **sella: Go on. Out. Before I start charging you for the sentiment.**
*Played:* attentive, warm; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Narrator for her listening. Pictures it fondly. A little laugh at herself on the guess.

```
[attentive, warm, quietly] Go on. Out. Before I start charging you for the sentiment.
```
Subtitle: Go on. Out. Before I start charging you for the sentiment.

### 34. `dlg.sella.past.1.p1.wav`

*Where:* dialogue.json sella/past#1; part 2 of 4: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / **sella: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with…** / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* attentive, warm; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Narrator for her listening. Teasing 'cloister rat', admiring. 'Good for you, love.'

```
[attentive, warm, quietly] A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love. ...You know where that goes, love. You know exactly where.
```
Subtitle: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love. ...You know where that goes, love. You know exactly where.

### 35. `dlg.sella.past.2.p1.wav`

*The same words are also* `dlg.sella.past.6.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#2; part 2 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / **sella: Worse company than the Kerchiefs, and you walked away from it.** / narrator: She laughs, low. / sella: Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactl… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* attentive, conspiratorial; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Narrator for her listening and her low laugh. 'Takes one to know one.'

```
[attentive, conspiratorial, quietly] Worse company than the Kerchiefs, and you walked away from it.
```
Subtitle: Worse company than the Kerchiefs, and you walked away from it.

### 36. `dlg.sella.past.2.p3.wav`

*Where:* dialogue.json sella/past#2; part 4 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Worse company than the Kerchiefs, and you walked away from it. / narrator: She laughs, low. / **sella: Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactl…** / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* attentive, conspiratorial; doing: listens to your past; pace: measured; volume: quiet.
*Note:* Narrator for her listening and her low laugh. 'Takes one to know one.'

```
[attentive, conspiratorial, quietly] Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactly where.
```
Subtitle: Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactly where.

### 37. `dlg.sella.past.3.p1.wav`

*The same words are also* `dlg.sella.past.7.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#3; part 2 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / **sella: Chapel lamps, with nobody to see them but you, and you lit them anyway.** / narrator: She's quiet a moment. / sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* moved; doing: listens to your past; pace: slow; volume: quiet.
*Note:* Narrator for her listening and her quiet. Then genuinely moved, soft.

```
[moved, quietly] Chapel lamps, with nobody to see them but you, and you lit them anyway.
```
Subtitle: Chapel lamps, with nobody to see them but you, and you lit them anyway.

### 38. `dlg.sella.past.3.p3.wav`

*Where:* dialogue.json sella/past#3; part 4 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / narrator: She's quiet a moment. / **sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.…** / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* moved; doing: listens to your past; pace: slow; volume: quiet.
*Note:* Narrator for her listening and her quiet. Then genuinely moved, soft.

```
[moved, quietly] That's the saddest thing anyone's told me up here, love, and they tell me some sad things. ...You know where that goes, love. You know exactly where.
```
Subtitle: That's the saddest thing anyone's told me up here, love, and they tell me some sad things. ...You know where that goes, love. You know exactly where.

### 39. `dlg.sella.past.4.p1.wav`

*Where:* dialogue.json sella/past#4; part 2 of 2: narrator: You tell her. She listens properly, chin on her fist, the way she does everything. / **sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. …**
*Played:* fond surprise; doing: to know them a little; pace: measured; volume: level.
*Wants:* to know them a little
*Note:* She listens properly and enjoys the picture of them young. 'I'd have guessed, but not that' is warm and slightly puzzled. What is said here may be sold, and she knows it.

```
[fond surprise] A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that.
```
Subtitle: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. ...I'd not have guessed. I'd have guessed, but not that.

### 40. `dlg.sella.past.5.p1.wav`

*Where:* dialogue.json sella/past#5; part 2 of 2: narrator: You tell her. She listens properly, chin on her fist, the way she does everything. / **sella: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with…**
*Played:* admiring warmth; doing: to approve of their escape; pace: brisk; volume: quiet.
*Wants:* to approve of their escape
*Note:* A gentle tease ('cloister rat'), then 'Good for you, love' warmly meant: she knows about getting out.

```
[admiring warmth, quietly] A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love.
```
Subtitle: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with their lens in your pocket. ...Good for you, love.

### 41. `dlg.sella.past.6.p3.wav`

*Where:* dialogue.json sella/past#6; part 4 of 4: narrator: You tell her. She listens properly, chin on her fist, the way she does everything. / sella: Worse company than the Kerchiefs, and you walked away from it. / narrator: She laughs, low. / **sella: Takes one to know one. Don't tell Rook.**
*Played:* kinship; doing: to share a secret back; pace: measured; volume: quiet.
*Wants:* to share a secret back
*Note:* The pause is her low laugh. 'Takes one to know one' hints at her own past, unexplained. 'Don't tell Rook' is a shared joke.

```
[kinship, quietly] Takes one to know one. Don't tell Rook.
```
Subtitle: Takes one to know one. Don't tell Rook.

### 42. `dlg.sella.past.7.p3.wav`

*Where:* dialogue.json sella/past#7; part 4 of 4: narrator: You tell her. She listens properly, chin on her fist, the way she does everything. / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / narrator: She's quiet a moment. / **sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.**
*Played:* moved; doing: to honour what they told her; pace: slow; volume: quiet.
*Wants:* to honour what they told her
*Note:* She is quiet a moment before the second sentence. 'Saddest thing' is said without performance; the last clause keeps it from tipping into pity.

```
[moved, quietly] That's the saddest thing anyone's told me up here, love, and they tell me some sad things.
```
Subtitle: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.

### 43. `dlg.sella.sleeptalk.0.p0.wav`

*Where:* dialogue.json sella/sleeptalk#0; part 1 of 3: **sella: You said a name. Over and over, like you'd got hold of it in the dark and didn't want to l…** / narrator: She shrugs one shoulder. / sella: Didn't catch it. I don't think you did either.
*Played:* gentle, uneasy; doing: you said a name; pace: slow; volume: quiet.
*Note:* Careful and kind. Narrator: the shrug. 'I don't think you did either.' gentle and unsettling.

```
[gentle, uneasy, quietly] You said a name. Over and over, like you'd got hold of it in the dark and didn't want to let go.
```
Subtitle: You said a name. Over and over, like you'd got hold of it in the dark and didn't want to let go.

### 44. `dlg.sella.sleeptalk.0.p2.wav`

*Where:* dialogue.json sella/sleeptalk#0; part 3 of 3: sella: You said a name. Over and over, like you'd got hold of it in the dark and didn't want to l… / narrator: She shrugs one shoulder. / **sella: Didn't catch it. I don't think you did either.**
*Played:* gentle, uneasy; doing: you said a name; pace: slow; volume: quiet.
*Note:* Careful and kind. Narrator: the shrug. 'I don't think you did either.' gentle and unsettling.

```
[gentle, uneasy, quietly] Didn't catch it. I don't think you did either.
```
Subtitle: Didn't catch it. I don't think you did either.

### 45. `dlg.sella.stairs_say.0.wav`

*Where:* dialogue.json sella/stairs_say#0
*Played:* teasing; doing: you know the stairs; pace: measured; volume: quiet.

```
[teasing, quietly] You're getting good at my stairs, love. Careful. People'll think you live here.
```
Subtitle: You're getting good at my stairs, love. Careful. People'll think you live here.

### 46. `dlg.sella.stairs_say.1.wav`

*Where:* dialogue.json sella/stairs_say#1
*Played:* dry, wicked; doing: the creaking steps; pace: measured; volume: quiet.
*Note:* The wives joke deadpan.

```
[dry, wicked, quietly] Mind the fourth. And the ninth. Rook says they're for the drunks. I say they're for the wives.
```
Subtitle: Mind the fourth. And the ninth. Rook says they're for the drunks. I say they're for the wives.

### 47. `dlg.sella.stairs_say.2.wav`

*Where:* dialogue.json sella/stairs_say#2
*Played:* warm, teasing; doing: the bath; pace: measured; volume: quiet.

```
[warm, teasing, quietly] In you go. Bath's run. It's warm, I promise. For a bit.
```
Subtitle: In you go. Bath's run. It's warm, I promise. For a bit.

### 48. `dlg.sella.stairs_room.0.p1.wav`

*The same words are also* `dlg.sella.stairs_room.4.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/stairs_room#0; part 2 of 2: narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. Your buckles take … / **sella: All that steel, and under it, look. A person.**
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.
*Note:* Plain; her words are hers.

```
[plain, quietly] All that steel, and under it, look. A person.
```
Subtitle: All that steel, and under it, look. A person.

### 49. `dlg.sella.stairs_room.1.p1.wav`

*The same words are also* `dlg.sella.stairs_room.5.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/stairs_room#1; part 2 of 2: narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. She takes your han… / **sella: Gently, upstairs. I mean it. I like this jug.**
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.

```
[plain, quietly] Gently, upstairs. I mean it. I like this jug.
```
Subtitle: Gently, upstairs. I mean it. I like this jug.

### 50. `dlg.sella.stairs_room.2.p1.wav`

*The same words are also* `dlg.sella.stairs_room.6.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/stairs_room#2; part 2 of 2: narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. She lays her palm … / **sella: Your hands are hot and the rest of you's a cellar floor. Pick one, love.**
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.
*Note:* Plain; 'cellar floor' level.

```
[plain, quietly] Your hands are hot and the rest of you's a cellar floor. Pick one, love.
```
Subtitle: Your hands are hot and the rest of you's a cellar floor. Pick one, love.

### 51. `dlg.sella.stairs_room.3.p1.wav`

*The same words are also* `dlg.sella.stairs_room.7.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/stairs_room#3; part 2 of 3: narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. She comes round be… / **sella: There. Now you know what it's like,** / narrator: and you jump. She's delighted.
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.

```
[plain, quietly] There. Now you know what it's like,
```
Subtitle: There. Now you know what it's like,

### 52. `dlg.sella.stairs_rules.0.p1.wav`

*Where:* dialogue.json sella/stairs_rules#0; part 2 of 2: narrator: In the bath she slides her hands down your arms, and stops. Under the warm water you are c… / **sella: ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say …**
*Played:* shaken, then professional; doing: you're cold as the river; pace: slow; volume: quiet.
*Note:* Narrator through the cold, long and quiet. Then her rules, steadying herself with the patter.

```
[shaken, then professional, quietly] ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder.
```
Subtitle: ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder.

### 53. `dlg.sella.stairs_rules.1.wav`

*Where:* dialogue.json sella/stairs_rules#1
*Played:* frank, wry; doing: her rules; pace: measured; volume: quiet.
*Note:* The deaf-ear joke deadpan.

```
[frank, wry, quietly] Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder; Rook's walls are thin, but she's deaf in the left ear.
```
Subtitle: Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder; Rook's walls are thin, but she's deaf in the left ear.

### 54. `dlg.sella.stop_paid.0.p1.wav`

*Where:* dialogue.json sella/stop_paid#0; part 2 of 4: narrator: She sits back on her heels, and doesn't sulk, and doesn't ask why. / **sella: Then I'll have the bath. It's paid for.** / narrator: She counts thirteen coins back into your palm and closes your fingers on them. / sella: Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or …
*Played:* graceful, kind; doing: you stop; pace: measured; volume: quiet.
*Note:* Narrator: no sulk. Practical with the coins. 'Either's all right, love.' meant.

```
[graceful, kind, quietly] Then I'll have the bath. It's paid for.
```
Subtitle: Then I'll have the bath. It's paid for.

### 55. `dlg.sella.stop_paid.0.p3.wav`

*Where:* dialogue.json sella/stop_paid#0; part 4 of 4: narrator: She sits back on her heels, and doesn't sulk, and doesn't ask why. / sella: Then I'll have the bath. It's paid for. / narrator: She counts thirteen coins back into your palm and closes your fingers on them. / **sella: Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or …**
*Played:* graceful, kind; doing: you stop; pace: measured; volume: quiet.
*Note:* Narrator: no sulk. Practical with the coins. 'Either's all right, love.' meant.

```
[graceful, kind, quietly] Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or you won't. Either's all right, love. Go on.
```
Subtitle: Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or you won't. Either's all right, love. Go on.

### 56. `dlg.sella.rest_night.0.p0.wav`

*The same words are also* `dlg.sella.rest_night_paid.0.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/rest_night#0; part 1 of 3: **sella: Sleep.** / narrator: She looks at you as if you'd asked her to recite something in a foreign tongue. / sella: You've paid fifteen gold to sleep.
*Played:* baffled amusement; doing: you paid to sleep; pace: measured; volume: quiet.
*Note:* Narrator for the look. Incredulous.

```
[baffled amusement, quietly] Sleep.
```
Subtitle: Sleep.

### 57. `dlg.sella.rest_night.0.p2.wav`

*The same words are also* `dlg.sella.rest_night_paid.0.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/rest_night#0; part 3 of 3: sella: Sleep. / narrator: She looks at you as if you'd asked her to recite something in a foreign tongue. / **sella: You've paid fifteen gold to sleep.**
*Played:* baffled amusement; doing: you paid to sleep; pace: measured; volume: quiet.
*Note:* Narrator for the look. Incredulous.

```
[baffled amusement, quietly] You've paid fifteen gold to sleep.
```
Subtitle: You've paid fifteen gold to sleep.

### 58. `dlg.sella.rest_bed.0.wav`

*Where:* dialogue.json sella/rest_bed#0
*Played:* bossy, wry; doing: lie down, then; pace: brisk; volume: quiet.
*Note:* Rapid little orders; the chair line dry.

```
[bossy, wry, quietly] ...Lie down, then. No. Boots off; Rook'll have my hide. Shift over. I'm not sitting up all night in a chair. I've done that for worse money.
```
Subtitle: ...Lie down, then. No. Boots off; Rook'll have my hide. Shift over. I'm not sitting up all night in a chair. I've done that for worse money.

### 59. `dlg.sella.rest_morning.0.p1.wav`

*Where:* dialogue.json sella/rest_morning#0; part 2 of 2: narrator: She's sitting on the edge of the bed with her hand flat on your chest. / **sella: You were cold as the river all night. Like lying next to a stone. And now look at you: war…**
*Played:* unsettled, then fond; doing: you were cold all night; pace: slow; volume: quiet.
*Note:* Narrator: her hand on your chest. Quiet wonder at the cold. Then warm and wry: 'Best money I ever made.'

```
[unsettled, then fond, quietly] You were cold as the river all night. Like lying next to a stone. And now look at you: warm as toast. ...Fifteen gold to lie awake next to a stone. Best money I ever made. Don't tell anyone.
```
Subtitle: You were cold as the river all night. Like lying next to a stone. And now look at you: warm as toast. ...Fifteen gold to lie awake next to a stone. Best money I ever made. Don't tell anyone.

### 60. `dlg.sella.rest_morning.1.p0.wav`

*Where:* dialogue.json sella/rest_morning#1; part 1 of 3: **sella: Fifteen gold to watch you snore. Best money I ever made.** / narrator: She's already dressed. She doesn't count it. / sella: Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.
*Played:* fond, teasing; doing: best money; pace: measured; volume: quiet.
*Note:* Narrator: she doesn't count it. 'Rich and bored.' a grin.

```
[fond, teasing, quietly] Fifteen gold to watch you snore. Best money I ever made.
```
Subtitle: Fifteen gold to watch you snore. Best money I ever made.

### 61. `dlg.sella.rest_morning.1.p2.wav`

*Where:* dialogue.json sella/rest_morning#1; part 3 of 3: sella: Fifteen gold to watch you snore. Best money I ever made. / narrator: She's already dressed. She doesn't count it. / **sella: Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.**
*Played:* fond, teasing; doing: best money; pace: measured; volume: quiet.
*Note:* Narrator: she doesn't count it. 'Rich and bored.' a grin.

```
[fond, teasing, quietly] Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.
```
Subtitle: Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.

### 62. `dlg.sella.door.0.p0.wav`

*Where:* dialogue.json sella/door#0; part 1 of 3: **sella: That? It's Rook's.** / narrator: She sits on the bed to do up her boots, and doesn't look up. / sella: Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funn…
*Played:* matter-of-fact, guarded; doing: the bolt and Rook; pace: measured; volume: quiet.
*Note:* Narrator: her boots. Plain about danger; 'I'll not say which.' closed.

```
[matter-of-fact, guarded, quietly] That? It's Rook's.
```
Subtitle: That? It's Rook's.

### 63. `dlg.sella.door.0.p2.wav`

*Where:* dialogue.json sella/door#0; part 3 of 3: sella: That? It's Rook's. / narrator: She sits on the bed to do up her boots, and doesn't look up. / **sella: Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funn…**
*Played:* matter-of-fact, guarded; doing: the bolt and Rook; pace: measured; volume: quiet.
*Note:* Narrator: her boots. Plain about danger; 'I'll not say which.' closed.

```
[matter-of-fact, guarded, quietly] Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funny she's up those stairs before he's finished turning. I've needed her twice in seven years. Once for a drover. Once for one of the Watch, and I'll not say which. ...So, no. I've never shot it. It's not my door. Nothing in here's my door.
```
Subtitle: Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funny she's up those stairs before he's finished turning. I've needed her twice in seven years. Once for a drover. Once for one of the Watch, and I'll not say which. ...So, no. I've never shot it. It's not my door. Nothing in here's my door.

### 64. `dlg.sella.door_years.0.p0.wav`

*Where:* dialogue.json sella/door_years#0; part 1 of 3: **sella: Twenty-two, and sure I was cleverer than everyone in the valley. I was right about most of…** / narrator: She laughs, low. / sella: I'm twenty-nine, love, since you're doing sums. Seven years at the top of Rook's stairs, a…
*Played:* wry, warm; doing: her years; pace: measured; volume: quiet.
*Note:* Narrator: a low laugh. Self-mocking.

```
[wry, warm, quietly] Twenty-two, and sure I was cleverer than everyone in the valley. I was right about most of them.
```
Subtitle: Twenty-two, and sure I was cleverer than everyone in the valley. I was right about most of them.

### 65. `dlg.sella.door_years.0.p2.wav`

*Where:* dialogue.json sella/door_years#0; part 3 of 3: sella: Twenty-two, and sure I was cleverer than everyone in the valley. I was right about most of… / narrator: She laughs, low. / **sella: I'm twenty-nine, love, since you're doing sums. Seven years at the top of Rook's stairs, a…**
*Played:* wry, warm; doing: her years; pace: measured; volume: quiet.
*Note:* Narrator: a low laugh. Self-mocking.

```
[wry, warm, quietly] I'm twenty-nine, love, since you're doing sums. Seven years at the top of Rook's stairs, and I've only fallen down them twice.
```
Subtitle: I'm twenty-nine, love, since you're doing sums. Seven years at the top of Rook's stairs, and I've only fallen down them twice.

### 66. `dlg.sella.door_south.0.p0.wav`

*Where:* dialogue.json sella/door_south#0; part 1 of 3: **sella: I told you. A house in the south. A door that locks from the inside.** / narrator: She stands, and checks her hair in the jug, and doesn't look at you. / sella: And somebody who knocks.
*Played:* wistful, guarded; doing: the house in the south; pace: slow; volume: quiet.
*Note:* Narrator: she checks her hair, not looking at you. 'And somebody who knocks.' quiet.

```
[wistful, guarded, quietly] I told you. A house in the south. A door that locks from the inside.
```
Subtitle: I told you. A house in the south. A door that locks from the inside.

### 67. `dlg.sella.door_south.0.p2.wav`

*Where:* dialogue.json sella/door_south#0; part 3 of 3: sella: I told you. A house in the south. A door that locks from the inside. / narrator: She stands, and checks her hair in the jug, and doesn't look at you. / **sella: And somebody who knocks.**
*Played:* wistful, guarded; doing: the house in the south; pace: slow; volume: quiet.
*Note:* Narrator: she checks her hair, not looking at you. 'And somebody who knocks.' quiet.

```
[wistful, guarded, quietly] And somebody who knocks.
```
Subtitle: And somebody who knocks.

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

### 72. `dlg.sella.free_door.0.p0.wav`

*Where:* dialogue.json sella/free_door#0; part 1 of 3: **sella: I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd he…** / narrator: She shakes her head. / sella: Nobody does that. Nobody's ever done that.
*Played:* moved, wondering; doing: nobody does that; pace: slow; volume: quiet.
*Note:* Quiet, wondering.

```
[moved, wondering, quietly] I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd hear it by morning.
```
Subtitle: I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd hear it by morning.

### 73. `dlg.sella.free_door.0.p2.wav`

*Where:* dialogue.json sella/free_door#0; part 3 of 3: sella: I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd he… / narrator: She shakes her head. / **sella: Nobody does that. Nobody's ever done that.**
*Played:* moved, wondering; doing: nobody does that; pace: slow; volume: quiet.
*Note:* Quiet, wondering.

```
[moved, wondering, quietly] Nobody does that… Nobody's ever done that.
```
Subtitle: Nobody does that. Nobody's ever done that.

### 74. `dlg.sella.free_door.1.wav`

*Where:* dialogue.json sella/free_door#1
*Played:* nervous, honest; doing: she doesn't know how; pace: slow; volume: quiet.
*Note:* A small laugh at her own lie.

```
[nervous, honest, quietly] I don't know how to do this one. ...That's a lie. I know how. I don't know how to do it like this.
```
Subtitle: I don't know how to do this one. ...That's a lie. I know how. I don't know how to do it like this.

### 75. `dlg.sella.free_want.0.p0.wav`

*Where:* dialogue.json sella/free_want#0; part 1 of 3: **sella: Ask me that again and I'll cry, and I don't cry, so don't.** / narrator: She takes a breath. / sella: Yes. ...Yes. There. Said it. Come here.
*Played:* near tears, then decided; doing: yes; pace: slow; volume: quiet.
*Note:* Narrator: the breath. 'Yes.' twice, the second firmer. 'Come here.' soft.

```
[near tears, then decided, quietly] Ask me that again and I'll cry, and I don't cry, so don't.
```
Subtitle: Ask me that again and I'll cry, and I don't cry, so don't.

### 76. `dlg.sella.free_want.0.p2.wav`

*Where:* dialogue.json sella/free_want#0; part 3 of 3: sella: Ask me that again and I'll cry, and I don't cry, so don't. / narrator: She takes a breath. / **sella: Yes. ...Yes. There. Said it. Come here.**
*Played:* near tears, then decided; doing: yes; pace: slow; volume: quiet.
*Note:* Narrator: the breath. 'Yes.' twice, the second firmer. 'Come here.' soft.

```
[near tears, then decided, quietly] Yes. ...Yes. There. Said it. Come here.
```
Subtitle: Yes. ...Yes. There. Said it. Come here.

### 77. `dlg.sella.free_stop.0.p1.wav`

*Where:* dialogue.json sella/free_stop#0; part 2 of 4: narrator: She lets out a breath she's been holding since the stairs. / **sella: All right.** / narrator: And it is; you can see it is. / sella: All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'…
*Played:* relief, tender; doing: just sit; pace: slow; volume: quiet.
*Note:* Narrator: the held breath. The Rook joke soft.

```
[relief, tender, quietly] All right.
```
Subtitle: All right.

### 78. `dlg.sella.free_stop.0.p3.wav`

*Where:* dialogue.json sella/free_stop#0; part 4 of 4: narrator: She lets out a breath she's been holding since the stairs. / sella: All right. / narrator: And it is; you can see it is. / **sella: All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'…**
*Played:* relief, tender; doing: just sit; pace: slow; volume: quiet.
*Note:* Narrator: the held breath. The Rook joke soft.

```
[relief, tender, quietly] All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'd think we'd died.
```
Subtitle: All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'd think we'd died.

### 79. `dlg.sella.free_sleep.0.p1.wav`

*Where:* dialogue.json sella/free_sleep#0; part 2 of 2: narrator: She laughs, properly, the first time tonight. / **sella: You and your sleeping. ...Yes. All right. Yes.**
*Played:* delighted, shy; doing: yes, sleep; pace: measured; volume: quiet.
*Note:* Narrator: a proper laugh.

```
[delighted, shy, quietly] You and your sleeping. ...Yes. All right. Yes.
```
Subtitle: You and your sleeping. ...Yes. All right. Yes.

### 80. `dlg.sella.free_bolt.0.p1.wav`

*Where:* dialogue.json sella/free_bolt#0; part 2 of 2: narrator: She reaches behind her without looking and finds the bolt. It sticks halfway; nobody has e… / **sella: ...There.**
*Played:* plain; doing: the bolt; pace: slow; volume: quiet.
*Note:* Plain; her word is hers.

```
[plain, quietly] ...There.
```
Subtitle: ...There.

### 81. `dlg.sella.free_m_downstairs.0.p1.wav`

*Where:* dialogue.json sella/free_m_downstairs#0; part 2 of 2: narrator: She laughs. / **sella: Downstairs Rook hears everything and charges nobody. You'd be better off with me. ...No. Y…**
*Played:* wry, then honest; doing: go on; pace: measured; volume: quiet.
*Note:* Narrator: she laughs. The turn 'No. You wouldn't.' honest.

```
[wry, then honest, quietly] Downstairs Rook hears everything and charges nobody. You'd be better off with me. ...No. You wouldn't. That's the point, love. Go on.
```
Subtitle: Downstairs Rook hears everything and charges nobody. You'd be better off with me. ...No. You wouldn't. That's the point, love. Go on.

### 82. `dlg.sella.free_m_who.0.p0.wav`

*Where:* dialogue.json sella/free_m_who#0; part 1 of 3: **sella: You know who. Everybody pays; she pays most.** / narrator: She pulls the quilt up to her chin. / sella: I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don'…
*Played:* honest, uncomfortable; doing: Vonnra pays; pace: slow; volume: quiet.
*Note:* Narrator: the quilt. Her honesty stumbling; a beat where the name would be.

```
[honest, uncomfortable, quietly] You know who. Everybody pays; she pays most.
```
Subtitle: You know who. Everybody pays; she pays most.

### 83. `dlg.sella.free_m_who.0.p2.wav`

*Where:* dialogue.json sella/free_m_who#0; part 3 of 3: sella: You know who. Everybody pays; she pays most. / narrator: She pulls the quilt up to her chin. / **sella: I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don'…**
*Played:* honest, uncomfortable; doing: Vonnra pays; pace: slow; volume: quiet.
*Note:* Narrator: the quilt. Her honesty stumbling; a beat where the name would be.

```
[honest, uncomfortable, quietly] I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don't know. That's the honest answer, and I'm out of practice at those. Don't make me practise before breakfast.
```
Subtitle: I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don't know. That's the honest answer, and I'm out of practice at those. Don't make me practise before breakfast.

### 84. `dlg.sella.free_m_kiss.0.p1.wav`

*Where:* dialogue.json sella/free_m_kiss#0; part 2 of 3: narrator: She lets you. Then she pushes you off by the face, gently, with the flat of her hand. / **sella: Out. Before I get used to it.** / narrator: She's smiling. She doesn't stop smiling until you're down the stairs, and you know that be…
*Played:* plain; doing: out; pace: measured; volume: quiet.
*Note:* Plain; her words are hers.

```
[plain, quietly] Out. Before I get used to it.
```
Subtitle: Out. Before I get used to it.

### 85. `dlg.sella.refuse_roost.0.p1.wav`

*Where:* dialogue.json sella/refuse_roost#0; part 2 of 4: narrator: At the top of the stairs she stops with her hand on the door. / **sella: They're saying you burned the Roost with folk still in it.** / narrator: She puts the coins back in your hand, all of them. / sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…
*Played:* cool, firm; doing: she won't work tonight; pace: slow; volume: quiet.
*Note:* Narrator at the door and the coins. Cool, not cruel. 'Come back when I can't.' quiet.

```
[cool, firm, quietly] They're saying you burned the Roost with folk still in it.
```
Subtitle: They're saying you burned the Roost with folk still in it.

### 86. `dlg.sella.refuse_roost.0.p3.wav`

*Where:* dialogue.json sella/refuse_roost#0; part 4 of 4: narrator: At the top of the stairs she stops with her hand on the door. / sella: They're saying you burned the Roost with folk still in it. / narrator: She puts the coins back in your hand, all of them. / **sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…**
*Played:* cool, firm; doing: she won't work tonight; pace: slow; volume: quiet.
*Note:* Narrator at the door and the coins. Cool, not cruel. 'Come back when I can't.' quiet.

```
[cool, firm, quietly] I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working with that in the room. ...Come back when I can't.
```
Subtitle: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working with that in the room. ...Come back when I can't.

### 87. `dlg.sella.say_keegan.0.wav`

*Where:* dialogue.json sella/say_keegan#0
*Played:* delighted gossip; doing: Keegan's list; pace: measured; volume: level.
*Note:* Teasing; 'the whole chapter' mock-doom.

```
[delighted gossip] The knight's been asking Rook what you like for breakfast. In full sentences, love. With a list. ...She's going to read you a chapter after. You know that. You'll have to sit through the whole chapter.
```
Subtitle: The knight's been asking Rook what you like for breakfast. In full sentences, love. With a list. ...She's going to read you a chapter after. You know that. You'll have to sit through the whole chapter.

### 88. `dlg.sella.say_rav.0.wav`

*Where:* dialogue.json sella/say_rav#0
*Played:* fond, frank; doing: be kind to Rav; pace: measured; volume: quiet.
*Note:* 'He's softer than he drinks.' gentle.

```
[fond, frank, quietly] You went round the back of the Flagon after closing. Rav's been up my stairs twice in seven years, and both times to lance something. Be kind to him. He's softer than he drinks.
```
Subtitle: You went round the back of the Flagon after closing. Rav's been up my stairs twice in seven years, and both times to lance something. Be kind to him. He's softer than he drinks.

## Said in passing

### 89. `bark.sella.day.0.wav`

*Where:* npcs.json sella.barks[0]
*Played:* amused; pace: measured; volume: level.

```
[amused] Buy a girl a drink? No? Buy yourself one, then. You look like you need it.
```
Subtitle: Buy a girl a drink? No? Buy yourself one, then. You look like you need it.

### 90. `bark.sella.day.1.wav`

*Where:* npcs.json sella.barks[1]
*Played:* amused; pace: measured; volume: level.

```
[amused] You've got road on you. I can smell it from here.
```
Subtitle: You've got road on you. I can smell it from here.

### 91. `bark.sella.day.2.wav`

*Where:* npcs.json sella.barks[2]
*Played:* amused; pace: measured; volume: level.

```
[amused] Rook's stew or my company. Only one of them's warm.
```
Subtitle: Rook's stew or my company. Only one of them's warm.

### 92. `bark.sella.night.0.wav`

*Where:* npcs.json sella.nightBarks[0]
*Played:* teasing; pace: measured; volume: quiet.

```
[teasing, quietly] Cold night to sleep alone, love.
```
Subtitle: Cold night to sleep alone, love.

### 93. `bark.sella.night.1.wav`

*Where:* npcs.json sella.nightBarks[1]
*Played:* teasing; pace: measured; volume: quiet.

```
[teasing, quietly] Rook's walls are thin. Just so you know.
```
Subtitle: Rook's walls are thin. Just so you know.

### 94. `bark.sella.night.2.wav`

*Where:* npcs.json sella.nightBarks[2]
*Played:* teasing; pace: measured; volume: quiet.

```
[teasing, quietly] The blue room's got a lamp lit. Guess who's in it.
```
Subtitle: The blue room's got a lamp lit. Guess who's in it.

### 95. `bark.sella.night.3.wav`

*Where:* npcs.json sella.nightBarks[3]
*Played:* teasing; pace: measured; volume: quiet.

```
[teasing, quietly] Rook's walls are thin and I'm not quiet. Fair warning.
```
Subtitle: Rook's walls are thin and I'm not quiet. Fair warning.


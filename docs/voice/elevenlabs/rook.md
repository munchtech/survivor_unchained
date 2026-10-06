# Mother Rook: ElevenLabs packet

Voice id in the game: `rook`. 54 takes to record (6,561 characters; about 19,683 credits at three tries a line). Status: **final** (the story lead, 2026-10-03): record it.

## Who they are

**Mother Rook** (the Last Lamp). Short sentences, bossy imperatives, kindness said sideways ("Sit down before you fall down"). Yorkshire turns: "love" is Sella's, Rook's is "pet". Counts beds and debts; knows everyone's business and admits to most of it. Never says please, never says sorry, never cries in front of anyone. Laughs on the out-breath. *Casting:* 60, Yorkshire, warm, dry, bossy.

*Wants:* the inn kept and everyone fed. *Hides:* she has sold every traveller on the ford road to Vonnra, and watched the carters go down it and not come back.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Mother Rook`. Never describe a voice as sounding like a real person.

```
Native English (British, Yorkshire). Female, 60s. Studio quality. Persona: a Yorkshire innkeeper. A sixty-year-old innkeeper from Yorkshire in the north of England, with a broad, flat northern Yorkshire accent: short 'a' sounds, 'love' rhymes with 'good'. A warm, husky, lived-in alto. Dry, brisk and bossy, kind underneath, quick to a dry laugh on the out-breath. Broad Yorkshire accent. No reverb or effects.
```

Preview text:

```
Another one off the Low Ford road. I'm Rook, and this is the Last Lamp: bed, bread, a bath if you ask nicely, and a strongroom for what you'd rather not carry about.
```

In the Voice Library instead: search for *Yorkshire*, *female*, *60*, and listen for this: A sixty-year-old innkeeper from Yorkshire in the north of England, with a broad, flat northern Yorkshire accent: short 'a' sounds, 'love' rhymes with 'good'. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.rook.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice rook
```

## Saying the names

The text to paste already respells these; keep the respelling: Brannoc as *Brannock*, Maeca as *Mayka*, Penhale as *Pen-hale*, Penhales as *Pen-hales*, Vonnra as *Vonra*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Rook

### 1. `dlg.rook.first.0.wav`

*Where:* dialogue.json rook/first#0
*Played:* dry, brisk, kind underneath; doing: takes charge of a bloodied stranger; pace: brisk; volume: level.
*Wants:* to take charge of you, and to see who you are
*Hides:* Vonnra pays her for news of Low Ford arrivals, double for this one
*Note:* 'Well.' a beat, looking you over: partly for Vonnra's money, and the kindness is real as well. On the Chid sentence she watches your face for how you take 'blue lights going out'. A dry edge on 'bleeding on my step'. No laugh at the end: a breath, and the warmth is in the order itself.

```
[dry, brisk, kind underneath] Well… The one who walked up from the Low Ford at dawn. Chid came in babbling about blue lights going out at the crossing, and here you are, bleeding on my step. I'm Rook. This is the Last Lamp. [inhales] Sit down before you fall down.
```
Subtitle: Well. The one who walked up from the Low Ford at dawn. Chid came in babbling about blue lights going out at the crossing, and here you are, bleeding on my step. I'm Rook. This is the Last Lamp. Sit down before you fall down.

### 2. `dlg.rook.first.1.wav`

*Where:* dialogue.json rook/first#1
*Played:* brisk, businesslike; doing: sells you a bed; pace: brisk; volume: level.
*Wants:* your custom
*Note:* A list she has said a thousand times; a dry twinkle on 'if you ask nicely'.

```
[brisk, businesslike] Another one off the Low Ford road. I'm Rook, and this is the Last Lamp: bed, bread, a bath if you ask nicely, and a strongroom for what you'd rather not carry about.
```
Subtitle: Another one off the Low Ford road. I'm Rook, and this is the Last Lamp: bed, bread, a bath if you ask nicely, and a strongroom for what you'd rather not carry about.

### 3. `dlg.rook.hub.0.wav`

*Where:* dialogue.json rook/hub#0
*Played:* tired, dry, fond; doing: late-night welcome; pace: measured; volume: quiet.
*Note:* Night-time voice, lower. Dry joke: stew's cold, beds aren't.

```
[tired, dry, fond, quietly] Late. Stew's cold. Beds aren't.
```
Subtitle: Late. Stew's cold. Beds aren't.

### 4. `dlg.rook.hub.1.wav`  **RE-RECORD: the words changed**

*Where:* dialogue.json rook/hub#1
*Played:* gruff fondness; doing: she saved you food; pace: measured; volume: quiet.
*Note:* Conspiratorial on 'Don't tell the others.' Kindness said sideways.

```
[gruff fondness, quietly] There you are. I kept a bowl back. The others can whistle.
```
Subtitle: There you are. I kept a bowl back. The others can whistle.

### 5. `dlg.rook.hub.2.wav`

*Where:* dialogue.json rook/hub#2
*Played:* brisk, friendly; doing: what do you want; pace: brisk; volume: level.
*Note:* Busy; wiping a cup.

```
[brisk, friendly] Back again. What'll it be?
```
Subtitle: Back again. What'll it be?

### 6. `dlg.rook.rumours.0.wav`

*Where:* dialogue.json rook/rumours#0
*Played:* dry, gossipy, then uneasy; doing: the town's news, and a strange dog; pace: measured; volume: level.
*Note:* Wry tally of who's counting what. The dog story slows and darkens: 'whines at the floor' uneasy; 'won't be told' firm.

```
[dry, gossipy, then uneasy] Nothing you don't know already, pet; you did half of it. Holloway's counting what's left, Harlan's counting what came back, and the Pen-hales say their dog won't go in the barn any more. Stands at the door and whines at the floor, and won't be told.
```
Subtitle: Nothing you don't know already, pet; you did half of it. Holloway's counting what's left, Harlan's counting what came back, and the Penhales say their dog won't go in the barn any more. Stands at the door and whines at the floor, and won't be told.

### 7. `dlg.rook.rumours.1.wav`

*Where:* dialogue.json rook/rumours#1
*Played:* dry amusement; doing: news of the cure; pace: measured; volume: level.
*Note:* Pleased; mock-scorn on Holloway sulking. 'mind' Yorkshire, a gentle reminder.

```
[dry amusement] Wenna says the stream's running clean. The wolves have gone quiet, and Holloway's sulking because there's nobody left to pay. Harlan's still asking after his boy, mind.
```
Subtitle: Wenna says the stream's running clean. The wolves have gone quiet, and Holloway's sulking because there's nobody left to pay. Harlan's still asking after his boy, mind.

### 8. `dlg.rook.rumours.2.wav`

*Where:* dialogue.json rook/rumours#2
*Played:* flat, disapproving; doing: news of the slaughter; pace: measured; volume: level.
*Note:* 'None.' flat and pointed. 'Make of that what you like.' cool.

```
[flat, disapproving] No wolves on the road now. None. Brannoc's never seen so many pelts, and Mayka hasn't been in since. Make of that what you like. Harlan's still asking after his boy.
```
Subtitle: No wolves on the road now. None. Brannoc's never seen so many pelts, and Maeca hasn't been in since. Make of that what you like. Harlan's still asking after his boy.

### 9. `dlg.rook.rumours.3.wav`

*Where:* dialogue.json rook/rumours#3
*Played:* dry, gossipy; doing: news, and a debt; pace: measured; volume: level.
*Note:* Dry wit on 'which is how you know it's settled'. Grievance on Jessop's unpaid rounds.

```
[dry, gossipy] The wolves are settled, one way or another, and nobody's thanked anybody for it, which is how you know it's settled. Harlan's still asking after his boy, mind. And Jessop, the toll clerk, owes me for three rounds and hasn't been back to pay.
```
Subtitle: The wolves are settled, one way or another, and nobody's thanked anybody for it, which is how you know it's settled. Harlan's still asking after his boy, mind. And Jessop, the toll clerk, owes me for three rounds and hasn't been back to pay.

### 10. `dlg.rook.rumours.4.wav`

*Where:* dialogue.json rook/rumours#4
*Played:* warm, wry; doing: news of Jory's return; pace: brisk; volume: level.
*Note:* Warmth for Jory; exasperated fondness for Harlan. 'Pick one.' dry.

```
[warm, wry] Jory Coyle's home, asleep in my good room with the lamp lit, and Harlan's been up my stairs four times to look at him. The wolves are another matter: Holloway's paying for pelts, Mayka says they're sick, and the Pen-hale boy says they drink from the stream and fall down. Pick one.
```
Subtitle: Jory Coyle's home, asleep in my good room with the lamp lit, and Harlan's been up my stairs four times to look at him. The wolves are another matter: Holloway's paying for pelts, Maeca says they're sick, and the Penhale boy says they drink from the stream and fall down. Pick one.

### 11. `dlg.rook.rumours.5.wav`

*Where:* dialogue.json rook/rumours#5
*Played:* subdued, weary; doing: Harlan's grief; pace: measured; volume: quiet.
*Note:* Hurt that he won't open even to her. Tired on 'I've stopped asking.'

```
[subdued, weary, quietly] Harlan's shut his shutters and won't open the door, not even to me. And the wolves are still at it: Holloway's paying for pelts, Mayka says they're sick. Don't ask me which. I've stopped asking.
```
Subtitle: Harlan's shut his shutters and won't open the door, not even to me. And the wolves are still at it: Holloway's paying for pelts, Maeca says they're sick. Don't ask me which. I've stopped asking.

### 12. `dlg.rook.rumours.6.wav`

*Where:* dialogue.json rook/rumours#6
*Played:* gossipy, sly; doing: the town's stories; pace: brisk; volume: level.
*Note:* Rattling through the rumours, then lower and knowing about Jessop's money. 'Pick a story.' dry.

```
[gossipy, sly] Wolves, mainly. Holloway's paying for pelts, Mayka says they're sick, Harlan says they ate his caravan, and the Coyle boy's still missing. And Jessop, the toll clerk, was buying rounds at the Flagon like he'd come into money, the night the wagons went. Pick a story.
```
Subtitle: Wolves, mainly. Holloway's paying for pelts, Maeca says they're sick, Harlan says they ate his caravan, and the Coyle boy's still missing. And Jessop, the toll clerk, was buying rounds at the Flagon like he'd come into money, the night the wagons went. Pick a story.

### 13. `dlg.rook.clerk.0.wav`

*Where:* dialogue.json rook/clerk#0
*Played:* knowing, aggrieved; doing: Jessop's suspicious night; pace: measured; volume: level.
*Note:* Mimic his 'done somebody a favour' with scorn. 'Rav's always there.' dry. Pause, then the debt, still annoyed.

```
[knowing, aggrieved] Clerks don't buy rounds. Jessop bought three, the night Coyle's wagons went missing, and kept telling the room he'd "done somebody a favour". Rav was there; Rav's always there. ...Jessop's not been in since. He still owes me for the third.
```
Subtitle: Clerks don't buy rounds. Jessop bought three, the night Coyle's wagons went missing, and kept telling the room he'd "done somebody a favour". Rav was there; Rav's always there. ...Jessop's not been in since. He still owes me for the third.

### 14. `dlg.rook.town.0.wav`

*Where:* dialogue.json rook/town#0
*Played:* brisk, wry; doing: the lay of the land; pace: brisk; volume: level.
*Note:* Pointing out roads. Comic weariness on 'at length'. Last line dry.

```
[brisk, wry] Three roads meet here, and everyone on them stops at my door. South's the Low Ford. East's the Old Road and the Verge. North's shut, and a girl in shiny armour will tell you why, at length. Everybody else you'll meet whether you want to or not.
```
Subtitle: Three roads meet here, and everyone on them stops at my door. South's the Low Ford. East's the Old Road and the Verge. North's shut, and a girl in shiny armour will tell you why, at length. Everybody else you'll meet whether you want to or not.

### 15. `dlg.rook.runs.0.wav`

*Where:* dialogue.json rook/runs#0
*Played:* sly, amused; doing: who really runs the town; pace: measured; volume: level.
*Note:* Three verdicts, each drier. 'with interest' disdain. Laugh on the out-breath on 'draw your own conclusions'.

```
[sly, amused] Holloway thinks he does. Vonra knows she does. Pell's got it written down in a book somewhere, with interest. And I feed all three of them, so you can draw your own conclusions.
```
Subtitle: Holloway thinks he does. Vonnra knows she does. Pell's got it written down in a book somewhere, with interest. And I feed all three of them, so you can draw your own conclusions.

### 16. `dlg.rook.ford.0.wav`

*Where:* dialogue.json rook/ford#0
*Played:* candid, unrepentant; doing: admits she reports on travellers; pace: measured; volume: quiet.
*Note:* Lower after the pause, honest. 'Don't look like that, pet' brisk and unrepentant on top, and she changes the subject fast.

```
[candid, unrepentant, quietly] Not many, this last year. The ford's been bad since the winter. ...Vonra pays me to tell her who comes up that road, and when… Don't look like that, pet; she pays everyone for something. I'd told her about you before you'd finished your stew.
```
Subtitle: Not many, this last year. The ford's been bad since the winter. ...Vonnra pays me to tell her who comes up that road, and when. Don't look like that, pet; she pays everyone for something. I'd told her about you before you'd finished your stew.

### 17. `dlg.rook.ford2.0.wav`

*Where:* dialogue.json rook/ford2#0
*Played:* uneasy; doing: Vonnra paid double for you; pace: slow; volume: quiet.
*Note:* 'She's never paid me double for anything.' is more than she meant to say. Then she's busy with a cup.

```
[uneasy, quietly] Nothing. She paid me double. She's never paid me double for anything.
```
Subtitle: Nothing. She paid me double. She's never paid me double for anything.

### 18. `dlg.rook.firstlamp.0.wav`

*Where:* dialogue.json rook/firstlamp#0
*Played:* fond pride, then firm; doing: the story of the inn's name; pace: measured; volume: level.
*Note:* Telling a town legend she loves. Softer on 'the last one lit'. 'Just leave him where he lies.' firm and protective.

```
[fond pride, then firm] You found old Ashe, and his trunk. Captain of the first Watch, when it was forty lamps and not four. This inn's named for his: the Last Lamp, because it was the last one lit the night they closed the north road. We light the hearth from it every winter. Keep what was in the trunk; he'd have wanted it used. Just leave him where he lies.
```
Subtitle: You found old Ashe, and his trunk. Captain of the first Watch, when it was forty lamps and not four. This inn's named for his: the Last Lamp, because it was the last one lit the night they closed the north road. We light the hearth from it every winter. Keep what was in the trunk; he'd have wanted it used. Just leave him where he lies.

### 19. `dlg.rook.c.0.wav`

*Where:* dialogue.json rook/c#0
*Played:* puzzled, curious; doing: the note's initial is wrong; pace: measured; volume: quiet.
*Note:* 'owt' rhymes with 'out'. Slows, thinking. 'Now there's a thing.' intrigued.

```
[puzzled, curious, quietly] Was it? Ashe was Ashe, all his life; never heard him called owt else. ...Somebody else's note, then, in a dead man's trunk. Now there's a thing.
```
Subtitle: Was it? Ashe was Ashe, all his life; never heard him called owt else. ...Somebody else's note, then, in a dead man's trunk. Now there's a thing.

### 20. `dlg.rook.lamp.0.wav`

*Where:* dialogue.json rook/lamp#0
*Played:* proud, then wry; doing: the lamp's story, and Chid; pace: measured; volume: level.
*Note:* Pride on her mother. Brisk instruction about Chid. 'Lord knows he doesn't.' dry, fond.

```
[proud, then wry] It is. My mother carried it up from the chapel the year the Order left, and it's not gone out since. You've one too, I see. Go and see Chid. He needs somebody who knows what the light's for. Lord knows he doesn't.
```
Subtitle: It is. My mother carried it up from the chapel the year the Order left, and it's not gone out since. You've one too, I see. Go and see Chid. He needs somebody who knows what the light's for. Lord knows he doesn't.

### 21. `dlg.rook.wanted.0.wav`

*Where:* dialogue.json rook/wanted#0
*Played:* sharp, protective; doing: warns you off trouble; pace: brisk; volume: quiet.
*Note:* Low so the room doesn't hear. Dry on 'which is true'. Firm last sentence.

```
[sharp, protective, quietly] Holloway's men were in asking after you. I told them you owed me money, which is true. Don't bring trouble under my roof.
```
Subtitle: Holloway's men were in asking after you. I told them you owed me money, which is true. Don't bring trouble under my roof.

### 22. `dlg.rook.cb_shrine_lit.0.wav`

*Where:* dialogue.json rook/cb_shrine_lit#0
*Played:* amused, then brusque; doing: thanks you for the shrine; pace: measured; volume: level.
*Note:* Amused at Chid. No catch: Rook never cries in front of anyone. A pause after 'My mother's lamp's got a sister again.', then brisk: 'Don't make a habit of it.'

```
[amused, then brusque] Chid came running in this morning without his shoes on. The shrine lamp, he says. My mother's lamp's got a sister again… ...Your bowl's on the house tonight. Don't make a habit of it.
```
Subtitle: Chid came running in this morning without his shoes on. The shrine lamp, he says. My mother's lamp's got a sister again. ...Your bowl's on the house tonight. Don't make a habit of it.

### 23. `dlg.rook.cb_freed_teamsters.0.wav`

*Where:* dialogue.json rook/cb_freed_teamsters#0
*Played:* gruff warmth; doing: praises you by scolding; pace: measured; volume: level.
*Note:* Mock-scolding, clearly pleased. Laugh on the out-breath at the end.

```
[gruff warmth] Jory Coyle's in my good room, and Harlan's tried to pay me for it twice. You've a lot to answer for, pet, bringing that much crying into one house.
```
Subtitle: Jory Coyle's in my good room, and Harlan's tried to pay me for it twice. You've a lot to answer for, pet, bringing that much crying into one house.

### 24. `dlg.rook.cb_burned_roost.0.wav`

*Where:* dialogue.json rook/cb_burned_roost#0
*Played:* cold anger; doing: condemns you for the cages; pace: slow; volume: quiet.
*Note:* No warmth at all. Long pause after the first sentence. The verdict quiet and final.

```
[cold anger, quietly] There were people in those cages. ...I'll take your money. I'll not have you in my kitchen.
```
Subtitle: There were people in those cages. ...I'll take your money. I'll not have you in my kitchen.

### 25. `dlg.rook.cb_nemesis_slain.0.wav`

*Where:* dialogue.json rook/cb_nemesis_slain#0
*Played:* approving, stern; doing: approves of you taking your things back; pace: measured; volume: level.
*Note:* Approving 'Good.' Then a hard little homily, like a mother's.

```
[approving, stern] You went back for your things. Good. Never let anything keep what's yours; it only teaches it to take more.
```
Subtitle: You went back for your things. Good. Never let anything keep what's yours; it only teaches it to take more.

### 26. `dlg.rook.cb_opened_vault.0.wav`

*Where:* dialogue.json rook/cb_opened_vault#0
*Played:* wary, dry; doing: you smell of the vault; pace: measured; volume: quiet.
*Note:* Sniffs. Doesn't want to know. Dry about Chid.

```
[wary, dry, quietly] You smell of cold stone. Don't tell me where you've been. Chid'll tell me anyway, and get it wrong.
```
Subtitle: You smell of cold stone. Don't tell me where you've been. Chid'll tell me anyway, and get it wrong.

### 27. `dlg.rook.say_calling.0.wav`

*Where:* dialogue.json rook/say_calling#0
*Played:* shrewd, dry; doing: reads you as a soldier; pace: measured; volume: level.
*Note:* Observant; a little dig at the end.

```
[shrewd, dry] You sit like you're expecting the door to come in. Watch, were you? Or wanted to be.
```
Subtitle: You sit like you're expecting the door to come in. Watch, were you? Or wanted to be.

### 28. `dlg.rook.say_calling.1.wav`

*Where:* dialogue.json rook/say_calling#1
*Played:* dry warning; doing: mind the furniture; pace: brisk; volume: level.
*Note:* Deadpan threat about the bench.

```
[dry warning] Mind the bench. The last one your size broke it, and I made him pay for it twice.
```
Subtitle: Mind the bench. The last one your size broke it, and I made him pay for it twice.

### 29. `dlg.rook.say_calling.2.wav`

*Where:* dialogue.json rook/say_calling#2
*Played:* dry, wry; doing: no fires indoors; pace: brisk; volume: level.
*Note:* Bossy, then a wicked little joke about Sella.

```
[dry, wry] If you're going to set anything on fire, pet, do it outside. Sella's got the only warm room in the house and she charges.
```
Subtitle: If you're going to set anything on fire, pet, do it outside. Sella's got the only warm room in the house and she charges.

### 30. `dlg.rook.say_calling.3.wav`

*The same words are also* `dlg.rook.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json rook/say_calling#3
*Played:* startled, then dry; doing: you crept in; pace: measured; volume: level.
*Note:* Mild suspicion; the bell threat dry.

```
[startled, then dry] You came in without the door making a sound. That door always makes a sound. Do it again and I'll put a bell on you.
```
Subtitle: You came in without the door making a sound. That door always makes a sound. Do it again and I'll put a bell on you.

### 31. `dlg.rook.say_woman.0.wav`

*Where:* dialogue.json rook/say_woman#0
*Played:* frank, protective; doing: warns a woman about jealous wives; pace: measured; volume: quiet.
*Note:* Woman to woman, low. Dry twist on 'for their wives'. 'they're not particular' wry.

```
[frank, protective, quietly] There's a bolt on the inside of your door. Use it. Not for the men; for their wives. They come up the stairs looking for Sella and they're not particular.
```
Subtitle: There's a bolt on the inside of your door. Use it. Not for the men; for their wives. They come up the stairs looking for Sella and they're not particular.

### 32. `dlg.rook.t_rook.0.wav`

*Where:* dialogue.json rook/t_rook#0
*Played:* dry, hiding grief; doing: her husband; pace: measured; volume: quiet.
*Note:* Fond, clipped list: drank, sang flat. Then quieter: the north road. Defensive about the chair; 'that's the only reason' too firm, which gives her away.

```
[dry, hiding grief, quietly] There was. Drank with the Watch, sang flat, and went up the north road with the last lot that went. I kept his chair by the hearth. I sit in it now. It's a good chair; that's the only reason.
```
Subtitle: There was. Drank with the Watch, sang flat, and went up the north road with the last lot that went. I kept his chair by the hearth. I sit in it now. It's a good chair; that's the only reason.

### 33. `dlg.rook.cb_told_brannoc.0.p0.wav`

*Where:* dialogue.json rook/cb_told_brannoc#0; part 1 of 3: **rook: You told Brannoc about his girl.** / narrator: She wipes the same bit of counter for a while. / rook: Good. Somebody had to, and it was never going to be me. ...Sit down. You look like you wan…
*Played:* grief held down, gruff; doing: thanks you for telling Brannoc; pace: slow; volume: quiet.
*Note:* Not looking at you. 'Good.' thick. 'it was never going to be me' honest. Then brusque kindness to hide it: she wants something to do with her hands.

```
[grief held down, gruff, quietly] You told Brannock about his girl.
```
Subtitle: You told Brannoc about his girl.

### 34. `dlg.rook.cb_told_brannoc.0.p2.wav`

*Where:* dialogue.json rook/cb_told_brannoc#0; part 3 of 3: rook: You told Brannoc about his girl. / narrator: She wipes the same bit of counter for a while. / **rook: Good. Somebody had to, and it was never going to be me. ...Sit down. You look like you wan…**
*Played:* grief held down, gruff; doing: thanks you for telling Brannoc; pace: slow; volume: quiet.
*Note:* Not looking at you. 'Good.' thick. 'it was never going to be me' honest. Then brusque kindness to hide it: she wants something to do with her hands.

```
[grief held down, gruff, quietly] Good. Somebody had to, and it was never going to be me. ...Sit down. You look like you want feeding, and I want something to do with my hands.
```
Subtitle: Good. Somebody had to, and it was never going to be me. ...Sit down. You look like you want feeding, and I want something to do with my hands.

### 35. `dlg.rook.valley.0.wav`

*Where:* dialogue.json rook/valley#0
*Played:* flat, closing a door; doing: what happened to Ashford; pace: measured; volume: quiet.
*Hides:* she knows who stood on which side of it, and that it isn't over (the Kerchiefs are what's left of Ashford)
*Note:* No warmth to spare. 'Ashford was.' on its own. The 'pet' is habit, not softness. The don'ts flat, each one a door closing, with no build.

```
[flat, closing a door, quietly] Ashford was… Half of it went to the Morrow in one night, pet, and the other half the year after, coughing. [inhales] Don't ask Holloway about it. Don't ask Mayka. Don't ask a Kerchief, if you meet one… And don't ask me twice.
```
Subtitle: Ashford was. Half of it went to the Morrow in one night, pet, and the other half the year after, coughing. Don't ask Holloway about it. Don't ask Maeca. Don't ask a Kerchief, if you meet one. And don't ask me twice.

### 36. `dlg.rook.mother.0.p1.wav`

*Where:* dialogue.json rook/mother#0; part 2 of 2: narrator: She stops wiping the cup. She looks at your face a beat too long, and then out of the wind… / **rook: ...Sit down, pet.**

```
...Sit down, pet.
```
Subtitle: ...Sit down, pet.

### 37. `dlg.rook.mother2.0.p0.wav`

*Where:* dialogue.json rook/mother2#0; part 1 of 3: **rook: She went in her sleep, pet. A week since.** / narrator: She sets the cup down. / rook: Chid brought her down and saw to her. I sat with her, after.

```
She went in her sleep, pet. A week since.
```
Subtitle: She went in her sleep, pet. A week since.

### 38. `dlg.rook.mother2.0.p2.wav`

*Where:* dialogue.json rook/mother2#0; part 3 of 3: rook: She went in her sleep, pet. A week since. / narrator: She sets the cup down. / **rook: Chid brought her down and saw to her. I sat with her, after.**

```
Chid brought her down and saw to her. I sat with her, after.
```
Subtitle: Chid brought her down and saw to her. I sat with her, after.

### 39. `dlg.rook.mother_where.0.wav`

*Where:* dialogue.json rook/mother_where#0

```
Quiet Garden, behind the shrine. There's a marker. No name on it yet; you can tell Chid what to cut.
```
Subtitle: Quiet Garden, behind the shrine. There's a marker. No name on it yet; you can tell Chid what to cut.

### 40. `dlg.rook.mother_short.0.p1.wav`

*Where:* dialogue.json rook/mother_short#0; part 2 of 2: narrator: Something goes across her face, and is put away. / **rook: You came, pet. That's the part that counts.**

```
You came, pet. That's the part that counts.
```
Subtitle: You came, pet. That's the part that counts.

### 41. `dlg.rook.mother_room.0.p1.wav`

*Where:* dialogue.json rook/mother_room#0; part 2 of 2: narrator: She turns a ring on the nail behind the bar, among the keys, without looking at it. / **rook: Back room's yours, if you want it. It's been free a week.**

```
Back room's yours, if you want it. It's been free a week.
```
Subtitle: Back room's yours, if you want it. It's been free a week.

## Said in passing

### 42. `bark.rook.day.0.wav`

*Where:* npcs.json rook.barks[0]
*Played:* proud, dry; pace: brisk; volume: level.
*Note:* Calling out to the room.

```
[proud, dry] Beds are dry and the stew's hot. That's more than most can say.
```
Subtitle: Beds are dry and the stew's hot. That's more than most can say.

### 43. `bark.rook.day.1.wav`

*Where:* npcs.json rook.barks[1]
*Played:* bossy; pace: brisk; volume: raised.
*Note:* Sharp order.

```
[bossy, loudly] Wipe your boots.
```
Subtitle: Wipe your boots.

### 44. `bark.rook.day.2.wav`

*Where:* npcs.json rook.barks[2]
*Played:* dry, bossy; pace: brisk; volume: raised.
*Note:* Deadpan.

```
[dry, bossy, loudly] If you're bleeding, bleed outside.
```
Subtitle: If you're bleeding, bleed outside.

### 45. `bark.rook.day.3.wav`

*Where:* npcs.json rook.barks[3]
*Played:* dry, sly; pace: measured; volume: level.
*Note:* Wry on 'ask Sella'.

```
[dry, sly] Rooms upstairs by the night. By the hour, ask Sella.
```
Subtitle: Rooms upstairs by the night. By the hour, ask Sella.

### 46. `bark.rook.night.0.wav`

*Where:* npcs.json rook.nightBarks[0]
*Played:* tired, firm; pace: measured; volume: quiet.
*Note:* Night voice.

```
[tired, firm, quietly] Lamps stay lit till the last one's in.
```
Subtitle: Lamps stay lit till the last one's in.

### 47. `bark.rook.night.1.wav`

*Where:* npcs.json rook.nightBarks[1]
*Played:* tired, warm; pace: measured; volume: quiet.
*Note:* Kind and sleepy.

```
[tired, warm, quietly] Bed's warm if you want it. Stew's gone.
```
Subtitle: Bed's warm if you want it. Stew's gone.

### 48. `bark.rook.night.2.wav`

*Where:* npcs.json rook.nightBarks[2]
*Played:* hushing; pace: measured; volume: hushed.
*Note:* Shushing the room.

```
[hushing, whispers] Quietly, now. People are sleeping.
```
Subtitle: Quietly, now. People are sleeping.

### 49. `bark.rook.night.3.wav`

*Where:* npcs.json rook.nightBarks[3]
*Played:* dry, wicked; pace: measured; volume: quiet.
*Note:* A joke at Sella's expense, fond.

```
[dry, wicked, quietly] Going up to Sella's? Wipe your boots twice. She's particular about her floor and nothing else.
```
Subtitle: Going up to Sella's? Wipe your boots twice. She's particular about her floor and nothing else.

### 50. `bark.rook.said.0.wav`

*Where:* npcs.json rook.said[0]
*Played:* worried, dry; doing: Harlan is grieving; pace: measured; volume: level.
*Note:* Said to nobody; 'He's sent it back.' flat, a little hurt.

```
[worried, dry] Harlan's not eating. I've sent bread. He's sent it back.
```
Subtitle: Harlan's not eating. I've sent bread. He's sent it back.

### 51. `bark.rook.said.1.wav`

*Where:* npcs.json rook.said[1]
*Played:* quiet, closed; doing: Nell's hook by the door; pace: slow; volume: quiet.
*Note:* 'I know. Leave it.' stops the subject dead.

```
[quiet, closed, quietly] Hook's empty. I know. Leave it.
```
Subtitle: Hook's empty. I know. Leave it.

### 52. `bark.rook.said.2.wav`

*Where:* npcs.json rook.said[2]

```
Lamp burned all night for you, pet. A night's ember. It's on your slate.
```
Subtitle: Lamp burned all night for you, pet. A night's ember. It's on your slate.

### 53. `bark.rook.said.3.wav`

*Where:* npcs.json rook.said[3]

```
Face like a wet week. Eat first. It'll still be there after.
```
Subtitle: Face like a wet week. Eat first. It'll still be there after.

### 54. `bark.rook.said.4.wav`

*Where:* npcs.json rook.said[4]

```
Sit down before you fall down. Again.
```
Subtitle: Sit down before you fall down. Again.


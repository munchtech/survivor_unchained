# The narrator: ElevenLabs packet

Voice id in the game: `narrator`. 391 takes to record (37,107 characters; about 111,321 credits at three tries a line). Status: **on hold, except the 66 takes marked LOCKED FOR RECORDING** (the story lead, 2026-10-11): record those now and hold the rest (recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording).

## Who they are

**The narrator.** Present tense, second person, plain nouns and working verbs; one image per line, never two adjectives where one will do. Says what happens and what can be seen, never what it means. Never theatrical, never cute, never names a feeling the scene has already shown. Never enters a bedroom: at a love scene the voice stops at the door. Says less from Act 2's turn on (shorter dawns, a line missing here and there), and the player should take it for style. *Casting (the owner, 6 October):* a woman of about sixty, plain and dry, level, a woman who has told people bad news before; the valley's accent, lightly (northern, not RP). No warmth, no "winter's tale": she lets warmth in once in the whole game, at "There you are." The quoted words of the survivor's mother ("Lamp's lit, Spark.") are said exactly as plainly as the rest; she does no voice for anyone.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The narrator`. Never describe a voice as sounding like a real person.

```
Native English (British, northern English). Female, 60s. Studio quality. Persona: a plain-spoken northern woman. A woman of about sixty with a plain, dry, level voice and a light northern English accent. She speaks evenly and close, at one steady pace, like a woman who has told people bad news before and does not dress it up. No warmth, no performance, never theatrical, never a storyteller's lilt. Light northern English accent. No reverb or effects.
```

Preview text:

```
Prints in the frost, your own. They come up from the river. None go down to it.
```

In the Voice Library instead: search for *light northern English (the valley's)*, *female*, *60*, and listen for this: A woman of about sixty with a plain, dry, level voice and a light northern English accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **55** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_drowned_fire.bedroll.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice narrator
```

## Saying the names

The text to paste already respells these; keep the respelling: Brannoc as *Brannock*, Greymuzzle as *Grey-muzzle*, Maeca as *Mayka*.

## How she reads

The narrator never shows a feeling: plain, the same pace throughout, and the facts do the work (the story lead's rule). The notes say what each line is doing; play none of it. Her tags say only how loud.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: drowned fire

### 1. `dlg.cin_drowned_fire.bedroll.0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `say.24c69afd4e5e.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_drowned_fire/bedroll#0
*Played:* plain; doing: you did not sleep here; pace: slow; volume: quiet.
*Note:* One plain fact, close.
*Length:* the cut is timed to it: 2.4–2.8 s, first sound to last word.

```
[quietly] Your bedroll has not been slept in.
```
Subtitle: Your bedroll has not been slept in.

### 2. `dlg.cin_drowned_fire.prints.0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `say.2d8b284f0b0e.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_drowned_fire/prints#0
*Played:* plain; doing: your own prints come from the river; pace: slow; volume: quiet.
*Note:* Two plain facts; a pause, then 'None go down to it.' on its own.
*Length:* the cut is timed to it: 6.0–7.0 s (about 0.7 s of pause before 'None go down to it.'), first sound to last word.

```
[quietly] Prints in the frost, your own. They come up from the river… None go down to it.
```
Subtitle: Prints in the frost, your own. They come up from the river. None go down to it.

### 3. `dlg.cin_drowned_fire.lamp.0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `say.e6fc0151e69a.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_drowned_fire/lamp#0
*Played:* volume: quiet.

```
[quietly] Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder.
```
Subtitle: Far up the road one lamp burns high in the dark, and a voice comes down to you over the frost, close as if she stood at your shoulder.

### 4. `dlg.cin_drowned_fire.frost.0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `say.1096c4f7e3e0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_drowned_fire/frost#0
*Played:* plain; doing: something is coming; pace: slow; volume: quiet.
*Note:* Plain.
*Length:* the cut is timed to it: 2.6–3.2 s, first sound to last word.

```
[quietly] Past the firelight, the frost is breaking.
```
Subtitle: Past the firelight, the frost is breaking.

## Scenes: Prologue

### 5. `say.8caf4a838291.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: reads a dead man and his last words; pace: slow; volume: quiet.
*Note:* The book's three lines read as written words, plainly, one after another.

```
[quietly] A Watchman, gray-bearded and a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes: Lamps at the Low Ford lit again, and not by us. Not oil. Wrong color. Sent Dannet for the captain. Dannet not back. The Warden is walking. I can hear it singing in the water.
```
Subtitle: A Watchman, gray-bearded and a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes: "Lamps at the Low Ford lit again, and not by us. Not oil. Wrong color." "Sent Dannet for the captain. Dannet not back." "The Warden is walking. I can hear it singing in the water."

### 6. `say.178e6dd0ad78.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: a dead man speaks to you alone; pace: slow; volume: quiet.
*Note:* A hush: one of his four whispers.

```
[quietly] ...and for you alone, the dead man's jaw moves.
```
Subtitle: ...and for you alone, the dead man's jaw moves.

### 7. `say.3dcd3f3caa00.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: tells the survivor the fire is no protection; pace: measured; volume: quiet.
*Note:* Two plain sentences; the second as plain as the first.

```
[quietly] The fire is almost out. It will not hold them back.
```
Subtitle: The fire is almost out. It will not hold them back.

### 8. `say.4d8a46e7502e.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: the quake stops; the way is north; pace: measured; volume: quiet.
*Note:* 'For now.' on its own, then a pause; the road north plainly.

```
[quietly] The ground goes still. For now… The road runs north, toward the Waystation.
```
Subtitle: The ground goes still. For now. The road runs north, toward the Waystation.

### 9. `say.2b72fa1dd85e.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: shows the ambush before it springs; pace: slow; volume: quiet.
*Note:* Three images, each given its own room; a pause before 'They were waiting.'

```
[quietly] A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins… They were waiting.
```
Subtitle: A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting.

### 10. `say.4a0952027e25.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: a threat notices you; pace: measured; volume: quiet.
*Note:* Even; the last sentence slower: it turns to look at you.

```
[quietly] Something in old armor is standing guard over the dead watchman. It turns to look at you.
```
Subtitle: Something in old armor is standing guard over the dead watchman. It turns to look at you.

### 11. `say.0663505a2971.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: the first dead you killed was a child; pace: slow; volume: quiet.
*Note:* Plain, the same pace throughout; the facts do the grief. No catch before 'twelve at most'; 'and new boots' no softer than the rest.

```
[quietly] The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.
```
Subtitle: The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.

### 12. `say.1e2fc7986134.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: the fight ends, something waits ahead; pace: slow; volume: quiet.
*Note:* The fight is over: a breath before it. Then water, and a cold blue light, plainly.

```
[quietly] The dead go quiet. Somewhere ahead, water, and a cold blue light.
```
Subtitle: The dead go quiet. Somewhere ahead, water, and a cold blue light.

### 13. `say.f1f67faea5fb.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: something strange beyond the fence; pace: measured; volume: quiet.
*Note:* Plain; 'The graves are listening.' said as simple fact.

```
[quietly] Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.
```
Subtitle: Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.

### 14. `say.f67dd9f6e97c.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: the Warden is seen for the first time; pace: slow; volume: quiet.
*Note:* A hush: one of his four whispers. A pause after 'in the ford'; 'with a lamp in its fist' plain.

```
[quietly] Something lies in the ford… larger than any man, with a lamp in its fist.
```
Subtitle: Something lies in the ford, larger than any man, with a lamp in its fist.

### 15. `say.33579e176a7e.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: the Warden's heart, still alive; pace: slow; volume: quiet.
*Note:* After the fight, unhurried; 'full of cold light' plain.

```
[quietly] Where the Warden fell, its heart is still burning: a stone the size of a fist, full of cold light.
```
Subtitle: Where the Warden fell, its heart is still burning: a stone the size of a fist, full of cold light.

### 16. `say.e9a2a9ccac15.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* volume: quiet.

```
[quietly] In the reeds on the far bank, someone is standing very still.
```
Subtitle: In the reeds on the far bank, someone is standing very still.

### 17. `say.3beaff2ef058.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: the night is over; pace: slow; volume: level.
*Note:* Dawn, plainly; 'then gold' given room, no warmer than the rest.

```
Gray light, then gold. Up the road, the Waystation's gate is opening.
```
Subtitle: Gray light, then gold. Up the road, the Waystation's gate is opening.

### 18. `say.93b63298edc0.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* volume: quiet.

```
[quietly] As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again. You try to call up your mother's face, and find it is not quite where you left it. Her voice is still there. Lamp's lit, Spark. Stay where it reaches.
```
Subtitle: As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again. You try to call up your mother's face, and find it is not quite where you left it. Her voice is still there. "Lamp's lit, Spark. Stay where it reaches."

### 19. `say.c4d495431666.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: death will not take you yet; pace: measured; volume: quiet.
*Note:* Low and level, not triumphant.

```
[quietly] The ember will not let you go so easily.
```
Subtitle: The ember will not let you go so easily.

## Cinematic: first light

### 20. `dlg.cin_first_light.back.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json cin_first_light/back#0
*Played:* plain; doing: the ember fades; pace: slow; volume: quiet.
*Note:* Plain and slow.
*Length:* the cut is timed to it: 3.6–4.2 s, first sound to last word.

```
[quietly] The sun clears the trees, and the ember goes back into the ground.
```
Subtitle: The sun clears the trees, and the ember goes back into the ground.

### 21. `dlg.cin_first_light.face.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json cin_first_light/face#0
*Played:* plain; doing: the mother's face; pace: slow; volume: quiet.
*Note:* Plain and slow; the strangeness is in the words.
*Length:* the cut is timed to it: 4.6–5.4 s (the cut then holds three seconds of silence), first sound to last word.

```
[quietly] You try to call up your mother's face, and find it is not quite where you left it. Her voice is still there. Lamp's lit, Spark. Stay where it reaches.
```
Subtitle: You try to call up your mother's face, and find it is not quite where you left it. Her voice is still there. "Lamp's lit, Spark. Stay where it reaches."

### 22. `dlg.cin_first_light.baking.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json cin_first_light/baking#0
*Played:* plain; doing: ordinary life; pace: slow; volume: quiet.
*Note:* Dawn, plainly.
*Length:* the cut is timed to it: 2.4–3.0 s, first sound to last word.

```
[quietly] Somewhere up the street, someone is baking.
```
Subtitle: Somewhere up the street, someone is baking.

## Scenes: Verge

### 23. `say.ac8270282f9f.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the Pack lets you pass; pace: slow; volume: quiet.
*Note:* Still and level.

```
[quietly] The wolves watch you come. None of them move to stop you.
```
Subtitle: The wolves watch you come. None of them move to stop you.

### 24. `say.3ff82d4e2ac7.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the wolf cloak has damned you; pace: measured; volume: quiet.
*Note:* The second sentence a shade quicker: every wolf is on its feet.

```
[quietly] They smell the cloak before they see you. Every wolf in the Hollow is on its feet.
```
Subtitle: They smell the cloak before they see you. Every wolf in the Hollow is on its feet.

### 25. `say.3869640818fe.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the Pack knows what you did; pace: measured; volume: quiet.
*Note:* Plain; the second sentence is fact, not reproach.

```
[quietly] They smell the blood on you before they see you: one of theirs, since you last slept.
```
Subtitle: They smell the blood on you before they see you: one of theirs, since you last slept.

### 26. `say.6ea507a14576.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: you are surrounded; pace: slow; volume: quiet.
*Note:* Low and level.

```
[quietly] Low growling from every side of the Hollow.
```
Subtitle: Low growling from every side of the Hollow.

### 27. `say.0762cf80c852.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the Kerchief camp is ordinary; pace: measured; volume: quiet.
*Note:* Plain; the ordinary details do it.

```
[quietly] Red cloth at every tent, washing on a line, children with a wooden sword. They see your colors and go back to what they were doing.
```
Subtitle: Red cloth at every tent, washing on a line, children with a wooden sword. They see your colors and go back to what they were doing.

### 28. `say.2133e8a51219.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a woman feeds the caged; pace: measured; volume: quiet.
*Note:* Plain; no comment in the voice.

```
[quietly] By the cages a woman is passing stew in through the bars. Her own child holds up a bowl beside her.
```
Subtitle: By the cages a woman is passing stew in through the bars. Her own child holds up a bowl beside her.

### 29. `say.7afbb86d6b6e.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs

```
The camp is struck: cold fires, and pale squares in the grass where the tents stood. They took everything that would carry. The Coyle wagons they left where they stood.
```
Subtitle: The camp is struck: cold fires, and pale squares in the grass where the tents stood. They took everything that would carry. The Coyle wagons they left where they stood.

### 30. `say.060466d9cefd.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the thing in the pit; pace: slow; volume: quiet.
*Note:* The size given slowly, a phrase at a time. A pause before 'You watch it long enough'; the end flat.

```
[quietly] The ground shivers. At the bottom of the pit lies something pale and segmented, bigger than a house. It does not move… You watch it long enough to be sure, and you are not.
```
Subtitle: The ground shivers. At the bottom of the pit lies something pale and segmented, bigger than a house. It does not move. You watch it long enough to be sure, and you are not.

### 31. `say.b76e3053dc5f.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the Morrow is alive; pace: very slow; volume: hushed.
*Note:* A hush: one of his four whispers. 'slow, patient, enormous' each its own beat; a long pause after 'Not breathing.'; 'Praying.' barely voiced.

```
[whispers] Under the silence you hear it, for as long as a held breath: slow, patient, enormous. Not breathing… Praying.
```
Subtitle: Under the silence you hear it, for as long as a held breath: slow, patient, enormous. Not breathing. Praying.

### 32. `say.0b5e75f9dfa0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the caravan was robbed, not eaten; pace: measured; volume: level.
*Note:* Plain; 'Wolves do not drive wagons.' as simple fact.

```
Three wagons, dragged off the road into the trees. Wolves do not drive wagons.
```
Subtitle: Three wagons, dragged off the road into the trees. Wolves do not drive wagons.

### 33. `say.e6c4fb3a8998.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: clues at the wreck; pace: measured; volume: quiet.
*Note:* Short observations; a pause before 'Under the seat'.

```
[quietly] Kerchief arrows in the sideboards, red-fletched. The strongbox bolts are sprung, the box gone. Under the seat: a torn manifest.
```
Subtitle: Kerchief arrows in the sideboards, red-fletched. The strongbox bolts are sprung, the box gone. Under the seat: a torn manifest.

### 34. `say.20dc615919d1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the trail leads to the ravine; pace: measured; volume: quiet.
*Note:* Short; 'Toward the ravine.' a shade lower.

```
[quietly] Deep ruts, heavy wagons, driven south-east into the trees. Toward the ravine.
```
Subtitle: Deep ruts, heavy wagons, driven south-east into the trees. Toward the ravine.

### 35. `say.cfa493798ba7.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a moment of safety; pace: slow; volume: quiet.
*Note:* Plain and slow.

```
[quietly] The old fire takes. For a little while, this is a safe place.
```
Subtitle: The old fire takes. For a little while, this is a safe place.

### 36. `say.8e845892b699.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the wolf was poisoned; pace: measured; volume: quiet.
*Note:* A list, plainly; the last sentence slower.

```
[quietly] No wound. Black gums, milky eyes, ribs like a washboard, and the belly swollen hard. It drank something that rotted it from the inside.
```
Subtitle: No wound. Black gums, milky eyes, ribs like a washboard, and the belly swollen hard. It drank something that rotted it from the inside.

### 37. `say.52d0f1dfa274.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a wolf dead of no wound; pace: measured; volume: quiet.
*Note:* Plain.

```
[quietly] A wolf, dead, with no wound on it. Its eyes have gone milky.
```
Subtitle: A wolf, dead, with no wound on it. Its eyes have gone milky.

### 38. `say.7197a1b189a3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the stream is wrong; pace: slow; volume: quiet.
*Note:* Three senses, unhurried.

```
[quietly] The water is warm, and faintly green, and smells like a chapel lamp.
```
Subtitle: The water is warm, and faintly green, and smells like a chapel lamp.

### 39. `say.84f6c2c74004.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the source of the poison; pace: measured; volume: quiet.
*Note:* Short observations; a slight lift on 'the drag-marks of lamps' (a clue).

```
[quietly] Riveted iron, warm to the touch, spilling glowing slurry into the stream. Small clawed prints all round it, and the drag-marks of lamps.
```
Subtitle: Riveted iron, warm to the touch, spilling glowing slurry into the stream. Small clawed prints all round it, and the drag-marks of lamps.

### 40. `say.3cc85cd8c414.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: to make the player feel one charge's weight in the hand; pace: slow; volume: quiet.
*Wants:* to make the player feel one charge's weight in the hand
*Note:* Low and close, as if not to wake them. A pause before 'the way they have waited for everyone'.

```
[quietly] You pry one charge out of the straw. The rest sit there and wait, the way they have waited for everyone.
```
Subtitle: You pry one charge out of the straw. The rest sit there and wait, the way they have waited for everyone.

### 41. `say.4acad56ca838.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: to let the relief arrive in the silence; pace: slow; volume: quiet.
*Wants:* to let the relief arrive in the silence
*Note:* 'One at a time' slow; 'not go off' flat and quiet.

```
[quietly] You roll them down into the ravine's water one at a time, and listen to each one not go off.
```
Subtitle: You roll them down into the ravine's water one at a time, and listen to each one not go off.

### 42. `say.769a1c759f88.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: get clear; pace: quick; volume: level.
*Note:* Tight and quick; 'Run.' short, not shouted.

```
The fuse fizzes. You have a few seconds. Run.
```
Subtitle: The fuse fizzes. You have a few seconds. Run.

### 43. `say.384c340b6b6d.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the sigil wakes; pace: slow; volume: quiet.
*Note:* 'like an eye opening' slower; a pause before 'The door is listening.'

```
[quietly] The fragment fits one notch of the seven, and under your hand the whole sigil wakes, violet, like an eye opening… The door is listening.
```
Subtitle: The fragment fits one notch of the seven, and under your hand the whole sigil wakes, violet, like an eye opening. The door is listening.

### 44. `say.9757e1dab88e.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the sigil waits for night; pace: measured; volume: quiet.
*Note:* Plain; the last clause level.

```
[quietly] The fragment fits one notch of the seven, and the stone warms under it. Whatever the sigil is waiting for, it is not daylight.
```
Subtitle: The fragment fits one notch of the seven, and the stone warms under it. Whatever the sigil is waiting for, it is not daylight.

### 45. `say.66cdbe61b828.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: reading the Legion's words; pace: slow; volume: quiet.
*Note:* The inscription read slowly as old written words; 'all empty' quiet.

```
[quietly] Old-empire script over the door. Here the Seventh Legion buried what it could not burn. Below it, a sigil with seven notches, all empty.
```
Subtitle: Old-empire script over the door. Here the Seventh Legion buried what it could not burn. Below it, a sigil with seven notches, all empty.

### 46. `say.20b15596c09c.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the sealed door; pace: slow; volume: quiet.
*Note:* The Latin said slowly, as old words.

```
[quietly] A door of black stone, smooth as glass. Cut over it, words in a dead tongue: hic legio septima sepelivit quod urere non potuit. Under them, a violet sigil you cannot read. It hums against your teeth.
```
Subtitle: A door of black stone, smooth as glass. Cut over it, words in a dead tongue: hic legio septima sepelivit quod urere non potuit. Under them, a violet sigil you cannot read. It hums against your teeth.

### 47. `say.82b1e8294244.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a key-stone in dead hands; pace: slow; volume: quiet.
*Note:* Plain.

```
[quietly] In the bones of one hand, a wedge of black stone cut to fit something.
```
Subtitle: In the bones of one hand, a wedge of black stone cut to fit something.

### 48. `say.8591ecfe4019.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the skull turns; pace: slow; volume: hushed.
*Note:* A hush: one of his four whispers.

```
[whispers] The skull turns, very slightly, toward you.
```
Subtitle: The skull turns, very slightly, toward you.

### 49. `say.6e1fab16785e.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: someone went in and did not come out; pace: measured; volume: quiet.
*Note:* The token a careful find; a pause before 'None coming away.'

```
[quietly] Bootprints in the mud, fresh, going up to the door… None coming away. Trodden into one heel-print: a copper toll-token, stamped with three roads.
```
Subtitle: Bootprints in the mud, fresh, going up to the door. None coming away. Trodden into one heel-print: a copper toll-token, stamped with three roads.

### 50. `say.b40ac14379d8.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a treasure where wolves go to die; pace: slow; volume: quiet.
*Note:* Slow; 'cold as snow' no softer than the rest.

```
[quietly] Under the brambles, where the wolves go when one of them is dying: a circlet of moonsilver, cold as snow.
```
Subtitle: Under the brambles, where the wolves go when one of them is dying: a circlet of moonsilver, cold as snow.

### 51. `say.ca6fbefec176.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a freed prisoner; pace: measured; volume: quiet.
*Note:* Plain; the nails are the detail.

```
[quietly] A teamster, thin and gray, stumbles out and grips your arm. His nails are broken to the quick from the bars.
```
Subtitle: A teamster, thin and gray, stumbles out and grips your arm. His nails are broken to the quick from the bars.

### 52. `say.75abd0854536.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a freed prisoner; pace: measured; volume: quiet.
*Note:* Plain.

```
[quietly] A woman who will not stop saying thank you.
```
Subtitle: A woman who will not stop saying thank you.

### 53. `say.fccd00002739.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: Jory in the cage; pace: measured; volume: quiet.
*Note:* Plain.

```
[quietly] A young man, freckled, still holding the bars after the door is open.
```
Subtitle: A young man, freckled, still holding the bars after the door is open.

### 54. `say.f1bc8c3f22ed.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the pump breaks; pace: measured; volume: quiet.
*Note:* Each stopping its own short sentence.

```
[quietly] Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.
```
Subtitle: Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.

### 55. `say.a4755c96100b.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the cost of the blast; pace: slow; volume: quiet.
*Note:* Level and quiet throughout, 'Most of them do not crawl far.' included.

```
[quietly] When the dust comes down, the hillside is a wound. Small shapes crawl out of it with their lamps still lit. Some of them are on fire. Most of them do not crawl far.
```
Subtitle: When the dust comes down, the hillside is a wound. Small shapes crawl out of it with their lamps still lit. Some of them are on fire. Most of them do not crawl far.

### 56. `say.26621b48a47e.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the cost of the fire; pace: slow; volume: quiet.
*Note:* Level; a pause before 'and then there is only the fire', said low.

```
[quietly] The fire takes the tents, and then the cages. There is screaming, and the smell, and hands through the bars; and then there is only the fire.
```
Subtitle: The fire takes the tents, and then the cages. There is screaming, and the smell, and hands through the bars; and then there is only the fire.

### 57. `say.0622cbb5851c.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a hidden glade; pace: measured; volume: quiet.
*Note:* Quick on the fire, slower on the glade.

```
[quietly] The brambles go up like paper. Beyond them, a glade full of pale light.
```
Subtitle: The brambles go up like paper. Beyond them, a glade full of pale light.

### 58. `say.005625eee2b8.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a hidden glade; pace: measured; volume: quiet.
*Note:* The effort, then slower on the glade.

```
[quietly] You hack a way through the brambles. Beyond them, a glade full of pale light.
```
Subtitle: You hack a way through the brambles. Beyond them, a glade full of pale light.

### 59. `say.3f7b7c5bd5a4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the Pack runs with you; pace: slow; volume: quiet.
*Note:* Still and slow.

```
[quietly] Four gray shapes fall in beside you at the edge of the wood.
```
Subtitle: Four gray shapes fall in beside you at the edge of the wood.

### 60. `say.e08ae8c1e46c.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: your fallen things, found; pace: measured; volume: quiet.
*Note:* Plain; 'most of them' level.

```
[quietly] Where you fell. The ground has kept your things for you, most of them.
```
Subtitle: Where you fell. The ground has kept your things for you, most of them.

## Scenes: Waystation

### 61. `say.6947705bd0e4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain; doing: a small human mark on the well; pace: measured; volume: quiet.
*Note:* Read 'M. + J.' as letters: 'em and jay'.

```
[quietly] The water is a long way down, and clean. Somebody has scratched M and J into the stone.
```
Subtitle: The water is a long way down, and clean. Somebody has scratched M and J into the stone.

### 62. `say.8b004f74544d.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain; doing: the warehouse opens; pace: measured; volume: quiet.
*Note:* Plain; the ledger line level.

```
[quietly] The clerk's key turns sweetly. Inside: crates, dust, and a ledger Pell should have burned.
```
Subtitle: The clerk's key turns sweetly. Inside: crates, dust, and a ledger Pell should have burned.

### 63. `say.ff981a5b72be.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain; doing: the warehouse opens; pace: measured; volume: quiet.
*Note:* Quiet and careful.

```
[quietly] The lock gives under your picks. Inside: crates, dust, and a ledger Pell should have burned.
```
Subtitle: The lock gives under your picks. Inside: crates, dust, and a ledger Pell should have burned.

### 64. `say.546ec60933f6.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain; doing: Nell's burial; pace: slow; volume: quiet.
*Note:* Three strokes, each its own beat; 'and steps back, and back.' level.

```
[quietly] The whole town is in the Quiet Garden, round a fresh grave beside the old captain's stone. Brannock kneels at its head with an iron marker and his hammer: three strokes, iron into earth. Rook sets the inn's lamp at its foot, lit, in broad daylight, and steps back, and back.
```
Subtitle: The whole town is in the Quiet Garden, round a fresh grave beside the old captain's stone. Brannoc kneels at its head with an iron marker and his hammer: three strokes, iron into earth. Rook sets the inn's lamp at its foot, lit, in broad daylight, and steps back, and back.

### 65. `say.0d5976546998.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs

```
You stand at it a while.
```
Subtitle: You stand at it a while.

### 66. `say.9a0e5952f0c0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs

```
A plain wooden marker, a few stones along from the old captain's. No name on it yet. The earth on it is dark, and has not settled.
```
Subtitle: A plain wooden marker, a few stones along from the old captain's. No name on it yet. The earth on it is dark, and has not settled.

### 67. `say.a5b99f61e011.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain; doing: an old captain's trunk; pace: slow; volume: quiet.
*Note:* The note read as written words: 'Keep the lights lit.' Then the initial: 'C.'

```
[quietly] Beside the old captain's stone, sunk in the nettles, a trunk the Watch forgot: ember shards, a purse, and a note. Keep the lights lit. C.
```
Subtitle: Beside the old captain's stone, sunk in the nettles, a trunk the Watch forgot: ember shards, a purse, and a note. Keep the lights lit. C.

### 68. `say.8c1f7c369819.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain; doing: arrival in town; pace: measured; volume: level.
*Note:* A list of sensations, unhurried; 'News travels fast here.' plain.

```
The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.
```
Subtitle: The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.

### 69. `say.a49e30d2ba1e.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain; doing: a new stall in town; pace: measured; volume: level.
*Note:* Plain; a slight lift on 'places the road forgets'.

```
A cartographer has set up a stall on the Old Road, by the east gate: maps to places the road forgets.
```
Subtitle: A cartographer has set up a stall on the Old Road, by the east gate: maps to places the road forgets.

## Scenes: the clock (dusk, night, getting up)

### 70. `say.9dc671546463.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: lets the dusk call land on a memory she won't name; pace: slow; volume: quiet.
*Note:* Straight after the gate's call. It is her own words coming back to her from a stranger's mouth, and she says nothing about that: flat, a fact about doors. No ache, no weight on 'door'.

```
[quietly] You have heard that said at a door.
```
Subtitle: You have heard that said at a door.

### 71. `say.10bf2fd84dd3.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: gets her child up; pace: measured; volume: quiet.
*Note:* Three words, the way you'd say them at a bedside before light: not a cheer, not an order, no surprise. The player has just died, and nothing in her voice says so.

```
[quietly] You get up.
```
Subtitle: You get up.

### 72. `say.c4c1c1ee88e3.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: tells the price without naming it; pace: measured; volume: quiet.
*Note:* The line the game turns on, and it must sound like nothing. The first rising cost twenty-six lives; every one since costs one, someone in the valley, and she knows it. Say it as plainly as the weather, the second sentence no heavier than the first: no warning, no irony, no comfort. The player should hear "it gets easier" every time until the stair, and hear the price on a replay.

```
[quietly] You get up. It takes less than it did.
```
Subtitle: You get up. It takes less than it did.

### 73. `say.c8db02ffeab0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: marks the middle of the night; pace: measured; volume: level.
*Note:* A clock line, heard mid-fight. Two plain facts; the lamp still lit is only a lamp.

```
Half the night is gone. Up on the Toll Tower, the one lamp is still lit.
```
Subtitle: Half the night is gone. Up on the Toll Tower, the one lamp is still lit.

### 74. `say.977de4be60a3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: ends a night the survivor stood through; pace: measured; volume: level.
*Note:* Tired and level. A small easing on 'the warmth comes back into your hands', no relief in the voice.

```
You see the night out on your feet. At first light the warmth comes back into your hands.
```
Subtitle: You see the night out on your feet. At first light the warmth comes back into your hands.

### 75. `say.fda6ac6c6045.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: she goes on into the dark; pace: measured; volume: level.
*Note:* Two short sentences, the second no heavier than the first. Not a warning.

```
You do not go back to the lamps. You go on.
```
Subtitle: You do not go back to the lamps. You go on.

### 76. `say.5cbd1ba39848.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: reports the Pack gone quiet; pace: measured; volume: quiet.
*Note:* The quiet is the news. Plain; let the line end and stay ended.

```
[quietly] Out past the lamps, the Pack has stopped howling.
```
Subtitle: Out past the lamps, the Pack has stopped howling.

### 77. `say.1ad34f33a2b4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: shows the Kerchiefs' fires from far off; pace: measured; volume: level.
*Note:* One image, said as a fact: 'the way a town lights its windows' is plain, not pretty.

```
Up the Old Road the Kerchiefs' fires are lit all along the ravine, the way a town lights its windows.
```
Subtitle: Up the Old Road the Kerchiefs' fires are lit all along the ravine, the way a town lights its windows.

### 78. `say.f9f2c5cad405.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: something is wrong at the Dig; pace: measured; volume: level.
*Note:* The wrongness is in 'all moving the same way'; don't lean on it. Level, like counting.

```
On the hill over the Dig, the lamps are all moving the same way.
```
Subtitle: On the hill over the Dig, the lamps are all moving the same way.

### 79. `say.87df61b27292.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: the sealed door has woken; pace: slow; volume: quiet.
*Note:* A beat after 'has woken'. 'Its light is violet' plain, the color as a fact.

```
[quietly] Out in the Verge, the sealed door has woken. Its light is violet.
```
Subtitle: Out in the Verge, the sealed door has woken. Its light is violet.

### 80. `say.fdad90e14306.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: the Verge's night begins; pace: measured; volume: level.
*Note:* Plain, level: the ember coming up is weather, not alarm.

```
Out in the Verge, the ember is coming up.
```
Subtitle: Out in the Verge, the ember is coming up.

## Scenes: the Dig at night

### 81. `say.cddfb7c98244.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Dig.cs
*Played:* plain; doing: opens the Dig's night; pace: measured; volume: level.
*Note:* Arrival. The second sentence is the threat; say it no faster and no louder than the first.

```
The ember takes you to the edge of the Dig. Every lamp in the hole is coming up at once.
```
Subtitle: The ember takes you to the edge of the Dig. Every lamp in the hole is coming up at once.

### 82. `say.18e64cad88a1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Dig.cs
*Played:* plain; doing: the first stage done; the next one waits; pace: measured; volume: level.
*Note:* Mid-fight, between stages. 'The rails are singing' is plain description.

```
The last windlass goes over. Down the tub-way the brake-house lamp is lit, and the rails are singing.
```
Subtitle: The last windlass goes over. Down the tub-way the brake-house lamp is lit, and the rails are singing.

### 83. `say.a89cdacbc1f4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Dig.cs
*Played:* plain; doing: shows the lamplings carrying the crates; pace: measured; volume: level.
*Note:* Mid-fight. Plain; the oddness of 'carrying a crate' is in the words, not the voice.

```
Past the brake-house stands the pump-house, and every lampling between you and it is carrying a crate.
```
Subtitle: Past the brake-house stands the pump-house, and every lampling between you and it is carrying a crate.

### 84. `say.0f4d56f97d68.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Dig.cs
*Played:* plain; doing: someone is in the pump-house; pace: measured; volume: quiet.
*Note:* Mid-fight. A little slower on 'one after another', as if watching them come on.

```
[quietly] Past the brake-house stands the pump-house. Somebody inside is lighting lamps, one after another.
```
Subtitle: Past the brake-house stands the pump-house. Somebody inside is lighting lamps, one after another.

### 85. `say.8ea79d1dcdf1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Dig.cs
*Played:* plain; doing: the lamplings give up; pace: slow; volume: quiet.
*Note:* The Dig's end. Plain and quiet; there is pity in the picture, none in the voice.

```
[quietly] Every lampling left on the lip lies down flat, with its hands over its lamp.
```
Subtitle: Every lampling left on the lip lies down flat, with its hands over its lamp.

## Scenes: the Hollow at night

### 86. `say.44a50d15b7fa.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Hollow.cs
*Played:* plain; doing: opens the Hollow's night; pace: measured; volume: level.
*Note:* Arrival. 'And it smells wrong' plain, a fact noted, no shudder.

```
The ember takes you down the clough, into the Hollow. The stream is loud here, and it smells wrong.
```
Subtitle: The ember takes you down the clough, into the Hollow. The stream is loud here, and it smells wrong.

### 87. `say.59a5da567e47.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Hollow.cs
*Played:* plain; doing: the Pack falls quiet; a sick thing is near; pace: slow; volume: quiet.
*Note:* Mid-fight. Let the quiet in before 'In the quiet'. 'Something in the brush coughing' plain.

```
[quietly] The howling stops. In the quiet you can hear the stream, and something in the brush coughing.
```
Subtitle: The howling stops. In the quiet you can hear the stream, and something in the brush coughing.

### 88. `say.1394532b178f.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Hollow.cs
*Played:* plain; doing: the den, and the sick wolves in it; pace: slow; volume: quiet.
*Note:* Mid-fight. A beat before 'and in it'. 'Gray shapes that do not get up' plain; they are dying, and she won't say so.

```
[quietly] The deadfalls burn. Past them is the den's mouth, and in it, gray shapes that do not get up.
```
Subtitle: The deadfalls burn. Past them is the den's mouth, and in it, gray shapes that do not get up.

### 89. `say.648f54abf56c.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Hollow.cs
*Played:* plain; doing: the boss is coming; pace: measured; volume: level.
*Note:* Mid-fight. No build: the second sentence as level as the first.

```
The wolves back away from you, low, into a ring. Something is coming out of the den.
```
Subtitle: The wolves back away from you, low, into a ring. Something is coming out of the den.

## Scenes: the Roost at night

### 90. `say.54d6b6c86b5d.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Roost.cs
*Played:* plain; doing: opens the Roost's night; pace: measured; volume: level.
*Note:* Arrival. The whistles are a fact; 'and another answering' a touch slower.

```
The ember takes you up the ruts below the Roost. Somewhere above, a whistle, and another answering.
```
Subtitle: The ember takes you up the ruts below the Roost. Somewhere above, a whistle, and another answering.

### 91. `say.884076412b80.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Roost.cs
*Played:* plain; doing: the cage yard, held; pace: measured; volume: level.
*Note:* Mid-fight. 'Three whistles, and none answering' is the camp silenced; plain. 'Somebody very big' dry, no joke in it.

```
Three whistles, and none answering. Ahead, the cage yard: four empty cages, and somebody very big still standing guard on them.
```
Subtitle: Three whistles, and none answering. Ahead, the cage yard: four empty cages, and somebody very big still standing guard on them.

### 92. `say.c12346388d1c.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Roost.cs
*Played:* plain; doing: the cage yard, and three graves; pace: slow; volume: quiet.
*Note:* Mid-fight. The graves are the news: a beat before 'and three mounds of new earth', and no weight on it.

```
[quietly] Three whistles, and none answering. Ahead, the cage yard: four empty cages, and three mounds of new earth beside them.
```
Subtitle: Three whistles, and none answering. Ahead, the cage yard: four empty cages, and three mounds of new earth beside them.

### 93. `say.8f4acfe90f92.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Roost.cs
*Played:* plain; doing: the cage yard, one cage empty; pace: measured; volume: quiet.
*Note:* Mid-fight. 'With nobody in it' plain; it is the fourth cage, and she doesn't say whose.

```
[quietly] Three whistles, and none answering. Ahead, the cage yard: four cages, and the fourth stands open with nobody in it.
```
Subtitle: Three whistles, and none answering. Ahead, the cage yard: four cages, and the fourth stands open with nobody in it.

### 94. `say.ed1ff5a67b8c.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Roost.cs
*Played:* plain; doing: the levy forms up; pace: measured; volume: level.
*Note:* Mid-fight. 'The way they were taught' carries Ashford's soldiers in it; say it as drill, flat.

```
Past the cages, the camp's fires, and the levy forming up the way they were taught: in step, pikes level.
```
Subtitle: Past the cages, the camp's fires, and the levy forming up the way they were taught: in step, pikes level.

### 95. `say.c52914d98baf.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Roost.cs
*Played:* plain; doing: the crates are gone; the camp falls back; pace: measured; volume: level.
*Note:* Mid-fight. Three sentences, even; a beat before 'Then they part.'

```
Where the crates stood there is a hole in the yard. Beyond it, the Kerchiefs fall back to the big fire and stand there with their torches up. Then they part.
```
Subtitle: Where the crates stood there is a hole in the yard. Beyond it, the Kerchiefs fall back to the big fire and stand there with their torches up. Then they part.

### 96. `say.cbc22a062d1e.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Roost.cs
*Played:* plain; doing: the camp falls back for its chief; pace: measured; volume: level.
*Note:* Mid-fight. Even; a beat before 'Then they part.'

```
The Kerchiefs fall back to the big fire and stand there with their torches up. Then they part.
```
Subtitle: The Kerchiefs fall back to the big fire and stand there with their torches up. Then they part.

## Scenes: the Vault at night

### 97. `say.def83ed2ca1b.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Vault.cs
*Played:* plain; doing: opens the vault's night; pace: slow; volume: quiet.
*Note:* Arrival. A beat before 'On the stair'. 'Coming up in step' plain: the dread is in 'in step'.

```
[quietly] Through the door: a long hall, and the head of a stair. On the stair, something is coming up in step.
```
Subtitle: Through the door: a long hall, and the head of a stair. On the stair, something is coming up in step.

### 98. `say.9bf57b5df8e4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Vault.cs
*Played:* plain; doing: the next stage: a bow at the hall's end; pace: measured; volume: level.
*Note:* Mid-fight. Plain; 'a great bow' is a size, not wonder.

```
The first ranks are down. The hall runs on ahead, long and straight, and at the end of it something is winding a great bow.
```
Subtitle: The first ranks are down. The hall runs on ahead, long and straight, and at the end of it something is winding a great bow.

### 99. `say.a83f4948df17.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Vault.cs
*Played:* plain; doing: the standards go up; pace: measured; volume: level.
*Note:* Mid-fight. 'One after another' with three even beats; 'and the dead turn to face them' level.

```
Down the hall, three standards go up one after another, and the dead turn to face them.
```
Subtitle: Down the hall, three standards go up one after another, and the dead turn to face them.

### 100. `say.4350b3e997df.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* godot/logic/Play/Story/Vault.cs
*Played:* plain; doing: the vault's dead come to attention; pace: slow; volume: quiet.
*Note:* The fight's end. A beat before 'all at once'; 'with one sound' last and plain.

```
[quietly] The last standard goes down. Along the walls, the dead stand to attention, all at once, with one sound.
```
Subtitle: The last standard goes down. Along the walls, the dead stand to attention, all at once, with one sound.

## Conversations: Rook

### 101. `dlg.rook.cb_told_brannoc.0.p1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json rook/cb_told_brannoc#0; part 2 of 3: rook: You told Brannoc about his girl. / **narrator: She wipes the same bit of counter for a while.** / rook: Good. Somebody had to, and it was never going to be me. ...Sit down. You look like you wan…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She wipes the same bit of counter for a while.
```
Subtitle: She wipes the same bit of counter for a while.

### 102. `dlg.rook.mother.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json rook/mother#0; part 1 of 2: **narrator: She stops wiping the cup. She looks at your face a beat too long, and then out of the wind…** / rook: ...Sit down, pet.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She stops wiping the cup. She looks at your face a beat too long, and then out of the window at the tower, and then at the cup.
```
Subtitle: She stops wiping the cup. She looks at your face a beat too long, and then out of the window at the tower, and then at the cup.

### 103. `dlg.rook.mother2.0.p1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json rook/mother2#0; part 2 of 3: rook: She went in her sleep, pet. A week since. / **narrator: She sets the cup down.** / rook: Chid brought her down and saw to her. I sat with her, after.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She sets the cup down.
```
Subtitle: She sets the cup down.

### 104. `dlg.rook.mother_short.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json rook/mother_short#0; part 1 of 2: **narrator: Something goes across her face, and is put away.** / rook: You came, pet. That's the part that counts.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Something goes across her face, and is put away.
```
Subtitle: Something goes across her face, and is put away.

### 105. `dlg.rook.mother_quiet.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json rook/mother_quiet#0
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She lets it be quiet. She's good at that.
```
Subtitle: She lets it be quiet. She's good at that.

### 106. `dlg.rook.mother_room.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json rook/mother_room#0; part 1 of 2: **narrator: She turns a ring on the nail behind the bar, among the keys, without looking at it.** / rook: Back room's yours, if you want it. It's been free a week.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She turns a ring on the nail behind the bar, among the keys, without looking at it.
```
Subtitle: She turns a ring on the nail behind the bar, among the keys, without looking at it.

## Conversations: Chid

### 107. `dlg.chid.first.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/first#0; part 2 of 3: chid: Oh! A lantern of the Order! Lit! / **narrator: He looks from the lantern to you, a moment longer than people do.** / chid: Oh, sit down, sit, sit. I'm Chid. They call me the Fool, which is fair. This is the shrine…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks from the lantern to you, a moment longer than people do.
```
Subtitle: He looks from the lantern to you, a moment longer than people do.

### 108. `dlg.chid.first.1.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/first#1; part 2 of 3: chid: Oh! A visitor. Hello! / **narrator: He looks at you a moment longer than people do.** / chid: I'm Chid. They call me the Fool, which is fair. This is the shrine of the Morning Light. I…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you a moment longer than people do.
```
Subtitle: He looks at you a moment longer than people do.

### 109. `dlg.chid.woke.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/woke#0; part 2 of 3: chid: Up again. / **narrator: He has the kettle on already.** / chid: The carter sends his regards. You'll be sore a day or two. Whatever did it has your things…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He has the kettle on already.
```
Subtitle: He has the kettle on already.

### 110. `dlg.chid.woke.1.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/woke#1; part 2 of 3: chid: You're up. A carter brought you in. / **narrator: He isn't looking at you.** / chid: ...Well. Someone did. You'll be sore a day or two, and whatever did this still has your th…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He isn't looking at you.
```
Subtitle: He isn't looking at you.

### 111. `dlg.chid.woke.2.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/woke#2; part 2 of 3: chid: You're awake! A carter found you. The same carter, as it happens; he's starting to think y… / **narrator: He laughs, and stops.** / chid: You'll be sore a day or two. Whatever did this is still out there. It'll have your things.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He laughs, and stops.
```
Subtitle: He laughs, and stops.

### 112. `dlg.chid.relight.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/relight#0
*Played:* plain; doing: the shrine is lit again; pace: slow; volume: quiet.
*Note:* The Order's words said with care; the kettle line plain.

```
[quietly] You open your lantern and say the words you learned at seven, the ones about the dark being only the part of the day that hasn't happened yet. The shrine takes the flame as if it had been waiting for it. Chid makes a sound like a kettle.
```
Subtitle: You open your lantern and say the words you learned at seven, the ones about the dark being only the part of the day that hasn't happened yet. The shrine takes the flame as if it had been waiting for it. Chid makes a sound like a kettle.

### 113. `dlg.chid.note.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/note#0; part 2 of 5: chid: Was there! / **narrator: He's suddenly very interested in a candle.** / chid: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, wh… / narrator: He stops. / chid: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's suddenly very interested in a candle.
```
Subtitle: He's suddenly very interested in a candle.

### 114. `dlg.chid.note.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/note#0; part 4 of 5: chid: Was there! / narrator: He's suddenly very interested in a candle. / chid: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, wh… / **narrator: He stops.** / chid: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He stops.
```
Subtitle: He stops.

### 115. `dlg.chid.cb_nell.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.chid.cb_nell.1.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/cb_nell#0; part 2 of 4: chid: I sang it flat. I always have. There's always somebody who has the tune. / **narrator: He is quiet, which he never is.** / chid: She was very light. ...Sit down a minute. / narrator: He moves up the bench, though there's nobody else on it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He is quiet, which he never is.
```
Subtitle: He is quiet, which he never is.

### 116. `dlg.chid.cb_nell.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.chid.cb_nell.1.p3.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/cb_nell#0; part 4 of 4: chid: I sang it flat. I always have. There's always somebody who has the tune. / narrator: He is quiet, which he never is. / chid: She was very light. ...Sit down a minute. / **narrator: He moves up the bench, though there's nobody else on it.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He moves up the bench, though there's nobody else on it.
```
Subtitle: He moves up the bench, though there's nobody else on it.

### 117. `dlg.chid.carter.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carter#0; part 2 of 3: chid: ...You know, I never asked his name. I should ask his name. Next time. / **narrator: He puts a cup in your hands.** / chid: Drink that. It's only hot water. There's nothing in it but hot.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts a cup in your hands.
```
Subtitle: He puts a cup in your hands.

### 118. `dlg.chid.carried.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carried#0

```
You wake on the bench in Chid's shrine, and it is morning. Your collar is stiff with a wolf's spit, dried. Nothing ate you. Something carried you out of the Hollow, and somebody else carried you home.
```
Subtitle: You wake on the bench in Chid's shrine, and it is morning. Your collar is stiff with a wolf's spit, dried. Nothing ate you. Something carried you out of the Hollow, and somebody else carried you home.

### 119. `dlg.chid.carried.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carried#1

```
You wake on the bench in Chid's shrine, and it is morning. Your hands are crossed on your chest, the way the Kerchiefs lay out their dead. You do not remember crossing them.
```
Subtitle: You wake on the bench in Chid's shrine, and it is morning. Your hands are crossed on your chest, the way the Kerchiefs lay out their dead. You do not remember crossing them.

### 120. `dlg.chid.carried.2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carried#2

```
You wake on the bench in Chid's shrine, and it is morning. There is lamp-soot all over your coat in small handprints, where a great many little hands lifted you, and then put you down.
```
Subtitle: You wake on the bench in Chid's shrine, and it is morning. There is lamp-soot all over your coat in small handprints, where a great many little hands lifted you, and then put you down.

### 121. `dlg.chid.carried.3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carried#3

```
You wake on the bench in Chid's shrine, and it is morning. Over your breastbone, faint as an old bruise, is the print of a mailed hand.
```
Subtitle: You wake on the bench in Chid's shrine, and it is morning. Over your breastbone, faint as an old bruise, is the print of a mailed hand.

### 122. `dlg.chid.carried.4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carried#4

```
You wake on the bench in Chid's shrine, and it is morning.
```
Subtitle: You wake on the bench in Chid's shrine, and it is morning.

### 123. `dlg.chid.carried_chid.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.chid.carried_chid.1.p1.wav`, `dlg.chid.carried_chid.2.p1.wav`, `dlg.chid.carried_chid.3.p1.wav`, `dlg.chid.carried_chid.4.p1.wav`, `dlg.chid.carried_chid.5.p1.wav`, `dlg.chid.carried_chid.6.p1.wav`, `dlg.chid.carried_chid.7.p1.wav`, `dlg.chid.carried_chid.8.p1.wav`, `dlg.chid.carried_chid.9.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/carried_chid#0; part 2 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / **narrator: He doesn't look at you.** / chid: Somebody brought you in. A carter, I expect. / narrator: He has a small book in both hands, held the way you hold a bird. / chid: I was keeping this for you. It's only an old office, what the keepers said at night. There…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't look at you.
```
Subtitle: He doesn't look at you.

### 124. `dlg.chid.carried_chid.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carried_chid#0; part 4 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / chid: Somebody brought you in. A carter, I expect. / **narrator: He has a small book in both hands, held the way you hold a bird.** / chid: I was keeping this for you. It's only an old office, what the keepers said at night. There…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He has a small book in both hands, held the way you hold a bird.
```
Subtitle: He has a small book in both hands, held the way you hold a bird.

### 125. `dlg.chid.carried_chid.7.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.chid.carried_chid.8.p3.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json chid/carried_chid#7; part 4 of 5: chid: You're awake! Good. Good. It's morning, and you've slept the whole night on my bench, and … / narrator: He doesn't look at you. / chid: Somebody brought you in from the old door. A carter, I expect. / **narrator: He's quiet a moment, which isn't like him.** / chid: I've read about the ones behind that door. In a very old book. Ask me, when you've eaten.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's quiet a moment, which isn't like him.
```
Subtitle: He's quiet a moment, which isn't like him.

### 126. `dlg.chid.carried_who.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/carried_who#0; part 2 of 3: chid: Oh, somebody kind. There are more of them about at night than you'd think. / **narrator: He busies himself with the kettle.** / chid: ...Eat something. The day's yours.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He busies himself with the kettle.
```
Subtitle: He busies himself with the kettle.

### 127. `dlg.chid.office.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/office#0; part 2 of 5: chid: You've been up the Tower. / **narrator: He doesn't ask what she told you. He has a small book in both hands, held the way you hold…** / chid: I want you to have this. It's only an old office: the watch-hours, what the keepers said a… / narrator: He opens it at the last page, and doesn't look at it. / chid: There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't ask what she told you. He has a small book in both hands, held the way you hold a bird.
```
Subtitle: He doesn't ask what she told you. He has a small book in both hands, held the way you hold a bird.

### 128. `dlg.chid.office.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/office#0; part 4 of 5: chid: You've been up the Tower. / narrator: He doesn't ask what she told you. He has a small book in both hands, held the way you hold… / chid: I want you to have this. It's only an old office: the watch-hours, what the keepers said a… / **narrator: He opens it at the last page, and doesn't look at it.** / chid: There's a bit at the end. You'll know it when you need it. ...Not now. It reads better in …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He opens it at the last page, and doesn't look at it.
```
Subtitle: He opens it at the last page, and doesn't look at it.

### 129. `dlg.chid.office_end.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/office_end#0; part 1 of 2: **narrator: He puts his hand over yours, flat on the cover.** / chid: Not now, I said! ...It's the end of the watch. One keeper asks, and the other one answers,…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts his hand over yours, flat on the cover.
```
Subtitle: He puts his hand over yours, flat on the cover.

### 130. `dlg.chid.names_write.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/names_write#0; part 1 of 2: **narrator: He watches you write it, and doesn't look at what.** / chid: Good. Keep it somewhere dry.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He watches you write it, and doesn't look at what.
```
Subtitle: He watches you write it, and doesn't look at what.

### 131. `dlg.chid.cut.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/cut#0; part 1 of 2: **narrator: There is a mallet and a chisel on the bench beside him, and he doesn't pick them up.** / chid: You've been to the garden. I saw. ...It wants a name, that marker. My hand's still steady,…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] There is a mallet and a chisel on the bench beside him, and he doesn't pick them up.
```
Subtitle: There is a mallet and a chisel on the bench beside him, and he doesn't pick them up.

### 132. `dlg.chid.cut_mam.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/cut_mam#0; part 2 of 3: chid: Mam. / **narrator: He says it over, under his breath, as if it might get away.** / chid: That's the first name anybody has. I'll cut it tonight.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He says it over, under his breath, as if it might get away.
```
Subtitle: He says it over, under his breath, as if it might get away.

### 133. `dlg.chid.cut_plain.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/cut_plain#0; part 1 of 2: **narrator: He nods.** / chid: Plain, then. The ground knows who's in it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He nods.
```
Subtitle: He nods.

### 134. `dlg.chid.cut_wait.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json chid/cut_wait#0; part 1 of 2: **narrator: He waits, and then he puts the chisel away.** / chid: It'll keep. Come and tell me when it comes to you.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He waits, and then he puts the chisel away.
```
Subtitle: He waits, and then he puts the chisel away.

## Conversations: Brannoc

### 135. `dlg.brannoc.first.0.p1.wav`  **LOCKED FOR RECORDING**

*The same words are also* `dlg.brannoc.first.1.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/first#0; part 2 of 5: brannoc: Hunter. Good. You'll know a clean pelt. Brannoc. Iron, and things with fur on. / **narrator: The hammer. He looks you over.** / brannoc: ...Came up the Low Ford road? Irons on it. Mine. Ten. / narrator: The hammer. / brannoc: Best I've done.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer. He looks you over.
```
Subtitle: The hammer. He looks you over.

### 136. `dlg.brannoc.first.0.p3.wav`  **LOCKED FOR RECORDING**

*The same words are also* `dlg.brannoc.first.1.p3.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/first#0; part 4 of 5: brannoc: Hunter. Good. You'll know a clean pelt. Brannoc. Iron, and things with fur on. / narrator: The hammer. He looks you over. / brannoc: ...Came up the Low Ford road? Irons on it. Mine. Ten. / **narrator: The hammer.** / brannoc: Best I've done.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer.
```
Subtitle: The hammer.

### 137. `dlg.brannoc.hub.2.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/hub#2; part 1 of 2: **narrator: He works one-handed; the other hand is bound in rag. He doesn't stop when you come in, and…** / brannoc: Steel or fur?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He works one-handed; the other hand is bound in rag. He doesn't stop when you come in, and he doesn't send you away.
```
Subtitle: He works one-handed; the other hand is bound in rag. He doesn't stop when you come in, and he doesn't send you away.

### 138. `dlg.brannoc.irons.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/irons#0; part 1 of 2: **narrator: He looks at the two irons on the rack for a long time.** / brannoc: Twelve ordered. Ten went down to the ford, at night, square coin on the anvil. ...Buyer'll…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at the two irons on the rack for a long time.
```
Subtitle: He looks at the two irons on the rack for a long time.

### 139. `dlg.brannoc.irons.1.p1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/irons#1; part 2 of 3: brannoc: Spares. Twelve ordered for the Low Ford, last winter. Ten collected, at night, coin left o… / **narrator: He runs his thumb along one.** / brannoc: Didn't ask who. Paid for my girl's boots.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He runs his thumb along one.
```
Subtitle: He runs his thumb along one.

### 140. `dlg.brannoc.mark.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/mark#0; part 1 of 4: **narrator: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is.** / brannoc: Mine. / narrator: He holds it a long time. / brannoc: ...Mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is.
```
Subtitle: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is.

### 141. `dlg.brannoc.mark.0.p2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/mark#0; part 3 of 4: narrator: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is. / brannoc: Mine. / **narrator: He holds it a long time.** / brannoc: ...Mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He holds it a long time.
```
Subtitle: He holds it a long time.

### 142. `dlg.brannoc.mark.1.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/mark#1; part 1 of 6: **narrator: He takes it. Turns it to the light. Puts his thumb under the socket.** / brannoc: Mine. Mark's under there. / narrator: He weighs it. / brannoc: Thing in the water had it? ...Took it off a post, then. Good iron. Held. / narrator: He gives it back. / brannoc: Keep it. It'll hold.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes it. Turns it to the light. Puts his thumb under the socket.
```
Subtitle: He takes it. Turns it to the light. Puts his thumb under the socket.

### 143. `dlg.brannoc.mark.1.p2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/mark#1; part 3 of 6: narrator: He takes it. Turns it to the light. Puts his thumb under the socket. / brannoc: Mine. Mark's under there. / **narrator: He weighs it.** / brannoc: Thing in the water had it? ...Took it off a post, then. Good iron. Held. / narrator: He gives it back. / brannoc: Keep it. It'll hold.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He weighs it.
```
Subtitle: He weighs it.

### 144. `dlg.brannoc.mark.1.p4.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/mark#1; part 5 of 6: narrator: He takes it. Turns it to the light. Puts his thumb under the socket. / brannoc: Mine. Mark's under there. / narrator: He weighs it. / brannoc: Thing in the water had it? ...Took it off a post, then. Good iron. Held. / **narrator: He gives it back.** / brannoc: Keep it. It'll hold.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He gives it back.
```
Subtitle: He gives it back.

### 145. `dlg.brannoc.irons_after.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/irons_after#0; part 1 of 4: **narrator: He puts his hand flat on the two irons.** / brannoc: Buyer'll be back for these. Buyer can come and ask me himself. Or herself. / narrator: The hammer comes down. / brannoc: I'll know the coin.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts his hand flat on the two irons.
```
Subtitle: He puts his hand flat on the two irons.

### 146. `dlg.brannoc.irons_after.0.p2.wav`  **LOCKED FOR RECORDING**

*The same words are also* `dlg.brannoc.nell_lie.0.p0.wav`, `dlg.brannoc.nell_look.0.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/irons_after#0; part 3 of 4: narrator: He puts his hand flat on the two irons. / brannoc: Buyer'll be back for these. Buyer can come and ask me himself. Or herself. / **narrator: The hammer comes down.** / brannoc: I'll know the coin.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer comes down.
```
Subtitle: The hammer comes down.

### 147. `dlg.brannoc.nell.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell#0; part 1 of 4: **narrator: He doesn't look up from the anvil, and he doesn't stop.** / brannoc: You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the gray m… / narrator: The hammer stops. / brannoc: Mine. Nell. ...You pass them?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't look up from the anvil, and he doesn't stop.
```
Subtitle: He doesn't look up from the anvil, and he doesn't stop.

### 148. `dlg.brannoc.nell.0.p2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell#0; part 3 of 4: narrator: He doesn't look up from the anvil, and he doesn't stop. / brannoc: You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the gray m… / **narrator: The hammer stops.** / brannoc: Mine. Nell. ...You pass them?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer stops.
```
Subtitle: The hammer stops.

### 149. `dlg.brannoc.nell_ditch.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_ditch#0; part 1 of 2: **narrator: He puts the hammer down. You have never seen him put the hammer down.** / brannoc: ...Had the reins. She'd want the reins. Always wanted the reins.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts the hammer down. You have never seen him put the hammer down.
```
Subtitle: He puts the hammer down. You have never seen him put the hammer down.

### 150. `dlg.brannoc.nell_gone.0.p1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_gone#0; part 2 of 2: brannoc: Quick, then. Water's quick. / **narrator: He picks the hammer up and holds it, and doesn't use it.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He picks the hammer up and holds it, and doesn't use it.
```
Subtitle: He picks the hammer up and holds it, and doesn't use it.

### 151. `dlg.brannoc.nell_risen.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_risen#0; part 1 of 4: **narrator: He looks at you then. Properly, for the first time.** / brannoc: Got up. / narrator: He says it the way he tests an edge. / brannoc: Got up, and you put her down. ...Was it quick?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you then. Properly, for the first time.
```
Subtitle: He looks at you then. Properly, for the first time.

### 152. `dlg.brannoc.nell_risen.0.p2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_risen#0; part 3 of 4: narrator: He looks at you then. Properly, for the first time. / brannoc: Got up. / **narrator: He says it the way he tests an edge.** / brannoc: Got up, and you put her down. ...Was it quick?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He says it the way he tests an edge.
```
Subtitle: He says it the way he tests an edge.

### 153. `dlg.brannoc.nell_quick.0.p0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `dlg.rav.leg_held.0.p2.wav`, `dlg.scene_knocking.tell.0.p4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/nell_quick#0; part 1 of 2: **narrator: A long time.** / brannoc: ...Thank you.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A long time.
```
Subtitle: A long time.

### 154. `dlg.brannoc.nell_slow.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_slow#0
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He nods, once, as if you've told him a price.
```
Subtitle: He nods, once, as if you've told him a price.

### 155. `dlg.brannoc.nell_lie.0.p2.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_lie#0; part 3 of 4: narrator: The hammer comes down. / brannoc: Low Kiln, then. Good. / **narrator: And again.** / brannoc: Aunt'll feed her up. She's thin.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] And again.
```
Subtitle: And again.

### 156. `dlg.brannoc.fang.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/fang#0; part 1 of 2: **narrator: He holds it up to the forge-light and turns it.** / brannoc: Worn flat on the one side. He chewed on that side.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He holds it up to the forge-light and turns it.
```
Subtitle: He holds it up to the forge-light and turns it.

### 157. `dlg.brannoc.nell_iron.0.p0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `dlg.brannoc.nell_iron.1.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/nell_iron#0; part 1 of 2: **narrator: His eyes go to the iron at your belt, and stay there.** / brannoc: ...That was in its hand. The thing in the water.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] His eyes go to the iron at your belt, and stay there.
```
Subtitle: His eyes go to the iron at your belt, and stay there.

### 158. `dlg.brannoc.nell_iron.2.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_iron#2; part 1 of 2: **narrator: He looks at the two irons on the rack, and then at you.** / brannoc: The thing in the water. What was it carrying.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at the two irons on the rack, and then at you.
```
Subtitle: He looks at the two irons on the rack, and then at you.

### 159. `dlg.brannoc.nell_hand.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_hand#0; part 1 of 2: **narrator: He holds out his hand. You put the iron in it. He turns it to the forge, and his thumb goe…** / brannoc: Lifts it up. To see your face. ...Does it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He holds out his hand. You put the iron in it. He turns it to the forge, and his thumb goes under the socket and finds the mark without looking.
```
Subtitle: He holds out his hand. You put the iron in it. He turns it to the forge, and his thumb goes under the socket and finds the mark without looking.

### 160. `dlg.brannoc.nell_told.0.p0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `dlg.jory.truth_ask.0.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/nell_told#0; part 1 of 2: **narrator: He doesn't move.** / brannoc: Lifts it up. To see your face. ...Does it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't move.
```
Subtitle: He doesn't move.

### 161. `dlg.brannoc.nell_letters.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_letters#0; part 1 of 2: **narrator: The forge ticks. He does not move for a long time.** / brannoc: Knew my mark before she knew her letters.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The forge ticks. He does not move for a long time.
```
Subtitle: The forge ticks. He does not move for a long time.

### 162. `dlg.brannoc.nell_thought.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_thought#0; part 1 of 2: **narrator: Longer.** / brannoc: She'd have thought I'd come for her.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Longer.
```
Subtitle: Longer.

### 163. `dlg.brannoc.nell_shut.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_shut#0; part 1 of 2: **narrator: Nothing. Then he gives you the iron back, carefully, the way you'd hand someone a thing th…** / brannoc: Forge is shut.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Nothing. Then he gives you the iron back, carefully, the way you'd hand someone a thing that was still hot. On the anvil the bar goes from orange to gray.
```
Subtitle: Nothing. Then he gives you the iron back, carefully, the way you'd hand someone a thing that was still hot. On the anvil the bar goes from orange to gray.

### 164. `dlg.brannoc.nell_shut.1.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_shut#1; part 1 of 2: **narrator: Nothing. On the anvil the bar goes from orange to gray.** / brannoc: Forge is shut.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Nothing. On the anvil the bar goes from orange to gray.
```
Subtitle: Nothing. On the anvil the bar goes from orange to gray.

### 165. `dlg.brannoc.nell_lantern.0.p0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_lantern#0; part 1 of 2: **narrator: He takes the lantern down off its hook, and lights it, and takes a blanket off the shelf.** / brannoc: You know the place.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes the lantern down off its hook, and lights it, and takes a blanket off the shelf.
```
Subtitle: He takes the lantern down off its hook, and lights it, and takes a blanket off the shelf.

### 166. `dlg.brannoc.nell_with.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_with#0
*Played:* volume: quiet.

```
[quietly] He doesn't wait for anything else. He goes out, and you go with him, down toward the south gate.
```
Subtitle: He doesn't wait for anything else. He goes out, and you go with him, down toward the south gate.

### 167. `dlg.brannoc.nell_alone.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/nell_alone#0
*Played:* volume: quiet.

```
[quietly] He nods, once, and goes out past you with the lantern and the blanket, down toward the south gate.
```
Subtitle: He nods, once, and goes out past you with the lantern and the blanket, down toward the south gate.

### 168. `dlg.brannoc.dusk_call.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/dusk_call#0
*Played:* volume: quiet.

```
[quietly] The forge is banked, but Brannock is still at the anvil, and when you pass he calls you over without looking up.
```
Subtitle: The forge is banked, but Brannoc is still at the anvil, and when you pass he calls you over without looking up.

### 169. `dlg.brannoc.dusk_call.1.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json brannoc/dusk_call#1
*Played:* volume: quiet.

```
[quietly] As the light goes, the hammer at the smithy stops. Brannock calls you over, without looking up.
```
Subtitle: As the light goes, the hammer at the smithy stops. Brannoc calls you over, without looking up.

## Conversations: Holloway

### 170. `dlg.holloway.first.1.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/first#1; part 2 of 3: holloway: You're the one put the Ford-Warden down. / **narrator: He looks at you a moment longer than he means to.** / holloway: The Watch kept that crossing, once. Then we couldn't. ...Thank you. Holloway. Captain of w…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you a moment longer than he means to.
```
Subtitle: He looks at you a moment longer than he means to.

### 171. `dlg.holloway.hub.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/hub#0; part 1 of 2: **narrator: A letter lies open on his knee under the gate-lamp, a silver seal broken on it. He turns i…** / holloway: What.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A letter lies open on his knee under the gate-lamp, a silver seal broken on it. He turns it over when you come, and puts his cup on it.
```
Subtitle: A letter lies open on his knee under the gate-lamp, a silver seal broken on it. He turns it over when you come, and puts his cup on it.

### 172. `dlg.holloway.hub.1.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/hub#1; part 1 of 4: **narrator: On the ground in the gateway, his back to the post, a cup in his fist.** / holloway: Gate open. Count short. Cup empty. / narrator: He finds you. / holloway: You. What.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] On the ground in the gateway, his back to the post, a cup in his fist.
```
Subtitle: On the ground in the gateway, his back to the post, a cup in his fist.

### 173. `dlg.holloway.hub.1.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.holloway.roll.0.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json holloway/hub#1; part 3 of 4: narrator: On the ground in the gateway, his back to the post, a cup in his fist. / holloway: Gate open. Count short. Cup empty. / **narrator: He finds you.** / holloway: You. What.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He finds you.
```
Subtitle: He finds you.

### 174. `dlg.holloway.hub.2.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/hub#2; part 1 of 4: **narrator: On the ground in the gateway, his back to the post, a cup in his fist, counting under his …** / holloway: ...Forty-four. Forty— / narrator: He loses it, and starts again at one. / holloway: What.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] On the ground in the gateway, his back to the post, a cup in his fist, counting under his breath.
```
Subtitle: On the ground in the gateway, his back to the post, a cup in his fist, counting under his breath.

### 175. `dlg.holloway.hub.2.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/hub#2; part 3 of 4: narrator: On the ground in the gateway, his back to the post, a cup in his fist, counting under his … / holloway: ...Forty-four. Forty— / **narrator: He loses it, and starts again at one.** / holloway: What.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He loses it, and starts again at one.
```
Subtitle: He loses it, and starts again at one.

### 176. `dlg.holloway.hub.6.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/hub#6; part 1 of 2: **narrator: He straightens when you come in, and then looks annoyed that he did.** / holloway: You. What is it?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He straightens when you come in, and then looks annoyed that he did.
```
Subtitle: He straightens when you come in, and then looks annoyed that he did.

### 177. `dlg.holloway.ashford.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.rav.cb_killed_redcowl.0.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json holloway/ashford#0; part 2 of 5: holloway: Then don't. / **narrator: He doesn't look up.** / holloway: ...Garrison town, up the valley. The ground went one night, and the lower town with it. I … / narrator: He picks up the cup. / holloway: That's the report.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't look up.
```
Subtitle: He doesn't look up.

### 178. `dlg.holloway.ashford.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/ashford#0; part 4 of 5: holloway: Then don't. / narrator: He doesn't look up. / holloway: ...Garrison town, up the valley. The ground went one night, and the lower town with it. I … / **narrator: He picks up the cup.** / holloway: That's the report.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He picks up the cup.
```
Subtitle: He picks up the cup.

### 179. `dlg.holloway.cb_freed_teamsters.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/cb_freed_teamsters#0; part 1 of 4: **narrator: He's been drinking since dawn, and he's not hiding it.** / holloway: Three in! I was on the gate. Three in, and the count's— hell, I don't know what the count … / narrator: He sits down hard. / holloway: Don't let it go to your head. Eleven Watchmen couldn't do it. Eleven Watchmen can't do muc…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's been drinking since dawn, and he's not hiding it.
```
Subtitle: He's been drinking since dawn, and he's not hiding it.

### 180. `dlg.holloway.cb_freed_teamsters.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/cb_freed_teamsters#0; part 3 of 4: narrator: He's been drinking since dawn, and he's not hiding it. / holloway: Three in! I was on the gate. Three in, and the count's— hell, I don't know what the count … / **narrator: He sits down hard.** / holloway: Don't let it go to your head. Eleven Watchmen couldn't do it. Eleven Watchmen can't do muc…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He sits down hard.
```
Subtitle: He sits down hard.

### 181. `dlg.holloway.say_calling.2.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/say_calling#2; part 2 of 3: holloway: Burns, does it? What's it run on? / **narrator: He looks at your hands.** / holloway: Everything runs on something. I'll want it written down.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at your hands.
```
Subtitle: He looks at your hands.

### 182. `dlg.holloway.ledger_early.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/ledger_early#0; part 1 of 4: **narrator: He reads it standing up. Then he sits down and reads it again.** / holloway: Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's cler… / narrator: He shuts it. / holloway: Don't tell me where you got it. If you tell me, I have to do something about it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He reads it standing up. Then he sits down and reads it again.
```
Subtitle: He reads it standing up. Then he sits down and reads it again.

### 183. `dlg.holloway.ledger_early.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/ledger_early#0; part 3 of 4: narrator: He reads it standing up. Then he sits down and reads it again. / holloway: Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's cler… / **narrator: He shuts it.** / holloway: Don't tell me where you got it. If you tell me, I have to do something about it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He shuts it.
```
Subtitle: He shuts it.

### 184. `dlg.holloway.post.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/post#0; part 1 of 2: **narrator: He says nothing for long enough that you think he hasn't heard.** / holloway: Gray beard, proud of it? Bad hip? ...Corran. He had that post before I had this one. I wro…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He says nothing for long enough that you think he hasn't heard.
```
Subtitle: He says nothing for long enough that you think he hasn't heard.

### 185. `dlg.holloway.post2.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/post2#0; part 2 of 3: holloway: Not by us. We've not had oil for those lamps since my first winter, and nobody's asked me … / **narrator: He writes something down, and crosses it out.** / holloway: So somebody had ember, and irons to burn it in. And a reason. ...I'll send two men down wi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He writes something down, and crosses it out.
```
Subtitle: He writes something down, and crosses it out.

### 186. `dlg.holloway.letter.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/letter#0; part 2 of 3: holloway: Mine. From the north, about the north. / **narrator: The cup doesn't move.** / holloway: Read your own post, if anybody writes to you.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The cup doesn't move.
```
Subtitle: The cup doesn't move.

### 187. `dlg.holloway.roll.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/roll#0; part 1 of 4: **narrator: He isn't looking at you. He's looking down the dark road, and his lips are moving.** / holloway: ...Abbot. Two bairns. Ancell. His mam. Bede. Nobody. Carrow. A wife, and one coming. / narrator: He finds you. / holloway: Garrison. The roll. I say it at night. Keeps them in order.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He isn't looking at you. He's looking down the dark road, and his lips are moving.
```
Subtitle: He isn't looking at you. He's looking down the dark road, and his lips are moving.

### 188. `dlg.holloway.roll2.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json holloway/roll2#0; part 2 of 2: holloway: Dunning. Two bairns. Ede. Her da. Fenn. Nobody. Gale. ...Gale. / **narrator: He stops on it, and drinks, and starts again at Abbot.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He stops on it, and drinks, and starts again at Abbot.
```
Subtitle: He stops on it, and drinks, and starts again at Abbot.

## Conversations: Tam

### 189. `dlg.tam.fetch.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json tam/fetch#0
*Played:* plain; doing: bringing Tam's father home; pace: measured; volume: level.
*Note:* Plain; 'But he comes.' short.

```
You walk the boy as far as the fence where his Pa lost the goat, and go on into the trees for his Pa. He calls you several things on the way back, and one of them is a fool. But he comes.
```
Subtitle: You walk the boy as far as the fence where his Pa lost the goat, and go on into the trees for his Pa. He calls you several things on the way back, and one of them is a fool. But he comes.

## Conversations: Maeca

### 190. `dlg.maeca.hub.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.maeca.say_sella.0.p1.wav`, `dlg.maeca.ashford.0.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json maeca/hub#0; part 1 of 2: **narrator: She doesn't look up from her cup.** / maeca: It's late. Say it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't look up from her cup.
```
Subtitle: She doesn't look up from her cup.

### 191. `dlg.maeca.invite.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/invite#0; part 1 of 2: **narrator: She finishes her cup and stands.** / maeca: I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She finishes her cup and stands.
```
Subtitle: She finishes her cup and stands.

### 192. `dlg.maeca.blind.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind#0; part 1 of 3: **narrator: Off in the Hollow the Pack is loud, a long tangle of voices, and she stops with her hands …** / maeca: They're eating. / narrator: She pulls you down onto the hides. Her hands are hard and careful, the way they are with a…

```
Off in the Hollow the Pack is loud, a long tangle of voices, and she stops with her hands on your buckle and listens, and then she laughs: a short surprised sound, as if she'd trodden on something.
```
Subtitle: Off in the Hollow the Pack is loud, a long tangle of voices, and she stops with her hands on your buckle and listens, and then she laughs: a short surprised sound, as if she'd trodden on something.

### 193. `dlg.maeca.blind.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind#0; part 3 of 3: narrator: Off in the Hollow the Pack is loud, a long tangle of voices, and she stops with her hands … / maeca: They're eating. / **narrator: She pulls you down onto the hides. Her hands are hard and careful, the way they are with a…**

```
She pulls you down onto the hides. Her hands are hard and careful, the way they are with a snare, and then they're not careful. The fire goes down to embers. Neither of you feeds it. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.
```
Subtitle: She pulls you down onto the hides. Her hands are hard and careful, the way they are with a snare, and then they're not careful. The fire goes down to embers. Neither of you feeds it. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.

### 194. `dlg.maeca.blind.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind#1
*Played:* plain; doing: a night with Maeca; pace: slow; volume: quiet.
*Note:* Low and close, unhurried; he is not in the bed. Her words are hers.

```
[quietly] She doesn't talk, and then neither of you needs to. She comes round the fire to you, and that seems to be a decision. Her hands are hard and careful, the way they are with a snare: slow, listening, ready to stop. They become sure. Once, far off, the Pack calls, and she goes still against you until it's done. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.
```
Subtitle: She doesn't talk, and then neither of you needs to. She comes round the fire to you, and that seems to be a decision. Her hands are hard and careful, the way they are with a snare: slow, listening, ready to stop. They become sure. Once, far off, the Pack calls, and she goes still against you until it's done. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.

### 195. `dlg.maeca.blind_morning.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_morning#0; part 1 of 2: **narrator: Gray light. She's already up, barefoot in the frost, listening.** / maeca: Go on, then. The wood's awake, and so's Holloway, and he'll count us both.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Gray light. She's already up, barefoot in the frost, listening.
```
Subtitle: Gray light. She's already up, barefoot in the frost, listening.

### 196. `dlg.maeca.blind_morning.1.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_morning#1; part 1 of 2: **narrator: Gray light. She's already up, barefoot in the frost, listening to the wood.** / maeca: The Pack found me, after Ashford. A cave mouth, and a lad I'd been fond of dying in it. Th…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Gray light. She's already up, barefoot in the frost, listening to the wood.
```
Subtitle: Gray light. She's already up, barefoot in the frost, listening to the wood.

### 197. `dlg.maeca.kerchiefs.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/kerchiefs#0; part 2 of 3: maeca: Some. / **narrator: She drinks, and looks at the cup instead of you.** / maeca: Fed some of them, once. Buried more. ...Ask me about wolves.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She drinks, and looks at the cup instead of you.
```
Subtitle: She drinks, and looks at the cup instead of you.

### 198. `dlg.maeca.cb_knelt.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/cb_knelt#0; part 2 of 3: maeca: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge. / **narrator: She looks at your knees.** / maeca: He let you. ...He doesn't let me, and he's known me ten years.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at your knees.
```
Subtitle: She looks at your knees.

### 199. `dlg.maeca.blood.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blood#0; part 1 of 2: **narrator: At the edge of the Hollow she stops, and sniffs, once, and turns round.** / maeca: Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night ta…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] At the edge of the Hollow she stops, and sniffs, once, and turns round.
```
Subtitle: At the edge of the Hollow she stops, and sniffs, once, and turns round.

### 200. `dlg.maeca.blind_walk.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_walk#0; part 1 of 3: **narrator: She goes out by the east gate without a lamp, and you follow her along the Old Road past t…** / maeca: Him. And the bitch with the white foot. / narrator: She walks on.
*Played:* plain; doing: the walk to the Blind; pace: slow; volume: quiet.
*Note:* Narrator plain and starlit; a beat before 'and is answered'. Maeca just above a breath, naming neighbours by their voices. Narrator plain: the narrator never shows a feeling.

```
[quietly] She goes out by the east gate without a lamp, and you follow her along the Old Road past the wreck, by starlight and the white of the frost. She doesn't make a sound. Once she stops, and you stop, and somewhere off in the Hollow a wolf calls and is answered.
```
Subtitle: She goes out by the east gate without a lamp, and you follow her along the Old Road past the wreck, by starlight and the white of the frost. She doesn't make a sound. Once she stops, and you stop, and somewhere off in the Hollow a wolf calls and is answered.

### 201. `dlg.maeca.blind_walk.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_walk#0; part 3 of 3: narrator: She goes out by the east gate without a lamp, and you follow her along the Old Road past t… / maeca: Him. And the bitch with the white foot. / **narrator: She walks on.**
*Played:* plain; doing: the walk to the Blind; pace: slow; volume: quiet.
*Note:* Narrator plain and starlit; a beat before 'and is answered'. Maeca just above a breath, naming neighbours by their voices. Narrator plain: the narrator never shows a feeling.

```
[quietly] She walks on.
```
Subtitle: She walks on.

### 202. `dlg.maeca.blind_walk.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_walk#1
*Played:* plain; doing: she lets you lead; pace: slow; volume: quiet.
*Note:* Narrator plain: the narrator never shows a feeling. The gift is the fact itself; don't lean on it.

```
[quietly] The Old Road, the wreck, the frost. You know the way now, and she lets you walk in front.
```
Subtitle: The Old Road, the wreck, the frost. You know the way now, and she lets you walk in front.

### 203. `dlg.maeca.blind_fire.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_fire#0
*Played:* plain; doing: the Blind; pace: slow; volume: quiet.
*Note:* One action at a time; the look across the fire held.

```
[quietly] The Hunters' Blind is a lean-to of hides against a fallen oak, with a fire the size of a hat. She sits, and pulls her boots off first thing, and sets her bare feet flat on the cold ground, as if she were listening through them. She feeds the fire one stick at a time. She doesn't talk. After a while she takes the crossbow off her back, and checks it, and lays it down by her right hand, and turns and looks at you across the fire as if you were a track she has been following for days.
```
Subtitle: The Hunters' Blind is a lean-to of hides against a fallen oak, with a fire the size of a hat. She sits, and pulls her boots off first thing, and sets her bare feet flat on the cold ground, as if she were listening through them. She feeds the fire one stick at a time. She doesn't talk. After a while she takes the crossbow off her back, and checks it, and lays it down by her right hand, and turns and looks at you across the fire as if you were a track she has been following for days.

### 204. `dlg.maeca.blind_ask.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_ask#1
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She holds out her hand. That's all.
```
Subtitle: She holds out her hand. That's all.

### 205. `dlg.maeca.blind_leave.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_leave#0; part 1 of 2: **narrator: She nods at the fire.** / maeca: Mind the frost on the Old Road. It's worse by the wreck.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She nods at the fire.
```
Subtitle: She nods at the fire.

### 206. `dlg.maeca.watch_only.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/watch_only#0
*Played:* plain; doing: a night keeping watch; pace: slow; volume: quiet.
*Note:* Plain and slow.

```
[quietly] You keep the fire. She keeps the dark. Some time after midnight she comes in from the edge of the light and sits down with her back against yours, and you can feel her breathing, slow, and listening. You sleep like that, sitting up. In the morning the frost is on both your shoulders and not between them.
```
Subtitle: You keep the fire. She keeps the dark. Some time after midnight she comes in from the edge of the light and sits down with her back against yours, and you can feel her breathing, slow, and listening. You sleep like that, sitting up. In the morning the frost is on both your shoulders and not between them.

### 207. `dlg.maeca.watch_morning.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/watch_morning#0; part 2 of 3: maeca: You kept quiet. / **narrator: She stands, and stretches, and looks at the Hollow, not you.** / maeca: Most can't.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She stands, and stretches, and looks at the Hollow, not you.
```
Subtitle: She stands, and stretches, and looks at the Hollow, not you.

### 208. `dlg.maeca.blind_dark.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_dark#0
*Played:* plain; doing: you're cold; pace: slow; volume: quiet.
*Note:* The inversion (your skin colder than her feet) is nearly funny: straight and level, don't darken it. The last sentence hangs, not drops: the player's choice follows.

```
[quietly] Afterwards, in the dark under the hides, she puts her feet against your legs… and flinches… you're colder than they are. She starts to take them back—
```
Subtitle: Afterwards, in the dark under the hides, she puts her feet against your legs, and flinches: you're colder than they are. She starts to take them back.

### 209. `dlg.maeca.blind_dark.1.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_dark#1; part 1 of 6: **narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis…** / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* plain; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[quietly] Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow. Outside, in the frost, you hear them come: soft feet, a long way round, and then a sigh, and then another. The Pack, lying down round the Blind in the dark. She lifts her head.
```
Subtitle: Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow. Outside, in the frost, you hear them come: soft feet, a long way round, and then a sigh, and then another. The Pack, lying down round the Blind in the dark. She lifts her head.

### 210. `dlg.maeca.blind_dark.1.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_dark#1; part 3 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / **narrator: She lies back down, her ear where it was.** / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* plain; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[quietly] She lies back down, her ear where it was.
```
Subtitle: She lies back down, her ear where it was.

### 211. `dlg.maeca.blind_dark.1.p4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.maeca.blind_dark.2.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json maeca/blind_dark#1; part 5 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / **narrator: Against your chest you feel her lips move, without a sound.** / maeca: What were you?
*Played:* plain; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[quietly] Against your chest you feel her lips move, without a sound.
```
Subtitle: Against your chest you feel her lips move, without a sound.

### 212. `dlg.maeca.blind_dark.2.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_dark#2; part 1 of 4: **narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis…** / maeca: You walk quiet. You never talk about before. / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* plain; doing: she asks what you were; pace: slow; volume: quiet.
*Hides:* she is counting your heart between her sentences
*Note:* As blind_dark.1 without the Pack. 'What were you?' careful, no stress on 'were', after a real count of about three seconds.

```
[quietly] Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow.
```
Subtitle: Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow.

### 213. `dlg.maeca.blind_dark.3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind_dark#3
*Played:* plain; doing: quiet; pace: slow; volume: quiet.
*Note:* Plain.

```
[quietly] The fire's down to embers. Far off, the Pack is quiet.
```
Subtitle: The fire's down to embers. Far off, the Pack is quiet.

### 214. `dlg.maeca.blind2_feet.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind2_feet#0; part 1 of 4: **narrator: You take one in your hands. The sole is hard as boot leather, and scarred: old white lines…** / maeca: Your hands are colder than my feet. / narrator: She doesn't take them back. / maeca: Hold them anyway. ...Nobody's held those.
*Played:* plain; doing: her scarred feet; pace: slow; volume: quiet.
*Note:* The scars described plainly; her words are hers.

```
[quietly] You take one in your hands. The sole is hard as boot leather, and scarred: old white lines across the ball of the foot, a ridge along the heel where something cut it to the bone a long time ago and it healed badly in the cold. She lets you hold it. She lets you hold the other. She lies very still, the way she lay still when the Pack called, and doesn't say anything for a long time. Then, into the dark, very low:
```
Subtitle: You take one in your hands. The sole is hard as boot leather, and scarred: old white lines across the ball of the foot, a ridge along the heel where something cut it to the bone a long time ago and it healed badly in the cold. She lets you hold it. She lets you hold the other. She lies very still, the way she lay still when the Pack called, and doesn't say anything for a long time. Then, into the dark, very low:

### 215. `dlg.maeca.blind2_feet.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind2_feet#0; part 3 of 4: narrator: You take one in your hands. The sole is hard as boot leather, and scarred: old white lines… / maeca: Your hands are colder than my feet. / **narrator: She doesn't take them back.** / maeca: Hold them anyway. ...Nobody's held those.
*Played:* plain; doing: her scarred feet; pace: slow; volume: quiet.
*Note:* The scars described plainly; her words are hers.

```
[quietly] She doesn't take them back.
```
Subtitle: She doesn't take them back.

### 216. `dlg.maeca.blind2_let.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind2_let#0
*Played:* plain; doing: she curls up; pace: slow; volume: quiet.
*Note:* Plain.

```
[quietly] She tucks them up under her instead, the way a dog curls its nose under its tail, and goes to sleep. In the night, half awake, you feel her put them back against you, slowly, as if she was trying it out.
```
Subtitle: She tucks them up under her instead, the way a dog curls its nose under its tail, and goes to sleep. In the night, half awake, you feel her put them back against you, slowly, as if she was trying it out.

### 217. `dlg.maeca.told_true.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/told_true#0; part 2 of 3: maeca: Thought so. You put your feet down like you're asking the ground first. / **narrator: She almost smiles.** / maeca: I'd have liked you, then. Probably would have shot you for poaching.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She almost smiles.
```
Subtitle: She almost smiles.

### 218. `dlg.maeca.told_true.1.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/told_true#1; part 2 of 3: maeca: Letters. / **narrator: She thinks about it.** / maeca: Tracks for people who sit still. ...Read me something, one day. Not now.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She thinks about it.
```
Subtitle: She thinks about it.

### 219. `dlg.maeca.told_little.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/told_little#0; part 1 of 4: **narrator: She doesn't push.** / maeca: All right. / narrator: And it is. / maeca: ...Keep it, then. I keep mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't push.
```
Subtitle: She doesn't push.

### 220. `dlg.maeca.told_little.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/told_little#0; part 3 of 4: narrator: She doesn't push. / maeca: All right. / **narrator: And it is.** / maeca: ...Keep it, then. I keep mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] And it is.
```
Subtitle: And it is.

### 221. `dlg.maeca.blind3_morning.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind3_morning#0; part 1 of 6: **narrator: Gray light. She's awake before you, as always, but she hasn't got up. Her head is still on…** / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Gray light. She's awake before you, as always, but she hasn't got up. Her head is still on your chest. Her face is very still.
```
Subtitle: Gray light. She's awake before you, as always, but she hasn't got up. Her head is still on your chest. Her face is very still.

### 222. `dlg.maeca.blind3_morning.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind3_morning#0; part 3 of 6: narrator: Gray light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / **narrator: She doesn't lift her head.** / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't lift her head.
```
Subtitle: She doesn't lift her head.

### 223. `dlg.maeca.blind3_morning.0.p4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/blind3_morning#0; part 5 of 6: narrator: Gray light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / **narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the…** / maeca: Go on. Holloway'll count us.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She gets up, then, and goes out barefoot into the frost, and stands there listening to the wood with her back to you.
```
Subtitle: She gets up, then, and goes out barefoot into the frost, and stands there listening to the wood with her back to you.

### 224. `dlg.maeca.say_sella.1.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/say_sella#1; part 2 of 3: maeca: You go up Sella's stairs. Rook talks. / **narrator: A shrug.** / maeca: She's honest about what she charges. That's more than most.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A shrug.
```
Subtitle: A shrug.

### 225. `dlg.maeca.say_sella_both.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/say_sella_both#0; part 1 of 2: **narrator: A nod.** / maeca: Good. Now I know.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A nod.
```
Subtitle: A nod.

### 226. `dlg.maeca.say_sella_you.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/say_sella_you#0; part 1 of 2: **narrator: She looks at you, long, the way she looks at a track that might be lying.** / maeca: We'll see.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you, long, the way she looks at a track that might be lying.
```
Subtitle: She looks at you, long, the way she looks at a track that might be lying.

### 227. `dlg.maeca.shed_fur_braid.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/shed_fur_braid#0; part 1 of 2: **narrator: She sits with her back to the fire and braids it on her knee, gray and gray and white, the…** / maeca: Next to the skin. They'll know you in the dark.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She sits with her back to the fire and braids it on her knee, gray and gray and white, the way you'd braid a child's hair. She doesn't talk. When it's done she bites the end off.
```
Subtitle: She sits with her back to the fire and braids it on her knee, gray and gray and white, the way you'd braid a child's hair. She doesn't talk. When it's done she bites the end off.

### 228. `dlg.maeca.fire.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.scene_did_he.told.0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json maeca/fire#0; part 1 of 2: **narrator: She looks at you for a long time.** / maeca: If you're going in there with a blade, I'll not help you. ...Take fire, and feed it. They …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you for a long time.
```
Subtitle: She looks at you for a long time.

### 229. `dlg.maeca.watch.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json maeca/watch#0; part 2 of 3: maeca: Men. Deserters, mostly, and the ones the road loses. The Watch won't pay for it, so Hollow… / **narrator: She drinks.** / maeca: I take it. Every week. ...He'd pay me double, if I let him. I don't let him.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She drinks.
```
Subtitle: She drinks.

## Conversations: Harlan

### 230. `dlg.harlan.first.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/first#0; part 2 of 3: harlan: You. Jory says it was you at the cage with the bar in your hands, and he's told it four ti… / **narrator: He takes your hand in both of his.** / harlan: Harlan Coyle, of the Coyle Company. Any other day I'd have said that first.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes your hand in both of his.
```
Subtitle: He takes your hand in both of his.

### 231. `dlg.harlan.first.1.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/first#1; part 1 of 2: **narrator: The shutters are half closed, and he doesn't get up.** / harlan: Harlan Coyle. You'll have heard. Everyone's heard. ...Buy something, or don't.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The shutters are half closed, and he doesn't get up.
```
Subtitle: The shutters are half closed, and he doesn't get up.

### 232. `dlg.harlan.first.2.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/first#2; part 2 of 3: harlan: That's my seal. That's— / **narrator: He's round the counter before you can blink, hands out, and then he doesn't touch it.** / harlan: Where did you get that? Where was it? Where's the boy that was driving it?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's round the counter before you can blink, hands out, and then he doesn't touch it.
```
Subtitle: He's round the counter before you can blink, hands out, and then he doesn't touch it.

### 233. `dlg.harlan.hub.2.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/hub#2; part 1 of 2: **narrator: He doesn't get up.** / harlan: Three days of watching that road. I stopped. Somebody has to keep the stock, I told myself…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't get up.
```
Subtitle: He doesn't get up.

### 234. `dlg.harlan.hub.3.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/hub#3; part 1 of 2: **narrator: He keeps his eyes on the bend in the Old Road while he talks.** / harlan: I keep thinking the lead wagon'll come round there, Jory shouting that he got lost. Any wo…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He keeps his eyes on the bend in the Old Road while he talks.
```
Subtitle: He keeps his eyes on the bend in the Old Road while he talks.

### 235. `dlg.harlan.knew.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/knew#0; part 2 of 2: harlan: Jory? Jory knows salt from sugar on a good day. He didn't know. ...He didn't know. / **narrator: He goes back to counting the jars.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He goes back to counting the jars.
```
Subtitle: He goes back to counting the jars.

### 236. `dlg.harlan.betrayed.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/betrayed#0; part 2 of 3: harlan: You brought him home. Then you sold my strongbox to a fence for the price of a good horse. / **narrator: He counts a hundred onto the counter, coin by coin, and doesn't push it towards you.** / harlan: For the boy. I said I would. Take it, and get away from my stall.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He counts a hundred onto the counter, coin by coin, and doesn't push it towards you.
```
Subtitle: He counts a hundred onto the counter, coin by coin, and doesn't push it towards you.

### 237. `dlg.harlan.jory_now.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/jory_now#0; part 2 of 3: harlan: He asked me what was in the crates. I told him salt. / **narrator: He looks at his hands.** / harlan: He didn't believe me. First time in his life. ...That's the worst of it, friend. He always…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at his hands.
```
Subtitle: He looks at his hands.

### 238. `dlg.harlan.roost.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/roost#0; part 1 of 6: **narrator: He sits down, which you haven't seen him do.** / harlan: Three. In cages. / narrator: He's counting something on his fingers, and he stops. / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / narrator: He stops that too. / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He sits down, which you haven't seen him do.
```
Subtitle: He sits down, which you haven't seen him do.

### 239. `dlg.harlan.roost.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/roost#0; part 3 of 6: narrator: He sits down, which you haven't seen him do. / harlan: Three. In cages. / **narrator: He's counting something on his fingers, and he stops.** / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / narrator: He stops that too. / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's counting something on his fingers, and he stops.
```
Subtitle: He's counting something on his fingers, and he stops.

### 240. `dlg.harlan.roost.0.p4.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/roost#0; part 5 of 6: narrator: He sits down, which you haven't seen him do. / harlan: Three. In cages. / narrator: He's counting something on his fingers, and he stops. / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / **narrator: He stops that too.** / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He stops that too.
```
Subtitle: He stops that too.

### 241. `dlg.harlan.ledger_early.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/ledger_early#0; part 1 of 4: **narrator: He reads, and his finger stops on a line.** / harlan: That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's… / narrator: He looks up. / harlan: For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holl…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He reads, and his finger stops on a line.
```
Subtitle: He reads, and his finger stops on a line.

### 242. `dlg.harlan.ledger_early.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/ledger_early#0; part 3 of 4: narrator: He reads, and his finger stops on a line. / harlan: That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's… / **narrator: He looks up.** / harlan: For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holl…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks up.
```
Subtitle: He looks up.

### 243. `dlg.harlan.crates.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/crates#0; part 1 of 4: **narrator: His face does what it does whenever anyone says those two letters.** / harlan: ...Are they. With the bandit. / narrator: He's already reaching for paper. / harlan: Thank you, friend. Leave that with me. Paid for is paid for.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] His face does what it does whenever anyone says those two letters.
```
Subtitle: His face does what it does whenever anyone says those two letters.

### 244. `dlg.harlan.crates.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/crates#0; part 3 of 4: narrator: His face does what it does whenever anyone says those two letters. / harlan: ...Are they. With the bandit. / **narrator: He's already reaching for paper.** / harlan: Thank you, friend. Leave that with me. Paid for is paid for.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's already reaching for paper.
```
Subtitle: He's already reaching for paper.

### 245. `dlg.harlan.be_dig.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/be_dig#0; part 1 of 2: **narrator: He takes a long time to answer.** / harlan: I sell salt to people who salt things. I sell iron to people who hit things. I don't ask t…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes a long time to answer.
```
Subtitle: He takes a long time to answer.

### 246. `dlg.harlan.cb_jory_knows.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json harlan/cb_jory_knows#0; part 1 of 2: **narrator: He doesn't say good morning.** / harlan: He knows. You told him. ...I'd have told him myself. One day. When it didn't matter any mo…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't say good morning.
```
Subtitle: He doesn't say good morning.

## Conversations: Jory

### 247. `dlg.jory.hub.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json jory/hub#0; part 2 of 3: jory: I'm all right. / **narrator: He isn't.** / jory: Uncle's counting crates that aren't there.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He isn't.
```
Subtitle: He isn't.

### 248. `dlg.jory.truth.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json jory/truth#0; part 1 of 4: **narrator: He laughs, once, as if you've told him a joke he didn't get.** / jory: Every rut in Thornhollow. I took them over every rut. / narrator: He stops laughing. / jory: ...Uncle knew. Didn't he. He told me salt.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He laughs, once, as if you've told him a joke he didn't get.
```
Subtitle: He laughs, once, as if you've told him a joke he didn't get.

### 249. `dlg.jory.truth.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json jory/truth#0; part 3 of 4: narrator: He laughs, once, as if you've told him a joke he didn't get. / jory: Every rut in Thornhollow. I took them over every rut. / **narrator: He stops laughing.** / jory: ...Uncle knew. Didn't he. He told me salt.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He stops laughing.
```
Subtitle: He stops laughing.

### 250. `dlg.jory.truth_knew.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json jory/truth_knew#0; part 1 of 2: **narrator: He nods. He keeps nodding.** / jory: Right. Right. ...Thank you. I think. I'll know when I've stopped feeling sick.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He nods. He keeps nodding.
```
Subtitle: He nods. He keeps nodding.

### 251. `dlg.jory.salt.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json jory/salt#0; part 1 of 2: **narrator: He nods, and it goes out of his face at once, the way it goes out of a child's.** / jory: Salt. Right. ...Thanks.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He nods, and it goes out of his face at once, the way it goes out of a child's.
```
Subtitle: He nods, and it goes out of his face at once, the way it goes out of a child's.

## Conversations: Sella

### 252. `dlg.sella.night.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/night#0; part 1 of 3: **narrator: The water's gone cool by the time either of you notices, and she drags the quilt off the b…** / sella: Don't, / narrator: and kisses you so you can't. After, you lie on the floor of the blue room with the lamp tu…

```
The water's gone cool by the time either of you notices, and she drags the quilt off the bed and onto the floor rather than walk three steps. She is slower tonight. She keeps a hand flat on you the whole time, the way you'd keep a hand on a horse you'd been told was skittish, and when you look at her she says,
```
Subtitle: The water's gone cool by the time either of you notices, and she drags the quilt off the bed and onto the floor rather than walk three steps. She is slower tonight. She keeps a hand flat on you the whole time, the way you'd keep a hand on a horse you'd been told was skittish, and when you look at her she says,

### 253. `dlg.sella.night.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/night#0; part 3 of 3: narrator: The water's gone cool by the time either of you notices, and she drags the quilt off the b… / sella: Don't, / **narrator: and kisses you so you can't. After, you lie on the floor of the blue room with the lamp tu…**

```
and kisses you so you can't. After, you lie on the floor of the blue room with the lamp turned down to a bead, and she doesn't get up to dress, and you don't ask why. You wake with her hair across your chest and the sun already up. She is dressed, and counting, and she counts it twice.
```
Subtitle: and kisses you so you can't. After, you lie on the floor of the blue room with the lamp turned down to a bead, and she doesn't get up to dress, and you don't ask why. You wake with her hair across your chest and the sun already up. She is dressed, and counting, and she counts it twice.

### 254. `dlg.sella.night.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/night#1
*Played:* plain; doing: a night with Sella; pace: slow; volume: quiet.
*Note:* Low and close, discreet; 'She is dressed, and counting.' plain. Her word is hers.

```
[quietly] She laughs when the water slops over the side, and again when you try to mop it with her shift. Then the lamp is down to a bead, and the blue room is a small warm place with the whole night outside it. She talks the way she always talks, low against your ear, telling you exactly what she means to do next and then doing it, and she's good at it and likes it and makes no secret of either. But there are gaps, tonight. Places where she stops mid-sentence and doesn't finish, and you don't need her to. You wake with her hair across your chest and the sun already up. She is dressed, and counting.
```
Subtitle: She laughs when the water slops over the side, and again when you try to mop it with her shift. Then the lamp is down to a bead, and the blue room is a small warm place with the whole night outside it. She talks the way she always talks, low against your ear, telling you exactly what she means to do next and then doing it, and she's good at it and likes it and makes no secret of either. But there are gaps, tonight. Places where she stops mid-sentence and doesn't finish, and you don't need her to. You wake with her hair across your chest and the sun already up. She is dressed, and counting.

### 255. `dlg.sella.night.2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/night#2
*Played:* plain; doing: a night with Sella; pace: slow; volume: quiet.
*Note:* Low and close, discreet.

```
[quietly] The blue room smells of lavender and lamp oil, and the bath is warm, at least to begin with. After that the door is shut, and what happens behind it is slow, and warm, and funny, and nobody's business but yours: her hair coming down, her mouth at your ear, her hands everywhere they're welcome and nowhere they're not. For a few hours the road and the dead on it are a long way off. You wake with her hair across your chest and the sun already up. She is dressed, and counting.
```
Subtitle: The blue room smells of lavender and lamp oil, and the bath is warm, at least to begin with. After that the door is shut, and what happens behind it is slow, and warm, and funny, and nobody's business but yours: her hair coming down, her mouth at your ear, her hands everywhere they're welcome and nowhere they're not. For a few hours the road and the dead on it are a long way off. You wake with her hair across your chest and the sun already up. She is dressed, and counting.

### 256. `dlg.sella.morning.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/morning#0; part 1 of 2: **narrator: She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone.** / sella: You were cold as the river all night, love. Like sleeping next to a stone. And now look at…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone.
```
Subtitle: She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone.

### 257. `dlg.sella.free_night.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_night#0; part 1 of 3: **narrator: She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undre…** / sella: You told me anyway, / narrator: and nothing else, and then she sleeps.

```
She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undresses you as if she's never done it before, which is absurd, and she knows it's absurd, and halfway through she laughs into your neck and can't stop. Then she does stop, and the laugh goes somewhere else. She's slower than on her working nights, and less sure, and once she stops altogether with her forehead against yours and just breathes, and you wait, and she goes on. The lamp burns down on its own. Nobody turns it. In the dark, much later, she says into your shoulder,
```
Subtitle: She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undresses you as if she's never done it before, which is absurd, and she knows it's absurd, and halfway through she laughs into your neck and can't stop. Then she does stop, and the laugh goes somewhere else. She's slower than on her working nights, and less sure, and once she stops altogether with her forehead against yours and just breathes, and you wait, and she goes on. The lamp burns down on its own. Nobody turns it. In the dark, much later, she says into your shoulder,

### 258. `dlg.sella.free_night.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_night#0; part 3 of 3: narrator: She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undre… / sella: You told me anyway, / **narrator: and nothing else, and then she sleeps.**

```
and nothing else, and then she sleeps.
```
Subtitle: and nothing else, and then she sleeps.

### 259. `dlg.sella.free_night.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_night#1
*Played:* plain; doing: a night Sella gives; pace: slow; volume: quiet.
*Note:* The narrator's, hushed and unhurried: the one night that isn't work, so no patter. Narrator plain: the narrator never shows a feeling. Her four words are hers, said into your shoulder.

```
[quietly] The blue room, and the lamp, and the bolt, which she shot herself. She doesn't talk the way she talks for money. For a while neither of you talks at all. She is slower than you have known her, and less sure, and there is a moment when she stops with her hands on your face and just looks, as if she is learning it, and doesn't make a joke of it. Later she lies awake, and you can feel her deciding something, and then she sleeps.
```
Subtitle: The blue room, and the lamp, and the bolt, which she shot herself. She doesn't talk the way she talks for money. For a while neither of you talks at all. She is slower than you have known her, and less sure, and there is a moment when she stops with her hands on your face and just looks, as if she is learning it, and doesn't make a joke of it. Later she lies awake, and you can feel her deciding something, and then she sleeps.

### 260. `dlg.sella.free_morning.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_morning#0; part 1 of 2: **narrator: She's still there when you wake.** / sella: Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anythi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's still there when you wake.
```
Subtitle: She's still there when you wake.

### 261. `dlg.sella.past.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.sella.past.1.p0.wav`, `dlg.sella.past.2.p0.wav`, `dlg.sella.past.3.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#0; part 1 of 4: **narrator: She goes still when you start. You know who buys what's said up here; she knows you know. …** / sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. … / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.

### 262. `dlg.sella.past.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.sella.past.1.p2.wav`, `dlg.sella.past.2.p4.wav`, `dlg.sella.past.3.p4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#0; part 3 of 4: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. … / **narrator: She doesn't say anything else for a while. Then:** / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't say anything else for a while. Then:
```
Subtitle: She doesn't say anything else for a while. Then:

### 263. `dlg.sella.past.2.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.sella.past.6.p2.wav`, `dlg.sella.door_years.0.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#2; part 3 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Worse company than the Kerchiefs, and you walked away from it. / **narrator: She laughs, low.** / sella: Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactl… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs, low.
```
Subtitle: She laughs, low.

### 264. `dlg.sella.past.3.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.sella.past.7.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#3; part 3 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / **narrator: She's quiet a moment.** / sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's quiet a moment.
```
Subtitle: She's quiet a moment.

### 265. `dlg.sella.past.4.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.sella.past.5.p0.wav`, `dlg.sella.past.6.p0.wav`, `dlg.sella.past.7.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/past#4; part 1 of 2: **narrator: You tell her. She listens properly, chin on her fist, the way she does everything.** / sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] You tell her. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: You tell her. She listens properly, chin on her fist, the way she does everything.

### 266. `dlg.sella.sleeptalk.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/sleeptalk#0; part 2 of 3: sella: You said a name. Over and over, like you'd got hold of it in the dark and didn't want to l… / **narrator: She shrugs one shoulder.** / sella: Didn't catch it. I don't think you did either.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She shrugs one shoulder.
```
Subtitle: She shrugs one shoulder.

### 267. `dlg.sella.stairs.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs#0
*Played:* plain; doing: a regular now; pace: measured; volume: quiet.
*Note:* Plain.

```
[quietly] She doesn't take your hand any more; she takes your sleeve, the way you'd take a regular's. Rook's stairs creak on the fourth step and the ninth. On the fourth she looks back, to check you're stepping over it. You are.
```
Subtitle: She doesn't take your hand any more; she takes your sleeve, the way you'd take a regular's. Rook's stairs creak on the fourth step and the ninth. On the fourth she looks back, to check you're stepping over it. You are.

### 268. `dlg.sella.stairs.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs#1
*Played:* plain; doing: up the stairs; pace: measured; volume: quiet.
*Note:* Plain.

```
[quietly] She takes the coins first and your hand second, and leads you up Rook's narrow stairs. They creak on the fourth step and the ninth, and she steps over both without looking.
```
Subtitle: She takes the coins first and your hand second, and leads you up Rook's narrow stairs. They creak on the fourth step and the ninth, and she steps over both without looking.

### 269. `dlg.sella.stairs.2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs#2
*Played:* plain; doing: you're learning; pace: brisk; volume: quiet.
*Note:* Plain and brisk.

```
[quietly] Coins, then your hand, then the stairs. Fourth step, ninth step. You're learning.
```
Subtitle: Coins, then your hand, then the stairs. Fourth step, ninth step. You're learning.

### 270. `dlg.sella.stairs_room.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#0; part 1 of 2: **narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. Your buckles take …** / sella: All that steel, and under it, look. A person.
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.
*Note:* Plain; her words are hers.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck.
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck.

### 271. `dlg.sella.stairs_room.1.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#1; part 1 of 2: **narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. She takes your han…** / sella: Gently, upstairs. I mean it. I like this jug.
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. She takes your hands, one and then the other, and turns them over, and looks at the knuckles.
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. She takes your hands, one and then the other, and turns them over, and looks at the knuckles.

### 272. `dlg.sella.stairs_room.2.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#2; part 1 of 2: **narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. She lays her palm …** / sella: Your hands are hot and the rest of you's a cellar floor. Pick one, love.
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.
*Note:* Plain; 'cellar floor' level.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower.
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower.

### 273. `dlg.sella.stairs_room.3.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#3; part 1 of 3: **narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. She comes round be…** / sella: There. Now you know what it's like, / narrator: and you jump. She's delighted.
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. She comes round behind you to start on the laces, and says into your ear,
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. She comes round behind you to start on the laces, and says into your ear,

### 274. `dlg.sella.stairs_room.3.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.sella.stairs_room.7.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/stairs_room#3; part 3 of 3: narrator: The blue room again: the quilt, the jug, the bath, her, all of it blue. She comes round be… / sella: There. Now you know what it's like, / **narrator: and you jump. She's delighted.**
*Played:* plain; doing: the blue room; pace: measured; volume: quiet.

```
[quietly] and you jump. She's delighted.
```
Subtitle: and you jump. She's delighted.

### 275. `dlg.sella.stairs_room.4.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#4; part 1 of 2: **narrator: The blue room is blue because the lamp glass is, and everything in it takes the color: the…** / sella: All that steel, and under it, look. A person.
*Played:* plain; doing: the blue room; pace: slow; volume: quiet.
*Note:* The two mothers a nice turn, unhurried.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck.
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck.

### 276. `dlg.sella.stairs_room.5.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#5; part 1 of 2: **narrator: The blue room is blue because the lamp glass is, and everything in it takes the color: the…** / sella: Gently, upstairs. I mean it. I like this jug.
*Played:* plain; doing: the blue room; pace: slow; volume: quiet.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She takes your hands, one and then the other, and turns them over, and looks at the knuckles.
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She takes your hands, one and then the other, and turns them over, and looks at the knuckles.

### 277. `dlg.sella.stairs_room.6.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#6; part 1 of 2: **narrator: The blue room is blue because the lamp glass is, and everything in it takes the color: the…** / sella: Your hands are hot and the rest of you's a cellar floor. Pick one, love.
*Played:* plain; doing: the blue room; pace: slow; volume: quiet.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower.
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower.

### 278. `dlg.sella.stairs_room.7.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_room#7; part 1 of 3: **narrator: The blue room is blue because the lamp glass is, and everything in it takes the color: the…** / sella: There. Now you know what it's like, / narrator: and you jump. She's delighted.
*Played:* plain; doing: the blue room; pace: slow; volume: quiet.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She comes round behind you to start on the laces, and says into your ear,
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the color: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She comes round behind you to start on the laces, and says into your ear,

### 279. `dlg.sella.stairs_rules.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stairs_rules#0; part 1 of 2: **narrator: In the bath she slides her hands down your arms, and stops. Under the warm water you are c…** / sella: ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] In the bath she slides her hands down your arms, and stops. Under the warm water you are cold: not chilled, cold, like something brought up off the riverbed. She doesn't make a joke of it. She keeps her hands where they are for a long time, as if that would help.
```
Subtitle: In the bath she slides her hands down your arms, and stops. Under the warm water you are cold: not chilled, cold, like something brought up off the riverbed. She doesn't make a joke of it. She keeps her hands where they are for a long time, as if that would help.

### 280. `dlg.sella.stop_paid.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stop_paid#0; part 1 of 4: **narrator: She sits back on her heels, and doesn't sulk, and doesn't ask why.** / sella: Then I'll have the bath. It's paid for. / narrator: She counts thirteen coins back into your palm and closes your fingers on them. / sella: Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She sits back on her heels, and doesn't sulk, and doesn't ask why.
```
Subtitle: She sits back on her heels, and doesn't sulk, and doesn't ask why.

### 281. `dlg.sella.stop_paid.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/stop_paid#0; part 3 of 4: narrator: She sits back on her heels, and doesn't sulk, and doesn't ask why. / sella: Then I'll have the bath. It's paid for. / **narrator: She counts thirteen coins back into your palm and closes your fingers on them.** / sella: Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She counts thirteen coins back into your palm and closes your fingers on them.
```
Subtitle: She counts thirteen coins back into your palm and closes your fingers on them.

### 282. `dlg.sella.rest_night.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.sella.rest_night_paid.0.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json sella/rest_night#0; part 2 of 3: sella: Sleep. / **narrator: She looks at you as if you'd asked her to recite something in a foreign tongue.** / sella: You've paid fifteen gold to sleep.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you as if you'd asked her to recite something in a foreign tongue.
```
Subtitle: She looks at you as if you'd asked her to recite something in a foreign tongue.

### 283. `dlg.sella.rest_dark.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/rest_dark#0
*Played:* plain; doing: she watches you sleep; pace: slow; volume: quiet.
*Note:* Low and close; the watching very quiet.

```
[quietly] She lies down on top of the quilt with all her clothes on, and you under it, and for a while she talks: about Rook, about Holloway's feet, about a man from Low Kiln who wanted her to bark. You don't hear the end of the man from Low Kiln. Some time in the night you half wake and she isn't talking. She's lying on her side, watching you, the way you'd watch weather.
```
Subtitle: She lies down on top of the quilt with all her clothes on, and you under it, and for a while she talks: about Rook, about Holloway's feet, about a man from Low Kiln who wanted her to bark. You don't hear the end of the man from Low Kiln. Some time in the night you half wake and she isn't talking. She's lying on her side, watching you, the way you'd watch weather.

### 284. `dlg.sella.rest_morning.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/rest_morning#0; part 1 of 2: **narrator: She's sitting on the edge of the bed with her hand flat on your chest.** / sella: You were cold as the river all night. Like lying next to a stone. And now look at you: war…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's sitting on the edge of the bed with her hand flat on your chest.
```
Subtitle: She's sitting on the edge of the bed with her hand flat on your chest.

### 285. `dlg.sella.rest_morning.1.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/rest_morning#1; part 2 of 3: sella: Fifteen gold to watch you snore. Best money I ever made. / **narrator: She's already dressed. She doesn't count it.** / sella: Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's already dressed. She doesn't count it.
```
Subtitle: She's already dressed. She doesn't count it.

### 286. `dlg.sella.door.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/door#0; part 2 of 3: sella: That? It's Rook's. / **narrator: She sits on the bed to do up her boots, and doesn't look up.** / sella: Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funn…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She sits on the bed to do up her boots, and doesn't look up.
```
Subtitle: She sits on the bed to do up her boots, and doesn't look up.

### 287. `dlg.sella.door_south.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/door_south#0; part 2 of 3: sella: I told you. A house in the south. A door that locks from the inside. / **narrator: She stands, and checks her hair in the jug, and doesn't look at you.** / sella: And somebody who knocks.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She stands, and checks her hair in the jug, and doesn't look at you.
```
Subtitle: She stands, and checks her hair in the jug, and doesn't look at you.

### 288. `dlg.sella.free_decline.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_decline#0; part 2 of 5: sella: Your loss, love. Literally; I'm worth a fortune. / **narrator: She means it lightly, and very nearly manages it.** / sella: ...No, it's all right. It is. I'll not ask twice. I don't ask twice. / narrator: She pats your cheek, once, like a regular's. / sella: Go on. Rook's stew's still warm.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She means it lightly, and very nearly manages it.
```
Subtitle: She means it lightly, and very nearly manages it.

### 289. `dlg.sella.free_decline.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_decline#0; part 4 of 5: sella: Your loss, love. Literally; I'm worth a fortune. / narrator: She means it lightly, and very nearly manages it. / sella: ...No, it's all right. It is. I'll not ask twice. I don't ask twice. / **narrator: She pats your cheek, once, like a regular's.** / sella: Go on. Rook's stew's still warm.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She pats your cheek, once, like a regular's.
```
Subtitle: She pats your cheek, once, like a regular's.

### 290. `dlg.sella.free_ask.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_ask#0; part 1 of 2: **narrator: She looks at you for a long moment, as if you were a coin she was checking for clipping.** / sella: I said I'd not ask twice. I never said I'd not answer. ...Come on, then. Before I think be…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you for a long moment, as if you were a coin she was checking for clipping.
```
Subtitle: She looks at you for a long moment, as if you were a coin she was checking for clipping.

### 291. `dlg.sella.free_stairs.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_stairs#0
*Played:* plain; doing: she forgets the step; pace: slow; volume: quiet.
*Note:* The creak 'loud as a shout' given its beat; then quieter.

```
[quietly] She doesn't take your hand on the stairs, or your sleeve. She goes up ahead of you, and on the fourth step she forgets to step over it, and it creaks, loud as a shout, and she stops dead with one foot on it and laughs at herself, and that's worse, somehow, than if she hadn't. In the blue room she turns the lamp up, not down. She stands with her back against the door as if somebody might try it.
```
Subtitle: She doesn't take your hand on the stairs, or your sleeve. She goes up ahead of you, and on the fourth step she forgets to step over it, and it creaks, loud as a shout, and she stops dead with one foot on it and laughs at herself, and that's worse, somehow, than if she hadn't. In the blue room she turns the lamp up, not down. She stands with her back against the door as if somebody might try it.

### 292. `dlg.sella.free_door.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_door#0; part 2 of 3: sella: I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd he… / **narrator: She shakes her head.** / sella: Nobody does that. Nobody's ever done that.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She shakes her head.
```
Subtitle: She shakes her head.

### 293. `dlg.sella.free_want.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_want#0; part 2 of 3: sella: Ask me that again and I'll cry, and I don't cry, so don't. / **narrator: She takes a breath.** / sella: Yes. ...Yes. There. Said it. Come here.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She takes a breath.
```
Subtitle: She takes a breath.

### 294. `dlg.sella.free_stop.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_stop#0; part 1 of 4: **narrator: She lets out a breath she's been holding since the stairs.** / sella: All right. / narrator: And it is; you can see it is. / sella: All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She lets out a breath she's been holding since the stairs.
```
Subtitle: She lets out a breath she's been holding since the stairs.

### 295. `dlg.sella.free_stop.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_stop#0; part 3 of 4: narrator: She lets out a breath she's been holding since the stairs. / sella: All right. / **narrator: And it is; you can see it is.** / sella: All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] And it is; you can see it is.
```
Subtitle: And it is; you can see it is.

### 296. `dlg.sella.free_sit.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_sit#0
*Played:* plain; doing: sitting together; pace: slow; volume: quiet.
*Note:* Plain and slow.

```
[quietly] You sit on the bed with your backs to the wall, and she tells you about the house in the south: which room faces the sun; the color of the door; the knock. Then she sends you down the stairs, and stands at the top to watch you skip the fourth.
```
Subtitle: You sit on the bed with your backs to the wall, and she tells you about the house in the south: which room faces the sun; the color of the door; the knock. Then she sends you down the stairs, and stands at the top to watch you skip the fourth.

### 297. `dlg.sella.free_sleep.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_sleep#0; part 1 of 2: **narrator: She laughs, properly, the first time tonight.** / sella: You and your sleeping. ...Yes. All right. Yes.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs, properly, the first time tonight.
```
Subtitle: She laughs, properly, the first time tonight.

### 298. `dlg.sella.free_sleep_bed.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_sleep_bed#0
*Played:* plain; doing: she sleeps; pace: slow; volume: quiet.
*Note:* Low and close.

```
[quietly] She reaches behind her without looking and finds the bolt, and shoots it. Then she gets into the bed in her shift, and you get in beside her, and she lies with her back against you and pulls your arm over her like a blanket. She's asleep before you are. She's still there when you wake.
```
Subtitle: She reaches behind her without looking and finds the bolt, and shoots it. Then she gets into the bed in her shift, and you get in beside her, and she lies with her back against you and pulls your arm over her like a blanket. She's asleep before you are. She's still there when you wake.

### 299. `dlg.sella.free_bolt.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_bolt#0; part 1 of 2: **narrator: She reaches behind her without looking and finds the bolt. It sticks halfway; nobody has e…** / sella: ...There.
*Played:* plain; doing: the bolt; pace: slow; volume: quiet.
*Note:* Plain; her word is hers.

```
[quietly] She reaches behind her without looking and finds the bolt. It sticks halfway; nobody has ever shot it. She has to turn round and put her shoulder to it, swearing, and it goes home with a sound like the last coin put down on a counter. Her back is still to you. Her forehead is against the door.
```
Subtitle: She reaches behind her without looking and finds the bolt. It sticks halfway; nobody has ever shot it. She has to turn round and put her shoulder to it, swearing, and it goes home with a sound like the last coin put down on a counter. Her back is still to you. Her forehead is against the door.

### 300. `dlg.sella.free_m_downstairs.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_m_downstairs#0; part 1 of 2: **narrator: She laughs.** / sella: Downstairs Rook hears everything and charges nobody. You'd be better off with me. ...No. Y…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs.
```
Subtitle: She laughs.

### 301. `dlg.sella.free_m_who.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_m_who#0; part 2 of 3: sella: You know who. Everybody pays; she pays most. / **narrator: She pulls the quilt up to her chin.** / sella: I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don'…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She pulls the quilt up to her chin.
```
Subtitle: She pulls the quilt up to her chin.

### 302. `dlg.sella.free_m_kiss.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_m_kiss#0; part 1 of 3: **narrator: She lets you. Then she pushes you off by the face, gently, with the flat of her hand.** / sella: Out. Before I get used to it. / narrator: She's smiling. She doesn't stop smiling until you're down the stairs, and you know that be…
*Played:* plain; doing: out; pace: measured; volume: quiet.
*Note:* Plain; her words are hers.

```
[quietly] She lets you. Then she pushes you off by the face, gently, with the flat of her hand.
```
Subtitle: She lets you. Then she pushes you off by the face, gently, with the flat of her hand.

### 303. `dlg.sella.free_m_kiss.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/free_m_kiss#0; part 3 of 3: narrator: She lets you. Then she pushes you off by the face, gently, with the flat of her hand. / sella: Out. Before I get used to it. / **narrator: She's smiling. She doesn't stop smiling until you're down the stairs, and you know that be…**
*Played:* plain; doing: out; pace: measured; volume: quiet.
*Note:* Plain; her words are hers.

```
[quietly] She's smiling. She doesn't stop smiling until you're down the stairs, and you know that because the ninth step creaks behind you: she came down two steps to watch you go, and forgot it.
```
Subtitle: She's smiling. She doesn't stop smiling until you're down the stairs, and you know that because the ninth step creaks behind you: she came down two steps to watch you go, and forgot it.

### 304. `dlg.sella.refuse_roost.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/refuse_roost#0; part 1 of 4: **narrator: At the top of the stairs she stops with her hand on the door.** / sella: They're saying you burned the Roost with folk still in it. / narrator: She puts the coins back in your hand, all of them. / sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] At the top of the stairs she stops with her hand on the door.
```
Subtitle: At the top of the stairs she stops with her hand on the door.

### 305. `dlg.sella.refuse_roost.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json sella/refuse_roost#0; part 3 of 4: narrator: At the top of the stairs she stops with her hand on the door. / sella: They're saying you burned the Roost with folk still in it. / **narrator: She puts the coins back in your hand, all of them.** / sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She puts the coins back in your hand, all of them.
```
Subtitle: She puts the coins back in your hand, all of them.

## Conversations: Pell

### 306. `dlg.pell.hub.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json pell/hub#0; part 1 of 2: **narrator: He smiles a little too quickly.** / pell: Ah. You. What can I do for you today, specifically?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He smiles a little too quickly.
```
Subtitle: He smiles a little too quickly.

### 307. `dlg.pell.confront.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json pell/confront#0; part 2 of 3: pell: Where did you— the clerk. Of course. / **narrator: He studies your face, and something in his own unclenches.** / pell: ...You don't know what you're holding, do you? How refreshing. Let's be civilized. There's…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He studies your face, and something in his own unclenches.
```
Subtitle: He studies your face, and something in his own unclenches.

### 308. `dlg.pell.t_pell.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json pell/t_pell#0; part 2 of 3: pell: My sister kept the books in Ashford, in the lower town. I came up to collect them, after. … / **narrator: He straightens a pen that was straight.** / pell: Somebody barred it. I know who. ...So I count. Somebody ought to know what things cost.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He straightens a pen that was straight.
```
Subtitle: He straightens a pen that was straight.

## Conversations: Rav

### 309. `dlg.rav.cb_killed_redcowl.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.rav.owes_two.0.p1.wav`, `dlg.scene_knocking.knock.0.p3.wav`, `dlg.scene_knocking.home.0.p1.wav`, `dlg.scene_knocking.tell.0.p2.wav`, `dlg.scene_knocking.saw.0.p3.wav`, `dlg.scene_knocking.knows.0.p3.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json rav/cb_killed_redcowl#0; part 3 of 4: narrator: He doesn't look up. / rav: You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated… / **narrator: He drinks.** / rav: No. He'd have said it was the job. It was always the job, with him. Get out of my light fo…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He drinks.
```
Subtitle: He drinks.

### 310. `dlg.rav.leg_held.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/leg_held#0; part 1 of 4: **narrator: He puts the cup down, very carefully, as if it were full.** / rav: ...Did he. / narrator: A long time. / rav: Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts the cup down, very carefully, as if it were full.
```
Subtitle: He puts the cup down, very carefully, as if it were full.

### 311. `dlg.rav.back_room.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room#0
*Played:* plain; doing: Rav's surgery; pace: measured; volume: quiet.
*Note:* Plain; the moving jar and the trophy needle as plain facts.

```
[quietly] Behind the Crooked Flagon there's a lean-to with a lamp, a scrubbed table, a shelf of jars, one of them moving, and a sail-needle stuck in a cork like a trophy. Rav is sitting on the table with his feet on a stool and two cups already poured.
```
Subtitle: Behind the Crooked Flagon there's a lean-to with a lamp, a scrubbed table, a shelf of jars, one of them moving, and a sail-needle stuck in a cork like a trophy. Rav is sitting on the table with his feet on a stool and two cups already poured.

### 312. `dlg.rav.back_room_look.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room_look#0; part 2 of 7: rav: You came. / **narrator: He looks faintly alarmed about it.** / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / rav: You're cold, pal. Cold as a cellar step. / narrator: He frowns at your wrist, then lets it go. / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks faintly alarmed about it.
```
Subtitle: He looks faintly alarmed about it.

### 313. `dlg.rav.back_room_look.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room_look#0; part 4 of 7: rav: You came. / narrator: He looks faintly alarmed about it. / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / **narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do…** / rav: You're cold, pal. Cold as a cellar step. / narrator: He frowns at your wrist, then lets it go. / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at your eyes, and your tongue, and your hands, turning them over the way Sella does, but for different reasons. He listens at your back with his ear flat against it, and tells you to cough. He's quiet a moment.
```
Subtitle: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella does, but for different reasons. He listens at your back with his ear flat against it, and tells you to cough. He's quiet a moment.

### 314. `dlg.rav.back_room_look.0.p5.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room_look#0; part 6 of 7: rav: You came. / narrator: He looks faintly alarmed about it. / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / rav: You're cold, pal. Cold as a cellar step. / **narrator: He frowns at your wrist, then lets it go.** / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He frowns at your wrist, then lets it go.
```
Subtitle: He frowns at your wrist, then lets it go.

### 315. `dlg.rav.back_room_drink.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room_drink#0; part 2 of 3: rav: For one of us. / **narrator: He drinks his, then looks at yours.** / rav: Both of us, evidently. ...Go home, pal. You've got a job up the Old Road, and I've got a b…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He drinks his, then looks at yours.
```
Subtitle: He drinks his, then looks at yours.

### 316. `dlg.rav.back_room_kiss.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room_kiss#0; part 1 of 4: **narrator: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. …** / rav: Not yet, pal. Not three cups down, and not while you're still needing things off me: keys,… / narrator: He picks up his cup. / rav: Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's t…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. Then he puts a hand flat on your chest and moves you back a foot, gently, the way he'd move a patient.
```
Subtitle: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. Then he puts a hand flat on your chest and moves you back a foot, gently, the way he'd move a patient.

### 317. `dlg.rav.back_room_kiss.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room_kiss#0; part 3 of 4: narrator: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. … / rav: Not yet, pal. Not three cups down, and not while you're still needing things off me: keys,… / **narrator: He picks up his cup.** / rav: Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's t…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He picks up his cup.
```
Subtitle: He picks up his cup.

### 318. `dlg.rav.back_room_end.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/back_room_end#0; part 2 of 3: rav: "Doctor." / **narrator: He snorts.** / rav: Get out of my surgery.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He snorts.
```
Subtitle: He snorts.

### 319. `dlg.rav.came_back.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/came_back#0; part 1 of 4: **narrator: He's at his table. He's sober, or near it. He's shaved.** / rav: You came back. / narrator: He looks at you for a long time. / rav: Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. .…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's at his table. He's sober, or near it. He's shaved.
```
Subtitle: He's at his table. He's sober, or near it. He's shaved.

### 320. `dlg.rav.came_back.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/came_back#0; part 3 of 4: narrator: He's at his table. He's sober, or near it. He's shaved. / rav: You came back. / **narrator: He looks at you for a long time.** / rav: Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. .…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you for a long time.
```
Subtitle: He looks at you for a long time.

### 321. `dlg.rav.cb_spared_redcowl.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/cb_spared_redcowl#0; part 1 of 4: **narrator: Two cups are out before you reach his table, and he fills them both.** / rav: Busy night up the ruts, I hear. Heard a man got up off his knee after, on a leg he'd no bu… / narrator: He pushes one across. / rav: Good work, that leg. Whoever did it. ...That one doesn't go on the slate, pal.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Two cups are out before you reach his table, and he fills them both.
```
Subtitle: Two cups are out before you reach his table, and he fills them both.

### 322. `dlg.rav.cb_spared_redcowl.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json rav/cb_spared_redcowl#0; part 3 of 4: narrator: Two cups are out before you reach his table, and he fills them both. / rav: Busy night up the ruts, I hear. Heard a man got up off his knee after, on a leg he'd no bu… / **narrator: He pushes one across.** / rav: Good work, that leg. Whoever did it. ...That one doesn't go on the slate, pal.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He pushes one across.
```
Subtitle: He pushes one across.

## Conversations: Vonnra

### 323. `dlg.vonnra.hub.2.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json vonnra/hub#2; part 1 of 2: **narrator: Her lamp is lit, and she is looking south, toward the ford.** / vonnra: Traveler. The road is quiet tonight. It will not always be. Payment, always.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Her lamp is lit, and she is looking south, toward the ford.
```
Subtitle: Her lamp is lit, and she is looking south, toward the ford.

### 324. `dlg.vonnra.f_below.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json vonnra/f_below#0; part 2 of 2: vonnra: And the door in the hillside... / **narrator: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame …**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The roof shivers under the table, and the glass of her lamp rings in its frame. The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the braziers on the wall do not. She looks east, into the dark, and does not finish.
```
Subtitle: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the braziers on the wall do not. She looks east, into the dark, and does not finish.

### 325. `dlg.vonnra.f_chart.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.vonnra.f_chart.1.p0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json vonnra/f_chart#0; part 1 of 3: **narrator: She takes a folded chart from under the ledger and lays it between you. It is in the Wayfi…** / vonnra: That would be ten gold. This once, no charge. The rest you will walk into yourself, and yo… / narrator: The ledger lies open, her hand flat on the right-hand page, and from where you sit you can…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She takes a folded chart from under the ledger and lays it between you. It is in the Wayfinder's hand, and its margins are written full.
```
Subtitle: She takes a folded chart from under the ledger and lays it between you. It is in the Wayfinder's hand, and its margins are written full.

### 326. `dlg.vonnra.f_chart.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.vonnra.f_chart.1.p2.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json vonnra/f_chart#0; part 3 of 3: narrator: She takes a folded chart from under the ledger and lays it between you. It is in the Wayfi… / vonnra: That would be ten gold. This once, no charge. The rest you will walk into yourself, and yo… / **narrator: The ledger lies open, her hand flat on the right-hand page, and from where you sit you can…**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The ledger lies open, her hand flat on the right-hand page, and from where you sit you can read the left. Twenty-six lines, every one struck through. The twenty-fifth: Nell, the smith's girl. With Wat. The twenty-sixth: A woman. No name. And under them a twenty-seventh, not struck: From the ford. Got up.
```
Subtitle: The ledger lies open, her hand flat on the right-hand page, and from where you sit you can read the left. Twenty-six lines, every one struck through. The twenty-fifth: Nell, the smith's girl. With Wat. The twenty-sixth: A woman. No name. And under them a twenty-seventh, not struck: From the ford. Got up.

### 327. `dlg.vonnra.jessop.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json vonnra/jessop#0; part 2 of 3: vonnra: Gone south. On the toll's business. / **narrator: She turns a page of the ledger that does not need turning.** / vonnra: Clerks go south, traveler. It is the direction they fall in.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She turns a page of the ledger that does not need turning.
```
Subtitle: She turns a page of the ledger that does not need turning.

### 328. `dlg.vonnra.f_past.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.vonnra.f_past.1.p1.wav`, `dlg.vonnra.f_past.2.p1.wav`, `dlg.vonnra.f_past.3.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json vonnra/f_past#0; part 2 of 2: vonnra: And before the ford: a child following tracks through these woods, with a bow too big for … / **narrator: She is not looking at your palm.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She is not looking at your palm.
```
Subtitle: She is not looking at your palm.

### 329. `dlg.vonnra.f_accuse.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json vonnra/f_accuse#0; part 2 of 4: vonnra: I did not kill him. / **narrator: For the first time she looks at your face and not at your hand. It goes on long enough tha…** / vonnra: ...Sit down. / vonnra: I have not finished reading.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] For the first time she looks at your face and not at your hand. It goes on long enough that the lamp gutters.
```
Subtitle: For the first time she looks at your face and not at your hand. It goes on long enough that the lamp gutters.

### 330. `dlg.vonnra.f_ford.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.vonnra.f_ford.1.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json vonnra/f_ford#0; part 2 of 3: vonnra: And the ford. / **narrator: She turns the cup over on the table.** / vonnra: He would have held that lamp out of the water until the river ran dry, traveler. Two hundr…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She turns the cup over on the table.
```
Subtitle: She turns the cup over on the table.

### 331. `dlg.vonnra.f_did.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json vonnra/f_did#0; part 2 of 3: vonnra: When the lamp went into the water, his heart came up out of it, and a little lamp-person w… / **narrator: She lays her hand flat on the cup.** / vonnra: You stopped the drowning, traveler. You also did this.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She lays her hand flat on the cup.
```
Subtitle: She lays her hand flat on the cup.

## Conversations: Keegan

### 332. `dlg.keegan.say_calling.3.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.keegan.say_calling.4.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json keegan/say_calling#3; part 2 of 3: keegan: The handbook says to challenge anyone who approaches unseen. / **narrator: She checks.** / keegan: It does not say what to do if one forgets. ...Halt. Belatedly.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She checks.
```
Subtitle: She checks.

### 333. `dlg.keegan.say_risen.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/say_risen#0; part 2 of 3: keegan: I am told you were carried into the shrine under a sheet. / **narrator: She looks at you very carefully, from your boots upwards, and back down.** / keegan: You look well. You look extremely well. ...I've got to go and read something. I— I have to…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you very carefully, from your boots upwards, and back down.
```
Subtitle: She looks at you very carefully, from your boots upwards, and back down.

### 334. `dlg.keegan.supper.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper#0; part 2 of 3: keegan: I have not. I am on watch. / **narrator: She looks at the bread in her hand, which she has evidently been holding for some time.** / keegan: Chapter eleven, paragraph six permits "a meal taken in company for the purposes of morale"…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at the bread in her hand, which she has evidently been holding for some time.
```
Subtitle: She looks at the bread in her hand, which she has evidently been holding for some time.

### 335. `dlg.keegan.supper_table.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_table#0
*Played:* plain; doing: supper at the gate; pace: slow; volume: quiet.
*Note:* Plain and slow.

```
[quietly] She breaks the bread and gives you the larger half without seeming to decide to. There's a heel of cheese, and a flask that turns out to be water, and the north road beyond the gate is black all the way to the hills.
```
Subtitle: She breaks the bread and gives you the larger half without seeming to decide to. There's a heel of cheese, and a flask that turns out to be water, and the north road beyond the gate is black all the way to the hills.

### 336. `dlg.keegan.supper_wends.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_wends#0; part 2 of 3: keegan: Rhetoric, to the sons and daughters of people who could afford it. I was very good. I was … / **narrator: She smiles at the road.** / keegan: I taught them chiasmus. "The Vigil keeps the gate, and the gate keeps the Vigil." It has k…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She smiles at the road.
```
Subtitle: She smiles at the road.

### 337. `dlg.keegan.supper_age.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_age#0; part 2 of 3: keegan: Twenty-six. The handbook says that is old for a probationer. The handbook says a great man… / **narrator: She looks at you sidelong.** / keegan: How old are you? No. Do not answer. I should only write it down.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you sidelong.
```
Subtitle: She looks at you sidelong.

### 338. `dlg.keegan.supper_letters.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_letters#0; part 1 of 2: **narrator: She doesn't answer for so long that you think she won't.** / keegan: That is a possibility I have considered. I have considered it every month for two years, o…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't answer for so long that you think she won't.
```
Subtitle: She doesn't answer for so long that you think she won't.

### 339. `dlg.keegan.supper_read.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_read#0; part 1 of 4: **narrator: She is very obviously delighted, and very obviously trying not to be.** / keegan: Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body b… / narrator: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gat… / keegan: ...You did not fall asleep. Nobody has ever not fallen asleep.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She is very obviously delighted, and very obviously trying not to be.
```
Subtitle: She is very obviously delighted, and very obviously trying not to be.

### 340. `dlg.keegan.supper_read.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_read#0; part 3 of 4: narrator: She is very obviously delighted, and very obviously trying not to be. / keegan: Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body b… / **narrator: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gat…** / keegan: ...You did not fall asleep. Nobody has ever not fallen asleep.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She reads you chapter twelve, on the care of the blade, all of it, by the light of the gate lamp, and it is beautiful, actually.
```
Subtitle: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gate lamp, and it is beautiful, actually.

### 341. `dlg.keegan.supper_ch4.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_ch4#0; part 1 of 3: **narrator: She closes the book.** / keegan: No. / narrator: She says it gently, and then she doesn't say anything else for a while, and her hand stays…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She closes the book.
```
Subtitle: She closes the book.

### 342. `dlg.keegan.supper_ch4.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_ch4#0; part 3 of 3: narrator: She closes the book. / keegan: No. / **narrator: She says it gently, and then she doesn't say anything else for a while, and her hand stays…**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She says it gently, and then she doesn't say anything else for a while, and her hand stays flat on the cover.
```
Subtitle: She says it gently, and then she doesn't say anything else for a while, and her hand stays flat on the cover.

### 343. `dlg.keegan.supper_hand.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_hand#0; part 1 of 4: **narrator: You put your hand over hers on the stone. She lets it stay there for a count of three.** / keegan: I am on duty. / narrator: She takes her hand back. Then, without looking, she puts it back, under yours, for another… / keegan: ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] You put your hand over hers on the stone. She lets it stay there for a count of three.
```
Subtitle: You put your hand over hers on the stone. She lets it stay there for a count of three.

### 344. `dlg.keegan.supper_hand.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_hand#0; part 3 of 4: narrator: You put your hand over hers on the stone. She lets it stay there for a count of three. / keegan: I am on duty. / **narrator: She takes her hand back. Then, without looking, she puts it back, under yours, for another…** / keegan: ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She takes her hand back. Then, without looking, she puts it back, under yours, for another count of three.
```
Subtitle: She takes her hand back. Then, without looking, she puts it back, under yours, for another count of three.

### 345. `dlg.keegan.supper_end.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json keegan/supper_end#0; part 2 of 3: keegan: Goodnight. / **narrator: As you go:** / keegan: It was good for morale. Mine. I checked.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] As you go:
```
Subtitle: As you go:

## Conversations: the Wayfinder

### 346. `dlg.wayfinder.margin.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json wayfinder/margin#0; part 2 of 3: ysolde: Who came back, from where, how long they lasted, what they carried out. Name first; I'm a … / **narrator: She dips her pen.** / ysolde: Speaking of which. How do I put you down?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She dips her pen.
```
Subtitle: She dips her pen.

### 347. `dlg.wayfinder.margin_name.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json wayfinder/margin_name#0; part 1 of 2: **narrator: She writes it, blots it, and blows on it.** / ysolde: There. Now you're in the margins for good.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She writes it, blots it, and blows on it.
```
Subtitle: She writes it, blots it, and blows on it.

### 348. `dlg.wayfinder.margin_nobody.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json wayfinder/margin_nobody#0; part 2 of 3: ysolde: Nobody. / **narrator: She writes it without blinking.** / ysolde: You'd be surprised how often Nobody comes back. More than most.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She writes it without blinking.
```
Subtitle: She writes it without blinking.

### 349. `dlg.wayfinder.margin_lark.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json wayfinder/margin_lark#0; part 1 of 2: **narrator: She looks at you over the pen for a moment, then writes.** / ysolde: Lark. You look like a Lark. Larks get up early and make a great deal of noise about it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you over the pen for a moment, then writes.
```
Subtitle: She looks at you over the pen for a moment, then writes.

## Conversations: Greymuzzle

### 350. `dlg.greymuzzle.first.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/first#0
*Played:* plain; doing: meeting the old wolf; pace: slow; volume: quiet.
*Note:* Still; a long pause after 'for a long time'; the last image very quiet.

```
[quietly] The old wolf comes out of the rocks alone. He is gray to the eyes, and thin, and he does not growl. He looks at you for a long time. Behind him, in the shadow of the stones, wolves lie in the dirt and do not get up.
```
Subtitle: The old wolf comes out of the rocks alone. He is gray to the eyes, and thin, and he does not growl. He looks at you for a long time. Behind him, in the shadow of the stones, wolves lie in the dirt and do not get up.

### 351. `dlg.greymuzzle.show.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/show#0
*Played:* plain; doing: the sick Pack; pace: slow; volume: quiet.
*Note:* Plain and close; 'and cannot' after a small pause. It ends on him waiting.

```
[quietly] He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. Then your collar, for longer; and his tail moves, once. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Grey-muzzle looks east, toward the stream, then back at you, and waits.
```
Subtitle: He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. Then your collar, for longer; and his tail moves, once. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Greymuzzle looks east, toward the stream, then back at you, and waits.

### 352. `dlg.greymuzzle.show.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/show#1
*Played:* plain; doing: the sick Pack; pace: slow; volume: quiet.
*Note:* As show.0; the lip lifting given its beat.

```
[quietly] He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Grey-muzzle looks east, toward the stream, then back at you, and waits.
```
Subtitle: He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Greymuzzle looks east, toward the stream, then back at you, and waits.

### 353. `dlg.greymuzzle.ally.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/ally#0
*Played:* plain; doing: the Pack's answer; pace: slow; volume: quiet.
*Note:* 'He is not coming.' on its own. 'They are his answer.' plain.

```
[quietly] Grey-muzzle lifts his head and howls, once. Four of the strongest get up and come to stand beside you. The old wolf lies back down among the sick. He is not coming. They are his answer.
```
Subtitle: Greymuzzle lifts his head and howls, once. Four of the strongest get up and come to stand beside you. The old wolf lies back down among the sick. He is not coming. They are his answer.

### 354. `dlg.greymuzzle.again.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/again#0
*Played:* plain; doing: the Pack has turned its back; pace: slow; volume: quiet.
*Note:* Flat and final.

```
[quietly] Grey-muzzle comes out of the rocks, looks at you for a long moment, and lies down with his back to you. Behind him, the others do the same.
```
Subtitle: Greymuzzle comes out of the rocks, looks at you for a long moment, and lies down with his back to you. Behind him, the others do the same.

### 355. `dlg.greymuzzle.again.1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/again#1
*Played:* plain; doing: the Pack is dying; pace: slow; volume: quiet.
*Note:* Plain.

```
[quietly] Grey-muzzle doesn't come out. Two of the wolves you saw lying in the dirt are not there any more. The others watch you the way they watch weather.
```
Subtitle: Greymuzzle doesn't come out. Two of the wolves you saw lying in the dirt are not there any more. The others watch you the way they watch weather.

### 356. `dlg.greymuzzle.again.2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/again#2
*Played:* plain; doing: the Pack is well; pace: measured; volume: quiet.
*Note:* Plain.

```
[quietly] Grey-muzzle is on his feet. So are the others. He looks at you, and then away, which from a wolf is as good as thanks.
```
Subtitle: Greymuzzle is on his feet. So are the others. He looks at you, and then away, which from a wolf is as good as thanks.

### 357. `dlg.greymuzzle.again.3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json greymuzzle/again#3
*Played:* plain; doing: the old wolf waits; pace: slow; volume: quiet.
*Note:* Plain.

```
[quietly] Grey-muzzle watches you from the rocks. He does not get up.
```
Subtitle: Greymuzzle watches you from the rocks. He does not get up.

## Conversations: Redcowl

### 358. `dlg.redcowl.first.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/first#0; part 1 of 2: **narrator: Every crossbow in the camp is on you, and nobody's laughing.** / redcowl: You're the one who's been putting my lads in the ground. Redcowl. Talk, and talk slow.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Every crossbow in the camp is on you, and nobody's laughing.
```
Subtitle: Every crossbow in the camp is on you, and nobody's laughing.

### 359. `dlg.redcowl.trick.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/trick#0; part 2 of 3: redcowl: The Watch. Holloway hasn't got the men to— / **narrator: A whistle from the ridge. The whole camp stops.** / redcowl: —PACK IT UP! PACK IT UP! Leave the heavy stuff!
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A whistle from the ridge. The whole camp stops.
```
Subtitle: A whistle from the ridge. The whole camp stops.

### 360. `dlg.redcowl.crates_dig.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/crates_dig#0; part 1 of 4: **narrator: He doesn't laugh.** / redcowl: The hill. / narrator: He looks north-east, past the ravine wall, at nothing you can see. / redcowl: The one that's been knocking at night. ...How deep are they going?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't laugh.
```
Subtitle: He doesn't laugh.

### 361. `dlg.redcowl.crates_dig.0.p2.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/crates_dig#0; part 3 of 4: narrator: He doesn't laugh. / redcowl: The hill. / **narrator: He looks north-east, past the ravine wall, at nothing you can see.** / redcowl: The one that's been knocking at night. ...How deep are they going?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks north-east, past the ravine wall, at nothing you can see.
```
Subtitle: He looks north-east, past the ravine wall, at nothing you can see.

### 362. `dlg.redcowl.crates_keep.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/crates_keep#0; part 2 of 3: redcowl: Then nobody's having them. Not the hole in the hill. Not Holloway. Not your merchant, and … / **narrator: A laugh, but not the big one.** / redcowl: Guarding crates. My mother'd laugh herself sick.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A laugh, but not the big one.
```
Subtitle: A laugh, but not the big one.

### 363. `dlg.redcowl.crates_charge.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/crates_charge#0; part 1 of 2: **narrator: He looks at you a long while. Then he whistles, and a lad brings one over, walking like he…** / redcowl: Take it. Put it where it'll do the most harm to the right people. And run.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you a long while. Then he whistles, and a lad brings one over, walking like he's carrying a sleeping baby.
```
Subtitle: He looks at you a long while. Then he whistles, and a lad brings one over, walking like he's carrying a sleeping baby.

### 364. `dlg.redcowl.birds.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*The same words are also* `dlg.redcowl.birds.1.p1.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json redcowl/birds#0; part 2 of 3: redcowl: Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober. / **narrator: The laugh stops.** / redcowl: Birds don't have names, lass. Not in my camp.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The laugh stops.
```
Subtitle: The laugh stops.

### 365. `dlg.redcowl.ashford.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/ashford#0; part 1 of 2: **narrator: The laugh goes out of him like a lamp.** / redcowl: Don't. You get to say that once in my camp. You've said it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The laugh goes out of him like a lamp.
```
Subtitle: The laugh goes out of him like a lamp.

### 366. `dlg.redcowl.pell_given.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json redcowl/pell_given#0; part 2 of 3: redcowl: Ha! Somebody who knows where the rats sleep. / **narrator: He's already shouting for boots.** / redcowl: Go home. Stay off the square tonight.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's already shouting for boots.
```
Subtitle: He's already shouting for boots.

## Conversations: Scene_gate_dawn

### 367. `dlg.scene_gate_dawn.gate.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_gate_dawn/gate#0

```
The gate has stood open all night. Captain Holloway is asleep on the ground in the gateway, his back to the post, his lamp burned out and a bottle by his hand. Mayka sits on the step beside him with her crossbow across her knees. She is awake.
```
Subtitle: The gate has stood open all night. Captain Holloway is asleep on the ground in the gateway, his back to the post, his lamp burned out and a bottle by his hand. Maeca sits on the step beside him with her crossbow across her knees. She is awake.

### 368. `dlg.scene_gate_dawn.wake.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_gate_dawn/wake#0; part 2 of 3: holloway: ...One in. / **narrator: He looks past you at the empty road.** / holloway: Count's right.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks past you at the empty road.
```
Subtitle: He looks past you at the empty road.

### 369. `dlg.scene_gate_dawn.all.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_gate_dawn/all#0; part 2 of 2: holloway: Gate was open. Somebody had to stand in it. / **narrator: Maeca looks at the ground he slept on, and then at him, and says nothing.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Mayka looks at the ground he slept on, and then at him, and says nothing.
```
Subtitle: Maeca looks at the ground he slept on, and then at him, and says nothing.

### 370. `dlg.scene_gate_dawn.bar.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_gate_dawn/bar#0

```
He gets up, and puts his shoulder to the gate, and bars it. Mayka picks up his bottle, looks at what's left in it, and pours it out on the step.
```
Subtitle: He gets up, and puts his shoulder to the gate, and bars it. Maeca picks up his bottle, looks at what's left in it, and pours it out on the step.

## Conversations: Scene_in_my_count

### 371. `dlg.scene_in_my_count.crowd.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_in_my_count/crowd#0

```
There are folk at the gate end of the square when you come down, and the talk stops when they see you.
```
Subtitle: There are folk at the gate end of the square when you come down, and the talk stops when they see you.

### 372. `dlg.scene_in_my_count.between.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_in_my_count/between#0

```
They are between you and the street, and they are not moving.
```
Subtitle: They are between you and the street, and they are not moving.

### 373. `dlg.scene_in_my_count.captain.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_in_my_count/captain#0; part 1 of 2: **narrator: He comes down the street at a walk, not hurrying, and he has been drinking. He walks throu…** / holloway: She's in my count.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He comes down the street at a walk, not hurrying, and he has been drinking. He walks through them, not round them, and stops with his back to you.
```
Subtitle: He comes down the street at a walk, not hurrying, and he has been drinking. He walks through them, not round them, and stops with his back to you.

### 374. `dlg.scene_in_my_count.men.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_in_my_count/men#0

```
Nobody moves. Two of his own men are at the back of the crowd, and they stay there.
```
Subtitle: Nobody moves. Two of his own men are at the back of the crowd, and they stay there.

### 375. `dlg.scene_in_my_count.through.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_in_my_count/through#0; part 2 of 3: holloway: Anybody wants her out of it comes through me. / **narrator: He sways, and plants his feet.** / holloway: ...And I'm drunk, so it'll take you all morning.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He sways, and plants his feet.
```
Subtitle: He sways, and plants his feet.

### 376. `dlg.scene_in_my_count.gone.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_in_my_count/gone#0

```
It takes a while. He stands there until the last of them has gone home, and then he sits down where he stood.
```
Subtitle: It takes a while. He stands there until the last of them has gone home, and then he sits down where he stood.

### 377. `dlg.scene_in_my_count.sit.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_in_my_count/sit#0

```
You sit. After a while he passes you the cup. There's nothing in it. Neither of you says so.
```
Subtitle: You sit. After a while he passes you the cup. There's nothing in it. Neither of you says so.

## Conversations: Scene_knocking

### 378. `dlg.scene_knocking.ground.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/ground#0

```
The ground turns over under the square, and every lamp on the wall dips and comes back. At the gate Holloway hasn't moved. He's sitting against the post with his cup, and he's listening to something.
```
Subtitle: The ground turns over under the square, and every lamp on the wall dips and comes back. At the gate Holloway hasn't moved. He's sitting against the post with his cup, and he's listening to something.

### 379. `dlg.scene_knocking.knock.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/knock#0; part 2 of 5: holloway: Knocking. / **narrator: He listens.** / holloway: From under. / narrator: He drinks. / holloway: No. Course not.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He listens.
```
Subtitle: He listens.

### 380. `dlg.scene_knocking.tell.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/tell#0; part 1 of 6: **narrator: He counts on his fingers, loses his place, and starts again.** / holloway: Ground went. Lower town with it. Night. Half the garrison on the hill, at the cave mouths.… / narrator: He drinks. / holloway: Me at the top. Lamp. Windlass. Lid. Counting them up. Lamp in my eyes. One. Two. / narrator: A long time. / holloway: Ninety-one. Then I looked down.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He counts on his fingers, loses his place, and starts again.
```
Subtitle: He counts on his fingers, loses his place, and starts again.

### 381. `dlg.scene_knocking.saw.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/saw#0; part 2 of 7: holloway: Dead. Climbing. Gray, all of them, and not a sound out of them. Under the last of ours, cl… / **narrator: He holds one hand flat over the other.** / holloway: Four hundred behind me, asleep. Bairns. / narrator: He drinks. / holloway: Lid down. Bar across. Sat on it. / narrator: He breathes out, a long way. / holloway: Three days, they knocked.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He holds one hand flat over the other.
```
Subtitle: He holds one hand flat over the other.

### 382. `dlg.scene_knocking.saw.0.p5.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/saw#0; part 6 of 7: holloway: Dead. Climbing. Gray, all of them, and not a sound out of them. Under the last of ours, cl… / narrator: He holds one hand flat over the other. / holloway: Four hundred behind me, asleep. Bairns. / narrator: He drinks. / holloway: Lid down. Bar across. Sat on it. / **narrator: He breathes out, a long way.** / holloway: Three days, they knocked.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He breathes out, a long way.
```
Subtitle: He breathes out, a long way.

### 383. `dlg.scene_knocking.knows.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/knows#0; part 2 of 5: holloway: Pell. / **narrator: His eyes go past you, to the step, and come back to the cup.** / holloway: Went up after, for his sister's money. Found the lid barred from the top. / narrator: He drinks. / holloway: He's a careful man. He's waiting for a price.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] His eyes go past you, to the step, and come back to the cup.
```
Subtitle: His eyes go past you, to the step, and come back to the cup.

### 384. `dlg.scene_knocking.silent.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/silent#0
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He counts. You can see his lips do it.
```
Subtitle: He counts. You can see his lips do it.

### 385. `dlg.scene_knocking.wrote.0.p1.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/wrote#0; part 2 of 5: holloway: Wrote them down with the hill party. At the cave mouths. Some of the hill came home; nobod… / **narrator: He looks into the cup, finds it empty, and keeps holding it.** / holloway: Go to bed. / narrator: He gets up, holding the gatepost, and looks down the dark road. / holloway: Somebody's still out. ...Always somebody still out.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks into the cup, finds it empty, and keeps holding it.
```
Subtitle: He looks into the cup, finds it empty, and keeps holding it.

### 386. `dlg.scene_knocking.wrote.0.p3.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_knocking/wrote#0; part 4 of 5: holloway: Wrote them down with the hill party. At the cave mouths. Some of the hill came home; nobod… / narrator: He looks into the cup, finds it empty, and keeps holding it. / holloway: Go to bed. / **narrator: He gets up, holding the gatepost, and looks down the dark road.** / holloway: Somebody's still out. ...Always somebody still out.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He gets up, holding the gatepost, and looks down the dark road.
```
Subtitle: He gets up, holding the gatepost, and looks down the dark road.

## Conversations: Scene_did_he

### 387. `dlg.scene_did_he.well.0.p0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_did_he/well#0; part 1 of 2: **narrator: She's waiting for you at the well.** / maeca: He talked to you. Last night. At the gate.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's waiting for you at the well.
```
Subtitle: She's waiting for you at the well.

### 388. `dlg.scene_did_he.kept.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_did_he/kept#0

```
She looks at you the way she looks at a track that might be lying.
```
Subtitle: She looks at you the way she looks at a track that might be lying.

### 389. `dlg.scene_did_he.quiet.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_did_he/quiet#0

```
She waits. You don't fill it. She nods, slowly, as if you had.
```
Subtitle: She waits. You don't fill it. She nods, slowly, as if you had.

## Conversations: Scene_his_cup

### 390. `dlg.scene_his_cup.cup.0.wav`  HOLD: recast as a woman of about sixty, plain and dry (the story rewrite, 6 October); cast her anew before recording

*Where:* dialogue.json scene_his_cup/cup#0

```
At the gate, Holloway is on the ground with his back to the post, counting. He gets as far as ninety-one, and starts again. Mayka comes down the street, and takes the cup out of his hand, and fills it from her own flask, and gives it back. He drinks without looking at it. Then she sits down beside him with her crossbow across her knees, and he leans on her a little, and she lets him.
```
Subtitle: At the gate, Holloway is on the ground with his back to the post, counting. He gets as far as ninety-one, and starts again. Maeca comes down the street, and takes the cup out of his hand, and fills it from her own flask, and gives it back. He drinks without looking at it. Then she sits down beside him with her crossbow across her knees, and he leans on her a little, and she lets him.

## Conversations: Warden_answer

### 391. `dlg.warden_answer.wait.0.wav`  **LOCKED FOR RECORDING**

*Where:* dialogue.json warden_answer/wait#0
*Played:* volume: quiet.

```
[quietly] He waits for an answer, the lamp held up to your face.
```
Subtitle: He waits for an answer, the lamp held up to your face.


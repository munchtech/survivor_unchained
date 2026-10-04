# The narrator: ElevenLabs packet

Voice id in the game: `narrator`. 301 takes to record (29,769 characters; about 89,307 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

**Hold 2 of these** (marked HOLD below) until the owner's choice of how the hymn is sung (README) is back; the rest can be recorded now.

## Who they are

**The narrator.** Present tense, second person, plain nouns and working verbs; one image per line, never two adjectives where one will do. Says what happens and what can be seen, never what it means. Never theatrical, never cute, never names a feeling the scene has already shown. *Casting:* 50s, neutral RP, low and close; a winter's tale told by the fire, slight gravel, unhurried.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU The narrator`. Never describe a voice as sounding like a real person.

```
Native English (British, Received Pronunciation). Male, 50s. Studio quality. Persona: an old storyteller. A man in his mid fifties with a low, warm, slightly gravelly baritone and a neutral southern English Received Pronunciation accent. He speaks quietly and close, unhurried and even, like an old storyteller telling a winter's tale by the fire. Plain and grave, never theatrical. Crisp Received Pronunciation. No reverb or effects.
```

Preview text:

```
The fire has burned low. Out in the dark, the ground is moving, and somewhere ahead there is water, and a cold blue light. You get up, because there is nothing else to do.
```

In the Voice Library instead: search for *neutral southern English (RP)*, *male*, *50*, and listen for this: A man in his mid fifties with a low, warm, slightly gravelly baritone and a neutral southern English Received Pronunciation accent. Use only voices whose library licence allows commercial use.

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

## How he reads

The narrator never shows a feeling: plain, the same pace throughout, and the facts do the work (the story lead's rule). The notes say what each line is doing; play none of it. His tags say only how loud.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: drowned fire

### 1. `dlg.cin_drowned_fire.bedroll.0.wav`

*Where:* dialogue.json cin_drowned_fire/bedroll#0
*Played:* quiet unease; doing: you did not sleep here; pace: slow; volume: quiet.
*Note:* Plain and close.

```
[quietly] Your bedroll has not been slept in.
```
Subtitle: Your bedroll has not been slept in.

### 2. `dlg.cin_drowned_fire.prints.0.wav`

*Where:* dialogue.json cin_drowned_fire/prints#0
*Played:* creeping dread; doing: your own prints come from the river; pace: slow; volume: quiet.
*Note:* 'None go down to it.' alone, very quiet.

```
[quietly] Prints in the frost, your own. They come up from the river. None go down to it.
```
Subtitle: Prints in the frost, your own. They come up from the river. None go down to it.

### 3. `dlg.cin_drowned_fire.frost.0.wav`

*Where:* dialogue.json cin_drowned_fire/frost#0
*Played:* uneasy; doing: something is coming; pace: slow; volume: quiet.

```
[quietly] Past the firelight, the frost is breaking.
```
Subtitle: Past the firelight, the frost is breaking.

## Scenes: Prologue

### 4. `say.dabd6c78b40d.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* sombre, careful; doing: reads a dead man and his last words; pace: slow; volume: quiet.
*Note:* The book's lines read as written words, each more unsettled; 'singing in the water' nearly a whisper.

```
[quietly] A Watchman, grey-bearded and a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes: "Lamps at the Low Ford lit again, and not by us. Not oil. Wrong colour." "Sent Dannet for the captain. Dannet not back." "The Warden is walking. I can hear it singing in the water."
```
Subtitle: A Watchman, grey-bearded and a long time dead, sitting against the post as if he had only stopped for breath. Something has had his eyes. In his belt-book, three lines in a hand that worsens as it goes: "Lamps at the Low Ford lit again, and not by us. Not oil. Wrong colour." "Sent Dannet for the captain. Dannet not back." "The Warden is walking. I can hear it singing in the water."

### 5. `say.178e6dd0ad78.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* eerie wonder; doing: a dead man speaks to you alone; pace: slow; volume: hushed.

```
[whispers] ...and for you alone, the dead man's jaw moves.
```
Subtitle: ...and for you alone, the dead man's jaw moves.

### 6. `say.3dcd3f3caa00.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* flat warning; doing: tells the survivor the fire is no protection; pace: measured; volume: quiet.
*Note:* Matter-of-fact; the second sentence lands harder by being plainer.

```
[quietly] The fire is almost out. It will not hold them back.
```
Subtitle: The fire is almost out. It will not hold them back.

### 7. `say.4d8a46e7502e.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* uneasy calm; doing: the quake stops; the way is north; pace: measured; volume: quiet.
*Note:* 'For now.' on its own, dry. The road north plainly, a little warmer.

```
[quietly] The ground goes still. For now. The road runs north, toward the Waystation.
```
Subtitle: The ground goes still. For now. The road runs north, toward the Waystation.

### 8. `say.2b72fa1dd85e.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* grim, still; doing: shows the ambush before it springs; pace: slow; volume: quiet.
*Note:* Three images, each its own weight. A held beat before 'They were waiting', said colder and lower.

```
[quietly] A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting.
```
Subtitle: A wagon on its side, and the ditch beside it full of the drowned. One of them is still holding the reins. They were waiting.

### 9. `say.77eb67f9e183.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* tense, hushed; doing: a threat notices you; pace: measured; volume: quiet.
*Note:* Even through 'dead watchman', then the last sentence slower: it turns to look at you.

```
[quietly] Something in old armour is standing guard over the dead watchman. It turns to look at you.
```
Subtitle: Something in old armour is standing guard over the dead watchman. It turns to look at you.

### 10. `say.0663505a2971.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain, restrained; doing: the first dead you killed was a child; pace: slow; volume: quiet.
*Note:* The narrator never shows a feeling: plain, the same pace throughout, and the facts do the grief. No catch before 'twelve at most'; 'and new boots' no softer than the rest. That restraint is the scene.

```
[quietly] The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.
```
Subtitle: The last of them falls back into the ditch and stays there. The one with the reins was a girl, twelve at most: red hair under the weed, and new boots.

### 11. `say.1e2fc7986134.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* relief, then awe; doing: the fight ends, something waits ahead; pace: slow; volume: quiet.
*Note:* Exhale on 'The dead go quiet.' Then hushed, drawn forward: water, and a cold blue light.

```
[quietly] The dead go quiet. Somewhere ahead, water, and a cold blue light.
```
Subtitle: The dead go quiet. Somewhere ahead, water, and a cold blue light.

### 12. `say.f1f67faea5fb.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* uncanny, dry; doing: something strange beyond the fence; pace: measured; volume: quiet.
*Note:* Deadpan on 'The graves are listening.' Not spooky; simply true.

```
[quietly] Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.
```
Subtitle: Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.

### 13. `say.f67dd9f6e97c.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* awe, dread; doing: the Warden is seen for the first time; pace: slow; volume: hushed.
*Note:* Half a whisper. Space after 'in the ford'. 'with a lamp in its fist' plain and heavy.

```
[whispers] Something lies in the ford, larger than any man, with a lamp in its fist.
```
Subtitle: Something lies in the ford, larger than any man, with a lamp in its fist.

### 14. `say.33579e176a7e.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* wonder after violence; doing: the Warden's heart, still alive; pace: slow; volume: quiet.
*Note:* Breathing again after the fight. 'full of cold light' with quiet wonder.

```
[quietly] Where the Warden fell, its heart is still burning: a stone the size of a fist, full of cold light.
```
Subtitle: Where the Warden fell, its heart is still burning: a stone the size of a fist, full of cold light.

### 15. `say.3eba0841cd10.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* dawn relief, warmth; doing: the night is over; pace: slow; volume: level.
*Note:* The first warmth in the narrator's voice. 'then gold' opens up.

```
Grey light, then gold. Up the road, the Waystation's gate is opening.
```
Subtitle: Grey light, then gold. Up the road, the Waystation's gate is opening.

### 16. `say.8c74ea2b0476.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain, quiet; doing: dawn takes the ember back; pace: slow; volume: quiet.
*Note:* The narrator never shows a feeling. The rules plainly; 'from nothing.' level. The last sentence about the mother's face no softer than the rest: the fact does it.

```
[quietly] As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again, from nothing. You try to call up your mother's face, and find it is not quite where you left it.
```
Subtitle: As the sun clears the trees, the ember goes out of you and back into the ground, and everything it gave you goes with it. What you carry, and what you have learned, are still yours. When the dark comes again, it will burn again, from nothing. You try to call up your mother's face, and find it is not quite where you left it.

### 17. `say.24c69afd4e5e.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: you were not here; pace: measured; volume: quiet.
*Note:* One plain fact.

```
[quietly] Your bedroll has not been slept in.
```
Subtitle: Your bedroll has not been slept in.

### 18. `say.2d8b284f0b0e.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain, uneasy; doing: your own prints; pace: slow; volume: quiet.
*Note:* A beat before 'None go down to it.'

```
[quietly] Prints in the frost, your own. They come up from the river. None go down to it.
```
Subtitle: Prints in the frost, your own. They come up from the river. None go down to it.

### 19. `say.1096c4f7e3e0.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* plain; doing: dawn; pace: measured; volume: quiet.

```
[quietly] Past the firelight, the frost is breaking.
```
Subtitle: Past the firelight, the frost is breaking.

### 20. `say.c4d495431666.wav`

*Where:* godot/logic/Play/Zones/Prologue.cs
*Played:* grim, knowing; doing: death will not take you yet; pace: measured; volume: quiet.
*Note:* Low, a little ominous, not triumphant.

```
[quietly] The ember will not let you go so easily.
```
Subtitle: The ember will not let you go so easily.

## Cinematic: none cross

### 21. `dlg.cin_none_cross.call.0.p0.wav`

*Where:* dialogue.json cin_none_cross/call#0; part 1 of 2: **narrator: sung, under the water** / warden: Lamps are lit... stay where they reach...
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] sung, under the water
```
Subtitle: sung, under the water

## Cinematic: heart goes down

### 22. `dlg.cin_heart_goes_down.grateful.0.p1.wav`

*Where:* dialogue.json cin_heart_goes_down/grateful#0; part 2 of 3: grimtunnel: Finders keepers, surface-m— / **narrator: a sniff** / grimtunnel: ...Downstairs'll be ever so grateful.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] a sniff
```
Subtitle: a sniff

## Cinematic: first light

### 23. `dlg.cin_first_light.back.0.wav`

*Where:* dialogue.json cin_first_light/back#0
*Played:* gentle loss; doing: the ember fades; pace: slow; volume: quiet.

```
[quietly] The sun clears the trees, and the ember goes back into the ground.
```
Subtitle: The sun clears the trees, and the ember goes back into the ground.

### 24. `dlg.cin_first_light.face.0.wav`

*Where:* dialogue.json cin_first_light/face#0
*Played:* gentle loss, unsettling; doing: the mother's face; pace: slow; volume: quiet.
*Note:* Almost tender, and wrong.

```
[quietly] You try to call up your mother's face, and find it is not quite where you left it.
```
Subtitle: You try to call up your mother's face, and find it is not quite where you left it.

### 25. `dlg.cin_first_light.baking.0.wav`

*Where:* dialogue.json cin_first_light/baking#0
*Played:* dawn warmth; doing: ordinary life; pace: slow; volume: quiet.
*Note:* The first warmth after the night.

```
[quietly] Somewhere up the street, someone is baking.
```
Subtitle: Somewhere up the street, someone is baking.

## Cinematic: iron marker

### 26. `dlg.cin_iron_marker.verse1.0.p0.wav`  HOLD

*Where:* dialogue.json cin_iron_marker/verse1#0; part 1 of 2: **narrator: sung** / chid: Lie down, lie down, the lamps are tended, / and all the dark is kept; / the morning lies a…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] sung
```
Subtitle: sung

### 27. `dlg.cin_iron_marker.verse2.0.p0.wav`  HOLD

*Where:* dialogue.json cin_iron_marker/verse2#0; part 1 of 2: **narrator: sung** / chid: Lie down, lie down, the road is ended, / your toll is paid and kept; / the dark is but the…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] sung
```
Subtitle: sung

## Cinematic: raid on the roost

### 28. `dlg.cin_raid_on_the_roost.last.0.p1.wav`

*Where:* dialogue.json cin_raid_on_the_roost/last#0; part 2 of 3: redcowl: ...Ashford. / **narrator: a laugh** / redcowl: There. Now we've both said it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] a laugh
```
Subtitle: a laugh

## Scenes: Verge

### 29. `say.ac8270282f9f.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* calm, watchful; doing: the Pack lets you pass; pace: slow; volume: quiet.
*Note:* Still and level.

```
[quietly] The wolves watch you come. None of them move to stop you.
```
Subtitle: The wolves watch you come. None of them move to stop you.

### 30. `say.3ff82d4e2ac7.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* sudden danger; doing: the wolf cloak has damned you; pace: measured; volume: quiet.
*Note:* Tighten on the second sentence: every wolf is on its feet.

```
[quietly] They smell the cloak before they see you. Every wolf in the Hollow is on its feet.
```
Subtitle: They smell the cloak before they see you. Every wolf in the Hollow is on its feet.

### 31. `say.3a93e764b57c.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* dread, rueful; doing: the Pack knows what you did; pace: measured; volume: quiet.
*Note:* The second sentence a quiet reproach: Maeca warned you.

```
[quietly] They smell the blood on you before they see you. Mayka said none since you last slept.
```
Subtitle: They smell the blood on you before they see you. Maeca said none since you last slept.

### 32. `say.6ea507a14576.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* menace; doing: you are surrounded; pace: slow; volume: hushed.
*Note:* Low, almost under the breath.

```
[whispers] Low growling from every side of the Hollow.
```
Subtitle: Low growling from every side of the Hollow.

### 33. `say.f45eec417fcc.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: the Kerchief camp is ordinary; pace: measured; volume: quiet.
*Note:* The narrator never shows a feeling; the ordinary details do it.

```
[quietly] Red cloth at every tent, washing on a line, children with a wooden sword. They see your colours and go back to what they were doing.
```
Subtitle: Red cloth at every tent, washing on a line, children with a wooden sword. They see your colours and go back to what they were doing.

### 34. `say.2133e8a51219.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* plain; doing: a woman feeds the caged; pace: measured; volume: quiet.
*Note:* No comment in the voice.

```
[quietly] By the cages a woman is passing stew in through the bars. Her own child holds up a bowl beside her.
```
Subtitle: By the cages a woman is passing stew in through the bars. Her own child holds up a bowl beside her.

### 35. `say.31fa91331b11.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* awe and unease; doing: the thing in the pit; pace: slow; volume: quiet.
*Note:* Build the size slowly. A dry little pause around 'probably', then 'dead' flat and doubtful.

```
[quietly] The ground shivers. At the bottom of the pit lies something pale and segmented, bigger than a house, and — probably — dead.
```
Subtitle: The ground shivers. At the bottom of the pit lies something pale and segmented, bigger than a house, and — probably — dead.

### 36. `say.b76e3053dc5f.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* hushed awe, dread; doing: the Morrow is alive; pace: very slow; volume: hushed.
*Note:* The most important hush in Act 1. Each of 'slow, patient, enormous' its own breath. 'Not breathing.' then a long beat. 'Praying.' barely voiced.

```
[whispers] Under the silence you hear it, for as long as a held breath: slow, patient, enormous. Not breathing. Praying.
```
Subtitle: Under the silence you hear it, for as long as a held breath: slow, patient, enormous. Not breathing. Praying.

### 37. `say.0b5e75f9dfa0.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* dry, pointed; doing: the caravan was robbed, not eaten; pace: measured; volume: level.
*Note:* Deadpan on 'Wolves do not drive wagons.'

```
Three wagons, dragged off the road into the trees. Wolves do not drive wagons.
```
Subtitle: Three wagons, dragged off the road into the trees. Wolves do not drive wagons.

### 38. `say.e6c4fb3a8998.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* investigative, terse; doing: clues at the wreck; pace: measured; volume: quiet.
*Note:* Clipped observations, a beat before 'Under the seat'.

```
[quietly] Kerchief arrows in the sideboards, red-fletched. The strongbox bolts are sprung, the box gone. Under the seat: a torn manifest.
```
Subtitle: Kerchief arrows in the sideboards, red-fletched. The strongbox bolts are sprung, the box gone. Under the seat: a torn manifest.

### 39. `say.20dc615919d1.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* terse, drawn forward; doing: the trail leads to the ravine; pace: measured; volume: quiet.
*Note:* 'Toward the ravine.' lower, a destination.

```
[quietly] Deep ruts, heavy wagons, driven south-east into the trees. Toward the ravine.
```
Subtitle: Deep ruts, heavy wagons, driven south-east into the trees. Toward the ravine.

### 40. `say.cfa493798ba7.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* relief, warmth; doing: a moment of safety; pace: slow; volume: quiet.
*Note:* Warm and soft; the only comfort in the wood.

```
[quietly] The old fire takes. For a little while, this is a safe place.
```
Subtitle: The old fire takes. For a little while, this is a safe place.

### 41. `say.8e845892b699.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* clinical, grim; doing: the wolf was poisoned; pace: measured; volume: quiet.
*Note:* A list like a surgeon's; the last sentence slower and darker.

```
[quietly] No wound. Black gums, milky eyes, ribs like a washboard, and the belly swollen hard. It drank something that rotted it from the inside.
```
Subtitle: No wound. Black gums, milky eyes, ribs like a washboard, and the belly swollen hard. It drank something that rotted it from the inside.

### 42. `say.52d0f1dfa274.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* puzzled, sombre; doing: a wolf dead of no wound; pace: measured; volume: quiet.
*Note:* Plain.

```
[quietly] A wolf, dead, with no wound on it. Its eyes have gone milky.
```
Subtitle: A wolf, dead, with no wound on it. Its eyes have gone milky.

### 43. `say.7197a1b189a3.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* uneasy, sensory; doing: the stream is wrong; pace: slow; volume: quiet.
*Note:* Three senses, unhurried; 'a chapel lamp' with a faint wrongness.

```
[quietly] The water is warm, and faintly green, and smells like a chapel lamp.
```
Subtitle: The water is warm, and faintly green, and smells like a chapel lamp.

### 44. `say.84f6c2c74004.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* grim discovery; doing: the source of the poison; pace: measured; volume: quiet.
*Note:* Clipped, observant. Lift on 'the drag-marks of lamps' (a clue).

```
[quietly] Riveted iron, warm to the touch, spilling glowing slurry into the stream. Small clawed prints all round it, and the drag-marks of lamps.
```
Subtitle: Riveted iron, warm to the touch, spilling glowing slurry into the stream. Small clawed prints all round it, and the drag-marks of lamps.

### 45. `say.48cdd82e6c0b.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* wary, plain; doing: to make the player feel one charge's weight in the hand; pace: slow; volume: quiet.
*Wants:* to make the player feel one charge's weight in the hand
*Note:* Low and close, as if not to wake them. A small pause before 'the way they have waited for everyone': the crates are patient, and that is the threat.

```
[quietly] You prise one charge out of the straw. The rest sit there and wait, the way they have waited for everyone.
```
Subtitle: You prise one charge out of the straw. The rest sit there and wait, the way they have waited for everyone.

### 46. `say.4acad56ca838.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* held breath; doing: to let the relief arrive in the silence; pace: slow; volume: quiet.
*Wants:* to let the relief arrive in the silence
*Note:* 'One at a time' is a held breath; 'not go off' lands flat and quiet, almost dry. No triumph.

```
[quietly] You roll them down into the ravine's water one at a time, and listen to each one not go off.
```
Subtitle: You roll them down into the ravine's water one at a time, and listen to each one not go off.

### 47. `say.769a1c759f88.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* urgent; doing: get clear; pace: quick; volume: level.
*Note:* Tight and fast. 'Run.' sharp but not shouted.

```
The fuse fizzes. You have a few seconds. Run.
```
Subtitle: The fuse fizzes. You have a few seconds. Run.

### 48. `say.384c340b6b6d.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* awe, unease; doing: the sigil wakes; pace: slow; volume: quiet.
*Note:* 'like an eye opening' slower. 'The door is listening.' hushed.

```
[quietly] The fragment fits one notch of the seven, and under your hand the whole sigil wakes, violet, like an eye opening. The door is listening.
```
Subtitle: The fragment fits one notch of the seven, and under your hand the whole sigil wakes, violet, like an eye opening. The door is listening.

### 49. `say.9757e1dab88e.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* curious, uneasy; doing: the sigil waits for night; pace: measured; volume: quiet.
*Note:* The last clause dry and ominous.

```
[quietly] The fragment fits one notch of the seven, and the stone warms under it. Whatever the sigil is waiting for, it is not daylight.
```
Subtitle: The fragment fits one notch of the seven, and the stone warms under it. Whatever the sigil is waiting for, it is not daylight.

### 50. `say.66cdbe61b828.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* solemn; doing: reading the Legion's words; pace: slow; volume: quiet.
*Note:* The inscription read gravely as old words. 'all empty' quiet.

```
[quietly] Old-empire script over the door. Here the Seventh Legion buried what it could not burn. Below it, a sigil with seven notches, all empty.
```
Subtitle: Old-empire script over the door. Here the Seventh Legion buried what it could not burn. Below it, a sigil with seven notches, all empty.

### 51. `say.20b15596c09c.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* wary, solemn; doing: the sealed door; pace: slow; volume: quiet.
*Note:* The Latin said slowly and gravely, as old words.

```
[quietly] A door of black stone, smooth as glass. Cut over it, words in a dead tongue: hic legio septima sepelivit quod urere non potuit. Under them, a violet sigil you cannot read. It hums against your teeth.
```
Subtitle: A door of black stone, smooth as glass. Cut over it, words in a dead tongue: hic legio septima sepelivit quod urere non potuit. Under them, a violet sigil you cannot read. It hums against your teeth.

### 52. `say.82b1e8294244.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* quiet discovery; doing: a key-stone in dead hands; pace: slow; volume: quiet.
*Note:* Plain.

```
[quietly] In the bones of one hand, a wedge of black stone cut to fit something.
```
Subtitle: In the bones of one hand, a wedge of black stone cut to fit something.

### 53. `say.8591ecfe4019.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* eerie; doing: the skull turns; pace: slow; volume: hushed.

```
[whispers] The skull turns, very slightly, toward you.
```
Subtitle: The skull turns, very slightly, toward you.

### 54. `say.6e1fab16785e.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* investigative, uneasy; doing: someone went in and did not come out; pace: measured; volume: quiet.
*Note:* 'None coming away.' alone, ominous. The token a careful find.

```
[quietly] Bootprints in the mud, fresh, going up to the door. None coming away. Trodden into one heel-print: a copper toll-token, stamped with three roads.
```
Subtitle: Bootprints in the mud, fresh, going up to the door. None coming away. Trodden into one heel-print: a copper toll-token, stamped with three roads.

### 55. `say.b40ac14379d8.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* tender, sombre; doing: a treasure where wolves go to die; pace: slow; volume: quiet.
*Note:* Gentle; 'cold as snow' soft.

```
[quietly] Under the brambles, where the wolves go when one of them is dying: a circlet of moonsilver, cold as snow.
```
Subtitle: Under the brambles, where the wolves go when one of them is dying: a circlet of moonsilver, cold as snow.

### 56. `say.1a95cdeef839.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* pity, plain; doing: a freed prisoner; pace: measured; volume: quiet.
*Note:* No sentiment; the nails are the detail.

```
[quietly] A teamster, thin and grey, stumbles out and grips your arm. His nails are broken to the quick from the bars.
```
Subtitle: A teamster, thin and grey, stumbles out and grips your arm. His nails are broken to the quick from the bars.

### 57. `say.75abd0854536.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* wry tenderness; doing: a freed prisoner; pace: measured; volume: quiet.
*Note:* A small half-smile in the voice.

```
[quietly] A woman who will not stop saying thank you.
```
Subtitle: A woman who will not stop saying thank you.

### 58. `say.fccd00002739.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* pity, plain; doing: Jory in the cage; pace: measured; volume: quiet.

```
[quietly] A young man, freckled, still holding the bars after the door is open.
```
Subtitle: A young man, freckled, still holding the bars after the door is open.

### 59. `say.f1bc8c3f22ed.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* grim satisfaction; doing: the pump breaks; pace: measured; volume: quiet.
*Note:* Each stopping its own short sentence, settling.

```
[quietly] Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.
```
Subtitle: Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.

### 60. `say.a4755c96100b.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* horror held flat; doing: the cost of the blast; pace: slow; volume: quiet.
*Note:* Unflinching and quiet. 'Most of them do not crawl far.' almost gentle, which is worse.

```
[quietly] When the dust comes down, the hillside is a wound. Small shapes crawl out of it with their lamps still lit. Some of them are on fire. Most of them do not crawl far.
```
Subtitle: When the dust comes down, the hillside is a wound. Small shapes crawl out of it with their lamps still lit. Some of them are on fire. Most of them do not crawl far.

### 61. `say.26621b48a47e.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* horror held flat; doing: the cost of the fire; pace: slow; volume: quiet.
*Note:* Level, no relish. A breath before 'and then there is only the fire', said very low.

```
[quietly] The fire takes the tents, and then the cages. There is screaming, and the smell, and hands through the bars; and then there is only the fire.
```
Subtitle: The fire takes the tents, and then the cages. There is screaming, and the smell, and hands through the bars; and then there is only the fire.

### 62. `say.0622cbb5851c.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* wonder; doing: a hidden glade; pace: measured; volume: quiet.
*Note:* Quick on the fire, softer on the glade.

```
[quietly] The brambles go up like paper. Beyond them, a glade full of pale light.
```
Subtitle: The brambles go up like paper. Beyond them, a glade full of pale light.

### 63. `say.005625eee2b8.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* wonder; doing: a hidden glade; pace: measured; volume: quiet.
*Note:* Effort, then softer on the glade.

```
[quietly] You hack a way through the brambles. Beyond them, a glade full of pale light.
```
Subtitle: You hack a way through the brambles. Beyond them, a glade full of pale light.

### 64. `say.cc4a3505429e.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* quiet pride; doing: the Pack runs with you; pace: slow; volume: quiet.
*Note:* Warm and still.

```
[quietly] Four grey shapes fall in beside you at the edge of the wood.
```
Subtitle: Four grey shapes fall in beside you at the edge of the wood.

### 65. `say.e08ae8c1e46c.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* dry, a little rueful; doing: your fallen things, found; pace: measured; volume: quiet.
*Note:* Dry on 'most of them'.

```
[quietly] Where you fell. The ground has kept your things for you, most of them.
```
Subtitle: Where you fell. The ground has kept your things for you, most of them.

## Scenes: Waystation

### 66. `say.6947705bd0e4.wav`

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* quiet, faintly wistful; doing: a small human mark on the well; pace: measured; volume: quiet.
*Note:* Read 'M. plus J.' as letters: 'em and jay'.

```
[quietly] The water is a long way down, and clean. Somebody has scratched M and J into the stone.
```
Subtitle: The water is a long way down, and clean. Somebody has scratched M and J into the stone.

### 67. `say.8b004f74544d.wav`

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* dry satisfaction; doing: the warehouse opens; pace: measured; volume: quiet.
*Note:* 'turns sweetly' with a hint of relish; the ledger line dry.

```
[quietly] The clerk's key turns sweetly. Inside: crates, dust, and a ledger Pell should have burned.
```
Subtitle: The clerk's key turns sweetly. Inside: crates, dust, and a ledger Pell should have burned.

### 68. `say.ff981a5b72be.wav`

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* dry satisfaction; doing: the warehouse opens; pace: measured; volume: quiet.
*Note:* Quiet, careful, like a lockpick's breath.

```
[quietly] The lock gives under your picks. Inside: crates, dust, and a ledger Pell should have burned.
```
Subtitle: The lock gives under your picks. Inside: crates, dust, and a ledger Pell should have burned.

### 69. `say.546ec60933f6.wav`

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain, still; doing: Nell's burial; pace: slow; volume: quiet.
*Note:* The narrator never shows a feeling. Three strokes, each its own beat. 'and steps back, and back.' level.

```
[quietly] The whole town is in the Quiet Garden, round a fresh grave beside the old captain's stone. Brannock kneels at its head with an iron marker and his hammer: three strokes, iron into earth. Rook sets the inn's lamp at its foot, lit, in broad daylight, and steps back, and back.
```
Subtitle: The whole town is in the Quiet Garden, round a fresh grave beside the old captain's stone. Brannoc kneels at its head with an iron marker and his hammer: three strokes, iron into earth. Rook sets the inn's lamp at its foot, lit, in broad daylight, and steps back, and back.

### 70. `say.a5b99f61e011.wav`

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* quiet discovery; doing: an old captain's trunk; pace: slow; volume: quiet.
*Note:* The note read gently, as written words: 'Keep the lights lit.' Then the initial: 'C.'

```
[quietly] Beside the old captain's stone, sunk in the nettles, a trunk the Watch forgot: ember shards, a purse, and a note. Keep the lights lit. C.
```
Subtitle: Beside the old captain's stone, sunk in the nettles, a trunk the Watch forgot: ember shards, a purse, and a note. Keep the lights lit. C.

### 71. `say.8c1f7c369819.wav`

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain, observant; doing: arrival in town; pace: measured; volume: level.
*Note:* A list of sensations, unhurried. 'News travels fast here.' dry.

```
The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.
```
Subtitle: The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.

### 72. `say.a49e30d2ba1e.wav`

*Where:* godot/logic/Play/Zones/Waystation.cs
*Played:* plain, mildly intrigued; doing: a new stall in town; pace: measured; volume: level.
*Note:* Lift slightly on 'places the road forgets'.

```
A cartographer has set up a stall on the Old Road, by the east gate: maps to places the road forgets.
```
Subtitle: A cartographer has set up a stall on the Old Road, by the east gate: maps to places the road forgets.

## Conversations: Rook

### 73. `dlg.rook.cb_told_brannoc.0.p1.wav`

*Where:* dialogue.json rook/cb_told_brannoc#0; part 2 of 3: rook: You told Brannoc about his girl. / **narrator: She wipes the same bit of counter for a while.** / rook: Good. Somebody had to, and it was never going to be me. ...Sit down. You look like you wan…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She wipes the same bit of counter for a while.
```
Subtitle: She wipes the same bit of counter for a while.

## Conversations: Chid

### 74. `dlg.chid.woke.0.p1.wav`

*Where:* dialogue.json chid/woke#0; part 2 of 3: chid: Up again. Up's good. / **narrator: He has the kettle on already.** / chid: The carter brought you in, before you ask. You'll be sore a day or two. Whatever did it ha…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He has the kettle on already.
```
Subtitle: He has the kettle on already.

### 75. `dlg.chid.woke.1.p1.wav`

*Where:* dialogue.json chid/woke#1; part 2 of 3: chid: You're up. A carter brought you in. / **narrator: He isn't looking at you.** / chid: Well. Someone did. Someone always does. You'll be sore a day or two, and whatever did this…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He isn't looking at you.
```
Subtitle: He isn't looking at you.

### 76. `dlg.chid.woke.2.p1.wav`

*Where:* dialogue.json chid/woke#2; part 2 of 3: chid: You're awake! A carter found you. The same carter, as it happens; he's starting to think y… / **narrator: He laughs, and stops.** / chid: You'll be sore a day or two. Whatever did this is still out there. It'll have your things.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He laughs, and stops.
```
Subtitle: He laughs, and stops.

### 77. `dlg.chid.relight.0.wav`

*Where:* dialogue.json chid/relight#0
*Played:* quiet reverence, then fond humour; doing: the shrine is lit again; pace: slow; volume: quiet.
*Note:* The words of the Order said with care. 'as if it had been waiting for it' with wonder. The kettle line with a smile.

```
[quietly] You open your lantern and say the words you learned at seven, the ones about the dark being only the part of the day that hasn't happened yet. The shrine takes the flame as if it had been waiting for it. Chid makes a sound like a kettle.
```
Subtitle: You open your lantern and say the words you learned at seven, the ones about the dark being only the part of the day that hasn't happened yet. The shrine takes the flame as if it had been waiting for it. Chid makes a sound like a kettle.

### 78. `dlg.chid.note.0.p1.wav`

*Where:* dialogue.json chid/note#0; part 2 of 5: chid: Was there! / **narrator: He's suddenly very interested in a candle.** / chid: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, wh… / narrator: He stops. / chid: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's suddenly very interested in a candle.
```
Subtitle: He's suddenly very interested in a candle.

### 79. `dlg.chid.note.0.p3.wav`

*Where:* dialogue.json chid/note#0; part 4 of 5: chid: Was there! / narrator: He's suddenly very interested in a candle. / chid: A C. Lovely. Lots of people start with C. Cuthbert. Cressida. There was a Cormac, once, wh… / **narrator: He stops.** / chid: It's a lovely old hand, whoever it was. Nobody makes a C like that any more. Nobody's made…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He stops.
```
Subtitle: He stops.

### 80. `dlg.chid.cb_nell.0.p1.wav`

*Where:* dialogue.json chid/cb_nell#0; part 2 of 3: chid: I sang it flat. I always have. There's always somebody who has the tune. / **narrator: He is quiet, which he never is.** / chid: She was very light. ...Sit down a minute. Not on the step. Here. By me.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He is quiet, which he never is.
```
Subtitle: He is quiet, which he never is.

### 81. `dlg.chid.cb_nell.1.p1.wav`

*Where:* dialogue.json chid/cb_nell#1; part 2 of 3: chid: We buried Nell behind the shrine, next to old Ashe. Brannoc made the marker himself. Iron.… / **narrator: He is quiet, which he never is.** / chid: She was very light. ...Sit down a minute. Not on the step. Here. By me.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He is quiet, which he never is.
```
Subtitle: He is quiet, which he never is.

### 82. `dlg.chid.carter.0.p1.wav`

*Where:* dialogue.json chid/carter#0; part 2 of 3: chid: ...You know, I never asked his name. I should ask his name. Next time. / **narrator: He puts a cup in your hands.** / chid: Drink that. It's only hot water. There's nothing in it but hot.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts a cup in your hands.
```
Subtitle: He puts a cup in your hands.

## Conversations: Brannoc

### 83. `dlg.brannoc.hub.1.p0.wav`

*Where:* dialogue.json brannoc/hub#1; part 1 of 2: **narrator: He works. He doesn't stop when you come in, and he doesn't send you away.** / brannoc: Steel or fur?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He works. He doesn't stop when you come in, and he doesn't send you away.
```
Subtitle: He works. He doesn't stop when you come in, and he doesn't send you away.

### 84. `dlg.brannoc.irons.0.p0.wav`

*Where:* dialogue.json brannoc/irons#0; part 1 of 2: **narrator: He looks at the two irons on the rack for a long time.** / brannoc: Twelve ordered. Ten went down to the ford, at night, square coin on the anvil. ...Buyer'll…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at the two irons on the rack for a long time.
```
Subtitle: He looks at the two irons on the rack for a long time.

### 85. `dlg.brannoc.mark.0.p0.wav`

*Where:* dialogue.json brannoc/mark#0; part 1 of 4: **narrator: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is.** / brannoc: Mine. / narrator: He holds it a long time. / brannoc: ...Mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is.
```
Subtitle: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is.

### 86. `dlg.brannoc.mark.0.p2.wav`

*Where:* dialogue.json brannoc/mark#0; part 3 of 4: narrator: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is. / brannoc: Mine. / **narrator: He holds it a long time.** / brannoc: ...Mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He holds it a long time.
```
Subtitle: He holds it a long time.

### 87. `dlg.brannoc.mark.1.p0.wav`

*Where:* dialogue.json brannoc/mark#1; part 1 of 4: **narrator: He takes it. Turns it to the light. Puts his thumb under the socket.** / brannoc: Mine. Mark's under there. Last winter's work: twelve for the Low Ford, ten collected, at n… / narrator: He gives it back. / brannoc: Keep it. It's done what it was for.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes it. Turns it to the light. Puts his thumb under the socket.
```
Subtitle: He takes it. Turns it to the light. Puts his thumb under the socket.

### 88. `dlg.brannoc.mark.1.p2.wav`

*Where:* dialogue.json brannoc/mark#1; part 3 of 4: narrator: He takes it. Turns it to the light. Puts his thumb under the socket. / brannoc: Mine. Mark's under there. Last winter's work: twelve for the Low Ford, ten collected, at n… / **narrator: He gives it back.** / brannoc: Keep it. It's done what it was for.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He gives it back.
```
Subtitle: He gives it back.

### 89. `dlg.brannoc.irons_after.0.p0.wav`

*Where:* dialogue.json brannoc/irons_after#0; part 1 of 4: **narrator: He puts his hand flat on the two irons.** / brannoc: Buyer'll be back for these. Buyer can come and ask me himself. Or herself. / narrator: The hammer comes down. / brannoc: I'll know the coin.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts his hand flat on the two irons.
```
Subtitle: He puts his hand flat on the two irons.

### 90. `dlg.brannoc.irons_after.0.p2.wav`

*Where:* dialogue.json brannoc/irons_after#0; part 3 of 4: narrator: He puts his hand flat on the two irons. / brannoc: Buyer'll be back for these. Buyer can come and ask me himself. Or herself. / **narrator: The hammer comes down.** / brannoc: I'll know the coin.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer comes down.
```
Subtitle: The hammer comes down.

### 91. `dlg.brannoc.nell.0.p0.wav`

*Where:* dialogue.json brannoc/nell#0; part 1 of 4: **narrator: He doesn't look up from the anvil, and he doesn't stop.** / brannoc: You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the grey m… / narrator: The hammer stops. / brannoc: Mine. Nell. ...You pass them?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't look up from the anvil, and he doesn't stop.
```
Subtitle: He doesn't look up from the anvil, and he doesn't stop.

### 92. `dlg.brannoc.nell.0.p2.wav`

*Where:* dialogue.json brannoc/nell#0; part 3 of 4: narrator: He doesn't look up from the anvil, and he doesn't stop. / brannoc: You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the grey m… / **narrator: The hammer stops.** / brannoc: Mine. Nell. ...You pass them?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer stops.
```
Subtitle: The hammer stops.

### 93. `dlg.brannoc.nell_ditch.0.p0.wav`

*Where:* dialogue.json brannoc/nell_ditch#0; part 1 of 2: **narrator: He puts the hammer down, and looks at the two irons still on the rack, and then he doesn't…** / brannoc: ...Had the reins. She'd want the reins. Always wanted the reins.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts the hammer down, and looks at the two irons still on the rack, and then he doesn't look at anything.
```
Subtitle: He puts the hammer down, and looks at the two irons still on the rack, and then he doesn't look at anything.

### 94. `dlg.brannoc.nell_ditch.1.p0.wav`

*Where:* dialogue.json brannoc/nell_ditch#1; part 1 of 4: **narrator: He puts the hammer down. You have never seen him put the hammer down.** / brannoc: ...Had the reins. / narrator: A long breath, through the nose. / brannoc: She'd want the reins. Always wanted the reins.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts the hammer down. You have never seen him put the hammer down.
```
Subtitle: He puts the hammer down. You have never seen him put the hammer down.

### 95. `dlg.brannoc.nell_ditch.1.p2.wav`

*Where:* dialogue.json brannoc/nell_ditch#1; part 3 of 4: narrator: He puts the hammer down. You have never seen him put the hammer down. / brannoc: ...Had the reins. / **narrator: A long breath, through the nose.** / brannoc: She'd want the reins. Always wanted the reins.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A long breath, through the nose.
```
Subtitle: A long breath, through the nose.

### 96. `dlg.brannoc.nell_gone.0.p1.wav`

*Where:* dialogue.json brannoc/nell_gone#0; part 2 of 3: brannoc: Quick, then. Water's quick. / **narrator: He picks the hammer up and holds it, and doesn't use it.** / brannoc: Forge is shut. Go on.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He picks the hammer up and holds it, and doesn't use it.
```
Subtitle: He picks the hammer up and holds it, and doesn't use it.

### 97. `dlg.brannoc.nell_risen.0.p0.wav`

*Where:* dialogue.json brannoc/nell_risen#0; part 1 of 4: **narrator: He looks at you then. Properly, for the first time.** / brannoc: Got up. / narrator: He says it the way he tests an edge: weighing it. / brannoc: Got up, and you put her down. ...Was it quick?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you then. Properly, for the first time.
```
Subtitle: He looks at you then. Properly, for the first time.

### 98. `dlg.brannoc.nell_risen.0.p2.wav`

*Where:* dialogue.json brannoc/nell_risen#0; part 3 of 4: narrator: He looks at you then. Properly, for the first time. / brannoc: Got up. / **narrator: He says it the way he tests an edge: weighing it.** / brannoc: Got up, and you put her down. ...Was it quick?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He says it the way he tests an edge: weighing it.
```
Subtitle: He says it the way he tests an edge: weighing it.

### 99. `dlg.brannoc.nell_quick.0.p0.wav`

*Where:* dialogue.json brannoc/nell_quick#0; part 1 of 4: **narrator: A long time.** / brannoc: ...Thank you. / narrator: The forge ticks as it cools. / brannoc: Forge is shut. Go on.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A long time.
```
Subtitle: A long time.

### 100. `dlg.brannoc.nell_quick.0.p2.wav`

*Where:* dialogue.json brannoc/nell_quick#0; part 3 of 4: narrator: A long time. / brannoc: ...Thank you. / **narrator: The forge ticks as it cools.** / brannoc: Forge is shut. Go on.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The forge ticks as it cools.
```
Subtitle: The forge ticks as it cools.

### 101. `dlg.brannoc.nell_slow.0.p0.wav`

*Where:* dialogue.json brannoc/nell_slow#0; part 1 of 2: **narrator: He nods, once, as if you've told him a price.** / brannoc: Forge is shut.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He nods, once, as if you've told him a price.
```
Subtitle: He nods, once, as if you've told him a price.

### 102. `dlg.brannoc.nell_lie.0.p0.wav`

*Where:* dialogue.json brannoc/nell_lie#0; part 1 of 4: **narrator: The hammer comes down.** / brannoc: Low Kiln, then. Good. / narrator: And again. / brannoc: Aunt'll feed her up. She's thin.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer comes down.
```
Subtitle: The hammer comes down.

### 103. `dlg.brannoc.nell_lie.0.p2.wav`

*Where:* dialogue.json brannoc/nell_lie#0; part 3 of 4: narrator: The hammer comes down. / brannoc: Low Kiln, then. Good. / **narrator: And again.** / brannoc: Aunt'll feed her up. She's thin.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] And again.
```
Subtitle: And again.

### 104. `dlg.brannoc.nell_look.0.p1.wav`

*Where:* dialogue.json brannoc/nell_look#0; part 2 of 3: brannoc: Didn't look. / **narrator: The hammer comes down.** / brannoc: No. ...Nobody looks.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The hammer comes down.
```
Subtitle: The hammer comes down.

## Conversations: Holloway

### 105. `dlg.holloway.hub.2.p0.wav`

*Where:* dialogue.json holloway/hub#2; part 1 of 2: **narrator: A letter lies open under his lamp, a silver seal broken on it. He turns it face down when …** / holloway: What.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A letter lies open under his lamp, a silver seal broken on it. He turns it face down when you come in, and puts his cup on it.
```
Subtitle: A letter lies open under his lamp, a silver seal broken on it. He turns it face down when you come in, and puts his cup on it.

### 106. `dlg.holloway.hub.4.p0.wav`

*Where:* dialogue.json holloway/hub#4; part 1 of 2: **narrator: He straightens when you come in, and then looks annoyed that he did.** / holloway: You. What is it?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He straightens when you come in, and then looks annoyed that he did.
```
Subtitle: He straightens when you come in, and then looks annoyed that he did.

### 107. `dlg.holloway.ledger_early.0.p0.wav`

*Where:* dialogue.json holloway/ledger_early#0; part 1 of 4: **narrator: He reads it standing up. Then he sits down and reads it again.** / holloway: Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's cler… / narrator: He shuts it. / holloway: Don't tell me where you got it. If you tell me, I have to do something about it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He reads it standing up. Then he sits down and reads it again.
```
Subtitle: He reads it standing up. Then he sits down and reads it again.

### 108. `dlg.holloway.ledger_early.0.p2.wav`

*Where:* dialogue.json holloway/ledger_early#0; part 3 of 4: narrator: He reads it standing up. Then he sits down and reads it again. / holloway: Two payments, one night. Forty to "R." Ten to Jessop, "for the road": that's Vonnra's cler… / **narrator: He shuts it.** / holloway: Don't tell me where you got it. If you tell me, I have to do something about it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He shuts it.
```
Subtitle: He shuts it.

### 109. `dlg.holloway.post.0.p0.wav`

*Where:* dialogue.json holloway/post#0; part 1 of 2: **narrator: He says nothing for long enough that you think he hasn't heard.** / holloway: Grey beard, proud of it? Bad hip? ...Corran. He had that post before I had this one. I wro…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He says nothing for long enough that you think he hasn't heard.
```
Subtitle: He says nothing for long enough that you think he hasn't heard.

### 110. `dlg.holloway.post2.0.p1.wav`

*Where:* dialogue.json holloway/post2#0; part 2 of 3: holloway: Not by us. We've not had oil for those lamps since my first winter, and nobody's asked me … / **narrator: He writes something down, and crosses it out.** / holloway: So somebody had oil. And a reason. ...I'll send two men down with a cart. I owe Corran a h…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He writes something down, and crosses it out.
```
Subtitle: He writes something down, and crosses it out.

### 111. `dlg.holloway.letter.0.p1.wav`

*Where:* dialogue.json holloway/letter#0; part 2 of 3: holloway: Mine. From the north, about the north. / **narrator: The cup doesn't move.** / holloway: Read your own post, if anybody writes to you.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The cup doesn't move.
```
Subtitle: The cup doesn't move.

## Conversations: Tam

### 112. `dlg.tam.fetch.0.wav`

*Where:* dialogue.json tam/fetch#0
*Played:* dry humour, warm; doing: bringing Tam's father home; pace: measured; volume: level.
*Note:* Wry on 'one of them is a fool'. 'He comes.' warm and short.

```
You walk the boy as far as the fence where his Pa lost the goat, and his Pa out of the trees on the other side. He calls you several things on the way, and one of them is a fool. He comes.
```
Subtitle: You walk the boy as far as the fence where his Pa lost the goat, and his Pa out of the trees on the other side. He calls you several things on the way, and one of them is a fool. He comes.

## Conversations: Maeca

### 113. `dlg.maeca.hub.0.p0.wav`

*Where:* dialogue.json maeca/hub#0; part 1 of 2: **narrator: She doesn't look up from her cup.** / maeca: It's late. Say it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't look up from her cup.
```
Subtitle: She doesn't look up from her cup.

### 114. `dlg.maeca.invite.0.p0.wav`

*Where:* dialogue.json maeca/invite#0; part 1 of 2: **narrator: She finishes her cup and stands.** / maeca: I'm going out to the Blind. The fire's big enough for two, if you can keep quiet. Most can…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She finishes her cup and stands.
```
Subtitle: She finishes her cup and stands.

### 115. `dlg.maeca.blind.1.wav`

*Where:* dialogue.json maeca/blind#1
*Played:* intimate, quiet; doing: a night with Maeca; pace: slow; volume: hushed.
*Note:* Close and unhurried, tasteful, no breathiness. The last image tender and a little wry.

```
[whispers] Off in the Hollow the Pack is loud, a long tangle of voices, and she stops with her hands on your buckle and listens, and then she laughs: a short surprised sound, as if she'd trodden on something. "They're eating." She pulls you down onto the hides. Her hands are hard and careful, the way they are with a snare, and then they're not careful. The fire goes down to embers. Neither of you feeds it. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.
```
Subtitle: Off in the Hollow the Pack is loud, a long tangle of voices, and she stops with her hands on your buckle and listens, and then she laughs: a short surprised sound, as if she'd trodden on something. "They're eating." She pulls you down onto the hides. Her hands are hard and careful, the way they are with a snare, and then they're not careful. The fire goes down to embers. Neither of you feeds it. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.

### 116. `dlg.maeca.blind.2.wav`

*Where:* dialogue.json maeca/blind#2
*Played:* intimate, quiet; doing: a night with Maeca; pace: slow; volume: hushed.
*Note:* Close and unhurried; the boots a small ceremony.

```
[whispers] She doesn't talk, and then neither of you needs to. She undoes your boots before anything else, and sets them side by side outside the hides, and that seems to be a decision. Her hands are hard and careful, the way they are with a snare: slow, listening, ready to stop. They become sure. Once, far off, the Pack calls, and she goes still against you until it's done. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.
```
Subtitle: She doesn't talk, and then neither of you needs to. She undoes your boots before anything else, and sets them side by side outside the hides, and that seems to be a decision. Her hands are hard and careful, the way they are with a snare: slow, listening, ready to stop. They become sure. Once, far off, the Pack calls, and she goes still against you until it's done. Later, under the hides, she sleeps like a hunter: lightly, one hand on the crossbow and the other on you.

### 117. `dlg.maeca.blind_morning.0.p0.wav`

*Where:* dialogue.json maeca/blind_morning#0; part 1 of 2: **narrator: Grey light. She's already up, barefoot in the frost, listening.** / maeca: Go on, then. The wood's awake, and so's Holloway, and he'll count us both.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Grey light. She's already up, barefoot in the frost, listening.
```
Subtitle: Grey light. She's already up, barefoot in the frost, listening.

### 118. `dlg.maeca.blind_morning.1.p0.wav`

*Where:* dialogue.json maeca/blind_morning#1; part 1 of 2: **narrator: Grey light. She's already up, barefoot in the frost, listening to the wood.** / maeca: The Pack found me, after Ashford. Three days in a cave mouth with the garrison dead round …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Grey light. She's already up, barefoot in the frost, listening to the wood.
```
Subtitle: Grey light. She's already up, barefoot in the frost, listening to the wood.

### 119. `dlg.maeca.kerchiefs.0.p1.wav`

*Where:* dialogue.json maeca/kerchiefs#0; part 2 of 3: maeca: Some. / **narrator: She drinks, and looks at the cup instead of you.** / maeca: Fed some of them, once. Buried more. ...Ask me about wolves.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She drinks, and looks at the cup instead of you.
```
Subtitle: She drinks, and looks at the cup instead of you.

### 120. `dlg.maeca.cb_knelt.0.p1.wav`

*Where:* dialogue.json maeca/cb_knelt#0; part 2 of 3: maeca: You went into the Hollow with nothing on your hands and knelt to him. I was on the ridge. / **narrator: She looks at your knees.** / maeca: He let you. ...He doesn't let me, and he's known me ten years.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at your knees.
```
Subtitle: She looks at your knees.

### 121. `dlg.maeca.blood.0.p0.wav`

*Where:* dialogue.json maeca/blood#0; part 1 of 2: **narrator: At the edge of the Hollow she stops, and sniffs, once, and turns round.** / maeca: Not with that on you. Wash. River's that way. ...Or sleep, and come tomorrow. The night ta…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] At the edge of the Hollow she stops, and sniffs, once, and turns round.
```
Subtitle: At the edge of the Hollow she stops, and sniffs, once, and turns round.

### 122. `dlg.maeca.blind_walk.0.p0.wav`

*Where:* dialogue.json maeca/blind_walk#0; part 1 of 3: **narrator: She goes out by the east gate without a lamp, and you follow her along the Old Road past t…** / maeca: Him. And the bitch with the white foot. / narrator: She walks on.
*Played:* hushed, attentive; doing: the walk to the Blind; pace: slow; volume: quiet.
*Note:* Narrator plain and starlit; a beat before 'and is answered'. Maeca just above a breath, naming neighbours by their voices. Narrator plain: the narrator never shows a feeling.

```
[quietly] She goes out by the east gate without a lamp, and you follow her along the Old Road past the wreck, by starlight and the white of the frost. She walks barefoot on ground that would cut you through your boots, and doesn't make a sound. Once she stops, and you stop, and somewhere off in the Hollow a wolf calls and is answered.
```
Subtitle: She goes out by the east gate without a lamp, and you follow her along the Old Road past the wreck, by starlight and the white of the frost. She walks barefoot on ground that would cut you through your boots, and doesn't make a sound. Once she stops, and you stop, and somewhere off in the Hollow a wolf calls and is answered.

### 123. `dlg.maeca.blind_walk.0.p2.wav`

*Where:* dialogue.json maeca/blind_walk#0; part 3 of 3: narrator: She goes out by the east gate without a lamp, and you follow her along the Old Road past t… / maeca: Him. And the bitch with the white foot. / **narrator: She walks on.**
*Played:* hushed, attentive; doing: the walk to the Blind; pace: slow; volume: quiet.
*Note:* Narrator plain and starlit; a beat before 'and is answered'. Maeca just above a breath, naming neighbours by their voices. Narrator plain: the narrator never shows a feeling.

```
[quietly] She walks on.
```
Subtitle: She walks on.

### 124. `dlg.maeca.blind_walk.1.wav`

*Where:* dialogue.json maeca/blind_walk#1
*Played:* plain; doing: she lets you lead; pace: slow; volume: quiet.
*Note:* Narrator plain: the narrator never shows a feeling. The gift is the fact itself; don't lean on it.

```
[quietly] The Old Road, the wreck, the frost… You know the way now, and she lets you walk in front… which she has never done.
```
Subtitle: The Old Road, the wreck, the frost. You know the way now, and she lets you walk in front, which she has never done.

### 125. `dlg.maeca.blind_fire.0.wav`

*Where:* dialogue.json maeca/blind_fire#0
*Played:* still, charged; doing: the Blind; pace: slow; volume: quiet.
*Note:* One action at a time. The look across the fire held.

```
[quietly] The Hunters' Blind is a lean-to of hides against a fallen oak, with a fire the size of a hat. She feeds it one stick at a time. She doesn't talk. After a while she takes the crossbow off her back, and checks it, and lays it down by her right hand, and turns and looks at you across the fire as if you were a track she has been following for days.
```
Subtitle: The Hunters' Blind is a lean-to of hides against a fallen oak, with a fire the size of a hat. She feeds it one stick at a time. She doesn't talk. After a while she takes the crossbow off her back, and checks it, and lays it down by her right hand, and turns and looks at you across the fire as if you were a track she has been following for days.

### 126. `dlg.maeca.blind_ask.1.wav`

*Where:* dialogue.json maeca/blind_ask#1
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She holds out her hand. That's all.
```
Subtitle: She holds out her hand. That's all.

### 127. `dlg.maeca.blind_leave.0.p0.wav`

*Where:* dialogue.json maeca/blind_leave#0; part 1 of 2: **narrator: She nods at the fire.** / maeca: Mind the frost on the Old Road. It's worse by the wreck.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She nods at the fire.
```
Subtitle: She nods at the fire.

### 128. `dlg.maeca.watch_only.0.wav`

*Where:* dialogue.json maeca/watch_only#0
*Played:* tender, quiet; doing: a night keeping watch; pace: slow; volume: quiet.
*Note:* Calm. The frost line a quiet image of closeness.

```
[quietly] You keep the fire. She keeps the dark. Some time after midnight she comes in from the edge of the light and sits down with her back against yours, and you can feel her breathing, slow, and listening. You sleep like that, sitting up. In the morning the frost is on both your shoulders and not between them.
```
Subtitle: You keep the fire. She keeps the dark. Some time after midnight she comes in from the edge of the light and sits down with her back against yours, and you can feel her breathing, slow, and listening. You sleep like that, sitting up. In the morning the frost is on both your shoulders and not between them.

### 129. `dlg.maeca.watch_morning.0.p1.wav`

*Where:* dialogue.json maeca/watch_morning#0; part 2 of 3: maeca: You kept quiet. / **narrator: She stands, and stretches, and looks at the Hollow, not you.** / maeca: Most can't.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She stands, and stretches, and looks at the Hollow, not you.
```
Subtitle: She stands, and stretches, and looks at the Hollow, not you.

### 130. `dlg.maeca.blind_dark.0.wav`

*Where:* dialogue.json maeca/blind_dark#0
*Played:* level, nearly funny; doing: you're cold; pace: slow; volume: hushed.
*Note:* The inversion (your skin colder than her feet) is nearly funny: straight and level, don't darken it. The last sentence hangs, not drops: the player's choice follows.

```
[whispers] Afterwards, in the dark under the hides, she puts her feet against your legs… and flinches… you're colder than they are. She starts to take them back—
```
Subtitle: Afterwards, in the dark under the hides, she puts her feet against your legs, and flinches: you're colder than they are. She starts to take them back.

### 131. `dlg.maeca.blind_dark.1.p0.wav`

*Where:* dialogue.json maeca/blind_dark#1; part 1 of 6: **narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis…** / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* hushed, careful; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[whispers] Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow. Outside, in the frost, you hear them come: soft feet, a long way round, and then a sigh, and then another. The Pack, lying down round the Blind in the dark. She lifts her head.
```
Subtitle: Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow. Outside, in the frost, you hear them come: soft feet, a long way round, and then a sigh, and then another. The Pack, lying down round the Blind in the dark. She lifts her head.

### 132. `dlg.maeca.blind_dark.1.p2.wav`

*Where:* dialogue.json maeca/blind_dark#1; part 3 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / **narrator: She lies back down, her ear where it was.** / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* hushed, careful; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[whispers] She lies back down, her ear where it was.
```
Subtitle: She lies back down, her ear where it was.

### 133. `dlg.maeca.blind_dark.1.p4.wav`

*Where:* dialogue.json maeca/blind_dark#1; part 5 of 6: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: They don't do that. Not for me. Not for anyone. / narrator: She lies back down, her ear where it was. / maeca: You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk a… / **narrator: Against your chest you feel her lips move, without a sound.** / maeca: What were you?
*Played:* hushed, careful; doing: the Pack lies down round you; she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences; it is slow, and at night it can stop for a count of seven
*Note:* Narrator plain, the Pack's arrival a held breath. Maeca flat on 'They don't do that', because she can't afford the wonder. 'What were you?' careful, not curious: no stress on 'were', even weight, asked to the dark, after a real count of about three seconds.

```
[whispers] Against your chest you feel her lips move, without a sound.
```
Subtitle: Against your chest you feel her lips move, without a sound.

### 134. `dlg.maeca.blind_dark.2.p0.wav`

*Where:* dialogue.json maeca/blind_dark#2; part 1 of 4: **narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis…** / maeca: You walk quiet. You never talk about before. / narrator: Against your chest you feel her lips move, without a sound. / maeca: What were you?
*Played:* hushed, careful; doing: she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences
*Note:* As blind_dark.1 without the Pack. 'What were you?' careful, no stress on 'were', after a real count of about three seconds.

```
[whispers] Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow.
```
Subtitle: Later, with the fire down, she lies with her head on your chest, listening the way she listens to the Hollow.

### 135. `dlg.maeca.blind_dark.2.p2.wav`

*Where:* dialogue.json maeca/blind_dark#2; part 3 of 4: narrator: Later, with the fire down, she lies with her head on your chest, listening the way she lis… / maeca: You walk quiet. You never talk about before. / **narrator: Against your chest you feel her lips move, without a sound.** / maeca: What were you?
*Played:* hushed, careful; doing: she asks what you were; pace: slow; volume: hushed.
*Hides:* she is counting your heart between her sentences
*Note:* As blind_dark.1 without the Pack. 'What were you?' careful, no stress on 'were', after a real count of about three seconds.

```
[whispers] Against your chest you feel her lips move, without a sound.
```
Subtitle: Against your chest you feel her lips move, without a sound.

### 136. `dlg.maeca.blind_dark.3.wav`

*Where:* dialogue.json maeca/blind_dark#3
*Played:* still; doing: quiet; pace: slow; volume: hushed.

```
[whispers] The fire's down to embers. Far off, the Pack is quiet.
```
Subtitle: The fire's down to embers. Far off, the Pack is quiet.

### 137. `dlg.maeca.blind2_feet.0.wav`

*Where:* dialogue.json maeca/blind2_feet#0
*Played:* tender, sombre; doing: her scarred feet; pace: slow; volume: hushed.
*Note:* The scars described gently; the stillness at the end weighty.

```
[whispers] You take one in your hands. The sole is hard as boot leather, and scarred: old white lines across the ball of the foot, a ridge along the heel where something cut it to the bone a long time ago and it healed badly in the cold. She lets you hold it. She lets you hold the other. She lies very still, the way she lay still when the Pack called, and doesn't say anything for a long time. Into the dark, very low: "Your hands are colder than my feet." A pause. "Hold them anyway. ...Nobody's held those."
```
Subtitle: You take one in your hands. The sole is hard as boot leather, and scarred: old white lines across the ball of the foot, a ridge along the heel where something cut it to the bone a long time ago and it healed badly in the cold. She lets you hold it. She lets you hold the other. She lies very still, the way she lay still when the Pack called, and doesn't say anything for a long time. Into the dark, very low: "Your hands are colder than my feet." A pause. "Hold them anyway. ...Nobody's held those."

### 138. `dlg.maeca.blind2_let.0.wav`

*Where:* dialogue.json maeca/blind2_let#0
*Played:* tender, wry; doing: she curls up; pace: slow; volume: hushed.
*Note:* A small smile at the dog image.

```
[whispers] She tucks them up under her instead, the way a dog curls its nose under its tail, and goes to sleep. In the night, half awake, you feel her put them back against you, slowly, as if she was trying it out.
```
Subtitle: She tucks them up under her instead, the way a dog curls its nose under its tail, and goes to sleep. In the night, half awake, you feel her put them back against you, slowly, as if she was trying it out.

### 139. `dlg.maeca.told_true.0.p1.wav`

*Where:* dialogue.json maeca/told_true#0; part 2 of 3: maeca: Thought so. You put your feet down like you're asking the ground first. / **narrator: She almost smiles.** / maeca: I'd have liked you, then. Probably would have shot you for poaching.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She almost smiles.
```
Subtitle: She almost smiles.

### 140. `dlg.maeca.told_true.1.p1.wav`

*Where:* dialogue.json maeca/told_true#1; part 2 of 3: maeca: Letters. / **narrator: She thinks about it.** / maeca: Tracks for people who sit still. ...Read me something, one day. Not now.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She thinks about it.
```
Subtitle: She thinks about it.

### 141. `dlg.maeca.told_true.3.p1.wav`

*Where:* dialogue.json maeca/told_true#3; part 2 of 3: maeca: Lamps. Nobody coming. / **narrator: A long breath.** / maeca: I held a cave mouth three days for nobody coming. We'd have got on.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A long breath.
```
Subtitle: A long breath.

### 142. `dlg.maeca.told_little.0.p0.wav`

*Where:* dialogue.json maeca/told_little#0; part 1 of 4: **narrator: She doesn't push.** / maeca: All right. / narrator: And it is. / maeca: ...Keep it, then. I keep mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't push.
```
Subtitle: She doesn't push.

### 143. `dlg.maeca.told_little.0.p2.wav`

*Where:* dialogue.json maeca/told_little#0; part 3 of 4: narrator: She doesn't push. / maeca: All right. / **narrator: And it is.** / maeca: ...Keep it, then. I keep mine.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] And it is.
```
Subtitle: And it is.

### 144. `dlg.maeca.blind3_morning.0.p0.wav`

*Where:* dialogue.json maeca/blind3_morning#0; part 1 of 6: **narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on…** / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on your chest. Her face is very still.
```
Subtitle: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on your chest. Her face is very still.

### 145. `dlg.maeca.blind3_morning.0.p2.wav`

*Where:* dialogue.json maeca/blind3_morning#0; part 3 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / **narrator: She doesn't lift her head.** / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the… / maeca: Go on. Holloway'll count us.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't lift her head.
```
Subtitle: She doesn't lift her head.

### 146. `dlg.maeca.blind3_morning.0.p4.wav`

*Where:* dialogue.json maeca/blind3_morning#0; part 5 of 6: narrator: Grey light. She's awake before you, as always, but she hasn't got up. Her head is still on… / maeca: Your heart's going like a hare's. / narrator: She doesn't lift her head. / maeca: All night it was a bear's in January. I counted between. ...I've lain with my ear to a lot… / **narrator: She gets up, then, and goes out barefoot into the frost, and stands there listening to the…** / maeca: Go on. Holloway'll count us.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She gets up, then, and goes out barefoot into the frost, and stands there listening to the wood with her back to you.
```
Subtitle: She gets up, then, and goes out barefoot into the frost, and stands there listening to the wood with her back to you.

### 147. `dlg.maeca.blind3_m_no.0.p1.wav`

*Where:* dialogue.json maeca/blind3_m_no#0; part 2 of 3: maeca: No. / **narrator: Not unkind.** / maeca: Don't make it a story. Not yet.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Not unkind.
```
Subtitle: Not unkind.

### 148. `dlg.maeca.say_sella.0.p1.wav`

*Where:* dialogue.json maeca/say_sella#0; part 2 of 3: maeca: You go up Sella's stairs. / **narrator: She doesn't look up from her cup.** / maeca: Not for money, now. Rook talks. ...Is it her, or me, or both? I don't mind which. I mind n…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't look up from her cup.
```
Subtitle: She doesn't look up from her cup.

### 149. `dlg.maeca.say_sella.1.p1.wav`

*Where:* dialogue.json maeca/say_sella#1; part 2 of 3: maeca: You go up Sella's stairs. Rook talks. / **narrator: A shrug.** / maeca: She's honest about what she charges. That's more than most.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A shrug.
```
Subtitle: A shrug.

### 150. `dlg.maeca.say_sella_both.0.p0.wav`

*Where:* dialogue.json maeca/say_sella_both#0; part 1 of 2: **narrator: A nod.** / maeca: Good. Now I know.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A nod.
```
Subtitle: A nod.

### 151. `dlg.maeca.say_sella_you.0.p0.wav`

*Where:* dialogue.json maeca/say_sella_you#0; part 1 of 2: **narrator: She looks at you, long, the way she looks at a track that might be lying.** / maeca: We'll see.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you, long, the way she looks at a track that might be lying.
```
Subtitle: She looks at you, long, the way she looks at a track that might be lying.

## Conversations: Harlan

### 152. `dlg.harlan.first.0.p1.wav`

*Where:* dialogue.json harlan/first#0; part 2 of 3: harlan: You. Jory says it was you at the cage with the bar in your hands, and he's told it four ti… / **narrator: He takes your hand in both of his.** / harlan: Harlan Coyle, of the Coyle Company. Any other day I'd have said that first.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes your hand in both of his.
```
Subtitle: He takes your hand in both of his.

### 153. `dlg.harlan.first.1.p0.wav`

*Where:* dialogue.json harlan/first#1; part 1 of 2: **narrator: The shutters are half closed, and he doesn't get up.** / harlan: Harlan Coyle. You'll have heard. Everyone's heard. ...Buy something, or don't.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The shutters are half closed, and he doesn't get up.
```
Subtitle: The shutters are half closed, and he doesn't get up.

### 154. `dlg.harlan.first.2.p1.wav`

*Where:* dialogue.json harlan/first#2; part 2 of 3: harlan: That's my seal. That's— / **narrator: He's round the counter before you can blink, hands out, and then he doesn't touch it.** / harlan: Where did you get that? Where was it? Where's the boy that was driving it?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's round the counter before you can blink, hands out, and then he doesn't touch it.
```
Subtitle: He's round the counter before you can blink, hands out, and then he doesn't touch it.

### 155. `dlg.harlan.hub.2.p0.wav`

*Where:* dialogue.json harlan/hub#2; part 1 of 2: **narrator: He doesn't get up.** / harlan: Three days of watching that road. I stopped. Somebody has to keep the stock, I told myself…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't get up.
```
Subtitle: He doesn't get up.

### 156. `dlg.harlan.hub.3.p0.wav`

*Where:* dialogue.json harlan/hub#3; part 1 of 2: **narrator: He keeps his eyes on the bend in the Old Road while he talks.** / harlan: I keep thinking the lead wagon'll come round there, Jory shouting that he got lost. Any wo…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He keeps his eyes on the bend in the Old Road while he talks.
```
Subtitle: He keeps his eyes on the bend in the Old Road while he talks.

### 157. `dlg.harlan.betrayed.0.p1.wav`

*Where:* dialogue.json harlan/betrayed#0; part 2 of 3: harlan: You brought him home. Then you sold my strongbox to a fence for the price of a good horse. / **narrator: He counts a hundred onto the counter, coin by coin, and doesn't push it towards you.** / harlan: For the boy. I said I would. Take it, and get away from my stall.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He counts a hundred onto the counter, coin by coin, and doesn't push it towards you.
```
Subtitle: He counts a hundred onto the counter, coin by coin, and doesn't push it towards you.

### 158. `dlg.harlan.jory_now.0.p1.wav`

*Where:* dialogue.json harlan/jory_now#0; part 2 of 3: harlan: He asked me what was in the crates. I told him salt. / **narrator: He looks at his hands.** / harlan: He didn't believe me. First time in his life. ...That's the worst of it, friend. He always…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at his hands.
```
Subtitle: He looks at his hands.

### 159. `dlg.harlan.roost.0.p0.wav`

*Where:* dialogue.json harlan/roost#0; part 1 of 6: **narrator: He sits down, which you haven't seen him do.** / harlan: Three. In cages. / narrator: He's counting something on his fingers, and he stops. / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / narrator: He stops that too. / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He sits down, which you haven't seen him do.
```
Subtitle: He sits down, which you haven't seen him do.

### 160. `dlg.harlan.roost.0.p2.wav`

*Where:* dialogue.json harlan/roost#0; part 3 of 6: narrator: He sits down, which you haven't seen him do. / harlan: Three. In cages. / **narrator: He's counting something on his fingers, and he stops.** / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / narrator: He stops that too. / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's counting something on his fingers, and he stops.
```
Subtitle: He's counting something on his fingers, and he stops.

### 161. `dlg.harlan.roost.0.p4.wav`

*Where:* dialogue.json harlan/roost#0; part 5 of 6: narrator: He sits down, which you haven't seen him do. / harlan: Three. In cages. / narrator: He's counting something on his fingers, and he stops. / harlan: Is one of them young? Fair, freckled, a mouth on him that'll get him— / **narrator: He stops that too.** / harlan: Get him out. Whatever it costs. Whatever they want, I'll pay it twice.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He stops that too.
```
Subtitle: He stops that too.

### 162. `dlg.harlan.ledger_early.0.p0.wav`

*Where:* dialogue.json harlan/ledger_early#0; part 1 of 4: **narrator: He reads, and his finger stops on a line.** / harlan: That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's… / narrator: He looks up. / harlan: For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holl…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He reads, and his finger stops on a line.
```
Subtitle: He reads, and his finger stops on a line.

### 163. `dlg.harlan.ledger_early.0.p2.wav`

*Where:* dialogue.json harlan/ledger_early#0; part 3 of 4: narrator: He reads, and his finger stops on a line. / harlan: That's the night. That's the night Jory's wagons went. Forty to "R." Ten to Jessop: that's… / **narrator: He looks up.** / harlan: For what road? Who's "R."? ...Find out who "R." is, friend. Please. Then take that to Holl…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks up.
```
Subtitle: He looks up.

### 164. `dlg.harlan.crates.0.p0.wav`

*Where:* dialogue.json harlan/crates#0; part 1 of 4: **narrator: His face does what it does whenever anyone says those two letters.** / harlan: ...Are they. With the bandit. / narrator: He's already reaching for paper. / harlan: Thank you, friend. Leave that with me. Paid for is paid for.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] His face does what it does whenever anyone says those two letters.
```
Subtitle: His face does what it does whenever anyone says those two letters.

### 165. `dlg.harlan.crates.0.p2.wav`

*Where:* dialogue.json harlan/crates#0; part 3 of 4: narrator: His face does what it does whenever anyone says those two letters. / harlan: ...Are they. With the bandit. / **narrator: He's already reaching for paper.** / harlan: Thank you, friend. Leave that with me. Paid for is paid for.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's already reaching for paper.
```
Subtitle: He's already reaching for paper.

### 166. `dlg.harlan.be_dig.0.p0.wav`

*Where:* dialogue.json harlan/be_dig#0; part 1 of 2: **narrator: He takes a long time to answer.** / harlan: I sell salt to people who salt things. I sell iron to people who hit things. I don't ask t…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He takes a long time to answer.
```
Subtitle: He takes a long time to answer.

### 167. `dlg.harlan.cb_jory_knows.0.p0.wav`

*Where:* dialogue.json harlan/cb_jory_knows#0; part 1 of 2: **narrator: He doesn't say good morning.** / harlan: He knows. You told him. ...I'd have told him myself. One day. When it didn't matter any mo…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't say good morning.
```
Subtitle: He doesn't say good morning.

## Conversations: Jory

### 168. `dlg.jory.hub.0.p1.wav`

*Where:* dialogue.json jory/hub#0; part 2 of 3: jory: I'm all right. / **narrator: He isn't.** / jory: Uncle's counting crates that aren't there.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He isn't.
```
Subtitle: He isn't.

### 169. `dlg.jory.truth.0.p0.wav`

*Where:* dialogue.json jory/truth#0; part 1 of 4: **narrator: He laughs, once, as if you've told him a joke he didn't get.** / jory: Every rut in Thornhollow. I took them over every rut. / narrator: He stops laughing. / jory: ...Uncle knew. Didn't he. He told me salt.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He laughs, once, as if you've told him a joke he didn't get.
```
Subtitle: He laughs, once, as if you've told him a joke he didn't get.

### 170. `dlg.jory.truth.0.p2.wav`

*Where:* dialogue.json jory/truth#0; part 3 of 4: narrator: He laughs, once, as if you've told him a joke he didn't get. / jory: Every rut in Thornhollow. I took them over every rut. / **narrator: He stops laughing.** / jory: ...Uncle knew. Didn't he. He told me salt.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He stops laughing.
```
Subtitle: He stops laughing.

### 171. `dlg.jory.truth_knew.0.p0.wav`

*Where:* dialogue.json jory/truth_knew#0; part 1 of 2: **narrator: He nods. He keeps nodding.** / jory: Right. Right. ...Thank you. I think. I'll know when I've stopped feeling sick.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He nods. He keeps nodding.
```
Subtitle: He nods. He keeps nodding.

### 172. `dlg.jory.truth_ask.0.p1.wav`

*Where:* dialogue.json jory/truth_ask#0; part 2 of 3: jory: I will. / **narrator: He doesn't move.** / jory: I will.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't move.
```
Subtitle: He doesn't move.

### 173. `dlg.jory.salt.0.p0.wav`

*Where:* dialogue.json jory/salt#0; part 1 of 2: **narrator: He nods, and it goes out of his face at once, the way it goes out of a child's.** / jory: Salt. Right. ...Thanks.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He nods, and it goes out of his face at once, the way it goes out of a child's.
```
Subtitle: He nods, and it goes out of his face at once, the way it goes out of a child's.

## Conversations: Sella

### 174. `dlg.sella.night.1.wav`

*Where:* dialogue.json sella/night#1
*Played:* warm, wry, intimate; doing: a night with Sella; pace: slow; volume: quiet.
*Note:* Fond and discreet. A smile at 'laughs at the last one' and 'nobody's business but yours'. 'She is dressed, and counting.' dry.

```
[quietly] The water's gone cool by the time either of you notices, and she drags the quilt off the bed and onto the floor rather than walk three steps. She is slower tonight. She keeps a hand flat on you the whole time, the way you'd keep a hand on a horse you'd been told was skittish, and when you look at her she says, "Don't," and kisses you so you can't. After, you lie on the floor of the blue room with the lamp turned down to a bead, and she doesn't get up to dress, and you don't ask why. You wake with her hair across your chest and the sun already up. She is dressed, and counting, and she counts it twice.
```
Subtitle: The water's gone cool by the time either of you notices, and she drags the quilt off the bed and onto the floor rather than walk three steps. She is slower tonight. She keeps a hand flat on you the whole time, the way you'd keep a hand on a horse you'd been told was skittish, and when you look at her she says, "Don't," and kisses you so you can't. After, you lie on the floor of the blue room with the lamp turned down to a bead, and she doesn't get up to dress, and you don't ask why. You wake with her hair across your chest and the sun already up. She is dressed, and counting, and she counts it twice.

### 175. `dlg.sella.night.2.wav`

*Where:* dialogue.json sella/night#2
*Played:* warm, wry, intimate; doing: a night with Sella; pace: slow; volume: quiet.
*Note:* Fond and discreet; the slopped water funny.

```
[quietly] She laughs when the water slops over the side, and again when you try to mop it with her shift. Then the lamp is down to a bead, and the blue room is a small warm place with the whole night outside it. She talks the way she always talks, low against your ear, telling you exactly what she means to do next and then doing it, and she's good at it and likes it and makes no secret of either. But there are gaps, tonight. Places where she stops mid-sentence and doesn't finish, and you don't need her to. You wake with her hair across your chest and the sun already up. She is dressed, and counting.
```
Subtitle: She laughs when the water slops over the side, and again when you try to mop it with her shift. Then the lamp is down to a bead, and the blue room is a small warm place with the whole night outside it. She talks the way she always talks, low against your ear, telling you exactly what she means to do next and then doing it, and she's good at it and likes it and makes no secret of either. But there are gaps, tonight. Places where she stops mid-sentence and doesn't finish, and you don't need her to. You wake with her hair across your chest and the sun already up. She is dressed, and counting.

### 176. `dlg.sella.night.3.wav`

*Where:* dialogue.json sella/night#3
*Played:* warm, wry, intimate; doing: a night with Sella; pace: slow; volume: quiet.
*Note:* Fond and discreet; 'and funny' with a smile.

```
[quietly] The blue room smells of lavender and lamp oil, and the bath is warm, at least to begin with. After that the door is shut, and what happens behind it is slow, and warm, and funny, and nobody's business but yours: her hair coming down, her mouth at your ear, her hands everywhere they're welcome and nowhere they're not. For a few hours the road and the dead on it are a long way off. You wake with her hair across your chest and the sun already up. She is dressed, and counting.
```
Subtitle: The blue room smells of lavender and lamp oil, and the bath is warm, at least to begin with. After that the door is shut, and what happens behind it is slow, and warm, and funny, and nobody's business but yours: her hair coming down, her mouth at your ear, her hands everywhere they're welcome and nowhere they're not. For a few hours the road and the dead on it are a long way off. You wake with her hair across your chest and the sun already up. She is dressed, and counting.

### 177. `dlg.sella.morning.0.p0.wav`

*Where:* dialogue.json sella/morning#0; part 1 of 2: **narrator: She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone.** / sella: You were cold as the river all night, love. Like sleeping next to a stone. And now look at…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone.
```
Subtitle: She's sitting on the edge of the bed, frowning, with her palm flat on your breastbone.

### 178. `dlg.sella.free_night.1.p0.wav`

*Where:* dialogue.json sella/free_night#1; part 1 of 3: **narrator: She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undre…** / sella: You told me anyway, / narrator: and nothing else, and then she sleeps.
*Played:* tender, quiet; doing: a night Sella gives; pace: slow; volume: hushed.
*Note:* The narrator's, hushed and unhurried: the one night that isn't work, so no patter. Narrator plain: the narrator never shows a feeling. Her four words are hers, said into your shoulder.

```
[whispers] She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undresses you as if she's never done it before, which is absurd, and she knows it's absurd, and halfway through she laughs into your neck and can't stop. Then she does stop, and the laugh goes somewhere else. She's slower than on her working nights, and less sure, and once she stops altogether with her forehead against yours and just breathes, and you wait, and she goes on. The lamp burns down on its own. Nobody turns it. In the dark, much later, she says into your shoulder,
```
Subtitle: She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undresses you as if she's never done it before, which is absurd, and she knows it's absurd, and halfway through she laughs into your neck and can't stop. Then she does stop, and the laugh goes somewhere else. She's slower than on her working nights, and less sure, and once she stops altogether with her forehead against yours and just breathes, and you wait, and she goes on. The lamp burns down on its own. Nobody turns it. In the dark, much later, she says into your shoulder,

### 179. `dlg.sella.free_night.1.p2.wav`

*Where:* dialogue.json sella/free_night#1; part 3 of 3: narrator: She doesn't talk the way she talks for money. She doesn't talk at all, at first. She undre… / sella: You told me anyway, / **narrator: and nothing else, and then she sleeps.**
*Played:* tender, quiet; doing: a night Sella gives; pace: slow; volume: hushed.
*Note:* The narrator's, hushed and unhurried: the one night that isn't work, so no patter. Narrator plain: the narrator never shows a feeling. Her four words are hers, said into your shoulder.

```
[whispers] and nothing else, and then she sleeps.
```
Subtitle: and nothing else, and then she sleeps.

### 180. `dlg.sella.free_night.2.wav`

*Where:* dialogue.json sella/free_night#2
*Played:* tender, quiet; doing: the free night; pace: slow; volume: hushed.
*Note:* Slower and softer; the look a held breath.

```
[whispers] The blue room, and the lamp, and the bolt, which she shot herself, which she has never done. She doesn't talk the way she talks for money. For a while neither of you talks at all. She is slower than you have known her, and less sure, and there is a moment when she stops with her hands on your face and just looks, as if she is learning it, and doesn't make a joke of it. Later she lies awake, and you can feel her deciding something, and then she sleeps.
```
Subtitle: The blue room, and the lamp, and the bolt, which she shot herself, which she has never done. She doesn't talk the way she talks for money. For a while neither of you talks at all. She is slower than you have known her, and less sure, and there is a moment when she stops with her hands on your face and just looks, as if she is learning it, and doesn't make a joke of it. Later she lies awake, and you can feel her deciding something, and then she sleeps.

### 181. `dlg.sella.free_morning.0.p0.wav`

*Where:* dialogue.json sella/free_morning#0; part 1 of 2: **narrator: She's still there when you wake, which she never is.** / sella: Don't tell Rook; she'll want a third of nothing, on principle. ...And don't tell me anythi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's still there when you wake, which she never is.
```
Subtitle: She's still there when you wake, which she never is.

### 182. `dlg.sella.past.0.p0.wav`

*Where:* dialogue.json sella/past#0; part 1 of 4: **narrator: She goes still when you start. You know who buys what's said up here; she knows you know. …** / sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. … / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.

### 183. `dlg.sella.past.0.p2.wav`

*Where:* dialogue.json sella/past#0; part 3 of 4: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. … / **narrator: She doesn't say anything else for a while. Then:** / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't say anything else for a while. Then:
```
Subtitle: She doesn't say anything else for a while. Then:

### 184. `dlg.sella.past.1.p0.wav`

*Where:* dialogue.json sella/past#1; part 1 of 4: **narrator: She goes still when you start. You know who buys what's said up here; she knows you know. …** / sella: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.

### 185. `dlg.sella.past.1.p2.wav`

*Where:* dialogue.json sella/past#1; part 3 of 4: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with… / **narrator: She doesn't say anything else for a while. Then:** / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't say anything else for a while. Then:
```
Subtitle: She doesn't say anything else for a while. Then:

### 186. `dlg.sella.past.2.p0.wav`

*Where:* dialogue.json sella/past#2; part 1 of 6: **narrator: She goes still when you start. You know who buys what's said up here; she knows you know. …** / sella: Worse company than the Kerchiefs, and you walked away from it. / narrator: She laughs, low. / sella: Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactl… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.

### 187. `dlg.sella.past.2.p2.wav`

*Where:* dialogue.json sella/past#2; part 3 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Worse company than the Kerchiefs, and you walked away from it. / **narrator: She laughs, low.** / sella: Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactl… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs, low.
```
Subtitle: She laughs, low.

### 188. `dlg.sella.past.2.p4.wav`

*Where:* dialogue.json sella/past#2; part 5 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Worse company than the Kerchiefs, and you walked away from it. / narrator: She laughs, low. / sella: Takes one to know one. Don't tell Rook. ...You know where that goes, love. You know exactl… / **narrator: She doesn't say anything else for a while. Then:** / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't say anything else for a while. Then:
```
Subtitle: She doesn't say anything else for a while. Then:

### 189. `dlg.sella.past.3.p0.wav`

*Where:* dialogue.json sella/past#3; part 1 of 6: **narrator: She goes still when you start. You know who buys what's said up here; she knows you know. …** / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / narrator: She's quiet a moment. / sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: She goes still when you start. You know who buys what's said up here; she knows you know. You tell her anyway. She listens properly, chin on her fist, the way she does everything.

### 190. `dlg.sella.past.3.p2.wav`

*Where:* dialogue.json sella/past#3; part 3 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / **narrator: She's quiet a moment.** / sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.… / narrator: She doesn't say anything else for a while. Then: / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's quiet a moment.
```
Subtitle: She's quiet a moment.

### 191. `dlg.sella.past.3.p4.wav`

*Where:* dialogue.json sella/past#3; part 5 of 6: narrator: She goes still when you start. You know who buys what's said up here; she knows you know. … / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / narrator: She's quiet a moment. / sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.… / **narrator: She doesn't say anything else for a while. Then:** / sella: Go on. Out. Before I start charging you for the sentiment.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't say anything else for a while. Then:
```
Subtitle: She doesn't say anything else for a while. Then:

### 192. `dlg.sella.past.4.p0.wav`

*Where:* dialogue.json sella/past#4; part 1 of 2: **narrator: You tell her. She listens properly, chin on her fist, the way she does everything.** / sella: A hunter. Out of these woods, with a bow too big for you, I'll bet, and mud to the knees. …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] You tell her. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: You tell her. She listens properly, chin on her fist, the way she does everything.

### 193. `dlg.sella.past.5.p0.wav`

*Where:* dialogue.json sella/past#5; part 1 of 2: **narrator: You tell her. She listens properly, chin on her fist, the way she does everything.** / sella: A cloister rat. Four years in a cellar reading dead men's letters, and you walked out with…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] You tell her. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: You tell her. She listens properly, chin on her fist, the way she does everything.

### 194. `dlg.sella.past.6.p0.wav`

*Where:* dialogue.json sella/past#6; part 1 of 4: **narrator: You tell her. She listens properly, chin on her fist, the way she does everything.** / sella: Worse company than the Kerchiefs, and you walked away from it. / narrator: She laughs, low. / sella: Takes one to know one. Don't tell Rook.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] You tell her. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: You tell her. She listens properly, chin on her fist, the way she does everything.

### 195. `dlg.sella.past.6.p2.wav`

*Where:* dialogue.json sella/past#6; part 3 of 4: narrator: You tell her. She listens properly, chin on her fist, the way she does everything. / sella: Worse company than the Kerchiefs, and you walked away from it. / **narrator: She laughs, low.** / sella: Takes one to know one. Don't tell Rook.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs, low.
```
Subtitle: She laughs, low.

### 196. `dlg.sella.past.7.p0.wav`

*Where:* dialogue.json sella/past#7; part 1 of 4: **narrator: You tell her. She listens properly, chin on her fist, the way she does everything.** / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / narrator: She's quiet a moment. / sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] You tell her. She listens properly, chin on her fist, the way she does everything.
```
Subtitle: You tell her. She listens properly, chin on her fist, the way she does everything.

### 197. `dlg.sella.past.7.p2.wav`

*Where:* dialogue.json sella/past#7; part 3 of 4: narrator: You tell her. She listens properly, chin on her fist, the way she does everything. / sella: Chapel lamps, with nobody to see them but you, and you lit them anyway. / **narrator: She's quiet a moment.** / sella: That's the saddest thing anyone's told me up here, love, and they tell me some sad things.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's quiet a moment.
```
Subtitle: She's quiet a moment.

### 198. `dlg.sella.sleeptalk.0.p1.wav`

*Where:* dialogue.json sella/sleeptalk#0; part 2 of 3: sella: You said a name. Over and over, like you'd got hold of it in the dark and didn't want to l… / **narrator: She shrugs one shoulder.** / sella: Didn't catch it. I don't think you did either.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She shrugs one shoulder.
```
Subtitle: She shrugs one shoulder.

### 199. `dlg.sella.stairs.0.wav`

*Where:* dialogue.json sella/stairs#0
*Played:* warm, wry; doing: a regular now; pace: measured; volume: quiet.
*Note:* The check on the fourth step a small tenderness.

```
[quietly] She doesn't take your hand any more; she takes your sleeve, the way you'd take a regular's. Rook's stairs creak on the fourth step and the ninth. On the fourth she looks back, to check you're stepping over it. You are.
```
Subtitle: She doesn't take your hand any more; she takes your sleeve, the way you'd take a regular's. Rook's stairs creak on the fourth step and the ninth. On the fourth she looks back, to check you're stepping over it. You are.

### 200. `dlg.sella.stairs.1.wav`

*Where:* dialogue.json sella/stairs#1
*Played:* warm, plain; doing: up the stairs; pace: measured; volume: quiet.

```
[quietly] She takes the coins first and your hand second, and leads you up Rook's narrow stairs. They creak on the fourth step and the ninth, and she steps over both without looking.
```
Subtitle: She takes the coins first and your hand second, and leads you up Rook's narrow stairs. They creak on the fourth step and the ninth, and she steps over both without looking.

### 201. `dlg.sella.stairs.2.wav`

*Where:* dialogue.json sella/stairs#2
*Played:* dry, warm; doing: you're learning; pace: brisk; volume: quiet.

```
[quietly] Coins, then your hand, then the stairs. Fourth step, ninth step. You're learning.
```
Subtitle: Coins, then your hand, then the stairs. Fourth step, ninth step. You're learning.

### 202. `dlg.sella.stairs_room.0.wav`

*Where:* dialogue.json sella/stairs_room#0
*Played:* warm, amused; doing: the blue room; pace: measured; volume: quiet.
*Note:* Her quoted line warm and wry if read in her voice; the narrator smiles at it.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck. "All that steel, and under it, look. A person."
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck. "All that steel, and under it, look. A person."

### 203. `dlg.sella.stairs_room.1.wav`

*Where:* dialogue.json sella/stairs_room#1
*Played:* warm, amused; doing: the blue room; pace: measured; volume: quiet.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. She takes your hands, one and then the other, and turns them over, and looks at the knuckles. "Gently, upstairs. I mean it. I like this jug."
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. She takes your hands, one and then the other, and turns them over, and looks at the knuckles. "Gently, upstairs. I mean it. I like this jug."

### 204. `dlg.sella.stairs_room.2.wav`

*Where:* dialogue.json sella/stairs_room#2
*Played:* warm, curious; doing: the blue room; pace: measured; volume: quiet.
*Note:* A small chill in 'cellar floor'.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower. "Your hands are hot and the rest of you's a cellar floor. Pick one, love."
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower. "Your hands are hot and the rest of you's a cellar floor. Pick one, love."

### 205. `dlg.sella.stairs_room.3.wav`

*Where:* dialogue.json sella/stairs_room#3
*Played:* warm, playful; doing: the blue room; pace: measured; volume: quiet.

```
[quietly] The blue room again: the quilt, the jug, the bath, her, all of it blue. She comes round behind you to start on the laces, and says into your ear, "There. Now you know what it's like," and you jump. She's delighted.
```
Subtitle: The blue room again: the quilt, the jug, the bath, her, all of it blue. She comes round behind you to start on the laces, and says into your ear, "There. Now you know what it's like," and you jump. She's delighted.

### 206. `dlg.sella.stairs_room.4.wav`

*Where:* dialogue.json sella/stairs_room#4
*Played:* warm, wry; doing: the blue room; pace: slow; volume: quiet.
*Note:* The two mothers a nice turn, unhurried.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck. "All that steel, and under it, look. A person."
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. Your buckles take an age. She undoes them as if she has done a great many, and laughs at the last one, which is stuck. "All that steel, and under it, look. A person."

### 207. `dlg.sella.stairs_room.5.wav`

*Where:* dialogue.json sella/stairs_room#5
*Played:* warm, wry; doing: the blue room; pace: slow; volume: quiet.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She takes your hands, one and then the other, and turns them over, and looks at the knuckles. "Gently, upstairs. I mean it. I like this jug."
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She takes your hands, one and then the other, and turns them over, and looks at the knuckles. "Gently, upstairs. I mean it. I like this jug."

### 208. `dlg.sella.stairs_room.6.wav`

*Where:* dialogue.json sella/stairs_room#6
*Played:* warm, wry; doing: the blue room; pace: slow; volume: quiet.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower. "Your hands are hot and the rest of you's a cellar floor. Pick one, love."
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She lays her palm flat on your chest and takes it away again, fast, then puts it back, slower. "Your hands are hot and the rest of you's a cellar floor. Pick one, love."

### 209. `dlg.sella.stairs_room.7.wav`

*Where:* dialogue.json sella/stairs_room#7
*Played:* warm, playful; doing: the blue room; pace: slow; volume: quiet.

```
[quietly] The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She comes round behind you to start on the laces, and says into your ear, "There. Now you know what it's like," and you jump. She's delighted.
```
Subtitle: The blue room is blue because the lamp glass is, and everything in it takes the colour: the quilt, the jug, the bath, her. She tests the water with her elbow like somebody's mother, and then tips your chin up with one finger like nobody's mother at all. She comes round behind you to start on the laces, and says into your ear, "There. Now you know what it's like," and you jump. She's delighted.

### 210. `dlg.sella.stairs_rules.0.p0.wav`

*Where:* dialogue.json sella/stairs_rules#0; part 1 of 2: **narrator: In the bath she slides her hands down your arms, and stops. Under the warm water you are c…** / sella: ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] In the bath she slides her hands down your arms, and stops. Under the warm water you are cold: not chilled, cold, like something brought up off the riverbed. She doesn't make a joke of it. She keeps her hands where they are for a long time, as if that would help.
```
Subtitle: In the bath she slides her hands down your arms, and stops. Under the warm water you are cold: not chilled, cold, like something brought up off the riverbed. She doesn't make a joke of it. She keeps her hands where they are for a long time, as if that would help.

### 211. `dlg.sella.stop_paid.0.p0.wav`

*Where:* dialogue.json sella/stop_paid#0; part 1 of 4: **narrator: She sits back on her heels, and doesn't sulk, and doesn't ask why.** / sella: Then I'll have the bath. It's paid for. / narrator: She counts thirteen coins back into your palm and closes your fingers on them. / sella: Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She sits back on her heels, and doesn't sulk, and doesn't ask why.
```
Subtitle: She sits back on her heels, and doesn't sulk, and doesn't ask why.

### 212. `dlg.sella.stop_paid.0.p2.wav`

*Where:* dialogue.json sella/stop_paid#0; part 3 of 4: narrator: She sits back on her heels, and doesn't sulk, and doesn't ask why. / sella: Then I'll have the bath. It's paid for. / **narrator: She counts thirteen coins back into your palm and closes your fingers on them.** / sella: Two for the water. That's Rook's rule, not mine. ...You'll come back when you want to. Or …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She counts thirteen coins back into your palm and closes your fingers on them.
```
Subtitle: She counts thirteen coins back into your palm and closes your fingers on them.

### 213. `dlg.sella.rest_night.0.p1.wav`

*Where:* dialogue.json sella/rest_night#0; part 2 of 3: sella: Sleep. / **narrator: She looks at you as if you'd asked her to recite something in a foreign tongue.** / sella: You've paid fifteen gold to sleep.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you as if you'd asked her to recite something in a foreign tongue.
```
Subtitle: She looks at you as if you'd asked her to recite something in a foreign tongue.

### 214. `dlg.sella.rest_night_paid.0.p1.wav`

*Where:* dialogue.json sella/rest_night_paid#0; part 2 of 3: sella: Sleep. / **narrator: She looks at you as if you'd asked her to recite something in a foreign tongue.** / sella: You've paid fifteen gold to sleep.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you as if you'd asked her to recite something in a foreign tongue.
```
Subtitle: She looks at you as if you'd asked her to recite something in a foreign tongue.

### 215. `dlg.sella.rest_dark.0.wav`

*Where:* dialogue.json sella/rest_dark#0
*Played:* tender, quiet; doing: she watches you sleep; pace: slow; volume: hushed.
*Note:* The Low Kiln man funny; the watching very quiet.

```
[whispers] She lies down on top of the quilt with all her clothes on, and you under it, and for a while she talks: about Rook, about Holloway's feet, about a man from Low Kiln who wanted her to bark. You don't hear the end of the man from Low Kiln. Some time in the night you half wake and she isn't talking. She's lying on her side, watching you, the way you'd watch weather.
```
Subtitle: She lies down on top of the quilt with all her clothes on, and you under it, and for a while she talks: about Rook, about Holloway's feet, about a man from Low Kiln who wanted her to bark. You don't hear the end of the man from Low Kiln. Some time in the night you half wake and she isn't talking. She's lying on her side, watching you, the way you'd watch weather.

### 216. `dlg.sella.rest_morning.0.p0.wav`

*Where:* dialogue.json sella/rest_morning#0; part 1 of 2: **narrator: She's sitting on the edge of the bed with her hand flat on your chest.** / sella: You were cold as the river all night. Like lying next to a stone. And now look at you: war…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's sitting on the edge of the bed with her hand flat on your chest.
```
Subtitle: She's sitting on the edge of the bed with her hand flat on your chest.

### 217. `dlg.sella.rest_morning.1.p1.wav`

*Where:* dialogue.json sella/rest_morning#1; part 2 of 3: sella: Fifteen gold to watch you snore. Best money I ever made. / **narrator: She's already dressed. She doesn't count it.** / sella: Don't tell anyone. They'll all want it, and then where will I be? Rich and bored.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She's already dressed. She doesn't count it.
```
Subtitle: She's already dressed. She doesn't count it.

### 218. `dlg.sella.door.0.p1.wav`

*Where:* dialogue.json sella/door#0; part 2 of 3: sella: That? It's Rook's. / **narrator: She sits on the bed to do up her boots, and doesn't look up.** / sella: Working nights it stays drawn back. Rook's got a key and a cudgel, and if a man turns funn…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She sits on the bed to do up her boots, and doesn't look up.
```
Subtitle: She sits on the bed to do up her boots, and doesn't look up.

### 219. `dlg.sella.door_years.0.p1.wav`

*Where:* dialogue.json sella/door_years#0; part 2 of 3: sella: Twenty-two, and sure I was cleverer than everyone in the valley. I was right about most of… / **narrator: She laughs, low.** / sella: I'm twenty-nine, love, since you're doing sums. Seven years at the top of Rook's stairs, a…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs, low.
```
Subtitle: She laughs, low.

### 220. `dlg.sella.door_south.0.p1.wav`

*Where:* dialogue.json sella/door_south#0; part 2 of 3: sella: I told you. A house in the south. A door that locks from the inside. / **narrator: She stands, and checks her hair in the jug, and doesn't look at you.** / sella: And somebody who knocks.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She stands, and checks her hair in the jug, and doesn't look at you.
```
Subtitle: She stands, and checks her hair in the jug, and doesn't look at you.

### 221. `dlg.sella.free_decline.0.p1.wav`

*Where:* dialogue.json sella/free_decline#0; part 2 of 5: sella: Your loss, love. Literally; I'm worth a fortune. / **narrator: She means it lightly, and very nearly manages it.** / sella: ...No, it's all right. It is. I'll not ask twice. I don't ask twice. / narrator: She pats your cheek, once, like a regular's. / sella: Go on. Rook's stew's still warm.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She means it lightly, and very nearly manages it.
```
Subtitle: She means it lightly, and very nearly manages it.

### 222. `dlg.sella.free_decline.0.p3.wav`

*Where:* dialogue.json sella/free_decline#0; part 4 of 5: sella: Your loss, love. Literally; I'm worth a fortune. / narrator: She means it lightly, and very nearly manages it. / sella: ...No, it's all right. It is. I'll not ask twice. I don't ask twice. / **narrator: She pats your cheek, once, like a regular's.** / sella: Go on. Rook's stew's still warm.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She pats your cheek, once, like a regular's.
```
Subtitle: She pats your cheek, once, like a regular's.

### 223. `dlg.sella.free_ask.0.p0.wav`

*Where:* dialogue.json sella/free_ask#0; part 1 of 2: **narrator: She looks at you for a long moment, as if you were a coin she was checking for clipping.** / sella: I said I'd not ask twice. I never said I'd not answer. ...Come on, then. Before I think be…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you for a long moment, as if you were a coin she was checking for clipping.
```
Subtitle: She looks at you for a long moment, as if you were a coin she was checking for clipping.

### 224. `dlg.sella.free_stairs.0.wav`

*Where:* dialogue.json sella/free_stairs#0
*Played:* tender, comic; doing: she forgets the step; pace: slow; volume: quiet.
*Note:* The creak 'loud as a shout' a beat of comedy; then quieter.

```
[quietly] She doesn't take your hand on the stairs, or your sleeve. She goes up ahead of you, and on the fourth step she forgets to step over it, and it creaks, loud as a shout, and she stops dead with one foot on it and laughs at herself, and that's worse, somehow, than if she hadn't. In the blue room she turns the lamp up, not down. She stands with her back against the door as if somebody might try it.
```
Subtitle: She doesn't take your hand on the stairs, or your sleeve. She goes up ahead of you, and on the fourth step she forgets to step over it, and it creaks, loud as a shout, and she stops dead with one foot on it and laughs at herself, and that's worse, somehow, than if she hadn't. In the blue room she turns the lamp up, not down. She stands with her back against the door as if somebody might try it.

### 225. `dlg.sella.free_door.0.p1.wav`

*Where:* dialogue.json sella/free_door#0; part 2 of 3: sella: I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd he… / **narrator: She shakes her head.** / sella: Nobody does that. Nobody's ever done that.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She shakes her head.
```
Subtitle: She shakes her head.

### 226. `dlg.sella.free_want.0.p1.wav`

*Where:* dialogue.json sella/free_want#0; part 2 of 3: sella: Ask me that again and I'll cry, and I don't cry, so don't. / **narrator: She takes a breath.** / sella: Yes. ...Yes. There. Said it. Come here.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She takes a breath.
```
Subtitle: She takes a breath.

### 227. `dlg.sella.free_stop.0.p0.wav`

*Where:* dialogue.json sella/free_stop#0; part 1 of 4: **narrator: She lets out a breath she's been holding since the stairs.** / sella: All right. / narrator: And it is; you can see it is. / sella: All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She lets out a breath she's been holding since the stairs.
```
Subtitle: She lets out a breath she's been holding since the stairs.

### 228. `dlg.sella.free_stop.0.p2.wav`

*Where:* dialogue.json sella/free_stop#0; part 3 of 4: narrator: She lets out a breath she's been holding since the stairs. / sella: All right. / **narrator: And it is; you can see it is.** / sella: All right. ...Sit with me, then. Just sit. I've never just sat in here with anybody. Rook'…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] And it is; you can see it is.
```
Subtitle: And it is; you can see it is.

### 229. `dlg.sella.free_sit.0.wav`

*Where:* dialogue.json sella/free_sit#0
*Played:* tender, quiet; doing: sitting together; pace: slow; volume: quiet.

```
[quietly] You sit on the bed with your backs to the wall, and she tells you about the house in the south: which room faces the sun; the colour of the door; the knock. Then she sends you down the stairs, and stands at the top to watch you skip the fourth.
```
Subtitle: You sit on the bed with your backs to the wall, and she tells you about the house in the south: which room faces the sun; the colour of the door; the knock. Then she sends you down the stairs, and stands at the top to watch you skip the fourth.

### 230. `dlg.sella.free_sleep.0.p0.wav`

*Where:* dialogue.json sella/free_sleep#0; part 1 of 2: **narrator: She laughs, properly, the first time tonight.** / sella: You and your sleeping. ...Yes. All right. Yes.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs, properly, the first time tonight.
```
Subtitle: She laughs, properly, the first time tonight.

### 231. `dlg.sella.free_sleep_bed.0.wav`

*Where:* dialogue.json sella/free_sleep_bed#0
*Played:* tender, quiet; doing: she sleeps; pace: slow; volume: hushed.

```
[whispers] She reaches behind her without looking and finds the bolt, and shoots it. Then she gets into the bed in her shift, and you get in beside her, and she lies with her back against you and pulls your arm over her like a blanket. She's asleep before you are. She's still there when you wake.
```
Subtitle: She reaches behind her without looking and finds the bolt, and shoots it. Then she gets into the bed in her shift, and you get in beside her, and she lies with her back against you and pulls your arm over her like a blanket. She's asleep before you are. She's still there when you wake.

### 232. `dlg.sella.free_bolt.0.wav`

*Where:* dialogue.json sella/free_bolt#0
*Played:* tender, comic; doing: the bolt; pace: slow; volume: quiet.
*Note:* The stuck bolt funny; the coin image quietly moving.

```
[quietly] She reaches behind her without looking and finds the bolt. It sticks halfway; nobody has ever shot it. She has to turn round and put her shoulder to it, swearing, and it goes home with a sound like the last coin put down on a counter. Her back is still to you. Her forehead is against the door. "...There."
```
Subtitle: She reaches behind her without looking and finds the bolt. It sticks halfway; nobody has ever shot it. She has to turn round and put her shoulder to it, swearing, and it goes home with a sound like the last coin put down on a counter. Her back is still to you. Her forehead is against the door. "...There."

### 233. `dlg.sella.free_m_downstairs.0.p0.wav`

*Where:* dialogue.json sella/free_m_downstairs#0; part 1 of 2: **narrator: She laughs.** / sella: Downstairs Rook hears everything and charges nobody. You'd be better off with me. ...No. Y…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She laughs.
```
Subtitle: She laughs.

### 234. `dlg.sella.free_m_who.0.p1.wav`

*Where:* dialogue.json sella/free_m_who#0; part 2 of 3: sella: You know who. Everybody pays; she pays most. / **narrator: She pulls the quilt up to her chin.** / sella: I said don't tell me. I didn't say I'd sell it. ...I didn't say I wouldn't, either. I don'…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She pulls the quilt up to her chin.
```
Subtitle: She pulls the quilt up to her chin.

### 235. `dlg.sella.free_m_kiss.0.wav`

*Where:* dialogue.json sella/free_m_kiss#0
*Played:* warm, wry; doing: out; pace: measured; volume: quiet.
*Note:* Her quoted word warm. The smile in the narration.

```
[quietly] She lets you. Then she pushes you off by the face, gently, with the flat of her hand. "Out. Before I get used to it." She's smiling. She doesn't stop smiling until you're down the stairs, and you know that because the ninth step creaks behind you: she came down two steps to watch you go, and forgot it.
```
Subtitle: She lets you. Then she pushes you off by the face, gently, with the flat of her hand. "Out. Before I get used to it." She's smiling. She doesn't stop smiling until you're down the stairs, and you know that because the ninth step creaks behind you: she came down two steps to watch you go, and forgot it.

### 236. `dlg.sella.refuse_roost.0.p0.wav`

*Where:* dialogue.json sella/refuse_roost#0; part 1 of 4: **narrator: At the top of the stairs she stops with her hand on the door.** / sella: They're saying you burned the Roost with folk still in it. / narrator: She puts the coins back in your hand, all of them. / sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] At the top of the stairs she stops with her hand on the door.
```
Subtitle: At the top of the stairs she stops with her hand on the door.

### 237. `dlg.sella.refuse_roost.0.p2.wav`

*Where:* dialogue.json sella/refuse_roost#0; part 3 of 4: narrator: At the top of the stairs she stops with her hand on the door. / sella: They're saying you burned the Roost with folk still in it. / **narrator: She puts the coins back in your hand, all of them.** / sella: I don't judge, love. It's bad for business. But I can smell it on you, and I'm not working…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She puts the coins back in your hand, all of them.
```
Subtitle: She puts the coins back in your hand, all of them.

## Conversations: Pell

### 238. `dlg.pell.hub.0.p0.wav`

*Where:* dialogue.json pell/hub#0; part 1 of 2: **narrator: He smiles a little too quickly.** / pell: Ah. You. What can I do for you today, specifically?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He smiles a little too quickly.
```
Subtitle: He smiles a little too quickly.

### 239. `dlg.pell.confront.0.p1.wav`

*Where:* dialogue.json pell/confront#0; part 2 of 3: pell: Where did you— the clerk. Of course. / **narrator: He studies your face, and something in his own unclenches.** / pell: ...You don't know what you're holding, do you? How refreshing. Let's be civilised. There's…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He studies your face, and something in his own unclenches.
```
Subtitle: He studies your face, and something in his own unclenches.

### 240. `dlg.pell.t_pell.0.p1.wav`

*Where:* dialogue.json pell/t_pell#0; part 2 of 3: pell: My sister kept the books in Ashford. I came up to collect them, after. There wasn't an Ash… / **narrator: He straightens a pen that was straight.** / pell: She wrote to me the week before. The garrison's boots had come in short, and somebody had …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He straightens a pen that was straight.
```
Subtitle: He straightens a pen that was straight.

## Conversations: Rav

### 241. `dlg.rav.cb_killed_redcowl.0.p0.wav`

*Where:* dialogue.json rav/cb_killed_redcowl#0; part 1 of 4: **narrator: He doesn't look up.** / rav: You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated… / narrator: He drinks. / rav: No. He'd have said it was the job. It was always the job, with him. Get out of my light fo…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't look up.
```
Subtitle: He doesn't look up.

### 242. `dlg.rav.cb_killed_redcowl.0.p2.wav`

*Where:* dialogue.json rav/cb_killed_redcowl#0; part 3 of 4: narrator: He doesn't look up. / rav: You killed him. ...Dunstan. That was his name, before the hat. Our mother's idea; he hated… / **narrator: He drinks.** / rav: No. He'd have said it was the job. It was always the job, with him. Get out of my light fo…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He drinks.
```
Subtitle: He drinks.

### 243. `dlg.rav.leg_held.0.p0.wav`

*Where:* dialogue.json rav/leg_held#0; part 1 of 4: **narrator: He puts the cup down, very carefully, as if it were full.** / rav: ...Did he. / narrator: A long time. / rav: Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He puts the cup down, very carefully, as if it were full.
```
Subtitle: He puts the cup down, very carefully, as if it were full.

### 244. `dlg.rav.leg_held.0.p2.wav`

*Where:* dialogue.json rav/leg_held#0; part 3 of 4: narrator: He puts the cup down, very carefully, as if it were full. / rav: ...Did he. / **narrator: A long time.** / rav: Course it held. I'm a good doctor. ...Go on, pal. Come back tomorrow.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A long time.
```
Subtitle: A long time.

### 245. `dlg.rav.back_room.0.wav`

*Where:* dialogue.json rav/back_room#0
*Played:* wry, observant; doing: Rav's surgery; pace: measured; volume: quiet.
*Note:* A little relish in the moving jar and the trophy needle.

```
[quietly] Behind the Crooked Flagon there's a lean-to with a lamp, a scrubbed table, a shelf of jars one of them moving , and a sail-needle stuck in a cork like a trophy. Rav is sitting on the table with his feet on a stool and two cups already poured.
```
Subtitle: Behind the Crooked Flagon there's a lean-to with a lamp, a scrubbed table, a shelf of jars one of them moving , and a sail-needle stuck in a cork like a trophy. Rav is sitting on the table with his feet on a stool and two cups already poured.

### 246. `dlg.rav.back_room_look.0.p1.wav`

*Where:* dialogue.json rav/back_room_look#0; part 2 of 7: rav: You came. / **narrator: He looks faintly alarmed about it.** / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / rav: You're cold, pal. Cold as a cellar step. / narrator: He frowns at your wrist, then lets it go. / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks faintly alarmed about it.
```
Subtitle: He looks faintly alarmed about it.

### 247. `dlg.rav.back_room_look.0.p3.wav`

*Where:* dialogue.json rav/back_room_look#0; part 4 of 7: rav: You came. / narrator: He looks faintly alarmed about it. / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / **narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do…** / rav: You're cold, pal. Cold as a cellar step. / narrator: He frowns at your wrist, then lets it go. / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at your eyes, and your tongue, and your hands, turning them over the way Sella does, but for different reasons. He listens at your back with his ear flat against it, and tells you to cough. He's quiet a moment.
```
Subtitle: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella does, but for different reasons. He listens at your back with his ear flat against it, and tells you to cough. He's quiet a moment.

### 248. `dlg.rav.back_room_look.0.p5.wav`

*Where:* dialogue.json rav/back_room_look#0; part 6 of 7: rav: You came. / narrator: He looks faintly alarmed about it. / rav: Right. Up on the table. Breathe in. Out. Don't flatter yourself, that's medical. / narrator: He looks at your eyes, and your tongue, and your hands, turning them over the way Sella do… / rav: You're cold, pal. Cold as a cellar step. / **narrator: He frowns at your wrist, then lets it go.** / rav: ...There's nothing wrong with you. That's the worrying part. Nobody's got nothing wrong wi…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He frowns at your wrist, then lets it go.
```
Subtitle: He frowns at your wrist, then lets it go.

### 249. `dlg.rav.back_room_drink.0.p1.wav`

*Where:* dialogue.json rav/back_room_drink#0; part 2 of 3: rav: For one of us. / **narrator: He drinks his, then looks at yours.** / rav: Both of us, evidently. ...Go home, pal. You've got a job up the Old Road, and I've got a b…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He drinks his, then looks at yours.
```
Subtitle: He drinks his, then looks at yours.

### 250. `dlg.rav.back_room_kiss.0.p0.wav`

*Where:* dialogue.json rav/back_room_kiss#0; part 1 of 4: **narrator: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. …** / rav: Not yet, pal. Not three cups down, and not while you're still needing things off me: keys,… / narrator: He picks up his cup. / rav: Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's t…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. Then he puts a hand flat on your chest and moves you back a foot, gently, the way he'd move a patient.
```
Subtitle: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. Then he puts a hand flat on your chest and moves you back a foot, gently, the way he'd move a patient.

### 251. `dlg.rav.back_room_kiss.0.p2.wav`

*Where:* dialogue.json rav/back_room_kiss#0; part 3 of 4: narrator: He lets you, for a moment. He tastes of the Flagon's piss and something under it, cloves. … / rav: Not yet, pal. Not three cups down, and not while you're still needing things off me: keys,… / **narrator: He picks up his cup.** / rav: Ask me again when you've stopped needing anything. I'll be here. I'm always here. That's t…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He picks up his cup.
```
Subtitle: He picks up his cup.

### 252. `dlg.rav.back_room_end.0.p1.wav`

*Where:* dialogue.json rav/back_room_end#0; part 2 of 3: rav: "Doctor." / **narrator: He snorts.** / rav: Get out of my surgery.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He snorts.
```
Subtitle: He snorts.

### 253. `dlg.rav.came_back.0.p0.wav`

*Where:* dialogue.json rav/came_back#0; part 1 of 4: **narrator: He's at his table. He's sober, or near it. He's shaved.** / rav: You came back. / narrator: He looks at you for a long time. / rav: Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. .…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's at his table. He's sober, or near it. He's shaved.
```
Subtitle: He's at his table. He's sober, or near it. He's shaved.

### 254. `dlg.rav.came_back.0.p2.wav`

*Where:* dialogue.json rav/came_back#0; part 3 of 4: narrator: He's at his table. He's sober, or near it. He's shaved. / rav: You came back. / **narrator: He looks at you for a long time.** / rav: Most folk wouldn't. Most folk would drink at Rook's for a month and hope I'd died of it. .…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you for a long time.
```
Subtitle: He looks at you for a long time.

### 255. `dlg.rav.came_back_sit.0.p0.wav`

*Where:* dialogue.json rav/came_back_sit#0; part 1 of 2: **narrator: A breath out through his nose.** / rav: Aye. Well. Sit, then.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A breath out through his nose.
```
Subtitle: A breath out through his nose.

## Conversations: Vonnra

### 256. `dlg.vonnra.hub.2.p0.wav`

*Where:* dialogue.json vonnra/hub#2; part 1 of 2: **narrator: Her lamp is lit, and she is looking south, toward the ford.** / vonnra: Traveller. The road was quiet tonight. It will not always be. Payment, always.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Her lamp is lit, and she is looking south, toward the ford.
```
Subtitle: Her lamp is lit, and she is looking south, toward the ford.

### 257. `dlg.vonnra.f_below.0.p1.wav`

*Where:* dialogue.json vonnra/f_below#0; part 2 of 2: vonnra: Last. Under the Verge, something is turning over in its sleep, and under a farm past the O… / **narrator: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame …**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The roof shivers under the table, and the glass of her lamp rings in its frame. The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the braziers on the wall do not. She looks east, into the dark, and does not finish.
```
Subtitle: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the braziers on the wall do not. She looks east, into the dark, and does not finish.

### 258. `dlg.vonnra.f_below.1.p1.wav`

*Where:* dialogue.json vonnra/f_below#1; part 2 of 2: vonnra: Last. Under the Verge, something is turning over in its sleep. The little lamp-people are … / **narrator: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame …**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The roof shivers under the table, and the glass of her lamp rings in its frame. The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the braziers on the wall do not. She looks east, into the dark, and does not finish.
```
Subtitle: The roof shivers under the table, and the glass of her lamp rings in its frame. The flame lies over toward the hill. Down in the town every lamp dips at once, and comes back; the braziers on the wall do not. She looks east, into the dark, and does not finish.

### 259. `dlg.vonnra.jessop.0.p1.wav`

*Where:* dialogue.json vonnra/jessop#0; part 2 of 3: vonnra: Gone south. On the toll's business. / **narrator: She turns a page of the ledger that does not need turning.** / vonnra: Clerks go south, traveller. It is the direction they fall in.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She turns a page of the ledger that does not need turning.
```
Subtitle: She turns a page of the ledger that does not need turning.

### 260. `dlg.vonnra.f_past.0.p1.wav`

*Where:* dialogue.json vonnra/f_past#0; part 2 of 2: vonnra: And before the ford: a child following tracks through these woods, with a bow too big for … / **narrator: She is not looking at your palm.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She is not looking at your palm.
```
Subtitle: She is not looking at your palm.

### 261. `dlg.vonnra.f_past.1.p1.wav`

*Where:* dialogue.json vonnra/f_past#1; part 2 of 2: vonnra: And before the ford: four years in a cloister cellar among dead men's letters, and a lens … / **narrator: She is not looking at your palm.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She is not looking at your palm.
```
Subtitle: She is not looking at your palm.

### 262. `dlg.vonnra.f_past.2.p1.wav`

*Where:* dialogue.json vonnra/f_past#2; part 2 of 2: vonnra: And before the ford: worse company than the Kerchiefs, and the trick of walking away from … / **narrator: She is not looking at your palm.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She is not looking at your palm.
```
Subtitle: She is not looking at your palm.

### 263. `dlg.vonnra.f_past.3.p1.wav`

*Where:* dialogue.json vonnra/f_past#3; part 2 of 2: vonnra: And before the ford: chapel lamps that nobody came to see, and you, lighting them anyway. / **narrator: She is not looking at your palm.**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She is not looking at your palm.
```
Subtitle: She is not looking at your palm.

### 264. `dlg.vonnra.f_accuse.0.p0.wav`

*Where:* dialogue.json vonnra/f_accuse#0; part 1 of 2: **narrator: For the first time she looks at your face and not at your hand. It goes on long enough tha…** / vonnra: ...Sit down. I have not finished reading.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] For the first time she looks at your face and not at your hand. It goes on long enough that the lamp gutters.
```
Subtitle: For the first time she looks at your face and not at your hand. It goes on long enough that the lamp gutters.

## Conversations: Keegan

### 265. `dlg.keegan.say_risen.0.p1.wav`

*Where:* dialogue.json keegan/say_risen#0; part 2 of 3: keegan: I am told you were carried into the shrine under a sheet. / **narrator: She looks at you very carefully, from your boots upwards, and back down.** / keegan: You look well. You look extremely well. ...I've got to go and read something. I— I have to…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you very carefully, from your boots upwards, and back down.
```
Subtitle: She looks at you very carefully, from your boots upwards, and back down.

### 266. `dlg.keegan.supper.0.p1.wav`

*Where:* dialogue.json keegan/supper#0; part 2 of 3: keegan: I have not. I am on watch. / **narrator: She looks at the bread in her hand, which she has evidently been holding for some time.** / keegan: Chapter eleven, paragraph six permits "a meal taken in company for the purposes of morale"…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at the bread in her hand, which she has evidently been holding for some time.
```
Subtitle: She looks at the bread in her hand, which she has evidently been holding for some time.

### 267. `dlg.keegan.supper_table.0.wav`

*Where:* dialogue.json keegan/supper_table#0
*Played:* quiet, warm; doing: supper at the gate; pace: slow; volume: quiet.
*Note:* Gentle; the dark road a quiet image.

```
[quietly] She breaks the bread and gives you the larger half without seeming to decide to. There's a heel of cheese, and a flask that turns out to be water, and the north road beyond the gate is black all the way to the hills.
```
Subtitle: She breaks the bread and gives you the larger half without seeming to decide to. There's a heel of cheese, and a flask that turns out to be water, and the north road beyond the gate is black all the way to the hills.

### 268. `dlg.keegan.supper_wends.0.p1.wav`

*Where:* dialogue.json keegan/supper_wends#0; part 2 of 3: keegan: Rhetoric, to the sons and daughters of people who could afford it. I was very good. I was … / **narrator: She smiles at the road.** / keegan: I taught them chiasmus. "The Vigil keeps the gate, and the gate keeps the Vigil." It has k…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She smiles at the road.
```
Subtitle: She smiles at the road.

### 269. `dlg.keegan.supper_age.0.p1.wav`

*Where:* dialogue.json keegan/supper_age#0; part 2 of 3: keegan: Twenty-six. The handbook says that is old for a probationer. The handbook says a great man… / **narrator: She looks at you sidelong.** / keegan: How old are you? No. Do not answer. I should only write it down.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you sidelong.
```
Subtitle: She looks at you sidelong.

### 270. `dlg.keegan.supper_letters.0.p0.wav`

*Where:* dialogue.json keegan/supper_letters#0; part 1 of 4: **narrator: She doesn't answer for so long that you think she won't.** / keegan: That is a possibility I have considered. / narrator: Very precisely. / keegan: I have considered it every month for two years, on the day the post does not come. I have …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She doesn't answer for so long that you think she won't.
```
Subtitle: She doesn't answer for so long that you think she won't.

### 271. `dlg.keegan.supper_letters.0.p2.wav`

*Where:* dialogue.json keegan/supper_letters#0; part 3 of 4: narrator: She doesn't answer for so long that you think she won't. / keegan: That is a possibility I have considered. / **narrator: Very precisely.** / keegan: I have considered it every month for two years, on the day the post does not come. I have …
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Very precisely.
```
Subtitle: Very precisely.

### 272. `dlg.keegan.supper_read.0.p0.wav`

*Where:* dialogue.json keegan/supper_read#0; part 1 of 4: **narrator: She is very obviously delighted, and very obviously trying not to be.** / keegan: Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body b… / narrator: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gat… / keegan: ...You did not fall asleep. Nobody has ever not fallen asleep.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She is very obviously delighted, and very obviously trying not to be.
```
Subtitle: She is very obviously delighted, and very obviously trying not to be.

### 273. `dlg.keegan.supper_read.0.p2.wav`

*Where:* dialogue.json keegan/supper_read#0; part 3 of 4: narrator: She is very obviously delighted, and very obviously trying not to be. / keegan: Chapter nine. On bathing. "The knight shall wash at need, and not for pleasure, the body b… / **narrator: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gat…** / keegan: ...You did not fall asleep. Nobody has ever not fallen asleep.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She reads you chapter twelve, on the care of the blade, all of it, by the light of the gate lamp, and it is beautiful, actually.
```
Subtitle: She reads you chapter twelve, on the care of the blade, all of it, by the light of the gate lamp, and it is beautiful, actually.

### 274. `dlg.keegan.supper_ch4.0.p0.wav`

*Where:* dialogue.json keegan/supper_ch4#0; part 1 of 3: **narrator: She closes the book.** / keegan: No. / narrator: She says it gently, and then she doesn't say anything else for a while, and her hand stays…
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She closes the book.
```
Subtitle: She closes the book.

### 275. `dlg.keegan.supper_ch4.0.p2.wav`

*Where:* dialogue.json keegan/supper_ch4#0; part 3 of 3: narrator: She closes the book. / keegan: No. / **narrator: She says it gently, and then she doesn't say anything else for a while, and her hand stays…**
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She says it gently, and then she doesn't say anything else for a while, and her hand stays flat on the cover.
```
Subtitle: She says it gently, and then she doesn't say anything else for a while, and her hand stays flat on the cover.

### 276. `dlg.keegan.supper_hand.0.p0.wav`

*Where:* dialogue.json keegan/supper_hand#0; part 1 of 4: **narrator: You put your hand over hers on the stone. She lets it stay there for a count of three.** / keegan: I am on duty. / narrator: She takes her hand back. Then, without looking, she puts it back, under yours, for another… / keegan: ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] You put your hand over hers on the stone. She lets it stay there for a count of three.
```
Subtitle: You put your hand over hers on the stone. She lets it stay there for a count of three.

### 277. `dlg.keegan.supper_hand.0.p2.wav`

*Where:* dialogue.json keegan/supper_hand#0; part 3 of 4: narrator: You put your hand over hers on the stone. She lets it stay there for a count of three. / keegan: I am on duty. / **narrator: She takes her hand back. Then, without looking, she puts it back, under yours, for another…** / keegan: ...That was epizeuxis. The same thing, twice, at once, for emphasis. Goodnight.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She takes her hand back. Then, without looking, she puts it back, under yours, for another count of three.
```
Subtitle: She takes her hand back. Then, without looking, she puts it back, under yours, for another count of three.

### 278. `dlg.keegan.supper_end.0.p1.wav`

*Where:* dialogue.json keegan/supper_end#0; part 2 of 3: keegan: Goodnight. / **narrator: As you go:** / keegan: It was good for morale. Mine. I checked.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] As you go:
```
Subtitle: As you go:

## Conversations: the Wayfinder

### 279. `dlg.wayfinder.margin.0.p1.wav`

*Where:* dialogue.json wayfinder/margin#0; part 2 of 3: ysolde: Who came back, from where, how long they lasted, what they carried out. Name first; I'm a … / **narrator: She dips her pen.** / ysolde: Speaking of which. How do I put you down?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She dips her pen.
```
Subtitle: She dips her pen.

### 280. `dlg.wayfinder.margin_name.0.p0.wav`

*Where:* dialogue.json wayfinder/margin_name#0; part 1 of 2: **narrator: She writes it, blots it, and blows on it.** / ysolde: There. Now you're in the margins for good.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She writes it, blots it, and blows on it.
```
Subtitle: She writes it, blots it, and blows on it.

### 281. `dlg.wayfinder.margin_nobody.0.p1.wav`

*Where:* dialogue.json wayfinder/margin_nobody#0; part 2 of 3: ysolde: Nobody. / **narrator: She writes it without blinking.** / ysolde: You'd be surprised how often Nobody comes back. More than most.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She writes it without blinking.
```
Subtitle: She writes it without blinking.

### 282. `dlg.wayfinder.margin_lark.0.p0.wav`

*Where:* dialogue.json wayfinder/margin_lark#0; part 1 of 2: **narrator: She looks at you over the pen for a moment, then writes.** / ysolde: Lark. You look like a Lark. Larks get up early and make a great deal of noise about it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] She looks at you over the pen for a moment, then writes.
```
Subtitle: She looks at you over the pen for a moment, then writes.

## Conversations: Greymuzzle

### 283. `dlg.greymuzzle.first.0.wav`

*Where:* dialogue.json greymuzzle/first#0
*Played:* still, solemn; doing: meeting the old wolf; pace: slow; volume: quiet.
*Note:* A nature-documentary stillness. Long beat after 'for a long time'. The last image very quiet.

```
[quietly] The old wolf comes out of the rocks alone. He is grey to the eyes, and thin, and he does not growl. He looks at you for a long time. Behind him, in the shadow of the stones, wolves lie in the dirt and do not get up.
```
Subtitle: The old wolf comes out of the rocks alone. He is grey to the eyes, and thin, and he does not growl. He looks at you for a long time. Behind him, in the shadow of the stones, wolves lie in the dirt and do not get up.

### 284. `dlg.greymuzzle.show.0.wav`

*Where:* dialogue.json greymuzzle/show#0
*Played:* sombre pity; doing: the sick Pack; pace: slow; volume: quiet.
*Note:* Plain and close; 'and cannot' after a small beat. End on him waiting: an open question.

```
[quietly] He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. Then your collar, for longer; and his tail moves, once. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Grey-muzzle looks east, toward the stream, then back at you, and waits.
```
Subtitle: He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. Then your collar, for longer; and his tail moves, once. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Greymuzzle looks east, toward the stream, then back at you, and waits.

### 285. `dlg.greymuzzle.show.1.wav`

*Where:* dialogue.json greymuzzle/show#1
*Played:* sombre pity; doing: the sick Pack; pace: slow; volume: quiet.
*Note:* As show.0; the lip lifting a tense beat.

```
[quietly] He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Grey-muzzle looks east, toward the stream, then back at you, and waits.
```
Subtitle: He comes close enough to smell your hand, then your face, and his lip lifts off his teeth, and goes down again. He turns and walks into the Hollow, and you follow. The sick ones' eyes are milky; their gums are black. One of them tries to stand when it sees you, and cannot. Greymuzzle looks east, toward the stream, then back at you, and waits.

### 286. `dlg.greymuzzle.ally.0.wav`

*Where:* dialogue.json greymuzzle/ally#0
*Played:* solemn, moved; doing: the Pack's answer; pace: slow; volume: quiet.
*Note:* 'He is not coming.' alone. 'They are his answer.' warm and grave.

```
[quietly] Grey-muzzle lifts his head and howls, once. Four of the strongest get up and come to stand beside you. The old wolf lies back down among the sick. He is not coming. They are his answer.
```
Subtitle: Greymuzzle lifts his head and howls, once. Four of the strongest get up and come to stand beside you. The old wolf lies back down among the sick. He is not coming. They are his answer.

### 287. `dlg.greymuzzle.again.0.wav`

*Where:* dialogue.json greymuzzle/again#0
*Played:* cold rejection; doing: the Pack has turned its back; pace: slow; volume: quiet.
*Note:* Flat and final.

```
[quietly] Grey-muzzle comes out of the rocks, looks at you for a long moment, and lies down with his back to you. Behind him, the others do the same.
```
Subtitle: Greymuzzle comes out of the rocks, looks at you for a long moment, and lies down with his back to you. Behind him, the others do the same.

### 288. `dlg.greymuzzle.again.1.wav`

*Where:* dialogue.json greymuzzle/again#1
*Played:* sombre; doing: the Pack is dying; pace: slow; volume: quiet.
*Note:* Quiet reproach, never stated.

```
[quietly] Grey-muzzle doesn't come out. Two of the wolves you saw lying in the dirt are not there any more. The others watch you the way they watch weather.
```
Subtitle: Greymuzzle doesn't come out. Two of the wolves you saw lying in the dirt are not there any more. The others watch you the way they watch weather.

### 289. `dlg.greymuzzle.again.2.wav`

*Where:* dialogue.json greymuzzle/again#2
*Played:* warm, understated; doing: the Pack is well; pace: measured; volume: quiet.
*Note:* A smile in the last clause.

```
[quietly] Grey-muzzle is on his feet. So are the others. He looks at you, and then away, which from a wolf is as good as thanks.
```
Subtitle: Greymuzzle is on his feet. So are the others. He looks at you, and then away, which from a wolf is as good as thanks.

### 290. `dlg.greymuzzle.again.3.wav`

*Where:* dialogue.json greymuzzle/again#3
*Played:* still; doing: the old wolf waits; pace: slow; volume: quiet.
*Note:* Plain.

```
[quietly] Grey-muzzle watches you from the rocks. He does not get up.
```
Subtitle: Greymuzzle watches you from the rocks. He does not get up.

## Conversations: Redcowl

### 291. `dlg.redcowl.first.0.p0.wav`

*Where:* dialogue.json redcowl/first#0; part 1 of 2: **narrator: Every crossbow in the camp is on you, and nobody's laughing.** / redcowl: You're the one who's been putting my lads in the ground. Redcowl. Talk, and talk slow.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Every crossbow in the camp is on you, and nobody's laughing.
```
Subtitle: Every crossbow in the camp is on you, and nobody's laughing.

### 292. `dlg.redcowl.trick.0.p1.wav`

*Where:* dialogue.json redcowl/trick#0; part 2 of 3: redcowl: The Watch. Holloway hasn't got the men to— / **narrator: a whistle, from the ridge; the whole camp stops** / redcowl: —PACK IT UP! PACK IT UP! Leave the heavy stuff!
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] a whistle, from the ridge; the whole camp stops
```
Subtitle: a whistle, from the ridge; the whole camp stops

### 293. `dlg.redcowl.crates_dig.0.p0.wav`

*Where:* dialogue.json redcowl/crates_dig#0; part 1 of 4: **narrator: He doesn't laugh.** / redcowl: The hill. / narrator: He looks north-east, past the ravine wall, at nothing you can see. / redcowl: The one that's been knocking at night. ...How deep are they going?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He doesn't laugh.
```
Subtitle: He doesn't laugh.

### 294. `dlg.redcowl.crates_dig.0.p2.wav`

*Where:* dialogue.json redcowl/crates_dig#0; part 3 of 4: narrator: He doesn't laugh. / redcowl: The hill. / **narrator: He looks north-east, past the ravine wall, at nothing you can see.** / redcowl: The one that's been knocking at night. ...How deep are they going?
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks north-east, past the ravine wall, at nothing you can see.
```
Subtitle: He looks north-east, past the ravine wall, at nothing you can see.

### 295. `dlg.redcowl.crates_keep.0.p1.wav`

*Where:* dialogue.json redcowl/crates_keep#0; part 2 of 3: redcowl: Then nobody's having them. Not the hole in the hill. Not Holloway. Not your merchant, and … / **narrator: A laugh, but not the big one.** / redcowl: Guarding crates. My mother'd laugh herself sick.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] A laugh, but not the big one.
```
Subtitle: A laugh, but not the big one.

### 296. `dlg.redcowl.crates_charge.0.p0.wav`

*Where:* dialogue.json redcowl/crates_charge#0; part 1 of 2: **narrator: He looks at you a long while. Then he whistles, and a lad brings one over, walking like he…** / redcowl: Take it. Put it where it'll do the most harm to the right people. And run.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He looks at you a long while. Then he whistles, and a lad brings one over, walking like he's carrying a sleeping baby.
```
Subtitle: He looks at you a long while. Then he whistles, and a lad brings one over, walking like he's carrying a sleeping baby.

### 297. `dlg.redcowl.birds.0.p1.wav`

*Where:* dialogue.json redcowl/birds#0; part 2 of 3: redcowl: Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober. / **narrator: The laugh stops.** / redcowl: Birds don't have names, lass. Not in my camp.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The laugh stops.
```
Subtitle: The laugh stops.

### 298. `dlg.redcowl.birds.1.p1.wav`

*Where:* dialogue.json redcowl/birds#1; part 2 of 3: redcowl: Ha! A little bird. Sings for its drink, and sews a fair seam when it's sober. / **narrator: The laugh stops.** / redcowl: Birds don't have names, lad. Not in my camp.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The laugh stops.
```
Subtitle: The laugh stops.

### 299. `dlg.redcowl.ashford.0.p0.wav`

*Where:* dialogue.json redcowl/ashford#0; part 1 of 4: **narrator: The laugh goes out of him like a lamp.** / redcowl: Don't. / narrator: Quiet. / redcowl: You get to say that once in my camp. You've said it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] The laugh goes out of him like a lamp.
```
Subtitle: The laugh goes out of him like a lamp.

### 300. `dlg.redcowl.ashford.0.p2.wav`

*Where:* dialogue.json redcowl/ashford#0; part 3 of 4: narrator: The laugh goes out of him like a lamp. / redcowl: Don't. / **narrator: Quiet.** / redcowl: You get to say that once in my camp. You've said it.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] Quiet.
```
Subtitle: Quiet.

### 301. `dlg.redcowl.pell_given.0.p1.wav`

*Where:* dialogue.json redcowl/pell_given#0; part 2 of 3: redcowl: Ha! Somebody who knows where the rats sleep. / **narrator: He's already shouting for boots.** / redcowl: Go home. Stay off the square tonight.
*Played:* the narrator's aside inside someone else's line: plain, quiet, observant; the narrator never shows a feeling.

```
[quietly] He's already shouting for boots.
```
Subtitle: He's already shouting for boots.


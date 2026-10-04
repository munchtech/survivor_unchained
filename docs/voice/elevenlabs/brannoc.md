# Brannoc: ElevenLabs packet

Voice id in the game: `brannoc`. 49 takes to record (2,197 characters; about 6,591 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Brannoc** (smith). Fewest words in town: fragments, two sentences at the most, the hammer under everything. Talks about iron the way other people talk about weather. Never small talk, never thanks anyone in words (once: when he is told his daughter's end was quick). The only question he ever asks is about Nell; when he stops hammering, the narrator says so, because it is the loudest thing he does. *Casting:* 50, Cornish, deep and slow.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Brannoc`. Never describe a voice as sounding like a real person.

```
Native English (British, Cornish). Male, 50s. Studio quality. Persona: a Cornish blacksmith. A fifty-two-year-old blacksmith from Cornwall with a very deep, slow, rough bass voice and a broad Cornish West Country accent with a rolled 'r'. Few words, heavy and blunt, each one set down like iron on an anvil. Thick Cornish accent. No reverb or effects.
```

Preview text:

```
Steel or fur? Iron's good this year. Good ore, from the north, before the road shut. Won't see the like again.
```

In the Voice Library instead: search for *Cornish*, *male*, *50*, and listen for this: A fifty-two-year-old blacksmith from Cornwall with a very deep, slow, rough bass voice and a broad Cornish West Country accent with a rolled 'r'. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_road_back.place.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice brannoc
```

## Saying the names

The text to paste already respells these; keep the respelling: Brannoc as *Brannock*, Thornhollow'll as *Thorn-hollow'll*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: road back

### 1. `dlg.cin_road_back.place.0.wav`

*Where:* dialogue.json cin_road_back/place#0
*Played:* grief, plain; doing: Brannoc at the ford; pace: slow; volume: quiet.

```
[grief, plain, quietly] You know the place.
```
Subtitle: You know the place.

### 2. `dlg.cin_road_back.wat.0.wav`

*Where:* dialogue.json cin_road_back/wat#0
*Played:* grief, recognition; doing: he names the carter; pace: very slow; volume: hushed.

```
[grief, recognition, whispers] ...Wat.
```
Subtitle: ...Wat.

## Conversations: Brannoc

### 3. `dlg.brannoc.first.0.wav`

*Where:* dialogue.json brannoc/first#0
*Played:* gruff approval; doing: sizes up a hunter; pace: slow; volume: level.
*Wants:* trade
*Note:* Each fragment set down like a weight. 'Good.' approving. The last fragment a statement of trade.

```
[gruff approval] Hunter. Good. You'll know a clean pelt. Brannock. Iron, and things with fur on.
```
Subtitle: Hunter. Good. You'll know a clean pelt. Brannoc. Iron, and things with fur on.

### 4. `dlg.brannoc.first.1.wav`

*Where:* dialogue.json brannoc/first#1
*Played:* blunt, laconic; doing: what he does; pace: slow; volume: level.
*Note:* Deep, slow, few words. 'Which?' a flat question.

```
[blunt, laconic] Brannock. I make things of iron. I buy things with fur on. Which?
```
Subtitle: Brannoc. I make things of iron. I buy things with fur on. Which?

### 5. `dlg.brannoc.hub.0.wav`

*Where:* dialogue.json brannoc/hub#0
*Played:* tired, curt; doing: night; pace: slow; volume: quiet.
*Note:* Short.

```
[tired, curt, quietly] Forge is banked. Make it quick.
```
Subtitle: Forge is banked. Make it quick.

### 6. `dlg.brannoc.hub.1.p1.wav`

*The same words are also* `dlg.brannoc.hub.3.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/hub#1; part 2 of 2: narrator: He works. He doesn't stop when you come in, and he doesn't send you away. / **brannoc: Steel or fur?**
*Played:* quiet acceptance; doing: lets you stay; pace: slow; volume: quiet.
*Note:* Narrator: he keeps working and doesn't send you away. Then 'Steel or fur?' gentler than ever before.

```
[quiet acceptance, quietly] Steel or fur?
```
Subtitle: Steel or fur?

### 7. `dlg.brannoc.hub.2.wav`

*Where:* dialogue.json brannoc/hub#2
*Played:* gruff welcome; doing: glad you're back; pace: slow; volume: level.
*Note:* 'Good.' almost warm.

```
[gruff welcome] Back. Good. Steel or fur?
```
Subtitle: Back. Good. Steel or fur?

### 8. `dlg.brannoc.cloak.0.wav`

*Where:* dialogue.json brannoc/cloak#0
*Played:* craftsman's pride, warning; doing: the cloak is done; pace: slow; volume: level.
*Note:* Pride; the last line a plain warning.

```
[craftsman's pride, warning] There. Warmest thing you'll ever wear. Every wolf in Thorn-hollow'll know what it is.
```
Subtitle: There. Warmest thing you'll ever wear. Every wolf in Thornhollow'll know what it is.

### 9. `dlg.brannoc.irons.0.p1.wav`

*Where:* dialogue.json brannoc/irons#0; part 2 of 2: narrator: He looks at the two irons on the rack for a long time. / **brannoc: Twelve ordered. Ten went down to the ford, at night, square coin on the anvil. ...Buyer'll…**
*Played:* cold suspicion, grief turned to anger; doing: he knows what the irons did; pace: slow; volume: quiet.
*Note:* Narrator holds the long look. Then a ledger of facts, flat. A pause. The last line low and dangerous.

```
[cold suspicion, grief turned to anger, quietly] Twelve ordered. Ten went down to the ford, at night, square coin on the anvil. ...Buyer'll want these two. Buyer can come and ask me for them.
```
Subtitle: Twelve ordered. Ten went down to the ford, at night, square coin on the anvil. ...Buyer'll want these two. Buyer can come and ask me for them.

### 10. `dlg.brannoc.irons.1.wav`

*Where:* dialogue.json brannoc/irons#1
*Played:* flat, then regret; doing: who bought the irons; pace: slow; volume: level.
*Note:* Facts, like reading a tally. 'Didn't ask who.' plain. Pause. 'Should've.' heavy, quiet regret.

```
[flat, then regret] Spares. Lamp-irons for the Low Ford. Twelve ordered last winter, ten collected. Collected at night; coin left on the anvil. Old coin, the square kind. Didn't ask who. ...Should've.
```
Subtitle: Spares. Lamp-irons for the Low Ford. Twelve ordered last winter, ten collected. Collected at night; coin left on the anvil. Old coin, the square kind. Didn't ask who. ...Should've.

### 11. `dlg.brannoc.cb_killed_greymuzzle.0.wav`

*Where:* dialogue.json brannoc/cb_killed_greymuzzle#0
*Played:* blunt regret; doing: a craftsman's loss; pace: slow; volume: level.
*Note:* Matter-of-fact about the fang.

```
[blunt regret] Grey one's dead. Should've brought him here. Fang like that.
```
Subtitle: Grey one's dead. Should've brought him here. Fang like that.

### 12. `dlg.brannoc.cb_wolf_slaughter.0.wav`

*Where:* dialogue.json brannoc/cb_wolf_slaughter#0
*Played:* flat, faintly disapproving; doing: too many wolves dead; pace: slow; volume: level.
*Note:* Three fragments. 'Wood'll be quiet.' a little too quiet.

```
[flat, faintly disapproving] Lot of pelts. Lot of wolves. Wood'll be quiet.
```
Subtitle: Lot of pelts. Lot of wolves. Wood'll be quiet.

### 13. `dlg.brannoc.say_calling.0.wav`

*Where:* dialogue.json brannoc/say_calling#0
*Played:* professional; doing: your shield; pace: slow; volume: level.

```
[professional] Shield's warped. Bring it. No charge for looking.
```
Subtitle: Shield's warped. Bring it. No charge for looking.

### 14. `dlg.brannoc.say_calling.1.wav`

*Where:* dialogue.json brannoc/say_calling#1
*Played:* approving; doing: your blade; pace: slow; volume: level.
*Note:* 'Good.' approving.

```
[approving] Edge is chewed. You hit things. Good.
```
Subtitle: Edge is chewed. You hit things. Good.

### 15. `dlg.brannoc.say_calling.2.wav`

*Where:* dialogue.json brannoc/say_calling#2
*Played:* dismissive, then interested; doing: your staff; pace: slow; volume: level.
*Note:* Dismissive fragments; then 'Ferrule's loose. That is.' iron, his trade.

```
[dismissive, then interested] Staff. Wood. Not my trade. ...Ferrule's loose. That is.
```
Subtitle: Staff. Wood. Not my trade. ...Ferrule's loose. That is.

### 16. `dlg.brannoc.say_calling.3.wav`

*The same words are also* `dlg.brannoc.say_calling.4.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/say_calling#3
*Played:* approving; doing: your knives; pace: slow; volume: level.
*Note:* Four words, each tested like an edge.

```
[approving] Knives. Light. Still. Sharp.
```
Subtitle: Knives. Light. Still. Sharp.

### 17. `dlg.brannoc.t_brannoc.0.wav`

*Where:* dialogue.json brannoc/t_brannoc#0
*Played:* gruff fondness; doing: his mother; pace: slow; volume: level.
*Note:* Fragments; a ghost of a smile on 'Worse temper.' 'Hammer's hers.' proud.

```
[gruff fondness] Mother. Better smith than me. Worse temper. Hammer's hers.
```
Subtitle: Mother. Better smith than me. Worse temper. Hammer's hers.

### 18. `dlg.brannoc.mark.0.p1.wav`

*Where:* dialogue.json brannoc/mark#0; part 2 of 4: narrator: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is. / **brannoc: Mine.** / narrator: He holds it a long time. / brannoc: ...Mine.
*Played:* devastated recognition; doing: his iron killed his daughter; pace: very slow; volume: quiet.
*Note:* Narrator through the handling. 'Mine.' barely voiced. Narrator holds the long time. The second '...Mine.' broken.

```
[devastated recognition, quietly] Mine.
```
Subtitle: Mine.

### 19. `dlg.brannoc.mark.0.p3.wav`

*Where:* dialogue.json brannoc/mark#0; part 4 of 4: narrator: He takes it. Turns it to the light. Puts his thumb under the socket, where the mark is. / brannoc: Mine. / narrator: He holds it a long time. / **brannoc: ...Mine.**
*Played:* devastated recognition; doing: his iron killed his daughter; pace: very slow; volume: quiet.
*Note:* Narrator through the handling. 'Mine.' barely voiced. Narrator holds the long time. The second '...Mine.' broken.

```
[devastated recognition, quietly] ...Mine.
```
Subtitle: ...Mine.

### 20. `dlg.brannoc.mark.1.p1.wav`

*Where:* dialogue.json brannoc/mark#1; part 2 of 4: narrator: He takes it. Turns it to the light. Puts his thumb under the socket. / **brannoc: Mine. Mark's under there. Last winter's work: twelve for the Low Ford, ten collected, at n…** / narrator: He gives it back. / brannoc: Keep it. It's done what it was for.
*Played:* recognition, unease; doing: his mark on the iron; pace: slow; volume: level.
*Note:* 'Mine.' plain. Facts, flat. Narrator gives it back. 'It's done what it was for.' grim.

```
[recognition, unease] Mine. Mark's under there. Last winter's work: twelve for the Low Ford, ten collected, at night, square coin on the anvil.
```
Subtitle: Mine. Mark's under there. Last winter's work: twelve for the Low Ford, ten collected, at night, square coin on the anvil.

### 21. `dlg.brannoc.mark.1.p3.wav`

*Where:* dialogue.json brannoc/mark#1; part 4 of 4: narrator: He takes it. Turns it to the light. Puts his thumb under the socket. / brannoc: Mine. Mark's under there. Last winter's work: twelve for the Low Ford, ten collected, at n… / narrator: He gives it back. / **brannoc: Keep it. It's done what it was for.**
*Played:* recognition, unease; doing: his mark on the iron; pace: slow; volume: level.
*Note:* 'Mine.' plain. Facts, flat. Narrator gives it back. 'It's done what it was for.' grim.

```
[recognition, unease] Keep it. It's done what it was for.
```
Subtitle: Keep it. It's done what it was for.

### 22. `dlg.brannoc.irons_after.0.p1.wav`

*Where:* dialogue.json brannoc/irons_after#0; part 2 of 4: narrator: He puts his hand flat on the two irons. / **brannoc: Buyer'll be back for these. Buyer can come and ask me himself. Or herself.** / narrator: The hammer comes down. / brannoc: I'll know the coin.
*Played:* cold resolve; doing: waits for the buyer; pace: slow; volume: quiet.
*Note:* Low threat. 'Or herself.' a beat, he suspects. Narrator: the hammer comes down. 'I'll know the coin.' very quiet.

```
[cold resolve, quietly] Buyer'll be back for these. Buyer can come and ask me himself. Or herself.
```
Subtitle: Buyer'll be back for these. Buyer can come and ask me himself. Or herself.

### 23. `dlg.brannoc.irons_after.0.p3.wav`

*Where:* dialogue.json brannoc/irons_after#0; part 4 of 4: narrator: He puts his hand flat on the two irons. / brannoc: Buyer'll be back for these. Buyer can come and ask me himself. Or herself. / narrator: The hammer comes down. / **brannoc: I'll know the coin.**
*Played:* cold resolve; doing: waits for the buyer; pace: slow; volume: quiet.
*Note:* Low threat. 'Or herself.' a beat, he suspects. Narrator: the hammer comes down. 'I'll know the coin.' very quiet.

```
[cold resolve, quietly] I'll know the coin.
```
Subtitle: I'll know the coin.

### 24. `dlg.brannoc.nell.0.p1.wav`

*Where:* dialogue.json brannoc/nell#0; part 2 of 4: narrator: He doesn't look up from the anvil, and he doesn't stop. / **brannoc: You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the grey m…** / narrator: The hammer stops. / brannoc: Mine. Nell. ...You pass them?
*Played:* fear held still; doing: asks after his daughter; pace: slow; volume: quiet.
*Wants:* to hear she's safe
*Note:* Narrator: he doesn't stop. Brannoc's facts come out like hammer strokes, too many words for him, which is the tell. 'Twelve. Red hair. New boots.' Narrator: the hammer stops. 'Mine. Nell.' Then the only question he ever asks, very quiet.

```
[fear held still, quietly] You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the grey mare. Toll work. Said he'd be over the ford by dark. Girl with him. Twelve. Red hair. New boots. Going to her aunt at Low Kiln.
```
Subtitle: You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the grey mare. Toll work. Said he'd be over the ford by dark. Girl with him. Twelve. Red hair. New boots. Going to her aunt at Low Kiln.

### 25. `dlg.brannoc.nell.0.p3.wav`

*Where:* dialogue.json brannoc/nell#0; part 4 of 4: narrator: He doesn't look up from the anvil, and he doesn't stop. / brannoc: You came up the Low Ford road. ...Carter went south a fortnight back. Wat, with the grey m… / narrator: The hammer stops. / **brannoc: Mine. Nell. ...You pass them?**
*Played:* fear held still; doing: asks after his daughter; pace: slow; volume: quiet.
*Wants:* to hear she's safe
*Note:* Narrator: he doesn't stop. Brannoc's facts come out like hammer strokes, too many words for him, which is the tell. 'Twelve. Red hair. New boots.' Narrator: the hammer stops. 'Mine. Nell.' Then the only question he ever asks, very quiet.

```
[fear held still, quietly] Mine. Nell. ...You pass them?
```
Subtitle: Mine. Nell. ...You pass them?

### 26. `dlg.brannoc.nell_ditch.0.p1.wav`

*Where:* dialogue.json brannoc/nell_ditch#0; part 2 of 2: narrator: He puts the hammer down, and looks at the two irons still on the rack, and then he doesn't… / **brannoc: ...Had the reins. She'd want the reins. Always wanted the reins.**
*Played:* stunned, flat; doing: learns she died; pace: very slow; volume: quiet.
*Hides:* he suspects whose coin paid for the irons
*Note:* He does not break. Narrator gives the look at the irons. Then facts about his daughter, flat: 'Had the reins.' barely voiced. The love is only in saying 'the reins' again. No breath of his own: the narrator describes it.

```
[stunned, flat, quietly] ...Had the reins. She'd want the reins. Always wanted the reins.
```
Subtitle: ...Had the reins. She'd want the reins. Always wanted the reins.

### 27. `dlg.brannoc.nell_ditch.1.p1.wav`

*Where:* dialogue.json brannoc/nell_ditch#1; part 2 of 2: narrator: He puts the hammer down. You have never seen him put the hammer down. / **brannoc: ...Had the reins. She'd want the reins. Always wanted the reins.**
*Played:* stunned, flat; doing: learns she died; pace: very slow; volume: quiet.
*Hides:* he suspects whose coin paid for the irons
*Note:* He does not break. Narrator: the hammer goes down, which you have never seen. 'Had the reins.' barely voiced. Narrator: the long breath (so none in his read). Flat facts about his daughter; the love is only in saying 'the reins' again.

```
[stunned, flat, quietly] ...Had the reins. [a long breath, through the nose] She'd want the reins. Always wanted the reins.
```
Subtitle: ...Had the reins. She'd want the reins. Always wanted the reins.

### 28. `dlg.brannoc.nell_gone.0.p0.wav`

*Where:* dialogue.json brannoc/nell_gone#0; part 1 of 3: **brannoc: Quick, then. Water's quick.** / narrator: He picks the hammer up and holds it, and doesn't use it. / brannoc: Forge is shut. Go on.
*Played:* grief shutting down; doing: accepts it; pace: slow; volume: quiet.
*Note:* 'Quick, then. Water's quick.' a man holding himself up. Narrator for the hammer. 'Forge is shut. Go on.' near breaking, then steady.

```
[grief shutting down, quietly] Quick, then. Water's quick.
```
Subtitle: Quick, then. Water's quick.

### 29. `dlg.brannoc.nell_gone.0.p2.wav`

*The same words are also* `dlg.brannoc.nell_quick.0.p3.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json brannoc/nell_gone#0; part 3 of 3: brannoc: Quick, then. Water's quick. / narrator: He picks the hammer up and holds it, and doesn't use it. / **brannoc: Forge is shut. Go on.**
*Played:* grief shutting down; doing: accepts it; pace: slow; volume: quiet.
*Note:* 'Quick, then. Water's quick.' a man holding himself up. Narrator for the hammer. 'Forge is shut. Go on.' near breaking, then steady.

```
[grief shutting down, quietly] Forge is shut. Go on.
```
Subtitle: Forge is shut. Go on.

### 30. `dlg.brannoc.nell_risen.0.p1.wav`

*Where:* dialogue.json brannoc/nell_risen#0; part 2 of 4: narrator: He looks at you then. Properly, for the first time. / **brannoc: Got up.** / narrator: He says it the way he tests an edge: weighing it. / brannoc: Got up, and you put her down. ...Was it quick?
*Played:* terrible stillness; doing: she rose and you killed her; pace: very slow; volume: quiet.
*Note:* Narrator: he looks at you. 'Got up.' weighed. Narrator explains how he says it. Then slowly, all of it. A long pause. 'Was it quick?' the most fragile thing he says.

```
[terrible stillness, quietly] Got up.
```
Subtitle: Got up.

### 31. `dlg.brannoc.nell_risen.0.p3.wav`

*Where:* dialogue.json brannoc/nell_risen#0; part 4 of 4: narrator: He looks at you then. Properly, for the first time. / brannoc: Got up. / narrator: He says it the way he tests an edge: weighing it. / **brannoc: Got up, and you put her down. ...Was it quick?**
*Played:* terrible stillness; doing: she rose and you killed her; pace: very slow; volume: quiet.
*Note:* Narrator: he looks at you. 'Got up.' weighed. Narrator explains how he says it. Then slowly, all of it. A long pause. 'Was it quick?' the most fragile thing he says.

```
[terrible stillness, quietly] Got up, and you put her down. ...Was it quick?
```
Subtitle: Got up, and you put her down. ...Was it quick?

### 32. `dlg.brannoc.nell_quick.0.p1.wav`

*Where:* dialogue.json brannoc/nell_quick#0; part 2 of 4: narrator: A long time. / **brannoc: ...Thank you.** / narrator: The forge ticks as it cools. / brannoc: Forge is shut. Go on.
*Played:* grief and gratitude; doing: the one thank you; pace: very slow; volume: hushed.
*Note:* The only thanks he gives in the game. Narrator holds the long time. '...Thank you.' barely there, deep and cracked. Narrator: the forge cools. 'Forge is shut. Go on.' quiet.

```
[grief and gratitude, whispers] ...Thank you.
```
Subtitle: ...Thank you.

### 33. `dlg.brannoc.nell_slow.0.p1.wav`

*Where:* dialogue.json brannoc/nell_slow#0; part 2 of 2: narrator: He nods, once, as if you've told him a price. / **brannoc: Forge is shut.**
*Played:* grief taken like a blow; doing: accepts the price; pace: slow; volume: quiet.
*Note:* Narrator: he nods as if told a price. 'Forge is shut.' flat, final.

```
[grief taken like a blow, quietly] Forge is shut.
```
Subtitle: Forge is shut.

### 34. `dlg.brannoc.nell_lie.0.p1.wav`

*Where:* dialogue.json brannoc/nell_lie#0; part 2 of 4: narrator: The hammer comes down. / **brannoc: Low Kiln, then. Good.** / narrator: And again. / brannoc: Aunt'll feed her up. She's thin.
*Played:* relief, fragile; doing: believes your lie; pace: slow; volume: quiet.
*Note:* Narrator for each hammer stroke. 'Low Kiln, then. Good.' relief. 'Aunt'll feed her up. She's thin.' tender, which makes the lie worse.

```
[relief, fragile, quietly] Low Kiln, then. Good.
```
Subtitle: Low Kiln, then. Good.

### 35. `dlg.brannoc.nell_lie.0.p3.wav`

*Where:* dialogue.json brannoc/nell_lie#0; part 4 of 4: narrator: The hammer comes down. / brannoc: Low Kiln, then. Good. / narrator: And again. / **brannoc: Aunt'll feed her up. She's thin.**
*Played:* relief, fragile; doing: believes your lie; pace: slow; volume: quiet.
*Note:* Narrator for each hammer stroke. 'Low Kiln, then. Good.' relief. 'Aunt'll feed her up. She's thin.' tender, which makes the lie worse.

```
[relief, fragile, quietly] Aunt'll feed her up. She's thin.
```
Subtitle: Aunt'll feed her up. She's thin.

### 36. `dlg.brannoc.nell_look.0.p0.wav`

*Where:* dialogue.json brannoc/nell_look#0; part 1 of 3: **brannoc: Didn't look.** / narrator: The hammer comes down. / brannoc: No. ...Nobody looks.
*Played:* bitter, flat; doing: nobody looks; pace: slow; volume: quiet.
*Note:* Repeats it flat. Narrator for the hammer. 'No.' Then quiet bitterness: 'Nobody looks.'

```
[bitter, flat, quietly] Didn't look.
```
Subtitle: Didn't look.

### 37. `dlg.brannoc.nell_look.0.p2.wav`

*Where:* dialogue.json brannoc/nell_look#0; part 3 of 3: brannoc: Didn't look. / narrator: The hammer comes down. / **brannoc: No. ...Nobody looks.**
*Played:* bitter, flat; doing: nobody looks; pace: slow; volume: quiet.
*Note:* Repeats it flat. Narrator for the hammer. 'No.' Then quiet bitterness: 'Nobody looks.'

```
[bitter, flat, quietly] No. ...Nobody looks.
```
Subtitle: No. ...Nobody looks.

## Said in passing

### 38. `bark.brannoc.day.0.wav`

*Where:* npcs.json brannoc.barks[0]
*Played:* gruff; pace: slow; volume: level.

```
[gruff] Good steel's not cheap. Nor's a good pelt.
```
Subtitle: Good steel's not cheap. Nor's a good pelt.

### 39. `bark.brannoc.day.1.wav`

*Where:* npcs.json brannoc.barks[1]
*Played:* gruff; pace: slow; volume: level.

```
[gruff] Mind the sparks.
```
Subtitle: Mind the sparks.

### 40. `bark.brannoc.day.2.wav`

*Where:* npcs.json brannoc.barks[2]
*Played:* gruff; pace: slow; volume: level.

```
[gruff] Bring me hides. I'll make you something worth wearing.
```
Subtitle: Bring me hides. I'll make you something worth wearing.

### 41. `bark.brannoc.day.3.wav`

*Where:* npcs.json brannoc.barks[3]
*Played:* gruff; pace: slow; volume: level.

```
[gruff] Hit a man with this and he stays hit.
```
Subtitle: Hit a man with this and he stays hit.

### 42. `bark.brannoc.night.0.wav`

*Where:* npcs.json brannoc.nightBarks[0]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] Forge is banked. First light.
```
Subtitle: Forge is banked. First light.

### 43. `bark.brannoc.night.1.wav`

*Where:* npcs.json brannoc.nightBarks[1]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] Arm aches worse at night. Old iron does.
```
Subtitle: Arm aches worse at night. Old iron does.

### 44. `bark.brannoc.night.2.wav`

*Where:* npcs.json brannoc.nightBarks[2]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] Fire keeps me company.
```
Subtitle: Fire keeps me company.

### 45. `bark.brannoc.night.3.wav`

*Where:* npcs.json brannoc.nightBarks[3]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] Banked. Go away.
```
Subtitle: Banked. Go away.

### 46. `bark.brannoc.night.4.wav`

*Where:* npcs.json brannoc.nightBarks[4]
*Played:* tired; pace: slow; volume: quiet.

```
[tired, quietly] Two on the rack. Leave them.
```
Subtitle: Two on the rack. Leave them.

### 47. `bark.brannoc.said.0.wav`

*Where:* npcs.json brannoc.said[0]
*Played:* flat, hopeful; doing: Nell on the road; pace: slow; volume: level.
*Note:* Few words; the hope hidden in the counting.

```
[flat, hopeful] Low Kiln's three days. She'll be there by now.
```
Subtitle: Low Kiln's three days. She'll be there by now.

### 48. `bark.brannoc.said.1.wav`

*Where:* npcs.json brannoc.said[1]
*Played:* flat; doing: the irons he made; pace: slow; volume: quiet.
*Hides:* what the irons were for
*Note:* The second 'Twelve.' quieter.

```
[flat, quietly] Twelve, I made.
```
Subtitle: Twelve, I made.

### 49. `bark.brannoc.said.2.wav`

*Where:* npcs.json brannoc.said[2]
*Played:* gruff, closed; doing: keep out; pace: slow; volume: level.
*Note:* A door shut.

```
[gruff, closed] Forge is lit. Don't come in.
```
Subtitle: Forge is lit. Don't come in.


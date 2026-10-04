# Townsman, old: ElevenLabs packet

Voice id in the game: `folk_m2`. 43 takes to record (2,470 characters; about 7,410 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

An old countryman in his seventies from the West Country of England with a creaky, slow voice and a broad rural accent. Wry and weary.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Townsman, old`. Never describe a voice as sounding like a real person.

```
Native English (British, West Country). Male, 70s. Studio quality. Persona: an old West Country countryman. An old countryman in his seventies from the West Country of England with a creaky, slow voice and a broad rural accent. Wry and weary. Broad West Country accent. No reverb or effects.
```

Preview text:

```
My gran swore the Warden was a story to keep children off the ford. Morning.
```

In the Voice Library instead: search for *West Country*, *male*, *70*, and listen for this: An old countryman in his seventies from the West Country of England with a creaky, slow voice and a broad rural accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/folk.1.m.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice folk_m2
```

## Saying the names

The text to paste already respells these; keep the respelling: Maeca as *Mayka*, Redcowl as *Red-cowl*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Passers-by

### 1. `folk.1.m.wav`

*Where:* folk.json lines[1]
*Played:* irritable warning; pace: measured; volume: level.

```
[irritable warning] Mind the cart.
```
Subtitle: Mind the cart.

### 2. `folk.3.m.wav`

*Where:* folk.json lines[3]
*Played:* grumbling; pace: measured; volume: level.

```
[grumbling] Bread's up again. It's always up.
```
Subtitle: Bread's up again. It's always up.

### 3. `folk.5.m.wav`

*Where:* folk.json lines[5]
*Played:* suspicious; pace: measured; volume: level.

```
[suspicious] You're not from the Waystation.
```
Subtitle: You're not from the Waystation.

### 4. `folk.7.m.wav`

*Where:* folk.json lines[7]
*Played:* sharp, territorial; pace: measured; volume: level.

```
[sharp, territorial] Don't stand in the well-queue unless you're drawing.
```
Subtitle: Don't stand in the well-queue unless you're drawing.

### 5. `folk.9.m.wav`

*Where:* folk.json lines[9]
*Played:* amused gossip; pace: measured; volume: level.

```
[amused gossip] Chid rang the bell twice this morning. Nobody's told him once does it.
```
Subtitle: Chid rang the bell twice this morning. Nobody's told him once does it.

### 6. `folk.11.m.wav`

*Where:* folk.json lines[11]
*Played:* kindly warning; pace: measured; volume: quiet.

```
[kindly warning, quietly] Evening. Get indoors soon.
```
Subtitle: Evening. Get indoors soon.

### 7. `folk.13.m.wav`

*Where:* folk.json lines[13]
*Played:* quiet warning; pace: measured; volume: quiet.

```
[quiet warning, quietly] Lamps are lit. Stay where they reach.
```
Subtitle: Lamps are lit. Stay where they reach.

### 8. `folk.15.m.wav`

*Where:* folk.json lines[15]
*Played:* sour, then grudging; pace: measured; volume: level.

```
[sour, then grudging] Shit weather, shit road, shit luck. Morning.
```
Subtitle: Shit weather, shit road, shit luck. Morning.

### 9. `folk.17.m.wav`

*Where:* folk.json lines[17]
*Played:* scornful joke; pace: measured; volume: level.

```
[scornful joke] Holloway couldn't find his own arse with a lantern and a map.
```
Subtitle: Holloway couldn't find his own arse with a lantern and a map.

### 10. `folk.19.m.wav`

*Where:* folk.json lines[19]
*Played:* dry joke; pace: measured; volume: level.

```
[dry joke] If the wolves don't get you, Rook's stew will.
```
Subtitle: If the wolves don't get you, Rook's stew will.

### 11. `folk.21.m.wav`

*Where:* folk.json lines[21]
*Played:* fond, wry; pace: measured; volume: level.

```
[fond, wry] Sella took three coppers off me for a smile. Worth four.
```
Subtitle: Sella took three coppers off me for a smile. Worth four.

### 12. `folk.23.m.wav`

*Where:* folk.json lines[23]
*Played:* rueful; pace: measured; volume: quiet.

```
[rueful, quietly] Somebody's having a better night than me. Rook's walls are thin.
```
Subtitle: Somebody's having a better night than me. Rook's walls are thin.

### 13. `folk.25.m.wav`

*Where:* folk.json lines[25]
*Played:* sad, respectful; pace: measured; volume: level.

```
[sad, respectful] The Captain carried the front of Aldo's coffin himself. Wouldn't let anyone spell him.
```
Subtitle: The Captain carried the front of Aldo's coffin himself. Wouldn't let anyone spell him.

### 14. `folk.27.m.wav`

*Where:* folk.json lines[27]
*Played:* blunt, apologetic; pace: measured; volume: level.

```
[blunt, apologetic] You smell like the dead. No offence. Everybody does, lately.
```
Subtitle: You smell like the dead. No offence. Everybody does, lately.

### 15. `folk.29.m.wav`

*Where:* folk.json lines[29]
*Played:* curious, hopeful; pace: measured; volume: level.

```
[curious, hopeful] They say the Ford-Warden's down. Was that you?
```
Subtitle: They say the Ford-Warden's down. Was that you?

### 16. `folk.31.m.wav`

*Where:* folk.json lines[31]
*Played:* outraged; pace: measured; volume: level.

```
[outraged] Wolves took the Oswin goats. In daylight!
```
Subtitle: Wolves took the Oswin goats. In daylight!

### 17. `folk.33.m.wav`

*Where:* folk.json lines[33]
*Played:* uneasy, knowing; pace: measured; volume: level.

```
[uneasy, knowing] Wolves don't behave like that. Not healthy ones.
```
Subtitle: Wolves don't behave like that. Not healthy ones.

### 18. `folk.35.m.wav`

*Where:* folk.json lines[35]
*Played:* pitying; pace: measured; volume: level.

```
[pitying] Tam's farm was hit. Poor lad's sleeping in the Watch-house.
```
Subtitle: Tam's farm was hit. Poor lad's sleeping in the Watch-house.

### 19. `folk.37.m.wav`

*Where:* folk.json lines[37]
*Played:* uneasy; pace: measured; volume: level.

```
[uneasy] Quiet out east now. Too quiet, Mayka says.
```
Subtitle: Quiet out east now. Too quiet, Maeca says.

### 20. `folk.39.m.wav`

*Where:* folk.json lines[39]
*Played:* wary, half joking; pace: measured; volume: level.

```
[wary, half joking] Wolf-friend. Keep them out of my hen-house, that's all I ask.
```
Subtitle: Wolf-friend. Keep them out of my hen-house, that's all I ask.

### 21. `folk.41.m.wav`

*Where:* folk.json lines[41]
*Played:* astonished; pace: measured; volume: level.

```
[astonished] Wenna's been smiling. Wenna. Smiling.
```
Subtitle: Wenna's been smiling. Wenna. Smiling.

### 22. `folk.43.m.wav`

*Where:* folk.json lines[43]
*Played:* accusing; pace: measured; volume: level.

```
[accusing] Heard somebody sold the Dig to Pell. Heard it was you.
```
Subtitle: Heard somebody sold the Dig to Pell. Heard it was you.

### 23. `folk.45.m.wav`

*Where:* folk.json lines[45]
*Played:* pitying; pace: measured; volume: level.

```
[pitying] Harlan's not slept since the wagons went.
```
Subtitle: Harlan's not slept since the wagons went.

### 24. `folk.47.m.wav`

*Where:* folk.json lines[47]
*Played:* fearful gossip; pace: measured; volume: level.

```
[fearful gossip] Kerchiefs, they say. Red rags and no mercy.
```
Subtitle: Kerchiefs, they say. Red rags and no mercy.

### 25. `folk.49.m.wav`

*Where:* folk.json lines[49]
*Played:* pitying; pace: measured; volume: level.

```
[pitying] Those poor teamsters. Harlan hasn't opened the shutters.
```
Subtitle: Those poor teamsters. Harlan hasn't opened the shutters.

### 26. `folk.51.m.wav`

*Where:* folk.json lines[51]
*Played:* insinuating; pace: measured; volume: level.

```
[insinuating] Pell's been generous lately. With you, especially.
```
Subtitle: Pell's been generous lately. With you, especially.

### 27. `folk.53.m.wav`

*Where:* folk.json lines[53]
*Played:* grumbling; pace: measured; volume: level.

```
[grumbling] Salt's doubled. The Kerchiefs are bleeding the road dry.
```
Subtitle: Salt's doubled. The Kerchiefs are bleeding the road dry.

### 28. `folk.55.m.wav`

*Where:* folk.json lines[55]
*Played:* sceptical; pace: measured; volume: level.

```
[sceptical] Red-cowl dead. I'll believe it when I see the hat.
```
Subtitle: Redcowl dead. I'll believe it when I see the hat.

### 29. `folk.57.m.wav`

*Where:* folk.json lines[57]
*Played:* accusing; pace: measured; volume: level.

```
[accusing] That's Coyle cloth on your back, isn't it.
```
Subtitle: That's Coyle cloth on your back, isn't it.

### 30. `folk.59.m.wav`

*Where:* folk.json lines[59]
*Played:* scandalised; pace: measured; volume: level.

```
[scandalised] Wanted, they said at the Watch. Wanted! You've a nerve walking here.
```
Subtitle: Wanted, they said at the Watch. Wanted! You've a nerve walking here.

### 31. `folk.63.m.wav`

*Where:* folk.json lines[63]
*Played:* teasing; pace: measured; volume: level.

```
[teasing] Chid says you died. You look well on it.
```
Subtitle: Chid says you died. You look well on it.

### 32. `folk.77.m.wav`

*Where:* folk.json lines[77]
*Played:* relieved gossip; pace: measured; volume: level.

```
[relieved gossip] Pack tore Tam's farm to bits. His Pa was in town, thank God. Somebody fetched him in.
```
Subtitle: Pack tore Tam's farm to bits. His Pa was in town, thank God. Somebody fetched him in.

### 33. `folk.79.m.wav`

*Where:* folk.json lines[79]
*Played:* frightened whisper; pace: measured; volume: quiet.

```
[frightened whisper, quietly] That's the one. Don't look. DON'T look.
```
Subtitle: That's the one. Don't look. DON'T look.

### 34. `folk.85.m.wav`

*Where:* folk.json lines[85]
*Played:* terrified politeness; pace: measured; volume: quiet.

```
[terrified politeness, quietly] Evening. Please don't hit me. Evening.
```
Subtitle: Evening. Please don't hit me. Evening.

### 35. `folk.87.m.wav`

*Where:* folk.json lines[87]
*Played:* sad gossip; pace: measured; volume: level.

```
[sad gossip] Harlan stood at the graves the whole afternoon. Didn't say a word. Didn't take his hat off, either. Forgot he had it on.
```
Subtitle: Harlan stood at the graves the whole afternoon. Didn't say a word. Didn't take his hat off, either. Forgot he had it on.

### 36. `folk.89.m.wav`

*Where:* folk.json lines[89]
*Played:* bawdy gossip; pace: measured; volume: quiet.

```
[bawdy gossip, quietly] Sella's got a new customer, the walls are saying. The walls are very specific.
```
Subtitle: Sella's got a new customer, the walls are saying. The walls are very specific.

### 37. `folk.93.m.wav`

*Where:* folk.json lines[93]
*Played:* gruff kindness; pace: measured; volume: quiet.

```
[gruff kindness, quietly] If you're going to throw up, do it in the trough. The horses have seen worse.
```
Subtitle: If you're going to throw up, do it in the trough. The horses have seen worse.

### 38. `folk.95.m.wav`

*Where:* folk.json lines[95]
*Played:* amused gossip; pace: measured; volume: level.

```
[amused gossip] Sella was singing on the stairs this morning. Sella. Singing. Somebody's in trouble.
```
Subtitle: Sella was singing on the stairs this morning. Sella. Singing. Somebody's in trouble.

### 39. `folk.97.m.wav`

*Where:* folk.json lines[97]
*Played:* tender; pace: measured; volume: level.

```
[tender] They buried Brannoc's girl behind the shrine. Chid sang. Chid can't sing. Nobody minded.
```
Subtitle: They buried Brannoc's girl behind the shrine. Chid sang. Chid can't sing. Nobody minded.

### 40. `folk.99.m.wav`

*Where:* folk.json lines[99]
*Played:* grumbling; pace: measured; volume: level.

```
[grumbling] Jessop from the toll owes me four coppers and a ladder. Gone south, they say. Took neither.
```
Subtitle: Jessop from the toll owes me four coppers and a ladder. Gone south, they say. Took neither.

### 41. `folk.103.m.wav`

*Where:* folk.json lines[103]
*Played:* gossip, a little sad; pace: measured; volume: level.

```
[gossip, a little sad] Jory Coyle's stopped calling his uncle Uncle. Calls him Mister Coyle in the shop, in front of customers.
```
Subtitle: Jory Coyle's stopped calling his uncle Uncle. Calls him Mister Coyle in the shop, in front of customers.

### 42. `folk.105.m.wav`

*Where:* folk.json lines[105]
*Played:* scornful; pace: measured; volume: level.

```
[scornful] Pell Varrow's gone south on a horse he hadn't paid for. Course he hadn't.
```
Subtitle: Pell Varrow's gone south on a horse he hadn't paid for. Course he hadn't.

### 43. `folk.107.m.wav`

*Where:* folk.json lines[107]
*Played:* gossip, matter-of-fact; doing: a death in town; pace: measured; volume: level.

```
[gossip, matter-of-fact] Old Oswin's gone to the Morrow. Sat down in his chair after his dinner and went.
```
Subtitle: Old Oswin's gone to the Morrow. Sat down in his chair after his dinner and went.


# A Watchman at the gate: ElevenLabs packet

Voice id in the game: `guard`. 22 takes to record (834 characters; about 2,502 credits at three tries a line). Status: **draft, except the 2 takes marked LOCKED FOR RECORDING** (the story lead, 2026-10-11): record those now.

**2 takes are LOCKED FOR RECORDING** (marked below).

**Hold 9 of these** (marked HOLD below, with why); the rest can be recorded now.

## Who they are

**The Waystation's watchmen.** Tired men with colds; they say to each other what they always say and watch the survivor too long after.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU A Watchman at the gate`. Never describe a voice as sounding like a real person.

```
Native English (British, northern English). Male, 30s. Studio quality. Persona: a northern town guard. A tired town guard in his thirties with a plain, gruff baritone and a flat northern English accent. Bored and matter-of-fact. Broad northern English accent. No reverb or effects.
```

Preview text:

```
Keep your weapon sheathed in town. East road's that way. Mind the wolves.
```

In the Voice Library instead: search for *northern English*, *male*, *30*, and listen for this: A tired town guard in his thirties with a plain, gruff baritone and a flat northern English accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.cin_first_light.dawn.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice guard
```

## Saying the names

The text to paste already respells these; keep the respelling: Maeca as *Mayka*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Cinematic: first light

### 1. `dlg.cin_first_light.dawn.0.wav`  **LOCKED FOR RECORDING**

*The same words are also* `guard.0.wav`*: record once; the importer copies the take.*
*Where:* dialogue.json cin_first_light/dawn#0
*Played:* bored, matter-of-fact; doing: a guard at dawn; pace: measured; volume: level.
*Length:* the cut is timed to it: 2.4–3.0 s, first sound to last word.

```
[bored, matter-of-fact] Dawn arrivals. We don't get many that live.
```
Subtitle: Dawn arrivals. We don't get many that live.

## Scenes: the clock (dusk, night, getting up)

### 2. `say.9790cd22614c.wav`  **LOCKED FOR RECORDING**

*Where:* godot/logic/Play/Journey.Day.cs
*Played:* plain; doing: calls the town in at dusk, as every evening; pace: measured; volume: raised.
*Note:* Called from the gate, out over the road: the Order's evening call, worn smooth by use. Two sentences at the same pitch, no tune in it, no warmth or warning. (The survivor's mother said it small, at a door; he does not know that.)

```
[plain, loudly] Lamps are lit. Stay where they reach.
```
Subtitle: Lamps are lit. Stay where they reach.

## Conversations: Scene_count_right

### 3. `dlg.scene_count_right.ten.0.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_count_right/ten#0

```
...Nine.
```
Subtitle: ...Nine.

### 4. `dlg.scene_count_right.ten.1.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_count_right/ten#1

```
...Ten.
```
Subtitle: ...Ten.

### 5. `dlg.scene_count_right.take.0.p1.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_count_right/take#0; part 2 of 2: narrator: He looks at Maeca, and his voice goes up, and he brings it down. / **guard: Maeca. ...You'll come with us.**

```
Mayka. ...You'll come with us.
```
Subtitle: Maeca. ...You'll come with us.

## Conversations: Scene_one_in

### 6. `dlg.scene_one_in.tolley.0.p1.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_one_in/tolley#0; part 2 of 4: narrator: He doesn't look away from the road. / **guard: He's been there since the bell. Just stood. Not knocking. Not anything.** / narrator: His voice goes. / guard: Captain never once barred it on anybody.

```
He's been there since the bell. Just stood. Not knocking. Not anything.
```
Subtitle: He's been there since the bell. Just stood. Not knocking. Not anything.

### 7. `dlg.scene_one_in.tolley.0.p3.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_one_in/tolley#0; part 4 of 4: narrator: He doesn't look away from the road. / guard: He's been there since the bell. Just stood. Not knocking. Not anything. / narrator: His voice goes. / **guard: Captain never once barred it on anybody.**

```
Captain never once barred it on anybody.
```
Subtitle: Captain never once barred it on anybody.

### 8. `dlg.scene_one_in.open.0.p1.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_one_in/open#0; part 2 of 2: narrator: He comes down off the wall and lifts the bar himself. / **guard: ...Somebody's still out.**

```
...Somebody's still out.
```
Subtitle: ...Somebody's still out.

### 9. `dlg.scene_one_in.in_tolley.0.p1.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_one_in/in_tolley#0; part 2 of 2: narrator: He holds the gate for you, and doesn't look at him. / **guard: ...One in.**

```
...One in.
```
Subtitle: ...One in.

## Conversations: Scene_his_table

### 10. `dlg.scene_his_table.door.0.p0.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_his_table/door#0; part 1 of 3: **guard: Somebody's got to go through his table. The lads won't, and I can't.** / narrator: He holds the Watch-house door open, and doesn't go in. / guard: He said you were in his count.

```
Somebody's got to go through his table. The lads won't, and I can't.
```
Subtitle: Somebody's got to go through his table. The lads won't, and I can't.

### 11. `dlg.scene_his_table.door.0.p2.wav`  HOLD: Act 2: held until the editor and the owner pass it

*Where:* dialogue.json scene_his_table/door#0; part 3 of 3: guard: Somebody's got to go through his table. The lads won't, and I can't. / narrator: He holds the Watch-house door open, and doesn't go in. / **guard: He said you were in his count.**

```
He said you were in his count.
```
Subtitle: He said you were in his count.

## Said in passing

### 12. `guard.1.wav`

*Where:* npcs.json guards[1]
*Played:* bored, matter-of-fact; pace: measured; volume: level.

```
[bored, matter-of-fact] Keep your weapon sheathed in town.
```
Subtitle: Keep your weapon sheathed in town.

### 13. `guard.2.wav`

*Where:* npcs.json guards[2]
*Played:* bored, matter-of-fact; pace: measured; volume: level.

```
[bored, matter-of-fact] East road. Mind the wolves.
```
Subtitle: East road. Mind the wolves.

## Passers-by

### 14. `folk.71.m.wav`

*Where:* folk.json lines[71]
*Played:* curt; pace: measured; volume: level.

```
[curt] All quiet. Keep it that way.
```
Subtitle: All quiet. Keep it that way.

### 15. `folk.72.m.wav`

*Where:* folk.json lines[72]
*Played:* curt; pace: measured; volume: level.

```
[curt] Gates are shut till dawn.
```
Subtitle: Gates are shut till dawn.

### 16. `folk.73.m.wav`

*Where:* folk.json lines[73]
*Played:* curt; pace: measured; volume: level.

```
[curt] Walk on, traveler.
```
Subtitle: Walk on, traveler.

### 17. `folk.74.m.wav`

*Where:* folk.json lines[74]
*Played:* rough; pace: measured; volume: level.

```
[rough] Piss off home. It's past curfew.
```
Subtitle: Piss off home. It's past curfew.

### 18. `folk.75.m.wav`

*Where:* folk.json lines[75]
*Played:* threatening; pace: measured; volume: level.

```
[threatening] Keep that blade sheathed or I'll sheathe it for you.
```
Subtitle: Keep that blade sheathed or I'll sheathe it for you.

### 19. `folk.76.m.wav`

*Where:* folk.json lines[76]
*Played:* tired; pace: measured; volume: level.

```
[tired] Captain's doubled the gate. Wolves.
```
Subtitle: Captain's doubled the gate. Wolves.

### 20. `folk.81.m.wav`

*Where:* folk.json lines[81]
*Played:* uneasy; pace: measured; volume: level.

```
[uneasy] Captain says to let you be. Captain says it like he's not sure.
```
Subtitle: Captain says to let you be. Captain says it like he's not sure.

### 21. `folk.94.m.wav`

*Where:* folk.json lines[94]
*Played:* rough threat; pace: measured; volume: level.

```
[rough threat] Indoors, before I find a reason. I'm good at finding reasons.
```
Subtitle: Indoors, before I find a reason. I'm good at finding reasons.

### 22. `folk.106.m.wav`

*Where:* folk.json lines[106]
*Played:* uneasy; pace: measured; volume: level.

```
[uneasy] Captain's had a letter with a silver seal. Hasn't said a word since. Not that he says many.
```
Subtitle: Captain's had a letter with a silver seal. Hasn't said a word since. Not that he says many.


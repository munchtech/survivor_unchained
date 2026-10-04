# Townswoman, young: ElevenLabs packet

Voice id in the game: `folk_f2`. 47 takes to record (3,056 characters; about 9,168 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

A young woman from the West Country of England with a bright, quick voice and a rural West Country accent. Sharp-tongued and amused.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Townswoman, young`. Never describe a voice as sounding like a real person.

```
Native English (British, West Country). Female, 20s. Studio quality. Persona: a West Country countrywoman. A young woman from the West Country of England with a bright, quick voice and a rural West Country accent. Sharp-tongued and amused. Thick West Country accent. No reverb or effects.
```

Preview text:

```
Two coppers for a turnip. Two! You're not from the Waystation, are you?
```

In the Voice Library instead: search for *West Country*, *female*, *20*, and listen for this: A young woman from the West Country of England with a bright, quick voice and a rural West Country accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/folk.0.f.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice folk_f2
```

## Saying the names

The text to paste already respells these; keep the respelling: Penhale as *Pen-hale*, Redcowl as *Red-cowl*, Vonnra as *Vonra*.

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Passers-by

### 1. `folk.0.f.wav`

*Where:* folk.json lines[0]
*Played:* gruff greeting; pace: measured; volume: level.

```
[gruff greeting] Morning.
```
Subtitle: Morning.

### 2. `folk.2.f.wav`

*Where:* folk.json lines[2]
*Played:* outraged, haggling; pace: measured; volume: level.

```
[outraged, haggling] Two coppers for a turnip. Two!
```
Subtitle: Two coppers for a turnip. Two!

### 3. `folk.4.f.wav`

*Where:* folk.json lines[4]
*Played:* wry, weathered; pace: measured; volume: level.

```
[wry, weathered] Rain by evening, my knee says.
```
Subtitle: Rain by evening, my knee says.

### 4. `folk.6.f.wav`

*Where:* folk.json lines[6]
*Played:* weary; pace: measured; volume: level.

```
[weary] Another one off the road. They keep coming.
```
Subtitle: Another one off the road. They keep coming.

### 5. `folk.8.f.wav`

*Where:* folk.json lines[8]
*Played:* squeamish; pace: measured; volume: level.

```
[squeamish] Is that blood? Don't tell me.
```
Subtitle: Is that blood? Don't tell me.

### 6. `folk.10.f.wav`

*Where:* folk.json lines[10]
*Played:* dry joke; pace: measured; volume: level.

```
[dry joke] The Flagon's ale is half water. The water's half ale.
```
Subtitle: The Flagon's ale is half water. The water's half ale.

### 7. `folk.12.f.wav`

*Where:* folk.json lines[12]
*Played:* uneasy; pace: measured; volume: quiet.

```
[uneasy, quietly] Nothing good walks about after dark.
```
Subtitle: Nothing good walks about after dark.

### 8. `folk.14.f.wav`

*Where:* folk.json lines[14]
*Played:* startled, then deflated; pace: measured; volume: quiet.

```
[startled, then deflated, quietly] Is that the watch? Oh. You.
```
Subtitle: Is that the watch? Oh. You.

### 9. `folk.16.f.wav`

*Where:* folk.json lines[16]
*Played:* grumbling; pace: measured; volume: level.

```
[grumbling] Bloody wolves. Bloody Watch. Bloody bread.
```
Subtitle: Bloody wolves. Bloody Watch. Bloody bread.

### 10. `folk.18.f.wav`

*Where:* folk.json lines[18]
*Played:* sly gossip; pace: measured; volume: level.

```
[sly gossip] Pell counts his coin in bed. Alone, obviously.
```
Subtitle: Pell counts his coin in bed. Alone, obviously.

### 11. `folk.20.f.wav`

*Where:* folk.json lines[20]
*Played:* bitter joke; pace: measured; volume: level.

```
[bitter joke] My husband went out to the Verge a month back. Some days I hope he stays out.
```
Subtitle: My husband went out to the Verge a month back. Some days I hope he stays out.

### 12. `folk.22.f.wav`

*Where:* folk.json lines[22]
*Played:* knowing gossip; pace: measured; volume: level.

```
[knowing gossip] Rook's upstairs rooms go by the hour now. Don't ask how I know.
```
Subtitle: Rook's upstairs rooms go by the hour now. Don't ask how I know.

### 13. `folk.24.f.wav`

*Where:* folk.json lines[24]
*Played:* grim humour; pace: measured; volume: level.

```
[grim humour] Buried two this week. The ground's full and the priest's a fool. Says so himself.
```
Subtitle: Buried two this week. The ground's full and the priest's a fool. Says so himself.

### 14. `folk.26.f.wav`

*Where:* folk.json lines[26]
*Played:* weary contempt; pace: measured; volume: level.

```
[weary contempt] Keep walking, hero. I've had my fill of heroes.
```
Subtitle: Keep walking, hero. I've had my fill of heroes.

### 15. `folk.28.f.wav`

*Where:* folk.json lines[28]
*Played:* impressed, wary; pace: measured; volume: level.

```
[impressed, wary] Came up the Low Ford at night? You're brave or daft.
```
Subtitle: Came up the Low Ford at night? You're brave or daft.

### 16. `folk.30.f.wav`

*Where:* folk.json lines[30]
*Played:* wondering; pace: measured; volume: level.

```
[wondering] My gran swore the Warden was a story to keep children off the ford.
```
Subtitle: My gran swore the Warden was a story to keep children off the ford.

### 17. `folk.32.f.wav`

*Where:* folk.json lines[32]
*Played:* practical; pace: measured; volume: level.

```
[practical] Holloway's paying five a pelt, if you've the stomach.
```
Subtitle: Holloway's paying five a pelt, if you've the stomach.

### 18. `folk.34.f.wav`

*Where:* folk.json lines[34]
*Played:* frightened; pace: measured; volume: level.

```
[frightened] Wolves at the gate last night. At the gate!
```
Subtitle: Wolves at the gate last night. At the gate!

### 19. `folk.36.f.wav`

*Where:* folk.json lines[36]
*Played:* grateful; pace: measured; volume: level.

```
[grateful] You're the one who cleared the wolves. My boy can walk to the mill again.
```
Subtitle: You're the one who cleared the wolves. My boy can walk to the mill again.

### 20. `folk.38.f.wav`

*Where:* folk.json lines[38]
*Played:* amazed; pace: measured; volume: level.

```
[amazed] They say wolves walk beside you out there. I'd not believe it but for Maeca's face.
```
Subtitle: They say wolves walk beside you out there. I'd not believe it but for Maeca's face.

### 21. `folk.40.f.wav`

*Where:* folk.json lines[40]
*Played:* grudging, hopeful; pace: measured; volume: level.

```
[grudging, hopeful] Tam says the stream runs clear again. Tam says a lot, but still.
```
Subtitle: Tam says the stream runs clear again. Tam says a lot, but still.

### 22. `folk.42.f.wav`

*Where:* folk.json lines[42]
*Played:* suspicious, dry; pace: measured; volume: level.

```
[suspicious, dry] Pell's diggers moved their pipe. Pell Varrow, doing a kindness. Check your purse.
```
Subtitle: Pell's diggers moved their pipe. Pell Varrow, doing a kindness. Check your purse.

### 23. `folk.44.f.wav`

*Where:* folk.json lines[44]
*Played:* accusing, amused; pace: measured; volume: level.

```
[accusing, amused] You lied to Holloway about the wolves. Everybody knows. He does too.
```
Subtitle: You lied to Holloway about the wolves. Everybody knows. He does too.

### 24. `folk.46.f.wav`

*Where:* folk.json lines[46]
*Played:* sad gossip; pace: measured; volume: level.

```
[sad gossip] The Coyle wagons had the Oswin girl's wedding cloth on them.
```
Subtitle: The Coyle wagons had the Oswin girl's wedding cloth on them.

### 25. `folk.48.f.wav`

*Where:* folk.json lines[48]
*Played:* joyful; pace: measured; volume: level.

```
[joyful] Jory Coyle's home! Harlan wept in the street, I saw it.
```
Subtitle: Jory Coyle's home! Harlan wept in the street, I saw it.

### 26. `folk.50.f.wav`

*Where:* folk.json lines[50]
*Played:* disgusted; pace: measured; volume: level.

```
[disgusted] Pell Varrow, selling his own neighbours. I bought eggs from that man.
```
Subtitle: Pell Varrow, selling his own neighbours. I bought eggs from that man.

### 27. `folk.52.f.wav`

*Where:* folk.json lines[52]
*Played:* grumbling; pace: measured; volume: level.

```
[grumbling] Kerchiefs hit the Pen-hale farm again. Prices'll climb, you watch.
```
Subtitle: Kerchiefs hit the Penhale farm again. Prices'll climb, you watch.

### 28. `folk.54.f.wav`

*Where:* folk.json lines[54]
*Played:* awed, uneasy; pace: measured; volume: level.

```
[awed, uneasy] The Roost burned, they say. You could see the smoke from the wall.
```
Subtitle: The Roost burned, they say. You could see the smoke from the wall.

### 29. `folk.56.f.wav`

*Where:* folk.json lines[56]
*Played:* incredulous; pace: measured; volume: level.

```
[incredulous] You made a deal with Red-cowl? With Red-cowl?
```
Subtitle: You made a deal with Redcowl? With Redcowl?

### 30. `folk.58.f.wav`

*Where:* folk.json lines[58]
*Played:* admiring; pace: measured; volume: level.

```
[admiring] Harlan says you brought every crate home. Every one.
```
Subtitle: Harlan says you brought every crate home. Every one.

### 31. `folk.60.f.wav`

*Where:* folk.json lines[60]
*Played:* frightened, hushed; pace: measured; volume: quiet.

```
[frightened, hushed, quietly] Did you feel the ground go, last night? Like something rolling over.
```
Subtitle: Did you feel the ground go, last night? Like something rolling over.

### 32. `folk.62.f.wav`

*Where:* folk.json lines[62]
*Played:* curious; pace: measured; volume: level.

```
[curious] Vonra read your fortune? She never reads for free.
```
Subtitle: Vonnra read your fortune? She never reads for free.

### 33. `folk.64.f.wav`

*Where:* folk.json lines[64]
*Played:* relieved, wondering; pace: measured; volume: level.

```
[relieved, wondering] They carried you in past my door. I thought that was you done.
```
Subtitle: They carried you in past my door. I thought that was you done.

### 34. `folk.78.f.wav`

*Where:* folk.json lines[78]
*Played:* scandalised gossip; pace: measured; volume: level.

```
[scandalised gossip] Chid's not aged a day since my mam was a girl. Says it's clean living. Have you SEEN where he lives?
```
Subtitle: Chid's not aged a day since my mam was a girl. Says it's clean living. Have you SEEN where he lives?

### 35. `folk.80.f.wav`

*Where:* folk.json lines[80]
*Played:* hushed, scared; pace: measured; volume: quiet.

```
[hushed, scared, quietly] They say that one's killed more than the fever year did.
```
Subtitle: They say that one's killed more than the fever year did.

### 36. `folk.82.f.wav`

*Where:* folk.json lines[82]
*Played:* approving; pace: measured; volume: level.

```
[approving] Is that a woman in all that? Good for her. Good for her.
```
Subtitle: Is that a woman in all that? Good for her. Good for her.

### 37. `folk.84.f.wav`

*Where:* folk.json lines[84]
*Played:* nervous warning; pace: measured; volume: level.

```
[nervous warning] Don't stand so near the thatch, spark-hands.
```
Subtitle: Don't stand so near the thatch, spark-hands.

### 38. `folk.86.f.wav`

*Where:* folk.json lines[86]
*Played:* horrified gossip; pace: measured; volume: level.

```
[horrified gossip] They say you could hear them from the ridge. The ones in the cages. They say it went on a while.
```
Subtitle: They say you could hear them from the ridge. The ones in the cages. They say it went on a while.

### 39. `folk.88.f.wav`

*Where:* folk.json lines[88]
*Played:* uneasy; pace: measured; volume: quiet.

```
[uneasy, quietly] You can still see their lamps up on the hill at night. Fewer every night.
```
Subtitle: You can still see their lamps up on the hill at night. Fewer every night.

### 40. `folk.90.f.wav`

*Where:* folk.json lines[90]
*Played:* dry joke; pace: measured; volume: level.

```
[dry joke] The Flagon's piss is cheaper than the Flagon's ale, and honestly? You can't tell.
```
Subtitle: The Flagon's piss is cheaper than the Flagon's ale, and honestly? You can't tell.

### 41. `folk.92.f.wav`

*Where:* folk.json lines[92]
*Played:* proud; pace: measured; volume: level.

```
[proud] Kerchief lad tried his luck with my daughter. She broke his nose with a bucket. Never been prouder.
```
Subtitle: Kerchief lad tried his luck with my daughter. She broke his nose with a bucket. Never been prouder.

### 42. `folk.96.f.wav`

*Where:* folk.json lines[96]
*Played:* quiet, sad; pace: measured; volume: quiet.

```
[quiet, sad, quietly] Brannoc's girl went south with Wat's cart a fortnight back. Quietest forge in the valley since, and that's saying something.
```
Subtitle: Brannoc's girl went south with Wat's cart a fortnight back. Quietest forge in the valley since, and that's saying something.

### 43. `folk.98.f.wav`

*Where:* folk.json lines[98]
*Played:* sad, pitying; pace: measured; volume: quiet.

```
[sad, pitying, quietly] Brannoc's stopping carters off the south road, asking after a red-haired girl. Nobody's had the heart to say they've not seen her.
```
Subtitle: Brannoc's stopping carters off the south road, asking after a red-haired girl. Nobody's had the heart to say they've not seen her.

### 44. `folk.100.f.wav`

*Where:* folk.json lines[100]
*Played:* uneasy; pace: measured; volume: level.

```
[uneasy] Penhales' dog won't go in the barn. Stands at the door and whines at the floor.
```
Subtitle: Penhales' dog won't go in the barn. Stands at the door and whines at the floor.

### 45. `folk.102.f.wav`

*Where:* folk.json lines[102]
*Played:* bitter; pace: measured; volume: level.

```
[bitter] Watch brought old Corran home from the ford post. Wrote him down a deserter, they did. Deserted to where, I ask you.
```
Subtitle: Watch brought old Corran home from the ford post. Wrote him down a deserter, they did. Deserted to where, I ask you.

### 46. `folk.104.f.wav`

*Where:* folk.json lines[104]
*Played:* scandalised whisper; pace: measured; volume: quiet.

```
[scandalised whisper, quietly] They say a cart went out of the east gate the night Pell vanished, and Vonra let it through without the toll. Vonra. Without the toll.
```
Subtitle: They say a cart went out of the east gate the night Pell vanished, and Vonnra let it through without the toll. Vonnra. Without the toll.

### 47. `folk.108.f.wav`

*Where:* folk.json lines[108]
*Played:* warning, kindly; doing: the lamps; pace: measured; volume: level.

```
[warning, kindly] No carter's been up the Old Road in a month. So who keeps bringing that one in?
```
Subtitle: No carter's been up the Old Road in a month. So who keeps bringing that one in?


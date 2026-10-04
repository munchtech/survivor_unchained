# Snib: ElevenLabs packet

Voice id in the game: `snib`. 15 takes to record (2,199 characters; about 6,597 credits at three tries a line). Status: **draft**, until the story lead (a7622ae77d19e31dc) checks every line and marks it final.

## Who they are

**Snib** (self-appointed foreman). Third person, panic, capitals on the stressed word, and the gag where he contradicts himself in the next breath ("The pump does not pump itself. It does, actually."). Loyal to "Boss" and terrified of him. *Casting:* small and fast, pitched up, a tinny lamp ring on stressed words.

## Casting the voice

In ElevenLabs: **Voices → Add a new voice → Voice Design**. Paste this as the description, and the preview text below as the text; generate, listen to the three, and regenerate until one is this person. Save it as `SU Snib`. Never describe a voice as sounding like a real person.

```
Native English (British, London). Male, ageless, not human. Studio quality. Persona: Goblin character. A small, nervous goblin-like creature with a high, thin, fast, squeaky voice and a rough London accent. Panicky and talking too fast, stressing odd words. Broad London accent. No reverb or effects.
```

Preview text:

```
Snib is FOREMAN. Snib says who goes past the pump, and Snib says nobody! The pump does not pump itself. It does, actually. But nobody!
```

In the Voice Library instead: search for *goblinish London*, *male*, *ageless*, and listen for this: A small, nervous goblin-like creature with a high, thin, fast, squeaky voice and a rough London accent. Use only voices whose library licence allows commercial use.

## Settings

- Model: **Eleven v4** (`eleven_v4`): the most emotive, and it follows the audio tags in square brackets.
- Stability: **45** (lower is more expressive and less steady; raise it if the voice drifts from line to line). Similarity: **75**.
- One line at a time, as below; regenerate until the read matches the direction. Two regenerations of the same text are free within two hours.
- Download as **WAV** (from History if the download button gives MP3; MP3 at 192 kbps also works). Save each take into one folder under the exact name given, e.g. `~/Downloads/su_vo/dlg.snib.first.0.wav`.

Then bring them into the game (it trims, levels, mixes and replaces the placeholders, and lists what is missing or wrong):

```
python tools/vo/import_takes.py ~/Downloads/su_vo --voice snib
```

## The lines

Each: what is going on, how it is played, then the text to paste (the bracketed tags are ElevenLabs audio tags: they are acted, not spoken), the words the subtitle shows (what the take must say), and the file name.

## Conversations: Snib

### 1. `dlg.snib.first.0.wav`

*Where:* dialogue.json snib/first#0
*Played:* panicky bluster; doing: stops you at the pump; pace: quick; volume: shout.
*Wants:* you gone, and to look important
*Note:* 'Oi! OI!' squeaky shouting. Self-important 'Foreman's orders!'. A pause; proud: 'Snib is the foreman.' Fussy. 'Snib does not know who.' then, deflating, 'Snib knows exactly who.' Then 'What do you want? Quick.'

```
[panicky bluster, shouting] Oi! OI! Surface-meat! No surface-meat past the pump! Foreman's orders! ...Snib is the foreman. Snib. Pump is BROKEN. Somebody broke it. Snib does not know who. Snib knows exactly who. What do you want? Quick.
```
Subtitle: Oi! OI! Surface-meat! No surface-meat past the pump! Foreman's orders! ...Snib is the foreman. Snib. Pump is BROKEN. Somebody broke it. Snib does not know who. Snib knows exactly who. What do you want? Quick.

### 2. `dlg.snib.first.1.wav`

*Where:* dialogue.json snib/first#1
*Played:* panicked bluster; doing: to stop the intruder and look important; pace: measured; volume: shout.
*Wants:* to stop the intruder and look important
*Note:* Big shout on 'OI!', a lamp-ring on the stressed words. Then the self-introduction is proud and small. 'It does, actually' is the contradiction gag: a sudden honest deflation before 'But quick'.

```
[panicked bluster, shouting] Oi! OI! Surface-meat! No surface-meat past the pump! Foreman's orders! ...Snib is the foreman. Snib. What do you want? Quick. The pump does not pump itself. It does, actually. But quick.
```
Subtitle: Oi! OI! Surface-meat! No surface-meat past the pump! Foreman's orders! ...Snib is the foreman. Snib. What do you want? Quick. The pump does not pump itself. It does, actually. But quick.

### 3. `dlg.snib.hub.0.wav`

*Where:* dialogue.json snib/hub#0
*Played:* grumpy pride; doing: still here; pace: quick; volume: level.
*Note:* Two self-important statements.

```
[grumpy pride] You again. Pump is BROKEN. Somebody broke it. Snib does not know who. Snib knows exactly who. Foreman is still foreman.
```
Subtitle: You again. Pump is BROKEN. Somebody broke it. Snib does not know who. Snib knows exactly who. Foreman is still foreman.

### 4. `dlg.snib.hub.1.wav`

*Where:* dialogue.json snib/hub#1
*Played:* nervous pride; doing: to sound in charge of a change he fears; pace: quick; volume: level.
*Wants:* to sound in charge of a change he fears
*Note:* 'Boss likes deeper' is brave; 'Boss has not SAID he likes it' is the panic underneath. Settle back into 'Foreman is still foreman' as reassurance to himself.

```
[nervous pride] You again. Pipe goes to the sinkhole now. Deeper. Boss likes deeper. Boss has not SAID he likes it. Foreman is still foreman.
```
Subtitle: You again. Pipe goes to the sinkhole now. Deeper. Boss likes deeper. Boss has not SAID he likes it. Foreman is still foreman.

### 5. `dlg.snib.hub.2.wav`

*Where:* dialogue.json snib/hub#2
*Played:* grudging recognition; doing: to show nothing has changed and he is in charge; pace: quick; volume: level.
*Wants:* to show nothing has changed and he is in charge
*Note:* Weary self-important routine, two status reports.

```
[grudging recognition] You again. Pump is still pumping. Foreman is still foreman.
```
Subtitle: You again. Pump is still pumping. Foreman is still foreman.

### 6. `dlg.snib.ember.0.wav`

*Where:* dialogue.json snib/ember#0
*Played:* nervous babble; doing: tells too much; pace: quick; volume: level.
*Note:* 'KNOW' stressed. Babbling the chain of who pays who faster and faster. A pause; panicked: 'Snib did not say any of this.'

```
[nervous babble] Snib does not KNOW where powder comes from. Powder comes in a crate. Crate comes from the Kerchiefs. The Kerchiefs get crates from a man with soft hands and a big book. Boss pays the man. Man pays the Kerchiefs. Everybody is happy except wagons. ...Snib did not say any of this.
```
Subtitle: Snib does not KNOW where powder comes from. Powder comes in a crate. Crate comes from the Kerchiefs. The Kerchiefs get crates from a man with soft hands and a big book. Boss pays the man. Man pays the Kerchiefs. Everybody is happy except wagons. ...Snib did not say any of this.

### 7. `dlg.snib.poison.0.wav`

*Where:* dialogue.json snib/poison#0
*Played:* defensive, fervent; doing: justifies the pump; pace: quick; volume: level.
*Note:* Dismissive. Then the Boss's fervour quoted, 'DOWN' stressed, eyes wide. Callous last line.

```
[defensive, fervent] Poison? It is slurry. Waste. Has to go somewhere. Boss says dig deeper, dig faster, the heart is hungry, the heart wants DOWN. Boss has a heart to feed and Snib has a pump to run. The wolves can drink somewhere else.
```
Subtitle: Poison? It is slurry. Waste. Has to go somewhere. Boss says dig deeper, dig faster, the heart is hungry, the heart wants DOWN. Boss has a heart to feed and Snib has a pump to run. The wolves can drink somewhere else.

### 8. `dlg.snib.move.0.wav`

*Where:* dialogue.json snib/move#0
*Played:* dawning delight; doing: takes your idea as his; pace: quick; volume: raised.
*Note:* Thinking: '...The sinkhole.' Then excited, shouting orders: 'Snib has had an idea!' proud.

```
[dawning delight, loudly] ...The sinkhole. Deeper. Deeper is good. Boss likes deeper. Fine! FINE. Lads! Turn the pipe! Snib has had an idea!
```
Subtitle: ...The sinkhole. Deeper. Deeper is good. Boss likes deeper. Fine! FINE. Lads! Turn the pipe! Snib has had an idea!

### 9. `dlg.snib.lamp.0.wav`

*Where:* dialogue.json snib/lamp#0
*Played:* awe, terror; doing: the Boss's lamp; pace: quick; volume: raised.
*Note:* 'LAMP' awestruck. 'SPIT' stressed. A pause; frightened denial. Then shouting orders.

```
[awe, terror, loudly] That is the Boss's LAMP. The spare! Boss never lends the spare. Boss does not lend his SPIT. ...Snib did not see you. Snib did not see the lamp. Lads! The pipe! Turn the pipe! The Boss says!
```
Subtitle: That is the Boss's LAMP. The spare! Boss never lends the spare. Boss does not lend his SPIT. ...Snib did not see you. Snib did not see the lamp. Lads! The pipe! Turn the pipe! The Boss says!

### 10. `dlg.snib.bribe.0.wav`

*Where:* dialogue.json snib/bribe#0
*Played:* sly, greedy; doing: names a price; pace: measured; volume: quiet.
*Note:* Conspiratorial whisper; 'Pumps break.' sly.

```
[sly, greedy, quietly] A week? Snib could lose a week. Snib could lose a week for forty. The pump could break. Pumps break.
```
Subtitle: A week? Snib could lose a week. Snib could lose a week for forty. The pump could break. Pumps break.

### 11. `dlg.snib.bribed.0.wav`

*Where:* dialogue.json snib/bribed#0
*Played:* hammy fake dismay; doing: the pump 'breaks'; pace: measured; volume: level.
*Note:* Terribly acted sorrow. 'SO sad.' over the top.

```
[hammy fake dismay] Oh no. Oh dear. The pump has broken. What a shame. Snib will be SO sad.
```
Subtitle: Oh no. Oh dear. The pump has broken. What a shame. Snib will be SO sad.

### 12. `dlg.snib.pipelads.0.wav`

*Where:* dialogue.json snib/pipelads#0
*Played:* flat dread, then panic; doing: the fate of pipe-lads; pace: measured; volume: quiet.
*Note:* Flat and quiet, unusually, about going blind and the warm slurry. 'Snib got promoted.' hollow. Then scared and loud: 'Snib wants you to LEAVE.'

```
[flat dread, then panic, quietly] Pipe-lads go blind by spring. Then deaf. Then they go in the slurry, because it is warm, and they do not come out. Snib was a pipe-lad. Snib got promoted. ...Snib does not want to talk about pipe-lads. Snib wants you to LEAVE.
```
Subtitle: Pipe-lads go blind by spring. Then deaf. Then they go in the slurry, because it is warm, and they do not come out. Snib was a pipe-lad. Snib got promoted. ...Snib does not want to talk about pipe-lads. Snib wants you to LEAVE.

### 13. `dlg.snib.what.0.wav`

*Where:* dialogue.json snib/what#0
*Played:* proud explanation, then unease; doing: what he pumps; pace: quick; volume: level.
*Note:* Proud 'Slurry!'. 'Stream is very obliging.' pleased. Then quieter: he's never needed to KNOW.

```
[proud explanation, then unease] Slurry! What is left when the stones are cooked. Pipe takes it down to the stream, stream takes it AWAY. Stream is very obliging. ...Snib does not know where the stream goes after. Snib has never needed to KNOW.
```
Subtitle: Slurry! What is left when the stones are cooked. Pipe takes it down to the stream, stream takes it AWAY. Stream is very obliging. ...Snib does not know where the stream goes after. Snib has never needed to KNOW.

## In a fight

### 14. `cbark.6c1ce83b343d.wav`

*Where:* godot/logic/Play/Bosses/ArenaBosses.cs

```
"Snib will tell Boss you said hello. Snib will NOT tell Boss."
```
Subtitle: "Snib will tell Boss you said hello. Snib will NOT tell Boss."

### 15. `cbark.746d49e0a695.wav`

*Where:* godot/logic/Play/Zones/Verge.cs
*Played:* panicky bluster; doing: Snib shouts a warning; pace: quick; volume: shout.
*Note:* Squeaky shout.

```
[panicky bluster, shouting] OI! No surface-meat past the pump!
```
Subtitle: OI! No surface-meat past the pump!


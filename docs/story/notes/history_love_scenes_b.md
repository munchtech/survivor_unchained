# RETIRED (28 October 2026): the love scenes, B

The owner removed the love-scene options and the romance routes (OWNER_NOTES, 28 October). Sella stays who she is and likes the survivor; her free night is now the night she sits with you (`sella.free_door`, `free_what`, `free_sit`). Maeca's Blind is the watch night (`watch_only`, `blind_dark`, the gray lights). Nothing below is in the game. Kept as the history of B.

---

# The love scenes: B, the lovers' own lines

The owner chose B on 6 October: at a love scene the narrator (under twist A,
her mother; `TREATMENT.md` §3.4) stops at the door, and behind it only the
lovers speak. Nothing is explicit; the night fades at the moment itself. The
editor's reasons (notes 02 §10): B keeps twist A whole (silent narration in
the room would invite "Mum was watching?"), B is the better writing, and a
voice close in the dark has the stronger sex appeal.

## The four conditions, and how B meets them

1. **The bolt is the door.** The narrator's last line before the door is the
   bolt, heard from the stairs (`sella.free_bolt`, and the same sentence
   opening `free_sleep_bed`: one take). Then she is silent until you come back
   down. `free_stairs` lost its two sentences in the room; Sella's "Lamp stays
   up tonight." keeps the lamp.
2. **No "Boots."** Maeca's first word in B is "...Hear that?"; the boots are
   gone from A as well.
3. **"One hand on the crossbow and the other on you"** (the plant for the
   rope) opens the gray light at the Blind, outside the door, in the
   narrator's voice (`maeca.blind_morning`, the first morning).
4. **B lives or dies on the takes.** Directed line by line
   (`tools/vo/direction/love_b.json`): low and close, nearly a whisper, never
   breathy; each "..." a real silence of two to four seconds (the importer
   keeps up to four for these lines); a laugh that sounds made is cut. **A is
   the fallback** for any take that can't be made to sound like a person: the
   narration as it stood at `fd0b8a9b` (`git show
   fd0b8a9b:godot/data/content/dialogue.json`, the same node ids), shown as
   unvoiced text over one held object (`stairs_room` without the
   elbow-and-chin sentence, "She tests the water with her elbow like
   somebody's mother...", which under twist A puts a mother in the room;
   `free_bolt` is B's in either version).

## The rules behind the door

- **Where the door is.** Sella: from the blue room (`stairs_room` on) to the
  last morning line (`door_south`, `free_m_*`), the night she's paid to sleep
  and the stop included. Maeca: from under the hides (`blind` on) to
  `blind3_morning`. The walk to the Blind, the fire and the first gray light
  are outside, and stay narrated.
- **On black, a direction is a caption:** what is heard ("(the hides
  rustle)", "(water poured)") or how she says it ("(low, against your
  chest)"), never what is seen. A visual direction there would be the
  narrator's prose by another name.
- **The mornings are lit:** her directions may place her ("(on the edge of
  the bed, her palm flat on your breastbone)"); they are played, never read.
- **Nothing behind the door is the narrator's to record,** locked or not
  (`tools/vo/elevenlabs.py` `DOOR`; `tools/vo/tests/test_door.py`), and the
  data keeps it so (`StoryRewriteTests.The_narrator_stops_at_the_door`).
- **The sounds are the game's, not the actor's** (for cinematics and sound):
  water poured and slopping over the side, the bath moving, buckles and the
  one that sticks, a lace, coins counted (twice after the cold bath; thirteen
  back into your palm), the fourth and ninth steps, the bolt that sticks and
  then goes home, the hides, the fire shifting and the embers ticking, the
  Pack far off (fed and loud; one call), soft feet in the frost and the
  Pack's sighs round the Blind.

## B as it plays (the data; the other variants follow the same rules)

## Sella

### The blue room (`stairs_room`, eight variants: the first time by calling, then again)

> (water poured) It's the lamp glass. Everyone asks. Everything up here comes out blue. ...Warm. Told you. Chin up. Let me look at you. (buckles, quick, one after another) I've undone a few of these, love. (one sticks; she laughs) All that steel, and under it, look. A person.
>
> (water poured) Blue room again. Same jug, same quilt. ...Same me. (buckles, quick, one after another) I've undone a few of these, love. (one sticks; she laughs) All that steel, and under it, look. A person.

### The bath (`stairs_rules`, if she has felt the cold in you)

> (the bath water moving; then still) ...You're cold. Not chilled, love. Cold. Under warm water. (a long quiet; no joke in it) ...Right. Rules. Anything you'd rather I didn't, say so. Anything you'd rather I did, say it louder.

### The first night (`night`, the last variant)

> Bath's warm. Was warm. ...Leave it, love. Come here. There. Now, any hand of mine that's not welcome, you say, and I'll find it somewhere it is. ...That's it. Slow. Nobody's paying me to hurry. ...Listen. Can't hear the road from up here. Can't hear the river. That's what the fifteen's for. (morning: coins, counted)

### Three nights or more (`night`, the middle variant)

> (water slopping over the side; she laughs) That's the floor, then. ...Not with my shift, you great— give it here. ...Right. I'll tell you what I'm going to do, love, and then I'm going to do it. First I'm going to— ...First. ...You know. Come here. (morning: coins, counted)

### The cold bath (`night`, the first variant)

> Water's gone cold. ...Leave it. I'm not walking three steps for a bed; bring the quilt. ...Easy. Easy, love. ...Don't. ...Don't look at me. ...I'm not getting dressed. Don't ask me why. (morning: coins, counted, and counted again)

### The night she's paid to sleep (`rest_night_paid`, `rest_dark`)

> (as if it's a word in a foreign tongue) Sleep. ...You've paid fifteen gold to sleep.
>
> ...and there's Rook at the top of the stairs with her cudgel, and him in his shirt— no. That one's for another night. ...There was a man from Low Kiln, wanted me to bark. Like a dog. And I said— (she breaks off; then, softer) ...Go on, then. Sleep. Somebody ought to watch you.

### Her free night: the stairs and the door (`free_stairs`, `free_door`)

> She doesn't take your hand on the stairs, or your sleeve. She goes up ahead of you, and on the fourth step she forgets to step over it, and it creaks, loud as a shout, and she stops dead with one foot on it and laughs at herself, and that's worse, somehow, than if she hadn't.  *(the narrator, on the stairs)*
>
> Lamp stays up tonight. ...I keep thinking about you sitting on my bed telling me where you're from. Knowing who'd hear it by morning. ...Nobody does that. Nobody's ever done that.

### The bolt (`free_bolt`): the narrator's last line

> Behind the door, the bolt sticks halfway; nobody has ever shot it. Swearing, and a shoulder to it, and then it goes home, with a sound like the last coin put down on a counter. "...There."

### Her free night (`free_night`: if she told her knowing it would be sold; otherwise)

> My hands don't know what they're doing. ...Seven years, love, and I can't undo a lace. Don't you laugh. Don't you dare— (she laughs, and can't stop, and then she does) ...Wait. ...All right. All right. (much later; into your shoulder) ...You told me anyway.
>
> No talking. I talk for money. ...Stay like that. Let me look. ...I'm not making a joke of it. Don't you make one. ...Yes.

### If you only sit, or only sleep (`free_sit`; `free_sleep_bed`, which opens on the same bolt)

> The house. In the south. ...Kitchen faces the sun. Green door. Not blue; nothing in it blue. (a breath) And somebody who knocks. ...Go on, then. Down you go. Mind the fourth.
>
> (Behind the door, the bolt sticks halfway; nobody has ever shot it. Swearing, and a shoulder to it, and then it goes home, with a sound like the last coin put down on a counter.) Shift over. Arm. ...Your arm, love, over. Like a blanket. There.

### A morning after (`free_m_kiss`; the mornings take lit directions)

> (she lets you; then pushes you off by the face, gently, with the flat of her hand) Out. Before I get used to it. (smiling, all the way to the stairs; behind you, the ninth step creaks) ...I'm not watching you go. Go on.

## Maeca

### The first night at the Blind (`blind`: the Pack fed; otherwise)

> (far off, the Pack, loud) ...Hear that? (a short laugh, surprised out of her) They're eating. ...Down. On the hides. ...Quiet. I said quiet.
>
> (the fire shifts; then her voice, close) ...Hold still. Slow. Say stop and I stop. (far off, the Pack calls; nothing, until it's done) ...All right.

### After (`blind_dark`; `blind2_feet`, `blind2_let`)

> ...You're colder than my feet. (the hides rustle) How are you colder than my feet.
>
> ...Two toes short. The wet had them, a long time back. (a long quiet) ...Hold them anyway. ...Nobody's held those.
>
> (a long quiet; then, half asleep, close) ...Keep still. ...They're only feet.
>
> (outside, in the frost: soft feet, a long way round; a sigh; another) ...They don't do that. Not for me. Not for anyone. (low, against your chest) You walk quiet. You came into my Hollow and knelt to him, and he let you. You never talk about before. (almost no sound) ...What were you?
>
> (the embers tick) ...They've settled. (her breathing slowing) Sleep.

### The gray light (`blind_morning`, outside the door: the narrator opens it)

> (Gray light. She's already up, crouched in the frost at the mouth of the Blind, listening to the wood: one hand on the crossbow and the other on you.) The Pack found me, after Ashford. A cave mouth, and a lad I'd been fond of dying in it. The old gray one came and lay down across the way in. Kept the cold off. Kept everything off. ...That's why. That's all of why. Don't make it a story.

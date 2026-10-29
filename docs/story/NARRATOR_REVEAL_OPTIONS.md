# The narrator is her mother: two ways to make it a reveal (Story 12, 28 October 2026)

**The problem (the owner, 28 October):** C04's first dawn says she can't hold her
mother's FACE but still has her VOICE, and the narrator then speaks the call in her
own voice ("Lamp's lit, Spark. Stay where it reaches."); the dawns take the voice
away. The player is told what the voice is and invited to compare it with the only
voice in the game. The bottom of the stair (C43) then confirms instead of turning.

**What a change costs: nothing to re-record.** Every narrator take in
`godot/art/vo/narrator` is a Maya1/Seed-VC placeholder (`tools/vo/manifest.json`,
`"placeholder": true`); the C04 face line's take is already STALE (made before "Her
voice is still there" was added). A rewrite means re-locking two to four lines and
regenerating placeholders. No ElevenLabs cost.

## Option A (recommended): the flip. She keeps the face; the voice is the one thing she cannot find.

What the player hears and sees, beat by beat:

1. **C04, the first dawn** (`cin_first_light.face`): *"You try to call up your
   mother's voice, and it is not there. Not faint: gone, as if someone had taken it
   out of the room. Her face is exactly where you left it: the line between her
   brows, the thread she bit instead of cutting."* The narrator never says the call.
   There is nothing to compare her with.
2. **Day 3** (`dawn.voice` in rules.json, renamed `dawn.face`): *"Her face is going
   the way her voice went. The brows first. You still have the word."*
3. **Day 6** (`dawn.word`): unchanged. *"This morning it takes you a moment to find
   her word. It is there."* The journal keeps *"Spark. What she called me, at dusk."*
4. **The first dusk at the gate:** the Watch call the lamps ("Lamp's lit. Stay where
   it reaches.") in a Watchman's voice; the storybook's Watchman already says it. The
   player learns the WORDS from the valley, never the voice from her.
5. **After Act 2's turn** (unchanged): *"Somebody used to call you something at dusk.
   One short word. It was yours."* Then the line stops coming, and the dawns thin
   (editor notes 01 §4: the player hears her leaving).
6. **C43, the bottom of the stair:** the voice moves out of the air and into the pale
   thing below, and for the first time in the game says the call: **"Lamp's lit,
   Spark."** The narrator's voice, which the player has heard every night, saying the
   one line she never said, from a place. Choices as planned ("Mam?" / (Listen.) /
   "Let them go."). Then, first person, once: *"I came up with you. Somebody had to
   tell you where you were."* / *"You'd have sat down in the road and waited for me."*
   And the re-read lands on its own: of course she could never find her mother's
   voice. It was never in her memory to lose. It was in her ear the whole game.
7. **The endings** as planned: A, *"You lie down."* then *"I'm here."*; B, *"It's
   morning, Spark. Go on."* and silence; C, her voice fading under the others.

Why A: the false belief stays whole (players do not ask who a narrator is); the flip
gives the reveal a mechanism that clicks on the re-read (the voice was not gone, it
was here); losing the FACE is sadder on screen than losing a voice, and it sets the
stair: by Act 3 she has lost the face, and at the bottom the face is in front of her
with the narrator's voice coming out of it. Both come back at once, and *"Her face
is exactly where she left it"* becomes the line it was always meant to be.

Would a player say "what the fuck" out loud: yes, the good kind (my score 8/10,
against about 5/10 today, where the beat is told). Cost: three line changes (C04's
face line, the day-3 report, `StoryRewriteTests.Her_mothers_word_is_Spark_and_the_dawns_take_it_away`),
one re-lock, placeholders; one to two hours.

## Option B: keep the voice, hide the comparison, plant a false voice.

1. C04 keeps *"Her voice is still there"* but the narrator does NOT quote the call:
   it is heard as an echo in a second, younger voice (a sound cue: a child's memory
   of it), so the player's ear holds a "mother's voice" that is not the narrator's.
2. The dawns take that remembered voice, as now.
3. A false match in Act 1: a woman of the Watch calls the lamps at the gate and the
   narrator says *"That isn't it."* (misdirection: the game is seen to rule voices
   out).
4. C43: the narrator's own voice says *"Lamp's lit, Spark"* from below. The re-read:
   the remembered voice was the child's memory of her; the plain dry narrator is
   what that voice became, and she has narrated her own child forgetting her.

Why not B: it needs a second recorded voice (a new ElevenLabs casting), a sound cue,
and a planted contradiction (remembered voice vs narrator) that some players will
read as a continuity error rather than a twist. More parts, less click.

## Either way (line level, no gate needed)

- The narrator never says "Spark" before C43 (today she does, in C04).
- From Act 2's turn her dawns thin: shorter lines, one missing here and there.
- At C43 the voice LEAVES the player (from the air down into the pale thing); it
  does not arrive from below (editor notes 01 §4).

**Recommendation: A.** On the owner's pick, the writer edits `cin_first_light.face`,
`rules.json` `dawn.voice`, the test, `docs/story/TREATMENT.md` §2 and §3.4, and
re-locks; the cinematics lead gets one note (C04 A7 holds on her face, not her ear).

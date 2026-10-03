# Editorial letter: *Survivor Unchained*

To the author,

This is a developmental editor's letter on the story of *Survivor
Unchained* as it stands on the working branch: the whole arc in
`docs/STORY_BIBLE.md`, the voices, the Act 1 writing pass, and every
line of Act 1 that ships (the dialogue, journal, barks, townsfolk, item
lore, morning reports, the prologue, the Waystation, the Verge and the
arenas). Acts 2 and 3 exist as a bible, not yet as text, so my notes on
them are notes on a plan.

It is long because you asked for depth. It is organised as editors'
letters usually are (`CRAFT_STUDY.md` §13): what I think the story is;
what already works and why, so you know what to protect; the important
problems ranked by impact, each diagnosed as what a player experiences,
where, why, and why it matters, with possible approaches; how it holds up
against the best of the genre; how the play and the theme support each
other or don't; and a plan in order.

The other files go deeper. `NOTES_BY_ACT.md` has the act-by-act and
thread-by-thread notes. `LINE_NOTES.md` has the line edits.
`IDEAS.md` has the menu of improvements, each costed.
`THE_EMBER_REVEAL.md` drafts the large reveal you asked for (what the
ember really is). `REALNESS_AND_EXTREMES.md` answers your second request
(how human the cast is, and the truly heinous turns available).
`CRAFT_STUDY.md` is the study all of this rests on.

Everything here is diagnosis first. Where I suggest a cure it is one of
several. You know what the game is for; I only know what it does to a
reader.

---

## 1. What this story is

On the surface: a traveller drowned at a ford rises not knowing they are
dead, kills the thing that drowned them, walks into a failing crossroads
town, and over three acts learns what they are (Act 2), who made them and
why (Act 3), and decides what to do with it (the endings). Underneath the
town lies a vast chained thing praying to die; its pain is the light
everyone in the valley lives by; the woman who reads fortunes at the toll
drowned a dozen carters to make the survivor, because she needs one of
their kind to lie down in the chain forever.

That is the plot. What the story is *about*, judging by what is actually
written, is something the bible does not quite say, and I think it is the
most valuable thing in the project:

> **Everyone in this valley is keeping the lights on with a debt to the dead that they cannot pay.**

Holloway signed for the boots of a garrison that died barefoot. Maeca is
what is left of it. Brannoc forged the irons that drowned his daughter.
Harlan sells ember to the hole that killed his sister. Pell counts because
his sister kept Ashford's books. Redcowl feeds forty-one survivors of a
town he will not name. Rook lights her hearth from a dead captain's lamp.
Chid keeps a dead order's shrine. Vonnra keeps her dead family's duty with
other people's lives. Keegan guards a gate for a Vigil that will not answer
her letters. Ysolde sells the living to feed her risen brother. The
lamplings carry out their own burned dead and count them, to forty, and
start again. And every one of them counts something. (`NOTES_BY_ACT.md`
§0.1 has the table.)

That unity was not imposed; it grew from writing each person truthfully,
and it is why the Waystation feels like a town and not a quest hub. It
also tells you what your three endings are about. Re-forge the chain:
keep paying. Break it: let the debt go. Take the light: take the debt into
yourself. Every NPC has already made that choice in small. The player
makes it last.

**What it wants to be,** judging by the brief ("Diablo 5 RC good") and the
design: a dark fantasy action RPG where a day of choices in a living town
alternates with nights of ember-fuelled horde combat, and the story
stands beside the genre's best. Its ambition is closer to *Planescape:
Torment*'s heart inside *Hades*' loop than to Diablo's story. That is the
right ambition.

---

## 2. What already works, and why

In order of how much I would protect it.

**2.1 The voices.** `VOICES.md` is a real voice bible and the dialogue
honours it. Most lines could be attributed with the names removed, which
is Gene Wolfe's test (`CRAFT_STUDY.md` §11.1). The "never" rules (Rav
never names his brother; Redcowl never says Ashford; Vonnra never answers
yes or no; Brannoc never thanks anyone), each with one written exception
placed where breaking it *is* the scene, are an exceptional device: the
exception lands because the rule held. Keep the rules sacred.

**2.2 The narrator, and the morning reports.** Present tense, second
person, one image per line, never what it means: Glen Cook's
understatement plus Hemingway's omission. The morning reports are the best
prose in the game ("One of them sat by the pile and counted them. It got
to forty and started again."), and they land at the quietest moment of the
loop, which is exactly where restraint pays most. They should be the house
standard for every new line (`LINE_NOTES.md` §8).

**2.3 Nell.** The ambush at the wagon, the line after it ("The one with the
reins was a girl, twelve at most: red hair under the weed, and new boots."),
and Brannoc's question days later make a three-stage recognition built on
the player's own hands, which no novel can do. Its consequences run across
all three acts (the last two irons, the Kiln Ford, a second Unchained, the
heart's cage). It is the best-built thing in the game, and Brannoc's scene
is the best-written. `WRITING_PASS.md` asks you to confirm its tone: in my
reading it is right, and should not gain a word.

**2.4 Sella's pillow talk quoted in the fortune.** "(She is not looking at
your palm.)" It is fair (the player told Sella; the player knows Vonnra
buys Sella's talk), surprising and inevitable at once, and it pays inside
Act 1. It is the model twist for the rest of the game (`CRAFT_STUDY.md` §3).

**2.5 A cast of people who believe they are right.** Pell ("I'm not a good
man. I'm a careful one."), Redcowl feeding his prisoners before his own,
Harlan, Vonnra. Nobody in Act 1 is a cartoon. (This strength has a shadow,
which is problem 5.)

**2.6 The consequence ledger.** Every Act 1 fact is mapped to where it lands
in Acts 2 and 3. Delayed consequence that is personal and moves across
acts is the craft of the Bloody Baron (`CRAFT_STUDY.md` §10.2). The
found-early principle (a thing found before its quest starts its story,
and the person it belongs to reacts to a survivor who arrives knowing) is
Larian's "weird Dungeon Master" stance at a town's scale, done thoroughly.

**2.7 The plants.** "You try to call up your mother's face, and find it is
not quite where you left it." "Not breathing. Praying." "It was never locked
from the outside." "Keep the lights lit. — C." "The water took it, or you
left it on the far bank. Most do." The best of these are true twice, which
is the definition of a fair plant.

**2.8 The editorial infrastructure.** A private myth bible, a voice bible,
a writing spec with every fact's writer and reader, and `StoryLint.cs`,
which catches unreachable nodes, unearned journal lines and facts asked
about but never set. Most studios ship without this. It means the fixes
in this letter can be made safely.

---

## 3. The problems, ranked by impact

### Problem 1. The nights, where most of the game is played, are silent.

**What the player experiences.** By day, a dense, reactive, beautifully
voiced story. By night, thirty-minute horde arenas with no story in them:
no voice, no line from the boss, no change from the random ember scars but
a name on a health bar. Greymuzzle, the most dignified creature in the
game, becomes a half-hour boss fight. Redcowl, its second-best talker, dies
silent as an "enforcer". The result screen says "The story goes on."

**Where.** `godot/logic/Play/Zones/Verge.cs` (`MakeStoryFights`),
`ArenaRun.cs`, `src/Ui/ArenaResult.cs`.

**Why.** The arenas were built as a system, and the story was built in
the town, and nothing yet joins them. And the four story arenas in Act 1
are all the *violent* routes (hunt the Pack, raid the Roost, hold the Dig,
open the vault). A player who cures the wolves, bargains for the cages and
moves the pump plays no story arena in Act 1 at all.

**Why it matters.** It is the game's central split: play and story are in
different rooms. Clint Hocking's "ludonarrative dissonance" was coined for
exactly this (`CRAFT_STUDY.md` §8.10): what the game is about as play
and what it is about as story come apart. The genre's best answer is
*Hades*, where every death is a return home and the story happens there;
where bosses remember you; where "the sting" is taken out of failure by
making it the plot. And the brief says all story beats are night arenas,
so a silent night is a silent beat. It also sends a message the game does
not intend: the merciful player gets less story than the violent one.

**Possible approaches,** cheapest first (`IDEAS.md` I-1 to I-8):
- Bosses who speak and remember: an intro, a taunt and last words per
  story arena, gated by facts (Redcowl's last words depend on whether you
  said "Ashford" to him). A few fields and twenty lines. [I-4]
- A dawn line per story arena, won and lost, in the morning-report voice,
  replacing "The story goes on." [I-7]
- One line that says what an arena *is*: the survivor is a light in the
  dark, and everything that has lost a light comes to it. That turns the
  genre's loop (more power, more enemies) into the story's logic. [I-1]
- The Wayfinder as the arenas' voice across runs, commenting on how you
  did, *Hades*-style, while writing you into the margin that will end up
  in Sallow's ledger. [I-8]
- A story arena on every route, not only the violent one. [I-3]
- And the deepest version: the arenas are how Vonnra prepares the link.
  An Unchained who never burns goes dim; the survivor burns brighter
  every night they fight; Vonnra pays for the Wayfinder's maps. The core
  loop turns out to be the antagonist's plan. [I-2]

### Problem 2. The protagonist has no want.

**What the player experiences.** The survivor arrives and solves the
town's problems. Their own story in Act 1 is one line at dawn and one line
of sleep-talk. The three questions that make the spine (what are you, who
made you, what will you do) are asked *of* them; nothing is asked *by*
them.

**Why it matters.** Sol Stein's first triage question is whether the
protagonist is strong enough (`CRAFT_STUDY.md` §2.14). A protagonist
without a want is a camera, and the ending's question ("What will you do
with it?") becomes abstract: a choice about a god, made by someone with no
stake. The survivor's voice (short, plain, dry) is right; it is their
*role* that is empty.

**Possible approaches.** Give each background one named person the
survivor was going to or coming from on the night of the ford; let theirs
be the face that "is not quite where you left it"; let the memory mechanic
take them piece by piece in Act 2; let the survivor hear them at the
bottom of the stair in Act 3 (`IDEAS.md` I-11; `NOTES_BY_ACT.md` §0.4;
`THE_EMBER_REVEAL.md` §7). Then the cosmic choice is decided by a single
relationship, as *Planescape*'s and *The Witcher 3*'s are. And the
backgrounds' own promises need paying: a hunter who grew up in Thornhollow,
whom nobody in the Waystation recognises; a devout raised by an Order that
supposedly left seventy years ago.

### Problem 3. The Act 1 mystery's keystone does not hold, and four questions are open.

**What the player experiences.** A careful player solving "who lit the
lamps?" will notice that the text says lit lamps *keep the Warden asleep*
(Keegan), *feed the Warden* (the prologue, and the boss fight teaches it
with the player's own hands), and were relit *to wake it* (the bible).
Keegan's key line ("They were to keep the Warden asleep. If somebody lit
them again, somebody wanted it awake.") is a non sequitur.

**Why it matters.** A mystery is a contract (Knox's fair play; Sanderson's
First Law; `CRAFT_STUDY.md` §3.4). The player solving it is reasoning from
these lines. If the logic breaks, the player concludes either that the
writers did not notice or that Keegan is lying, and neither is wanted.

**The fix** (`LINE_NOTES.md` note 1): two kinds of light. The Order's
lamps burned ember, which feeds a Warden; the Watch burned oil, which gives
light and nothing to drink, so the Warden slept; the Watch ran out of oil;
last winter someone hung twelve new irons made to hold ember, and lit them
with it. This repairs every line, explains why Vonnra needed *new irons*,
and makes Holloway's "no oil since my first winter" a clue.

**The four questions** every attentive player will ask, and the bible
should answer before Act 2 is written (`NOTES_BY_ACT.md` §0.3):
1. What do the lamps do? (above)
2. Why didn't Vonnra use Chid, an Unchained who has lived across the
   square for two hundred years? (Suggested: an Unchained who never
   burns goes dim; the chain needs a bright one. `IDEAS.md` I-2.)
3. Who carried the survivor back to the fire? (Suggested: Chid, already
   seeded by Rook's "Chid came in babbling about blue lights going out at
   the crossing". `IDEAS.md` I-9.)
4. Where does the devout survivor's Order still exist, and why does a
   hunter born in Thornhollow go unrecognised?

### Problem 4. The central twist is the genre's most guessable, and the game says it early.

**What the player experiences.** A game called *Survivor Unchained*, about
the risen dead, in which the hero respawns at a shrine every time they die,
in a genre trained by *Planescape*, *Dark Souls* and *Dead Cells*, will
make players guess "I am one of the risen" within hours. The game then
nearly says it: the trait `risen_once` reads "You have died and come back";
Vonnra says "You have already died on this road"; the townsfolk say "Chid
says you died. You look well on it." And the second question (Vonnra made
you) is answered in Act 1 for a careful player, by design: the accusation
is the act's reward.

**Why it matters.** It is a problem only if Acts 2 and 3 stage these as
revelations and wait for a gasp. Hitchcock's bomb under the table is the
answer (`CRAFT_STUDY.md` §3.6): fifteen seconds of surprise or fifteen
minutes of suspense. Most secrets are worth more as dramatic irony. And a
twist that is a ledger entry ("what you are", bible beat 11, lands through
"the ledger, Keegan's chapter four, and Chid") is recognition by token,
Aristotle's weakest kind (§3.2).

**Possible approaches.**
- Remove the interface's statement of the twist (`LINE_NOTES.md` §4.4).
- Stage "what you are" as a confrontation, not a revelation: Keegan at the
  gate asking "Did you die on the Low Ford road?" of a survivor the player
  knows did. The drama is her duty and what the survivor answers.
- Start the memory cost at that moment, so knowing what you are is the
  moment it starts costing you who you were.
- Put the true surprises *underneath* the guessable ones, where a player
  who solved the surface will not look: Vonnra went into the ford first,
  or chose Nell on purpose; Chid watched the drownings, hoping one would
  rise; the ember is the dead. These are drafted in
  `THE_EMBER_REVEAL.md` and `REALNESS_AND_EXTREMES.md`.

### Problem 5. The valley is too forgivable.

**What the player experiences.** (This is your note on realness, and I
agree with it.) Read the cast's secrets in a row and every one has a noble
or understandable motive: Vonnra to save the valley, Holloway to cover his
commander, Harlan to keep the Company alive, Pell to keep the ember from
the Dig, Redcowl to feed his people, Ysolde to feed her brother. The kind
characters (Rook, Chid, Wenna, Keegan, Maeca) have no shadow at all.

**Why it matters.** It is the inverse of grimdark's hollowness, and just as
unreal: the *sympathetic-reason trap*. Real people also do terrible things
for small reasons (fear, money they did not need, loneliness, vanity, not
wanting to be the one to make a fuss), and kind things for bad ones. The
reader recognises a person in the motive beneath the defensible one.
Martin's mantra is "the human heart in conflict with itself"; a heart with
one good reason is not in conflict (`CRAFT_STUDY.md` §2.1).

**Possible approaches** (`REALNESS_AND_EXTREMES.md`): give every named
person a third layer of motive, the small human one a friend would name
after the funeral (Holloway sold the boots; Rook knew what the carters'
money was for; Wenna chose who got the bitterroot in the fever year; Keegan
has returned an Unchained to the dark before, a girl of fourteen; Brannoc
took the irons money because Nell needed boots); give the hard people one
unearned kindness each; keep a few fixed points clean (Tam, Snib,
Greymuzzle). And ration the extremes: one major heinous turn per act, each
a human choice that breaks something the story set up as sacred, planted at
least twice, said in one line.

### Problem 6. Act 2 is too big to build well.

**What the player will experience** if it is built as written: twelve beats,
three new major characters (Sallow, Edric, the second Unchained), a new
location, a war, a breakthrough, the boots, the irons, romances, and well
over a hundred outcome combinations before Act 3 multiplies them. The
reactivity per thread in Act 1 (sixteen test scenarios for the caravan
alone) cannot be sustained across that.

**Why it matters.** Larian's companion spreadsheets took "a small army"
(`CRAFT_STUDY.md` §10.6). Scope that outruns the team produces exactly the
Season 8 failure: correct destinations reached too fast, without the
intermediate beats that earned Act 1 (§4.4). And none of Act 2's beats is
yet assigned to a night, though every big beat is supposed to be one.

**Possible approach.** Six nights, each a story arena with a speaking boss
and day scenes before and after: the breakthrough; the boots (with
Holloway's letter); the second crossing (with Sella and Jory); chapter four
(with "what you are"); Silverstair (with the army); the war at the gate.
Everything else folds into day scenes and morning reports. The ledger
survives whole (`NOTES_BY_ACT.md` §3.1; `IDEAS.md` I-33).

### Problem 7. The Morrow is abstract, and the endings echo *Dark Souls*.

**What the player will experience.** A vast pale thing praying to die is
pitiable at a distance; nobody the player has met is in it. And the three
endings (re-forge the chain, break it, take the light) map onto *Dark
Souls*' link the fire, let it fade, and become the Dark Lord. Players will
see it.

**Why it matters.** The bible's Morrow is a fine Omelas (`CRAFT_STUDY.md`
§5.10): the town lives by a chained thing's pain. But the strongest
reveals are personal and recontextualise what the audience has *already
done* (the Red Wedding; *Bloodborne*'s insight; *Spec Ops*' white
phosphorus). This one tells the player that their power hurt something far
away. It does not say whom.

**The approach you asked for** is drafted in `THE_EMBER_REVEAL.md`: **ember
is the dead.** The Morrow is an ancient thing that eats the light of every
death in the valley and keeps it; ember is the held dead, leaking up; the
player has burned them since the first night, Nell among them; the Morrow's
prayer is theirs, and it is names. Twenty seeds for it are already in the
shipped text. It makes each ending mean more (keep burning your
grandmothers; let them go; take them all into yourself); it turns the
*Dark Souls* echo into a conversation (that game's souls are anonymous;
these have names); and it lets the ending decide whether the arenas still
exist.

### Problem 8 (smaller). Three things worth deciding.

- **The fortune is a recap at a climax.** Nine pages of summary end Act 1;
  the act needs a turn of its own and a night (`NOTES_BY_ACT.md` §2.8;
  `IDEAS.md` I-5, I-28).
- **The concept art and the prose are in different registers.** The prose
  is frost, barefoot hunters and a smith's apron; the calling sheets are
  high-glamour costume. That is a legitimate genre choice, and not this
  writing's. Decide which the game is, because the dissonance will be felt
  most in the intimate scenes, where the prose is most careful.
- **Sella's Act 2 arc punishes her for helping.** The helper destroyed to
  motivate the hero is an old pattern. Keep the event; give her the choice
  (`NOTES_BY_ACT.md` §2.7).

---

## 4. Against the best of the genre

**The premise** (a drowned traveller who rises not knowing they are dead,
in a valley that lives by a chained god's light) is strong, and stronger
than most in the genre because it is *small*: one town, one valley, one
crossing. Diablo I's Tristram is the model (`CRAFT_STUDY.md` §4.6), and
it is the right one.

**The spine** (three questions, one per act) is clean and teachable, and
it is a spine about identity in a story whose heart is debt. Add the
controlling idea (§1 above) above the three questions and the endings
gain their meaning.

**The twists.** Measured against the fair-twist checklist
(`CRAFT_STUDY.md` §3):

| Twist | Planted | Fair | Surprising | Inevitable | Verdict |
|---|---|---|---|---|---|
| Sella's talk in the fortune | yes | yes | yes | yes | A model. |
| Nell | yes | yes | yes | yes | The best in the game. |
| Vonnra lit the lamps | heavily | yes | for some | yes | Designed to be solved; Act 3 needs a further turn. |
| You are Unchained | heavily | yes | rarely | yes | Stage as dramatic irony, not revelation. Remove the interface's statement. |
| Holloway and the boots | yes | yes | yes | yes | A model of a sociological twist. Write the Act 2 scene for a player who already suspects. |
| Chid is Unchained, and "C." | yes | yes | mildly | yes | Fine as irony. Deepen with the fire at the ford, and perhaps the heinous version. |
| Jessop on the stair | yes | yes | yes | yes | The best image in Act 3. |
| Grimtunnel the believer | no | not yet | — | — | Plant in the prologue. |
| The Morrow prays to die | yes | yes | yes | yes | Strong but abstract; make it personal. |
| (proposed) Ember is the dead | twenty seeds already | yes | yes | yes | See `THE_EMBER_REVEAL.md`. |

**The endings** are all defensible, which is the hardest thing in an
ending set (the *Pentiment* standard: no right answer). They need to be
*played* rather than chosen from a menu (the Season 8 lesson: dramatise the
decisive choice, with the alternative visible), and ending C needs a road
rather than a checklist (track what the survivor *took*, all game).

**The world** keeps Tolkien's distance and Wolfe's ignorant natives:
nobody explains the Legion, the Order or the Vigil, and they should not.
What it needs is a private timeline that does not contradict itself, a
glossary, and a colour sheet.

---

## 5. Theme and play

The game's two halves are a gift most games would kill for, and they are
not yet used.

**By day, no ember.** The survivor is ordinary: talks, investigates,
chooses, fights with what they carry. This is where mercy lives (cure the
wolves; bargain for the cages; tell Brannoc the truth).

**By night, ember.** The survivor burns: the Morrow's light (or the dead's)
in them, power growing by the minute, the horde thickening to meet it. At
dawn it all goes out, "and everything it gave you goes with it", and the
survivor's mother's face is not quite where they left it.

Read as theme, that is extraordinary: **power is borrowed from the dead,
it costs you who you are, and it does not keep.** It is Stormbringer as a
day cycle (`CRAFT_STUDY.md` §5.4). Every night the player chooses to burn,
and every dawn they lose something. Nothing in the game says so yet. The
dawn line in the prologue is the only place the cost is felt.

Three harmonies to build, in order of cost:

1. **Say what the nights are** (I-1): the survivor is a light, and the dark
   comes to lights. The loop becomes the story's logic.
2. **Let the cost be felt** before it is explained: a small wrongness at
   dawn after heavy nights, from Act 1 (I-36); the explicit memory
   mechanic from Act 2's turn; the names burned by the heart in Act 3
   (I-30).
3. **Let the ending decide the loop** (I-34): after the chain breaks there
   is no more ember and no more arenas. The last thing the mercy ending
   costs the player is the power they used all game.

And one disharmony to fix: the merciful routes have no nights (Problem 1,
I-3).

---

## 6. Line-level patterns

Not a line edit (that is `LINE_NOTES.md`), but habits worth fixing
globally:

- **The narrator occasionally winks** ("— probably — dead"). It never
  should.
- **The interface sometimes speaks for the story** ("An ember arena: the
  story remembers how it goes"; "The story goes on."; the `risen_once`
  trait). The interface may describe; it must never say what something
  means, and never answer a question before its act.
- **Images repeat** ("hums against your teeth" twice; "probably" twice).
  Once is usually enough (Browne and King).
- **Names collide with clues** ("Red Wat" in the nemesis list; the
  board's "R." in a town hunting for "R."; the Watch's shield device is a
  torch in a story about lamps).
- **Static repetition**: the same death line ("A carter found you") and
  the same barks forever. A repeated line that changes is the oldest
  trick in run-based writing; use it.
- **A character's "never" broken by accident** (Maeca says "Ashford" on
  meeting you; Vonnra's "the only thing I will ever say to you without
  charging for it" is broken three times).

---

## 7. The plan

In order. Each step makes the next one cheaper.

**Now: the cheap, high-value fixes (data, days not weeks)**
1. Fix the lamps' logic: oil and ember (`LINE_NOTES.md` note 1). Update
   the bible §1 to match.
2. Remove the interface's statement of the twist (`risen_once`), the
   narrator's winks, the name collisions, Maeca's early "Ashford",
   Vonnra's broken "only" (`LINE_NOTES.md`).
3. Plant what Act 2 and 3 will need while it is cheap: the drowning in the
   game's first line; the Warden's "AGAIN?"; Grimtunnel's faith; "gone to
   the Morrow"; Chid's wet cloak; Kell's lamp; item lore for ember and the
   starting gear (`LINE_NOTES.md` §2, §6; `IDEAS.md` I-17, I-19, I-22).
4. Give the nights faces and endings: bosses who speak, a dawn per story
   arena, the line that says what an arena is (`IDEAS.md` I-1, I-4, I-7).
5. Make the town notice: reactive barks and Chid's carter wearing thin
   (`IDEAS.md` I-10, I-15).

**Next: decisions for the bible (before any Act 2 text)**
6. Adopt (or correct) the controlling idea: the debt to the dead.
7. Answer the four open questions (the lamps, Chid, the fire, the
   backgrounds) and write the private timeline.
8. Decide on the ember reveal (`THE_EMBER_REVEAL.md`): take it whole, take
   only its memory rule, or leave ember as the bible has it.
9. Write the third layer of motive for every named person, and choose the
   extremes, one major per act (`REALNESS_AND_EXTREMES.md`).
10. Give the survivor their person (`IDEAS.md` I-11).

**Then: structure**
11. Act 1's last night: the Ford, Relit (`IDEAS.md` I-5), and the fortune
    interrupted (I-28).
12. A story arena on every route (I-3).
13. Act 2 as six nights (I-33), with Pell's numbers as its clock (I-35),
    Sallow's letter first (I-12), and Keegan winning the argument (I-13).
14. Act 3's descent as a single long night; the ending played, not chosen;
    the ending deciding the arenas (I-34).

**Throughout**
15. Hold every new line to the morning reports, to `VOICES.md`, and to the
    checklist at the end of `LINE_NOTES.md`; keep `StoryLint` green; and
    play every branch, not just read it.

---

## 8. Close

The hardest things in this kind of writing are already done here: a town
of people who sound like themselves, a narrator with restraint, a child's
death written so that it hurts and does not wallow, consequences that
travel across acts, and twists built from the player's own hands. Most
games in this genre never get there. What remains is mostly a matter of
joining the two halves of the game so that the nights tell the story the
days are writing, and of being braver with the people: letting them be as
small and as terrible and as kind as people are.

The story is about what we owe the dead and how we keep the lights on.
When the player understands that the light they have burned every night
was the dead, that the gentlest man in the valley sat in the reeds and
watched them drown because he was lonely, and that the person they were
travelling to is down there saying their name, the game will be what the
brief asks: not a polish pass on Diablo, but something that stands beside
the best of its kind.

With respect, and with great enjoyment of the work,

the editor

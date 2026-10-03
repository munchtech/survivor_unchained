# Craft study: dark fantasy, in books, games and film

A working reference for the author of *Survivor Unchained*, built from a
study of the genre's masters and of the editors who shaped them. It is
organised by problem, not by author: each section states principles, the
technique behind each one, named examples, and what it means for this
game. It is meant to be open on the desk while writing.

**How it was made.** Wide web research across author interviews and
blogs, craft essays and lectures, criticism, GDC talks and postmortems,
and writing on editing. Sources are listed per section and gathered at
the end. Published works are paraphrased; quotations are kept to a
sentence or two and attributed. Where a source was available only at
second hand (a summary of an interview rather than the interview), it is
marked *(secondhand)*. Where a reading is mine rather than a source's, it
is marked *(reading)*. Lines from *Survivor Unchained* are quoted freely.

**The sections.** Other files in `docs/editorial/` cite them by number.

- §1 Prose and voice
- §2 Character: arcs, moral complexity, villains who believe they are right
- §3 Twists: fair, earned, re-readable; foreshadowing and payoff
- §4 Structure and pacing: from the personal to the epic
- §5 Theme: cost, corruption, mercy, faith; where grimdark goes hollow
- §6 Worldbuilding: the iceberg, the withheld, the implied history
- §7 Lore in items and places
- §8 Story that grows run by run; play that tells the story
- §9 Barks and reactivity
- §10 Choice, consequence and companions
- §11 Dialogue and subtext
- §12 Lessons from film, television and manga
- §13 Editing: how editors read, diagnose and write notes; checklists

---

## §1 Prose and voice

### Principles

**1.1 Style is the world.** In a secondary world there is no consensus
reality to lean on; every word is creation. Le Guin's "From Elfland to
Poughkeepsie" (1972): "the style, of course, is the book." Her test, the
*Poughkeepsie test*: swap the invented names in a passage for modern
ones (a senator, a ministry). If it still reads like the evening news,
the diction is doing no world-making. Archaism is optional; distance and
consistency are not. *(Le Guin's own worked example is paraphrased from
memory by the researcher.)*

**1.2 Choose speed or spell, on purpose.** Howard's stacked modifiers
accelerate because they are concrete and sit on hard verbs ("kinetic",
in Frank Coffman's reading; Stephen King said the prose "nearly gives
off sparks"). Clark Ashton Smith's rare nouns decelerate, deliberately:
his stated aim was "verbal black magic", prose as incantation. Ornament
fails only when it is abstract ("ineffable"). Ask of a passage whether
it wants to run or to entrance.

**1.3 Understatement carries atrocity.** Glen Cook wanted Croaker to
sound like "sitting in a bar telling the stories", not a bard in a hall;
horror is reported in a clause and passed over, which implies it is
routine, which is worse. The danger is monotony: reviewers of the
*Black Company* found the laconic voice could numb. Vary the rhythm.

**1.4 Tone is the narrator's attitude to violence, not its quantity.**
Guy Gavriel Kay's novels are full of massacre and are not grimdark,
because his narrator grieves: his signature move is to zoom out of a
scene for a sentence and tell you how a minor character's life will end,
then return. Foreknowledge makes the present scene precious. (LARB on
Kay.)

**1.5 Change the prose, not just the opinions, per voice.** Abercrombie
gives each point-of-view character a different *texture*: Glokta's
italic counter-voice, Logen's refrains ("Say one thing for Logen
Ninefingers..."), Ferro's staccato sentences with no colour words at
all, because her inner life has no pleasure in it. He tunes a voice by
revising all of one character's chapters together. (Writer Unboxed
interview.)

**1.6 What a character notices is who they are.** Glokta experiences the
Inquisition as *stairs*, because pain makes stairs the most important
fact in the world (Fantasy-Faction on *The Blade Itself*).

**1.7 Choose the person and tense that embody the psychology.** Jemisin
wrote test chapters in several voices; Essun's second person conveys
"the not-all-here of her", a woman dissociated by trauma (Jemisin's
blog, 2015). Hobb's retrospective first person lets the older Fitz leak
regret, producing dread rather than suspense: "He is a lens, but not
always a perfectly clear one" (Hobb to Andrew Liptak).

**1.8 Soothe or unsettle, on purpose.** Moorcock's attack on "nursery"
prose in "Epic Pooh" (1978) is unfair to Tolkien's war chapters, but it
is a usable line-edit question for a scene of horror: does this sentence
reassure the reader that nothing truly bad can happen? James Enge's only
rule: "Either it works as verbal music or it doesn't."

**1.9 In a high style, contrast keys.** Anna Smith Spark's lyrical
grimdark is kept from cloying by a vulgar, comic soldier's voice and
changes of pace, "deliberately done to change pace and key totally"
(Fantasy Hive). Peake's grotesque mixes "camp and the archaic, gothic
and the farce": comedy and horror as one instrument.

**1.10 One signature narrator, in aphorisms.** *Darkest Dungeon*'s
Ancestor (Wayne June) speaks in one- or two-sentence sayings about
*situations*, not events ("Overconfidence is a slow and insidious
killer"). Sayings survive hundreds of repetitions the way proverbs do,
and one voice holds the whole game together. Chris Bourassa called
writing June into the full game "one of the best decisions we've made"
(Game Developer, Road to the IGF).

### For this game

The narrator's rules in `VOICES.md` ("present tense, second person,
plain nouns and working verbs; one image per line... says what happens
and what can be seen, never what it means") are Cook's understatement
plus Hemingway's omission, and they are kept almost everywhere. The
morning reports are the model (`LINE_NOTES.md` §8). The places where the
narrator slips are winks ("— probably —"), shared lines with the
interface, and repeated images. The per-character voices pass
Abercrombie's test: most lines could be attributed with the names
removed.

Sources: Le Guin, en.wikipedia.org/wiki/From_Elfland_to_Poughkeepsie,
jmbaldwinwriter.substack.com/p/thoughts-on-from-elfland-to-poughkeepsie;
Howard, en.wikipedia.org/wiki/Styles_and_themes_of_Robert_E._Howard;
Smith, en.wikipedia.org/wiki/Clark_Ashton_Smith; Cook,
strangehorizons.com/wordpress/non-fiction/articles/interview-glen-cook/;
Kay, lareviewofbooks.org/article/fantastic-worlds-guy-gavriel-kay/;
Abercrombie, writerunboxed.com/?p=1035,
fantasy-faction.com/2014/character-immersion-and-the-narrative-voice;
Jemisin, nkjemisin.com/2015/08/tricking-readers-into-acceptance/;
Hobb, andrewliptak.com/robin-hobb-the-farseer-trilogy-folio-society/;
Moorcock, en.wikipedia.org/wiki/Epic_Pooh,
jamesenge.com/2025/03/31/swords-against-style/; Smith Spark,
fantasy-hive.co.uk/2018/09/interview-with-anna-smith-spark-the-tower-of-living-and-dying/;
Darkest Dungeon,
gamedeveloper.com/audio/road-to-the-igf-red-hook-studios-i-darkest-dungeon-i-.

---

## §2 Character: arcs, moral complexity, villains who believe they are right

### Principles

**2.1 Grey means a heart in conflict with itself, not general badness.**
Martin calls Faulkner's "the human heart in conflict with itself" his
mantra: Ned's honour against his children's safety, Jaime's honour
against his love. The conflict lives inside one person, not only between
factions. *(secondhand)*

**2.2 Write the villain's book in your head.** Hobb: villains "don't
think of themselves as the villain. They simply have something they want
to get done". The writer must "put it on like a coat". Regal, rewritten
from his side, "would be a tragic hero" (Hobb, Dragonsteel Nexus talk).
Abercrombie prefers "villains with a face... People like us, but who see
things differently" (2012 AMA).

**2.3 The corrupted reformer.** Tolkien's Sauron began "with fair
motives" (Letter 131); Saruman argues for Knowledge, Rule, Order;
Le Guin's Cob opens the door between life and death from fear of dying;
Bakker's Consult try to seal the world off from a hell that is real.
Make the villain *right about the problem and monstrous in the
solution*. *(Letter 131 secondhand.)*

**2.4 Grief is the strongest villain engine.** Kay's Brandin erases
Tigana's very name from grief for his son; the reader wants him dead and
grieves when he dies. Lynch's Grey King avenges his murdered family.

**2.5 Menace through courtesy.** Clarke's Gentleman with the
Thistle-down Hair never threatens like a villain; he gives gifts, keeps
bargains to the letter, and kills to honour his friends. The Lord-
Exchequer in this game's bible ("apologises often and means none of it")
belongs to this family. *(reading)*

**2.6 The mentor turned inside out.** Abercrombie was struck by
Tolkien's remark that in a war allegory Gandalf would have used the
Ring; Bayaz is that Gandalf (2012 AMA). An ally whose agenda the
player cannot override (Morrigan in *Dragon Age: Origins*: "she would do
it regardless of the player", David Gaider to Game Informer) is the
game version.

**2.7 The only one who wants change.** Peake's Steerpike keeps our
sympathy because he is the only person in Gormenghast who wants the
suffocating Ritual to end, and he works through his victims' real
grievances. The villain is right about the problem.

**2.8 Make the monster charismatic, human, wounded, and tested.** Mark
Lawrence's "Clockwork Orange bet": a compelling voice holds the reader
"almost irrespective of what he does, as long as he is clearly human"
(Mythic Scribes). The critique (Liz Bourke) is as instructive: without
an outside view or a cost the narrator registers, the book never puts
moral distance on him. Lawrence's own fix was a second voice (Katherine's
diary).

**2.9 Give the cynic a vocation of care.** Croaker is the Company's
physician; his snark is the armour of a man who patches bodies daily.
Grimness without a caring centre goes hollow (Reactor on *The Black
Company*).

**2.10 The rogue's vices list is as long as the virtues.** Lynch on
Locke: "charming, loyal... and clever" and "self-pitying, morally weak,
careless, and stubborn to the point that he's a danger to himself and
others" (Fantasy-Faction).

**2.11 Arcs can be circles.** Logen vows to be a better man and becomes
the Bloody-Nine again; his refrain ("you have to be realistic") is the
self-justification that tracks the relapse.

**2.12 Heroism in a grim world is a choice made with full knowledge of
the cost, and witnessed.** Gemmell's Druss, sixty, arthritic, comes down
the mountain to die at Dros Delnoch; Rek inherits his courage. Gemmell
wrote *Legend* believing he had cancer; it is about how to die well, not
how to win.

**2.13 A grotesque is one physical exaggeration that shows one
obsession.** Peake's Flay: cracking knees and rigid loyalty.

**2.14 The protagonist needs a want.** Sol Stein's triage questions come
first in any edit: is the conflict stark enough? Is the protagonist
strong enough? Is the antagonist worthy? (Stein on Writing,
*secondhand*.) A protagonist without a want is a camera.

### For this game

Every major NPC in Act 1 believes they are right, and most are partly
right (Pell: "I'm not a good man. I'm a careful one."; Redcowl feeds his
prisoners before his own; Harlan sells to the thing that killed his
sister to keep the Company alive). This is the cast's great strength.
The two gaps are the protagonist's want (`NOTES_BY_ACT.md` §0.4) and an
antagonist with a face for each night (`NOTES_BY_ACT.md` §2.9). Vonnra
is the game's Morrigan (2.6) and should be structured as such.

Sources: Martin,
news.medill.northwestern.edu/chicago/georgerrmartin *(secondhand)*;
Hobb, dragonsteelbooks.com/blogs/the-cognitive-realm/robin-hobb-writing-villians;
Abercrombie 2012 AMA (r/Fantasy); Tolkien Letter 131 via
en.wikipedia.org/wiki/Saruman; Bakker,
jrrtolkien.it/an-interview-with-r-s-bakker/; Kay,
en.wikipedia.org/wiki/Tigana; Lynch, fantasy-faction.com/2011/scott-lynch-interview;
Clarke, stevenhsilver.com/ivsc.html; Gaider,
gameinformer.com (Morrigan, past and present, 2013); Peake,
ebsco.com research starter on the Gormenghast trilogy; Lawrence,
mythicscribes.com/interviews/mark-lawrence/, Bourke at reactormag.com;
Cook, reactormag.com/glen-cooks-the-black-company-is-grimdark-but-never-hopeless/;
Gemmell, en.wikipedia.org/wiki/Legend_(Gemmell_novel).

---

## §3 Twists: fair, earned, re-readable; foreshadowing and payoff

### The theory

**3.1 Surprising yet inevitable, with the weight on "inevitable".**
Aristotle (*Poetics* 1452a): the strongest effect comes when events
happen "contrary to expectation yet on account of one another". He ranks
things that happen *because of* each other above things that merely
happen *after* each other. Test: can the story be retold as "therefore"
and "but", never "and then"?

**3.2 The best recognition arises from the incidents themselves.**
Aristotle ranks recognition by tokens (a scar, a necklace, a found
letter, a convenient confession) lowest; the best is produced by the
plot's own pressure (Oedipus). A ledger entry that tells the hero what
they are is a token.

**3.3 Recontextualise; never invalidate.** After a good twist, earlier
scenes mean *more* (*The Sixth Sense*, Snape's "Always", the *Berserk*
Eclipse). After a bad one they stop counting ("it was a dream"). *The
Usual Suspects* is the edge case: invalidation works only when being
conned is the theme.

**3.4 Fair play.** Knox (1929) and Van Dine (1928): the culprit is on
stage early; every clue is "plainly stated"; no undiscovered poisons.
For fantasy, Sanderson's First Law is the same rule: "An author's ability
to solve conflict with magic is directly proportional to how well the
reader understands said magic." No new power, prophecy or bloodline
introduced to make a twist work.

**3.5 Omit, never lie.** *The Murder of Roger Ackroyd*: the narrator is
the murderer; everything he wrote was true, he left out ten minutes.
Sayers defended it. The fair-play rule for unreliable narrators is
omission yes, falsehood no. Hobb's Fitz, Jemisin's Hoa and Clarke's
narrator all keep it.

**3.6 Prefer the bomb under the table.** Hitchcock to Truffaut: a hidden
bomb gives "fifteen seconds of surprise"; show the audience the bomb and
the dull conversation becomes "fifteen minutes of suspense". Lessing
said the same in the eighteenth century (Bordwell). Most secrets are
worth more as dramatic irony. Save true surprise for one or two
load-bearing turns.

### Techniques of concealment

From Sally and Tony Hope on Christie, and from film:

- **The list.** Hide the clue among more vivid items.
- **Emotional distraction.** Follow the plant at once with something
  louder (a death, a kiss, a joke).
- **Delay.** Plant very early; attach meaning very late.
- **The split clue.** Two innocent halves in different places.
- **Category assumption.** The reader rules out the child, the narrator,
  the victim, the kind priest.
- **The rule that hides the twist is itself the clue.** *The Sixth
  Sense*'s "they only see what they want to see"; *BioShock*'s "Would
  you kindly", said at the start of nearly every instruction.
- **The clue has its own reason to be there.** Wildfire in *Blackwater*
  first appears as a scene about Tyrion's control of the city, so we do
  not notice it is a weapons briefing.
- **The frame is a fair hiding place.** Hobb's chapter epigraphs turn out
  to be Fitz's own biased history; Sanderson's *Mistborn* logbook
  epigraphs carry the twist about the Lord Ruler; Clarke's footnotes
  carry the rules the plot later obeys.
- **Give each clue once.** Wolfe would not give a clue twice, and
  defined a great story as one "reread with increasing pleasure". But
  "complex" needs clear structure or "it's simply confused... a box of
  junk" (Wolfe to Lawrence Person, 1988). The surface read must satisfy
  on its own.

### Making the big turn land

**3.7 Earn the dyscatastrophe** (the Red Wedding pattern): name the
genre expectation you are breaking (Martin: everyone expected the son to
avenge the father, so Robb had to die); root the blow in a character's
*virtuous* choice (Robb marries for honour and breaks his pact); set up
the sacred law that makes it an atrocity (guest right); let the last
clues arrive through the character's senses just before (the music too
loud, the song). Martin could not write the chapter, skipped it, and
came back after finishing the book (60 Minutes, 2019).

**3.8 Earn the eucatastrophe the same way.** Tolkien's "good catastrophe"
"does not deny the existence of dyscatastrophe"; the eagles land
because defeat was real and imminent. Frodo *fails* at the Crack of
Doom; his earlier pity for Gollum is what saves the quest (Letter 246).
Mercy shown early pays off structurally a thousand pages later.

**3.9 Twist the motive, not only the fact.** The most re-readable twists
change *why*: Snape, Griffith's dream, Jemisin's reveal that Damaya,
Syenite and Essun are one woman, which Jemisin built to "trick readers
into caring" about a woman she expected them to hate. The strongest
twist answers "why is this story told this way?"

**3.10 Plant the twist as character before plot.** Ofelia's disobedience
is a flaw before it is her salvation; Griffith's willingness to spend
lives is visible long before the Eclipse. A turn reads as earned when
the trait was already true.

**3.11 Dramatise the decisive choice.** *Game of Thrones* season 8's
"The Bells" had foreshadowed its destination for years and skipped the
path: we never saw the choice under pressure with the alternative
visible (The Ringer, Paste). Gawain's vision at the Green Chapel is the
counter-example: the whole cost of the wrong choice is shown, so the
right one is earned in seconds.

**3.12 Calibrate with readers, in revision.** Sanderson tracks where
beta readers guess: too early, you "overplayed your hand"; never, add
plants; ideal, most readers get it a beat before the reveal. Hobb adds
foreshadowing in final revision, once she knows the ending.

**3.13 Avoid twist inflation and the mystery box.** A reversal at the
end of every chapter becomes the pattern and stops landing; "a mystery
is not necessarily a story" (critiques of *Lost*, *Westworld* season 2).
Several small surprises beat stacked major ones. Michael Stackpole: a
twist should be "strong, quick, and hurt a lot" (Writing Excuses ep. 19).

**3.14 Survive being known.** Crowds guess (*Westworld* season 1). The
real test is whether the story still works when the twist is common
knowledge.

**3.15 The clue in plain sight.** Ronald Knox: the skilled author
flourishes the clue "defiantly in our faces... what do you make of
that?" — "and we make nothing." The most visible place there is (a name,
a title, an idiom) is the best hiding place. *(Knox quoted via
secondary summaries.)*

### A fair-twist checklist

1. The twist-bearing person or thing appears early and openly.
2. Every load-bearing fact is on the page before the reveal.
3. The narrator (and the interface) may omit, never lie.
4. The reveal arises from incidents, not tokens or new rules.
5. It recontextualises; on reread, earlier scenes gain meaning.
6. It changes the protagonist's fortune or moral position (reversal
   and recognition in one beat).
7. It lands on the theme.
8. It is calibrated: most players get it a beat before.

### For this game

The game's twists rated against this list are in `NOTES_BY_ACT.md`.
The models already in the text: Sella's pillow talk quoted in the
fortune (fair, surprising and inevitable, inside Act 1); Nell (a
three-stage recognition); Vonnra's "The water took it, or you left it
on the far bank. Most do." (true twice). The risks: the "what you are"
reveal is the genre's most guessable and is staged with tokens; the
interface says it in Act 1 (`risen_once`); the logic of the lamps is
broken (`LINE_NOTES.md` note 1). `THE_EMBER_REVEAL.md` is an attempt
at 3.7, 3.9 and 3.15 together.

Sources: Aristotle via english.hawaii.edu/criticalink/aristotle/;
Knox and Van Dine, umsl.edu/~gradyf/film/knoxdecalogue.htm and
vandinerules.htm; CrimeReads on the magician's contract; Hope on
Christie, crossexaminingcrime.com (2024 review); Sayers and Ackroyd,
booksbywomen.org; Hitchcock and Lessing,
davidbordwell.net/blog/2013/11/29/hitchcock-lessing-and-the-bomb-under-the-table/;
Sanderson, brandonsanderson.com/sandersons-first-law/,
faq.brandonsanderson.com; Writing Excuses ep. 19; Martin,
cbsnews.com (60 Minutes, 2019); Tolkien,
tolkiengateway.net/wiki/Letter_246, irc.tolkiengateway.net/wiki/Eucatastrophe;
Wolfe, gwern.net/doc/fiction/gene-wolfe/2007-person.pdf; Jemisin,
nkjemisin.com/2015/08/tricking-readers-into-acceptance/; The Bells,
theringer.com (2019), pastemagazine.com; No Film School on twist vs
reveal; Hobb epigraphs,
jeffreydavidoutcalt.substack.com/p/on-the-use-of-epigraphs-and-metanarratives.

---

## §4 Structure and pacing: from the personal to the epic

**4.1 Promise, progress, payoff.** Sanderson: the opening makes
promises (tone, genre, the kind of conflict); the middle shows
*measurable* progress ("people drop off a book [when] there weren't
enough signposts of progress"); the ending pays the promise, surprisingly
but fully. Dark fantasy may break the genre promise (Abercrombie's quest
reaches the edge of the world and the Seed is not there) if it keeps
the tonal promise.

**4.2 Every unit has an inciting incident, a turn, a crisis, a climax
and a resolution.** Shawn Coyne's *Story Grid* "Five Commandments", for
scene, sequence, act and whole story alike. A scene with no value shift
is a candidate for a cut. His Six Core Questions are a developmental
editor's first page: genre; its conventions and obligatory scenes;
point of view; the objects of desire (wants and needs); the controlling
idea; beginning hook, middle build, ending payoff.

**4.3 The epic is built from the personal.** *Arcane* braids a political
war (Piltover and Zaun) with two sisters, so every escalation is a
family wound. Zeynep Tufekci (Scientific American, 2019) argued that
early *Thrones* told *sociological* stories (characters shaped by
institutions and incentives), and that late *Thrones* collapsed into
psychological whim ("she makes it personal"). Do both: institutions
pressing on people.

**4.4 Pacing is part of earning.** Season 8's correct destinations
reached too fast read as fiat; every turn needs its intermediate beats
on the page.

**4.5 Frame betrayal with its aftermath.** *Berserk*'s Golden Age is a
flashback framed by its consequences (the Brand, Guts's hatred), so the
reader loves for twelve volumes what they know will be lost. Pan's
Labyrinth opens on the dying girl.

**4.6 The descent is a structure.** Diablo I is one town and sixteen
levels under a cathedral; each level is a step nearer Hell; the
geography is the plot.

**4.7 Time limits make choices.** *Pentiment* gives each act a few days
before an accusation is due; investigating one lead costs another. You
always judge with incomplete knowledge (Josh Sawyer). Moorcock's pulp
formula: four parts of six chapters, the plot moving significantly by
the end of each quarter; "you don't have any encounter without at least
information coming out of it" *(secondhand, via Colin Greenland)*.

**4.8 Interleaved strands must earn their place.** Lynch admits his
lore-only interludes in *The Lies of Locke Lamora* slowed the book; the
character interludes that pay off in the next present chapter worked.
And let the hero discover the twist, not have the villain explain it.

**4.9 Convergence.** The "Sanderlanche": a long build, then every planted
promise pays off in sequence. The dark version pays off with cost
(Abercrombie's Battle of Adua).

### For this game

Act 1 has clocks (the caravan's four days; the wolves' escalation), the
found-early principle, and an ending that is a recap. Act 2 as written
has twelve beats; `NOTES_BY_ACT.md` §3.1 proposes six, each a night.
Act 3's descent is Diablo's structure (4.6) and should be built as one.

Sources: Sanderson, brandonsanderson.com/blogs/blog/brandon-sandersons-2025-guide-to-plot-lecture-2;
Story Grid, storygrid.com/editors-six-core-questions-part-1/;
Tufekci, scientificamerican.com/blog/observations/the-real-reason-fans-hate-the-last-season-of-game-of-thrones/;
Arcane, reactormag.com; Berserk, thepopverse.com (Miura interview,
2000); Diablo, gamebanshee.com (The Making of Diablo); Pentiment,
shacknews.com/article/146276; Lynch, fantasy-faction.com/2011/scott-lynch-interview;
Moorcock's method, interestingliterature.com/2014/11/michael-moorcock-how-to-write-a-novel-in-3-days.

---

## §5 Theme: cost, corruption, mercy, faith; where grimdark goes hollow

### Where darkness goes hollow

| Failure | Symptom | Counter-example |
|---|---|---|
| Grit as costume | Gore and cynicism with no question. Erikson: "Grittiness for its own sake is all peacock" | Erikson's Itkovian; Cook's Croaker as doctor |
| Unquestioned filth | Violence that revels "without questioning it" (Abercrombie) | Martin's guest right: horror measured against a sacred norm |
| Deaths without attachment | Characters die before we care | Martin: "I try to make you feel them more"; Lynch's Calo, Galdo and Bug |
| No stakes for virtue | Since everyone is bad, no choice matters | Tolkien's pity for Gollum; Severian's knife for Thecla |
| Monotone voice | Endless snark or endless gloom | Peake's farce-gothic; Leiber's comedy setting up the rats |
| Free power | Magic with no price | Stormbringer's soul-debt; Earthsea's "To light a candle is to cast a shadow" |
| Nihilism | Right action "impossible or futile" (Liz Bourke) | Erikson's thief who can "take down a god" |
| Victims as props | Secondary characters exist to die | Lynch; Jemisin's Uche, whose death is the book |

**The common thread** (A1 synthesis): every enduring dark writer keeps
*one thing sacred*, so that it can be desecrated and defended. Tolkien's
mercy; Howard's elegy; Leiber's friendship; Moorcock's Balance and
Elric's remorse; Smith's longing for rest; Le Guin's equilibrium;
Wolfe's slow redemption; Cook's brotherhood; Martin's guest right;
Erikson's compassion. Grimdark goes hollow when nothing is sacred,
because then nothing can be desecrated.

### Principles

**5.1 Earned darkness has five marks:** consequence that persists;
agency (characters choose and can be judged: Jared Shurin includes
agency in his very definition of grimdark); particular victims; a moral
reference point somewhere in the text (not necessarily the narrator);
and hope that is paid for rather than sprinkled ("Hope has to be
earned", Lee Konstantinou on hopepunk).

**5.2 Make the emotional climax an act of absorbing suffering, not
inflicting it.** Erikson's *Memories of Ice*: Itkovian, Shield Anvil of
a war-god, takes into himself the grief of the T'lan Imass, an undead
army hundreds of thousands of years old, and dies of it. The peak of a
book full of massacre is an act of mercy towards the ancient dead. "Compassion
is priceless... It must be given freely. In abundance."

**5.3 The dead may want rest.** In Clark Ashton Smith's "The Empire of
the Necromancers", a raised kingdom of the dead rebels against its
raisers and returns to the grave: the sacred thing in a godless world is
rest *(reading)*. Le Guin's *The Farthest Shore*: Cob opens a door
between life and death, and the world's meaning drains through it.

**5.4 Power is a withdrawal from someone else.** Stormbringer drinks
souls and feeds Elric; Moorcock: "The whole point... was addiction." The
craft lessons (A1, A2): the weapon must *want* things and sometimes win
(it kills Cymoril); the bond is affectionate as well as hateful (it calls
Elric "friend"); give the user a prior, smaller dependency so the reader
sees the trade-up; a small early bargain seeds the end; and let the
weapon speak the last verdict ("I was a thousand times more evil than
thou!"). Hobb's founding question: "What if magic was addictive and the
addiction was completely destructive?"

**5.5 Cosmic horror needs one human who does not kneel.** Guts the
Struggler in *Berserk*: not that he wins, but that he refuses. Small
comforts (Puck, a found family) carry the hope.

**5.6 Comedy is the set-up for the knife.** Leiber's drunken bonding in
"Ill Met in Lankhmar" is the reason the heroes' lovers die; Lynch spends
pages on the twins' jokes before the Grey King kills them; Abercrombie's
jokes lower the guard. Make the reader laugh with the people you will
kill.

**5.7 Beauty can implicate.** Smith Spark wants the reader to feel a
dragon burning a city as "terrible wonderful horrifying annihilating
beauty" and to notice that they did.

**5.8 Refuse consolation in structure, keep wonder.** Miéville lets the
government win in *Perdido Street Station*, and still praises Tolkien's
monsters: the best anti-consolation writers abolish the guarantee, not
the wonder.

**5.9 Faith as discipline, not opposite.** Gemmell's Thirty, warrior-
priests who know the day of their death and go to it; Kay's three faiths
in *Al-Rassan*, each with real devotion. Faith in dark fantasy is most
powerful when it is sincere and costly, not when it is a hypocrisy to
expose.

**5.10 The omelas problem.** A society that lives by one creature's
suffering (Le Guin's "The Ones Who Walk Away from Omelas") is the
strongest available frame for a moral choice about comfort and cost
*(reading)*.

### For this game

The game keeps several things sacred already: Rook's kindness, Chid's
joy, Tam being right, Brannoc's one thank-you, guest-right of a kind at
the Last Lamp. The bible's Morrow is an Omelas (5.10). The Act 3 endings
are a version of Itkovian's choice (5.2): take the suffering in (ending
C), let it go (B), or keep it chained (A). `THE_EMBER_REVEAL.md` makes
5.3 and 5.4 literal: the power the player uses every night is other
people's light, and the dead want rest.

Sources: Erikson, reactormag.com/steven-erikson-talks-with-peter-orullian/,
thecriticaldragon.com/2016/04/18/in-the-dragons-den-interview-with-steven-erikson-part-1/,
en.wikipedia.org/wiki/Memories_of_Ice; Abercrombie and grimdark,
damiengwalter.com/2015/03/08/grimdark-what-is-it-joe-abercrombie-in-discussion-with-ahimsa-kerp/;
Bourke and Shurin via en.wikipedia.org/wiki/Grimdark; hopepunk,
en.wikipedia.org/wiki/Hopepunk; Smith,
en.wikipedia.org/wiki/Clark_Ashton_Smith; Moorcock,
en.wikipedia.org/wiki/Stormbringer; Hobb, buzzymag.com/robin-hobb-interview/;
Berserk, thepopverse.com; Leiber, en.wikipedia.org/wiki/Ill_Met_in_Lankhmar;
Smith Spark, fantasy-hive.co.uk (2018); Miéville,
infinityplus.co.uk/nonfiction/intchina.htm, tolkienlibrary.com;
Gemmell, en.wikipedia.org/wiki/David_Gemmell.

---

## §6 Worldbuilding: the iceberg, the withheld, the implied history

**6.1 Show the far island; do not land on it.** Tolkien (1963) put part
of his book's appeal down to "glimpses of a large history in the
background", like seeing "far off an unvisited island": "To go there is
to destroy the magic, unless new unattainable vistas are again
revealed." Every answered question should open an unanswered one.

**6.2 Mechanisms of depth** (scholarship on Tolkien): casual reference
as if the reader already knows (Éowyn's horn from "the Hoard of Scatha
the Worm", never explained); allusive comparison at a crisis; relics and
ruins; fictive documents and small contradictions as the seams of real
history; different cultures sounding different.

**6.3 A living witness of a greater past** (Elrond remembering the Last
Alliance) establishes decline cheaply, the elegiac note dark fantasy
inherits.

**6.4 Natives do not understand their own world.** Wolfe: the alien
farmer who explains how his society works "ain't necessarily the
truth". Severian does not know his guild's tower is a grounded
spaceship. Implied history is more believable when the locals are
ignorant of it.

**6.5 "Never resolve too much, never explain it all, and never, ever,
reveal everything"** (Erikson). But Erikson paid in readers who gave
up on *Gardens of the Moon*; borrow the principle and give one stable
anchor per section.

**6.6 A limited witness gets mystery for free.** Croaker is not in
charge, so neither he nor we know the grand plan or the menhirs on the
Plain of Fear.

**6.7 Bury the iceberg in documents.** Clarke's two hundred footnotes;
Hobb's epigraphs; Jemisin's stonelore (survival commandments whose
omissions turn out to be political); the Black Company's Annals.

**6.8 Macro to micro.** Jemisin: environment, then disaster, then
culture, then law; Lynch derives Camorr from what a con artist needs.

**6.9 A quarter turn, not a full rotation.** Kay's "history with a
quarter turn to the fantastic": a small fantastical element strips the
reader's smugness about the past.

**6.10 Do not spend the top of the cosmology early.** Miura withdrew the
chapter that explained *Berserk*'s Idea of Evil because it boxed the
story in. Mystery at the top of a world is a resource you can spend
once.

**6.11 Real words carry etymology.** Wolfe's fuligin, destrier,
cacogen are real archaic English; the reader half-feels their roots
*(reading)*. The game's own names (Morrow, Ashford, Low Kiln, the Last
Lamp, Silverstair) work this way already.

**6.12 Keep a private bible the text never breaks.** Martin wrote the
mythic backstory for *Elden Ring* and the game shows only its ruins
(Miyazaki to EDGE and IGN). The iceberg must be consistent under the
water.

### For this game

`STORY_BIBLE.md` is the private bible (6.12) and is unusually thorough.
The text keeps 6.1 and 6.4 well: nobody explains the Legion, the Order
or the Vigil; the iceberg names (the Karrash, the Collegium, the
Glass-sworn, the Low Cloister, Saint Wend's) appear once each. Needed: a
timeline that does not contradict itself (`NOTES_BY_ACT.md` §0.3) and a
glossary so the next writer neither contradicts nor duplicates. The
valley's place names are already the best clue (6.11): "the Morrow",
"Ash-of-Morrow" (`THE_EMBER_REVEAL.md` §5).

Sources: en.wikipedia.org/wiki/Impression_of_depth_in_The_Lord_of_the_Rings;
Wolfe, gwern.net (Person interview, 1988/2007); Erikson,
thecriticaldragon.com (2016); Cook, strangehorizons.com reviews;
Clarke, stevenhsilver.com/ivsc.html; Jemisin,
masterclass.com (worldbuilding), electricliterature.com interview;
Kay, soden.substack.com/p/a-quarter-turn; Berserk,
thefilibusterblog.com on the withdrawn chapter; Elden Ring,
eldenring.wiki.gg/wiki/Interviews, tweaktown.com.

---

## §7 Lore in items and places

**7.1 Write the myth in full; ship its ruins.** FromSoftware's method:
the history lives in a private document; the player gets fragments in
item descriptions, statues and the placing of bodies. Miyazaki traces it
to reading Western fantasy as a child beyond his reading level and
filling the gaps with imagination, and wants players to have that
experience *(secondhand: the Guardian interview, via later reports)*.
He has also said, frankly, "I'm just not good at implementing direct
narrative" *(secondhand, WIRED 2016)*.

**7.2 Item text in two to five sentences.** What it is; who held it;
one detail that hints at a larger tragedy. Never resolve the hint in the
same item.

**7.3 Spread one story across a set.** An armour set or a set of relics
tells one character's arc; collecting them is reading it.

**7.4 Place before text.** Environmental storytelling: a key beside a
body that died reaching it; enemy placement as narration. Miyazaki often
begins area design from the lore.

**7.5 Knowledge can cost.** *Bloodborne*'s Insight reveals hidden horrors
(the Amygdalae on the buildings) and raises your vulnerability to
Frenzy: Lovecraft's idea that knowledge is dangerous, made a mechanic.
The mid-game turn to cosmic horror lands because Insight foreshadowed it.

**7.6 Hide story in sound.** *Returnal*'s narrative director advised
players to listen to an enemy's sounds for hints at the ending.

**7.7 Secrets are narrative in this genre.** *Vampire Survivors*' hidden
characters and absurd unlocks turned discovery itself into the story the
community shared. A dark game can use the same structure with grim
payoffs.

**7.8 Give lore a reader.** *Pillars of Eternity*'s Watcher can read
souls' past lives: a diegetic reason the hero sees the lore in things.

### For this game

Item lore exists for some items (the Warden's lamp-iron, the manuals,
Grimtunnel's lamp) and is the best low-cost channel the game has unused:
starting weapons and ember itself have none (`LINE_NOTES.md` §6). The
survivor already has a reason to read the light in things (they are made
of it). Kell's lamp, which "came back up on its own, still lit", is a
FromSoftware item waiting to be found.

Sources: denofgeek.com (Miyazaki); en.wikipedia.org/wiki/Hidetaka_Miyazaki;
eldenring.wiki.gg/wiki/Interviews; unwinnable.com/2024/01/12/bloodbornes-fresh-insight-on-cosmic-horror/;
gamingtrend.com (Returnal, Gregory Louden); filmstories.co.uk
(Vampire Survivors); en.wikipedia.org/wiki/Pillars_of_Eternity.

---

## §8 Story that grows run by run; play that tells the story

### Run-based narrative

**8.1 Give the fiction a reason that failure moves the story.** Greg
Kasavin started *Hades* from the observation that "you don't really die
for real in roguelike games": make the hero immortal, make death a
return home, and "take the sting out of failure". Death is where the
story happens.

**8.2 Characters notice the loop.** When you reach a boss for the
fiftieth time, "why not have the characters acknowledge and be self
aware of the cycle?" (Kasavin, LudoNarraCon). Meg remembers last night's
fight. The feeling Kasavin aims at is someone noticing your haircut:
being noticed "makes you feel good".

**8.3 Ration conversation per cycle.** One exchange per character per
return home: it rations content over hundreds of runs, makes each
exchange deliberate, and stops a player mining a character dry.

**8.4 Gate by conditions, with priority.** *Hades* has more than 22,000
lines (over 300,000 voiced words, from a studio of under twenty). Each
line has requirements (what has been seen; which boss beaten with which
weapon); story-critical beats outrank relationship, which outranks
flavour, which outranks fallback *(the priority scheme is reported by
players and later accounts; the GDC talk was not watched)*.

**8.5 The first clear is a turn, not the end.** Zagreus escapes and is
pulled back; the family plot advances with each clear; the credits come
on the tenth; an epilogue feast rewards long-term play.

**8.6 Never make the player re-read story.** Alexis Kennedy called
*Sunless Sea*'s split between permadeath roguelike and story RPG his
"biggest mistake": players hated re-reading early stories after each
death. Skip, summarise, or react to the repeat.

**8.7 Give legacy between failures.** Sunless Sea's successor captain
inherits a chart; *Hades* keeps keepsakes and the Mirror. A lost run
keeps something the story can mention.

**8.8 Author the fires; let the player walk between them.** Failbetter's
image of "campfires in a darkened desert" *(via IF50's summary)*: big
hand-made beats, with systemic storylets between. Two named shapes fit
this game exactly: the **Carousel** (states that cycle, such as morning,
evening and night, changing what is available) and the **Midnight
Staircase** (push on for a better payoff at greater risk).

**8.9 Make the respawn diegetic.** *Dead Cells*: "The Beheaded is not a
person; it's a concept of survival" *(secondhand)*. *Returnal*: Selene
finds her own corpses carrying logs from other loops. *Planescape*:
dying is sometimes the key to a door.

### Harmony between play and story

**8.10 Audit every verb against the theme.** Clint Hocking's
"Ludonarrative Dissonance in Bioshock" (2007): the game's *ludic*
contract rewarded self-interest while its *narrative* contract forced
you to help Atlas; "a powerful dissonance between what it is about as a
game, and what it is about as a story". The lesson is not "never
constrain", but do not let the mechanics argue the opposite of the
story unless the story is about that contradiction.

**8.11 Harmony done right.** *Hades* (death is going home); *Darkest
Dungeon* (stress is losing control of people: Bourassa, "we wanted to
communicate that by making you lose your grip on them"); *Bloodborne*
(knowledge raises danger); *Inscryption* (sacrifice is both the core
mechanic and the theme: Daniel Mullins pushed it as far as the avatar
sacrificing body parts); *Planescape* (immortality is the curse).

**8.12 The body count needs a fiction.** A survivors game makes the
hero kill thousands a night. The fiction must account for it, or the
day story feels hollow (B research, applying Hocking).

**8.13 Inner voices for abilities.** *Disco Elysium*'s twenty-four
skills each talk; your build decides which voices you hear, so the build
is a character (Robert Kurvitz credits *Planescape* as one of the "two
biggest favors" anyone did him).

### For this game

This is the section that matters most for *Survivor Unchained*, and it is
where the game is weakest: the night arenas, where most play happens,
carry almost no story, and their result says "The story goes on."
`EDITORIAL_LETTER.md` problem 1 and `IDEAS.md` I-1 to I-8 apply 8.1 to
8.12 directly. The game has a gift most roguelikes lack: its respawn is
*already* its secret (the survivor is Unchained; 8.9), and the ember that
resets each dawn can carry memory (8.10, 8.11; `THE_EMBER_REVEAL.md`).

Sources: Hades,
screenhub.com.au (Kasavin, LudoNarraCon),
gamedeveloper.com/design/roguelikes-and-narrative-design-with-i-hades-i-creative-director-greg-kasavin,
inlander.com (Kasavin interview), invenglobal.com (Supergiant),
gdcvault.com/play/1026975/Breathing-Life-into-Greek-Myth; Sunless Sea,
gamedeveloper.com/audio/postmortem-failbetter-games-i-sunless-sea-i-;
Failbetter, if50.substack.com/p/2009-fallen-london,
emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/,
emshort.blog/2019/11/29/storylets-you-want-them/; Hocking,
clicknothing.com (2007); Darkest Dungeon, killscreen.com,
gamedeveloper.com (affliction system deep dive); Inscryption,
gamedeveloper.com/design/how-game-jam-sacrifices-became-inscryption;
Dead Cells, en.wikipedia.org/wiki/Dead_Cells; Returnal, gamingtrend.com;
Disco Elysium, gamebanshee.com, pcgamer.com.

---

## §9 Barks and reactivity

**9.1 Barks are rules, not scripts.** Elan Ruskin's GDC 2012 talk on
Valve's response system (*Left 4 Dead 2*, *Dota 2*): an event sends a
query (who is speaking, what just happened, where, who is near, what has
been said already); every line is a rule with criteria; the rule that
matches the *most* criteria wins. Specific lines beat general ones; the
general ones are the fallback. Memory is just more facts ("said X").

**9.2 Players treasure the rarest line.** Robert Yang's commentary on
the same system: the most specific match produces a "self-branching
structure", and players prize the lines that show the game noticed
something unusual.

**9.3 Write a fallback for every event; layer specifics on it.** The
system improves the more is added.

**9.4 Escalate rather than repeat.** Store "already said"; the third
time is different from the first.

**9.5 Barks as aphorisms survive repetition** (*Darkest Dungeon*, §1.10).
Write per *situation class* with four to eight variants.

**9.6 Tie voice to a state meter.** *Darkest Dungeon*'s afflictions
change both the mechanics and the bark pool: each class has its own
lines per affliction, spoken *before* the hero acts on their own. The
player learns to read the bark as a warning.

**9.7 A bark must trigger, inform and characterise** (How To Write A Game
substack); and audit for frequency (a line heard forty times an hour
must be bland enough to survive or have enough variants) and for
shaming (an in-character line that mocks failure can be bad for the
player).

**9.8 Remember the unforgivable.** Krystian Majewski's critique of Ken
Levine's "narrative Lego" Passions: meters have no memory ("The fact
that I destroyed an entire town wasn't a big deal anymore" after small
favours) and turn people into vending machines. Big acts need permanent
flags.

### For this game

The barks are well voiced and almost wholly static; the data needed to
make them reactive (the `cb:` history, facts, deaths) already exists.
`LINE_NOTES.md` §10 proposes the rule (a bark per settled thread per
person) and examples. The game already has a very good *memory of the
unforgivable* (Greymuzzle's promise; the burned Roost; Rook's kitchen).

Sources: gdcvault.com/play/1015528/,
emshort.blog/2012/03/16/gdc-2012-talk-on-dynamic-dialogue/,
blog.radiator.debacle.us/2012/07/rule-databases-for-contextual-narrative.html;
howtowriteagame.substack.com/p/how-to-write-video-game-barks;
gamedeveloper.com/design/stepped-on-a-narrative-lego.

---

## §10 Choice, consequence and companions

**10.1 No right answer, and no neutral one.** Sawyer on *Pentiment*:
"there cannot be a right answer"; there is no canonical killer.
Sapkowski's "The Lesser Evil": Geralt's attempt at neutrality ends in the
massacre at Blaviken. Neutrality is a choice with fallout.

**10.2 Separate the choice from its consequence in time and place.** The
Bloody Baron (designed by Paweł Sasko, written by Karolina Stachyra):
the choice at the Whispering Hillock lands hours later on the orphans of
Crookback Bog. Players cannot easily connect or save-scum it, so it
feels like fate. *Pentiment*'s town remembers your accusation for
decades.

**10.3 The client is the culprit.** Stachyra's turn: "a man who asks you
to find his family turns out to be someone who actually ruined this
family" (Kotaku). And the mirror: the Baron and Geralt as "two fathers
who lost their loved ones" (Sasko).

**10.4 A big choice should make the player stand up and walk.** Marcin
Blacha (CD Projekt): the player "puts the controller away, stands up,
and starts walking, thinking about the choice" *(secondhand)*. Remove
morality meters for the big ones; let the world be the meter.

**10.5 The story bends, never dead-ends.** Larian's "n+1" fallbacks for
when "the player fucked up everything"; plot-critical items always end
up with you (Swen Vincke). And: "The main character of the game is the
person playing the game... therefore that's the canonical story" (Adam
Smith).

**10.6 The cost of reactivity is real.** Larian's companion-combination
spreadsheets: "row after row after row, and it takes a small army"
(Chrystal Ding); a writer played one branch set eighteen times.

**10.7 Some choices express character, not outcome.** *Kentucky Route
Zero* lets you choose how Conway remembers his past; *80 Days* puts
choices at the line ("do I meet their eye?"). Not every choice should
fork the plot.

**10.8 Every companion carries the central question in their own form.**
*Planescape: Torment*'s "What can change the nature of a man?" is asked
by Ravel and lived by Dak'kon, Annah, Fall-from-Grace and Morte. Eric
Fenstermaker (*Pillars*): themes "as questions rather than as moral
suggestions".

**10.9 A companion needs a place to shine and a payoff.** Avellone's
process: decide where they shine mechanically; give a barebones
background uncovered by talk; find a tone; weave in the theme; make
sure "the player should feel that they are gaining something of value
from the interaction".

**10.10 Fill amnesia with guilt.** *Planescape*'s Nameless One is
surrounded by people who remember what he did. The *Dark Urge* in
*Baldur's Gate 3* adds an inner voice urging murder. Amnesia works when
other people hold the memory.

**10.11 Origins that come back.** *Dragon Age: Origins*' six beginnings
return later (the Dwarf Noble meets the brother who framed them). A
background is a debt the plot pays.

**10.12 The final antagonist can be a severed part of the hero.** The
Transcendent One is the Nameless One's mortality; Le Guin's Ged names
his shadow with his own name.

### For this game

The consequence ledger (bible §10) is 10.2 done with discipline, and
Nell's irons are the Bloody Baron in one smith. The game's risk is 10.6:
the reactivity per thread in Act 1 is admirable and cannot be sustained
across Act 2's twelve beats. The backgrounds promise origins (10.11)
that do not yet come back (a hunter who grew up in Thornhollow, whom
nobody knows; a devout raised by a "dead" order). The central question
(10.8) is already carried by every NPC: each owes the dead
(`NOTES_BY_ACT.md` §0.1).

Sources: Pentiment, shacknews.com/article/146276,
thegamer.com/interview-obsidian-josh-sawyer-pentiment/; Witcher,
kotaku.com (Bloody Baron, 2015), shacknews.com/article/94509,
gamedeveloper.com (Sasko's ten lessons, GDC 2023),
notebookcheck.net (Blacha); BG3, 80.lv (Ding, Smith), rpgsite.net
(Dark Urge), gamespot.com ("The Box That Broke Baldur's Gate 3");
KRZ, funambulism.com (2013), rhizome.org; 80 Days, if50.substack.com;
Planescape, gamedeveloper.com (Avellone interview), metafilter.com/119296;
Avellone on companions, gamebanshee.com/kahp; Pillars,
rpgcodex.net (Fenstermaker); Dragon Age, en.wikipedia.org/wiki/Dragon_Age:_Origins.

---

## §11 Dialogue and subtext

**11.1 The speaker is identified by what is said.** Wolfe: what one
character says in a situation "is not the speech that [another] would
make under that circumstance... if the reader is intelligent, [she]
knows who said that from what was said."

**11.2 The violence is under the courtesy.** Hobb's court speech: Chade
and Fitz talk about poisons and never say "son"; Regal's menace is
politeness. The narrator misreads the subtext and the reader reads it
correctly.

**11.3 Proverbs carry culture and threat.** "A Lannister always pays his
debts" is a boast that context turns into a threat. House words and
mottos compress a culture into a line.

**11.4 Resist the Urge to Explain.** Browne and King's R.U.E.: if the
line and the action carry the feeling, do not add the explanation.

**11.5 Myth economy.** *Conan the Barbarian* (1982): long stretches with
no dialogue, and then lines short and ritual enough to sound ancient.
Sparse lines feel old precisely because they are sparse.

**11.6 Banter is characterisation and set-up.** Lynch's Locke and Jean;
Cook's sappers. The low voices keep the high voices honest (Erikson's
soldiers beside his gods).

**11.7 Always-forward conversations for story beats.** Cardboard
Computer built "always-moving-forward conversations" instead of the
hub-and-spoke question menu, for scenes that must move.

### For this game

`VOICES.md`'s "never" rules (Rav never names his brother; Redcowl never
says Ashford; Vonnra never answers yes or no) are 11.1 and 11.2 made into
house law, and the single written exception per rule is a superb device:
breaking it *is* the scene. The hub-and-spoke dialogue (a hub of
questions) is right for the town and wrong for the big beats; the fortune
and Brannoc's Nell scene already run forward, and every Act 2 and 3 story
beat should (11.7).

Sources: Wolfe, gwern.net (1988 interview); Hobb, A2 dossier (reading);
Browne and King via fictionfoundry.alumni.columbia.edu/seffw;
Conan, reactormag.com/the-brilliant-ambiguity-of-conan-the-barbarians-riddle-of-steel;
KRZ, funambulism.com/2013/07/23/interview-cardboard-computer-on-kentucky-route-zero/.

---

## §12 Lessons from film, television and manga

**12.1 Commit to a register.** Boorman's *Excalibur* has to do with
"mythical truth, not historical truth": formal, incantatory dialogue
that strengthens the myth. Half-naturalistic, half-mythic speech sounds
like a costume party.

**12.2 The land and the king are one.** In *Excalibur* the realm decays
and blooms with Arthur's integrity. Externalise moral state into the
world, so the audience sees the cost of a choice without being told.

**12.3 The antagonist is the consequence of the hero's choice.** Mordred
is Arthur's sin grown up in golden armour; Jinx grows from Vi's "jinx";
Griffith's fall begins when Guts leaves.

**12.4 Mirror the plots visually.** *Pan's Labyrinth*'s Pale Man at his
banquet rhymes with Vidal at his dinner: del Toro said the Pale Man
"represents fascism and the Church eating the children when they have a
perversely abundant banquet in front of them".

**12.5 Plant the virtue as a flaw.** Ofelia's disobedience costs her at
the Pale Man's table and saves her brother at the end.

**12.6 Keep one hard clue on each side of an ambiguity.** The chalk door
keeps *Pan's Labyrinth*'s "real or imagined?" a genuine either/or.

**12.7 Image, music and ritual over exposition.** *Conan*'s first fifteen
minutes are almost wordless; the silent Night King at Hardhome
frightens more than the battle.

**12.8 Let the villain argue the theme better than the hero.** Thulsa
Doom's "flesh is stronger" speech, delivered from total power, is the
film's counter-argument; the climax answers an argument, not just a
fight.

**12.9 Close the arc; leave the facts.** *The Green Knight* does not say
whether Gawain dies; it says he chose honour. Ambiguity about meaning
frustrates; ambiguity about fact can satisfy (Lowery: "that doesn't mean
that he's dead"). And its vision of a cowardly life earns the right
choice in seconds.

**12.10 Give the audience the knowledge a character lacks at the break.**
In *Arcane* we see Vi try to come back; Powder never does. Her turn is
tragic, not villainous, because her misreading is reasonable.

**12.11 Villains who love someone give us a door into them.** Silco and
Jinx.

**12.12 Frame the betrayal with its aftermath, and build the friendship
backward from the wound.** Miura began with anger: "if Guts is angry,
there is going to have to be an object of that anger... the idea of
making the target of Guts' anger a friend... naturally came to mind"
(2000 interview).

**12.13 The Brand.** *Berserk* makes a theme (marked by trauma, never
safe) into a recurring device: the Brand bleeds when evil approaches, so
every night is a siege. *(reading: the closest analogue anywhere in the
study to this game's nights.)*

**12.14 Tell sociological stories too** (Tufekci, §4.3).

Sources: Excalibur, moriareviews.com/fantasy/excalibur-film-1981.htm,
dmrbooks.com (2023); The Green Knight,
en.wikipedia.org/wiki/The_Green_Knight_(film), slashfilm.com;
Pan's Labyrinth, faroutmagazine.co.uk/meaning-the-pale-man-pans-labyrinth/,
hypercritic.org; Conan, en.wikipedia.org/wiki/Conan_the_Barbarian_(1982_film),
reactormag.com; Game of Thrones, see §3 and §4; Arcane, reactormag.com;
Berserk, thepopverse.com (2000 interview), en.wikipedia.org/wiki/Griffith_(Berserk).

---

## §13 Editing: how editors read, diagnose and write notes

### The levels

| Level | Addresses | Delivers |
|---|---|---|
| Developmental (structural) | Premise, structure, plot, character, point of view, pacing, stakes, theme, genre promises | An editorial letter, plus margin notes |
| Line | Sentence and paragraph: rhythm, clarity, word choice, voice, redundancy, dialogue flow | Tracked changes and queries |
| Copy | Spelling, grammar, punctuation, consistency, cross-reference; builds the style sheet | Tracked changes, style sheet, queries |
| Proof | Typos and format in final proofs | Marked proofs |

(Editorial Freelancers Association; Reedsy; Chicago practice of light,
medium and heavy copyediting.) Order matters more than labels: big to
small. Sol Stein calls it **triage**: fix the life-and-death issues first
(is the conflict stark enough; is the protagonist strong enough; is the
antagonist worthy) before polishing sentences in scenes that may be cut.

### How great editors read

- **Perkins** (Scribner's): the book belongs to the author; "He never
  tells you what to do... he suggests to you... what you want to do
  yourself" (Roger Burlingame). His Gatsby letter (1924) is the model
  note: sincere, specific praise; then two structural problems, each
  described as the reader's experience ("Gatsby is somewhat vague. The
  reader's eyes can never quite focus upon him"); a direction rather
  than a draft (his history could come out "bit by bit"); and the
  solution left to Fitzgerald, who moved Gatsby's past earlier. *(The
  full letter was not retrieved; two phrases are confirmed.)*
- **Lish and Carver**: the cautionary tale. Lish cut *Beginners* by
  about half and rewrote endings; "A Small, Good Thing" lost the baker's
  apology and the shared bread, its grace. The test of an edit: does it
  make the book more like itself?
- **Gottlieb**: "Our job is to serve the word, serve the author, serve
  the text"; readers should not see the editor's hand.
- **Toni Morrison** as editor: tailored to each author; mentor,
  advocate, line and structural editor; editing includes advocacy.
- **Susan Bell** (*The Artful Edit*): "To edit is to listen, above all."
  Get distance (time, a different format, reading aloud) to hear what is
  on the page rather than what was meant.

### Diagnose, don't prescribe

Neil Gaiman: "when people tell you something's wrong or doesn't work for
them, they are almost always right. When they tell you exactly what they
think is wrong and how to fix it, they are almost always wrong." So a
note is: **symptom** (the reader's experience) → **location** → **likely
cause** → **why it matters** (which promise or theme it undermines) →
**one to three possible approaches**, offered as options → a **question**
back to the author. Praise should be specific and true, so the author
knows what to protect; criticism specific and ranked. (Formulaic
praise-criticism-praise trains the writer to discount the praise.)

### The editorial letter

1. Framing: what was read, how the letter is organised; the book is the
   author's.
2. What the book is, in your words (if it surprises the author, that is
   the most important note).
3. What works, specifically, ranked, so it is protected.
4. Major issues ranked by impact, each as symptom, location, cause,
   stakes, approaches.
5. A twist and setup/payoff audit where relevant.
6. Secondary issues.
7. Line-level patterns (not a line edit): recurring habits with an
   example or two.
8. Answers to the author's own questions.
9. A revision plan: the order of operations.
10. Close: encouragement tied to this book's potential.

### Checklists

**Developmental pass.** Read once without marking; write a paragraph on
what the work is trying to be. Then: premise and promise (paid?); genre
conventions present and freshened; controlling idea in one sentence;
protagonist's want and need, active choices; a worthy antagonist with an
argument; stakes personal, relational and world-level, escalating;
beginning hook, middle build, ending payoff; every scene has a value
shift; causality reads "therefore/but"; each major character turn has a
setup, intermediate beats and an on-page choice; a fair-play audit of
every twist; a setup/payoff ledger; point of view and withholding
licensed by the frame; worldbuilding rules established before they solve
problems; proportion; the sociological layer; the ending closes the arc.

**Line pass.** Voice against the voice bible; show and tell; R.U.E.;
dialogue mechanics; repetition and echoes ("once is usually enough");
flab; specificity; rhythm (read aloud); register discipline (no modern
idiom in a mythic voice unless meant); clue sentences neutral enough to
hide and clear enough to be fair.

**Copy pass, with game additions.** Agree the level and house style;
keep a style sheet (names, invented terms, capitals, numbers); continuity
(names, ages, wounds, day counts, who knows what when); and for games:
string IDs and named placeholders intact; no sentence built by
concatenating strings; plural and gender handling; translator context
(who speaks, to whom, tone, length); budget thirty to forty per cent
expansion for German and more for short strings; bark variant counts and
repetition; voice-over matches subtitles; every branch condition checked
("can this line fire if X is dead?"); no text baked into images.

### For this game

`VOICES.md` is already a voice bible, `STORY_BIBLE.md` a private myth
bible, and `StoryLint.cs` an automated continuity editor (unreachable
nodes, journal lines never earned, facts asked about but never set,
pronoun drift). That is unusually good editorial infrastructure. Missing:
a world glossary and colour sheet (proper nouns, colours that mean
factions), a timeline, and localisation notes (several dialogue lines
are built with `{name}` mid-sentence, which is fine; check that none are
concatenated, and that the `sex`-gated variants cover every addressed
line).

Sources: the-efa.org/editorial-services-definitions/;
reedsy.com/editing/copy-editing; killzoneblog.com (Stein, via Meg
Gardiner); blog.loa.org/2010/09/maxwell-perkins-editor-of-f-scott.html,
flavorwire.com (Gatsby letter); nybooks.com/articles/2010/05/27/two-raymond-carvers/,
themillions.com; npr.org (Gottlieb, 2023); thenation.com (Morrison as
editor); saranwrappedletters.substack.com (Susan Bell);
Gaiman via killzoneblog.com/2010/02/ten-rules-for-writing-fiction.html;
storygrid.com; radicalcandor.com; Netflix Games internationalisation
requirements; gridly.com; alconost.com.

---

## Thirty principles to keep on the desk

1. Style is the world (Le Guin). Run the Poughkeepsie test.
2. Report atrocity in a clause and move on (Cook); vary the rhythm.
3. Tone is the narrator's attitude to violence, not its amount (Kay).
4. What a character notices is who they are (Abercrombie's Glokta).
5. Every villain is the hero of their own book (Hobb's Regal).
6. Right about the problem, monstrous in the solution (Tolkien's Saruman; Peake's Steerpike).
7. Give the cynic a vocation of care (Cook's Croaker).
8. The protagonist needs a want (Stein's triage).
9. Surprising yet inevitable; "on account of one another" (Aristotle).
10. Recognition from the incidents, never from tokens (Aristotle).
11. Recontextualise, never invalidate (*The Sixth Sense*; Snape).
12. Omit, never lie (Christie, Sayers).
13. Prefer the bomb under the table (Hitchcock).
14. Earn the dyscatastrophe: a virtuous choice, a sacred law, sensory last clues (the Red Wedding).
15. Dramatise the decisive choice (the failure of "The Bells"; Gawain's vision).
16. Show the far island; do not land on it (Tolkien).
17. Natives do not understand their own world (Wolfe).
18. Never explain it all (Erikson); give the reader one anchor.
19. Write the myth in full; ship its ruins (FromSoftware, Martin).
20. Keep one thing sacred so it can be desecrated (the canon's common thread).
21. The climax can be absorbing suffering, not inflicting it (Erikson's Itkovian).
22. Power is a withdrawal from someone else; the weapon wants things (Moorcock's Stormbringer).
23. Cosmic horror needs one who will not kneel (Miura's Guts).
24. Make failure move the story (*Hades*).
25. Characters notice the loop; the boss remembers (*Hades*).
26. Never make the player re-read story (*Sunless Sea*).
27. Barks are rules; the most specific match wins (Valve, Ruskin).
28. Separate choice from consequence in time and place (the Bloody Baron).
29. Audit every verb against the theme (Hocking; *Inscryption*).
30. Diagnose where it hurts; leave the cure to the author (Gaiman, Perkins).

---

## A note on the sources

The research behind this study ran to about 280 searches and fetches
across four parallel lines of inquiry (literary foundations, modern dark
fantasy, game narrative, and film, twists and editing). Some primary
sources could not be opened and are cited through reputable secondary
accounts; those are marked *(secondhand)* above. In particular: Le
Guin's and Moorcock's essays in full, Abercrombie's "The Value of Grit",
the Guardian's 2015 Miyazaki interview, most GDC Vault videos, the full
Perkins Gatsby letter and the Paris Review's Gottlieb interview. Any
quotation drawn from these should be checked against the original before
it is reused in public.

# The big twist: three options for the owner

> **Decided (11 October):** the owner took **A and B together**; C is dropped.
> He still wants a bigger, whole-game "WHAT THE FUCK" moment: "those are just
> like 'ohhh yeahhh'". The next writer proposes it (`docs/handoff/story.md`).

The writer, 11 October 2026. The owner: "we need a big twist nobody sees
coming, maybe chid being evil?" A twist nobody sees coming is planted from the
first scenes, so it has to be chosen before the early lines are recorded. Here
are three. Each one is tested against the editor's six tests (the false
belief, five or more re-reads, fair but hidden, "it was obvious", a real cost,
the player's own hands).

The four approved twists stay in every option: "You did this" (Act 1),
"Ninety-two" and the woman with the lamp (Act 2), the voice (Act 3).

**Recommendation: A.** Ranking A, B, C. A and B don't conflict, so the owner
could take both. A and C are two readings of the same night, so it's one or
the other.

---

## A. "Not yet": Chid made you

**The false belief.** Chid is the one harmless person in the valley: a fool,
two hundred years old, who carries you home every time you die and never asks
anything of you. By Act 2 the player has "solved" him. He's Unchained, he's
"C.", and they dread losing him at dawn (the editor's irony, kept). Solving
the secret they were shown hides the one they weren't.

**The truth.** For two hundred years Chid has been alone. The Order's keepers
watched in pairs: one asks "Is it morning?" at the end of the watch, and the
other answers "Not yet", "so nobody has to sit up the whole night on their
own" (his own words, `chid.office_end`). His other keeper was Tobin, who
became the Warden. When the irons were lit last winter, Chid went down to the
reeds every night and watched the drowned get up, hoping one would get up
*with its mind*. Twenty-five rose mindless, Nell among them, and he warned
nobody. Then the survivor's mother came to the Waystation, dying, with a child
on the road. Her hands were bad, so Chid wrote her letter for her, and he
chose its words: *Come home by the Low Ford. I'll be at the water with a lamp,
so you'll see me.* On the seventh evening he walked her down to the water's
edge and held her hand while the Warden took her. She would be down there
first, holding on, when her child drowned. Vonnra drowned twenty-six and made
nothing. The fool across the square made the survivor in a week, for company.

He doesn't scheme after that, and he doesn't have to. Everything he does for
the survivor on screen is true kindness, and it is tending what he made.

**The reveal (three beats; the last is the twist).**
1. **C32, Rook's kitchen** (Act 2's end), inside the bigger reveal: "Her hands
   were bad. Chid wrote it for her; I took it to the carrier. ...The last
   night he went down with her. Said she oughtn't to be on her own." The
   player, reeling from the cut-down, hears comfort.
2. **C42, Chid's truth** (Act 3): he is Unchained, "C.", Tobin's keeper. Asked
   about her: "I sat with her at the edge. I held her hand. ...She wasn't on
   her own." That builds the false belief: he comforted her as she died.
3. **C43, the voice:** after "I came up with you.", a new choice, "How did
   you get down here?" Her answer, plain as all her lines: "The kind one
   walked me to the edge. He'd written that I'd be at the water, so you'd see
   me. ...He held my hand while it took me. He said you'd come up yourself,
   if I was down here first."
4. **The coda** (after any ending, his bench at dawn): "She told me." He: "...Did
   she. (He smiles: she is in there, and it worked.) I only wanted somebody
   to answer." Then the game's last choice, the mirror of its first: "Is it
   morning?" (Nod.) lets him go. (Say nothing.) he lets go anyway, as Tobin
   did. **"Not yet."** is new: the Order's answer, and the art the player has
   risen by all game. He sits up alone, every night, for good, which is what
   he gave Tobin. (The coin's "Oh, my knees!" stays where it falls.)

**The seeds** (most are already in the data, written innocent; new ones
marked).

| Where | What it says or shows | First read | Re-read |
|---|---|---|---|
| C01 `cin_drowned_fire`, shot 6 | the letter in her coat, run to blue water | home, her mother failing | he wrote it, and its route |
| Prologue (`Prologue.cs`), the ford after the Warden falls (**new**, staging) | across the water, in the reeds, someone standing very still; gone when the camera comes back. Optional narrator line: "In the reeds on the far bank, someone is standing very still." | a drowned, a lampling, a watcher | the mother, narrating her killer plainly |
| `rook.first` | "Chid came in babbling about blue lights going out at the crossing, and here you are" | the town fool saw the fight | he was there all night, and home before you |
| Day 2's morning (treatment §3.3; **not yet in the data**) | Chid brought a woman in from the ford before light and buried her behind the shrine. "Nobody's claimed her." | he buries the drowned | he knew her name, and left it off the marker |
| `chid.first` (**one direction added**) | "(He looks at you a moment longer than people do.)" | he knew your mother at the shrine (C32 explains it innocently) | he's looking at what he made |
| `chid.woke`, `chid.carter`, `chid.carried_who` | "A carter found you"; "Oh, somebody kind. There are more of them about at night than you'd think." | a white lie, a running joke | he follows you every night |
| `chid.before` | "It's been a long time since I saw anyone do that. I'd forgotten how it looks." | an old man's wonder | he made it happen |
| `chid.names`, `chid.names_write` | "Write the names down... It always takes the names first." / "(He watches you write it, and doesn't look at what.) Good. Keep it somewhere dry." | tact | he doesn't need to look: she told him the word. And "dry": the letter, the water |
| `chid.office`, `chid.office_end`, item `keepers_office` | "One keeper asks, and the other one answers, so nobody has to sit up the whole night on their own." Last page: "Is it morning? Not yet." | tenderness; a gift | his motive in his own words |
| The art *Not Yet* (Act 2 on) | she rises by his answer | a power | the player's own hands, every rise |
| `chid.t_chid` | "They're all gone now. I keep thinking I'll get used to that. I keep not." | grief | loneliness that will do anything |
| `chid.shrine` | "It was never for seeing by... it was for keeping company." | the Order's lore | himself |
| `chid.warden` | "That's the trouble with guards: they outlast whatever they were guarding against, and then they guard against us." | a wry line | Tobin guarded the crossing against him |
| Ashe's trunk (`Waystation.cs`, `say.a5b99f61e011`), `chid.note` | "ember shards, a purse, and a note: 'Keep the lights lit. — C.'" | a friend's note | he once paid the Watch's old captain to burn ember at the ford; Ashe kept the purse and never did |
| `chid.cb_nell`, C08 | "She was very light." He sings her down flat. | grief with a laugh | he watched her drown from the reeds |
| C32, C42 (Act 2 and 3; new) | "he went down with her"; "She wasn't on her own." | comfort | the walk to the edge |

**Why nobody sees it, and why it's obvious after.** Chid is the comic relief,
the gentlest man, and the one secret the game lets the player solve early.
His kindness is real on every screen, so no seed reads as a threat. After
C43, a replay finds him everywhere: at the ford that night, home before you,
burying her, watching you write the word without looking, giving you the
words you rise by.

**The emotional spine.**
- **Brannoc:** untouched. One shade, never pressed: Chid watched Nell drown and
  sang at her grave.
- **Maeca and Holloway:** untouched.
- **Her mother:** deepened. Her death gets a hand, and the voice that kept the
  player company exists because of a murder done for company. The summit
  (C43) gets its knife at the moment of most warmth. Her love is untouched:
  she went to the edge to be seen. The narrator's every plain line about Chid
  re-reads as a mother describing her killer to her child, because she must
  never say what it means. The risk is one blow too many on her; it's said
  once, by her, and then left.
- **The canon's rule holds.** Why one rises with their mind is still never
  confirmed. Chid *hoped* her holding on would do it; the game shows only
  that she came up with her child.

**What it changes.**
- **Treatment:** §3.3 (Chid writes the letter; Rook posts it and sells the
  date; "he went down with her"); §3.4 (the C43 exchange and the coda's third
  answer); §3.5 (the reserve, reworked: no longer "Chid drowned Tobin"); §6
  Chid (irony that hides a twist); §7's Act 3 table.
- **Bible:** §1 (the mother's last week), §3 (Chid's row), §5 (his entry and
  third layer), §8 (Chid's truth, the coda).
- **Data, Act 1:** `chid.first` (one direction); day 2's morning report
  (write it); the prologue's reeds (staging, combat and the experience
  director; the optional narrator line). Everything else stands as written.
  Acts 2 and 3 are not in the data yet.

**Early lines it touches:** very few. Chid's Act 1 lines already carry the
seeds as written; only `chid.first` gains a direction. Possibly one new
prologue narrator line. Rook, the narrator's existing prologue lines, C02 to
C04, Holloway, Maeca and Brannoc are untouched.

---

## B. "Count's right": Holloway knew

**The false belief.** Holloway never knew anyone came out from under his lid.
The canon says so ("He never learns it"), and the kill plays on it: Maeca's
secret, his blind spot.

**The truth.** As the lid came down he saw her face, ninety-two, turned up
into his lamp. He has known for ten years that she lived, so the ones under
him weren't all dead. Everything he does is for her. He pays her out of his
own pocket every week: the widow's ration, for a living woman. He sleeps
beside her loaded crossbow every night. He drinks what she pours. At the lip
of the hole he looks up at her and grins, "Count's right": ninety-two up, and
he's the last. He climbs into her knife on purpose.

**The reveal.**
1. **C20b, the fourth dusk:** risen at his gate, his lips moving. Close, the
   survivor (who alone hears the dead, as in the prologue) hears him count:
   "...Ninety. Ninety-one. ...Ninety-two." Then he lifts his hands, and she
   lays him down. "One in."
2. **C22, his table:** the daybook. "91 up. Lid down." The names below, with
   who each left. At the foot, "92." and no name, and beside it the one word
   he never said: "Sorry." Taken to Maeca, she reads it. The planned "He
   never counted me." becomes: "...He counted me."

**The seeds.**

| Where | What it says or shows | Re-read |
|---|---|---|
| `scene_gate_dawn` | asleep on a stool beside Maeca's loaded crossbow. "Waits up for you. ...Somebody waits up for him." | he sleeps next to her bolt on purpose |
| Maeca's signature | "I track for the Watch, before you ask. Not wolves." He pays her himself. | what does she track? Nothing. It's a ration |
| The roll (Act 1, at the gate) (**one beat added**) | "Abbot. Two bairns. Ancell. His mam..." He always stops at ninety-one, and starts again. | he never says the last number aloud |
| `scene_knocking` (**one direction added**) | "Does anyone else know?" "Pell." His eyes go past you, to the step where Maeca sits. | the one lie a good man tells |
| `scene_knocking` | "Both numbers are right. That's the trouble with counting." | he knows one of them is wrong |
| `scene_did_he` | "...Did he." | she thinks he never knew; he did |
| `scene_his_cup` (**one direction added**) | she fills his cup; he drinks without looking at it | he'd drink whatever she poured |
| C20 | "Count's right." He looks up at her and grins. | there you are |

**Why nobody sees it.** The kill is already the twist. Players believe the
story's secret is spent and his ignorance is the tragedy. Obvious after: every
night beside her bolt, the pay, the grin.

**The emotional spine.**
- **Holloway** goes from victim to a man who saved them all, laughed, and
  climbed to her knife.
- **Maeca:** her ten years of waiting were answered before she struck. The
  HOLY SHIT is unchanged; the aftermath doubles, for her and for the player.
- **Brannoc and her mother:** untouched.

**What it changes.**
- **Treatment:** §0 and §4.1 ("He never learns it" becomes "he saw her face"),
  §4.4, and §4.6 (C20b, C22).
- **Bible:** §3 and §5, Holloway and Maeca.
- **Data, Act 1:** three directions and one beat of the roll. Act 2 isn't
  written yet.

**Early lines it touches:** Holloway's confession and roll (mid Act 1), and
the gate scenes' directions. Maeca's words are unchanged.

---

## C. "She went in first": her mother chose it

**The false belief.** After C32, the mother was taken by accident, waiting
on the bank with her lamp.

**The truth.** By the seventh evening she knew what the ford did, and that her
letter was already on the road. She couldn't stop her child coming. So she
did the one thing left: she walked into the water first, to be down there,
holding on, when her child came.

**The reveal.** C43, after "I came up with you.": "How?" "I went in first.
...Somebody had to be down here to hold on."

**The seeds.**
- The letter: "I'll be at the water with a lamp."
- Her word, "Stay where it reaches." She went past it.
- The prologue's woman, who lifts the lamp and doesn't strike.
- Chid's hope, said once in Act 1 (one new sentence in `chid.before`): "Some
  say it's because somebody down there won't let go of them. I like that
  one."
- C32, Rook: "The seventh night she didn't stop on the bank. She walked
  straight in. I thought she'd seen you."

**Why it ranks third.** It's moving (devastation and elation at once), but it
comes close to a law, that love holds you up, which the canon forbids because
a player would apply it backwards to Nell. It's a turn on an approved twist
rather than a new one, and fewer players would call it unseen.

**Early lines it touches:** one sentence in `chid.before`.

---

## The ranking, and why A

1. **A** is the owner's instinct, made to fit the canon, and it re-reads the
   whole game: every death and carry-home, the word, the office, the art the
   player rises by, the narrator's lines about him. It lands at the summit,
   and it ends the game on the mirror of its first choice. It costs almost
   nothing in the early lines, because the seeds are already written. Chid
   stays irony on the surface (the editor's note) and becomes the twist
   underneath.
2. **B** is the best value for its cost, a knife into the centrepiece. It
   works alone or alongside A.
3. **C** is the tender reading of A's night. One or the other.

**Considered and set aside:**
- **Holloway is the survivor's father.** Huge, but soap (the editor rejected
  "Vonnra is the aunt" for the same reason), and it fights the backgrounds.
- **Maeca is Unchained since Ashford.** It crowds the rarity the whole plot
  rests on.
- **Jory came home dead.** It sours Act 1's elation, but it lands on a minor
  character.

**Scenes no option touches** (safe to settle for voicing now):
- C02 `cin_none_cross`, C03 `cin_heart_goes_down` and `warden_answer`;
- C04 `cin_first_light`;
- the prologue's existing narrator lines;
- Vonnra's `far_voice`;
- Rook's Act 1 lines;
- Brannoc's.

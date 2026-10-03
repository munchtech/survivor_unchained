# Story bible

The truth under Survivor Unchained, for the people who write it and build it:
the whole arc, act by act; who everyone really is; how every thread can end;
and which choice in Act 1 decides what, and when. What the player sees in
Act 1 is the surface; this is what it rests on. Keep every act's content
consistent with it, and never let a character say an answer out loud before
the act that answers it (section 3 says which act that is).

How people talk: `VOICES.md`. The Act 1 implementation spec, with every
fact, entry and test: `WRITING_PASS.md`. How the world remembers:
`godot/README.md` and `godot/logic/World/`.

---

## 1. Premise and spine

**The world under the world.** Under Thornhollow lies the **Morrow**: a thing
vast, pale and segmented, older than the old empire, alive, and bound. The
old empire's Seventh Legion found it, could not kill it, and chained it ("Here
the Seventh Legion buried what it could not burn"). The chain is seven links.
Each link is anchored in a **heart**, a great stone cut with a sigil, and each
heart was given a keeper: the **Wardens**, made by the Order of the Morning
Light to stand at seven crossings and kill anything that came near. The
Ford-Warden at the Low Ford was one. The valley still calls its hills "the
Morrow" without knowing why: Morrow pippins, Morrow cloth, Vonnra
Ash-of-Morrow.

**Ember is the Morrow's light,** and its pain. It leaks up through the ground
as stone and dust. The Order burned it in its chapel lamps and called it the
morning ("the dark is only the part of the day that hasn't happened yet" was
never a metaphor: their morning was chained underneath them). The Watch burned
it in the ford lamps to keep the Wardens asleep. The Dig cooks it into slurry.
Everyone in the valley lives by it, and almost nobody knows what it is.

**The risen and the Unchained.** When someone dies in the dark near ember, the
Morrow's light sometimes goes into them and they get up. Almost always they
rise **mindless**: the dead in the barrow, the drowned in the ditch on the Low
Ford road. Once in a great many deaths, one rises **with their mind**: an
**Unchained**. They burn at night, when the chain is weakest (the Legion's
sigils drink sunlight; the dark is when they starve), and at dawn the light
drains back into the ground and leaves them ordinary. That is the ember the
player grows each night and loses each dawn. Each Unchained is a piece of the
Morrow walking about, a link coming loose. The title means both things: the
survivor is unchained from death, and through people like them the Morrow is
coming unchained.

**The survivor.** A traveller (who they were is their background) who tried
the Low Ford at dusk, was drowned by the Warden, was carried back to the south
bank, and woke by a dying fire not knowing they had died. That night the
Morrow's light in them let them do what no living traveller had: kill the
Warden. They do not know they are dead. The town half suspects ("You were
cold when they brought you in... Then you weren't"); the old orders would know
at a glance; one person arranged it.

**Why the lamps were lit.** The chain is failing. Ten years ago the ground
under **Ashford**, a mining town up the valley, gave way into the Morrow's
outer workings: the **Ashford Fall**. Half the town went into the dark; the
year after was the **fever year**, ember sickness in the wells. Vonnra, the
last of the binders' line (Ash-of-Morrow: the family that kept the Legion's
sigils), knows the chain cannot be re-forged by the living: the Legion's dead
hold the inner door from inside ("It was never locked from the outside"), and
only something of the Morrow's own light can walk through them and lie down
in the chain as a new link. She needs an Unchained. Unchained are rare: you
must drown a great many to get one. So last winter she had twelve lamp-irons
forged for the Low Ford, paid in the binders' square coin, relit the lamps to
wake the Warden, and sent travellers across after dark on toll work at double
pay. The drowned rose mindless in the ditch, one after another (a carter
called Wat; Brannoc's daughter Nell), until one night a light went out at the
crossing, and then another came on. The survivor is her answer.

**What the survivor did first.** Killing the Ford-Warden loosed its heart, one
of the seven, and Grimtunnel carried it down the hole. The prologue's victory
was the chain's first break. The tremors start there. Vonnra had meant the
heart to stay in the ford: "I am not angry. I am arranging."

## 2. The shape of the game

| Act | Name | Days (rough) | What it is about | Ends with |
|---|---|---|---|---|
| Prologue | The Low Ford | night 0 | Ember, the Warden, the heart stolen. | Dawn; the gate opens. |
| 1 | The Waystation | 1 to ~7 | Arrival. Two troubles (the wolves, the caravan), three mysteries (the sealed door, the thing below, the lamps). | Vonnra reads your fortune. |
| 2 | The North Road | ~8 to ~20 | The ground opens under the Penhale farm. Keegan's chapter four. The Vigil's cages. **What you are.** | The Vigil's war at the north gate; Vonnra asks you to come down with her. |
| 3 | The Morrow | ~21 to the end | Down the stair. **Who made you, and why.** Chid's truth. Grimtunnel at the bottom. What the Morrow prays for. | Three endings, each with variants; an epilogue page per person and place. |

The game asks three questions, one an act: **What are you?** (Act 2 answers.)
**Who made you, and why?** (Act 3.) **What will you do with it?** (The ending.)
Act 1 asks none of them out loud; it plants all three.

## 3. Who is really who

| Who | Seems | Is | Comes out |
|---|---|---|---|
| The survivor | A lucky traveller | Unchained: drowned at the Low Ford, risen with their mind | Act 2 (the Vigil's ledger, Keegan, Chid) |
| Vonnra Ash-of-Morrow | Toll-keeper, far seer | Last binder. Lit the lamps, made the survivor, let the caravan go, sent her clerk through the door. Her "sight" is old lore and bought talk. | Act 3 (sooner, and in her own words, if accused in Act 1) |
| Chid | A cheerful fool of a priest | An Unchained of the Order's day, near two hundred years old; "C." of the note in Ashe's trunk | Act 3 |
| Jessop | Vonnra's toll clerk, gone south | Bought by Pell to turn the Coyle wagons; Vonnra let it happen, then sent him through the sealed door to see if a living man could pass. His are the bootprints going in. | Act 3 (on the stair) |
| Nell | Brannoc's girl, safe at Low Kiln | Drowned at the ford a fortnight before the survivor; rose in the ditch; the survivor put her down | Act 1 (if Brannoc is told), or Act 2 |
| Wat | A carter | Drowned on toll work, the "quick crossing" | Act 1 hint, Act 3 |
| Corran, Dannet | Watch deserters | Corran died at his post; Dannet, his runner, went to the Toll Tower first and was sent back down the road at night | Act 1 (Corran), Act 2 (Dannet's body, a Toll Tower pass on it) |
| Captain Holloway | A tired honest captain | Ashford's quartermaster who signed for boots that never came; holds a letter from the north asking for "the one from the ford" | Act 2 |
| Maeca Barefoot | A hunter with a theory | Last of the Ashford garrison; the Pack saved her; half the Kerchiefs are her old neighbours | Act 1 (the Pack, if her lover), Act 2 |
| Harlan Coyle | The grieving uncle | Has sold the Dig its blasting ember for two years | Act 1 (to the player), Act 2 (to everyone) |
| Pell Varrow | The villain of the caravan | Paid to stop the ember reaching the Dig, and to ruin Coyle; holds the numbers that say when the chain breaks, and his sister's letter about the boots | Act 1 (why), Act 2 (the numbers, the letter) |
| Redcowl | A bandit with cages | Dunstan Cutwell, Rav's brother, leader of Ashford's dispossessed; the closest thing to a resistance | Act 1 (Ashford, unsaid; his name, if he dies), Act 2 |
| Rav Cutwell | The defector, the outcast's friend | Redcowl's brother; gave him the night the wagons would come; stole the clerk's key himself | Act 1 (the brother, if Redcowl dies; "the little bird"), Act 2 |
| Brannoc | A smith of few words | Forged the irons that woke the Warden that drowned his daughter | Act 1 |
| Dame Keegan Orme | Comic, probationary | The last true knight of the Argent Vigil; chapter four of her handbook is about the survivor | Act 2 |
| Ysolde Marrow, the Wayfinder | A cartographer of arenas | Sells the names of those who come back to the Vigil's Lord-Exchequer, to keep her brother Edric (Unchained since the barrow) fed in his cages | Act 2 |
| Lord-Exchequer Orrin Sallow | "A gentleman in the north who likes silver ink" | Has turned the Vigil from killing Unchained to buying them, as soldiers who rise every night, for a war in the south | Act 2 |
| Sella | The blue room's professional | Sells what is said upstairs; Vonnra outbids everyone | Act 1 (the fortune quotes your pillow talk) |
| Mother Rook | Knows everything | Paid by Vonnra for news of the ford road (double for you); her mother brought Chid bread | Act 1 (the money), Act 3 (the bread) |
| Grimtunnel | A thieving Boss | A believer, carrying a god its heart | Act 3 |
| Snib | Self-appointed foreman | Exactly what he looks like. Survives everything. | Always |
| Tam Penhale | A farm boy nobody believes | Right, every time | Act 2 (the knocking) |
| The Morrow | A thing praying under the Verge | Prays to be let die. The chain has kept it alive and harvested for two thousand years. | Act 3 |

## 4. Factions and their true aims

| Faction | Face | True aim |
|---|---|---|
| **The Watch** (Holloway) | Keeps the roads and the peace. | Founded to keep the ford lamps and the Wardens asleep, and to "keep it done". Its charter (lost, or burned) also told it to put down the risen. It has forgotten all of it except the habit of counting. Eleven men, a year unpaid. |
| **The Argent Vigil** (Keegan; Lord-Exchequer Orrin Sallow) | Knights who guard the north road. | Kept the ledger of the Unchained and "returned them to the dark" (handbook, chapter four) to keep the chain tight. Sallow stopped killing them and started buying them, in silver cages at the chapterhouse at **Silverstair**, for a war in the south. Keegan's letters go unanswered because she is a loose end. |
| **The Order of the Morning Light** (Chid) | A dead priesthood with one fool left. | Made the Wardens and worshipped the light they guarded. "Left" Thornhollow when the Vigil came for it for sheltering Unchained. Its last priest is one. |
| **The binders** (Vonnra) | A toll-keeper's family. | Kept the Legion's sigil-keys and the square coin, and the duty of the chain. One left. |
| **The Dig** (Grimtunnel, Snib) | Diggers with lamps on their heads. | Lamplings are the empire's lamp-tenders gone feral. Grimtunnel has found the Morrow and worships it; he is carrying the Warden's heart down to it, believing it will be grateful and make his people the light of the world. |
| **The Kerchiefs** (Redcowl) | Road bandits in red. | What is left of Ashford's levy and its families. Red was Ashford's colour. They rob the road because the Watch abandoned them, and they feed forty-one mouths on it. They carried the Dig's ember for two years without asking what it was. |
| **The Coyle Company** (Harlan) | Honest merchants. | Has sold blasting ember to the Dig, through Pell's books and the Kerchiefs' road, for two years. It kept the Company alive. The "B.E." crates on Jory's wagons were the latest. |
| **Pell's books** | A greedy factor. | Pell has read the receipts and knows how much ember has gone into that hill. He took the Dig's money to procure the B.E., paid the Kerchiefs to take the caravan, and meant to "tell Holloway where they camp, after", so the crates would end in the Watch's hands, never the Dig's, and Coyle's ruin would be his profit. A swindle that happened to protect the valley. |
| **The Pack** (Greymuzzle) | Sick wolves. | Poisoned by the Dig's slurry. Greymuzzle is old enough to remember Ashford: he found Maeca in a cave mouth there and lay across it to keep her alive. |
| **The Seventh Legion** | Dead. | Still keeping the inner door, from the inside. They part for the Morrow's own light. |

## 5. The people: face, secret, arc, ends

Every secret is hinted in Act 1 and answered in the act named in section 3.
None of them says it.

- **Mother Rook.** *Face:* the innkeeper who knows everything. *Secret:* Vonnra
  pays her to report who comes up the Low Ford road, and paid double for the
  survivor. Her mother carried the Order's lamp up from the chapel the year the
  Order "left", and brought Chid bread. *Arc:* loyal to the town, not to
  Vonnra; when she learns in Act 2 what the money bought (the carters, Nell),
  she turns, and the Last Lamp becomes the place the town hides its own. *Ends:*
  keeps the inn through anything; the last lamp lit in every ending but the
  break, where she lights a candle instead.
- **Captain Holloway.** *Face:* a tired, honest captain. *Secret:* he was the
  Ashford garrison's quartermaster. When the Fall came the Watch command turned
  the relief wagons back, and Holloway signed for the boots and supplies as
  delivered, to cover his commander. The garrison held the cave mouths
  barefoot and died. Maeca is the last of it. He also holds a letter from
  Sallow asking for "the one from the ford" (seen face down on his table in
  Act 1). *Arc:* Act 2 makes him choose between the letter's money (his men
  unpaid a year) and the survivor, and makes the boots come out. *Ends:* dies
  holding the north gate against the Vigil; hands the survivor over and is
  killed by Maeca; confesses, is forgiven by nobody, and keeps the gate anyway;
  hanged by Redcowl's people.
- **Maeca Barefoot.** *Face:* a hunter with a theory. *Secret:* the Pack saved
  her life after Ashford, which is why she has never hunted a wolf. Half the
  Kerchiefs are her old neighbours ("Fed some of them, once. Buried more.").
  *Arc:* the boots. *Ends:* leaves with the Pack into the deep wood; takes the
  Watch after Holloway; dies at the breakthrough's edge if the Pack is gone and
  she has nothing left to hold; the survivor's lover, at the end, if both live.
- **Old Wenna.** *Face:* a rude herbalist. *Secret:* she nursed the fever year,
  knows ember sickness by smell, and made the blightward mask for it. She has
  suspected for a decade that the fever came out of the ground. *Arc:* Act 2's
  breakthrough is the fever year again, and she is the only one who has been
  through it. *Ends:* saves the Penhales with her teas and her mask (if the
  survivor has it); dies nursing in the bad air; "dies happy, then keeps
  living, to spite everyone".
- **Tam Penhale.** Nine, and right. His family's farm is where the Dig breaks
  through in Act 2 (he hears it knocking in Act 1). *Ends:* the farm lost or
  spared; his Pa alive or not; Tam grows up, and is right about that too.
- **Brannoc.** *Face:* a smith of few words. *Secret:* he forged the Low
  Ford's new lamp-irons last winter for a buyer who paid in square coin and
  never showed a face; ten of twelve were collected. He suspects whose coin.
  *Arc:* his daughter Nell went south a fortnight before the survivor came up
  the road, with Wat the carter on toll work, and drowned at the ford, and rose
  in the ditch, and the survivor put her down. Whether the survivor tells him
  decides whether he forges the last two irons in Act 2 (and so whether a
  second crossing is woken), and whether in Act 3 he makes the cage the
  Warden's heart has to be carried in. *Ends:* breaks the last irons and hunts
  the coin; forges them and learns too late; makes the heart's cage; never
  works for the survivor again.
- **Harlan Coyle.** *Face:* the grieving uncle, the most sympathetic man in
  town. *Secret:* the Coyle Company has supplied the Dig's blasting ember for
  two years. He put Jory on the road with six crates he knew were bound for the
  hole, and told him not to take them over ruts. His grief is real; so is his
  guilt. *Arc:* exposed in Act 2, by Jory (if the survivor told Jory) or by
  Pell's receipts. *Ends:* funds the evacuation and the Kerchiefs' pay with
  everything he has; hanged by the Watch; driven out of the valley; killed at
  the breakthrough he paid for.
- **Jory Coyle.** Did not know. Finds out, in Act 1 if the survivor tells him.
  *Ends:* runs the Company honestly; walks out on his uncle and takes the south
  road (and, if the Kiln Ford is lit, drowns there and rises); dies in the
  breakthrough.
- **Pell Varrow.** *Face:* the villain of the caravan plot. *Secret:* a careful
  man who lost his sister in the Ashford Fall, has read the receipts, and is
  doing the wrong things for the right reason (and for profit, because he
  cannot help it). "I'm not a good man. I'm a careful one." He has two things
  Act 2 needs: the numbers (how much ember went into the hill, so how deep,
  so which night the chain goes) and his sister's last letter, about the
  garrison's boots "signed for full". *Ends:* keeps the evacuation ledger and
  saves the town by arithmetic; hangs; dies in Redcowl's cage; is never seen
  again.
- **Rav Cutwell.** *Face:* the defector, the outcast's friend. *Secret:* Redcowl
  is his brother, Dunstan. Rav still drinks with the toll clerk and still sends
  word down to the Roost: he gave Redcowl the night the Coyle wagons would come.
  The clerk's key he "found on a stool" he had taken himself. He is ashamed of
  all of it and will do it again. *Ends:* stays the town's doctor; takes the
  red hat when his brother dies, and leads the Kerchiefs as the army they have
  become; hanged for the tip-off.
- **Chid.** *Face:* the Fool, a priest of a dead order. *Secret:* an Unchained
  of the Order's day, near two hundred years old, who cannot stay dead and does
  not age. He wrote the note in Ashe's trunk ("Keep the lights lit. — C.") to a
  friend. He has seen the dead get up before; he knows what the survivor is, and
  is the gentlest person who knows. *Ends:* see the endings: goes dark at dawn;
  lies down in the chain in the survivor's place; is given the coin and ages
  at last; kneels to a new god, or will not.
- **Vonnra Ash-of-Morrow.** *Face:* toll-keeper, far seer, the one who reads
  your fortune. *Secret:* she relit the ford lamps to make an Unchained and
  means to use the survivor to re-forge the chain: to walk them down through
  the Legion's dead and bind them in as the new link, forever. She believes it
  is the only way the valley lives. She sent the carters. The toll clerk who
  sent Coyle's wagons off the road was her clerk; she let it happen, because a
  ruined Coyle sells no more ember to the Dig, and then she sent Jessop through
  the sealed door to learn whether a living man could pass. Her far sight is
  old lore and bought talk (Rook, Sella, Pell): the fortune quotes what the
  survivor said in Sella's bed. Her grandmother's coin, square, stamped VII, is
  the Legion's own token: the toll at the inner door, and it buys one return.
  *Arc:* the trusted figure with the deepest secret, and good reasons. *Ends:*
  binds the survivor; is refused; drowns herself at the Low Ford to rise and
  take the survivor's place ("It is not often the second thing happens", and it
  does); dies at the bottom; gives the survivor the coin.
- **Dame Keegan Orme.** *Face:* comic, earnest, probationary. *Secret:* the last
  true knight of the Vigil, and does not know it. Chapter four of her handbook
  is "Of the Unchained, and Their Return to the Dark". She has started to see
  the signs in the survivor and is very much hoping she is wrong. *Ends:* steps
  aside and comes north, and re-founds the Vigil as what it was meant to be;
  stands at the gate and dies there; spares the survivor and is disgraced; the
  survivor's lover, as a tragedy, if Act 2 opens that route.
- **Sella.** *Face:* the blue room's frank, funny professional. *Secret:* she
  sells what is said upstairs, and Vonnra outbids everyone for it. A lover with
  a motive, though not a cruel one: she would sell Vonnra a lie for you, if
  asked and paid. *Ends:* gets her house in the south with a door that locks
  from the inside; flees south on a toll cart after lying for you, drowns at
  the Kiln Ford, and rises: the second Unchained.
- **Redcowl** (Dunstan Cutwell). *Face:* the bandit chief with cages. *Secret:*
  the leader of Ashford's dispossessed, who kept his prisoners fed and who
  would, if anyone asked him straight, fight the Dig before the Watch would.
  Never says "Ashford", and lets nobody say it twice. *Ends:* killed in Act 1;
  holds the breakthrough's mouth with his people and the six crates and dies
  in it; takes the Waystation's gate after Holloway; hanged.
- **Ysolde Marrow, the Wayfinder.** *Face:* a cartographer of arenas. *Secret:*
  she writes down who comes back from her maps and sells the list to Sallow.
  Her brother Edric did come out of the barrow in the Morrow hills, twelve years
  back, risen with his mind; the Vigil took him, and her notes pay for his keep.
  She has drawn the barrow eleven times and still cannot get the corners right.
  *Ends:* frees Edric with the survivor and leaves the valley; dies at
  Silverstair; keeps selling.
- **Lord-Exchequer Orrin Sallow.** Act 2's antagonist. Courteous, patient, and
  a collector: of debts, of ledgers, of the dead who get up. Writes in silver
  ink. Wants the survivor because they come back more often than most.
- **Grimtunnel.** *Face:* a thieving Boss. *Secret:* a believer. He thinks he is
  freeing a god. *Ends:* crushed when the chain is re-forged; dies at the end of
  his faith when the Morrow dies; kneels to the survivor.
- **Snib.** Exactly what he looks like. Survives everything, in every ending.

## 6. Act 1: The Waystation

### What happens

The survivor walks up from the Low Ford at dawn into a town with two troubles
and three mysteries, and every route through them is written so it can be
walked in any order (`WRITING_PASS.md` has each graph).

- **The Beast Problem.** The wolves are sick, not bold: the Dig's slurry is in
  the stream. Kill them for the bounty (or lie about it), find the cause, speak
  with Greymuzzle, run with the Pack, talk or bribe Snib into moving the
  outflow, break the pump, blow it (with a charge from Pell's shop, or one from
  Redcowl's crates), sell the cure to Pell, or do nothing and watch the wolves
  come to the gate.
- **The Missing Caravan.** Harlan's nephew is in a Kerchief cage. Follow the
  ruts, read the toll ledger, find Jessop the clerk who sent them the wrong
  way (and find he is gone), break into Pell's warehouse, bluff Redcowl, show
  him who sold him out (and decide whether to tell him where Pell sleeps), buy
  the prisoners, fight for them, return the cargo, sell it, keep it. Decide what
  happens to the six "B.E." crates: tell Redcowl what they are for and he keeps
  them from the Dig; tell Harlan where they are and they go home to be sold on;
  burn the Roost and they go up with it. Tell Jory what he carried, or tell him
  salt.
- **The Sealed Vault, the Thing Below** (mysteries, as before) and **the Lamps
  at the Low Ford** (new): the dead watchman's book, Holloway's deserters,
  Keegan's "somebody wanted it awake", Brannoc's irons and his mark on the
  lamp-iron the survivor carries, Rook's double pay, the carters' notice, the
  square coin at Vonnra's throat, and Nell. Never stated; assembled. At the
  fortune the survivor who holds enough of it can say it to Vonnra's face. She
  does not say no. She says their name.

### Chapter one's mysteries, answered

| Mystery | What the player learns in Act 1 | The truth |
|---|---|---|
| Why are the wolves sick? | Slurry from the Dig. | The Dig is digging toward the Morrow, faster since it got the heart; the slurry is its light, cooked. |
| Who took the caravan? | Pell paid Redcowl; Jessop, a toll clerk, sent them off the road. | Pell paid to stop the B.E. reaching the Dig and to break Coyle; Rav gave Redcowl the date; Jessop was Vonnra's and she let it happen; Harlan knew what was in the crates. |
| Where is Jessop? | "Gone south." Not been seen since. | Through the sealed door, on Vonnra's errand. His are the bootprints, and the toll-token trodden into one. |
| What is behind the sealed door? | "A stair going down, older than the door." | The way down to the Morrow, kept from inside by the Legion's dead. Its sigil's seven notches take the binders' seven keys; the bones held one, Vonnra keeps six. |
| What is under the Verge? | Something pale and huge, "Not breathing. Praying." Tam's farm knocks at night. | The Morrow. It prays to be let die. |
| Who lit the ford lamps? | "Not by us." Brannoc's irons, square coin. Toll work, double pay, "quick means after dark". | Vonnra, to drown travellers until one rose Unchained. |
| Why does the ember burn only at night? | It just does. | The chain is sun-bound; in the dark the Morrow's light leaks into its carriers. |
| Who is "C."? | Not Ashe. Chid admires the handwriting. | Chid. |

### Seeds planted in Act 1, and where they pay off

Node references are `conversation.node` in `godot/data/content/dialogue.json`
unless a file is named. Deliberate inconsistencies are marked **(on purpose)**.
Each seed names the beat it pays (section 7 and 8). `WRITING_PASS.md` section
9 has the same list as a table with the facts that carry them.

**Vonnra and the lamps** (pays: Act 3, Vonnra's truth; Act 2, the second crossing)
- `rook.ford`, `rook.ford2`: Vonnra pays Rook for news of Low Ford arrivals,
  and paid double for the survivor. Journal: `lamps/rook`.
- `vonnra.first` (ford variant): "So. The one from the ford. ...Sooner than I
  had thought."
- `vonnra.ford`: "A light going out at the crossing. And then... another one
  coming on. It is not often the second thing happens." (The survivor's death
  and rising. In Act 3 it happens again, if she drowns herself.)
- `vonnra.f_self` (fallback): "the lamps lit for you."
- `vonnra.f_past` (fallback): "Of before the ford, I see very little. The
  water took it, or you left it on the far bank. Most do." (The drowning.)
- `vonnra.cb_core_stolen`: "I am not angry. I am arranging." (She meant the
  heart to stay in the ford.)
- `vonnra.say_calling` (arcanist): "Some of them keep ledgers." (Sallow.)
- `vonnra.cb_exposed_pell`: Pell "owed me a great deal".
- `brannoc.irons`, `brannoc.mark`: twelve lamp-irons, ten collected at night,
  paid in square old coin; his mark under the socket of the lamp-iron the
  Warden carried (`items.json` `wardens_lampiron` lore). **(on purpose)**
  twelve ordered, ten collected: the last two are for the Kiln Ford (Act 2).
  `brannoc.irons_after`: "Buyer can come and ask me himself. Or herself."
- `board.read`: "CARTERS WANTED ... Toll work, paid DOUBLE for a quick
  crossing. Apply at the Toll Tower. — V." and the pencil underneath:
  "quick means after dark", "Wat went. Wat's not back." Journal: `lamps/notice`.
- `brannoc.nell`: Wat had "toll work. Said he'd be over the ford by dark."
- `sella.buyers`: Vonnra pays for all the talk upstairs, more than anyone.
  `sella.past` then `vonnra.f_past`: the fortune quotes what the survivor told
  Sella about their life, with "(She is not looking at your palm.)" Her sight
  is bought; the first Act 1 twist that pays inside Act 1.
- `Prologue.cs` (the dead watchman's book): "Lamps at the Low Ford lit again,
  and not by us." `holloway.post`: the dead man is Corran, written down as a
  deserter; his runner Dannet "never came up the road" (Act 2: Dannet's body,
  with a Toll Tower pass on it). Journal: `lamps/book`, `lamps/post`.
- `keegan.warden`, `keegan.who`: "If somebody lit them again, somebody wanted
  it awake." "Someone who wanted a heart. You tell me; you were there."
- **(on purpose)** `concerns.json` vonnra: she "misses nothing that comes
  through the east gate", and `vonnra.ledger_read` says the caravan never came
  through it: her own clerk sent it away. `vonnra.jessop`: "Clerks go south,
  traveller. It is the direction they fall in."
- `vonnra.f_accuse`: told to her face, she says neither yes nor no; she calls
  the survivor by name for the first time ("Sit down, {name}. I have not
  finished reading."), and does from then on. Fact `vonnra.accused`.

**The Unchained** (pays: Act 2, what you are)
- `chid.before` (after a death): "You were cold when they brought you in...
  Then you weren't. ...It's been a long time since I saw anyone do that."
- `chid.names` (day three): "It always takes the names first. Then the faces."
  `sella.sleeptalk`: "You said a name. Over and over... I don't think you did
  either." `Prologue.cs` dawn: the survivor reaches for their mother's face and
  it is not quite where they left it.
- `chid.say_calling` (arcanist): "You burn, don't you? Not like a candle."
- `sella.say_calling` (arcanist): "Are you on fire? You're a little bit on fire."
- `keegan.ready`: "You would not like it if I saw them." `keegan.north`,
  `keegan.ch4`: chapter four. `keegan.say_risen` (after a death): "You look
  well. You look extremely well. ...I've got to go and read something." (The
  contraction is the tell.)
- `keegan.say_calling` (arcanist): "The Vigil kept a ledger of— never mind."
- `wayfinder.notes`: "You come back more often than most... So has he."
  `wayfinder.margin`: how she writes the survivor down: their name, "Nobody",
  or "Lark". Fact `wayfinder.name` decides the name in Sallow's ledger.

**Chid** (pays: Act 3)
- `chid.long`: Rook's mother brought him bread. `chid.warden`: "Before me,
  certainly, which is a long time." `npcs.json` chid bark: "Morning comes. It
  always has. I should know." `folk.json`: "Chid's not aged a day since my mam
  was a girl." **(on purpose)** `folk.json`: "the priest's a fool. Says so
  himself."
- `Waystation.cs` garden note "Keep the lights lit. — C."; `rook.c`: Ashe was
  never called anything else **(on purpose)**; `chid.note`: "Nobody makes a C
  like that any more. Nobody's made a C like that in... well. Ages."
- `chid.cb_core_stolen`: the heart "was one of the old ones. They're not meant
  to be carried about."

**Ashford, the boots** (pays: Act 2, Holloway's letter and the boots)
- `maeca.first`, `maeca.barefoot`, `maeca.signed`: boots signed for, never
  came; "Somebody with a good hand and a ledger."
- `holloway.maeca`, `holloway.ashford`: "I counted boots for the Ashford
  garrison, once, and I was good at it."
- `pell.t_pell`: his sister wrote the week before the Fall that the garrison's
  boots "had come in short, and somebody had signed for them full". Where that
  letter is in Act 2 depends on Pell's fate.
- `maeca.blind_morning` (romance): the Pack saved her after Ashford.
- `maeca.cb_burned_roost`: "I was at Ashford." `maeca.kerchiefs`: "Fed some
  of them, once. Buried more."
- `wenna.fever`: the fever year came the year after Ashford "went into the
  ground"; same smell as the slurry.
- `redcowl.who`: "what's left when a town goes into the ground and the Watch
  counts its boots and goes home". `redcowl.ashford`: say it once in his camp
  and he goes cold; fact `redcowl.ashford_said`.
- `holloway.hub` (wolves at the gate): Aldo's wife is at Low Kiln.

**Harlan, Pell and the crates** (pays: Act 2, Harlan exposed; the breakthrough; the army's powder)
- `harlan.be`, `harlan.g`, `harlan.knew`: "He didn't know. ...He didn't know.
  I did." `harlan.be_dig`: "I don't ask the salt what it's for, friend."
- `jory.crates`: six crates "we weren't to open... and not to take over ruts".
  `jory.truth` / `jory.salt`: what the survivor tells him; facts
  `jory.knows_be`, `jory.lied_to`. `harlan.cb_jory_knows`, `harlan.jory_now`.
- `harlan.cb_sold_dig`: "I've sold worse, to worse."
- `harlan.t_harlan`: Jory's mother (Harlan's sister) went with the fever year:
  the Coyle Company sells ember to the thing that killed her.
- `pell.t_pell`: Pell's sister kept the books in Ashford.
- `pell.caravan`: "someone ought to own those wagons who knows what not to put
  in them." `pell.why`: "It wasn't the salt I was paying for."
- `pell.books`, `pell.books2`: "Nobody digs that deep for coal."
- `redcowl.pell`: "tell Holloway where they camp, after." Then the survivor
  says where Pell sleeps, or does not: fact `pell.fate` (`taken` or `ran`).
- `redcowl.crates_keep`: "Not the hole in the hill. Not Holloway. Not your
  merchant." Fact `be.crates`.
- `snib.ember`: "Boss pays the man. Man pays the Kerchiefs."
- `holloway.caravan2`: "a short list in a town this size".

**Rav and Redcowl** (pays: Act 2, the tip-off, the hat)
- `rav.redcowl`: the sewn-on leg; "I don't do family histories."
- `redcowl.birds`: "A little bird. Sings for its drink, and sews a fair seam."
- `rav.cb_burned_roost`: "He'll have got out. He always gets out."
- `rav.cb_killed_redcowl`: "Dunstan. That was his name, before the hat. Our
  mother's idea." (The one time Rav names him.) `redcowl.crates_keep`: "My
  mother'd laugh herself sick."
- `rav.clerk` (outcast): the clerk's key, which Rav "found" on a stool.
- `npcs.json` rav bark: "Red cloth's a hard habit to break."

**The north** (pays: Act 2)
- `keegan.vigil`: the chapterhouse does not answer.
- `wayfinder.notes`: silver ink (argent) in the north.
- `holloway.hub` and `holloway.letter` (night, day three on): a letter with a
  silver seal, turned face down. Fact `holloway.letter_seen`.
- `keegan.ashe`: Ashe "closed the north road with forty lamps and walked back
  through it with one".
- `wayfinder.t_wayfinder`: her brother did not come out of a barrow in the
  Morrow hills; she has drawn it eleven times (Edric, Act 2).

**Below** (pays: Act 2, the breakthrough; Act 3)
- `quests.json` vault entries, `Verge.cs` vaultdoor: seven notches, one
  fragment; the sigil wakes after dark.
- `Verge.cs` vault bones (faith): "It was never locked from the outside."
- `Verge.cs` vault bootprints and `quests.json` `vault/bootprints`: fresh, going
  in; a copper toll-token trodden into one (Jessop).
- `Verge.cs` sinkhole (faith): "Not breathing. Praying."
- `survivor.first`: "Grimtunnel brought it a heart." `survivor.what`: Kell's
  lamp came back up on its own, still lit.
- `snib.pipelads`: the Dig's pipe-lads go blind, then deaf, then into the warm
  slurry.
- `tam.tock`: the ground under the Penhale farm knocks at night. Journal:
  `below/tock`. `folk.json`: the Penhales' dog will not go in the barn.
- `rules.json` `jory.nights`: Ewan, the fourth cage, who did not last.
- `vonnra.f_below`: "they think it will be grateful."

## 7. Act 2: The North Road

Begins the dawn after the fortune (`chapter.done`). Each beat says what
decides it. Facts are Act 1's unless marked.

**1. The breakthrough.** The Dig breaks into the Morrow's outer workings.
- *Where:* under the Penhale farm; but if `dig.pump` is `blown` the Dig's
  mouth fell in during Act 1 and the lamplings dug a new way down from the old
  sinkhole, so it opens in the Verge and the farm is spared.
- *How wide:* count what fed the Dig: one if the six crates reached it
  (`be.crates` is `harlan`, or unset at the act's end while Redcowl lives and
  has not been told, or the tricked camp was left to the lamplings), one if
  `dig.pump` was still `running` at the act's end. Nought: a slow sinking with
  two days' warning. One: the barn goes in a night. Two: the farm goes into
  the ground at once, Ashford again.
- *Who is home:* Tam's Pa, unless `tam.pa_in` or `tam.farm` (emptied or
  raided) took him off the farm. A survivor who heard Tam's knocking
  (`tam.tock`) can go out at the act's first dawn and bring the family in.
- *Who holds the edge:* the Pack, led by Maeca, if `beasts.outcome` is `cured`
  or `allied`; otherwise the Watch and whoever else will come. Wenna's
  blightward mask (`once:mask`) lets the survivor walk the bad air.
- *The Watch's powder:* if the crates fell to the Watch (Redcowl dead,
  `roost.cleared`, crates never claimed), Holloway can collapse the hole:
  the town saved, the farm and the lamplings under it buried, the quick way
  down closed.

**2. Keegan's chapter four.** She has watched for the signs (`keegan.saw_risen`,
the arcanist's burning, how often the survivor comes back). Act 2 brings her
to ask, straight: "Did you die on the Low Ford road?" Her respect and trust,
and whether the survivor lies to her now, decide: she steps aside and comes
north (her companion route; at Silverstair she breaks with the Vigil); she
stands at the gate to return the survivor to the dark (a night duel: kill her,
or spare her and leave her disgraced); or she lets them pass and writes to
the chapterhouse, which already knows.

**3. Holloway's letter.** From Sallow: deliver "the one from the ford" and the
Vigil will settle the Watch's arrears. Decided by Holloway's trust plus
respect, with `holloway.post_told` counting for the survivor (he owes them
Corran) and an unsettled `holloway.lied_to` against: high, he burns it and
says so; low, he hands the survivor over (an ambush at the north gate);
between, he tells Keegan and does nothing. `holloway.letter_seen` lets the
survivor ask him outright before he decides.

**4. The boots.** Pell's sister's letter says somebody signed for the
garrison's boots in full. Who holds it follows Pell's fate:
- `caravan.pell` `exposed`: in the warehouse the Watch sealed; Holloway finds
  it, and burns it or brings it to Maeca, by what he chose in beat 3.
- `pell.fate` `ran`: Pell carries it and comes back with it, to buy his own
  safety from Holloway, or to give to the survivor.
- `pell.fate` `taken`: Redcowl has Pell and his satchels, and reads it, and
  the Kerchiefs come for Holloway at the worst possible moment.
- `caravan.pell` `ally`: Pell offers it to the survivor as payment.
- otherwise: Pell keeps it until someone asks the right way.
Maeca learns from the survivor, from Holloway, or from Redcowl. What she does
depends on her regard for the survivor and on Greymuzzle (alive or not): she
kills Holloway at the gate; she leaves with the Pack; she makes him hold the
gate beside her.

**5. Harlan exposed.** By Jory, at the act's first morning, if
`jory.knows_be` (and harder if `jory.told_knew`); otherwise by Pell's
receipts, later. The survivor chooses: hand him to Holloway; let him make it
right (he funds the evacuation and the Kerchiefs' pay); let the town find out
its own way. If `be.crates` is `harlan`, he sold the Dig the ember that opened
the farm, and knows it. If `jory.lied_to`, Jory learns the survivor lied too.

**6. Pell's numbers.** Pell knows how much ember went into the hill, so how
deep, so which night the chain gives. He is in Redcowl's cage, where Jory was
(`pell.fate` `taken`), back from the south (`ran`), in the cells about to hang
(`exposed`), the survivor's man (`ally`), or still at his warehouse. Free him,
or let the law that was right about the caravan be wrong about everything
else.

**7. The army.** If Redcowl lives and is not at war with the survivor, he
comes to the Waystation with forty-one mouths and a dozen blades: the bandits
are the army. With `be.crates` `redcowl` they bring six crates of powder for
the tunnels. With `redcowl.ashford_said` he tells the survivor the levy's
story. Rav's tip-off comes out (Redcowl tells it, laughing; a survivor with
`redcowl.birds` guessed it). If Redcowl died in Act 1, Rav goes down to the
Roost and puts on the hat: the doctor leads the army, and his regard for the
survivor (`rav` affection after `cb_killed_redcowl`) decides whether it
fights beside them.

**8. Brannoc's two irons and the second crossing.** A hooded buyer comes for
the last two irons, with square coin.
- `nell.told` `gone` or `risen`: he will not sell. He breaks them, and asks the
  survivor to sit up with him at the forge: the buyer wears the Toll Tower's
  violet (a new clerk, never Vonnra herself). No second crossing.
- `nell.told` `lie` or `evaded`: he forges and sells. The Kiln Ford, the next
  crossing south, is lit, and its Warden wakes. Later Wat's grey mare comes up
  the south road alone, or Aldo's widow comes up from Low Kiln and says no
  carter came, and Brannoc learns Nell drowned, and learns the survivor said
  they passed nobody (`lie`) or did not look (`evaded`, the lesser wound).
  He never works for them again.
- The Kiln Ford, lit, is Vonnra's second chance: who drowns there rises as a
  **second Unchained**: Sella, if she lied to Vonnra for the survivor and fled
  south on a toll cart; Jory, if he walked out on Harlan by the south road; or
  a stranger.

**9. Sella's lies.** Pay her and she feeds Vonnra whatever the survivor wants
fed. Vonnra knows, in the end; she always does. Sella pays: with the Kiln Ford
lit, she runs, and the road is the one Vonnra built.

**10. Silverstair.** The north gate opens (Keegan aside, beaten or gone). The
chapterhouse: silver cages, the risen kept for a war in the south, Sallow's
ledger. The survivor's entry is in Ysolde's hand: "From the Low Ford. Risen the
night the Warden woke. Comes back more often than most." The name is theirs,
"Nobody", or "Lark" (`wayfinder.name`); with a false name, Sallow's men have
spent a month looking for someone who does not exist, and the survivor walks
in a day before they are known. Edric Marrow is in a cage. The survivor
chooses: free the cages (the freed follow them south; Sallow's war comes at
once); leave them; bargain.

**11. What you are (the act's turn).** The ledger, Keegan's chapter four, and
Chid, if the survivor goes to him, say it: the survivor died at the Low Ford
and rose with their mind. Every seed in section 6 lands here: "You were cold
when they brought you in", the far bank, the names going first, the mother's
face. Mechanically, from here the night's ember can be made to cost a memory
the player chooses.

**12. The war at the gate.** Sallow's people come south for the Unchained: the
survivor, Chid, the freed. Who holds the north gate is everything Act 2
decided (Holloway, Keegan, Maeca and the Pack, Redcowl's people or Rav's,
Brannoc). Afterwards Vonnra opens her cellar to the survivor: six sigil-keys,
kept by her family, and the one from the bones' hand makes seven. "Come down
with me."

## 8. Act 3: The Morrow

**Vonnra's truth.** With `vonnra.accused`, she tells it at the top of the
stair, in her own words and her own time: she owes the survivor for having
seen her. Without it, the survivor finds the pieces on the stair and she
admits only what they hold. The whole of it: the Ashford Fall; the failing
chain; the irons and the square coin; the carters' notice and the drowned
(Wat, Nell); the caravan she let go; Jessop sent through the door; the
survivor made.

**The stair.** The Legion's dead part for the Morrow's own light. Jessop is on
the stair, risen and held by the dead, Varrow silver and a Toll Tower token in
his purse: the bootprints' end.

**The heart.** At the bottom Grimtunnel holds the Warden's heart up to
something praying. To re-forge the chain the heart must go back into its
place, and it must be carried. In the cage Brannoc made for it (only if he
knows about Nell and stood with the survivor), it can be carried. Without
it, it burns whoever carries it: an Unchained can, at the price of names.

**Chid's truth.** He is Unchained, from the Order's day. He wrote the note to
Ashe. If the chain is re-forged tight, every Unchained goes back to the dark,
him included. He has known all along and wants the survivor to choose without
thinking of him; he is the one person who never asked anything of them.

**The inner door and the coin.** The dead at the inner door take a toll: one
square coin of the Legion, stamped VII. Vonnra's grandmother's. It buys one
thing that cannot be bought twice: one Unchained back up into the light, alive
and unlit, an ordinary mortal. Vonnra gives it to the survivor if her respect
for them is high (accusing her, and being right, raises it; lying to her
lowers it); otherwise she keeps it, for herself or for the second Unchained.

**What the Morrow prays for.** To be let die. The chain has kept it alive and
harvested for two thousand years; ember is its pain.

**The endings.** Three, all defensible; each with variants.
- **A. Re-forge the chain** (Vonnra's way). An Unchained lies down in the chain
  as the new link, forever. The valley keeps its lamps and its ember. Every
  other Unchained goes dark at dawn, except the coin's holder. Who lies down:
  the survivor; or Chid, if he offers (his trust high, and the survivor told
  him the truth about themselves); or Vonnra, if she was accused, respects the
  survivor, and was refused (she drowns herself at the Low Ford and rises, and
  "the second thing" happens a second time); or the second Unchained (Sella,
  Jory or a stranger), chosen for them; or one of Silverstair's caged, a
  stranger for everyone.
- **B. Break the chain and let the Morrow die.** No more ember anywhere. The
  lamps go out; Sallow's army falls down at dawn; the Unchained die properly,
  the survivor too, except the coin's holder: keep it, or give it to Chid (he
  ages at last), to Edric, or to the second Unchained. A world without its
  light, and without its cage.
- **C. Take the light.** Only if the survivor refused Vonnra, lied to or
  escaped the Vigil, and holds the Warden's heart: they carry the Morrow's light
  up themselves, the first Unchained who stays lit by day. A new god in the
  valley, and a new thing to fear. Keegan kneels or dies trying; Grimtunnel
  worships; Snib survives.

**The epilogue.** A page per person and place, worked out from the world, the
way `Chapter.cs` writes Act 1's: who lived, who rules the gate, what the
Penhale farm became, who keeps the Last Lamp lit.

## 9. How every thread ends

| Thread | Ends | Decided by |
|---|---|---|
| The Pack | Gone (slaughtered); the survivor's (allied); back in the deep wood (cured); hold the breakthrough's edge with Maeca; Greymuzzle dies of age at Act 2's end if alive | `beasts.outcome`, `greymuzzle`, `promise.broken` |
| The Dig | Blown (Act 1); boils over; breaks through under the farm or at the sinkhole; Grimtunnel crushed, faithless, or kneeling | `dig.pump`, `be.crates`, the ending |
| The Coyle Company | Honest, under Jory; Harlan funds the evacuation; Harlan hanged or driven out; the Company gone | `jory.knows_be`, `be.crates`, Act 2 choice |
| Pell | Saves the town by arithmetic; hangs; dies in Redcowl's cage; gone | `caravan.pell`, `pell.fate`, Act 2 choice |
| The Kerchiefs | Broken (Redcowl dead and Rav stays a doctor); the army under Redcowl; the army under Rav | `redcowl`, `be.crates`, `rav` regard |
| The Watch | Holloway dies at the gate; hands the survivor over; confesses; hanged | Holloway's regard, `holloway.post_told`, `holloway.lied_to`, the boots |
| Maeca | Leaves with the Pack; takes the Watch; dies at the edge; the survivor's | `maeca.lover`, the Pack, the boots |
| Brannoc | Breaks the irons and makes the heart's cage; forges them and learns too late | `nell.told` |
| Wenna | Saves the Penhales; dies in the bad air; outlives everyone to spite them | the mask, the breakthrough's width |
| Tam and the Penhales | Farm lost or spared; Pa alive or dead | `dig.pump`, `be.crates`, `tam.pa_in`, `tam.tock` |
| Keegan and the Vigil | Re-founded by Keegan; Keegan dead at the gate; Keegan disgraced; Sallow's war won or broken | Act 2 choices, `keegan.saw_risen` |
| Ysolde and Edric | Both free and gone; Ysolde dead at Silverstair; the notes go on | Act 2 choice, `wayfinder.name` |
| Sella | Her house in the south; drowned at the Kiln Ford and risen | Act 2 lies, `nell.told` (the irons) |
| Rook | Keeps the Last Lamp lit in every ending but B | the ending |
| Chid | Dark at dawn; the link; ages with the coin; kneels or will not | the ending, the coin |
| Vonnra | Binds the survivor; refused; becomes the link; dies at the bottom | `vonnra.accused`, the ending |
| The Waystation | Keeps its lamps; loses them; lives under a new god | the ending |

## 10. The consequence ledger

What Act 1 records, and where it lands. `WRITING_PASS.md` section 9 gives
each one's exact writer and reader.

| Act 1 fact | Set by | Lands |
|---|---|---|
| `be.crates` (`redcowl`, `harlan`, unset; burned with the Roost) | `redcowl.crates_keep`, `harlan.crates` | Act 2 beat 1 (how wide the breakthrough), beat 7 (the army's powder), beat 5 (what Harlan sold) |
| `redcowl.gave_charge` | `redcowl.crates_charge` | Act 1 (blow the pump with Redcowl's blessing); Act 2 (Redcowl remembers whose side the survivor took) |
| `jory.knows_be`, `jory.told_knew`, `jory.lied_to` | `jory.truth`, `jory.salt` | Act 2 beat 5; beat 8 (Jory on the south road) |
| `pell.fate` (`taken`, `ran`) | `redcowl.pell` | Act 2 beats 4 and 6 |
| `nell.told` (`gone`, `risen`, `lie`, `evaded`) | `brannoc.nell` | Act 2 beat 8 (the irons, the second crossing); Act 3 (the heart's cage) |
| `brannoc.saw_iron`, `brannoc.waits_buyer` | `brannoc.mark`, `brannoc.irons_after` | Act 2 beat 8 |
| `vonnra.accused` | `vonnra.f_accuse` | Act 3 (Vonnra's truth, the coin, ending A's Vonnra variant) |
| `vonnra.asked_jessop` | `vonnra.jessop` | Act 3 (the stair) |
| `sella.heard_past` | `sella.past` | Act 1 (the fortune quotes it); Act 2 (what Vonnra knows of the survivor) |
| `sella.sleeptalk` | `sella.sleeptalk` | Act 2 beat 11 |
| `holloway.post_told` | `holloway.post` | Act 2 beats 3 and 4 (Dannet's body) |
| `holloway.letter_seen` | `holloway.letter` | Act 2 beat 3 |
| `keegan.saw_risen` | `keegan.say_risen` | Act 2 beat 2 |
| `wayfinder.name` (`given`, `nobody`, `false`) | `wayfinder.margin` | Act 2 beat 10 |
| `tam.tock` | `tam.tock` | Act 2 beat 1 (who is home) |
| `maeca.kerchiefs`, `redcowl.ashford_said`, `redcowl.birds` | their nodes | Act 2 beats 4 and 7 |
| `chid.note_asked` | `chid.note` | Act 3 (Chid's truth comes easier) |
| `harlan.told_dig` | `harlan.be_dig` | Act 2 beat 5 (he has been told once already) |
| `dig.pump`, `tam.pa_in`, `tam.farm`, `beasts.outcome` | the Beast Problem | Act 2 beat 1 |
| `caravan.pell`, `redcowl`, `roost.cleared` | the Missing Caravan | Act 2 beats 1, 4, 6, 7 |
| `maeca.lover`, `sella.free` | the romances | Act 2 and the epilogue |
| `risen_once` (trait) | a death | Act 2 beat 2 |

## 11. Romance

All adults, all consenting; romance carries the intrigue.

- **Sella** (paid; open from the first night). *How:* "How much for the
  night?", fifteen gold, any survivor. *Reveals:* after `rook`, `sella.buyers`:
  she sells what is said upstairs, Vonnra above all; in the morning she may
  ask where the survivor comes from (`sella.past`), and the fortune then quotes
  it. *Costs:* gold; what you say upstairs reaches Vonnra. *Reacts:*
  `sella.say_maeca` (when Maeca is your lover), `sella.say_woman`. *Off the
  clock:* after three paid nights and enough warmth, one night she will not
  take the money (`sella.free`, `sella.free_night`), and in the morning warns
  you not to tell her anything you would not want Vonnra to hear. Fact:
  `sella.free`. *Act 2:* pay her to lie to Vonnra; she pays for it.
- **Maeca** (earned). *How:* her respect at 30 or more and her affection at 10
  or more, the Pack's trouble settled (cured or allied), at night in the
  tavern: she asks you out to the Hunters' Blind (`maeca.invite`); after
  that, `maeca.hub` offers the Blind on any night while it lasts. *Reveals:*
  `maeca.blind_morning`, the first time: the Pack saved her after Ashford.
  *Costs:* everything, if Greymuzzle dies (`maeca.gone` names it); she will
  learn who signed for the boots in Act 2, and you may be the one who tells her.
  Fact: `maeca.lover`.
- **Keegan** (teased, not opened). `keegan.dinner`: chapter eleven,
  fraternisation, read four times. An Act 2 route, and a tragedy if it is
  followed: chapter four is about you.
- **Act 2 routes:** Rav (wry, drunk, grieving his brother; if he takes the hat,
  the route goes with him to the Roost); Ysolde (after Edric, if he is freed;
  never while she is selling you).

### Intimate scenes and the explicit slots

The game will have a setting for intimate scenes (show in full, or cut
away), offered in the settings and when such a scene begins. Content reads
it as the fact `settings.intimacy`: `"full"` shows the full scene; anything
else (or nothing) shows the cut-away. **The lead wires the setting; nothing
in the game writes the fact yet.** Every intimate scene is written in full
before and after, with a cut-away version of the moment itself, and an
explicit-variant slot keyed to `settings.intimacy == "full"` that holds a
placeholder for the owner's writer:

| Slot | Node | Who, where, tone |
|---|---|---|
| 1 | `sella.night` | Sella and the survivor, the blue room at the top of Rook's stairs, by lamplight; warm, unhurried and funny, tenderness at the edges and quickly put away; ends with her asleep across you and the sun up. |
| 2 | `maeca.blind` | Maeca and the survivor, the Hunters' Blind in the Verge at night; wordless, wary, careful hands that become sure ones, frost outside, the Pack far off. |
| 3 | `sella.free_night` | Sella and the survivor, the blue room, not for money for the first time; slower and less sure than her working nights, the patter dropping away; a door she bolts herself. |

Each slot's text starts `[explicit scene:` so it can be found and tested
for; replace the whole placeholder with the scene.

## 12. Facts the story keeps

Act 1 (first pass): `promise.pack`, `promise.broken` (the Greymuzzle promise);
`wolf.blood` (Maeca's rule, washed at dawn); `bounty.stopped` (Holloway's
change of heart); `tam.pa_in`, `tam.farm` = `emptied`; `stream.clear` (the
stream healed, whatever the Pack's ending); `player.pardoned` (the strongbox
forgiven for Pell's ledger); `maeca.lover`; per-person flags `cb:<event>` (a
deed quoted back) and `say:<key>` (a remark made once). History events:
`farm_saved`, `broke_promise`, `bribed_snib`. Second pass: `aldo.buried`,
`caravan.bodies` (each set a day after its death, for the next morning's
report), `sella.free`; per-person `t_<npc>` once-flags for each character's
one question about themselves.

Act 1 (the writing pass): `nell.told`, `nell.buried`, `nell.asking`,
`brannoc.saw_iron`, `brannoc.waits_buyer`, `be.crates`, `redcowl.gave_charge`,
`redcowl.ashford_said`, `redcowl.birds`, `jory.knows_be`, `jory.told_knew`,
`jory.lied_to`, `pell.fate`, `harlan.told_dig`, `holloway.post_told`,
`holloway.letter_seen`, `vonnra.accused`, `vonnra.asked_jessop`,
`sella.heard_past`, `sella.sleeptalk`, `keegan.saw_risen`, `wayfinder.name`,
`tam.tock`, `maeca.kerchiefs`, `chid.note_asked`. History events:
`told_brannoc`, `lied_brannoc`, `crates_redcowl`, `crates_harlan`, `told_jory`,
`gave_pell`, `accused_vonnra`. A new mystery quest, `lamps`. Every one is
listed with its writer, its readers and its tests in `WRITING_PASS.md`.

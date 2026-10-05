# Story bosses: the fights at the end of the story's nights

The combat lead's half of `docs/design/STORY_NIGHTS_AND_TIME.md`. That document is the experience director's and covers the night's shape, falling and getting up, and the day's clock. This one covers what she fights: each story fight's way in (its beats, their goals and waves) and its boss (phases, telegraphs, adds, how the space changes, how it is beaten), plus the lengths, and what the simulation needs to run and measure it.

The owner approved it on 4 October. The Hollow by Night is built as the template (section 8 says what is built, what the first runs measured, and what is still to tune and to see in the game). Every number here is a starting point for the harness, set against the units in `docs/bosses/SURVIVORS_BOSSES.md` §0.

The owner, 4 October: "story nights ... should be much more specialized and fun - smaller arena - and they don't need endless - they have proper arpg end bosses right?"

**What changes, in one paragraph.** Today a story fight is twenty minutes of the table's horde on the table's 168 m arena, and then the story's foe for about eighty seconds. The foe runs a table ruler's script, and Redcowl's is the Red Hand's. A story fight becomes a short night in a place made for it:
- three authored beats on the way in, each ended by its goal, never by a clock;
- then a boss of three to four minutes on its own ground. Each of its phases changes the space, and it ends the way its cinematic does (C10 to C13).

The way in teaches the boss. Each beat's named foe shows one of the boss's mechanics before the boss uses it.

---

## 0. What every story fight keeps

### 0.1 The shape, in numbers

| Part | Length at par (first try, planned draft) | Ends when |
|---|---|---|
| The way in | 6–9 min: three beats of 1.5–3 min | each beat's goal is met |
| The boss | 3–4 min, transitions included | its ending (C10–C13) |
| The night | 10–14 min, 12 at par | the boss's ending; then back into the same night |

- **No clock anywhere.** There is no survival timer and no beat timer. A player who stands still in a beat stays in it.
- **A strong build cannot skip the boss.** Its floors are 25, 30 and 25 s, so an absurd build takes about two minutes at the least. It sees every phase, and its surplus shows as the Break.
- **A weak build sees every move.** Each phase has a 75 s ceiling. The soft enrage comes at 4:30 and the hard one at 6:00, so a weak build meets the boss's whole fight before an enrage meets it.

### 0.2 The build she brings

- **The ember drafts from nothing,** as in any night, paid 2.5 times quicker (experience agreed; `StoryNight.EmberPace`).
- **The yardstick is a table night's twelfth minute, not its twentieth.** Measured (two table nights, warden, deft): a table night has killed about 1,000 by minute 3, 8,000 to 9,000 by minute 12 and 20,000 by minute 20, and its ember stands at about 13, 31 and 45. A twelve-minute night in a smaller place cannot feed the ember twenty thousand kills, and should not try. So the boss is measured against what the night gives: about a table night's minute-12 build (ember about 30, about 32 cards at the boss).
- **Each stage has a crowd, finite and softened by its minute.** A story night is still a night: the crowd is the ember's food.
  - Each stage keeps its crowd at a number (the Hollow's: 26, 38, 44), from its own points out of her reach, until its pool is spent (300, 520, 650).
  - The crowd is softened as a table night's is at the minute the stage stands for (`ArenaRun.FodderEase`), so the build's growth shows as a crowd that melts.
  - **An ember floor at each stage's end** (10, 20, 28): what its dead would have given her if she was quicker than they were many. A quick stage is not a weaker night.
- **Two great blessings:**
  - one as the night opens, as now;
  - one as the boss ground opens, drawn from all of them, with one card that answers the boss's weakness (`SURVIVORS_BOSSES.md` §0.17).
- **Creature levels are fixed per stage,** by the table minute each stands for (a level every two and a half minutes over the tier's base, tier × 3 − 2):
  - the stages stand for minutes 2, 6 and 10: levels +0, +2 and +4;
  - the boss stands for minute 12: +4.

  A slow stage is not a harder one, and a stage is the same stage after a rise.
- **Nothing is farmed.** A stage's crowd is finite, and its named foe does not come again.

### 0.3 The beats

- **Goals:** bring down a named foe, break things (locks, windlasses, standards), light things, silence a caller, or free someone. One goal a beat, two at most.
- **One named foe a beat,** a miniboss from its people's roster (`MapOffers.Peoples`). Each previews one of the boss's mechanics: the boss is learned on the way in, as Nightreign's gauntlet before a Nightlord shows who is coming (`docs/bosses/RESEARCH.md` §4.5).
- **Waves** are authored, on top of the stage's crowd (0.2), set off by:
  - the beat's start;
  - the goal's progress (a lock broken, a picket silenced, Old Blue giving ground);
  - the named foe's arrival.
- **Between beats:** a sight or a line (the story lead's), 5–10 s of quiet, and the way to the next space opens.

### 0.4 The contract for a story boss

Everything in `ArenaBoss` holds: gates with floors and ceilings, the Break, the stagger bar, a weakness that breaks a channel, endings that wait for the last floor (`Spent`). A story boss adds the following.

- **Three phases, each a change of space:**
  - Greymuzzle: a ring that moves;
  - Redcowl: carts dragged into walls;
  - Grimtunnel: ground that splits;
  - the Barrow Lord: ranks that close.
- **Timings:**
  - floors of 25, 30 and 25 s;
  - ceilings of 75 s on the first two phases;
  - a soft enrage at 4:30 (its cadence a quarter quicker, its adds back to full);
  - a hard enrage at 6:00, named for each boss.

  These are fields on the script, not the table's 180 and 300 s.
- **The horde is off.** The only creatures on its ground are the adds it calls, each with a job. The arrival clears the field, as `MakeWay` does today.
- **Health:** start at the table ruler's multiplier × 1.6, at the boss ground's level (+4), and measure to the time. **The target is the length, not the number.** Greymuzzle: 88, the same at every tier (his level grows him, and the night eases each tier: `StoryNight.TierEase`), his blows at ×2.3 of his body's: his teeth are in his marked moves, not a brawl.
- **Damage:** in `SURVIVORS_BOSSES.md` §0.8's bands, as multiples of its blow:
  - contact ×0.4–0.6;
  - telegraphed blows ×1.5–2;
  - arena mechanics with 2 s or more of warning ×3.5–4.5, never a certain kill from full health.
- **A weakness and a bane:**
  - The weakness is a school, named on its card, whose single hit breaks its channel.
  - The bane is knowledge learned by day that makes the fight kinder. It is never needed, and without it the same tool is still there to be found.
- **Its ending is the story's.** Each one is a hook the script runs when it is spent:
  - let go or killed (Greymuzzle);
  - the kneel and the last words (Redcowl);
  - down the hole (Grimtunnel);
  - the hand at the gate (the Barrow Lord).

  The cinematic plays in and out through the boss hooks (`docs/cinematics/README.md` 11a).
- **Getting up (the owner: "GET UP TWICE IS TOO GENEROUS"; `SKILLS_DESIGN.md` §16.10):**
  - **Act 1:** one rise a night, to the start of the stage she fell in, with the build she brought into it; at the boss, to its opening, whole.
  - **From Act 2 (`chapter.done`):** none, unless she carries the one power that gets her up.
  - That power is **Not Yet**, an art held in the art's place (learned from Chid's *The Keeper's Office*), or **Cold, Then Not**, a legendary great blessing in the ember's draft.
  - **One rise a fight,** however many ways she has it; in Act 1 the night's own rise is one of those ways.
  - The third fall of the old rule is gone: a fall with no rise left is the night lost, and she wakes in town a day on (experience's).
- **A rise at the boss** restores its ground to the moment it opened: the ring, walls, pits, posts, fires and frost. The arrival's cinematic does not play again: a two-second re-entry does instead (his howl, the laugh, "Nondum"), so the arrival hook is told whether this is a first arrival or a rise.
- **Arena changes end with the fight,** within 3 s of the ending.

### 0.5 Rules every story boss keeps

From `SURVIVORS_BOSSES.md` §0.14, and one new rule:
- **Living walls are never targets.** These are the Pack's ring, the Legion's front, locked shields and the guard before the den. What she should kill is an ordinary target. Nothing soaks auto-aim.
- **Every weapon family can win.** Each boss has a window that melee reaches and a reason for range.
- **Attacking is never punished; standing in the wrong place is.**
- **Never out of reach for more than 3 s,** outside a phase's turn.
- **New: a story's outcome is never decided by the build by accident.** Weapons fire on their own at whatever is near.
  - So the B.E. crates are fired by a prompt, not by fire landing near them; a fire build standing beside them must not burn the Coyle cargo for her.
  - Greymuzzle is let go by a choice.
  - A cage post breaks because she chose to stand by it.
- **A voice before the killing move.** Redcowl's laugh, the Barrow Lord's orders and Snib's warnings come before the ground's mark, and are never instead of it. The telegraph language is `SURVIVORS_BOSSES.md` §0.9's.

### 0.6 What the harness is to show

Measured by the `story` harness (section 5.4), at tiers 1–4, with 16 seeds, planned and careless drafts, and deft and plain hands.

| Measure | Target |
|---|---|
| The night, planned draft and deft hands | 10–14 min, median 12 |
| The way in | 6–9 min; no beat over 3 min at its median |
| The boss, at par | 3:00–4:00 |
| The boss, absurd build | at least 1:55 (the floors hold) |
| The boss, a build at half par | every phase by its ceilings; meets the soft enrage |
| Cards at the boss | a table night's minute-12 count (about 32), within two |
| Won on the first try, with Act 1's one rise, plain hands | planned 90% or more; careless 70–80% |
| The boss on its first life, plain hands | 55–70%: it kills a first-timer sometimes |
| Runs under half health somewhere on the way in, plain hands | 20–35%: the way in has a dip, not a stroll (the table night's run-ups measured 2–5%) |
| Falls in a beat, plain hands | 5% of beats or fewer: the danger is at the boss |
| Telegraphed blows taken at the boss, plain hands | 3–6 on average |

---

## 1. The Hollow by Night: Greymuzzle, *Who Kept the Cold Off*

**Who he is.** The Pack's old dog-wolf, grey to the eyes, limping a little on the left fore. The Pack is sick from the slurry in the stream, not wicked, and his sick lie in the den's mouth. He wants to die on his feet in his own place (C10). This is the killing road of the Beast Problem. Maeca would not come.

**The question.** *Can you fight an old wolf in his own house?*
- The Pack is his walls.
- The cold is his weapon.
- His age is his only opening.

**The place** (what combat needs; the look is arena art's). About 60 by 80 m in all, in three spaces bent round in a hook (the outline and every point are in `HollowByNight.Ground`, `Play/Story/Hollow.cs`, for arena art to build to):
- **The clough** (south): a cut 14–16 m wide and about 26 m long, the stream down its east side, a rock at its head.
- **The sick water:** a flat about 24 m across where the stream pools. It has stepping stones, reeds, violet slurry shallows that slow and poison, and two deadfalls (heaps of dead wood) on the far bank.
- **The den floor** (the boss ground): a bowl about 32 m across.
  - The den's mouth is under the roots at its north edge.
  - Four deadfalls stand 10 m from its middle.
  - Root-knuckles and stones give low cover, never cover that hides a mark.

**Deadfalls.** She stands at one for 2 s and the ember in her lights the dead wood. It burns for 20 s and can be lit again any number of times. The Pack will not cross a fed fire's light, which reaches 5 m. A lit deadfall is a place, not a target.

### The way in

| # | Space | Goal | Named foe, and what it teaches | Waves | Length |
|---|---|---|---|---|---|
| 1 | The clough | Silence Old Blue | **Old Blue** (`mb_caller`) howls from a rock every 9 s: a 4 s channel on his bar. Damage of 3% of his health, a stagger or one hit of fire breaks it, and each howl he finishes calls five wolves from the clough's head. **His voice sets the pace, not his health:** four howls broken on a rock (or six howled) and he gives ground up the cut, his health held at his rock's mark (70%, 40%) until he does. Between rocks the Pack stands in the way and he is out of reach behind it: first the yearlings run a ring round her (8 + tier), then the whole cut comes down at her in five files of 3 + tier. On the rock at the clough's head there is nowhere left to go. *Teaches the moon-howl: a howl is a channel, and fire breaks it; and the ring.* | Wolves in twos and threes (18 standing). The ring; the rush. | about 1:45 |
| 2 | The sick water | Light both deadfalls on the far bank | The first light wakes the reeds: seven pulses of the sick and the whole (5 + tier), one every 17 s, on the reeds' own time. A fed fire's light is her room (the Pack will not cross it) and burns 20 s: the stage asks her to keep one fed. **Greenbelly** (`mb_blight_mother`) wades out with the fourth, bursting and brooding; her bite and trail are thinned here, her burst is the lesson. *Teaches the deadfalls: the ember lights dead wood, the Pack will not cross the light, and a fire is kept, not lit once.* | The reeds' pulses; the shallows slow and sting. | about 1:50 |
| 3 | The den's mouth (the place's set piece) | Bring down Whitethroat | **Whitethroat** (`mb_whitethroat`) runs the Drive every 11 s. The wolves close in a crescent (6 + tier) and she runs the gap they leave, a lane across it. Go through the wolves, never the gap. Her yearlings take the blows for her while she drives (she takes ×0.08); when her run misses she pants 2.5 s inside a pale-blue ring and takes ×2. At half the whole Pack wheels (9 + tier, every 9 s); at a quarter her yearlings ring the heroine and she is out of reach until it breaks. *Teaches the ring, and that a wolf who misses is open.* | The crescents. | about 1:40 |

The sick lie in the den's mouth (the story's sight). Then the Pack backs off her into a ring, and he walks out through it (C10's arrival).

### The boss

**Body.** The Pack-Mother's body (`boss_pack`, named Greymuzzle), slowed to Speed 4.6 for his limp. Health 88 times his body's at every tier, his blows at ×2.3. He is wordless: what is heard is the Pack.

**The Pack's ring.** About twenty wolves stand shoulder to shoulder round the fight, 12 m from the bowl's middle, with a grey hard edge drawn at their feet.
- They are not targets and cannot be hurt. They are the arena's wall.
- Touching the ring, a wolf snaps: she is shoved 2.5 m back in, and bitten (×0.3) at most every two seconds. A shove gives no moment of grace, so the ring is never a safe place to stand (`SKILLS_DESIGN.md` §16.7's lesson with bad ground). The first runs found a bot shoved ten times running for 10 each; the bite's two seconds of grace end that.
- A lit deadfall inside the ring makes it bow out round the fire's light. Fires are room.

| Phase | Its moves | How the space changes |
|---|---|---|
| **1. The Old Way** (100% to 65%) | **Stalk:** between moves he circles her at 7–9 m, limping, and does not brawl; walked into, he snaps (×0.3, at most every 1.5 s).<br>**Lunge** (every 4.5 s): a lane through her and 4 m past, 2.2 m wide, marked 0.9 s, ×1.6. He ends where it ends, and if that is the ring, it opens for him.<br>**Hamstring** (within 5 m, every 5 s): a 70° cone, 4.2 m, 0.8 s, ×1.5, and she is slowed by 55% for 2 s. Lamed, she is his: his next lunge comes at once.<br>**The Pack's turn** (every 13 s, not while he holds the den): a growl goes round the ring, and three of it cut across her from three sides, 0.4 s apart, each lane marked 1.1 s and more, ×1.5. The ground between the lanes is the answer, and it moves as each one lands.<br>**The ring's bite** (every 9 s): a growl behind her, then one wolf of the ring runs a lane across, marked 1.0 s, ×1.2, and goes back to its place.<br>**His age:** after every second lunge he stands and pants for 2.5 s. A pale-blue ring is round him, his breath smokes thick, and he takes ×1.25. | The ring holds at 12 m. Each fire she lights bows it out. |
| **2. The Moon** (65% to 30%) | He goes back to the den's mouth. The ring opens on that side, and five wolves stand guard in an arc before it, open at both ends: melee's way in is round the guard's ends to his flank.<br>**The moon clears** (as the phase begins): his first howl cannot be broken. The cold bites ×0.45 a second and his dead run every 1.5 s: the fires are the answer the sick water taught.<br>**The moon-howl** (then every 22 s): he sits and howls, an 8 s channel ("The moon-howl: break it!").<br>&nbsp;&nbsp;– The moon clears and **the cold** comes in from the ring at 1.2 m a second: violet frost that chills and bites (×0.15 a second, no grace).<br>&nbsp;&nbsp;– The frost stops at a lit deadfall's light, which stays clear.<br>&nbsp;&nbsp;– **His dead** (pale wolves, not targets) run lanes across her every 2 s, marked 1.2 s, ×1.5. They swerve round a fed fire.<br>&nbsp;&nbsp;– Break the howl with damage of 6% of his health inside it, a stagger, or one hit of fire. He is then held for 3 s and the frost melts back.<br>**The guard** before the den is not a target. Inside 2 m it shoves her 3 m back onto the den floor (never into the ring), bitten as the ring bites. Shots and zones pass over it.<br>**Between howls** he comes out, runs a chain of two lunges at her, goes back, and pants: melee's window. | The frost closes in during each howl. A fire is a room in it. |
| **3. On His Feet** (30% to 0) | He leaves the den's mouth for good. No more howls.<br>**Shake** (within 5.5 m, every 6 s): a 120° cone, 5 m, 1.0 s, ×1.8.<br>**Lunge chains of three** (every 8 s): each lane 2.6 m wide, marked 0.7 s, ×1.6. The second and third lead where she is going (0.6 s). Then he pants for 3 s.<br>**The last of the Pack** (at 15%): the ring breaks and comes in, twelve wolves that are ordinary targets. | The ring closes to 9 m, then breaks at 15% and the bowl opens to its edge. |

- **Weakness: fire.** It breaks the moon-howl, and the fires are fire.
- **Bane: Maeca's fed fires** ("They won't come near a fire that's fed"; `bane.fires`, set by her talk `maeca.fire`). The deadfalls are marked from the boss's first second, they burn for 35 s instead of 20, and the ring bows 7 m round them.
- **Enrages:**
  - **soft** (4:30): the ring closes 2 m and bites every 5 s;
  - **hard** (6:00), **The Long Hunt**: the light falls to half and never comes back, and he lunges out of the dark every 3 s.
- **The ending (C10).** Spent, he goes down on his side, and the ring lies down where it stands.
  - **Where the let-go is open** (`promise.pack`, not broken, the stream clean): two prompts wait at his side, *Let him go* and *Finish it*, with no clock.
    - Let go: he gets up and walks to the den (the `LetGo` built today), and `greymuzzle` becomes `spared`.
    - Finished: C10's death; `promise.broken` is set with the killed outcome, and Maeca turns against her as her rule says (story confirmed).
  - **Otherwise** he dies, with his look past her to the den.
  - Built on the story lead's `OnSpare` and `SpareVerb`, which `StoryFights.Spec` carries for the Hollow and the Roost: the choice is offered where the spec carries both outcomes.

---

## 2. Raid on the Roost: Redcowl, *Of the Kerchiefs*

**Who he is.** Dunstan Cutwell, Rav's brother, the last captain of a levy whose town he will not name. He feeds forty-one mouths by robbing the road. He comes into a fight like a host into his own camp: the laugh is the bait and "Mind where you swing" is the hook (C11). His bairns are asleep behind the line. Rav sewed his leg back on with a sail-needle, and it is the leg he owes him.

**The question.** *Can you hear the hook in the laugh, and do you still swing with his children asleep behind him?*

**This replaces the Red Hand's script for Redcowl.** The Toll, the thief and the bell are the table's ruler's, and stay his. Redcowl gets his own fight.

**The place.** About 55 m, climbing north, in four spaces:
- **The ruts:** a ravine road 14 m wide, with lips on both banks where the pickets stand.
- **The cage yard:** beside the road, with the four cages and a store.
- **The camp's yard:** open ground where the levy can form and march. The six B.E. crates stand by the store while they are still in the yard.
- **His own fire** (the boss ground): a hearth yard about 30 m across.
  - The big fire stands at its back, with a line of carts and the tents behind it.
  - Torches stand on poles.
  - His people stand round with torches: watchers, not fighters, and not targets.

### The way in

| # | Space | Goal | Named foe, and what it teaches | Waves | Length |
|---|---|---|---|---|---|
| 1 | The ruts | Silence the three pickets | Each picket has a torch and a whistle on a bank's lip. While one stands, its whistle calls footpads off both banks at once (the pincer). **Firepot Nan** (`mb_firepot_nan`) comes with the third whistle and lobs pots from the lip. *Teaches the lobbed circle and fire left burning: his thrown torch.* | Footpads in pincers; pillagers on the lips (no more than 3 throwing). | 1.5–2.5 min |
| 2 | The cage yard | Break the locks, or bring down Barn-Door if the cages are empty | **Barn-Door** (`mb_barn_door`, shielded, ironbound) holds the cage row. A lock is a target only while she stands within 4 m of it, so her fire breaks the one she stands by. *Teaches his cage: to break a post, stand by it.* If the caravan's men are still held (`caravan.survivors` unset), the freed run down the ruts; they do not fight. The last lock broken runs the cage rescue's own effects (`Verge.OpenCage`): `caravan.survivors` = `rescued`, the quest entry, the deed and the cage lines, Jory's included. The fourth cage stands empty with its door open (C06). | Footpads from the store; bruisers with Barn-Door. | 2–3 min |
| 3 | The camp's yard (the place's set piece) | Break the levy: bring down the Pike-Captain | **The levy** forms and marches in step: 6 + tier pikes (`levy_pike`) in a line, locked. The line is not a target while it holds. Shots pass through it at half to what is behind, and area and melee break a man at its ends. **The Pike-Captain** (`mb_pike_captain`) walks behind the line and is the target. The line wavers when he takes damage of 5% of his health within 6 s, and breaks when he falls. *Teaches the levy he calls in his second phase.* | The line, twice if the first breaks early; footpads at its flanks. | 2–3 min |

**The crates** (only while `be.crates` is unset or `redcowl`). In the camp's yard, a torch burns on a post beside the six crates, with a prompt: *Fire the crates* (1 s).
- A 12 m amber ring is marked for 3 s (a shout of "DOWN!"), then a crater.
- Everything in the ring takes the arena-mechanics band (×4): the levy line breaks, and the Pike-Captain goes to a quarter of his health.
- The beat ends within seconds, and `be.crates` becomes `burned`, with everything the story does with that: Act 2's breakthrough is narrower, and the army has no powder.

It is a shortcut that costs the story, chosen with a prompt, never by a fire build's stray shot. **With no crates** (`harlan`, `dig`, `watch`, `sunk` or `burned`), the third beat is the levy alone and nothing else changes. That night needs no extra beat.

The crates stay out of the boss ground on purpose. A powder store going up beside the tents of sleeping children is not a choice the game should put at her feet.

Then the Kerchiefs hold their ground and part, torches up, and he comes through them (C11's arrival, the bairns line).

### The boss

**Body.** `redcowl`: one model with the greataxe (C11). Until it exists, the Red Hand's body. Health is the Red Hand's multiplier × 1.2, a start of `35 + 5.6 × tier`.

| Phase | Its moves | How the space changes |
|---|---|---|
| **1. The Host** (100% to 65%) | **The Greeting** (within 5 m, every 5 s): a wide sweep, a 150° cone, 4.5 m, 1.0 s, ×1.4.<br>**"Ha! HA."**, then **the Hook** (every 10 s). The laugh comes first: his head goes back, and there is no mark yet (0.6 s; the voice before the killing move). Then he brings the axe overhead down a 7 m line, 2.2 m wide, marked 1.2 s, ×2.0. The axe sticks: he is open for 1.8 s (a pale-blue ring) and takes ×1.25. **The laugh is always the hook.**<br>**Pass the torch** (when she keeps beyond 9 m for 4 s): a watcher hands him a torch and he throws it, a 2.4 m circle, 1.2 s, ×1.2, leaving fire for 3 s.<br>**His lot:** two footpads at a time from the watchers' ring, four alive at most, all ordinary targets. | His people's torches are the light; the yard is open. |
| **2. Forty-One Mouths** (65% to 30%) | **"Red to me! Up, my lot!"** as the phase begins: a rallying call, a 3 s channel.<br>**The cage** (every 18 s): bruisers drop a ring of ten posts round her, 5 m out, marked grey for 1.5 s and then solid for 8 s.<br>&nbsp;&nbsp;– It has **one gap, the door, facing him**. He waits at the door with the Hook down the door's lane.<br>&nbsp;&nbsp;– Inside are two footpads.<br>&nbsp;&nbsp;– Ways out: stand by a post (the posts are targets only from inside, nearest first, so her weapons break the one she stands by); dash out before it closes; or let the Hook land in the door and go out behind it.<br>**The levy** (once, at 50%): six pikes march in step out of the cart-line under the old red standard with the arms of his town (C06). They push, and are not targets while locked. They break when he is hurt hard (5% in 6 s) or staggered.<br>**The Hook** goes on, every 12 s. | The call drags the carts into two short walls (marked grey for 1.5 s, then solid). The yard becomes a pen about 22 m across. |
| **3. Mind Where You Swing** (30% to 0) | **The laugh is gone.** He never laughs again.<br>**Chains** (every 7 s): the Hook (marked 1.3 s, longer now there is no laugh), then the Greeting, then a shoulder charge (a lane 8 m long, 0.8 s, ×1.6). The axe sticks at the chain's end for 1.5 s.<br>**The bairns** (once, at 15%): a child cries behind the carts. He stops and turns his head to the tents for 3 s: open, ×1.5 taken, the fight stopped for him. Then, cold: "Mind where you swing." His cadence is ×0.85 to the end. | The watchers lower their torches and the light draws in. |

- **Weakness: storm.** One hit breaks "Red to me! Up, my lot!": he is held for 3 s, the carts still come, and the levy does not (his people heard nothing).
- **Bane: the leg** (Rav's talk of the sail-needle, `rav.redcowl`; read from Rav's flag `once:redcowl`, which his hub's choice records). He wrenches the stuck axe out on the sewn leg, so the open moment is 2.6 s and his stagger fills twice as fast in it. The leg holds: it never breaks, and his last words pay it.
- **Enrages:**
  - **soft** (4:30): a cage every 12 s;
  - **hard** (6:00), **All Forty-One**: the whole camp turns out at the carts, torches up, and the levy re-forms every 15 s.
- **The ending (C11).** Spent, he goes down on one knee with the axe-head in the dirt, laughs, and says his last line: the town if she said it to him, the leg if not. `redcowl.last_words` is set as C11 sets it, then `OnWin`.

---

## 3. The Dig Boils Over: Grimtunnel, *Ever So Grateful*

**Who he is.** The Boss of the Dig: three lamps, a grudge, and the Warden's heart keeping him company in the dark, its cold blue showing through the cracks in his hide (C12). He is a believer, not long angry about anything. He cannot die in an arena; the fight is won when he goes back down the hole, delighted. Snib comments.

**The question.** *Can you keep your feet when the ground is the enemy, and its Boss is in a very good mood?*

**The place.** About 55 m, curving round the great pit:
- **The pit:** the Dig's north side, a drop that cannot be stood on.
- **The edge:** the headframe and two more shaft heads along the lip, each with a windlass.
- **The tub-way:** rails running along the lip to a brake-house at the east end.
- **The pump-house:** at the outflow.
- **The boss ground:** the lip by the headframe's ruin, about 30 m between the pit's edge and the spoil heaps, with the line of the crack across it. Snib's perch is on the nearest heap.

### The way in

| # | Space | Goal | Named foe, and what it teaches | Waves | Length |
|---|---|---|---|---|---|
| 1 | The edge | Break the three windlasses | Each shaft head boils lamplings until its windlass is broken and the shaft falls in ("until nothing more comes up"). The windlasses are the beat's targets. **The Wick-Mother** (`mb_wick_mother`) comes up with the second shaft's wave, and her swarm comes from below. *Teaches what comes up under her: the deep lamp, and the Under.* | Lamplings from each open shaft; wicks with the Wick-Mother. | 2–3 min |
| 2 | The tub-way | Bring down the Chucker at the brake-house | **The Chucker** (`mb_bombardier`) lobs pots from the brake-house. Ore tubs run down the rails at her: lanes marked 1.5 s, ×1.5, that flatten lamplings in their way too. *Teaches lanes and lobs, and that his own crew's hazards hurt his own: Snib's barrel.* | Sappers on the heaps; lamplings along the rails. | 1.5–2.5 min |
| 3 | The pump (the place's set piece) | Bring down the Perfect of Fuses | **While the pump runs:** **the Perfect of Fuses** (`mb_fuse_boss`) sends fuse-runners at her with lit crates. These are moving bombs: kill them, or step off as one blows (a 3 m ring, 1.5 s). When he falls, his last crate rolls into the engine and **the pump blows**: a 10 m ring marked for 3 s, everyone out. `dig.pump` becomes `blown` with the win, as now. **If the pump already stands still** (`broken`, `blown` or `moved`), its wreck is held by **the Lamplighter** (`mb_lamplighter`, fans of flame) instead. *Teaches the crates' burst: the barrel.* | Fuse-runners in threes; sappers. | 2–3 min |

Then the ground between her and the pit splits in a line, and he hauls himself up out of it (C12's arrival, the pump line).

### The boss

**Body.** `grimtunnel_roused`, with an emissive seam mask for the heart's blue (C12). Health is the table's multiplier × 1.2, a start of `22 + 3.6 × tier`.

| Phase | Its moves | How the space changes |
|---|---|---|
| **1. The Shift** (100% to 65%) | **His three lamps flare in turn** (every 7 s):<br>&nbsp;&nbsp;– **red, the blasting ember:** three charges lobbed round her, 2.2 m circles, 1.4 s, ×1.6, leaving fire for 3 s;<br>&nbsp;&nbsp;– **blue, the deep lamp:** a 1.8 m circle at her feet, 1.0 s, ×0.8, and 2 + tier diggers come up through it;<br>&nbsp;&nbsp;– **green, slurry:** a 60° cone, 7 m, 1.2 s, ×1.2, leaving ground that slows for 4 s.<br>While a lamp flares (2.5 s), blows on him count against it too. A lamp is 8% of his health; broken, its verb is gone for the night (as built).<br>**Under** (every 12 s): he dives, and the mound runs at her for up to 3 s. The mound is him: it takes half, and every weapon reaches it. He bursts up where it stops: a 3.5 m circle, 1.2 s, ×2.0. Then he is dazed for 4 s and takes ×1.5. Frost on the mound brings him up at once, dazed for 8 s.<br>**Moths** (every 20 s): 6 + 2 × tier lamplings surface round the brightest thing: his lit lamp, burning ground, or her. | The crack stays open behind him. Snib comments from the heap. |
| **2. The Collapse** (65% to 30%) | Each Under leaves a **sinkhole** where he burst: 2.6 m, marked grey for 1.5 s. There are up to 5 + tier; the oldest fills when the cap is passed.<br>**Snib's barrel** (at 55%, then every 25 s): Snib rolls a barrel of blasting ember off the heap, with his warning first ("Boss! BOSS! Not the good stuff! It IS the good stuff.").<br>&nbsp;&nbsp;– The barrel is **not a target**. She kicks it by walking into it, and it rolls 8 m the way she went.<br>&nbsp;&nbsp;– If it touches him or a flaring lamp, it blows (a 4 m circle, 1.2 s); her own burning ground does not set it off. On him that is a tenth of his health, and his hide cracks: ×1.25 taken for 12 s.<br>&nbsp;&nbsp;– Left alone for 12 s, he picks it up and throws it at her: a 4 m circle, marked 2.0 s, ×3.5. | The ground fills with holes that she and his crew route round. |
| **3. The Heart** (30% to 0) | The Warden's heart wakes in him, blue in every seam.<br>**The crack opens:** marked grey for 2 s, the line he came up through widens to 4 m across the ground's middle, splitting it in two. He crosses by Under; she crosses at its ends, or with a dash (5.5 m).<br>**The heart's pulse** (every 10 s): he slams the ground and three blue bands run out from him. Each is clear inside, marked 1.0, 1.6 and 2.2 s, ×1.0, and chills for 1.5 s.<br>**In a temper:** a third quicker, his pick within 4 m every 3 s, a 90° cone, 3.6 m, 0.9 s, ×1.5. | The ground is in two halves. The pits stay. |

- **Weakness: frost.** It stops him under the ground.
- **Bane: his own lamp** (`grimtunnels_lamp`, carried from the prologue). Set it down with a prompt, and his next two Unders come up under it, dazed for twice as long: he cannot resist his own light.
- **Enrages:**
  - **soft** (4:30): the pits stop filling, and moths come every 12 s;
  - **hard** (6:00), **The Fall**: the floor caves from the edge inward, a ring of pits closing 2 m every 10 s.
- **The ending (C12).** Spent, he reels, tumbles back into the crack and hangs by his claws ("I told it about you! It went ever so QUIET!"), then drops. The crack grinds shut, every pit fills in a rolling wave, the lamplings dive, and Snib has the last word. As built (`GoDown`), now with the cinematic.

---

## 4. Behind the Sealed Door: the Barrow Lord, *Of the Seventh Legion*

**Who he is.** An officer of the Seventh Legion, armour green with age, an iron crest. The Legion has held the inner door for two thousand years. The dead know what she is; they have been waiting for her, and she is early. He gives his orders to his dead in the old tongue, one plural word each, and to her he says only "Nondum" and, at the end, "Redi" (C13). **They are not beaten. They send her home.**

**The question.** *Can you read a formation, and will you go back when you are sent?*

**The place** (story's canon, from the experience director): the fight is at the head of the stair and never goes down it. Going down is Act 3, and in C13 Jessop stands far below. The space is the Legion's hall, its roof fallen in and open to the moon, with its wall tops standing:
- **The hall:** about 22 m wide and 40 m long, from the door at the south to the stair's head at the north. It has fallen roof-beams and sarcophagi as low cover (which stop a lane), and niches in the walls.
- **The head of the stair** (the boss ground): a landing about 30 m wide and 20 m deep before the stair's mouth in the north wall.
  - The stair's mouth cannot be walked into.
  - The dead come up it.
  - Ranks of the dead stand at attention along its walls: the walls of the fight are men.

The door plays first, outside, as C13's door.

### The way in

| # | Space | Goal | Named foe, and what it teaches | Waves | Length |
|---|---|---|---|---|---|
| 1 | The hall's south end, as the first ranks come up | Bring down the Decurion | The dead come up the stair in files and march the hall's length. **The Decurion** (`mb_decurion`, "Scuta!") leads the third rank in a shield line. *Teaches the line: locked shields are not targets, it breaks at its ends, and its halves wheel.* | Files of risen; archers behind. | 1.5–2.5 min |
| 2 | The hall's length | Bring down the Scorpion | **The Scorpion** (`mb_old_quarrel`) kneels at the stair's head and shoots down the hall's length: aimed lines, a step off is a dodge. The beams and sarcophagi stop his bolts. *Teaches the pilum: a lane is dodged by a step, and cover stops it.* | Bone heaps; risen in twos. | 1.5–2.5 min |
| 3 | The hall (the place's set piece) | Break the three standards | **The Signifer** (`mb_ford_bell`, "Signa!") plants three standards down the hall. While one stands, it raises a file of the dead every 10 s and quickens the dead near it. A standard is a breakable part (holy and fire ×1.5); the Signifer falls with the last. *Teaches the standard at the heart of his testudo, and Chid's bane* (below). | Files from each standing standard. | 2–3 min |

Then the dead part, and he comes up through them: "Nondum" (C13's arrival).

### The boss

**Body.** `boss_dead`. Health is the table's multiplier × 1.2, a start of `20 + 3.5 × tier`.

| Phase | Its moves | How the space changes |
|---|---|---|
| **1. The Drill** (100% to 70%) | **"Iungite!"** (close up, every 16 s): 6 + tier shieldmen rise in a line between him and her and march at her at 2 m a second. Locked shields are not targets. Shots pass through at half to what is behind, and area and melee break a man, splitting the line there.<br>**Pilum** (every 7 s, when she is beyond 5 m): a lane 20 m long, 1.3 m wide, 1.0 s, ×1.6. The pilum stays in the ground for 6 s as a small collider: cover from the next.<br>**Gladius** (within 4.8 m, every 6 s): a 90° cone, 4.5 m, 0.9 s, ×1.5. | The ranks stand on the walls. |
| **2. Testudo** (70% to 40%) | **"Testudo!"** (as the phase begins, then every 22 s): eight shields ring him at 3.6 m, with **the standard** at the centre. The standard is a part: 6% of his health, holy and fire ×1.5.<br>&nbsp;&nbsp;– Shots aimed at him arc over the rim; melee and zones reach through the gaps at half.<br>&nbsp;&nbsp;– Break the standard and the ring drops; he is held for 3 s.<br>&nbsp;&nbsp;– Otherwise the ring opens after 6 s for **the Charge of the Century**: three columns run lanes out from him (2.2 m wide, 1.3 s, ×1.5), two below 55%. The gaps are the safety.<br>**Chid's bane:** a broken standard can be lifted (a prompt). Carried, it stops the century closing up for the rest of the fight: they followed the pole, and the ranks on the walls turn to face it in her hands. | At each testudo, a rank steps down off each wall into the fight. The landing narrows 2 m a side. |
| **3. Nondum** (40% to 0) | **The front:** the ranks come down off the walls and close round the fight in a front, a step every 8 s, to 8 m from the landing's middle. Their shields have a grey edge and are not targets. Touching the front shoves her 2 m back, ×0.5. **Holy on him makes the front give a step:** the dead give ground to the Order's school.<br>**Gladius** (within 4.8 m, every 4 s): the cone, then a lane 5 m long, 0.7 s, ×1.5.<br>**"Tenete!"** (every 12 s): a band round her, 4.5 to 6.5 m, 1.5 s, ×0.8; caught in it, she is held for 1.2 s.<br>**He will not lie down** (spent): he goes down inside a pale-blue circle (3 m) for 8 s.<br>&nbsp;&nbsp;– Standing in it for 3 s lays him down; holy does it twice as fast. The front's dead come at the circle to drag her out.<br>&nbsp;&nbsp;– If she fails, he rises with a quarter of his health, a fifth quicker, and the phase runs again.<br>&nbsp;&nbsp;– If she lays him down, he does not stay down: C13's hand at the gate. | The landing closes to the front's ring, and opens again only at the end. |

- **Weakness: holy.** It lays him down twice as fast, makes the front give ground, and keeps his raised dead down.
- **Bane: the standard** (Chid: "They never followed a man. Never. They followed the pole."; `bane.pole`, set by his talk `chid.legion`). Without it, the standard still breaks, but it cannot be lifted.
- **Enrages:**
  - **soft** (4:30): a new line forms every 10 s;
  - **hard** (6:00), **The Last Watch**: the front walks in to 5 m.
- **The ending (C13).** She lays him down, and he gets up inside her weapon, puts his gauntlet flat on her breastbone ("Redi"), and pushes once. The dead step back onto the stair together and stand. The night ends there, as every story fight's does: C13 stages the open stair-head, but there is no way out to walk to, and the result follows. C13's shot 1 reads "The blow. He does not fall."; with the laying down it becomes "she stands over him, and he will not stay down". That is the cinematics lead's line to change.

---

## 5. What the simulation needs

All of this is combat's to build once the owner approves. Arena art builds the places (the outline builder, agreed with experience); combat owns walkable ground and colliders that change mid-fight.

### 5.1 The story night runtime

A new `Play/Zones/StoryNight.cs` (a `ZoneRuntime` and an `IBossArena`), not a mode of `ArenaRun`.
- **Why separate:** `ArenaRun` is the table's night. Its clock, `ArenaPacing`, `Escalation`, the Kindling and the long night are all things a story night drops.
- **What it shares with `ArenaRun`:** a small kit factored out of it: spawn and harden, the chests and loot, the boss's arrival (`MakeWay`), the victory and the result.
- **Beats are data:** `Play/Story/Beats.cs`, one script per fight, as a list of beats. Each beat has:
  - its space and level;
  - its goal (`Kill`, `Break`, `Light`, `Silence`, `Free`, with what it counts);
  - its waves and their triggers;
  - its named foe.
- **Checkpoints:** a snapshot of the battle's player side at each beat's start and at the boss's opening, which a rise restores:
  - the weapons and their ranks, the boons and great blessings, the ember and its level, the stats, health, dash charges and draughts.

  The beat's creatures are cleared and its waves begin again. Experience owns the rise's flow; the snapshot is ours.
- **Space:**
  - walkable ground that opens (the boss ground, the cart walls, the crack, the pits) as live changes to `InBounds` and colliders;
  - a moving bound (the Pack's ring, the Legion's front), composed into `InBounds`.
- **Pay:** XP and crafting for the night's own length (with experience and crafting: `Arenas.XpFor`, `Crafting.Night`).

### 5.2 The contract: `StoryBoss`

A subclass of `ArenaBoss` with:
- `SoftAt` and `HardAt` as fields, with the table's 180 and 300 s as their defaults;
- floors and ceilings per section 0.4;
- `Ending(Enemy)`, the story's end, run when it is spent;
- `Arrive(bool rise)`: the arrival hook, the cinematic on a first arrival and the two-second re-entry on a rise;
- a reset that a rise calls.

The story scripts are their own classes: `Greymuzzle`, `Redcowl`, `GrimtunnelStory` and `BarrowLordStory`. The story's spec picks them; the table's rulers stay exactly as they are. Shared moves move from the table's scripts into `ArenaBoss`, so both use them: lunge chains, Hamstring, Pilum, Testudo, the lamps, Under.

`IBossArena` gains:
- `Part(def, x, z)`: a breakable piece (a standard, a lock, a windlass, a post), a stationary creature, as the ember-core is;
- `Bound`: a moving ring or front, with its dressing creatures, which are never targets;
- `Prompt(id, x, z, text, act)`: a prompt in battle (let him go, fire the crates, lift the standard, set the lamp);
- `LightPool(x, z, r, life)`: a fed fire's light, which bounds the ring, the cold and his dead's lanes;
- `Field`: the cold, frost that closes in and stops at a light;
- `Pushable(x, z)`: Snib's barrel, kicked by walking into it, blowing on what it touches;
- `ShovePlayer(dx, dz, metres, damage)`: new in `Battle`, which today has knockback only for creatures. It gives no moment of grace.

### 5.3 BossSense

`BossSense` is what a person does after dying to the boss once. For the story it needs to:
- **go to the objective:** the runtime publishes the goal's point (a deadfall to light, a lock to stand by, the lay-down circle, a prompt), and the hands go there when no blow threatens;
- **read moving bounds:** the ring and the front become out of bounds for the steering's candidates, with a margin;
- **fight the fires:** in Greymuzzle's moon-howl, stand in a fed fire's light, and light the nearest deadfall when none burns;
- **get out of a cage:** when shut in one, go to the post furthest from the door, away from him, and stand;
- **kick the barrel:** come at it from the side away from Grimtunnel and walk through it;
- **make choices by policy:** let him go, fire the crates, lift the standard, set the lamp, each a flag, so the harness measures both ways.

The laugh needs nothing new: the Hook's lane is a marked blow like any other.

### 5.4 The harness

A `story` command (`godot/balance/Harness/StorySim.cs`):

`story --fight hollow|roost|dig|vault|all --tiers 1,2,3,4 --seeds 16 --policy planned,careless --hands deft,plain`

It runs each night through its beats and boss, with rises, and writes JSONL with:
- each beat's minutes, falls and lowest health;
- the boss's phase times, its time to kill, its Break and the telegraphed blows taken;
- falls at the boss;
- the night's minutes;
- the cards at the boss against a table night's minute 20;
- the choices made.

`Report.cs` prints section 0.6's table, and `Targets.cs` holds the targets.

### 5.5 Tests (`godot/tests`)

- **The floors hold:** an absurd build takes each story boss through the game's own wiring and takes at least its floors. This is §16.1's lesson: the game's boss scripts once never ran while the tests passed.
- **Beats end on goals, never on time:** hands that stand still never finish a beat.
- **Rises restore:** a fall in beat 2 restores the build as it entered; at the boss, full health, phase one, and the ground as it opened.
- **Endings set the story's facts:** `greymuzzle` dead or spared, `redcowl.last_words`, `dig.pump` blown when it ran, `vault.opened`.
- **Arena changes end within 3 s of the ending:** the ring, posts, carts, pits, crack, front and frost.
- **The crates go up only by their prompt:** a fire build standing by them does not blow them.
- **One test for each mechanic:** a lamp broken, a lock by position, a post by position, the barrel kicked into him, the standard lifted.

### 5.6 Order

1. **The runtime, the contract and the Hollow by Night, as the template** (experience's order: its kit is furthest along, and its ending is the richest). Then measure it with the harness and judge it on screen at full resolution.
2. **The Roost, the Dig and the Vault,** once the Hollow has been judged.

The table's nights and rulers are unchanged throughout.

---

## 6. For the other leads

- **Story** (`a73ca9d35d0c487a9`): done. The words (the pulls, the sights between beats, and the fights' voices) are in `WRITING_PASS.md` §21 at `worktree-agent-a73ca9d35d0c487a9@25bb2dc3`; copy them from there when building.
  - The banes read `bane.fires` and `bane.pole`. Take both off StoryLint's seed list when the fights read them. The leg reads Rav's flag `once:redcowl`.
  - Confirmed: freeing the men runs the cage rescue's effects; Greymuzzle's let-go is her choice; C13's laying down is in the bible.
- **Experience** (`ab406cf9ddd22b03b`): the Roost's third beat is the levy, with the crates as an optional shortcut, so a night without crates still has its set piece. Fire near the crates becomes a prompt (section 0.5).
- **Arena art** (`a26767f7f9955cb56`): each place's spaces and sizes are in its section. Every place needs low cover only, a boss ground that reads at 30 m by night, and the landmark at the edge, not in the fight.
- **Animation** (`a435f4dd0ac80df75`):
  - Greymuzzle: his limp, the pant, the sitting howl and the lying down.
  - Redcowl: the laugh, the axe stuck and wrenched out, the head turned to the tents, and the kneel on the axe.
  - Grimtunnel: hanging by the claws.
  - The Barrow Lord: rising inside her reach, and the hand.
- **Cinematics** (`a3058a45eee41d695`): C13's shot 1 now follows the laying down (section 4). Each fight needs its two boss hooks.

## 7. Later

- **The Road Back** (C14, `road_back`) is built in this shape when the story stages it: the Low Ford road at the wagon, the drowned out of the river, Brannoc holding the edge of his lantern's light as an ally, and Wat as the boss, won at dawn.
- **The later story bosses** in `docs/bosses/` (the Thing in the Barn, the Warden of the Kiln Ford, the Silver Penitent, the Centurion of the Stair, Grimtunnel at the bottom) take this contract from the start.

## 8. Built, measured, and what is left (4 October)

### 8.1 Built: the template, on the Hollow

- **The runtime:** `Play/Zones/StoryNight.cs`.
  - The game makes a story night of any story fight with a script (`StoryScripts.For`); the other three still run as a table's night, told quicker, until theirs are written.
  - `--stage N` begins one at its Nth stage, for pictures and play (`--stage 3` is the boss).
- **The fight's pages:**
  - `Play/Story/StoryPlace.cs`: the place as spaces of capsules, gates and points, its walls, and the spaces open now. Arts are bound by the open spaces, so no blink or leap crosses a shut gate.
  - `Play/Story/StoryFight.cs`: the stage and fight bases, the deadfalls, and `IStoryArena`.
  - `Play/Story/Hollow.cs`: the place and its three stages.
- **The boss:**
  - `Play/Bosses/StoryBoss.cs`: the contract, with a soft enrage at 4:30 and a hard one at 6:00.
  - `Play/Bosses/Greymuzzle.cs`: the ring, the old way, the moon and its cold, on his feet, and his end.
- **The battle:**
  - `Sim/Checkpoint.cs`: a journal of the build's verbs, `Snapshot` and `Restore`, and `ShovePlayer`.
  - `Battle.CancelBlows`; `HurtByGround` made public with a name; `Enemy.Scripted` (a creature the script moves in its mind's place).
- **The rise:** one rise a fight (`PlayerState.Rose`), the art Not Yet (`cold_then_not`) and *The Keeper's Office*. The maps' falls go to one (`SKILLS_DESIGN.md` §16.10).
- **The hands:**
  - `BossSense` reads the stage's goal, the moon-howl's cold (to a fed fire, or to light one), and the ring as a wall.
  - The harness's `Pilot` goes to the goal; `NavField` walks it round the walls within the place's box.
- **The harness:** `story` (`balance/Harness/StorySim.cs`, `--fight --tiers --seeds --policies --bot --act2 --choice`), with section 0.6's table. `STORY_TRACE=KEY` traces one night.
- **Tests:** `StoryNightTests` and `CheckpointTests`. They cover:
  - the gate shut, the place holding her walking and dashing, and every stage walkable;
  - stages ending on their goals, never a clock;
  - Old Blue's howl broken by fire, and a deadfall lit (the Pack keeps out of its light);
  - Act 1's one rise and the build put back, then the lost night waking her in town; from Act 2, no rise without the art;
  - the ring holding, and a fire bowing it;
  - the floors holding against an absurd build;
  - her choice at his side, both ways;
  - the cold, kept off by a fire;
  - a rise at the boss beginning him again;
  - pay for the night's own minutes.

### 8.2 Tuned (4 October, evening)

The Hollow, tiers 1–4, 64 nights a row (`story --fight hollow --tiers 1,2,3,4 --seeds 16 --bot plain,deft --policies greedy,random`):

| Hands, draft | Won | Night (min) | Way in (min) | Stages (s) | Boss (s) | Under half on the way in | Boss on its first life |
|---|---|---|---|---|---|---|---|
| deft, greedy | 97–100% | 8.8–11.2 | 5.0–5.9 | ~105 / 112 / 90–120 | 212–292 | 11–25% | 95–100% |
| plain, greedy | 86–88% | 8.8–10.7 | 4.9–6.2 | ~105 / 110 / 90–130 | 189–252 | 16–36% | 81–88% |
| plain, random | 80–89% | 10.6–13.4 | 5.9–7.1 | ~110 / 111 / 140–190 | 257–343 | 11–38% | 78–89% |

- Falls in a stage: none. Cards at the boss: 32 at every tier.
- The experience director, on the length: "a tight 10 beats a padded 12". The night is about ten minutes planned and deft; nothing is padded to reach twelve.
- The boss's first life is above its 55–70%: the bots don't learn between tries, so a fall at the boss is decided by the build and a rise rarely changes it; pushing it lower took the planned win under 90%. It is to be judged at the screen.

How it got there:
- **The stages were given beats with their own pace** (his voice, the reeds' pulses, her drives), not health; the first runs' stages ended in half a minute because a minute-6 build melts fodder.
- **His teeth went into his marked moves:** two thirds of what hurt her was his brawl between moves. He stalks now, and his moves hit harder.
- **Every tier is the same night:** creature health eased 0.3 a tier and bite 0.2, named foes and his health not grown by the tier, ember per kill normalised to the tier, and a dusk on the first stage (a level a tier above the first). Tier 3 had run twice as long and three times as dangerous.
- **Found on the way:** the harness's hands stood stuck at walls' corners (a quarter of runs timed out in the water; fixed in the Pilot and the place's NavField); Burn Bright stacked its numbers at each rank and kept them through a rise (fixed in `Boons.cs`, with a test over every blessing); Cold, Then Not burned everything in eight metres in one frame (now each body as the fire's front reaches it, after a 0.35 s cold).

### 8.3 What is left, in order

1. **The Roost, the Dig and the Vault** in the Hollow's shape (Redcowl's spared end plays `.spared` then `.flit`), with story's words (`WRITING_PASS.md` §23).
2. **The Hollow at the screen:** the experience director is running it at 1920×1080, stage by stage.
3. **Data owed by others:** the place drawn to `HollowByNight.Ground` (arena art).

### 8.4 To see in the game (none of it has been seen yet)

- The place: the walls are invisible inside the old round arena until arena art builds the outline. Do the gates read as shut? (Today they are only marks of posts.)
- The ring: twenty wolves standing still, facing in. Does it read as a wall, and does a shove read as a shove?
- The deadfalls: today they are only a light coming on, with no wood and no flame drawn. They need a look (skills VFX or arena art).
- The cold: a band of violet ground closing in. Is it readable over the ring and the lanes?
- Greymuzzle panting (the pale-blue ring), lying down, the two prompts at his side, and his walk to the den.
- The stage's lines (the story's words) as she crosses between stages, and "You get up." with its fade (experience's staging of `StoryFall`).
- The camera: 22 m on the way in and 27 m at the boss. Is all of the den floor in view?
- The art Not Yet in the arts screen: it has no active use, its icon is the blessing's, and it has no facets.

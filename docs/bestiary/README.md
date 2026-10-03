# The bestiary: monsters, counters and depth

A design study of the creatures that fill the ember arenas: what each asks
of the survivor, what answers it (skills, arts, statuses, gear, blessings,
oaths), what risk and reward should go with the answers, how kinds mix in a
horde, and how the same arena can be played relaxed or sweaty. Written for
the main session to read and judge; **nothing in the game was changed**. The
one piece of code is a measuring probe under `probe/`, which compiles the
game's logic read-only.

The owner's brief: *"think about the various monster types we will have in
our arenas, counters to them both in items and skills, pros and cons cost
benefit risk reward analysis and the complexities of varying mob types. this
game can truly be played as simply or as sweaty as the player would like."*
Bosses are the `claude/cloud-bosses` session's; they appear here only where
they meet the horde.

## The files, in reading order

| # | File | What it is |
|---|---|---|
| 1 | `README.md` | this: the map, the ten recommendations, the decisions |
| 2 | `ROLES.md` | sixteen roles (fodder to thief), what each asks, how the relaxed player survives it and the sweaty one exploits it, the engine verbs behind it, and what the roster covers today |
| 3 | `ROSTER.md` | the four peoples creature by creature, measured; what each lacks; sixteen proposed creatures in the code's units; contested ground; tuning notes |
| 4 | `COUNTERS.md` | the matrix: roles against the skills (measured), statuses, arts (measured), affixes, Marks, sets, Named items, blessings and oaths (measured); twelve champion Signs; which lopsided cells are good and which are traps |
| 5 | `RISK_REWARD.md` | what the arena pays, the cost of a counter, generalist and specialist, the oaths' win rates from the balance lab, a Weight for each oath, champions and Signs, expected values |
| 6 | `HORDES.md` | what mixes do (measured), the pairings that make emergent problems, a readability budget by tier, the half hour's shape, signature events, mixing from tier 1 to the top |
| 7 | `DEPTH.md` | simple to sweaty: what reading buys (measured), every system both ways, floor and ceiling by tier, auto-pilot rules, what each player must be told |
| 8 | `IMPLEMENTATION.md` | every proposal mapped onto the code, sized, in build order |
| – | `RESEARCH.md` | the sources: survivors-likes, ARPGs, Hades, Doom, Risk of Rain, Left 4 Dead and more; 21 lessons |
| – | `probe/` | the measuring program, its results and its limits |

## What the measurements found

The probe put each kind of creature (and five mixes) against fourteen
skills, two gear variants, a generalist pair and nine arts, with the
balance lab's plain and deft bots, 4,352 runs. The balance lab itself was
run across every oath at tier 2. The findings that drive the
recommendations:

1. **A crowd's danger is its biggest blow.** The 0.45 s of grace after a
   blow caps intake at about 2.2 blows a second, so fourteen risen hurt a
   warden 20–30% of their health a minute and one barrow knight 150–450%.
2. **The guard is the one hard counter, and it is aimed at projectiles.**
   Knifestorm kills 0.1× the median against guards; a champion bruiser
   takes 56–99 s to kill with Volley, Knifestorm or Rimeshard.
3. **Guards in front of throwers are the strongest emergent problem**:
   the shield-wall mix hurt 2.8× what its kinds do alone.
4. **Lobbers hard-counter melee** when the player stays off the fire, and
   that is a good trade the player chooses.
5. **Frost is the elite answer, on defence**: Rimeshard halves the hurt from
   elites and chargers without killing them faster.
6. **Seeking Motes and Arcweb never fall below neutral**: generalists far
   ahead of the field.
7. **Mirror Step halves or thirds the damage of every role**: a must-pick
   art anyone can learn.
8. **The oath of the hunt is by far the hardest and is paid like a mild
   one** (`RISK_REWARD.md` has the balance lab's win rates).
9. **Reading matters against only four roles today** (ranged, lobber,
   charger, lunging elites); wolves, fodder, guards and raisers play the
   same for a reader and a non-reader.

## Top ten recommendations

1. **Fix the four measured problems first** (`IMPLEMENTATION.md` §1, XS):
   champion guards at 60%, a melee champion and herald for the Lamplings,
   the oath of the hunt repriced, Mirror Step's reflections ignored by
   champions. Each is one number or one line.
2. **Give champions Signs** (`COUNTERS.md` §4): twelve one-verb affixes with a
   tell and two answers each, forbidden pairs, one or two by tier. Eight of
   them are built from verbs the code already has. This is the largest gap
   in the horde and where the sweaty player reads, prepares and profits.
3. **Spend the verbs already written** (`ROSTER.md`, `IMPLEMENTATION.md` §3):
   `Orbit`, `Trail`, `Split` and multi-shot are coded and unused. Seven
   creatures (Ridge-Runner, Slurry Sow, Bone-Heap, Wick, Lamp-Pole, Levy
   Crossbow, Blasting-Cart) cost data and a look each, and the Lamplings
   double.
4. **Cap the telegraphs, not only the shooters** (`HORDES.md` §3): wind-ups,
   burrowers, bursts and enemy ground each get a counter like
   `RangedCap`, and a readability budget by tier.
5. **Compose each people's signature problem as an event** (`HORDES.md`
   §4.3): the Wall, the Ford Rises, the Dig Opens, the Ring. The shield wall
   becomes a moment with a tell, three times a run, instead of the steady
   state after minute nine.
6. **Let the table tell more** (`DEPTH.md` §5.1): the people's question in a
   line, the reward and Weight in a line, and the survivor's own build
   against the people's resistances. Counters are only fair when they can
   be scouted.
7. **Teach through death and the bestiary** (`DEPTH.md` §5.3): the end of a
   lost arena names the tell that was missed; the codex grows a creature's
   role, tell, answers and resistances as it is killed.
8. **Price the oaths by measured difficulty and show the Weight**
   (`RISK_REWARD.md` §4), Hades' way: speed costs three times what damage
   does.
9. **Add auras, mending and thieves** (`IMPLEMENTATION.md` §8, §10): two
   small specs and one behaviour give five creatures (the howler, the lamp,
   the drummer, the goodwife, the bell) and four Signs, plus the
   treasure-goblin chase (the Glimmer-Thief eats ember stones, which are
   light).
10. **Keep the floor's rules** (`DEPTH.md` §4): no immunities, guards ≤ 80%,
    resistances ≤ 50%, wind-ups ≥ 0.6 s, no rank-and-file blow above a
    quarter of a fair health bar, no art required, every Sign answerable two
    ways. The relaxed player keeps winning tiers 1–2 on auto-pilot.

## Decisions for the owner

1. **Should enemy hazards hurt the horde?** Pots, burning ground and death
   bursts hurt only the survivor today. Letting them hurt the horde at half
   turns every lobber and exploder into a tool for the sweaty player and
   costs the relaxed one nothing, but it softens the oaths of embers and
   ruin (`IMPLEMENTATION.md` §9).
2. **Mirror Step: weaken it, or keep it as the relaxed player's lifeline?**
   It is the best defensive tool in the game for anyone. A champion that
   sees through reflections keeps it strong against the crowd.
3. **Signs: how many, how soon?** The proposal is none at tier 1 before
   minute 10, two from tier 4, three on late heralds. Fewer keeps the first
   arenas gentle; more gives the sweaty player more to read.
4. **Contested ground** (two peoples at war in one arena): an offer from
   tier 3, or kept for the endless play past the half hour?
5. **Thieves**: the Glimmer-Thief steals ember stones from the ground
   (never what the survivor holds). Is any stealing acceptable, or should
   the thief only carry a purse of its own?
6. **Weight**: show it on the table as a number (Hades' heat), or keep the
   table in words?
7. **The Lamplings' champion**: the Blasting-Cart (new art: a cart) or the
   tunneler (no art) until the cart exists?

## Status and confidence

- Code read on `claude/vigilant-galileo-l6jqyx` at `9e0f22e`; every claim
  about the code names the file.
- The probe's numbers are matchups, not difficulty: one skill, no draft, a
  creature level of 5, a warden's body, lone elites fought standing. Ratios
  between loadouts are the trustworthy part (`probe/README.md`).
- The balance lab's oath sweep is small (tier 2, two seeds a cell, the deft
  bot); its win rates are a direction, not a table to tune from.
- Research is cited per claim in `RESEARCH.md`; claims that could not be
  confirmed are marked.

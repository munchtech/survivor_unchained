# One build: the night's cards are her talent tree

Classes design (C2), 5 November 2026. The owner's decision of 4 November is locked ("sounds good"): one character, one build, one combat everywhere, and the cards are the talent tree. This page designs inside it. It is design and data only; the Warden slice builds it. It supersedes CLASSES.md §2.10, CLASS_IDENTITY_AND_TALENTS.md §3.2 "By night" and §3.3's night points, and SKILLS_DESIGN's random draft. The lamps themselves are `godot/data/content/skill_lamps.json`, with the warden's seven wicks written in full.

## For the owner (one page)

**The rule.** She is one build everywhere: her calling and type, the Lamps, the skills she carries, each skill's wick, her Flare and her gear. A fight in town, on the Verge, in a story fight, in a map or at the Wayfinder's table is the same fight with the same numbers. Night is mood and pacing, never a rule. What differs is the **run** (a table night, a map, a story's night, the prologue's Ford): the ember burns only in a run.

**The ember lights lamps on her own skills.** Each time it rises she gets three cards, and every card is a dark lamp on a skill she carries. She lights one. It costs nothing and burns until first light. No card is power from nowhere: each one is a lamp she could light for good in town.

**Every lamp changes how a skill plays.** A wick is twelve lamps in three strands, and each strand ends in a **Turn** that transforms the skill. A lamp is one of four things:
- an element swap: Sunder's edge takes holy fire;
- a shape: the heavy line splits in three;
- a trigger: a block swings Oathblade at once;
- a cost with its pay-off: Sunder swings slower, but every second swing is heavy.

No lamp is a bare "+10%". Each lamp also adds a rank to its skill, and rank is how the skill hits harder. The card shows the rank going up, so nothing is hidden.

**Lit for good.** Each skill earns a point every third level, eight by level 22. At a lamp-post in town a point lights a lamp with oil. From then on it burns from the first second of every fight, by day too, and the ember never offers it again. A Turn takes two points. Changing them stays free in town.

**Try before you buy.** First light puts out what the ember lit, and nothing else. Her own lamps, skills, level, gear and gold stay. Losing a night costs that night's loot and the time spent. The dawn card remembers: *"You lit Splitting Stroke three nights running. Light it for good at the lamp-post: 2 points."* The lamp-post glows on that lamp when she gets back.

**One rule that scales.** Lamps she has lit for good are already burning, so the ember only offers what she hasn't lit. A newcomer's cards are first lamps and a first Turn. A veteran's are the deep end:
- a **second Turn** (one may burn beside a Turn she has lit for good);
- the last lamps of her strands;
- **Unions**, a lamp two of her skills share once each burns a Turn.

**A newcomer's first night.** She walks into the Low Ford with her sword and her greatsword cleave, and almost nothing lit. The first kill spills ember. When it rises, the fight freezes on three cards and one line explains what a card is. She takes *Third Blow*: every third cleave lands heavy and cracks the ground. Three cards later the strand's Turn is waiting, because a finished strand always deals its Turn. *Splitting Stroke*: every second swing splits the earth. By the time the Warden comes, her sword throws crescents of light and the ground breaks wherever she turns. At first light the lamps go out over the dawn card. It shows what the ember lit, what she keeps (four levels, her gear) and one line telling her what to light for good. Her second and third nights start with that lamp already burning, the Turns she liked come sooner, and a third skill opens at level 4 to light.

**A veteran's tier-4 night.** She queues tier 4 at level 30 with six skills, each already burning eight lamps. From the first second, every other swing splits the ground in three, the bell drags the pack onto her shield, and every blow that lands on her answers in light. Her cards are the deep end. Sunder's heavy line takes holy fire beside the Turn she lit for good. A strand gets its last lamp. Then a Union lights: with Dawnpulse and Judgement Disc each burning a Turn, the disc carries the dawn and breaks into light wherever it strikes. By midnight she has lit everything she can reach, and the horde is what keeps growing. The last cards burn a skill hotter for the endless dark.

**Cut:**
- the day skill book (tomes, "every third level teaches", attribute needs);
- separate day and night slots;
- the random draft (new skills at night, passives, blessings, "+X%" rank cards);
- CLASSES §2.10's quarter sizes by night;
- the separate night kit.

**Kept:** a pick every time the ember rises, evolutions (now Turns), Unions, the Flare, the Lamps and Wicks, the table's tier pick, and the endless.

**Three questions for you (my pick first):**
1. **Where do skills come from, now that tomes go?** *Pick: each skill her calling may carry opens at a level (her type's first), and she chooses what to carry at a lamp-post.* Gear can still lend one. The alternatives are skills found as loot, as with PoE's gems, or every skill open from level 1.
2. **A Union is one lamp that two skills share, and both keep firing.** Today's merge replaces two skills with one and frees a slot. *Pick: shared (Hades' duo blessings).* A merge at night only loses a skill, because nothing can fill the freed slot until dawn.
3. **A newcomer's first nights carry two or three skills, not the old night's six.** *Pick: keep the slots (two at level 1, three at 4, six by 20). Her Turns fill the screen.* The alternative is three slots from level 1.

---

## 1. The rule, exactly

| | The world (town, the Verge, story zones by day) | A run (table nights, maps, story nights, the prologue's Ford) |
|---|---|---|
| Her build | whole: the board, carried skills at their rank, oil lamps, Hand, Flare, gear | the same, whole, from the first second |
| The ember | does not burn | burns: kills spill it, it rises (about 23 times in a 12-minute tier-1 night, measured on rc3), each rise deals three cards |
| Lamp sizes | in full | in full (CLASSES §2.10's quarter is struck) |
| At the end | nothing to take | first light puts out the ember's lamps and levels |

- **Slots:** two at level 1 (her grip and her type's first skill), three at 4, four at 8, five at 14, six at 20 (CLASS_IDENTITY §3.7, already `SkillBook.SlotsAt`). One count everywhere; the night's six combat slots go.
- **Skills open by level** (question 1). Each skill record carries `opens` (the warden's in the JSON): her type's signatures at 1-3, the other type's at 4-6, then kindred and valley skills as she grows. She carries any open skill her calling may carry, swapped at a lamp-post in town. Gear that grants a skill is unchanged.
- **Points and rank:** a carried skill has one point at level 1 and one more every third level (eight at 22: today's `SkillBook.Rank`). A lead-in costs 1, a Turn 2, a Union 2 (one from each of its skills). **A skill's rank is the points burning on its wick**, oil and ember together, and each rank is its growth (+16% damage for most skills, `growth` in skills.json), shown in the skill's sum (`WickBook.Sum`). By day rank is at most 8; a run can take it to 13.
- **The Turn rule:** one Turn per skill by day. In a run a second Turn may burn **beside a Turn lit with oil**. Never a third.
- **Respec:** free at any lamp-post in a town, never mid-run (§3.5 stands). Light my way spends unplanned points on the suggested strand, so a player who never plans still has every point burning.

## 2. The offer (each time the ember rises)

1. **Candidates:** for every carried skill, the first dark lamp of each strand whose parent burns; a Turn only if the Turn rule allows it; every Union whose two skills each burn a Turn.
2. **Always dealt, never left to chance** (as evolutions are today): a Turn whose three lead-ins burn, and a ready Union. If more are ready than there are cards, the ones on the skill that has dealt the most damage tonight come first.
3. **The rest, drawn by weight:** ×3 a lamp that continues a strand already burning (oil or ember), ×1.5 Light my way's suggested strand, ×1 any other; a card just shown ×0.15 (a reroll looks again).
4. **Spread:** at most two of the three cards from one skill, while two or more skills have candidates.
5. **Never:** a burning lamp, a lamp whose parent is dark, a Turn the rule forbids, a banished lamp (banished for the night).
6. **Count:** three, a fourth with luck (today's `LevelUp.Count`). Skip, reroll and banish stay.
7. **Nothing left to light:** the ember's surplus, three cards: *Hotter* (one skill +1 rank tonight, ten at most a night; this is the endless's honing), *Banked* (a third of a Flare), *A draught* (mend 30%).

The card: the lamp's name, the skill's glyph, its strand's pips (which lamp of four), the one line, and "rank 4 → 5" (a Turn "→ 6"). A Turn's card is drawn larger. A Union shows both glyphs.

## 3. What dawn takes, and what the dawn card remembers

- **First light takes:** every lamp the ember lit and the ranks they brought, and the ember's levels. **On a loss** it also takes the run's loot (today's rule), and the time (story nights wake her in town).
- **Never:** oil lamps, the board, her skills, her level, her gear, gold already banked, traits.
- **The card** (H8's `DawnCard`, re-worded by the build lead when the rule lands; not touched here): the ember's lamps by name (Turns first, then "and N more"); "You keep": your lamps, your gear, your gold, the level the night taught; and **one memory line**, the first that applies:
  1. a lamp lit three or more runs running: *"You lit Splitting Stroke three nights running. Light it for good at the lamp-post: 2 points."*
  2. else the Turn on the skill that dealt the most damage: *"Splitting Stroke did most of your killing tonight."* plus the same price;
  3. else the first Turn she lit.
- **The price** is the lamp's cost plus any dark lamps under it. If the skill hasn't the points yet, the line names the first lamp of that strand she can light now: *"Start it: light Third Blow for good (1 point)."*
- **The save keeps** each lamp's runs lit and the last run's number. The lamp-post glows that lamp until she lights it or dismisses it.

## 4. The data model (`godot/data/content/skill_lamps.json`)

**One record per lamp, for every skill.** It replaces `wicks.json` (day strands with shared lead-ins), the evolutions and catalysts in `skills.json` (night) and the unions' merge. The game does not read it yet; the build lead wires it. Fields:
- `id` (`<skill>.<strand>.<n>`), `skill`, `strand`, `n` (1-3 lead-ins, 4 the Turn), `parent` (the lamp before; a Union lists two Turns' strands);
- `name`, `rule` (the one line, numbers in it);
- `kind`: `element`, `shape`, `trigger`, `cost` (a cost and its pay-off) or `calling` (the calling's mechanic deepened);
- `turn`, `cost`, `effects` (engine keys);
- `engine`: `built` (the sim does it today), `rule` (a named rule exists), `new` (to build);
- `from` (what it replaces: an evolution, a v1 skill lamp, a built Turn);
- `draft: true` where the name waits for the story writer.

Each skill's header lists its strands, the suggested strand (Light my way) and `opens`.

## 5. The migration list (for the build lead)

1. **The wicks' lead-ins are bare percents: about 75% of today's wick lamps.** All nine per wick come from `wicks.json`'s three shared templates ("+10% damage", "+10% area", "8% shorter cooldown", "15% chance to {status}", "+10% damage to {statused} enemies"). They retire. `skill_lamps.json` replaces `wicks.json`; the built Turns' engine keys carry over.
2. **The night draft's full pool is what is cut** (`LevelUp.Draft`):
   - new skills at night and the night's six combat slots;
   - rank cards ("+16% damage");
   - the passives and their catalysts;
   - great and milestone blessings;
   - the Flare's four blessings (`bright_hour`, `ember_answers_twice`, `short_wick`, `called_shot`): the Flare lead folds them into Flare lamps or retires them.

   §2's offer replaces it. Kept: `Count`, skip, reroll, banish.
3. **Evolutions become Turns.** Two per base skill, on its wick (the warden's six are in the JSON). `Battle.Evolve` becomes lighting a Turn; catalysts go.
4. **Unions become shared lamps.** Each needs a Turn burning on both skills; both keep firing; the union weapon's behavior becomes the lamp's effect. The merge and the freed slot go.
5. **`SkillBook` retired.**
   - `Learn`, `Tome`, `Calling()`, `Meets`, `Attribute`, `Need`, `NightRank`, `Attuned` and `Familiar` go.
   - `SlotsAt` stays as the one slot count; `Rank` stays as points by level.
   - `opens` replaces learning.
   - Tomes leave the loot tables, shops and quest rewards (the loot lead).
   - Saves: known skills open, slotted skills carried, discovered dropped.
6. **`WickBook`:** from "a plan, and rank lights its first r" to a lit set: oil lamps (paid with points) and ember lamps (tonight). `Battle.Relight` goes. Rank = points burning.
7. **`Journey.StartBattle` and `Journey.Douse`:**
   - A run starts with the whole build: `Character.Kit(ch)` as by day, sizes in full.
   - `EmberOn` is set only in a run. `b.Night` becomes mood only.
   - `Douse` puts out ember lamps and ember levels and leaves the carried skills as they are; it no longer rebuilds the kit from gear.
   - The two gear kits (`Kits`, CRAFTING_DESIGN 20.2) fold into one, and coals and Marks work in every run (the crafting lead).
8. **CLASSES §2.10 struck.** `LampLoadout.Night`, `Lamps.NightSize`, `NightCut`, `GiftSize`, `ReflexSize` and the smalls' road lean go. Every lamp works in full everywhere, and the board's smalls give their own numbers.
9. **The Lamps screen and wick panel** (UI lead):
   - an ember lamp is drawn as an ember (ember color, a slow flicker), an oil lamp burns steady, a dark lamp is dark;
   - no points are shown or spent during a run, and an ember lamp reads "until first light";
   - the lamp-post glows the dawn's suggestion;
   - a skill's rank reads as the points burning.
10. **The dawn card** (`DawnCard.Build`): H8's words are re-worded to §3 ("The ember takes" becomes the ember's lamps by name), plus the memory line. `CharacterData` gains each lamp's runs lit and last run.
11. **The tutorial** (`docs/story/TUTORIAL_COPY.md`; the story lead owns the words):
    - F4 "A skill" becomes one card explained at the first rise: a freeze, the arrow on the card's skill glyph and strand pips. *"The ember lights a lamp on one of your skills. Choose one. It burns until first light."*
    - F3 (the great blessing) is cut.
    - F12's middle line becomes *"The ember's lamps went out at first light. Light the ones you liked for good at a lamp-post."*
12. **The harness:**
    - The bots play a full build from minute 0 (`--onebuild`, §6).
    - One balance band for all replaces "a full board at night within ×1.25 of an empty one" and the ×1.25 night lean. At each tier, for every level band that plays it, the human wins 78-85%, deft 95%+, standing falls 80%+ and idler 70%+.
13. **Maps and story nights:**
    - The ember burns in maps too.
    - Story nights stop "starting with nothing"; their ember floors and great blessings go, and their stages are re-measured.
14. **Her swings land on the clip's contact frame** (A1's routing, GATE M1). Today a swing's damage lands on the sim's own timer, and no C# reads the clip's contact frame. In the Warden slice a melee blow (her grip's swings, Sunder, Oathblade, Groundbreaker's heave) deals its damage on its clip's contact frame, so the lamps that count swings and heavy blows (*Third Blow*, *Splitting Stroke*, *Crescent*) land on the frame the player sees. The combat lead, with A1's Stage B clips.
15. **Docs:** CLASSES §2.10, CLASS_IDENTITY §3.2 "By night" and §3.3 "Points" are marked superseded by this page.

## 6. The harness note (H6's 45-60 s rule, on a full build)

Numbers only. No retuning here; that is the build lead's job.

**The setup.** The harness switch `--onebuild` lives under godot/balance only (commit cbde3e259). It approximates the rule until the offer exists:
- She starts with her slots' worth of her calling's skills at day rank, wicks lit by Light my way, and the board lit for her level.
- Lamp sizes are in full by night.
- The draft can only rank or hone what she carries. A rank still lights the next wick lamp, so the night still climbs.

It is the Pack's board, tier 1 (a 10-minute table night). The numbers are won/fell %, across the four callings.

| Run | Seeds | standing | idler | kiter | human (lowest life) | careless | deft | human's boss s |
|---|---|---|---|---|---|---|---|---|
| R0 rc3 at HEAD, level 1, the old draft | 16 | 0/100 | 28/72 | 9/91 | 84/16 (0.27) | 67/33 | 98/2 | 138 |
| R1 one build, level 5 (3 skills, rank 2) | 32 | 0/100 | 3/97 | 4/96 | **61/39** (0.22) | 39/61 | **76/24** | 230 |
| R2 one build, level 10 (4 skills, rank 4) | 16 | 0/100 | **61/39** | 27/73 | **100/0** (0.35) | 98/2 | 100/0 | 142 |
| R3 one build, level 30, full board, tier 1 | 16 | 5/95 | | | 100/0 (0.54) | | 100/0 | 58 |
| R3 the same, **tier 4** | 16 | **23/77** | | | **75/25** (0.41) | | **83/17** | 65 |

Read against H6's gate (standing falls 80%+, idler 70%+, human wins 78-85%, deft 95%+):
- **The 45-60 s rule holds on a full build.** Standing still falls on every tier-1 night at every level, even at level 30 with the full board (95%). Marks on her before the boss stay at 22-28 a night (R0: 23).
- **The bands don't hold yet**, and they miss in both directions:
  - At level 5 the first table night is too hard: human 61%, deft 76%. The reaver's human wins only 12%, against the warden's 91%, the stalker's 75% and the arcanist's 66%.
  - At level 10 it is too easy: the human wins every night, and the idler wins 61%.
  - A veteran at tier 4 sits under the band (human 75%, deft 83%), with standing just under the gate (falls 77%).
  - The old night evened out every level by drafting from nothing. One build has to be tuned per level band and tier, which is §5 item 12's single balance band.
- **What it doesn't measure:**
  - the real offer (a choice of lamp, the new lead-ins, Turns always dealt, second Turns, Unions);
  - chests, which still open by the old rules.
  - The human's ember still reaches 25 by the end of a tier-1 night, so about 23-25 rises a night stands.
- **The data:** scratch `classes_c2\h\r0-r3.jsonl` (backed up to `survivorsunchained_inputs\scratch_classes_c2\`), `run.sh`; `python tools/balance/danger.py <file> --by tier` or `--by calling`.

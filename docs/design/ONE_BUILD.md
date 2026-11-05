# One build: the night's cards are her talent tree

Classes design (C2), 5 November 2026. The owner's decision of 4 November is locked ("sounds good"): one character, one build, one combat everywhere, and the cards are the talent tree. This page designs inside it. It is design and data only; the Warden slice builds it. It supersedes CLASSES.md §2.10, CLASS_IDENTITY_AND_TALENTS.md §3.2 "By night" and §3.3's night points, and SKILLS_DESIGN's random draft. The lamps themselves are `godot/data/content/skill_lamps.json`, with the warden's seven wicks written in full.

## For the owner (one page)

**The rule.** She is one build everywhere: her calling and type, the Lamps, the skills she carries, each skill's wick, her Flare and her gear. A fight in town, on the Verge, in a story fight, in a map or at the Wayfinder's table is the same fight with the same numbers. Night is mood and pacing, never a rule. What differs is the **run** (a table night, a map, a story's night, the prologue's Ford): the ember burns only in a run.

**The ember lights lamps on her own skills.** Each time it rises she gets three cards, and every card is a dark lamp on a skill she carries. She lights one. It costs nothing and burns until first light. No card is power from nowhere: each one is a lamp she could light for good in town.

**Every lamp changes how a skill plays.** A wick is twelve lamps in three strands, and each strand ends in a **Turn** that transforms the skill. A lamp is one of four things:
- an element swap: Sunder takes holy fire, and what it sears burns;
- a shape: the heavy line splits in three;
- a trigger: a block swings Oathblade at once;
- a cost with its pay-off: Sunder strikes softer, but every swing sears.

No lamp is a bare "+10%". Each lamp also adds a rank to its skill (a Turn adds two), and rank is how a skill hits harder. The card shows the hit itself, before and after (Sunder's hit 41 → 45), so nothing is hidden.

**Lit for good.** Each skill she carries has its own points, not a shared pool: one at level 1 and one more every third level, eight by level 22. At a lamp-post in town a point lights a lamp with oil. From then on it burns from the first second of every fight, by day too, and the ember never offers it again. A Turn takes two points. Changing them stays free at a lamp-post, and *Light my way* lights any points she leaves to it each time she comes into a town.

**Try before you buy.** First light puts out what the ember lit, and nothing else. Her own lamps, skills, level, gear and gold stay, and so do the levels the night taught her. Losing a night costs that night's loot and the time spent. The dawn card remembers, and its price is honest. When the strand's three lead-ins already burn for good it reads *"You lit Splitting Stroke three times running. Light it for good at the lamp-post: 2 points."* For a newcomer who can't afford it yet, it names the first step: *"Start it: light Third Blow for good, 1 point."* The lamp-post glows on that lamp when she gets back.

**One rule that scales.** Lamps she has lit for good are already burning, so the ember only offers what she hasn't lit. A newcomer's cards are first lamps and a first Turn. A veteran's are the deep end:
- a **second Turn** (one may burn beside a Turn she has lit for good);
- the last lamps of her strands;
- **Unions**, a lamp two of her skills share once each burns a Turn.

**A newcomer's first night.** She walks into the Low Ford with her greatsword's cleave (Sunder) and Oathblade, the blade that swings on its own. Nothing is lit for good: she has never stood at a lamp-post. The first kill spills ember. When it rises, the fight freezes on three cards and one line explains what a card is. She takes *Third Blow*: every third cleave lands heavy and cracks the ground. Two more cards finish the strand, and the next rise deals its Turn, because a finished strand's Turn is always dealt: *Splitting Stroke*, every second swing heavy, splitting the earth. By the time the Warden comes, her blade throws crescents of light and the ground breaks wherever she turns. At first light the lamps go out over the dawn card. It shows what the ember lit, what she keeps (her gear, the four levels the night taught) and one line telling her what to light for good. When she comes into the Waystation her points light for the first time: *Light my way* follows the dawn card's line, or she lights her own at the lamp-post. Her second and third nights start with those lamps burning, the Turns she liked come sooner, and from her second night a third skill rides with her (the slot opened at level 4).

**A veteran's tier-4 night.** She queues tier 4 at level 30 with six skills, eight points burning on each, a Turn among them. From the first second every other swing splits the ground, the bell drags the pack onto her shield, and every blow that lands on her answers in light. Her cards are the deep end, and each rise deals one of them for certain. Sunder's heavy line splits in three, a second Turn beside the one she lit for good. With Dawnpulse and Judgment Disc each burning a Turn, a Union lights: the disc carries the dawn and breaks into light wherever it strikes. Strands take their last lamps. By the boss most of her strands are full. Only the endless runs the ember out of lamps, and then the cards burn a skill hotter.

**Cut:**
- the day skill book (tomes, "every third level teaches", attribute needs);
- separate day and night slots;
- the random draft (new skills at night, passives, blessings, "+X%" rank cards; a rank comes back only as *Hotter*, when nothing is left to light);
- CLASSES §2.10's quarter sizes by night;
- the separate night kit.

**Kept:** a pick every time the ember rises, evolutions (now Turns), Unions, the Flare, the Lamps and Wicks, the table's tier pick, and the endless.

**Decided here:** a Union is one lamp two skills share, and both keep firing (Hades' duo blessings). Today's merge frees a slot that nothing can fill until dawn, so in a run it only loses a skill. Say if you want the merge back.

**Two questions for you (my pick first):**
1. **Where do skills come from, now that tomes go?** *Pick: each skill her calling may carry opens at a level (her type's first), and she chooses what to carry at a lamp-post.* Skills come on a schedule the story can teach, and loot stays gear: PoE's gem hunt is its least approachable part. Gear can still lend a skill. The alternatives are skills found as loot, as PoE's gems are, or every skill open from level 1.
2. **A newcomer's first nights carry two or three skills, not the old night's six.** *Pick: keep the slots (two at level 1, three at 4, six by 20).* One count everywhere, each new slot is a moment, and her Turns fill the screen. The alternative is three slots from level 1.

---

## 1. The rule, exactly

| | The world (town, the Verge, story zones by day) | A run (table nights, maps, story nights, the prologue's Ford) |
|---|---|---|
| Her build | whole: the board, carried skills at their rank, oil lamps, Hand, Flare, gear | the same, whole, from the first second |
| The ember | does not burn | burns: kills spill it, it rises (about 23 times in a tier-1 night of 10 minutes, measured on rc3), each rise deals three cards |
| Lamp sizes | in full | in full (CLASSES §2.10's quarter is struck) |
| At the end | nothing to take | first light puts out the ember's lamps; the ember sinks back to nothing |

- **A rise is not a level.** The night also teaches her levels, as today, and those stay. The ember's rises are only the night's cards.
- **Slots:** two at level 1 (her grip, Sunder for a sunderer or Oathblade for a bulwark, and one more skill open at 1), three at 4, four at 8, five at 14, six at 20 (CLASS_IDENTITY §3.7, already `SkillBook.SlotsAt`). One count everywhere; the night's six combat slots go.
- **Skills open by level** (question 1). Each skill record carries `opens` (the warden's in the JSON): Oathblade and Judgment Disc at 1, her type's signatures at 1-3, the other type's at 4-6. She carries any open skill her calling may carry, swapped at a lamp-post in town. Gear that grants a skill is unchanged.
- **Points:** each carried skill has its own points: one at level 1 and one more every third level (eight at 22: today's `SkillBook.Rank`). A lead-in costs 1, a Turn 2, a Union 2 (one from each of its skills). **A point burns once it is lit.** *Light my way* lights the points she leaves to it each time she comes into a town, and a lamp-post is where she lights or changes them herself; a new character's first run (the Ford) has nothing lit for good.
- **Rank:** a skill's rank is the points burning on its wick, oil and ember together. Each rank is its growth (+16% damage for most skills, `growth` in skills.json), shown as the skill's hit on every card and in its sum (`WickBook.Sum`). With no point burning a skill is rank 0, its first hit. Out of a run rank is at most 8 (`Weapons.MaxRank`). In a run it reaches 13 from her lamps (nine lead-ins and two Turns), one more for each Union the skill shares, and *Hotter* adds up to ten a night across all her skills.
- **The Turn rule:** one Turn per skill out of a run. In a run a second Turn may burn **beside a Turn lit with oil**. Never a third.
- **Respec:** free at any lamp-post in a town, never mid-run (CLASS_IDENTITY §3.5 stands). *Light my way* lights unplanned points: the dawn card's lamp first, then the suggested strand, then the skill's next strand once that is full, so a player who never plans still has every point burning.

## 2. The offer (each time the ember rises)

1. **Candidates:** for every carried skill, the first dark lamp of each strand whose parent burns; a Turn only if the Turn rule allows it; every Union whose two skills each burn a Turn.
2. **One card is always dealt** when anything is ready: the ready Turn or Union on the skill that has dealt the most damage tonight (ties: the one ready longest, then the skill carried first). A Turn is ready when its three lead-ins burn; a Union when both its skills burn a Turn. The other ready ones are drawn at ×6. (Today's draft deals one weapon's evolutions at a time, and a Union only when no evolution is ready.)
3. **The rest, drawn by weight:** ×3 a lamp that continues a strand already burning (oil or ember), ×1.5 *Light my way*'s suggested strand, ×1 any other, ×6 a ready Turn or Union not dealt; a card just shown ×0.15 (a reroll looks again). Weights multiply: the next lamp on the suggested strand, already burning, is ×4.5.
4. **Spread:** at most two cards from one skill, of three or four, while two or more skills have candidates.
5. **Never:** a burning lamp, a lamp whose parent is dark, a Turn the rule forbids, a banished lamp. A banish closes that strand for the night, and the card says so.
6. **Count:** three, a fourth with luck (today's `LevelUp.Count`). Skip, reroll and banish stay. With fewer candidates than cards, the surplus fills the rest.
7. **Nothing left to light:** the ember's surplus, three cards: *Hotter* (the skill that has dealt the most tonight burns one rank hotter until first light, its hit shown rising; ten a night in all; this is the endless's honing), *Banked* (a third of a Flare), *A draught* (mend 30%). A newcomer's two skills hold 20 lamps in a run (nine lead-ins and a Turn each), so a night of more rises ends on the surplus: the build lead checks the Ford's rise count against it.

**The card:** the lamp's name, the skill's glyph, its strand's pips (which lamp of four), the one line, and the skill's hit before and after, the lamp's own change counted: "41 → 45 (rank 4 → 5)", a Turn "41 → 49"; a cost lamp's can fall (*Hot Iron* "41 → 38"), and a hit that splits shows its parts (*Threefold* "41 → 3 × 14"). A Turn's card is drawn larger, and one that takes over a lead-in says so ("takes Third Blow's place"; the lead-in keeps its rank). A second Turn's card says why it may burn ("beside Splitting Stroke, lit for good"). A Union shows both glyphs. The line's keywords (heavy, sear, bleed, barrier, Stone, the wall answers, champion, lesser things, daylight and the rest) are marked, and holding the card reads each in one line (the JSON's `keywords`). On the wick panel, a dark Turn on a skill that already burns one reads "one Turn on this skill; a second only in a run, beside one lit for good".

**Which lamp wins.** On one skill, a Turn's rule wins over a lead-in's on the same thing (a wait, a timer, its targets), and slows and speeds multiply. The card names what it sets aside, as it says "takes Third Blow's place": *Shield of Morning* sets aside *Slow to Anger*'s wait, *Circle of Dawn* the timer that *Keep Time* and *Burnt Offering* slow, and *Open Rebuke* the targets *Dazed* drops. A lead-in offered while that Turn burns says so ("Shield of Morning sets this wait aside"). Two Turns on one skill both hold, and counts multiply: *Aegis Wheel* beside *Threefold* throws six small discs.

## 3. What dawn takes, and what the dawn card remembers

- **First light takes:** every lamp the ember lit and the ranks they brought, and the ember sinks back to nothing. **On a loss** it also takes the run's loot (today's rule) and the time (story nights wake her in town).
- **Never:** oil lamps, the board, her skills, her level and the levels the night taught, her gear, gold already banked, traits.
- **The card** (H8's `DawnCard`, re-worded by the build lead when the rule lands; not touched here): the ember's lamps by name (Turns first, then "and N more"); "You keep": your lamps, your gear, your gold, the levels the night taught; and **one memory line**, the first that applies:
  1. a lamp lit three or more runs running: *"You lit Splitting Stroke three times running."*;
  2. else the Turn on the skill that dealt the most damage: *"Splitting Stroke did most of your killing tonight."*;
  3. else the first lamp she lit.
- **The price line** follows the memory line. The price is the lamp's cost plus the dark lamps under it (its strand's lead-ins not yet lit for good). If the skill has that many points in all (respec is free, so spent points count): *"Light it for good at the lamp-post: 2 points."* If it hasn't, the line names the first lamp of that strand she can light now: *"Start it: light Third Blow for good, 1 point."*
- **A second Turn and a Union.** A second Turn's line reads *"Light it for good in Splitting Stroke's place: 2 points. Splitting Stroke can still burn beside it in a run."* A Union costs 1 point on each skill, plus, on a skill with no Turn lit for good, that Turn's price; the line names that Turn first. Of several lamps lit three runs running, a Turn or Union comes first, then the one on the skill that dealt the most damage.
- **The save keeps** each lamp's count of runs lit in a row and the last run's number. The lamp-post glows that lamp until she lights it or dismisses it.

## 4. The data model (`godot/data/content/skill_lamps.json`)

**One record per lamp, for every skill.** It replaces `wicks.json` (day strands with shared lead-ins), the evolutions and catalysts in `skills.json` (night) and the unions' merge. The game does not read it yet; the build lead wires it. Fields:
- `id` (`<skill>.<strand>.<n>`), `skill`, `strand`, `n` (1-3 lead-ins, 4 the Turn), `parent` (the lamp before; a Union lists two Turns' strands);
- `name`, `rule` (the one line, numbers in it);
- `kind`: `element`, `shape`, `trigger`, `cost` (a cost and its pay-off) or `calling` (the calling's mechanic deepened);
- `turn`, `cost`, `effects` (engine keys);
- `engine`: `built` (the sim does it today), `rule` (a named rule exists), `new` (to build);
- `from` (what it replaces: an evolution, a v1 skill lamp, a built Turn);
- `supersedes` (the lead-ins whose effect a Turn takes over; they keep their rank);
- `draft: true` where the name waits for the story writer.

Each skill's header lists its strands, the suggested strand (*Light my way*) and `opens`. The top-level `keywords` holds the card's one-line explanations. `tools/classes/skill_lamps_check.py` checks the file: parents, Turns, costs, kinds, unique names, no bare-percent line, no barrier or mend under 2% of health an event unless the line holds a cap of 2% or more, Stones a line can reach, and the keywords.

## 5. The migration list (for the build lead)

1. **The wicks' lead-ins are bare percents: about 75% of today's wick lamps.** All nine per wick come from `wicks.json`'s three shared templates ("+10% damage", "+10% area", "8% shorter cooldown", "15% chance to {status}", "+10% damage to {statused} enemies"). They retire. `skill_lamps.json` replaces `wicks.json`; the built Turns' engine keys carry over.
2. **The night draft's full pool is what is cut** (`LevelUp.Draft`):
   - new skills at night and the night's six combat slots;
   - rank cards ("+16% damage");
   - the passives and their catalysts;
   - great and milestone blessings;
   - `LevelUp.Respite` (Second Wind 35%, Scavenged Coin): §2's surplus replaces it;
   - the Flare's four blessings (`bright_hour`, `ember_answers_twice`, `short_wick`, `called_shot`): the Flare lead folds them into Flare lamps or retires them;
   - **chests** (`ChestItemKind` Evolution, Rank and Passive): a chest lights the top 1, 3 or 5 of tonight's candidates by weight, a ready Turn first.

   §2's offer replaces it. Kept: `Count`, skip, reroll, banish.
3. **Evolutions become Turns.** Each evolution becomes a Turn on its skill's wick (the warden's are in the JSON, named in `from`). `Battle.Evolve` becomes lighting a Turn. Catalysts go, and with them gear's `stand:` keys (gear that stands in for a catalyst, `kit.Stands` in `Character.cs`; the loot lead).
4. **Unions become shared lamps.** Each needs a Turn burning on both skills; both keep firing; the union weapon's behavior becomes the lamp's effect. The merge and the freed slot go.
5. **`SkillBook` retired.**
   - `Learn`, `Tome`, `Calling()`, `Meets`, `Attribute`, `Need`, `NightRank`, `Attuned` and `Familiar` go.
   - `SlotsAt` stays as the one slot count; `Rank` stays as points by level.
   - `opens` replaces learning.
   - `Weapons.MaxRank` (8) caps `SkillBook.Rank` and drives the "at rank 8 it evolves" hint. It stays the day's cap; a run's is §1's (13, plus Unions and *Hotter*); the hint goes.
   - Tomes leave the loot tables, shops and quest rewards (the loot lead).
   - Saves: known skills open, slotted skills carried, discovered dropped.
6. **`WickBook`:** from "a plan, and rank lights its first r" to a lit set: oil lamps (paid with points at a lamp-post) and ember lamps (tonight). `Battle.Relight` goes. Rank = points burning. The `night` flag on `WickBook.Sum` and the `Content.Wicks` loader go; `Sum` reads the lit set.
7. **`Journey.StartBattle` and `Journey.Douse`:**
   - A run starts with the whole build: `Character.Kit(ch)` as by day, sizes in full.
   - `EmberOn` is set only in a run. `b.Night` becomes mood only.
   - `Douse` puts out the ember's lamps and sinks the ember, and leaves the carried skills as they are; it no longer rebuilds the kit from gear.
   - `kit.StartLevels` (the `spark` trait, the `ember_start` tag) stays as rises at minute 0, each dealing its offer.
   - The two gear kits (`Kits`, CRAFTING_DESIGN 20.2) fold into one, and coals and Marks work in every run (the crafting lead).
8. **CLASSES §2.10 struck.** `LampLoadout.Night`, `Lamps.NightSize`, `NightCut`, `GiftSize`, `ReflexSize` and the smalls' road lean go. Every lamp works in full everywhere, and the board's smalls give their own numbers. `LampBook.Switch` is gated on "not `TimeOfDay.Night`" (LAMPS_V2_RULES): the gate becomes "not in a run".
9. **The Lamps screen and wick panel** (UI lead):
   - an ember lamp is drawn as an ember (ember color, a slow flicker), an oil lamp burns steady, a dark lamp is dark;
   - no points are shown or spent during a run, and an ember lamp reads "until first light";
   - points are lit only at a lamp-post, and the lamp-post glows the dawn's suggestion;
   - a skill's rank reads as the points burning, and its hit as a number;
   - the card's keywords and its Turn lines (§2).
10. **The dawn card** (`DawnCard.Build`): H8's words are re-worded to §3 ("The ember takes" becomes the ember's lamps by name), plus the memory line and the price line. `CharacterData` gains each lamp's runs lit in a row and the last run.
11. **The tutorial** (`docs/story/TUTORIAL_COPY.md`; the story lead owns the words):
    - F4 "A skill" becomes one card explained at the first rise: a freeze, the arrow on the card's skill glyph and strand pips. *"The ember lights a lamp on one of your skills. Choose one. It burns until first light."*
    - F5 ("First light takes it back") is cut: she starts with her skills, and nothing she carries is lent.
    - F3 (the great blessing) is cut.
    - F12's middle line becomes *"The ember's lamps went out at first light. Light the ones you liked for good at a lamp-post."*
    - New, at her first lamp-post: *"Each skill has its own points. A point lights a lamp for good; a Turn takes two. Change them free here. Leave them, and Light my way lights them for you."*
    - F9 ("Three lamps guard the Warden"): the boss's lamps share the word with her skill lamps in the same prologue. The story lead checks the two can't be confused, and renames the boss's if they can.
12. **The harness:**
    - The bots play a full build from minute 0 (`--onebuild`, §6).
    - One balance band for all replaces "a full board at night within ×1.25 of an empty one" and the ×1.25 night lean. At each tier, for every level band that plays it, the human wins 78-85%, deft 95%+, standing falls 80%+ and idler 70%+.
13. **Maps and story nights:**
    - The ember burns in maps too.
    - Story nights stop "starting with nothing"; their ember floors and great blessings go, and their stages are re-measured.
14. **Her swings land on the clip's contact frame** (A1's routing, GATE M1). Today a swing's damage lands on the sim's own timer, and no C# reads the clip's contact frame. In the Warden slice a melee blow (Sunder, Oathblade, Groundbreaker's heave) deals its damage on its clip's contact frame, so the lamps that count swings and heavy blows (*Third Blow*, *Splitting Stroke*, *Crescent*) land on the frame the player sees. The combat lead, with A1's Stage B clips.
15. **Docs:** CLASSES §2.10, CLASS_IDENTITY §3.2 "By night" and §3.3 "Points" are marked superseded by this page.
16. **American spelling** (the owner, 20 October): "Judgement" becomes "Judgment" in the display names: skills.json's Judgement Disc, the union Dawn's Judgement, and every text that names them. The ids stay.

## 6. The harness note (H6's 45-60 s rule, on a full build)

Numbers only. No retuning here; that is the build lead's job.

**The setup.** The harness switch `--onebuild` lives under godot/balance only (commit cbde3e259; without the flag a run writes the same lines as before it, checked by sorted-line compare on arena, types, pair and story batches). It approximates the rule until the offer exists:
- She starts with her slots' worth of her calling's skills at day rank, wicks lit by *Light my way*, and the board lit for her level.
- Lamp sizes are in full by night.
- The draft can only rank or hone what she carries. A rank still lights the next wick lamp, so the night still climbs.

It is the Pack's board, tier 1 (a table night of 10 minutes). The numbers are won/fell %, across the four callings; "standing falls at" is the standing bot's median time to fall, and "longest quiet" the human's median longest stretch, from 0:45 to the boss, without a mark laid on her.

| Run | Seeds | standing | standing falls at | idler | kiter | human (lowest life) | longest quiet | careless | deft | human's boss s |
|---|---|---|---|---|---|---|---|---|---|---|
| R0 rc3 at HEAD, level 1, the old draft | 16 | 0/100 | 74 s | 28/72 | 9/91 | 84/16 (0.27) | 23 s | 67/33 | 98/2 | 138 |
| R1 one build, level 5 (3 skills, rank 2) | 32 | 0/100 | 97 s | 3/97 | 4/96 | **61/39** (0.22) | 23 s | 39/61 | **76/24** | 230 |
| R2 one build, level 10 (4 skills, rank 4) | 16 | 0/100 | 113 s | **61/39** | 27/73 | **100/0** (0.35) | 24 s | 98/2 | 100/0 | 142 |
| R3 one build, level 30, full board, tier 1 | 16 | 5/95 | 165 s | | | 100/0 (0.54) | 28 s | | 100/0 | 58 |
| R3 the same, **tier 4** | 16 | **23/77** | 131 s | | | **75/25** (0.41) | 24 s | | **83/17** | 65 |

Read against H6's gate (something to dodge every 45-60 s; standing falls 80%+, idler 70%+, human wins 78-85%, deft 95%+):
- **The 45-60 s rule holds on a full build.** The human's longest stretch without a mark laid on her is 23-28 s at every level (rc3: 23 s), inside 45-60 s. Standing still falls on every tier-1 night at every level, 95% even at level 30 with the full board, though later as her build grows: a median of 74 s on rc3, 97 s at level 5, 113 s at level 10 and 165 s at level 30.
- **The bands don't hold yet**, and they miss in both directions:
  - At level 5 the first table night is too hard: human 61%, deft 76%. The reaver's human wins only 12%, against the warden's 91%, the stalker's 75% and the arcanist's 66%.
  - At level 10 it is too easy: the human wins every night, and the idler wins 61%.
  - A veteran at tier 4 sits under the band (human 75%, deft 83%), with standing just under the gate (falls 77%).
  - R3's tier 1 (human 100%) is not a level-30 player's tier: it is there for the standing check, and the band applies to the level bands that play a tier.
  - The old night evened out every level by drafting from nothing. One build has to be tuned per level band and tier, which is §5 item 12's single balance band.
- **What it doesn't measure:**
  - the real offer (a choice of lamp, the new lead-ins, the one card always dealt, second Turns, Unions);
  - chests, which still open by the old rules;
  - the Turns that answer blows (*Shield of Morning*, *Circle of Dawn*, *The Answer*, *Stone Bell*): the standing bot is re-run with each lit, and with all four together, before the slice ships.
  - The human's ember still reaches 25 by the end of a tier-1 night, so about 23-25 rises a night stands.
- **The data:** scratch `classes_c2\h\r0-r3.jsonl` (backed up to `survivorsunchained_inputs\scratch_classes_c2\`), `run.sh`; `python tools/balance/danger.py <file> --by tier` or `--by calling`.

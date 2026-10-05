# Story nights and the day's clock

A proposal for the owner, by the experience director. Nothing here is built yet. Building starts
when the owner approves (section 3 lists the choices that are the owner's). The bosses' moves are
the combat lead's: `docs/design/STORY_BOSSES.md` (on `worktree-agent-a708da2c97bf85c95`), which
holds each fight's beats, bosses and numbers.

The owner, 4 October:
- "story nights are what? arenas that happen because of the story? if were going to do that they
  should be much more specialized and fun - smaller arena - and they don't need endless - they have
  proper arpg end bosses right?"
- "time passing should probably happen because some users may not figure out the rest mechanic and
  anotehr way to prompt advancement is worth it, and also just natural."


## The owner's decisions (4 October 2026)

The design is approved, with these decisions. They overrule the doc below where it differs.

1. **Losing a story fight wakes her in town** (Chid carries her home), and time has passed: the night is lost and she wakes the next morning. "We can't die" is part of the game, but losing costs her time ("having to die for a time"), and gives her a day to get new gear and prepare before she tries again. The fight waits for another night. **Getting up (owner, revised): once, and only early.** In Act 1's story fights she may rise once, at the start of the stage she fell in (or the boss's opening). From Act 2 on there's no rising at all, unless she carries the skill that grants it. The rise is a skill or spell, not a hidden trait (owner: "the trait can just be a skill/spell right - can get it in arenas or learn it for story etc"). In arenas and maps it's a rare draft pick, so it costs her another power that run. For story fights it's learned in town and taken in, so it costs one of the slots she carries. "Get up twice is too generous ... as we move on you shouldn't get to rise and keep fighting unless you have a trait for it. thats a balancing nightmare". The same rule applies to the atlas maps: no falls to spare without the trait.
2. **Redcowl gets a spare-or-kill choice** at his knee, as Greymuzzle does: "Spare him" or "Finish it". The story bible already has both branches (he lives and returns in Act 2, or dies and Rav speaks his name). C11's last words play only if he dies; the story lead writes the spared ending.
3. **Day length:** 12 minutes of free play (the recommendation).
4. **Time passes outside fights and their stages.** A night left alone passes (the recommendation).
5. **Several fights in one night are allowed** if she goes straight from one to the next. Because the clock runs outside fights, that takes direct intent.

## 1. Story fights: their own places, their own bosses

**Today.** A story fight (`Verge.MakeStoryFights`) is the round 168 m arena of the table's nights,
told quicker. It runs 20 minutes of horde (heralds, turns, a breather) and then the story's foe for
about 80 seconds. No endless comes after the boss. It is a table night with a name. The fight the
story spent a chapter earning lasts less than a minute and a half.

**Decision.** A story fight is a short night in a place made for it. It has a way in, the place's
own set piece and a proper boss. It keeps the ember: it is still a night, so she starts with
nothing, burns and drafts. It drops the clock, the climbing horde, the heralds, the turns and the
endless hour.

### The shape: 10 to 14 minutes, 12 at par on a first try

| Beat | Length | What happens |
|---|---|---|
| The pull | seconds | The ember takes her there (as now). One line from the story names the place, never a clock. |
| The way in | 6–9 min in all | Three or four authored beats of 1.5–3 min, each a wave with a goal or a small set piece. A beat ends when its goal is met, never on a timer. One story sight or line comes between beats. |
| The place's set piece | inside the way in | The thing only this place has, played: hold an edge, break a thing, open a door. It ends with the boss's sign: a sound, then a light at the edge it will come from. |
| The boss | 3–4 min | A proper ARPG boss on its own ground, which opens at the end. It has three phases, and each one changes the space. Telegraphs are on the ground. Adds are the boss's own, each with a job, and the horde is off or a trickle. One weakness is the bane the day taught (Maeca's fed fires, Chid's standard, Grimtunnel's own lamp). The cinematic plays in and out (C10–C13). |
| The end | — | No endless and no way out. The boss's end is the fight's end: the story's last line, then back where she was pulled from, into the same night (story's rule: the line never claims the dawn, and the town talks about it that night). |

- **The build.** Embers are paid about 2.5 times faster (combat's number), so she meets the boss
  with about what a table night has at minute 20. That build is the boss's yardstick: about 3–4
  minutes at par, against the table rulers' 60–120 s.
  - The waves are finite and creature levels are fixed per beat. So the build at the boss is set by
    the content, a slow beat is no harder, and nothing is farmed.
  - A great blessing comes as the night opens, and another as the boss's ground opens, after its
    arrival.
- **The tension.** The way in should feel dangerous without killing her. The aim is that 20–35% of
    runs dip under half health somewhere on the way in, with falls in 5% of beats or fewer (combat's
    harness measures both). The real danger is at the boss: it fells her on its first life in about
    a third of tries.
- **The place.** About 50–60 m across, hand-shaped, with a separate boss ground. Today's arena is
  168 m across. From the camera's 22 m, a 50–60 m place is about a screen and a half: close enough
  that the place itself is the fight.
- **Pay.** XP and crafting are paid for the fight's own length, not against a 30-minute clock
  (`Arenas.XpFor` scales to 30 today).
- **Why this length.** It is long enough for a build to be earned and tested, and short enough to
  replay a fall without dread. It is also a third shorter than today's 20 minutes, so the story
  never sits behind long arenas.

### Falling and getting up

- **A fall in a beat:** she gets up at that beat's start, with the build and health she brought
  into it.
- **A fall at the boss:** she gets up as its ground opens, at full health, in phase one, with her
  build. The ground is as it opened. The arrival's cinematic does not play again; a two-second
  re-entry (his howl, his laugh, his "Nondum") does instead.
- **Two rises a night** (open choice 1). The third fall is the loss the story already writes: each
  fight's `OnLose`, and its lost line as she comes to in the same night. The fight then waits at its
  place and at the table for another night, as now. "Let the night go" is on the fall screen from
  the first fall.
- **A rise is quick:** a three-second fade with no screens. Story's line is "You get up." (the
  prologue's words), then the second time "You get up. It takes less than it did."
- **What to build:** combat snapshots the battle at each beat's start and at the boss's opening
  (`STORY_BOSSES.md` §5.1). The run restores it, and the beat's waves begin again.
- **The odds:** first-try wins with the two rises at 90% or more for a planned draft, and 70–80% for
  a careless one (combat's §0.6).

### What each fight needs

- **Arena art** (`a26767f7f9955cb56`): one bespoke place per fight, built from its people's kit (the
  Hollow, Ruts, Dig and Barrow grounds). Each has:
  - the way in as two to four linked spaces;
  - a boss ground with the place's landmark at the heart of the fight;
  - each phase's change as a state of the place (something falls, floods, burns or opens).

  The fight must read at 30 m by night.
  - **Agreed with arena art:** `ArenaGen` assumes a circle beyond `Closed`, so the builder will take
    an outline (a union of shapes per space). `Inside` becomes a signed distance from that outline,
    and the rim is traced from its contours, so a place can have several. The grid shrinks to about
    90 m, which makes the paint about three times finer for the closer fight. That is a few days in
    `ArenaGen` and `Ground.cs`.
  - Paint and props can change live. Walkable ground and colliders that change mid-fight (a boss
    ground opening, a floor falling) are the simulation's part, with combat.
- **Combat** (`a708da2c97bf85c95`, in `STORY_BOSSES.md`): each boss's phases, moves, adds and
  space mechanics; the beats' waves and goals; the ember's rate; the snapshots; health measured
  against the build above. **Agreed with combat:** this section's numbers are its frame (10–14
  minutes, beats that end on their goals, a 3–4 minute boss, embers ×2.5, 50–60 m). Redcowl gets
  his own script instead of the Red Hand's.
- **Story** (`a73ca9d35d0c487a9`): the pull's line, a sight or line between beats, the boss's own
  words (wordless, orders, Snib's comments), the rise's line, and the ends (C10–C13 and the
  existing won and lost lines). **Agreed with story:** the rise, dusk and night-alone lines are
  drafted (quoted below). The pull's line and the sights between beats come once
  `STORY_BOSSES.md` fixes each fight's beats. The bible's share number follows the owner's choice of
  day length.
- **Experience** (mine): the night's shape and staging, the fall and rise flow, the clock (section
  2), and judging each fight in real runs at full resolution.
- **Order:** build the Hollow by Night first, as the template. Its kit is among arena art's
  furthest along (stream, mist, moss and roots), and its den, next on arena art's list anyway, can
  be built as the boss ground from the start. Its ending is the richest (let go or killed), and the wolves are most routes' first
  trouble. The other three follow once the Hollow has been judged.

### Every story fight, and its form

Act 1 has four story fights, all built today as 20-minute nights. The details of each boss are
combat's to write; the places are arena art's.

| Fight (`id`) | Foe | The way in | The place's set piece | The boss's ground and its end |
|---|---|---|---|---|
| The Hollow by Night (`hollow_by_night`) | Greymuzzle, the Pack | Down the clough along the sick stream: wolves in twos and threes, and the blighted ones slow. The Pack is sick, not wicked: no human bones. | The den's mouth. The sick lie there, and the Pack herds her away from it. | The den's floor. He hunts, howls the Pack into a ring (fire breaks it), then fights alone on his feet. Where the facts hold, letting him go is her choice at his side ("Let him go" or "Finish it"; story to confirm). Otherwise he dies (C10). |
| Raid on the Roost (`roost_raid`) | Redcowl, the Kerchiefs | Up the ruts through the camp's pickets in the dark. Torches and bells call each picket's wave. | The levy marching in step through the camp's yard. The six B.E. crates are an optional shortcut beside it, only while they are still there (`be.crates` unset or `redcowl`). They go up by a prompt, *Fire the crates*, never by a fire build's stray shot, and that sets `be.crates` to `burned`. With no crates, the beat is the levy alone. | His own fire, with his children asleep behind the line. Today he runs the Red Hand's script; he needs his own. He kneels, laughs and gives his last words (C11). |
| The Dig Boils Over (`dig_boils`) | Grimtunnel, the Lamplings | Lamplings pour up out of the pit. Hold the edge by the headframe, then the rails. | The pump: running, it is blown in the fight (`dig.pump` becomes `blown`, as now). | The pit's lip, with the heart's light in his cracks and Snib's comments. He goes back down the hole, delighted, and never dies (C12). |
| Behind the Sealed Door (`vault_opened`) | The Barrow Lord, the Risen | The sigil is set and the door wakes violet. Inside is the Legion's hall at the head of the stair, and the dead come up it in ranks. She never goes down it: going down is Act 3, and in C13 Jessop stands far below and she must not pass him. The hall's roof has fallen in, so it is open to the moon with its wall tops standing. That keeps the arena's camera, with no ceiling to cut away. | The century's hall: the shield wall, and the standard (Chid's bane). | The head of the stair, with his one-word orders. He is laid down, and holy does it twice as fast. His hand at the gate (*Redi*) sends her home (C13). |

Later story fights are designed in `docs/bosses/` but not built: the Thing in the Barn, the Warden
of the Kiln Ford, the Silver Penitent (Silverstair and the war at the gate), the Centurion of the
Stair, and Grimtunnel at the bottom. Each is built in this shape from the start.

**Unchanged:**
- the day bosses (the Slurry Engine, Keegan at first light, the Keeper), which are already this
  kind of fight, by day and without ember;
- the prologue's Ford-Warden;
- the table's nights and the Verge's scars, which stay 30 minutes and endless;
- the atlas's maps, whose length waits on the owner's answer.

## 2. A natural day's clock

**Today.** The day only changes by "wait for nightfall" (`GameMenus.Rest`, `Journey.Nightfall`) or
by sleeping at the inn (`Journey.Sleep`). A player who never finds the inn's rest stays in one day.

**Decision.** Time moves on its own: dawn, day, dusk, night. Night calls the night's fight.

- **The day is 12 minutes of free play:** dawn 1, day 9, dusk 2.
  - **Why 12:** Act 1's days carry about 6–12 minutes of talk and cinematics each (45–85 minutes
    of dialogue over about seven days), and the clock stops for those. So 12 free minutes make the
    story's day of about 20 minutes (`STORY_BIBLE.md` §2).
  - It fits a trip into the Verge and back, which is about 7 minutes a day across Act 1.
  - A player who never finds the inn still sees a night within a quarter of an hour.
- **It stops** in conversations, cinematics, every page and menu (pack, journal, map, shop, the
  table, rest), the draft and the chest, the pause, and travel and loads. It runs while she is free
  in the town or the Verge, fights by day included. It never runs in an arena, which is its own
  night, or in the prologue. On day 1 it starts when the arrival ends: when the first of the two
  troubles (`beasts` or `caravan`) reaches her journal. Until then she has nowhere to be.
- **Dusk is the warning.** The lamps are lit and the town thins to its dusk folk. The gate guard
  gives the town's evening call ("Lamps are lit. Stay where they reach."), then one line names the
  night's fight (story's drafts):
  - Hollow: "Out past the lamps, the Pack has stopped howling."
  - Roost: "Up the Old Road, the Kerchiefs' fires are lit all along the ravine."
  - Dig: "On the hill over the Dig, the lamps are all moving the same way."
  - Vault: "Out in the Verge, the sealed door has woken. Its light is violet."
  - Nothing open: "Out on the Verge, the ember is coming up."
- **Nightfall calls the night's fight.**
  - The night's fight is the open story fight, or else the Wayfinder's table and the Verge's scars.
  - Its mark lights on the map, and a beam stands at its place.
  - "Answer the night" (one held key, from anywhere in the town or the Verge) lets the ember pull
    her straight there. A card names the fight first and lists any others open that night.
- **Not ready?** Nothing forces a fight. The night holds for 6 minutes of free play: shop, talk to
  the night's folk, or go to Pell's door. At 3 minutes, one nudge ("Half the night is gone"). At 6,
  the night passes on its own (open choice 3): a fade, and story's line, "You see the night out on
  your feet. At first light the warmth comes back into your hands." The world moves on a day, as when she sleeps, but without the inn's rest. A story fight that wasn't
  fought waits; nothing is lost but the night.
- **One fight a night** (open choice 4). After any night's fight she comes back into the same
  night, as now, and the town talks about it that night. The night's other fights close. The
  night's clock resumes with at least 3 minutes left, so there is time to hear the town. Then the
  inn's bed, or the night passing on its own, moves her on.
- **The skips stay.**
  - The inn's sleep goes to the next morning, healed, with the overnight talk, from any hour.
  - "Wait for nightfall" jumps to the night from day or dusk.
  - Both are now shortcuts, not the only way forward.
- **The turns of the day** cross-fade the light over about a minute. The town's lamp shadows
  already run only at dusk and by night, so a moving clock costs nothing there by day. Performance
  checks the cost of the blend's frames.
- **The 40% and the night lengths.**
  - In the story bible's own arithmetic, days count as story and nights as arena. Act 1 today is
    seven 20-minute days, three or four 20-minute story nights and three or four 30-minute table
    nights: about 44% days.
  - With 12-minute story fights and one fight a night, an eight-day Act 1 (four story fights, four
    table nights) is about 49% days. Shorter story fights push the share up, and this is that
    cost, stated plainly.
  - The lever is the day's length (choice 2): an 8-minute day brings Act 1 to about 43%. The share
    falls in Acts 2 and 3 either way.
  - The table's nights stay at 30 minutes. The atlas's maps wait on the owner.
    `WorldState.TimeIn` measures it in playtests.

## 3. For the owner: four choices

1. **Getting up after a fall in a story fight.** I recommend two rises a night, then the story's
   own loss, and the fight waits for another night. This keeps the stakes, and the losses the story
   wrote. The alternative is unlimited rises from the last checkpoint.
2. **The day's length.** I recommend 12 minutes of free play, which makes about 20 with the talk;
   Act 1 is then about half days. The alternatives are 8 (brisker; back to about 43% days) or 16
   (more room to wander; about 53%).
3. **A night left alone.** I recommend that it passes on its own after 6 minutes, so a lost player
   always moves on. The alternative is that the night holds until she fights or sleeps.
4. **How many fights a night.** I recommend one. She comes back into the night to hear the town,
   and then the bed or the night's own end moves her on, so the cycle stays clean: a day, then one
   night's fight. The alternative is today's rule, where she can take another scar the same night.

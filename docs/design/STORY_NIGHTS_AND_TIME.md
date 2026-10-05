# Story nights and the day's clock

A proposal for the owner, by the experience director. Nothing here is built yet. Building starts
when the owner approves (section 3 lists the choices that are the owner's). The bosses' moves are
the combat lead's: `docs/design/STORY_BOSSES.md`.

The owner, 4 October:
- "story nights are what? arenas that happen because of the story? if were going to do that they
  should be much more specialized and fun - smaller arena - and they don't need endless - they have
  proper arpg end bosses right?"
- "time passing should probably happen because some users may not figure out the rest mechanic and
  anotehr way to prompt advancement is worth it, and also just natural."

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
| The dawn | — | No endless and no way out. The boss's end is the night's end: the story's last line, then back where she was pulled from, at dawn. |

- **The build.** Embers are paid about 2.5 times faster (combat's number), so she meets the boss
  with about what a table night has at minute 20. That build is the boss's yardstick: about 3–4
  minutes at par, against the table rulers' 60–120 s.
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
  build.
- **Two rises a night** (open choice 1). The third fall is the loss the story already writes (each
  fight's `OnLose` and its lost line). Dawn comes, and the fight waits at its place and at the table
  for another night, as now. "Let the night go" is on the fall screen from the first fall.
- **A rise is quick:** a three-second fade with no screens. The line is the story's (the ember
  gets her up).
- **What to build:** combat snapshots the battle at each beat's start and at the boss's opening.
  The run restores it.

### What each fight needs

- **Arena art** (`a26767f7f9955cb56`): one bespoke place per fight, built from its people's kit (the
  Hollow, Ruts, Dig and Barrow grounds). Each has:
  - the way in as two to four linked spaces;
  - a boss ground with the place's landmark at the heart of the fight;
  - each phase's change as a state of the place (something falls, floods, burns or opens).

  The fight must read at 30 m by night. `ArenaGen`'s places already shape any outline (`Closed`).
- **Combat** (`a708da2c97bf85c95`, in `STORY_BOSSES.md`): each boss's phases, moves, adds and
  space mechanics; the beats' waves and goals; the ember's rate; the snapshots; health measured
  against the build above.
- **Story** (`a73ca9d35d0c487a9`): the pull's line, a sight or line between beats, the boss's own
  words (wordless, orders, Snib's comments), the rise's line, and the ends (C10–C13 and the
  existing won and lost lines).
- **Experience** (mine): the night's shape and staging, the fall and rise flow, the clock (section
  2), and judging each fight in real runs at full resolution.
- **Order:** build the Hollow by Night first, as the template. Its kit is arena art's furthest
  along, its ending is the richest (let go or killed), and the wolves are most routes' first
  trouble. The other three follow once the Hollow has been judged.

### Every story fight, and its form

Act 1 has four story fights, all built today as 20-minute nights. The details of each boss are
combat's to write; the places are arena art's.

| Fight (`id`) | Foe | The way in | The place's set piece | The boss's ground and its end |
|---|---|---|---|---|
| The Hollow by Night (`hollow_by_night`) | Greymuzzle, the Pack | Down the clough along the sick stream: wolves in twos and threes, and the blighted ones slow. The Pack is sick, not wicked: no human bones. | The den's mouth. The sick lie there, and the Pack herds her away from it. | The den's floor. He hunts, howls the Pack into a ring (fire breaks it), then fights alone on his feet. He is let go or he dies (C10). |
| Raid on the Roost (`roost_raid`) | Redcowl, the Kerchiefs | Up the ruts through the camp's pickets in the dark. Torches and bells call each picket's wave. | The yard and the six B.E. crates. Fire near them blows them, a choice made in play that sets `be.crates` to `burned`. | His own fire, with his children asleep behind the line. Today he runs the Red Hand's script; he needs his own. He kneels, laughs and gives his last words (C11). |
| The Dig Boils Over (`dig_boils`) | Grimtunnel, the Lamplings | Lamplings pour up out of the pit. Hold the edge by the headframe, then the rails. | The pump: running, it is blown in the fight (`dig.pump` becomes `blown`, as now). | The pit's lip, with the heart's light in his cracks and Snib's comments. He goes back down the hole, delighted, and never dies (C12). |
| Behind the Sealed Door (`vault_opened`) | The Barrow Lord, the Risen | The sigil is set and the door wakes violet. Down the stair, the Legion's dead come in ranks. | The century's hall: the shield wall, and the standard (Chid's bane). | The foot of the stair, with his one-word orders. He is laid down, and holy does it twice as fast. His hand at the gate sends her home (C13). |

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
  night, or in the prologue. On day 1 it waits until the arrival's introductions are done (story
  names the step).
- **Dusk is the warning.** The lamps are lit and the town thins to its dusk folk. One line names
  what the night holds ("The Hollow is waiting"; the words and any sound are story's).
- **Nightfall calls the night's fight.**
  - The night's fight is the open story fight, or else the Wayfinder's table and the Verge's scars.
  - Its mark lights on the map, and a beam stands at its place.
  - "Answer the night" (one held key, from anywhere in the town or the Verge) lets the ember pull
    her straight there. A card names the fight first and lists any others open that night.
- **Not ready?** Nothing forces a fight. The night holds for 6 minutes of free play: shop, talk to
  the night's folk, or go to Pell's door. At 3 minutes, one nudge ("Half the night is gone"). At 6,
  the night passes on its own (open choice 3): a fade, and "You saw the night out on your feet". The
  world moves on a day, as when she sleeps, but without the inn's rest. A story fight that wasn't
  fought waits; nothing is lost but the night.
- **One fight a night** (open choice 4): every arena ends at dawn (`STORY_BIBLE.md` "The nights").
  After any night's fight she comes back at dawn of the next day. The overnight news (who heard
  what) follows the night's result.
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
4. **How many fights a night.** I recommend one: the arena's end is the dawn, and the cycle stays
   clean. The alternative is today's rule, where she comes back to the same night and can take
   another scar.

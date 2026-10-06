p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\docs\SKILLS_DESIGN.md'
s = open(p, encoding='utf-8').read()

def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b, 1)

rep('''  stood in a boss's combo and fell, making fragile ranged builds look worse
  than they are), use the art on a crowd, drink when low. **Deft** hands
  (`--bot deft`, from the lab) also step off a lunge's line, out from under
  a lobbed pot and off burning ground, and close on throwers.''',
'''  stood in a boss's combo and fell, making fragile ranged builds look worse
  than they are), use the art on a crowd, drink when low. **Deft** hands
  (`--bot deft`, from the lab) also step off a lunge's line, out from under
  a lobbed pot and off burning ground, and close on throwers. **Both read the
  bosses** (`Play/Bosses/BossSense.cs`, section 16.2); `--bossread 0` gives
  the hands as they were.''')

rep('''---

## 16. Before and after''', '''---

## 16. Enemies, bosses and the long night

The night's other half: what the survivor fights. The bestiary and the bosses
were studied by two cloud sessions (`docs/bestiary/`, `docs/bosses/`); this
section is what was built from them, and the decisions they left open.

### 16.1 The bosses

**The contract** (`Play/Bosses/ArenaBoss.cs`): three phases, each a gate that
ends at its health mark or a 60 s ceiling and never before its floor (15, 20,
15 s); damage past a mark is the **Break**, shown as one number as the phase
turns; a soft enrage at three minutes (moves a quarter quicker, the horde back
to full) and a hard one at five (its signature on a loop); crowd control fills
a **stagger bar** instead of locking it; a **weakness** school breaks its
channel. Each boss asks one question in its own people's terms:

| Boss | Its question | Its tell of soul |
|---|---|---|
| The Pack-Mother (Greymuzzle in his Hollow) | She herds you: go through the wolves, never the gap | the moon-howl that fire breaks; the last of the Pack round you |
| The Barrow Lord | Walls of men: read the formation | orders in the old empire's tongue; he will not lie down until stood over |
| The Ganger (Grimtunnel on his own night) | The ground is the enemy | one lamp for three verbs (his three, and he goes back down the hole) |
| The Red Hand | What is your build without its best piece? | the Toll takes a weapon; the thief carries it; storm makes him drop it |

**On screen** (checked frame by frame with `--on boss`, and `--marks`, a
gallery of every telegraph round the survivor):

- Each boss wears its own body (`boss_pack`, `boss_dead`, `boss_lamplings`,
  `boss_kerchiefs`): its people's champion's, half again as big, named, so it
  glows; its flash under a build's hits softened so it stays itself.
- **The telegraph language**: amber for a blow (a disc that fills to its
  moment, a lane, a cone, a band whose inside is clear), violet hatching for
  ground that stays bad, pale blue dashes for ground to stand on, a grey hard
  edge for ground that will be solid. The move's name is said over the boss
  for as long as its mark stands; the BREAK is said alone, high and gold.
- The arrival: a sign two minutes out from its bearing, the camera turned to
  it, its weakness named, and **the people make way**: the crowd past the
  share it is held at falls back into the dark and is let go out of sight.
- The stagger bar has its own groove under the health from the first second.

**Health to the contract** (90–120 s at par, about 50 s at the least for an
absurd build, an enrage for a weak one), measured with deft hands at tiers
1–3 and the table's oaths: the Pack-Mother 69 → 84 s and the Red Hand 72 →
84 s (both then raised a further tenth), the Barrow Lord 80 → 86 s, the
Ganger 92 → 98 s. Health per boss: Pack-Mother `30 + 5t`, Barrow Lord
`13 + 2.2t`, the Ganger and Grimtunnel `18 + 3t`, the Red Hand `21 + 3.5t`,
times its people's champion's.

### Why this is the answer

The cloud probe found bosses living 16–20 s and Grimtunnel kited forever;
health alone drags slow builds past two minutes while fast ones still skip
the fight. Gates with floors give every build the whole fight, show a strong
build off as a Break instead of skipping the boss, and let enrages pace a
weak one. The bodies and the language came from looking: before them the
Red Hand was the size of a footpad, the move names vanished in a frame
under the build's damage numbers, the stagger bar was clipped out of sight,
and a band's safe inside was painted as danger. **The game's boss scripts
did not run at all** (its battle copied the zone's hooks before the boss
came); the tests shared the zone's hooks and passed. A test now runs a boss
through the game's own wiring.

### 16.2 The bots read the bosses

`BossSense` is what anyone does after dying to a boss once: it steps out of
a marked blow by its shape (walking to where it will not be when the blow
lands, dashing in time when walking will not do), leaves ground about to
close, stands over the Barrow Lord, runs down the thief, closes on
Grimtunnel while a lamp flares. A relaxed player reacts in 0.45 s and misses
one marked blow in five; a practised one 0.25 s and one in twenty. The
game's `--auto` uses the same sense, so pictures show a fight fought.

| Plain hands, 192 runs | Before | Reading the bosses |
|---|---|---|
| The Barrow Lord won | 21% | 90% |
| Blows landed / marked, all bosses | 310 / 4473 | 3 / 3107 (before the misses) |
| Won (greedy / random) | 70% / 71% | 92% / 87% |

### Why this is the answer

A sweep measures the bot as much as the game. The old hands never laid the
Barrow Lord down and lost to him four times in five; they stood in every
lane. Balancing to that would have softened a fight a person wins on the
second try. One sense shared by every bot, with a human's reaction and
misses, makes the numbers the game's.

### 16.3 The long night

The owner: **"endless is truly endless - just keep ramping up till its
impossible (or not if the users get better and better and finding ways to
win haha)"**. No Dawn: past the win the night goes on until the survivor
falls or takes the way out. It climbs on three lines at once
(`Play/Zones/ArenaRun.cs`, "the long night"):

- **The horde hardens** by the minute (`ArenaRun.Hardening`): health
  `1 + 0.1m + 0.006m²`, blows `1 + 0.035m`, smoothly for the first hour past
  the half hour; from then on both compound by 3% a minute, so by two hours
  past nothing stands. A little quicker too, to a ceiling of 15% (pace a
  player can still read and outrun). No minute is a tenth harder than the
  last: a slope, never a cliff.
- **The dark swears an oath** every five minutes: one more of the table's
  oaths, named as it comes with what answers it, listed with the run's own,
  paying what it pays at the table. First the questions of where to stand
  (embers, champions, ruin, the vigil), then pace and number (the hunt, the
  swarm), last those that grind (winter, iron, blight, the deep); never the
  moonless, since the night must stay readable. Out of oaths, it deepens,
  two levels a time.
- **What rules the people comes again** every quarter hour, its sign a
  minute before: its own fight, a third more health and a quarter more bite
  each time, its chest a card richer; heralds in between.

Fair throughout: the crowd's number, its throwers and every telegraph keep
their caps; nothing kills without a mark; every new pressure is announced.

| Deft hands, tier 2, story level, table oaths (won runs) | Before | After |
|---|---|---|
| Minutes past the half hour: median (p10–p90) | 21 (9–40) | LN_AFTER |
| Furthest | 62 | LN_FURTHEST |
| What ended them | heralds and the Kerchiefs' bruisers first, then lamplings | LN_KILLERS |

### Why this is the answer

Before, the endless phase was one line: everything harder by the minute.
It killed every run (polynomials do), but the only thing that changed was
how long things took to die. The genre's best endless modes add questions
as they go (Halls of Torment's breaking Vault, Hades' heat); our oaths are
already that, each with its rule, its answers and its pay, so the dark
taking them is the world's own escalation, readable because the player has
met each one at the table. The returns give the long night set pieces and
a rhythm. The first version made the first return a wall (the night's
hardening and its levels on top of the boss's own: the sweep's runs fell to
it more than to anything) and swore the winter's crawl and iron skin early;
returns now grow by a rule a player can learn, and the oaths that grind come
last. The compounding waits an hour so the long tail belongs to great
builds and great hands; after it, nothing holds for ever, as asked.

### 16.4 Decisions the studies left open

Recorded here because this area owns them; the story's are the bible's
("The nights") and are followed.

- **Fight length**: 90–120 s at par, by gates; built (16.1).
- **Clear or thin the horde for the boss**: clear 8 m round its entrance, hold
  the rest at 40%, and make way at the arrival; full at the soft enrage.
- **A boss that takes ember takes no cards**: the bar and the level step
  back; the build stays (the Mithrix lesson).
- **The endless hour's end**: none (the owner); 16.3.
- **Grimtunnel never dies in an arena** (the bible): he goes back down the
  hole, delighted; a table's Lamplings field **the Ganger**, never him or his
  name.
- **Keegan's duel at first light** (the bible): a day fight without ember;
  not an arena, so not built here.
- **New outcomes from fights**: **Greymuzzle let go** is built narrowly, as
  the bible has it: only if she knelt and promised and the stream already
  runs clean, he goes down, gets up and goes to his sick (`greymuzzle` =
  `spared`, Maeca's regard up; the story lead owns the words). The crates,
  the pump and Edric use values that already exist, when their fights do.
- **Banes**: learned by day, recorded once seen, never hidden for good; the
  weakness is named on arrival.
- **The Silver Penitent**: yes, last, behind a flag (not started).
- **Oaths on bosses**: lightly, one visible change each (the iron oath
  halves the stagger bar's filling: `MapRules.StaggerTaken`); the horde
  carries the rest. Not yet built.
- **Enemy hazards hurt the horde** at half, the horde's own hazards only, not
  an oath's ground: not yet built.
- **Signs**: none at tier 1 before minute ten, one at tiers 1–3, two from
  tier 4, three on late heralds: not yet built.
- **Contested ground** (two peoples at war): from Act 2, as the bible has it,
  and a candidate for the long night's deeper hours.
- **Thieves**: ember stones on the ground only, never what is held; a
  carrier, in the lamplings' words. The Red Hand's Toll is a boss's verb, and
  recoverable.
- **Weight as a number** beside the words, for planners: yes, not yet built.
- **Mirror Step** stays strong against the crowd; champions and bosses see
  through it (built).
- **The Lamplings' champion** is the digger until the Blasting-Cart has art.
- **An oath's ember**: every oath that promised more ember paid none (the dead
  left the same stones under any oath); `MapRules.EmberGain` pays it now.

---

## 17. Before and after''')

rep('''---

## 17. Open''', '''---

## 18. Open''')
open(p, 'w', encoding='utf-8').write(s)
print("ok")

# Arena bosses: designs for the night

Eight bosses for the ember arenas, a midpoint for the fifteenth minute, and
two shapes for the endless hour after the win. Each is fitted to the story
bible's people, to the code's units and to what the research says works
(`MECHANICS.md` for the why; `IMPLEMENTATION.md` for the how). Every
number here is a proposal for the balance lab, sized against the probe
(`AUDIT.md` §4); none of it is in the game.

## 0. The rules every arena boss keeps

These come first because they fix the current boss's biggest problems
whichever designs are built.

**0.1 The boss is not the herald.** Heralds stay the people's champion. The
boss is its own creature, with its own view, verbs, bar and music, and its
lieutenant at the fifteenth minute (§9) is the only preview the player gets.

**0.2 The run-up (28:00 to 30:00).** Build on `docs/feel` S-11, which already
specifies the valley before the peak. Add, per boss, a sign in the world
before the bar: the Pack-Mother's howl from one edge of the map, the Barrow
Lord's drum, Grimtunnel's knocking, the Red Hand's whistle. Each is a sound
first, then a light on the arena's edge at the bearing it will come from.
The player turns to face it before it arrives.

**0.3 The arrival.** The boss enters from where the sign was, onto the
picture (12–14 m from the survivor, not 18), with its own entrance (§ per
boss) and a name card. Its escort is its own kind, not a random draw.

**0.4 The horde during the fight.** Not held at half by a blind spawner:
each boss says what the horde does (the Pack-Mother commands it, the Barrow
Lord raises it, Grimtunnel's lamplings flock to light). The default, for a
boss that does not say, is the S-12 breather: 40% of the target, so the
boss is the thing on screen.

**0.5 Phases are gates, not just thresholds.** Each phase ends at a health
mark **or** at its time ceiling, whichever comes first (Brotato's rule:
`RESEARCH.md` §3.1), and cannot end before its time floor:
- **The mark.** Damage past a phase's mark is not taken off the next phase;
  it fills the **Break**. When the phase ends the boss staggers for 2.5 s,
  plus up to 2.5 s more by the overflow, and the overflow lands as one
  big number ("BREAK 48,210"). The stagger is the transition: the boss
  cannot be hurt in it.
- **The floor** (10–20 s a phase). Before it, health stops at the mark and
  everything more goes to the Break. A strong build never skips a phase,
  and its surplus is shown, not silently thrown away (Gungeon's hidden cap
  is the warning: `MECHANICS.md` §7).
- **The ceiling** (60 s a phase, 90 s for the last). Past it, the next
  phase begins anyway at the health the boss has. A weak build sees every
  move the boss has before it meets the enrage.
- **What overkill buys.** The fight's summed Break is its score: past a
  par amount the boss's chest gains an item, and a fight won with no
  heavy blow taken (§0.8's middle band) gains another ("Unscathed", the
  Master Round's lesson). Surplus power and clean play both turn into
  something, rather than being cancelled.

**0.6 The budget.** Fight length at par (the probe's bot at ×2, roughly an
ordinary player at that tier): **90–120 s**, of which 60–75 s is damage time
and the rest transitions, invulnerable moves and phases that ask for
movement. A strong build (×4 to ×10) should still take **45–60 s**, held up
by the time floors. A weak build (×0.5) should take 4–5 minutes and meet
the soft enrage. Today it is 7–45 s at par and 2–5 minutes at ×0.5, with no
enrage (`AUDIT.md` §4).

**0.7 Health.** The def's `Health` (level 1) × `ScaleFor(level)` × a boss
multiplier, as now, but with the multiplier raised and flattened across
tiers: **× (12 + 2 × tier)** instead of × (6 + 2 × tier) (× 14 at tier 1,
× 20 at tier 4). With the bosses' own level-1 `Health` (about twice the
champions' they replace) that is about 70–90 s of the probe's par damage
at every tier. Every design below gives its level-1 `Health`; at the half
hour the level is 14 at tier 1 (`ScaleFor` × 11.9), 16 at tier 2 (× 14.6)
and 20 at tier 4 (× 20.9).

**0.8 Damage.** The survivor carries roughly 400–700 health at the half hour
(the probe's boss lunge, 99, was 13–25% of it). Three bands, in units of
the def's `Damage` (× `ScaleFor` × 1.3 as now):
- **contact and small shots**: × 0.5–0.8 (5–8% of a par survivor);
- **telegraphed blows**: × 1.5–2 (25–35%): two mistakes hurt, three kill;
- **arena mechanics** with a 2 s or longer telegraph: × 3–4 (60–80%), never
  a certain kill from full health, so a mistake costs the fight's margin,
  not the run.

**0.9 Telegraphs.** The language in `MECHANICS.md` §2: amber for "a blow is
coming here" (circle, line, cone, ring), violet for "this ground stays bad",
pale blue for "stand here" (safe zones, the boss's weak moment). Wind-ups no
shorter than 0.8 s for a single blow, 1.2–1.5 s for a heavy one, 2–3 s for
anything that covers the arena. Every telegraph has a sound, and every boss
attack that can be perfect-dodged says so by being `telegraphed` in
`HurtPlayer`.

**0.10 Soft and hard enrage.** At 3 minutes the boss's cadence quickens by
a quarter and the horde's share returns to 100% (the soft enrage: the fight
gets harder, not impossible). At 5 minutes the boss performs its final move
on a loop (the hard enrage, named for each boss) that a weak build can
survive for perhaps a minute. Both are announced. Neither is reached by an
ordinary build.

**0.11 The kill.** `docs/feel` S-11 (slow motion, silence, a chord, the horde
dying in rings). Add: **the boss drops the run's best chest** (3 items at
least, 5 at tier 3 and up, evolutions first), its Named roll and its people's
signature item (`docs/items/ACQUISITION.md` §4), and a per-boss death that
says who it was (below). The way out opens where it fell, as now.

**0.12 What the oaths do to a boss.** Each oath changes the boss in the
same direction it changes the horde, and says so on the name card:

| Oath | On the boss |
|---|---|
| Swarm | Its add waves are half again as large. |
| Champions | Its lieutenant returns at 30:00 beside it (a second, smaller bar). |
| Deep Dark | Two levels, as for the horde; nothing else. |
| Long Vigil | Its phases' time floors are a third shorter, its cadence a fifth faster. |
| Long Winter | Its heavy blows chill. |
| Blight | It leaves blighted ground where it walks (violet, 2 s). |
| Embers | Its telegraphed blows leave burning ground. |
| Hunt | A fifth faster, and its wind-ups a tenth shorter (never under 0.7 s). |
| Iron | Its Break bar fills a third slower from anything but criticals. |
| Moonless | Its telegraphs are drawn only inside your light; the sound cues double. |
| Ruin | Its adds burst; it bursts once, at each phase change. |

## 1. The Pack-Mother, Alpha of the Deep Wood

*The Pack. Table tiers I–IV. In the story, **Greymuzzle, the Old Alpha**
(The Hollow by Night).*

**Who she is.** The Pack is sick, not bold: the Dig's slurry is in the
stream (`STORY_BIBLE.md` §6). The Pack-Mother is what leads it where
Greymuzzle does not: a great grey she-wolf, older than the wolves around
her, blind in one eye, the slurry's green in her breath. She is not hunting
the survivor; she is herding them, away from the den. The fight is a hunt
run backwards: the survivor is the deer.

**The question it asks.** *Can you see the drive coming and refuse to be
herded?* A movement fight, with a damage check in the middle.

**Body.** `wolf_matriarch`: Health 1,100, Speed 6.2, Damage 24, Radius 1.1,
Mass 12, AttackEvery 0.8, Scale 1.9. Resists as the Pack. At tier 1: about
183,000 health (today's boss: 49,000); at par about 105 s with her time
out of reach.

**The run-up.** At 28:00, a howl from one edge of the map; the wolves on the
field lift their heads and break off toward it for a moment. At 29:30 two
green eyes at the edge of the survivor's light, on that bearing.

**Phase 1, the Drive (100%–65%).** She will not close. She runs the edge of
the survivor's light (light radius + 2 m), and the wolves do the work:
- **The Drive** (every 14 s): she howls (a rising two-note call), and the
  Pack forms a crescent on one side of the survivor, 10 m out, and walks
  forward. The open side is the trap: she waits beyond it, and a **lunge
  lane** (amber line, 1.0 s) is drawn across the gap as the crescent closes.
  Counter: go *through* the crescent's thinnest point (the wolves are
  ordinary; a dash or an area skill breaks them), never into the gap.
- **Hamstring** (when within 6 m): a single bite, 0.8 s wind-up, × 1.5 and a
  2 s slow. Perfect-dodgeable.
- She can be hit only when she lunges or in the survivor's light; she
  flees the light after 3 s in it. Ranged builds and a lantern's reach
  shine here; melee builds catch her at the end of every lunge.

**Phase 2, the Moon (65%–30%).** The sky clears; the arena brightens
(`AtmosphereFor`, a moon key light) and her shadow is long. She stops
hiding and circles at 12 m:
- **Moon-howl** (at the start, then every 25 s): the light dims to the
  survivor's own radius for 8 s, and **three spectral wolves** (her dead,
  `wolf_spirit_hostile`, Health 0: they cannot be hurt) run straight lanes
  across the survivor's light, each lane telegraphed 1.2 s. The damage
  check: while they run, she sits howling at the edge, and a Break of 6% of
  her health in those 8 s cuts the howl short (`BossBar.Channel`, "The
  moon-howl: break it!") and stuns her 3 s.
- **The Pack's turn**: every wolf killed within 8 m of her in this phase
  makes her faster for 6 s (a stack, at most 5): killing the Pack in front
  of her enrages her. Counter: fight the Pack away from her.

**Phase 3, the Den (30%–0).** She stands. No more drives; she fights at the
survivor's side with everything left:
- **Shake** (every 6 s): a 120° cone in front, 1.0 s, × 1.8.
- **Lunge** chains of three, each lane telegraphed 0.8 s, the second and
  third aimed where the survivor *will* be (their velocity × 0.6 s).
- At 15% the last of the Pack comes (a ring of 12 wolves at 14 m, closing).

**The horde.** Wolves only, all fight long; boars stop coming. The Pack is
her tool, never her shield: she takes nothing from them except the Phase 2
stacks. The arena's trees matter: a lunge that ends in a trunk stuns her
for 2 s (as a boar's charge does now, `Ai.cs:130`).

**Soft and hard enrage.** At 3 minutes the drives come every 9 s. At 5
minutes, **The Long Hunt**: the light shrinks to half and does not recover;
she lunges from the dark every 3 s.

**With the survivor's tools.** Hunter's Mark finds her even in the dark
(the mark draws her outline for its 5 s): the blessing that answers her.
Spirit Companion's wolves will not fight her; they whine and stay at heel
(a line of bark, and a good moment). Fear and freeze do nothing, as now;
stuns are 0.6 s, but each one adds to her Break. The Moonless oath doubles
her darkness; the Hunt oath makes her lunges faster.

**Scaling.** Tier raises health and damage only. The phase floors (15 s,
20 s, 15 s) hold a ×10 build to about 55 s.

**The death.** She does not fall where she stands: she runs, hurt, to the
arena's edge, and lies down at the foot of a standing stone. The Pack stops.
Every wolf on the field turns and goes past the survivor to her, and lies
down round her (`Behavior.Flee` toward a point, then `Stationary`), and the
howl that started the fight is answered once from the far wood. Silence,
then the chord. No wolf attacks again in this arena; the endless hour is
fought against what comes from the dark instead (§11).

**Drops.** The run's chest (3/5 items), Pack-Mother's Collar (Named, her
home), wolf pelts, the Pack's Own set pieces.

**Greymuzzle, the story's version.** The same fight, with three changes.
Greymuzzle does not herd; he shields. In Phase 2 he stands over the den
mouth and will not leave it (a fixed point in the arena), and the wolves
throw themselves in front of the survivor's projectiles for him. If Maeca is
the survivor's friend, her name card line is three words, as her voice sheet
allows: "He's old. Quick." And if the stream already runs clean
(`stream.clear`), his eyes are clear too: at 30% he stops and looks at the
survivor, and a prompt offers *Let him go*. The fight ends there, won, and
the Pack is spared (a new outcome for the owner to name; `beasts.outcome`
today has `cured`, `allied`, `exploited`, `ignored` and `slaughtered`). It
gives the night's fight a door to the kinder ending the day already has.

## 2. The Barrow Lord, Who Would Not Lie Down

*The Risen. Table tiers I–IV. In the story, **the Barrow Lord, of the
Seventh Legion** (Behind the Sealed Door).*

**Who he is.** A centurion of the Seventh Legion, buried with his century
"under what it could not burn". The Legion's dead hold the inner door from
inside; he is one who came out to see why the chain is loose, and found the
valley full of the risen. He still drills them. He speaks, in a dead man's
Latin-flattened Common, only orders: "Close up." "Hold." "Rise."

**The question it asks.** *Can you read a formation and break it?* An
arena-shaping fight: his walls are men.

**Body.** `barrow_lord`: Health 1,250, Speed 2.6, Damage 30, Radius 1.3, Mass
40, AttackEvery 1.3, Scale 2.4. Resists as the Undead (holy hurts him
half again). At tier 1: about 207,000 health; at par about 120 s.

**The run-up.** A drum, slow, under the music from 28:00; the risen on the
field stop and turn to face it, then go on. At 29:40, the ground at the
bearing splits along a line, and he rises with his standard.

**Phase 1, the Drill (100%–70%).** He walks behind his century:
- **Close Up** (every 16 s, a drum roll then "Close up!"): eight
  `risen_warrior` rise in a line 14 m long, shields locked (`Guard`, arc
  180°), and march across the arena toward the survivor at 2 m/s. The line
  is a moving wall: projectiles from the front glance off, and the men do
  not step aside. Counter: go round its end (the line is 14 m; a dash or
  Vault clears it), or break one shield (the line breaks at that man and
  the two halves wheel inward), or use something that is not a projectile.
- **Pilum** (every 7 s): from behind the line he throws a spear: a line
  telegraph 20 m long, 1.0 s, × 1.6; it stays stuck in the ground 6 s as a
  small collider (an obstacle you can hide behind).
- He is behind his men; ranged builds must go round, melee must go through.

**Phase 2, the Testudo (70%–40%).** He joins the line:
- **Testudo**: twelve shields form a ring round him (radius 4 m); he is
  untouchable from outside, and the ring turns slowly to face the survivor.
  A lit **standard** stands in the ring's centre. Counter: break the
  standard (a breakable part, 6% of his health, holy and fire half again),
  which drops the ring and stuns him 3 s; or wait 12 s for him to open it
  and charge.
- **Charge of the Century** (when the testudo opens): three columns of four
  risen run straight lanes from the ring outward, one toward the survivor
  and two either side of it (three line telegraphs, 1.3 s). The gaps are
  the safety; they close by one column at 55%.
- **Rise** (when a man of his falls): the dead get up as they do now
  (`RaiseSpec`), but only his men, and only once each: a grave remains, and
  a grave already risen does not rise again.

**Phase 3, Who Would Not Lie Down (40%–0, then again).** He fights alone:
- **Gladius** (every 4 s): a two-strike combo, a 90° cone then a short
  lunge, 0.9 s and 0.7 s, × 1.5 each.
- **Hold!** (every 12 s): a ring telegraph round the survivor at 6 m, 1.5 s:
  every grave inside it sends up a hand (a root, 1.2 s). Stand outside the
  ring, or dash as it closes.
- **At 0 health he falls, and does not die.** He lies in the ground,
  glowing, for 8 s; the bar reads "He will not lie down" and a pale-blue
  circle (the safe colour) is drawn round him, 3 m. **Stand in it** for 3 s
  (a channel the survivor holds, shown on the bar) and he is laid down for
  good. If the survivor does not, he rises with 25% and Phase 3 begins
  again, a fifth faster. Holy damage while he lies there counts the 3 s
  twice as fast. The hordes's risen try to drag the survivor out of the
  circle (they come at it from every side).

**Why this works.** Phase 3's last beat turns the damage race into a
movement choice at the moment of victory: the horde's whole job is to keep
you out of a circle. Builds that overkill him still have to stand still in
the middle of the dead. Players remember the fights they *finished*.

**Soft and hard enrage.** At 3 minutes, a new line forms every 10 s. At 5
minutes, **The Last Watch**: the whole century rises at once round the
arena's edge and walks inward, shields locked, a closing ring of walls;
it reaches the middle in 40 s.

**With the survivor's tools.** Holy builds (Dawnpulse, Hallowed Ground) are
his answer: they burn the standard and count the lay-down twice. Shield
Bash and Bull Rush break a shield in the line (bash interrupts; the
interrupt already exists). Grave Call's servants and Risen Servants fight
for the survivor in Phase 1, but in Phase 3 **he calls them back**: "Rise,
and to me" (any raised ally within 10 m changes side for 6 s): the boss who
steals the survivor's own dead.

**The death.** He sinks into the ground standing, a hand raised in a
salute that is not to the survivor but to something below. Every risen on
the field kneels, then falls, as one, and the drum stops on the off-beat.
On the Barrow-Wood themes, the graves close.

**Drops.** The run's chest, the Barrow Lord's Helm (Named, Act 2 and on),
barrow dust, Legion fragments at tier IV.

**The story's version (Behind the Sealed Door).** The fight is inside the
door, on the stair's first landing: a narrower arena (radius 40), a wall at
the north where the stair goes down. When he is laid down, the dead of the
stair part, and the bootprints going in are visible past them: the
journal's line for Jessop.

## 3. Grimtunnel, Roused, Come Up Out of the Dark

*The Lamplings. Table tiers I–IV. In the story, **The Dig Boils Over**.*

**Who he is.** The Boss of the Dig: three lamps and a grudge, a believer
carrying a god its heart. He cannot die before Act 3 (`STORY_BIBLE.md` §3),
and the story's outcome already says "drove Grimtunnel back down". So this
fight is won when he goes back down the hole, not when he dies. It is the
one comic boss: Snib comments.

**The question it asks.** *Can you keep your feet when the ground itself
is the enemy?* An arena-shaping fight with breakable parts.

**Body.** `grimtunnel_boss`: Health 950, Speed 3.6, Damage 22, Radius 1.0,
Mass 10, AttackEvery 1.1, Scale 2.3. Fire resistant (50%), frost
vulnerable. At tier 1: about 158,000 health; at par about 100 s, a third of
it underground.

**His three lamps.** Each is a breakable part on his harness (red, blue,
green; 8% of his health each), and each lamp lit gives him a verb:
- **Red, the blasting ember**: lobbed charges (a circle, 1.4 s, × 1.6, leaves
  burning ground 3 s), three at a time.
- **Blue, the deep lamp**: the lamplings see by it; while it burns, any
  lampling that surfaces does so *under the survivor* (a 1.0 s circle at
  their feet).
- **Green, the slurry**: a sprayed cone of slurry (60°, 1.2 s) that leaves
  violet ground that slows.
Break a lamp and that verb is gone for the fight; a broken lamp's shards
burst (the colour's school). The bar shows three lamp icons.

**Phase 1, the Dig (100%–60%).** He tunnels:
- **Under** (every 12 s): he dives, a mound travels toward the survivor
  (visible, with a sound like rocks in a barrel), and he **bursts up**
  where it stops: a circle 3.5 m, 1.2 s from when the mound stops moving.
  While under he cannot be hurt; above, for 4 s after, he is dazed and
  takes half again.
- **Lamp-moths**: the lamplings flock to light. Every 20 s, ten lamplings
  surface round the *brightest thing* in the arena: a lamp of his, a
  burning patch, the survivor's own light. A survivor who has broken his
  lamps is the brightest thing.

**Phase 2, the Collapse (60%–25%).** The ground goes:
- **Sinkholes**: each Under now leaves a pit (radius 3 m, a hole in the
  ground: unwalkable, `InBounds` false, collision added) where he burst. Up
  to six pits; the oldest fills in when a seventh opens. The arena fills
  with holes the player must route round, and the horde routes round them
  too (the flow field re-bakes).
- **Snib's charge** (once, at 50%): Snib shouts from the edge ("Boss! BOSS!
  Not the good stuff! It IS the good stuff.") and a crate of blasting ember lands in the
  middle (a barrel prop). Hit it when Grimtunnel is within 5 m and it blows
  (× 0.1 of his health, and his armour off for the rest of the phase).
  Miss, and he hits it himself in 20 s and the blast is round the survivor.

**Phase 3, the Boil (25%–0).** He is out of his hole and in a temper:
- He runs at the survivor's light, faster (Speed 4.8), swinging a pick (a
  90° cone, 0.9 s, × 1.5).
- Every 15 s the Dig **boils**: violet slurry wells up in a ring that
  expands from the arena's centre (a ring telegraph that moves outward at
  4 m/s; jump it, dash through it, or stand on a pit's rim where it breaks).

**Victory: back down the hole.** At 0 he does not die. He grabs the nearest
pit's edge ("Not done! Not DONE!"), is pulled in by the lamplings below,
and the pit collapses on top of him. The ground in a 10 m circle round it
falls in and rises again as rubble; the run's chest is thrown up out of the
dust a second later. Every lampling on the field dives underground and is
gone. Snib's last line from the edge: "Snib will tell Boss you said hello. Snib will NOT tell Boss."

**Soft and hard enrage.** At 3 minutes, the pits stop filling in. At 5
minutes, **The Fall**: the arena's floor caves from the edge inward, a ring
of pits closing at 2 m every 10 s (Ashford's Fall, small).

**With the survivor's tools.** Frost builds stop his Under (a frozen mound
surfaces at once, stunned). Cinderwake is risky: burning ground is bright,
and the lamplings come for it. Vault and Grapple Chain cross the pits;
Bull Rush pushes him into one (a lamp breaks). Moonless arenas are kind to
the survivor here: less light, fewer moths.

**Drops.** The run's chest, Grimtunnel's Spare Lamp (Named), Snib's Hard Hat
(rare), ember shards and slurry.

## 4. The Red Hand, Warlord of the Ravine

*The Kerchiefs. Table tiers I–IV. In the story, **Redcowl** (Raid on the
Roost).*

**Who he is.** The Kerchiefs are what is left of Ashford's levy: red was
Ashford's colour. The Red Hand is their war-captain, a big man in a red
brigandine with a tollman's bell on his belt, who takes a toll from
everything that passes, the survivor included. He is the boss who steals.

**The question it asks.** *What is your build without its best piece?* A
fight about the survivor's own tools.

**Body.** `red_hand`: Health 1,050, Speed 3.8, Damage 26, Radius 0.95, Mass
8, AttackEvery 1.0, Scale 1.6. At tier 1: about 174,000 health; at par
about 105 s.

**The run-up.** A whistle, three notes, from one edge, and an answering
whistle from another; at 29:30 the toll bell, then he walks in with a
crossbow on his shoulder and two bruisers carrying a cage on poles.

**Phase 1, the Toll (100%–65%).**
- **The Toll** (every 30 s, first at 10 s): he rings the bell ("Toll's
  due."), and a footpad dashes in, touches the survivor and runs. The
  survivor's **highest-ranked weapon stops firing**, its icon greyed in the
  HUD with a red kerchief over it, and the thief (`toll_thief`, Health ×
  2 of a footpad, fast, `Behavior.Flee`) runs for the arena's edge with a
  light on him. Kill him within 12 s and the weapon comes back with a
  surge (it fires three times at once). Let him go and it comes back after
  25 s on its own. The thief is telegraphed: a red ring round the survivor
  1.0 s before he touches (dash out of it and he misses, and is stunned).
- **Volley** (every 9 s): he and four pillagers fire crossbows: five line
  telegraphs in a fan from him, 1.1 s, × 1.2.
- **Firepots** from the pillagers, as now, capped.

**Phase 2, the Cages (65%–30%).**
- **Cage** (every 20 s): the bruisers drop a cage over the survivor's
  position: a ring of eight posts (radius 5 m) telegraphed 1.5 s, then
  solid colliders for 10 s. Inside, footpads; outside, he waits with the
  crossbow. Dash out before it closes, or break a post (a breakable part,
  a moderate hit), or fight through. Walls you can see and break.
- **The Levy** (once, at 50%): eight bruisers in a shield line (Guard) with
  red colours, marching in step: the Ashford levy's drill. Unlike the
  Barrow Lord's line it does not raise the dead; it pushes (knockback on
  touch). The levy breaks if he is hit hard (a Break of 5% in 6 s): they
  look to him and waver.

**Phase 3, the Hand (30%–0).**
- He drops the crossbow and fights with a maul: a two-handed overhead (a
  circle at the end of a 4 m line, 1.2 s, × 2.0) and a sweep (a 160° cone,
  1.0 s, × 1.4).
- **Takes everything** (once, at 15%): the toll bell rings three times, and
  **all** the survivor's weapons stop for 6 s while the survivor's arts and
  dash still work: the moment the survivor's hands are their own. A red
  ring telegraphs it 2 s; a perfect dodge through it cancels it.

**Why this works.** The genre's strongest fantasy is the build; the Toll
makes the player notice what each piece of it is doing, and the chase to
get it back is a short, sharp objective inside the boss fight. It never
removes more than one piece for long, and always gives it back.

**Soft and hard enrage.** At 3 minutes, the toll every 15 s. At 5 minutes,
**Everything Owed**: the thief takes a weapon every 10 s and they do not
come back until he is dead.

**With the survivor's tools.** Mark Prey on the thief kills him outright
(not a boss, `Arts.cs:796`): a lovely answer. Smoke Bomb makes the toll
miss. Time Slip freezes the thief. Iron Vow's barrier makes the touch miss
(the barrier takes it). The Oath of Champions brings his lieutenant (the
Enforcer) back beside him.

**The death.** He goes down on one knee and takes off the brigandine's red
hood, and under it is a face, middle-aged, Ashford's; the bell drops and
rolls, ringing, and every Kerchief on the field stops, takes off their red
cloth, and walks away (`Flee`). Stolen weapons come back in one surge.

**Drops.** The run's chest, Ashford Levy Colours, red cloth, the Red Hand
set.

**Redcowl, the story's version.** Redcowl fights as the Red Hand, with
three changes: he never says "Ashford" (his lines in `VOICES.md` voice:
rough, Scots edge); the cage holds the caravan's prisoners if they are
still held (`caravan.survivors`), and breaking it frees them (they run;
they do not fight); and **the six crates** are in the arena if `be.crates`
is unset: stacked at the Roost's centre. Hit them with fire and they blow
(a crater, the arena's middle gone, and everything in it hurt, Redcowl
too): the story's B.E. go up here, and `be.crates` is set to `burned`.

## 5. The Warden of the Kiln Ford

*The Drowned (a new people: the Low Ford's dead and the Kiln Ford's, risen
mindless in the ditches). Act 2, only if the Kiln Ford is lit (`nell.told`
is `lie` or `evaded`, `STORY_BIBLE.md` §7.8). At the table thereafter as
**a Warden's echo** of either crossing.*

**Who it is.** The second of the seven Wardens woken: made by the Order of
the Morning Light to keep a crossing and kill what comes near. The Kiln Ford
Warden is a woman in Order's mail, drowned and huge, with a lamp in each
hand (Brannoc's last two irons, lit). It sings in the water, as the dead
watchman wrote of the first.

**The question it asks.** *Will you remember the first Warden?* The
prologue's language, at the scale of a horde: lamps that ward her, a charge
you steer into them, a channel you break. The players who learned the Ford-
Warden are rewarded for it.

**Body.** `kiln_warden`: Health 1,300, Speed 2.6, Damage 30, Radius 1.5, Mass
40, AttackEvery 1.4, Scale 2.8. At tier 2 (where Act 2 starts): about
303,000 health; par about 120 s, much of it behind the ward.

**The arena.** A ford: the arena's middle is a river (a band 14 m wide
across the map), with **stepping stones** (circles 2.5 m) across it. Water is
walkable but slow (× 0.6) and the drowned rise from it. Six lamp-irons stand
in two rows along the banks.

**Phase 1, the Lamps (100%–60%).** As the Ford-Warden, at scale:
- **The ward**: damage taken × (1 − 0.12 × lamps lit): × 0.28 with all six.
  The bar is grey while any burn.
- **Charge** (every 8 s): a line 24 m, 1.3 s, "It lowers its head..."; a lamp
  in the lane is snuffed and she is stunned 4 s, taking × 1.5. Lamps also
  break to blows (each has 2% of her health).
- **Cleave** (when within 5 m): circle 3.4 m, 1.05 s, × 1.5.
- **Sing**: while she sings (a held note, every 20 s for 5 s), the drowned
  rise from the water in the river's band only. Stay on the stones.

**Phase 2, the Flood (60%–25%).** She calls the river up:
- **The flood**: the water's band widens by 4 m every 20 s (a shrinking
  arena: the banks are what is left). Water's slow becomes × 0.45.
- **Channel** (at 60% and 40%): "RISE, YOU WHO DROWNED HERE." The Ford-
  Warden's channel exactly, 6 s, broken by a 9% Break or an interrupt;
  finished, it heals 6% and relights a lamp.
- **The lamps go under**: lamps in the water cannot be lured into; only
  bank lamps can. The puzzle tightens as the river grows.

**Phase 3, the Drowning (25%–0).** The water is everywhere but the stones:
- She walks the river at full speed (water does not slow her) and the
  survivor's only good footing is the stones and what is left of the banks.
- **Undertow** (every 10 s): a ring round her, 6 m, 1.4 s: anything in water
  inside it is pulled 3 m toward her.

**Soft and hard enrage.** At 3 minutes, the flood rises every 12 s. At 5
minutes, **High Water**: only the stones are above it.

**Brannoc's choice, in the fight.** If Brannoc knows about Nell and broke
the last irons, this fight does not exist; if he forged them and learned
later, the lamps are his work. At the table, the Warden's echo uses the
Ford-Warden (three lamps, the Low Ford's river, a man) with the Kiln
Ford's flood.

**The death.** The water goes down all at once, back into its band, and she
sits in it, the two lamps going out one after another. On her: the second
heart, if the story wants one; for the table's echo, the Warden's Lamp
(Named, the echo's only home, `docs/items/ACQUISITION.md` §4).

## 6. The Silver Penitent

*The Vigil. Act 2 (Silverstair and the war at the gate) and the table. The
items plan's "Sallow's champion".*

**Who he is.** One of the Unchained in Sallow's silver cages, bought and
armoured in argent plate for the war in the south: a soldier who rises
every night. His helm has no face but a silver ledger-plate with his entry
on it: a name scratched out, "From the Kiln road. Risen in the barrow
year. Comes back." He is the survivor as the Vigil would make them, and he
burns as they do: he has an ember of his own.

**The question it asks.** *Who can burn brighter?* A rival who grows by the
same rules the survivor does, and who comes back.

**Body.** `silver_penitent`: Health 900, Speed 4.2, Damage 24, Radius 0.8,
Mass 6, AttackEvery 0.9, Scale 1.3 (man-sized: the one boss who is not big,
and reads by his light, not his bulk). Shadow-resistant, holy-vulnerable
(he is Unchained). At tier 2: about 210,000 health, spent twice (he comes
back).

**His ember.** He collects ember. **Every ember stone the survivor leaves on
the ground within 20 m of him is his**: he pulls it as the survivor's vacuum
does (a visible stream of motes to him) and every 40 stones he takes a
level: one of the survivor's own weapons, at rank 1, then deeper. His
weapons are drawn from the survivor's build (the same art, coloured silver
and hostile). A survivor who collects cleanly keeps him poor; one who lets
the field fill with stones meets their own build turned round.

**Phase 1, the Rival (100%–60%).** He fights like the survivor: he moves,
dashes (a short line, telegraphed 0.4 s: his dash is not an attack), and his
weapons fire at a third of their rate. The horde is the Vigil's caged risen
(Silverstair's people); his kills of the horde drop stones too (he does not
fight them; they part for him).
- **Silver Ink** (every 15 s): he writes in the air, a line drawn across the
  survivor's position (a line telegraph 1.4 s): crossed while it burns
  (3 s, violet), it takes an ember level's worth of stones off the survivor
  (spilled, and his to take). The ledger's entry, written.

**Phase 2, the Return (60%–30%).** "Return to the dark" (Keegan's chapter
four, in Sallow's book):
- **At 60% he dies.** He falls, the light goes out of him, and the bar
  empties. Then, 6 s later, at the arena's edge, he **rises** with the
  phase's health ("He comes back more often than most."), and every stone on
  the field flies to him at once. The fight's twist, and the first time the
  player sees someone else come back.
- **Censers**: two Vigil knights swing censers (a mobile violet zone each,
  radius 4 m): inside, the survivor's ember pickup is halved.

**Phase 3, the Ledger (30%–0).**
- He uses the survivor's art (their ability, at its cooldown × 2), and their
  best weapon at full rate.
- **Cage** (every 18 s): the silver cage drops over the survivor (as the Red
  Hand's, but silver, and it drains 1% ember per second while closed).

**How to keep him down.** At 0 he falls again, and rises again in 8 s
unless the survivor **takes his ember**: stand over him (a pale-blue circle,
2.5 m) and the motes come out of him to the survivor (3 s). Taken, he is
laid down; the survivor gains three ember levels at once (the reward is
literally his power). Left, he rises with 20%, and Phase 3 begins again.
Mirror of the Barrow Lord's lay-down, and the story's: an Unchained can be
put down only by taking what keeps them up.

**Why this works.** It is the boss that steals the player's tools in the
truest way: it is built from them. It rewards a habit (clean collection)
the genre already teaches, and turns the survivor's power into the fight's
difficulty without a single damage multiplier. Its two returns are a
story beat played as mechanics.

**Soft and hard enrage.** At 3 minutes, his rate goes to two thirds. At 5
minutes, **Paid in Full**: every stone in the arena is his, wherever it lies.

**The death.** He kneels and takes off the helm. Under it, a young man,
grey with the dawn that is not here; he says one plain line ("Was I in the
book long?") and is gone. The survivor's journal: his scratched-out name,
if Ysolde's notes are found later. On the field the caged risen stop, and
stand there, waiting for orders that do not come.

**Drops.** The run's chest, Chapter Four (Keegan's handbook, Named), silver
ink, argent scraps, the Argent Vigil set.

## 7. The Thing in the Barn

*The Fevered (Act 2, the breakthrough under the Penhale farm; the items
plan's people). Act 2 story and the table.*

**Who it is.** Not a creature: a part of one. When the Dig breaks into the
Morrow's outer workings, something pale and segmented comes up under the
Penhale barn: a feeler of the Morrow, or a thing that lives on it. Tam heard
it knocking in Act 1. The Fevered are the farmhands and the neighbours
with the fever year's sickness in them again.

**The question it asks.** *Can you listen?* A boss under the ground,
telegraphed by sound first: the fight for players who play with the sound
on, with every cue also shown.

**Body.** `barn_thing` (the head; the segments are parts): Health 1,400,
Speed (underground) 5, Damage 28, Radius 2.0, Scale 3.2. Only its surfaced
parts can be hurt. At tier 2: about 326,000 health.

**The knocking.** Tam's knock is the fight's language: **one knock** = it is
moving; **two** = it will surface within 2 s; **three** = it will surface
under the survivor. Each knock also pulses a dust ring on the ground where
the sound comes from (shown as well as heard: an accessibility rule, not an
option), and the HUD's compass edge shows the bearing.

**Phase 1, the Knocking (100%–65%).**
- **Surface** (every 10 s): three knocks, then a 3 m circle under the
  survivor (1.2 s): segments burst up in an arc, the head among them. The
  segments stay up 6 s (breakable parts, each 3% of the whole; break all
  three and the head is stunned up for 6 s more).
- **Drag**: it pulls the Fevered under. Every 15 s, a cluster of the horde
  sinks into a dust ring (1.0 s) and it heals 1% per creature dragged.
  Kill the horde before it does; or let it, and it surfaces where it fed.
  The boss that feeds on the horde.

**Phase 2, the Bad Air (65%–30%).**
- The fever: violet bad air seeps from every hole it has made (a growing
  zone per surfacing, 5 m, staying), poisoning; the healing cut of the
  Blight oath applies in it. Wenna's blightward mask (if worn by day, it
  carries) halves it: the day's gear answering the night.
- **The barn falls** (once, at 50%): the barn (a large prop in the arena's
  middle) collapses; its beams become cover (colliders) and the knocking
  echoes off them (two bearings for each knock for 10 s).

**Phase 3, the Mouth (30%–0).** It comes up and stays up: a ring of segments
round a pale opening at the arena's centre, the ground round it opening by
a metre every 20 s. It sweeps (a 180° cone, 1.5 s, × 2) and breathes (a
line 16 m, 1.2 s, poison ground).

**Soft and hard enrage.** At 3 minutes, it surfaces every 7 s. At 5
minutes, **Ashford Again**: the ground goes, from the barn outward.

**The death.** The segments go slack and slide back down, and the ground
closes over them, too fast, like something being pulled; the knocking
stops, then, very far below, knocks **once**. (The Morrow is not dead. It
prays.) The farm is spared or lost as the story set (`STORY_BIBLE.md` §7.1).

**Drops.** The run's chest, the Penhale Lantern, bitterroot, moonpetal.

## 8. The Centurion of the Stair

*The Legion (Act 3, the stair down to the Morrow). The last arena boss; at
the table thereafter as an echo.*

**Who he is.** The Seventh Legion's dead keep the inner door "from inside",
and part for the Morrow's own light. The Centurion keeps the toll: one
square coin, stamped VII. He is not hostile to the survivor; he is hostile
to anything that comes down without paying, and the survivor burns with
the Morrow's light. The fight is a ritual as much as a battle.

**The question it asks.** *How much of your light will you spend?* The boss
that turns the survivor's ember into the price of the fight.

**Body.** `centurion`: Health 1,500, Speed 3.0, Damage 34, Radius 1.4, Mass 50,
AttackEvery 1.2, Scale 2.6. At tier 4: about 626,000 health.

**The parting.** The Legion's dead stand in ranks across the stair. They
**part for light**: while the survivor holds more than half an ember level's
bar (a light of their own, shown as an aura), the ranks within 4 m step
aside; below it, they close and push. The survivor's XP bar becomes their
key.

**Phase 1, the Ranks (100%–60%).** Formations as the Barrow Lord's, but the
lines open for the lit survivor and close on the unlit. He stands behind
them at the door.

**Phase 2, the Toll (60%–25%).** "The toll." He opens his hand:
- **Pay** (a prompt at the door): spend three ember levels (cards stay; the
  bar and the level go back) and the Legion lays down its shields for 30 s:
  he fights alone and takes × 2.
- **Refuse**: the ranks close entirely and must be broken by force.
- The choice is offered every 30 s. It is the only place in the game where
  ember is spent, and it prefigures the coin.

**Phase 3, the Door (25%–0).** He fights at the door with the Legion's whole
drill (all of the Barrow Lord's moves, and the Close Up's lines twice as
long).

**The death.** He does not die; he steps aside, and the door opens. "Paid."
If the survivor carries Vonnra's coin, he takes it in Phase 2 instead of
ember, and the survivor keeps every level: the coin's first, smallest use
(the bible keeps its great one for the ending).

## 9. The fifteenth minute: the Kindling

The great blessing at 15:00 is today an announcement. Make it a moment, and
make it the boss's first verse.

**What happens.** At 14:30 the horde draws back 15 m and thins to a third
(the S-12 breather). In the middle of the arena **a heart** surfaces: a
stone the size of a cart wheel, cut with a sigil, burning, one of the
chain's lesser links (the story's hearts in miniature: the Warden's was
one of the seven). Round it, the **lieutenant**: the boss's own creature,
with one of the boss's verbs and a fifth of a boss's health:

| People | Lieutenant | The verb it previews |
|---|---|---|
| The Pack | the Pack-Mother's yearling | the Drive (a crescent, a lunge across the gap) |
| The Risen | the Barrow Lord's standard-bearer | Close Up (a line of four shields) |
| The Lamplings | a sapper-foreman with one lamp | Under (the mound and the burst) |
| The Kerchiefs | the Red Hand's toll-taker | the Toll (a thief, a chase) |

**The heart.** The great blessing is owed whatever happens (it is never
lost). Break the heart within 60 s (it has the lieutenant's health, and
breaking it stuns the lieutenant 4 s) and the great blessing is offered
from **four** instead of three, with one deepening; fail, and it is three.
Kill the lieutenant as well and it drops the run's mid chest.

**Why.** Every survivors-like that players praise for bosses teaches their
language before the exam (VS's Arcana bosses at 11 and 21; Halls of Torment's
stage bosses before the Lord; `RESEARCH.md`). The Kindling puts a fight
where the run's pacing already wants a peak, and its reward is the run's
most important choice made better, not a bigger number.

## 10. The endless hour: Echoes

After the win, the herald every five minutes becomes **an echo**: one of the
*other* peoples' bosses, from the table's tier, cast in pale ember
(`view:echo` tinting the boss's view), at 60% of its health and the first
two of its phases only. Each echo killed drops a chest and gives the
**chain** a link on the HUD (one of seven). At seven links the next echo is
the Ford-Warden itself, and its death is the arena's highest score.

Scaling after the win already hardens the horde; echoes harden with it (×
(1 + 0.1 × minutes past) health). They give the endless hour a goal (the
chain) and a gallery (every boss the survivor has met), and they make each
people's boss worth having learned.

## 11. The endless hour: the Dawn

The bible's own hard enrage: the Unchained burn at night, and **at dawn the
light drains back into the ground and leaves them ordinary** (§1). Make it
the end of every arena.

- **At 50:00** the arena's sky begins to grey at the east edge (a slow change
  of the atmosphere preset); the music thins.
- **At 55:00 the dawn line**: a band of daylight enters from the east edge
  and crosses the arena at 1 m every 4 s. In daylight the survivor's ember
  drains (one ember level each 5 s, cards and all, from the most recent),
  and nothing of the night can stand in it (creatures that touch it go
  still and grey, and fall). The night side is the arena, and it shrinks.
- **At 60:00 or when the last of the night is gone**: "Dawn." The fight is
  over; the survivor leaves with everything earned, the run ends as a win,
  and the journal says "Saw the night out".

Why: it is a hard cap like the Reaper, but it is the world's rule, not a
monster's, and it is beautiful where the Reaper is a joke the genre has
learned to wink at. The last minutes are a choice between staying lit and
running toward the dark: the run's best image. It also gives the engine a
ceiling (the horde's numbers at 60 minutes are knowable).

(For the story's later acts the owner may prefer a hunter instead: the
Vigil's knights coming at 45:00 for an Unchained who stays too long. Dawn
is recommended; see `README.md`, decision 4.)

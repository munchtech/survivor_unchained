# Callings: two ways each, the Lamps, and the Flare

The classes plan covers what makes the four callings different, the skill tree, the ultimates, the new skills, and how all of it reaches the nights, the maps and endless. **It is a plan only: no game code until the owner approves it.** Classes design lead, 11 October 2026; judged by a max judge (PASS WITH FIXES, all fixes applied). Research notes: `docs/design/notes/classes_*.md`. The warden's tree, drawn: `docs/design/classes_warden_lamps.svg`.

---

## For the owner (one page)

**Two ways per calling:**
- **Warden:** a *Sunderer* (greatsword: slow, staggering blows that split the ground) or a *Bulwark* (sword and shield: walk in, let them hit you, and they break on it).
- **Reaver:** a *Butcher* (twin axes: fights best bleeding) or *Chainbound* (a hooked chain that drags the horde into knots, with lightning running down it).
- **Arcanist:** a *Kindler* (fire and frost on the ground: freeze them, then shatter them) or a *Moonweaver* (moonlight that hunts on its own and marks what it touches).
- **Stalker:** a *Roadknife* (twin blades: every dash goes through the crowd) or a *Verge-Hunter* (longbow: far off, pinning the front).

**The tree is the Lamps.** It is one dark map, and each calling owns a quarter of it. You light one lamp a level, plus one for each story boss. Each type is a road, and your two roads meet at a bridge for hybrids. They also run on into your neighbors' quarters. A new player clicks the glowing lamp, and their skills visibly change. A planner hunts the blue lamps (big rules with a price) and the lamps that make two skills feed each other. Anyone can go anywhere; home is closer. Respec is free in town.

**Q / right-click becomes the Flare: your ultimate.** It fills fastest when you're in trouble. You're untouchable while it plays, and casting it near death heals you. Each calling has four (a big instant *Strike* and a timed *Stand* per type), with three lamps each that reshape it. Each one has its own staged look, a frozen key pose and hitstop. The movement art moves into the dash.

**Price:** about 22 lead sessions. Every Flare and new weapon is animated for both heroes. The Flare is new power at night, so the nights get rebalanced.

---

## 0. What exists, and what this changes

**The buttons.**
- *Today:* combat skills fire themselves. The hands have the dash (two charges), one **art** (Q / right-click) and the draught (R).
- *After:* the same, but Q / right-click is the **Flare** (the ultimate), and the draught stays on R. The code renames in two steps, and the name `Ultimate` is never reused: today's `Act.Ultimate` (the draught) becomes `Act.Draught` first, then `Act.Ability` becomes `Act.Flare`.
- *Why:* the owner said "it dosn't HAVE to be movement". The two dash charges are already two movement buttons.

**The Kin movement arts** (`Abilities.Kin`: bull_rush, grapple, mirror_step, vault).
- *Today:* each calling starts with one, pressed on its own button.
- *After:* the Kin becomes the calling's **dash form**. Its effect rides the first dash after its own wait (§2.3); the dashes in between are plain.
- *The other movement arts* (Leap, Blink, Sprint, Wraith Walk, Cinder Trail, Echo Step) stay learnable from manuals by anyone, as dash forms of their own. The timed ones become riders (Wraith Walk: half a ghost for 1.5 s after the dash).
- *Why:* the Kin were tuned for 7 to 11 s waits, and the dash comes back in 2.6 s. A wait per form keeps their power where it was. `ArtBook`'s ranks and all four facets of each art carry over as lamps. It also gives four calling-flavored answers to the owner's crowd note ("a brief knock-aside on a dash").

**The calling's other arts** (Shield Bash, Bulwark, War Cry, Time Slip, Mark Prey, Smoke Bomb).
- *Today:* pressed.
- *After:* they become **reflexes**: lamps that fire the art on their own when something happens (a champion closes in, a big blow lands, a perfect dash).
- *Why:* our genre fires itself. Grim Dawn's procs ("on block: ...") are the best version of this in an ARPG (`notes/classes_grim_dawn.md`).

**The night's draft** (26 combat skills in 10 paths; `SKILLS_DESIGN.md`).
- *After:* **unchanged, and still open to everyone.** Sixteen new combat skills join it, two per type. The Lamps change *how* drafted skills behave, never *which* skills you may take.
- *Why:* SKILLS_DESIGN §4 rejected a tree that chooses the night's skills ("the build should be discovered in the run"). The Lamps don't choose them. They decide what your Sunder does when the ember brings it.

**Levels and progression** (level cap 30, no paragon (§14.1); day skills rank with level; four attributes).
- *After:* **unchanged.** Lamps come from levels (29), story fights (about 13) and the atlas (8, finite): about **50 lamps** at the end of everything.
- *Why:* §14.1's reason still holds. An open-ended climb buries both gear and the ember.

**Leans and the calling's own great blessing.**
- *Today:* the calling's paths lean the draft ×1.3, and each calling has its own great blessing.
- *After:* both kept. The road you've lit deepest adds a small lean toward its type's cards (§2.10).
- *Why:* "certain things are easier".

---

## 1. Two ways per calling

Each type is built on three things:
- a **grip**: what's in the hands, which sets the clips and the silhouette;
- **a mechanic it alone builds around**, given by its road's first lamp, so it's there from level 1;
- a **minute-to-minute loop**.

Any calling can hold any grip; it only needs the attribute (`SkillBook.Need`). The Lamps make a calling's own grips better.

**Rule for every new skill:** a combat skill never moves the survivor. Only the dash and the Flare move her, so the player always owns where she is.

### The warden: hold the line

| | **Sunderer** (greatsword) | **Bulwark** (sword and shield) |
|---|---|---|
| Fantasy | The Watch's old two-handed blade, carried by someone who has stopped retreating | One shield on a wall built for sixty |
| Grip skill | **Sunder** (new): a slow 220° cleave; every fourth swing is a **heavy** overhead that splits the ground in a 7 m line | **Oathblade** (exists), with the shield blocking |
| Built around | **Heavy blows** (they stagger; champions break), armor broken (**Sundered**), holy fire riding the edge | **Stones**: each block lays one; at ten, the wall answers with a Rebuke all around. Barrier, retaliation, hallowed ground |
| Minute to minute | Wade to the edge of the horde, face where the line should fall, and let each heavy blow crack a lane open | Walk *into* the thickest press and stand. The Watch Bell drags them onto you, every block rebukes, and the crowd dies against the shield |
| Its skills | Sunder, **Groundbreaker** (new), Dawnpulse, Cleaver | Oathblade, **Rebuke** (new), **Watch Bell** (new), Judgement Disc, Hallowed Ground |
| Why it feels different | You choose where the blow falls: offense by size, with a weight you feel in every hitstop | You choose where to stand, and the horde chooses to die on it: offense by being hit |

### The reaver: take it out of them

| | **Butcher** (twin axes) | **Chainbound** (hooked chain) |
|---|---|---|
| Fantasy | A slaughterer who fights best bleeding (the name is the existing vocabulary: Butcher's Cleaver, Butcher's Wheel) | The reaver who took the chain off, and kept it |
| Grip skill | **Carve** (new): a fast three-chop flurry on the nearest, every half second; each chop bleeds | **Chain Lash** (new): a 7 m whip arc; the farthest thing struck is hooked and dragged 3 m in |
| Built around | **Frenzy** (hits stack attack speed), bleed, **fighting best hurt** (low health is strength), drinking life | **Bound** (a new status: tethered, can't move away, takes more from area), gathering then bursting, **lightning**: the storm is the Chainbound's |
| Minute to minute | In the middle of it with your health swinging: Frenzy climbs, bleeds stack, kills mend, and a low bar is when you hit hardest | At chain's length: hook the stragglers, anchor the pack, yank it into one knot, then break the knot with lightning |
| Its skills | Carve, **Hurled Cleaver** (new), Axe Gyre, Reaving Arc | Chain Lash, **Anchor** (new), Iron Palms, Arcweb, Thunderhead |
| Why it feels different | Close, fast, frantic and risky; the screen is red and so is your bar | Mid-range control: you arrange the horde before you kill it, like herding |

### The arcanist: some of them keep ledgers

| | **Kindler** (ember staff) | **Moonweaver** (wand) |
|---|---|---|
| Fantasy | Burns ember the way the whole valley does, and carries the ford's cold | Moonlight and moonfire, sent to find their own way |
| Grip skill | **Cinderfall** (exists) | **Seeking Motes** (exists) |
| Built around | **Ground**: burning fields and frozen fields, and fire on the frozen shatters them | **Marks**: motes mark, and a marked thing that dies passes its mark on. Projectile count, seeking |
| Minute to minute | Lay the field and stand behind it: a wall of fire between you and them, frost under the pack, and fire dropped on it once it freezes | Keep moving. The motes do the aiming, the wells guard where you were, the lantern-wisps wander out, and every death passes the mark on |
| Its skills | Cinderfall, **Pyre Line** (new), **Rime Field** (new), Firepot, Rimeshard, Hoarfrost | Seeking Motes, **Moonwell** (new), **Lantern-Man** (new), Moonbrand, Umbral Bolt |
| Why it feels different | It's about *where*: placement and timing (freeze, then shatter) | It's about *spreading*: one mark becomes a screen of them, always on the move |

### The stalker: never there when it lands

| | **Roadknife** (twin blades) | **Verge-Hunter** (longbow) |
|---|---|---|
| Fantasy | The road's knife-fighter: through the crowd and out before it closes | The Verge's hunter: far off, patient, never missing |
| Grip skill | **Twin Fangs** (new): after each dash, the two nearest are cut twice; within the Opening every Fang strikes true | **Volley** (exists), loosed from a longbow |
| Built around | **The dash and the Opening** (true strikes after a dash), poison stacks, dashing *through* things | **Distance** (blows from beyond 8 m), pierce, roots (snares), the prey and the spirit beasts that run it down |
| Minute to minute | Dash through packs, never round them; each pass leaves a wake of blades and each Opening is a burst of true strikes | Kite at range: snares pin the front, Heartseeker spears the toughest and everything in line, and the pack never reaches you |
| Its skills | Twin Fangs, **Cutting Wake** (new), Knifestorm, Gale Chakram, Blightfield | Volley, **Heartseeker** (new), **Snare-Line** (new), Thornbloom, Spirit Herd |
| Why it feels different | Its dash is its weapon: going in. Poison, never bleed (bleed is the Butcher's) | Its dash is its escape, and distance is its damage |

**Kept apart on purpose:** bleed and fighting hurt belong to the Butcher; poison and the dash to the Roadknife; lightning to the Chainbound; marks that pass on death to the Moonweaver; the prey (one marked target) to the Verge-Hunter.

---

## 2. The Lamps (the tree)

### 2.1 Why a board of lamps

"Lamps are lit. Stay where they reach" is the valley's evening call. The tree is drawn as a dark map of the valley's roads, and **you light lamps along them**; each lit lamp throws light on the next. Lamps that change the rules burn **blue**, because ember burns blue only in an iron. The words on screen stay plain: "3 lamps to light", "Blue lamp", "Road of the Sunderer". The first hour teaches four words: **lamp**, **road**, **blue lamp** and **Flare**. The rest (hearth, bridge, crossing, reflex) are names on the map, read when needed.

### 2.2 Layout

One shared board: a ring of eight roads around four homes.

```
                 Moonweaver ── Night Road ── Chainbound
                /                                     \
          Kindler                                    Butcher
            |      ARCANIST                REAVER       |
      Firebreak                                      Shambles
            |      STALKER                 WARDEN       |
       Verge-Hunter                                  Sunderer
                \                                     /
                 Roadknife ── Duelist's Road ── Bulwark
```

Each calling's **quarter** has three parts:
- **The hearth** (14 lamps), where you start:
  - the dash form and its four lamps;
  - the calling's two reflexes and three upgrades;
  - two Flare lamps;
  - two blue lamps: the calling's own, and **Banked Flame**.
- **Two roads** (32 lamps each), one per type:
  - the **entry** lamp, which carries the type's mechanic;
  - seven small lamps;
  - nine **skill lamps**: three each for the type's three signature skills;
  - five **notables**;
  - two **blue lamps**;
  - two **ultimate lamps**, with three modifiers each.

  A skill's own marker on the map is not a lamp: it shows where that skill's three lamps hang.
- **The bridge** (6 lamps) between its own two roads: the hybrid's lamps and one blue lamp.

Between neighboring quarters is a **crossing** (6 lamps, shared): two attribute lamps, two small lamps, and two notables that join both sides' mechanics. There are four:
- the **Shambles** (Sunderer and Butcher: heavy blows and bleeding);
- the **Night Road** (Chainbound and Moonweaver: chains and marks);
- the **Firebreak** (Kindler and Verge-Hunter: burning ground and arrows);
- the **Duelist's Road** (Roadknife and Bulwark: blocks and perfect dashes).

**Totals.** The board holds **360 lamps**: four quarters of 84, plus 24 on the crossings. At the end of everything a survivor has about **50**. A full road plus the whole hearth is 46. But a player carries one Flare at a time and three or four of a road's skills, so a focused build needs about 35, and the other 15 are the planner's: the other road, the bridge, a crossing.

**Depth.** Each road has depth gates, counted in lamps lit on that road (the free Strike counts):

| Lamps lit on the road | What opens |
|---|---|
| 3 | the road's ultimate Strike |
| 6 | its notables |
| 12 | its blue lamps and its Stand |

This is Grim Dawn's mastery bar and Last Epoch's mastery threshold. Going deep at home is strong, and dipping into the other road costs real lamps.

### 2.3 Lamp kinds

| Kind | Looks like | What it does | Rule |
|---|---|---|---|
| **Small** | a wick | a number tied to a condition or *two* tags ("+12% heavy-blow damage to staggered things"), or +2 to an attribute | Never a bare "+n%" (D4's flat nodes, `notes/classes_diablo.md`) |
| **Entry** | a lantern | the type's mechanic, from level 1 | One per road, lit by choosing the type |
| **Skill lamp** | a lamp with the skill's glyph | changes one skill (Last Epoch's skill trees, as three lamps per skill) | Wakes when you carry the skill: by day, or when the night's draft brings it |
| **Notable** | a lantern, named | one rule that deepens the mechanic or joins two things | Shows the glyphs of the skills it feeds |
| **Blue lamp** | a blue flame in an iron | a big rule **with a real price** (PoE's keystones, Grim Dawn's transmuters) | 28 on the board, each named |
| **Reflex** | a lamp with the art's glyph | fires a calling art when a condition is met | Its wait shows as a small arc on the HUD |
| **Dash form** | a boot-mark | the dash's effect, riding the first dash after the form's own wait | One form at a time; the dash pip shows when it's ready |
| **Ultimate** | a great lantern | learns a Flare | |
| **Ultimate modifier** | a small lantern by it | reshapes that Flare | Any number, one lamp each |

**Dash forms' waits:**

| Form | Wait |
|---|---|
| Bull Rush | 8 s |
| Grapple Chain | 6 s |
| Mirror Step | 8 s |
| Vault | 6 s |
| Learned forms | their art's old wait |

### 2.4 Where lamps come from, and respec

- **Levels:** one lamp a level, from 2 to 30 (29 in all). Today's attribute point a level stays.
- **Story fights:** one lamp for each story boss beaten for the first time. Act 1 has four, and there are about 13 over the three acts. The lamp is lit as the dawn comes: a story moment, not a menu.
- **The atlas:** eight lamps for atlas milestones (the experience lead places them), and no more. There is no paragon; §14.1 stands.
- **Respec is free, by day, at any lamp-post in a town.** Lamps go out one at a time or all at once, and there are **two saved layouts**. You can never respec mid-night or mid-map. It's free because planning is only fun when trying is free (D3's and Last Epoch's lesson; PoE's regret orbs and Grim Dawn's unrefundable bar are the failures, `notes/`).

### 2.5 Click and have fun: the new player

1. **At creation**, after picking the calling, pick its type from two cards. Each card has a five-second clip of the type playing and one line ("Slow, huge blows that split the ground"). The type sets the starting grip, lights the road's entry lamp (so the mechanic is there at level 1), and gives that road's Strike. It's never a lock.
2. **Each level**, the board opens on your quarter with **the next suggested lamp glowing** along your road. Click it, or anything next to a lit lamp. A toggle, **Light my way**, lights the suggested lamp for you every level (D4's and Last Epoch's recommended path).
3. **Every lamp's text is one line**, with the glyphs of the skills it feeds. A lamp that feeds nothing you carry is dimmed and says so, so there are no trap choices.
4. **The first blue lamp** opens at about level 12, by when the player knows their type. It's offered with its price in one red line.
5. **On a pad:** the stick moves lamp to lamp along the roads, and the shoulders jump between the hearth, your roads and the bridge (UI design, phase 3).

The new player's whole experience: pick the look you like, click the glowing lamp, and watch your skills change (Sunder's arc gets wider; the heavy blow splits two cracks).

### 2.6 Plan for hours: the planner

The depth is in **links between systems**, not bigger numbers:
- **Blue lamps that change a skill's mode.** Hunter's Stillness: standing still, every arrow pierces everything.
- **Blue lamps that change your body's rules.** Weight of the Oath: every blow is heavy, and you swing slower than anything can fix.
- **Notables that make one skill feed another**, and **reflexes chained to them.** Dawn Rhythm fires Dawnpulse on a heavy blow; a heavy blow on a champion fills its stagger; Shield Bash fires when the champion closes in; its stun ...
- **The bridge and the crossings.** These are hybrids inside a calling (Sword-and-Board: a greatsword and a shield at once) and across callings (the Duelist's Road: a perfect dash counts as a block).
- **The Flare's lamps:** three modifiers per ultimate, plus the hearth's two Flare lamps and Banked Flame.
- **Gear that touches the board.** A new Legendary family, the **lamp-lit** items, each lights one blue lamp anywhere on the board (PoE's Thread of Hope; Grim Dawn's skill-granting items). Corran's Sword is the model. Loot owns the list.
- **The night's draft on top.** Statuses, unions and discoveries (SKILLS_DESIGN §5) combine with what your lamps make of each skill.

### 2.7 Anyone can do anything, but home is easier and better

- **Any skill, any night.** The draft offers everything to everyone, as it does now. A warden can draft Moonbrand, and it works at full ember power; it just has no warden lamps feeding it.
- **Any grip, by day.** Any calling can hold a longbow if it has the Finesse, which the crossings' attribute lamps and gear provide.
- **Any road.** Walking into a neighbor's quarter costs the lamps in between. The next quarter over is affordable (the crossing is 6 lamps). The far side of the board isn't, at 50 lamps, and that's on purpose (PoE).
- **Not ultimates.** They are the calling's identity and the one hard lock, like the calling's own great blessing (open question 1).
- **Measured.** On its own roads, a type plays at most ×1.25 better than the same skills drafted off-calling, so "mostly possible" stays true. The harness holds it (§7).

### 2.8 The warden's quarter in full

Drawn in `docs/design/classes_warden_lamps.svg`. The other callings follow the same shape (§2.9).

**The hearth (14).**
- **The Warden's Oath** (start). The dash form is **Bull Rush**: every 8 s, the next dash is a 6 m charge behind a barrier of 15% of health. What's in the way is thrown aside; a champion stops it, stunned. Its lamps:
  - **Iron Hide:** barrier 25%.
  - **Pile Driver:** the rush ends in a slam that stuns 3 m around.
  - **Unbroken:** each thing struck adds 2% to the barrier.
  - **Gore:** what's struck bleeds, and champions take half again.
- **Reflex: Shield Bash.** "When three or more things, or a champion, are within 2.5 m: bash. They're thrown back and stunned 1.5 s, and a channel breaks. Every 7 s." Upgrades:
  - **Concussion:** stun +1 s.
  - **Shield Wall:** 8% barrier per thing struck, to 40%.
- **Reflex: Braced.** "A blow that takes a seventh of your health or more plants you for 3 s: blows cut by 65%, arrows turned back. Every 20 s." Upgrade:
  - **Rallying Stand:** mend 4% a second while braced.
- **Flare lamps:**
  - **Kindled Oath:** blows taken fill the Flare 20% faster.
  - **Last at the Crossing:** a Flare cast below a third of health also gives a barrier of 30%.
- **Blue lamps:**
  - **Hold Fast:** "You can't be thrown, stunned or slowed. Your dash is 30% shorter."
  - **Banked Flame** (every hearth has it): "Hold two Flares. Each fills 30% slower."

**The Sunderer's road (32).**
- **Entry, Two Hands:** heavy blows stagger ordinary things for 0.4 s.
- **Small (7):**
  - heavy blows +12% to staggered things;
  - +8% area to heavy and nova skills;
  - +2 Might (twice);
  - staggered things take 10% more holy;
  - each heavy blow landed in the last 3 s gives +1 armor (to +10);
  - Sunder +10% reach while you stand still.
- **Skill lamps:**
  - **Sunder:** *Wide Swing* (arc 300°), *Third Blow* (every third swing is heavy), *Burning Edge* (the heavy line sears).
  - **Groundbreaker:** *Twin Cracks* (two cracks, splayed 30°), *Fault Line* (cracks run 14 m), *Upheaval* (lesser things are thrown up for 0.8 s and take 30% more while airborne).
  - **Dawnpulse:** *Dawn Rhythm* (it fires when you land a heavy blow instead of on its timer, at most every 1.5 s), *Wider Morning*, *Searing Light*.
- **Notables:**
  - **Breaking Point:** champions fill a stagger bar from heavy blows and break for 1.5 s.
  - **Sundered:** heavy blows break armor; Sundered things take 20% more from heavy blows for 4 s.
  - **Momentum of the Blade:** a swing that kills three makes the next one 25% faster.
  - **Morning in the Steel:** heavy blows on seared things burst in holy light 3 m around.
  - **Rooted Stance:** after 1 s standing still, heavy blows are 20% wider. It pairs with Hold the Crossing.
- **Blue lamps:**
  - **Weight of the Oath:** "Every blow you strike is heavy and always staggers: Sunder's line comes on every swing. You swing 45% slower, and nothing can make you swing faster. You never strike true."
  - **The Unbroken Line:** "Sunder's heavy blow no longer splits a line. It breaks the ground all around you, 4 m, at half the blow."
- **Ultimates** (see §3.6):
  - **The Long Cut** (Strike), with *Second Cut*, *Line of Morning* and *Through the Wall*;
  - **Dawn in the Steel** (Stand), with *High Morning*, *Crescents Through* and *Mending Light*.

**The Bulwark's road (32).**
- **Entry, Shield Arm:** each block lays a **stone**, up to ten. At ten, the wall answers with a Rebuke all around you.
- **Small (7):**
  - +5% block while you stand still;
  - +5% block against champions;
  - +2 Resolve (twice);
  - barrier +15% while Stones are at five or more;
  - Rebuke and Watch Bell +15% on champions;
  - blocks mend 0.5% while above half health.
- **Skill lamps:**
  - **Oathblade:** *Shield and Edge* (after a block, Oathblade swings at once), *Reaching Oath* (reach +1.5 m), *Morning Edge* (each swing throws a crescent 6 m, as Oathkeeper does but weaker).
  - **Rebuke:** *Wider Rebuke*, *Rebuke the Strong* (champions take double), *Answering Light* (each rebuke mends 1%).
  - **Watch Bell:** *Loud Bell* (10 m), *Iron Bell* (things drawn in are slowed 30%), *Bell and Barrier* (3% barrier for each thing drawn in, from 2%).
- **Notables:**
  - **Mortar:** Stones last through a lull, and each gives 1% barrier.
  - **Turned Arrows:** blocked missiles fly back.
  - **Planted:** +15% block while standing still.
  - **Heavy Shield:** blocking a champion's blow stuns it 0.5 s.
  - **Faith in the Wall:** while your barrier is above a fifth of health, holy damage +20%.
- **Blue lamps:**
  - **The Wall Holds:** "Block chance is doubled (to 75% at most), but you can't block while moving."
  - **Bearer of Blows:** "What you block isn't lost: it's stored, and let out as holy damage by your next Rebuke. You mend 30% less."
- **Ultimates:**
  - **Bell of the Morning** (Strike), with *Fourth Toll*, *Bell for the Dead* and *Healing Peal*;
  - **Sixty on the Wall** (Stand), with *Shield-Brothers*, *The Wall Walks* and *Night Watch*.

**The bridge: Sword and Board (6).**
- **Notables:**
  - **Shield Swing:** heavy blows lay stones, and each block makes the next heavy blow 30% harder.
  - **Oath and Bell:** the Watch Bell tolls when you stagger something, at most every 3 s.
- **Small:** two lamps (Might and Resolve).
- **Blue lamp, Sword-and-Board:** "You may carry a greatsword and a shield together. The greatsword strikes 15% slower, and the shield blocks half as often."

**The crossings.**
- **The Shambles** (toward the Butcher):
  - **Opened Up:** a heavy blow on a bleeding thing deals the rest of its bleed at once.
  - **Cleaver's Weight:** every third chop of Carve is heavy.
- **The Duelist's Road** (toward the Roadknife):
  - **Parry:** a perfect dash lays a stone.
  - **Return Cut:** a block gives an Opening, so blows strike true for 1 s.

### 2.9 The other three quarters

Same shape: the hearth's dash form and reflexes, two roads, the bridge.

**Reaver.**
- **Dash form, Grapple Chain:** every 6 s, the next dash throws the hook up to 12 m at the first thing in its aim and hauls her to it. With nothing to bite, it's a plain dash. Its lamps:
  - **Whirling Chain:** on landing, the chain whirls 3 m around;
  - **Moored:** landing gives a 12% barrier;
  - **Second Hook:** a kill within 3 s brings the wait back;
  - **Reel:** lesser things are dragged to you instead.
- **Reflex, War Cry:** "ten or more things within 5 m, or a champion strikes you: roar. Lesser things flee 2.5 s, and you strike 25% harder for 6 s. Every 16 s." Upgrades: **Terror** and **Bloodlust**.
- **Reflex, Red Tide:** "below a third of health: a red roar that mends 10% and drives you 30% harder for 4 s. Every 25 s." Upgrade: **Second Tide** (every 18 s).
- **Hearth blue, Nothing Spared:** "All mending is 50% stronger. You have no draught."

| Road | Entry (the mechanic) | Notables | Blue lamps (the price in italics) | Skill lamps |
|---|---|---|---|---|
| **Butcher** | **Red Hands:** each hit +1% attack speed (Frenzy), to 20; it fades out of the fight | **Deep Frenzy** (Frenzy to 40), **Fights Best Hurt** (below a third of health, blows 30% harder and kills mend 1%: Blood Up's first rank, by day and in maps), **Open Vein** (a blow on a thing bleeding for 3 s bursts the bleed), **Red Work** (killing a bleeding thing mends 1%), **Hamstrung** (bleeding champions are 20% slower) | **Always Bleeding:** you count as below a third of health for Fights Best Hurt and Blood Up; *you can't be mended above half, and the rest is lost*. **The Butcher's Count:** each kill gives +1% damage for 10 s, to 50; *you take more by half the Count* | Carve (*Four Chops*, *Deeper Cuts*, *Reaching Chops*); Hurled Cleaver (*Two Cleavers*, *Ricochet*, *Another Way Back*); Axe Gyre (*Bleeding Gyre*, *Wide Gyre*, *Gyre on a Kill*) |
| **Chainbound** | **Hooked:** Chain Lash's hook leaves things Bound for 2 s | **Fast Binding** (Bound lasts 4 s; Anchor binds 7 m), **Conductor** (shock on a Bound thing leaps to every other Bound thing), **Short Leash** (hooked things are dragged 2 m further), **Knot** (eight Bound things close together are stunned 1 s), **Iron Reach** (Iron Palms strike Bound things from 6 m) | **The Long Chain:** melee skills reach 3 m further and hook the last thing they hit; *they strike 20% weaker*. **Lightning Rod:** storm skills strike Bound things first, and 40% harder; *you take 15% more from storm and fire* | Chain Lash (*Double Lash*, *Barbed Hook*, *Lash Back*); Anchor (*Two Anchors*, *Heavy Anchor*, *Live Anchor*); Iron Palms (*Palm on the Chain*, *Ringing Palm*, *Palm Storm*) |
| **Bridge: Hook and Hatchet** | | **Red Chain** (Bound things bleed; bleeding things stay Bound 1 s longer) | **Cleaver on a Chain:** Hurled Cleaver flies on your chain, hooks what it hits and drags it to you; *it no longer returns through the crowd* | |

**Arcanist.**
- **Dash form, Mirror Step:** every 8 s, the next dash leaves two reflections where she stood. They draw what hunts her, and burst when broken. Its lamps: **Hall of Mirrors**, **Cold Glass**, **Fighting Reflections** and **Glass Heart**.
- **Reflex, Time Slip:** "a blow that would take a quarter of your health, or a champion's mark closing on you: 3.5 s at a third of the speed. Every 30 s." Upgrades: **Borrowed Time** and **Deep Slip**.
- **Reflex, Spellward:** "a barrier of 10% of health whenever three spells land in one second. Every 8 s." Upgrade: **Thick Ward** (15%).
- **Hearth blue, Unbound Casting:** "Spells wait 30% less. You have 20% less health."

| Road | Entry (the mechanic) | Notables | Blue lamps (the price in italics) | Skill lamps |
|---|---|---|---|---|
| **Kindler** | **Fire on Ice:** fire striking a frozen thing shatters it, 2 m around, at half its blow | **Thermal Shock** (the shatter is 3 m and hits as hard as the blow), **Ashen Ground** (burning ground lasts 50% longer), **Ford-Cold Ground** (Rime Field chills before it freezes), **Firebreak Wall** (Pyre Line stops missiles), **Stand in Your Fire** (in your burning ground: +20% armor, spells 10% faster) | **Frostfire:** burn and chill no longer cancel; your fire chills and your frost burns; *each is 30% weaker*. **Ash Walker:** in your burning or frozen ground you take 40% less; *outside it your spells are 15% weaker* | Cinderfall (*Two Cinders*, *Wider Fall*, *Slow Burning*); Pyre Line (*Cross of Fire*, *Hedge of Fire*, *Rolling Wall*); Rime Field (*Quick Frost*, *Wide Field*, *Shatter Field*) |
| **Moonweaver** | **Moonmarked:** motes mark what they strike; a marked thing that dies passes its mark to one more | **Silvered** (marks pass to two, and the marked take 10% more), **Many Lights** (+1 projectile to spells), **Moon-Drawn** (motes seek the marked first), **Still Water** (Moonwell lasts 50% longer and fires 30% faster), **Moonfire** (a mark that passes burns violet: the new bearer takes moonfire) | **The Echo:** every spell fires again 0.5 s later at half strength; *spells wait 25% longer*. **Crowded Sky:** spells with projectiles fire two more, all seeking, *and no two strike the same thing; each is 35% weaker* | Seeking Motes (*Split Motes*, *Swift Motes*, *Heavy Motes*); Moonwell (*Twin Wells*, *Wide Well*, *Deep Well*); Lantern-Man (*Two Lanterns*, *Far-Wandering*, *Guttering*) |
| **Bridge: The Ledger** | | **Two Schools** (Rime Field's frozen ground makes Lantern-Man flare twice as often) | **The Ledger** ("Some of them keep ledgers."): each fire or frost spell makes your next moon or shadow spell 30% harder, and the other way round; *a spell of the same side twice running is 15% weaker* | |

**Stalker.**
- **Dash form, Vault:** every 6 s, the next dash springs 6 m the way you aim, untouchable in the air, and leaves caltrops where you left. Its lamps:
  - **Parting Volley:** knives loosed back at where you left;
  - **Caltrops Hold:** what steps on them is stuck 1.5 s;
  - **Light Feet:** landing gives back a dash;
  - **Nimble:** the wait is a third shorter.
- **Reflex, Mark Prey:** "every 9 s the strongest thing in sight becomes your prey: it takes 50% more and dies below 20%." Upgrades: **Two Prey** and **Executioner**.
- **Reflex, Smoke Bomb:** "a perfect dash throws smoke: 3 s unseen, sure true strikes. Every 12 s." Upgrade: **Choking Smoke**.
- **Hearth blue, Light Step:** "Three dash charges. Each dash is 30% shorter."

| Road | Entry (the mechanic) | Notables | Blue lamps (the price in italics) | Skill lamps |
|---|---|---|---|---|
| **Roadknife** | **Opening:** for 2 s after a dash, blows strike true | **Wide Opening** (3 s), **Adder's Kiss** (poison stacks to ten; at ten it bursts), **Through, Not Around** (dashing through things cuts them; each one cut gives back 2% of a dash), **Slip the Blow** (the perfect dash window is 50% longer), **Venom Edge** (true strikes add two poison) | **Never Still:** dashes come back 40% faster; *standing still for a second halves your blows until you move*. **Adder's Patience:** poison stacks without limit and never fades while you keep striking; *you can't strike true* | Twin Fangs (*Third Fang*, *Quick Fangs*, *Venom Fangs*); Cutting Wake (*Wide Wake*, *Lingering Wake*, *Wake of Smoke*); Knifestorm (*Fan Out*, *Knives Return*, *Poisoned Steel*) |
| **Verge-Hunter** | **Far Eye:** blows from beyond 8 m strike true one time in four | **Pinned** (Heartseeker roots lesser things it passes through), **Run It Down** (when the prey dies, Spirit Herd's beasts run down the next strongest), **Fletcher's Eye** (+1 pierce), **Hold the Distance** (blows from beyond 8 m +20%), **Spring Back** (the Vault springs back from your aim, and landing looses a Volley) | **Long Sight:** blows from beyond 8 m strike 50% harder; *within 4 m, 30% weaker*. **Hunter's Stillness:** after a second standing still, every arrow pierces everything; *moving, arrows can't pierce* | Volley (*Wide Volley*, *Twice Fletched*, *Barbed*); Heartseeker (*Split Heart*, *Quick Draw*, *Heart of Thorns*); Snare-Line (*More Snares*, *Biting Snares*, *Snare and Burn*) |
| **Bridge: Bow and Blade** | | **Quick Hands** (after a dash, your next Volley looses at once) | **Close and Far:** within 4 m your blades strike 30% harder, beyond 8 m your arrows do; *in between, both are 15% weaker* | |

**The other crossings.**
- **The Night Road:**
  - **Lightning Leaps the Chain:** storm that strikes a Bound thing runs to everything Bound.
  - **Moon on the Chain:** a marked Bound thing marks everything Bound to it.
- **The Firebreak:**
  - **Fire Arrows:** arrows that pass through your burning ground catch fire.
  - **Frozen Snares:** snares in Rime Field freeze what they hold.

### 2.10 By day, by night, in maps: one rule

| | Rules (entries, notables, blue lamps, reflexes, dash form, skill lamps, the Flare and its lamps) | Sizes ("more", "faster", "harder", +%) | Counts (projectiles, pierce, chains, targets) | Small lamps |
|---|---|---|---|---|
| **By day and in maps** | in full | in full | in full | in full |
| **By night** (the table's arenas and story fights) | **in full**: they wake on whatever the draft brings | **at a quarter**; a blue lamp's *price* stays in full | at most +1 each from the whole board | become a **×1.25 lean** toward the road's cards, as the Edge does (SKILLS_DESIGN §14.2) |

By night, every lamp keeps its rule but not its size. This keeps the night the ember's ("power from nothing, gone at dawn"; SKILLS_DESIGN principle 8): identity crosses into the night and numbers barely do. The harness holds a full 50-lamp board at night within ×1.25 of an empty one.

**Leans.** The calling's path lean (×1.3 to ×1.5) and the road's lean multiply, and they are clamped at ×2.

**The grip skill.** The weapon in hand already brings its skill to the night at its rank (§10). When the survivor holds a different weapon, the road's grip skill is offered in the first draft instead.

---

## 3. The Flare (ultimates)

### 3.1 The buttons

- **Q / right-click / pad Y: the Flare.**
- **R / pad X: the draught.**
- **Space / Shift / pad A: the dash,** with two charges, the perfect window and i-frames; the dash form rides it after the form's wait.
- **The Flare on the HUD:** the "art in hand" slot becomes the Flare, the centerpiece between the globes (UI design's instrument). It fills as a rising ember. When it's full, it breathes, and her eyes, hands and weapon edge glow in the calling's hue.
- **Reflexes on the HUD:** their waits show as small arcs beside it.

### 3.2 How it fills: a dopamine life-saver

The meter runs from 0 to 100. It fills **fastest when you're in trouble**, and slowest from simply killing (`notes/classes_ultimates.md`: FF's limit break, Hades' Call). Starting numbers, for the harness to tune:

| Source | Fill | Why |
|---|---|---|
| Blows taken | +1.2 for each 1% of health lost; doubled below a third of health | Being hurt is when you need it |
| **Close calls** | a perfect dash +10; blocking a champion's or boss's blow +6 | Rewards the skill the dash already teaches |
| **The ember answers** | the first drop below a quarter of health: +35 (at most once every 45 s) | The life-saver: a half-full Flare is ready just as you're nearly dead |
| Bosses | +1 for each 1% of their health you deal | Two or three Flares in a boss fight, from fighting it well |
| Champions | +0.25 for each 1% of their health you deal; +8 on the kill | A champion is a step, not a full Flare |
| Ordinary kills | +0.25 each, at most +1 a second | The horde can't spam it |

*Always Bleeding* never counts as low health for the meter.

**Targets:**
- the first Flare about 90 to 120 s into a night;
- then one every 60 to 90 s;
- two or three in a boss fight;
- faster when it's going badly.

**Starting charge:** nights and maps start empty, and story fights start at half (they're short). In a map, the meter carries between areas.

### 3.3 The window

- **Untouchable while it plays:**
  - a **Strike** holds the controls for its length (at most 1.2 s), untouchable throughout and for 0.4 s after its last blow;
  - a **Stand** gives the controls back at once, is untouchable for its first 1.5 s, and then its own stated defense holds (§3.6).
- **The flare burns the air:** at the key pose, enemy missiles within 6 m are burned away.
- **A flare at the edge burns brighter:** cast below a quarter of health, it also mends 20% of health over a second, and its reach is 25% larger. That makes every Flare a life-saver by design.
- **Against bosses:** a Flare breaks a boss's channel and staggers it a little, but never stuns it outright. A boss's danger marks always draw over the Flare's light.

### 3.4 Choosing and shaping

- **Four per calling:** one **Strike** (instant: one decisive moment) and one **Stand** (a timed state) for each type. A road's Strike opens at depth 3, and its Stand at depth 12. The type chosen at creation gives its Strike from level 1.
- **One carried at a time.** Change it in the book by day, or at a night's start before the first draft.
- **Three modifier lamps each,** on the road beside it, plus the hearth's two Flare lamps and Banked Flame (two charges).
- **Damage scales with level:** the character's level by day and in maps, the ember's at night. A Flare counts as its type's tags (The Long Cut is heavy), so the road's lamps feed it.
- **Four new great blessings at night** touch the Flare, one per role:
  - **Bright Hour** (power): the Flare is 40% larger.
  - **The Ember Answers Twice** (ward): below a quarter of health the Flare fills to full, once a night.
  - **Short Wick** (quickening): it fills 35% faster.
  - **Called Shot** (answer): it deals 60% more to champions and bosses.

### 3.5 The shared beat: every Flare's grammar

This is what makes every ultimate feel like a limit break. The experience lead builds it once (camera, time), skills VFX builds the screen side (the grade), and every Flare uses it.

1. **The press (t = 0):**
   - Time drops to 8% for 0.22 s of real time.
   - The music ducks 9 dB, and a sub-drop "inhale" (an ember catching) plays under the calling's stinger.
   - The world desaturates 70% and darkens by a quarter, except her. The vignette is soft, with no hard edge.
   - The camera pushes in 12% and pitches down 4° over 0.18 s (ease-out).
   - Her ember glow ignites in the calling's hue.
2. **The key pose (up to 0.3 s):** her anticipation pose is held. This is the poster frame, and the weapon's light peaks on it.
3. **The release:**
   - Time returns over 0.08 s.
   - **Hitstop** on the main blow: 6 to 8 frames (100 to 133 ms); 2 to 3 frames on lesser hits.
   - Shake trauma 0.5 to 0.8, scaled by the settings.
   - The camera eases back to play framing over 0.6 s.
4. **The look's laws** (skills VFX, inherited):
   - No hoops: a shockwave is dust, debris, heat shimmer and lit ground cracks, never a bright-edged ring, and a spinning thing reads as dark iron and motion blur, not a lit circle.
   - Light reads as light, never as geometry; no solid white bars.
   - A gaussian never makes an edge.
   - Light is held below the knee, except a Flare's own short column moment.
   - Enemy danger marks draw over everything.
5. **The last blow:** a Flare that kills a boss plays 0.6 s at 20% speed while the camera orbits 15° around the boss, then hands over to the victory.
6. **Hues:**

| Type | Hue |
|---|---|
| Warden | dawn-gold on steel |
| Butcher | blood-red on iron |
| Chainbound | storm-blue on dark iron |
| Kindler | ember-amber with ford-blue |
| Moonweaver | moonlight silver-blue with moonfire violet |
| Roadknife | steel with poison-green |
| Verge-Hunter | bone-white with Verge green |

### 3.6 The sixteen: staging briefs

Each brief says what the Flare does and its defense, then the camera, animation, VFX, sound and hitstop beyond the shared beat. Times run from the release.

#### Warden: Sunderer

**The Long Cut** (Strike, 0.8 s). One horizontal sweep of a blade grown to 12 m of dawn light, then a vertical cleave that splits the ground in a 24 m line.
- *Horde:* everything within 12 m is cut, and the line carves a lane.
- *Boss:* the cleave lands as a heavy blow and Sunders it (armor −30% for 8 s).
- **Camera:** pulled out 10% for the sweep, then a fast 6° roll into the cleave's direction.
- **Animation:**
  - key pose: blade low behind, both hands, weight on the back foot;
  - the sweep, 0.25 s: a full turn on the planted foot;
  - a 0.1 s rise;
  - the cleave down, 0.12 s;
  - a recovery kneel, 0.3 s.
- **VFX:**
  - the blade lengthens as a core of gold light inside a heat shimmer (not a solid bar);
  - the sweep leaves a smear of light at knee height;
  - the cleave opens a ground crack that glows from below, with dust jetting up along its length in sequence (a running fuse) and chunks thrown out.
- **Sound:** a long metal draw; the sweep's air-roar; for the cleave, a bell-struck impact with sub, then rock tearing along the line.
- **Hitstop:** 3 frames on the sweep, 8 on the cleave; shake 0.8.

**Dawn in the Steel** (Stand, 6 s). The greatsword burns with morning. Swings are 40% faster, every swing throws a crescent of light 10 m, and every heavy blow staggers whatever it hits.
- *Defense:* blows on her are cut by 30%.
- *Horde:* the crescents mow lanes.
- *Boss:* the staggers stack quickly, and the crescents hit it from range.
- **Camera:** a 0.5 s push-in, then normal; a slight zoom-out (5%) while it lasts, so the crescents' reach shows.
- **Animation:** key pose with the blade raised flat overhead, light pouring down it; then her swing clips at 1.4×, the blade trailing light.
- **VFX:**
  - the blade's edge is a white-gold core shedding ember sparks;
  - the crescents are thin, sharp and visibly traveling (the skills lead's note on Rend and Mend: thin, darker, seen to travel);
  - a faint gold mote-rise around her feet.
- **Sound:** a held tone without a choir (the Order's evening call, hummed low, never words) under each swing's ring.
- **Hitstop:** 2 frames a swing, 5 on heavy blows.

#### Warden: Bulwark

**Bell of the Morning** (Strike, 0.9 s). She strikes her shield like a bell, three times. Each toll stuns every lesser thing on screen for 1 s and sears them, and each mends her 4%. The third toll is a holy blast 8 m around.
- *Horde:* the screen stops three times.
- *Boss:* each toll breaks a channel and fills its stagger.
- **Camera:** still, with a tiny push on each toll (2%, 4%, 8%).
- **Animation:** key pose with the shield raised to the face and the sword pommel drawn back; three pommel strikes 0.25 s apart, the third full-bodied.
- **VFX:**
  - each toll sends a **pressure wave**, seen only as a ripple in the air and dust lifting off the ground outward (no ring);
  - lesser things' rims flash gold as it passes;
  - on the third toll, light pours up from the shield as a short column.
- **Sound:** a real bronze bell, recorded close, its decay ringing under the fight for 4 s. The world's sounds drop out for 80 ms after each toll.
- **Hitstop:** 4, 4 and 8 frames.

**Sixty on the Wall** (Stand, 6 s). This is the wall the Watch built for sixty: fifty-nine spectral shield-bearers of the Watch close in an arc in front of her and hold.
- *What it does:* it blocks every missile, the press throws back what touches it, and every block on it rebukes.
- *Defense:* she takes 80% less.
- *Horde:* a front that doesn't break.
- *Boss:* its charges and missiles break on the wall.
- *Lore:* the story lead confirms the bearers fit.
- **Camera:** pulls back 15% and lifts 6° to show the whole wall, and holds there while it lasts.
- **Animation:** key pose with the sword raised and the shield planted (the "form up" call); the bearers step in from either side in a 0.4 s ripple and lock shields.
- **VFX:**
  - the bearers are faint, cold-gold silhouettes in Watch mail, lit from behind like figures in lamp-smoke, not glowing ghosts (the skills lead flagged Barrow Host's pale ghosts);
  - their shield rims catch the light;
  - a block flashes on the struck shield only.
- **Sound:** sixty shields locking, in layered thuds rippling outward; a low murmur of men; each block a shield-crack.
- **Hitstop:** 4 frames at the lock, 1 frame per block.

#### Reaver: Butcher

**The Butcher's Bill** (Strike, up to 1.2 s). She leaps on the strongest thing within 10 m and chops it: one chop for each tenth of her health missing (at least four), and each chop mends 2%. If it dies, the chops she has left go with her to the next strongest within 6 m. Each chop splashes bleeding 2 m around. This is her *fights best hurt*, paid out in one go.
- *Horde:* the toughest near her, gone, and her health back.
- *Boss:* up to ten heavy chops, landing behind it and staying inside its reach.
- **Camera:** follows the leap with a 0.15 s lag, and pushes 8% on landing.
- **Animation:** key pose crouched, both axes back, teeth bared; the leap, 0.25 s; alternating chops 0.06 s apart, the last two-handed overhead; a vault off to the next.
- **VFX:**
  - dark red arcs that hang for a moment and fall as droplets;
  - each chop's mend is a thin red thread drawn back into her;
  - blood mist on the last chop;
  - her eyes and the axe edges glow ember-red.
- **Sound:** a grunt on the leap; wet, heavy chops rising in pitch; a bone-crack on the last; a low growl between.
- **Hitstop:** 2 frames on each chop, 7 on the last.

**Butcher's Hour** (Stand, 8 s). Frenzy fills at once. She strikes twice as fast, every blow bleeds, blows execute ordinary things below 15%, and every kill adds 0.3 s.
- *Defense:* every kill mends 1%.
- *Horde:* a red blur.
- *Boss:* sustained damage while it lasts, her health held up by the mending.
- **Camera:** 3% closer for its length, with a faint red vignette.
- **Animation:** key pose with her head thrown back in a roar and the axes out wide; then her swing set at 2×, in a forward-leaning hunt stance.
- **VFX:**
  - red smoke trails from the axes, and from her shoulders like breath in cold air;
  - the world tints slightly warmer;
  - executions burst in a short spray.
- **Sound:** her heartbeat under everything, quickening; the chops tighter and drier.
- **Hitstop:** 1 frame on every hit, 4 on executions.

#### Reaver: Chainbound

**Drag Them Under** (Strike, 0.8 s). She whirls the chain once overhead and casts it out. Hooks bite up to 24 things within 14 m, and she hauls them all into one knot at her feet, then drives the chain into the ground. The slam stuns 1 s and breaks the knot.
- *Horde:* the edge of the screen comes to her and dies.
- *Boss:* it's hooked, dragged 3 m and stunned 1.5 s, and a channel breaks.
- **Camera:** zooms out 15% for the cast, then rushes back in with the haul.
- **Animation:** key pose with the chain whirling overhead, one foot forward; the cast's throw, 0.15 s; the haul, a two-hand heave back, 0.3 s; a downward drive, 0.12 s.
- **VFX:**
  - the chain splits into many hooked lines (dark iron catching the light), each visible as it bites;
  - the hauled things slide on the ground with dust wakes;
  - the slam throws dirt and stone upward in a cone.
- **Sound:** the whirl's hum; a ratcheting rush; one massive iron-and-earth slam.
- **Hitstop:** 2 frames as the hooks bite, 8 on the slam.

**Storm on the Chain** (Stand, 5 s). She raises the chain like a lightning rod and the sky answers. Then she lashes it in sweeping figure-eights 8 m out in front of her. At the end of each sweep a bolt strikes the chain and runs down it into everything the sweep touched. Bound things call bolts of their own.
- *Defense:* the sweeping chain knocks back what it hits and turns missiles.
- *Horde:* a storm she walks into the crowd.
- *Boss:* about two bolts a second while it's in reach.
- **Camera:** steady, 8% out.
- **Animation:** key pose with the chain raised skyward; then a walking lash loop (sweep, return, sweep).
- **VFX:**
  - the chain is dark iron with motion blur, never a lit circle;
  - the current shows only as brief, fine forks running down short lengths of it after each strike (no white tubes, as with the Tempest);
  - each bolt drops from above with a short sky flash;
  - scorch marks are left where the sweeps ended.
- **Sound:** the chain's whir; thunder cracks layered with a tight electric snap; rain-hiss under it.
- **Hitstop:** 3 frames on each sky strike.

#### Arcanist: Kindler

**Burns Twice** (Strike, 1.1 s). She drives the staff down, and frost races out across the ground under every pack on screen (0.4 s). Then twelve embers fall on the frozen ground, and each impact shatters everything frozen around it. It's the old wives' saying on the ford road: a fire lit on ice burns twice.
- *Horde:* the screen's packs freeze, then break.
- *Boss:* it's chilled, and four of the embers seek it.
- **Camera:** lifts 8° and pulls out 15% to show the fall, then settles back.
- **Animation:**
  - key pose: staff raised two-handed, ember lit in her eyes;
  - the drive down, 0.15 s;
  - head up and held as the embers fall;
  - a sweep down on the last.
- **VFX:**
  - the frost is crystalline texture racing over the ground (not a ring);
  - each ember is a streak of molten light with a smoke trail, falling at an angle (never vertical white bars);
  - impacts throw flame jets turned along their way on the screen (Firepot's method), with a spray of ice shards and steam;
  - the ground is left charred and wet.
- **Sound:** a creak of ice spreading; a rising roar from the sky; staggered impacts, each a hiss and glass-shatter at once.
- **Hitstop:** 3 frames on the first impact, 6 on the last.

**Hard Winter** (Stand, 6 s). The ford's cold comes up out of the ground. Everything on screen slows 60% and freezes after 2 s in it, and her spells shatter what's frozen. When it ends, the thaw bursts.
- *Defense:* the slow itself; nothing reaches her quickly.
- *Horde:* the whole screen frozen in place, then broken.
- *Boss:* slowed 40%, and the thaw-burst hits it hard.
- **Camera:** no push; a slow 3% drift inward over its length (the hush of cold).
- **Animation:** key pose with the staff driven into the ground and frost crawling up her arm; then normal casting.
- **VFX:**
  - rime spreads outward over the ground as crystalline frost texture (not a ring);
  - breath steams from everything, and frozen things glaze;
  - at the end, the ice cracks with meltwater spray and a shatter burst on each.
- **Sound:** the wind drops out; a high, glassy ring; creaking ice. The thaw is a chorus of cracks.
- **Hitstop:** 6 frames on the thaw-burst.

#### Arcanist: Moonweaver

**The Branding** (Strike, 1.0 s). She closes her hand, and every enemy on screen is branded with a crescent. 0.6 s later the brands burst in order, outward from her, and each death passes a mark on.
- *Horde:* a silver wave rolling out to the screen's edge, then the marks running on through what's left.
- *Boss:* its brand bursts last and hardest.
- **Camera:** a 5% pull-out as the brands appear, to show the whole screen lit.
- **Animation:** key pose with one hand raised, fingers spread, hair lifting; the hand closes slowly into a fist (0.3 s); a small turn of the wrist as the bursts start.
- **VFX:**
  - each brand is a small silver crescent glint above the target's head, all appearing in one frame;
  - the bursts are violet moonfire tongues (Moonbrand's crisp jets), traveling outward in a visible ripple of timing, with no ring drawn;
  - a passed mark is a thin silver arc hopping to the next.
- **Sound:** a single high chime as they brand; then a rolling run of soft detonations from near to far, like a peal.
- **Hitstop:** 2 frames as the brands land, 5 on the boss's burst.

**The Drowned Moon** (Stand, 6 s). The moon comes up in the ground, the way the ford reflects a moon that isn't in the sky. A pool of moonlight 5 m wide opens at her feet and follows her, and motes pour up out of it, twelve a second, seeking and marking.
- *Defense:* things that enter the pool are slowed 40% and marked.
- *Horde:* a silver storm that finds everything.
- *Boss:* the motes favor it once the lesser things are dead.
- **Camera:** lifts 6° and pulls back 8% so the pool reads from above.
- **Animation:** key pose with her arms drawn down and apart, palms to the ground (calling it up); then normal casting with a slower, gliding gait.
- **VFX:**
  - the pool is the ground turned to still water holding a pale moon's reflection, lit from below, held flat on the ground;
  - its edge fades softly, with no rim;
  - motes rise from it as crescent glints with violet moonfire trails;
  - marked things carry a small crescent.
- **Sound:** a low swell like a breath held under water; each mote a soft chime, piling into a shimmering chord.
- **Hitstop:** none (it's a flow); 4 frames as the pool opens.

#### Stalker: Roadknife

**The Road's Toll** (Strike, 1.2 s). She's gone in smoke and strikes twelve things in 1.2 s, flickering between them, the last blow on the strongest. Each is cut and poisoned, and anything below 25% dies. She reappears where she started.
- *Horde:* a dozen champions and elites cut down.
- *Boss:* the last four cuts all land on it.
- **Camera:** still, so the flicker reads, with a light 5% zoom out.
- **Animation:** key pose with the blades crossed at the chest, half crouched; then twelve 0.1 s strike poses (cut, back-cut, thrust), each a single held frame with motion smear; she reappears in a low finish.
- **VFX:**
  - her afterimages hang for 0.2 s at each strike point, fading in steel-grey;
  - a green-black poison bloom on each target;
  - the trail between strikes is a thin smoke line.
- **Sound:** one slice per hit in quick succession, rising; a sheath sound on the finish.
- **Hitstop:** 1 frame per cut, 6 on the last.

**Through and Through** (Stand, 6 s). For 6 s her dashes are free and endless, and every one cuts what it passes through. Everything she passed through is **notched**. When it ends, every notch is cut at once.
- *Defense:* the dash's i-frames are 50% longer while it holds.
- *Horde:* a scribble of dashes through the crowd, then the whole scribble opens at once.
- *Boss:* notched every pass; the final cut lands once per notch.
- **Camera:** 6% out to show the paths.
- **Animation:** key pose with a blade flicked out to each side and her cloak snapping; her dash clip chained, with a spin-cut variant on every third dash.
- **VFX:**
  - each dash leaves a fading steel-grey streak on the ground;
  - a notch is a small pale tick-mark above the notched;
  - at the end, every notch opens in the same frame as a bright cut-line with a green poison bloom.
- **Sound:** whip-quick dash swishes; a tally of small "tick" sounds as notches land; at the end, one huge layered slice.
- **Hitstop:** none per dash; 8 frames on the final cut.

#### Stalker: Verge-Hunter

**One Arrow** (Strike, 0.9 s). One arrow, drawn to the ear and loosed down the screen. It pierces everything in a 30 m line, splits three times on the toughest things it passes, and kills ordinary things below 30%.
- *Horde:* a lane cut through the whole screen.
- *Boss:* one huge true strike (double crit damage).
- **Camera:** a 0.2 s look along the arrow's line (the camera turns 8° and leads toward it), then back.
- **Animation:** key pose at full draw, string at the ear, bow canted, eye down the shaft; the bow arm snaps forward on release; the follow-through is held 0.3 s.
- **VFX:**
  - the arrow trails a long, thin pressure wake that bends the air (shimmer) and raises dust in a line;
  - each split is a quick bright fleck;
  - anything struck kicks back.
- **Sound:** the long creak of the draw; a whip-crack release; a tearing sound down the line; impacts in sequence.
- **Hitstop:** 7 frames on the first impact.

**Pinning Rain** (Stand, 5 s). She looses into the sky and marks ground 12 m across where she aims. Arrows fall on it in a steady rain for 5 s, rooting what they strike for 0.5 s.
- *Defense:* what's in the field can't reach her.
- *Horde:* a killing field she drives them into.
- *Boss:* rooted again and again (0.2 s each on a boss).
- **Camera:** lifts 10° to show the field, and holds.
- **Animation:** key pose with the bow aimed at the sky and a fan of arrows on the string; she looses three times in quick succession, then plays normally.
- **VFX:**
  - the arrows fall as dark streaks with pale fletching glints (thin, never bars), thudding into the ground and staying planted until it ends;
  - the field's edge is only where the planted arrows stop.
- **Sound:** a rising whistle; a rain of thuds, dense and rhythmic.
- **Hitstop:** none per arrow; 3 frames on the first wave.

### 3.7 Modifiers (three per ultimate)

| Ultimate | Modifier lamps |
|---|---|
| The Long Cut | **Second Cut** (another sweep 0.3 s later, inside the 1.2 s), **Line of Morning** (the line burns 4 s), **Through the Wall** (the line runs 36 m, and Sundered is −40% on bosses) |
| Dawn in the Steel | **High Morning** (8 s), **Crescents Through** (crescents pierce everything), **Mending Light** (a kill by a crescent mends 0.5%) |
| Bell of the Morning | **Fourth Toll**, **Bell for the Dead** (lesser things flee 3 s after the last toll), **Healing Peal** (each toll mends 8%) |
| Sixty on the Wall | **Shield-Brothers** (the wall strikes out once a second), **The Wall Walks** (it moves with you), **Night Watch** (9 s) |
| The Butcher's Bill | **Running Tab** (the leftover chops can go on twice), **Wide Chops** (each chop strikes everything 2 m around), **Feast** (each kill mends 10%) |
| Butcher's Hour | **Overtime** (a kill adds 0.6 s), **Red Mist** (lesser things near you flee), **Not Today** (while it holds, you can't fall below 1 health) |
| Drag Them Under | **Deeper** (the hooks reach the whole screen), **Grinder** (the knot is shredded for a breath before the slam), **Hold Him** (a boss is pinned 3 s) |
| Storm on the Chain | **Second Length** (a second chain; the sweeps alternate), **Earthing** (each sky strike mends 1%), **Wide Lash** (sweeps reach 11 m) |
| Burns Twice | **More Embers** (eighteen), **Black Ice** (frozen things below half health shatter even without an ember), **Called Down** (every ember on the toughest frozen thing) |
| Hard Winter | **Deep Winter** (freezes after 1 s), **Thaw-Burst** (twice the burst), **Winter Keeps** (mend 2% a second while it holds) |
| The Branding | **Second Brand** (it brands again 1 s later), **Branded Deep** (the bursts are 50% wider), **The Eye** (the boss is branded three times) |
| The Drowned Moon | **Full Moon** (twice the motes), **Moonset** (it ends by bursting upward, 8 m around), **Silver Tide** (marks pass to three) |
| The Road's Toll | **Toll Doubled** (eighteen cuts, at the same length), **Last Cut** (the last blow kills below 40%), **Gone** (unseen for 3 s after) |
| Through and Through | **Deeper Notches** (each pass notches twice), **Wake of Blades** (the paths stay as Cutting Wake for 2 s), **Free Hands** (it lasts 8 s) |
| One Arrow | **Split Thrice More**, **Pinned to the Earth** (everything struck is rooted 2 s), **Through the Heart** (triple crit damage on a boss) |
| Pinning Rain | **Follow the Hunter** (the field moves with you), **Iron Rain** (arrows stun), **Thorned Rain** (Thornbloom grows where they fell) |

---

## 4. The new skill list

**Counts:**
- 16 new combat skills (two per type), each with two evolutions (32), and 4 new unions (one for each calling's hybrid): 52 new draft pieces.
- 16 ultimates (48 modifiers).
- 8 reflexes (six of them today's pressed arts) and 4 dash forms (today's Kin arts).
- 4 Flare great blessings.
- 4 new tags (**Heavy**, **Shield**, **Twin**, **Hook**) and one new status (**Bound**).

With today's 26, that's **42 combat skills**: enough for eight types of three signature skills each, with every skill wanted by at least two builds (SKILLS_DESIGN principle 5). Synergy over count: each new skill was chosen for what it joins, not to fill a slot.

| Skill | Type it feeds (also wanted by) | Tags | Role | What it does | Path(s) | Evolutions |
|---|---|---|---|---|---|---|
| **Sunder** | Sunderer (Bulwark via Sword-and-Board) | Melee, Steel, Physical, Area, Heavy | grip, clear | Slow 220° cleave; every fourth swing a heavy line 7 m | Steel and Blood, Dawn's Light | *Skybreaker* (the heavy line runs the screen's width), *Sunlit Edge* (every swing sears, and seared things burst) |
| **Groundbreaker** | Sunderer (Chainbound) | Melee, Physical, Area, Heavy | control | Every 5 s a crack runs to the densest pack within 10 m, and the ground heaves (stun 0.6 s) | Steel and Blood | *Faultlines* (three cracks), *The Deep Heave* (heaved things are thrown, and land as blows on others) |
| **Rebuke** | Bulwark (Sunderer) | Holy, Nova, Shield | retaliation | Each block strikes the blocker and three near it with holy light | Dawn's Light | *Righteous Answer* (rebukes chain), *Shield of Morning* (rebukes leave a barrier) |
| **Watch Bell** | Bulwark (Chainbound, Verge-Hunter) | Aura, Holy, Shield | taunt, defense | Every 6 s a toll draws everything within 8 m to you for 2 s; 2% barrier for each | Dawn's Light, the Host | *Curfew Bell* (drawn things are slowed and take more), *Alarm Bell* (tolls also stun) |
| **Carve** | Butcher | Melee, Steel, Physical, Twin | grip, single-target | Three fast chops on the nearest every half second, each bleeding | Steel and Blood | *Butcher's Block* (every tenth flurry is a cleave all around), *Red Ribbon* (chops send bleeding arcs 4 m) |
| **Hurled Cleaver** | Butcher (Chainbound) | Thrown, Projectile, Steel, Physical | reach | Every 3 s a cleaver flies at the farthest bleeding thing within 12 m and returns | Steel and Blood, the Hunt | *Twin Cleavers* (two, crossing), *Gibbet* (it hooks on the way back) |
| **Chain Lash** | Chainbound (Butcher) | Melee, Steel, Physical, Area, Hook | grip, gather | 7 m whip arc; the farthest thing struck is hooked and dragged in | Steel and Blood, the Storm | *Scourge* (two lashes, crossing), *Live Wire* (the lash shocks, and the shock runs the chain) |
| **Anchor** | Chainbound (Bulwark, Kindler) | Area, Physical, Hook, Zone | control | Every 7 s an anchor lands in the thick of it; everything 5 m around is Bound to it for 3 s, then yanked together | the Storm, the Host | *Sea Anchor* (it drags its catch around you), *Storm Anchor* (it calls lightning on the knot) |
| **Pyre Line** | Kindler (Verge-Hunter) | Spell, Fire, Zone, Area | wall, area denial | Every 6 s a line of fire 8 m long rises between you and the densest pack | the Pyre | *Firestorm Line* (the wall rolls forward), *Hearth Line* (standing near it mends) |
| **Rime Field** | Kindler (Moonweaver, Chainbound) | Spell, Frost, Zone, Area | control, setup | Every 7 s the ground under the thickest pack frosts; what stays 1.5 s freezes for 2 s | the Long Winter | *Hard Frost* (frozen things shatter at half health), *Ford-Water* (the field follows you) |
| **Moonwell** | Moonweaver (Kindler) | Spell, Arcane, Zone, Projectile | turret | A well of moonlight hangs where it's cast for 8 s, firing motes at what passes within 7 m; two at most | the Weave | *Moonpool* (wells mark what they strike), *Wellspring* (three wells, and the motes split) |
| **Lantern-Man** | Moonweaver (Verge-Hunter) | Spell, Arcane, Projectile, Dot | roaming area | A slow moonfire wisp drifts out along your path, flaring at three things every 0.3 s and marking what it burns | the Weave, the Grave | *Lantern-Men* (it splits in two when its target dies), *Will-o'-the-Wisp* (it follows you and draws foes to itself) |
| **Twin Fangs** | Roadknife | Melee, Steel, Physical, Twin | grip, burst | After each dash, the two nearest are cut twice; within the Opening every Fang strikes true | the Hunt | *Viper's Fangs* (each cut stacks poison twice), *Wolf's Fangs* (Fangs strike the three nearest) |
| **Cutting Wake** | Roadknife (Verge-Hunter, any dash build) | Physical, Steel, Zone, Trap | dash payoff | Each dash leaves hanging blades along its path for 1.5 s, cutting and poisoning what crosses | the Hunt, the Wild | *Razor Wake* (the blades fly at the nearest when it ends), *Smoke Wake* (it leaves smoke that hides you) |
| **Heartseeker** | Verge-Hunter (Moonweaver) | Projectile, Ranged, Physical | single-target, pierce | Every 3 s a heavy arrow at the toughest within 20 m, piercing everything in line; true on the prey | the Hunt | *Heart of the Pack* (it splits on a kill), *Thorn Heart* (it plants Thornbloom where it stops) |
| **Snare-Line** | Verge-Hunter (Roadknife, Kindler) | Trap, Nature, Area | control | Every 6 s a line of snares falls across the thickest approach 6 m ahead; what steps in is rooted 1.5 s | the Wild, the Hunt | *Bramble Line* (the snares become thorns that poison), *Deadfall* (logs fall on what's rooted) |

**The four unions** are the hybrid's payoff at night, and they free a slot as unions do:
- **The Gate and the Sword** (warden): Sunder (*Sunlit Edge*) + Rebuke (*Shield of Morning*). A heavy blow every second that rebukes all around.
- **Gibbet Chain** (reaver): Hurled Cleaver (*Gibbet*) + Chain Lash (*Scourge*). A cleaver on a chain, whirling, hooking and bleeding.
- **Moon on the Ice** (arcanist): Moonwell (*Moonpool*) + Rime Field (*Hard Frost*). Wells over frozen ground whose motes shatter what's frozen.
- **Blade and Briar** (stalker): Cutting Wake (*Smoke Wake*) + Snare-Line (*Bramble Line*). Every dash lays a line of thorned snares.

All of these names, and the evolutions' lines, go to the story lead for the valley's voice and Act 1 safety, as every name in SKILLS_DESIGN did. The names most likely to change are Roadknife, Burns Twice, The Branding and Pinning Rain.

---

## 5. Arenas and endless

**The nights (the table's arenas).** The draft is as it was: from nothing, open to everyone, gone at dawn. What changes is who you are while you draft:
- the Lamps' rules wake on whatever the ember brings, so your Sunder lamps are waiting when Sunder comes (at night, sizes run at a quarter, §2.10);
- your deepest road leans its type's cards;
- the Flare starts empty and fills from the fight;
- the four Flare great blessings sit among the others, dealt by role.

A warden who drafts Volley and Moonbrand all night plays a full ember build: possible, as the owner wants. A warden who drafts Sunder, Groundbreaker and Dawnpulse finds them already shaped by thirty lit lamps, which is easier and better.

**Story fights.** The same, but the Flare starts at half, because the fights are ten to fourteen minutes. Story bosses are written to have a Flare moment: a phase where a Flare breaks a channel or a wall (combat's boss briefs).

**Maps (the atlas).** Everything applies in full: the Lamps, gear, day skills at their ranks, the Flare. The Flare carries between a map's areas. Two new map mods are build checks, read on the chart:
- **Smothered** (prefix): the Flare fills 30% slower.
- **Bright** (suffix, weakening the survivor): a Flare cast mends nothing.

**Endless (past the boss, the long night).** Truly endless means the power must keep growing as the horde does:
- Every five minutes past the half hour, the Flare **grows a rank**. Its damage climbs with no cap. Its size grows until it fills the screen and then stops, so it stays readable.
- The kill fill's cap stays at +1 a second, so danger still fills the meter faster than killing does, and the deep night's danger makes Flares come often.
- **Banked Flame** (two charges) comes into its own: one Flare spent on a close call, and another ready.
- Honing (SKILLS_DESIGN §8.5) and the Flare's ranks are the open axes, so the hundredth minute still has something growing.

---

## 6. Build examples

### Warden

1. **The Wall (simple).** A Bulwark following the glow. She carries Oathblade, Rebuke, the Watch Bell and Judgement Disc, has Mortar and Planted lit, and carries Bell of the Morning.
   - *How it plays:* walk into the thickest press and stand. The bell drags them in, every block rebukes, and at ten stones the wall answers all around her.
   - *When it goes wrong:* three tolls stop the screen and mend her.
2. **Weight of the Morning (planner).** A Sunderer with the blue lamp **Weight of the Oath**: every swing is a heavy line, slower than anything can fix, and never a true strike.
   - *The links:* **Dawn Rhythm** fires Dawnpulse on heavy blows (at most every 1.5 s, which is now about every swing). **Burning Edge** makes the lines sear, and **Morning in the Steel** bursts seared things on the next heavy blow. Each slow swing sears, bursts and pulses dawn.
   - *Holding her ground:* **Hold Fast** in the hearth keeps her planted, and at night Hold the Crossing doubles down on standing still.
   - *Her Flare:* The Long Cut with **Through the Wall** opens bosses' armor for the whole build.
3. **Sword-and-Board (hybrid).** The bridge's blue lamp lets her carry a greatsword and a shield.
   - *The links:* **Shield Swing** lets heavy blows lay stones, and **Bearer of Blows** stores everything blocked for the next Rebuke. Across the **Duelist's Road**, **Parry** turns perfect dashes into stones.
   - *Her Flare:* Bell of the Morning with **Healing Peal** is the reset.

### Reaver

1. **Red Work (simple).** A Butcher: Carve, Hurled Cleaver and Axe Gyre, with Deep Frenzy and Open Vein lit, carrying Butcher's Hour.
   - *How it plays:* wade in and let Frenzy climb.
   - *When the bar drops:* the Hour turns the fight around.
2. **Lightning Rod (planner).** A Chainbound with **The Long Chain** (melee reaches 3 m further and hooks) and **Lightning Rod** (storm strikes Bound things first, and harder).
   - *The links:* Iron Palms with **Iron Reach**, plus Anchor, plus Arcweb at night. Hook and anchor the pack into a Bound knot, and every storm skill hits all of it at once.
   - *Across the Night Road:* **Lightning Leaps the Chain** runs every bolt through every chain.
   - *Her Flare:* Storm on the Chain with **Earthing** keeps her alive.
3. **The Bill Comes Due (hybrid).** The bridge's **Cleaver on a Chain** makes the cleaver drag bleeding things in. **Red Chain** makes Bound things bleed, and **Always Bleeding** keeps her fighting hurt at all times.
   - *The price:* her life is held at half, and everything mended above it is lost.
   - *Her Flare:* The Butcher's Bill, where every tenth of health missing is another chop, and each chop mends. It's the build's payoff and its life-saver.

### Arcanist

1. **Fire and Ice (simple).** A Kindler: Cinderfall, Pyre Line and Rime Field, carrying Burns Twice.
   - *How it plays:* freeze the pack, drop fire on it, and watch it shatter.
2. **Crowded Sky (planner).** A Moonweaver with:
   - **Crowded Sky:** two more projectiles, each seeking a different thing;
   - **Silvered** and **Moon-Drawn:** marks pass to two on a death, and motes seek the marked;
   - **Moonfire:** a passed mark burns;
   - two Moonwells.

   At night, Second Reading fires everything at once, and a single kill passes marks across the screen in a chain. The Drowned Moon with **Silver Tide** turns the end of a night into a silver flood.
3. **The Ledger (hybrid).** The bridge's blue lamp rewards alternating schools: Rime Field, then Lantern-Man, then Cinderfall, then Seeking Motes, each 30% harder for the one before.
   - *The links:* **Two Schools** makes the lanterns flare twice as often over frozen ground.
   - *Her Flare:* Hard Winter with **Deep Winter** freezes the screen, and the moon spell after it is the Ledger's payoff.

### Stalker

1. **Hunter's Line (simple).** A Verge-Hunter: Volley, Heartseeker and Snare-Line, with the Mark Prey reflex, carrying One Arrow.
   - *How it plays:* kite. The snares hold the front, and Heartseeker spears the prey and everything in front of it.
2. **Never Still (planner).** A Roadknife with:
   - **Light Step:** three dashes;
   - **Never Still:** they come back 40% faster, but standing still halves her blows;
   - **Through, Not Around:** each dash cuts and refunds dash;
   - Twin Fangs firing on every dash, and Cutting Wake.

   She dashes through packs constantly. **Adder's Patience** gives up true strikes for unending poison stacks, so Opening's crits are traded for a poison that never stops. The **Smoke Bomb** reflex fires on every perfect dash. Through and Through with **Wake of Blades** is the build turned up to full.
3. **Firebreak (cross-calling).** A bow-and-blade build with **Close and Far**, then across the **Firebreak** into the arcanist's quarter.
   - *The links:* **Fire Arrows** sets Volley alight through burning ground. At night she drafts Firepot and Cinderfall (off-calling, and fully allowed) to lay that ground.
   - *Her Flare:* Pinning Rain with **Thorned Rain** pins the burning pack.
   - *Why it works:* it's possible because the board connects, and it costs because the crossing is far from her hearth.

---

## 7. Implementation: phases, costs, risks

Sizes are in lead sessions. One session is about 300k tokens of a `su-lead-high`, with workers and runners under it and max judges for every look. **Hero order:** every clip is counted for both bodies. Whichever hero the beta ships first gets each clip first (the coordinator's call; the owner's direction is a male hero to start), and the other body follows in the same phase.

| Phase | What | Code | Art | Animation | VFX and sound | Who | Size |
|---|---|---|---|---|---|---|---|
| **1. Systems** | The Lamps' data (`Content/Lamps.cs`, `data/content/lamps.json`); lamps from levels and story fights; respec and layouts; the night rule and leans; the new tags and Bound; reflexes (arts become triggers); dash forms (the Kin onto the dash with waits; `ArtBook` migration, all four facets kept); the Flare's meter, window and clutch; the `Act` renames in two steps, with the bindings and save migration (a full lamp refund); the harness taught types, lamps and Flares; tests | large | none | none | none | combat (systems) lead + workers | 3 |
| **2. The beat and four Flares** | The shared beat (time, grade, camera push, hitstop, last blow), then one Flare per calling on grips we already have: **Bell of the Morning** (sword and shield, the warden's starting Strike), **Butcher's Hour** (axes; proves the Stand grammar cheaply), **Burns Twice** (staff), **The Road's Toll** (daggers) | small | none | 4 Flare clips × 2 bodies | 4 Flares, the beat | experience (camera, time), skills VFX (look, sound), animation | 3 |
| **3. The Lamps screen and the HUD** | A UI design brief (a board of lamps over the live world, under our panel rules; pad navigation along roads, with the shoulders jumping between regions) and UI art (lamps, blue lamps, roads); the Flare as the instrument's centerpiece; the reflexes' wait arcs | medium | lamp glyphs, board | none | the full Flare's breath | UI design (su-lead-max brief), UI art | 2 |
| **4. New grips** | Greatsword, hooked chain and longbow as items and props (a two-handed rule in `Items`; twin blades reuse the daggers, twin axes the axes); clips per grip (idle, run, two swings, heavy, hit), plus the one-handed greatsword set for Sword-and-Board | small | 3 props | about 22 clips × 2 bodies | swing trails | loot (items), outfits or arena art (props), animation | 3 |
| **5. New skills** | 16 skills, 32 evolutions, 4 unions: logic, harness balance, look and sound, names from story | medium | none | none | 52 pieces | combat, skills VFX, story (names) | 4 to 5 |
| **6. The other twelve Flares** | As phase 2, including the spectral Watch bearers of Sixty on the Wall | small | Watch bearers | 12 Flare clips × 2 bodies | 12 Flares | as phase 2 | 5 |
| **7. Tuning and teaching** | A balance sweep (types, lamps and Flares at tiers 1 to 4 and in endless); the first-hour teaching (creation's type cards, the first lamp, the first Flare); the codex's text | small | type cards' clips | none | none | combat, experience, story | 1 to 2 |

**Acceptance** (the harness and the judges):
- Every type is within ×1.35 of the median at tiers 1 to 4 (the paths' band).
- On-calling is at most ×1.25 over the same skills off-calling.
- A full board at night is within ×1.25 of an empty one.
- Flare timing: the first by about 2 minutes, then one every 60 to 90 s at night, and two or three in a boss fight. Flares do 15 to 25% of a boss's damage.
- Every Flare is judged at 1:1 in a packed horde and on a boss, against §3.5's laws.

**Risks:**
1. **Animation is the long pole.** That's 16 Flare clips and about 22 grip clips, all twice over. Phase 2 proves the beat on grips we already have.
2. **Performance.** Sixteen Flares over 300 creatures. The rendering lead budgets each Flare (particles, lights, overdraw) before it's built.
3. **Readability.** Flares must never hide a danger mark. Enemy marks draw on top, and Flares hold their light below the knee (§3.5).
4. **The night's balance.** The Flare is new power at night. The ember curve (SKILLS_DESIGN §11) is re-measured, and story bosses' health may rise.
5. **Opacity and trap lamps.** There are 360 lamps of text. One line each, the "feeds" glyphs, dimming, Light my way and the free respec answer it.
6. **Migration.** Saved arts become dash forms with all their facets, the bindings move, and existing saves get a full refund of lamps.
7. **Names and tone.** About 400 new names. The story lead checks each one for the valley's voice and for Act 1 safety.
8. **Scope.** If tokens or time press, phases 1 to 3 alone give the owner class identity and four Flares to play. The rest can follow one calling at a time.

---

## 8. Open questions for the owner

**Decided (the owner, 11 October 2026): "go with all 8 recommendations".** All eight below are answered as recommended. Phase 1 (systems) starts now.

1. **Should ultimates be locked to the calling?** *Recommend yes:* they're the identity, and the only hard lock. Everything else stays open to everyone.
2. **Free respec by day at any town lamp-post, with two saved layouts?** *Recommend yes:* planning is only fun when trying is free.
3. **Pick the type at creation?** *Recommend yes,* for the starting grip, the road's mechanic and the first Flare, but never as a lock: the Lamps decide what you become.
4. **Q / right-click becomes the Flare, the draught stays on R, and the movement art rides the dash on its own wait?** *Recommend yes.*
5. **The names "the Lamps" (the tree) and "the Flare" (the ultimate)?** *Recommend yes,* with the story lead checking the voice.
6. **About 50 lamps at the very end (levels, story bosses, the atlas), with no open-ended climb?** *Recommend yes:* it keeps §14.1's reasoning.
7. **Build first: the systems, plus one Flare per calling** (Bell of the Morning, Butcher's Hour, Burns Twice, The Road's Toll), so you can play the look before the rest? *Recommend yes.*
8. **Keep the 0.22 s freeze on every Flare, even in endless?** *Recommend yes:* it's the dopamine, and a setting can shorten it.

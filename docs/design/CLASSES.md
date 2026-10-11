# Callings: two ways each, the Lamps, and the Flare

The classes plan: what makes the four callings different, the skill tree, the ultimates, the new skills, and how it all reaches the nights, the maps and endless. **A plan only: no game code until the owner approves it.** Classes design lead, 11 October 2026. Research notes: `docs/design/notes/classes_*.md`. The Warden's tree, drawn: `docs/design/classes_warden_lamps.svg`.

---

## For the owner (one page)

**Two ways per calling.** The warden is a *Sunderer* (greatsword: slow, huge, staggering blows) or a *Bulwark* (sword and shield: walk in, let them hit you, and they die on it). The reaver is a *Butcher* (twin axes, bleeding, fighting best hurt) or *Chainbound* (a hooked chain that drags the horde into knots, with lightning running down it). The arcanist is a *Kindler* (fire and frost on the ground: freeze them, then shatter them) or a *Moonweaver* (moonlight and lightning that hunt on their own). The stalker is a *Skirmisher* (twin blades, dashing through the crowd) or a *Verge-Hunter* (longbow, far away, pinning the front).

**The tree is called the Lamps.** It's one dark map, and each calling owns a quarter of it. You light one lamp a level (and more for story bosses). Each type is a road, the two roads meet at a bridge for hybrids, and your roads run on into your neighbors' quarters. A new player clicks the glowing lamp and it just works; a planner hunts the blue lamps (big rules with a price) and the lamps that make two skills feed each other. Anyone can walk anywhere; home is closer. Respec is free in town.

**Q / right-click becomes the Flare: your ultimate.** It fills fastest when you're in trouble (blows taken, perfect dodges, dropping low), you're untouchable while it plays, and casting it near death heals you. Each calling has four (a big instant *Strike* and a timed *Stand* per type), and each has three lamps that reshape it. Every one gets a frozen key pose, hitstop and a staged look. The movement art moves into the dash.

**Cost:** 16 new skills, 16 ultimates, 3 new weapons; animation is the long pole. **First:** the systems and one ultimate per calling.

---

## 0. What exists, and what this changes

| Today | After this plan | Why |
|---|---|---|
| Combat skills fire themselves; hands are the dash (two charges), one **art** (Q / right-click) and the draught (R) | The same, but Q / right-click is the **Flare** (ultimate). The draught stays on R (the `Act.Ultimate` that means the draught today is renamed `Draught`) | The owner: "it dosn't HAVE to be movement". Two dash charges are already two movement buttons |
| Each calling starts with a movement art (`Abilities.Kin`: bull_rush, grapple, mirror_step, vault) | The Kin becomes the calling's **dash form**: the dash itself turns into a bull rush, a hooked chain, a mirror step or a vault, keeping its i-frames and perfect window. The other movement arts (Leap, Blink, Sprint, Wraith Walk, Cinder Trail, Echo Step) are dash forms anyone can learn from manuals, as today | Nothing is thrown away: `ArtBook`'s ranks and facets carry over to the dash. And the owner's crowd note ("a brief knock-aside on a dash") gets four calling-flavored answers |
| The calling's other arts (Shield Bash, Bulwark, War Cry, Time Slip, Mark Prey, Smoke Bomb) are pressed | They become **reflexes**: lamps that fire the art on their own when something happens (a champion closes in, a big blow lands, a perfect dash) | Our genre fires itself. Grim Dawn's procs ("on block: ...") are the best version of that in an ARPG (`notes/classes_grim_dawn.md`) |
| 26 combat skills in 10 paths; the night's draft (`SKILLS_DESIGN.md`) | **Unchanged and still open to everyone.** 16 new combat skills join it, two per type. The Lamps change *how* drafted skills behave, never *which* ones you may take | SKILLS_DESIGN §4 rejected a tree that chooses the night's skills ("the build should be discovered in the run"). The Lamps don't: they decide what your Sunder does when the ember brings it |
| Level cap 30, no paragon (§14.1); day skills rank with level; four attributes | **Unchanged.** Lamps come from levels (29), story fights (about 13) and the atlas (8, finite): about **50 lamps** at the end of everything | §14.1's reason holds: an open-ended climb buries gear and the ember |
| The calling's paths lean the draft ×1.3; the calling's own great blessing | Kept. The road you've walked furthest leans its type's skills a little more, and its grip skill comes in the first draft | "Certain things are easier" |

---

## 1. Two ways per calling

Each type is built on a **grip** (what's in the hands, so what the clips and the silhouette are), a **mechanic it alone builds around**, and a **minute-to-minute loop**. Any calling can hold any grip (it asks the attribute, `SkillBook.Need`); the Lamps make one's own grip better.

### The warden: hold the line

| | **Sunderer** (greatsword) | **Bulwark** (sword and shield) |
|---|---|---|
| Fantasy | The Watch's old two-handed blade, carried by someone who has stopped retreating | One shield on a wall built for sixty |
| Grip skill | **Sunder** (new): a slow 220° cleave; every fourth swing is a **heavy** overhead that splits the ground in a 7 m line | **Oathblade** (exists), with the shield blocking |
| Built around | **Heavy blows**: stagger, armor broken (**Sundered**), holy fire riding the edge | **Block**: blocks build **Ward**; at ten the shield answers on its own. Barrier, retaliation, hallowed ground |
| Minute to minute | Wade to the edge of the horde, face where the line should fall, and let each heavy blow crack a lane open. Champions stagger and break | Walk *into* the thickest press and stand. The Watch Bell drags them onto you, every block rebukes, and the crowd dies against the shield |
| Its skills | Sunder, **Groundbreaker** (new), Dawnpulse, Cleaver | Oathblade, **Rebuke** (new), **Watch Bell** (new), Judgement Disc, Hallowed Ground |
| Why it feels different | You choose where the blow falls. Offense by size, with a weight you feel in every hitstop | You choose where to stand, and the horde chooses to die on it. Offense by being hit |

### The reaver: take it out of them

| | **Butcher** (twin axes) | **Chainbound** (hooked chain) |
|---|---|---|
| Fantasy | A slaughterer who fights best bleeding | The reaver who took the chain off, and kept it |
| Grip skill | **Carve** (new): a fast three-chop flurry on the nearest, every half second; each chop bleeds | **Chain Lash** (new): a 7 m whip arc; the farthest thing struck is hooked and dragged 3 m in |
| Built around | **Frenzy** (hits stack attack speed), bleed, **Blood Up** (low health is strength), drinking life | **Bound** (new status: tethered, can't move away, takes more from area); gather, then burst. Lightning runs along chains |
| Minute to minute | In the middle of it, health swinging: Frenzy climbs, bleeds stack, kills mend, and a low bar is when you hit hardest | At chain's length: hook the stragglers, anchor the pack, yank it into one knot, then break the knot with storm |
| Its skills | Carve, **Hurled Cleaver** (new), Axe Gyre, Reaving Arc | Chain Lash, **Anchor** (new), Iron Palms, Arcweb, Thunderhead |
| Why it feels different | Close, fast, frantic, risky; the screen is red and so is your bar | Mid-range control. You arrange the horde before you kill it; it feels like herding |

### The arcanist: some of them keep ledgers

| | **Kindler** (ember staff) | **Moonweaver** (wand) |
|---|---|---|
| Fantasy | Burns ember the way the whole valley does, and carries the ford's cold | Moonlight and lightning, sent to find their own way |
| Grip skill | **Cinderfall** (exists) | **Seeking Motes** (exists) |
| Built around | **Ground**: burning fields, frozen fields, and **Thermal Shock** (fire on the frozen shatters them) | **Many lights**: projectile count, seeking, **marks that pass on** when the marked die, lightning that forks |
| Minute to minute | Lay the field and stand behind it: a wall of fire between you and them, frost under the pack, and when it freezes, drop fire on it | Keep moving. The motes do the aiming, the wells guard where you were, the sparks wander out, and every death passes the mark on |
| Its skills | Cinderfall, **Pyre Line** (new), **Rime Field** (new), Firepot, Rimeshard, Hoarfrost | Seeking Motes, **Moonwell** (new), **Wandering Spark** (new), Moonbrand, Arcweb, Thunderhead |
| Why it feels different | It's about *where*: placement and timing (freeze, then shatter) | It's about *how many*: streams, chains and marks, always on the move |

### The stalker: never there when it lands

| | **Skirmisher** (twin blades) | **Verge-Hunter** (longbow) |
|---|---|---|
| Fantasy | The road's knife-fighter: through the crowd and out before it closes | The Verge's hunter: far off, patient, never missing |
| Grip skill | **Twin Fangs** (new): quick double cuts on the nearest; for 2 s after a dash every Fang strikes true (**Opening**) | **Volley** (exists), loosed from a longbow |
| Built around | **The dash**: dashing through things cuts them, perfect dashes throw smoke, poison stacks | **Distance**: blows from beyond 8 m, pierce, roots (snares), marked prey, spirit beasts |
| Minute to minute | Dash *through* packs, never round them. Each pass leaves a wake of hanging blades, each Opening is a burst of crits, then out | Kite at range. Snares pin the front, Heartseeker spears the toughest and everything in line, and the pack never reaches you |
| Its skills | Twin Fangs, **Cutting Wake** (new), Knifestorm, Gale Chakram, Blightfield | Volley, **Heartseeker** (new), **Snare-Line** (new), Thornbloom, Spirit Herd |
| Why it feels different | Its dash is its weapon: going in | Its dash is its escape, and distance is its damage |

**Rule for every new skill:** a combat skill never moves the survivor. Only the dash and the Flare move her, so the player always owns where she is.

---

## 2. The Lamps (the tree)

### 2.1 Why a board of lamps

"Lamps are lit. Stay where they reach" is the valley's evening call. The tree is drawn as a dark map of the valley's roads, and **you light lamps along them**: each lit lamp throws light on the next ones. Lamps that change the rules burn **blue** (ember burns blue only in an iron). The words on screen stay plain: "3 lamps to light", "Blue lamp", "Road of the Sunderer".

### 2.2 Layout

One shared board, a ring of eight roads round four homes.

```
                Moonweaver ── Storm Road ── Chainbound
               /                                     \
         Kindler                                    Butcher
           |      ARCANIST                REAVER       |
     Firebreak                                      Shambles
           |      STALKER                 WARDEN       |
      Verge-Hunter                                  Sunderer
               \                                     /
                Skirmisher ── Duelist's Road ── Bulwark
```

Each calling's **quarter** has:
- **The hearth** (12 lamps), where you start: the dash form (the Kin) and its three lamps, the calling's two reflexes and their upgrades, two Flare lamps, and two blue lamps (the calling's own, and **Banked Flame**).
- **Two roads** (about 31 lamps each), one per type: the entry lamp, six small lamps, nine **skill lamps** (three each for the type's three signature skills), five **notables**, two **blue lamps**, and two **ultimate lamps** with three modifiers each.
- **The bridge** (6 lamps) between its own two roads: the hybrid's lamps and one blue lamp.

Between neighboring quarters is a **crossing** (6 lamps, shared): two attribute lamps, two small lamps and two notables that join both sides' mechanics. The crossings are the **Shambles** (Sunderer and Butcher: heavy blows and bleeding), the **Storm Road** (Chainbound and Moonweaver: chains and lightning), the **Firebreak** (Kindler and Verge-Hunter: burning ground and arrows), and the **Duelist's Road** (Skirmisher and Bulwark: blocks and perfect dashes).

The board holds about **344 lamps** (four quarters of 80, plus 24 on the crossings). At the end of everything a survivor has about **50**. A full road plus the hearth is about 43, so every survivor chooses what to leave dark.

**Depth.** A road's ultimate Strike needs 3 lamps lit on that road, its notables 6, and its blue lamps and its Stand 12. This is Grim Dawn's mastery bar and Last Epoch's mastery threshold: going deep at home is strong, and dipping into the other road costs real lamps.

### 2.3 Lamp kinds

| Kind | Looks like | What it does | Rule |
|---|---|---|---|
| **Small** | a wick | a number tied to *two* tags or a condition ("+12% heavy-blow damage to staggered things"), or +2 to an attribute | Never a bare "+n% damage" (D4's flat nodes, `notes/classes_diablo.md`) |
| **Skill lamp** | a lamp with the skill's glyph | changes one skill (Last Epoch's skill trees, three lamps per skill) | Wakes when you carry the skill: by day, or when the night's draft brings it |
| **Notable** | a lantern, named | one rule that joins two things ("blocks count toward ...") | Says which skills it feeds |
| **Blue lamp** | a blue flame in an iron | a big rule **with a price** (PoE's keystones, Grim Dawn's transmuters) | 28 on the board, named, never a plain upgrade |
| **Reflex** | a lamp with the art's glyph | fires a calling art on a condition | Each has an internal wait, shown on the HUD |
| **Dash form** | a boot-mark | turns the dash into the calling's movement art | One form at a time, chosen in the book |
| **Ultimate** | a great lantern | learns a Flare | |
| **Ultimate modifier** | a small lantern by it | reshapes that Flare | Any number, each one lamp |

### 2.4 Where lamps come from, and respec

- **Levels:** one lamp a level, 2 to 30 (29). Today's attribute point a level stays.
- **Story fights:** one lamp for each story boss beaten the first time (Act 1 has four; about 13 over the three acts). The lamp is lit as the dawn comes: a story moment, not a menu.
- **The atlas:** eight lamps for atlas milestones (the experience lead places them), finite. No paragon: §14.1 stands.
- **Respec is free, by day, at any lamp-post in a town** (lamps go out one at a time or all at once), plus **two saved layouts**. Never mid-night or mid-map. Why free: planning is only fun if trying is free (D3's and Last Epoch's lesson; PoE's regret orbs and Grim Dawn's unrefundable bar are the failure, `notes/`).

### 2.5 Click and have fun: the new player

1. **At creation**, after the calling, pick its type from two cards, each with a five-second clip of the type playing and one line ("Slow, huge blows that split the ground"). It sets the starting grip, lights the road's entry lamp and gives that road's Strike ultimate. It's never a lock.
2. **Each level** the board opens on your quarter with **the next suggested lamp glowing** along your road. Click it, or anything beside a lit lamp. A toggle, **Light my way**, lights the suggested lamp for you every level (D4's and Last Epoch's recommended path).
3. **Every lamp's text is one line** and shows the glyphs of the skills it feeds. A lamp that feeds nothing you carry is dimmed and says so: no trap choices.
4. **The first blue lamp** comes at about level 12, by when the player knows their type. It's offered with a one-line price in red.

The new player's experience is: pick the look you like, click the glowing lamp, and your skills visibly change (Sunder's arc gets wider; the heavy blow splits two cracks).

### 2.6 Plan for hours: the planner

The depth is in **links between systems**, not in bigger numbers:
- **Blue lamps that change a skill's mode** (Rain Archer: Volley falls from above instead of flying), and **blue lamps that change your body's rules** (Weight of the Oath: every blow is heavy, slower, and can never crit).
- **Notables that make one skill feed another** (Dawn Rhythm: Dawnpulse fires on a heavy blow instead of on its timer), and **reflexes chained to them** (a heavy blow on a champion triggers Shield Bash, whose stun triggers ...).
- **The bridge and the crossings:** hybrids inside a calling (Sword-and-Board: a greatsword and a shield at once) and across (the Duelist's Road: a perfect dash counts as a block).
- **The Flare's lamps:** three modifiers per ultimate, plus the hearth's Flare lamps and Banked Flame.
- **Gear that touches the board:** a new Legendary family, **lamp-lit** items, each lighting one blue lamp anywhere on the board (PoE's Thread of Hope; Grim Dawn's skill-granting items). Corran's Sword is the model. Loot owns the list.
- **The night's draft on top:** statuses, unions and discoveries (`SKILLS_DESIGN.md` §5) combine with what your lamps make of each skill.

### 2.7 Anyone can do anything, but home is easier and better

- **Any skill, any night:** the draft offers everything to everyone, as now. A warden can draft Moonbrand and it works at full ember power. It just has no warden lamps feeding it.
- **Any grip, by day:** any calling can hold a longbow if it has the Finesse. The crossings' attribute lamps and gear provide it.
- **Any road:** walking into a neighbor's quarter costs the lamps between. The next quarter over is affordable (the crossing is 6 lamps). The far side of the board isn't, at 50 lamps, and that's on purpose (PoE).
- **Not ultimates:** they are the calling's identity, the one hard lock, like the calling's own great blessing. (Open question 1.)
- **Measured:** on its own roads a type plays at most ×1.25 better than the same skills drafted off-calling. "Mostly possible" stays true, and the harness holds it (§7).

### 2.8 The warden's quarter in full

Drawn in `docs/design/classes_warden_lamps.svg`. The other callings follow the same shape (§2.9).

**The hearth (12).**
- Start: **The Warden's Oath** (the dash is **Bull Rush**: a 6 m charge behind a barrier of 15% of health; what's in the way is thrown aside; a champion stops it, stunned). Dash form lamps: **Iron Hide** (barrier 25%), **Pile Driver** (the rush ends in a slam that stuns 3 m round), **Unbroken** (each thing struck adds 2% to the barrier).
- Reflex **Shield Bash**: "When three or more things, or a champion, are within 2.5 m: bash. They're thrown back and stunned 1.5 s, and a channel breaks. Every 7 s." Upgrades: **Concussion** (stun +1 s), **Shield Wall** (8% barrier per thing struck, to 40%).
- Reflex **Bulwark**: "A blow that takes a seventh of your health or more plants you for 3 s: blows cut by 65%, arrows turned back. Every 20 s." Upgrade: **Rallying Stand** (mend 4% a second while planted).
- Flare: **Kindled Oath** (blows taken fill the Flare 20% faster) and **Last at the Crossing** (a Flare cast below a third of health also gives a barrier of 30%).
- Blue: **Hold Fast**: "You can't be thrown, stunned or slowed. Your dash is 30% shorter." Blue: **Banked Flame** (every hearth has it): "Hold two Flares. Each fills 30% slower."

**The Sunderer's road (31).**
- Entry **Two Hands**: heavy skills +10% area.
- Small: heavy blows +12% to staggered things; +8% area to heavy and nova skills; +2 Might (twice); staggered things take 10% more holy; each heavy blow landed in the last 3 s gives +1 armor (to +10).
- Skill lamps. **Sunder**: *Wide Swing* (arc 300°), *Third Blow* (every third swing is heavy), *Burning Edge* (the heavy line sears). **Groundbreaker**: *Twin Cracks* (two cracks, splayed 30°), *Fault Line* (cracks run 14 m), *Upheaval* (lesser things are thrown up for 0.8 s and take 30% more while airborne). **Dawnpulse**: *Dawn Rhythm* (it fires when you land a heavy blow instead of on its timer, at most every 1.5 s), *Wider Morning*, *Searing Light*.
- Notables: **Stagger** (heavy blows stagger ordinary things 0.4 s; champions fill a stagger bar and break for 1.5 s), **Sundered** (heavy blows break armor: Sundered things take 20% more from heavy blows for 4 s), **Momentum of the Blade** (a swing that kills three makes the next one 25% faster), **Morning in the Steel** (heavy blows on seared things burst in holy light 3 m round), **Rooted Stance** (after 1 s standing still, heavy blows are 20% wider: it pairs with Hold the Crossing).
- Blue: **Weight of the Oath**: "Every blow you strike is heavy: 40% slower, twice as hard, and always staggers. You can never strike true (crit)." Blue: **The Unbroken Line**: "Sunder's heavy blow no longer splits a line. It breaks the ground all round you, 6 m. Your dash recharges 25% slower."
- Ultimates: **The Long Cut** (depth 3; modifiers *Second Cut*, *Line of Morning*, *Through the Wall*) and **Dawn in the Steel** (depth 12; *Long Morning*, *Crescents Through*, *Mending Light*). See §3.6.

**The Bulwark's road (31).**
- Entry **Shield Arm**: +10% block.
- Small: +5% block (twice); +2 Resolve (twice); barrier +15%; retaliation +20%.
- Skill lamps. **Oathblade**: *Shield and Edge* (after a block, Oathblade swings at once), *Long Oath* (reach +1.5 m), *Morning Edge* (each swing throws a crescent 6 m, as Oathkeeper does but weaker). **Rebuke**: *Wider Rebuke*, *Rebuke the Strong* (champions take double), *Answering Light* (each rebuke mends 1%). **Watch Bell**: *Loud Bell* (10 m), *Iron Bell* (things drawn in are slowed 30%), *Bell and Barrier* (3% barrier for each thing drawn in, from 2%).
- Notables: **Ward** (each block is a Ward, up to ten; at ten your shield answers with a Rebuke all round you), **Turned Arrows** (blocked missiles fly back), **Shield-Wall** (+15% block while standing still), **Heavy Shield** (blocking a champion's blow stuns it 0.5 s), **Faith in the Wall** (while your barrier is above a fifth of health, holy damage +20%).
- Blue: **The Wall Holds**: "Block chance is doubled (to 75% at most), but you can't block while moving." Blue: **Bearer of Blows**: "What you block isn't lost: it's stored and let out as holy damage by your next Rebuke. You mend 30% less."
- Ultimates: **Bell of the Morning** (depth 3; *Fourth Toll*, *Bell for the Dead*, *Healing Peal*) and **Sixty on the Wall** (depth 12; *Shield-Brothers*, *The Wall Walks*, *Long Watch*).

**The bridge: Sword and Board (6).** Notable **Shield Swing** (heavy blows count as blocks for Ward, and each block makes the next heavy blow 30% harder). Notable **Oath and Bell** (Watch Bell tolls when you stagger something, at most every 3 s). Two small lamps (Might and Resolve). Blue: **Sword-and-Board**: "You may carry a greatsword and a shield together. The greatsword strikes 15% slower, and the shield blocks half as often."

**The crossings.** The **Shambles** (toward the Butcher): **Opened Up** (a heavy blow on a bleeding thing deals the rest of its bleed at once) and **Cleaver's Weight** (Carve's every third chop is heavy). The **Duelist's Road** (toward the Skirmisher): **Parry** (a perfect dash counts as a block for Ward) and **Riposte** (a block gives an Opening: blows strike true for 1 s).

### 2.9 The other three quarters

Same shape: the hearth's dash form and reflexes, two roads, the bridge.

**Reaver.** Dash form **Grapple Chain** (throws the hook 12 m at the first thing in its aim and hauls her to it; with nothing to bite it's a plain dash): *Anchor*, *Second Hook*, *Reel*. Reflex **War Cry** ("ten or more things within 5 m, or a champion strikes you: roar; lesser things flee 2.5 s; you strike 25% harder for 6 s; every 16 s"): *Terror*, *Bloodlust*. Second reflex **Red Tide** (below a third of health: a red roar that mends 10% and drives you 30% harder for 4 s; every 25 s). Hearth blue: **Nothing Spared**: "All mending is 50% stronger. You have no draught."

| Road | Notables | Blue lamps (the price in italics) | Skill lamps |
|---|---|---|---|
| **Butcher** | **Frenzy** (each hit +1% attack speed, to 30; fades out of the fight), **Open Vein** (a blow on a thing bleeding for 3 s bursts the bleed), **Red Work** (killing a bleeding thing mends 1%), **Butcher's Rhythm** (every 10 Frenzy adds a chop to Carve), **Hamstrung** (bleeding champions are 20% slower) | **Always Bleeding**: Blood Up counts you as below a third of health, always; *you can't be mended above 60%: the rest becomes barrier*. **The Butcher's Count**: each kill +1% damage for 10 s, to 50%; *you take 15% more* | Carve (*Four Chops*, *Deeper Cuts*, *Long Reach*); Hurled Cleaver (*Two Cleavers*, *Ricochet*, *Another Way Back*); Axe Gyre (*Bleeding Gyre*, *Wide Gyre*, *Gyre on a Kill*) |
| **Chainbound** | **Bound** (the hook and the anchor leave things Bound 3 s), **Conductor** (shock on a Bound thing leaps to every other Bound thing), **Short Leash** (hooked things are dragged 2 m further), **Knot** (eight Bound things close together are stunned 1 s), **Long Arms** (Iron Palms strike Bound things from 6 m) | **The Long Chain**: melee skills reach 3 m further and hook the last thing they hit; *they strike 20% weaker*. **Lightning Rod**: storm skills strike Bound things first and 40% harder; *you take 15% more from storm and fire* | Chain Lash (*Double Lash*, *Barbed Hook*, *Lash Back*); Anchor (*Two Anchors*, *Heavy Anchor*, *Live Anchor*); Iron Palms (*Palm on the Chain*, *Ringing Palm*, *Palm Storm*) |
| **Bridge: Hook and Hatchet** | **Red Chain** (Bound things bleed; bleeding things stay Bound 1 s longer) | **Cleaver on a Chain**: Hurled Cleaver flies on your chain, hooks what it hits and drags it to you; *it no longer returns through the crowd* | |

**Arcanist.** Dash form **Mirror Step** (step 5 m, leaving two reflections that draw what hunts you and burst when broken): *Hall of Mirrors*, *Cold Glass*, *Glass Heart*. Reflex **Time Slip** ("a blow that would take a quarter of your health, or a champion's mark closing on you: 3.5 s at a third of the speed; every 30 s"): *Borrowed Time*, *Deep Slip*. Second reflex **Spellward** (a barrier of 10% of health whenever three spells land in one second, every 8 s). Hearth blue: **Unbound Casting**: "Spells wait 30% less. You have 20% less health."

| Road | Notables | Blue lamps (the price in italics) | Skill lamps |
|---|---|---|---|
| **Kindler** | **Thermal Shock** (fire striking frozen things shatters them, 3 m, half again their blow), **Ashen Ground** (burning ground lasts 50% longer), **Ford-Cold Ground** (Rime Field chills before it freezes), **Firebreak Wall** (Pyre Line stops missiles), **Stand in Your Fire** (in your burning ground: +20% armor, spells 10% faster) | **Frostfire**: burn and chill no longer cancel; your fire chills and your frost burns; *each 30% weaker*. **Ash Walker**: in your burning or frozen ground you take 40% less; *outside it your spells are 15% weaker* | Cinderfall (*Two Cinders*, *Wider Fall*, *Slow Burning*); Pyre Line (*Cross of Fire*, *Long Line*, *Rolling Wall*); Rime Field (*Quick Frost*, *Wide Field*, *Shatter Field*) |
| **Moonweaver** | **Lunar Mark** (motes mark; a marked thing that dies passes the mark to two), **Many Lights** (+1 projectile to spells), **Forking** (lightning forks once more), **Moon-Drawn** (motes seek the marked first), **Still Water** (Moonwell lasts 50% longer and fires 30% faster) | **The Echo**: every spell fires again 0.5 s later at half strength; *spells wait 25% longer*. **Crowded Sky**: spells with projectiles fire two more, and all seek; *each is 35% weaker* | Seeking Motes (*Split Motes*, *Swift Motes*, *Heavy Motes*); Moonwell (*Twin Wells*, *Wide Well*, *Well of Storms*); Wandering Spark (*Two Sparks*, *Long Wander*, *Overcharge*) |
| **Bridge: The Ledger** | **Two Schools** (Rime Field's frozen ground makes Wandering Spark arc twice as often) | **The Ledger** ("Some of them keep ledgers."): each fire or frost spell makes your next moon or storm spell 30% harder, and the other way round; *a spell of the same side twice running is 15% weaker* | |

**Stalker.** Dash form **Vault** (spring 6 m back from your aim, untouchable in the air, leaving snares): *Parting Volley*, *Snare Line*, *Light Feet*. Reflex **Mark Prey** (every 9 s the strongest thing in sight is marked: it takes 50% more and dies below 20%): *Two Marks*, *Executioner*. Reflex **Smoke Bomb** (a perfect dash throws smoke: 3 s unseen, sure crits; every 12 s): *Choking Smoke*, *Ambush*. Hearth blue: **Light Step**: "Three dash charges. Each dash is 30% shorter."

| Road | Notables | Blue lamps (the price in italics) | Skill lamps |
|---|---|---|---|
| **Skirmisher** | **Opening** (for 2 s after a dash, blows strike true), **Adder's Kiss** (poison stacks to ten; at ten it bursts), **Through, Not Around** (dashing through things cuts them; each one cut gives back 2% of a dash), **Slip the Blow** (the perfect dash window is 50% longer), **Red Edge** (true strikes bleed) | **Never Still**: dashes come back 40% faster; *standing still for a second halves your blows until you move*. **Adder's Patience**: poison stacks without limit and never fades while you keep striking; *you can't strike true* | Twin Fangs (*Third Fang*, *Quick Fangs*, *Venom Fangs*); Cutting Wake (*Long Wake*, *Lingering Wake*, *Wake of Smoke*); Knifestorm (*Fan Out*, *Knives Return*, *Poisoned Steel*) |
| **Verge-Hunter** | **Pinned** (Heartseeker roots lesser things it passes through), **Mark the Herd** (when the prey dies its mark passes to two), **Fletcher's Eye** (+1 pierce), **Hold the Distance** (blows from beyond 8 m +20%), **Spirit of the Verge** (Spirit Herd's beasts charge your prey) | **Long Sight**: blows from beyond 8 m strike 50% harder; *within 4 m, 30% weaker*. **Rain Archer**: Volley no longer flies; it falls from above on the thickest pack, wider; *it can't pierce* | Volley (*Wide Volley*, *Twice Fletched*, *Barbed*); Heartseeker (*Split Heart*, *Quick Draw*, *Heart of Thorns*); Snare-Line (*Long Line*, *Biting Snares*, *Snare and Burn*) |
| **Bridge: Bow and Blade** | **Quick Hands** (after a dash, your next Volley looses at once) | **Close and Far**: within 4 m your blades strike 30% harder, beyond 8 m your arrows do; *in between, both are 15% weaker* | |

**The other crossings.** The **Storm Road**: **Lightning Leaps the Chain** (storm that strikes a Bound thing runs to everything Bound) and **Charged Mote** (a mote striking a Bound thing shocks it). The **Firebreak**: **Fire Arrows** (arrows that pass through your burning ground catch fire) and **Frozen Snares** (snares in Rime Field freeze what they hold).

### 2.10 By day, by night, in maps: one rule

| | Rules (notables, blue lamps, reflexes, dash form, skill lamps, the Flare and its lamps) | Numbers (small lamps) |
|---|---|---|
| **By day and in maps** | in full | in full |
| **By night** (the table's arenas and story fights) | **in full**: they wake on whatever the draft brings | **a quarter**, and their sum capped at +25% (the Edge's night cap, SKILLS_DESIGN §14.2) |

This keeps the night the ember's ("power from nothing, gone at dawn"): numbers barely cross, and identity does. On top of that, **the road you've lit deepest leans its type's skills ×1.4** (the calling's ×1.3 lean folds into it; leans stay under ×2), and **that type's grip skill is offered in the first draft**, as banked skills are (§10).

---

## 3. The Flare (ultimates)

### 3.1 The buttons

- **Q / right-click / pad Y: the Flare.** `Act.Ability` becomes `Act.Ultimate`, and the draught's act (today misnamed `Ultimate`) becomes `Act.Draught` on R / pad X. Saved bindings migrate.
- **Space / Shift / pad A: the dash** (two charges, perfect window, i-frames), in the calling's form.
- The HUD's "art in hand" slot becomes the Flare: the centerpiece between the globes (UI design's instrument). It fills as a rising ember. Full, it breathes, and her eyes, hands and weapon edge glow in the calling's hue.

### 3.2 How it fills: a dopamine life-saver

The meter runs 0 to 100. It fills **fastest when you're in trouble**, and slowest from simply killing (`notes/classes_ultimates.md`: FF's limit break and Hades' Call). Starting numbers, for the harness to tune:

| Source | Fill | Why |
|---|---|---|
| Blows taken | +1.2 for each 1% of health lost; doubled below a third of health | Being hurt is when you need it |
| **Close calls** | a perfect dash +10; blocking a champion's or a boss's blow +6 | Rewards the skill the dash already teaches |
| **The ember answers** | the first drop below a quarter of health: +35 (once every 45 s) | The life-saver. A half-full Flare is ready when you're nearly dead |
| Champions and bosses | +1 for each 1% of their health you deal; a champion killed +8 | One to three Flares in a boss fight, from fighting it well |
| Ordinary kills | +0.25 each, at most +1 a second | The horde can't spam it |

**Targets:** the first Flare about 90 to 120 s into a night; then one every 60 to 90 s; two or three in a boss fight; faster when it's going badly. Nights and maps start empty, and story fights at half (they're short). Maps keep it between areas.

### 3.3 The window

- **Untouchable while it plays.** For a Strike, from the press until 0.4 s after its last blow lands. For a Stand, for its first 1.5 s; after that the Stand's own defense holds.
- **The flare burns the air:** at the key pose, enemy missiles within 6 m are burned away.
- **A flare at the edge burns brighter:** cast below a quarter of health, it also mends 20% of health over a second, and its reach is 25% larger. Every Flare is a life-saver by design.
- **Bosses:** a Flare breaks a boss's channel and staggers it a little, but never stuns it outright. A boss's danger marks always draw over the Flare's light.
- **Control:** a Strike takes the controls for at most 0.6 s. A Stand gives them back at once.

### 3.4 Choosing and shaping

- **Four per calling:** one **Strike** (instant, one decisive moment) and one **Stand** (a timed state) per type. Strikes come at road depth 3, Stands at depth 12. The type chosen at creation gives its Strike from level 1.
- **One carried at a time,** changed in the book by day (or at a night's start, before the first draft).
- **Three modifier lamps each** on the road beside it, plus the hearth's two Flare lamps and Banked Flame (two charges).
- **Damage scales with level:** the character's by day and in maps, the ember's at night. A Flare counts as its type's tags (The Long Cut is heavy), so the road's lamps feed it.
- **Four new great blessings at night** touch the Flare, one per role: **Bright Hour** (power: the Flare is 40% larger), **The Ember Answers Twice** (ward: below a quarter of health, the Flare fills to full, once a night), **Short Wick** (quickening: it fills 35% faster), **Called Shot** (answer: it deals 60% more to champions and bosses).

### 3.5 The shared beat: every Flare's grammar

This is what makes every ultimate feel like a limit break. It's built once by the experience lead (camera, time) and skills VFX (screen), then every ultimate uses it.

1. **The press (t = 0).** Time drops to 8% for 0.22 s of real time. The music ducks 9 dB, and a sub-drop "inhale" (an ember catching) plays under the calling's stinger. The world desaturates 70% and darkens a quarter, everything except her, with a soft vignette and no hard edge. The camera pushes in 12% and pitches down 4° over 0.18 s (ease-out). Her ember glow ignites in the calling's hue.
2. **The key pose (up to 0.3 s).** Her anticipation pose is held: the poster frame. The weapon's light peaks.
3. **The release.** Time returns over 0.08 s. **Hitstop** on the main blow: 6 to 8 frames (100 to 133 ms); 2 to 3 frames on the lesser hits. Shake trauma 0.5 to 0.8, scaled by the settings. The camera eases back to play framing over 0.6 s.
4. **The look's laws** (skills VFX, inherited): no hoops (a shockwave is dust, debris, heat shimmer and lit ground cracks, never a bright-edged ring); light reads as light, never geometry; gaussians never an edge; light held below the knee except a Flare's own column moment. Enemy danger marks draw over everything.
5. **The last blow:** a Flare that kills a boss plays 0.6 s at 20% speed while the camera orbits 15° round the boss, then hands over to the victory.
6. **Hues:** warden dawn-gold on steel; Butcher blood-red on iron; Chainbound storm-blue on iron; Kindler ember-amber with ford-blue; Moonweaver moonlight silver-blue with moonfire violet; Skirmisher steel with poison-green; Verge-Hunter bone-white with Verge green.

### 3.6 The sixteen: staging briefs

Each lists what it does, then camera, animation, VFX, sound and hitstop beyond the shared beat. Times are from the release.

#### Warden: Sunderer

**The Long Cut** (Strike). One horizontal sweep of a blade grown to 12 m of dawn light, then a vertical cleave that splits the ground in a 24 m line. *Horde:* everything within 12 m is cut; the line carves a lane. *Boss:* the cleave lands as a heavy blow and Sunders it (armor −30% for 8 s).
- Camera: pulled out 10% for the sweep, then a fast 6° roll into the cleave's direction.
- Animation: key pose blade low behind, both hands, weight on the back foot; the sweep 0.25 s (a full 360° turn on the planted foot); a 0.1 s rise; the cleave down 0.12 s; a recovery kneel 0.3 s.
- VFX: the blade lengthens as a core of gold light inside a heat shimmer (not a solid bar). The sweep leaves a smear of light at knee height. The cleave opens a ground crack that glows from below, with dust jetting up along its length in sequence (a running fuse), and chunks thrown out.
- Sound: a long metal draw; the sweep's air-roar; for the cleave, a bell-struck impact with sub, then rock tearing along the line.
- Hitstop: 3 frames on the sweep; 8 on the cleave; shake 0.8.

**Dawn in the Steel** (Stand, 6 s). The greatsword burns with morning: swings are 40% faster, every swing throws a crescent of light 10 m, and every heavy blow staggers whatever it hits. *Horde:* the crescents mow lanes. *Boss:* staggers stack quickly, and the crescents hit it from range.
- Camera: a 0.5 s push-in, then normal; a slight zoom-out (5%) while it lasts, so the crescents' reach shows.
- Animation: key pose blade raised flat overhead, light pouring down it; then her swing clips at 1.4× with the blade trailing light.
- VFX: the blade's edge is a white-gold core with ember sparks shedding; crescents are thin, sharp and travel visibly (the skills lead's note on Rend and Mend: thin, darker, seen to travel). A faint gold mote-rise round her feet.
- Sound: a choir-less held tone (the Order's evening call, hummed low, never words) under each swing's ring.
- Hitstop: 2 frames a swing, 5 on heavy blows.

#### Warden: Bulwark

**Bell of the Morning** (Strike). She strikes her shield like a bell, three times. Each toll stuns every lesser thing on screen for 1 s and sears, and the third toll is a holy blast 8 m round. Each toll mends 4%. *Horde:* the screen stops three times. *Boss:* each toll breaks a channel and fills its stagger.
- Camera: still; a tiny push with each toll (2%, 4%, 8%).
- Animation: key pose shield raised to the face, sword pommel drawn back; three pommel strikes, 0.25 s apart, the third full-bodied.
- VFX: each toll sends a **pressure wave** visible only as a ripple in the air and dust lifting off the ground outward (no ring), and lesser things' rims flash gold as it passes. The third toll pours light up from the shield as a short column.
- Sound: a real bronze bell, recorded close, with its decay ringing under the fight for 4 s. The world's sounds drop out for 80 ms after each toll.
- Hitstop: 4, 4, 8 frames.

**Sixty on the Wall** (Stand, 6 s). The wall the Watch built for sixty: fifty-nine spectral shield-bearers of the Watch close in an arc in front of her and hold. It blocks every missile, the press throws back what touches it, every block on it rebukes, and she takes 80% less. *Horde:* a front that doesn't break. *Boss:* its charges and missiles break on the wall.
- Camera: pulls back 15% and lifts 6° to show the whole wall; holds there while it lasts.
- Animation: key pose sword raised, shield planted (the "form up" call); the spectral bearers step in from either side in a 0.4 s ripple and lock shields.
- VFX: the bearers are faint, cold-gold silhouettes in Watch mail, lit from behind like figures in lamp-smoke (not glowing ghosts: the skills lead flagged Barrow Host's pale ghosts). Their shield rims catch the light. A block flashes on the struck shield only.
- Sound: sixty shields locking (layered thuds rippling outward); a low murmur of men; each block a shield-crack.
- Hitstop: 4 frames at the lock; 1 frame per block.

#### Reaver: Butcher

**Bone-Toll** (Strike). She leaps on the strongest thing in 12 m and hacks it five times. If it dies, she leaps to the next strongest, three times at most. Each blow splashes bleeding 3 m round. *Horde:* three champions gone. *Boss:* five heavy blows (the leap stays within the boss's reach and lands behind it).
- Camera: follows the leap with a 0.15 s lag; pushes 8% on each landing.
- Animation: key pose crouched, both axes back, teeth bared; the leap 0.3 s; five alternating chops 0.08 s apart, the last two-handed overhead; a vault off to the next.
- VFX: dark red arcs that hang a moment and fall as droplets; blood mist on the last chop. Her eyes and the axe edges glow ember-red.
- Sound: the leap's grunt; five wet, heavy chops rising in pitch; a bone-crack on the fifth; a low growl between.
- Hitstop: 2 frames each on chops one to four; 7 on the fifth.

**Butcher's Hour** (Stand, 8 s). Frenzy fills at once. She strikes twice as fast, every blow bleeds, blows execute ordinary things below 15%, and every kill mends 1% and adds 0.3 s. *Horde:* a red blur. *Boss:* sustained damage while it lasts, with her life held up by the mending.
- Camera: 3% closer for its length; a faint red vignette.
- Animation: key pose head thrown back in a roar, axes out wide; then her swing set at 2×, with a forward-leaning hunt stance.
- VFX: red smoke trails from the axes and from her shoulders like breath in cold air; the world tints slightly warmer; executions burst in a short spray.
- Sound: her heartbeat under everything, quickening; chops tighter and drier.
- Hitstop: 1 frame on every hit, 4 on executions.

#### Reaver: Chainbound

**Drag Them Under** (Strike). She whirls the chain once overhead and casts it out: hooks bite up to 24 things within 14 m, and she hauls them all into one knot at her feet, then drives the chain into the ground. The slam stuns 1 s and breaks the knot. *Horde:* the screen's edge comes to her and dies. *Boss:* it's hooked and dragged 3 m and stunned 1.5 s (a channel breaks).
- Camera: zooms out 15% for the cast, then rushes back in with the haul.
- Animation: key pose the chain whirling overhead, one foot forward; the cast's throw 0.15 s; the haul, a two-hand heave back 0.3 s; a downward drive 0.12 s.
- VFX: the chain splits into many hooked lines (iron, dark, catching the light), each visible as it bites; the hauled things slide on the ground with dust wakes; the slam throws dirt and stone upward in a cone.
- Sound: the whirl's hum; a ratcheting rush; one massive iron-and-earth slam.
- Hitstop: 2 frames as the hooks bite; 8 on the slam.

**Storm on the Chain** (Stand, 5 s). She spins the chain round her in a 7 m circle and the sky answers: lightning strikes the chain and runs down it, so everything the chain sweeps is shocked, and Bound things call bolts. *Horde:* a moving storm she walks through the crowd. *Boss:* bolts strike it twice a second while it's in reach.
- Camera: steady, 8% out.
- Animation: key pose the chain raised like a lightning rod, sky-ward; then a walking spin loop.
- VFX: the chain glows white-blue where the current runs, as fine forking light (no white tubes, as with the Tempest); bolts strike from above with a brief sky flash; scorch marks remain.
- Sound: the chain's whir; thunder cracks layered with a tight electric snap; rain-hiss under it.
- Hitstop: 3 frames on each sky strike.

#### Arcanist: Kindler

**Skyfire** (Strike). She lifts her staff and the sky burns: twelve falling embers hit the thickest packs on screen over 2.5 s, each a blast 4 m round, and the ground burns 6 s. *Horde:* the screen's dense packs erased. *Boss:* four of them seek it.
- Camera: lifts 8° and pulls out 15% to show the fall; settles back over the 2.5 s.
- Animation: key pose staff raised two-handed, head tilted up, ember lit in her eyes; held while the stars fall; a sweep down with the last.
- VFX: each ember is a streak of molten light with a smoke trail, falling at an angle (never vertical white bars); impacts throw flame jets turned along their way on the screen (Firepot's method) and leave burning ground with charred edges.
- Sound: a rising roar from the sky, then staggered heavy impacts; crackle of the burning ground after.
- Hitstop: 3 frames on the first impact and the last.

**Hard Winter** (Stand, 6 s). The ford's cold comes up out of the ground: everything on screen slows 60% and freezes after 2 s still in it; her spells shatter what's frozen; when it ends, the thaw bursts. *Horde:* the whole screen frozen in place, then broken. *Boss:* slowed 40%, and the thaw-burst hits it hard.
- Camera: no push; a slow 3% drift inward over its length (the hush of cold).
- Animation: key pose staff driven into the ground, frost crawling up her arm; then normal casting.
- VFX: rime spreads outward over the ground as crystalline frost texture (not a ring), breath steams from everything, frozen things glaze; at the end, the ice cracks with meltwater spray and a shatter burst on each.
- Sound: wind drops out; a high glassy ring; creaking ice; the thaw is a chorus of cracks.
- Hitstop: 6 frames on the thaw-burst.

#### Arcanist: Moonweaver

**The Storm Answers** (Strike). She opens her hand, and lightning laces every enemy on screen: a lattice of arcs jumps from her to everything within 16 m, then six heavy bolts strike the strongest. *Horde:* shocked to the screen's edge. *Boss:* takes all six bolts.
- Camera: a white sky-flash, then 10% out to show the lattice.
- Animation: key pose one hand raised, fingers splayed, hair lifting with static; a snap closed on release.
- VFX: arcs are thin, branching and electric blue, drawn over 0.15 s as a spreading web (no white balls); heavy bolts are thick with a bright core and fork, each leaving a scorch.
- Sound: the lattice is a fizzing tear of static; each bolt a distinct thunderclap, the last loudest.
- Hitstop: 2 frames on the lattice; 6 on the last bolt.

**Moonrise** (Stand, 6 s). A great moon rises behind her, low and silver, and motes pour out of it, twelve a second, seeking. They mark, and the marks pass on when the marked die. *Horde:* a silver storm that finds everything. *Boss:* the motes favor it once the lesser things are dead.
- Camera: lifts 6° and pulls back 8%, so the moon sits in frame behind her.
- Animation: key pose arms drawn up and apart (raising it); then normal casting with a slower, floating gait.
- VFX: the moon is a pale disc with soft craters, half-transparent, lighting the ground silver; motes are crescent glints with violet moonfire trails (Moonbrand's palette); marked things carry a small crescent.
- Sound: a low swell like a breath held under water; each mote a soft chime that piles into a shimmering chord.
- Hitstop: none (it's a flow); 4 frames as it rises.

#### Stalker: Skirmisher

**A Hundred Cuts** (Strike). She's gone in smoke, and strikes twelve things in 1.2 s, flickering between them, the last blow on the strongest. Each is cut, bleeds and is poisoned; anything below 25% dies. She reappears where she started. *Horde:* a dozen champions and elites cut down. *Boss:* the last four cuts all land on it.
- Camera: still (so the flicker reads), with a light zoom out 5%.
- Animation: key pose blades crossed at the chest, half crouched; then twelve 0.1 s strike poses (cut, back-cut, thrust), each a single held frame with motion smear; she reappears in a low finish.
- VFX: her afterimages hang for 0.2 s at each strike point, fading in steel-grey; a green-black poison bloom on each target; the trail between strikes is a thin smoke line.
- Sound: one slice per hit in quick succession, rising; a sheath sound on the finish.
- Hitstop: 1 frame per cut; 6 on the last.

**The Long Smoke** (Stand, 7 s). A cloud of smoke 10 m round fills where she stands and holds there. In it she's unseen, moves 30% faster, every blow strikes true, and lesser things inside lose her and strike each other. *Horde:* a pocket where the crowd turns on itself. *Boss:* it loses her for 2 s (missiles lose track).
- Camera: no push; a darker grade inside the cloud.
- Animation: key pose a smoke bomb thrown down at her feet, cloak swirling; normal clips after, at 1.3× pace.
- VFX: dense, rolling smoke that hugs the ground, lit from inside by brief steel glints when she strikes; enemies inside go dim and lose their rim lights.
- Sound: a hiss and pop; muffled sound inside the cloud (a low-pass on everything but her blades).
- Hitstop: 1 frame per hit.

#### Stalker: Verge-Hunter

**The Long Shot** (Strike). One arrow drawn to the ear and loosed down the screen. It pierces everything in a 30 m line, splits three times on the toughest things it passes, and kills ordinary things below 30%. *Horde:* a lane cut through the whole screen. *Boss:* one huge true strike (double crit damage).
- Camera: a 0.2 s look along the arrow's line (the camera turns 8° and leads toward it), then back.
- Animation: key pose full draw, string at the ear, bow canted, eye down the shaft; release with the bow arm snapping forward; follow-through held 0.3 s.
- VFX: the arrow trails a long, thin pressure wake that bends the air (shimmer) and raises dust in a line; each split is a quick bright fleck; anything struck kicks back.
- Sound: the long creak of the draw; a whip-crack release; a supersonic tear down the line; impacts in sequence.
- Hitstop: 7 frames on the first impact.

**Sky of Arrows** (Stand, 5 s). She looses a volley into the sky and marks ground 12 m across where she aims. Arrows fall on it in a steady rain for 5 s, rooting what they strike for 0.5 s. *Horde:* a killing field she drives them into. *Boss:* rooted repeatedly (each root 0.2 s on a boss).
- Camera: lifts 10° to show the field; holds.
- Animation: key pose bow aimed at the sky, a fan of arrows on the string; she looses three times in quick succession, then plays normally.
- VFX: arrows fall as dark streaks with pale fletching glints (thin, never bars), thudding into the ground and staying planted until it ends; a faint drift of dust over the field.
- Sound: a rising whistle; a rain of thuds, dense and rhythmic.
- Hitstop: none per arrow; 3 frames on the first wave.

### 3.7 Modifiers (three per ultimate)

| Ultimate | Modifier lamps |
|---|---|
| The Long Cut | **Second Cut** (another sweep 0.6 s later), **Line of Morning** (the line burns 4 s), **Through the Wall** (the line runs 36 m, and the Sundered armor is −40% on bosses) |
| Dawn in the Steel | **Long Morning** (8 s), **Crescents Through** (crescents pierce everything), **Mending Light** (a crescent kill mends 0.5%) |
| Bell of the Morning | **Fourth Toll**, **Bell for the Dead** (lesser things flee 3 s after the last toll), **Healing Peal** (each toll mends 8%) |
| Sixty on the Wall | **Shield-Brothers** (the wall strikes out once a second), **The Wall Walks** (it moves with you), **Long Watch** (9 s) |
| Bone-Toll | **Toll Again** (two more leaps), **Bell-Ringer** (each chop stuns 2 m round), **Feast** (each kill mends 10%) |
| Butcher's Hour | **Overtime** (a kill adds 0.6 s), **Red Mist** (lesser things near you flee), **Not Today** (while it holds, you can't fall below 1 health) |
| Drag Them Under | **Deeper** (hooks reach the whole screen), **Grinder** (the knot is shredded for 3 s before the slam), **Hold Him** (a boss is pinned 3 s) |
| Storm on the Chain | **Two Chains** (two circles, crossing), **Earthing** (each sky strike mends 1%), **Wide Whirl** (10 m) |
| Skyfire | **More Stars** (eighteen), **Ember Rain** (the ground burns 10 s), **Called Down** (all the stars on the toughest thing) |
| Hard Winter | **Deep Winter** (freezes after 1 s), **Thaw-Burst** (twice the burst), **Winter Keeps** (mend 2% a second while it holds) |
| The Storm Answers | **Second Peal** (it strikes again 1 s later), **Grounded** (each thing struck gives 1% barrier), **The Eye** (twelve bolts on the strongest) |
| Moonrise | **Full Moon** (twice the motes), **Moonset** (it ends falling, a blast 8 m round), **Silver Tide** (marks pass to three) |
| A Hundred Cuts | **More Cuts** (eighteen), **Last Cut** (the last blow kills below 40%), **Gone** (unseen 3 s after) |
| The Long Smoke | **Thicker** (10 s), **Choking** (poison in the smoke), **Turned** (things inside fight each other 3 s after it clears) |
| The Long Shot | **Split Thrice More**, **Pinned to the Earth** (everything struck is rooted 2 s), **Through the Heart** (triple crit damage on a boss) |
| Sky of Arrows | **Follow the Hunter** (the field moves with you), **Iron Rain** (arrows stun), **Thorned Rain** (Thornbloom grows where they fell) |

---

## 4. The new skill list

**Counts:** 16 new combat skills (two per type), each with two evolutions (32), and 4 new unions (one per calling's hybrid): 52 new draft pieces. Plus 16 ultimates (48 modifiers), 8 reflexes (six of them today's pressed arts) and 4 dash forms (today's Kin arts), 4 Flare great blessings, 4 new tags (**Heavy**, **Shield**, **Twin**, **Hook**) and one new status (**Bound**). With today's 26, there are **42 combat skills**: enough for eight types of three signature skills each, with every skill wanted by at least two builds (SKILLS_DESIGN principle 5). Synergy over count: each new skill was chosen for what it joins, not to fill a slot.

| Skill | Type it feeds (also wanted by) | Tags | Role | What it does | Path(s) | Evolutions |
|---|---|---|---|---|---|---|
| **Sunder** | Sunderer (Bulwark via Sword-and-Board) | Melee, Steel, Physical, Area, Heavy | grip, clear | Slow 220° cleave; every fourth swing a heavy line 7 m | Steel and Blood, Dawn's Light | *Skybreaker* (the heavy line runs the screen's width), *Sunlit Edge* (every swing sears; seared things burst) |
| **Groundbreaker** | Sunderer (Chainbound) | Melee, Physical, Area, Heavy | control | Every 5 s a crack runs to the densest pack in 10 m; the ground heaves (stun 0.6 s) | Steel and Blood | *Faultlines* (three cracks), *The Deep Heave* (heaved things are thrown, and land as blows on others) |
| **Rebuke** | Bulwark (Sunderer) | Holy, Nova, Shield | retaliation | Each block strikes the blocker and three near it with holy light | Dawn's Light | *Righteous Answer* (rebukes chain), *Shield of Morning* (rebukes leave a barrier) |
| **Watch Bell** | Bulwark (Chainbound, Verge-Hunter) | Aura, Holy, Shield | taunt, defense | Every 6 s a toll draws everything within 8 m to you for 2 s; 2% barrier for each | Dawn's Light, the Host | *Curfew Bell* (drawn things are slowed and take more), *Alarm Bell* (tolls also stun) |
| **Carve** | Butcher (Skirmisher) | Melee, Steel, Physical, Twin | grip, single-target | Three fast chops on the nearest, each bleeding | Steel and Blood | *Butcher's Block* (every tenth flurry is a cleave all round), *Red Ribbon* (chops send bleeding arcs 4 m) |
| **Hurled Cleaver** | Butcher (Chainbound, Skirmisher) | Thrown, Projectile, Steel, Physical | reach | Every 3 s a cleaver flies at the farthest bleeding thing in 12 m and returns | Steel and Blood, the Hunt | *Twin Cleavers* (two, crossing), *Gibbet* (it hooks on the way back) |
| **Chain Lash** | Chainbound (Butcher) | Melee, Steel, Physical, Area, Hook | grip, gather | 7 m whip arc; the farthest thing struck is hooked and dragged in | Steel and Blood, the Storm | *Scourge* (two lashes, crossing), *Live Wire* (the lash shocks, and the shock runs the chain) |
| **Anchor** | Chainbound (Bulwark, Kindler) | Area, Physical, Hook, Zone | control | Every 7 s an anchor lands in the thick of it; everything 5 m round is Bound to it 3 s, then yanked together | the Storm, the Host | *Sea Anchor* (it drags its catch round you), *Storm Anchor* (it calls lightning on the knot) |
| **Pyre Line** | Kindler (Verge-Hunter) | Spell, Fire, Zone, Area | wall, area denial | Every 6 s a line of fire 8 m long rises between you and the densest pack | the Pyre | *Firestorm Line* (the wall rolls forward), *Hearth Line* (standing near it mends) |
| **Rime Field** | Kindler (Moonweaver, Chainbound) | Spell, Frost, Zone, Area | control, setup | Every 7 s the ground under the thickest pack frosts; what stays 1.5 s freezes 2 s | the Long Winter | *Black Ice* (frozen things shatter at half health), *Ford-Water* (the field follows you) |
| **Moonwell** | Moonweaver (Kindler) | Spell, Arcane, Zone, Projectile | turret | A well of moonlight hangs where cast for 8 s, firing motes at what passes within 7 m; two at most | the Weave | *Moonpool* (wells mark what they strike), *Wellspring* (three wells, and motes split) |
| **Wandering Spark** | Moonweaver (Chainbound) | Spell, Storm, Chain, Projectile | roaming area | A slow ball of lightning drifts out along your path, arcing to three things every 0.3 s | the Storm, the Weave | *Ball Lightning* (it grows as it arcs, and bursts), *Will-o'-the-Wisp* (it follows you and draws foes) |
| **Twin Fangs** | Skirmisher (Butcher) | Melee, Steel, Physical, Twin | grip, burst | Quick double cuts on the nearest; for 2 s after a dash every Fang strikes true | the Hunt, Steel and Blood | *Viper's Fangs* (each cut stacks poison twice), *Wolf's Fangs* (Fangs strike the two nearest) |
| **Cutting Wake** | Skirmisher (Verge-Hunter, any dash build) | Physical, Steel, Zone, Trap | dash payoff | Each dash leaves hanging blades along its path for 1.5 s, cutting and poisoning what crosses | the Hunt, the Wild | *Razor Wake* (blades fly at the nearest when it ends), *Smoke Wake* (it leaves smoke that hides you) |
| **Heartseeker** | Verge-Hunter (Moonweaver) | Projectile, Ranged, Physical | single-target, pierce | Every 3 s a heavy arrow at the toughest within 20 m, piercing everything in line; true on the marked | the Hunt | *Heart of the Pack* (it splits on a kill), *Thorn Heart* (it plants Thornbloom where it stops) |
| **Snare-Line** | Verge-Hunter (Skirmisher, Kindler) | Trap, Nature, Area | control | Every 6 s a line of snares falls across the thickest approach 6 m ahead; what steps in is rooted 1.5 s | the Wild, the Hunt | *Bramble Line* (snares become thorns that poison), *Deadfall* (logs fall on what's rooted) |

**The four unions** (the hybrid's payoff at night, freeing a slot as unions do):
- **The Gate and the Sword** (warden): Sunder (*Sunlit Edge*) + Rebuke (*Shield of Morning*): a heavy blow every second that rebukes all round.
- **Gibbet Chain** (reaver): Hurled Cleaver (*Gibbet*) + Chain Lash (*Scourge*): a cleaver on a chain, whirling, hooking and bleeding.
- **Moon on the Ice** (arcanist): Moonwell (*Moonpool*) + Rime Field (*Black Ice*): wells over frozen ground whose motes shatter what's frozen.
- **Blade and Briar** (stalker): Cutting Wake (*Smoke Wake*) + Snare-Line (*Bramble Line*): every dash lays a line of thorned snares.

Their names and the evolutions' lines go to the story lead for the valley's voice and Act 1 safety, as every name in SKILLS_DESIGN did.

---

## 5. Arenas and endless

**The nights (the table's arenas).** The draft is as it was: from nothing, open to everyone, gone at dawn. What changes is who you are while you draft:
- the Lamps' rules wake on whatever the ember brings (your Sunder lamps are waiting when Sunder comes);
- your deepest road leans its type's skills, and its grip skill comes in the first draft;
- the Flare starts empty and fills from the fight;
- the four Flare great blessings sit among the others, dealt by role.

A warden who drafts Volley and Moonbrand all night plays a full ember build: possible, as the owner wants. A warden who drafts Sunder, Groundbreaker and Dawnpulse finds them already shaped by thirty lit lamps: easier and better.

**Story fights.** The same, but the Flare starts at half (the fights are ten to fourteen minutes). Story bosses are written to have a Flare moment: a phase where a Flare breaks a channel or a wall (combat's boss briefs).

**Maps (the atlas).** Everything in full: the Lamps, gear, day skills at their ranks, the Flare. The Flare carries between a map's areas. New map mods: **Smothered** (prefix: the Flare fills 30% slower) and **Bright** (suffix, weakening the survivor: a Flare cast mends nothing). Both are build checks, read on the chart.

**Endless (past the boss, the long night).** Truly endless means the power must keep growing as the horde does:
- every five minutes past the half hour, the Flare **grows a rank**: 10% wider and harder, with no cap;
- the kill fill's cap stays at +1 a second, so danger keeps filling it faster than killing does, and the deep night's danger makes Flares come often;
- **Banked Flame** (two charges) comes into its own: a Flare on a close call and another ready;
- honing (SKILLS_DESIGN §8.5) and the Flare's ranks are the open axes, so the hundredth minute still has something growing.

---

## 6. Build examples

**Warden**
1. *The Wall (simple).* Bulwark, following the glow: Oathblade, Rebuke, Watch Bell and Judgement Disc, with Ward and Shield-Wall lit and Bell of the Morning carried. Walk into the thickest press and stand. The bell drags them in, every block rebukes, and at ten Ward the shield answers all round. When it goes wrong, three tolls stop the screen and mend you.
2. *Weight of the Morning (planner).* Sunderer with the blue lamp **Weight of the Oath** (every blow heavy, slower, no crits). Then **Dawn Rhythm** (Dawnpulse fires on heavy blows, so now on every blow), **Morning in the Steel** (heavy blows on seared things burst) and **Burning Edge** (heavy lines sear): one slow swing sears, bursts and pulses dawn. Hold Fast in the hearth keeps her planted, and at night Hold the Crossing doubles down on standing still. The Long Cut with **Through the Wall** opens bosses' armor for the whole build.
3. *Sword-and-Board (hybrid).* The bridge's blue lamp lets her carry a greatsword and a shield. **Shield Swing** turns heavy blows into Ward, and **Bearer of Blows** stores everything blocked for the next Rebuke. Across the **Duelist's Road**, **Parry** counts perfect dashes as blocks. Bell of the Morning with **Healing Peal** is the reset.

**Reaver**
1. *Red Work (simple).* Butcher: Carve, Hurled Cleaver and Axe Gyre, with Frenzy and Open Vein lit and Butcher's Hour carried. Wade in, let Frenzy climb, and when the bar drops, the Hour turns the fight round.
2. *Lightning Rod (planner).* Chainbound with **The Long Chain** (melee reaches 3 m further and hooks) and **Lightning Rod** (storm strikes Bound things first and harder). Iron Palms with **Long Arms**, Anchor, and Arcweb at night: hook and anchor the pack into a Bound knot, and every storm skill hits all of it at once. Across the **Storm Road**, **Lightning Leaps the Chain** runs every bolt through every chain. Storm on the Chain with **Earthing** keeps her alive.
3. *Gibbet (hybrid).* The bridge's **Cleaver on a Chain** makes the cleaver drag bleeding things in, **Red Chain** makes Bound things bleed, and **Always Bleeding** keeps Blood Up on always (life held at 60%, the rest barrier). The price is real, and Bone-Toll with **Feast** is the life-saver.

**Arcanist**
1. *Fire and Ice (simple).* Kindler: Cinderfall, Pyre Line and Rime Field, with Thermal Shock lit and Skyfire carried. Freeze the pack, drop fire on it, and watch it shatter.
2. *Crowded Sky (planner).* Moonweaver with **Crowded Sky** (two more projectiles, all seek), **Lunar Mark** and **Moon-Drawn** (motes mark, seek the marked, and marks pass on death), and two Moonwells. At night Second Reading fires everything at once, and a single kill passes marks across the screen in a chain. Moonrise with **Silver Tide** turns the end of a night into a silver flood.
3. *The Ledger (hybrid).* The bridge's blue lamp rewards alternating schools: Rime Field, then Wandering Spark, then Cinderfall, then Seeking Motes, each 30% harder for the last. **Two Schools** makes sparks arc twice as often over frozen ground. Hard Winter with **Deep Winter** freezes the screen, and the next storm spell is the Ledger's payoff.

**Stalker**
1. *Hunter's Line (simple).* Verge-Hunter: Volley, Heartseeker and Snare-Line, with the Mark Prey reflex and The Long Shot carried. Kite, let the snares hold the front, and Heartseeker spears the marked and everything in front of it.
2. *Never Still (planner).* Skirmisher with **Light Step** (three dashes), **Never Still** (they come back 40% faster, but standing still halves her blows), **Through, Not Around** (each dash cuts and refunds dash) and Cutting Wake: she dashes through packs constantly. **Adder's Patience** gives up crits for unending poison stacks, and the **Smoke Bomb** reflex fires on every perfect dash. The Long Smoke with **Choking** turns the crowd on itself.
3. *Firebreak (cross-calling).* Bow and blade with **Close and Far**, then across the **Firebreak** into the arcanist's quarter: **Fire Arrows** sets Volley alight through burning ground. At night she drafts Firepot and Cinderfall (off-calling, fully allowed) to lay that ground. Sky of Arrows with **Thorned Rain** pins the burning pack. It's possible because the board connects, and it costs because the crossing is far from her hearth.

---

## 7. Implementation: phases, costs, risks

Sizes are lead sessions (one session is about 300k tokens of a `su-lead-high`, with workers and runners under it and max judges for every look).

| Phase | What | Code | Art | Animation | VFX and sound | Who | Size |
|---|---|---|---|---|---|---|---|
| **1. Systems** | The Lamps' data (`Content/Lamps.cs`, `data/content/lamps.json`), lamps from levels and fights, respec and layouts, the night/day rule, leans; the new tags and Bound; reflexes (arts become triggers); dash forms (Kin into the dash, `ArtBook` migration); the Flare meter, window and clutch; `Act` renames and the bindings and save migration; the harness taught types, lamps and Flares; tests | large | none | none | none | combat (systems) lead + workers | 3 |
| **2. The beat and four Flares** | The shared beat (time, grade, camera push, hitstop, last blow); one Flare per calling on grips we already have: Sixty on the Wall (sword and shield), Bone-Toll (axes), Skyfire (staff), A Hundred Cuts (daggers) | small | spectral Watch bearers | 4 Flare clips, hers first | 4 Flares, the beat | experience (camera, time), skills VFX (look, sound), animation | 3 |
| **3. The Lamps screen and the Flare on the HUD** | UI design brief (a board of lamps over the live world, our panel rules) and UI art (lamps, blue lamps, roads; the Flare as the instrument's centerpiece) | medium | lamp glyphs, board | none | the full Flare's breath | UI design (su-lead-max brief), UI art | 2 |
| **4. New grips** | Greatsword, hooked chain and longbow as items and props (two-handed rule in `Items`; twin blades reuse the daggers, twin axes the axes); clips per grip: idle, run, two swings, heavy, hit, for her (him later) | small | 3 props | about 18 clips | swing trails | loot (items), outfits or arena art (props), animation | 3 |
| **5. New skills** | 16 skills, 32 evolutions, 4 unions: logic, harness balance, look and sound, names from story | medium | none | none | 52 pieces | combat, skills VFX, story (names) | 4 to 5 |
| **6. The other twelve Flares** | as phase 2 | small | per Flare | 12 Flare clips | 12 Flares | as phase 2 | 5 |
| **7. Tuning and teaching** | A balance sweep (types, lamps, Flares at tiers 1 to 4 and endless); the first-hour teaching (creation's type cards, the first lamp, the first Flare); the codex's text | small | type cards' clips | none | none | combat, experience, story | 1 to 2 |

**Acceptance (the harness and judges):**
- every type within ×1.35 of the median at tiers 1 to 4 (the paths' band);
- on-calling at most ×1.25 over the same skills off-calling;
- the first Flare by about 2 minutes, then one every 60 to 90 s at night, two or three in a boss fight, and Flares at 15 to 25% of a boss's damage;
- every Flare judged at 1:1 in a packed horde and on a boss, against §3.5's laws.

**Risks:**
1. **Animation is the long pole.** That's 16 Flare clips and about 18 grip clips, twice over once the male hero has his own. Mitigation: phase 2 proves the beat on grips we have; the hero follows hers.
2. **Performance.** Sixteen Flares over 300 creatures. Each Flare gets a budget from the rendering lead (particles, lights, overdraw) before it's built.
3. **Readability.** Flares must never hide a danger mark. Enemy marks draw on top, and Flares hold below the knee (§3.5).
4. **The night's balance.** The Flare is new power at night. The ember curve (§11) is re-measured, and story bosses' health may rise.
5. **Opacity and trap lamps.** About 344 lamps of text. Mitigations: one line each, "feeds" glyphs, dimming, Light my way, free respec.
6. **Migration.** Saved arts become dash forms, bindings move, and existing saves get a full refund of lamps.
7. **Name and tone.** About 400 new names; the story lead checks each for the valley's voice and Act 1 safety.
8. **Scope.** If tokens or time press, phases 1 to 3 alone give the owner class identity and four awesome Flares; the rest can follow by calling.

---

## 8. Open questions for the owner

1. **Ultimates locked to the calling?** *Recommend yes:* they're the identity, and the only hard lock. Everything else stays open to everyone.
2. **Free respec by day at any town lamp-post, with two saved layouts?** *Recommend yes:* planning is only fun when trying is free.
3. **Pick the type at creation?** *Recommend yes,* for the starting grip and first Flare, but never a lock: the Lamps decide what you become.
4. **Q / right-click becomes the Flare, the draught stays on R, and the movement art moves into the dash?** *Recommend yes.*
5. **The names "the Lamps" (tree) and "the Flare" (ultimate)?** *Recommend yes,* with the story lead checking the voice.
6. **About 50 lamps at the very end (levels, story bosses, the atlas), with no open-ended climb?** *Recommend yes;* it keeps §14.1's reasoning.
7. **First build: the systems plus one Flare per calling** (Sixty on the Wall, Bone-Toll, Skyfire, A Hundred Cuts), so you can play the look before the rest? *Recommend yes.*
8. **The freeze on every Flare (0.22 s), even in endless?** *Recommend yes:* it's the dopamine. A setting can shorten it.

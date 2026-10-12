# The four quarters, the bridges, the crossings and the sixteen Flares (docs/design/CLASSES.md §2.8-2.9, §3.6-3.7).
# Read by lamps_build.py (exec'd there: M, A, R, F, RX, FL, FM, hearth, road, bridge, crossing, flare are its).
# Names are drafts until the story lead has read them for the valley's voice (§4, risk 7).

THIRD = round(1 / 3, 4)

# ------------------------------------------------------------------ Flares --
# Phase 1 plays each as its kind's plain form (Lamps.cs FlareDef); phase 2 stages the first four, phase 6 the rest.
# power: each blow's damage at level 1. A Strike's blows land over its length; a Stand pulses `blows` a second.
flare("the_long_cut", "The Long Cut", "warden", "sunderer", "strike", 0.8, 12, 2, 1380, "holy", ["melee", "area", "heavy", "holy"], "A sweep of dawn 12 m round, then a cleave down a 24 m line.")
flare("dawn_in_the_steel", "Dawn in the Steel", "warden", "sunderer", "stand", 6, 10, 2, 345, "holy", ["melee", "area", "heavy", "holy"], "For 6 s the blade burns with morning: faster swings, crescents of light, every heavy blow staggers.")
flare("bell_of_the_morning", "Bell of the Morning", "warden", "bulwark", "strike", 0.9, 14, 3, 920, "holy", ["area", "holy", "shield"], "Three tolls on the shield: each stuns and sears everything near, and mends you 4%. The last is a holy blast 8 m round.",
      beat={"first": 0.3, "step": 0.25, "hitstop": 4, "hitstopLast": 8},
      args={"toll": 0.45, "blast": 1.25, "blastRadius": 8, "stun": 1, "sear": 2, "mend": 0.04, "peal": 0.08, "stagger": 15, "flee": 3})
flare("sixty_on_the_wall", "Sixty on the Wall", "warden", "bulwark", "stand", 6, 7, 1, 345, "holy", ["area", "holy", "shield"], "For 6 s the Watch's shield-bearers hold an arc in front of you.", "cut", 0.5)
flare("the_butchers_bill", "The Butcher's Bill", "reaver", "butcher", "strike", 1.2, 10, 6, 520, "physical", ["melee", "steel", "physical", "twin"], "A leap on the strongest near you, and a chop for each tenth of health you're missing.")
flare("butchers_hour", "Butcher's Hour", "reaver", "butcher", "stand", 8, 4, 0, 290, "physical", ["melee", "steel", "physical", "twin"], "For 8 s: Frenzy full, blows twice as fast, every blow bleeds, ordinary things below 15% die, and each kill adds 0.3 s and mends 1%.",
      beat={"key": 0.3, "hitstop": 1, "hitstopExecute": 4},
      args={"faster": 2, "bleed": 0.4, "bleedSeconds": 3, "execute": 0.15, "extend": 0.3, "overtime": 0.6, "mend": 0.01, "mistRadius": 5, "flee": 1.5})
flare("drag_them_under", "Drag Them Under", "reaver", "chainbound", "strike", 0.8, 14, 2, 1590, "physical", ["melee", "physical", "area", "hook"], "Hooks bite everything within 14 m and haul them into one knot for the slam.")
flare("storm_on_the_chain", "Storm on the Chain", "reaver", "chainbound", "stand", 5, 8, 2, 400, "storm", ["melee", "storm", "area", "hook"], "For 5 s the chain sweeps 8 m out, and the sky strikes down it.")
flare("burns_twice", "Burns Twice", "arcanist", "kindler", "strike", 1.1, 14, 12, 1160, "fire", ["spell", "fire", "frost", "area"], "Frost races under every pack near, then twelve embers fall on the frozen ground, and each shatters what is frozen round it.",
      beat={"key": 0.15, "frost": 0.3, "first": 0.55, "last": 1.05, "hitstop": 2, "hitstopLast": 6},
      args={"frost": 0.3, "freeze": 2, "chill": 3, "ember": 0.675, "shatter": 1.0, "emberRadius": 2.5, "onBoss": 4, "moreEmbers": 18, "blackIce": 0.5})
flare("hard_winter", "Hard Winter", "arcanist", "kindler", "stand", 6, 12, 1, 345, "frost", ["spell", "frost", "area", "zone"], "For 6 s the ford's cold: everything near slows and freezes, and the thaw bursts.")
flare("the_branding", "The Branding", "arcanist", "moonweaver", "strike", 1.0, 14, 2, 2100, "arcane", ["spell", "arcane", "area"], "Every enemy near is branded; the brands burst outward, each death passing a mark.")
flare("the_drowned_moon", "The Drowned Moon", "arcanist", "moonweaver", "stand", 6, 5, 3, 255, "arcane", ["spell", "arcane", "projectile", "zone"], "For 6 s a pool of moonlight follows you and looses motes.")
flare("the_roads_toll", "The Road's Toll", "stalker", "roadknife", "strike", 1.2, 12, 12, 2100, "physical", ["melee", "steel", "physical", "twin"], "Gone in smoke: twelve cuts in 1.2 s on the strongest near, each poisoned, and anything below 25% dies. On a boss, the last four.",
      beat={"key": 0.24, "first": 0.24, "last": 1.12, "hitstop": 1, "hitstopLast": 6},
      args={"poison": 0.5, "poisonSeconds": 4, "execute": 0.25, "lastCut": 0.4, "onBoss": 4, "doubled": 18, "gone": 3})
flare("through_and_through", "Through and Through", "stalker", "roadknife", "stand", 6, 3, 2, 290, "physical", ["melee", "steel", "physical"], "For 6 s your dashes are free and endless, and every one cuts.")
flare("one_arrow", "One Arrow", "stalker", "verge_hunter", "strike", 0.9, 30, 1, 2990, "physical", ["projectile", "ranged", "physical"], "One arrow down a 30 m line, splitting three times on the toughest.")
flare("pinning_rain", "Pinning Rain", "stalker", "verge_hunter", "stand", 5, 6, 3, 205, "physical", ["projectile", "ranged", "physical", "area"], "For 5 s arrows rain on ground 12 m across, rooting what they strike.")

P_FIRST = 2   # the four Flares phase 2 stages
P_REST = 6

# ------------------------------------------------------------------ warden --
w = hearth("warden",
    ("The Warden's Oath", "Your dash form is Bull Rush: every 8 s the next dash is a 6 m charge behind a barrier of 15% of health. What's in the way is thrown aside; a champion stops it, stunned."),
    ("bull_rush", 8),
    [("iron_hide", "Iron Hide", "Bull Rush's barrier is 25% of health."),
     ("pile_driver", "Pile Driver", "The rush ends in a slam that stuns everything 3 m round."),
     ("unbroken", "Unbroken", "Each thing the rush strikes adds 2% of health to the barrier."),
     ("gore", "Gore", "What the rush strikes bleeds, and champions take half again.")],
    ("Shield Bash", "When three or more things, or a champion, are within 2.5 m: bash. They're thrown back and stunned 1.5 s, and a channel breaks. Every 7 s.",
     "shield_bash", "crowd", 7, {"count": 3, "radius": 2.5}),
    [(F("shield_bash", "concussion"), "Concussion", "Shield Bash stuns a second longer."),
     (F("shield_bash", "shield_wall"), "Shield Wall", "Shield Bash gives a barrier of 8% of health for each thing struck, to 40%.")],
    ("Braced", "A blow that takes a seventh of your health or more plants you for 3 s: blows cut by 65%, arrows turned back. Every 20 s.",
     "bulwark", "big_blow", 20, {"share": round(1 / 7, 4)}),
    [(F("bulwark", "rallying"), "Rallying Stand", "Mend 4% of health a second while braced.")],
    [("Kindled Oath", "Blows taken fill the Flare 20% faster.", R("flare.hurt_fill", more=0.2)),
     ("Last at the Crossing", "A Flare cast below a third of health also gives a barrier of 30% of health.", R("flare.low_barrier", below=THIRD, barrier=0.3))],
    ("Hold Fast", "You can't be thrown, stunned or slowed. Your dash is 30% shorter.", [R("hold_fast", dash=0.3)]))

sund = road("warden", w, "sunderer", "Road of the Sunderer", "Slow, huge blows that split the ground.",
    ("Two Hands", "Heavy blows stagger ordinary things for 0.4 s.", [R("heavy.stagger", phase=4, seconds=0.4)]),
    [("Heavy blows strike 12% harder at staggered things.", [R("heavy.vs_staggered", phase=4, more=0.12)]),
     ("Heavy and nova skills reach 8% wider.", [R("tags.area", tags="heavy,nova", inc=0.08)]),
     ("+2 Might.", [A("might")]),
     ("Staggered things take 10% more holy.", [R("staggered.holy", phase=4, more=0.1)]),
     ("+2 Might.", [A("might")]),
     ("Each heavy blow landed in the last 3 s gives +1 armor, to +10.", [R("heavy.armor", phase=4, per=1, cap=10, seconds=3)]),
     ("Standing still, Sunder reaches 10% further.", [R("sunder.still_reach", phase=5, inc=0.1)])],
    [("sunder", [("Wide Swing", "Sunder's arc is 300°.", [R("sunder.wide_swing", phase=5)]),
                 ("Third Blow", "Every third swing of Sunder is heavy.", [R("sunder.third_blow", phase=5)]),
                 ("Burning Edge", "Sunder's heavy line sears.", [R("sunder.burning_edge", phase=5)])]),
     ("groundbreaker", [("Twin Cracks", "Groundbreaker opens two cracks, splayed 30°.", [R("groundbreaker.twin", phase=5)]),
                        ("Fault Line", "Groundbreaker's cracks run 14 m.", [R("groundbreaker.fault_line", phase=5)]),
                        ("Upheaval", "Lesser things heaved are thrown up 0.8 s, and take 30% more while airborne.", [R("groundbreaker.upheaval", phase=5)])]),
     ("dawnpulse", [("Dawn Rhythm", "Dawnpulse fires when you land a heavy blow instead of on its timer, at most every 1.5 s.", [R("dawnpulse.rhythm", phase=4, every=1.5)]),
                    ("Wider Morning", "Dawnpulse reaches 20% wider.", [R("skill.area", skill="dawnpulse", inc=0.2)]),
                    ("Searing Light", "Dawnpulse sears what it strikes.", [R("skill.status", skill="dawnpulse", status="sear")])])],
    [("Breaking Point", "Champions fill a stagger bar from heavy blows and break for 1.5 s.", [R("breaking_point", phase=4, seconds=1.5)], ["sunder", "groundbreaker"]),
     ("Sundered", "Heavy blows break armor: Sundered things take 20% more from heavy blows for 4 s.", [R("sundered", phase=4, more=0.2, seconds=4)], ["sunder"]),
     ("Momentum of the Blade", "A melee swing that kills three makes that skill's next swing come 25% sooner.", [R("momentum", kills=3, sooner=0.25)], ["sunder", "oathblade"]),
     ("Morning in the Steel", "Heavy blows on seared things burst in holy light 3 m round.", [R("morning_in_the_steel", phase=4, radius=3)], ["sunder", "dawnpulse"]),
     ("Rooted Stance", "After 1 s standing still, heavy blows are 20% wider.", [R("rooted_stance", phase=4, inc=0.2)], ["sunder", "groundbreaker"])],
    [("Weight of the Oath", "Every blow you strike is heavy and always staggers: Sunder's line comes on every swing. You swing 45% slower, nothing can make you swing faster, and you never strike true.", [R("weight_of_the_oath", phase=4, slower=0.45)]),
     ("The Unbroken Line", "Sunder's heavy blow no longer splits a line: it breaks the ground all around you, 4 m, at half the blow.", [R("unbroken_line", phase=5, radius=4, share=0.5)])],
    ("the_long_cut", "The Long Cut", [
        ("Second Cut", "Another sweep 0.3 s later, inside the 1.2 s.", FM("the_long_cut", "long_cut.second_cut", P_REST)),
        ("Line of Morning", "The line burns for 4 s.", FM("the_long_cut", "long_cut.line_of_morning", P_REST)),
        ("Through the Wall", "The line runs 36 m, and Sundered is 40% weaker armor on bosses.", FM("the_long_cut", "long_cut.through_the_wall", P_REST))]),
    ("dawn_in_the_steel", "Dawn in the Steel", [
        ("High Morning", "It holds 8 s.", FM("dawn_in_the_steel", "dawn_steel.high_morning", P_REST)),
        ("Crescents Through", "Its crescents pierce everything.", FM("dawn_in_the_steel", "dawn_steel.crescents_through", P_REST)),
        ("Mending Light", "A kill by a crescent mends 0.5%.", FM("dawn_in_the_steel", "dawn_steel.mending_light", P_REST))]))

bulw = road("warden", w, "bulwark", "Road of the Bulwark", "Walk in, let them hit you, and they break on it.",
    ("Shield Arm", "Your shield turns one blow in seven. Every blow that reaches you, turned or not, lays a stone; at six, the wall answers with a rebuke of holy light 8 m all around you.",
     [R("shield_arm", block=0.15, stones=6, struck=1, radius=8, lull=6, rebuke=10, per_level=0.08)], ["oathblade"]),
    [("+5% block while you stand still.", [R("block.still", add=0.05)]),
     ("+5% block against champions' and bosses' blows.", [R("block.champions", add=0.05)]),
     ("+2 Resolve.", [A("resolve")]),
     ("Barrier is 15% stronger while you hold three stones or more.", [R("stones.barrier", at=3, more=0.15)]),
     ("+2 Resolve.", [A("resolve")]),
     ("Rebukes and the Watch Bell strike champions 15% harder.", [R("rebuke.champions", more=0.15)]),
     ("Each block mends 0.5% of health while you're above half.", [R("block.mend", share=0.005, above=0.5)])],
    [("oathblade", [("Shield and Edge", "After a block, Oathblade swings at once.", [R("oathblade.shield_and_edge")]),
                    ("Reaching Oath", "Oathblade reaches 1.5 m further.", [R("skill.reach", skill="oathblade", add=1.5)]),
                    ("Morning Edge", "Each Oathblade swing throws a crescent of light 6 m.", [R("oathblade.morning_edge", phase=5)])]),
     ("rebuke", [("Readier Wall", "The wall answers at five stones.", [R("rebuke.readier", phase=5)]),
                 ("Rebuke the Strong", "Rebuke strikes champions twice as hard.", [R("rebuke.strong", phase=5)]),
                 ("Answering Light", "Each rebuke mends 1% of health.", [R("rebuke.answering", phase=5)])]),
     ("watch_bell", [("Loud Bell", "The Watch Bell draws from 10 m.", [R("watch_bell.loud", phase=5)]),
                     ("Iron Bell", "What the bell draws in is slowed 30%.", [R("watch_bell.iron", phase=5)]),
                     ("Bell and Barrier", "Each thing the bell draws gives a barrier of 3% of health.", [R("watch_bell.barrier", phase=5)])])],
    [("Mortar", "Stones last through a lull, and each block gives a barrier of 1% of health.", [R("mortar", barrier=0.01)], ["oathblade"]),
     ("Turned Arrows", "Blocked missiles fly back at whoever loosed them.", [R("turned_arrows")], []),
     ("Planted", "+15% block while you stand still.", [R("block.still", add=0.15)], []),
     ("Heavy Shield", "Blocking a champion's blow stuns it 0.5 s.", [R("heavy_shield", seconds=0.5)], []),
     ("Faith in the Wall", "While your barrier is above a fifth of health, holy damage is 20% higher.", [R("faith_in_the_wall", at=0.2, inc=0.2)], ["rebuke", "watch_bell", "dawnpulse"])],
    [("The Wall Holds", "Block chance is doubled, to 75% at most, but you can't block while moving.", [R("wall_holds", cap=0.75)]),
     ("Bearer of Blows", "What you block isn't lost: it's stored, and let out as holy damage by your next rebuke. You mend 30% less.", [R("bearer_of_blows", less=0.3)])],
    ("bell_of_the_morning", "Bell of the Morning", [
        ("Fourth Toll", "The bell tolls a fourth time.", FM("bell_of_the_morning", "bell.fourth_toll", P_FIRST)),
        ("Bell for the Dead", "Lesser things flee for 3 s after the last toll.", FM("bell_of_the_morning", "bell.for_the_dead", P_FIRST)),
        ("Healing Peal", "Each toll mends 8%.", FM("bell_of_the_morning", "bell.healing_peal", P_FIRST))]),
    ("sixty_on_the_wall", "Sixty on the Wall", [
        ("Shield-Brothers", "The wall strikes out once a second.", FM("sixty_on_the_wall", "sixty.shield_brothers", P_REST)),
        ("The Wall Walks", "The wall moves with you.", FM("sixty_on_the_wall", "sixty.wall_walks", P_REST)),
        ("Night Watch", "It holds 9 s.", FM("sixty_on_the_wall", "sixty.night_watch", P_REST))]))

bridge("warden", sund, bulw,
    [("+2 Might.", [A("might")]), ("Heavy blows and blocks each make the next 10% harder, for 2 s.", [R("heavy_block.chain", phase=4, more=0.1)]), ("+2 Resolve.", [A("resolve")])],
    ("Shield Swing", "Heavy blows lay stones, and each block makes the next heavy blow 30% harder.", [R("shield_swing", phase=4, more=0.3)], ["sunder"]),
    ("Sword-and-Board", "You may carry a greatsword and a shield together. The greatsword strikes 15% slower, and the shield blocks half as often.", [R("sword_and_board", phase=4, slower=0.15, block=0.5)]),
    ("Oath and Bell", "The Watch Bell tolls when you stagger something, at most every 3 s.", [R("oath_and_bell", phase=5, every=3)], ["watch_bell"]))

# ------------------------------------------------------------------ reaver --
rv = hearth("reaver",
    ("The Reaver's Chain", "Your dash form is Grapple Chain: every 6 s the next dash throws the hook up to 12 m at the first thing in its aim and hauls you to it. With nothing to bite, it's a plain dash."),
    ("grapple", 6),
    [("whirling_chain", "Whirling Chain", "On landing, the chain whirls, striking everything 3 m round."),
     ("anchor", "Moored", "Landing gives a barrier of 12% of health."),
     ("second_hook", "Second Hook", "A kill within 3 s of the haul brings the wait back."),
     ("reel", "Reel", "Lesser things are dragged to you instead.")],
    ("War Cry", "Ten or more things within 5 m, or a champion strikes you: roar. Lesser things flee 2.5 s, and you strike 25% harder for 6 s. Every 16 s.",
     "warcry", "swarm", 16, {"count": 10, "radius": 5}),
    [(F("warcry", "terror"), "Terror", "Champions flee the roar too, for a second."),
     (F("warcry", "bloodlust"), "Bloodlust", "You run 20% faster while the roar drives you.")],
    ("Red Tide", "Below a third of health: a red roar that mends 10% of health and drives you 30% harder for 4 s. Every 25 s.",
     "red_tide", "low", 25, {"below": THIRD}),
    [(R("red_tide.second", wait=18), "Second Tide", "Red Tide comes every 18 s.")],
    [("Blood for the Flare", "Kills by a bleed fill the Flare as a champion's kill does, a tenth as much.", R("flare.bleed_kill", fill=0.2)),
     ("Not Done Yet", "A Flare cast below a third of health mends half again as much.", R("flare.low_mend", below=THIRD, more=0.5))],
    ("Nothing Spared", "All mending is 50% stronger. You have no draught.", [M("healing", 0.5), R("no_draught")]))

butch = road("reaver", rv, "butcher", "Road of the Butcher", "Twin axes, and you fight best bleeding.",
    ("Red Hands", "Each hit gives +1% attack speed (Frenzy), to 20; it fades when the fight lulls.", [R("frenzy", per=0.01, cap=20, fade=3)], ["axe_gyre", "carve"]),
    [("Bleeding things take 10% more from melee.", [R("bleeding.melee", more=0.1)]),
     ("Bleeds last 20% longer while Frenzy is at ten or more.", [R("frenzy.bleed_longer", at=10, inc=0.2)]),
     ("+2 Might.", [A("might")]),
     ("Below half health, kills mend 0.5% of health.", [R("low.kill_mend", below=0.5, share=0.005)]),
     ("+2 Might.", [A("might")]),
     ("Thrown steel strikes bleeding things 12% harder.", [R("tags.vs_bleeding", tags="thrown", more=0.12)]),
     ("Frenzy fades half as fast.", [R("frenzy.slow_fade", share=0.5)])],
    [("carve", [("Four Chops", "Carve chops four times.", [R("carve.four", phase=5)]),
                ("Deeper Cuts", "Carve's bleeds run 30% deeper.", [R("carve.deeper", phase=5)]),
                ("Reaching Chops", "Carve reaches 1.5 m further.", [R("carve.reaching", phase=5)])]),
     ("hurled_cleaver", [("Two Cleavers", "Two cleavers fly.", [R("cleaver.two", phase=5)]),
                         ("Ricochet", "The cleaver strikes a second bleeding thing on its way back.", [R("cleaver.ricochet", phase=5)]),
                         ("Another Way Back", "The cleaver comes back by another path.", [R("cleaver.way_back", phase=5)])]),
     ("axe_gyre", [("Bleeding Gyre", "Axe Gyre's axes make what they strike bleed.", [R("skill.status", skill="axe_gyre", status="bleed")]),
                   ("Wide Gyre", "Axe Gyre whirls 25% wider.", [R("skill.area", skill="axe_gyre", inc=0.25)]),
                   ("Gyre on a Kill", "A kill by the axes brings Axe Gyre's next whirl 30% sooner.", [R("skill.kill_sooner", skill="axe_gyre", sooner=0.3)])])],
    [("Deep Frenzy", "Frenzy builds to 40.", [R("frenzy.deep", cap=40)], ["axe_gyre", "carve"]),
     ("Fights Best Hurt", "Below a third of health, blows strike 30% harder and kills mend 1%.", [R("fights_best_hurt", below=THIRD, more=0.3, mend=0.01)], []),
     ("Open Vein", "A blow on a thing bleeding for 3 s or more bursts the bleed.", [R("open_vein", seconds=3)], ["carve", "axe_gyre"]),
     ("Red Work", "Killing a bleeding thing mends 1% of health.", [R("red_work", share=0.01)], []),
     ("Hamstrung", "Bleeding champions are 20% slower.", [R("hamstrung", slow=0.2)], [])],
    [("Always Bleeding", "You always count as below a third of health for Fights Best Hurt and Blood Up. You can't be mended above half, and what would mend past it is lost.", [R("always_bleeding", cap=0.5)]),
     ("The Butcher's Count", "Each kill gives +1% damage for 10 s, to 50. You take more by half the Count.", [R("butchers_count", per=0.01, cap=50, seconds=10, price=0.5)])],
    ("the_butchers_bill", "The Butcher's Bill", [
        ("Running Tab", "The leftover chops can go on twice.", FM("the_butchers_bill", "bill.running_tab", P_REST)),
        ("Wide Chops", "Each chop strikes everything 2 m round.", FM("the_butchers_bill", "bill.wide_chops", P_REST)),
        ("Feast", "Each kill mends 10%.", FM("the_butchers_bill", "bill.feast", P_REST))]),
    ("butchers_hour", "Butcher's Hour", [
        ("Overtime", "A kill adds 0.6 s.", FM("butchers_hour", "hour.overtime", P_FIRST)),
        ("Red Mist", "Lesser things near you flee.", FM("butchers_hour", "hour.red_mist", P_FIRST)),
        ("Not Today", "While it holds, you can't fall below 1 health.", FM("butchers_hour", "hour.not_today", P_FIRST))]))

chain = road("reaver", rv, "chainbound", "Road of the Chainbound", "A hooked chain that drags the horde into knots, with lightning down it.",
    ("Hooked", "Chain Lash's hook leaves things Bound for 2 s: tethered where they stand, and taking more from what strikes an area.", [R("hooked", phase=5, seconds=2)], ["chain_lash"]),
    [("Bound things take 10% more from storm.", [R("bound.storm", more=0.1)]),
     ("Area skills strike 8% harder at Bound things.", [R("tags.vs_bound", tags="area", more=0.08)]),
     ("+2 Might.", [A("might")]),
     ("Shock lasts 20% longer on Bound things.", [R("bound.shock_longer", inc=0.2)]),
     ("+2 Wits.", [A("wits")]),
     ("Each Bound thing within 6 m gives +1 armor, to +10.", [R("bound.armor", per=1, cap=10, radius=6)]),
     ("Storm skills reach 10% further while three or more things are Bound.", [R("bound.storm_reach", at=3, inc=0.1)])],
    [("chain_lash", [("Double Lash", "Chain Lash lashes twice.", [R("chain_lash.double", phase=5)]),
                     ("Barbed Hook", "The hooked thing bleeds.", [R("chain_lash.barbed", phase=5)]),
                     ("Lash Back", "The lash cracks back the way it came.", [R("chain_lash.back", phase=5)])]),
     ("anchor", [("Two Anchors", "Two anchors land.", [R("anchor.two", phase=5)]),
                 ("Heavy Anchor", "The anchor's landing stuns 0.5 s.", [R("anchor.heavy", phase=5)]),
                 ("Live Anchor", "The anchor shocks what it binds.", [R("anchor.live", phase=5)])]),
     ("iron_palms", [("Palm on the Chain", "Iron Palms strike Bound things 20% harder.", [R("skill.vs_bound", skill="iron_palms", more=0.2)]),
                     ("Ringing Palm", "Iron Palms shock what they strike.", [R("skill.status", skill="iron_palms", status="shock")]),
                     ("Palm Storm", "Iron Palms strike 15% more often.", [R("skill.sooner", skill="iron_palms", sooner=0.15)])])],
    [("Fast Binding", "Bound lasts 4 s, and Anchor binds 7 m round.", [R("fast_binding", seconds=4, radius=7)], ["chain_lash", "anchor"]),
     ("Conductor", "Shock on a Bound thing leaps to every other Bound thing.", [R("conductor")], ["iron_palms"]),
     ("Short Leash", "Hooked things are dragged 2 m further.", [R("short_leash", phase=5, add=2)], ["chain_lash"]),
     ("Knot", "Eight Bound things close together are stunned 1 s.", [R("knot", count=8, radius=3, seconds=1)], ["anchor"]),
     ("Iron Reach", "Iron Palms strike Bound things from 6 m.", [R("iron_reach", reach=6)], ["iron_palms"])],
    [("The Long Chain", "Melee skills reach 3 m further and hook the last thing they hit. They strike 20% weaker.", [R("long_chain", reach=3, weaker=0.2)]),
     ("Lightning Rod", "Storm skills strike Bound things first, and 40% harder. You take 15% more from storm and fire.", [R("lightning_rod", more=0.4, price=0.15)])],
    ("drag_them_under", "Drag Them Under", [
        ("Deeper", "The hooks reach the whole screen.", FM("drag_them_under", "drag.deeper", P_REST)),
        ("Grinder", "The knot is shredded for a breath before the slam.", FM("drag_them_under", "drag.grinder", P_REST)),
        ("Hold Him", "A boss is pinned 3 s.", FM("drag_them_under", "drag.hold_him", P_REST))]),
    ("storm_on_the_chain", "Storm on the Chain", [
        ("Second Length", "A second chain; the sweeps alternate.", FM("storm_on_the_chain", "storm_chain.second_length", P_REST)),
        ("Earthing", "Each sky strike mends 1%.", FM("storm_on_the_chain", "storm_chain.earthing", P_REST)),
        ("Wide Lash", "The sweeps reach 11 m.", FM("storm_on_the_chain", "storm_chain.wide_lash", P_REST))]),
    grip=None)

bridge("reaver", butch, chain,
    [("+2 Might.", [A("might")]), ("Bleeding things are Bound 1 s on a hook.", [R("bleed.hook_bind", phase=5, seconds=1)]), ("+2 Resolve.", [A("resolve")])],
    ("Red Chain", "Bound things bleed; bleeding things stay Bound 1 s longer.", [R("red_chain", seconds=1)], ["chain_lash", "anchor"]),
    ("Cleaver on a Chain", "Hurled Cleaver flies on your chain, hooks what it hits and drags it to you. It no longer returns through the crowd.", [R("cleaver_on_a_chain", phase=5)]),
    ("Hook and Hatchet", "A blow on a Bound thing adds a stack of Frenzy.", [R("hook_and_hatchet")], ["axe_gyre", "chain_lash"]))

# ---------------------------------------------------------------- arcanist --
ar = hearth("arcanist",
    ("The Arcanist's Glass", "Your dash form is Mirror Step: every 8 s the next dash leaves two reflections where you stood. They draw what hunts you, and burst when broken."),
    ("mirror_step", 8),
    [("three_mirrors", "Hall of Mirrors", "Mirror Step leaves three."),
     ("cold_glass", "Cold Glass", "A breaking reflection chills everything it cuts."),
     ("fighting_reflections", "Fighting Reflections", "Your reflections strike at what comes for them."),
     ("glass_heart", "Glass Heart", "Each reflection that breaks mends 4% of health.")],
    ("Time Slip", "A blow that would take a quarter of your health, or a champion's mark closing on you: 3.5 s at a third of the speed. Every 30 s.",
     "time_slip", "dire", 30, {"share": 0.25}),
    [(F("time_slip", "borrowed_time"), "Borrowed Time", "Dashes come back three times as fast in the slip."),
     (F("time_slip", "deep_slip"), "Deep Slip", "In the slip, everything moves at a fifth.")],
    ("Spellward", "Whenever three of your spells land in one second: a barrier of 10% of health. Every 8 s.",
     "spellward", "spells", 8, {"count": 3, "barrier": 0.1}),
    [(R("spellward.thick", barrier=0.15), "Thick Ward", "Spellward's barrier is 15% of health.")],
    [("Kindling", "Spells that strike three or more things at once fill the Flare a little.", R("flare.spell_fill", count=3, fill=0.5)),
     ("Glass Clutch", "A Flare cast below a third of health leaves two reflections.", R("flare.low_mirrors", below=THIRD, count=2))],
    ("Unbound Casting", "Spells wait 30% less. You have 20% less health.", [R("unbound_casting", sooner=0.3), M("maxHealth", -0.2, kind="more", price=True)]))

kind = road("arcanist", ar, "kindler", "Road of the Kindler", "Fire and frost on the ground: freeze them, then shatter them.",
    ("Fire on Ice", "Fire striking a frozen thing shatters it, 2 m round, at half its blow.", [R("fire_on_ice", radius=2, share=0.5)], ["cinderfall", "rime_field"]),
    [("Burning things take 10% more from frost.", [R("burning.frost", more=0.1)]),
     ("Chill builds 15% faster on things standing in your fire.", [R("fire.chill_faster", inc=0.15)]),
     ("+2 Wits.", [A("wits")]),
     ("Zone spells last 15% longer while you stand in one.", [R("zone.longer", inc=0.15)]),
     ("+2 Wits.", [A("wits")]),
     ("Shatters strike champions 15% harder.", [R("shatter.champions", more=0.15)]),
     ("Frozen things take 10% more from fire.", [R("frozen.fire", more=0.1)])],
    [("cinderfall", [("Two Cinders", "Cinderfall drops two.", [R("cinderfall.two")]),
                     ("Wider Fall", "Cinderfall lands 25% wider.", [R("skill.area", skill="cinderfall", inc=0.25)]),
                     ("Slow Burning", "Cinderfall's burn lasts 50% longer.", [R("skill.burn_longer", skill="cinderfall", inc=0.5)])]),
     ("pyre_line", [("Cross of Fire", "A second line crosses the first.", [R("pyre_line.cross", phase=5)]),
                    ("Hedge of Fire", "The line is 12 m long.", [R("pyre_line.hedge", phase=5)]),
                    ("Rolling Wall", "The line rolls toward the pack.", [R("pyre_line.rolling", phase=5)])]),
     ("rime_field", [("Quick Frost", "Rime Field freezes after 1 s.", [R("rime_field.quick", phase=5)]),
                     ("Wide Field", "Rime Field is 30% wider.", [R("rime_field.wide", phase=5)]),
                     ("Shatter Field", "What thaws in Rime Field shatters.", [R("rime_field.shatter", phase=5)])])],
    [("Thermal Shock", "The shatter is 3 m round and strikes as hard as the blow.", [R("thermal_shock", radius=3, share=1)], ["cinderfall", "rime_field"]),
     ("Ashen Ground", "Your burning ground lasts 50% longer.", [R("ashen_ground", inc=0.5)], ["cinderfall", "pyre_line"]),
     ("Ford-Cold Ground", "Rime Field chills before it freezes.", [R("ford_cold", phase=5)], ["rime_field"]),
     ("Firebreak Wall", "Pyre Line stops missiles.", [R("firebreak_wall", phase=5)], ["pyre_line"]),
     ("Stand in Your Fire", "In your burning ground: +20% armor, and spells come 10% sooner.", [R("stand_in_fire", armor=0.2, sooner=0.1)], [])],
    [("Frostfire", "Burn and chill no longer cancel: your fire chills and your frost burns. Each is 30% weaker.", [R("frostfire", weaker=0.3)]),
     ("Ash Walker", "In your burning or frozen ground you take 40% less. Outside it, your spells are 15% weaker.", [R("ash_walker", less=0.4, weaker=0.15)])],
    ("burns_twice", "Burns Twice", [
        ("More Embers", "Eighteen embers fall.", FM("burns_twice", "burns.more_embers", P_FIRST)),
        ("Black Ice", "Frozen things below half health shatter even without an ember.", FM("burns_twice", "burns.black_ice", P_FIRST)),
        ("Called Down", "Every ember falls on the toughest frozen thing.", FM("burns_twice", "burns.called_down", P_FIRST))]),
    ("hard_winter", "Hard Winter", [
        ("Deep Winter", "It freezes after 1 s.", FM("hard_winter", "winter.deep", P_REST)),
        ("Thaw-Burst", "The thaw bursts twice as hard.", FM("hard_winter", "winter.thaw_burst", P_REST)),
        ("Winter Keeps", "Mend 2% a second while it holds.", FM("hard_winter", "winter.keeps", P_REST))]))

moon = road("arcanist", ar, "moonweaver", "Road of the Moonweaver", "Moonlight that hunts on its own and marks what it touches.",
    ("Moonmarked", "Motes mark what they strike; a marked thing that dies passes its mark to one more.", [R("moonmarked", passes=1)], ["seeking_motes", "moonwell"]),
    [("Marked things take 8% more from projectiles.", [R("marked.projectiles", more=0.08)]),
     ("Arcane projectiles fly 15% faster.", [R("tags.projectile_speed", tags="arcane", inc=0.15)]),
     ("+2 Wits.", [A("wits")]),
     ("A marked thing's death mends 0.3% of health.", [R("marked.kill_mend", share=0.003)]),
     ("+2 Wits.", [A("wits")]),
     ("Arcane strikes champions 10% harder while they're marked.", [R("marked.arcane_champions", more=0.1)]),
     ("Marks last 30% longer.", [R("marks.longer", inc=0.3)])],
    [("seeking_motes", [("Split Motes", "Seeking Motes split in two on a kill.", [R("motes.split")]),
                        ("Swift Motes", "Seeking Motes come 20% sooner.", [R("skill.sooner", skill="seeking_motes", sooner=0.2)]),
                        ("Heavy Motes", "Seeking Motes strike 25% harder and fly slower.", [R("skill.harder", skill="seeking_motes", more=0.25)])]),
     ("moonwell", [("Twin Wells", "Three wells may hang at once.", [R("moonwell.twin", phase=5)]),
                   ("Wide Well", "Wells fire at what passes within 9 m.", [R("moonwell.wide", phase=5)]),
                   ("Deep Well", "Wells hold 12 s.", [R("moonwell.deep", phase=5)])]),
     ("lantern_man", [("Two Lanterns", "Two wisps drift out.", [R("lantern_man.two", phase=5)]),
                      ("Far-Wandering", "The wisp drifts 50% further.", [R("lantern_man.far", phase=5)]),
                      ("Guttering", "The wisp bursts when it goes out.", [R("lantern_man.gutter", phase=5)])])],
    [("Silvered", "Marks pass to two, and the marked take 10% more.", [R("silvered", passes=2, more=0.1)], ["seeking_motes"]),
     ("Many Lights", "Spells loose one more projectile.", [R("tags.projectiles", tags="spell", add=1)], ["seeking_motes", "moonwell"]),
     ("Moon-Drawn", "Motes seek the marked first.", [R("moon_drawn")], ["seeking_motes"]),
     ("Still Water", "Moonwell lasts 50% longer and fires 30% faster.", [R("still_water", phase=5)], ["moonwell"]),
     ("Moonfire", "A mark that passes flares violet: the new bearer takes a tenth of the dead one's health as moonfire.", [R("moonfire", share=0.1)], ["seeking_motes", "lantern_man"])],
    [("The Echo", "Every spell fires again 0.5 s later at half strength. Spells wait 25% longer.", [R("the_echo", delay=0.5, share=0.5, longer=0.25)]),
     ("Crowded Sky", "Spells with projectiles loose two more, all seeking, and no two strike the same thing; each is 35% weaker.", [R("crowded_sky", add=2, weaker=0.35)])],
    ("the_branding", "The Branding", [
        ("Second Brand", "It brands again 1 s later.", FM("the_branding", "branding.second", P_REST)),
        ("Branded Deep", "The bursts are 50% wider.", FM("the_branding", "branding.deep", P_REST)),
        ("The Eye", "The boss is branded three times.", FM("the_branding", "branding.eye", P_REST))]),
    ("the_drowned_moon", "The Drowned Moon", [
        ("Full Moon", "Twice the motes.", FM("the_drowned_moon", "drowned.full_moon", P_REST)),
        ("Moonset", "It ends by bursting upward, 8 m round.", FM("the_drowned_moon", "drowned.moonset", P_REST)),
        ("Silver Tide", "Marks pass to three.", FM("the_drowned_moon", "drowned.silver_tide", P_REST))]))

bridge("arcanist", kind, moon,
    [("+2 Wits.", [A("wits")]), ("Marked things freeze 20% sooner.", [R("marked.freeze_sooner", inc=0.2)]), ("+2 Resolve.", [A("resolve")])],
    ("Two Schools", "Rime Field's frozen ground makes Lantern-Man flare twice as often.", [R("two_schools", phase=5)], ["rime_field", "lantern_man"]),
    ("The Ledger", "Some of them keep ledgers. Each fire or frost spell makes your next moon or shadow spell 30% harder, and the other way round. A spell of the same side twice running is 15% weaker.", [R("the_ledger", more=0.3, weaker=0.15)]),
    ("Cold Moon", "Motes chill what they strike; a frozen thing's mark passes when it shatters.", [R("cold_moon")], ["seeking_motes", "cinderfall"]))

# ----------------------------------------------------------------- stalker --
st = hearth("stalker",
    ("The Stalker's Spring", "Your dash form is Vault: every 6 s the next dash springs 6 m the way you aim, untouchable in the air, and leaves caltrops where you left."),
    ("vault", 6),
    [("volley", "Parting Volley", "In the air, knives are loosed back at where you left."),
     ("snare_line", "Caltrops Hold", "What steps on the caltrops is stuck 1.5 s."),
     ("light_feet", "Light Feet", "Landing gives back a dash."),
     ("nimble", "Nimble", "Vault's wait is a third shorter.")],
    ("Mark Prey", "Every 9 s the strongest thing in sight becomes your prey: it takes 50% more and dies below 20%.",
     "mark_prey", "every", 9, {}),
    [(F("mark_prey", "twin_marks"), "Two Prey", "The two strongest become prey."),
     (F("mark_prey", "executioner"), "Executioner", "Prey dies outright below 30%.")],
    ("Smoke Bomb", "A perfect dash throws smoke: 3 s unseen, and your strikes are sure. Every 12 s.",
     "smoke_bomb", "perfect", 12, {}),
    [(F("smoke_bomb", "choking"), "Choking Smoke", "The smoke hangs where it fell and poisons what breathes it.")],
    [("Hunter's Patience", "Perfect dashes fill the Flare half again as much.", R("flare.perfect_fill", more=0.5)),
     ("Into the Smoke", "A Flare cast below a third of health leaves you unseen for 2 s after.", R("flare.low_unseen", below=THIRD, seconds=2))],
    ("Light Step", "Three dash charges. Each dash is 30% shorter.", [M("dashCharges", 1, kind="flat"), R("light_step", shorter=0.3)]))

knife = road("stalker", st, "roadknife", "Road of the Roadknife", "Twin blades: every dash goes through the crowd.",
    ("Opening", "For 2 s after a dash, your blows strike true.", [R("opening", seconds=2)], ["twin_fangs", "knifestorm"]),
    [("Poisoned things take 10% more from steel.", [R("poisoned.steel", more=0.1)]),
     ("True strikes poison what they strike.", [R("true.poison", stacks=1)]),
     ("+2 Finesse.", [A("finesse")]),
     ("Dashes come back 8% faster while something within 4 m is poisoned.", [R("poison.dash_faster", radius=4, inc=0.08)]),
     ("+2 Finesse.", [A("finesse")]),
     ("Thrown steel strikes 12% harder within the Opening.", [R("opening.thrown", more=0.12)]),
     ("Poison lasts 20% longer on champions.", [R("poison.champions_longer", inc=0.2)])],
    [("twin_fangs", [("Third Fang", "Twin Fangs cut a third time.", [R("twin_fangs.third", phase=5)]),
                     ("Quick Fangs", "Twin Fangs come on every dash, even a plain one, twice as soon.", [R("twin_fangs.quick", phase=5)]),
                     ("Venom Fangs", "Twin Fangs' cuts each poison twice.", [R("twin_fangs.venom", phase=5)])]),
     ("cutting_wake", [("Wide Wake", "The wake is twice as wide.", [R("cutting_wake.wide", phase=5)]),
                       ("Lingering Wake", "The wake hangs 3 s.", [R("cutting_wake.lingering", phase=5)]),
                       ("Wake of Smoke", "The wake hides you while you stand in it.", [R("cutting_wake.smoke", phase=5)])]),
     ("knifestorm", [("Fan Out", "Knifestorm looses two more knives.", [R("skill.projectiles", skill="knifestorm", add=2)]),
                     ("Knives Return", "Knifestorm's knives come back through the crowd.", [R("knifestorm.return")]),
                     ("Poisoned Steel", "Knifestorm's knives poison.", [R("skill.status", skill="knifestorm", status="poison")])])],
    [("Wide Opening", "The Opening lasts 3 s.", [R("opening.wide", seconds=3)], ["twin_fangs", "knifestorm"]),
     ("Adder's Kiss", "Poison stacks to ten; at ten it bursts.", [R("adders_kiss", cap=10)], ["knifestorm"]),
     ("Through, Not Around", "Dashing through things cuts them, and each one cut gives back 2% of a dash.", [R("through_not_around", share=0.02)], ["cutting_wake"]),
     ("Slip the Blow", "The perfect dash's window is 50% longer.", [R("slip_the_blow", inc=0.5)], []),
     ("Venom Edge", "True strikes add two poison.", [R("venom_edge", stacks=2)], ["twin_fangs", "knifestorm"])],
    [("Never Still", "Dashes come back 40% faster. Standing still for a second halves your blows until you move.", [R("never_still", faster=0.4, weaker=0.5)]),
     ("Adder's Patience", "Poison stacks without limit and never fades while you keep striking. You can't strike true.", [R("adders_patience")])],
    ("the_roads_toll", "The Road's Toll", [
        ("Toll Doubled", "Eighteen cuts, in the same time.", FM("the_roads_toll", "toll.doubled", P_FIRST)),
        ("Last Cut", "The last blow kills below 40%.", FM("the_roads_toll", "toll.last_cut", P_FIRST)),
        ("Gone", "Unseen for 3 s after.", FM("the_roads_toll", "toll.gone", P_FIRST))]),
    ("through_and_through", "Through and Through", [
        ("Deeper Notches", "Each pass notches twice.", FM("through_and_through", "through.deeper", P_REST)),
        ("Wake of Blades", "The paths stay as Cutting Wake for 2 s.", FM("through_and_through", "through.wake", P_REST)),
        ("Free Hands", "It lasts 8 s.", FM("through_and_through", "through.free_hands", P_REST))]))

verge = road("stalker", st, "verge_hunter", "Road of the Verge-Hunter", "A longbow: far off, pinning the front.",
    ("Far Eye", "Blows from beyond 8 m strike true one time in four.", [R("far_eye", range=8, chance=0.25)], ["volley", "heartseeker"]),
    [("Projectiles strike 10% harder at rooted or slowed things.", [R("projectiles.vs_held", more=0.1)]),
     ("Arrows fly 15% further and faster.", [R("tags.projectile_speed", tags="ranged", inc=0.15)]),
     ("+2 Finesse.", [A("finesse")]),
     ("The prey takes 10% more from projectiles.", [R("prey.projectiles", more=0.1)]),
     ("+2 Finesse.", [A("finesse")]),
     ("Standing still, projectiles come 8% sooner.", [R("still.projectiles_sooner", sooner=0.08)]),
     ("Traps strike 12% harder at things beyond 8 m.", [R("tags.far", tags="trap", more=0.12, range=8)])],
    [("volley", [("Wide Volley", "Volley looses two more arrows.", [R("skill.projectiles", skill="volley", add=2)]),
                 ("Twice Fletched", "Volley's arrows pierce once more.", [R("skill.pierce", skill="volley", add=1)]),
                 ("Barbed", "Volley's arrows make what they strike bleed.", [R("skill.status", skill="volley", status="bleed")])]),
     ("heartseeker", [("Split Heart", "Heartseeker splits in two where it stops.", [R("heartseeker.split", phase=5)]),
                      ("Quick Draw", "Heartseeker comes every 2 s.", [R("heartseeker.quick", phase=5)]),
                      ("Heart of Thorns", "Heartseeker roots what it pierces.", [R("heartseeker.thorns", phase=5)])]),
     ("snare_line", [("More Snares", "Snare-Line lays half again as many.", [R("snare_line.more", phase=5)]),
                     ("Biting Snares", "The snares bleed what they hold.", [R("snare_line.biting", phase=5)]),
                     ("Snare and Burn", "The snares burn what they hold.", [R("snare_line.burn", phase=5)])])],
    [("Pinned", "Heartseeker roots lesser things it passes through.", [R("pinned", phase=5)], ["heartseeker"]),
     ("Run It Down", "When the prey dies, Spirit Herd's beasts run down the next strongest.", [R("run_it_down")], ["spirit_herd"]),
     ("Fletcher's Eye", "Projectiles pierce once more.", [M("pierce", 1, kind="flat")], ["volley", "heartseeker"]),
     ("Hold the Distance", "Blows from beyond 8 m strike 20% harder.", [R("hold_the_distance", range=8, more=0.2)], ["volley", "heartseeker"]),
     ("Spring Back", "Vault springs back from your aim, and landing looses a Volley.", [R("spring_back")], ["volley"])],
    [("Long Sight", "Blows from beyond 8 m strike 50% harder. Within 4 m, 30% weaker.", [R("long_sight", range=8, more=0.5, near=4, weaker=0.3)]),
     ("Hunter's Stillness", "After a second standing still, every arrow pierces everything. Moving, arrows can't pierce.", [R("hunters_stillness", after=1)])],
    ("one_arrow", "One Arrow", [
        ("Split Thrice More", "It splits three more times.", FM("one_arrow", "arrow.split", P_REST)),
        ("Pinned to the Earth", "Everything struck is rooted 2 s.", FM("one_arrow", "arrow.pinned", P_REST)),
        ("Through the Heart", "Triple crit damage on a boss.", FM("one_arrow", "arrow.heart", P_REST))]),
    ("pinning_rain", "Pinning Rain", [
        ("Follow the Hunter", "The field moves with you.", FM("pinning_rain", "rain.follow", P_REST)),
        ("Iron Rain", "The arrows stun.", FM("pinning_rain", "rain.iron", P_REST)),
        ("Thorned Rain", "Thornbloom grows where they fell.", FM("pinning_rain", "rain.thorned", P_REST))]))

bridge("stalker", knife, verge,
    [("+2 Finesse.", [A("finesse")]), ("After a dash, your next arrow strikes true.", [R("dash.true_arrow")]), ("+2 Wits.", [A("wits")])],
    ("Quick Hands", "After a dash, your next Volley looses at once.", [R("quick_hands")], ["volley"]),
    ("Close and Far", "Within 4 m your blades strike 30% harder, beyond 8 m your arrows do. In between, both are 15% weaker.", [R("close_and_far", near=4, far=8, more=0.3, weaker=0.15)]),
    ("Knife and Fletch", "Thrown knives pierce once more while you hold a bow.", [R("knife_and_fletch", phase=4)], ["knifestorm"]))

# --------------------------------------------------------------- crossings --
crossing("shambles", sund, butch,
    [("+2 Might.", [A("might")]), ("+2 Might.", [A("might")])],
    [("Bleeding things are staggered 20% longer.", [R("bleeding.stagger_longer", phase=4, inc=0.2)]), ("Melee strikes 8% harder at bleeding champions.", [R("tags.vs_bleeding_champions", tags="melee", more=0.08)])],
    ("Opened Up", "A heavy blow on a bleeding thing deals the rest of its bleed at once.", [R("opened_up", phase=4)], ["sunder", "carve"]),
    ("Cleaver's Weight", "Every third chop of Carve is heavy.", [R("cleavers_weight", phase=5)], ["carve"]))

crossing("night_road", chain, moon,
    [("+2 Wits.", [A("wits")]), ("+2 Might.", [A("might")])],
    [("Marked things are Bound 0.5 s longer.", [R("marked.bound_longer", seconds=0.5)]), ("Storm and arcane strike Bound marked things 10% harder.", [R("bound_marked.more", more=0.1)])],
    ("Lightning Leaps the Chain", "Storm that strikes a Bound thing runs to everything Bound.", [R("lightning_leaps")], ["iron_palms", "chain_lash"]),
    ("Moon on the Chain", "A marked Bound thing marks everything Bound to it.", [R("moon_on_the_chain")], ["seeking_motes", "anchor"]))

crossing("firebreak", kind, verge,
    [("+2 Wits.", [A("wits")]), ("+2 Finesse.", [A("finesse")])],
    [("Projectiles strike burning things 8% harder.", [R("projectiles.vs_burning", more=0.08)]), ("Traps last 20% longer on burning ground.", [R("traps.burning_longer", inc=0.2)])],
    ("Fire Arrows", "Arrows that pass through your burning ground catch fire.", [R("fire_arrows")], ["volley", "pyre_line"]),
    ("Frozen Snares", "Snares in Rime Field freeze what they hold.", [R("frozen_snares", phase=5)], ["snare_line", "rime_field"]))

crossing("duelists_road", knife, bulw,
    [("+2 Finesse.", [A("finesse")]), ("+2 Resolve.", [A("resolve")])],
    [("A perfect dash gives a barrier of 5% of health.", [R("perfect.barrier", share=0.05)]), ("Blocks give 1 s of the Opening.", [R("block.opening", seconds=1)])],
    ("Parry", "A perfect dash lays a stone.", [R("parry")], ["oathblade"]),
    ("Return Cut", "A block gives an Opening: your blows strike true for 1 s.", [R("return_cut", seconds=1)], ["twin_fangs", "oathblade"]))

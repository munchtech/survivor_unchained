# Lamps v2: the data and the sim rules (Classes 18, Phase 2)

The contract between the board's data (`tools/classes/lamps_v2.py` → `godot/data/content/lamps_v2.json`) and the fight (`godot/logic/Sim`). It follows CLASS_IDENTITY_AND_TALENTS.md §3.2-3.6. The layout (ids, kinds, regions, groups, positions, edges, gates) is `board_v2.json` from `tools/classes/board_v2.py`, and **it is frozen**: UI lays the Lamps screen out from it.

## The data

`lamps_v2.py` reads `lamps.json` (v1, built by `lamps_build.py`) and `board_v2.json`, and writes `lamps_v2.json`. That file has the same shape as `lamps.json` (`story`, `roads`, `flares`, `lamps`) plus `version: 2` and `groups` (copied from board_v2). Each lamp:
- **From board_v2:** `id`, `kind`, `region` (now also `ford`, `oldroad`), `group`, `calling`, `x`, `y`, `at`, `gate`.
- **`road`** = the board_v2 `group` (LampBook counts depth by it: "hearth", a road id, "{calling}.bridge", a crossing id, "ford", "path.{id}").
- **A kept v1 lamp** keeps its v1 `name`, `text`, `effects`, `feeds` and `early`. Its `at` and `gate` come from board_v2.
- **A new lamp** gets these from `lamps_v2.py`:
  - `name`: a draft. **`"draft": true`** marks it for the story writer.
  - `text`: one line.
  - `price`: blue lamps only; the red line, kept out of `text`.
  - `effects`.
  - `feeds` (skill ids, where it feeds named skills).
- **Gone:** the 72 v1 `skill` lamps (they become wicks).

Effects use v1's helpers (`M`, `A`, `R`, `F`, `FM`). **`phase`** has the same meaning as v1's: 1 = live now. A higher phase means inert until that phase's skills or systems land (4 = kindred moves, 5 = the valley's new skills and Turns not yet built). The test "every phase-1 rule is read by the fight" covers v2 too.

**Words (§3.6):**
- Every lamp is one line, in the board's voice (short, concrete, second person, American spelling), with numbers in the line.
- A small is never a bare "+n%": it names a condition or two tags.
- A notable is one rule that deepens or joins.
- A blue is a big rule; its price goes in `price`.
- By night a small gives nothing but its road's lean (v1's rule, CLASSES §2.10); a notable's sizes run at a quarter. Rites, links, Hand lamps and blue prices are rules, so they're in full.

## Rites (72): `R("rite", tags="<tag>", mech="<mech>", ...)`

A rite puts a calling's mechanic onto one tag. It works for whoever lights it: the mechanic's numbers come from the args or hands.json, never from her Hand being on. It dims when she carries no skill with the tag.

| mech | Whose | What a skill with the tag gets | Args |
|---|---|---|---|
| `heavy` | sunderer | the warden Hand's heavy blow: every `every`th firing is heavy (stun, knockback, stagger, from hands.json) | `every` (default the Hand's) |
| `stone` | bulwark | a blow on a champion lays a Stone (once a firing), as the Hand's Holy does | |
| `bleed` | butcher | what it strikes bleeds `share` of the hit over 3 s (feeds Frenzy) | `share` |
| `bind` | chainbound | the first thing struck each firing is Bound `seconds` (a champion half as long) | `seconds` |
| `ground` | kindler | its kills leave the arcanist Hand's ground. The school is the skill's if fire, frost or arcane; otherwise fire | |
| `mark` | moonweaver | what it strikes is Marked (Moonmarked's rules, if lit, apply) | `seconds` |
| `opening` | roadknife | for 2 s after a dash its blows strike true (the stalker Hand's window) | `seconds` |
| `far` | verge_hunter | its blows from beyond 8 m strike true one time in four (Far Eye) | `range`, `chance` |
| `hand` | the Old Roads | resolved by her calling: warden `heavy`, reaver `bleed`, arcanist `ground`, stalker `opening` | |

Where each kind goes:
- **Road rites** use the road's own mech.
- **Bridge rites:** rite1 uses the calling's first road's mech, rite2 the second's.
- **Crossing rites:** one per side; rite1 uses side A's calling and rite2 side B's (`groups[].callings` order), each with the mech of that calling's road nearest the crossing.
- **Old Road rites** use `hand`, with the path's school tags.

Rites are for her **off-road** skills: choose tags that the rite's own road doesn't already carry, and that at least one skill in `skills.json` has. Today that's area, spell, projectile, physical, melee, steel, shadow, holy, thrown, nova, nature, zone, fire, explosion, arcane, frost, storm, summon, aura, orbit, bounce, chain, heal, dot, beam. A rite on a tag with no skill yet (trap, hook, twin) is phase 4 or 5.

## Links (32): `R("link", trigger="<trigger>", wait=<s>, tags="<hint tags>")`

When the trigger comes and the link's wait is up, the skill she picked for this link fires once, free (`Weapons.Echo`); its own timer is untouched.
- **The pick** is saved per layout: `LampLayout.Links[lampId] = skillId`.
- **No pick, or the picked skill isn't carried:** Light my way's pick is the carried skill sharing the most tags with `tags`, ties broken by the order she carries them. With nothing carried, the link sleeps.
- **For the view:** the sim emits `Ev.Link { Lamp, Skill, X, Z }` when a link fires. Its wait is readable (`Battle.LinkWait(lampId)` → 0..1) for the HUD's arc, which is UI's to draw.

| trigger | When | Args |
|---|---|---|
| `block` | any block (a lamp's or the Warding light's) | |
| `dash` | any dash | |
| `heavy` | a heavy blow lands | |
| `champion_kill` | an elite or boss dies | |
| `hurt` | one blow takes `share` of health or more | `share` |
| `low` | she falls below half health | |
| `flare` | she presses a Flare | |
| `crowd` | `count` or more things within `radius` m (checked 4 times a second) | `count`, `radius` |
| `still` | after `seconds` standing still (then every wait while still) | `seconds` |
| `kills` | every `count`th kill | `count` |
| `status_kill` | something carrying `status` dies | `status` |

The wait is 4-12 s: the trigger's rarity sets it, never a skill's power.

## Hand lamps (16): `R("hand", <field>=<delta>, ...)`

They deepen her Hand by adding deltas to hands.json's numbers. The fields are hands.json's (warden: `every`, `stun`, `stones`, `rebuke`, ...; reaver: `per`, `cap`, `area`, `below`; arcanist: `radius`, `seconds`, `burn`, `cap`; stalker: `seconds`, `pierce`).
- The four in a hearth make a ladder: hand1 to hand4, each a step.
- Warden example: every 6 → 5 → 4, plus a lamp that lets heavy blows lay a stone.
- They are rules, so they're in full by night.
- They do nothing when the Hand is off (*Unhoused*).
- One may also carry a rule of its own (`hand.<calling>.<slug>`) where a pure number isn't the right deepening, but at most one per calling.

## Small and notable rules (new; one place in the sim, `Sim/BoardRules.cs`)

| rule | Args | Reads as |
|---|---|---|
| `tags.more` | `more`, optional `when` (a ModWhen name: Moving, Still, LowHealth, FullHealth, InBurning, AfterDash, Healthy), optional `vs` (a status: the struck must carry it) | "Fire and frost skills strike 6% harder at chilled things" |
| `tags.area` (v1) | `inc` | |
| `tags.sooner` | `sooner` (share off the wait) | |
| `tags.duration` | `inc` | |
| `tags.projectiles` (v1) | `add` (a count: by night +1 at most, board-wide) | |
| `tags.status` | `status`, `chance` | skills with the tags inflict a status |
| `tags.kill_mend` | `share` (of health) | kills by them mend her |

These take `tags` (any of them).
- **Smalls:** one effect with two tags, or one tag plus a `when`/`vs`.
- **Notables:** two effects that join two tags or two mechanics, or a v1 rule.
- **Hearth smalls** (`{calling}.hearth.p1/p2`) feed the calling's own mechanic: v1 rule ids at a small size, or `tags.*` on its Hand's tags.
- Attribute lamps: `A("might"|"finesse"|"wits"|"resolve")`, as in v1.

## The new blue lamps (17)

The rule ids are fixed; the content writes the args and the words.

| Lamp | rule | Rule | Price | Phase |
|---|---|---|---|---|
| `shambles.blue` | `blue.butchers_block` | heavy blows on bleeding things burst the bleed: all its damage at once | -20% maximum health | 1 |
| `night_road.blue` | `blue.tethered_stars` | Bound things count as Marked; a Bound thing that dies binds the two nearest for 2 s | spells come 20% slower | 1 |
| `firebreak.blue` | `blue.kindled_frost` | fire striking a chilled thing freezes it first (Fire on Ice then shatters it) | your frost skills strike 25% softer | 1 |
| `duelists_road.blue` | `blue.bell_and_blade` | a perfect dash counts as a block, and a block as a perfect dash | both windows 30% shorter | 1 if the sim has a perfect dash, else 4 |
| `vigil.blue` | `blue.vigil` | while you hold three stones or more, spells strike 30% harder | the wall never answers (no rebuke) | 1 |
| `poachers.blue` | `blue.poachers_mercy` | a blow that strikes true on a bleeding thing doubles its bleed | one dash charge | 1 |
| `ford.unhoused` | `blue.unhoused` | lamps on other callings' roads open with no depth (their gates are ignored) | your Hand is gone | 1 (LampBook and the Hand) |
| `path.steel.blue` | `blue.iron_pilgrim` | thrown skills return through you and strike again | you can't carry Projectile spells | 5 (the Return Turn) |
| `path.host.blue` | `blue.pack_remembers` | summons stay the night and grow 2% with every kill, to 40% | one dash charge | 1 if summons have a lifetime to lift, else 5 |
| `path.storm.blue` | `blue.lightning_rod` | storm and chain skills strike the nearest champion first, 40% harder | missiles strike you 25% harder | 1 |
| `path.grave.blue` | `blue.mourners_debt` | kills by shadow skills mend 1% of health | nothing else mends you | 1 |
| `path.weave.blue` | `blue.unspun` | arcane skills come 30% sooner | each arcane firing costs 1% of health | 1 |
| `path.pyre.blue` | `blue.pyre_walker` | burning ground never harms you, and standing in it you strike 25% harder | your burns last half as long | 1 |
| `path.rime.blue` | `blue.drowned_lung` | frost skills freeze in half the time | you can't be mended while you stand still | 1 |
| `path.wild.blue` | `blue.feral` | nature skills strike 40% harder while you move | you can't block or strike true | 1 |
| `path.hunt.blue` | `blue.long_watch` | blows from beyond 10 m strike 35% harder | blows within 4 m strike 35% softer | 1 |
| `path.dawn.blue` | `blue.unsetting_sun` | holy skills sear what they strike; a seared thing that dies mends you 0.3% | by night, holy skills come 20% slower | 1 |

**Who decides the phase:** the code lead, if a rule needs a system the sim lacks. That phase is reported, and the content follows it.

## The flag

- **v2 is the default** (game, harness and tests). v1 (`lamps.json`) stays reachable for one release: the env `SU_LAMPS_V2=0`, `Lamps.UseV2(false)`, or `--lampsv1` on the game or the harness.
- With v1 the sim is byte-identical to integration before v2 (the Act 1 gate).
- With v2:
  - unknown lit ids in a save are dropped on load (save v6 does the real migration);
  - the `--board` pages draw v2's lamps.

## By night (Classes 19-20; v2 only, by night only: day and v1 byte-identical)

Every lamp keeps its rule but not its size (CLASSES §2.10). What that means rule by rule:
- **Notables:** sizes at a quarter (`Size`, `SizeOn`).
- **Facets keep their rule, not their size** (`NightCut`, `GiftSize`): nimble, light_feet's speed, concussion and pile_driver stuns, snare hold, cold_glass, terror, executioner, deep_slip, borrowed_time, second_hook, reel and bloodlust at a quarter. A facet's own damage (gore's bleed, choking's poison) stays in full.
- **Blue gifts** at a quarter (wall_holds, bearer_of_blows, the BoardRules draft blues, and `flare.banked`'s banked bonus only: the Flare's own hit is unchanged). Prices stay in full, except the four that follow their gift (§2.10), Always Bleeding's among them: mends stop at 7/8 (`MendCeiling`).
- **Lamp barriers** (`Ward`, `LampBarrier`) at a quarter; a reflex's barrier (Shield Wall, Spellward) at a quarter of that, 1/16 (`LampBarrier(..., reflex: true)`).
- **A lamp reflex's numbers are sizes,** a quarter (`ReflexSize`, inside `RunReflex` only; a Hand art keeps its numbers): shield_bash stun, bulwark cut (`Player.BulwarkSize`), warcry fear and +%, red_tide mend and +%, time_slip's slowdown (world rate about 0.833), smoke_bomb unseen and sure strikes, mark_prey strength and execute line (`Enemy.PreySize`). The trigger (count, radius, wait) and the reflex's own hit stay in full.
- **Statuses a rule lays** carry its size (Frostfire's chill and burn at a quarter).
- Rites, links and Hand lamps keep their numbers in full.

## As built (the code lead, 2 November)

The sim side is `Sim/BoardRules.cs` plus guarded hooks (every one behind `LampLoadout.Board`, set when a v2 rule is lit). With v2 off the harness is byte-identical to before (full and empty lamps byte-for-byte; suggested the same lines). What the contract left open, and how the code reads it:
- **Args:** an `args` value that is a word (`mech`, `trigger`, `when`, `vs`, `status`) lands in `LampEffect.Words`; numbers in `Args`. `status` may also be the effect's own `status` field.
- **By night:** a small (v1 or v2) gives only its road's lean (the lead's ruling, 2 November: CLASSES §2.10 stands; the contract's first draft was wrong). Notables' sizes run at a quarter (`Size`, `SizeOn`); facets, blue gifts, barriers and reflex numbers too ("By night" above). Rites, links and Hand lamps are read in full.
- **`Battle.LinkWait(lamp)`** is the share of the wait still to run: 0 ready, 1 just fired. `Battle.LinkSkill(lamp)` is the skill it would fire now.
- **Links:** a `kills` link counts every kill, fires on the count-th if its wait is up (else on the next one that is); `crowd` and `still` are checked 4 times a second; `hurt` reads one blow after the shield; `low` is the crossing of half health.
- **Rites:** a heavy rite counts its own firings and applies only to skills the warden's Hand doesn't already make heavy. A stone rite makes the wall answer on hands.json's numbers for any calling.
- **Hand lamps:** `hand` deltas add to hands.json's number of the same name (`per_level` or `perLevel`); nothing when Unhoused. `hand.warden.heavy_stone` and `hand.stalker.second_wind` are built.
- **Blues, all phase 1 but Iron Pilgrim (5):** Bell and Blade is built (the sim has a perfect dodge): its "windows" are the perfect-dodge window and a lamp block's chance. Pack Remembers is built (summons have a lifetime: it is lifted; the growth is +`per` damage a kill of hers, to `cap`). Lightning Rod's 40% is on champions. Poacher's Mercy doubles a thing's bleed at most once a second. Unspun's cost never takes her last point of health. Mourner's Debt blocks every other mend (regen, draughts, lifesteal). Feral turns off the Warding light and lamp blocks. Drowned Lung's `faster` 0.5 = chill builds twice as fast from frost skills.
- **Stat prices** live in `LampBook.BluePrices`: Butcher's Block `health` (less maximum health, More), Poacher's Mercy and Pack Remembers `charges` (from the base two: one fewer; a gear charge still adds).
- **Unhoused:** "other callings' roads" = lamps with a calling that isn't hers; crossings, the Ford and the Old Roads keep their gates.
- **Points (Phase 2, session 2):** `LampBook.AtlasLamps` is 30 on v2 (8 on v1). `lamps.atlas` grows by one on each tier's first clear, any people (`Maps.Atlas.Complete`, fact `atlas.tier.<n>`): 16 tiers today; no atlas bosses exist yet. Relit lamp-posts: `LampBook.RelightPost(w, id)` sets `lampposts.<id>` for an id in lamps_v2.json `posts` (Act 1: `act1.post1`-`4`); each adds one to `Earned` (v2 only). Their placement is Env/story's.
- **Layouts:** three (`LampState.Count`), each with `Carried` (the day slots' skills). `LampBook.Switch(ch, index, world, zone)` swaps the whole build, carried skills included, only where `LayoutsOpen`: a town (`LampBook.Towns`), not `TimeOfDay.Night`, no map or arena under way. `Saves.Write` keeps the active layout's `Carried`.
- **Save v6** (`LampBook.MigrateSix`): three layouts, each refunded to its free lamps, wicks and link picks cleared (Light my way's strands), skills her calling can't carry to the storeroom as tomes (a shelf is added if it's full), the carried skills copied into each layout.

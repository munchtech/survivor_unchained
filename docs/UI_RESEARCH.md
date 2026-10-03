# UI research: what makes a game's interface fun, clear and easy

The theory and the genre references behind `UI_DESIGN.md`. Every rule the
design follows is traced to something here; the sources are listed at the
end. The audience is whoever touches the interface next: a designer, the art
agent, or the owner deciding whether a change is right.

Our game is two genres at once, and the research is read through that lens:

- **By day, an ARPG**: a town, people, quests, gear, a pack, skills learned,
  a journal, a map. Slow, deliberate, read at leisure.
- **By night, a survivors-style roguelite**: an arena, a horde, automatic
  weapons, a draft of cards every minute or so, blessings, a boss at the
  half hour. Fast, glanced at, decided in seconds.

The two halves want different interfaces (dense and browsable by day, sparse
and glanceable by night) that still read as one game.

---

## 1. How players perceive, attend and remember

### 1.1 Perception is built, not received
Celia Hodent (*The Gamer's Brain*, from her UX work on Fortnite at Epic)
starts from the fact that perception is subjective: players see what they
expect and what they are looking for, and miss the rest (inattentional
blindness). Two consequences for us:

- What matters must be *pre-attentively* distinct: it pops by colour, size,
  motion or shape before the player looks for it. Rarity, danger, "ready"
  and "new" are our pre-attentive signals and must never be spent on
  decoration.
- The player's attention in a fight is on the survivor and the horde
  around them. Anything that needs reading in a fight must sit there or be
  readable in peripheral vision (by colour and shape, not words).

### 1.2 Gestalt grouping
The Gestalt laws (Laws of UX: proximity, similarity, common region,
uniform connectedness, Prägnanz) decide what the eye reads as one thing.
For a game HUD:

- **Proximity**: what belongs together sits together (health with its
  shield and statuses; the dash with its charges).
- **Common region**: a frame says "this is one object" (a card, a slot, a
  tooltip). A frame round things that are *not* one object lies.
- **Similarity**: same function, same look, everywhere. A keycap is a
  keycap whether in the HUD, a hint or a menu footer.
- **Prägnanz**: simple shapes read fastest; ornament belongs on edges, not
  on the information.

### 1.3 Working memory is tiny
Miller's 7±2 is the folk number; modern estimates (Cowan) are nearer four
chunks. Hodent's "minimum workload" pillar and Nielsen's "recognition rather
than recall" say the same thing: never make the player remember what the
screen could show. In a survivors draft this is decisive: a card that says
"Rank 3 to 4" is only half an answer if the player cannot see *which* of
their skills it is and what else they hold.

### 1.4 Decision time and target size
- **Hick's law**: decision time grows with the number of choices (roughly
  logarithmically). Survivors-likes settle on three or four cards for a
  reason; ARPG top-level menus should stay short with depth behind them.
- **Fitts's law**: time to hit a target grows with distance and shrinks
  with size. On a pad the "distance" is the number of presses: the most
  common action must be zero or one press away, and focus must start on
  the likeliest choice.
- **Choice overload**: past a handful of options people choose worse and
  enjoy it less. Long lists need grouping (chunking) and a sensible default.

### 1.5 Response time
The **Doherty threshold** (Laws of UX): interaction feels fluent when the
system answers within about 400 ms. Every press must show *something* at
once (a highlight, a sound), even if the result animates for longer.

---

## 2. Usability frameworks

### 2.1 Nielsen's ten heuristics, read for a game
1. **Visibility of system status**: health, cooldowns, charges, what the
   ember is doing, what a press did. Status that changes in a fight must
   be visible without opening anything.
2. **Match with the real world**: our words are the fiction's words
   (ember, arts, the pack, the self) but each must still say what it does;
   where the fiction's word is opaque, the interface glosses it once.
3. **User control and freedom**: Back is always B / Escape and always does
   the same thing; nothing irreversible without a second step.
4. **Consistency and standards**: Jakob's law: players spend most of their
   time in *other* games. A on a pad confirms, B backs out, LB/RB change
   tabs, right-click equips in an ARPG, number keys pick cards.
5. **Error prevention**: the draft's half-second "armed" delay (a held key
   cannot spend a level) is exactly this; keep and extend it.
6. **Recognition over recall**: show the build beside the draft; show the
   worn item beside the one hovered; show the key on the button.
7. **Flexibility**: shortcuts for experts (hotkeys per screen, number keys)
   without removing the slow path (click, navigate).
8. **Aesthetic and minimalist design**: every element competes for
   attention; anything that is not needed *now* goes (a fight timer by day
   in a town is noise).
9. **Recover from errors**: a refused action says why ("You need 40 gold",
   "Take it in hand somewhere safe") and plays a distinct "no" sound.
10. **Help in context**: the parchment hint card that appears when a thing
    is first met, never a manual.

### 2.2 Hodent's two pillars
Hodent's framework splits game UX into **usability** and
**engage-ability**.

Usability pillars: *signs and feedback*, *clarity*, *form follows
function*, *consistency*, *minimum workload*, *error prevention and
recovery*, *flexibility*. Engage-ability rests on *motivation*
(self-determination theory), *emotion* (game feel, discovery, surprise)
and *game flow* (the difficulty curve and the learning curve). Her
practical rule for onboarding is learning by doing: teach a thing at the
moment it is needed, in context, and let the player do it straight away.

### 2.3 Game UI taxonomy (Fagerholt and Lorentzon, *Beyond the HUD*)
Two questions sort every element: is it in the fiction, and is it in the
3D space?

| | In the 3D space | On the screen plane |
|---|---|---|
| **In the fiction** | *Diegetic*: a lamp that is lit, a map on a table | *Meta*: the red bruise at the screen's edge when hurt |
| **Not in the fiction** | *Spatial*: names over heads, a ring under a boss's blow | *Non-diegetic*: the HUD, menus |

We already use all four: the Wayfinder's table and the notice board are
diegetic; names and barks are spatial; the bruise vignette and the pull
into an arena are meta; the HUD and screens are non-diegetic. The design
uses this deliberately: things the survivor would know (their wounds, the
dark) lean meta and diegetic; game rules (ranks, cooldowns) stay honest
non-diegetic UI.

---

## 3. Motivation, reward and feeling good

### 3.1 Competence, autonomy, relatedness
Rigby and Ryan's PENS model (self-determination theory applied to games,
*Glued to Games*) finds that games hold us when they satisfy three needs:

- **Competence**: the player feels they are getting better and *sees* it.
  Interfaces serve competence by making mastery legible: ranks rising,
  numbers growing, a skill evolving, "your longest arena yet".
- **Autonomy**: choices feel freely made and meaningful. The draft, the
  facets, the dialogue choices; the UI's job is to make each choice's
  consequences clear enough that it is a *choice*, not a guess.
- **Relatedness**: what you do matters to others. The journal's "Known
  to Holloway, Maeca" and the town's barks are relatedness made visible.

### 3.2 Goals in sight
- **Goal-gradient effect**: effort rises as a goal nears. The ember bar
  and the experience bar should make "nearly there" visible (a brighter
  leading edge, a glow in the last tenth).
- **Zeigarnik effect**: unfinished tasks stay in mind. A short, always
  visible objective tracker keeps the story's open threads in mind
  without a menu.
- **Peak-end rule** (Kahneman): an experience is remembered by its peak
  and its end. The arena's result screen is the end of a half hour;
  it must land (count up what was won, celebrate a record) rather than
  list it.

### 3.3 Rewards and their presentation
The psychology of Diablo III's loot (Jamie Madigan): unexpected rewards
release the most dopamine, and the multisensory cue ("the little 'ting!'
sound and seeing the beautiful, coloured text") is part of the reward, not
a wrapper on it. The anticipation before the reveal is often stronger than
the reveal. Rules we take: rarer things *look and sound* rarer (a ladder of
colour, light and sound), reveals take a beat, and the best moments get a
flourish (a card that evolves a skill is not presented like a +5% stat).

We take the presentation, not the exploitation: no artificial scarcity, no
spending prompts, no streak-loss pressure. Reward psychology is used to make
real achievements feel like achievements.

### 3.4 Juice and game feel
"Juice it or lose it" (Martin Jonasson and Petri Purho, GDC Europe 2012):
constant, bountiful feedback (things that bounce, flash and make a sound
when touched) makes a game feel alive and the player powerful. Jan Willem
Nijman's "The Art of Screenshake" makes the same case for impact. Masahiro
Sakurai on hitstop: a brief pause at impact lets the eye register the hit
and sells its force, and belongs in every genre.

For the interface: every interactive element answers hover and press
(highlight, a small scale, a tick), choices *land* (the chosen card
flares, the rest fall away), numbers count up instead of appearing, and
nothing animates longer than it needs to (Doherty).

### 3.5 Feeling clever
The best onboarding makes the player *discover* the rule, then feel clever
for it. Super Mario Bros. 1-1 teaches without a word: the level's layout
makes the first Goomba and the first block unavoidable, and the player
works out the rule themselves. In UI terms:

- Give the player the evidence and let them draw the conclusion: lighting a
  card's tags where the build already has them teaches synergy without a
  tutorial; lighting the skill a rank card would raise teaches "ranks go
  to things you hold".
- Name a thing *after* the player has done it (a codex entry, a "discovered
  in the arena" line), so the name confirms understanding instead of
  demanding it.
- Never explain in text what a highlight can show.

---

## 4. Seeing clearly

### 4.1 Hierarchy and the fight
In a horde game the play space is the centre of the screen; the HUD lives
at the edges and in the corners. Blizzard's Angela Del Priore (Diablo IV's
lead UI designer) reported that their action bar tested best at the bottom
centre on a PC monitor, and in the left corner when people sat further
from the screen; they offered both. The rule: the closer a thing is to the
action, the faster it is read, but the more it covers.

Survivors-likes resolve this by putting health *on the character*
(Vampire Survivors' bar under the hero, 20 Minutes Till Dawn's hearts):
the one number that can end the run is where the eyes already are.

### 4.2 Combat readability
Overwatch's art directors (GDC 2017) built the look around readability:
recognisable silhouettes, effects that never hide what threatens you.
Soulstone Survivors shows the cost of getting this wrong: players lose runs
because their own effects hide incoming attacks, and the game had to add a
"special effects visibility" slider. For us: threats (telegraphs, the boss)
own the warm-red end of the palette; the player's own effects stay below
them in brightness; the HUD never adds clutter to the centre.

### 4.3 Colour
- **Value before hue**: the eye reads light against dark first. Our panels
  are near-black iron; text is warm off-white; the few things that matter
  carry colour.
- **Colour means something or nothing**: gold for the interface itself and
  for "yours", ember orange for the night's power, blood red for health and
  danger, a cool blue for the day's growth and for shields.
- **Colour-blind safety**: about one man in twelve has a colour vision
  deficiency, mostly red-green. The Game Accessibility Guidelines' basic
  rule: never convey information by colour alone. Rarity carries a name
  and a mark count as well as a colour; good/bad deltas carry a sign (+/-)
  and an arrow; pad face buttons carry their letter. The Okabe-Ito palette
  (orange, sky blue, bluish green, yellow, blue, vermilion, reddish purple)
  is the reference for hues that stay distinct under every common
  deficiency.
- **Contrast**: WCAG asks 4.5:1 for body text and 3:1 for large text and
  the edges of interface components; we hold body text to 7:1 on our
  plates, since games are played at a distance and in motion.

### 4.4 Text
The Xbox Accessibility Guidelines (XAG 101) set minimum default text sizes
by body height: **18 px at 1080p on PC**, 26 px for console/TV distance;
text should scale to 200%; lines should stay under about 80 characters;
line spacing about 1.5; sentence case for sentences (all caps only for
one- or two-word labels); at least one plain sans serif option. Game
Accessibility Guidelines add: subtitles with a speaker name, a backing, and
at most about 38 characters per line at TV size.

Our current interface sets much secondary text at 12-14 px. The design
raises the floor (see the type scale in `UI_DESIGN.md`).

### 4.5 Motion and comfort
Screen shake and flashes must be optional (we have a shake setting).
Repeated full-screen flashes risk photosensitive seizures (WCAG 2.3.1: no
more than three flashes a second); a level-up flare should be a bright
burst that resolves into shape, not a strobe.

---

## 5. Pad and keyboard as equals

### 5.1 The 10-foot interface
Microsoft's guidance for TV and gamepad interfaces: focus must be
"clear and unmistakable" (a thin default focus rectangle is invisible from
a sofa), every element must be reachable with four directions plus select
and back, navigation must be predictable, and the path to the common task
must be short.

### 5.2 What the ARPGs did
- **Diablo II: Resurrected** switches its whole interface to a controller
  layout the moment a pad is touched: six skills on face buttons and
  triggers (six more under a held trigger), potions on the D-pad, an
  inventory remade for the pad, and loot spread out on the ground so it can
  be picked up with a stick.
- **Diablo IV** was built for both from the start: "unified" but not
  identical layouts, keeping keyboard and mouse conventions and adding pad
  shortcuts and alternative flows. Every skill slot is rebindable on both.
- **Path of Exile 2** uses a separate controller interface on PC and
  console; its players report that moving round the inventory with a pad
  is still clunky and too fast, which is the lesson: grid movement needs a
  deliberate repeat rate and a visible cursor.
- **Torchlight II** on console used a radial menu to jump to gear
  categories.

### 5.3 Conventions players already know (Jakob's law)
- A confirms, B backs out (and closes), X and Y are the secondary and
  tertiary action on the focused thing.
- LB/RB move between top-level tabs; LT/RT between sub-pages.
- The D-pad and the left stick both move focus; holding repeats after a
  short delay.
- View/Back opens the inventory or the character hub; Menu/Start pauses.
- Prompts follow the device last touched, at once.

---

## 6. Learning without being taught

- **Progressive disclosure** (Nielsen, 1995): show what is needed now,
  reveal depth on demand. In a game: hide the six empty weapon slots by
  day (they mean nothing until the night), reveal facets only when a rank
  opens one, show affix detail on a hold or a second look.
- **Just-in-time hints**: our hint card appears when a thing is first met.
  The design keeps it and makes its key prompt follow the device.
- **Show the consequence before the commitment**: Hades says on a boon card
  which slot it fills and what it would replace. The same rule gives the
  draft its build strip and the pack its side-by-side comparison.

---

## 7. The genre, game by game

### 7.1 ARPGs (the day)

**Diablo IV.** Health and resource as globes either side of a centred
skill bar; a minimap top right with the quest tracker under it. The UI team
dropped variable item sizes in the inventory to "avoid interrupting gameplay
with pockets of inventory management", moved item icons to renders of the
3D models for realism, toned down icon backgrounds and moved rarity into
border decoration for a "wider range in accessibility". The paragon board
was criticised for readability; complex boards need strong hierarchy.
*Take:* uniform 1×1 slots (we have them), rarity in the frame not the fill,
item art from the 3D model (we photograph ours), a minimap with the tracker
beneath, unified-not-identical pad layouts.

**Diablo II: Resurrected.** Automatic switch to a full controller interface;
skills on face buttons; potions on the D-pad. *Take:* switch prompts by
device instantly; keep the draught on one button.

**Path of Exile (1 and 2).** Depth on demand: holding Alt shows an item's
mod tiers and ranges; loot filters. The passive tree is the genre's cautionary
tale of overwhelming first contact. *Take:* a second layer of detail behind a
hold (planned for affixes), never a wall of nodes on first sight.

**Last Epoch.** Each skill has its own specialisation tree, with slots
unlocked by level (shown as numbered hexagons at the top of the screen);
affix tiers are shown; a built-in loot filter. New players report the
first sight of the specialisation screen as confusing. *Take:* our arts'
facets are a small, friendly version of specialisation: show the slots
and what level opens them (we do: "rank II opens the first").

**Grim Dawn.** The devotion constellation map is a memorable *diegetic-ish*
skill screen (a sky of gods) but needs community tools to navigate.
Comparison tooltips beside the hovered item. *Take:* the hovered item and
the worn one side by side.

**Torchlight II.** Praised for simplifying the genre's clutter: colour-coded
loot, side-by-side comparisons, quick, intuitive menus. *Take:* simplicity
as a feature.

**Lost Ark.** Dense, MMO-like HUD, minimap and tracker; players are taught
to hide it (Alt+X). *Take:* density is a cost; ours stays lean.

### 7.2 Survivors-likes (the night)

**Vampire Survivors.** The template: a full-width experience bar at the top
(players complain it is too thin), the timer at the top centre, weapons and
passives as small icons top-left (six of each), a level-up panel of three or
four choices that says "New!" or the next level, and that an item is
"needed to evolve" a weapon. Reroll, skip and banish. *Take:* the top bar,
the timer, empty slots as a promise of six, "New" and "evolves with"
written on the card. *Avoid:* the thin bar; text overflowing cards.

**Brotato.** Between waves, the shop always shows the full stat panel
beside the offers, items can be locked, and rarity runs white, blue,
purple, red. *Take:* the build is visible while choosing.

**HoloCure.** The level-up menu shows the player's stats on the left and
four options on the right, colour-coded by type (stat, item, weapon,
skill), with reroll, eliminate and hold. *Take:* type by colour *and*
label; the build beside the choice.

**20 Minutes Till Dawn.** Upgrades come in small trees (take the first to
unlock the next); synergies are marked with a distinct red icon and border.
*Take:* make "this combines with what you have" a visible, distinct state.

**Halls of Torment.** A late-90s Diablo look applied to a survivors
run: framed panels, traits on level-up, blessings bought between runs,
items found in the run. *Take:* the frame language of a classic ARPG suits
a horde game if the centre stays clear.

**Deep Rock Galactic: Survivor.** Weapons level as they are used; at set
levels (6, 12, 18) an overclock choice appears. *Take:* milestone choices
are announced as different from ordinary ones (our blessing milestones and
evolutions).

**Soulstone Survivors.** Many skills and very heavy effects; players lose
runs to their own clutter; a slider for effect visibility. *Take:* the
HUD must not add to the centre's noise; consider the slider.

**Death Must Die.** Hades-like gods' boons plus Diablo-like gear inside a
survivors run. *Take:* the closest neighbour to our two-genre mix; boons
announced by who gives them, gear compared like an ARPG.

### 7.3 Hades and Hades II
The genre's best explanation of choices. Each god's boons are framed in the
god's colour and sigil; rarity runs Common (white), Rare (blue), Epic
(purple), Heroic (red), with Duo and Legendary as special tiers; a boon says
which slot it fills (attack, special, cast, dash, call) and so what it would
replace; duo boons appear only once their prerequisites are held, and the
Codex lists prerequisites. Hades won IGDA awards for UI art and UI/UX. Its
art direction is "clarity under pressure and personality everywhere else":
lavishly ornamented frames, but clean faces for the text that must be read
at speed. *Take:* frame by source and rarity, say what a choice replaces or
deepens, ornament the frame and keep the text plain.

---

## 8. What this means for Survivor Unchained

The rules `UI_DESIGN.md` is built on:

1. **The centre belongs to the fight.** By night the only HUD near the
   survivor is their own health (and charges), drawn under them.
2. **Day and night interfaces differ on purpose.** Night: sparse, glanced,
   colour-coded. Day: browsable, read, detailed.
3. **Colour is a language**: gold (yours, the interface), ember (night's
   power), blood (health, danger), cool blue (day's growth, shields),
   rarity's ladder. Never colour alone: every colour has a word, a mark or a
   shape with it.
4. **Recognition over recall everywhere a choice is made**: the build
   beside the draft, the worn item beside the hovered one, the key on the
   button.
5. **Pad and keyboard are equals**: every screen navigable with four
   directions, A/B/X/Y, bumpers and triggers; a focus ring you can see from
   a sofa; prompts that follow the device.
6. **Every press answers within a frame**: highlight, scale, sound; choices
   land with a flourish; rarer looks and sounds rarer.
7. **Teach by showing**: light what fits, name things after they happen,
   hints only at first contact.
8. **Readable by default**: body text 18 px or more at 1080p, nothing under
   15 px, sentence case, lines under 80 characters, contrast 7:1 for body
   text on plates.
9. **Show what a choice costs or replaces before it is made.**
10. **End on a high**: arena results and level-ups count up and celebrate.

---

## Sources

- Celia Hodent, *The Gamer's Brain: How Neuroscience and UX Can Impact
  Video Game Design* (CRC Press, 2017):
  [Routledge](https://routledge.com/9781498775502); her talk
  [The UX of Fortnite](https://interaction19.ixda.org/program/talk-the-ux-of-fortnite-celia-hodent/).
- Jakob Nielsen, [10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/);
  progressive disclosure (1995), summarised at
  [UXPin](https://www.uxpin.com/studio/author/hello/page/21).
- Jon Yablonski, [Laws of UX](https://lawsofux.com/) (Fitts, Hick, Miller,
  Doherty threshold, goal-gradient, peak-end, Von Restorff, Zeigarnik,
  Gestalt laws).
- Erik Fagerholt and Magnus Lorentzon, *Beyond the HUD: User Interfaces for
  Increased Player Immersion in FPS Games* (Chalmers, 2009), as summarised in
  [Game Developer](https://www.gamedeveloper.com/design/user-interface-design-in-video-games).
- Scott Rigby and Richard Ryan, *Glued to Games*; the
  [PENS model](https://selfdeterminationtheory.org/player-experience-of-needs-satisfaction-pens/).
- Jamie Madigan, [The Psychology of Diablo III Loot](https://www.gamedeveloper.com/design/the-psychology-of-i-diablo-iii-i-loot).
- Martin Jonasson and Petri Purho, "Juice It or Lose It" (GDC Europe 2012),
  discussed at [RPG Playground](https://rpgplayground.com/research-making-a-juicy-game/);
  Jan Willem Nijman, "The Art of Screenshake".
- Masahiro Sakurai on hitstop:
  [Source Gaming](https://sourcegaming.info/2015/11/11/thoughts-on-hitstop-sakurais-famitsu-column-vol-490-1/),
  [Nintendo Wire](https://nintendowire.com/news/2022/12/12/this-week-in-sakurai-12-5-12-11-fine-tuning-hit-stop-and-cheating-the-system/).
- Microsoft, [Xbox Accessibility Guideline 101: text display](https://learn.microsoft.com/en-us/gaming/accessibility/xbox-accessibility-guidelines/101);
  [Designing for Xbox and TV](https://learn.microsoft.com/pl-pl/windows/apps/design/devices/designing-for-tv);
  [Gamepad and remote interactions](https://learn.microsoft.com/en-au/windows/uwp/ui-input/gamepad-and-remote-interactions).
- [Game Accessibility Guidelines](https://gameaccessibilityguidelines.com/basic/);
  IGDA GA-SIG [Game Accessibility Top Ten](https://igda-gasig.org/how/game-accessibility-top-ten-se/).
- Okabe and Ito colour-blind-safe palette:
  [reference](https://siegal.bio.nyu.edu/color-palette/).
- Blizzard, [Diablo IV Quarterly Update, February 2020](https://news.blizzard.com/en-us/article/23308274/diablo-iv-quarterly-updatefebruary-2020)
  (Angela Del Priore on UI); [Diablo IV paragon and itemisation update](https://www.wowhead.com/news=325390/diablo-iv-quarterly-update-december-2021-paragon-board-itemization-and-visual);
  community feedback on [the skill tree's readability](https://www.icy-veins.com/forums/topic/52508-official-response-to-feedback-regarding-the-diablo-4-skill-tree/).
- Diablo II: Resurrected controller interface:
  [Blizzplanet](https://blizzplanet.substack.com/p/diablo-ii-resurrected-tech-alpha-controller-ui),
  [Notebookcheck](https://www.notebookcheck.net/Diablo-2-Resurrected-gameplay-footage-sheds-light-on-some-key-gameplay-improvements.524226.0.html).
- Path of Exile: [Advanced Mod Descriptions and tiers](https://www.pathofexile.com/forum/view-thread/2138559);
  PoE2 controller feedback on [Steam](https://steamcommunity.com/app/2694490/discussions/0/4628106793389741569).
- Last Epoch: [specialisation](https://upcomer.com/how-to-specialize-in-skills-in-last-epoch),
  [loot filter](https://maxroll.gg/last-epoch/resources/loot-filter-guide).
- Grim Dawn: [Devotion](https://www.grimdawn.com/guide/character/devotion).
- Torchlight II: [Game Chronicles review](https://gamechronicles.com/game-reviews/torchlight-ii-review-xbox-one/).
- Lost Ark: [PC Gamer tips](https://pcgamer.com/lost-ark-guide-tips-and-tricks).
- Vampire Survivors: [evolution guide](https://www.gamespot.com/articles/vampire-survivors-how-to-evolve-weapons/1100-6508815/);
  [accessibility notes](https://www.familygamingdatabase.com/accessibility/Vampire+Survivors).
- Brotato: [beginner's guide](https://fantasywarden.com/games/brotato-beginners-guide).
- HoloCure: [level-up menu](https://gamepretty.com/holocure-save-the-fans-general-guide-v0-6/).
- 20 Minutes Till Dawn: [synergies](https://20-minutes-till-dawn.fandom.com/wiki/Synergies).
- Halls of Torment: [Godot showcase](https://godotengine.org/showcase/halls-of-torment/),
  [Chasing Carrots](https://www.chasing-carrots.com/halls-of-torment/).
- Deep Rock Galactic: Survivor: [weapons](https://deeprockgalactic.wiki.gg/wiki/Survivor:Weapons).
- Soulstone Survivors: [effect visibility](https://steamcommunity.com/app/2066020/discussions/0/3591086730691827584).
- Death Must Die: [PCGamesN](https://www.pcgamesn.com/death-must-die/steam-game).
- Hades and Hades II: [boons](https://hades2.wiki.fextralife.com/Boon),
  [IGDA awards](https://www.videogameschronicle.com/news/hades-wins-9-times-at-the-igda-global-industry-game-awards/),
  [art direction](https://80.lv/articles/a-behind-the-scenes-look-at-the-effects-in-hades/).
- Overwatch, "The Art of Overwatch: Evolving" (GDC 2017):
  [GDC Vault](https://gdcvault.com/play/1024268/The-Art-of-Overwatch-Evolving).
- Super Mario Bros. World 1-1: [Wikipedia](https://en.wikipedia.org/wiki/World_1-1).
- Edd Coates, [Game UI Database](https://www.gameuidatabase.com/about.php):
  the reference library for every screen type named here.

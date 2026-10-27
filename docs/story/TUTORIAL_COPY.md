# The tutorial's words: Ember, and the freeze-frame callouts

The copy for the Prologue's teaching pass (the Low Ford road, `godot/logic/Play/Zones/Prologue.cs`). The story writer supplies the words and says where each one belongs. The experience director places them and sets the timing; UI design draws the callout, judged at 1:1. Its words match the storybook intro (`docs/story/storybook/sb00_stay_where_they_reach.md`).

> The owner, 18 October: "we also need to make the 'tutorial' more explanative and engaging in explaining things - this is ember, these are skills ember lets you use for a brief time yada yada - some of the things that pop up on screen are great, but a more direct helper tip like freeze frame arrow point kinda deal for some stuff".

**What a callout is** (the owner's): the game freezes, an arrow and a short callout point at the thing, the player acts, and play resumes. Some here are **arrows only**: the arrow and words show for 4 s while play runs. The Prologue is "a tutorial that never stops to be one", so it freezes only where the moment needs it. The existing pop-ups that work stay (listed at the end).

## How the words are written

- **The interface's voice:** plain, second person, present tense. It says what a thing does. One line, at most 14 words, with a title of one to three words. Keys come from the player's bindings (`Key(...)`), never hard-coded.
- **The intro's words, kept:** ember is *the light the dead carry*; it *rises*; it *lends*; it lasts *until dawn* (in the Prologue; "until the night ends" anywhere else); *first light* takes it back. SB00 says "takes back what it lent", so the interface says "lends". The player hears one idea twice and learns it once.
- **Never why.** No line says why she can burn ember. That is Act 2's question, *what you are*.
- **Two levels, kept apart** (the experience audit's "two levels at once"): the ember's levels are lent for the night and taken back; the character's level is what the night taught her, and only it is called *yours* or said to *stay*.

## The Ember explanation: one idea across the night

Read in order, these lines are the whole explanation: what ember is, that it rises, that it lends skills, and that first light takes them back while what she learned stays. Each shows at the moment it is true.

1. **Ember** (F1, the first ember on the ground near her): *The light the dead carry. Come close and it comes to you.*
2. **Rising** (F2, straight after F1): *Ember fills this. When it's full, the ember rises.*
3. **A skill** (F4, the first skill draft): *The ember lends you skills as it rises. Choose one.*
4. **Your skill** (F5, the first combat skill on the console): *It fires on its own, like your weapon. First light takes it back.*
5. **A great blessing** (F3, its own panel, 40 s into the Rising once F4 was seen): *The ember lends you a blessing. It changes how you fight until dawn.*
6. **The ember goes out** (the douse's announcement, at dawn): "The ember goes out" over *First light takes back what it lent*. It is an announcement, not a callout: the narrator says the rest (C04 A, or her caption).
7. **What the night taught you** (F12, after her dawn line, at the Level banner): *You gained four levels tonight, and they're yours to keep. / The ember's skills were only lent; traits stay. / Press `Key("character")` to choose two.* (au1 item 13; counts from the night.)

(27 Oct, i14, checked in a real run, f7a: all seven show, in this order. F1 and F2 had come the wrong way round, F2 at 43.6 s and F1 at 49.2 s, because F1 was asked at any ember on the field and let go at once when none lay near her. Now F1 is asked only with an ember near her and never after F2, and F2 comes without F1 only 30 s into the Rising. The list is in the order the night shows them: F3 has come after F4 since 26 Oct.)

**For the journal** (a `learn` with the first ember gathered, `lore.ember`; the journal remembers what the valley believes):
*"Ember: light that seeps up from under the valley. After dark the dead get up full of it, and it spills when they fall. At first light, what's in them sinks back into the ground."*

## The callouts, and where each belongs

| # | Id | Fires (Prologue stage and moment) | The arrow points at | Kind | Title | Line |
|---|---|---|---|---|---|---|
| F1 | `ember_ground` | `Rising`: the first ember lies on the ground (the first kill, a few seconds in) | the nearest ember stone | freeze | Ember | The light the dead carry. Come close and it comes to you. |
| F2 | `ember_bar` | the first ember gathered | the ember bar, top center | arrow only | Rising | Ember fills this. When it's full, the ember rises. |
| F3 | `great_blessing` | its own panel, granted 40 s into `Rising` once F4 was seen and no level's draft is owed (26 Oct, au1 item 2: no longer stacked on the first card); no Flare blessing is offered until F8 has taught the Flare (au1 item 3) | the cards | on the panel | A great blessing | The ember lends you a blessing. It changes how you fight until dawn. |
| F4 | `first_draft` | the first skill draft, at the ember's first rise | the first combat-skill card | on the panel | A skill | The ember lends you skills as it rises. Choose one. |
| F5 | `first_skill` | the first combat skill lands on the console | its slot | arrow only | the skill's name | It fires on its own, like your weapon. First light takes it back. |
| F6 | `dash` | `Ambush`: the wagon's trap springs after its line (the drowned out of the ditch, and five bowmen ahead of her who loose together); the freeze comes while that volley is in the air at her (a bolt within 4 m and coming at her), so the roll answers a real danger; the bolts in flight are ringed in the world. 20 s on, or in `Road2`/`Post`, it comes all the same (26 Oct, au i15: in the Rising it had nothing to dodge, her health full until 2:46) | the dash on the console | freeze | Dash | On the volley: `Key("dash")`: roll through the bolts; nothing touches you mid-roll. Two charges; they come back. (Fallback, no volley: `Key("dash")`: a roll nothing can touch. Two charges; they come back.) |
| F6b | `form` | `Ambush`, 10 s of play after F6 at the soonest: her calling's art rides the dash and is lit, four or more of the dead within 6 m | the dash on the console | freeze | the art's name | When your dash is aflame, it's a charge that throws the dead aside. / Big ones stop it, but they're stunned, and their spell breaks. (The dash ring glows ember when the form is ready.) (Bull Rush; Grapple, Mirror Step and Vault have their own line in `Prologue.FormWords`.) |
| F7 | `red_line` | `Post`: the Barrow Knight's first red line appears (the Knight doesn't begin it under another callout, a narrated line or an owed draft, nor while it stands behind something tall, and holds it once while F7 waits; 27 Oct, i14: in real runs the first came under the Knight's own line and the next behind the cracked wall, both let go) | the red line on the ground | freeze | Red line | The Knight is about to strike along this line. Get off it. |
| F8 | `art` | `Barrow`: the Grave-Caller within 16 m and her art ready (today's `ability` tip) | the art's ring (Q), and the Grave-Caller | freeze | the art's name | If it interrupts: `Key("ability")`: your art. It breaks the Grave-Caller's channel. Otherwise: `Key("ability")`: your art. Kill the Grave-Caller before it raises more. |
| F9 | `lamps` | `Boss`: 3 s after C02 hands back | the three blue lamps | freeze | The lamps | Three lamps guard the Warden. While they burn, he barely feels a blow. / Put them out: break them, or lure his charge into one. (The ring never sits in the minimap's corner.) |
| F10 | `draught` | the first time her health falls under half, anywhere in the Prologue (26 Oct, au i15: under 40% a real run never came); it waits only for another freeze (5 s after it), never for a tip or a prompt | the draught on the console | freeze | Draught | Drink a draught to mend: `Key(...)`, the draught's binding. |
| F12 | `level` | the first character level, at dawn, **after** the narrator's dawn line ends | the Level announcement | freeze | What the night taught you | (26 Oct, au1 item 13) You gained four levels tonight, and they're yours to keep. / The ember's skills were only lent; traits stay. / Press `Key("character")` to choose two. (Counts from the night; "traits" marked in ember; the banner reads "Two new traits to choose (C)".) |
| L1 | `ember_lock` | `Rising` (or `Road`), once the ember has risen and F5 was seen, fewer than five of the dead within 6 m, 4 s clear of any other callout, line or tip (27 Oct, au1 item 14: the "4" on the lock was never taught) | the lock at the chain's middle (`GameHud.EmberLockArea`) | arrow only | The lock | The ember's level tonight. It springs open each time the ember rises. ("level" marked) |
| L2 | `tally` | the first gold in hand (the wagon's spilled coins), in a calm: the `Road`, the `Ambush` before the ditch rises (the trap waits for it and springs 2 s after), `Road2`, `ToFord` or `Dawn`, nothing hostile within 8 m, 4 s clear of anything else; let go if the calm ends (27 Oct, au1 item 14) | the tally's slain and gold, lower right (`GameHud.TallyArea`) | arrow only | The tally | How long you've lasted, the dead you've put down, and your gold. ("gold" marked) |
| L3 | `minimap` | the Waystation, first time in: once C04 B and its words are over and the screen has been clear 4 s (27 Oct, au1 item 14) | the corner map (`GameHud.MinimapArea`) | arrow only | The map | Who has news for you, and the ways out. `Key("map")`: the whole map. ("map" marked) |
| ~~L4~~ | ~~`talk`~~ **CUT (27 Oct, MR5 judge: the prompt "E Talk Tam" is the lesson; the code is removed)** | anywhere, the first time the talk prompt is up (someone in reach), 4 s clear of anything else (27 Oct, au1 item 14) | the interact prompt (`GameHud.PromptArea`) | arrow only | Talk | `Key("interact")`: talk. A mark over someone's head means news for you. ("talk" marked) |
| F13 | `flare` | *When the Flare lands on Q (CLASSES.md):* its meter first full | the Flare's ring | freeze | Flare | `Key("flare")`: your Flare. It fills fastest when you're in trouble. |

(There is no F11: the dawn's own words are the announcement's and the narrator's, item 6 above.)

Notes for the experience director:
- **One at a time.** Never two at once, never inside a cinematic or a narrated line, never stacked on a draft panel except F3 and F4, which are about the panel.
- F3 replaces the Prologue's first `SetDraftTip` text for that one panel. The general draft tip stays for later panels.
- F7: trim the red-line sentence from the Elites pop-up, since the freeze says it.
- F9 says why the lamps matter in the tale's own terms (SB00: "Oil, never ember. Nobody remembers why."). Keep today's `lamps2` pop-up for the trick (lure his charge into a lamp).
- F10: today the draught is on `Key("ultimate")`. CLASSES.md renames it to `Act.Draught` on R, so use the draught's binding when this is built.
- Break the channel (pop-up, 26 Oct): reads "The Warden is raising the drowned. / Break it: Bull Rush into him, or use your Flare. / If he finishes, a lamp lights again." (keys as the tip's chips; without a form or Flare: "Hurt him hard enough and it breaks.") (`Key("ability")` no longer exists: Act.Ability became the Flare on 11 Oct.)
- Your pack stays at the chest; F8 waits until it is gone (au1 item 10).
- F13 waits for the Flare (CLASSES.md: "It fills fastest when you're in trouble"). Until then, F8 teaches Q as the art.
- Each callout shows once, on the first journey. A "Tips" setting can turn them off.

## The pop-ups that stay (they work: the experience audit, "What works")

Move ("Keep moving. Your weapon strikes on its own."), Shieldmen, Elites (F7 takes its red-line sentence), The Watch-post, Your pack, Break the channel, the lamps' lure (`lamps2`), and By day. The Prologue's narration is the narrator's and is not touched. Her dawn line ("everything it gave you goes with it... your mother's face... not quite where you left it") is where SB00's "No more than that" first cracks.

## Pacing (26 Oct, au i15)

- **The road's words wait their turn.** Between the Rising and the ford, each narrated line and tip comes once nothing is being narrated and no callout is up, and 4 s of play after the one before (2 s after a callout). No line is cut off by the next, and no two land together.
- **The road north** pop-up is folded into the narrator's line ("The road runs north, toward the Waystation") and the objective ("Follow the road north"): it came with that line and said the same.
- **The Road's beat** is the wagon, quiet: when the road line plays ("The ground goes still..."), the Rising's leftover dead fall quietly away (within 40 m of her) and nothing spawns in the Road. The coins spill at the wagon's tail then, bait she walks to. Its line is read, then 0.8 s of silence, then the ditch rises; the objective "Survive the ambush at the wagon" appears with the trap, not before. No new words.
- **Spacing (second pass).** A narrated line's gap is measured from its end (1.5 s at least). A narrated line with no voice-over stays up at least its length / 17 characters a second.
- **Shield tip** (text now: "Their *raised shields* stop your shots. Strike from the side, or up close."; title "Shieldmen") is queued from the trap, about 18 s into the fight, when shieldmen first stand; it no longer rides the Knight line.
- **Road2 line** ("The last of them falls back into the ditch..."): the dead around her fall away and nothing spawns for 6 s. **ToFord**: no spawns, so "The dead go quiet" is true.
- **Lessons keep their distance (27 Oct, au1 item 14).** L1-L4 come only after 4 s with nothing else on the screen (no callout, narrated line, tip, banner, cinematic or panel), and the road's next words wait 4 s after one ends. A lesson whose calm ends before it can show is let go, never shown in the fight (the tally). The Ambush's trap waits for the tally and springs 2 s after it (its fallback moved from 16 s to 30 s into the stage so the wagon's line and the lesson both fit). In the Waystation, talking waits for the map's lesson.

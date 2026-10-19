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

1. **Ember** (F1, the first ember on the ground): *The light the dead carry. Come close and it comes to you.*
2. **Rising** (F2, the first ember gathered): *Ember fills this. When it's full, the ember rises.*
3. **A great blessing** (F3, the first draft panel): *The ember lends you a blessing. It changes how you fight until dawn.*
4. **A skill** (F4, the first skill draft): *The ember lends you skills as it rises. Choose one.*
5. **Your skill** (F5, the first combat skill on the console): *It fires on its own, like your weapon. First light takes it back.*
6. **The ember goes out** (the douse's announcement, at dawn; today "The ember goes out" over "It burns only in the dark"): make its second line *First light takes back what it lent*. It is an announcement, not a callout: the narrator says the rest (C04 A, or her caption).
7. **What the night taught you** (F12, after her dawn line): *This one stays, night and day. Open `Key("character")` to spend it.*

**For the journal** (a `learn` with the first ember gathered, `lore.ember`; the journal remembers what the valley believes):
*"Ember: light that seeps up from under the valley. After dark the dead get up full of it, and it spills when they fall. At first light, what's in them sinks back into the ground."*

## The callouts, and where each belongs

| # | Id | Fires (Prologue stage and moment) | The arrow points at | Kind | Title | Line |
|---|---|---|---|---|---|---|
| F1 | `ember_ground` | `Rising`: the first ember lies on the ground (the first kill, a few seconds in) | the nearest ember stone | freeze | Ember | The light the dead carry. Come close and it comes to you. |
| F2 | `ember_bar` | the first ember gathered | the ember bar, top center | arrow only | Rising | Ember fills this. When it's full, the ember rises. |
| F3 | `great_blessing` | the first draft panel (ember level 2; the panel already pauses) | the cards | on the panel | A great blessing | The ember lends you a blessing. It changes how you fight until dawn. |
| F4 | `first_draft` | the first skill draft after it | the first combat-skill card | on the panel | A skill | The ember lends you skills as it rises. Choose one. |
| F5 | `first_skill` | the first combat skill lands on the console | its slot | arrow only | the skill's name | It fires on its own, like your weapon. First light takes it back. |
| F6 | `dash` | `Rising`: the first time six risen are within 3 m of her (or at 14 s, as today, if that never happens) | the dash on the console | freeze | Dash | `Key("dash")`: a roll nothing can touch. Two charges; they come back. |
| F7 | `red_line` | `Post`: the Barrow Knight's first red line appears | the red line on the ground | freeze | Red line | The Knight is about to strike along this line. Get off it. |
| F8 | `art` | `Barrow`: the Grave-Caller within 16 m and her art ready (today's `ability` tip) | the art's ring (Q), and the Grave-Caller | freeze | the art's name | If it interrupts: `Key("ability")`: your art. It breaks the Grave-Caller's channel. Otherwise: `Key("ability")`: your art. Kill the Grave-Caller before it raises more. |
| F9 | `lamps` | `Boss`: 3 s after C02 hands back | the three blue lamps | freeze | The lamps | While these burn, the Warden barely feels a blow. Break them. |
| F10 | `draught` | the first time her health falls under 40%, anywhere in the Prologue | the draught on the console | freeze | Draught | Drink a draught to mend: `Key(...)`, the draught's binding. |
| F12 | `level` | the first character level, at dawn, **after** the narrator's dawn line ends | the Level announcement | freeze | What the night taught you | This one stays, night and day. Open `Key("character")` to spend it. |
| F13 | `flare` | *When the Flare lands on Q (CLASSES.md):* its meter first full | the Flare's ring | freeze | Flare | `Key("flare")`: your Flare. It fills fastest when you're in trouble. |

(There is no F11: the dawn's own words are the announcement's and the narrator's, item 6 above.)

Notes for the experience director:
- **One at a time.** Never two at once, never inside a cinematic or a narrated line, never stacked on a draft panel except F3 and F4, which are about the panel.
- F3 replaces the Prologue's first `SetDraftTip` text for that one panel. The general draft tip stays for later panels.
- F7: trim the red-line sentence from the Elites pop-up, since the freeze says it.
- F9 says why the lamps matter in the tale's own terms (SB00: "Oil, never ember. Nobody remembers why."). Keep today's `lamps2` pop-up for the trick (lure his charge into a lamp).
- F10: today the draught is on `Key("ultimate")`. CLASSES.md renames it to `Act.Draught` on R, so use the draught's binding when this is built.
- F13 waits for the Flare (CLASSES.md: "It fills fastest when you're in trouble"). Until then, F8 teaches Q as the art.
- Each callout shows once, on the first journey. A "Tips" setting can turn them off.

## The pop-ups that stay (they work: the experience audit, "What works")

Move ("Keep moving. Your weapon strikes on its own."), The road north, Shieldmen, Elites (F7 takes its red-line sentence), The Watch-post, Your pack, Break the channel, the lamps' lure (`lamps2`), and By day. The Prologue's narration is the narrator's and is not touched. Her dawn line ("everything it gave you goes with it... your mother's face... not quite where you left it") is where SB00's "No more than that" first cracks.

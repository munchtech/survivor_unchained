# The tutorial's words: Ember, and the freeze-frame callouts

The copy for the Prologue's teaching pass (the Low Ford road, `godot/logic/Play/Zones/Prologue.cs`). The story writer supplies the words and says where each one belongs. The experience director places them and sets the timing; UI design draws the callout, judged at 1:1.

> The owner, 18 October: "we also need to make the 'tutorial' more explanative and engaging in explaining things - this is ember, these are skills ember lets you use for a brief time yada yada - some of the things that pop up on screen are great, but a more direct helper tip like freeze frame arrow point kinda deal for some stuff".

**What a callout is** (the owner's): the game freezes, an arrow and a short callout point at the thing, the player acts, and play resumes. The existing pop-ups that work stay (listed at the end).

## How the words are written

- **The interface's voice:** plain, second person, present tense. It says what a thing does. One line, at most 14 words, with a title of one to three words. Keys come from the player's bindings (`Key(...)`), never hard-coded.
- **The intro's words, kept:** ember is *the light the dead carry*; it *rises*; it *lends*; it lasts *until dawn* (in the Prologue; "until the night ends" anywhere else); *first light* takes it back. SB00 says "takes back what it lent", so the interface says "lends". The player hears one idea twice and learns it once.
- **Never why.** No line says why she can burn ember. That is Act 2's question, *what you are*. The interface tells her what it does for her, and the intro tells the valley's belief.
- **Two levels, kept apart** (the experience audit's "two levels at once"): the ember's levels are lent for the night; the character's level is what the night taught her, and it stays. The words never mix the two.

## The Ember explanation: one idea across the night

Read in order, these lines are the whole explanation: what ember is, that it rises, that it lends skills, and that first light takes them back while what she learned stays. Each fires at the moment it is true, as a freeze-frame callout (F1-F5, F11-F12 below).

1. **Ember** (the first ember on the ground): *The light the dead carry. Come close and it comes to you.*
2. **Rising** (the first ember gathered): *Ember fills this. When it's full, the ember rises.*
3. **A blessing** (the first draft panel, the great blessing): *The ember lends you a blessing. It changes how you fight until dawn.*
4. **A skill** (the first skill draft): *Each time the ember rises, it lends you a skill. Choose one.*
5. **Your skill** (the first combat skill on the console): *It fires on its own. It's yours until dawn.*
6. **First light** (the ember goes out): *First light takes back what the ember lent. What you learned, you keep.*
7. **What the night taught you** (the first character level, at dawn): *This is yours, and it stays. Spend it here.*

**For the journal** (a `learn` with the first ember gathered, `lore.ember`; the journal remembers what the valley believes):
*"Ember: light that seeps up from under the valley. After dark the dead get up full of it, and it spills when they fall. It burns only until first light."*

## The freeze-frame callouts, and where each belongs

| # | Id | Fires (Prologue stage and moment) | The arrow points at | Title | Line |
|---|---|---|---|---|---|
| F1 | `ember_ground` | `Rising`: the first ember lies on the ground (the first kill, a few seconds in) | the nearest ember stone | Ember | The light the dead carry. Come close and it comes to you. |
| F2 | `ember_bar` | the first ember gathered | the ember bar, top center | Rising | Ember fills this. When it's full, the ember rises. |
| F3 | `great_blessing` | the first draft panel (ember level 2, the great blessing; the panel already pauses) | the cards | A blessing | The ember lends you a blessing. It changes how you fight until dawn. |
| F4 | `first_draft` | the first skill draft after it | the first combat-skill card | A skill | Each time the ember rises, it lends you a skill. Choose one. |
| F5 | `first_skill` | the first combat skill lands on the console | its slot | the skill's name | It fires on its own. It's yours until dawn. |
| F6 | `dash` | `Rising`: the first time six risen are within 3 m of her (or at 14 s, as today, if that never happens) | the dash on the console | Dash | `Key("dash")`: a roll nothing can touch. Two charges; they come back. |
| F7 | `red_line` | `Post`: the Barrow Knight's first red line appears | the red line on the ground | Red line | It's about to strike along this. Get off it. |
| F8 | `art` | `Barrow`: the Grave-Caller within 16 m and her art ready (today's `ability` tip) | the art's ring (Q), and the Grave-Caller | the art's name | If it interrupts: `Key("ability")`: your art. It breaks the Grave-Caller's spell. Otherwise: `Key("ability")`: your art. Kill the Grave-Caller before it raises more. |
| F9 | `lamps` | `Boss`: 3 s after C02 hands back | the three blue lamps | The lamps | While these burn, the Warden barely feels a blow. Break them. |
| F10 | `draught` | the first time her health falls under 40%, anywhere in the Prologue | the draught on the console | Draught | `Key("ultimate")`: drink a draught. It mends you at once. |
| F11 | `dawn` | `Dawn`: the douse (after C04 A, or at its caption without it) | the ember bar emptying, and the console's skills going dark | First light | First light takes back what the ember lent. What you learned, you keep. |
| F12 | `level` | the first character level, at dawn (`Douse`'s level announcement) | the character key (C) | What the night taught you | This is yours, and it stays. Spend it here. |
| F13 | `flare` | *When the Flare lands on Q (CLASSES.md):* its meter first full | the Flare's ring | Flare | `Key("flare")`: your Flare. It fills fastest when you're hurt. |

Notes for the experience director:
- **One at a time.** Never two at once, never inside a cinematic or a story line, and never stacked on a draft panel except F3 and F4, which are about the panel.
- F3 replaces the Prologue's first `SetDraftTip` text for that one panel. The general draft tip stays for later panels.
- F9 says why the lamps matter, in the tale's own terms: the Warden drinks their ember (SB00: "Oil, never ember. Nobody remembers why."). Keep today's `lamps2` pop-up for the trick (lure his charge into a lamp).
- F10's key: today the draught is on `Key("ultimate")`. CLASSES.md renames it to `Act.Draught` on R, so use whichever binding names the draught when this is built.
- F13 waits for the Flare. Until then, F8 teaches Q as the art.
- Each callout shows once, on the first journey. A "Tips" setting can turn them off, and a later journey does without them.

## The pop-ups that stay (they work: the experience audit, "What works")

Move ("Keep moving. Your weapon strikes on its own."), The road north, Shieldmen, Elites (F7 adds the freeze at its first red line), The Watch-post, Your pack, Break the channel, the lamps' lure (`lamps2`), and By day. The Prologue's narration is the narrator's and is not touched. Her dawn line ("everything it gave you goes with it... your mother's face... not quite where you left it") is where SB00's "No more than that" first cracks.

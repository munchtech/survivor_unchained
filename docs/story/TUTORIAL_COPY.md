# The tutorial's words: the Low Ford as an ARPG (M6, 10 Nov)

The copy and the moments for the first hour's teaching (`docs/design/ARPG.md` section 5; the Low Ford road, `godot/logic/Play/Zones/Prologue.cs` and `Prologue.Day.cs`). It replaces the survivors night's table (F1-F13, L1-L4: the ember's draft, the lent skills, the dawn card, "what the night taught you"), which is retired: git history holds it (before tutorial-m6). The experience lead owns the flow and the words; the UI lead owns every element's look (the callout panel, arrows, rings, banners and toasts are the existing ones; no new look is made here).

> The owner, 18 October: "a more direct helper tip like freeze frame arrow point kinda deal for some stuff". "this is ember, these are skills ember lets you use for a brief time".

**What a callout is:** the game freezes, an arrow and a short line point at the thing, the player acts (the answer key) or continues, and play resumes. **Arrow only:** the arrow and words show 4 s while play runs. It freezes only where the moment needs it. One at a time; never inside a cinematic, a narrated line or an open screen; each once a profile; the "Tips" setting turns them off.

## How the words are written

- **The interface's voice:** plain, second person, present tense. It says what a thing does. One line of at most 14 words (two short lines where marked), a title of one to three words. Keys from the player's bindings (`Key(...)`), never hard-coded.
- **The tale's words, kept** (SB00): ember is *the light the dead carry*; it *lends*; *first light takes back what it lent*. Only the Flare is lent. Levels, skills, lamps and gear are hers and are never called lent.
- **Never why.** No line says why she can burn ember (Act 2).
- **One level.** The ember is her experience: it fills the coin's ring and rises into her level. There is no second, night-only level any more.

## The callouts, beat by beat

| # | Id | Fires | Points at | Kind | Title | Line |
|---|---|---|---|---|---|---|
| A1 | `move` | `Wake`, 1.2 s after C01 hands back, she stands by the fire | the movement keys' chip; no world point | arrow | Move | `Key(move)`: walk. The road runs north, out of the firelight. |
| A2 | `swing` | the lone drowned one (`n_lone`) awake, within 7 m and well on screen | the Skill1 seat, and the drowned one ringed | freeze, answer Skill1 | Swing | Hold `Key(Skill1)` to swing at what's under the cursor. You walk as you swing. |
| A3 | `ember_ground` | the lone one's ember, held at rest on the ground until A3 closes (every kill's ember rests 0.35 s, then flies to her and pays her experience as it lands) | the ember stone | freeze | Ember | The light the dead carry. It comes to you, and it makes you stronger. |
| A3b | `ember_ring` | the first ember landed, 0.6 s after A3 closes | the coin's experience ring | arrow | Your level | Ember fills this ring. When it's full, you rise a level. |
| A4 | `resolve` | the three on the road (`n_three`), her first landed swing on them | the Resolve hair (the Drowned Girl's figure) | arrow | Resolve | Every blow that lands builds Resolve. Your skills burn it. |
| A4b | `groundbreaker` | Resolve at or past Groundbreaker's cost, two or more of the three within its reach, 2 s after A4 | the Skill2 seat, and the pack under the cursor ringed | freeze, answer Skill2 | Groundbreaker | When Resolve is full, it heaves itself at the pack. `Key(Skill2)`: heave now. |
| A5 | `captain` | the first pack's captain (`n_first`) awake, in the open, within 14 m | the captain (its plate and its body) | freeze | Captain | Packs travel with a captain. The captain carries the better gear. |
| A5a | `lamp` | **skills-p7's seam:** the first level-up card offering a lamp (Third Blow), once the card is up | Sunder's wick on the card, before and after | on the card | A lamp | Each level lights a lamp on a skill. This one makes every third swing heavy. |
| A6 | `rare` | **loot-m9's seam:** the captain's first Rare on the ground with its beam, nothing hostile within 8 m | the Rare's label | arrow | A Rare | That beam is a Rare: rarer and better. Click its name to take it. |
| A6b | `filter` | **loot-m9's seam:** 3 s after the Rare is taken, with three or more common drops on the ground | the filter key's chip, then the ground labels | arrow | The filter | `Key(filter)`: hide what you don't want. Rares and better always show. |
| A7 | `dash` | the road ambush's charger (`n_cart`) starts its telegraph and she is on its lane or within 2 m of it | the red lane, then the dash pips | freeze, answer Dash | Dash | Red on the ground is a blow coming. `Key(Dash)`: roll through; nothing touches you mid-roll. (two lines) |
| A8 | `elite` | the Barrow Knight awake and his plate up, in the open | his plate: the bar and the affix | freeze | An elite | Elites carry a name, a bar and an affix. Read the affix before you close. |
| A9 | `post` | 2 s after she relights the first lamp-post, its rise done | the post's light on the corner map | arrow | Lamp-post | Fall, and you rise here. `Key(Map)`: travel between lit posts. |
| A10 | `raiser` | the Barrow's Grave-Caller up and within 16 m, 4 s clear of other lessons | the Grave-Caller, ringed under the hover | freeze | Raiser | It raises the dead. Hover it to target it, and kill it first. |
| A11 | `lamps` | `Boss`, 3 s after C02 hands back, his lamps lit | the three blue lamps | freeze | The lamps | Three lamps guard the Warden. While they burn, he barely feels a blow. (two lines, kept) |
| A11b | `flare` | 3 s after A11 closes (the Flare lent at C02's hand-back, its meter full) | the Flare's key and the nearest lit lamp | freeze, answer Flare | The Flare | The ember lends you its fire for this fight. `Key(Flare)`: break a lamp. |
| A12 | (the dawn page) | after C03, before C04 A | none | storybook | | see "The dawn page" |
| A13 | `leap` | **skills-p7's seam:** Heroic Leap on a seat (level 4) and the wolves' ring closed round her | the Leap's seat, then a point outside the ring | freeze, answer its key | Heroic Leap | `Key(Skill3)`: leap where you aim. Over them and out of the ring. |
| A13b | `charge` | **skills-p7's seam:** Shield Charge on a seat (level 5), the next pack within 10 m | its seat | freeze, answer its key | Shield Charge | `Key(Skill4)`: charge into the pack. The first one you hit is stunned. |
| A14 | (the square's lamp) | the Waystation, after C04 B: she reaches the square's lamp | none | banner | The Flare | (banner) Lit for good. `Key(Flare)` |

Seam beats (A5a, A6, A6b, A13, A13b) are wired to wait on their lanes' events and stay inert until those exist. Their keys come from those lanes' bindings: the filter has no binding yet; Skill3 and Skill4 are what the seats show. If Shield Charge's stun is not its first facet when skills-p7 lands, its second sentence changes with it.

## The dawn page (A12)

**One plate, SB00's P5 "First light"** (plate `ink_p3d`, `art/storybook/sb00/p3d/dawn.png`: the risen fold at dawn, the light sinking into the ground, the Watchman's lamp guttering), its own camera tilt and touches, over its own line and take: *"At first light it sinks into the ground and takes back what it lent. No more than that."* (`sb_stay_where_they_reach` `.dawn`). The player hears the tale's rule a second time, and this time it happens to her. About 9 s, skippable as SB00 is. No new art or voice.

Then, as play resumes at dawn, the existing banner: **The Flare goes out** over *Lent for the night. It burns again at the Waystation's lamp.* The Flare's key goes dark. Nothing else is taken.

## Kept, reworded and retired

**Kept:** the draught (F10: "Drink a draught to mend: `Key(draught)`."); the lamps' lure (`lamps2`); Break his spell (the channel: the Flare branch only, since the lent Flare is the one answer she has in the fight; without it, "Hurt him hard enough and it breaks."); the corner map's lesson in the Waystation (L3); the lore journal entry for ember; the Lamp board tip (flagged for M7a: once lamps come from levels, its "each lamp-post you relight is a lamp to spend" goes with them).

**Reworded:**
- *Your pack:* "What you find, you keep. Press `Key(inventory)` to open your *pack* and wear the jerkin." (the ember-won't-outlast-the-night clause goes)
- *Shieldmen:* "Their *raised shields* stop your blows. Strike from the side, or up close."
- *Rested* (the post's Rest): "{post}. Fall, and you rise here."
- *The tally:* "The dead you've put down, and your gold." (if the HUD still shows the tally)

**Retired (code removed or left inert behind the draft flag):** Move ("your weapon strikes on its own"), Rising (F2), A skill (F4), Your skill (F5), A great blessing (F3), The ember's count (L1), Red line (F7: A7 teaches the red ground once for every telegraph), Elites (A8 says it), Form (F6b: the art riding the dash), the art at the Grave-Caller (F8: A10 replaces it, and she has no Flare there), What the night taught you (F12), By day ("the ember sleeps"; the day is the same game), the dawn card and Douse's "The ember goes out" announcement (the page and the Flare banner replace them).

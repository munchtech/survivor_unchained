# M4: the ARPG HUD (six keys, Resolve, dash pips, the level-up card, the routes): the design (M4 UI lead 1, 9 Nov)

The builders work from this page; the judge gets its "Judge" section. Brief: `tools/scratch/coordinator/briefs/M4_ui_lead1.md`. Owner rules that bind: `docs/handoff/ui_art.md` §1-2 (SOUL; one ornamental frame per screen; panels end cleanly; empty slots quiet; ember only for meaning), the hands rule (ARPG.md PICKED: "the slot UI shows which keys she actually presses"), bottomScale 0.85 with the small marks held at their 100% pixel size (`HudBottom.Keep`), 0 alloc per frame, redraw only on change.

## 1. The six keys (seats)

- **Bindings (Controls.cs, ours; main approved):** Skill1 = Mouse0 (LMB, the grip), Skill2 = Mouse2 (RMB), Skill3-6 = Digit1-4 (ARPG.md 3.1; taught_builds.json's slot order). The Flare loses Mouse2 and keeps KeyQ. Mouse names: Mouse0 LMB, Mouse1 MMB, Mouse2 RMB. Skill1-6 join `Rebindable`.
- **Preset 2, "Q E R F":** Skill3-6 = Q, E, R, F (LMB and RMB unchanged); the Flare to Digit1, the Draught to Digit2, Interact to G. One saved `preset` field beside the bindings.
- **Pad:** Skill1 (the grip) A, Skill2 X, Skill3 RB, Skill4 RT, Skill5 Y, Skill6 B (the thumb holds the swing on A while the index fires the two pressed movement skills on RB and RT); Dash LB, Flare LT, Draught d-pad up (check `Move` does not read the d-pad in play), Interact shares A out of a fight; Experience (held LB today) moves to d-pad down. M3's press path reads these bindings (main told M3).
- **Seat order (view only; slots stay stable):** left to right `[1][2][3] (coin) [4][LMB][RMB]`: the keyboard's keys on the left, the mouse's on the right (Diablo III and IV's bar; the hand that presses is on that side). Seat k shows slot `SeatSlot = [2,3,4,5,0,1]`. The flask [R] and the dash [SPACE] keep their ends. Seats are fed from `w.Slot` and `w.Slot2`, never from `b.Weapons` order (today's GameHud loop under "The six places").
- **Key cap:** the R/SPACE chip (KeyTag Chip: 16 tall, r 3, 1 px bronze rim, bone Alegreya Sans 800, held at 100% px), centred on the seat's 12 o'clock and straddling the plate's top line and the ring. There is no room at the foot: the ring's bottom is the screen's foot. Mouse keys draw a mouse glyph (an 11x15 body, the pressed half bone and the other dark), never "LMB" text. The pad draws `Style.PadButton`. Caps re-label live on `Controls.DeviceChanged` and on any rebind or preset change. If the cap and the rank chip at 1:30 touch, the rank chip moves to 4:30 (measure).
- **Kinds at a glance (the hands rule):**
  - **Pressed, and hold (the grip):** bright cap; the dark well and the gold inlay as today (a button).
  - **Channeled (Bladestorm's first key):** bright cap on a 2 px gold underline ("held down"). While `w.Channeling`, a gold arc segment turns in the ring (0.75 turn/s) and the well stays lit.
  - **Kindled (`w.KindledNow`):** the cap at about 50% (no rim light: its key is the secondary use), and the well LIT like a lantern: a warm amber inner glow (the steel family's edge #ca6e06 at about 0.35, breathing ±15% over 2.5 s). "Lit and watching." When it fires itself, the well flares to the mid band (#f9b214) for 0.25 s and settles. Its own key wait (`PressWait`) is not shown.
- **Wait:** today's well fill from the foot (`DgMeters.Level`) and a long wait's gold seconds stay.
- **Cost:** a spender (`b.CostOf(w) > 0`) short of Resolve: the glyph cools (as when waiting) and a 2 px gold arc at the well's edge fills clockwise from 12 o'clock as Value/cost. Once the cost is met, the arc goes and the existing ready glow plays once.
- **Union (`w.Slot2 >= 0`):** both rings' inner edges go gold. Adjacent seats get a gold clasp across the gap at mid-height (a short bar with two rivets); non-adjacent seats each wear a small linked-rings mark at 10:30. While the storm runs, and until `w.BreakUntil`, the second key's seat breathes gold and its cap brightens: the bond's "press now".
- **Empty:** locked (not yet open, `SkillBook.SlotsAt`) = the ring and a dark well, no cap. Open but empty = the same, plus the cap at 30%.
- **Keys screen (Menus.cs, the Controls page):** a "Skill keys" row first. Two choice chips ("Mouse and 1-4", "Q E R F") sit over a miniature of the bar's six caps in seat order, with the pad glyphs under them. The Skill1-6 rebindable rows come below. Picking re-labels the HUD at once (one ornamental frame: the page's own).
- **Dev, for shots:** `--slots "sunder:hold,cleaver:channel,heroic_leap:press,groundbreaker:kindle,iron_vow:kindle,watch_bell:kindle"` (in slot order; through public sim APIs and SetForm, in a new src file), with `--grant-union bladestorm`. `--pad` exists and forces pad prompts.

## 2. Resolve: her hair takes fire (the pick, and why)

It lives on the Drowned Girl, as the brief asks. It is not a line along the bar (the owner doubted the XP line along it, 27 Oct), and not a ring on the orb (the shield's arc lives there, 2 Nov). **Resolve is heat rising through her hair:** the hair's sculpted gold ridges ("veins") light in the warden's steel bands, from the tips (by the plate, beside her neck) up to her crown. The bands are edge #ca6e06, mid #f9b214 and core #fbf1d8, read from `data/look/fx_language.json`, so each calling's resource takes its own school's bands. A crude PIL taste mock at 1:1 (a proxy, not the build): 25%, 60% and 100% read apart at a glance; full was too loud as a whole-hair blaze.
- **Texture:** `tools/uiforge/dg_resolve_veins.py`, beside `dg_figure_cut.py` (reuse its `hair_l` hair mask and highlight pass), writes `art/ui/lamp_life/drowned/lamp_veins.png` at the figure's 2x. Its channels:
  - R = vein strength: the ridge highlights inside the hair, dilated 1 px.
  - G = the gauge coordinate g: geodesic distance inside the hair mask from the crown, 1 at the crown and 0 at the tips. The front then runs as an arc across the locks, never a horizontal cut.
  - B = the soft hair mask.
  - The crown point and the params go into `lamp_geo.json` ("resolve").
- **Draw:** one quad over the figure (the same `LifeLamp.Group` transform), with `shaders/hud_dg_resolve.gdshader`. It is light drawn over the bronze: unshaded, stepped bands, a soft outer glow only.
  - Veins with g <= level are lit mid gold; the last ~6% of g under the front is core white-gold; the tips are edge amber.
  - A faint warm underglow fills the hair below the front.
  - When the figure fades (Behind), the veins hold at 0.6.
- **Motion (C#, from the API: On, Value, Max, Rate, LastReason, LastDelta, LastAt, SpentInStorm):** the level eases (0.12 s up, 0.2 s down). Each reason looks different:
  - **Landed:** a core-white packet runs from the tips to the front in 0.25 s, and the front flares for 0.15 s.
  - **Taken:** the same packet, in edge amber.
  - **Blocked:** a smaller packet in the steel-spark #fdd171 (a block fills less, and looks it).
  - **Spent:** the spent top band flashes core and goes dark in 0.2 s.
  - **Drained (Bladestorm):** the front recedes, with embers running down the veins (a scroll along g).
  - **Faded:** the lit veins cool mid, then edge, then bronze as they fall.
  - **Full (Value == Max):** one four-point glint at the crown (2-3 frames, FX_LANGUAGE §4), a slow shimmer down the veins every ~2.5 s, and a faint warm rim on her profile. Never a whole-hair blaze.
  - **Off** (`On` false: the arena, callings without a resource): no veins drawn.
- **Feed and shots:** GameHud.Frame reads `b.Resolve` once a frame into the view (uniforms set only on change). `--hud-pin resolve=0.6[:landed|taken|blocked|spent|drained|faded|full]` gives stills.

## 3. Dash pips under her life

`HerLight.Under` shows in campaign fights too. Today `underWanted` needs the ember; make it `b.Combat && (ember || b.Campaign)` with the fight on, fading out at peace, and keep the "Health under you" setting. The pips are sized to read at the play camera (the judge measures). A step won (`Ev.DashStep`):
- a charge: the new pip pops in with a core glint;
- stride, breath or landing: every pip glints once;
- either way, the step's name in small caps (Another Breath, Long Stride, Quick Breath, Hard Landing) shows under the pips for 1.6 s and fades.

Never a stat line, never "level".

## 4. The level-up card

One card over the world, rising from the level coin: centred on x 960, its foot clear of the beads and statuses, about 420x110. It uses the panel language: an ink ground at ~82%, a 1 px bronze rule top and bottom, no ornate border.
- **A new key:** header in small caps "LEVEL 4 · A NEW KEY" (bone). Body: the skill's gold glyph in a 40 px well, its name (display serif 26, cream), its key cap chip, and one line of what it does (UI sans 16, parchment 80%).
- **A lamp lit:** "LEVEL 6 · A LAMP LIT", the glyph, the skill's name, then "a blow 42 -> 47" (before dim, after bright).
- **Prompt row (optional):** a key chip and words, for M7a's "one press lights it"; the card then holds 3 s.
- **Timing:** in 0.18 s, hold 2.2 s, out 0.3 s, folding toward the seat that opened (its ring flashes). It waits while banners are held (`XpHoldUntil`) and while a screen is open.
- **API:** `GameHud.LevelCard(LevelCardSpec)` for M6 and M7; `--level-card slot:heroic_leap:4|lamp:sunder:6:42:47` for shots.
- **In the campaign** it replaces both of today's prints (M5's duplicate mark): the coin's "LEVEL N" title (GameHud ~801) and Journey's "Level N" banner (Journey.cs ~281). The arena keeps the ember's own.

## 5. The routes (judges' marks)

- **Damage numbers** move off skill gold, into a UI family of bone and ink (`Hits.Numbers.cs` Restyle ~200, `Hits.cs` ~120):
  - normal: bone #e9dfcc at 85%, smaller, so the impacts outshine them (P7 r1), lifted beside the impact rather than on it;
  - crit: white #ffffff, larger, with a 0.08 s punch and no "!".
- **The target ellipse** (`FoeMarks.cs` ~258-268) turns bone #e6dcc8 over its ink line instead of BronzeHi; its mini bar's frame goes ink and bone.
- **Champion plates:** there is no fade code. The late plate comes from M5's 4 s breather gate (`Battle.cs` ~722, 39cc1839d). Show the plate within 0.15 s of the champion coming on screen, breather or not: a plate names, it does not invite a hit.
- **The coat badge** over her head after the Legendary pickup: grep did not find it (try BattleFx.Loot, GroundLabels, HudMark). Find it in the `m5_zones\clip_r4b` frames after the pickup, then remove it or cap it at 1.5 s.
- **The dawn frame** (`DawnCardView.cs`): one title, one line of what the dark took and what she keeps (two short columns at most), and the go-on prompt. The wording is M6's.
- **Still open from M5 r1:**
  - done objectives get a tick in the tracker;
  - the boss bar's shielded state becomes a silver sheen over the red, not flat grey #8a8a9a (`GameHud.cs` ~1158);
  - check that the strongbox ceremony's icons show name and rarity (ChestCeremony.cs ~185 names them), and whether the judge's frame caught the icons before the names.

## Build split (sequential in ui-m4; one `dotnet build` at a time)

- **A:** section 1 (seats, bindings, presets, pad, the keys screen, `--slots`).
- **B:** sections 2 and 3.
- **C:** sections 4 and 5.

Each builder is a `su-lead-high` at medium with Context budget 250k. A runner shoots, then the judge.

## Judge (max, foreground, 1:1, 1920x1080 at `--hud-scale 0.85`, plus one 2560x1440)

**The build in the frames:** `--slots` plus `--grant-union bladestorm`: LMB Sunder (the break), RMB Cleaver (the held spin), 1 Leap (pressed), and 2-4 Groundbreaker, Iron Vow and Watch Bell (kindled).

**Frames:** the Low Ford by day and by night, the warden pressing in that build.
- Mid-storm (the drain, the bond live), a kindled firing, the Leap on its wait, Groundbreaker short of its cost.
- The taught build at level 9 (no Union) and at level 4 (three seats locked).
- Resolve at 0, at 60% after a landed blow, and full.
- The pad frame.
- The level card (a new key, a lamp lit).
- A step won.
- The routes' frames.

**The whole-frame question first:** "would this HUD ship in a AAA ARPG; does it have soul; can a player read what she presses in one glance?" Nothing reaches the owner before a PASS; after it, one Resolve picture goes to main.

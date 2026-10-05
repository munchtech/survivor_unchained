# Handoff: UI design lead

For the next UI design lead of Survivor Unchained. This file and the repository are all you get.

Read these first:
1. `docs/team/README.md`
2. this file
3. `docs/team/ui_design.md` (one page)
4. `docs/design/UI_RESEARCH.md` (the approved direction)

Branch: `worktree-agent-aab47bfdab5955dac`. It's pushed and has the integration branch `claude/vigilant-galileo-l6jqyx` merged. The main session merges it, and you open no PRs. 663 tests are green.

Older handoffs are in git history: `git log -- docs/handoff/ui_design.md`.

---

## 1. The owner, in their words

- **The bar:**
  - "AAA standard", "strive for excellent, above and beyond"
  - "I don't want to polish, I want to create perfection"
  - "Do we have soul?"
  - "we are striving for perfection"
- **On the old frames:** they looked "a little drab and low effort and low def". Then:
  - "those borders are just ugly, adding more of them dosn't make them better";
  - the inventory and character page "not look rooted in ui research", "ai looking", in need of "considerable help".
- **On the greyboxes:** "the ui layouts look better". Then:
  - "we want to minimize wasted space. if were taking up a lot of extra space have it fade or taper out. or just waste less space altogether to begin with. don't have to be pixel perfect no waste space, but there is a lot of dead space that dosn't do anything, even with artwork."
- **On inventory:** "a very intuitive inventory management is smart. things that can be tucked away like spellbooks or stuff is useful, inventory management is a very real concern in these games so we need it, but we also don't want to feel cheated with things that should stack, or should not even take up inventory spots directly either."
- **On the art:** it "needs soul, maybe some chains or something. but those lame borders before were soulless slop". Chains are our motif, used with purpose.
- **Standing rules:**
  - Full-page screens pause the world only in arena combat, and are often not the best choice.
  - Self is not merged into the Pack.
  - Creation always shows her dressed.
  - Heavy work takes turns: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "ui design: <job>"`. Use `take gpu` for ComfyUI. Give the turn back the moment the job ends.

## 2. The brief (the coordinator's, current)

1. **Build the approved layouts in the game.** Use plain tonal styles first, calling UI art's frame names (see 7), so their art drops in. The layouts are Self, Pack, Storeroom, Trader and the bench, in `docs/ui_review/greybox/` and "Our screens" plus "After the owner's first look" in UI_RESEARCH.md. Approved by the owner:
   - Rook's shelves;
   - the bench as two panels with the smith live in the world between them.
2. **The day's clock** (experience director, ab406cf9ddd22b03b):
   - **A day dial by the zone name:** an arc in four bands in proportion (dawn 1, day 9, dusk 2, night 6 minutes), with her mark moving round it.
     - Dusk is ember-warm and night is moon-blue. The present band is lit.
     - At night a pale moon rides the arc, and the tail cools after the nudge.
     - It dims while the clock is still. No numbers.
     - Data: `World.Clock`, `DayClock.DayAt/DuskAt/NightAt/NightEnds`, `Journey.ClockStarted`, `GameClock.FreePlay`.
     - Judge at `--clock 590/710/890/1070` with `--fixed-fps 60`.
   - **The fall's two choices** (`Game/GameFall.cs`):
     - "Get up" and "Let the night go" as a held moment, with no page. The world is held and darkened on its own layer, and the HUD stays bright.
     - Today it's the use-key prompt.
     - Switches: `--quick warden --sex female --night hollow --stage 3 --auto idle --die 10,26 --choose rise` (or `--choose letgo --die 10`).
3. **The map result and the Wayfinder's table and atlas.** Both are seen and poor:
   - the result has two half-empty boxes, and its telling runs past 9 s, so the back button isn't up by then;
   - the table is an iron plate with the HUD showing round it;
   - the atlas's "The chart is used up" line is clipped under the parchment.
   Redo them in the approved restraint. The crafting lead says the Wayfinder's table will also host chart crafting on the bench pattern.
4. **The heroine's portraits.** When the main session says her head has changed, re-run `python tools/assets/heroine_paint.py` and `python tools/assets/creation_portraits.py`, then shoot the Look's parts.
5. **The male hero's Look** with ab82cbe99e2937ddd, once his body lands: extend `Portraits.cs` and `creation_portraits.py --sex male`.
6. **Loot lead (a9a9c345a35e1fcad).** They own stacking, the slotless stores and the item filter. You own the screens. A filter screen is coming.

## 3. Done this session (all pushed)

| Commit | What |
|---|---|
| fdad746a | **The pack's swap flash.** Wearing a weapon flashed the world figure pale for one frame: the new PlayerView's carried light sat at its feet. `PlayerView.Follow` now copies the light, and the old figure hides at once. Seen frame by frame at 60 fps. The doll showed no T and no blink. |
| c05e1bf6 | **The day clock on screen:** a smoke behind the line under the picture, narrator in italic, `[[act]]` tokens in tracked steps drawn as the key itself, the house's rule on fade cards, and dawn and nightfall glows (`hud.Fade(..., glow)`). Also a `--clock S` switch. |
| 74c2df3b | `Style.PageTheme` (a slim scroll bar with a gold grip, on every Overlay) and `FadeEnds` (a scroll that fades at its ends). |
| d9cbfafd | **The Look's portrait light** (`GameFront.PortraitLight`): key, fill, warm edge and cool rim at head and shoulders and nearer. The fire comes off her face through a stand-in light. `--rig K,F,E,R` sets the strengths. Before and after: `docs/ui_review/look_light_before_after.jpg`. |
| 31d7a46f, 644fb432 | **UI_RESEARCH.md**, the greyboxes, and `tools/uigreybox`. |
| 0042c324 | **The arena (draft) cards centred.** The words had risen to the plain card's inset, 18 px left of centre. Short text now centres in the card. **Credits:** the index wraps and drops "Used under", rail-less groups, a fading rule under heads, the OFL's headings set, and fading ends. Legal (af0973d59a5b2817a) passed the screen. |

## 4. Next, in order

The brief in 2. Start with Self or Pack in the game, plain, and shoot at 1920x1080 against the greybox.

The crafting lead's new needs for the bench and table (Forge.cs on their branch):
- Marks are a seam row with a violet grade badge, I to VI.
- Chart crafting at the Wayfinder's table: the mods are rows with wax seals (red for the foe, violet for yours). Pin and Scrape are cards; Ink, Burn and redraw, and Annotate are tiles on the whole chart.
- A crafter's first telling can run to seven lines.
- Snib's slurry odds sit inside the Steep card.

### The loot lead's rules to size the Pack, Storeroom and filter for (a9a9c345a35e1fcad)

The full design is coming in `docs/design/LOOT_DESIGN.md` §6–8.

- **The 24-place grid holds gear only.** Everything else is slotless and counted, in four tabs:
  - **Pouch:** materials, the crafters' currencies and trophies.
  - **Satchel:** manuals (stack to 3), tomes and charts. Each chart is its own entry, so this tab is a scrolling list sortable by tier, not a row of tiles.
  - **Key ring:** quest things and tools. Things still needed carry a small "needed" mark and can't be dropped or sold.
  - **Belt (new, the 4th tab):** draughts and remedies, counted per kind, up to 10 each.
- **The purse** stays on the Standing line.
- **Tiles:** every tile shows its item level, plus an up-arrow from `Loot.IsUpgrade(ch, item)`.
- **Tooltips:**
  - the second line carries the make word: Worn, Sound, Wrought, Legion, Heartwrought;
  - the compare shows deltas plainly, using `Loot.Power`.
- **New tier, Set:** verdigris #3fd6c0, between Epic and Legendary. Its tooltip has the set name, "2 of 4 worn", and the bonuses lit or unlit. Legendary (amber #ffb040) gets a lore line and a power block. Storied is coming.
- **Filter screen** (`Rpg/LootFilter`):
  - four presets (Everything, Default, Strict, Only the best);
  - toggles: always show upgrades, my calling's weapons, commons of a better make, break down what's hidden at a fight's end, and the drop-sound floor;
  - an advanced rule list comes later.
  - Legendary, Set, Storied and quest things are never hidden. A held key shows hidden labels.
- **Results:** the night's and the map's result gather what the filter shows; overflow of Rare and up goes to Rook's, said on the result. "Broken down: N things for X old iron."

My answers to them:
- Four tabs fit in 484 px.
- The satchel opens as a list of up to 4 visible rows that scrolls.
- On a 72 px tile, item level is a small number top-left and the upgrade arrow top-right.
- Set needs a second cue besides its colour (teal sits near uncommon green for some eyes): a small chain-link mark, which fits the motif.

## 5. Decisions (one line each, with why)

- **One frame per screen.** Hierarchy comes from tone, spacing, type and rules. Every boxed thing being framed meant nothing had hierarchy (the owner's "ugly borders").
- **Colour is rarity, state, or the one primary action.** That's how the eye finds the rare thing in a grid.
- **Empty is quiet.** A recessed tile with the name of what goes there; only filled slots carry colour.
- **Panels hug.** Grids show the rows in use plus one, and the count says the rest. Surfaces that run on taper into the world (the owner on wasted space).
- **The counters are two fitted panels, the keeper live in the world between.** It's not a full page (the owner's rule), and the world is live content.
- **No inspect panel.** The card opens on the world's side, with the worn piece beside it and the deltas marked.
- **Spend with a preview** (Elden Ring): green deltas everywhere until Confirm or Undo.
- **Irreversible acts are held** (`Style.HoldButton`, built by crafting).
- **Portrait light only from head and shoulders inward.** The full figure keeps the camp's light, so the shot stays honest.
- **`hud.Say` narrator lines are italic.** That matches the cinematics.

## 6. Failures and why

- **PowerShell `Get-Content -Raw` / `Set-Content -Encoding utf8` mangled UTF-8** (· became Â·) and added a BOM to two `.cs` files. I restored them from git.
  - Edit source only with the Edit tool.
  - For small replacements in Python files use `[IO.File]::ReadAllText/WriteAllText`.
- **A commit message with double quotes broke PowerShell's argument passing.** Write the message to a file and use `git commit -F`.
- **Some `--clock` shots looked wrong** because I took dusk to be at 660. It's at 600 (dawn 60 + day 540). Also, without `--fixed-fps 60` the first load frame counts as play.
- **The first greyboxes had tall half-empty panels.** The owner wanted no dead space; fitted and tapered panels fixed it.
- **Key presses in shots on the title:** a mouse resting over the menu re-took the focus on every rebuild (MenuList's MouseEntered). It's a real bug with a resting mouse, not yet fixed: gate hover-focus on real mouse motion (`Nav.KeyMode`).

## 7. Gotchas

- **Setup:**
  - Junction `godot/assets` to `public/assets` and set skip-worktree on it.
  - `godot/override.cfg` sets the user folder (`SurvivorUnchainedUiLead5`).
  - Copy `.godot` (without `mono`) and `public/assets/**/*.import` from a recent worktree, then run `dotnet build` and `--headless --import`. The first import took about 15 minutes; later ones about a minute.
  - Never commit the `.import` files the import dirties (only new art's), nor `.uid` files.
- **Shots:** `scratchpad/uid5/shot.ps1 NAME SECONDS [args]`. Set `$env:SHOT_ENGINE="--fixed-fps 60"` for frame-exact runs.
  - Contact sheets: `scratchpad/uid5/sheet.py NAME OUT "x0,y0,x1,y1:w:h"...`.
  - Crops: `trip.py NAME "box" OUT frames...`.
  - Use `--sex female`: `--quick` alone builds the old male model.
  - `--items "iron_helm:2,butchers_cleaver:1"`; `--clicks "1300:580,r1245:715"` (`r` is a right click, every `--click-every` s).
  - `--open forge:brannoc` (not harlan); `--open draft` in `--zone arena`.
- **Memory:** many agents run Godot. An out-of-memory shows as `Parameter "mem" is null`; take the turn and retry.
- **Fonts:** Alegreya Sans lacks → ← ▲ ●. Draw them, or use Alegreya.
- **UI art's frame names to call:**
  - panel, row and row_on, well, slot and slot_0..5;
  - rule_h and rule_v, side, tooltip, chip, price, button and its states, keycap;
  - node_taken, node_next and node_later;
  - round and round_hover;
  - tab_hover and tab_pressed (still owed on the book's tabs).
- **Files are CRLF.**

## 8. Collaborators (ids current at handoff)

- **Main session (coordinator):** message `main`. It relays the owner and merges.
- **UI art, a0bff3ffe4d3ad748:** dresses your layouts once they're built; owes the taper and the chain motif.
- **Experience director, ab406cf9ddd22b03b:** the day dial and the fall's choices (2.2).
- **Crafting, af01b0d61ef656dd4:**
  - the shelves logic is at af01b0d61ef656dd4@012403dd (`Crafting.ShelfPrice` / `BuyShelf`, 24 a shelf);
  - Forge.cs content for the bench and the table;
  - `Style.HoldButton`.
- **Loot and itemisation, a9a9c345a35e1fcad:** the stores, stacking and filter rules.
- **Legal, af0973d59a5b2817a:** the credits pass; no reply needed unless section names change.
- **Male hero, ab82cbe99e2937ddd.**
- **Face lead:** a successor is starting; ask main for the id. They judge faces under `--rig`.

## 9. Read first

1. `docs/design/UI_RESEARCH.md` and `docs/ui_review/greybox/greybox_sheet.jpg`.
2. `tools/uigreybox/screens.py`: the layouts in numbers (x, y, sizes) to build from.
3. `godot/src/Ui/Overlay.cs` (Page, SidePanel, Pane), `Style.cs`, `Ornate.cs` (Backdrop, FadeEnds) and `UiArt.cs`.
4. `godot/src/Ui/Pack.cs`, `Panels.cs` (the character page and the draft), `Forge.cs`, `MapResult.cs`, `MapTable.cs` and `GameHud.cs` (the corner, objectives and Say).
5. `godot/src/Game/GameFront.cs` (creation, the portrait light), `GameClock.cs` and `GameFall.cs`.

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-aab47bfdab5955dac (its tip)

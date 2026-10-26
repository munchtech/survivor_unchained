# Handoff: UI design lead

## Paused here (UI 11, 26 Oct; branch ui-11, worktree .claude/worktrees/ui-11, junction godot/assets to its OWN public/assets)
Restarted by the owner: "fire up the ui lead before anymore damage is done... just need those two leads to work together." Plan approved by the coordinator (routed-notes MR first, then v2 spec, ONE strong piece, owner gate before going wide). ARMOR/COLOR settled: all-American game text (creation was already American; 3 strays fixed).
**Split with Experience (agreed with Experience 4; Experience 5 is a1ba20804a4ea22b7):** UI owns how every element looks and where it sits; Experience owns when it shows, what it says and the teaching flow. Sign-off goes both ways (each element's teaching need is a hard constraint). Neither side edits the other's code without asking. Perf budget: the whole HUD under 1 ms a frame, redraws on change, breathing effects in shaders, no per-frame node churn. Experience's no-look perf pass (pooled minimap marks, redraw-on-change) is at play-1@54e83e86: merge it before touching Instrument.cs/Minimap.cs. Experience's list of the tutorial's 13 UI elements is in the v2 doc's brief and in play-1's docs/handoff/experience.md top.
**Audit (1:1, shots o1a_* at 1080 through the hub, o1b_* at 1440 (2526x1421, the work area), worktree godot/.shots/):** the instrument's LAYOUT is sound; its LOOK is a stand-in far behind the bar. No UI-art PNG ever landed (cuff, socket, lock, bezel, groove): flat drawn rings, plain sockets, a cartoon padlock, a plastic life disc. The chain is the only piece with soul. Minimap parchment, the crowded ~13 px header, and the thin boss bar are stand-ins too. The teaching cards wear the "lame borders". The tutorial's callouts work, but their look is placeholder. The UI art cache tools/comfy/out/uiforge is GONE everywhere (generators in tools/uiforge survive).
**Done, UNJUDGED:** fd76a6e4 = the routed notes 1-9 (blocked floater kept clear of barks; the header follows the time live; the Q vessel shows the Flare's own glyph (FlareDef.Icon, lamps.json icons); one Style.KeyCap for tips and callouts; card footers anchored, level baselines; neutral tags in InkDim; tally falloff + rimmed type; Armor strays). Tests 1054/0/8. Frames: godot/.shots/n1_* (crops n1_crop_*). 2cb52ff3 = docs/design/HUD_V2.md (the v2 spec: one forged object, three bodies on one chain, a riveted joint instead of the eye, blood-in-thick-glass shader, stamped iron key tags, enamel-inlay skill glyphs, cards hung from the chain; production plan and the first piece's 12-point judge checklist).
**Next:**
1. Judge n1_* (tips/callouts at max, the rest at xhigh; whole-frame gate first). Note from the solver: the tally falloff barely shows at dawn (raise BuildTally's 0.4). Env's town judge also saw the dim italic objective line ghosting over a tree (env-16 .shots/e9d4_town_o_03.png, x 1000-1400, y 195-210): give it contrast. Fix, then MR (merge integration first: unlink the junction, merge, relink).
2. Decide the v2 doc's five decisions (its section "Decisions": the layout nudges, BossBar lamps lit of N (encounter data, ask Experience), enamel inlays, cards hung from the chain, who builds blender_irons.py). Then build the FIRST PIECE (the left half: life cuff+glass, the draught on its lug + R tag, three seats, chain to the lock) in the game, A|B at 1:1, 1080+1440, on o1a_08/o1a_36. Max judge with the doc's checklist, then the coordinator shows the OWNER before anything goes wide.
3. Then build v2 wide, item 14 input to Experience, the old Next (map/journal unseen fixes).
Estimate as sent: ~3-4M tokens, 3-5 working days; notes MR ~3 h, owner gate ~1 day, wide build 2-3 days. Spent so far: notes solver 179k, design solver 168k, lead ~140k.
Scratch: coordinator scratchpad ui11\ (play.py set to ui-11 with RES env, sheet.py, the o1 sheets, the design solver's art_sheet.png/top_1to1.png).

For the next UI design lead. Read `docs/team/README.md`, `RESUME.md` and `OWNER_NOTES.md` ("UI design and UI art: the HUD is the keystone"), then this page, then `docs/team/ui_design.md` (status, and the spec UI art starts from), then `docs/design/UI_RESEARCH.md` ("The HUD"). Pictures: `docs/ui_review/build9/`. Older handoffs: `git log -- docs/handoff/ui_design.md`.

**Branch:** `worktree-agent-adba22c3df8f39418` (integration merged at 6407046a). Open no PRs. Stopped at the owner's wind-down: everything builds, tests green.

## 1. The owner, in their words
- "the bottom skill bar and health globes and stuff need to be incredible, its a keystone of that kind of game"; the old foot "is a relic of our old garbage ui".
- "ember on the bottom sliding the boss stuff up"; the clock, kills and gold to a lower corner; "one composed group, not loose pieces"; the minimap "the same pass".
- Journal and Map: no full screen ("feels bad"), the half-window panel "with an option to expand", dead space cut, centred.
- Tips: no shrinking ("more distracting not less"). The tab chain: "I love the direction just needs polish".
- Standing: "we are striving for perfection"; no AI boxes; panels over the world; no fades; soul from the chain, coals, the lamp, sparingly.

## 2. Done (this session; build9 shows it)
All seven of the owner's HUD notes are built (status page "Current state"). Code: `src/Ui/Instrument.cs` (new: Instrument, Vessel, Cuff with the shared `Cuff.Band`, Socket, Round, EmberChain with its Lock), `shaders/hud_vessel.gdshader` (new), `GameHud.cs` (the old ember bar, console, globe, slots, ring and pips removed; tally, boss bar, tips, statuses, passives, corner), `Minimap.cs` (Bezel), `Book.cs` (Journal: panel and wide), `MapScreen.cs` (panel and wide), `Overlay.BookPanel` (width, expand word), `ChainTabs.cs` (polish), `Controls.cs` (`Act.Expand`), `Ornate.cs` (the dead Globe removed), `UiArt.cs` (registry).

- **Character creation, two screens (UI creation lead 1, 20 Oct; branch ui-create):** the owner's "pick calling /arms and look/name". Screen 1 holds sex (the man greyed, "coming later"), calling, weapon, art in hand and origin. Screen 2 holds Face n/10, Hair n/3, hair colour, eyes (7 over 6), skin (no names anywhere, light to deep), No paint / Paint n/7, name and begin. No sliders, no Body part, no cameos. Data and saves are unchanged. Focus shapes are opt-in in Nav (Loud, Framed, round bead rings). Max judges r1 and r2 at 1:1, 1080 and 1440: the UI ships, and every remaining NO is art: the braid hairline at the Look, Face 5's olive cast against her body, Paint 1/7 smudge, the woad look, the Warden pauldron's inner edge, the scene. Open for the owner: ARMOUR/COLOUR spelling on screen. Closed as known: the FACE label over "Face 1/10" (and HAIR, PAINT). The pitch for "All four known" was dropped from the art caption.

## 3. Next
1. **Shoot what is built but unseen** (status page, Next 1), then a strict 1:1 self-critique of the whole HUD before the main session shows the owner.
2. **With UI art** (starts from the status page's spec): bring their cuffs, sockets, lock, bezel and groove in and judge at 1:1 at 1080 and 1440.
3. Then the earlier queue: portraits when the face lead messages (`tools/assets/heroine_paint.py brows`, `creation_portraits.py`); the male Look; `StoryChoices` at 1:1.

## 4. Decisions (why)
- **Her irons:** two cuffs joined by a chain, the ember as its heat, the level on its lock: one object with meaning (Survivor *Unchained*), symmetric, the only ornament on the HUD.
- **Round vs square:** what she lives and acts by is round, what fires by itself square: told apart before reading.
- **Always shown,** at peace too: the keystone stays put (wounds carry into town).
- **Day shows only what is carried, centred;** night shows all six places (the empties promise the night's arsenal).
- **Tips wait for banners;** the top edge is the boss's alone.
- **Line glyphs** for the art in its glass and the six places (painted arts covered the glass; one hand per row).
- **The map opens filling its window** (a square town in a wide window left table bands); "All I know" shows all.
- **The Journal wide is the parchment book over the world;** in the panel it is type on the panel like the rest of the book.

## 5. Failures and gotchas
- **The worktree guard** refuses complex shell (heredocs, computed `sed` lines, `cd` into the main checkout). Put edits in scratch scripts and run them plainly; my tools (`shots.py` batch runner with turns, `sub.py` asserted substitutions, `cut.py` marker cuts) were in the session scratchpad `uid9/`; rewrite them if the scratchpad is gone.
- **Git Bash mangles arguments that start with `/`** (`/// <summary>`): set `MSYS_NO_PATHCONV=1`.
- **Files are CRLF in the worktree:** keep their endings when rewriting.
- **A method named `Content()` shadows the `Content` namespace** (the codex broke).
- **`ColorRect` gives a shader 0 to 1 UVs; `DrawRect` does not.** The vessel's glass is a ColorRect.
- **Shots:** `--resolution 2560x1440` came out 2526x1421 (the desktop's work area); `--fixed-fps` is an engine argument (before `--`).
- **Worktree set-up:** `godot/assets` is a junction to `public/assets` (skip-worktree); the `.godot` cache was copied from the main checkout with robocopy; untracked `.import`/`.uid` sidecars copied in. Never commit them.

## 6. Collaborators
- **Main session:** relays the owner, merges. **UI art** (paused): starts from the status page's spec. **The face lead:** portraits. **The experience director:** the day dial now rides the minimap's bezel.

HANDOFF READY: docs/handoff/ui_design.md on worktree-agent-adba22c3df8f39418@(this commit)

## Late notes recovered from unmerged branches (10 October cleanup)

Written by woken leads on 4 and 5 October after this page, and never merged. Check each against the code and later pages before acting; some may be done or stale.

From `worktree-agent-aab47bfdab5955dac` (2026-10-04 ed2ea5c5):

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


From `worktree-agent-ac76f400913a109cd` (2026-10-04 859c031d):

7. **The forge** (crafting lead `a97e32948c5bf419d`; `godot/src/Ui/Forge.cs`, ForgeScreen; spec `docs/CRAFTING_DESIGN.md` 14): restyle or rebuild. Wanted: the house's frame art for seam rows and craft tiles; a crafted moment (a hammer-strike flash on the seam that changed, the heat gauge's cells burning out one by one); a pad flow check (worn, then seam, then craft). Shoot: `--quick warden --zone waystation --time day --items "old_iron*14,wolf_pelt*5,ember_shard*9,iron_helm:3" --gold 400 --open "talk:brannoc>work my gear" --anvil iron_helm` (add `--pad --focus temper` for the heat preview). The arena result's `Carried out` now shows materials as slots (`src/Ui/ArenaResult.cs`, Haul).. The old list: announcements, item card, journal deeds and codex, HUD dash and draught; `docs/ui_review/`;

From `worktree-agent-a565196002a51af40` (2026-10-05 3c9aa379):

6. **Spare or finish** (combat's `StoryChoices` in `WorldType.cs`, shown by `GameHud.Choice`/`ChoiceHeld` from `GameChoice.cs`, on `worktree-agent-a427a874da78cba8b` at cdce2802): type in the banner's place, a ledger line filling under each answer while its key is held. Merge their branch and judge it beside the fall's choices (one family: the held moment as type on the world).
7. **Portraits** when the face lead messages: re-run `tools/assets/heroine_paint.py` and `tools/assets/creation_portraits.py`, then shoot the Look. The male Look waits for the male hero lead.
- **`G.After` stops while the sim is paused**, so a fall can't hold the world still before the result (combat's StandDown stills it instead).
- **Combat (a427a874da78cba8b):** fixed the let-go fall on their branch (`StoryNight.StandDown`: her weapons quiet, the ground cleared, every creature still, her controls held). They also flagged "Survived" over a story night with no clock: it now reads "fought". Their branch has the spare-or-finish choice (section 4, 6).

# Handoff: classes (phase 1, systems: the Lamps, the Flare, dash forms, reflexes)

Written by the first classes lead for its successor. Branch `classes/phase1` (from integration `cdd42d06`); see the last line for the commit.

## 1. The owner's words

- 11 October 2026, on docs/design/CLASSES.md: **"go with all 8 recommendations"** (§8): Flares locked to the calling; respec free by day with two layouts; the type picked at creation, never a lock; Q / right-click is the Flare, the draught stays on R, the Kin rides the dash on its own wait; the names the Lamps and the Flare; about 50 lamps at the end; systems first, then one Flare per calling; the 0.22 s freeze stays, with a setting to shorten it.
- The Flare: "it should be AWESOME. it should look AWESOME." (phase 2's; ours is the logic). The bar: "we are striving for perfection".

## 2. The brief (phase 1, CLASSES.md §7; spec §0, §2, §3.1-3.4, §5, §7)

Lamps' data; lamps from levels and story fights; respec and layouts; the night rule and leans; the new tags and Bound; reflexes; dash forms (ArtBook migration, all four facets); the Flare's meter, window and clutch (logic and data); the `Act` renames in two steps with bindings and a save migration (full lamp refund); the harness taught types, lamps and Flares; tests. Acceptance (harness): types within ×1.35 of the median at tiers 1-4; on-calling ≤ ×1.25; a full board at night within ×1.25 of an empty one; Flare timing (first by ~2 min, then every 60-90 s, 2-3 per boss, 15-25% of a boss's damage). Not ours: Flare clips/VFX/camera (phase 2), the Lamps screen (phase 3), new weapons (phase 4). A plain debug readout is fine.

## 3. Done (session 1)

- **Act renames, both steps** (`95922558`, `36e775ce`): `Act.Draught` (R, pad X; a saved "ultimate" binding is read as it), `Act.Flare` (Q / Mouse2, pad Y; a saved "ability" is read as it). Q still calls `UseAbility` (WorldScene, Autopilot) until the Flare is wired.
- `AbilityKind.RedTide` and `Spellward` exist as reflex-only arts (no behaviour yet: `UseAbility`'s switch returns false). ArtsScreen lists them as learnable to their callings: hide reflex-only arts there when wiring.
- `StoryLint.Outside` lists the fact `lamps.atlas` (written by the atlas, not the story).
- **The board:** `tools/classes/lamps_build.py` + `lamps_quarters.py` are the source (edit there, run, commit the JSON) → `godot/data/content/lamps.json`: 360 lamps, 8 roads, 16 Flares (generic numbers), story lamps' fight ids. Every effect has a `phase` (1 live now; 2 first four Flares' mods; 4 heavy/greatsword/shield-grip; 5 new skills; 6 other Flares).
- `logic/Content/Lamps.cs` (data, board joins, night constants, `FlarePower`), `logic/Rpg/LampBook.cs` (earned = level-1 + story wins (`arena.<id>`=won) + atlas fact `lamps.atlas` ≤ 8; three free lamps: start, type's entry, type's Strike; light/unlight (stays connected and gated)/clear/SetType (all out)/two layouts/Carry/Suggest/LightSuggested/`Loadout(ch, night)`), `logic/Sim/LampLoadout.cs` (what a fight gets; `Size()` quarters by night, `Full()` for prices).
- `CharacterData.Lamps` (null in old saves; `LampBook.State` creates).
- **Tags** Heavy, Shield, Twin, Hook appended to `Tag`; **Bound** appended to `StatusKind`: `Enemy.BoundX/Z`, tether in `Ai.FinishMove` (`Battle.BoundSlack` 0.8 m; bosses never locked), +20% from Area (`Battle.BoundArea`), `ApplyStatus` case.
- `tests/LampsTests.cs` (shape, reach, small-lamp rule, arts/facets exist, earning, gates, respec, type, layouts, Flares, night loadout).

## 4. Next, in order

1. **Battle wiring** (`Sim/Arts.cs`, `Sim/Battle.cs`, `Journey.StartBattle`, `Character.Kit`): `BattleSetup` gets `LampLoadout`, form wait, reflex ranks, char level. Design decided:
   - `ch.Ability` stays "the art in hand" = **the dash form** (movement arts, or Not Yet). Creation and the v5 save migration turn a held calling art into the calling's Kin. Kin facets come only from lamps; learned forms keep ArtBook rank facets.
   - `Dash()`: if a form is in hand and `p.AbilityCd <= 0`, cast it with the dash's direction (wait = `KinWait` or the art's Cooldown, × RankHaste). Forms that move her (Rush, Leap, Blink, Mirror Step's step) replace the dash's motion; i-frames and the perfect window stay. Bull Rush to spec: 6 m, barrier 15% (Iron Hide 25%). Vault springs the way you aim.
   - Reflexes: own waits; run an art by swapping `p.AbilityCd` in and out (the art functions adjust it). Facets: union of form and reflex facets (assert ids unique across arts). Triggers: crowd, big_blow, swarm, low, dire, spells, every, perfect. New arts Red Tide and Spellward (append to `AbilityKind`).
   - Flare: meter per §3.2 (hooks in `HurtPlayerRaw`, `PerfectDodge`, the block branches, `HitEnemy` for boss/champion share, kills with a +1/s cap); `Stat.UltCharge` → `FlareFill`; Banked Flame two charges; story fights start at 50 (StoryNight), maps carry (MapRun). `UseFlare` on Q: Strike holds controls ≤1.2 s, untouchable +0.4 s, blows over its length; Stand: untouchable 1.5 s, pulses; burns missiles within 6 m; clutch below 25%: mend 20% over 1 s, reach +25%; bosses interrupted and lightly staggered. New `Ev.Flare` events; `FlareFreeze = 0.22` with a setting scale for phase 2.
2. Save v5 is in (`ch.Lamps` created: full refund). Add to it, with the wiring: a held calling art becomes the calling's Kin (and the same in `Character.Create`).
3. Wire the phase-1 rules (the lamps' `rule` ids with phase 1; a test that each is handled by `Battle`), the road lean in the draft (×1.25 for `Lean`'s skills, × path lean, clamp ×2), the four Flare great blessings, map mods Smothered/Bright, endless Flare ranks.
4. Harness: `--type`, `--lamps empty|full|suggested`, Flare cast policy and the timing/share report; judge the acceptance numbers (a `su-lead-max` judge on the numbers).
5. HUD debug readout of the meter and the board; status/handoff.

## 5. Gotchas

- `dotnet test` takes 5 min (760 + new). Don't build while a worker builds the same project (obj locks).
- The worktree is 8 on disk at the start (the cap). This one is `agent-a2a42cd8430929a76`.
- Small lamps by night give nothing but the road's lean; attribute lamps likewise (§2.10).
- Lamp text must say what the lamp does; the names are drafts for the story lead.
- Tests: 771 green (3 min 45 s).

HANDOFF READY: docs/handoff/classes.md on classes/phase1@14b6be4b

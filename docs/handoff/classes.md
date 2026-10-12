# Handoff: classes (phase 2: staged Flares measured, judge next)

Written by the seventh classes lead (12 October) at the context budget. Branch `classes-6` (worktree `agent-a5b513003773e2317`). See the last line for the commit.

## 1. The owner's words
- "go with all 8 recommendations" (CLASSES §8); the Flare "should be AWESOME. it should look AWESOME."; "we are striving for perfection". 12 October: "go just classes for now" (classes is the only lead running).
- 11 October: "rebuke should probably do a little more damage than that yeah".
- 12 October, Banked Flame: (1) "sounds good": Light my way never lights it (DONE, `LampBook.Suggest` skips `flare.banked`). (2) "0-5% faster is barely anything though, seems like its a lot of risk with not much reward". Played well, it must be a clear reward worth the risk of its 30% slower fill, and its text must make it a trap-free choice. "A blue lamp should feel worth building around."

## 2. The brief (main session, 12 October) and where each step stands
1. **The rebuke's checks: DONE, reported to main.** Whole, it took 8-14% of a boss, a rival to the Flare. A boss now takes half (`shield_arm boss=0.5`, in its text): 4.5-5.3%. Act 1 with a bulwark (`story --type bulwark`) is within -5%/+4% of the old rule, falls no higher. The Prologue can't hold a bulwark (no type choice in play yet; SetType is harness-only) and has no balance harness; Act 1 at level 1 stands in for it.
2. **Merge:** main merges the whole branch after a **go/no-go from you, based on the judge's verdict on all four staged Flares.** If one fails and its fix is long, gate just that one back to its plain form (FlareBlow's switch in `Flare.cs`; its data `blows`/`power` changed too, see git history of `lamps_quarters.py`) so the rest can merge.
3. **Phase 2, the judge (NEXT):** the numbers are in `scratchpad/c7/sheet2.md`. The confirming run `c7/fin/` (story arcanist at Burns x0.8; kindler arena full/empty; Banked Flame cells sunderer T4 L10 and L30 full) was running at handoff: read it with `python c7/stcmp.py c7/st/base.jsonl c7/fin/story_arc.jsonl` and `python c7/p2stat.py fin=c7/fin/burn_full.jsonl fin=c7/fin/burn_empty.jsonl`, add the lines to the sheet, and check that Burns at x0.8 lands Act 1 within about ±3%. Then a fresh `su-lead-max` judge (Context budget: 150k) gets the sheet, the owner's words, CLASSES §3.5-3.6/§7 and a checklist: (a) each Flare's design against its brief; (b) Act 1 kill time for the staged defaults (Burns, Toll) within a few % of the plain forms'; (c) the arena took-share band, given that boss gates make it insensitive to power (sheet D); (d) Burns' full board at 27% from Called Down; (e) Butcher's Hour: 9-13% slower boss kills at T3-T4 than the Bill, no damage of its own; is its extension cap (its length again) right, and does it need a boss answer; (f) the T1 median of about 25.8% (the butcher's Bill at 31%; my reading: weak kit, not a strong Flare; the Bill is staged in phase 6); (g) merge safety. Then send main a go/no-go.
4. **Banked Flame, after the verdict:** re-run the two cells (in `c7/fin/`, the banking pilot). Then propose 2-3 options with numbers at 48 seeds for the banking pilot and a non-banking one (`--bank 0`), for example a 15-20% price, a second charge that fills faster or comes cheaper, or a gift that pays even when spent at once (say, a banked charge's Flare 25% stronger). Have the judge pick, and fold the pick into the go/no-go.

## 3. Decisions this session (why)
- The Toll's poison is its own DoT (`TollVenom`/`TickVenom` in FlareStaged.cs). Her poison stack ticks at its strongest rate times its stacks, so a 2100-power cut lifted her whole stack and took its credit (71% of a boss at T4).
- The Toll's boss cuts carry four cuts' worth (`onBoss`; data `bossWorth` overrides). This is the plain form's worth after power went 700 to 2100. The judge had written "12/boss cuts", but at 12 it did 5-8x the plain form per cast.
- Burns' embers strike a boss only when aimed at it, and never fall back onto a lone boss.
- `bossMul` (a Flare arg in FlareHit, bosses only), calibrated on Act 1 story kill time: Burns 0.8, Toll 0.85. The arena took-share is set by the boss gates, so it is no lever (sheet D).

## 4. Gotchas
- The harness reads `lamps.json` at process start. Variant scripts patch `lamps_quarters.py`, rebuild and restore (`c7/var.sh`, `c7/r3.sh`). Never build Release balance while a run is going: the dll is locked, the build fails quietly with "2 Error(s)" and the old dll runs.
- Baseline (integration) harness: `c7/base/godot/balance/bin/Release/net8.0/Balance.dll` (git archive of integration, built). Its story has no `--type`.
- In foreground bash, wait with `for i in $(seq 1 58); do [ -f done ] && break; sleep 10; done`.
- Scripts in `c7/`: `rebcheck.py` (rebuke A/B), `p2stat.py [--split] label=file` (Flare per type/tier, boss split by source), `stcmp.py base now [callings]` (story), and c6's `typeband.py`. Scratch root: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\ba85aba8-36f4-4cf9-99c5-4c5ef9e4a65c\scratchpad\`.

## 5. Files to read first
`godot/logic/Sim/FlareStaged.cs`, `Flare.cs` (FlareBlow), `WardenLamps.cs` (Rebuke), `godot/logic/Rpg/LampBook.cs` (Suggest), `tools/classes/lamps_quarters.py` (the flare() lines), `docs/design/CLASSES.md` §3.6 and §7, `c7/sheet2.md`.

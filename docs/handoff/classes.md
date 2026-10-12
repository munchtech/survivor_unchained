# Handoff: classes (session 9: Hour hotfix merged, press-stagger hotfix in progress, early modifiers built)

Written by the ninth classes lead (12 October) at the context budget. Branch `classes-8` (worktree `agent-a54ebb1323cb25841`), last commit on the last line of git log. Scratch: `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\1515c1de-1208-43e2-b6eb-5133e0d07e1c\scratchpad\classes\` (below `N/`); the eighth lead's tools and runs are in `...\ba85aba8-...\scratchpad\c8\` (`c8/`).

## 1. The owner's words and the coordinator's standing calls
- Banked Flame: "0-5% faster is barely anything though, seems like its a lot of risk with not much reward": played well it must be a clear reward; a non-banker no worse than today; its line honest.
- "begin planning for flares to have 1 per spec" (via main). Build nothing for phase 6 until the owner approves.
- Coordinator (12 Oct): ship the **press-stagger fix as its own hotfix from integration** (like the Hour's), and in the same hotfix re-tune the four Act 1 story-boss health multipliers back to their **pre-Flare kill times for both deft and plain pilots, with no rise in falls**. That is within the owner's 11 October yes; only an outcome off that target goes to main as a question. Report kill time per boss vs pre-Flare, wins, falls, and the checks. Light my way's early rule: go (done). Phase-6 owner lines: bring them once the 10 fixes are in.
- Keep the Hour falls follow-up on the list (0.066 vs the plain form's 0.056 a run).

## 2. Where each step stands
1. **Butcher's Hour: MERGED** (integration a86814cc, from `classes-hourfix`, deleted). Every blow while it holds deepens one bleed (`deepen` arg, bleed 0.8). Act 1 vs plain form, 3072 runs a side: mean -1.6%, worst cell -5.2%, won 98.1 -> 97.8%, falls 0.056 -> 0.066 (1.6 sigma). Mend 2% (0.064) and execute 25% (0.065) did not move falls: a solver if it still shows after the stagger fix (`N/st/ph_all.jsonl`, `hd_all.jsonl`; `N/falls.py`).
2. **Press stagger: IN PROGRESS (hotfix).** Bug: Flare.cs:210 `AddStagger(e, e.Boss ? 15 : 30)` on a 0-1 gauge stuns a boss 3 s (1.25x taken) every press; the Bell's `"stagger": 15` (lamps.json, lamps_quarters.py) same unit. Fix: 0.15 / 0.3 and the Bell 0.15 (make the press value a data/const with a comment).
   - Scratch tree `N/st2/godot` = integration (f0a525fa) + the fix + switches: `SU_NOFLARE=1` (no Flare), `SU_HM_Redcowl|BarrowLordStory|Greymuzzle|GrimtunnelStory=<mul>` (health). Runs: `bash N/s2run.sh <tag> ENV=...` -> `N/s2/<tag>.jsonl` (all callings, 96 seeds, greedy/random, plain/deft, 6144 runs, ~45-60 min). Queue `N/s2q1.sh` (background, was running): `pre` (no Flare, old health 103/130/100/109 = the pre-Flare target) then `fix0` (fix at today's 118/148/110/123).
   - First read (classes-8 tree, deft, 48 seeds, `N/bk/sg_deft.jsonl` vs `bk/ref_b1.jsonl`): bosses +1.5% longer (warden +3.8%, worst cell +10%), falls 0.025 -> 0.031.
   - Next: per boss (fight) and pilot, compare `fix0` to `pre` (mean boss seconds; write a small per-fight script from `N/bsum.py`); scale each mul by pre/fix0, re-run, iterate once; falls no higher than `pre`... then build the hotfix like `N/hf/mk.py` (temp index on integration, `git commit-tree`, branch `classes-staggerfix`), export it (`git archive` to scratch) and confirm one run matches; report to main. Boss files: `godot/logic/Play/Bosses/{Redcowl,BarrowLordStory,Greymuzzle,GrimtunnelStory}.cs` HealthMul (Roost, Vault, Hollow, Dig). Then merge integration into classes-8.
3. **Light my way early modifiers: BUILT** (b9db3807, tests green): `"early"` on More Embers, Bell for the Dead, Toll Doubled; `LampBook.Suggest` skips other modifiers until `chapter.done`; arena harness boards light the whole path. CLASSES §7 rule rewritten. To measure: More Embers dig deft at 384 fresh seeds (if past 6%, switch to Black Ice); Toll Doubled alone; `Balance.dll suggest` path.
4. **Banked Flame: measured, judge next.** Arena boss floors (ArenaBoss phase `Floor` minimum times; overflow only lengthens the Break stagger) hide any burst reward at arena bosses: say so plainly. Numbers (boss kill time vs no lamp; banked b1 / unbanked b0):
   - Floors off, T4 L30 deft (`c8/runs/*_L30f0`, `N/bk/ar_*`): cur -13.3% / +5.6% (median); A15 -11.8/+3.7; B -15.9/+3.2; **C (every Flare 25% harder) -17.0/+0.1 (mean -20.5/-2.4)**; D -12.7/+5.6; BC -9.9/+0.8 (mean -14.4); C40 arena pending (`N/bankq2.sh`).
   - Act 1 (L1, deft, 48 seeds, every calling; `N/bk/*.jsonl`, `python N/bsum.py bk/ref_b1.jsonl ...`): cur -5.5/+5.6; B -4.3; C -8.0/+4.4; BC -7.0/+3.4; C40 -8.2.
   - Floors on (arena T4 L10/L30, deft and plain): every variant within ±4%. Plain hands T4 L10 (`c8/runs/*_plain`): falls 0-3 of 48, no life-saver signal; banked low-HP runs a little fewer.
   - Lead's lean: C (text: "Hold two Flares. Each fills 30% slower and strikes 25% harder."). Judge questions: pick; and whether arena floors should let a burst through (overflow shortens the next phase's floor), which is the only way a boss-burst reward can show at arena bosses (a design change for main/owner).
5. **Bell Vault plain cell** (~-7% pooled): judge says measure 3 arms after the stagger fix (`N/judge1_verdict.md` Q2).
6. **Phase-6 plan: judged, PASS WITH 10 FIXES** (`N/judge1_verdict.md`): apply the fixes to CLASSES §7 "Phase 6 plan" (a su-worker can, with that file), then send main the owner lines from the same file.

## 3. Tools
- Harness copy `N/bal1` (this session's build; rebuild after logic changes: `cd godot/balance && dotnet build -c Release`, copy). Story runs from cwd `godot/`. `--over DIR` data overrides; `N/mkargs.py lamps.json out flare k=v`; `N/mkvar.py` (Banked variants, `N/bover/`).
- Summaries: `N/stsum.py base now [calling]`, `N/cell.py a b fight hands`, `N/took.py`, `N/falls.py`, `N/bsum.py` (per calling, Act 1), `c8/bstat.py` (arena Banked).
- Python on Windows: give it `C:/...` paths, not `/c/...`.

## 4. Next, in order
Stagger hotfix (tune, build, confirm, report) -> merge integration into classes-8 -> Banked Flame judge (lean sheet from §2.4) -> phase-6 fixes and owner lines -> Bell Vault arms, More Embers / Toll Doubled checks -> Hour falls solver if still high.

# Handoff: classes (session 11: the Flare cuts arena phase floors; Banked Flame reworked)

Written by the eleventh classes lead (12 October). Branch `classes-8` (worktree `agent-a54ebb1323cb25841`), last commit on the last line of git log. Scratch `N/` = `C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\33ad5b17-6735-4f1b-843e-85f16b19e648\scratchpad\classes\` (older: `1515c1de-...\scratchpad\classes\`, called `O/`).

## Start here
1. **Merge request sent** (Banked Flame H plus the arena cut; numbers in CLASSES §7 line 901 item (2) and acceptance item 5). Wait for the coordinator's merge and the owner's word on the summary (judge 5's paragraph, in `N/judge5_sheet.md`'s verdict as relayed; the owner may want story bosses cut too: today they keep their floors).
2. **Next: the phase-6 plan** (CLASSES §7, 6a) and its owner lines (`O/judge1_verdict.md`, bottom) to a lean `su-lead-max` judge (Context budget 120k), then to the coordinator for the owner. No phase-6 code before the owner approves.
3. Pass on to UI/codex: "a Flare shortens the boss phase it lands in, by at most half, never under 6 s" should be taught (judge 3).
4. Open, not blocking: the arcanist's full board (Burns Twice with all three modifiers) reads 34-40% of a boss with no lamp (acceptance (2) wants 15-30%): phase 7's sweep. The reaver deft banker sits at the band's fast edge (-22 to -23% at L30).

## 1. Done this session
- Merged `claude/vigilant-galileo-l6jqyx` (docs only), 834 tests passed.
- **The cut (owner: "let arena phases shorten")**, 4659982f + b8828e4b: `ArenaBoss.FloorNow = max(Floor*FloorScale*(1-FlareCut), min(Floor*FloorScale, 6))`; `FlareCut = min(0.5, 1.0 * Enemy.FlareTook / phase span)`; only health credited "flare" counts (Battle.cs next to BossHealthBy). Story bosses exempt (`StoryBoss.FlareCuts => false`). Harness `--flarecut MAX[,RATE]` (default 0.5,1), `ArenaBoss.PhaseLog` -> `BossPhases` in arena results. Tests in BossTests and StoryNightTests.
  - Cut alone, every player: arena bosses -6 to -15% (arcanist -18 to -24%); the Flare's no-lamp share fell (arcanist 43->34%, 48->40%).
- **Judge 3** (a46133c0270318ade, sheet `N/judge3_sheet.md`): cut PASS (rate 1, cap half) plus the 6 s minimum; story bosses keep floors PASS; Banked Flame not bound by the 35% line (its own kill-time bound); keep the price; M1/M2 asked.
- **M1** (`N/m12/pa_*`): a phase-aware banker (holds the second charge while this phase's cut >= 0.25) beat firing both at once for every calling; now the harness default (`--phaseaware 0` for the old hands).
- **M2** (`N/m12/m2*`): C40's non-banker cost the arcanist L30 +14/+17% (plain) and +5/+9% (deft): the half cap swallows "strikes 40% harder".
- **Judge 5** (a8ae3459f53288069, sheet `N/judge5_sheet.md`): H PASS at held 0.75; band restated to 6-25% (no single held fits 8-20%); warden L10 confirmed at 192 seeds a hand (`N/j5/`): -14.3% / -9.8%. Results `N/j4/`, summary `python N/j4sum.py`.
- **Judge 4** (aefdc28772b26d345, sheet `N/judge4_sheet.md`): FAIL for C40; fix applied in daa58e19: Banked Flame = "Hold two Flares. The second fills half as fast; a Flare fired with both held strikes 75% harder." (`slower 0, second 0.5, harder 0, held 0.75`). Tests: data and behavior (a held shot 1.75x, never-held fill unchanged).
- **The Hour at the Dig** closed without a trim: fresh seeds at twice the runs -2.3%, pooled -4.0% (inside ±6%). Arms tried and dropped (`N/dig/`). CLASSES §7 notes for Bell's Vault, the Hour's falls and the Dig written (31f9ed99).
- C40 floors-on numbers (the old `bq4.sh`, folded in): banker -3% before the cut; the reserve saves nothing (falls 5 vs 6 of 384, `N/fc2/res_*`).

## 2. Tools
- Harness copies: `N/bal3` (cut, C40), `N/bal6` (+6 s, phase log, phase-aware flag), `N/bal7` (H lamp, phase-aware default), `N/bal8` (+ `FlareFullBankShots` in results). Rebuild after logic changes: `cd godot/balance && dotnet build -c Release`, copy to a new `N/balX`. Runs use cwd `godot/` (data read from there).
- Overrides: `N/over/plainhour3` (plain Hour), `N/over/nomods`, `N/over/cdonly` (Burns Twice modifiers off / Called Down alone; made from C40-era lamps.json: remake from the current one before reuse).
- Python on Windows: give it `C:/...` paths.

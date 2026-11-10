# The ARPG design lead 1 (8-9 Nov): `docs/design/ARPG.md` on design-arpg; three judge rounds, the last FAIL close with its five fixes applied; a confirm judge is needed before the owner sees it

Brief: `tools/scratch/coordinator/briefs/ARPG_design_lead1.md`. Owner's words: `docs/design/ARPG_DIRECTION.md`, `SIEGES.md`, and on the dash: "its decent fundamentally - its improvements behind the scenes are awkward - just pushing the button leveling it up is weird". Report to main. Docs only, no game code. The worktree is a junction worktree (`godot\assets` links to its own `public\assets`): never merge, reset or checkout without the junction rule in `lead_brief.md`.

- **The page:** `docs/design/ARPG.md`, with the owner's one-page, the systems table, skills and Unions, the arena, the tutorial, acts and zones, loot, death and difficulty, the siege hooks, the migration list M1-M11, and 13 owner's calls with picks first.
- **The picks:**
  - pressed skills (six keys, Resolve built by the grip, waits on movement, never rooted, kindled skills keep a press);
  - the arena's rule: the ember casts for her;
  - Unions on two keys with a bond (Bladestorm = Cleaver + Sunder: hold to spin, a fresh press of Sunder breaks it);
  - slots at levels 1/4/5/7/9;
  - the dash's steps from story beats and gear, never from level-up cards;
  - levels light lamps anywhere out of a fight, and lamp-posts change them;
  - handcrafted acts, generated endgame maps;
  - world tiers;
  - she rises at a lamp-post.
- **Judge (Item: ARPG design, 3 of 3 rounds, su-lead-max, foreground):** r1 FAIL medium (13 findings), r2 FAIL close (9), r3 FAIL close (5: map rises against the owner's MapRun rule, board points from posts, Iron Vow unbuilt, the total, M1 wording). All of r3's fixes are applied but not judged after them. **Next:** main raises the cap for one confirm judge (the r3 list as the checklist), then PROPOSAL READY and the owner's pick.
- **Sent early to main for the skills lead (skills-p7):**
  - Rule 1: the dash is a plain evade with visible steps; Bull Rush becomes the pressed Shield Charge, whose four facets are its wick (Pile Driver is the Turn);
  - the Union's two keys;
  - since then: dash steps come from story beats and gear, and the hearth lamps hold only the endings;
  - the WIP's union must split so each key drives its half;
  - Bladestorm paid from Resolve.
- **Gotchas:**
  - "The Deep Shaw" is a name the table generates, not a place.
  - Cleaver, Heroic Leap and Iron Vow have no wick in `skill_lamps.json`.
  - `MapRun.cs:34` records the owner's "a fall closes the map".
- **Cost:** lead ~0.32M; surveys 2 × Sonnet; judges 135k + 128k + 111k.

**PROPOSAL (needs a confirm judge) design-arpg@HEAD**

# C2 one build (5 Nov, lead 2): MR READY classes-c2@f83bb3878 (judge PASS WITH KNOWN, the known list closed)

Branch `classes-c2` (junction to its own `public\assets`), integration merged at e3fcfb760, pushed. Suite 1565/0/10 after the merge. Report to coordinator cd68c87d via SendMessage "main".

- **The judge (Item: C2 design, 3 of 3 rounds, all max, foreground):** r1 FAIL, distance close (the JSON medium: Rebuke's answering strand at source, about six Turns that didn't transform); r2 FAIL, close (ten line marks); r3 **PASS WITH KNOWN, close**, its eight known items closed in f83bb3878. What changed: Rebuke's answering strand remade (the light travels: The Long Answer, Tidings, Slow to Anger, Open Rebuke); Shield of Morning, Circle of Dawn, Stone Bell, Crow's Foot rewritten as true Turns; Back Furrow, Morning Road, Turned Aside replace lead-ins that were smaller copies of their Turns; points burn once lit (Light my way on coming into a town, the dawn card's lamp first), so the Ford starts with nothing lit; one card an offer always dealt; the card shows the hit; keywords; the honest price line; Union shared is a decided line (two owner questions left); 11 migration items added (16 in all); §6 in seconds.
- **The harness switch is inert:** it wrote `"OneBuild":false` and `"Kit":[]` into every line without the flag; both are now left out when off (bf959efa7). Base d243d83fb vs head, no flag, sorted-line compare: arena 36/36, types 32/32, pair 16/16, story 64/64 identical; with `--onebuild` 8/8 lines carry Kit and /onebuild. Script: `survivorsunchained_inputs\scratch_classes_c2\lead2\eq\eq.sh`.
- **The JSON is the source now** (lead 1's generator retired; backed up in `scratch_classes_c2\lead1\`). The checker adds: no barrier or mend under 2% of health an event without a cap, blow-fed barriers bounded, Stones a line can reach (the wall answers at six), keywords, "judgement".
- **For the owner (two questions, the picks):** skills open by level (a schedule the story can teach; loot stays gear); keep the slots 2/3/4/5/6. Decided by design: a Union is one shared lamp, both skills firing (a merge only loses a skill mid-run).
- **For the C2 build lead:** ONE_BUILD §5 (16 items; item 14 is A1's "swing damage at the clip's contact frame"; item 16 renames Judgement to Judgment in skills.json); §6's misses are numbers only (level 5 too hard, level 10 too easy, the tier-4 veteran under the band; re-run the standing bot with the four blow-fed Turns lit, each and together).
- **Cost:** lead 2 ~0.29M; judges 139k + 124k + 120k = 0.38M; $0 API. Lead 1 ~0.6M. C2 design in all ~1.27M.

# C2 one build (5 Nov, lead 1): the four deliverables are on the branch; HANDOFF READY at ~285k. Next: the judge, then merge and MR

Brief: `docs/team/hook/C2_one_build.md`; coordinator brief `tools/scratch/coordinator/briefs/C2_lead1.md`.
- **Branch:** worktree `.claude/worktrees/classes-c2`, branch `classes-c2`, cut from d6b6a8345 (integration not merged in since).
- **Junction worktree:** `godot\assets` links to its own `public\assets`. Before merging, remove the link (`cmd /c rmdir godot\assets`), merge, then remake it and `git update-index --assume-unchanged godot/assets`.
- **Report to:** coordinator 88131549, via SendMessage "main".

## State (all committed)
1. **`docs/design/ONE_BUILD.md`** (d243d83fb, cae5f9a21): the owner's page; the rule; the offer; what dawn takes and the dawn card's memory; the data model; the 14-item migration list (item 1: the wicks' bare-percent lead-ins; item 2: the night draft's full pool, cut); and the harness note (§6).
   - The coordinator asked for, and got, one paragraph each on a newcomer's first night and a veteran's tier-4 night, in play terms.
   - Three open questions, each with my pick:
     - skills open by level (no tomes);
     - Unions as a shared lamp, both skills firing (Hades' duos), not a merge;
     - keep the slots (2/3/4/5/6), so a first night has 2-3 skills.
2. **`godot/data/content/skill_lamps.json`** plus `tools/classes/skill_lamps_check.py` (ed3a9cd4b): the warden's 7 wicks in full (84 lamps), Dawn's Judgement, and two proposed Unions (Broken Country, Curfew). The checker passes. The game doesn't read the file.
   - The solver's four calls, which I accept:
     - the evolutions' pure multipliers dropped, since rank carries power;
     - Reckoning remade as endless climbing ricochets;
     - the bare-stat v1 lamps dropped or given a mechanic;
     - Dawn Rhythm adds to the timer rather than replacing it.
   - Generator: scratch `classes_c2\gen_skill_lamps.py`.
3. **Harness `--onebuild`** under godot/balance only (cbde3e259). It is unverified that the sim is byte-identical without the flag: a no-flag run was argued from the code, never diffed. The R0-R3 tables are in ONE_BUILD §6.
   - The 45-60 s rule holds: standing falls on every tier-1 night, at every level.
   - The bands miss: level 5 is too hard (human 61%; reaver 12%), level 10 too easy (human 100%, idler wins 61%), and a veteran at tier 4 is under the band (human 75%).
   - Data: scratch `classes_c2\h\` (r0-r3.jsonl, run.sh).

## Next (in order)
1. **The judge.** One su-lead-max judge in the foreground on ONE_BUILD.md, `Item: C2 design`, round cap 3.
   - The question: would a PoE veteran and a first-time player both understand this in the game, one system at a time, never a wiki?
   - Give it the page and `skill_lamps.json`, not my conclusions.
   - `Marionette/JUDGES_PAUSED` says `allow: judge`, but a foreground subagent suits a text page.
2. Make the judge's fixes.
3. Merge `origin/claude/vigilant-galileo-l6jqyx`, under the junction rule.
4. Run `dotnet test` in godot/tests. The last green was 1565/0/10; nothing under logic/ or src/ changed, but the new data file and the harness must not trip a test.
5. Push, then put `MR READY classes-c2@<sha>` here and send it to main, with the three questions and the cost.
6. Back up scratch `classes_c2\` to `survivorsunchained_inputs\scratch_classes_c2\` and clear only that subfolder.


Older blocks: history/classes.md (grep by keyword, never read whole).

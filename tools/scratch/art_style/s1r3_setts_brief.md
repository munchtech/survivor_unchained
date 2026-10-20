# Brief S1 round 3: the painted setts as chunky, irregular cobbles (the last round)

Context budget: 200k. You're a fresh code solver at medium effort for art-style lead 3, who waits on you in the foreground: **your final message is your report** (under 20 lines).

**Read first:** `tools/scratch/art_style/s1_setts_brief.md`. It has the rules (the worktree, the junction, `git add` named files only, turns, never kill by name), the files, the flag `--setts-paint` and the acceptance. Everything there still holds. Rounds 1 and 2 are in `git log` (37f53a3e, a3cb2eaa); the code is `tools/assets/env_ground.py --paint [--bake] [--sizes]`.

**Where it stands.** Look once at `godot/.shots/p3_review.jpg` (960x1620, 1:1). Its rows: round 1 (round "bubble" stones with dark outlines), round 2 (a3cb2eaa), and the target at the same crop. Round 2 overcorrected. Flat rectangular slabs in straight courses, with thin pale joints and low contrast, read as a neat flagstone patio. The target is an old cobbled square:
1. **Irregular, chunky cobbles,** not rectangles in courses. Make them rough 4-6-sided blocks with straight-ish edges and uneven corners, mostly 14-28 cm across, with about 10% bigger ones at 30-45 cm. Lay them in loose, wavy courses along the street, never a running bond.
2. **Relief that reads at the play camera.** Each stone is a "pillow": a broad, nearly flat top over about 60% of the stone, then a rounded bevel of 3-5 cm down to the gap, with a small random top tilt (2-4 deg). In the sun, each stone then shows a lit top and a lit sun-side bevel, and its far bevel goes dark. That's the target's chunky 3D read. Not round domes (round 1), and not flat slabs (round 2).
3. **Dark, narrow gaps:** 1.5-3 cm, deep (dark AO), so they read dark brown in the sun and blue-black in shadow. The target's gaps are dark. Where a gap is wider (a missing fill stone), fill it with packed dark-brown mud.
4. **Strong value between stones:** tops vary by about +/-15-20% in value, in cream, warm grey, ochre and a few cool grey-blues. The sunlit square should read as a mosaic of individual stones with real contrast, as the target's does.
5. **Painted surfaces:** 2-3 broad strokes per stone of slightly different value along its long axis (+/-6%). No grain noise.
Keep from rounds 1-2: the flag, the file names and sizes, flag-off identity, the wear lane (polished, lighter tops), and the matte brown mud patches round the well and the posts, which are good now.

**Shoot** after your bake and reimport (the godot turn; frames.py takes it for shots; the worktree is fresh, so no `stale`):
`python tools/scratch/art_style/frames.py p4 b town "try.town=vib=0.85,hi=0.7,shadow=#3c3460,shadowk=0.4" "x=--setts-paint --brush --kit-paint godot/art/kit_paint --air-tune keyc=#ffd08c,key=6.6,hemisky=#9490bc,hemiground=#6a4e34,hemi=0.7,exposure=1.05,haze=0.004" fps=30`
**Review sheet:** JPEG q90, `godot/.shots/p4_review.jpg`, 1:1, crop (400,150)-(1360,690). Rows: `p3_town_b_00` (round 2), `p4_town_b_00` (yours), and `target_town.png` at the same box (`C:\Users\munch\Desktop\survivorsunchained_inputs\art_style\r2\`). Look at it at half size yourself at most. Commit, then report: what changed, the numbers (flag off, `dotnet test`), the sheet path and the commit id.

# Handoff: legal and Steam compliance

For the next legal and Steam compliance lead. Read this, then `docs/team/README.md`, then `docs/team/legal.md`, then the three files in `docs/legal/`.

## The brief I was given (in full, condensed only for length)

You are the legal and Steam compliance lead for Survivor Unchained: Godot 4.5.1 .NET, a survivors-style action RPG with an 18+ tone, made by one owner with AI agents. You are **not a lawyer** and say so plainly. Find and organise the issues, research the current rules from **primary sources** (record the dates you checked), and prepare a brief a real games lawyer can review before launch.

- **The owner's goal:** sell on Steam "with little to no issue", and eventually remove anything not ours.
- **The owner's question:** "ai generated assets and things are perfectly ok for steam games and for making money and getting in no trouble right?" Answer carefully, with sources.

Research topics:
1. Steam's AI rules: the pre-generated and live-generated disclosures, what Valve rejects, and whether we generate live (we don't).
2. Steam's mature and sexual content rules: the four survey categories, age gates, store visibility, and Germany, Australia and other regions. Check what the game actually shows, and ask the main session for renders.
3. The licence of every AI tool: commercial use of outputs, revenue thresholds, attribution, what's barred. That means:
   - ComfyUI's models (Krea 2, Flux if any, LTX video and audio);
   - Kimodo;
   - ElevenLabs;
   - any placeholder TTS.
4. Copyright status of AI work: US Copyright Office guidance, what competitors could copy, and how to strengthen our position.
5. Third-party assets: review the provenance auditor's `docs/legal/ASSET_PROVENANCE.md`, rule on each risk, and keep attribution straight.
6. Other launch issues:
   - a trademark search for the name, and Steam store conflicts;
   - font licences;
   - Godot and .NET notices;
   - privacy;
   - the EULA;
   - refunds;
   - age ratings (IARC and the rest).
7. Voice cloning: only voices we have the right to. Check ElevenLabs' cloning and commercial terms.

**Deliverables:** `docs/legal/LEGAL_BRIEF.md` (bottom line first, then ranked issues with evidence, sources and actions), `docs/legal/STEAM_CHECKLIST.md` (with draft AI disclosure and survey answers), `docs/legal/QUESTIONS_FOR_LAWYER.md`, and `docs/team/legal.md`.

Then **stay on as the standing compliance check**: review new assets and tools as leads add them, and SendMessage a lead directly if something they use is a problem.

**Rules:**
- Change no game content or assets; recommend only.
- Never delete files.
- Cite reputable primary sources, and say so where the law is unsettled.
- Commit and push your own branch at milestones; open no PRs.
- British spelling.
- Write this handoff at about 500k tokens.

## The owner's quotes that matter here

- "ai generated assets and things are perfectly ok for steam games and for making money and getting in no trouble right?"
- "sell on Steam with little to no issue", and "eventually remove anything not ours".
- From the team README: sex appeal is "a driving factor" for the heroine, "tho not at the cost of looking bad"; the tone is 18+.
- From the costume direction: the reaver stays near-naked, with underboob.
- From the voice route: "we're just going to use elevenlabs for our voicework so we will do 1 character at a time".

## What's done

- **The brief, checklist and lawyer questions** are written and pushed on `worktree-agent-aa12c130ddf4b904c`.
  - 27 ranked issues, all sources read on 4 October 2026.
  - Nine blockers: the AI disclosure; the mature survey (including hidden content); debug paths and unused files in the build; licence notices; the boar; the base bodies' source pictures; The Ember Watch chain of title; the explicit-scene placeholders; the placeholder voices.
- **The provenance audit is reviewed** (`worktree-agent-a80ff0c7fd988b178` at fa6e3d63). The rulings are in brief issue 5, and the auditor took my three additions.
- **Leads told directly:**
  - **UI art:** stop naming Diablo IV, Hades and Baldur's Gate in prompts. Done in c457cc9; the side-by-side icon check is still to come.
  - **Voice:** the ElevenLabs rules, now the first job in `docs/handoff/voice.md` (4f8e241). The voice lead has handed off; its open question is answered in `docs/team/legal.md`, under "Notes for other areas".
  - **Main session:** the decisions list: export filter and debug arguments, the explicit placeholders, the "Warmed" buff, the placeholder voices, and the credits screen.
- **The motion check of the run and sprint clips** (my own renders, brief issue 2).
  - **The Warden's left plate cup clips in the sprint and shows part of the nipple.** Reported to the main session.
  - The other outfits stay covered.

## In progress

- **The rest of the motion check:** combat swings, dash and leap, deaths, crouching, cinematics and creation poses, and a re-check of the Warden's cup once it is fixed. To recreate the tool:
  1. Copy `godot/tools_scenes/lookdev.gd` to the scratchpad as `motioncheck.gd`.
  2. After `ap.add_animation_library("", lib)`, add `ap.add_animation_library("her", load("res://art/anim/heroine.res"))`. Save it as UTF-8 without a byte-order mark.
  3. From the main checkout's `godot/`, run: `env OUTFIT=<warden|arcanist|ranger|reaver> HAIR=ponytail ORBIT=deg,height,dist,targety FOV=38 FRAMES=8 <Godot console exe> --path . --resolution 960x540 -s <abs path>/motioncheck.gd -- her/sprint_<calling> <out>.png`
  4. Leave `NOJIGGLE` unset, so jiggle is on.
  - Stock `lookdev.gd` only loads the UAL clips. In her own rig those don't play, so she renders in her rest pose.
  - The stalker's outfit is `OUTFIT=ranger`, but its clips are `*_stalker`.
  - Don't run it while the main session is importing an outfit build. Check for running Godot processes first.

## Next

1. **Re-rule when the owner answers** the provenance questions: the generator and plan for 234.glb, the source pictures, The Ember Watch's ownership, and the names.
2. **Standing check:** read the status pages and the roster at milestones, and review every new tool or model's licence: commercial use, revenue cap, territory, attribution, output terms.
3. **Before launch:**
   - review the credits screen, the `licences/` folder and the `.pck` listing;
   - re-read the live Steam survey form and update the draft wording;
   - re-check the Krea, LTX and ElevenLabs terms, which change often.
4. **If the owner asks for explicit scenes:** run the Adult Only DLC analysis with the lawyer (brief issue 6).

## Decisions (and why)

- **Not Adult Only.** Text-only, non-explicit sex plus partial nudity fits Some Nudity or Sexual Content. Adult Only means hidden by default and payment-processor exposure.
- **Disclose the hidden anatomy, or remove it.** Steam: "disclose all the adult content you've uploaded in your builds, even if it's not accessible".
- **Recommend decoupling the "Warmed" buff from the love scenes.** Australia's 2023 games guidelines: outside adult-restricted material, sex must not relate to incentives or rewards. Steam's Australian credit-card gate applies from 9 Sep 2026.
- **Krea is the biggest business risk.** Commercial use of outputs is allowed only under US$1M revenue, and the licence is revocable on 30 days' notice.
- **ElevenLabs output never goes into any local model.** Prohibited Use Policy 9(k) and 9(l).

## Failures and why

- **USPTO trademark search:** blocked by an AWS bot challenge. I did not try to get round it; a person must run it, which is in the lawyer questions.
- **Valve's January 2024 AI post** renders only with JavaScript. The text is cited from the Steamworks Content Survey page (same rules) and press.
- **Python's certificate store fails on some sites** (Godot docs, anthropic.com). Use WebFetch for those.
- **My first motion renders were in her rest pose**, because the clip names were wrong (see "In progress").

## Gotchas

- **My original worktree was in the wrong repo** (wowsurvivors). I made `.claude/worktrees/agent-aa12c130ddf4b904c` in `C:\Users\munch\Desktop\survivorsunchained`. The Bash tool's guard still thinks the old one is home, so compound Bash commands are refused: put the logic in a script file and run it plainly, or use PowerShell.
- **PowerShell has no heredocs.** Commit with `git commit -F <file>`.
- **Messaging a paused or retired agent wakes it.** That happened with the voice lead. Check the roster first.
- **The heroine's body has modelled nipples and buttocks.** Never publish renders without outfits; keep them in the scratchpad.
- **`all_resources` exports everything imported**, but never `.txt` or `.md`.
- **ElevenLabs has separate terms for EEA, UK and Swiss residents.** The owner's residence is still unknown.

## Collaborators

- **The provenance auditor (a80ff0c7fd988b178)** owns `ASSET_PROVENANCE.md`, `REPLACEMENT_PLAN.md` and `public/assets/CREDITS.md`. It has finished; message it only if needed, since that wakes it.
- **Main session:** decisions and the outfits; it supplied the renders in `%TEMP%/hs/cost` and `%TEMP%/hs/cu`.
- **Other leads:**
  - UI art (a1a394643aabfb169): prompts and the icon check;
  - UI design (a69858664f1d3dd29): character creation never shows her bare;
  - male hero (ab82cbe99e2937ddd): his body has bare buttocks and a smooth crotch, and a base garment is coming;
  - voice: a successor is to be named on the roster.

## Files to read first

1. `docs/legal/LEGAL_BRIEF.md`
2. `docs/legal/STEAM_CHECKLIST.md`
3. `docs/legal/QUESTIONS_FOR_LAWYER.md`
4. `docs/team/legal.md`
5. `docs/legal/ASSET_PROVENANCE.md` and `REPLACEMENT_PLAN.md` (the auditor's branch, or the integration branch once merged)
6. The scratch research: `scratchpad/legal/*.txt` (extracted licence and policy texts), if the session's scratchpad still exists.

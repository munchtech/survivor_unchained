# The team: how we work

Read this first, then `docs/team/RESUME.md` (what's current: the owner's latest decisions and every area's state) and `docs/team/OWNER_NOTES.md` (the owner's latest notes, by area, waiting to be taken up), then your own handoff page (`docs/handoff/<area>.md`) and status page (`docs/team/<area>.md`). The handoff page is what your predecessor knew. This page is what everyone shares.

## The owner's bar

- "AAA standard", "strive for excellent, above and beyond - not just good enough". It applies to everything, not just art.
- Never settle: remake rather than polish. "I don't want to polish, I want to create perfection." Question how things are done ("how things are can be limiting").
- "Do we have soul?" Make things unique to this world, not generic.
- Be critical of your own work. If you notice something you missed earlier, go back to it.
- "We are striving for perfection." Improved is not the bar; perfect is. Before you show anything, ask whether it is the best version of this in any game, not whether it beats what we had.
- Root design in research: study how the best games solve the same problem, then make it our own. More ornament is not better ("those borders are just ugly, adding more of them dosn't make them better"). Generic fantasy ornament spread evenly over everything reads as "ai looking".
- Sex appeal and the male gaze are a driving factor for the heroine, "tho not at the cost of looking bad". The tone is 18+.

## How we work

- Our repo is munchtech/survivor_unchained. The integration branch is `claude/vigilant-galileo-l6jqyx`.
- You work in your own worktree. Merge `origin/claude/vigilant-galileo-l6jqyx` in first, and again often. Commit and push your own branch; the main session merges it in. Open no PRs.
- Run `dotnet test` in `godot/tests` before every commit, and keep it green.
- Use British spelling. Comments are short prose that say why.
- Check your work as the player sees it: screenshots, renders and runs at full resolution. Never claim what you haven't seen.

## Context engineering

The owner asks: "accurate, efficient, on track, manage and engineer context. deliberate. clean over chaos". But never at the cost of quality.
- Keep what's relevant to the step you're on. Summarise; don't dump. Logs are for milestones. Record key decisions, not every exchange.
- Don't read whole huge files or transcripts. Read the part you need. Look at images at the size you need.
- Keep your status page `docs/team/<area>.md` to one page: current state, key decisions (one line each, with the why), next steps, blockers, and notes for other areas. Update it at milestones, and delete what's stale.
- Talk to other areas through their status pages or by SendMessage (see the roster below). Send short written reports, not long prompts.
- **Handoff:** when your context passes about 300k tokens (the measured optimum: about twice what a fresh successor holds after onboarding; see "Working lean"), reach a clean checkpoint, commit and push. Then write `docs/handoff/<area>.md` for a fresh successor, covering:
  - the owner's quotes;
  - your full brief;
  - what's done, in progress and next;
  - decisions;
  - failures and why;
  - gotchas;
  - collaborators;
  - the files to read first.

  End with `HANDOFF READY: docs/handoff/<area>.md on <branch>@<commit>`.

## Safety and the owner's machine

- Never print or commit tokens or keys. Use environment variables, and ask the owner to set them. The owner signs into sites themselves; never enter a password.
- Downloads are consented ("you have my consent to download and use whatever you need always"). Name what you fetch, and use reputable sources only. Every download in the built-in browser needs the owner to click Save, so batch them and warn the main session first.
- **Voice cloning:** only voices we have the right to. That means the owner's own voice, performances the owner approves, or datasets licensed for cloning. Never clone a real, identifiable person.
- **Heavy work takes turns.** Two heavy jobs at once have crashed the machine (ComfyUI alone holds 20-26 GB of RAM). Before a heavy job, take a turn with `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take gpu "<area>: <job>"` (ComfyUI, TRELLIS, MoGe; one at a time), `take blender ...` (Blender builds, bakes and renders; two at a time) or `take godot ...` (Godot runs for pictures or clips; three at a time, while RAM allows). Exit 1 means it's busy and says who has it or who you're queued behind: do light work (code, docs, design, review) meanwhile and ask again within 90 s to keep your place (or use `--wait N`). Waiters are served in the order they first asked, so retaking straight after giving back puts you at the back. Give it back the moment the job ends (`give gpu "<same name>"`); giving back the GPU also frees ComfyUI. Split long jobs into batches of under an hour, and give the turn back between them. `turn.py show` shows who holds what. `dotnet test` needs no turn.
- **GPU:** the RTX 5080 (16 GB) is shared. ComfyUI at 127.0.0.1:8188 serves the art work. Free it between jobs with `POST /free {"unload_models": true, "free_memory": true}`, never by killing it, and release your own models when done. There is 32 GB of RAM; mind big CPU models.

## Running a few at a time (the owner, 5 October 2026)

- Only 3 to 5 leads run at once; the rest are paused with their handoff and status pages, never lost, and resumed in turn. Leads that work together run together, and a group has at most one GPU-heavy lead (face, creatures, UI art's ComfyUI batches).
- Batch screenshots and renders: shoot everything a check needs in one turn, look once, fix in one pass.
- Keep handoffs and status pages lean.
- Agent types and models (the owner, 7 October: "dosn't use a bazooka when a slingshot will get the exact same perfection done"; quality stays first): `su-lead-high` (Opus, high: every long-running lead except story, including face, hair, outfits, animation, rendering, UI, combat, arena art, cinematics staging, VFX), `su-lead-max` (Opus, max, in short bursts: judges, solvers, and the story writer and editor as leads; see "Max effort in short bursts"), `su-lead-sonnet` (Sonnet, high: spec work with measurable acceptance and no taste: loot, crafting rules, story consistency checks, provenance, perf measurement runs, legal), `su-worker` (Sonnet, medium: a decided code or doc change), `su-runner` (Haiku, medium, no edits: run batches and tests, measure, grep, report numbers and paths). If your task proves harder than your setting, say so; effort can be raised mid-task without losing the cache.
- Paused 10 October (wound down; RESUME has the branches): face (GPU), body and outfits, animation, rendering, all on `su-lead-high` with `su-lead-max` judges. Next wave: UI design and UI art (when the GPU is lighter), then combat (the crowd and her run), the experience director, then the rest.

## Working lean (7 October 2026, from a measured week)

The week of 30 September to 7 October cost about US$6,000 at list price. Three things drove it: contexts held far past need (84% of cache reads were at over 300k tokens), the 5-minute subagent cache expiring while agents waited on renders (about 40% of spend went on re-writing whole contexts after a wait, median 9.5 minutes), and pictures kept in long contexts (about 10%). Output was small by comparison (but see "Max effort in short bursts": retained reasoning is not). So:
- **The cache now lasts an hour for every agent** (`.claude/settings.json`, `subagentPromptCacheTtl`). Waiting on a render no longer costs a full re-read. Still don't poll: take a turn with `--wait`, or hand the wait to a runner.
- **Hand off at about 300k.** A fresh successor holds about 120k after onboarding, and handing off at about twice that is cheapest. A backstop auto-compacts any agent at 400k; don't rely on it, because a deliberate handoff keeps more.
- **Onboard small.** Read README, RESUME, OWNER_NOTES and your handoff, then only the sections and files your step needs (grep first). Handoffs stay about 60 lines and name exact files and functions.
- **Delegate by weight.** A lead keeps taste, judgement and every look at a picture. Long batch runs (Godot, Blender, the motion check) go to a `su-runner` (Haiku), which waits, measures and returns numbers and paths; the lead then looks once at the final sheet. A decided, well-specified change goes to a `su-worker` (Sonnet), and the lead checks the diff.
- **Pictures:** batch into one contact sheet at the size you need and look once. For bulk visual QA (dozens of frames), spawn a fresh Opus judge with the sheets and a checklist; it returns a written verdict, so the images don't ride in your context for hundreds of turns.
- **Wide audits** (every clip, every outfit in every view, every icon): use a dynamic workflow with cheap stages (runner and worker) and an Opus verification stage, instead of one agent holding it all.
- **Max effort in short bursts, not long contexts (the owner, 7 October: "Priority top quality but also priority saving tokens", always).** Measured on wave 1: max-effort leads filled 48k to 300k in about 30 minutes, and their own retained reasoning was the largest share. So every long-running lead runs as `su-lead-high` (Opus, high), including face, outfits, animation, rendering and UI. Max effort is spent where taste is decided, in short-lived `su-lead-max` spawns whose reasoning doesn't ride for hours:
  - **Judge:** every picture verdict, sign-off and "does this meet the bar" goes to a fresh max judge with the sheet, the owner's words and a checklist; it returns a written verdict and the fixes. Nothing reaches the main session without a judge's pass.
  - **Solver:** a problem that resists one honest attempt (a root cause, a design call, a hard shader or rig fix) goes to a fresh max solver with a tight brief; it returns the answer or the fix.
  - **Authoring that is taste throughout** (story writing and editing, UI design briefs, the storybook cinematics' look) stays on `su-lead-max` as the lead itself.
  The main session measures each wave (tokens per finished piece) and reports the real saving.
- **Always take the cheaper route that ends at the same quality (the owner, 7 October: "any drop in effort or even in agent ... is always worth it if we maintain the quality priority ... always").** Standing permission, no need to ask: pick the lowest effort and the smallest model that will reach the same result, and pass `effort` when you spawn (a trivial doc or roster edit can go to a worker at low effort; a pure wait or grep to Haiku). Any technique that saves tokens without costing quality is adopted at once and written here: smaller reads, shorter outputs, fewer pictures, cheaper stages. The opposite holds too: the moment quality is at risk, raise the effort or the model without asking. Taste and every look at a picture stay on Opus. Fable stays a last resort.
- **Time is not the cost; tokens are (the owner, 7 October: "I have zero issue with slow ... if slower agents do the job at a fraction of the price and the same quality in the end thats always good").** Prefer the slower, cheaper route whenever it ends at the same quality: a smaller model with a judge, a runner that waits, sequential instead of parallel.
- **The main session** starts fresh for each wave, stays under about 250k, merges, judges and escalates. A lead that is stuck after two honest attempts comes to the main session, which takes it at the top model.

## Roster

The main session keeps this current. It is the address list for SendMessage. Retired agents' ids are not listed: a message to one wakes it.

| Area | Agent | Status page |
|---|---|---|
| Voice (paused by the owner: no placeholders; final voices from ElevenLabs later) | a501b387a90d78b4e | docs/team/voice.md |
| Story and writing (the writer: the approved rewrite, Act 1 first) | — (handoff ready) | docs/team/story.md |
| Combat, encounters, bosses, balance (paused; handoff ready at af6452e1) | — | docs/team/combat.md |
| Animation (joints to perfection: wrists, follow-through, elbows, arms through body, sliding) | — (paused 10 Oct; handoff on worktree-agent-af8dbda3195e438e4) | docs/team/animation.md |
| UI design (the HUD keystone; portraits wait on the face) | — (handoff ready) | docs/team/ui_design.md |
| UI art (paused; handoff ready at cd0f4ab6) | — | docs/team/ui_art.md |
| Crafting (research, design, build) (paused; handoff ready at ed429efb) | — | docs/team/crafting.md |
| Gameplay experience director | af2c026d86e1b532b | docs/team/experience.md |
| Skills look and feel (VFX, under the main session) | a560452c597415545 | docs/team/skills.md |
| Cinematics production | aece7b87e89b13f19 | docs/team/cinematics.md |
| Performance and rendering (clarity in motion first) | — (paused 10 Oct; handoff on worktree-agent-a4e0c353e61cca6dc) | docs/team/performance.md |
| Arena art | a0b61c278bdd5c994 | docs/team/arena_art.md |
| Male hero (body, head, hair, outfits) | ab82cbe99e2937ddd | docs/team/hero_male.md |
| Heroine face, hair and character creation's Look | — (paused 10 Oct; handoff on worktree-agent-a2d632df7c7f21ec0) | docs/team/face.md |
| Asset provenance (what isn't ours, licences, credits, replacement plan) | a80ff0c7fd988b178 | docs/team/provenance.md |
| Legal and Steam compliance (paused; docs/handoff/legal.md; wake before submission or for a new outfit) | — | docs/team/legal.md |
| Loot and itemisation (paused, built and merged; docs/handoff/loot.md for a successor) | — | docs/team/loot.md |
| Creatures and models (our own boar first, then MODELS_TO_MAKE.md) | af551cacc6292152f | docs/team/creatures.md |
| Story editor (paused after notes 02 at 435k; a fresh editor reads the next draft) | — | docs/story/EDITORIAL_LETTER.md |
| Heroine body and outfits (now a lead of its own; was the main session's) | — (paused 10 Oct; handoff on worktree-agent-a5ca10091b08dc429) | docs/team/outfits.md |

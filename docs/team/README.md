# The team: how we work

Read this first, then your own handoff page (`docs/handoff/<area>.md`) and status page (`docs/team/<area>.md`). The handoff page is what your predecessor knew. This page is what everyone shares.

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
- **Handoff:** when your context passes about 500k tokens, reach a clean checkpoint, commit and push. Then write `docs/handoff/<area>.md` for a fresh successor, covering:
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
- **Heavy work takes turns.** Two heavy jobs at once have crashed the machine (ComfyUI alone holds 20-26 GB of RAM). Before a heavy job, take a turn with `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take gpu "<area>: <job>"` (ComfyUI, TRELLIS, MoGe, big Blender bakes or renders; one at a time) or `take godot ...` (Godot runs for pictures or clips; three at a time, while RAM allows). Exit 1 means it's busy and says who has it or who you're queued behind: do light work (code, docs, design, review) meanwhile and ask again within 90 s to keep your place (or use `--wait N`). Waiters are served in the order they first asked, so retaking straight after giving back puts you at the back. Give it back the moment the job ends (`give gpu "<same name>"`); giving back the GPU also frees ComfyUI. Split long jobs into batches of under an hour, and give the turn back between them. `turn.py show` shows who holds what. `dotnet test` needs no turn.
- **GPU:** the RTX 5080 (16 GB) is shared. ComfyUI at 127.0.0.1:8188 serves the art work. Free it between jobs with `POST /free {"unload_models": true, "free_memory": true}`, never by killing it, and release your own models when done. There is 32 GB of RAM; mind big CPU models.

## Roster

The main session keeps this current. It is the address list for SendMessage. Retired agents' ids are not listed: a message to one wakes it.

| Area | Agent | Status page |
|---|---|---|
| Voice (paused by the owner: no placeholders; final voices from ElevenLabs later) | a501b387a90d78b4e | docs/team/voice.md |
| Story and writing | a7ba8903f4c8261b1 | docs/team/story.md |
| Combat, encounters, bosses, balance | a5115633c7006e4d4 | docs/team/combat.md |
| Animation | a7dd95d00c4a6a017 | docs/team/animation.md |
| UI design (layouts, screens, the filter) | a4fdbc49786ba8b7f | docs/team/ui_design.md |
| UI art | a0bff3ffe4d3ad748 | docs/team/ui_art.md |
| Crafting (research, design, build) | ab0b263c720bdbda8 | docs/team/crafting.md |
| Gameplay experience director | a9f0d6c64d891d56d | docs/team/experience.md |
| Skills look and feel (VFX, under the main session) | abc6bbe020c7fe287 | docs/team/skills.md |
| Cinematics production | a7a4c20bcfd7ccfd3 | docs/team/cinematics.md |
| Performance | a0eb8c612c94d4aa5 | docs/team/performance.md |
| Arena art | aba487928a1515c93 | docs/team/arena_art.md |
| Male hero (body, head, hair, outfits) | ab82cbe99e2937ddd | docs/team/hero_male.md |
| Heroine face, hair and character creation's Look | a833b7942e978d994 | docs/team/face.md |
| Asset provenance (what isn't ours, licences, credits, replacement plan) | a80ff0c7fd988b178 | docs/team/provenance.md |
| Legal and Steam compliance (AI disclosure, mature content, licences, brief for a lawyer) | af0973d59a5b2817a | docs/team/legal.md |
| Loot and itemisation (paused, built and merged; docs/handoff/loot.md for a successor) | — | docs/team/loot.md |
| Creatures and models (our own boar first, then MODELS_TO_MAKE.md) | af551cacc6292152f | docs/team/creatures.md |
| Heroine outfits | main session | — |

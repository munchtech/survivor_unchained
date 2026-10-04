# The team: how we work

Read this first, then your own handoff page (`docs/handoff/<area>.md`) and status page (`docs/team/<area>.md`). The handoff page is what your predecessor knew. This page is what everyone shares.

## The owner's bar

- "AAA standard", "strive for excellent, above and beyond - not just good enough". It applies to everything, not just art.
- Never settle: remake rather than polish. "I don't want to polish, I want to create perfection." Question how things are done ("how things are can be limiting").
- "Do we have soul?" Make things unique to this world, not generic.
- Be critical of your own work. If you notice something you missed earlier, go back to it.
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
- **GPU:** the RTX 5080 (16 GB) is shared. ComfyUI at 127.0.0.1:8188 serves the art work. Free it between jobs with `POST /free {"unload_models": true, "free_memory": true}`, never by killing it, and release your own models when done. There is 32 GB of RAM; mind big CPU models.

## Roster

The main session keeps this current. It is the address list for SendMessage. Retired agents' ids are not listed: a message to one wakes it.

| Area | Agent | Status page |
|---|---|---|
| Voice (ElevenLabs packets, placeholders) | a501b387a90d78b4e | docs/team/voice.md |
| Story and writing | a7622ae77d19e31dc | docs/team/story.md |
| Combat, bosses, balance | a09c5a65f5a84319e | docs/team/combat.md |
| Animation | aa4f5fc266b043035 | docs/team/animation.md |
| UI design (character creation first) | ac76f400913a109cd | docs/team/ui_design.md |
| UI art | a72467cac33063d3a | docs/team/ui_art.md |
| Crafting (research, design, build) | a7862117a0240deb5 | docs/team/crafting.md |
| Gameplay experience director | a33f58e68e89e3ccf | docs/team/experience.md |
| Skills look and feel (VFX, under the main session) | a8bafe3cd8a229639 | docs/team/skills.md |
| Cinematics production | a2dfc75e2d351105a | docs/team/cinematics.md |
| Performance | a9586a5171413db0b | docs/team/performance.md |
| Heroine outfits | main session | — |

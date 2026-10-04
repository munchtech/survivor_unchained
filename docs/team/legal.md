# Legal and Steam compliance: status

Agent aa12c130ddf4b904c, branch `worktree-agent-aa12c130ddf4b904c` (worktree `.claude/worktrees/agent-aa12c130ddf4b904c` in survivorsunchained). Not a lawyer: I find and organise the issues, cite primary sources, and recommend. The owner and the main session decide.

## State (4 October 2026)

- **Delivered:**
  - `docs/legal/LEGAL_BRIEF.md`: the bottom line for the owner, then 27 ranked issues with evidence, sources and actions.
  - `docs/legal/STEAM_CHECKLIST.md`: the submission steps, draft survey answers, the AI disclosure and the credits line.
  - `docs/legal/QUESTIONS_FOR_LAWYER.md`: 14 questions.
- **Blockers before launch** (brief issues 1 to 6 and 11):
  - the honest AI and mature-content surveys;
  - debug paths and unused files out of the release build;
  - licence notices and credits shipped;
  - the boar;
  - the base bodies' source pictures;
  - explicit-scene placeholders out of release data;
  - placeholder voices replaced or dropped.
- **Biggest business risk:** the Krea 2 licence allows commercial use of outputs only under US$1M company revenue, and is revocable on 30 days' notice.
- **Not yet verified by me:** whether any nipple, areola or crotch shows in motion with jiggle on. I asked for a motion check in the checklist. Also open: the provenance auditor's final `ASSET_PROVENANCE.md`; its early findings are ruled on in brief issue 5.

## Key decisions (with why)

- **Survey answers:** General Mature, Frequent Violence or Gore, and Some Nudity or Sexual Content, but not Adult Only. Partial nudity plus non-explicit, text-only sex fits there. Explicit sex would move the game to hidden-by-default and payment-processor risk.
- **The hidden anatomy and the hero's debug body are disclosed or removed.** Steam requires disclosure of all adult content uploaded, even if unreachable.
- **Pre-generated AI is disclosed for art, effects, sound, motion, meshes, writing and voices; live generation is "no".** The game makes no AI or network calls.
- **Decoupling the "Warmed" buff from the love scenes is recommended.** In Australia, sex linked to rewards means R18+, and Steam's Australian credit-card gate applies from 9 Sep 2026.

## Next

1. Review `ASSET_PROVENANCE.md` when it lands (`worktree-agent-a80ff0c7fd988b178`), and rule on every row in the brief.
2. Standing check: review new tools and assets as leads add them. Read status pages at milestones.
3. When the main session has time: render a motion and jiggle check of each outfit, or ask for one.
4. Before launch: review the credits screen, the `licences/` folder and the `.pck` listing.

## Blockers on me

- The owner's answers on residence and business structure, and on the base bodies' generator and source pictures (`234.glb`, `woman.glb`, `ComfyUI_00008.glb`, `images/1.webp`).
- The USPTO search is behind a bot challenge, so a person must run the trademark search.

## Notes for other areas

- **Voice (successor):** ElevenLabs rules are in `docs/handoff/voice.md`.
  - Answer to the open question: running Whisper, UTMOS or a speaker embedding on the owner's ElevenLabs takes is a **grey area** under Prohibited Use Policy 9(k), "input for any machine learning". QA-only inference that trains nothing and keeps nothing is low risk, but the literal words reach it.
  - Until the lawyer or ElevenLabs confirms in writing:
    - keep the check opt-in;
    - never store speaker embeddings of ElevenLabs takes;
    - prefer the owner listening, or a word check on the subtitle text alone.
  - Use Voice Design voices for the narrator and the love interests.
- **UI art:** style-named prompts are fixed (c457cc9). The side-by-side icon check against Diablo IV and Hades is still to do before launch.
- **Main session:** decisions needed on:
  - the release export filter and gating debug arguments (brief issue 3);
  - stripping the explicit placeholders (issue 6);
  - the "Warmed" buff (issue 7);
  - the placeholder voices (issue 11);
  - the credits and licences screen (issue 4).
- **Hero lead:** good that a base garment is coming. Until then, `--body hero` must not reach a release build.
- **Anyone adding a tool or model:** tell me its licence link. I'll check commercial use, revenue limits, territory, attribution and output terms.

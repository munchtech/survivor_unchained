# Legal and Steam compliance: status

Agent aab20546fe06daa89 (successor to aa12c130ddf4b904c), branch `worktree-agent-aab20546fe06daa89` (worktree `.claude/worktrees/agent-aab20546fe06daa89` in survivorsunchained). Not a lawyer: I find and organise the issues, cite primary sources, and recommend. The owner and the main session decide. Predecessor's handoff: `docs/handoff/legal.md`.

## State (4 October 2026, paused at the coordinator's request)

- **Delivered (predecessor):** `docs/legal/LEGAL_BRIEF.md` (27 ranked issues), `STEAM_CHECKLIST.md`, `QUESTIONS_FOR_LAWYER.md`. The provenance audit has been reviewed and its rulings are in brief issue 5.
- **Merged:** `origin/claude/vigilant-galileo-l6jqyx` and `worktree-agent-aa12c130ddf4b904c` (5c74633d).
- **Launch blockers, as tracked:**
  - **Debug paths and export filter (performance lead a7145e18b3eb78294):** spec sent on 4 Oct. It covers:
    - `Args.All()` in `Shots.cs` returning nothing when `!OS.IsDebugBuild()`;
    - `exclude_filter` additions in all three presets: `tools_scenes/*`, the anime and woman bodies, `her_Hair_*`, `hero.glb` until his garment exists, the unused KayKit, web and Poly Haven files, and `art/vo/*`;
    - a zip-pack listing for me to review;
    - an optional guard test.

    No reply yet.
  - **Licences screen and folder (UI design):** the lead a69858664f1d3dd29 has handed off, and the job is first in its handoff. The successor is not yet on the roster. The sources are verified for the spec (below), which is to be written into brief issue 4.
  - **The boar; the base bodies' source; The Ember Watch:** waiting for the owner's answers (the main session asked).
  - **Placeholder voices:** all 19 takes in `godot/data/vo/index.json` are `placeholder`. They are covered by the `art/vo/*` exclusion above; the main session to confirm. `VoiceOver.cs:89` already tolerates a missing file.
- **Code checks (4 Oct):**
  - `--bare` hides the world, not her outfit.
  - The environment variables (`HAIRDEBUG`, `FX_LAYERS`, `CAMPFIRE_PARTS`, `FLORA_COUNT`) are effects only.
  - Every developer argument goes through `Args` in `Shots.cs`, so one gate covers them all.
- **Motion check:** not yet run this session, because the main checkout was importing outfits at 15:52. The predecessor's `motion.sh`, `motioncheck.gd` and `sheet.py` are intact in `scratchpad/legal/`. Clip names found in `heroine.res`:
  - `dash`, `leap`, `death`, `death_back`, `hit`;
  - `cast_bolt`, `cast_flick`, `cast_raise`;
  - `crossbow_shoot`, `throw`;
  - `sit_log`, `sit_back_heels`;
  - `idle_*_break`.

  The swing clip names (axe, daggers and sword families in `tools/anim/clips`) are still to be listed from Godot itself.

## Licences spec: verified sources (for brief issue 4)

- Godot 4.5.1:
  - `LICENSE.txt` and `COPYRIGHT.txt` at the `4.5.1-stable` tag. Both are live and return HTTP 200.
  - In game, `Engine.GetLicenseText()`, `GetLicenseInfo()` and `GetCopyrightInfo()` return the same notices, so the screen can't drift.
  - Godot's compliance page accepts a credits screen, a licences menu or an accompanying file.
- .NET 8:
  - Godot "bundles the parts of .NET needed to run already-compiled games" (C# basics page), so the runtime's notices apply.
  - Use `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT` from `dotnet/runtime` `release/8.0`, or better, from the runtime pack the first export restores.
- The OFL texts are in `godot/art/fonts`.
- The CC BY entries in `public/assets/CREDITS.md` meet §3(a): creator, title, link, licence and changes.
- **The player-facing text must drop the internal notes:** "under review", repo paths, and the tool line formats.

## Next (exact)

1. **Motion check, once the main checkout's import is idle.** Check that no `--import` process is writing to `godot/.godot/imported`.
   - List her clips from Godot: a three-line GDScript loading `res://art/anim/heroine.res`.
   - Run `motion.sh` with the clip loop changed to:
     - swings;
     - `dash` and `leap`;
     - `death` and `death_back`;
     - `hit`;
     - the casts, `throw` and `crossbow_shoot`;
     - the sits and the breaks;
     - all four outfits with jiggle on.
   - Then the cinematic poses (cinematics lead a3058a45eee41d695, `--cine`) and the creation poses.
   - Re-check the Warden's left cup when the main session says the fix has landed.
2. Write the licences spec into brief issue 4. Send it to the UI design successor once the roster names one.
3. Review the performance lead's pack listing when it comes.
4. Re-rule on the owner's provenance answers.
5. Standing check of new tools and assets. Recent ones to look at:
   - the skills lead's "filmed clips";
   - arena art's Hollow and Dig concepts;
   - the cinematics gestures.

## Key decisions (with why)

- **Survey:** General Mature, Frequent Violence or Gore, and Some Nudity or Sexual Content; not Adult Only. Text-only, non-explicit sex plus partial nudity fits there.
- **Hidden anatomy:** disclosed, and debug bodies removed from the build. Steam: disclose "all the adult content you've uploaded … even if it's not accessible".
- **Placeholder voices:** excluded at export rather than deleted. The owner wants none, and no files are deleted.
- **"Warmed" buff:** decoupling it from the love scenes is recommended. In Australia, sex tied to rewards means R18+, and the credit-card gate has applied since 9 Sep 2026.
- **Krea 2:** commercial use of outputs only under US$1M revenue, and the licence is revocable on 30 days' notice. It is the biggest business risk.

## Blockers on me

- The owner's answers on the bodies' sources, The Ember Watch, the boar (buy or replace), and his residence and business structure.
- A person must run the USPTO search (it sits behind a bot challenge).

## Notes for other areas

- **Performance (a7145e18b3eb78294):** the export spec is in your messages. Send me the zip-pack listing.
- **UI design successor:** the licences screen is first in `docs/handoff/ui_design.md`. Use `Engine.GetLicenseText()` and `GetCopyrightInfo()` for Godot's part. I'll check the wording.
- **Voice (successor):** the ElevenLabs rules are in `docs/handoff/voice.md`. Whisper, UTMOS and speaker embeddings on ElevenLabs takes are a grey area under Prohibited Use Policy 9(k). Keep them opt-in, and never store the embeddings.
- **UI art:** the side-by-side icon check against Diablo IV and Hades is still due before launch.
- **Anyone adding a tool or model:** send me its licence link.

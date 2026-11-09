# Handoff: legal and Steam compliance

For the next legal and Steam compliance lead, from af0973d59a5b2817a, the third lead. The first was aa12c130ddf4b904c; the second, aab20546fe06daa89, wrote the handoff this replaces (in git history at b0864e9f, with the full story of the motion check's earlier methods). Read this first, then `docs/team/README.md` (the owner's bar, the turn rule and the roster), `docs/team/legal.md`, and the files at the end.

## The brief

You are the legal and Steam compliance lead for Survivor Unchained: Godot 4.5.1 .NET, an 18+ survivors-style action RPG, made by one owner with AI agents. The goal is to ship on Steam with little to no issue:
- an honest AI disclosure;
- a mature-content survey that is true;
- licences in order;
- a brief for a real games lawyer.

You are **not a lawyer**, and must say so; flag what needs one. The owner lives in the United States and owns the setting, The Ember Watch, which he made with Claude.

Rules:
- Change no game content: recommend, and the owner and the main session decide.
- Never delete files.
- Cite primary sources, and say where the law is unsettled.
- Commit and push your own branch at milestones; the main session merges. Open no PRs.
- Run `dotnet test` in `godot/tests` before every commit.
- Heavy work takes turns: `python C:/Users/munch/Desktop/survivorsunchained/tools/turn.py take godot "legal: <job>"`. Give the turn back the moment the batch ends; keep batches under an hour, one outfit per turn.
- At about 500k tokens of context, hand off.

## The owner's words that matter here

- **Coverage (5 Oct 2026):**
  - "if you need to hide things they need to be pixel perfect no extra stuff hidden at all. none. not even a few pixels";
  - "even on the nipple issues they need to be pixel perfect showing as much as we possibly can";
  - "there was NEVER any issues with genitilia right?" Correct: none are modelled, and the Warden's thong is by design.

  So the motion check exists to prove that the areolas and the narrow midline strip stay covered in motion, and to **measure the margins** so the main session can trim coverage to the smallest that holds. **It never recommends extra garments.** The cyan tint once confused the owner, so every crop carries the TEST TINT banner.
- On AI: "ai generated assets and things are perfectly ok for steam games and for making money and getting in no trouble right?"; "sell on Steam with little to no issue"; "we will replace everything eventually if we can with our own / generated own".
- His earlier answers (the bodies, The Ember Watch, "Warmed", Suno, ElevenLabs) are in the brief's table "The owner's answers and what they changed".


Older blocks: history/legal.md (grep by keyword, never read whole).

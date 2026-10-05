# Survivor Unchained: legal and Steam compliance brief

Prepared by the legal and Steam compliance lead (an AI agent, aa12c130ddf4b904c) on 4 October 2026, for the owner and for the games lawyer who reviews it before launch. Updated the same evening by its successor (aab20546fe06daa89) after the owner's answers: see "The owner's answers and what they changed", below the bottom line.

**This is not legal advice. I am not a lawyer.** It organises the issues, cites the primary sources and the dates I read them, and proposes actions. Where the law is unsettled I say so. A qualified games lawyer should confirm everything marked for them in `QUESTIONS_FOR_LAWYER.md` before launch.

Companion files:
- `STEAM_CHECKLIST.md`: the submission steps, with draft survey answers and disclosure wording.
- `QUESTIONS_FOR_LAWYER.md`: the short list for counsel.
- `ASSET_PROVENANCE.md` and `REPLACEMENT_PLAN.md`: the provenance auditor's inventory (102 rows) and replacement order, on branch `worktree-agent-a80ff0c7fd988b178` at fa6e3d63. My rulings on its findings are in issue 5. I agree with the plan's order: stage 0 (answers and compliance) and stage 1 (the boar, the bodies, the face paint) come before launch.

---

## The bottom line, for the owner

You asked: *"ai generated assets and things are perfectly ok for steam games and for making money and getting in no trouble right?"*

**Mostly yes, but not automatically, and not "no trouble" without some work.**

1. **Steam allows AI-made games.** Valve reviews AI output the same way as anything else: it must not be illegal or infringing, and it must match your marketing. You must **disclose** the AI use in the content survey, and Valve shows the disclosure on the store page. Nothing in this game generates AI content while it runs. That is the easy case.
2. **You can make money with it, within each tool's licence.** Every tool we use allows commercial use of what it makes, with one catch that matters a great deal:
   - **Krea 2** painted much of the game's art. Its licence allows commercial use **only while your total annual revenue is under US$1 million**. Krea can also end the licence on 30 days' notice.
   - A successful launch could cross that line. Plan now: budget for Krea's enterprise licence, or replace Krea-made art over time. Replacing it fits your goal of removing whatever isn't ours.
   - LTX (effects and sounds) has a US$10 million line. The rest have no revenue limits.
3. **You may not own copyright in purely AI-made material.** The US Copyright Office says prompts alone don't make you an author. On 2 March 2026 the US Supreme Court declined to hear the leading challenge, so that position stands. The UK government plans to drop its special protection for computer-generated works.
   - So a competitor could, in principle, copy an individual AI-made icon or texture.
   - What you can protect: the game as a whole (your selection and arrangement), anything you personally made or changed, and your name and logo, by trademark.
   - Section 16 says how to strengthen this.
4. **"No trouble" depends on a few fixes before launch.** After your answers, six items still block launch:
   - the AI disclosure, filled in honestly;
   - the mature-content answers, which must cover what's hidden in the build as well as what's shown;
   - debug paths and unused files (including the hero's bare body) that ship in the build;
   - licence notices that don't ship yet;
   - the boar, which has conflicting licence terms: replace it, or buy the commercial version, before launch;
   - the placeholder voices, which must be replaced or dropped from the build.

   Three former blockers are cleared:
   - **The Ember Watch is yours.** Issue 5(e) explains what that means and what to keep.
   - **The explicit-scene placeholders are out** of the data.
   - **The base bodies can stay.** You made the pictures with Krea 2 Turbo and the 3D with TRELLIS 2, both on our own machine. Sign the short record in `records/BODIES_RECORD.md`, and confirm that no real person or anyone else's art went into the pictures (issue 5(b)).
5. **The mature content is sellable on Steam as it stands.** It counts as *Some Nudity or Sexual Content*, *Frequent Violence or Gore* and *General Mature Content*, not *Adult Only*.
   - **Explicit sex scenes** would move the game into Adult Only. That means hidden by default, a slower review, and exposure to the payment-card rules Valve added in July 2025.
   - **"Warmed" is now only a note that the night happened** (your decision; the story lead's change). Sex that granted a combat buff would have forced an R18+ rating in Australia. Without it, the game can be judged against MA 15+ instead (issue 7).
6. **Voices and music:**
   - ElevenLabs is fine for commercial use on a paid plan. Use only voices we have the right to: designed voices, your own voice, or performers who have consented in writing. Never feed ElevenLabs output into another AI model; its terms forbid it.
   - **Suno** (the hymn) is fine on a **Pro or Premier** plan, for a song you **download** through Suno's own download button. Suno assigns those songs to you. Free-plan songs are for personal, non-commercial use only (issue 28).

**In one line:** ship it with an honest disclosure, fix the six blockers (the boar is the biggest job), and plan for the Krea revenue cap, which now covers the bodies' pictures as well as the interface. Then the AI use itself is not what gets you into trouble.

---

## The owner's answers and what they changed (4 October 2026)

| The owner said | Ruling now | Issue |
|---|---|---|
| He lives in the **United States** | US law governs his own position: copyright, registration and his contracts. ElevenLabs' non-EEA terms apply to him. Steam needs his US tax form (W-9). Selling into the EU, UK and Australia still brings their content rules | 12, 16, 27 |
| **"Warmed"** should only say it happened | **Resolved** once merged. The story lead's change (`worktree-agent-a73ca9d35d0c487a9`@b47d98ea) removes the bonus, keeps the note, and adds a test. Australia's "sex related to rewards" trigger is gone | 7 |
| The base bodies: **"we made images in krea 2 turbo… we used trellis for the 3d… we made it in comfyui"** (a correction of his first answer, "krea assets") | **Kept, with conditions; no longer a blocker.**<br>- The picture came from Krea 2 Turbo on our own machine, under the same licence as the UI art: the US$1M cap and 30-day termination.<br>- The mesh came from TRELLIS 2 (MIT), also local.<br>- The machine's logs agree. The hero's picture most likely used a Civitai LoRA whose creator allows selling images.<br>- Conditions: no real person and no one else's art in the pictures, and a signed record. See `records/BODIES_RECORD.md` | 5(b) |
| **"I do not own [The Ember Watch]… I guess I own it?"** | **Yes: as far as anyone does, you own it.** There is no third party to clear. Copyright needs no registration to exist, but it protects only human-authored expression. Keep the records listed in 5(e). **Cleared as a blocker** | 5(e), 16 |
| **Replace everything** third-party with our own over time | Agreed. Only the boar must go before launch; credited CC0 and CC BY work can stay until replaced. "Generated own" replacements carry their generator's terms, so 5(g) sets rules | 5(a), 5(g) |
| **Export templates:** do what's needed | Noted. The release export (issue 3) can be built and its `.pck` listed when the GPU is free | 3 |
| **The hymn** will be made in **Suno** | Fine on a paid plan, downloaded through Suno. Disclose it as AI music | 28, 1 |

---

## What the game actually contains (facts the rulings rest on)

I checked these in the repository at `f56ee42` (integration branch) and in renders the main session supplied (dated 3 to 4 October 2026, 1920×1080 close-ups and 1000 px sheets in `%TEMP%/hs/cost` and `%TEMP%/hs/cu`).

- **Engine:** Godot 4.5.1 .NET (C#, .NET 8), Jolt physics. Windows, Linux and macOS export presets. Export filter `all_resources` (every imported resource ships, used or not).
- **No live AI generation.** The game makes no network calls and no AI calls at runtime. It writes only local files: `user://settings.json`, `user://bindings.json`, `user://saves`, and caches. No telemetry, analytics or Steamworks integration exists yet.
- **AI-made content that ships** (the provenance auditor's count, which I have spot-checked):
  - Krea 2 art: the painted UI (frames, cards, logo), 117 colour icons, 48 item icons, ground marks, and the heroine's and hero's face paint and irises;
  - LTX-2.5: 15 effect flipbooks and 5 sound takes;
  - the heroes' AI base meshes. Each is a picture made locally with Krea 2 Turbo, turned into 3D locally by TRELLIS 2, then rigged and rebuilt by agents (issue 5(b));
  - Kimodo: 10 folk motion clips;
  - 19 Maya1 and Seed-VC placeholder voice files in `godot/art/vo`;
  - story, dialogue and item text written by Claude agents under the owner's direction.
- **The heroine:**
  - Her body has modelled nipples and buttocks; skin is hidden only under outfit pieces (main session).
  - Jiggle physics on breasts and glutes runs in normal play (`HerJiggle`).
  - In the renders I saw:
    - Reaver: a single leather band covers the nipples, leaving heavy underboob; a low belt and loincloth flap.
    - Stalker: a leather corset with the nipples showing as a soft rise through it; the right buttock is bare in a thong cut, and a high cut runs over the right hip.
    - Warden: the plate skirt leaves the lower buttocks bare.
  - **My motion check** (issue 2): in the sprint, the Warden's left plate cup clips and shows part of the nipple. The other outfits stayed covered in the run and sprint clips. Her crotch is covered in all four outfits; whether it is modelled is still unconfirmed.
- **Character creation:** it never shows her or him without the calling's full outfit, has no base layer, and no shipped toggle for one (UI design lead, 4 Oct). A dev portrait tool once built her bare by mistake; it is fixed, and the images were re-rendered dressed.
- **The male hero:** a bare body with a smooth crotch and bare buttocks. He is reachable only through the debug argument `--body hero`, which is **not** gated to debug builds (`godot/src/Actors/People.cs:103`). A base garment is being added (hero lead, 4 Oct).
- **Sexual content in text** (`godot/data/content/dialogue.json`):
  - Romances with adult characters (ages stated in the text).
  - Love scenes are written as non-graphic "cut-aways" that end before the act.
  - Sella is a sex worker: the player pays 15 gold for a night (`sella.price`, `sella.rest_night`).
  - **The love scenes used to grant a combat buff:** `sella.night`, `sella.free_night` and `maeca.blind` applied `warmed`, "+8% damage, +5% speed, one day".
    - The owner removed the bonus. The story lead's b47d98ea (not yet merged) keeps `warmed` only as a note: "Warmed: last night is still with you".
    - A test (`QuestTests`) checks that damage, speed, health, armour, critical hits and regeneration are the same with it or without it.
    - The scenes still raise affection and trust, which is the relationship itself (issue 7).
  - Three placeholder lines reading "[explicit scene: … — to be written]" sat behind `settings.intimacy == "full"`. Nothing set that fact, so they were unreachable, but they shipped in the data. The story lead removed them (efc15256, now merged), and `StoryLint` keeps them out (issue 6).
- **Music (planned):** the hymn at Nell's grave is to be made by the owner in Suno (issue 28). The rest of the music is synthesised in code.
- **Violence:** constant horde combat against humans, undead and beasts. Blood, pools and gibs ("a blow far bigger than what it killed bursts the body"), and corpses that lie for 18 seconds. There is a gore setting (full, reduced, off).
- **Language:** infrequent strong language (one "fucking"; some "shit", "piss", "bitch", "bastard").
- **No drugs, gambling, loot boxes or sexual violence**, and no minors in sexual contexts. I searched the content data for each.

---

## Issue list

**Ranks:**
- **BLOCKER:** fix or answer before launch.
- **SHOULD FIX:** a real risk; fix before launch if possible.
- **FINE:** compliant; keep doing it.

"Lawyer" marks a point to confirm with counsel. All sources were read on 4 October 2026 unless stated.

| # | Issue | Rank |
|---|---|---|
| 1 | Steam AI disclosure (pre-generated; no live) | BLOCKER |
| 2 | Steam mature content survey, including content hidden in the build | BLOCKER |
| 3 | Debug paths and unused files in the release build | BLOCKER |
| 4 | Licence notices and credits missing from the build | BLOCKER |
| 5 | Third-party assets: the boar; the base bodies (local Krea 2 Turbo and TRELLIS 2); The Ember Watch | BLOCKER (boar); FINE with conditions (bodies); FINE (Ember Watch, with records) |
| 6 | Explicit-scene placeholders in shipped data; the explicit-content decision | DONE (removed, efc15256) / decision |
| 7 | Sex tied to a gameplay buff (Australia R18+, credit-card gate) | RESOLVED once b47d98ea merges |
| 8 | Krea 2 licence: US$1M revenue cap, revocable on notice | SHOULD FIX now; BLOCKER before revenue nears $1M |
| 9 | LTX-2.x licence conditions | FINE, with two duties |
| 10 | Other AI models (TRELLIS 2, Pixal3D, Kimodo and the rest) | FINE |
| 11 | Placeholder voices (Maya1, Seed-VC, VoxCPM2) | BLOCKER if shipped; FINE if replaced |
| 12 | ElevenLabs terms (finals) | SHOULD FIX (process) |
| 13 | Voice cloning and digital-replica law | FINE as practised; get written consents |
| 14 | Prompts that name other games (Diablo IV, Hades, Baldur's Gate) | SHOULD FIX |
| 15 | Warcraft-derived skill names; derivative Sketchfab models | SHOULD FIX |
| 16 | Copyright in AI-made work: what we own, what others may copy | SHOULD FIX (strategy) |
| 17 | The name "Survivor Unchained" | SHOULD FIX (clearance search) |
| 18 | Fonts | FINE (ship the OFL texts: #4) |
| 19 | Godot, .NET and engine notices | Part of #4 |
| 20 | Privacy | FINE (nothing collected) |
| 21 | EULA and refunds | FINE |
| 22 | Age ratings: Germany, Indonesia, Australia, UK, IARC | SHOULD FIX (Australia), else FINE |
| 23 | Store assets: capsules PG-13, screenshots | SHOULD FIX (process) |
| 24 | EU AI Act Article 50 and similar labelling duties | FINE, with a credits line |
| 25 | Payment-processor content rule (July 2025) | FINE while non-explicit |
| 26 | Claude-written text and code (Anthropic terms) | FINE |
| 27 | Business set-up: entity, residence (United States), governing terms | SHOULD FIX (lawyer) |
| 28 | Suno for the hymn | FINE on a Pro or Premier plan, with Suno's own download |

---

### 1. Steam AI disclosure: BLOCKER

**Evidence.**
- AI made the ship content listed in the facts above: art, effects, sounds, motion, base meshes, text and placeholder voices.
- No AI runs in the game.

**What Steam requires.**
- The content survey's third section covers generative AI "in creating content that ships with your game, and is consumed by players", such as artwork, sound, narrative and localisation. Efficiency tools are "not the focus".
- *Pre-generated* content is reviewed "the same way we evaluate all non-AI content", against the Steam Distribution Agreement's promises: no illegal or infringing content, and consistency with marketing.
- *Live-generated* content also needs a description of guardrails. Valve will not ship live-generated AI Adult Only Sexual Content.
- Valve introduced the rules on 10 January 2024 and says the disclosure appears on the store page.
- Press reports of a January 2026 revision say the form now asks about AI in store pages and marketing as well. The live form is the authority.

**Sources.**
- Steamworks, Content Survey: https://partner.steamgames.com/doc/gettingstarted/contentsurvey
- Valve, "AI Content on Steam" (10 Jan 2024): https://store.steampowered.com/news/group/4145017/view/3862463747997849618 (the page needs JavaScript; content confirmed through the Steamworks page above and press coverage)
- Revision report, secondary (17 Jan 2026): https://www.generationamiga.com/2026/01/17/valve-rewrites-steams-ai-disclosure-rules-for-developers/

**Action.**
1. Disclose pre-generated AI use for:
   - art, VFX, sound, animation and writing;
   - 3D base meshes, for as long as any AI-made mesh ships;
   - voices, if any synthetic voice ships;
   - music, once the Suno hymn ships (issue 28).

   Answer "no" to live generation. Use the draft wording in `STEAM_CHECKLIST.md`.
2. If capsules, trailers or store art use AI, disclose that too.
3. Keep an **AI asset ledger**: file, tool, model, date, prompt or source, and human changes. The provenance file is its start. It is our evidence if Valve or anyone else asks.
4. Re-read the live form at submission and update the wording if anything has changed.

### 2. Steam mature content survey, including what's hidden in the build: BLOCKER

**Evidence.** See the facts above.
- Partial nudity: bare buttocks, underboob, nipples showing through leather.
- Jiggle physics.
- Non-explicit sex scenes in text, including paid sex.
- Frequent gore against humans.
- Infrequent strong language.
- An anatomically detailed body hidden under outfits, and a bare male body behind a debug argument.

**What Steam requires.**
- "You must disclose all the adult content you've uploaded in your builds, even if it's not accessible or presented in your product."
- Steam lists four mature descriptors: General Mature Content; Frequent Violence or Gore; Some Nudity or Sexual Content; Adult Only Sexual Content. The last is hidden from users by default.
- Players see a warning page when a game's descriptors exceed their preferences.
- "Adult content that isn't appropriately labeled and age-gated" is not allowed on Steam.

**Sources.**
- Content Survey (above).
- Age gates: https://partner.steamgames.com/doc/store/age_gate
- Onboarding rules: https://partner.steamgames.com/doc/gettingstarted/onboarding

**Ruling.** Tick **General Mature Content**, **Frequent Violence or Gore** and **Some Nudity or Sexual Content**. Not Adult Only, unless issue 6 changes.
- In the free-text description, say plainly that the heroine's model has anatomical detail that her outfits always cover.
- This honesty is the protection. Games have been re-rated or pulled when hidden content was found later; the best-known case is GTA: San Andreas's "Hot Coffee" in 2005.

**My motion check** (4 Oct 2026; 960×540 renders, 8 frames at 1/15 s):
- What I rendered: all four outfits in her own `run_*` and `sprint_*` clips with jiggle on, from the front at chest height, the front below, behind and the side.
- Script: a scratch copy of `tools_scenes/lookdev.gd` that loads her clip library; it is listed in `docs/handoff/legal.md`.
- **Warden: a finding.** In the sprint, her left breast pushes through the plate cup: a small skin-coloured patch, the nipple area, shows through the metal in four of eight frames (`warden_sprint_chest_01`, `_02`, `_04`, `_05`). That is clipping, and it shows part of a nipple in normal play.
- **Reaver:** the band keeps the nipples covered throughout. Heavy underboob shows as the arms swing. The buttocks are fully bare (thong). The loincloth flap swings with the knee, but the crotch stays covered.
- **Stalker:** the nipples show as shapes through the leather, and the right buttock is bare. No exposure.
- **Arcanist:** a deep plunge, with the nipples showing as shapes through the suit. No exposure.
- **Warden, otherwise:** the lower buttocks show beneath the plate skirt. No exposure.
- **Not yet checked:** combat swings, the dash and leap, deaths, crouching, cinematic poses, and creation's poses.

**Action.**
1. Use the draft answers in `STEAM_CHECKLIST.md`.
2. **Fix the Warden's left cup clipping** in the sprint (outfits, main session). Until it's fixed, the survey's "no exposed nipples in play" is not true.
3. Extend the motion check to the clips not yet checked, at close range. If anything shows, fix it or disclose it.

### 3. Debug paths and unused files in the release build: BLOCKER

**Evidence.**
- `--body hero` loads the bare male body in any build (`People.cs:103` reads `Args` with no debug check).
- `tools_scenes/` ships, including `lookdev.gd`, whose `HIDE` setting hides outfit pieces.
- The export uses `export_filter="all_resources"`, so every imported file ships, used or not (auditor's finding 6):
  - KayKit characters;
  - `anime_female.glb` (an anime base body);
  - `woman.glb`;
  - git-ignored Poly Haven copies reached through the `godot/assets` link.

**Why it matters.**
- Steam's survey covers everything uploaded, not just what is reachable (issue 2).
- Data-miners extract `.pck` files. An unused body, or a nude view one command-line argument away, is exactly what turns into a re-rating or a headline.
- Unused third-party files also carry licence and credit duties for no benefit.

**Action.** These are recommendations; the main session decides and implements.
1. Gate developer arguments (`--body`, `--die`, `--quick`, `--shot` and the rest) behind `OS.IsDebugBuild()`, or strip them in release.
2. Add `tools_scenes/*` to the release `exclude_filter`.
3. Move to a resource list the game actually uses (the "selected resources" mode, or an exclude list for unused third-party packs and bodies). Then check the `.pck` contents before upload.

**Status (4 Oct, evening): done in code** by the performance lead at 8a770667, now merged:
- `Args.Dev` = `OS.IsDebugBuild()` gates the developer switches;
- the excludes below are in all three presets.

What remains is my review of the exported `.pck` listing, when the GPU is free.

The spec it implements:
- The performance lead (a7145e18b3eb78294) had the exact spec:
  - `Args` in `godot/src/Shots.cs` returns nothing when `!OS.IsDebugBuild()`. Every developer argument goes through it, so one change gates them all.
  - The `exclude_filter` list: `tools_scenes/*`, the anime and woman bodies and their hair, `hero.glb` until his base garment exists, the unused KayKit, web and Poly Haven files, and `art/vo/*` for the placeholder voices.
  - A zip-pack listing for me to review.
- The owner has approved the export templates, and the main session has fetched Godot's 4.5.1 mono templates. The build waits only for the GPU to be free.
- Checked and harmless: `--bare` hides the world, not an outfit. The environment switches (`HAIRDEBUG`, `FX_LAYERS`, `CAMPFIRE_PARTS`, `FLORA_COUNT`) change only effects and counts.

### 4. Licence notices and credits missing from the build: BLOCKER

**Evidence.**
- The export has no `.txt` or `.md` files.
- `godot/art/fonts/OFL-*.txt` exist in the repo but don't ship.
- No Godot or .NET notice ships, and no CC BY credit ships.
- The in-game credits (`godot/src/Ui/Front.cs`) are out of date (auditor's finding 5).

**What the licences require.**
- **Godot (MIT):**
  - include Godot's licence text, in credits, a licences screen or an accompanying file;
  - include Godot's `COPYRIGHT.txt` for its third-party parts (FreeType, ENet, mbedTLS, Jolt and others), which Godot recommends shipping, optionally as `GODOT_COPYRIGHT.txt`.
  - Source: https://docs.godotengine.org/en/stable/about/complying_with_licenses.html
- **.NET runtime (MIT)**, shipped with C# exports: include its `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT`.
  - Source: https://github.com/dotnet/runtime (repository root files)
- **SIL Open Font License 1.1** (Alegreya, Alegreya Sans, Cinzel): fonts may be bundled and sold with software. Each copy must carry the copyright notice and licence, as a text file or as metadata the user can see.
  - Source: https://openfontlicense.org/open-font-license-official-text/
- **CC BY 4.0** (13 Sketchfab models, 100STYLE): credit the creator, the title, the source link and the licence link, and indicate changes.
  - Source: https://creativecommons.org/licenses/by/4.0/legalcode.en §3(a)
- **CC0** (Quaternius, Poly Haven, ambientCG, Kenney, KayKit, MakeHuman): no credit required. Crediting is good practice.

**Action.** These are recommendations.
1. Add a "Credits and licences" screen reachable from the title and pause menus.
2. Ship a `licences/` folder beside the executable, containing:
   - `GODOT_LICENSE.txt` and `GODOT_COPYRIGHT.txt`;
   - the .NET `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT`;
   - the three OFL texts;
   - `CREDITS.txt`, with every CC BY credit and the AI tools line (issue 24).
3. Generate `CREDITS.txt` from the provenance ledger so it can't drift.
4. I will review the screen and the folder before launch.

**Status (4 Oct, evening): built; reviewed on paper, not yet seen in game.** The UI design lead (a26f87c39952dcd9c) built it at 178768aa:
- `Content/Credits.cs` cleans `CREDITS.md` by rule into `data/credits.json` and `licences/CREDITS.txt`, and a golden-file test keeps them in step.
- The page opens from the title and the pause menu.
- Godot's notices are read from the engine.
- `licences/` is packed and copied beside each build.

I compared the shipped notice texts with their sources. `GODOT_LICENSE.txt` and `GODOT_COPYRIGHT.txt` match 4.5.1-stable, the two .NET files match `release/8.0`, and the OFL texts match `art/fonts`. Every CC BY entry carries its source, creator, licence link and changes. Open items (sent to the lead):
- drop the entries for works the release excludes;
- make the AI section the single list in `STEAM_CHECKLIST.md` E;
- see the screen in game when the GPU is free.

**Specification** (for the UI design lead's successor; sources checked 4 Oct 2026).
- **Godot 4.5.1:**
  - Take `LICENSE.txt` and `COPYRIGHT.txt` from the `4.5.1-stable` tag of `godotengine/godot`.
  - On the screen, read the same notices from the engine: `Engine.GetLicenseText()`, `Engine.GetLicenseInfo()` and `Engine.GetCopyrightInfo()`. That way the screen can't drift from the engine that ships.
  - Godot's compliance page accepts a credits screen, a licences menu or "a file containing the license text". It suggests shipping `COPYRIGHT.txt` "rename[d] to GODOT_COPYRIGHT.txt".
- **.NET 8:**
  - Godot "bundles the parts of .NET needed to run already-compiled games" (Godot's C# basics page), so the runtime's notices apply.
  - Use `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT` from the runtime pack that the export restores (`microsoft.netcore.app.runtime.*` in the NuGet cache). Failing that, take them from `dotnet/runtime`, branch `release/8.0`.
  - Re-take all of these when Godot or .NET is upgraded.
- **Fonts:** `godot/art/fonts/OFL-*.txt` as they are.
- **CC BY works:** the entries in `public/assets/CREDITS.md` meet CC BY 4.0 §3(a): creator, title, link, licence link and changes. Keep its "provided as is, without warranty" sentence. That covers §3(a)(1)(A)(iii).
- **Player-facing text** is a cleaned copy of `CREDITS.md`. Drop its internal notes:
  - "under review" and "provenance under review";
  - repository paths;
  - the fetch tools' line-format notes;
  - the web-only section.

  Drop the anime and woman bodies too, once the export excludes them.
- **How the folder ships:** Godot's export doesn't copy loose files, so `tools/godot/export.sh` should copy `licences/` beside the executable after each export. For macOS, it goes inside the `.zip` beside the `.app`. The in-game screen can read its texts from the pack through an include filter (`licences/*.txt`).
- **Sources:**
  - https://docs.godotengine.org/en/stable/about/complying_with_licenses.html
  - https://docs.godotengine.org/en/stable/classes/class_engine.html
  - https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_basics.html

### 5. Third-party assets: BLOCKER (the boar), FINE with conditions (the bodies), SHOULD FIX (two), FINE (The Ember Watch)

These are my rulings on the auditor's findings (`ASSET_PROVENANCE.md`), updated for the owner's answers of 4 October. The owner's aim: "we will replace everything eventually if we can with our own / generated own".

- **(a) The boar** (`godot/art/beasts/boar.glb`, Sketchfab "Animated Realistic Boar" by AnimalMesh 3D): **BLOCKER.**
  - It is labelled CC BY 4.0, but its description says "personal use only; commercial use only for versions purchased on Fab or Patreon".
  - A CC licence, once granted, can't be revoked. But conflicting statements from the licensor invite a dispute and a Steam DMCA notice.
  - The owner plans to replace third-party work "eventually". **"Eventually" is too late for the boar:** it must be replaced before launch (`REPLACEMENT_PLAN.md` 1.1).
  - If the replacement won't be ready, buy the commercial version on Fab as a stop-gap and keep the receipt.
- **(b) The base bodies:** **FINE, with conditions** (re-ruled 4 Oct, evening, on the owner's corrected answer).
  - **What they are:**
    - the heroine's body, from the owner's `234.glb`;
    - the older woman, `woman.glb`, which is dropped from the build anyway (issue 3);
    - the hero's body, from `ComfyUI_00008.glb`;
    - the owner's reference sheet, `images/1.webp`.
  - **The owner's answer:** "we made images in krea 2 turbo for the IMAGE but we did not use hunyuan 3d. we used trellis for the 3d", and "we made it in comfyui". This corrects his first answer ("krea assets"). Krea's website was not used, so its plan terms and its Hunyuan-based 3D tool don't apply.
  - **The machine agrees.** The evidence is copied into `docs/legal/records/BODIES_RECORD.md` before the logs rotate away.
    - The only TRELLIS installed is TRELLIS 2 (since 30 Sep), run by ComfyUI's own nodes. No Hunyuan model is in ComfyUI, and no `nvdiffrast`, whose licence is non-commercial, is installed.
    - **The hero:** five Krea 2 Turbo prompts ran from 00:18 to 00:26 on 4 Oct, then a TRELLIS 2 run (with BiRefNet and DINOv3) at 00:28. `ComfyUI_00008.glb`, made by "ComfyUI", landed on the Desktop at 00:38.
    - **The heroine** (`234.glb`, in the repo by 1 Oct 23:08): the logs of that day don't name models. The owner's word, and TRELLIS 2 being the only TRELLIS installed, carry it.
  - **The licences that apply:**
    - **Krea 2 Community License** (issue 8). The pictures are Outputs of the Krea 2 Turbo weights we run locally, as for the UI art. Commercial use is allowed while total annual revenue is under US$1M, and the licence is revocable on 30 days' notice. Each body mesh is commercial use of a Krea picture. So **the bodies join the Krea footprint**: if revenue nears US$1M, or Krea gives notice, they need the enterprise licence or replacement like the rest.
    - **TRELLIS 2** (`microsoft/TRELLIS.2-4B`): MIT. Its DINOv3 encoder is under Meta's DINOv3 License, which allows commercial use and makes no claim on outputs; BiRefNet is MIT. ComfyUI itself is GPL-3.0, a tool licence that doesn't reach its outputs.
    - **A third-party LoRA, probably on the hero's picture.** Those runs attached 256 LoRA patches. The official darkbrush LoRA attaches 263, but `MysticXXX_KREA2_v1` has exactly 256 target layers. It was installed at 20:35 on 3 Oct, after the heroine was made. I identified it by its file hash on Civitai:
      - model 2728644, "[KREA 2] Mystic XXX" by `alcaitiff`, version 1.0 of 25 Jun 2026;
      - the creator's permissions allow commercial use of generated images (Image, Sell, Rent), need no credit, and allow derivatives;
      - Civitai flags it as an explicit adult concept LoRA, not a real person (`poi` false), and not involving minors;
      - its training data is unpublished. Whether a model's training on others' images taints its outputs is **unsettled law** everywhere, and the same is true of Krea 2 itself.
      - Either way the hero is covered: if it was darkbrush, that is Krea's own LoRA under the same licence.
  - **Lower likeness risk than it looks.** Neither hero's face comes from these pictures: both heads are MakeHuman (CC0), with face paint made separately. Only the body's shape does, which makes resemblance to a real person far less likely.
  - **Conditions for keeping them:**
    1. **No real person, and no one else's art.** The owner confirms in writing that each picture was made from his own words (text-to-image). No real person was named, no photo of a person was used, and no one else's picture was uploaded as an input. If any picture was image-to-image, he names the input and where it came from; the reference sheet `images/1.webp` is the one to account for.
    2. **The record.** The owner signs the paragraph listed at the end of `BODIES_RECORD.md`: date, local ComfyUI, Krea 2 Turbo, the LoRA, the input, TRELLIS 2. He confirms which LoRA the hero's picture used. Keep the record with the provenance file.
    3. **The Krea footprint.** List the heroine's and hero's bodies, and the 26 creation cameos made from her, in the Krea-made file list (`ASSET_PROVENANCE.md`) and in the stage 2 plan for the revenue cap.
    4. **Disclosure.** They stay in the Steam AI disclosure as AI-made base meshes, which `STEAM_CHECKLIST.md` D3 already covers.
  - **The owner's wish to make everything our own** still stands. These bodies can be rebuilt on MakeHuman later (`REPLACEMENT_PLAN.md` 1.2 and 1.3), but that's for ownership and the Krea cap, not because launch needs it.
  - **What I checked before** (Krea's website terms, its 3D tool's default Hunyuan3D 2.1 model, and that licence's EU and UK bar) no longer applies to these bodies. It stays in 5(g) as a rule for any future work. Sources:
    - https://www.krea.ai/terms
    - https://www.krea.ai/pricing
    - https://www.krea.ai/3d
    - https://huggingface.co/tencent/Hunyuan3D-2.1/blob/main/LICENSE
    - https://civitai.com/models/2728644 (with the API records cited in `BODIES_RECORD.md`)
- **(c) Chevalier Sword and Medieval Shield** (Sketchfab, "based on the concept by Guillem Daudén" and "by Artyom Vlaskin"): **SHOULD FIX.**
  - A 3D modeller's CC BY grant can't license the concept artist's own rights in the design.
  - Action: replace them, or obtain the concept artists' written permission.
- **(d) Character names carried over from The Ember Watch** (Maeca Barefoot, Vonnra Hydrocheck, Rav, Chid, Keegan): **FINE**, subject to the owner confirming that none is a real person's name or handle.
- **(e) The Ember Watch:** **FINE (cleared as a blocker), with records to keep.**
  - **The facts:**
    - Survivor Unchained's world, lore, weapons and combat roots were ported from The Ember Watch, hosted at `stevenrogerino/wowsurvivors`. Its commits are by Claude and `munch4lunchbot`.
    - The owner's answer (4 Oct): "I do not own it. I mean I made the game but nothing is copyrighted or anything - we built it all in claude with no generated content. I guess I own it?"
  - **What the answer means, in plain words:**
    1. **No one else has a claim, and that was the blocker.** The worry was that someone else might own the source. The owner made it, with Claude as his tool, and no other person contributed. So nobody else's permission is needed. Anthropic's terms assign Anthropic's rights in Claude's output to the user, "if any" (issue 26).
    2. **"Nothing is copyrighted" isn't quite right, and no registration is needed for what is protected.**
       - In the US, "Copyright protection … exists automatically from the moment the original work of authorship is fixed" (Copyright Office, Circular 1).
       - "registration is not a condition of copyright protection" (17 U.S.C. §408(a)).
       - Whatever in The Ember Watch is protected became the owner's the day it was written down (17 U.S.C. §201(a)).
    3. **But copyright covers only the human part.** "We built it all in claude" means the words and code were written by an AI from his direction. "No generated content" is true of pictures, but text written by Claude *is* AI-generated for copyright purposes.
       - The Copyright Office's position (*Copyright and Artificial Intelligence, Part 2*, 29 Jan 2025): purely AI-generated material is not protected, and "prompts do not alone provide sufficient control".
       - What is protected: his own expression wherever it can be seen in the result, his creative selection and arrangement, and his own edits.
       - Copyright never protects ideas, systems, names or titles in any case (17 U.S.C. §102(b); Circular 1: "Titles, names, short phrases, and slogans").
       - So he owns The Ember Watch in the sense that matters for selling the game: it's his to use and nobody can stop him. But a copier could take some AI-written parts of it, and he could do little about that.
    4. **Registration matters only for enforcing.** For a US work, you must register before you can sue for infringement (17 U.S.C. §411(a)). Statutory damages and attorney's fees need registration before the infringement, or within three months of first publication (§412).
       - The useful step is to register **Survivor Unchained itself** around launch, not The Ember Watch.
       - An online Standard Application costs US$65 (Copyright Office fees page, read 4 Oct 2026).
       - The application must disclose the AI-generated material and claim only the human contribution. The lawyer should draft that claim (`QUESTIONS_FOR_LAWYER.md`, question 2).
  - **Records to keep** (the owner's evidence of authorship and of no third party):
    1. A dated archive of The Ember Watch repository with its full history: a `git bundle` of `stevenrogerino/wowsurvivors`, kept offline.
    2. His own directions: chat transcripts, briefs, `CLAUDE.md` and memory files, design docs, anything he typed, drew or chose.
    3. A short signed and dated statement covering:
       - that he conceived and directed The Ember Watch and Survivor Unchained;
       - that no other person contributed creative material (or naming anyone who did, and what they did);
       - that the `stevenrogerino`, `munchtech` and `munch4lunchbot` accounts are his. If any is not, a one-paragraph written assignment from its holder is needed instead;
       - which AI tools he used.
    4. The version of Anthropic's terms in force while it was made (issue 26).
  - It began as a Warcraft fan work. Its own NOTICE says every borrowed name was replaced, and issue 15 covers the names that remain. Copyright doesn't protect names, but trade marks and the look of copying can still cause trouble.
  - **Sources:**
    - Circular 1: https://www.copyright.gov/circs/circ01.pdf
    - 17 U.S.C. §§102, 201, 408, 411 and 412: https://www.law.cornell.edu/uscode/text/17
    - Fees: https://www.copyright.gov/about/fees.html
    - Part 2 report: https://www.copyright.gov/ai/
- **(f) My rulings on the rest of the auditor's inventory** (`ASSET_PROVENANCE.md`, 4 Oct):
  - **CC0 sources: FINE.** Quaternius, KayKit, Kenney, Poly Haven, ambientCG, OpenGameArt and MakeHuman. Keep the courtesy credits.
  - **CC BY sources: FINE once credited** (issue 4): the wolf, the lampling, the nine other weapons, 100STYLE and the anime base. This includes the 48 item icons, which are photographs of the CC BY weapons and so carry their credit duty.
  - **Mixamo: FINE.** It is royalty-free in games, and no raw files ship.
  - **AccuRIG: FINE.** Our own sculpts were rigged with it, and no Reallusion content ships.
  - **The anime base body** (`anime_female.glb`, "Genshin Style Anime Female Base Mesh"): remove it from the build (issue 3). An unused youthful-styled body in an adult game is a needless risk.
  - **The older woman body** (`woman.glb`, unknown origin): remove it from the build.
  - **Watch list:**
    - never ship the `fantasy` sound pack: it claims CC0, but its files carry 2014 library metadata;
    - the `MysticXXX_KREA2_v1` LoRA is **now identified** (Civitai 2728644, by `alcaitiff`; the creator allows selling images). Outputs made with it may ship, with a ledger line, under the same Krea 2 terms (5(b));
    - never ship make3d's Hunyuan test models;
    - never ship motion captured from Pexels footage of identifiable people without a check.
  - **Marketing:** concept art and animatics made with Krea are Krea outputs. Using them on the store page or in a trailer is commercial use (issue 8), and it goes in the AI disclosure (issue 1).
  - **The web and Electron build** is a separate product. If it is ever sold, it needs its own notices.
- **(g) Rules for replacements, "our own / generated own"** (new, 4 Oct). A replacement is only an improvement if its own chain is cleaner than what it replaces. In order of preference:
  1. **Made by us** in Blender or in code, or on a CC0 base (MakeHuman, the UAL skeleton). There are no conditions.
  2. **Generated locally with an unrestricted model:** TRELLIS 2, Pixal3D or MoGe (MIT), or Kimodo (outputs ours). The input picture must be ours too:
     - our own render or drawing;
     - the owner's own photo, with a model release if a person is in it;
     - an image we generated ourselves.
  3. **Generated with Krea 2 locally:** allowed, but it adds to the US$1M revenue cap and the 30-day termination risk (issue 8). That includes a mesh made from a Krea picture, because it is commercial use of a Krea output.
  4. **Never for anything that ships:**
     - Hunyuan3D in any version, local or on Krea's website (the EU and UK bar);
     - any web generator on a free plan;
     - any picture of a real person without a release;
     - any picture of someone else's art;
     - any LoRA or checkpoint whose creator doesn't allow commercial use of images, or that is trained on a real person (Civitai's "poi" flag). Check each one's permissions before use, as was done for `MysticXXX_KREA2_v1` (allowed).

  Every replacement gets a ledger line before it lands: file, tool, model, licence, input, date. A CC0 asset (Quaternius, Poly Haven, Kenney) has no legal risk at all. Replacing it with a Krea-made one *raises* risk, so do those last, for ownership's sake only.

### 6. Explicit-scene placeholders and the explicit-content decision: BLOCKER (remove placeholders) / DECISION

**Evidence.**
- Three "[explicit scene: … — to be written]" slots shipped in `dialogue.json` behind `settings.intimacy == "full"`: `sella.night`, `sella.free_night` and `maeca.blind`. Three more, for Act 2, existed only in the docs.
- `docs/romance/README.md` plans beat sheets "for the owner's writer".
- **Status: the placeholders are removed** (story lead, efc15256, merged into the integration branch by 4 Oct evening):
  - Every scene keeps its non-explicit cut-away for all players.
  - `StoryLint` now fails if any "[explicit" text or `settings.intimacy` variant returns to `dialogue.json`.
  - The romance drafts in `docs/romance/data` still hold slots as notes only. They aren't shipped, and the test would catch them.

**Why it matters.**
- The placeholders are not explicit, but they are sexual descriptions shipped in data, and Steam's survey covers "all adult content uploaded".
- More importantly, writing explicit scenes would make this an **Adult Only Sexual Content** game. The consequences:
  - hidden from every user who hasn't opted in;
  - a longer review, because the build and store page are reviewed together;
  - a likely refusal or blocking in some regions;
  - exposure to the payment-network rule Valve added in July 2025 (issue 25);
  - Australian, UK and German age-verification friction.
- A paid-sex storyline in an Adult Only game is the kind of content most exposed to that rule.

**Action.**
1. Remove the placeholder slots from the release data (or strip them at export) until the decision is made.
2. **Decision for the owner, with the lawyer:** keep the base game non-explicit, the current cut-aways. If explicit scenes are ever wanted, ship them as a separate Adult Only DLC with its own survey and review, so the base game stays visible in the normal store.

### 7. Sex tied to a gameplay buff: RESOLVED once b47d98ea merges

**Status (4 Oct, evening).**
- The owner decided "we can remove that as a buff that does anything other than say it happened".
- The story lead's b47d98ea (`worktree-agent-a73ca9d35d0c487a9`) does that, and I have checked the diff:
  - `Character.cs` no longer adds the damage or speed modifiers;
  - the notices and the book drop the numbers ("Warmed: last night is still with you");
  - `QuestTests` checks that damage, speed, health, armour, critical hits and regeneration are the same with it and without it;
  - the story bible now says a love scene never gets a mechanical reward.
- The paid room's own "Rested: +5% health" comes from a bed, not sex, and is fine.
- Once merged, the survey answer "sexual content linked to rewards" becomes **no**.
- The game can then be judged against MA 15+ instead of being forced to R18+. MA 15+ allows "Sexual activity may be implied" and "Nudity should be justified by context", provided neither is "related to incentives or rewards".
- One question remains for the lawyer (`QUESTIONS_FOR_LAWYER.md`, question 7): the scenes still raise affection and trust, which is the relationship itself.

**Evidence (before the change).** `sella.night`, `sella.free_night` and `maeca.blind` applied the condition `warmed`. The notice text: "You feel good. Better than good. (Warmed: +8% damage, +5% speed, one day)". The scenes also grant affection and trust.

**Law.** Australia's *Guidelines for the Classification of Computer Games 2023* (F2023L01424):
- "Except in material restricted to adults, nudity and sexual activity must not be related to incentives or rewards."
- Incentives and rewards include "new skills or increases in attributes such as strength" and "making tasks easier to accomplish".
- So this game cannot be **MA 15+**; it is at least **R 18+**. (Under the 2023 guidelines, R 18+ no longer bars sex linked to rewards. Under the 2012 guidelines it did.)
- Since 9 September 2026, Australian Steam users must link an Australian credit card to view R18+ and mature content (the Age-Restricted Material App Distribution Services Code).
- Sources:
  - https://www.legislation.gov.au/F2023L01424/asmade/text
  - Steam's age-check notice: https://store.steampowered.com/agecheck/app/2172010/?cc=au

**Action.**
1. ~~Decouple the buff from sex.~~ **Done** by the owner's decision (b47d98ea); it remains to be merged.
2. Ask the lawyer whether relationship progress (affection and trust) from a love scene also counts as a reward.

### 8. Krea 2 licence: SHOULD FIX now; BLOCKER before revenue nears US$1M

**Evidence.** Krea 2 Turbo and the official darkbrush LoRA (`Comfy-Org/Krea-2`, `krea/Krea-2-LoRA-darkbrush`) made the painted UI, the icons, the face paint and irises, and the ground marks.

**The licence** (Krea 2 Community License Agreement v.1, 22 June 2026, read in full from the PDF in the Hugging Face repo):
- §2.3: commercial use of the model, derivatives "or Outputs" is permitted only while you, with affiliates, have **total annual revenue under US$1,000,000**, trailing twelve months, all sources. At or over it, "you must immediately cease Commercial Use and contact Krea" for an enterprise licence.
- §2.1 and §9.2: the licence is "revocable", and Krea "may terminate this Agreement … for any reason upon thirty (30) days' notice".
  - §9.4 then requires you to stop using and destroy the *model and Derivatives*. It does not mention Outputs, so whether outputs made earlier survive termination is **unclear** (lawyer).
- §4.2: you must implement "reasonable and appropriate Content Filter measures"; "manual human review processes" are listed as one.
- §4.3: disclose AI generation where a platform requires it. Steam does.
- §5.3: "You own all Outputs you generate, subject to your compliance with this Agreement."
- §8: you indemnify Krea against claims arising from your outputs.
- Delaware law.
- The Acceptable Use Policy (22 June 2026) bars CSAM, non-consensual intimate imagery, impersonation, IP infringement, and "obscene, or otherwise objectionable" content.
- Sources:
  - https://huggingface.co/Comfy-Org/Krea-2 (LICENSE.pdf)
  - https://krea.ai/krea-2-licensing
  - https://www.krea.ai/krea-2-use-policy

**Ruling.** Fine for launch below US$1M. It becomes a hard stop the day revenue reaches US$1M, or 30 days after a termination notice.

**Action.**
1. Record our content-filter practice in writing: every Krea output is reviewed by an agent and approved by the owner before it ships, and prompts never name real people. That is our §4.2 compliance.
2. Keep a list of every Krea-made shipped file (the auditor is building it). It includes the heroine's and hero's bodies and the 26 creation cameos, because the bodies were sculpted from Krea 2 Turbo pictures (issue 5(b)).
3. Either budget for an enterprise licence (ask Krea for a quote before launch; opensource@krea.ai), or schedule replacing Krea outputs with our own or differently licensed work. That also serves the "remove anything not ours" goal.
4. Lawyer: whether past outputs remain usable after the threshold or after termination.

### 9. LTX-2.x licence: FINE, with two duties

**Evidence.** LTX-2.5 (Lightricks) made 15 effect flipbooks and 5 sound takes. Its text encoder is Gemma 4 (Apache 2.0).

**The licence** (LTX-2.x Community License Agreement, 11 August 2026):
- Free use for entities with annual revenue under **US$10M**; a paid licence above it.
- "Licensor claims no rights in the Output."
- You must not "remove, disable, alter, or circumvent any … metadata, watermarking, content provenance, latent disclosure" applied to outputs.
- The Attachment A use restrictions bar placing generated content "in any context … without expressly and intelligibly disclaiming that the information and/or content is machine generated".
- Source: https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x

**Action.**
1. The credits and Steam AI disclosure name AI-generated effects and sound (issues 1 and 24). That satisfies the disclaimer.
2. Keep the original LTX outputs (masters) unaltered in an archive.
3. Lawyer: whether turning a clip into a sprite sheet or an OGG "removes metadata" in the licence's sense. It's a technical necessity, so I think not, but it's untested.

### 10. Other AI models: FINE

| Model | Use | Licence (checked 4 Oct 2026) | Outputs |
|---|---|---|---|
| TRELLIS 2 (Microsoft) | image to 3D base meshes | MIT (`microsoft/TRELLIS.2-4B`) | unrestricted |
| Pixal3D (TencentARC) | multi-view to 3D | MIT (`TencentARC/Pixal3D`) | unrestricted |
| MoGe-2 (Microsoft) | geometry in the TRELLIS graph | MIT (`Ruicheng/moge-2-vitl-normal`) | unrestricted |
| BiRefNet | background cut-outs | MIT | unrestricted |
| DINOv3 (Meta) | encoder inside TRELLIS | DINOv3 License (19 Aug 2025): commercial use allowed; trade controls; no output terms | ours |
| SAM 3D Body (Meta) | video to motion (`tools/anim/video_motion.py`) | SAM License (19 Nov 2025): same pattern | ours |
| Kimodo-SOMA-RP v1.1 (NVIDIA) | text to motion | NVIDIA Open Model License: "Models are commercially usable"; "NVIDIA does not claim ownership to any outputs"; model card: "ready for commercial use" | ours |
| Llama 3 8B (Meta) | Kimodo's text encoder only | Llama 3 Community License | no duty for motion outputs (we don't distribute Llama) |
| Qwen3-VL 4B, Qwen-Image VAE | Krea's text encoder and VAE | shipped inside the Krea repo, under Krea's terms | as issue 8 |
| Whisper | transcript checks | MIT / Apache 2.0 | n/a |
| **Hunyuan3D-2 and 2.1 (Tencent)**: `tools/make3d`, and the default model of Krea's website 3D tool | picture to 3D | **Tencent Hunyuan 3D 2.0 and 2.1 Community Licenses exclude the EU, UK and South Korea**; free under 1M monthly active users. The owner being in the US doesn't help: §5(c) of 2.1 bars displaying output outside the Territory, and EU and UK buyers would see it | **don't ship any output** (issues 5(b), 5(g)) |

Sources: each model's Hugging Face card or LICENSE file, as named. The Kimodo licence was read from `nvidia/Kimodo-SOMA-RP-v1.1/LICENSE`.

**Action.**
1. Retire `tools/make3d`'s Hunyuan backend for game assets, or confine it to throwaway concept work. Make TRELLIS 2 the default (the README already says it is coming).
2. Confirm that no shipped mesh is Hunyuan-made.

### 11. Placeholder voices: BLOCKER if shipped, FINE if replaced

**Evidence.**
- 19 files in `godot/art/vo`, flagged `placeholder`.
- The pipeline: Maya1 performs each line (Apache 2.0); Seed-VC converts it to the cast voice (GPL-3.0); the cast references were designed from text by VoxCPM2 (Apache 2.0).
- `tools/vo/cast.json` says "No voice here is, or is modelled on, any real person".
- The owner has paused placeholders; finals are to come from ElevenLabs.

**Licences.**
- All allow commercial use.
- GPL-3.0 governs Seed-VC's code and weights, not normally the audio it outputs. That is the usual reading of the GPL; a lawyer can confirm.
- If any placeholder ships, it is pre-generated AI audio and goes in the disclosure.

**Action.** Before launch, replace every placeholder with a final, or make the release build drop files marked `placeholder`. The voice handoff already proposes this (`docs/handoff/voice.md`, 4f8e241). It is the main session's decision.

### 12. ElevenLabs terms (the final voices): SHOULD FIX (process)

**The terms.** ElevenLabs Terms of Service (non-EEA, updated 31 March 2026). A separate version applies to residents of the EEA, Switzerland and the UK. **The owner lives in the United States, so the non-EEA terms are his.**
- Free users: non-commercial only. Paid users: commercial use. Help centre: "The free plan does not include a commercial license"; "Content generated using Beta Services cannot be used for any commercial purpose"; content made during a paid subscription stays commercially usable after it ends.
- §4(c): "you retain all rights in and to your Output".
- §4(d): ElevenLabs gets a **perpetual, irrevocable, sub-licensable licence to your Content** (inputs and outputs) to provide and improve its services. Our unreleased scripts are inputs.
- Prohibited Use Policy (17 August 2026):
  - 9(k) and 9(l) bar using Output "as input for any machine learning or training of artificial intelligence models", or in any training or testing dataset;
  - 9(e) bars removing proprietary markings associated with Output;
  - 5 bars impersonating a voice without consent;
  - 8 exempts "purely fictional contexts" from its violence and hate rules;
  - 2(c) bars facilitating "sexual services". It is aimed at real transactions, and a fictional sex worker's lines should not be caught, but I flag it for the lawyer.
- Voice Library Addendum (6 March 2026):
  - Library voices are other users' **own voices**, shared for use;
  - a voice owner may remove a voice after a notice period (30 days to 2 years);
  - Outputs made before that "remain available for use";
  - owners may switch on live moderation of what their voice says.
- Sound Effects Terms (12 Feb 2026): sound effects made with ElevenLabs are sublicensed to other users unless you click "Disable".

**Sources.**
- https://elevenlabs.io/terms-of-use
- https://elevenlabs.io/terms-of-use-eu
- https://elevenlabs.io/use-policy
- https://elevenlabs.io/vla
- https://elevenlabs.io/sound-effects-terms
- https://elevenlabs.io/docs/help-center/legal/can-i-publish-the-content-i-generate-on-the-platform

**Action.** I sent the voice lead the first four on 4 Oct; they are in the voice handoff as the successor's first job.
1. Record every final on a paid plan, with a released (not beta) model, and log the plan and model per take. The packets specify Eleven v4, which press reports as released on 28 Sep 2026; the owner should confirm the UI shows no beta label.
2. Never use ElevenLabs output as a reference, profile, fine-tune input or dataset for any local model.
3. Use Voice Design voices for the narrator and the love interests. If a Library voice is used anywhere, log its ID and notice period.
4. Keep the downloaded masters untouched.
5. Disable sublicensing of any ElevenLabs sound effects we use.
6. The importer's quality check, which runs Whisper, UTMOS and a speaker embedding on each take, is a grey area under 9(k). See "Notes for other areas" in `docs/team/legal.md`.

### 13. Voice cloning and digital-replica law: FINE as practised; get written consents

**Evidence.**
- Team rule (`docs/team/README.md`): only the owner's voice, performances the owner approves, or datasets licensed for cloning; never a real, identifiable person.
- The cast references are designed voices, not clones.

**Law.**
- US states now regulate digital replicas of voice and likeness: Tennessee's ELVIS Act (2024), and California's AB 2602 and AB 1836 (2024, on contracts for digital replicas and on deceased performers).
- The US Copyright Office's *Part 1: Digital Replicas* (31 July 2024) recommends a federal law.
- In the UK and EU, voice data is personal data (UK and EU GDPR), and passing-off and personality claims are possible.
- None of this bites if we never clone a real person without written consent.
- Source: https://www.copyright.gov/ai/ (Part 1)

**Action.** If the owner ever records himself, or a performer, for cloning, use a **written consent and licence**: a voice release covering AI cloning, the scope (this game and its marketing), the term, payment and withdrawal. The lawyer should draft it. Never use a Voice Library voice that sounds like a celebrity.

### 14. Prompts that name other games: SHOULD FIX

**Evidence.** These prompts ask for "the style of Diablo IV skill icons", "Diablo IV and Hades" or "Diablo and Baldur's Gate art style":
- `tools/uiforge/icons.py`, `emblems.py`, `items.py` and `explore.py`;
- `tools/comfy/ui_assets.json`;
- `tools/comfy/ui_concepts.py` and `concepts.py`.

**Law.**
- Style as such isn't protected by copyright.
- But an output substantially similar to a specific protected asset infringes however it was made.
- Steam checks that AI output isn't infringing (issue 1), and the Krea licence makes us indemnify Krea for infringing outputs.
- Prompting by product name raises both the odds and the optics.
- See also *Getty Images v Stability AI* [2025] EWHC 2863 (Ch), where trade-mark claims over reproduced watermarks partly succeeded. That case is a reminder that outputs echoing a source can create liability. The training-copy claims there were not decided in Getty's favour.

**Action.** Sent to the UI art lead on 4 Oct.
1. Describe looks in plain words. **Done:** all seven files rewritten with no product named (c457cc9 on `worktree-agent-a1a394643aabfb169`); the lead reports that shipped PNGs carry no prompt text.
2. Before launch, compare each shipped icon, emblem and frame from those prompts against the Diablo IV and Hades icon sets, and remake any close one. **Open:** the UI art lead has taken this on.

### 15. Warcraft-derived names; derivative Sketchfab models: SHOULD FIX

**Evidence.**
- Skill names Moonfire, Fan of Knives and Starfall ship. The Ember Watch had banned them as Warcraft names.
- Consecration and Whirlwind also ship.

**Ruling.**
- Single names and short phrases aren't protected by copyright.
- But distinctive names from a famous game, in a game that began as "wowsurvivors", invite a complaint and look derivative.
- **Rename Moonfire, Fan of Knives and Starfall.** Consecration and Whirlwind are ordinary words and can stay.
- Sword and shield: see 5(c).

### 16. Copyright in AI-made work: what we own and what others may copy: SHOULD FIX (strategy)

**The law (US).**
- Copyright Office, *Copyright and Artificial Intelligence, Part 2: Copyrightability* (29 January 2025):
  - "Copyright does not extend to purely AI-generated material, or material where there is insufficient human control over the expressive elements."
  - "prompts do not alone provide sufficient control".
  - Protection does cover a human's "works of authorship that are perceptible in AI-generated outputs, as well as the creative selection, coordination, or arrangement of material in the outputs, or creative modifications of the outputs".
  - Applicants must disclose more than de minimis AI content when registering (Registration Guidance, 88 Fed. Reg. 16190, 16 March 2023; *Zarya of the Dawn*, 21 Feb 2023).
- *Thaler v. Perlmutter*, D.C. Cir., 18 March 2025: authors must be human. The Supreme Court **denied certiorari on 2 March 2026**.
- Sources:
  - https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf
  - https://www.copyright.gov/ai/
  - On the cert denial, secondary: https://www.hklaw.com/en/insights/publications/2026/03/the-final-word-supreme-court-refuses-to-hear-case-on-ai-authorship

**The law (UK).**
- Copyright, Designs and Patents Act 1988 s 9(3) currently makes "the person by whom the arrangements necessary for the creation of the work are undertaken" the author of a computer-generated work.
- The Government's *Report on Copyright and Artificial Intelligence* (18 March 2026) prefers to **repeal** s 9(3), subject to further evidence.
- This is unsettled; don't rely on it.
- Source: https://www.gov.uk/government/publications/report-and-impact-assessment-on-copyright-and-artificial-intelligence

**The law (EU).** Protection needs the author's "own intellectual creation" (CJEU case law). Purely machine output is generally unprotected. This is unsettled at the edges.

**What that means here.** Almost everything in this game was made by AI under the owner's direction: generators for art, motion and sound, and agents for code and text. So:
- **Weakly protected:** individual AI images, icons, textures, effects, sounds and motion clips with little human change. In the US a competitor could probably copy one of them without infringing.
- **Better protected:**
  - the game as a whole: its selection, coordination and arrangement;
  - the owner's own creative input where it is perceptible: his drawn markups on outfits, any reference art he drew, lines he writes or rewrites himself;
  - human-modified assets;
  - the code and text to the extent a human shaped the expression. That is weaker than it sounds when an AI agent wrote it from a brief.
- **Separately protected:**
  - the name and logo, by **trademark** (issue 17);
  - the whole package, by **contract**: the Steam Subscriber Agreement bars copying;
  - unreleased material, as confidential information.

**Action (strengthening).**
1. Keep dated records of the owner's creative decisions: briefs, markups, selections, rejections, edits. The repo's history and the docs already do much of this; keep it.
2. Have the owner personally write or rewrite key text (names, the opening, signature lines) and personally mark up or paint over key art (the heroine, the logo, the capsule).
3. Consider a **US copyright registration** for the finished game, disclaiming AI-generated material accurately. Registration is the price of statutory damages in the US.
   - The owner lives in the US, so this is his home system.
   - File within three months of release to keep statutory damages and fees available (17 U.S.C. §412).
   - The plain-words explanation and the records to keep are in issue 5(e).
4. File trademarks for the name and logo (issue 17).

### 17. The name "Survivor Unchained": SHOULD FIX (clearance search)

**What I checked.**
- **Steam store search** (store API, 4 Oct 2026): no title "Survivor Unchained" or "Survivors Unchained".
  - Many titles use "Unchained" (Immortal: Unchained, Age of Conan: Unchained, Abyss Unchained, Unchained Relic, Little King Unchained, Unchained and others).
  - Many use "Survivor(s)" (Vampire Survivors, Deep Rock Galactic: Survivor, STAR WARS Jedi: Survivor and others).
- **A web search** found no game by this name.
- **USPTO:** the public search sits behind an AWS bot challenge that blocks automated searching. I didn't try to get round it, so **no trademark search has been done.**

**Risks to assess.**
- CBS owns well-known SURVIVOR marks (the television format), historically including games.
- "Survivor" is also a genre word, so a combined mark may be registrable, but this needs a professional opinion.
- Both words are weak on their own. The combination and the logo are what would be protected.

**Action.** The lawyer, or the owner through a search firm, runs a knock-out search:
- registers: USPTO, UKIPO, EUIPO (TMview), WIPO Global Brand Database;
- classes: 9 (downloadable game software), 41 (online game services), 28 if merchandise is planned.

Then decide whether to file. Until then, avoid sinking money into the logo.

### 18 and 19. Fonts, Godot and .NET: FINE once issue 4 is done

- **Alegreya, Alegreya Sans, Cinzel:** SIL OFL 1.1. Embedding and selling them in a game is allowed; ship the licence texts. If we ever modify a font, the Reserved Font Name rules apply; we don't.
- **Godot (MIT), Jolt (MIT, inside Godot), .NET 8 (MIT):** ship the notices (issue 4).

### 20. Privacy: FINE

**Evidence.** No data leaves the machine (see the facts). Steam's own data is covered by Steam's privacy policy.

**Action.** No privacy policy is needed for the game as it is. If the game ever adds any of the following, a privacy notice and UK/EU GDPR compliance are needed first:
- crash reporting;
- analytics;
- online features;
- Steamworks features that send data to our own servers;
- a mailing list.

### 21. EULA and refunds: FINE

- Without a game-specific EULA, the **Steam Subscriber Agreement** governs the licence to players: https://store.steampowered.com/subscriber_agreement/
- A custom EULA is optional. It could add a mod policy or a disclaimer, but it isn't needed for launch (lawyer).
- Refunds follow **Steam's standard policy**: within 14 days of purchase and under 2 hours played, at https://store.steampowered.com/steam_refunds/. Developers can't opt out. A game that disappoints in its first two hours will feel it.

### 22. Age ratings: SHOULD FIX (Australia), otherwise FINE

- **Steam self-rating.** Finishing the survey's General Content section "will generate ratings for several regional rating boards".
- **Germany:** since 15 November 2024, games without a valid age rating are hidden from German customers. Steam issues one from the survey. Never enter a USK rating unless the USK itself reviewed this exact build. Source: https://partner.steamgames.com/doc/gettingstarted/contentsurvey/germany
- **Indonesia:** the same mechanism; a missing rating may hide the game. Source: https://partner.steamgames.com/doc/gettingstarted/contentsurvey/indonesia
- **Australia:**
  - Classification law requires games sold in Australia to be classified. Steam's self-rating is not a Classification Board decision.
  - The Classification Board has acted against Refused Classification games on Steam.
  - Our content was R18+ at least because of issue 7. With the buff gone (b47d98ea), MA 15+ may be open to it, subject to the lawyer's view on affection and trust, and to the overall impact being no higher than "strong".
  - Lawyer: whether to obtain a formal classification.
- **UK:** since 2025 Steam asks UK users to verify their age with a credit card before they see mature content (Online Safety Act). This narrows the UK audience for any mature-flagged game.
- **IARC, ESRB, PEGI:** not needed for Steam; Steam is not an IARC storefront. They will be needed for consoles or other stores later.

### 23. Store assets: SHOULD FIX (process)

Steam rules (https://partner.steamgames.com/doc/store/assets/rules and https://partner.steamgames.com/doc/store/review_process):
- "All capsule images (store and library) must have PG-13 appropriate artwork."
- Screenshots must show gameplay only: no concept art or pre-rendered cinematic stills.
- The store page may show only what's in the game at launch.

The heroine's design is built around sex appeal, so the capsule art needs a deliberate PG-13 version. Use a confident pose with nothing beyond what a PG-13 film poster would show.

### 24. EU AI Act Article 50 and similar labelling duties: FINE, with a credits line

- Article 50(4) has applied from 2 August 2026. A deployer of AI that makes a *deep fake* must disclose it. Where the content forms part of an "evidently artistic, creative, satirical, fictional or analogous work", the duty is limited to disclosing that such content exists, "in an appropriate manner that does not hamper the display or enjoyment of the work".
- Our fantasy characters are unlikely to be deep fakes at all: content that "resembles existing persons … and would falsely appear … to be authentic".
- A credits line meets the limited duty in any case. So do the LTX and Krea disclosure terms (issues 8 and 9).
- Source: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50
- **Action:** add a credits line. A draft is in `STEAM_CHECKLIST.md`.

### 25. Payment-processor content rule (July 2025): FINE while non-explicit

In July 2025 Valve added to its rules: "Content that may violate the rules and standards set forth by Steam's payment processors and related card networks and banks … In particular, certain kinds of adult only content." It then retired a number of adult games (onboarding page above).

Our non-explicit content is well clear of this. It becomes a live risk only with Adult Only content (issue 6).

### 26. Claude-written text and code: FINE

- Anthropic's Consumer Terms (effective 8 October 2025): "we assign to you all of our right, title, and interest—if any—in Outputs". Commercial use isn't restricted, apart from building competing AI services and following the usage policy. Source: https://www.anthropic.com/legal/consumer-terms
- If the owner uses an API or commercial plan instead, the Commercial Terms apply; the lawyer can confirm which.
- The dialogue counts as AI narrative for Steam's disclosure (issue 1). Code is an efficiency tool and is outside the disclosure's focus.

### 27. Business set-up: SHOULD FIX (lawyer)

- Steam onboarding needs the legal entity that owns the game, with bank and tax details. You can onboard as a sole proprietor.
- There is a US$100 fee per game, a **21-day wait** after paying it, and a public "coming soon" page for at least two weeks.
- Source: https://partner.steamgames.com/doc/gettingstarted/onboarding

**The owner lives in the United States** (his answer, 4 Oct). So:
- **ElevenLabs:** the non-EEA terms apply (issue 12).
- **Hunyuan3D:** being in the US doesn't remove its bar. It forbids displaying output outside its Territory, and the game sells to the EU and UK (issue 10). We ship none.
- **Copyright and registration:** US law (issues 5(e) and 16).
- **Tax:** Steam's onboarding takes a US person's W-9, with an SSN for a sole proprietor or an EIN for a company.
- **His contracts:** the tools' own choices of law still govern them: Krea's website (California), the Krea 2 model licence (Delaware), Suno and the rest.
- **Still unknown: his state.** It decides how a company is formed and taxed, and which state digital-replica and privacy laws are his home ones.

**Lawyer:** whether to trade as a sole proprietor or through an LLC before signing the Steam Distribution Agreement, for liability. The Krea revenue test counts "affiliated entities", so structure matters.

### 28. Suno for the hymn: FINE on a Pro or Premier plan, with Suno's own download

**Evidence.**
- The owner will make the hymn at Nell's grave ("Lie Down") in Suno.
- Its words are the story lead's, in `godot/data/content`. All other music is synthesised in code.

**The terms** (Suno Terms of Service, effective 3 September 2026; pricing page, read 4 Oct 2026):
- **Ownership on a paid plan:** for Pro and Premier subscribers, "Suno hereby assigns to you all of its right, title and interest in and to any Output … generated from Submissions made by you". Suno adds that it "makes no representation or warranty to you that any copyright will vest in any Output". That matches the Copyright Office's position (issue 16): the song may be unprotected, though nobody else owns it either.
- **The free plan:** "you will only use such Outputs for your lawful, personal and non-commercial purposes". The pricing page says the Free plan has "No commercial rights" and "No monthly song downloads". **So make the hymn on Pro (US$8 a month; 20 downloads a month) or Premier.** Keep the receipt for the month it was made.
- **Commercial use needs a permitted download.**
  - "You may not commercially exploit Output that has not been downloaded by you through an approved channel". Recording or stream-ripping is prohibited.
  - You may "edit, process, or convert the format" of an Output "to the extent such use is incidental". So trimming it and converting it to OGG is fine.
  - Don't remove Suno's "fingerprint, watermark or metadata" in order to conceal provenance.
  - The rights in a download are "perpetual" and survive cancelling the subscription.
- **Remixes are never commercial:** "Nothing in this paragraph permits commercial use of any Remix". Make the hymn as an original generation, not a remix of anyone's song, and don't switch on remixing by others.
- **Suno's licence to what you give it:** a perpetual, irrevocable, sublicensable licence to all Content (the lyrics and the song). This covers improving its models and making Content "available to … other users of the Service as necessary to provide the Service".
  - The lyrics are ours and become partly public through the game anyway, so the risk is low.
  - Don't upload unreleased story material beyond the hymn.
- **Prohibited uses:**
  - no Output that infringes anyone's rights;
  - no impersonating an artist;
  - no using Suno or its Output "to … train other artificial intelligence and machine learning models".
- **"Applicable rights holders may also have the right to collect revenue related to distribution of Outputs on third party platforms."** On YouTube, a trailer carrying the hymn may draw automated claims. Keep the download record to answer them.
- **Suno's own litigation:** the record labels' copyright suits over Suno's training are, by press reports, partly settled (Warner Music Group, November 2025) and partly continuing in 2026. The reports conflict on the details, so the lawyer should check the docket. If a court ever found particular outputs infringing, a song that copies a real track would be the exposure. An original hymn with our own words and no named artist or song in the prompt is the low-risk case.

**Action.**
1. Use a Pro or Premier plan. Generate from our lyrics and a plain style description: no artist or song names.
2. Download through Suno's button. Keep the download, the receipt, the prompt and the date in the ledger.
3. Add music to the Steam AI disclosure and the credits line (`STEAM_CHECKLIST.md` D3 and E).
4. Never use a free-plan or remixed take, or a recording of the stream.

**Sources.**
- https://suno.com/terms
- https://suno.com/pricing
- Press on the litigation (secondary): https://www.digitalmusicnews.com/2026/04/09/suno-universal-music-lawsuit-settlement-impasse/ and https://www.musicbusinessworldwide.com/wheres-v6/

---

## Sources (all read on 4 October 2026 unless stated)

**Valve**
- Content Survey: https://partner.steamgames.com/doc/gettingstarted/contentsurvey
- Germany: https://partner.steamgames.com/doc/gettingstarted/contentsurvey/germany
- Indonesia: https://partner.steamgames.com/doc/gettingstarted/contentsurvey/indonesia
- Onboarding and rules: https://partner.steamgames.com/doc/gettingstarted/onboarding
- Review process: https://partner.steamgames.com/doc/store/review_process
- Age gates: https://partner.steamgames.com/doc/store/age_gate
- Graphical asset rules: https://partner.steamgames.com/doc/store/assets/rules
- AI Content on Steam (10 Jan 2024): https://store.steampowered.com/news/group/4145017/view/3862463747997849618
- Subscriber Agreement: https://store.steampowered.com/subscriber_agreement/
- Refunds: https://store.steampowered.com/steam_refunds/
- Australian age check: https://store.steampowered.com/agecheck/app/2172010/?cc=au

**Governments**
- US Copyright Office AI hub and Part 2 report (29 Jan 2025): https://www.copyright.gov/ai/
- UK *Report on Copyright and Artificial Intelligence* (18 Mar 2026): https://www.gov.uk/government/publications/report-and-impact-assessment-on-copyright-and-artificial-intelligence
- Australia, *Guidelines for the Classification of Computer Games 2023*: https://www.legislation.gov.au/F2023L01424/asmade/text
- EU AI Act Art. 50: https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-50
- US Copyright Office, Circular 1, *Copyright Basics*: https://www.copyright.gov/circs/circ01.pdf
- US Copyright Office fees: https://www.copyright.gov/about/fees.html
- 17 U.S.C. §§102, 201, 408, 411, 412: https://www.law.cornell.edu/uscode/text/17

**Tools**
- Krea 2 licence (22 Jun 2026), on the Hugging Face repo and https://krea.ai/krea-2-licensing; use policy at https://www.krea.ai/krea-2-use-policy
- Krea website: Terms of Use (last updated 20 May 2024), https://www.krea.ai/terms; pricing, https://www.krea.ai/pricing; 3D tool, https://www.krea.ai/3d (read 4 Oct 2026, evening)
- Tencent Hunyuan 3D 2.1 Community License (release date 13 Jun 2025): https://huggingface.co/tencent/Hunyuan3D-2.1/blob/main/LICENSE
- Suno Terms of Service (effective 3 Sep 2026): https://suno.com/terms; pricing, https://suno.com/pricing
- Godot `Engine` class (licence and copyright calls): https://docs.godotengine.org/en/stable/classes/class_engine.html; C# basics: https://docs.godotengine.org/en/stable/tutorials/scripting/c_sharp/c_sharp_basics.html
- LTX-2.x licence (11 Aug 2026): https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x
- NVIDIA Open Model License: https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/
- DINOv3 License: https://github.com/facebookresearch/dinov3
- SAM License: https://github.com/facebookresearch/sam-3d-body
- Hugging Face model cards named in issue 10
- ElevenLabs: the terms, use policy, Voice Library Addendum, sound effects terms and help centre linked in issue 12
- Anthropic Consumer Terms: https://www.anthropic.com/legal/consumer-terms
- MakeHuman export licence (CC0): https://static.makehumancommunity.org/makehuman/faq/can_i_sell_models_created_with_makehuman.html
- Godot licence compliance: https://docs.godotengine.org/en/stable/about/complying_with_licenses.html
- SIL OFL: https://openfontlicense.org/
- CC BY 4.0: https://creativecommons.org/licenses/by/4.0/legalcode.en

**Secondary** (used only where a primary source couldn't be read, and marked where used):
- Generation Amiga on the Jan 2026 AI form;
- Holland & Knight on the *Thaler* cert denial;
- Gaming On Linux on Valve's July 2025 rule;
- Digital Music News and Music Business Worldwide on Suno's litigation (issue 28).

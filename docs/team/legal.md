# Legal and Steam compliance: status

Agent aab20546fe06daa89 (successor to aa12c130ddf4b904c), branch `worktree-agent-aab20546fe06daa89`. Not a lawyer: I find and organise the issues, cite primary sources, and recommend. The owner and the main session decide.

**Handed off (context past 600k, 4 Oct late night): a successor starts from `docs/handoff/legal.md`.** No Godot or GPU turn is held.

**Launch blockers (4):**
- the AI disclosure, at submission;
- the mature survey, waiting on the motion re-measure on the tuck build;
- the licences screen, to be seen in game;
- the boar.

## State (4 October 2026, late evening): re-ruled on the owner's answers, documents only

- **Updated:** `docs/legal/LEGAL_BRIEF.md`, `STEAM_CHECKLIST.md` and `QUESTIONS_FOR_LAWYER.md`. There is a new table, "The owner's answers and what they changed", and a new issue 28 (Suno). There are now 17 questions for the lawyer.
- **Launch blockers now (4):**
  - the AI disclosure (owner, at submission);
  - the mature survey, with the motion check (the tooling is ready; waiting for the outfit import);
  - the licences screen: built and its texts verified; to be seen in game;
  - the boar (replace, or buy on Fab as a stop-gap).
- **Export and placeholder voices: done.** I reviewed the pack listing (`docs/legal/records/RELEASE_PACK_LISTING.txt`, a56abaf3a104be675): nothing excluded ships, and the release build ignores the switches. The Quaternius base bodies, `hero.res` and the voice index ship and are FINE. To do in the GPU check: confirm the Quaternius bodies have no anatomical detail.
- **Cleared:**
  - **The base bodies: kept, with conditions.** They are local Krea 2 Turbo pictures and TRELLIS 2 meshes, and the ComfyUI log agrees. The hero's picture probably used the Civitai LoRA "Mystic XXX" (2728644, alcaitiff), which allows selling images. The evidence is in `docs/legal/records/BODIES_RECORD.md`. Conditions:
    - the owner signs the record;
    - he confirms no real person and no one else's art went into the pictures;
    - the bodies join the Krea footprint.
  - **The Ember Watch:** the owner made it with Claude, and no third party is involved. Records are to be kept (issue 5(e)).
  - **Explicit placeholders:** efc15256 is merged.
  - **"Warmed":** b47d98ea is checked; it resolves the issue once merged.
- **Waiting for the GPU** (the coordinator's limit: no Godot until told):
  - the motion check, including the Warden's cup fix on `outfits-wip@2a856f05`;
  - the performance lead's release export and its `.pck` listing.

## Key decisions (with why)

- **Base bodies: kept, with conditions** (re-ruled after the owner corrected "krea assets" to "we made it in comfyui"). The pictures are under the same Krea 2 licence as the UI art: the US$1M cap and 30-day termination.
- **The boar: before launch too.** Its licensor's own words contradict its CC BY label.
- **The Ember Watch is the owner's.**
  - Copyright needs no registration to exist (17 U.S.C. §408(a)), but covers only human-authored expression (Copyright Office, Part 2).
  - Registering Survivor Unchained within three months of release keeps statutory damages and fees available (§412).
- **"Generated own" replacements (issue 5(g)):**
  - Our own work first; then local MIT-licensed models from inputs we own.
  - Krea 2 adds to the US$1M cap.
  - Never Hunyuan3D, free-plan web tools, or pictures of real people or others' art.
- **Suno: Pro or Premier only, through Suno's own download.** Free-plan output is non-commercial, and remixes never are.
- **US residence:** ElevenLabs' non-EEA terms; a W-9 for Steam; his state is still to be given.
- **Survey:** General Mature, Frequent Violence or Gore, and Some Nudity or Sexual Content; not Adult Only. Australia's MA 15+ is possible once the buff is gone.

## Next (exact)

0. **The motion check, reworked to the main session's four points** (tools in `tools/legal/motioncheck`):
   - a narrow genital strip (the vulva's footprint, ±1.2 cm);
   - areola margins per outfit, with where on the rim;
   - crops labelled as a test tint;
   - codes drawn last in the skin shader, so they show on tucked skin.

   **On build 854b927e:** the Warden's cup is fixed, and no areola shows in the Warden's or Arcanist's clips. My first, wide crotch reading is withdrawn.

   **Next:**
   - test the new codes (calibration, false positives; queued for a Godot turn);
   - then, on the main session's next build (the skin tuck), run every outfit and send the margins.

   **Heavy work takes turns:** `tools/turn.py take godot "legal: …"`, and give the turn back the moment the batch ends.
1. **When the coordinator frees the GPU:**
   - The motion check: `scratchpad/legal/motion.sh` with the clip loop changed to dash, leap, death, death_back, hit, cast_bolt, cast_flick, cast_raise, throw, crossbow_shoot, the swing clips (list them first from `res://art/anim/heroine.res`), the sits and the breaks. All four outfits, jiggle on.
   - Then the cinematic poses (`--cine`) and the creation poses.
   - Re-check the Warden's left cup on `outfits-wip` once the main session builds it.
2. Review the performance lead's pack listing.
3. Send the licences spec (brief issue 4) to the UI design successor once the roster names one.
4. Review `docs/art/MODELS_TO_MAKE.md` against issue 5(g) when it lands.
6. See the credits screen in game when the GPU is free, and check the UI design lead's next `CREDITS.md` pass against `STEAM_CHECKLIST.md` E.
5. **Standing check of recent additions:**
   - the skills lead's "filmed clips" (0d2e4a0b);
   - arena art's concepts;
   - the cinematics gestures;
   - `tools/uiforge/logo.py`.

## Blockers on me

- The owner's state of residence and his business structure (lawyer questions 12 and 2).
- A person must run the USPTO search (it sits behind a bot challenge).

## Notes for other areas

- **Main session and models planner:** issue 5(g) gives the rules for replacements. Hunyuan3D is never to be used, including on Krea's website. Every replacement needs a ledger line.
- **Owner:**
  - Keep the Ember Watch records listed in issue 5(e), and sign the short authorship statement once the lawyer drafts it.
  - Look in your email for Krea receipts covering the days the bodies were made.
  - Make the hymn on Suno Pro or Premier, and download it with Suno's button.
- **Performance (a7145e18b3eb78294):** the export spec is in your messages. Send me the zip-pack listing.
- **UI design successor:** the licences screen is first in `docs/handoff/ui_design.md`; the spec is in brief issue 4. Use `Engine.GetLicenseText()` and `GetCopyrightInfo()` for Godot's part.
- **Voice (successor):** the ElevenLabs rules are in `docs/handoff/voice.md`. The owner is in the US, so the non-EEA terms apply.
- **UI art:** the side-by-side icon check against Diablo IV and Hades is still due before launch.
- **Anyone adding a tool or model:** send me its licence link.

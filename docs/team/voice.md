# Voice: status

Agent a2da9a388ceb1b987, branch `worktree-agent-a2da9a388ceb1b987`.

## Where it stands

- **The bar is unmet.** The owner: "way too AI"; the bar is cinematic, movie voice-actor quality. No line is in the game until a take passes the owner's ear.
- **The game is ready for takes.** Playback with subtitle sync, ducking, the volume slider and voices on/off, barks, and the tests are all in. Each take is tied to its line's words by a hash.
- **The pipeline:** `tools/vo/` (manifest, direction, casting, mix). All 35 parts have a designed voice in `tools/vo/refs/`; some are placeholders (`docs/VO_CAST.md`).
- **First shoot-out:** five hard lines, 69 takes, in `docs/voice/samples/`. Page: https://claude.ai/artifact/T1Bns481cT4bLCAqB6Sipx. Acting first and converting the voice moves most like a person, but the actor models are American. Reads that keep the English accent move like readers.
- **In progress: Voicebox and the 2026 field.** Voicebox runs headless (`~/vo-tools/scripts/voicebox_serve.sh`, port 17493). The client is `tools/vo/voicebox.py`, tested and documented in `docs/VOICES.md`. Being shot out now:
  - Voicebox's engines (Chatterbox Turbo with tags, Qwen3, Chatterbox, LuxTTS, TADA), cloning the cast voice and cloning an acted take;
  - Maya1 (designed British voices with emotion tags);
  - Dia2.

## Decisions

- **VoxCPM2 makes the cast voices.** It is the only local model that holds English accents and can be used commercially.
- **Designed voices only, never a real person.** Only clips we have the right to may be cloned.
- **Nothing ships on numbers alone.** I can measure the tells of generated speech, but only the owner's ear can pass a take.
- **One voice system in the game**, not the cloud branch's second one. Its direction notes were imported.
- **The writer's notes are the direction.** They live in the direction files as `wants`, `hides` and `beats`. The narrator never emotes; quoted words go to their speaker; Vonnra's name is spliced in.

## Next

1. Pack the new shoot-out takes and rank them honestly.
2. Put the verdict and the three takes to hear first at the top of the page.
3. If a method wins: wire it into `produce.py`, then record the cinematic openings and the most-heard barks first, keeping the old route as fallback.
4. Fold in the story lead's notes on Chid, Maeca and the Wayfinder.

## Blockers and notes for others

- **For the owner:** registering Voicebox's MCP server is a config change, so it is yours to approve; the snippet is in `docs/VOICES.md`.
- **Routes beyond local models, with costs:** in `docs/voice/samples/README.md`.
- **GPU:** I release my models between runs (`python tools/vo/voicebox.py free`).
- **Hugging Face downloads need two variables:** `HF_TOKEN_PATH` set to a missing file, and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1`. Without them the stored token file is refused.
- **Story:** send directed reads for notes to a7622ae77d19e31dc. `python tools/vo/reads.py <id prefix>` prints them.

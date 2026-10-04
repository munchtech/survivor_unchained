# Voice: status

Agent a2da9a388ceb1b987, branch `worktree-agent-a2da9a388ceb1b987`. Paused for the owner's usage limit, mid round two of the shoot-out. Nothing of mine is running and none of my models are loaded on the GPU.

## Where it stands

- **The bar is unmet.** The owner: "way too AI"; the bar is cinematic, movie voice-actor quality. No line is in the game until a take passes the owner's ear.
- **The game is ready for takes:** playback, subtitle sync, ducking, settings, barks, and hash-checked tests.
- **The cast:** all 35 parts have a designed voice (`tools/vo/refs/`, `docs/VO_CAST.md`).
- **First shoot-out:** 69 takes in `docs/voice/samples/`. Page: https://claude.ai/artifact/T1Bns481cT4bLCAqB6Sipx.
- **Voicebox:** installed from source at `~/vo-tools/voicebox-src`, venv `~/vo-tools/voicebox`; it runs headless (`~/vo-tools/scripts/voicebox_serve.sh`).
  - Engines downloaded: Qwen3 1.7B, Chatterbox, Chatterbox Turbo, LuxTTS, TADA 1B, Kokoro.
  - Client: `tools/vo/voicebox.py`, tested (`python -m unittest discover -s tools/vo/tests`) and documented in `docs/VOICES.md` with the MCP snippet for the owner to approve.

## Round two of the shoot-out: state

Raw takes live in `~/vo-tools/shootout/raw/<line>/`. The runners skip takes that already exist, so rerunning picks up where this stopped.

| Step | State |
|---|---|
| Maya1: 20 takes, plus Seed-VC conversions `maya-vc` and `maya-vcf0` | done |
| Voicebox (`run_voicebox.py`): engines × {cast, acted} × 3 seeds | **part done**: line 1 (turbo, qwen, chatterbox) only |
| Dia2 (`run_dia2.py`; env `~/vo-tools/dia2-main/.venv`), then `run_vc.py dia2-free` | not run |
| VibeVoice 1.5B (`run_vibevoice.py`; env `~/vo-tools/vibevoice`) | installed, not run |
| `pack.py`, then the page with verdict and top 3 | not run |

Early numbers, unpacked (`tools/vo/shootout/peek.py`):
- **Maya1 → Seed-VC (`maya-vc`) is the first take heard as England (1.0) that also moves:** pace change 0.22, 2 breaths, words right, naturalness 3.45.
- **Maya1 alone** is British and clean (naturalness 4.4), but reads (pace 0.05–0.12).
- **Voicebox Qwen** is British and clean, but reads (pace 0.04).
- **Chatterbox Turbo** stops at a tag placed mid-line. `turbo_text` now keeps only tags at either end. **Delete the `vb_turbo*` takes for lines 1 and 2 before rerunning.**

## Next

1. Free ComfyUI's VRAM (`POST /free`) if it holds memory, then run `bash ~/vo-tools/scripts/round2.sh`. Remove its Maya1 wait, which is already satisfied, and start the Voicebox server first. Then run `round3.sh` (VibeVoice and the pack).
2. Rank honestly (`table.py`). Fill `docs/voice/samples/README.md`, put the verdict and the 3 takes to hear first at the top of the page (`page.py`, `page_template.html`), and republish the same artifact.
3. If a method wins (`maya-vc` is the lead to check), wire it into `produce.py`. Then record the cinematic openings (Prologue `say.*`) and the most-heard barks first, keeping `cont` as the fallback.
4. Survey write-up in `docs/VO_RESEARCH.md`, covering 2026, round two:
   - **Run:** Voicebox's engines, Maya1, Dia2, VibeVoice.
   - **Not run:**
     - MisoTTS 8B: too big for a shared 16 GB card.
     - Higgs v2: 24 GB recommended, and a community licence.
     - Step-Audio-EditX (Apache 2.0, edits the emotion of an existing take): 12–16 GB, Linux-tested. It is the next lever to try on our accented takes.
   - **The owner's Reddit list** could not be read: Reddit blocks this machine ("blocked by network security") and the browser pane refuses reddit.com. Ask the owner to paste it.
5. Fold `tools/vo/direction/PENDING.md` into the direction files once the story lead's rewrite (`worktree-agent-a7622ae77d19e31dc` @ 3f14126) reaches the integration branch. `lines.py` must also learn `bark.<npc>.said.<i>`.
6. Send the story lead (a7622ae77d19e31dc) the next batch: Vonnra's first meeting and the fortune, Harlan and Jory, and the opening cinematics.

## Decisions

- **VoxCPM2 designs the cast voices.** It is the only local model that holds English accents and can be used commercially.
- **Designed voices only, never a real person.** Only clips we have the right to may be cloned.
- **Nothing ships on numbers.** Measurements show the tells of generated speech; only the owner's ear passes a take.
- **One voice system in the game.**
- **The writer's notes are the direction** (`wants`, `hides`, `beats`):
  - the narrator never emotes;
  - quoted words go to their speaker;
  - Vonnra's name is spliced in, never "traveller".

## For the owner, and notes for others

- **To approve or decide:**
  - The Voicebox MCP registration (`docs/VOICES.md`).
  - The routes beyond local models, with costs (`docs/voice/samples/README.md`).
  - The hymn (`cin_iron_marker`) must be sung, with Vonnra's alto truly in tune, so it needs a singer we have the rights to, or a licensed singing synth.
- **Hugging Face downloads:** set `HF_TOKEN_PATH` to a missing file and `HF_HUB_DISABLE_IMPLICIT_TOKEN=1`; without them the stored token file is refused.
- **Bash scripts:** `TaskStop` on a bash script leaves its Python child running; kill the child too.

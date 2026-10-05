# Asset provenance: everything in Survivor Unchained that we didn't make

Audit of 2026-10-04 by the asset provenance auditor (agent a80ff0c7fd988b178), on branch `worktree-agent-a80ff0c7fd988b178`. This is an inventory only: nothing has been removed or replaced. The owner decides; the order of work is in `docs/legal/REPLACEMENT_PLAN.md`, and the credits are in `public/assets/CREDITS.md`.

The owner's goal: identify everything we use that isn't ours (that we didn't make, or that could get us in trouble if an attribution were missed), "with the goal of eventually removing anything not ours", so the game can be sold on Steam with little or no issue.

## How to read this

- **Ships** means it is inside the Steam build, the Godot export in `godot/export_presets.cfg`. That export uses `export_filter="all_resources"`, so every file Godot imports ships, used or not. `godot/assets` is a link to `public/assets`, so the web game's assets ship too, including git-ignored files on the exporting machine (`public/assets/env/polyhaven/`). Text files (`.txt`, `.md`) are not resources and do not ship. The older web build (`src/`, packaged by Electron) is a separate product and is marked as such.
- **Risk**:
  - **none**: our own work, with no third-party terms attached.
  - **low**: a permissive licence, checked at the source, whose obligations are met (or met by the corrected `CREDITS.md`).
  - **medium**: either an obligation not yet met in the build, a third party's design inside a licensed asset, or terms we must keep satisfying.
  - **high**: terms that conflict or can stop sales (a revenue cap, revocation), or a widely seen asset whose origin is unknown.
  - **UNKNOWN**: we could not establish the source or the licence. Treat these as high until the owner answers. No licence has been guessed.
- Licences were checked on 2026-10-04 at the asset sites' own pages and APIs. Sources:
  - Poly Haven: 78 ids through `api.polyhaven.com`.
  - ambientCG: 10 ids through its v2 API.
  - Sketchfab: 15 models through `api.sketchfab.com`, including their descriptions.
  - Hugging Face model cards, GitHub licence files and the licence PDFs embedded in the models on this PC.

## Summary

> **Update, 4 October 2026 (evening), by the legal lead (aab20546fe06daa89), from the owner's answers.** The bodies (PE-05, PE-06, PE-09) were made locally: Krea 2 Turbo pictures, TRELLIS 2 meshes, in our ComfyUI. They are now low risk with conditions, and part of the Krea footprint (AI-01). The Ember Watch (DA-02) is the owner's. The Mystic XXX LoRA (AI-15) is identified, and commercial use is allowed. The counts below are as audited; the rulings are in `docs/legal/LEGAL_BRIEF.md` issue 5.

### Counts by kind and risk (rows in the inventory below)

| Kind | none | low | medium | high | UNKNOWN | Rows |
|---|---|---|---|---|---|---|
| People and bodies (PE) | 3 | 5 | 0 | 1 | 3 | 12 |
| Creatures (CR) | 0 | 2 | 0 | 1 | 0 | 3 |
| Weapons (WE) | 0 | 9 | 2 | 0 | 0 | 11 |
| Environment models and kits (EN) | 2 | 5 | 0 | 0 | 0 | 7 |
| Textures, materials, HDRIs (TX) | 1 | 6 | 0 | 0 | 0 | 7 |
| Interface art, icons, fonts (UI) | 3 | 0 | 1 | 3 | 1 | 8 |
| Effects (FX) | 1 | 1 | 1 | 1 | 0 | 4 |
| Animation (AN) | 1 | 4 | 0 | 0 | 0 | 5 |
| Audio and voice (AU) | 1 | 3 | 1 | 0 | 0 | 5 |
| AI generators (AI) | 0 | 10 | 1 | 2 | 4 | 17 |
| Code, engine, libraries (CO) | 1 | 4 | 2 | 0 | 0 | 7 |
| Data and writing (DA) | 2 | 1 | 0 | 0 | 2 | 5 |
| Build and export (BU) | 0 | 1 | 2 | 0 | 0 | 3 |
| On disk or in the repo, not shipped (WL) | 3 | 3 | 0 | 1 | 1 | 8 |
| **Total** | **18** | **54** | **10** | **9** | **11** | **102** |

The 9 high rows are PE-08, CR-02, UI-01, UI-02, UI-03, FX-03, AI-01, AI-13 and WL-04. The 11 UNKNOWN rows are PE-05, PE-06, PE-09, UI-05, AI-04, AI-14, AI-15, AI-17, DA-02, DA-03 and WL-02.

> **Owner's answers (4 October 2026; see docs/legal/LEGAL_BRIEF.md 5(e) and 5(g)):**
> - **The bodies (PE-05, PE-06, PE-09):** "they were from krea assets that have since been deleted". The plan and input pictures can't be shown, and Krea's 3D tool defaults to Hunyuan3D 2.1. **Replace before launch** (docs/art/MODELS_TO_MAKE.md).
> - **The Ember Watch (DA-02):** the owner's own, made with Claude; no third party. **Cleared** (LEGAL_BRIEF 5(e)).
> - **Everything not ours** is to be replaced over time. The owner lives in the United States.

By file count (tracked files, without Godot's `.import` files):

- 1,274 shipped files come from third-party asset sources:

  | Source | Files |
  |---|---|
  | Quaternius | 859 |
  | Kenney | 184 |
  | Poly Haven | 125 (plus 180 git-ignored originals on the owner's disk) |
  | ambientCG | 52 |
  | KayKit | 16 (and inside the 3 zone landmark files) |
  | Sketchfab | 16 |
  | Fonts | 13 |
  | OpenGameArt | 5 |
  | MakeHuman | 4 (the rest is inside the heroes' `.glb` files) |

- 323 shipped files are AI-made or carry AI paint. The full list is in the appendix:
  - Krea 2: 225 UI files, 14 ground-mark files, plus 5 face and iris files and models.
  - LTX: 28 flipbook files (14 atlases and their `.json`) and 5 sounds.
  - 19 voice placeholders.
  - 26 cameo renders that carry her Krea face.
  - Kimodo: 10 clips in `folk.res`.

### The top risks, in order

1. **The boar (CR-02), high.**
   - Sketchfab labels it CC BY 4.0, but its description says: "This version is for personal use only. Commercial use is allowed only for versions purchased on Fab or Patreon."
   - The licensor's own words contradict the label. The legal lead has ruled it a blocker.
2. **The heroine's body (PE-06), and with it the cameos and her outfits' fit, UNKNOWN.**
   - She was made from the owner's "234.glb", and what generated it is not recorded.
   - Its texture was JPEG. That points away from our ComfyUI TRELLIS 2 saves (three PNGs) and make3d's Hunyuan3D-2 output (PNG), unless it was saved again in another tool; it doesn't rule them out.
   - The owner's Desktop held a Meshy image-to-model result at the time.
   - The input picture is unrecorded too. The owner's reference sheet is a render-like red-haired woman in a bodysuit, also of unknown origin.
   - If it came from Hunyuan3D-2, that licence excludes the EU, UK and South Korea. If it came from Meshy, Meshy's plan terms decide who owns it. If the picture was someone else's art or a real person, the body must be remade.
3. **Krea 2 (AI-01), high (business).** Almost all the interface art, the 117 colour icons, the 48 item icons, the ground marks and both heroes' face paint were painted by Krea 2 under the Krea 2 Community License Agreement (v1, 22 June 2026):
   - Commercial use of outputs is permitted only while total company-wide revenue is under US$1,000,000 a year, trailing twelve months, all sources (§2.3).
   - Krea may end the agreement for any reason on 30 days' notice (§9.2).
   - Launch is possible. But success, or a notice from Krea, would force a licence purchase or a replacement of every Krea asset.
4. **The male hero's body (PE-09) and the older woman body (PE-05), UNKNOWN.** Both come from ComfyUI 3D models of unrecorded input pictures.
5. **Two weapons modelled from other artists' concept art (WE-01, WE-10), medium.**
   - The Chevalier Sword is "based on the concept by Guillem Daudén" and was made as a Blade and Sorcery mod.
   - The Medieval Shield is "based on the concept by Artyom Vlaskin".
   - A modeller's CC BY grant can't license someone else's design.
6. **No licence notices ship (BU-01), medium, easy to fix.** Missing are:
   - Godot's MIT notice and its third-party `COPYRIGHT.txt`;
   - the .NET runtime notices;
   - the three OFL texts;
   - the CC BY notices.

   The in-game Credits (`godot/src/Ui/Front.cs`) are out of date. They name "Peter Nox" correctly, but they describe the woman's body wrongly. They omit KayKit, MakeHuman, Mixamo, Kimodo, ambientCG and the AI tools, and they have no licence links.
7. **Unused third-party files ship (BU-02), medium.** `all_resources` exports everything imported. That includes the KayKit characters and props, the anime body (CC BY), the older woman body (UNKNOWN), and 180 git-ignored Poly Haven originals on the owner's disk. The list is in BU-02.
8. **LTX 2.5 outputs (FX-02, AU-03), medium.**
   - They are free to use under US$10M revenue.
   - The acceptable-use terms require disclosing that content is machine generated, and forbid removing watermarking or provenance.
9. **The Ember Watch itself (DA-02) and its character names (DA-03), UNKNOWN.**
   - The world, lore, weapons and combat were ported from `stevenrogerino/wowsurvivors`, a repo under another account that munchtech can't push to. **Answered 4 Oct:** the owner made it, with Claude, so it is no longer a blocker (brief issue 5(e)).
   - Maeca Barefoot, Vonnra Hydrocheck, Rav, Chid and Keegan were "always the project's own characters" according to The Ember Watch's NOTICE. The owner should confirm none is a real person's name or handle.
10. **Warcraft-flavoured skill names (DA-04), low.** Starfall, "moonfire" and "fan of knives" sit on The Ember Watch's own banned list, which also includes Consecration and Whirlwind.

### Questions only the owner can answer (the UNKNOWNs)

1. **Answered (4 Oct):** Krea 2 Turbo made the picture and TRELLIS 2 the mesh, both in our ComfyUI (`docs/legal/records/BODIES_RECORD.md`). Asked: what made `234.glb` (the heroine's body): Meshy, TRELLIS 2, Hunyuan3D-2 or something else? Which plan or account was it on, and from what picture?
   - If Meshy: were you on a free or a paid plan? Meshy's pricing page says paid-plan users own their assets, while free-plan outputs are CC BY 4.0 with credit to Meshy.
   - Either plan allows commercial use, but only if the input picture was ours.
2. Where did the reference sheet you gave on 1 October come from (red hair, a black bodysuit, three views)? Was it AI from your own prompt (which tool), a render of purchased content (for example Daz 3D), or someone else's picture?
3. **Answered (4 Oct):** a Krea 2 Turbo picture made in our ComfyUI. Asked: what picture was `ComfyUI_00008.glb` (the male hero, TRELLIS 2) made from, and the earlier woman figure (`woman.glb`)?
4. Is any Ember Watch character named after a real person: a friend, a guildmate, a streamer or a handle?
5. **Answered (4 Oct):** the owner made it, with Claude; no third party (brief issue 5(e)). Asked: do you hold the rights to The Ember Watch (`stevenrogerino/wowsurvivors`), which Survivor Unchained's world, lore and weapons were ported from?
6. **Partly answered (4 Oct):** the log suggests it made the hero's picture; the LoRA is identified, and its creator allows commercial use (AI-15). Asked: did you use the `MysticXXX_KREA2_v1` LoRA (on this PC, not used by any repo tool) for any picture we built from?
7. The `fantasy` sound folder from kmontesdev's "CC0" pack carries Pro Tools metadata with library-style tags and 2014 dates. It isn't shipped; do you know where it came from?

### Made with AI: what, by which model and tool

| Model (tool) | Licence | What it made that ships |
|---|---|---|
| Krea 2 turbo + darkbrush LoRA, with Qwen3-VL 4B text encoder and Qwen-Image VAE (local ComfyUI; `tools/uiforge`, `tools/comfy/ui_art.py`, `marks.py`, `tools/assets/heroine_face.py`, `heroine_eyes.py`, `hero_male_face.py`) | Krea 2 Community License; Qwen parts Apache-2.0 | 225 UI files, 7 ground marks, the heroine's and hero's face paint and iris |
| LTX 2.5 22B distilled, with Gemma 4 12B text encoder and LTX upscaler (local ComfyUI; `tools/comfy/fx_clips.py`, `sfx_clips.py`) | LTX-2.x Community License Agreement; Gemma 4 Apache-2.0 | 14 effect flipbooks, 5 sound takes |
| TRELLIS 2 with DINOv3 ViT-L and MoGe 2 (local ComfyUI, `graphs/trellis_img.json`) | MIT; DINOv3 License; MIT | The hero's body sculpt; possibly the older woman's figure |
| Unknown (Meshy, TRELLIS 2 or Hunyuan3D-2: see PE-06) | UNKNOWN | The heroine's body |
| Reallusion AccuRIG | Reallusion EULA (own content may be rigged and used commercially) | The heroine's and hero's skin weights (folded onto our skeleton) |
| MakeHuman via MPFB2 | Assets CC0, code AGPL/GPL (not shipped) | The heroine's and hero's heads, eyes, brows, lashes, teeth and tongue |
| NVIDIA Kimodo-SOMA-RP (LLM2Vec on Llama 3 8B Instruct as its text encoder) | NVIDIA Open Model License; Llama 3 Community License | 10 townsfolk clips |
| Maya1 → Seed-VC, in voices designed by VoxCPM2; Whisper checks the words | Apache-2.0; GPL-3.0 (code); Apache-2.0; MIT | 19 placeholder voice takes (synthetic voices, none cloned) |
| BiRefNet (local ComfyUI) | MIT | UI cut-outs (masks only) |
| Claude (Anthropic), through Claude Code | Anthropic's terms assign outputs to the customer | The game's code, its writing and dialogue, and every tool in `tools/` |

Not shipped, for completeness:

- Krea 2 Large through Comfy's paid API node: concept art only. Most jobs were rejected by Krea's moderation, and none feeds the game.
- Pixal3D: experiments only.
- SAM 3D Body: a pipeline test on Pexels footage.
- The voice shoot-out models: Chatterbox, IndexTTS, Dia, Orpheus, F5, Kokoro, Qwen3-TTS.
- Hunyuan3D-2: make3d tests.
- MiniMax H3: installed, unused.

ElevenLabs is planned for the final voices.

## Licence terms, quoted briefly

| Source | Terms (short quote) | Link |
|---|---|---|
| Poly Haven | "All assets on this site are licensed as CC0"; no credit required | https://polyhaven.com/license |
| ambientCG | "Creative Commons CC0 1.0 Universal License"; attribution appreciated, not required | https://docs.ambientcg.com/license/ |
| Quaternius (all seven packs used) | "Free to use in personal, educational and commercial projects. (CC0 License)", on each pack's page, for every version | https://quaternius.itch.io/universal-animation-library (and each pack) |
| KayKit (five packs) | "Free for personal and commercial use, no attribution required. (CC0 Licensed)" | https://github.com/KayKit-Game-Assets |
| Kenney (four packs) | Licence line on each page: "Creative Commons CC0" | https://kenney.nl/assets/particle-pack |
| OpenGameArt recordings | Each entry's licence field: "CC0" | e.g. https://opengameart.org/content/park-ambiences |
| Sketchfab CC BY models | "Author must be credited. Commercial use is allowed." (API licence requirements) | https://sketchfab.com/licenses |
| CC BY 4.0 | Keep the creator's name, the notices and a link; "indicate if You modified" it (§3(a)) | https://creativecommons.org/licenses/by/4.0/legalcode.en |
| 100STYLE | "Creative Commons Attribution 4.0 International" | https://zenodo.org/records/8127870 |
| MakeHuman 1.2+ and MPFB2 | Assets "released under CC0 1.0 Universal"; exports are "your data" | https://github.com/makehumancommunity/makehuman/blob/master/LICENSE.md |
| Mixamo | Free for commercial use; no redistributing raw character or animation files | https://community.adobe.com/questions-696/mixamo-faq-licensing-royalties-ownership-eula-and-tos-589400 |
| NVIDIA Open Model License (Kimodo) | "NVIDIA claims no ownership rights in outputs." | https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-open-model-license/ |
| Krea 2 Community License | Commercial use of outputs only under "$1,000,000 USD" annual revenue (§2.3); 30 days' notice to terminate (§9.2) | https://huggingface.co/Comfy-Org/Krea-2/blob/main/LICENSE.pdf |
| LTX-2.x Community License | Paid licence for entities with "annual revenues of at least $10,000,000" (§2.1); "claims no rights in the Output" (§5) | https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2_x |
| DINOv3 License (inside TRELLIS 2) | Commercial use allowed; "Built with DINOv3" display when distributing DINO materials | https://ai.meta.com/resources/models-and-libraries/dinov3-license/ |
| SIL OFL 1.1 (fonts) | Each copy must contain "the above copyright notice and this license" | `godot/art/fonts/OFL-*.txt` |
| Godot (MIT) | "include the license text somewhere in your game"; also ship Godot's `COPYRIGHT.txt` | https://docs.godotengine.org/en/stable/about/complying_with_licenses.html |
| Reallusion AccuRIG | Own content rigged in AccuRIG may be used commercially; Reallusion's own content may not | https://discussions.reallusion.com/t/question-about-accurig-2s-eula/15034 |
| Meshy (if it made PE-06) | Premium: "you own all assets you create with Meshy"; free: "a CC BY 4.0 license" | https://www.meshy.ai/pricing |
| Steam | Pre-generated AI content "that ships with your game" must be disclosed | https://partner.steamgames.com/doc/gettingstarted/contentsurvey |
| Tencent Hunyuan 3D 2.0 (make3d only) | Not licensed in the EU, UK or South Korea (as recorded by `tools/make3d/backends.py`) | https://huggingface.co/tencent/Hunyuan3D-2/blob/main/LICENSE.txt |

## Inventory

Columns: path(s), what it is, source, licence, attribution required, ships, risk (and why), replacement path (what we'd make ourselves, how, and which lead).

### People and bodies (PE)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| PE-01 | `public/assets/people/Superhero_*_FullBody.*`, `Eyebrows_*`, `Hair_*` (Beard, Buns, Buzzed, BuzzedFemale, Long, SimpleParted), `T_Superhero_*`, `T_Regular_*`, `T_Eye_*`, `T_Hair_*`; `godot/art/srgb/people/*` | Townsfolk's and the kit man's bodies, brows and hair (the Risen are dressed from them too) | Quaternius, Universal Base Characters, https://quaternius.itch.io/universal-base-characters (`tools/assets/people.py`) | CC0 1.0 | No (courtesy credit given) | Yes | low: CC0 checked on the pack page | Folk bodies from MakeHuman's CC0 base through MPFB (`tools/assets/heroes.py` already builds them), dressed by our own outfit pipeline. Male hero lead and heroine face lead |
| PE-02 | `public/assets/people/{Male,Female}_{Peasant,Ranger}_*`, `T_Peasant_*`, `T_Ranger_*` | Folk clothes: peasant, ranger, hoods, pauldrons | Quaternius, Modular Character Outfits – Fantasy, https://quaternius.itch.io/modular-character-outfits-fantasy | CC0 1.0 | No | Yes | low | Our own clothes, made in Blender the way `heroine_outfits.py` makes hers, on our own folk bodies. Main session (outfits) and male hero lead |
| PE-03 | `godot/art/people/her_Hair_{Buns,BuzzedFemale,Long}.glb` | Quaternius hairstyles refitted to the anime body's head (`anime_hair.py`) | Quaternius, Universal Base Characters | CC0 1.0 | No | Yes (only the `--body anime` path uses them) | low | Drop from the build with PE-04; her own hair cards (PE-11) replace them |
| PE-04 | `godot/art/people/anime_female.glb` | A woman's body, reachable only with `--body anime` | "Genshin Style Anime Female Base Mesh For Blender" by David Onizaki (donizaki), https://sketchfab.com/3d-models/genshin-style-anime-female-base-mesh-for-blender-c2d6727e8c9742feb9a4a3bccac6e0e0; rigged by `anime_female.py` | CC BY 4.0 (API) | Yes | Yes (unused in play) | low on licence: checked, and the title names another company's game only as a style. The legal lead asks that it be removed anyway: an unused, youthful-styled body in an adult game is a needless ratings risk | Remove from the build (BU-02), with `her_Hair_*.glb` and the `--body anime` path; nothing to make |
| PE-05 | `godot/art/people/woman.glb`, `woman_mask.png` | The older woman survivor (`--body woman`, or when `heroine.glb` is missing) | "A figure made in ComfyUI and given to the game by its owner" (commit 2798a4e). The generator and input picture are not recorded. Skeleton joints fitted from PE-04 and the Quaternius skeleton | UNKNOWN (figure); CC0 (skeleton) | Unknown | Yes (fallback only) | UNKNOWN: the figure's origin is not established Excluded from release builds (8a770667), so nothing to clear | Remove from the build (BU-02); the heroine supersedes it |
| PE-06 | `godot/art/people/heroine.glb` (body mesh and `heroine_body_paint`) | The heroine's body: every woman survivor, in play and in creation | The owner's figure "234.glb" (commits da12945, b8d025c), rigged by Reallusion AccuRIG and laid on the Quaternius UAL skeleton by `build_heroine.py`. The generator is not recorded: the texture was JPEG, unlike ComfyUI's TRELLIS 2 saves (3 × PNG) and make3d's Hunyuan3D-2 (PNG), and the owner's Desktop held a Meshy image-to-model result then. The input picture is not recorded; the owner's reference sheet (`images/1.webp` in the session) is of unknown origin. **Answered (owner, 4 Oct):** the picture was made in our own ComfyUI with Krea 2 Turbo, and the mesh by TRELLIS 2 there; no web tool, no Hunyuan. The record: `docs/legal/records/BODIES_RECORD.md` | Krea 2 Community License (the picture, AI-01); MIT (TRELLIS 2, the mesh) | No | Yes, by default | low, with conditions (legal, 4 Oct): the owner signs the record and confirms no real person or others' art went into the picture; the body joins the Krea footprint (AI-01) | If the chain can't be shown clean (our own prompt in a tool whose terms give us the output, no real person, no third-party art): rebuild her on MakeHuman's CC0 body (`wrap_sculpt.py` already shrink-wraps MakeHuman onto a sculpt), sculpted to the brief, then refit the outfits. Heroine face lead with the main session |
| PE-07 | `heroine.glb` head and parts; `godot/art/people/head_tex/{green_eye.png, eyelashes03.png, teeth.png, tongue01_diffuse.png, heroine_lashes.png, heroine_graft.jpg}` | Her head, eyes, brows, lashes, teeth and tongue; the graft is MakeHuman skin where the sculpt had hair | MakeHuman system assets (base mesh, targets, high-poly eyes, eyebrow010, eyelashes03, teeth_base, tongue01) through MPFB2; skin "Light skin female ginger" by MargaretToigo, http://www.makehumancommunity.org/node/1130 | CC0 1.0 (asset headers; MPFB pack index `skins01_cc0`, `makehuman_system_assets_cc0`) | No | Yes | low | Keep (CC0), or paint our own skin over the same UVs. Heroine face lead |
| PE-08 | `head_tex/heroine_head.jpg`, `heroine_eye.png`, `heroine_iris.png` (and the copies inside `heroine.glb`) | Her face paint (skin, brows, lips), her eye whites with an iris, and the iris alone | Krea 2 turbo painting over flat renders of her MakeHuman head (`heroine_face.py`, `heroine_eyes.py`), laid over the CC0 skin and MakeHuman's whites | Krea 2 Community License (AI-01) over CC0 | No | Yes | high (business): AI-01 | Hand-paint her face from the CC0 skin (Krita or Substance), or use photographic skin from our own shoot with a signed model release. Draw the iris procedurally (the guide in `heroine_eyes.py` is already drawn). Heroine face lead |
| PE-09 | `godot/art/people/hero.glb` | The male hero (behind `--body hero` until his outfits exist) | Body: TRELLIS 2 sculpt `ComfyUI_00008.glb` from an unrecorded picture, rigged by AccuRIG. Head: MakeHuman (young_caucasian_male skin, eyebrow001, eyelashes01, brown eye; CC0). Face painted by Krea 2 (`hero_male_face.py`). **Answered (owner, 4 Oct):** the picture came from Krea 2 Turbo in our ComfyUI, probably with the Civitai LoRA in AI-15 (the log shows 256 LoRA patches); TRELLIS 2 ran at 00:28 and the file landed at 00:38 on 4 Oct. The record: `docs/legal/records/BODIES_RECORD.md` | Body: Krea 2 Community License (the picture) and MIT (TRELLIS 2); head CC0; face under the Krea licence | No | Not in release builds until his base garment exists (export exclude, 8a770667) | low, with conditions (body, as PE-06); high, business (Krea face and picture: AI-01) | As PE-06 and PE-08. Male hero lead |
| PE-10 | `godot/art/people/heroine_outfit_*.gltf/.bin`, `outfit_materials.json` | Her four outfits | Modelled in code in Blender (`heroine_outfits.py`); textures TX-04 to TX-06 | Our work (textures CC0) | No | Yes | none | Nothing to make |
| PE-11 | `godot/art/people/heroine_hair_*.gltf/.bin/.chain.json`; `head_tex/hair_strands.png`, `hair_scalp.png` | Her hair cards and strand atlas | Drawn and simulated in code (`heroine_hair.py`) | Our work | No | Yes | none | |
| PE-12 | `godot/art/people/paint/*.png`, `skin_pores.png` | Face-paint designs; skin-pore normal tile | Drawn in code (`heroine_paint.py`, `skin_pores.py`) | Our work | No | Yes | none | |

### Creatures (CR)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| CR-01 | `godot/art/beasts/wolf.glb` | Wolves, with the model's run, idle and crawl animations | "Animated Wolf Scene" by Roo (roo3d), https://sketchfab.com/3d-models/animated-wolf-scene-5d55506494e5460eaadf04370e07cd5c | CC BY 4.0 (API) | Yes | Yes | low: credited | Our own wolf, sculpted in Blender, rigged to a quadruped skeleton, its gait keyed with `tools/anim`'s solver. Arena art (model) and animation (rig, clips) |
| CR-02 | `godot/art/beasts/boar.glb` | Boars | "Animated Realistic Boar – 3D Animal Model" by AnimalMesh 3D, https://sketchfab.com/3d-models/animated-realistic-boar-3d-animal-model-f672a7fd93e84997b80a54ba30956111 | Labelled CC BY 4.0, but the description says "This version is for personal use only. Commercial use is allowed only for versions purchased on Fab or Patreon." | Yes | Yes | **high**: the licensor's own statement contradicts the label (legal lead: blocker) | Before launch: our own boar, made as CR-01. As a stop-gap, buy the commercial version on Fab and keep the receipt. Arena art and animation |
| CR-03 | `godot/art/beasts/lampling.glb` | Lamplings (hats, lamps and satchels added in code) | "Goblin Ghoul" by Rodrigo Bento, https://sketchfab.com/3d-models/goblin-ghoul-a6c6fffee3d34823b6d87a7054782577 | CC BY 4.0 (API) | Yes | Yes | low | An original lampling, made as CR-01. A creature this world owns deserves its own design |

### Weapons (WE): `public/assets/weapons/*.glb` (`godot/src/Actors/Arms.cs`)

Every weapon is CC BY 4.0, checked through Sketchfab's API on 2026-10-04 ("Author must be credited. Commercial use is allowed."). Each ships and each needs attribution. The 48 item icons (UI-03) are photographs of these models, painted over.

All eleven share one replacement path: our own weapons modelled in Blender to our own designs, with the outfit pipeline's CC0 materials, regripped in `Arms.cs` and photographed again for the icons. The main session should assign this; there is no weapons lead yet.

| # | Path | Model, author, URL | Risk |
|---|---|---|---|
| WE-01 | `chevalier_sword.glb` | "Chevalier Sword" by rubenve, https://sketchfab.com/3d-models/chevalier-sword-b2662f2666a844e8a1bd0e7c4a7672d8 | **medium**: the description says it was "made as a mod for blade and sorcery. Based on the concept by Guillem Daudén". The concept artist's design isn't covered by the modeller's grant |
| WE-02 | `viking_sword.glb` | "Viking Sword (Game Model)" by Michael Makivic, https://sketchfab.com/3d-models/viking-sword-game-model-a05d0bd73e9e4508b873ffd7b6a6238d | low |
| WE-03 | `longsword.glb` | "medieval sword" by LowSeb, https://sketchfab.com/3d-models/medieval-sword-da574cba504e4b83a3293f3d3bd067fb | low |
| WE-04 | `zweihander.glb` | "Zweihander" by Siesta, https://sketchfab.com/3d-models/zweihander-bde0f0351bf443f6bed68aeff84b4129 | low: the description links a GameBanana mod; the author invites changes |
| WE-05 | `mace.glb` | "Medieval Mace" by Kama Modeling (design); modelled and textured by Yavuz Temel; https://sketchfab.com/3d-models/medieval-mace-83217215a0c541b2956a8e87a4ae62fe | low: credit both names |
| WE-06 | `viking_axe.glb` | "Viking battle axe" by Mikhail Antonov, https://sketchfab.com/3d-models/viking-battle-axe-b7123192adbf40f68043c57dd8ddcd15 | low |
| WE-07 | `snake_axe.glb` | "Snake Axe" by Ashley Jay Thornton, https://sketchfab.com/3d-models/snake-axe-ace485ac031c4ee0a918e99d2b80560b | low |
| WE-08 | `mage_staff.glb` | "Mage Staff" by RMBehan, https://sketchfab.com/3d-models/mage-staff-a172d06792734bbc9b11272b4f497c2c | low |
| WE-09 | `crossbow.glb` | "Medieval Crossbow" by iedalton, https://sketchfab.com/3d-models/medieval-crossbow-cc36ed347db340d59bd2ec7b06ae0d63 | low |
| WE-10 | `shield_round.glb` | "Medieval Shield" by Artem Mykhailov, https://sketchfab.com/3d-models/medieval-shield-b98b8f64d935415aab0fe9b70074511f | **medium**: "Based on the concept by Artyom Vlaskin", as WE-01 |
| WE-11 | `daggers.glb` | "Silver Bladed weapons - Fantasy weapon set" by Peter Nox (listed as "Asylum Nox", peter.pottiez, when downloaded), https://sketchfab.com/3d-models/silver-bladed-weapons-fantasy-weapon-set-d5189211a1d348b0a9d7ddc052a22989 | low |

### Environment models and kits (EN)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| EN-01 | `public/assets/env/village/*` (176 glTF, textures as KTX2); `godot/art/srgb/env/village/*` | Houses, walls, roofs, the town's fabric | Quaternius, Medieval Village MegaKit (Standard), https://quaternius.itch.io/medieval-village-megakit (`tools/assets/env.py`) | CC0 1.0 | No | Yes | low | Our own modular kit in Blender with the CC0 building materials (TX-03). Arena art, low priority |
| EN-02 | `public/assets/env/props/*` (94 glTF); `godot/art/srgb/env/props/*` | The town's furniture and props | Quaternius, Fantasy Props MegaKit, https://quaternius.itch.io/fantasy-props-megakit | CC0 1.0 | No | Yes | low | As EN-01 |
| EN-03 | `public/assets/env/nature/*` (68 glTF); `godot/art/srgb/env/nature/*` | Trees, rocks, plants, pebbles; bark for the campfire | Quaternius, Stylized Nature MegaKit, https://quaternius.itch.io/stylized-nature-megakit | CC0 1.0 | No | Yes | low | Our own trees and plants (Blender geometry nodes), or more of the CC0 scans (EN-05) |
| EN-04 | `public/assets/characters/*.glb` (Adventurers: barbarian, knight, mage, rogue, rogue_hooded; Skeletons: skeleton_*); `public/assets/props/{adventure_items, dungeon, halloween, hex_buildings, hex_nature}.glb`; `public/assets/anim/humanoid.glb`; meshes and atlases embedded in `godot/data/zones/*/landmarks.glb`; `godot/data/zones/kaykit.json`; `public/assets/LICENSE-KayKit.txt` | Graves, fences, ruins, lanterns and banners in the zones' landmarks (the files themselves are unused by Godot) | Kay Lousberg, KayKit: Character Pack Adventures, Skeletons, Dungeon Remastered, Medieval Hexagon, Halloween Bits, https://github.com/KayKit-Game-Assets (`tools/assets/build.mjs`) | CC0 1.0 | No | Yes | low. Was missing from `CREDITS.md` (only the Adventurers' licence file was there) | Godot already makes KayKit pieces anew in code (`World/Pieces.cs`). Export the landmarks again without them, then drop the files. Arena art |
| EN-05 | `godot/art/world/*.glb` (33); the originals in `public/assets/env/polyhaven/**` (git-ignored, on the owner's disk, shipped through the link) | Rocks, roots, stumps, shrubs, grass, ferns, nettles, a statue, kite shield, lantern, crate, barrels, fire pit | Poly Haven models by Kless Gyzen, Rico Cilliers, Jenelle van Heerden, Rob Tuytel, Greg Zaal, Dario Barresi, Benny Weimer, Ulan Cabanilla, James Ray Cock, Jack Mava and Sebastian Platen (each in `CREDITS.md`) | CC0 1.0 (API) | No | Yes | low | Our own photogrammetry, or sculpted rocks. Lowest priority |
| EN-06 | `public/assets/env/custom/Well.gltf/.bin` | The town well | Modelled in Blender by script (commit 527fbcb) | Our work | No | Yes | none | |
| EN-07 | `godot/data/zones/{lowford,verge,waystation}/*` | Each zone's heights, paint, flora, props, water and landmarks | Exported from the web game (`tools/godot/export_zone.mjs`). Our layout; `landmarks.glb` carries KayKit (EN-04) | Our work, plus CC0 | No | Yes | none (the KayKit part is EN-04) | |

### Textures, materials and HDRIs (TX)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| TX-01 | `godot/art/ground/{albedo,normal,arh}.jpg`, `ground.json`; `public/assets/ground/*.ktx2` (web) | The Verge's ground | Poly Haven: sparse_grass (Amal Kumar), forest_leaves_02 (Rob Tuytel), forest_ground_04 (Rob Tuytel, Rico Cilliers), mud_forest (eye-candy.xyz), cobblestone_05 (Rob Tuytel), mossy_rock (Rob Tuytel), burned_ground_01 (Rob Tuytel) | CC0 1.0 (API) | No | Yes | low | Our own photographed ground, or procedural materials (Material Maker, Blender). Lowest priority |
| TX-02 | `godot/art/arena/{barrow,dig,hollow,ruts}/*`, `layers.json` | The four arenas' grounds | 22 more Poly Haven sets: brown_mud_02, brown_mud_03, brown_mud_leaves_01, dark_rock, dry_mud_field_001, forest_leaves_03, forest_leaves_04, grass_path_3, gravel_road, gravel_stones, ground_grey, muddy_tracks, quarry_wall, red_mud_stones, river_small_rocks, rocks_ground_06, rocky_terrain, rocky_trail, roots, stone_pathway_02, withered_grass, wood_chips (authors in `CREDITS.md`) | CC0 1.0 (API) | No | Yes | low | As TX-01 |
| TX-03 | `godot/art/materials/{castle_wall_slates, medieval_blocks_03, rock_boulder_dry, rough_wood, forest_ground_04}/*` | Dressed stone, slate roofs, headstones, timber, grave dirt | Poly Haven (Rob Tuytel; Dimitrios Savva and Rico Cilliers) | CC0 1.0 | No | Yes | low | As TX-01 |
| TX-04 | `godot/art/outfit/{brown_leather, curly_teddy_natural, fabric_leather_02, faux_fur_geometric, leather_red_02, metal_plate, metal_plate_02, rough_linen, rusty_metal_02, velour_velvet}_*`; `godot/art/people/outfit_tex/*` | Cloth, leather, fur and plate for the outfits | Poly Haven (Rob Tuytel; colormass and Rico Cilliers) | CC0 1.0 (API) | No | Yes | low. Nine of the ten were missing from `CREDITS.md` | Our own scanned or procedural fabrics. Low priority |
| TX-05 | `godot/art/outfit/{Leather014, Leather021, Leather024, Leather026, Leather034C, Leather037, Metal038, Metal046B, Metal048C, Metal053C}_*`; `godot/art/people/outfit_tex/*` | Leathers and metals for the outfits | ambientCG, https://ambientcg.com (`tools/assets/ambientcg.py`) | CC0 1.0 (API) | No | Yes | low | As TX-04 |
| TX-06 | `godot/art/outfit/outfit_*_diff.jpg`, `godot/art/people/outfit_tex/outfit_*_diff.jpg` | Tinted variants for each outfit colour | Made by `heroine_outfits.py` from TX-04 and TX-05 | CC0-derived | No | Yes | none | |
| TX-07 | `godot/art/studio/studio_small_08_1k.hdr` | The light the item photographs are taken in | "Studio Small 08" by Sergej Majboroda, Poly Haven | CC0 1.0 | No | Yes | low | Our own HDRI or a Blender light rig. Trivial |

### Interface art, icons and fonts (UI)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| UI-01 | `godot/art/ui/frames/*` (except `focus.png`), `bars/{casing,casing_boss,track,track_boss}.png`, `book/*`, `hud/*`, `medallion/*`, `minimap/frame.png`, `ornaments/*`, `title/logo.png` (60 files; listed in the appendix) | The interface's frames, plates, buttons, slots, cards, medallions, the book, the logo | Our geometry (forge height fields, Blender renders, `tools/uiforge`), painted over or painted by Krea 2 turbo with the darkbrush LoRA (`paintover.py`, `krea.py`, `fitall.py`); BiRefNet cut-outs | Krea 2 Community License (AI-01) | No | Yes | **high** (business): AI-01 | Ship the forged and Blender renders without the paint-over (the geometry and light are already ours), or have an illustrator paint over them. UI art lead |
| UI-02 | `godot/art/ui/icons/glyph_color/*.png` (117) | Skill, art, blessing and evolution icons | Krea 2 turbo with the darkbrush LoRA (`icons.py`, `emblems.py`) | Krea 2 Community License | No | Yes | **high** (business) | `emblems.py` already models each icon as shapes lit by our own matcaps; ship that render without the Krea pass, or commission an icon artist. UI art lead |
| UI-03 | `godot/art/ui/icons/item/*.png` (48) | Item icons | The game's own photographs of its item models (several are the CC BY weapons, WE-*), painted over by Krea 2 (`items.py`) | Krea 2 Community License, over CC BY photos | Yes (for the weapons in them) | Yes | **high** (business), and they derive from WE-* | Photograph our own item models (after WE-*) and grade them without Krea. UI art lead |
| UI-04 | `godot/art/ui/icons/{glyph (54), prompt (17), map (7)}/*`, `cursors/*` (3), `frames/focus.png`, `bars/{ember,experience,health}_fill.png`, `minimap/you.png` (86 files) | Value glyphs, pad prompts, map marks, cursors, focus ring, bar fills | Forged in code (`valueglyphs.py`, `padprompts.py`, `mapmarks.py`, `cursors.py`, `lightpieces.py`, `smallforge.py`) | Our work | No | Yes | none | |
| UI-05 | `godot/art/ui/create/female/*` (26) | Character creation's cameos (hair, faces, paints) | Photographs of the game's heroine (`creation_portraits.py`) | Inherits PE-06 and PE-08 | No | Yes | UNKNOWN: inherits her body's unknown origin and the Krea face | Re-shoot after PE-06 and PE-08 are settled (one command) |
| UI-06 | `godot/data/content/glyphs.json`, `src/ui/glyphs.ts` | The designer's line glyphs (24-unit SVG paths) | Written for the game (commit 77b4fe2, "engraved glyph set") | Our work | No | Yes | none | |
| UI-07 | `godot/art/fonts/{cinzel-*, alegreya-*, alegreya-sans-*}.woff2`, `OFL-*.txt` | The typefaces | Cinzel by Natanael Gama (Cinzel Project Authors, https://github.com/NDISCOVER/Cinzel); Alegreya and Alegreya Sans by Juan Pablo del Peral, Huerta Tipográfica (https://github.com/huertatipografica) | SIL OFL 1.1 | Yes: the copyright notice and the licence must travel with the font | Fonts yes; OFL texts **no** (not resources) | medium: notice not shipped (BU-01). Easy fix | Keep: OFL fonts are fine to ship. A commissioned typeface is optional |
| UI-08 | `godot/icon.png`, `desktop/icon.png` | The app icon (an ember and a broken chain) | Drawn for the game (commit fccdd37); simple vector shapes | Our work | No | Yes | none | |

### Effects (FX)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| FX-01 | `godot/art/fx/sprites.png` (68 layers), `sprites.json`, `embers.png`, `puff.png`, `runes_a.png`, `runes_b.png` | Particle sprites: smoke, sparks, flares, flames, runes, slashes | Kenney, Particle Pack, https://kenney.nl/assets/particle-pack | CC0 | No | Yes | low | Our own sprites rendered from Blender simulations, or drawn by hand. Skills VFX lead |
| FX-02 | `godot/art/fx/fb/*.png` + `*.json` (14 atlases); 20 atlases in the release pack on 4 Oct (ring and moon among the additions; legal: same LTX terms, prompts name no work) | Filmed bursts: arcane, blood, dust, embers, fire, frost, holy, nature, shadow, smoke, sparks, storm | LTX 2.5 on the local ComfyUI (`fx_clips.py`), cut by `flipbook.py` | LTX-2.x Community License (AI-03) | No (an AI disclosure is required) | Yes | medium: AI-03 | Simulate in Blender (Mantaflow fire and smoke, particles) and render to the same flipbooks, or use procedural shaders. Skills VFX lead |
| FX-03 | `godot/art/fx/marks/*.png` (7 marks, each with its emission map) | Scorch, cracks, frost, blight, roots, runes, sigil decals | Krea 2 turbo (`tools/comfy/marks.py`) | Krea 2 Community License (AI-01) | No | Yes | **high** (business) | Procedural decals in code (noise and SDF), as the forge does. Skills VFX lead |
| FX-04 | `godot/shaders/*`, `godot/src/Fx/*` | Shaders and procedural effects | Written for the game | Our work | No | Yes | none | |

### Animation (AN)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| AN-01 | `public/assets/people/UAL1.glb`, `UAL2.glb`; the skeleton every body is bound to | Fallback clips, and the game's skeleton standard | Quaternius, Universal Animation Library 1 and 2, https://quaternius.itch.io/universal-animation-library | CC0 1.0 | No | Yes | low: the whole rig depends on it, but it's CC0 | Keep (CC0). A skeleton of our own would mean retargeting everything, which is not worth it |
| AN-02 | `godot/art/anim/heroine.res`: idle_warden, idle_arcanist, idle_reaver, idle_stalker (and idle_stalker_break, keyed with 100STYLE as reference) | Her callings' idles | 100STYLE by Ian Mason, Sebastian Starke, Taku Komura, https://zenodo.org/records/8127870; retargeted, feet locked, looped, arms re-keyed (`tools/anim/manifest.json`) | CC BY 4.0 | Yes: credit, licence link, changes | Yes | low: credited, changes recorded | Key them (`tools/anim`), or capture the owner's own idles (AN-05's video route). Animation lead |
| AN-03 | `heroine.res`: leap ("Standing Melee Run Jump Attack"); `godot/art/anim/folk.res`: f/m idle, pick_up, sit_chair, sit_floor; f_walk; m_talk | Her Crashing Leap and 10 townsfolk clips | Adobe Mixamo, under the owner's Adobe account; raw FBX kept outside the repo | Mixamo terms: royalty-free in games; raw files not redistributed | No | Yes (baked) | low: terms tied to the owner's account; raw files not shipped | Keyed clips or our own capture. Animation lead |
| AN-04 | `folk.res`: f/m arms_crossed, cheer, wave, work; f_talk; m_walk | 10 townsfolk clips | NVIDIA Kimodo-SOMA-RP, generated from prompts (`kimodo_gen.py`) | NVIDIA Open Model License (outputs ours) | No (notice only when distributing the model) | Yes | low; AI-generated, so it must be disclosed | Keyed or captured. Animation lead |
| AN-05 | `heroine.res` (63 clips), `folk.res` (8), the crowd's baked gaits | Everything else she and the crowd do | Keyed in code (`tools/anim`: `gait.py`, `keyed.py`, `clips/*`, `crowd.py`) | Our work | No | Yes | none | |

### Audio and voice (AU)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| AU-01 | `godot/art/sound/{impact*, footstep_*, click, select, switch, toggle, tick, back, close, open, confirmation, error, drop, cloth*, belt*, book*, creak, door*, drawKnife, knifeSlice, handle*, scroll}_*.wav` (178 takes) | Impacts, footsteps, interface clicks, handling | Kenney: Impact Sounds, RPG Audio, Interface Sounds, https://kenney.nl/assets | CC0 | No | Yes | low | Our own Foley (the owner's microphone) or synthesis (the game already synthesises most sounds). Combat and Skills leads |
| AU-02 | `godot/art/sound/bed_birds_0.wav`, `bed_water_0.wav`, `bed_fire_0.wav`, `bed_crickets_0.wav`, `anvil_0.wav` | Ambience beds and the anvil | OpenGameArt: "Park ambiences" by thimras; "Fireplace Sound loop" by PagDev; "Crickets Ambient Noise - loopable" by Wolfgang_ (recording credited to Ted Kerr); "Blacksmith's Hammer" by vishwajai | CC0 | No | Yes | low | Our own field recordings |
| AU-03 | `godot/art/sound/tell_drum_0/1.wav`, `tell_howl_0/1.wav`, `tell_fuse_0.wav`; since added: `tell_fuse_1`, `tell_whistle_0/1` (8 takes in the release pack, 4 Oct; legal: same LTX terms, prompts name no work) | Combat tells | LTX 2.5's audio (`tools/comfy/sfx_clips.py`) | LTX-2.x Community License | No (AI disclosure) | Yes | medium: AI-03 | Record or synthesise. Combat lead |
| AU-04 | `godot/art/vo/**/*.ogg` (19), `godot/data/vo/index.json` | Placeholder voice takes for cinematic lines | Maya1 acts the line, Seed-VC converts it to the part's voice, designed by VoxCPM2 from a text description (all 37 references in `tools/vo/refs` are seeded designs; none is cloned); Whisper checks the words | Maya1 Apache-2.0; Seed-VC GPL-3.0 (code; outputs not covered); VoxCPM2 Apache-2.0 | No | Yes | low (licence). The owner wants no placeholders; they are AI and must be disclosed while they ship | Final takes recorded in ElevenLabs on a paid plan, keeping each voice's licence record, or by actors with signed releases. Voice lead |
| AU-05 | `godot/src/Audio/*` | The synthesised sounds and music | Written for the game | Our work | No | Yes | none | |

### AI generators (AI): the tools behind the assets above

| # | Model, tool, where | Licence | What it made | Ships | Risk | Notes |
|---|---|---|---|---|---|---|
| AI-01 | Krea 2 turbo (fp8), darkbrush LoRA, Qwen3-VL 4B encoder, Qwen-Image VAE; local ComfyUI; from https://huggingface.co/Comfy-Org/Krea-2 (originals `krea/Krea-2-Turbo`, `krea/Krea-2-LoRA-darkbrush`) | Krea 2 Community License Agreement v1 (22 June 2026); Qwen parts Apache-2.0 | UI-01 to UI-03, FX-03, PE-08, PE-09's face; the face references, concept sheets and cinematic storyboards (`tools/cinematics/boards.py`; not shipped) | Outputs ship | **high** (business) | §2.3: outputs only under US$1M company-wide revenue (trailing twelve months). §9.2: Krea may terminate on 30 days' notice. §4.3: disclose AI where a platform requires it (Steam does). The notice text and the "Krea" naming rule apply only if we distribute the model. Enterprise licence: opensource@krea.ai |
| AI-02 | Krea 2 Large, through Comfy's paid API node (`tools/comfy/concepts.py --large`) | Comfy API and Krea terms | Concept art (`tools/comfy/out/concepts_large`, now empty); most jobs rejected by Krea's moderation (ComfyUI log, 30 Sep) | No | low | Nothing shipped came from a paid API node, as far as the logs (30 Sep to 4 Oct) and the tools show |
| AI-03 | LTX 2.5 22B distilled, Gemma 4 12B encoder, LTX spatial upscaler; local ComfyUI | LTX-2.x Community License (licence embedded in the model file); Gemma 4 Apache-2.0 (Comfy-Org/gemma-4) | FX-02, AU-03 | Outputs ship | medium | Free under US$10M entity revenue (§2.1). No rights claimed in outputs (§5). Attachment A item 5: disclose content as machine generated. §6 and item 19: don't remove watermarking or provenance. Keep the source clips |
| AI-04 | TRELLIS 2 (microsoft/TRELLIS.2-4B), DINOv3 ViT-L, MoGe 2; local ComfyUI (`graphs/trellis_img.json`) | MIT; DINOv3 License; MIT | PE-06's and PE-09's bodies (the owner, 4 Oct; `docs/legal/records/BODIES_RECORD.md`); the first heroine attempt (c528caf, superseded) | Outputs ship | low: inputs are Krea 2 Turbo pictures made locally (AI-01) | DINOv3 asks for "Built with DINOv3" when distributing DINO materials; we distribute none. A courtesy line is in `CREDITS.md` |
| AI-05 | Pixal3D (TencentARC); local ComfyUI | MIT | Experiments (`wrap_to_scan.py`) | No | low | |
| AI-06 | BiRefNet; local ComfyUI | MIT | Cut-out masks for the UI | Masks only | low | |
| AI-07 | Reallusion AccuRIG 1.10 (`autorig_actor.fbx`) | Reallusion EULA: own content may be rigged and used; Reallusion content may not be repurposed | The heroine's and hero's weights | Weights ship | low | No Reallusion content ships: their skeleton is replaced by ours |
| AI-08 | MPFB2 in Blender, MakeHuman 1.2 assets | Code GPL-3.0 (not shipped); assets CC0 | PE-07, PE-09's head; `heroes.py` bodies (not shipped) | Assets ship | low | |
| AI-09 | NVIDIA Kimodo-SOMA-RP-v1.1 (text encoder LLM2Vec on Meta Llama 3 8B Instruct) | NVIDIA Open Model License; Llama 3 Community License | AN-04 | Outputs ship | low | We distribute neither model, so their notice rules don't bite. Credited as courtesy |
| AI-10 | Meta SAM 3D Body (Momentum Human Rig) | SAM License; MHR Apache-2.0 | A pipeline test clip from Pexels footage | No | low | Before any capture of a real performer ships, check the SAM licence on outputs and get a release from the performer |
| AI-11 | Maya1, Seed-VC, VoxCPM2, Whisper, UTMOS22, SpeechBrain ECAPA, emotion2vec+ | Apache-2.0; GPL-3.0; Apache-2.0; MIT; MIT; Apache-2.0; FunASR licence | AU-04 | Outputs ship | low | |
| AI-12 | Voice shoot-out: Chatterbox (MIT), IndexTTS-2.5, Dia, Orpheus, F5, Kokoro, Qwen3-TTS (Apache-2.0), through Voicebox (MIT) | Various | `docs/voice/samples` (repo only) | No | low | |
| AI-13 | Hunyuan3D-2 (`tools/make3d`) | Tencent Hunyuan 3D 2.0 Community License: not licensed in the EU, UK or South Korea | Test models in `tools/make3d/output` (git-ignored) | No | **high if ever used** | No shipped mesh traces to make3d (all its outputs are tests, with the licence recorded in each `.json`). Its outputs must never ship |
| AI-14 | Meshy image-to-model (a `meshy_image2model_00001_.glb` sat on the owner's Desktop on 2 Oct) | Meshy's terms (https://www.meshy.ai/pricing): on a premium plan, "you own all assets you create"; on a free plan, "a CC BY 4.0 license" (credit Meshy). Which plan was used is UNKNOWN | Nothing: the owner says the bodies were made in our ComfyUI (AI-01, AI-04), not in Meshy | No | none | Owner question 1, answered 4 Oct
| AI-15 | Installed on this PC but unused by any repo tool: MiniMax H3 (+ turbo LoRA), `MysticXXX_KREA2_v1` LoRA (a third-party Krea 2 LoRA trained with ai-toolkit; source unknown). **Identified (legal, 4 Oct):** Civitai model 2728644, "[KREA 2] Mystic XXX" by alcaitiff, v1.0 of 25 Jun 2026 (found by its SHA-256) | MiniMax H3 Community License; Mystic XXX: Krea 2 base terms, and the creator allows commercial use of images (Image, Sell, Rent), no credit, derivatives (Civitai) | Probably the picture for the hero's body (PE-09); the log fits its 256 layers | No | low: allowed by its creator; flagged an adult concept LoRA, not a real person | Owner question 6: the owner to confirm which LoRA the hero picture used. Either is allowed
| AI-16 | Claude (Anthropic), in Claude Code | Anthropic's commercial terms assign outputs to the customer | The code (`godot/src`, `godot/logic`, shaders, `tools/`), the writing and dialogue (`godot/data/content`), this audit | Yes | low | Steam's survey covers dialogue "consumed by players": disclose AI-assisted writing |
| AI-17 | ElevenLabs (planned final voices; packets in `docs/voice/elevenlabs`) | ElevenLabs terms: commercial use needs a paid plan; Voice Library voices carry their own terms | Nothing yet | Not yet | UNKNOWN until the plan and the voices are chosen | Keep the plan, invoices and each voice's terms with the takes |

### Code, engine and libraries (CO)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| CO-01 | Godot 4.5.1 .NET engine and export templates (`tools/godot/setup.sh` fetches them from godotengine/godot-builds) | The engine, including Jolt Physics, FreeType, HarfBuzz, ICU, mbedTLS, ENet, etc. | Godot Engine contributors, https://godotengine.org | MIT; third parties in Godot's `COPYRIGHT.txt` | Yes: the licence text in the game or alongside it | Yes | medium: no notice ships today (BU-01) | Keep; ship the notices |
| CO-02 | .NET 8 runtime and GodotSharp assemblies (in the export's data folder) | The C# runtime | Microsoft, .NET Foundation, Godot | MIT (with .NET's third-party notices) | Yes | Yes | medium: as CO-01 | Keep; ship the notices |
| CO-03 | `godot/src`, `godot/logic`, `godot/shaders`, `godot/scenes`, `godot/tools_scenes` | The game's code and shaders | Written for the game (with Claude). Techniques credited in comments: Stefan Gustavson's simplex noise (public domain), Inigo Quilez's texture-repetition method (our implementation), Kajiya-Kay hair shading (published) | Our work | No | Yes | none | |
| CO-04 | `godot/tests/Tests.csproj`: xunit 2.4.2, xunit.runner.visualstudio 2.4.5, Microsoft.NET.Test.Sdk 17.6.0 | Test framework | NuGet | Apache-2.0, Apache-2.0, MIT | No | No | low | |
| CO-05 | `package.json`: three (MIT), postprocessing (Zlib), n8ao (CC0), preact and @preact/signals (MIT), meshoptimizer (MIT), @fontsource/alegreya, alegreya-sans, cinzel (OFL); Electron (MIT plus Chromium's notices) | The older web game and its Electron wrapper | npm | As listed | Yes, if that build is ever sold | Only in the web and Electron build | low | Not the Steam build. If it ever ships, add its notices |
| CO-06 | `public/assets/basis/basis_transcoder.js/.wasm` | KTX2 transcoder for the web game | Binomial LLC, from three.js | Apache-2.0 | Yes (notice) | Only in the web build (not a Godot resource) | low | |
| CO-07 | `tools/**` dependencies: Blender (GPL; outputs free), gltfpack/meshoptimizer (MIT), KTX-Software toktx (Apache-2.0), ffmpeg (LGPL/GPL; outputs free), ComfyUI (GPL-3.0), Python packages (numpy, Pillow, scipy, OpenCV, librosa, soundfile, torch, transformers, diffusers, trimesh, pymeshlab, rembg, mediapipe and the MediaPipe face landmarker model) | Asset tooling | Various | Various, permissive or GPL | No | No | low: none of the tools ship, and tool licences don't reach their outputs | |

### Data and writing (DA)

| # | Path(s) | What | Source | Licence | Attribution | Ships | Risk | Replacement path |
|---|---|---|---|---|---|---|---|---|
| DA-01 | `godot/data/content/*.json`, `godot/data/cinematics/*.json`, `godot/logic/Content/*`, `godot/logic/World/*` | Story, dialogue, quests, items, looks, the hymn "Lie Down" | Written for the game by the story lead (Claude) under the owner's direction | Our work | No | Yes | none (disclose AI-assisted writing: AI-16) | |
| DA-02 | `src/content/weapons.ts`, `discoveries.ts`, `src/sim/battle.ts`, `docs/BETA_DESIGN.md`; the Credits line "World, lore and combat roots: The Ember Watch" | The world, lore, weapons and combat ported from The Ember Watch | `stevenrogerino/wowsurvivors` (on this PC). It started as a Warcraft fan work; its NOTICE says every borrowed name was replaced | UNKNOWN: presumed the owner's, not established. The repo belongs to the stevenrogerino account, which munchtech can't push to, and its 327 commits are all authored "Claude" | No | Yes | none (answered 4 Oct: the owner made it, with Claude, and no third party contributed). Keep the records in `docs/legal/LEGAL_BRIEF.md` issue 5(e) | If it isn't his: a written assignment from the repo's owner, or the world and lore rewritten. Story lead |
| DA-03 | Names in `godot/data/content`, `tools/vo/cast.json`: Maeca Barefoot, Vonnra Hydrocheck, Rav (Cutwell), Chid, Keegan, DZ | Characters carried over from The Ember Watch | The Ember Watch | Our work | No | Yes | UNKNOWN: whether any is a real person's name or handle (question 4) | Rename any that is. Story lead |
| DA-04 | `godot/logic/Content/Unions.cs` and `Paths.cs` ("starfall", "consecration"), `Boons.cs` ("Consecration"), `Weapons.cs` and `src/content/weapons.ts` ("Whirlwind"), `Paths.cs` ("moonfire" in text), `Abilities.cs` ("fan of knives" in text) | Skill and evolution names | Kept from The Ember Watch, whose own guard (`tools/check-original.js`) bans them as part of a Warcraft "constellation" | Words, not works | No | Yes | low (legal lead: rename Starfall, Moonfire, Fan of Knives; the plain words are fine alone) | New names in the game's own voice. Story lead with the combat lead |
| DA-05 | `godot/data/vo/index.json`, `godot/data/zones/kit_materials.json`, `godot/balance/*` | Indices and tuning | Our work | Our work | No | Yes | none | |

### Build and export (BU)

| # | What | Risk | Fix |
|---|---|---|---|
| BU-01 | No licence notice ships: Godot's MIT and `COPYRIGHT.txt`, the .NET notices, the three OFL texts, the CC BY notices (Sketchfab, 100STYLE) and `CREDITS.md` itself. `.txt` and `.md` aren't resources, so the export leaves them out. The in-game Credits (`godot/src/Ui/Front.cs`) are out of date and have no licence links | medium | A `licenses/` folder beside the executable (or in the pack with an include filter): Godot `LICENSE.txt` and `COPYRIGHT.txt`, .NET `THIRD-PARTY-NOTICES.TXT`, `OFL-*.txt`, `CREDITS.md`. In-game Credits generated from `CREDITS.md` with licence links. The legal lead specifies; the main session builds it |
| BU-02 | `export_filter="all_resources"` ships every imported file, used or not. Third-party files known to be unused by the Godot game: `public/assets/characters/*.glb` (9, KayKit), `public/assets/props/*.glb` (5, KayKit), `public/assets/anim/humanoid.glb` (KayKit), `public/assets/ground/*.ktx2` (web ground; Godot uses `godot/art/ground`), `public/assets/people/*.bake.webp` (9, web bakes), `public/assets/env/polyhaven/**` (180 git-ignored originals; Godot uses `godot/art/world`). Dev-only paths: `godot/art/people/anime_female.glb` and `her_Hair_*.glb` (`--body anime`), `woman.glb` and `woman_mask.png` (`--body woman` or fallback) | medium | Exclude those paths (and `tools_scenes/`) in the export presets' `exclude_filter`, or move to a resources-based export with an explicit include list. Main session, with the performance lead |
| BU-03 | Build-time fetches: NuGet (Godot.NET.Sdk from nuget.org); Godot binaries and export templates from github.com/godotengine/godot-builds; `npm ci` for the web build. Nothing is fetched at run time (no HTTP in `godot/src`) | low | |

### On disk or in the repo, not shipped (WL): a watch list

| # | Path(s) | What | Source | Licence | Risk if used |
|---|---|---|---|---|---|
| WL-01 | `tools/comfy/out/sfx/medieval*` (git-ignored) | 48 weapon-on-weapon recordings, sliced into 288 blows | "Medieval sound effects - Weapon impacts" by Ben Jaszczak and Brian Nelson, https://opengameart.org/node/146863 | CC0 ("no credit needs to be given") | low: fine to use; credit the authors |
| WL-02 | `tools/comfy/out/sfx/fantasy` (git-ignored) | 67 ambiences, battle, footsteps, hits, horse, dragon | "Fantasy Ambient Sound Effects Pack (CC0)" by kmontesdev, https://kmontesdev.itch.io/fantasy-ambient-sound-effects-pack-cc0 | Claimed CC0 by the uploader, but the WAVs carry Pro Tools metadata with library-style tags ("Drone, Alien, Cave, Science, Fiction, 5.1") dated 2014 | UNKNOWN: possibly re-uploaded library sounds. Don't use until the origin is shown |
| WL-03 | `tools/anim/clips/generated.py` (`test_video_pose`); footage under `C:/Users/munch/Tools/mocap` | A SAM 3D Body test on Pexels video 6769391 (plus 15 Pexels clips of people downloaded for tests) | Pexels | Pexels licence | low: test only. Don't ship motion of identifiable people without checking the Pexels terms |
| WL-04 | `tools/make3d/output/**` (git-ignored) | Five Hunyuan3D-2 test models | Tencent Hunyuan3D-2 | Not licensed in the EU, UK or South Korea | **high**: must never ship |
| WL-05 | `docs/concepts`, `docs/ui_review`, `docs/cinematics/shoot` (boards, `animatics/prologue.mp4`), `docs/hero_male`, `docs/team/face_sheets`, `docs/experience` | Concept art, storyboards and the animatic cut from them, review sheets | Krea 2 outputs, and game screenshots | Krea 2 terms | low: repo only. Any store-page or marketing use is commercial use of Krea outputs (AI-01) |
| WL-06 | `docs/voice/samples/*` | Voice shoot-out samples | AI-12 | Various | none (repo only) |
| WL-07 | `docs/bosses/notes/*`, `docs/feel/notes/*`, `docs/items/RESEARCH.md` | Research notes on other games (Diablo, Halls of Torment and others) | Our notes | Our work | none: notes, not shipped. Keep any quotes short |
| WL-08 | `tools/vo/refs/*.flac` (37) | Voice references for the placeholders | VoxCPM2 voice designs from text, with seeds (`refs/casting.json`) | Apache-2.0 model; outputs ours | none: synthetic, no real voice cloned |

## Notes for the people who act on this

- **Legal and Steam compliance lead (aa12c130ddf4b904c):**
  - The Steam pre-generated AI disclosure should name images (Krea 2), effects video and audio (LTX), 3D sculpts (TRELLIS 2 and the unknown generator), motion (Kimodo), placeholder voices (Maya1, Seed-VC, VoxCPM2), and code and dialogue written with Claude.
  - Krea's revenue cap and its 30-day termination are the biggest commercial exposure. Ask Krea (opensource@krea.ai) about an enterprise licence early.
- **Everyone:** run new third-party assets through `CREDITS.md` and this file, with the source URL and licence, before they land. The fetch tools in `tools/assets/` already append credit lines.

## Appendix: every AI-made shipped file

This lists every shipped file made by an AI generator, grouped by generator, from `git ls-files` on 2026-10-04. Regenerate it before release. The UI made without AI is listed too, so the boundary is clear.

The boundary follows the tools:

- `chrome.py`, `medals.py`, `pieces.py`, `paper.py`, `cards.py`, `plates.py`, `smalls.py`, `fitall.py`, `icons.py`, `emblems.py` and `items.py` all pass through `paintover.py` or `krea.py`.
- `valueglyphs.py`, `padprompts.py`, `mapmarks.py`, `cursors.py`, `lightpieces.py` and `smallforge.py` (the minimap arrow) do not.

Pieces that `chrome.py` makes again over a forged original (keycap, segment, row, the bars' grooves) are counted as painted. The UI art lead should confirm per file before replacing.

### Kimodo-SOMA-RP motion (10 of its clips; the rest Mixamo and keyed) (1 files)

- `godot/art/anim/`: folk.res

### LTX 2.5 video (flipbooks, tools/comfy/fx_clips.py + flipbook.py) (28 files)

- `godot/art/fx/fb/`: arcane_burst.json, arcane_burst.png, blood_splat.json, blood_splat.png, blood_spray.json, blood_spray.png, dust_ring.json, dust_ring.png, ember_motes.json, ember_motes.png, fire_blast.json, fire_blast.png, fire_loop.json, fire_loop.png, frost_burst.json, frost_burst.png, holy_burst.json, holy_burst.png, nature_burst.json, nature_burst.png, shadow_burst.json, shadow_burst.png, smoke_puff.json, smoke_puff.png, sparks.json, sparks.png, storm_strike.json, storm_strike.png

### Krea 2 turbo (ground marks, tools/comfy/marks.py) (14 files)

- `godot/art/fx/marks/`: blight.png, blight_emit.png, crack.png, crack_emit.png, frost.png, frost_emit.png, roots.png, roots_emit.png, runes.png, runes_emit.png, scorch.png, scorch_emit.png, sigil.png, sigil_emit.png

### Krea 2 turbo face and iris paint (heroine_face.py, heroine_eyes.py, hero_male_face.py; embedded in the .glb) (5 files)

- `godot/art/people/head_tex/`: heroine_eye.png, heroine_head.jpg, heroine_iris.png
- `godot/art/people/`: hero.glb, heroine.glb

### LTX 2.5 audio (tools/comfy/sfx_clips.py) (5 files)

- `godot/art/sound/`: tell_drum_0.wav, tell_drum_1.wav, tell_fuse_0.wav, tell_howl_0.wav, tell_howl_1.wav

### Krea 2 turbo + darkbrush LoRA (painted, or a Blender/forge render painted over) (225 files)

- `godot/art/ui/bars/`: casing.png, casing_boss.png, track.png, track_boss.png
- `godot/art/ui/book/`: open.png, ribbon.png
- `godot/art/ui/frames/`: banner.png, button.png, button_disabled.png, button_hover.png, button_pressed.png, button_primary.png, button_primary_hover.png, button_primary_pressed.png, card_common.png, card_epic.png, card_evolution.png, card_legendary.png, card_rare.png, card_uncommon.png, chip.png, console.png, crest_card.png, crest_row.png, header.png, hint.png, keycap.png, map_frame.png, paper.png, pillar.png, plate.png, prompt.png, row_on.png, segment_on.png, slab.png, slot.png, slot_common.png, slot_epic.png, slot_legendary.png, slot_rare.png, slot_relic.png, slot_uncommon.png, tab.png, tab_on.png, toast.png, tooltip.png, tooltip_worn.png, weapon_slot.png, well.png
- `godot/art/ui/hud/`: globe_glass.png, globe_rim.png, medal_heart.png, medal_level.png, ring_art.png
- `godot/art/ui/icons/glyph_color/`: aegis.png, arc.png, arc_fork.png, arc_sky.png, arcane.png, arrow.png, arrow_mark.png, arrow_rain.png, axe.png, axe_blood.png, axe_storm.png, beam_gaze.png, beam_green.png, beam_sun.png, bleed.png, blink.png, bolt.png, book.png, boot.png, chain.png, chakram.png, chakram_hail.png, chakram_razor.png, cinder.png, claw.png, coin.png, command.png, consecrate.png, crosshair.png, dagger.png, dagger_blood.png, dagger_flurry.png, disc.png, disc_aegis.png, disc_reckon.png, drain.png, echo.png, embers.png, execute.png, expand.png, feint.png, fist.png, flame.png, frostaura.png, hand.png, heart.png, herd.png, herd_great.png, herd_hunt.png, horns.png, hourglass.png, howl.png, kindling.png, leaf.png, leap.png, living_flame.png, magnet.png, mark.png, mirror.png, moon.png, moon_brand.png, moonfall.png, mote.png, mote_cascade.png, mote_star.png, nova_blood.png, nova_dawn.png, nova_harrow.png, nova_holy.png, nova_rend.png, nova_sun.png, palm.png, palm_storm.png, palm_temple.png, perennial.png, plague.png, pyre.png, retaura.png, risen.png, ruin.png, sanctify.png, scent.png, shard.png, shard_deep.png, shatter.png, shield.png, siphon.png, skull.png, slash_blood.png, slash_heavy.png, slash_holy.png, slash_quake.png, slash_spin.png, slash_steel.png, smoke.png, spear.png, spear_ice.png, spiritwolf.png, star.png, static.png, tether.png, tether2.png, tether_mark.png, thorn.png, triple.png, umbral.png, wing.png, wraith.png, zone_blight.png, zone_blight2.png, zone_bloom.png, zone_holy.png, zone_plague.png, zone_pyre.png, zone_root.png, zone_sanct.png, zone_thorn.png
- `godot/art/ui/icons/item/`: antidote.png, armor.png, armor_heavy.png, armor_light.png, axe.png, bandage.png, bomb.png, bone.png, book.png, bow.png, censer.png, chest.png, circlet.png, cleaver.png, cloak.png, dagger.png, dust.png, ember.png, fang.png, flower.png, helm.png, helm_light.png, hide.png, journal.png, kerchief.png, key.png, lamp.png, lantern.png, lens.png, map.png, mask.png, moon.png, pelt.png, picks.png, potion.png, ring.png, root.png, scroll.png, seed.png, shield.png, sigil.png, staff.png, sword.png, totem.png, vial.png, vial_orange.png, wand.png, wand_dark.png
- `godot/art/ui/medallion/`: ring.png
- `godot/art/ui/minimap/`: frame.png
- `godot/art/ui/ornaments/`: flourish.png, plaque_rule.png, rule.png
- `godot/art/ui/title/`: logo.png

### UI made without AI (forged in code or modelled in Blender, no paint-over) (86 files)

- `godot/art/ui/bars/`: ember_fill.png, experience_fill.png, health_fill.png
- `godot/art/ui/cursors/`: forbidden.png, hand.png, pointer.png
- `godot/art/ui/frames/`: focus.png
- `godot/art/ui/icons/glyph/`: amulet.png, armor.png, bolt_bone.png, bow.png, campfire.png, censer.png, cleaver.png, cloak.png, compass.png, crescent_holy.png, dash.png, drop.png, eye.png, firepot.png, frost.png, frost_orb.png, helm.png, hood.png, key.png, lock.png, map.png, mask.png, next.png, quest.png, relic.png, ring.png, scroll.png, sigil.png, slash.png, staff.png, stat_area.png, stat_armor.png, stat_cooldown.png, stat_critchance.png, stat_critdamage.png, stat_damage.png, stat_dashcharges.png, stat_dodge.png, stat_goldgain.png, stat_healing.png, stat_maxhealth.png, stat_movespeed.png, stat_pickupradius.png, stat_regen.png, stat_xpgain.png, sun.png, sword.png, talk.png, totem.png, venom_smoke.png, wand.png, zone.png, zone_fire_enemy.png, zone_venom.png
- `godot/art/ui/icons/map/`: danger.png, exit.png, mystery.png, person.png, place.png, quest.png, turn.png
- `godot/art/ui/icons/prompt/`: pad_a.png, pad_b.png, pad_dpad.png, pad_dpad_down.png, pad_dpad_left.png, pad_dpad_right.png, pad_dpad_up.png, pad_lb.png, pad_lstick.png, pad_lt.png, pad_menu.png, pad_rb.png, pad_rstick.png, pad_rt.png, pad_view.png, pad_x.png, pad_y.png
- `godot/art/ui/minimap/`: you.png

### Renders of the heroine (carry her Krea 2 face paint; body of unknown origin) (26 files)

- `godot/art/ui/create/female/`: face_doe.png, face_fey.png, face_hardwon.png, face_highborn.png, face_own.png, face_vixen.png, face_wildling.png, hair_bob.png, hair_bob_mask.png, hair_braid.png, hair_braid_mask.png, hair_long.png, hair_long_mask.png, hair_pixie.png, hair_pixie_mask.png, hair_ponytail.png, hair_ponytail_mask.png, look.png, paint_ash.png, paint_blood.png, paint_gilt.png, paint_kohl.png, paint_none.png, paint_ochre.png, paint_rouge.png, paint_woad.png

### Voice placeholders: Maya1 performance, Seed-VC conversion, VoxCPM2-designed voice (19 files)

- `godot/art/vo/grimtunnel/`: dlg.cin_heart_goes_down.downstairs.0.ogg, dlg.cin_heart_goes_down.grateful.0.ogg, dlg.cin_heart_goes_down.nobodys.0.ogg
- `godot/art/vo/guard/`: dlg.cin_first_light.dawn.0.ogg
- `godot/art/vo/narrator/`: dlg.cin_drowned_fire.bedroll.0.ogg, dlg.cin_drowned_fire.frost.0.ogg, dlg.cin_drowned_fire.prints.0.ogg, dlg.cin_first_light.back.0.ogg, dlg.cin_first_light.baking.0.ogg, dlg.cin_first_light.face.0.ogg, say.178e6dd0ad78.ogg, say.3dcd3f3caa00.ogg, say.4d8a46e7502e.ogg, say.dabd6c78b40d.ogg
- `godot/art/vo/warden/`: dlg.cin_none_cross.call.0.ogg, dlg.cin_none_cross.lie_down.0.ogg, dlg.cin_none_cross.none.0.ogg
- `godot/art/vo/warden_man/`: dlg.cin_heart_goes_down.morning.0.ogg
- `godot/art/vo/watchman/`: say.b81f9a1e8df8.ogg

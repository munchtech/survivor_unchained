# Steam submission checklist

Everything needed for a clean Steam submission of Survivor Unchained, with draft wording for the AI disclosure and the content survey. The reasons and sources are in `LEGAL_BRIEF.md` (issue numbers in brackets).

Prepared 4 October 2026 by the legal lead (aa12c130ddf4b904c), and updated that evening by its successor (aab20546fe06daa89) for the owner's answers: he lives in the US; "Warmed" is flavour only; the bodies are to be replaced; the hymn is from Suno. Not legal advice. The Steamworks forms are the authority: re-read each one when you fill it in, and change the wording here if the form has changed.

---

## A. Before you can submit (owner)

- [ ] Decide who signs the Steam Distribution Agreement: yourself as a sole proprietor, or a company. Ask the lawyer first [27].
- [ ] Have to hand:
  - legal name and company form, with no aliases;
  - a bank account in that exact name;
  - tax details. The owner lives in the US, so this is a **W-9**: his SSN as a sole proprietor, or the company's EIN. Verification takes 10 to 15 business days.
- [ ] Pay the US$100 app fee. You can't release until **21 days** after paying it.
- [ ] Publish a "Coming soon" page for **at least two weeks** before release.
- [ ] Plan at least **7 business days** each for store-page review and build review. Adult Only content takes longer.

Source: https://partner.steamgames.com/doc/gettingstarted/onboarding (read 4 Oct 2026).

## B. Fix before the build goes up (main session and leads)

- [x] **Debug paths out of release** [3]. Done by the performance lead (8a770667). The `.pck` listing (`docs/legal/records/RELEASE_PACK_LISTING.txt`, 4 Oct) has been reviewed by legal: nothing excluded ships, and the release build ignores the switches. Re-list the pack before every upload.
  - `--body` and other developer arguments only when `OS.IsDebugBuild()`;
  - `tools_scenes/*` excluded;
  - unused bodies and packs excluded, among them `anime_female.glb`, `woman.glb`, the KayKit characters and the git-ignored Poly Haven copies;
  - check the `.pck` listing before upload.
- [x] **Explicit-scene placeholders out of release data** [6]: the three `[explicit scene: … — to be written]` texts. Removed by the story lead (efc15256); `StoryLint` guards it. Tick for good once merged.
- [x] **Placeholder voices** [11]: dropped from release (`art/vo/*` excluded; the listing confirms none ship). Finals will be added with their own ledger lines.
- [ ] **Licence notices and credits ship** [4]:
  - a "Credits and licences" screen;
  - a `licences/` folder beside the executable, containing:
    - `GODOT_LICENSE.txt` and `GODOT_COPYRIGHT.txt`;
    - the .NET `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT`;
    - `OFL-Alegreya.txt`, `OFL-AlegreyaSans.txt` and `OFL-Cinzel.txt`;
    - `CREDITS.txt`, holding every CC BY credit and the AI tools line (section E).
- [ ] **Asset blockers cleared** [5]:
  - the boar replaced with our own, or the Fab commercial version bought as a stop-gap, with the receipt kept;
  - the heroine's and hero's base bodies **kept, with conditions** (re-ruled 4 Oct, evening). They are local Krea 2 Turbo pictures made into meshes by TRELLIS 2. The owner:
    - signs the record in `docs/legal/records/BODIES_RECORD.md`;
    - confirms no real person and no one else's art went into the pictures;
    - confirms which LoRA the hero's picture used.

    The bodies count in the Krea footprint [8];
  - `woman.glb` excluded from the build (done, 8a770667);
  - no Hunyuan3D output ships, in any version, local or from Krea's website.
- [x] ~~The Ember Watch's chain of title~~ [5e]: the owner made it with Claude, and no third party is involved. **Keep the records** listed in brief issue 5(e), and sign the short authorship statement.
- [ ] **"Warmed" is flavour only** [7]: the story lead's b47d98ea. Tick once it is merged; then answer "no" to sex linked to rewards.
- [ ] **Recommended** [15]: rename Moonfire, Fan of Knives and Starfall. Replace or clear the sword and shield made from other artists' concept art.
- [ ] **Motion check** [2]: in motion, with jiggle on and at close range, confirm that no nipple, areola or genital area ever shows on any outfit. Fix it or disclose it.
  - **The Warden's left cup: fixed** (854b927e). Verified with jiggle on in close front, three-quarter and overhead views: no areola shows.
  - **The Warden's crotch:** my first reading counted the groin beside her thong (`warden.thong`) and is withdrawn. She is to be re-counted against the narrow strip, the vulva's footprint, on the next build.
  - The second, automatic pass covers every clip for all four outfits (brief issue 2); it is in progress.
  - Re-run it after any outfit or body change, and before upload.
- [ ] **Icon check** [14]: icons made from the old style-named prompts compared with Diablo IV and Hades; any close one remade.

## C. Store page

- [ ] **Capsules** (header, small, main, vertical, library hero and logo): game art and the title only, with no review scores, awards or marketing text. **PG-13 artwork** on every capsule, including the heroine [23].
- [ ] **Screenshots:** gameplay only, with no concept art, pre-rendered cinematic stills or marketing text. Show only what's in the game at launch.
- [ ] **Description:** detailed and coherent, with no links to other stores. Anything planned must be clearly marked as not yet released.
- [ ] **Trailer:** if mature, it is shown behind the same content warnings as the page.
- [ ] **Supported OS:** Windows (and Linux and macOS only if those builds are tested). Each listed OS must launch in review.
- [ ] **Features ticked in Basic Info:** only what the build has (no cloud saves, achievements or controller support unless implemented). The build has a pad scheme; tick controller support only after testing.
- [ ] **AI disclosure** written for the page (section D3).
- [ ] **Legal lines:** the copyright line "© 2026 [owner's legal name or company]". Add a trademark notice only once a mark is filed or registered [17].
- [ ] **EULA:** none needed. The Steam Subscriber Agreement applies by default [21]. Add one only if the lawyer advises it.
- [ ] **Privacy policy:** none needed while the game collects nothing [20].

Sources: https://partner.steamgames.com/doc/store/assets/rules and https://partner.steamgames.com/doc/store/review_process (read 4 Oct 2026).

## D. Content survey: draft answers

The survey has three parts: General Content (which generates the regional ratings), Mature Content, and Generative AI. Valve compares the answers with the build and the page. **Disclose everything uploaded, even what can't be reached in play.**

### D1. General Content (drives the regional ratings, Germany and Indonesia included)

The question wording varies. Answer from these facts.

| Topic | Answer for this game |
|---|---|
| Violence | Yes: frequent, realistic-to-stylised fantasy violence against humans, undead and animals, with blood, gibs (bodies burst under heavy blows) and corpses that remain briefly. Player-controlled. A gore setting reduces or removes the blood. |
| Sexual content | Yes, non-explicit: optional romances between adults. Sexual activity is implied in text and ends before any act (a "cut-away"). One romance involves paying a sex worker. No sexual violence; no minors. |
| Nudity | Partial: revealing outfits that leave the buttocks and the underside of the breasts bare. Nipples show as shapes through clothing. No exposed nipples or genitals in play. The 3D body model has anatomical detail that outfits always cover. |
| Sexual content linked to rewards | **No**, once b47d98ea is merged. "Warmed" then only records that the night happened, with no effect on play [7]. Relationship values (affection, trust) still rise; the lawyer is to confirm that this isn't a "reward" in the Australian sense. Until the merge, the honest answer is yes. |
| Language | Infrequent strong language ("fucking", once), plus milder swearing. |
| Drugs, alcohol, tobacco | Alcohol is referenced (an inn; characters drink). No drug use. |
| Gambling, simulated gambling, loot boxes | None. |
| In-game purchases | None. |
| User interaction, chat, user-generated content | None (single player, offline). |
| Location sharing, data collection | None. |
| Horror and fear | Undead, dark themes, death. |
| Discrimination and hate | None. |

**Ratings section:**
- Enter no USK, PEGI, ESRB or IGRS ratings unless that body reviewed this exact build.
- Never enter an IARC-generated rating from another store.
- If you obtain an Australian classification [22], enter it here and enable the age gate.

### D2. Mature Content

Tick:
- [x] **General Mature Content**
- [x] **Frequent Violence or Gore**
- [x] **Some Nudity or Sexual Content**
- [ ] **Adult Only Sexual Content**: **no**, while the game stays non-explicit [6].

**Draft description for players** (Steam shows this text):

> Survivor Unchained is a dark fantasy action RPG for adults.
> - **Violence and gore:** constant combat against hordes of the dead, beasts and people, with blood and bodies that burst under heavy blows. A setting reduces the gore.
> - **Nudity and sexual themes:** the heroine wears revealing armour that leaves her buttocks and the underside of her breasts bare, with breast and body physics. There is no full nudity. Optional romances between adult characters include a paid night with a courtesan. Love scenes are written, not shown, and end before any sexual act.
> - **Mature themes:** death, the undead, grief and sex work; occasional strong language.

**Draft note for Valve's reviewers** (the free-text field, if offered):

> The heroine's 3D body is modelled with anatomical detail: breasts with nipples, and buttocks; no genitals are modelled. Every outfit covers the nipples in normal play. Some outfits leave the buttocks and underbust bare. The male hero's body likewise has bare buttocks under his clothing. Neither character can be undressed in the game. Love scenes are text only and end before any act. No content is generated by AI while the game runs.

Before submitting, adjust these sentences:
- **Crotch:** confirmed (4 Oct): a smooth form; no genitals are modelled. If the Warden's skirt still shows it at submission, say so (see the motion check in B).
- **Release build:** confirm the debug body is gone.
- **Hero's garment:** once he has his base garment, say that he is never bare.

### D3. Generative AI

- **Pre-generated AI content:** Yes.
- **Live-generated AI content:** No. The game makes no AI calls and no network calls while it runs.
- **Adult Only Sexual Content generated live:** not applicable.

**Draft disclosure** (shown on the store page; trim to the field's limit):

> Survivor Unchained is made by a solo developer working with AI tools, under his direction and with every asset reviewed by a person before it ships.
> - **Art:** AI image models, run locally, painted the interface art, icons, character face textures and some ground detail. AI image-to-3D tools made base meshes that were then rebuilt, rigged and textured.
> - **Music:** the hymn sung at a graveside was generated with Suno from lyrics written for the game. The rest of the music is synthesised by the game itself.
> - **Effects and sound:** an AI video and audio model generated some visual-effect animations and a few sound effects.
> - **Animation:** some motion was generated by an AI motion model, then retargeted and edited. The rest is hand-keyed or from licensed motion libraries.
> - **Writing:** the story, dialogue and item text were drafted with an AI writing assistant from the developer's design, then directed and edited.
> - **Voices:** character voices are synthetic voices designed for each character with ElevenLabs. No real actor's voice was cloned.
> - No AI generates content while you play.

Edit it to match the build at submission:
- Remove the voices bullet if no voice ships, and say "placeholder synthetic voices" if placeholders ship.
- If the owner records his own voice, say so.
- If the capsule, trailer or store art was made with AI, add: "Some store artwork was created with the help of AI image tools."
- The bodies stay (issue 5(b)), so keep "AI image-to-3D tools made base meshes" for as long as they ship.
- Drop the music bullet if the Suno hymn doesn't ship.

## E. Credits: the AI tools section [9, 24]

**One list, kept in one place:** the "Made with AI tools (disclosure)" section of `public/assets/CREDITS.md`. The screen and `licences/CREDITS.txt` are generated from it, and the Steam disclosure (D3) says the same in prose. It names only what is in the release build.

For the release as exported now (8a770667: no placeholder voices, no hero body), the section should read:

> Parts of the game were made with generative AI during development. Some images, 3D models, effects, sounds, motion and text in it were generated by AI, then reviewed and edited by the developer. Nothing is generated by AI while you play.
> - Images: most of the interface's painted art and icons, the ground marks of blows and spells, the heroine's face paint and irises, and the picture her body was sculpted from were made with Krea 2 (Krea 2 Community License); the interface's with Krea's darkbrush LoRA. Cut-outs used BiRefNet (MIT).
> - 3D: the heroine's base body was sculpted by TRELLIS 2 (Microsoft, MIT) with DINOv3 (Meta), then rebuilt and rigged for the game.
> - Effects video and some combat sounds were made with LTX 2.5 (Lightricks, LTX-2.x Community License), with Gemma 4 as its text encoder (Apache-2.0). This content is machine generated.
> - Motion: NVIDIA Kimodo (above).
> - Code and writing were written with Claude (Anthropic) under the owner's direction.

**Add each line only when what it covers ships:**
- **The hero** (when `hero.glb` ships): "the heroes' face paint", and his body in the 3D line. If the owner confirms it, add the "Mystic XXX" LoRA by alcaitiff (Civitai) to the images line. Credit isn't required, but it is accurate. Put "and the hero's" back in two other credits lines too:
  - the Reallusion AccuRIG line;
  - the MakeHuman heads line.

  Both drop it while he is excluded (UI design, after a185aea3).
- **Voices** (when finals ship): "Character voices are synthetic voices designed with ElevenLabs. No real person's voice is cloned." Add "voices" to the opening sentence.
- **Music** (when the hymn ships): "The graveside hymn was generated with Suno from lyrics written for the game." Add "music" to the opening sentence.

**Not in the list:**
- Pixal3D and the voice shoot-out models (never shipped);
- the placeholder-voice tools Maya1, Seed-VC and VoxCPM2 (excluded from release);
- MoGe 2 (the hero's TRELLIS 2 run doesn't load it).

**What has to be named, and why:**
- LTX's "machine generated" sentence is required (LTX-2.x Attachment A).
- The Krea 2 licence asks for disclosure where a platform requires it, which Steam does.
- Everything else is accuracy and courtesy.

Then add every CC BY credit in this form:

> "Title" by Author (link), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Modified: [what we changed].

Also add the fonts (SIL OFL 1.1), Godot Engine (MIT) and .NET (MIT).

## F. Regional checks after submission

- [ ] **Germany:** the game receives a rating from Steam's survey. Check the "missing rating" health page: https://partner.steamgames.com/healthcheck/missingratingforgermany/
- [ ] **Indonesia:** the same check: https://partner.steamgames.com/healthcheck/missingrequiredratings
- [ ] **Australia:**
  - With the buff gone [7], the survey answers no longer force R18+. MA 15+ allows implied sexual activity and nudity "justified by context", provided neither is tied to rewards.
  - Expect the age gate either way: since 9 Sep 2026, Australian users need a credit card to see mature content.
  - Lawyer: whether to seek a formal classification [22].
- [ ] **UK:** mature-flagged pages need credit-card age verification. Nothing for us to do, but expect fewer UK views.

## G. After release

- [ ] Any new content that changes a survey answer: contact Steam Support with a summary, the affected answer, and how a tester reaches the content. Some answers lock after approval.
- [ ] Keep the AI asset ledger and the provenance file current with every new asset.
- [ ] Watch revenue against the **Krea US$1M** and **LTX US$10M** thresholds [8, 9].
- [ ] **US copyright registration** of the game, within three months of release, to keep statutory damages and fees available [5e, 16]. The lawyer drafts the claim, which excludes the AI-generated material.

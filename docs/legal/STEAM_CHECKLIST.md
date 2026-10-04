# Steam submission checklist

Everything needed for a clean Steam submission of Survivor Unchained, with draft wording for the AI disclosure and the content survey. The reasons and sources are in `LEGAL_BRIEF.md` (issue numbers in brackets).

Prepared 4 October 2026 by the legal lead (aa12c130ddf4b904c). Not legal advice. The Steamworks forms are the authority: re-read each one when you fill it in, and change the wording here if the form has changed.

---

## A. Before you can submit (owner)

- [ ] Decide who signs the Steam Distribution Agreement: yourself as a sole proprietor, or a company. Ask the lawyer first [27].
- [ ] Have to hand:
  - legal name and company form, with no aliases;
  - a bank account in that exact name;
  - tax details (W-9 or W-8BEN style; verification takes 10 to 15 business days).
- [ ] Pay the US$100 app fee. You can't release until **21 days** after paying it.
- [ ] Publish a "Coming soon" page for **at least two weeks** before release.
- [ ] Plan at least **7 business days** each for store-page review and build review. Adult Only content takes longer.

Source: https://partner.steamgames.com/doc/gettingstarted/onboarding (read 4 Oct 2026).

## B. Fix before the build goes up (main session and leads)

- [ ] **Debug paths out of release** [3]:
  - `--body` and other developer arguments only when `OS.IsDebugBuild()`;
  - `tools_scenes/*` excluded;
  - unused bodies and packs excluded, among them `anime_female.glb`, `woman.glb`, the KayKit characters and the git-ignored Poly Haven copies;
  - check the `.pck` listing before upload.
- [ ] **Explicit-scene placeholders out of release data** [6]: the six `[explicit scene: … — to be written]` texts behind `settings.intimacy == "full"`.
- [ ] **Placeholder voices** [11]: replaced by finals, or dropped from release (they're marked `placeholder` in the index).
- [ ] **Licence notices and credits ship** [4]:
  - a "Credits and licences" screen;
  - a `licences/` folder beside the executable, containing:
    - `GODOT_LICENSE.txt` and `GODOT_COPYRIGHT.txt`;
    - the .NET `LICENSE.TXT` and `THIRD-PARTY-NOTICES.TXT`;
    - `OFL-Alegreya.txt`, `OFL-AlegreyaSans.txt` and `OFL-Cinzel.txt`;
    - `CREDITS.txt`, holding every CC BY credit and the AI tools line (section E).
- [ ] **Asset blockers cleared** [5]:
  - the boar bought on Fab or replaced;
  - the sources of the heroine's and hero's base bodies and pictures confirmed, and anything not ours remade;
  - no Hunyuan3D-2 output ships.
- [ ] **Recommended, not required** [7]: decouple the "Warmed" buff from the love scenes.
- [ ] **Recommended** [15]: rename Moonfire, Fan of Knives and Starfall. Replace or clear the sword and shield made from other artists' concept art.
- [ ] **Motion check** [2]: in motion, with jiggle on and at close range, confirm that no nipple, areola or genital area ever shows on any outfit. Fix it or disclose it.
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
| Sexual content linked to rewards | **Currently yes** (a temporary combat buff after a love scene). If issue 7 is fixed before submission, answer "no". |
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
- **Crotch:** confirm the heroine's crotch is a smooth form. If genitals are modelled, say so.
- **Release build:** confirm the debug body is gone.
- **Hero's garment:** once he has his base garment, say that he is never bare.

### D3. Generative AI

- **Pre-generated AI content:** Yes.
- **Live-generated AI content:** No. The game makes no AI calls and no network calls while it runs.
- **Adult Only Sexual Content generated live:** not applicable.

**Draft disclosure** (shown on the store page; trim to the field's limit):

> Survivor Unchained is made by a solo developer working with AI tools, under his direction and with every asset reviewed by a person before it ships.
> - **Art:** AI image models, run locally, painted the interface art, icons, character face textures and some ground detail. AI image-to-3D tools made base meshes that were then rebuilt, rigged and textured.
> - **Effects and sound:** an AI video and audio model generated some visual-effect animations and a few sound effects.
> - **Animation:** some motion was generated by an AI motion model, then retargeted and edited. The rest is hand-keyed or from licensed motion libraries.
> - **Writing:** the story, dialogue and item text were drafted with an AI writing assistant from the developer's design, then directed and edited.
> - **Voices:** character voices are synthetic voices designed for each character with ElevenLabs. No real actor's voice was cloned.
> - No AI generates content while you play.

Edit it to match the build at submission:
- Remove the voices bullet if no voice ships, and say "placeholder synthetic voices" if placeholders ship.
- If the owner records his own voice, say so.
- If the capsule, trailer or store art was made with AI, add: "Some store artwork was created with the help of AI image tools."

## E. Credits: the AI tools line [9, 24]

Put this in the in-game credits and in `CREDITS.txt`:

> Made with the help of AI tools: Krea 2 (Krea 2 Community License), LTX-2.5 (LTX-2.x Community License; some visual effects and sound effects are machine-generated), TRELLIS 2, Pixal3D, NVIDIA Kimodo, ElevenLabs voices, and writing assistance from Claude (Anthropic). Some images, effects, sounds, motion, voices and text in this game were generated by AI and reviewed and edited by the developer.

Then add every CC BY credit in this form:

> "Title" by Author (link), licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Modified: [what we changed].

Also add the fonts (SIL OFL 1.1), Godot Engine (MIT) and .NET (MIT).

## F. Regional checks after submission

- [ ] **Germany:** the game receives a rating from Steam's survey. Check the "missing rating" health page: https://partner.steamgames.com/healthcheck/missingratingforgermany/
- [ ] **Indonesia:** the same check: https://partner.steamgames.com/healthcheck/missingrequiredratings
- [ ] **Australia:**
  - The game will be treated as R18+ and age-gated, with a credit card required since 9 Sep 2026.
  - It will be **MA15+-eligible only** if the buff is decoupled [7].
  - Lawyer: whether to seek a formal classification [22].
- [ ] **UK:** mature-flagged pages need credit-card age verification. Nothing for us to do, but expect fewer UK views.

## G. After release

- [ ] Any new content that changes a survey answer: contact Steam Support with a summary, the affected answer, and how a tester reaches the content. Some answers lock after approval.
- [ ] Keep the AI asset ledger and the provenance file current with every new asset.
- [ ] Watch revenue against the **Krea US$1M** and **LTX US$10M** thresholds [8, 9].

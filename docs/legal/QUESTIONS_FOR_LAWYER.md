# Questions for a games lawyer

Survivor Unchained is a Godot (C#) survivors and action RPG for adults, to be sold on Steam. It is made by one owner with AI agents and AI generators. The background, evidence and sources are in `LEGAL_BRIEF.md` (issue numbers in brackets). Prepared 4 October 2026 by the legal lead (an AI agent, not a lawyer).

Updated the same evening by the successor legal lead (aab20546fe06daa89) for the owner's answers.

**Facts to give counsel first:**
- **Residence: the United States** (owner, 4 Oct 2026). His **state** is still to be given; it matters for question 12.
- Whether he trades personally or through a company: not yet decided (question 12).
- Expected first-year revenue: not yet given.
- The owner made The Ember Watch, the source of the world and lore, himself with Claude. No third party is involved.
- "Warmed" no longer has any effect in play.
- The heroes' base bodies were made locally: Krea 2 Turbo pictures, made into meshes by TRELLIS 2. They are kept, with conditions.
- The hymn will be made in Suno.

These change several answers below.

## Ownership and AI

1. **Krea 2 revenue cap** [8].
   - Krea's Community License allows commercial use of *Outputs* only while company-wide revenue is under US$1M (trailing twelve months). It is revocable on 30 days' notice, and §9.4 requires destroying only the "Model and Derivatives".
   - If revenue crosses US$1M, or Krea terminates, may we keep selling a game that already contains Krea outputs made under the licence?
   - What should an enterprise licence cover?
2. **Our copyright position and registration** [5e, 16].
   - Most assets, the code and the text were produced by AI (generators and agents) under the owner's direction, with selection and editing. The world and lore come from The Ember Watch, which the owner also made with Claude.
   - In the US, UK and EU, what do we own in practice?
   - Should we register the finished game in the US around launch? If so:
     - how should the claim describe the human contribution, and exclude the AI-generated code, text, art and music?
     - one registration, or several (the program, the audiovisual work, the text)?
   - Please review the records list in brief issue 5(e), and draft the owner's short signed statement of authorship. It should say that the `stevenrogerino`, `munchtech` and `munch4lunchbot` accounts are his, and that no one else contributed.
3. **LTX-2.x provenance clause** [9]. Does converting LTX video and audio outputs into sprite sheets and OGG files breach the bar on removing "metadata, watermarking, content provenance" from Outputs, if we keep the original outputs archived?
4. **Seed-VC (GPL-3.0)** [11]. Confirm that audio made with GPL-licensed voice-conversion weights carries no GPL obligation, if any placeholder voice ships.
5. **ElevenLabs** [12].
   - (a) ~~Which terms apply given the owner's residence?~~ Answered: he lives in the US, so the non-EEA Terms of Service apply.
   - (b) Does running speech recognition, a quality score and a speaker embedding on our own takes, only to check them, count as using Output "as input for any machine learning" (Prohibited Use Policy 9(k))?
   - (c) Could Policy 2(c), which bars facilitating "sexual services", be read against fictional dialogue for a courtesan character?
   - (d) Do we need an enterprise agreement to stop our unreleased scripts being covered by ElevenLabs' perpetual licence to Content?

## Content and ratings

6. **Steam survey scope** [2, 3]. Is our planned disclosure of the hidden anatomical detail, with debug paths and unused bodies removed from the build, enough to meet "disclose all the adult content you've uploaded"?
7. **Australia** [7, 22].
   - The love scenes used to grant a combat buff. The owner has removed it: "Warmed" now only records that the night happened (b47d98ea).
   - The scenes still raise affection and trust, which open later romance content. Does that relationship progress count as an "incentive or reward" under the 2023 guidelines? If not, can the game be MA 15+?
   - Should we obtain a formal classification, or rely on Steam's self-rating?
8. **Explicit content strategy** [6, 25]. If the owner later wants explicit love scenes, is a separate Adult Only DLC the right structure? What are the risks under Valve's July 2025 payment-network rule, Germany's youth-protection law (JuSchG and JMStV), and the UK and Australian age-assurance regimes?

## Third-party material and brand

9. **The boar and the derivative props** [5].
   - A Sketchfab model is labelled CC BY 4.0 while its description says personal use only. Is buying the Fab version enough, or should we simply replace it?
   - The CC BY sword and shield are based on other artists' concept art. Replace them, or get permission?
10. **"Survivor Unchained"** [17].
    - Please run, or commission, a clearance search: USPTO, UKIPO, EUIPO and WIPO; classes 9, 41 and 28.
    - Is CBS's SURVIVOR family a real obstacle?
    - Should we file, and where?
11. **Skill names** [15]. Is any risk left in generic spell names (Consecration, Whirlwind) once the distinctive Warcraft names are renamed?

## Business

12. **Structure** [27]. The owner lives in the US; his state is to be given.
    - Should he trade as a sole proprietor or through an LLC before signing the Steam Distribution Agreement?
    - How does that interact with the "affiliated entities" revenue tests in the Krea and LTX licences?
13. **Voice release** [13]. Please draft a short written consent and licence for the owner's own voice, or a performer's, for AI cloning: scope, term, payment and withdrawal.
14. **EULA** [21]. Is the Steam Subscriber Agreement enough, or do you recommend a short game-specific EULA (modding, AI disclosure, adult content acknowledgement)?

## Added after the owner's answers (4 October 2026, evening)

15. **The base bodies** [5b]. Corrected by the owner: the pictures were made locally with the Krea 2 Turbo open weights, and the meshes locally with TRELLIS 2 (MIT). Krea's website was not involved. The hero's picture probably used a Civitai LoRA whose creator allows commercial use of images; its training data is unpublished.
    - Is the owner's signed record (`docs/legal/records/BODIES_RECORD.md`) enough evidence?
    - Is a mesh made from a Krea Output itself "commercial use of Outputs" under §2.3 (the US$1M cap)? We assume so.
    - Does a third-party LoRA's unknown training data add any exposure beyond the base model's own unsettled training question?
16. **Suno for the hymn** [28].
    - On a Pro or Premier plan, Suno assigns its rights in Output to the user, and commercial use needs a permitted download. Is that enough for a song in a commercial game and its trailers?
    - What is our exposure if the labels' litigation against Suno ever finds its outputs infringing, given a song from our own lyrics with no artist or song named in the prompt?
    - Suno's terms say rights holders "may also have the right to collect revenue" on third-party platforms. How should we handle automated claims on trailers?
17. **Replacement assets made with AI** [5g]. Is our preference order sound?
    - Our own work first.
    - Then local models with unrestricted licences, from inputs we own.
    - Krea 2 only knowing it adds to the revenue cap.
    - Never Hunyuan3D, free-plan web tools, or pictures of real people or others' art.
18. **Is the heroine the owner's authorship?** [16]
    - Her body began as a TRELLIS 2 mesh from a Krea 2 picture. AI agents then resculpted and edited it at length in Blender, following the owner's direction: briefs, drawn markups, specific choices, and rejections of earlier rounds.
    - (a) Do the owner's directed iterations count as authorship? Where he set the exact shape (a markup, a measurement, a choice between options he specified), is that human control over expression? Or is it, in the Copyright Office's words, "re-rolling" that "does not change this analysis"?
    - Does an agent carrying out precise edits in a 3D tool differ, for authorship, from a prompt-to-image model?
    - (b) Does his selection and arrangement of the heroine as a whole qualify, as *Zarya of the Dawn*'s arrangement did? Body, head, outfits, hair, paint, proportions, and her character as written. If so, what should a registration claim, and what should it exclude?
    - What records best prove his contribution?
19. **Does the Krea 2 cap reach her reworked body?** [8, 16]
    - TRELLIS 2 made a mesh from a Krea 2 Turbo picture, and it was then heavily reworked.
    - The licence defines "Output" as content "generated by the Krea Model", which the mesh isn't. It defines "Derivative" as a modified *model*.
    - But "Commercial Use" is "any use of the Krea Model, Derivatives, or Outputs … directly or indirectly".
    - Does §2.3's US$1M threshold, or termination under §9.2 and §9.4, reach the shipped mesh? If so, does enough rework ever end that?
    - Her face paint and irises are direct Outputs, and we assume they are covered.

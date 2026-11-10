# P3 NPCs and creatures: lead 1 (coordinator #3, 9 Nov evening)

Context budget: 200k

**Why now.** The owner, 9 Nov evening, named four goals: "aaa quality. casually badass character with epic effects, a solid pipeline for armor creation and npc creation with marionette and a unique art style". No lead was on NPC creation. Also: "don't worry about the cost ... no budget just make it awesome" (lead_brief "Usage rules": the waste rules stay).

**What P3 is** (`docs/team/PIPELINE.md` P3 row, and "Marionette is the pipe"): source = Meshy generation from a JUDGED concept; build = the Marionette fixer (clean, painterly repaint, wrap to the base, rig on the base rig, export); check = the same bend strips as P1; judged once at the dialogue camera (NPCs) or the play camera (creatures). Every stage is a Marionette app tool with a build command and a check command, never a loose script one lead drives. Reports say "the app can now X".

**Where you work.** `C:\Users\munch\Desktop\Marionette` is on branch `npcgen-1` (pushed to origin; the earlier NPC generation and fixer work is there): that checkout is yours. Read `HANDOFF.md` "Start here" (lines 5-16) and only the sections it or your plan needs. A1 owns `C:\Users\munch\Desktop\Marionette_motion` (motion-a1): never touch it. The game repo is at its worktree cap (8): you have NO game worktree yet; read game files by absolute path from `C:\Users\munch\Desktop\survivorsunchained` (never edit or run git there). When you need in-game dialogue-camera shots, ask main for a slot. Your handoff file: `HANDOFF_P3.md` at the Marionette root (top block = the next lead's start pack).

**The owner's standing rules for NPCs (do not re-ask):**
- NPCs are GENERATED FULLY DRESSED (Meshy-style); no clothes or armor layers on NPCs. Layers and drag-and-drop gear are for the main characters only.
- Meshy only AFTER a judge approves the concept image. Nothing that needs crediting ships. Meshy Pro = generator, Marionette = fixer. Never OpenAI through Meshy. Generation dollars: $250/month cap stands (it is money, not tokens); tell main before it would be passed.
- The bar is Meshy/Tripo PARITY or better, judged at the CLOSEST framing the player sees (dialogue, chest-up): the armored guard was "really bad" chest-up on 21 Oct.
- Foundation, not test models: general fixes as reusable tools over one-model patches. Improve, don't preserve: better anatomy and clean lines over a faithful copy of the AI sculpt. Clean faces: no blotches or lopsided marks. Far behind after the first failed judge = scrap and regenerate, not patch.
- Grimtunnel and the Warden will be remade by P3 (the Warden is boss tier, a full-detail rebuild): later in your list, after the pipe proves on ordinary NPCs.
- Concept images: the ChatGPT imaging route (one driver at a time via `chatgpt.lock`; grep the game's `docs/team/README.md` for it).

**Dependencies.** The base rig and the bend check come from P1 (body picked "B, go" 9 Nov; `docs/handoff/body.md` top in the game repo says what landed and where). The painterly repaint must follow L1's look, which is NOT locked (L1 lead 11 is rebuilding night lighting; G2 not picked): build the repaint as a stage that takes the look's material and palette data as input, prove the other stages now, and do not lock a paint before G2. Anything you need from P1, P2 or L1 goes through main.

**First.** Orient within 60k, then send main your plan: the stages, which tools exist on `npcgen-1` and their true state (run them, don't trust the notes), which are missing, and a first proof set of three that spans the range (an ordinary townsperson, an armored guard, a creature), in build order with what "done" is for each stage (a command, a check, a number). Then build stage by stage. Judges per lead_brief (su-lead-max, foreground, 1:1 frames, own look first).

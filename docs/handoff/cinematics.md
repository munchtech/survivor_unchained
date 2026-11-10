# Cinematics: handoff

**H4 seams (3 Nov, seams-h4): every hand-back now goes through one cut rule (`godot/src/Game/GameSeam.cs`, measured by `--cutlog` + `tools/experience/cut_check.py`); C02 s5's swing, C03's walk-up and C04a's steered walk are being restaged there: see `docs/handoff/experience.md` "H4 seams" before touching c02/c03/c04a.**

**Face 49 (1 Nov) changed two shipped shots** (max SHIP; details in docs/handoff/face.md "Face 49"): C02 s8 lost its warm grade cue (zone night grade now), brighter lantern panes, the lantern key moved 25 deg toward the lens; C03 s8 restaged to a 3/4 front with the head nod halved (owner: "the neck looks wild there"), the heart's rigs as her key. C02 s4 stays cut. New cue knobs: `skin` `rim`, `lamp` `light`.

## MR READY: Cinematics 11 (29 Oct), branch cine-9: the reshoots are done; 3 max judge rounds (cap used)
**Final cuts (max r3 SHIP; every NO was cut, none closed as known):**
- **C02** plays s1, s2, s5, s8, s11, s12. W1 `call` is back on s2 (fit), heard before he is seen. s5: he rises from the water and the move ends on his lantern (the kneelers are pushed back into the fog, his boots ankle-deep). s8: her CU with his blue-white lantern in the lower-left corner as her ONLY key, "Lie down.". s11: the boss title lower-left, him backlit and tall on `folk/m_idle_armed`. CUT: s4 (her moonlit CU, NO twice: her skin goes bronze under cool low light), s6, s7, s10 (s3 and s9 stay cut).
- **C03** plays s1, s6, s8, s12. s1 is a 150 mm ECU lit only by his eye glow: two eye rigs, plus the `lamp` cue `"glint": 0` (new knob), and the bars are in from the start. "Is it morning?" plays over s6's fall, with the title after it. CUT: s2 (lit beard), s3b (her flat warm key on a cold night, NO in r2 and r3). s3b's world-state cues moved to the start of s6.
- **C01** s12: rear 3/4 at shoulder height, frost ahead past the firelight, fire 0.38 plus a warm rim rig (PASS r2, confirmed r3). The close-up rig doesn't trigger from behind.
**The game can now:**
- `skin` cue `off` (the close rig's parts off for a shot), `fill`, `fillColor`, `scale` (the face cap).
- `rig` cue `shadow` and `size`.
- `title` cue `place` (`lower`, `lower-left`; GameHud.Announce).
- `glow` cue `iron: "warden"`, `tilt`, `glass` (his lantern as a prop).
- `lamp` cue `glint`.
- Tests 1326/0/10.
**Routed (not fixed here):**
- **Face:** under cool or low light her skin goes bronze with a pink-white temple sheen. At extreme close-up it reads matte and low in saturation, so stage her at CU. The crown and braid read painted in a lit CU.
- **Warden:** the beard is still his brightest part at s11. The lamp fist and the beard tips show at s5's end. The cleaver reads flat white.
- **Env:** the ford's far treeline is pale-lilac cards, with a pink cliff (s5, s11).
- **UI:** his lines are labelled THE FORD-WARDEN before the s11 reveal (suggests "A VOICE IN THE WATER").
- **Not done:** the camp pack/saddlebags/bedroll rumple (unowned, play camera). Also C04 A0/A8b, still on the later list.
**Spend:** 6 medium solvers (~0.85M), 3 max judges (~0.37M), lead ~0.17M; API $0. Owner sheet: `survivorsunchained_inputs\cine11_owner\cine11_after_half.jpg`. Scratch backed up to `survivorsunchained_inputs\scratch_cine11` (verdicts r1/r2, shoot/jedit/sheet, edit scripts).

## MR READY: Cinematics 10 (29 Oct), branch cine-8: C01 done, the fixed list is empty
**C01 shipped cut (3 max judge rounds, cap used):** black 4 s with the `bedroll` line at 1.2 s -> s8a (the far lamp, lamp + call; PASS) -> s12 held on the crane's opening camera behind her, armed and firelit, the `frost` line (matched to the passed r4 frame on the PNGs) -> hard cut to play (PASS). About 24 s with the real takes. Cut: the shadow pan and prints shot (r1, far: darkness and stains; the `prints` line and its VO index entry are gone, `bedroll.next` = `lamp`), the bedroll close-up (r2, far), the rise s5, the breath s8, the turn s10 and the crane's middle (r3: her body surface, the braid, props; the risen read as lounging mannequins). The judge: don't spend more rounds there; if the owner misses the rise, stage it at the play camera. Docs: `docs/cinematics/shoot/c01.md`, `c01_drowned_fire.md`, the beat doc's top line.
**The camp set (first play space) rebuilt, PASS at the play camera (after beats before):** wool bedroll with a thick blanket (`OwnProps.cs` wool, albedo x0.65 after the judge; `tools/assets/env_props.py`, `env_wool_tile.py`), ring stones and ash bed on `Campfire.RingLayer` lit by a low `RingGlow` (`--campfire-ring K`), charred log ends, the crate and camp chest replaced by a pack and saddlebags (the tutorial's watch chest untouched). Judge's later marks (not fixed): the pack/saddlebags read as a board and a red box at play scale; the bedroll wants rumple.
**The game can now:** fire cue `lift`/`sway` (light raised over and drifting above burnt-down coals); pressed boot-print decals with normals and a `trample` amount; a `hair` cue (her hair swing, restored at the end); `--afterstills` (stills at +0.5/+2 s after control); her weapons hold through every cinematic and come back at control (her auto-attack had killed R1 on the first play frame); handover tests accept a last shot with no camera move.
**Merge notes:** GameCinema.cs changed (fire, prints, hair cue, weapon hold, afterstills), not its rig-light code (Face 48's); merge-tree with integration is clean at 436e05fcf. After Face 48 merges, main may ask for a C01 reshoot (s12's rigs are data: fill/bounce/eyes re-issued from the judged s8/s10 values). Tests 1308/0/10. Scratch backed up to `survivorsunchained_inputs\scratch_cine10` (briefs, verdict-bearing frames).
**Later list (unowned):** C02 s7 / his tired stance / lantern wait for Warden 6's model; C04 A0 (lamp place) and A8b (letter ink) kept for a later try (see Cinematics 9 below).


Older blocks: history/cinematics.md (grep by keyword, never read whole).

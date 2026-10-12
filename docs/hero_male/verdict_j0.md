# Judge j0: male hero body, keep or rebuild (12 Oct 2026)

**VERDICT: REBUILD-PATH-A, donor variant.** What the sculpt has at the bar is its surface detail on the front torso, arms and legs. The build type, back, posture, neck graft, face and skin all fail, and every change of shape on the 110k-triangle sculpt means a new bake. Rebuild on the MakeHuman man (one mesh, a native head, the MakeHuman rig and hands, the same UVs as her base). Use today's sculpt as a detail donor where it is right, so Path A starts at today's level of definition and doesn't have to earn it back with masks.

## Checklist
1. **Sex appeal: FAIL.** The front torso alone is striking (ab grid, V-taper). The whole body reads as a stage bodybuilder: traps climbing toward the earlobes, lats pushing the arms into a lat-spread idle, a shelf butt and swayback in profile, stage-size thighs. For most women that much mass is past the attractive peak, and men will read it as "gym", not "hero".
2. **Muscular and defined: NEAR.** Real separations in front: 3-row ab grid, linea alba, serratus, obliques, VMO teardrop, rectus femoris, calves, triceps, forearm veins. Smooth or wrong elsewhere: flat upper pecs, and no shoulder-blade landmarks on the back. His right lat is a smooth balloon, bigger than the left by more than the idle pose explains. The lats end in a sharp V fold with no erector columns, and the glutes are smooth. Type: classic-to-open bodybuilder (looks about 135-140 kg). That's wrong for a rugged 1.98 m hero. The target is an athletic heavyweight (looks about 110-118 kg).
3. **Proportion and scale: FAIL.** His height against hers is right (the 1.98/1.87 ratio holds in s2), and so is head height (about 7.4 heads). The head reads small only because the traps, shoulders and lats are oversized and the neck is a thin column under them. The arms hang a forearm's width off the ribs, the hands look soft and small next to the forearms, and the pelvis tips forward. Beside her he looks like a different build in a different material, not her equal.
4. **Face: FAIL.** Rugged, but gaunt and 45-55 years old (hollow cheeks, deep folds, heavy lids). The lower face is long and narrow with a soft jaw angle. The brows are painted as a dark smudge that bleeds onto the lids, and a dark band and crease run down his right cheek only (front view). The face is older than the body, far below her finished face, and pushed slightly forward in profile.
5. **Finish: FAIL.** Uniform orange-brown satin clay: no subsurface warmth, no pore or roughness detail, and shading baked into the color map. Visible errors:
   - a glossy vertical ridge on the right side of the neck and a hard crease under the jaw (the graft shows)
   - a dark fold on the right trap beside the neck
   - a dark dent in the left hip hollow (side view)
   - his left nipple is a raised, puffy disc (owner's taste: men's nipples flat)

   In s2, he and she look like they come from two different games.
6. **Against path A: PATH A (donor variant) is cheaper to the bar.** Keeping him saves only the detail on the front, arms and legs. The mass, back, posture, neck, face, hands and skin have to be redone anyway. The MakeHuman base is weak today (lean, flat, no definition), but it has the right foundations: one mesh, a native head, clean topology that deforms well, good hands, the rig, and her UVs and skin pipeline.

## What the rebuild must achieve (judge it against these)
- **Build:** athletic heavyweight at 1.98 m, about 8-10% body fat (a decathlete or rugby forward who has bulked up). Girth checks on the mesh: upper arm ≈ neck ≈ calf; shoulder girth ≈ 1.6x waist; thigh ≈ 1.75x knee. The arms hang close in the idle (no lat-spread look).
- **Traps and neck:** a gentle trap slope from the neck to the point of the shoulder. From behind, the top of the trap sits at about the lower third of the neck. The neck is thick enough that the head never reads small.
- **Front, at least today's level:**
  - torso: 3-row ab grid plus lower abs, linea alba, serratus fingers interlocking with the external oblique, a flatter oblique roll over the hip bone (Adonis lines)
  - chest and arms: a full upper pec with a clean groove between pec and delt, three deltoid heads, the biceps/brachialis/triceps horseshoe, forearm flexors split from extensors with 2-3 veins
  - legs: VMO teardrop, rectus femoris, groove between vastus lateralis and IT band, two gastrocnemius heads over the soleus
- **Back:** lats shaped as a symmetric fan with a clean edge, the lower-trap diamond, infraspinatus/teres knots over the shoulder blade, and erector columns on either side of the spinal channel down to two sacral dimples. Firm, squarer male glutes with a gluteus medius shelf. A neutral pelvis (in profile, glutes and shoulder blades sit close to one vertical line).
- **Neck:** soft neck muscles (no ridge), a subtle Adam's apple, and no seam anywhere.
- **Face:** 30-35 years old, handsome and rugged. A wider, squarer jaw with a visible angle, a strong chin, cheek hollows about half as deep, a straight heavy brow, slightly fuller lips, and clean paint mirrored left to right. Finished to her face's standard.
- **Skin:** her skin pipeline (subsurface, roughness, pores). A warmer, slightly darker male tone in her color family. No shading baked into the color map. Flat nipples.

## Donor variant (the cost cutter)
1. Put both bodies in the same pose (pose the sculpt with its AccuRIG rig). Shape the MakeHuman man toward the build target with MakeHuman's own sliders first.
2. Wrap the MakeHuman body toward the sculpt at about half weight, and only where its volume helps: pecs, delts, arms, thighs and calves. That halves the bodybuilder mass. Use zero weight on the head, neck, hands, feet, back and glutes. If half weight misses the build, generating a new, leaner TRELLIS donor of the target build is cheap.
3. Transfer only the sculpt's fine surface detail, not its volume: take the sculpt minus a heavily smoothed copy of itself, plus its 4K normal map, and project that onto MakeHuman's UVs through a mask with soft edges. Mask in the front abdominal wall, serratus and obliques, arms and forearms, the front and outer thighs, and the calves. Only the back, the glutes, and the neck-to-trap join are left to script.
4. Round 1 passes when the front and legs already match today's sheet and the back, face and skin meet the targets above.

Provenance: the donor carries the sculpt's Krea 2 origin into the rebuild. The brief says that is cleared; if legal ever says otherwise, fall back to pure Path A with the same targets.

## Must-fix before the owner sees full-res sheets
- Stop polishing the current body and don't send it as a candidate. If it appears as a "before", label it that way.
- The rebuild's first sheet needs:
  - a face at her standard (no darks on one side only, no painted brow smudge)
  - no neck seam or ridge, and flat nipples
  - correct back anatomy (no balloon lat, no V fold) and a neutral profile
  - skin in her pipeline
  - him beside her at the same scale and in the same light, in front, side, back and 3/4 views

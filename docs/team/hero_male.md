# Male hero: status

Branch `worktree-agent-ae2de192cce8298ca`. Handed off by ae2de192cce8298ca: read `docs/handoff/hero_male.md` first.

## Current state
- **In the game, gated.** With `--body hero` he is in play: his body on the game's skeleton (`hero.glb`), a MakeHuman head painted by Krea as his face, and flint-grey eyes. His skin is on the game's skin shader with the relief baked from his sculpt.
- **Without the flag,** men stay the kit's man, till his outfits exist.
- **Sheets:** `docs/hero_male/face3.jpg` and `docs/hero_male/body3.jpg`, rendered in Godot lookdev with `BODY=hero`.
- **Tools:** `tools/assets/hero_male_body.py`, `hero_male_head.py` and `hero_male_face.py`.
- **Shader:** `heroine_skin.gdshader` gained default-off `relief` and shaved-shadow (stubble and scalp) layers.

## Key decisions
- **His height: 1.98 m** to her 1.87 m, the usual male-to-female ratio.
- **A MakeHuman head:** the sculpt's eyes and lips were moulded shut.
- **The head 6% over his sculpt's:** it looked small on his neck.
- **Clean-shaven paint;** stubble is a shader layer and beards are cards, both options.
- **The kit man until his outfits exist,** so he is never shown naked in play.

## Next
1. Tune his skin (a little shiny); ease the boxy top of his skull.
2. Hair and beards: `hero_male_hair.py`.
3. His four outfits: `hero_male_outfits.py`. Then make him the default man.
4. The Look step for men, with UI design (ac76f400913a109cd).
5. His clip library, `him/`, from the animation lead (a1e3002b800ee55ac), who has the skeleton.

## Notes for other areas
- **Animation:** `hero.glb` was pushed at 6df994d; the skeleton is unchanged since.
- **UI:** a man's `PersonSpec` now has `Body = "man"` and `him:<calling>` appended to the outfit list.

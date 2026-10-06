p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528\docs\team\face.md'
s = open(p, encoding='utf-8').read()
old_head = s[s.index('Agent a6007bf07fd45ab0d'):s.index('## Current state')]
s = s.replace(old_head, 'Agent a2f7b0f1283f6144a, branch `worktree-agent-a7905c3e498df9528` (took over from a6007bf07fd45ab0d at v8e).\n'
              'The handoff is `docs/handoff/face.md`.\n\n')
start = s.index('## Current state')
end = s.index('- **heroine.glb and the outfits')
s = s[:start] + '''## Current state (2026-10-05)
- **v9** (sheets `godot/.shots/sbs_default_v9.jpg`, `presets_v9.jpg`, uncommitted): her lips meet again. v7's `portrait-heroine.target` is back (v8's wrap parted her lips by half a millimetre at her middle); `teeth_probe.py` sees no tooth from in front on any of 789 rays, hers or a preset's. Everything else as v8e: v8e answered the v7 list (eyes open on every preset, Saffron's smudge and Sunborn's seam gone, irises true to the portraits, the neck band gone, the hairline blended, the presets' lips clean).
- **Open, worst first:**
  1. Her skin pinker and smoother than her portrait at the Look (grain 0.020 against the portrait's 0.043). Found: her paint itself holds half the grain of the photograph laid on her front (0.026 against 0.057, `heroine_face.py`: the front blended half and half with older side paintings over her cheeks, then its contrast cut to MakeHuman's skin by `match`); the Look's warm key and the fire's edge light make the pink (under a white rig she is 8% light, hardly pink).
  2. Sunborn 1.2 times lighter than her portrait against hers (bluer still: 1.38 in blue); Doe, Saffron and Wildling 1.06 to 1.08. Every preset's paint is in her colouring; the skin tone (looks.json) makes the colour.
  3. Hair cards read as broad strokes at the close-up: each card's strands average to one flat band (strands 1 texel wide, no clumps between a strand and a card).
  4. Sloe and peat eyes a little dark; a pale wedge under her jaw (both sides, at a turn); pale patches on her upper chest (her body's paint: the main session's).
''' + s[end:]
open(p, 'w', encoding='utf-8').write(s)
print('ok')

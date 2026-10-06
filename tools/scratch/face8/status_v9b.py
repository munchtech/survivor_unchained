p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a43570e07edbe40b2\docs\team\face.md'
s = open(p, encoding='utf-8').read()
start = s.index('## Current state')
end = s.index('- **heroine.glb and the outfits')
s = s[:start] + '''## Current state (2026-10-05)
- **v9** (merged): her lips meet again (v7's `portrait-heroine.target`).
- **Portraits** (merged): each face's portrait is its own face, skin and eyes (`creation_portraits.py` passes `faceShape`); Sunborn, Moonlit and Saffron have theirs.
- **v9b** (this branch, for the main session's refit): the dark band down her throat and chest under a side light is gone (her normals joined along her middle, `heroine_head.py`); the white slivers along her lips at a turn are gone (her skin's sheen occluded by her AO; they were the rim light on her lips' inner linings, not teeth: `teeth_probe2.py` sees no tooth from ±30 degrees or ±20 up and down, any face). After the refit: the portraits again, then v10.
- **v10 in hand:** her paint's fine detail from the view that sees it best (`heroine_face.py`, committed, not yet laid on the faces): her mid-scale grain 0.87 of her portrait's (0.65 at v9) at the size her face is at the Look.
- **Open, worst first:** v10's grain on all ten faces; preset tones (Sunborn 1.13/1.37/1.70 lighter than her portrait in r/g/b under a white rig; her own 12% redder than hers); hair cards as broad strokes (no clumps between a strand and a card); her catchlight a blob the size of her pupil; brows faint and grey; sloe and peat dark; a pale wedge under her jaw at a turn.
''' + s[end:]
# the decisions
s = s.replace("## Key decisions (why)\n", "## Key decisions (why)\n"
              "- **Her normals joined along her middle** (`heroine_head.py`, where hers differ from the joined smooth ones by over 8 degrees within 2 cm of it): her body's halves meet unjoined there and her own normals leaned in toward the seam; a light from the side put half her throat in shade on a straight line.\n"
              "- **No sheen where her AO is deep** (`heroine_skin.gdshader`): the rim light's reflection on her lips' linings showed as white slivers at a turn.\n"
              "- **Fine detail from one view, broad colour from all** (`heroine_face.py`): blended as one, her front's grain was averaged with the side paintings' over her cheeks and cut by `match`: her paint held half her photograph's grain.\n", 1)
open(p, 'w', encoding='utf-8').write(s)
print('ok')

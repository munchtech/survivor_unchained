w = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7905c3e498df9528'
p = w + r'\docs\team\face.md'
s = open(p, encoding='utf-8').read()
a = s.index('- **v9b** (this branch')
b = s.index('- **v10 in hand:**')
s = s[:a] + '''- **v9b, half done** (this branch; code only, no refit needed yet): the white slivers along her lips at a turn are gone (her skin's sheen occluded by her AO; they were the rim light on her lips' inner linings, not teeth: `teeth_probe2.py` sees no tooth from ±30 degrees or ±20 up and down, any face). Her body's normals joined along her middle where they split (`heroine_head.py`, 797 corners). **The dark band down her throat under a side light is still there**: neither the join nor rounding her throat's normals (tried, reverted) moved it. It comes with the key alone, not its shadow; a clay render under a side light (`side_light.py`) shows her upper chest's normals broken into faceted shards, which are the "pale patches on her upper chest" in the Look, not her body's paint.
''' + s[b:]
s = s.replace("- **Her normals joined along her middle** (`heroine_head.py`, where hers differ from the joined smooth ones by over 8 degrees within 2 cm of it): her body's halves meet unjoined there and her own normals leaned in toward the seam; a light from the side put half her throat in shade on a straight line.\n",
              "- **Her normals joined along her middle** (`heroine_head.py`, where hers differ from the joined smooth ones by over 8 degrees within 2 cm of it): her body's halves meet unjoined there and her own normals were split (26 degrees at a point). (It did not cure the throat band.)\n", 1)
open(p, 'w', encoding='utf-8').write(s)

p = w + r'\docs\handoff\face.md'
s = open(p, encoding='utf-8').read()
a = s.index('- **v9b** (see the status page for its commit)')
b = s.index('## Next (worst first)')
s = s[:a] + '''- **v9b, half done** (code committed; the main session has not refitted it). Her lips' white slivers at a turn are gone: `heroine_skin.gdshader` occludes her sheen by her AO (`SPECULAR *= smoothstep(0.45, 0.95, ao)`). They were the rim light on her lips' inner linings, not teeth; `teeth_probe2.py` sees no tooth from ±30 degrees yaw or ±20 pitch, any face. `heroine_head.py` joins her body's split normals along her middle (797 corners).

''' + s[b:]
a = s.index('1. **After the main session')
b = s.index('2. **v10, skin grain.**')
s = s[:a] + '''1. **The throat band** (the portraits' dark vertical line down her throat and chest under their side key; the main session wants it gone before the portraits are merged again). Known:
   - It comes with the key alone (`LIGHTS=1,0,0`), with the key's shadow off too, and is gone without the key.
   - The NormalBuffer shows a step there.
   - Joining her middle's split normals did not move it; nor did rounding her throat's normals across her middle (tried in `heroine_head.py`, reverted).
   - Her throat's front is her head mesh down to her lower neck, then her body (`side_light.py` colours them).
   - A clay render under a side light shows her upper chest's normals broken into faceted shards. These are the "pale patches on her upper chest" in the Look. Tell the main session, whose body it is.
   - Next to try: the band in Blender under the portrait's exact light and camera (`side_light.py`, camera from her front at yaw -14); her head mesh's own neck normals (`normals_split_custom_set_from_vertices(hn)`); Godot's SSS (skin mode) at a terminator.
   - Then rebuild (`build_v9.ps1 -rest`; the worktree's built blend still holds the reverted rounding), send the blend for one refit, and rerun the portraits on your branch (`portraits.ps1`) once it's refitted.
''' + s[b:]
s = s.replace("HANDOFF READY: docs/handoff/face.md on worktree-agent-a7905c3e498df9528@(see the v9b commit)", "HANDOFF READY: docs/handoff/face.md on worktree-agent-a7905c3e498df9528@HEAD")
open(p, 'w', encoding='utf-8').write(s)
print('ok')

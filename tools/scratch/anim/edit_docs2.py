from pathlib import Path
W = Path(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa4f5fc266b043035')
p = W / 'public/assets/CREDITS.md'
s = p.read_text(encoding='utf-8')
old = """- Her Crashing Leap is Mixamo's "Standing Melee Run Jump Attack" (Adobe Mixamo, used in the game under Mixamo's terms; retargeted to her and retimed; the raw files are not distributed). Further Mixamo motion (the vault, the bull rush, the chain haul, townsfolk) is downloaded for the same use: see tools/anim/manifest.json.
- Motion generated with NVIDIA's Kimodo (Kimodo-SOMA-RP, NVIDIA Open Model License) and captured from video with Meta's SAM 3D Body (SAM License; Momentum Human Rig, Apache 2.0) is credited clip by clip in tools/anim/manifest.json when it ships."""
new = """- Her Crashing Leap is Mixamo's "Standing Melee Run Jump Attack" (Adobe Mixamo, used in the game under Mixamo's terms; retargeted to her and retimed; the raw files are not distributed).
- The townsfolk's walk (women's), standing idle, talk (men's), sitting on a chair and on the floor, and picking up are Mixamo's "Feminine Walk", "Weight Shift", "General Conversation", "Sitting Looking Side To Side", "Sitting" and "Picking Up" (Adobe Mixamo, used under Mixamo's terms; retargeted to the kit's bodies; raw files not distributed).
- The townsfolk's walk (men's), talk (women's), arms crossed, cheer, wave and work at a table are generated with NVIDIA's Kimodo (Kimodo-SOMA-RP, NVIDIA Open Model License; tools/anim/kimodo_gen.py). Each folk clip's source is in godot/art/anim/folk_clips.json.
- Motion captured from video with Meta's SAM 3D Body (SAM License; Momentum Human Rig, Apache 2.0) is credited clip by clip in tools/anim/manifest.json when it ships."""
assert old in s
p.write_text(s.replace(old, new), encoding='utf-8')

p = W / 'docs/ANIM_DESIGN.md'
s = p.read_text(encoding='utf-8')
old = """- Folk and the crowd keep the library."""
new = """- The crowd (VAT-baked) keeps the library; so do armed people (guards,
  bosses) and running townsfolk."""
assert old in s
s = s.replace(old, new)
marker = "## 5."
i = s.index(marker)
folk = """### 4.7 Townsfolk (`tools/anim/folk.py`, `godot/art/anim/folk.res`)
Unarmed people on the kit's bodies play their own clips where they have
them (`FolkClips`, through `People.Clip`), each made twice, for the women's
and the men's skeletons (their rests differ from the library's by up to
23 degrees at the neck, so one set would not sit right on both):
- `walk`: hers Mixamo's feminine walk (one whole cycle, closed on itself),
  his Kimodo's easy stride; played at the rate that keeps the feet planted.
- `idle` (Mixamo's weight shift), `talk` (hers Kimodo, both hands; his
  Mixamo's conversation), `arms_crossed` (Kimodo), `sit_chair`, `sit_floor`
  (Mixamo): loops.
- `cheer` (hers both arms, his a fist), `wave`, `work` (Kimodo), `pick_up`
  (Mixamo): played once.
Before, the library had them nod `Yes` for a cheer or a wave and crouch to
sit on the floor.

"""
s = s[:i] + folk + s[i:]
p.write_text(s, encoding='utf-8')
print('ok')

"""Swaps the repo generator's old marks section for marks_section.GD, and makes MARKS (or
LINEAR) runs use a linear tonemapper so the test codes read back exactly."""
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aab20546fe06daa89\tools\legal\motioncheck\make_motioncheck.py'
t = open(p, encoding='utf-8').read()
a = t.index('# MARKS=1: her areolas tinted magenta')
b = t.index("open(OUT, 'w'")
new = '''# MARKS=1: the test codes on her body (marks_section.py), after the outfit's own skin
# handling, so what is hidden in play stays hidden here.
swap('\\t\\t# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.\\n',
     '\\t\\tif OS.get_environment("MARKS") != "":\\n'
     '\\t\\t\\tfor bm in skel.get_children():\\n'
     '\\t\\t\\t\\tif bm is MeshInstance3D and not String(bm.name).contains(".") and not String(bm.name).contains("_") and bm.mesh.surface_get_format(0) & Mesh.ARRAY_FORMAT_COLOR:\\n'
     '\\t\\t\\t\\t\\tlegal_marks(bm)\\n'
     '\\t\\t# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.\\n')
# MARKS (or LINEAR=1, to test an outfit's own colours against the codes): a linear tonemapper.
swap('\\te.tonemap_mode = Environment.TONE_MAPPER_AGX\\n',
     '\\te.tonemap_mode = Environment.TONE_MAPPER_LINEAR if OS.get_environment("MARKS") != "" or OS.get_environment("LINEAR") != "" else Environment.TONE_MAPPER_AGX\\n')
sys.path.insert(0, HERE)
from marks_section import GD  # noqa: E402
src += GD
'''
t = t[:a] + new + t[b:]
open(p, 'w', encoding='utf-8', newline='\n').write(t)
print('ok')

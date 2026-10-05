"""The legal motion check's scene script, built from godot/tools_scenes/lookdev.gd
(docs/legal/LEGAL_BRIEF.md issue 2: Steam needs the mature-content survey to be true of
what a player can see). It adds to lookdev:
- her own clip library as "her/" (lookdev loads only the UAL clips, which her rig doesn't play);
- SPREAD=1: the clip loops in memory (nothing saved) and the FRAMES pictures are spread
  evenly over one pass of it, from 1 s in, so a short swing is seen whole with its jiggle warmed;
- VIEWS="name:deg,height,dist,targety:fov;...": several cameras in one run (the first is the
  window's, the rest SubViewports sharing its world); pictures are out_<name>_NN.png;
- FOLLOW=1: every camera keeps its offset from her hips, for clips that travel (dash, leap, vault);
- MARKS=1: her areolas and genital area drawn in unlit cyan, after the outfit's own skin hiding,
  for count.py to find (see that file). Pictures with MARKS and no OUTFIT show her bare: keep
  them out of the repo and never publish them.
    python make_motioncheck.py <out.gd>      (run.sh does this into its own output folder)
Written as UTF-8 without a byte-order mark (Godot refuses a BOM in GDScript)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOOKDEV = os.path.join(HERE, '..', '..', '..', 'godot', 'tools_scenes', 'lookdev.gd')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'motioncheck.gd')
src = open(LOOKDEV, encoding='utf-8-sig').read()


def swap(a, b):
    global src
    assert src.count(a) == 1, a
    src = src.replace(a, b)


swap('\t\tap.add_animation_library("", lib)\n',
     '\t\tap.add_animation_library("", lib)\n'
     '\t\tap.add_animation_library("her", load("res://art/anim/heroine.res"))\n')

swap('var players = []\n',
     'var players = []\n'
     'var clip_len = 0.0\n'
     'var follow_skel: Skeleton3D\n'
     'var follow_from = Vector3.ZERO\n'
     'var view_cams = []\n'
     'var view_from = []\n'
     'var view_names = []\n'
     'var view_ports = []\n')
swap('\t\tap.play(clips[i])\n',
     '\t\tif OS.get_environment("SPREAD") != "":\n'
     '\t\t\tvar anim = ap.get_animation(clips[i])\n'
     '\t\t\tanim.loop_mode = Animation.LOOP_LINEAR\n'
     '\t\t\tclip_len = max(clip_len, anim.length)\n'
     '\t\tap.play(clips[i])\n'
     '\t\tif follow_skel == null:\n'
     '\t\t\tvar sks = h.find_children("*", "Skeleton3D", true, false)\n'
     '\t\t\tif sks.size() > 0: follow_skel = sks[0]\n')
swap('\troot.add_child(rim)\n',
     '\troot.add_child(rim)\n'
     '\tvar views = OS.get_environment("VIEWS")\n'
     '\tif views != "":\n'
     '\t\tvar parts = views.split(";", false)\n'
     '\t\tfor vi in parts.size():\n'
     '\t\t\tvar p = parts[vi].split(":")\n'
     '\t\t\tvar o = p[1].split(",")\n'
     '\t\t\tvar c: Camera3D = cam\n'
     '\t\t\tvar port: Viewport = get_root()\n'
     '\t\t\tif vi > 0:\n'
     '\t\t\t\tvar sv = SubViewport.new()\n'
     '\t\t\t\tsv.size = Vector2i(960, 540)\n'
     '\t\t\t\tsv.msaa_3d = get_root().msaa_3d\n'
     '\t\t\t\tsv.render_target_update_mode = SubViewport.UPDATE_ALWAYS\n'
     '\t\t\t\troot.add_child(sv)\n'
     '\t\t\t\tc = Camera3D.new()\n'
     '\t\t\t\tsv.add_child(c)\n'
     '\t\t\t\tc.current = true\n'
     '\t\t\t\tport = sv\n'
     '\t\t\tvar a = deg_to_rad(float(o[0]))\n'
     '\t\t\tc.fov = float(p[2])\n'
     '\t\t\tc.look_at_from_position(Vector3(sin(a) * float(o[2]), float(o[1]), cos(a) * float(o[2])), Vector3(0, float(o[3]), 0))\n'
     '\t\t\tview_cams.append(c)\n'
     '\t\t\tview_from.append(c.global_position)\n'
     '\t\t\tview_names.append(p[0])\n'
     '\t\t\tview_ports.append(port)\n'
     '\telse:\n'
     '\t\tview_cams.append(cam)\n'
     '\t\tview_from.append(cam.global_position)\n'
     '\t\tview_names.append("")\n'
     '\t\tview_ports.append(get_root())\n')
swap('\t\tvar k = int((t - 1.0) * 15.0)\n',
     '\t\tvar step = 1.0 / 15.0\n'
     '\t\tif OS.get_environment("SPREAD") != "" and clip_len > 0.0: step = clip_len / float(int(frames))\n'
     '\t\tvar k = int((t - 1.0) / step)\n')
swap('\t\t\tget_root().get_texture().get_image().save_png(out.replace(".png", "_%02d.png" % k))\n',
     '\t\t\tfor vi in view_ports.size():\n'
     '\t\t\t\tvar tag = ("_" + view_names[vi]) if view_names[vi] != "" else ""\n'
     '\t\t\t\tview_ports[vi].get_texture().get_image().save_png(out.replace(".png", "%s_%02d.png" % [tag, k]))\n'
     '\t\t\t\tif follow_skel != null: save_landmarks(view_cams[vi], out.replace(".png", "%s_%02d.json" % [tag, k]))\n')
swap('\tt += delta\n',
     '\tt += delta\n'
     '\t# FOLLOW=1: every camera keeps its offset from her hips (taken at 0.5 s, once she has settled).\n'
     '\tif OS.get_environment("FOLLOW") != "" and follow_skel != null:\n'
     '\t\tvar hb = follow_skel.find_bone("pelvis")\n'
     '\t\tif hb < 0: hb = 0\n'
     '\t\tvar hp = follow_skel.global_transform * follow_skel.get_bone_global_pose(hb).origin\n'
     '\t\thp.y = 0.0\n'
     '\t\tif t < 0.5:\n'
     '\t\t\tfollow_from = hp\n'
     '\t\t\tfor vi in view_cams.size(): view_from[vi] = view_cams[vi].global_position\n'
     '\t\telse:\n'
     '\t\t\tfor vi in view_cams.size(): view_cams[vi].global_position = view_from[vi] + (hp - follow_from)\n')
# MARKS=1: the test codes on her body (marks_section.py), after the outfit's own skin
# handling, so what is hidden in play stays hidden here.
swap('\t\t# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.\n',
     '\t\tif OS.get_environment("MARKS") != "":\n'
     '\t\t\tfor bm in skel.get_children():\n'
     '\t\t\t\tif bm is MeshInstance3D and not String(bm.name).contains(".") and not String(bm.name).contains("_") and bm.mesh.surface_get_format(0) & Mesh.ARRAY_FORMAT_COLOR:\n'
     '\t\t\t\t\tlegal_marks(bm)\n'
     '\t\t# HAIR=<style> (heroine_hair_<style>.gltf; "none" for none), HAIRCOLOR=#rrggbb.\n')
# MARKS (or LINEAR=1, to test an outfit's own colours against the codes): a linear tonemapper.
swap('\te.tonemap_mode = Environment.TONE_MAPPER_AGX\n',
     '\te.tonemap_mode = Environment.TONE_MAPPER_LINEAR if OS.get_environment("MARKS") != "" or OS.get_environment("LINEAR") != "" else Environment.TONE_MAPPER_AGX\n')
sys.path.insert(0, HERE)
from marks_section import GD  # noqa: E402
src += GD
open(OUT, 'w', encoding='utf-8', newline='\n').write(src)
print('written', len(src))

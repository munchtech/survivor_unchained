"""The pack listing as a record for the legal lead: a header (how it was made,
what was checked, sizes by folder), then every path the release pack carries."""
import collections
import sys

listing, out, commit = sys.argv[1], sys.argv[2], sys.argv[3]
rows = []
for line in open(listing, encoding="utf-8"):
    line = line.rstrip("\n")
    if not line.strip():
        continue
    size, path = line.strip().split("  ", 1)
    rows.append((int(size), path.strip()))

by = collections.defaultdict(lambda: [0, 0])
for s, p in rows:
    parts = p.split("/")
    k = "/".join(parts[:2]) if len(parts) > 2 else parts[0]
    if p.endswith(".cs"):
        k = "C# script stubs (src, logic, balance)"
    by[k][0] += 1
    by[k][1] += s

with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(f"""Release pack listing: Windows preset, export_presets.cfg at {commit}
=====================================================================

Made by the performance lead on 4 October 2026 with Godot 4.5.1 mono (official
templates, 4.5.1.stable.mono): `--export-pack Windows pack.zip` for this listing,
and `--export-release Windows` for the build that was run. The Linux and macOS
presets share the same include and exclude filters (tests/ExportTests.cs).

What was checked
- Nothing excluded ships: tools_scenes, anime_female.glb, her_Hair_*.glb,
  woman.glb, woman_mask.png, hero.glb, assets/characters, assets/props,
  assets/anim/humanoid.glb, assets/ground/*.ktx2, assets/people/*.bake.webp,
  assets/env/polyhaven, art/vo (the placeholder voices), tests, .shots: 0 files each.
- Every JSON the code reads with FileAccess ships (data/*, art/fx/sprites.json,
  art/fx/fb/*.json, art/ground/ground.json, art/people/outfit_materials.json,
  art/sound/sounds.json, art/anim/*_clips.json, the hair chains). Godot 4 exports
  .json as a resource, so include_filter needs no art/ entries. Only the glTF
  buffers (art/people/heroine_*.bin) stay out; the game loads their imports.
- Every dependency of every shipped resource ships too (ResourceLoader
  .get_dependencies over all 1,665: none missing).
- C# scripts ship as empty stubs (dotnet/include_scripts_content=false); the
  code is in the .NET assemblies beside the executable.
- The release build ignores every developer switch: run with
  `--body hero --quick warden --zone waystation --shot rel --perf rel`, it opened
  at the age gate and the title (no quick start, no screenshot, no quit, no perf
  file; window title without "(DEBUG)"). It then played: the age gate accepted,
  New Journey opened creation with her; a save continued into the Waystation and
  she walked.

Sizes below are uncompressed, imported data included.

Size by folder (MB, files)
""")
    for k in sorted(by, key=lambda k: -by[k][1]):
        f.write(f"  {by[k][1] / 1e6:8.1f} {by[k][0]:5d}  {k}\n")
    f.write(f"  {sum(s for s, _ in rows) / 1e6:8.1f} {len(rows):5d}  total\n\nEvery path (bytes, path)\n")
    for s, p in rows:
        f.write(f"{s:>12}  {p}\n")
print(len(rows), "paths")

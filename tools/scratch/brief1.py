p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\docs\UI_ART_BRIEF.md'
s = open(p, encoding='utf-8').read()
pairs = [
("""   $GODOT --path godot -- --shot plate 5 --quick warden --zone waystation --open character
   $GODOT --path godot -- --shot draft 6 --quick reaver --zone arena --open draft
   $GODOT --path godot -- --shot pack 5 --quick warden --zone waystation --items chain_shirt:2,silver_ring:3,wolf_pelt --open inventory --pad --keys Right,Right
   $GODOT --path godot -- --shot hud 14 --quick reaver --zone arena --auto idle
   $GODOT --path godot -- --shot title 6
   ```
   (`--shot NAME --seconds S` in the code's own form: `--shot plate --seconds 5`.)""",
"""   $GODOT --path godot -- --shot plate --seconds 5 --quick warden --zone waystation --open character
   $GODOT --path godot -- --shot draft --seconds 6 --quick reaver --zone arena --open draft
   $GODOT --path godot -- --shot pack --seconds 5 --quick warden --zone waystation --items chain_shirt:2,silver_ring:3,wolf_pelt --open inventory --pad --keys Right,Right
   $GODOT --path godot -- --shot hud --seconds 14 --quick reaver --zone arena --auto idle
   $GODOT --path godot -- --shot title --seconds 6
   ```"""),
("""| You | `minimap/you.png` | 48×48 (24) | The survivor's arrow at the centre, **pointing up** (the code rotates it). Also used on the big map's legend |""",
"""| You | `minimap/you.png` | 48×48 (24) | The survivor's arrow at the centre, **pointing up** (the code rotates it) |"""),
]
for old, new in pairs:
    assert old in s, old[:60]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')

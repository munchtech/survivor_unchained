import sys
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a7a4c20bcfd7ccfd3\docs\cinematics\shoot"
EDITS = {
    "c01.md": [("- **Action:** she walks to `end` and turns north; the world runs at 0.25.",
                "- **Action:** her own body from the cut (`play`, `docs/cinematics/README.md` 5a): she walks to `end`, north, and stands, facing where play takes her up; the world runs at 0.25.")],
    "c02.md": [("- **Action:** he sets his guard (`Idle_Shield_Loop`).",
                "- **Action:** her own body from the cut (`play`), facing him where play takes her up; he sets his guard (`Idle_Shield_Loop`).")],
    "c04b.md": [("- **Sound:** `town` back to 0.5 over 2 s from 0.6 s.",
                 "- **Action:** her own body from the cut (`play`), facing north where play takes her up.\n- **Sound:** `town` back to 0.5 over 2 s from 0.6 s.")],
}
for name, rs in EDITS.items():
    p = W + "\\" + name
    t = open(p, encoding="utf-8", newline="").read()
    for a, b in rs:
        assert t.count(a) == 1, (name, a[:50])
        t = t.replace(a, b)
    open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")

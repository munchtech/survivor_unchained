"""Replace the status page's Next section with the handoff's order (one source of truth)."""
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a73ca9d35d0c487a9\docs\team\story.md"
t = open(p, "rb").read().decode("utf-8").replace("\r\n", "\n")
a = t.index("## Next\n")
b = t.index("## Blockers\n")
new = """## Next

The handoff (`docs/handoff/story.md` §3) has the detail. In order:
1. **The story fights and the day's clock**, once the owner approves
   experience's and combat's proposals (agreed, with two fixes). Their words
   are written (WRITING_PASS §21). The dusk, rise and night-left-alone lines go
   into data, and the bible's Pacing share is updated. The banes `bane.fires`
   and `bane.pole` are seeds until the fights read them.
2. **Vonnra's fortune gives the first chart** (`Journey.GiveChart`), which
   opens the atlas. It needs a hook and her line: priced, then waived.
3. The result screen's new slots, when experience sends UI's beats.
4. C14: `brannoc.road`, the `nell.burial` variant, its last lines and a
   RouteTests play, once combat builds the fight.
5. C01 to C04: the cinematics lead's line asks.
6. Act 2's text, when the owner asks.

"""
t = t[:a] + new + t[b:]
t = t.replace("Agent a73ca9d35d0c487a9, branch `worktree-agent-a73ca9d35d0c487a9`\n(successor to a035208561a66c171; handoff in `docs/handoff/story.md`).",
              "Agent a73ca9d35d0c487a9 (handed off past 500k), branch\n`worktree-agent-a73ca9d35d0c487a9`. A fresh successor starts from `docs/handoff/story.md`.")
open(p, "wb").write(t.replace("\n", "\r\n").encode("utf-8"))
print("ok")

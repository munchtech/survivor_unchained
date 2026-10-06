"""Replace pages.py's header() (from its def up to `def header_v1`) with binding_src.py."""
import os

S = os.path.dirname(os.path.abspath(__file__))
P = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d\tools\uiforge\pages.py"
src = open(P, encoding="utf-8").read()
new = open(os.path.join(S, "binding_src.py"), encoding="utf-8").read()
a = src.index("def header(ss=2, samples=192):")
b = src.index("def header_v1(")
src = src[:a] + new.rstrip() + "\n\n\n" + src[b:]
open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ok")

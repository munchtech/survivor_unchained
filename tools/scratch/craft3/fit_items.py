"""Cut and fit crafting's picked item icons with the UI art lead's pipeline (items.fit, PICKS)."""
import sys, os
UF = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af01b0d61ef656dd4\tools\uiforge"
sys.path.insert(0, UF)
os.chdir(UF)
import items
for k in sys.argv[1:]:
    items.fit(k)
    print("fit", k, flush=True)

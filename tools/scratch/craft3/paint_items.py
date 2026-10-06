"""Paint crafting's new item icons through the UI art lead's pipeline (tools/uiforge/items.py T2I):
python paint_items.py KEY... [--seed N] [--n N]"""
import sys, os
UF = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af01b0d61ef656dd4\tools\uiforge"
sys.path.insert(0, UF)
os.chdir(UF)
import items
args = sys.argv[1:]
seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 1100
n = int(args[args.index("--n") + 1]) if "--n" in args else 4
keys = [a for a in args if not a.startswith("--") and not a.isdigit()]
res = items.t2i(keys, seed=seed, n=n)
for k, paths in res.items():
    print(k, *paths, sep="\n  ")

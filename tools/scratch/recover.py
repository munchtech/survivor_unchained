import os, glob, shutil
SRV = r"C:\Users\munch\AppData\Local\Comfy-Desktop\ComfyUI-Shared\output"
RAW = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abd496197891ea843\tools\comfy\out\uiforge"
keys = "slash_steel slash_heavy disc axe mote cinder shard arrow".split()
os.makedirs(RAW + r"\icons", exist_ok=True)
for i, k in enumerate(keys):
    fs = sorted(glob.glob(SRV + rf"\many_{i:03d}__*.png"), key=os.path.getmtime)[-2:]
    for j, f in enumerate(fs):
        shutil.copy(f, RAW + rf"\icons\{k}_900_{j}.png")
        print(k, f)
os.makedirs(RAW + r"\card_epic", exist_ok=True)
for j, n in enumerate((43, 44, 45)):
    shutil.copy(SRV + rf"\uiforge_000{n}_.png", RAW + rf"\card_epic\card_epic_602_{j}.png")

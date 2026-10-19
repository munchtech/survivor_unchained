import sys, time, score as S
SP = "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-survivorsunchained/b8d13e5f-b1a5-4365-9d36-63505c60b8a1/scratchpad/"
socks = sys.argv[1].split(",")
grids = {}
if any(S.ROWS[s][0] == "pelvis" for s in socks): grids["pelvis"] = SP + "pelvis.npz"
if any(S.ROWS[s][0] == "spine_03" for s in socks): grids["spine_03"] = SP + "spine.npz"
s = S.Scorer(grids, socks)
for so in socks:
    t = time.time()
    r, clr = s.score(so, S.ROWS[so])
    print(so, f"{time.time()-t:.2f}s", {o: round(c*1000, 1) for o, c in clr.items()})
    for k, v in r.items():
        for o, (b, a, af, bf, g) in v.items():
            print(f"  {k:24} {o:9} body {b:5.1f} @{bf:22} arm {a:5.1f} @{af:22} gap {g:5.1f}")

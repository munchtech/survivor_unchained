from ev import *
c = apply("run_warden_town", dict(R.HILT), [0])
G = Gframes(c)[0]
for b in ("pelvis","upperarm_l","lowerarm_l","hand_l","upperarm_r","foot_l","head"):
    print(b, G[I[b]][:3,3].round(3))
print("pelvis R\n", G[I["pelvis"]][:3,:3].round(2))

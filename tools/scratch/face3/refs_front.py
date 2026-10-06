"""refs_front.py <out dir> <seed,...>: her default face, front only, large in the frame (for MoGe and for projection)."""
import os
import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9\tools\assets")
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6784044c82f101d9\tools\comfy")
import comfy  # noqa: E402
import face_refs  # noqa: E402

TEXT = ("A high-end beauty campaign photograph for a luxury cosmetics brand: a straight-on front view head-and-shoulders portrait of a "
        "breathtakingly beautiful, alluring young woman of twenty-four, looking straight into the camera, her face square to it and "
        "level. Fair porcelain skin with light delicate freckles across her nose and cheeks. Large bright green almond-shaped eyes with "
        "a slight upward tilt, a clearly defined upper eyelid crease, long dark lashes and a soft dark lash line. Softly arched, groomed "
        "auburn brows set high. A small straight refined nose with a gently upturned tip. Full, sensual, softly pouting lips, the lower "
        "lip fuller than the upper, a sharply defined cupid's bow, a soft rose tint, lips closed. High cheekbones, smooth full youthful "
        "cheeks, a slim tapered jaw and a small delicate chin, a slender neck, bare shoulders. Copper-red hair pulled back sleekly off "
        "her face and ears, her hairline and forehead visible. Serene, seductive neutral expression. Soft even beauty-dish light from the "
        "front, no harsh shadows, plain warm-grey studio background. Shot on an 85mm lens, sharp focus, luminous skin with fine natural "
        "texture.")

out = os.path.abspath(sys.argv[1])
os.makedirs(out, exist_ok=True)
try:
    for seed in [int(s) for s in sys.argv[2].split(",")]:
        got = comfy.run(face_refs.graph(TEXT, seed, "her_front", size=(1024, 1536)), out)
        os.replace(got[0], os.path.join(out, f"her_{seed}.png"))
        print("REF", seed)
finally:
    face_refs.free()

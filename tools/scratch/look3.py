from sp import *
import glob
fs = sorted(glob.glob(os.path.join(UI, "bars", "*.png")))
ims = []
for f in fs:
    im = Image.open(f)
    print(os.path.basename(f), im.size)
    ims.append(im)
sheet(ims).save(os.path.join(V, "bars.png"))
im = Image.open(os.path.join(OLD, "godot", ".shots", "a4_hud_night.png"))
zoom(im.crop((470, 0, 760, 60)), 4).save(os.path.join(V, "levelbar_z4.png"))

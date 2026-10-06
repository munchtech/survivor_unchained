import sys
sys.path.insert(0, r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-af551cacc6292152f\tools\creatures")
import bristles
from PIL import Image
S = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\boar\\"
bristles.draw(S + "bristles_test.png")
im = Image.open(S + "bristles_test.png").convert("RGBA")
bg = Image.new("RGBA", im.size, (150, 170, 140, 255))
a = im.split()[3].point(lambda v: 255 if v > 115 else 0)
bg.paste(im.convert("RGB"), (0, 0), a)
bg.save(S + "bristles_prev.png")

import os
import sys

from PIL import Image

UI = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a1a394643aabfb169\godot\art\ui"
out = sys.argv[1]
bg = (58, 40, 30, 255)
d = Image.open(os.path.join(UI, "frames", "column_divider.png")).convert("RGBA")
st = Image.open(os.path.join(UI, "frames", "column_divider_stone.png")).convert("RGBA")
mk = Image.open(os.path.join(UI, "ornaments", "section_mark.png")).convert("RGBA")
canvas = Image.new("RGBA", (900, 1140), bg)
# The divider at file size, and twice over (a second copy of its middle below, to see the seam).
canvas.alpha_composite(d, (20, 10))
mid = d.crop((0, 48, d.width, d.height - 48))
canvas.alpha_composite(d.crop((0, 600, d.width, d.height - 48)), (100, 10))
canvas.alpha_composite(mid.crop((0, 0, d.width, 500)), (100, 10 + d.height - 48 - 600))
# Its middle stone, at file size and at 4x.
canvas.alpha_composite(st, (20 + 24 - 32, 10 + 560 - 32))
canvas.alpha_composite(st.resize((256, 256), Image.LANCZOS), (220, 20))
canvas.alpha_composite(mk.resize((192, 192), Image.LANCZOS), (520, 20))
canvas.alpha_composite(mk, (520, 260))
canvas.convert("RGB").save(out)
print(out)

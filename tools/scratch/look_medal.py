"""A medal render: big (half the render), and at file size and shown size over the HUD's
ground, with a number on it like the code writes."""
import sys
from sp import *
from PIL import ImageFont

name = sys.argv[1]
num = sys.argv[2] if len(sys.argv) > 2 else "5"
big = Image.open(os.path.join(OUT, "relief", name + ".png")).convert("RGBA")
f = Image.open(os.path.join(OUT, "relief", name + "_file.png")).convert("RGBA")
shown = f.resize((f.width // 2, f.height // 2), Image.LANCZOS)
ground = Image.open(os.path.join(OLD, "godot", ".shots", "a4_hud_night.png")).convert("RGBA").crop((300, 300, 300 + 220, 300 + 120))
# Shown size on the night grass, x1 and zoomed x3 (nearest) to see pixels.
g = ground.copy()
g.alpha_composite(shown, (20, 20))
d = ImageDraw.Draw(g)
try:
    font = ImageFont.truetype(r"C:\Windows\Fonts\georgiab.ttf", 20)
except Exception:
    font = None
if num:
    cx, cy = 20 + shown.width / 2, 20 + shown.height / 2
    d.text((cx, cy), num, fill=(255, 200, 120, 255), font=font, anchor="mm")
g2 = g.copy()
g2.alpha_composite(f, (100, 0))
canvas = Image.new("RGB", (big.width // 2 + 20 + g.width * 3, max(big.height // 2, g.height * 3)), (28, 24, 22))
canvas.paste(on_bg(big.resize((big.width // 2, big.height // 2), Image.LANCZOS)), (0, 0))
canvas.paste(zoom(g.convert("RGB"), 3), (big.width // 2 + 20, 0))
canvas.save(os.path.join(V, f"{name}_look.png"))
g2.convert("RGB").save(os.path.join(V, f"{name}_real.png"))

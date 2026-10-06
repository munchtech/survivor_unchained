"""The heart medal with the stone icon laid over it as the code does (22 px shown, centred),
big and at shown size beside the health bar."""
import sys
from sp import *

src = sys.argv[1] if len(sys.argv) > 1 else "relief"
if src == "relief":
    medal = Image.open(os.path.join(OUT, "relief", "medal_heart_file.png")).convert("RGBA")
    stone = Image.open(os.path.join(OUT, "relief", "heart_stone_file.png")).convert("RGBA")
else:
    medal = Image.open(os.path.join(UI, "hud", "medal_heart.png")).convert("RGBA")
    stone = Image.open(os.path.join(UI, "icons", "glyph_color", "heart.png")).convert("RGBA")


def comp(scale):
    """scale: file px per shown px (2 = file size, 1 = shown... we compose at k x shown)."""
    m = medal.resize((medal.width * scale // 2, medal.height * scale // 2), Image.LANCZOS)
    st = stone.resize((22 * scale, 22 * scale), Image.LANCZOS)
    out = m.copy()
    out.alpha_composite(st, ((m.width - st.width) // 2, (m.height - st.height) // 2))
    return out


big = comp(8)
shown = comp(2)
ground = Image.open(os.path.join(OLD, "godot", ".shots", "a4_hud_night.png")).convert("RGBA")
g = ground.crop((0, 940, 460, 1080))
# Health bar placeholder area is in the shot already at (34+34, 1080-106+38); medal at (34, 974+30).
g.alpha_composite(shown, (34 - 11 - 0, 974 + 30 - 11 - 940 - 1))
canvas = Image.new("RGB", (big.width + 20 + g.width * 2, max(big.height, g.height * 2)), (28, 24, 22))
canvas.paste(on_bg(big), (0, 0))
canvas.paste(zoom(g.convert("RGB"), 2), (big.width + 20, 0))
canvas.save(os.path.join(V, "heart_look.png"))
g.convert("RGB").save(os.path.join(V, "heart_real.png"))

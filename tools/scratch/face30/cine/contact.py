"""python contact.py TAG [w] : working contact sheet of a variant's frames -> scratchpad f30/TAG_contact.jpg"""
import sys
from PIL import Image
SH = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2d632df7c7f21ec0\godot\.shots" + "\\"
OUT = r"C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\463a4243-9324-49b0-bda9-b9fb9a9d68b1\scratchpad\f30" + "\\"
tag = sys.argv[1]; w = int(sys.argv[2]) if len(sys.argv) > 2 else 280; h = w * 9 // 16
cols = ['c01_c01_s7_3', 'c01_c01_s8_3', 'c01_c01_s8b_3', 'c02_c02_s8_3', 'c04a_c04a_sa5_3', 'c04a_c04a_sa7_3', 'day', 'night']
m = Image.new('RGB', (len(cols) * w, 3 * h))
for r, f in enumerate(['own', 'saffron', 'sunborn']):
    for c, k in enumerate(cols):
        try: m.paste(Image.open(f'{SH}f30c{tag}_{f}_{k}.png').convert('RGB').resize((w, h)), (c * w, r * h))
        except FileNotFoundError: pass
m.save(OUT + tag + '_contact.jpg', quality=88)

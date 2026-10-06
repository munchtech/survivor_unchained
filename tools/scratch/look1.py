from sp import *
import os
im = Image.open(os.path.join(OLD, 'godot', '.shots', 'a4_hud_night.png'))
crops = [(480, 0, 620, 70), (10, 980, 160, 1070), (1760, 920, 1900, 1060)]
parts = [zoom(im.crop(c), 3) for c in crops]
sheet(parts).save(os.path.join(V, 'medals_ingame.png'))
zoom(im.crop((720, 940, 1200, 1060)), 2).save(os.path.join(V, 'skills_ingame.png'))
a = [Image.open(os.path.join(UI, 'hud', n)) for n in ('medal_level.png', 'medal_heart.png', 'ring_art.png')]
sheet(a, sizes=(None, 60)).save(os.path.join(V, 'medals_assets.png'))

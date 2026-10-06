import os
from PIL import Image
S = os.path.dirname(os.path.abspath(__file__))
W = Image.new('RGB', (1600, 928))
for i, (a, b) in enumerate([('portraits_raw', 'face_own'), ('p9b2', 'face_own'), ('portraits_raw', 'face_sunborn'), ('p9b2', 'face_sunborn')]):
    W.paste(Image.open(os.path.join(S, a, b + '.png')).convert('RGB').crop((200, 560, 1000, 1024)), ((i % 2) * 800, (i // 2) * 464))
W.save(os.path.join(S, 'band_v9b2.jpg'), quality=92)
print('ok')

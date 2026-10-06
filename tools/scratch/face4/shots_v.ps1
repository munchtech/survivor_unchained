param([string]$tag = 'v6')
# The Look's pictures of her default face under a godot turn, and the side-by-side in the four columns.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$g = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994\godot\.shots'
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: Look shots" --wait 30 | Out-Null
& "$sc\shot.ps1" "${tag}_long" 8 --new --sex female --step 1 --part 1 --hair long | Out-Null
& "$sc\shot.ps1" "${tag}_pony" 8 --new --sex female --step 1 --part 1 --hair ponytail | Out-Null
& "$sc\shot.ps1" "${tag}_long_l" 8 --new --sex female --step 1 --part 0 --hair long --turn 55 | Out-Null
& "$sc\shot.ps1" "${tag}_pony_r" 8 --new --sex female --step 1 --part 1 --hair ponytail --turn -40 | Out-Null
python $T give godot "face: Look shots" | Out-Null
Select-String -Path "$sc\logs\log_${tag}_long.txt" -Pattern "HerScalp" | Select-Object -First 2
python -c @"
from PIL import Image, ImageDraw
g, sc, tag = r'$g', r'$sc', '$tag'
H = 560
fit = lambda im: im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
cols = [('reference (her_23, Krea 2)', fit(Image.open(sc + r'\from_face3\refs_her\her_23.png').convert('RGB').crop((100, 170, 934, 1150)))),
        ('before: FACE v3 in game', fit(Image.open(sc + r'\from_face3\sbs_v3.jpg').convert('RGB').crop((468, 22, 865, 480)))),
        ('now (%s): Loose, Look close-up' % tag, fit(Image.open(g + r'\%s_long.png' % tag).convert('RGB').crop((660, 150, 1160, 740)))),
        ('now (%s): Tail, Look close-up' % tag, fit(Image.open(g + r'\%s_pony.png' % tag).convert('RGB').crop((660, 150, 1160, 740))))]
S = Image.new('RGB', (sum(i.width for _, i in cols), H + 22), (16, 16, 16))
d = ImageDraw.Draw(S)
x = 0
for t, i in cols:
    S.paste(i, (x, 22)); d.text((x + 6, 5), t, fill=(235, 235, 235)); x += i.width
S.save(g + r'\sbs_default_%s.jpg' % tag, quality=90)
print('SBS', S.size)
"@

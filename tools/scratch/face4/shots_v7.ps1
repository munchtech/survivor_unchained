param([string]$tag = 'v7')
# One godot turn: her default face (the four-column side-by-side), every preset at the Look's close-up (the ten-face
# sheet, each under its reference), and her at play zoom walking to the camera.
$w = 'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a833b7942e978d994'
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
$g = "$w\godot\.shots"
$T = 'C:/Users/munch/Desktop/survivorsunchained/tools/turn.py'
python $T take godot "face: v7 shots" --wait 60 | Out-Null
& "$sc\shot.ps1" "${tag}_long" 8 --new --sex female --step 1 --part 1 --hair long | Out-Null
& "$sc\shot.ps1" "${tag}_pony" 8 --new --sex female --step 1 --part 1 --hair ponytail | Out-Null
& "$sc\shot.ps1" "${tag}_pony_r" 8 --new --sex female --step 1 --part 1 --hair ponytail --turn -40 | Out-Null
$presets = Get-Content "$w\tools\assets\heroine_face\presets.json" -Raw | ConvertFrom-Json
foreach ($p in $presets) {
    if ($p.id -eq 'own') { continue }
    & "$sc\shot.ps1" "${tag}_p_$($p.id)" 8 --new --sex female --step 1 --part 1 --hair ponytail --preset $p.id --skin $p.skin --eyes $p.eyes | Out-Null
}
foreach ($c in 12.5, 22, 31) {
    & "$sc\shot.ps1" "${tag}_play_c$c" 9 --quick warden --sex female --hair long --zone arena --people dead --auto toward --cam $c | Out-Null
}
python $T give godot "face: v7 shots" | Out-Null
python -c @"
import json
from PIL import Image, ImageDraw
g, sc, tag, w = r'$g', r'$sc', '$tag', r'$w'
H = 560
fit = lambda im, h=H: im.resize((int(im.width * h / im.height), h), Image.LANCZOS)
crop = (660, 150, 1160, 740)
cols = [('reference (her_23, Krea 2)', fit(Image.open(sc + r'\from_face3\refs_her\her_23.png').convert('RGB').crop((100, 170, 934, 1150)))),
        ('before: FACE v3 in game', fit(Image.open(sc + r'\from_face3\sbs_v3.jpg').convert('RGB').crop((468, 22, 865, 480)))),
        ('now (%s): Loose, Look close-up' % tag, fit(Image.open(g + r'\%s_long.png' % tag).convert('RGB').crop(crop))),
        ('now (%s): Tail, Look close-up' % tag, fit(Image.open(g + r'\%s_pony.png' % tag).convert('RGB').crop(crop)))]
S = Image.new('RGB', (sum(i.width for _, i in cols), H + 22), (16, 16, 16)); d = ImageDraw.Draw(S); x = 0
for t, i in cols:
    S.paste(i, (x, 22)); d.text((x + 6, 5), t, fill=(235, 235, 235)); x += i.width
S.save(g + r'\sbs_default_%s.jpg' % tag, quality=90)
pre = json.load(open(w + r'\tools\assets\heroine_face\presets.json', encoding='utf-8'))
cw, rh = 330, 380
S = Image.new('RGB', (cw * 5, (rh * 2 + 22) * 2), (16, 16, 16)); d = ImageDraw.Draw(S)
for k, p in enumerate(pre):
    ref = p.get('ref', 'front/her_23').split('/')[-1]
    rp = sc + (r'\refs_front\%s.png' % ref if p['id'] != 'own' else r'\from_face3\refs_her\her_23.png')
    shot = g + (r'\%s_pony.png' % tag if p['id'] == 'own' else r'\%s_p_%s.png' % (tag, p['id']))
    x, y = (k % 5) * cw, (k // 5) * (rh * 2 + 22)
    r = Image.open(rp).convert('RGB'); r = r.crop((int(r.width * 0.12), int(r.height * 0.1), int(r.width * 0.88), int(r.height * 0.72))).resize((cw, rh), Image.LANCZOS)
    s = Image.open(shot).convert('RGB').crop((700, 160, 1120, 640)).resize((cw, rh), Image.LANCZOS)
    S.paste(r, (x, y + 22)); S.paste(s, (x, y + 22 + rh)); d.text((x + 6, y + 5), p['name'], fill=(235, 235, 235))
S.save(g + r'\presets_%s.jpg' % tag, quality=88)
print('SHEETS done')
"@

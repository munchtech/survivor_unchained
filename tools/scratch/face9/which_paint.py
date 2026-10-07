"""Which per-face output folder (inputs face4..face7 paint_<id>) made the face paint in use."""
import hashlib, os
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aed215ba3ca60cc29\tools\assets\heroine_face'
I = r'C:\Users\munch\Desktop\survivorsunchained_inputs'
ids = ['doe', 'fey', 'hardwon', 'highborn', 'moonlit', 'saffron', 'sunborn', 'vixen', 'wildling']


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()[:10]


for i in ids:
    cur = md5(os.path.join(W, 'face_paint_%s.png' % i))
    hits = []
    for f in ('face4', 'face5', 'face6', 'face7'):
        p = os.path.join(I, f, 'paint_' + i, 'face_paint.png')
        if os.path.exists(p):
            hits.append('%s:%s' % (f, 'SAME' if md5(p) == cur else 'diff'))
    print(i, cur, ' '.join(hits))
# hers
cur = md5(os.path.join(W, 'face_paint.png'))
for f in ('face4', 'face5', 'face6', 'face7'):
    for d in sorted(os.listdir(os.path.join(I, f))):
        p = os.path.join(I, f, d, 'face_paint.png')
        if d.startswith('paint') and os.path.exists(p) and md5(p) == cur:
            print('own SAME as', f, d)

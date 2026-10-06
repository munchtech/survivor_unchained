import os

S = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(S, 'do_anim.py')
s = open(p, encoding='utf-8').read()
s = s.replace('frames = chainanim.run(tabs, 1, 3, scale, bg=bg, y0=60.0, x0=34.0, x1=566.0, bg_after=bg2)',
              'frames = chainanim.run(tabs, 1, 3, scale, bg=bg, y0=62.0, bg_after=bg2)')
open(p, 'w', encoding='utf-8').write(s)
p = os.path.join(S, 'do_video.py')
s = open(p, encoding='utf-8').read()
s = s.replace("    a = chainanim.run(tabs, 1, 3, scale, bg=bgs[1], y0=60.0, x0=34.0, x1=566.0, bg_after=bgs[3], secs=1.0)",
              "    a = chainanim.run(tabs, 1, 3, scale, bg=bgs[1], y0=62.0, bg_after=bgs[3], secs=1.4)")
s = s.replace("    b = chainanim.run(tabs, 3, 0, scale, bg=bgs[3], y0=60.0, x0=34.0, x1=566.0, bg_after=bgs[0], secs=1.0)",
              "    b = chainanim.run(tabs, 3, 0, scale, bg=bgs[3], y0=62.0, bg_after=bgs[0], secs=1.4)")
s = s.replace("        s = SP.chain(int(round(links)), 0.32, seed)", "        s = SP.chain(int(round(links)), 0.32, seed)")
open(p, 'w', encoding='utf-8').write(s)
print(open(os.path.join(S, 'do_video.py')).read().count('secs=1.4'))

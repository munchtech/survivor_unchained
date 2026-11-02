import sys, os, numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/mock')
import foot as F
CW = os.path.dirname(os.path.abspath(__file__))
BOX = {'town_day': (914, 476, 992, 600), 'ford_night': (932, 478, 996, 590)}
RECTS = {'town_day': (893, 436, 130, 200), 'ford_night': (891, 432, 130, 200)}
for p, r in RECTS.items():
    fo, nf = F.foot_rgb(p)
    img = (np.clip(nf, 0, 1) * 255).astype(np.uint8)[..., ::-1].copy()
    m = np.zeros(img.shape[:2], np.uint8)
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    bx0, by0, bx1, by1 = BOX[p]
    m[:] = cv2.GC_BGD
    m[by0:by1, bx0:bx1] = cv2.GC_PR_BGD
    cx, cy = (bx0 + bx1) // 2, (by0 + by1) // 2
    cv2.ellipse(m, (cx, cy), ((bx1 - bx0) // 4, (by1 - by0) // 3), 0, 0, 360, cv2.GC_PR_FGD, -1)
    cv2.ellipse(m, (cx, cy - 6), (6, (by1 - by0) // 4), 0, 0, 360, cv2.GC_FGD, -1)
    cv2.grabCut(img, m, None, bg, fg, 10, cv2.GC_INIT_WITH_MASK)
    s = ((m == 1) | (m == 3)).astype(np.uint8)
    # keep the biggest component
    n, lab, stats, _ = cv2.connectedComponentsWithStats(s)
    if n > 1:
        k = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA]); s = (lab == k).astype(np.uint8)
    if p == 'town_day':                      # the sword, a 2 px blade grabCut can't see on the cobbles
        cv2.line(s, (937, 540), (935, 579), 1, 2)
    s = cv2.morphologyEx(s, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    np.save(os.path.join(CW, 'she_%s.npy' % p), s)
    x, y, w, h = r
    crop = img[y - 10:y + h + 10, x - 10:x + w + 10].copy()
    if 'night' not in p: pass
    crop = np.clip(crop.astype(np.float32) * (1.0 if 'day' in p else 1.6), 0, 255).astype(np.uint8)
    cs = s[y - 10:y + h + 10, x - 10:x + w + 10]
    cnt, _ = cv2.findContours(cs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(crop, cnt, -1, (0, 255, 0), 1)
    cv2.imwrite(os.path.join(CW, 'she_chk_%s.png' % p), cv2.resize(crop, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST))
    ys, xs = np.nonzero(s); print(p, s.sum(), xs.min(), xs.max(), ys.min(), ys.max())

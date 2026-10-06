import os
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a72467cac33063d3a"
p = os.path.join(W, "tools", "uiforge", "medals.py")
s = open(p, encoding="utf-8").read()

# 1. The chain as a helper.
a = s.index('# The stone: its half-width')
helper = '''def chain_round(R, c, rc, n, link_len, link_w, wire, base, open_at=0, gap=2.2):
    """A chain coiled round a circle (file px): `n` links (even), alternately lying flat and
    standing on edge, the flat link at `open_at` pried open on its outer side. Returns
    (height in file px, mask, the break's glow) at render res."""
    X, Y = R.xx / R.ss, R.yy / R.ss
    link_h = np.zeros(X.shape, np.float32)
    link_m = np.zeros(X.shape, np.float32)
    brk = np.zeros(X.shape, np.float32)
    for i in range(n):
        a = 2 * math.pi * i / n
        lx, ly = c + math.sin(a) * rc, c - math.cos(a) * rc
        ca, sa = math.cos(a), math.sin(a)
        u = (X - lx) * ca + (Y - ly) * sa
        v = -(X - lx) * sa + (Y - ly) * ca
        if i % 2 == 0:
            d = stadium_sd(X, Y, lx, ly, link_len, link_w, angle=a)
            hh = np.sqrt(np.clip(1 - (d / wire) ** 2, 0, 1)) * wire + base
            if open_at is not None and i == open_at:
                # Pried open: its outer side cut through, the ends sprung apart.
                cut = (np.abs(u) < gap) & (v < 0)
                hh = np.where(cut, 0, hh)
                brk = np.exp(-((u / (gap * 0.65)) ** 2 + ((v + link_w / 2) / (wire * 0.7)) ** 2)).astype(np.float32)
        else:
            # On edge: seen from above, a bar the length of the link's inside, standing taller.
            d = np.hypot(np.clip(np.abs(u) - (link_len - link_w) * 0.62, 0, None), v)
            hh = np.sqrt(np.clip(1 - (d / wire) ** 2, 0, 1)) * wire + base + link_w * 0.25
        m = (hh > base + 0.01) * np.clip((wire - d) * R.ss + 0.5, 0, 1)
        link_h = np.maximum(link_h, hh * m)
        link_m = np.maximum(link_m, m)
    return link_h, link_m, brk


'''
s = s[:a] + helper + s[a:]

# 2. The heart medal uses it.
a = s.index('        N = CHAIN\n        link_h = np.zeros_like(r)')
b = s.index('        h = np.where(link_m > 0.5, np.maximum(h, link_h), h)', a)
s = s[:a] + '        link_h, link_m, brk = chain_round(R, c, rc, CHAIN, 16.5, 8.6, 1.75, 2.4)\n' + s[b:]

# 3. The globe.
a = s.index('IRON = (')
s = s[:a] + open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "globe_src.py"), encoding="utf-8").read() + s[a:]
open(p, "w", encoding="utf-8").write(s)
print("patched")

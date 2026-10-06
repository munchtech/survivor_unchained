import os
W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a69858664f1d3dd29'


def edit(rel, pairs):
    """Exact replacements in a worktree file, each found once, its line endings kept."""
    p = os.path.join(W, rel)
    s = open(p, encoding='utf-8', newline='').read()
    crlf = '\r\n' in s
    for a, b in pairs:
        if crlf:
            a, b = a.replace('\n', '\r\n'), b.replace('\n', '\r\n')
        n = s.count(a)
        assert n == 1, (rel, n, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8', newline='').write(s)
    print('edited', rel, len(s))

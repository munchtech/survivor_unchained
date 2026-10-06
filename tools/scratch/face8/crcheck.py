import sys
O = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6007bf07fd45ab0d'
N = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a2f7b0f1283f6144a'
for f in sys.argv[1:]:
    a = open(O + '/' + f, 'rb').read(); b = open(N + '/' + f, 'rb').read()
    same = a.replace(b'\r\n', b'\n') == b.replace(b'\r\n', b'\n')
    print(f, len(a), len(b), 'old-crlf', a.count(b'\r\n'), 'new-crlf', b.count(b'\r\n'), 'same-ignoring-cr', same)

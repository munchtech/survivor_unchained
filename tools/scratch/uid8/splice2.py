import sys
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa1f430bd64b8d1ce\godot\src\Ui\Menus.cs'
new = open(sys.argv[1], encoding='utf-8').read()
s = open(p, encoding='utf-8', newline='').read()
crlf = '\r\n' in s
if crlf: new = new.replace('\r\n', '\n').replace('\n', '\r\n')
a = s.index('/// <summary>The settings, as rows of choices')
s = s[:a] + new
open(p, 'w', encoding='utf-8', newline='').write(s)
print('spliced at', a, 'crlf', crlf)

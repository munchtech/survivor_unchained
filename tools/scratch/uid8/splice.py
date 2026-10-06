import sys
p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa1f430bd64b8d1ce\godot\src\Ui\Front.cs'
new = open(sys.argv[1], encoding='utf-8').read()
s = open(p, encoding='utf-8', newline='').read()
crlf = '\r\n' in s
if crlf: new = new.replace('\r\n', '\n').replace('\n', '\r\n')
nl = '\r\n' if crlf else '\n'
a = s.index('    protected override void Build()' + nl + '    {' + nl + '        var a = Callings.Archetype(d.Archetype);')
b = s.index('    public override bool Key(Act a)' + nl + '    {' + nl + '        // Typing a name')
s = s[:a] + new + s[b:]
open(p, 'w', encoding='utf-8', newline='').write(s)
print('spliced', b - a, '->', len(new))

W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''        if (!runUp && seconds >= End - 120)
        {
            RunUp();
            B.Events.Drain();
        }''',
'''        if (!runUp && seconds >= End - 120) RunUp(quiet: true);'''),
('''    void RunUp()''', '''    void RunUp(bool quiet = false)'''),
('''        B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = sign });''',
'''        if (!quiet) B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = sign });'''),
('''        G.Announce(new Announcement("The half hour nears", "It comes from where the sign was", "danger", 2.6));''',
'''        if (!quiet) G.Announce(new Announcement("The half hour nears", "It comes from where the sign was", "danger", 2.6));'''),
])
print("ok")

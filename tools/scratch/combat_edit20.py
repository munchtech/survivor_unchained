W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Bosses\ArenaBoss.cs', [
('''    public void Begin(Enemy e)
    {
        E = e;''',
'''    /// <summary>Its health as it came (the creature it was is pooled: once it is gone the
    /// same body is soon a wolf, and its numbers are the wolf's).</summary>
    public double MaxHp { get; private set; }

    public void Begin(Enemy e)
    {
        E = e;
        MaxHp = e.MaxHp;'''),
])
edit(r'balance\Harness\ArenaSim.cs', [
('''            r.BossBreak = bs.BreakSum / Math.Max(1, bs.E.MaxHp);''',
'''            r.BossBreak = bs.BreakSum / Math.Max(1, bs.MaxHp);'''),
])
print("ok")

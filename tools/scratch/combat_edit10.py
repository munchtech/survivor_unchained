W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Zones\ArenaRun.cs', [
('''    /// <summary>Those falling back for their ruler, until they are out of sight.</summary>
    readonly HashSet<int> makingWay = new();''',
'''    /// <summary>Those falling back for their ruler, until they are out of sight (by pool
    /// slot and spawn, since a slot let go is soon another creature).</summary>
    readonly Dictionary<int, int> makingWay = new();'''),
('''            makingWay.Add(o.Id);''', '''            makingWay[o.Id] = o.Seed;'''),
('''        foreach (var id in makingWay.ToList())
        {
            var o = B.Enemies.Items[id];
            double d2 = (o.X - p.X) * (o.X - p.X) + (o.Z - p.Z) * (o.Z - p.Z);
            if (!o.Alive || o.State == EnemyState.Dying) makingWay.Remove(id);''',
'''        foreach (var (id, seed) in makingWay.ToList())
        {
            var o = B.Enemies.Items[id];
            double d2 = (o.X - p.X) * (o.X - p.X) + (o.Z - p.Z) * (o.Z - p.Z);
            if (!o.Alive || o.Seed != seed || o.State == EnemyState.Dying) makingWay.Remove(id);'''),
])
print("ok")

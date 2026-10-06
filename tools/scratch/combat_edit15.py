W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Bosses\ArenaBoss.cs', [
('''        TransitionT = 2.5 + Math.Min(2.5, over / Math.Max(1, e.MaxHp) * 25);
        e.TakenMul = 0;
        Channel = null;
        B.Interrupt(e);''',
'''        TransitionT = 2.5 + Math.Min(2.5, over / Math.Max(1, e.MaxHp) * 25);
        e.TakenMul = 0;
        Channel = null;
        // Whatever it was winding up is dropped, quietly: the turn is the news, not an
        // "Interrupted!" over it, and an old move must not finish in the new phase.
        move = null;
        e.State = EnemyState.Active;'''),
])

edit(r'src\Fx\Hits.cs', [
('''    /// <summary>A boss's word over its mark: steady for `life` seconds, then gone in a breath.</summary>''',
'''    /// <summary>The boss's words now showing put away (the BREAK is said alone).</summary>
    public void ClearWords()
    {
        for (int i = 0; i < words.Count; i++)
        {
            var (l, t, life, at) = words[i];
            if (t < 1) { l.Visible = false; words[i] = (l, 1, life, at); }
        }
    }

    /// <summary>A boss's word over its mark: steady for `life` seconds, then gone in a breath.</summary>'''),
])

edit(r'src\Fx\BattleFx.cs', [
('''                    var at = V(br.X, Y(br.X, br.Z) + 2.6, br.Z);
                    Hits.Word(at, $"BREAK {Math.Round(br.Amount):N0}", new Color(2.4f, 1.9f, 0.6f), 84, 2.2f);''',
'''                    // High over the boss and alone: the moves' names it would sit among are put away.
                    var at = V(br.X, Y(br.X, br.Z) + 5.2, br.Z);
                    Hits.ClearWords();
                    Hits.Word(at, $"BREAK {Math.Round(br.Amount):N0}", new Color(2.4f, 1.9f, 0.6f), 104, 2.4f);'''),
])
print("ok")

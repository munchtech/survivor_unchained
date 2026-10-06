W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic\Play\Bosses"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

r = W + r"\Redcowl.cs"
sub(r, """        if (S.CanSpare)
        {
            S.Offer("let_go", e.X, e.Z, S.SpareVerb, Him, () => Choose(true));
            S.Offer("finish", e.X, e.Z, "Finish it", Him, () => Choose(false));
        }
        else Choose(false);""", """        // Her choice, named on the screen and answered from wherever she stands (not a prompt at his side).
        if (S.CanSpare)
            S.Ask(Him, $"{S.SpareVerb}, or finish it", e.X, e.Z, new ChoiceAnswer("let_go", S.SpareVerb, () => Choose(true)), new ChoiceAnswer("finish", "Finish it", () => Choose(false)));
        else Choose(false);""")
sub(r, """    void Choose(bool spare)
    {
        S.Withdraw("let_go");
        S.Withdraw("finish");
        if (!spare)""", """    void Choose(bool spare)
    {
        S.Unask();
        if (!spare)""")
sub(r, """        e.TakenMul = 0;
        if (goT < 0 || (goT += dt) < 1.5) { e.Vx = e.Vz = 0; e.State = EnemyState.Idle; e.Anim = EnemyAnim.Idle; return true; }""", """        e.TakenMul = 0;
        // While she chooses, his lot keep back from her: the fight is over, however long she takes.
        if (goT < 0) foreach (var l in lot) if (l.E.Alive && l.E.Seed == l.Seed && l.E.State != EnemyState.Dying && (l.E.Status[StatusKind.Fear]?.T ?? 0) < 2) l.E.Status[StatusKind.Fear] = new StatusSlot(6, 1, 1, 0);
        if (goT < 0 || (goT += dt) < 1.5) { e.Vx = e.Vz = 0; e.State = EnemyState.Idle; e.Anim = EnemyAnim.Idle; return true; }""")
sub(r, """        levy = null;
        S.Withdraw("let_go");
        S.Withdraw("finish");""", """        levy = null;
        S.Unask();""")

g = W + r"\Greymuzzle.cs"
sub(g, """        if (S.CanSpare)
        {
            S.Offer("let_go", e.X, e.Z, S.SpareVerb, "Greymuzzle", () => Choose(true));
            S.Offer("finish", e.X, e.Z, "Finish it", "Greymuzzle", () => Choose(false));
        }
        else if (A.Spare) Choose(true);""", """        // Her choice, named on the screen and answered from wherever she stands (not a prompt at his side).
        if (S.CanSpare)
            S.Ask("Greymuzzle", $"{S.SpareVerb}, or finish it", e.X, e.Z, new ChoiceAnswer("let_go", S.SpareVerb, () => Choose(true)), new ChoiceAnswer("finish", "Finish it", () => Choose(false)));
        else if (A.Spare) Choose(true);""")
sub(g, """    void Choose(bool spare)
    {
        S.Withdraw("let_go");
        S.Withdraw("finish");
        if (!spare)""", """    void Choose(bool spare)
    {
        S.Unask();
        if (!spare)""")
sub(g, """        guard.Clear();
        S.Withdraw("let_go");
        S.Withdraw("finish");""", """        guard.Clear();
        S.Unask();""")
print("ok")

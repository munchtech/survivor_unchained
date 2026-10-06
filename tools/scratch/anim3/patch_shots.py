p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a03acf30b3e9bdd70\godot\src\Game\Game.cs"
s = open(p, encoding="utf-8").read()


def rep(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new)


rep('''            if (Shots.On("boss")) BossShot(e);''', '''            if (Shots.On("boss") || Shots.On("casts")) BossShot(e);''')
rep('''    /// <summary>--on boss: a frame of each boss move as it is marked, its Break, its
    /// stagger, its arrival and what is announced (Shots.Want).</summary>
    static void BossShot(CombatEvent e)
    {
        switch (e)
        {
            case Ev.Telegraph t when t.Boss && t.Label is { Length: > 0 } l: Shots.Want(l, Math.Min(0.7, t.Duration * 0.6)); break;''', '''    /// <summary>--on boss: a frame of each boss move as it is marked, its Break, its
    /// stagger, its arrival and what is announced (Shots.Want). --on casts: a run of
    /// frames, fifteen a second, through each creature's marked cast and a second after
    /// it (judging a slam or a call as the player sees it).</summary>
    static void BossShot(CombatEvent e)
    {
        switch (e)
        {
            case Ev.Telegraph t when Shots.On("casts") && t.Id >= 0 && t.Hostile:
                for (int i = 0; i * (1 / 15.0) < t.Duration + 1; i++) Shots.Want($"cast{t.Id}", i / 15.0);
                break;
            case Ev.Telegraph t when t.Boss && t.Label is { Length: > 0 } l: Shots.Want(l, Math.Min(0.7, t.Duration * 0.6)); break;''')
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")

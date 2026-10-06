L = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

sub(L + r"\Play\Bosses\StoryBoss.cs", """    /// <summary>What the space does each step while it lives (a ring that holds, frost that closes),
    /// whether or not it is moving: its moves are Act's, its ground is this.</summary>
    public virtual void Step(double dt) { }""", """    /// <summary>What the space does each step while it lives (a ring that holds, frost that closes),
    /// whether or not it is moving: its moves are Act's, its ground is this.</summary>
    public virtual void Step(double dt) { }

    /// <summary>Past its hard mark it hits the harder the longer it goes, three per cent a second: it is the end
    /// of it, one way or the other (escalate, never execute). A build that cannot finish it by then falls, and
    /// comes back a day on with better; without this, the weakest stood a single life of thirteen minutes at
    /// Grimtunnel and ten at Greymuzzle, neither of them able to end it.</summary>
    public void Grows(double dt)
    {
        if (Hard && E is { Alive: true } && !Ending) E.Damage *= 1 + 0.03 * dt;
    }""")
sub(L + r"\Play\Zones\StoryNight.cs", """                ShutBehind();
                script?.Step(dt);""", """                ShutBehind();
                script?.Grows(dt);
                script?.Step(dt);""")
sub(L + r"\Play\Bosses\Redcowl.cs", """        if (Hard && E != null && !Ending) E.Damage *= 1 + 0.03 * dt;
        StepGround(dt);""", """        StepGround(dt);""")
print("ok")

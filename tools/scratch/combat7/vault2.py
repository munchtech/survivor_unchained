L = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:70], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

f = L + r"\Play\Story\StoryFight.cs"
sub(f, """    /// <summary>The place's fires (id, point), and how long one burns.</summary>
    public virtual string[] Fires => [];""", """    /// <summary>The place's fires (id, point), and how long one burns.</summary>
    public virtual string[] Fires => [];
    /// <summary>What the fight itself stands in its place as the night opens (the Vault's cover down the hall),
    /// solid and drawn, before anything moves.</summary>
    public virtual void Furnish(IStoryArena a) { }""")
sub(f, """        "dig_boils" => new DigBoilsOver(),
        _ => null,""", """        "dig_boils" => new DigBoilsOver(),
        "vault_opened" => new VaultOpened(),
        _ => null,""")

n = L + r"\Play\Zones\StoryNight.cs"
sub(n, """        place.Build(b.Collision);
        b.Charges.Spikes = false;""", """        place.Build(b.Collision);
        Fight.Furnish(this);
        b.Charges.Spikes = false;""")

b = L + r"\Play\Bosses\BarrowLordStory.cs"
sub(b, """    /// <summary>The standard in a testudo (a part), and whether one broken can be lifted, and has been.</summary>
    Enemy? standard;
    double standardSeed, chargeT = -1, heldT;""", """    /// <summary>The standard in a testudo (a part), and whether one broken can be lifted, and has been.</summary>
    VaultOpened.Standard? standard;
    double chargeT = -1, heldT;""")
sub(b, """        var (dx, dz, _) = ToPlayer();
        standard = S.Spawn("legion_standard", e.X + dx * 1.4, e.Z + dz * 1.4, false, SpawnStyle.Rise);
        if (standard != null)
        {
            standardSeed = standard.Seed;
            standard.MaxHp = standard.Hp = MaxHp * 0.06;
            standard.Named = new Named { Title = "The standard" };
        }
        StepDown();""", """        var (dx, dz, _) = ToPlayer();
        standard = VaultOpened.Standard.Plant(S, e.X + dx * 1.4, e.Z + dz * 1.4, MaxHp * 0.06);
        StepDown();""")
sub(b, """        shell.Clear();
        if (Up(standard, standardSeed)) B.Enemies.Release(standard!);
        standard = null;
    }

    /// <summary>The standard is broken""", """        shell.Clear();
        standard?.Gone(B, true);
        standard = null;
    }

    /// <summary>The standard is broken""")
sub(b, """        foreach (var m in shell) if (Here(m)) B.Enemies.Release(m.E);
        shell.Clear();
        standard = null;
        chargeT = -1;""", """        foreach (var m in shell) if (Here(m)) B.Enemies.Release(m.E);
        shell.Clear();
        standard?.Gone(B, false);
        standard = null;
        chargeT = -1;""")
sub(b, """        if (standard != null && !Up(standard, standardSeed)) StandardBroken(standard.X, standard.Z);""",
"""        if (standard is { Up: false } broken) StandardBroken(broken.X, broken.Z);""")
sub(b, """    public Enemy? Standard => Up(standard, standardSeed) ? standard : null;""", """    public Enemy? Standard => standard is { Up: true } s ? s.E : null;""")
sub(b, """        if (Up(standard, standardSeed)) B.Enemies.Release(standard!);
        standard = null;
        foreach (var (id, _) in pila)""", """        standard?.Gone(B, true);
        standard = null;
        foreach (var (id, _) in pila)""")
print("ok")

L = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:60], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

b = L + r"\Play\Bosses\BarrowLordStory.cs"
sub(b, "        E.Channel = null;\n", "        Channel = null;\n")
sub(b, "    void Hold(double dt)\n", "    void Walls(double dt)\n")
sub(b, "        Hold(dt);\n        Front(dt);", "        Walls(dt);\n        Front(dt);")

e = L + r"\Content\Enemies.cs"
sub(e, """        new() { Id = "mb_ford_bell", Name = "The Signifer",""", """        // The Legion's standard, planted (the Vault's hall, the Barrow Lord's testudo): a part, not a fighter. While
        // it stands the dead round it are quicker and harder to hurt; holy and fire break it the sooner.
        new() { Id = "legion_standard", Name = "The Standard", Family = Family.Undead, Faction = Faction.Dead, Visual = "view:standard",
            Health = 260, Speed = 0, Damage = 0, Radius = 0.6, Mass = 999, Xp = 6, Behavior = Behavior.Stationary, AttackEvery = 1e9,
            Resists = new() { [School.Holy] = -0.5, [School.Fire] = -0.5, [School.Frost] = 0.25, [School.Shadow] = 0.35 },
            Aura = new(6, 4.5, 7, Haste: 1.3, Ward: 0.25),
            Note = "VII on a pole, on a rag that was red once. The dead never followed a man: they followed this." },
        new() { Id = "mb_ford_bell", Name = "The Signifer",""")
print("ok")

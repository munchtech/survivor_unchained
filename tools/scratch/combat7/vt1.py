p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\tests\VaultTests.cs"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:70], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)
sub(p, "public void The_Decurion_is_behind his_shields_until_she_is_round_them()", "public void The_Decurion_is_behind_his_shields_until_she_is_round_them()")
sub(p, """        Step(n, 6, each: _ => { p.X = 0; p.Z = 2; Quiet(n, s); });
        Assert.Contains(n.B.Blows, b => b.Label == "A bolt" || b.Source == s.Def.Name);""", """        Step(n, 9, each: _ => { p.X = 0; p.Z = 2; Quiet(n, s); }, until: () => n.B.Blows.Any(b => b.Label == "A bolt"));
        Assert.Contains(n.B.Blows, b => b.Label == "A bolt");""")
print("ok")

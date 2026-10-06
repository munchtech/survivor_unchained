L = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a427a874da78cba8b\godot\logic"
def sub(path, old, new, count=1):
    t = open(path, encoding="utf-8").read()
    n = t.count(old)
    assert n == count, (path, old[:70], n)
    t = t.replace(old, new)
    open(path, "w", encoding="utf-8", newline="").write(t)

v = L + r"\Play\Story\Vault.cs"
sub(v, """scorpion = A.Foe("mb_old_quarrel", x, z, 6);""", """scorpion = A.Foe("mb_old_quarrel", x, z, 9);""")
b = L + r"\Play\Bosses\BarrowLordStory.cs"
sub(b, "public override double HealthMul(int tier) => 135;", "public override double HealthMul(int tier) => 120;")
sub(b, """B.ShovePlayer(C.X - p.X, C.Z - p.Z, 2, grace <= 0 ? E.Damage * 0.5 : 0, "the front");""", """B.ShovePlayer(C.X - p.X, C.Z - p.Z, 2, grace <= 0 ? E.Damage * 0.3 : 0, "the front");""")
sub(b, """B.ShovePlayer(-Math.Sign(off), 0, 2, grace <= 0 ? E.Damage * 0.5 : 0, "the ranks");""", """B.ShovePlayer(-Math.Sign(off), 0, 2, grace <= 0 ? E.Damage * 0.3 : 0, "the ranks");""")
print("ok")

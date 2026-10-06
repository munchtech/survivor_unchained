W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'logic\Play\Bosses\ArenaBosses.cs', [
# Pack-Mother
('''    public override string WeaknessText => $"Fire breaks {Her} moon-howl";''',
'''    public override string WeaknessText => $"Fire breaks {Her} moon-howl";
    // Measured (docs/team/combat.md): at 12 + 2 a tier a par build broke her for 63% of
    // her health over the floors and won in 69 s; the contract asks 90-120.
    public override double HealthMul(int tier) => 27 + 4.5 * tier;'''),
# Barrow Lord
('''    public override double HealthMul(int tier) => 9 + 1.5 * tier;''',
'''    // 9 + 1.5 a tier measured 80 s and a 14% Break with his laying-down; the contract asks 90-120.
    public override double HealthMul(int tier) => 13 + 2.2 * tier;'''),
# Grimtunnel / Ganger
('''    public bool Ganger => ganger;''',
'''    public bool Ganger => ganger;
    // 12 + 2 a tier measured 92 s and a 66% Break (under the ground he takes half).
    public override double HealthMul(int tier) => 18 + 3 * tier;'''),
# Red Hand
('''    public override string WeaknessText => "Storm makes his thief drop what he took";''',
'''    public override string WeaknessText => "Storm makes his thief drop what he took";
    // 12 + 2 a tier measured 72 s and a 15% Break.
    public override double HealthMul(int tier) => 19 + 3.2 * tier;'''),
])
print("ok")

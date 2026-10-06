import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')
p = 'logic/Play/Zones/ArenaRun.cs'
s = open(p, encoding='utf-8').read()
for new, old in [
    ("    // A tier is three creature levels, the survivor's own pace (levels 1, 4, 7 for tiers 1, 2, 3):\n    // a tier is harder for being more of the horde, and more champions, not for outlevelling.\n    int Level() => Math.Max(1, Spec.Tier * 3 - 2 + levels + (int)(Minute / 2.5) + (int)(Beyond / 2));",
     "    int Level() => Math.Max(1, Spec.Tier * 2 - 1 + levels + (int)(Minute / 2.5) + (int)(Beyond / 2));"),
    ("(22 + 7.5 * Minute) * packSize * (1 + 0.2 * (Spec.Tier - 1)) * Bargain);", "(22 + 7.5 * Minute) * packSize * (1 + 0.12 * (Spec.Tier - 1)) * Bargain);"),
    ("R() < 0.012 * elites * (1 + Minute / 12) * (1 + 0.4 * (Spec.Tier - 1)))", "R() < 0.012 * elites * (1 + Minute / 12))"),
]:
    assert s.count(new) == 1, new[:40]
    s = s.replace(new, old)
open(p, 'w', encoding='utf-8').write(s)

p = 'balance/Program.cs'
s = open(p, encoding='utf-8').read()
old = '''    // --oaths none|all|a,b+c: unsworn, each oath alone, or the ones named ('+' swears two at once).
    var oaths = opt.List("oaths", "none") is ["all"] ? new[] { "none" }.Concat(MapOffers.Oaths.Select(o => o.Id)).ToArray() : opt.List("oaths", "none");'''
new = '''    // --oaths none|all|table|a,b+c: unsworn, each oath alone, as the Wayfinder's table swears
    // them (none or one at tier 1, two at tiers 2 and 3, three from 4), or the ones named ('+' swears two at once).
    var oaths = opt.Get("oaths", "none") == "table" ? ["table"] : opt.List("oaths", "none") is ["all"] ? new[] { "none" }.Concat(MapOffers.Oaths.Select(o => o.Id)).ToArray() : opt.List("oaths", "none");
    string[]? Sworn(string oath, int tier, int seed)
    {
        if (oath == "none") return null;
        if (oath != "table") return oath.Split('+');
        var rng = new Rng((uint)(seed * 104729 + tier * 7919 + 3));
        int n = tier <= 1 ? (seed % 3 == 0 ? 0 : 1) : Math.Min(3, 1 + tier / 2);
        return n == 0 ? null : rng.Shuffle(MapOffers.Oaths.Select(o => o.Id).ToList()).Take(n).ToArray();
    }'''
assert s.count(old) == 1
s = s.replace(old, new)
old2 = 'peoples[(s + w) % peoples.Length], oath == "none" ? null : oath.Split(\'+\'),'
assert s.count(old2) == 1
s = s.replace(old2, 'peoples[(s + w) % peoples.Length], Sworn(oath, tier, seed0 + s),')
open(p, 'w', encoding='utf-8').write(s)
print('ok')

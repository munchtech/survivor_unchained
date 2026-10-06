p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Book.cs'
s = open(p, encoding='utf-8').read()
old = '''                if (then != null && Math.Abs(then.Get(key) - now) > 1e-6)
                    line.AddChild(Style.Label($"to {fmt(then.Get(key))}", Style.UiBold, Style.Small, Style.Good));'''
new = '''                if (then != null && Math.Abs(then.Get(key) - now) > 1e-6)
                    line.AddChild(Style.Label(Change(key, now, then.Get(key)), Style.UiBold, Style.Small, Style.Good));'''
assert old in s
s = s.replace(old, new, 1)
old2 = '''    /// <summary>Where a number comes from: the calling's base, then each thing that moves it.</summary>'''
new2 = '''    /// <summary>What a point would change, as the change itself (a tenth of a percent shows).</summary>
    static string Change(string key, double now, double then) => key switch
    {
        Stat.CritChance or Stat.Dodge => $"{(then - now) * 100:+0.0;-0.0}%",
        Stat.Cooldown => $"{(1 / then - 1 / now) * 100:+0.0;-0.0}% faster",
        Stat.CritDamage => $"{then - now:+0.00;-0.00}×",
        Stat.MaxHealth or Stat.Armor or Stat.MoveSpeed or Stat.Regen or Stat.PickupRadius or Stat.DashCharges => $"{then - now:+0.##;-0.##}",
        _ => $"{(then - now) * 100:+0.#;-0.#}%",
    };

    /// <summary>Where a number comes from: the calling's base, then each thing that moves it.</summary>'''
assert old2 in s
s = s.replace(old2, new2, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')

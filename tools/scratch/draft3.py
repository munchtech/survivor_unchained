p = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src\Ui\Panels.cs'
s = open(p, encoding='utf-8').read()
pairs = [
("""    /// <summary>New to the build (said on the card: the survivors' "New!").</summary>""",
"""    /// <summary>The held skill this card would let evolve (a passive it needs), if any: the
    /// survivors' "needed to evolve", said on the card and lit in the build.</summary>
    WeaponInst? Evolves(Offer o)
    {
        if (o.Kind != OfferKind.Boon || v.Battle == null) return null;
        foreach (var w in v.Battle.Weapons)
            if (w.Evolution == null && LevelUp.EvolvesWith(w.Id).Any(e => e.Passives.Contains(o.Id))) return w;
        return null;
    }

    /// <summary>New to the build (said on the card: the survivors' "New!").</summary>"""),
("""        if (o.Kind == OfferKind.Evolve && Weapons.All.TryGetValue(o.Id, out var from))
            v2.AddChild(Style.Label($"{from.Name} becomes {o.Title}", Style.UiBold, Style.Caption, new Color("#ffd88a"), true, HorizontalAlignment.Center));""",
"""        if (o.Kind == OfferKind.Evolve && Weapons.All.TryGetValue(o.Id, out var from))
            v2.AddChild(Style.Label($"{from.Name} becomes {o.Title}", Style.UiBold, Style.Caption, new Color("#ffd88a"), true, HorizontalAlignment.Center));
        if (Evolves(o) is { } ev)
        {
            // It is what a held skill needs to evolve: said plainly, in gold.
            var badge = Style.Panel(Style.Box(new Color("#2a1c08"), Style.Gold, 1, 10, 6),
                Style.H(5, Glyphs.Icon("expand", 14, Style.EmberHi), Style.Label($"Evolves {ev.Def.Name} at rank {Weapons.MaxRank}", Style.UiBold, Style.Caption, Style.EmberHi)));
            badge.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
            v2.AddChild(badge);
        }"""),
("""            string? id = o.Kind is OfferKind.Rank or OfferKind.Evolve ? o.Id : o.Kind == OfferKind.Weapon ? "~new" : o.Kind == OfferKind.Boon && (o.From ?? 0) > 0 ? o.Id : null;
            if (id != null && buildChips.TryGetValue(id, out var lit)) lit.Modulate = new Color(1.5f, 1.35f, 1.1f);""",
"""            string? id = o.Kind is OfferKind.Rank or OfferKind.Evolve ? o.Id : o.Kind == OfferKind.Weapon ? "~new" : o.Kind == OfferKind.Boon && (o.From ?? 0) > 0 ? o.Id : null;
            if (id != null && buildChips.TryGetValue(id, out var lit)) lit.Modulate = new Color(1.5f, 1.35f, 1.1f);
            // A passive that would evolve a held skill lights that skill too.
            if (Evolves(o) is { } ev && buildChips.TryGetValue(ev.Id, out var evo)) evo.Modulate = new Color(1.6f, 1.3f, 0.9f);"""),
]
for old, new in pairs:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('done')

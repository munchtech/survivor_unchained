import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Content/Boons.cs', [
# Legion Bronze: heavy, and it shows.
("""            Text = "Old-empire bronze, green at the edges and still the hardest thing in the valley: +10% damage with everything.", Mods = r => [Inc(Stat.Damage, 0.1 * r, "boon:might")] },""",
 """            Text = "Old-empire bronze, green at the edges and still the hardest thing in the valley: +10% damage with everything, and your blows land 10% heavier.",
            Mods = r => [Inc(Stat.Damage, 0.1 * r, "boon:might"), Inc(Stat.Knockback, 0.1 * r, "boon:might")] },"""),
# Toll-Runner's Boots: what you run through comes with you.
("""            Text = "Worn thin on the toll road: +10% movement speed.", Mods = r => [Inc(Stat.MoveSpeed, 0.1 * r, "boon:fleetfoot")] },""",
 """            Text = "Worn thin on the toll road: +10% movement speed, and on the run ember comes to you from 10% farther.",
            Mods = r => [Inc(Stat.MoveSpeed, 0.1 * r, "boon:fleetfoot"), new StatMod(Stat.PickupRadius, ModKind.Inc, 0.1 * r, "boon:fleetfoot", ModWhen.Moving)] },"""),
# Watch Mail: the Watch counts.
("""            Text = "From the Watch's stores, never paid for: +3 armour. Each point helps a little less than the last.", Mods = r => [Flat(Stat.Armor, 3 * r, "boon:ironhide")] },""",
 """            Text = "From the Watch's stores, never paid for: +3 armour, and it counts: every tenth blow that reaches you glances off.", Mods = r => [Flat(Stat.Armor, 3 * r, "boon:ironhide")] },"""),
# Night-Eyes: the dark is where they see best.
("""            Text = "You see the weak places better in the dark: +7% critical strike chance.", Mods = r => [Flat(Stat.CritChance, 0.07 * r, "boon:precision")] },""",
 """            Text = "You see the weak places better in the dark: +7% critical strike chance, and twice that against anything beyond six paces.", Mods = r => [Flat(Stat.CritChance, 0.07 * r, "boon:precision")] },"""),
# Wolf-Tooth: the Pack takes the wounded.
("""            Text = "It bites deeper than it should: +25% critical strike damage.", Mods = r => [Flat(Stat.CritDamage, 0.25 * r, "boon:ferocity")] },""",
 """            Text = "It bites deeper than it should: +25% critical strike damage, and the wounded (below half) feel 12% more of it.", Mods = r => [Flat(Stat.CritDamage, 0.25 * r, "boon:ferocity")] },"""),
# Bitterroot: it draws what is in you.
("""            Text = "Chewed slowly, as the hunters do: +0.6 health regenerated per second.", Mods = r => [Flat(Stat.Regen, 0.6 * r, "boon:recovery")] },""",
 """            Text = "Chewed slowly, as the hunters do: +0.6 health regenerated per second, and burning or poison on you wears off twice as fast.", Mods = r => [Flat(Stat.Regen, 0.6 * r, "boon:recovery")] },"""),
# Fen Step: a blow missed is a step taken.
("""            Text = "Light on soft ground: +7% chance to avoid a blow entirely.", Mods = r => [Flat(Stat.Dodge, 0.07 * r, "boon:evasion")] },""",
 """            Text = "Light on soft ground: +7% chance to avoid a blow entirely, and a blow avoided leaves you 20% quicker for a moment.", Mods = r => [Flat(Stat.Dodge, 0.07 * r, "boon:evasion")],
            Triggers = [T(TriggerEvent.Dodge, [new Effect.Buff("fen_step", Stat.MoveSpeed, 0.2, ModKind.Inc, 1.5)], icd: 0.5)] },"""),
])

edit('logic/Sim/Battle.cs', [
# Bitterroot.
("""        if (p.BurnT > 0) { p.BurnT -= dt; HurtPlayerRaw(p.BurnDps * dt, School.Fire, "burning", null, true); }
        if (p.PoisonT > 0) { p.PoisonT -= dt; HurtPlayerRaw(p.PoisonDps * dt, School.Nature, "poison", null, true); }""",
 """        // Bitterroot draws it: what burns or poisons the survivor wears off twice as fast.
        double cure = Boons.ContainsKey("recovery") ? 2 : 1;
        if (p.BurnT > 0) { p.BurnT -= dt * cure; HurtPlayerRaw(p.BurnDps * dt, School.Fire, "burning", null, true); }
        if (p.PoisonT > 0) { p.PoisonT -= dt * cure; HurtPlayerRaw(p.PoisonDps * dt, School.Nature, "poison", null, true); }"""),
# Watch Mail: every tenth blow glances off (after dodge and ward, before armour).
("""        // Thorns answer before the armour question.""",
 """        // Watch Mail counts: every tenth blow that reaches the survivor glances off.
        if (Boons.ContainsKey("ironhide") && ++p.MailCount >= 10)
        {
            p.MailCount = 0;
            p.Iframes = Math.Max(p.Iframes, 0.25);
            Events.Emit(new Ev.PlayerHit { X = p.X, Z = p.Z, Amount = 0, School = school, Source = source, Blocked = true });
            Fire(TriggerEvent.Block, new ProcCtx { X = p.X, Z = p.Z });
            return 0;
        }
        // Thorns answer before the armour question."""),
("""    /// <summary>Risings From the Ashes still owed tonight (the ember's own, lost at dawn).</summary>
    public int Ashes;""",
 """    /// <summary>Risings From the Ashes still owed tonight (the ember's own, lost at dawn).</summary>
    public int Ashes;
    /// <summary>Blows that have reached the survivor since Watch Mail last turned one.</summary>
    public int MailCount;"""),
# Night-Eyes and Wolf-Tooth.
("""            double chance = st.Get(Stat.CritChance) + (Player.SureCritT > 0 ? 1 : 0) + (o.Weapon?.CritBonus ?? 0);
            crit = Rng.Next() < chance;
        }
        if (crit) dmg *= st.Get(Stat.CritDamage);""",
 """            double chance = st.Get(Stat.CritChance) + (Player.SureCritT > 0 ? 1 : 0) + (o.Weapon?.CritBonus ?? 0);
            // Night-Eyes: the far ones, in the dark, are seen best.
            if (Boons.TryGetValue("precision", out int eyes) && Dist(e.X, e.Z, Player.X, Player.Z) > 6) chance += 0.07 * eyes;
            crit = Rng.Next() < chance;
        }
        if (crit) dmg *= st.Get(Stat.CritDamage) * (e.Hp < e.MaxHp * 0.5 && Boons.TryGetValue("ferocity", out int tooth) ? 1 + 0.12 * tooth : 1);"""),
])
print('ok')

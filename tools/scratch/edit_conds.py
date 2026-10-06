import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:90], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

edit('logic/Sim/Battle.cs', [
("""        condScratch.Clear();
        condScratch.Add(p.Moving ? ModWhen.Moving : ModWhen.Still);
        if (p.Hp < MaxHp * 0.35) condScratch.Add(ModWhen.LowHealth);
        if (p.Hp >= MaxHp - 0.01) condScratch.Add(ModWhen.FullHealth);
        Stats.SetActive(condScratch);
    }""", """        condScratch.Clear();
        condScratch.Add(p.Moving ? ModWhen.Moving : ModWhen.Still);
        if (p.Hp < MaxHp * 0.35) condScratch.Add(ModWhen.LowHealth);
        if (p.Hp >= MaxHp - 0.01) condScratch.Add(ModWhen.FullHealth);
        // What gear asks of the moment: the dark, beasts close, fire underfoot, a dash just done.
        if (Night) condScratch.Add(ModWhen.Night);
        if (Time - dashEnded < 1.5) condScratch.Add(ModWhen.AfterDash);
        if ((senseT -= dt) <= 0)
        {
            senseT = 0.25;
            nearBeasts = HostilesInRadius(p.X, p.Z, 8).Any(e => e.Def.Family is Family.Wolf or Family.Boar or Family.Beast);
            inBurning = false;
            foreach (var z in Zones.Items)
                if (z.Alive && z.School == School.Fire && Dist(z.X, z.Z, p.X, p.Z) < z.Radius) { inBurning = true; break; }
        }
        if (nearBeasts) condScratch.Add(ModWhen.NearBeasts);
        if (inBurning) condScratch.Add(ModWhen.InBurning);
        Stats.SetActive(condScratch);
    }

    /// <summary>The dark (a night in the world, every arena): gear that
    /// answers to the night is awake.</summary>
    public bool Night;
    double senseT, dashEnded = -9;
    bool nearBeasts, inBurning;"""),
("""                AddBuff("momentum", Stat.MoveSpeed, Abilities.Dash.MomentumSpeed, ModKind.Inc, Abilities.Dash.Momentum, 1);""",
"""                AddBuff("momentum", Stat.MoveSpeed, Abilities.Dash.MomentumSpeed, ModKind.Inc, Abilities.Dash.Momentum, 1);
                dashEnded = Time;"""),
])

edit('logic/Play/Journey.cs', [
("""        b.EmberOn = combat && (arena || ember);""", """        b.EmberOn = combat && (arena || ember);
        b.Night = arena || ember || World.Time == TimeOfDay.Night;"""),
])
print("ok")

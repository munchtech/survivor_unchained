import os
os.chdir(r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09e0860794ed3e5c\godot')

def edit(p, pairs):
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert s.count(old) == 1, (p, old[:100], s.count(old))
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8').write(s)

A = 'logic/Play/Zones/ArenaRun.cs'
edit(A, [
("""using SurvivorUnchained.Maps;
using SurvivorUnchained.Rpg;""", """using SurvivorUnchained.Maps;
using SurvivorUnchained.Play.Bosses;
using SurvivorUnchained.Rpg;"""),
("""public sealed class ArenaRun : ZoneRuntime
{""", """public sealed class ArenaRun : ZoneRuntime, IBossArena
{"""),
("""    Enemy? boss, herald;
    readonly HashSet<int> chests = new();""",
 """    Enemy? boss, herald;
    readonly HashSet<int> chests = new();
    /// <summary>The boss's script (its phases, moves and weakness), the bearing its sign
    /// came from, and the share of its number the horde is kept at while it lives.</summary>
    ArenaBoss? script;
    double signAngle, bossShare = 0.4;
    bool runUp;
    public ArenaBoss? BossScript => script;"""),
# The horde during the fight: the boss's share of it.
("""        else if (bossUp && spawnT <= 0 && alive < Target() / 2)""",
 """        else if (bossUp && spawnT <= 0 && alive < Target() * bossShare)"""),
# The run-up: a sign at a bearing, two minutes out.
("""        if (!bossUp && !won && Seconds >= End) Boss();""",
 """        if (!runUp && !won && Seconds >= End - 120) RunUp();
        if (!bossUp && !won && Seconds >= End) Boss();"""),
("""    /// <summary>The half hour: what rules the people comes.</summary>
    void Boss()
    {
        bossUp = true;
        var p = B!.Player;
        var at = Around(R() * Math.PI * 2, 18) ?? (p.X + 8, p.Z);
        boss = Spawn(BossDef, at.X, at.Z, true, SpawnStyle.Walk);
        if (boss != null && Spec.BossName != null) boss.Named = new Named { Title = Spec.BossName };
        if (boss != null)
        {
            // A fight of half a minute to a minute for most builds (docs/SKILLS_DESIGN.md, "Bosses").
            boss.MaxHp = boss.Hp = boss.MaxHp * (10 + Spec.Tier * 4);
            boss.Damage *= 1.3;
        }
        for (int k = 0; k < 14; k++)
        {
            double a = k * Math.PI * 2 / 14;
            double x = at.X + Math.Cos(a) * 5, z = at.Z + Math.Sin(a) * 5;
            if (map.CanStand(x, z)) Spawn(Pick(), x, z);
        }
        B.Events.Emit(new Ev.Shake { Amount = 0.45 });
        G.Announce(new Announcement(BossName, BossTitle, "danger", 3, "The half hour"));
        Objectives();
    }""",
 """    /// <summary>Two minutes out: its sign, from the bearing it will come from (a sound,
    /// then a light on the arena's edge), so the survivor turns to face it.</summary>
    void RunUp()
    {
        runUp = true;
        var p = B!.Player;
        signAngle = R() * Math.PI * 2;
        string sign = BossDef switch
        {
            "wolf_alpha" => "A howl from the edge of the wood; the wolves lift their heads.",
            "barrow_knight" => "A drum, slow, under everything; the dead turn to face it.",
            "grimtunnel_roused" => "A blasting thump, and the ground shivers; picks rattle somewhere.",
            "enforcer" => "A whistle, three notes, and an answering whistle.",
            _ => "Something is coming.",
        };
        B.Events.Emit(new Ev.Bark { X = p.X, Z = p.Z + 3, Text = sign });
        G.Look.AddLight(p.X + Math.Cos(signAngle) * 26, 2.5, p.Z + Math.Sin(signAngle) * 26, "#ff6a3a", 3.2, 16, 0.25, 0.12, "#ff8a5a");
        G.Announce(new Announcement("The half hour nears", "It comes from where the sign was", "danger", 2.6));
    }

    /// <summary>The half hour: what rules the people comes, a boss and no herald: on the
    /// picture from the bearing of its sign, its own kind round it, the field
    /// cleared where it stands, its weakness named.</summary>
    void Boss()
    {
        bossUp = true;
        var p = B!.Player;
        if (!runUp) signAngle = R() * Math.PI * 2;
        var at = Around(signAngle, 13) ?? Around(R() * Math.PI * 2, 13) ?? (p.X + 8, p.Z);
        // Its ground cleared: the boss is the thing on screen.
        foreach (var o in B.Enemies.Living().ToList())
            if (o.Disposition == Disposition.Hostile && !o.Elite && (o.X - at.X) * (o.X - at.X) + (o.Z - at.Z) * (o.Z - at.Z) < 64) B.Enemies.Release(o);
        boss = Spawn(BossDef, at.X, at.Z, true, SpawnStyle.Walk);
        script = ArenaBosses.For(BossDef, this);
        if (boss != null)
        {
            boss.Boss = true;
            if (Spec.BossName != null) boss.Named = new Named { Title = Spec.BossName };
            boss.MaxHp = boss.Hp = boss.MaxHp * (script?.HealthMul(Spec.Tier) ?? 12 + 2 * Spec.Tier);
            boss.Damage *= script?.DamageMul ?? 1.3;
            if (script != null)
            {
                script.Begin(boss);
                Hooks.BossTick = (e, dt) => e == boss && script.Tick(e, dt);
                Hooks.OnBossHit = (e, school, dmg) => { if (e == boss) script.OnHit(e, school, dmg); };
                Hooks.OnBossStagger = e => { if (e == boss) script.OnStagger(e); };
            }
            B.Events.Emit(new Ev.Focus { X = at.X, Z = at.Z, Duration = 1.6 });
        }
        // Its own kind round it, not a random draw.
        string escort = people.Arena[0].Def;
        for (int k = 0; k < 10; k++)
        {
            double a = k * Math.PI * 2 / 10;
            double x = at.X + Math.Cos(a) * 5, z = at.Z + Math.Sin(a) * 5;
            if (map.CanStand(x, z)) Spawn(escort, x, z);
        }
        B.Events.Emit(new Ev.Shake { Amount = 0.45 });
        G.Announce(new Announcement(BossName, script != null ? $"{BossTitle} · Weakness: {script.WeaknessText}" : BossTitle, "danger", 3.4, "The half hour"));
        Objectives();
    }

    /* ------------------------------------------------- the boss's arena -- */

    int IBossArena.Tier => Spec.Tier;
    bool IBossArena.Sworn(string oath) => Spec.Oaths.Contains(oath);
    double IBossArena.R() => R();
    Enemy? IBossArena.Spawn(string def, double x, double z, bool elite, SpawnStyle? style) => Spawn(def, x, z, elite, style);
    bool IBossArena.CanStand(double x, double z) => map.CanStand(x, z) && !B!.Collision.Blocked(x, z, 0.6);
    void IBossArena.Say(string title, string? sub, string tone) => G.Announce(new Announcement(title, sub ?? "", tone, 2.4));
    void IBossArena.Bark(double x, double z, string text, string? speaker) => B?.Events.Emit(new Ev.Bark { X = x, Z = z, Text = text, Speaker = speaker });
    double IBossArena.HordeShare { set => bossShare = value; }
    void IBossArena.Won(double x, double z)
    {
        if (over || won) return;
        var b = boss;
        if (b != null) foreach (var l in OnLoot(b)) B!.SpawnPickup(l.Kind, x, z, l.Value, l.Ref);
        Victory(x, z);
    }"""),
# The run's best chest, from the boss: three upgrades at least, more at the high tiers, for a big Break and a clean fight.
("""        if (e == boss)
        {
            for (int k = 0; k < 2 + Spec.Tier / 2; k++)""",
 """        if (e == boss)
        {
            int n = 3 + (Spec.Tier >= 3 ? 2 : 0) + (script != null && script.BreakSum >= e.MaxHp * 0.1 ? 1 : 0) + (B!.BossBlowsTaken == 0 ? 1 : 0);
            o.Add(new Loot(PickupKind.Chest, "boss", n, true));
            for (int k = 0; k < 2 + Spec.Tier / 2; k++)"""),
("""        if (p.Kind != PickupKind.Chest || B == null) return true;
        int n = 1 + (R() < 0.3 ? 1 : 0) + (R() < 0.1 ? 1 : 0);""",
 """        if (p.Kind != PickupKind.Chest || B == null) return true;
        int n = p.Ref == "boss" ? (int)p.Value : 1 + (R() < 0.3 ? 1 : 0) + (R() < 0.1 ? 1 : 0);"""),
("""        if (e == boss && !over) Victory(e.X, e.Z);""",
 """        if (e == boss && !over) { script?.Fell(e); Victory(e.X, e.Z); }"""),
# The bar: the boss's with its gates, Break and stagger; a herald's is not a boss's (its music).
("""        if (boss is { Alive: true } b && b.State != EnemyState.Dying) G.SetBoss(new BossBar(BossName, BossTitle, b.Hp, b.MaxHp));
        else if (herald is { Alive: true } h && h.State != EnemyState.Dying) G.SetBoss(new BossBar(h.Named?.Title ?? $"Herald of {people.Name}", people.Name, h.Hp, h.MaxHp));""",
 """        if (boss is { Alive: true } b && b.State != EnemyState.Dying)
            G.SetBoss(script != null ? script.Bar(BossName, script is Grimtunnel g ? $"{BossTitle} · lamps: {g.Lamps}" : BossTitle) : new BossBar(BossName, BossTitle, b.Hp, b.MaxHp));
        else if (herald is { Alive: true } h && h.State != EnemyState.Dying) G.SetBoss(new BossBar(h.Named?.Title ?? $"Herald of {people.Name}", people.Name, h.Hp, h.MaxHp, IsBoss: false));"""),
])

edit('logic/Sim/Battle.cs', [
("""                    if (b.Damage > 0) HurtPlayer(b.Damage, b.School, b.Source, b.From, telegraphed: true);""",
 """                    if (b.Damage > 0 && HurtPlayer(b.Damage, b.School, b.Source, b.From, telegraphed: true) > 0 && b.From?.Boss == true) BossBlowsTaken++;"""),
("""    readonly List<EnemyBlow> blows = new();""",
 """    readonly List<EnemyBlow> blows = new();
    /// <summary>A boss's telegraphed blows that landed (a fight won with none is "unscathed").</summary>
    public int BossBlowsTaken;"""),
])

# The view: the boss's music for a boss only; the camera turned on Ev.Focus.
edit('src/Game/Game.cs', [
("""    public void SetBoss(BossBar? bar) { hud.Boss(bar); bossUp = bar != null; }""",
 """    public void SetBoss(BossBar? bar) { hud.Boss(bar); bossUp = bar is { IsBoss: true }; }"""),
])
print('ok')

using System;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play.Bosses;

/* The four peoples' rulers at the half hour (docs/bosses/SURVIVORS_BOSSES.md
 * sections 1-4), on the contract of ArenaBoss. Each asks one question, has
 * three phases, a weakness that breaks its channel, and a hard enrage of its
 * own. Damage is in the contract's bands, as multiples of the boss's blow:
 * contact about a half, telegraphed blows 1.5-2, arena-wide mechanics with
 * long telegraphs more. They wear their people's champion's body until
 * bodies of their own are made. */

public static class ArenaBosses
{
    /// <summary>The script for what rules a people (by the boss's kind).</summary>
    public static ArenaBoss? For(string def, IBossArena arena) => def switch
    {
        "boss_pack" => new PackMother(arena),
        "boss_dead" => new BarrowLord(arena),
        "grimtunnel_roused" => new Grimtunnel(arena),
        "boss_lamplings" => new Grimtunnel(arena, ganger: true),
        "boss_kerchiefs" => new RedHand(arena),
        _ => null,
    };
}

/// <summary>The Pack-Mother: she herds you; refuse to be herded. Fire breaks her
/// moon-howl. The same fight is Greymuzzle's in his own Hollow (the story's): he is
/// wordless, so the Pack's lines are what is heard, never what is said.</summary>
public sealed class PackMother : ArenaBoss
{
    public PackMother(IBossArena a) : base(a) { }
    protected override Phase[] Phases { get; } =
    [
        new("The Drive", 0.65, 15, 60),
        new("The Moon", 0.30, 20, 60),
        new("The Den", 0, 15, 0),
    ];
    public override School Weakness => School.Fire;
    public override string WeaknessText => $"Fire breaks {Her} moon-howl";
    /// <summary>Greymuzzle is a he; the Pack-Mother a she.</summary>
    bool He => A.BossName == "Greymuzzle";
    string Her => He ? "his" : "her";
    protected override string HardName => "The Long Hunt";
    double driveT = 6, biteT = 3, howlT, shakeT = 2, lungeT = 4;
    double howlHp;
    bool lastPack;

    protected override void Enter(int phase)
    {
        if (phase == 1) howlT = 1.5;
        if (phase == 2) { shakeT = 2; lungeT = 3; }
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        var p = B.Player;
        // The Pack's turn: each wolf at her side takes some of what comes at her.
        int pack = Near("wolf", 4) + Near("wolf_blighted", 4);
        e.TakenMul = 1 - Math.Min(0.25, 0.05 * pack);
        driveT -= dt; biteT -= dt; howlT -= dt; shakeT -= dt; lungeT -= dt;
        switch (PhaseIx)
        {
            case 0:
                if (driveT <= 0) { driveT = 14 * Cadence; Drive(); return true; }
                if (d < 6 && biteT <= 0) { biteT = 5 * Cadence; Hamstring(); return true; }
                return false;
            case 1:
                if (howlT <= 0) { howlT = 25 * Cadence; Howl(e); return true; }
                if (d < 6 && biteT <= 0) { biteT = 5 * Cadence; Hamstring(); return true; }
                return false;
            default:
                if (!lastPack && e.Hp < e.MaxHp * 0.15)
                {
                    lastPack = true;
                    A.Say("The last of the Pack", null, "danger");
                    Ring("wolf", 12, p.X, p.Z, 14);
                }
                if (d < 5.5 && shakeT <= 0) { shakeT = 6 * Cadence; Hold(1.0); Cone(5, 120, 1.0, 1.8, "Shake"); return true; }
                if (lungeT <= 0) { lungeT = (Hard ? 3 : 7) * Cadence; Chain(3); return true; }
                return false;
        }
    }

    /// <summary>The Drive: the Pack closes in a crescent on one side; she waits across
    /// the gap and runs its lane as it closes. Go through the wolves, not the gap.</summary>
    void Drive()
    {
        var p = B.Player;
        // The crescent on the far side of the survivor from her, its open side toward her.
        double away = Math.Atan2(p.Z - E.Z, p.X - E.X);
        A.Bark(E.X, E.Z, "A rising howl: the Pack wheels.", null);
        int n = 7 + A.Tier;
        for (int k = 0; k < n; k++)
        {
            double a = away + (k / (double)Math.Max(1, n - 1) - 0.5) * Math.PI * 1.1;
            double x = p.X + Math.Cos(a) * 10, z = p.Z + Math.Sin(a) * 10;
            if (A.CanStand(x, z)) A.Spawn("wolf", x, z);
        }
        Hold(1.0, () =>
        {
            var (dx, dz, d) = ToPlayer();
            double len = d + 6;
            double x1 = E.X + dx * len, z1 = E.Z + dz * len;
            Lane(E.X, E.Z, x1, z1, 2.4, 1.0, 1.8, "The Drive");
            Hold(1.0, () => DashTo(x1, z1, 0.4));
        });
    }

    void Hamstring()
    {
        Hold(0.8);
        var b = Cone(4.2, 70, 0.8, 1.5, "Hamstring");
        b.Slow = 0.55; b.SlowFor = 2;
    }

    /// <summary>The moon-howl: she sits at the edge and howls; her dead run lanes across
    /// the light. Damage of 6% of her health, a stagger, or fire cuts it short.</summary>
    void Howl(Enemy e)
    {
        Channel = "The moon-howl: break it!";
        ChannelProgress = 0;
        howlHp = e.Hp;
        A.Bark(e.X, e.Z, $"{(He ? "He" : "She")} sits back and howls at the moon.", null);
        double nextLane = 0.4;
        Hold(8, () => { Channel = null; }, t =>
        {
            ChannelProgress = t / 8;
            if (howlHp - E.Hp >= E.MaxHp * 0.06) { BreakChannel(E, "Hurt enough to stop"); return false; }
            if (t >= nextLane)
            {
                nextLane += 1.6;
                var p = B.Player;
                double a = A.R() * Math.PI * 2;
                double x0 = p.X + Math.Cos(a) * 12, z0 = p.Z + Math.Sin(a) * 12;
                Lane(x0, z0, p.X - Math.Cos(a) * 12, p.Z - Math.Sin(a) * 12, 1.8, 1.2, 1.5, He ? "His dead run" : "Her dead run", School.Frost);
            }
            return true;
        });
    }

    /// <summary>Lunges in a chain, the later ones aimed where the survivor is going.</summary>
    void Chain(int n)
    {
        if (n <= 0) return;
        var p = B.Player;
        double lead = n == 3 ? 0 : 0.6;
        double tx = p.X + p.Vx * lead, tz = p.Z + p.Vz * lead;
        double dx = tx - E.X, dz = tz - E.Z, d = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
        double len = Math.Min(14, d + 3);
        double x1 = E.X + dx / d * len, z1 = E.Z + dz / d * len;
        Lane(E.X, E.Z, x1, z1, 2.2, 0.8, 1.6, "Lunge");
        Hold(0.8, () => DashTo(x1, z1, 0.35, () => Chain(n - 1)));
    }

    protected override void OnSoft() { driveT = Math.Min(driveT, 4); }
    protected override void OnHard() { B.Rules.Light *= 0.5; }
}

/// <summary>The Barrow Lord: walls of men; read the formation and break it. He will
/// not lie down: at the end, stand over him to lay him down. Holy counts twice.</summary>
public sealed class BarrowLord : ArenaBoss
{
    public BarrowLord(IBossArena a) : base(a) { }
    protected override Phase[] Phases { get; } =
    [
        new("The Drill", 0.70, 15, 60),
        new("The Testudo", 0.40, 20, 60),
        new("Who Would Not Lie Down", 0, 15, 0),
    ];
    public override School Weakness => School.Holy;
    public override string WeaknessText => "Holy lays him down twice as fast";
    protected override string HardName => "The Last Watch";
    protected override bool DiesAtZero => false;
    double lineT = 4, pilumT = 6, testudoT = 1, gladiusT = 2, holdT = 6;
    double layT, layHeld;
    bool laying;
    int risings;
    /// <summary>He is down at one and must be stood over (the bots read it as a player does).</summary>
    public bool Laying => laying;

    // Undead resist frost and shadow; on him they do not, so every school can lay him down in time.
    public override double HealthMul(int tier) => 9 + 1.5 * tier;

    protected override void Enter(int phase)
    {
        if (phase == 1) testudoT = 1;
        if (phase == 2) { gladiusT = 1.5; holdT = 6; }
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (laying) return Lay(e, dt);
        if (e.Hp <= 1.5 && PhaseIx == Phases.Length - 1) { StartLay(e); return true; }
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        lineT -= dt; pilumT -= dt; testudoT -= dt; gladiusT -= dt; holdT -= dt;
        // While shieldmen stand round him, he takes half.
        e.TakenMul = Near("risen_warrior", 5) >= 4 ? 0.5 : 1;
        switch (PhaseIx)
        {
            case 0:
                if (lineT <= 0) { lineT = (Hard ? 6 : Soft ? 10 : 16) * Cadence; CloseUp(); return true; }
                if (pilumT <= 0 && d > 5) { pilumT = 7 * Cadence; Pilum(); return true; }
                return false;
            case 1:
                if (testudoT <= 0) { testudoT = 22 * Cadence; Testudo(e); return true; }
                if (pilumT <= 0 && d > 5) { pilumT = 7 * Cadence; Pilum(); return true; }
                return false;
            default:
                if (Hard && lineT <= 0) { lineT = 12; CloseUp(); }
                if (d < 4.8 && gladiusT <= 0)
                {
                    gladiusT = 4 * Cadence;
                    Hold(0.9, () =>
                    {
                        var (x, z, dd) = ToPlayer();
                        Lane(E.X, E.Z, E.X + x * 5, E.Z + z * 5, 2, 0.7, 1.5, "Gladius");
                        Hold(0.7);
                    });
                    Cone(4.5, 90, 0.9, 1.5, "Gladius");
                    return true;
                }
                if (holdT <= 0)
                {
                    holdT = 12 * Cadence;
                    var p = B.Player;
                    // His orders are in the old empire's tongue, one word each and
                    // plural, to his dead (docs/VOICES.md); what follows shows what they mean.
                    A.Bark(E.X, E.Z, "\"Tenete!\"", "The Barrow Lord");
                    var b = Band(p.X, p.Z, 4.5, 6.5, 1.5, 0.8, "Hold!", School.Shadow);
                    b.Slow = 0.05; b.SlowFor = 1.2;
                    return false;
                }
                return false;
        }
    }

    /// <summary>"Close up!": shieldmen rise in a line between him and the survivor and walk.</summary>
    void CloseUp()
    {
        var p = B.Player;
        A.Bark(E.X, E.Z, "\"Iungite!\"", "The Barrow Lord");
        double a = Math.Atan2(E.Z - p.Z, E.X - p.X);
        double cx = p.X + Math.Cos(a) * 9, cz = p.Z + Math.Sin(a) * 9;
        double sx = -Math.Sin(a), sz = Math.Cos(a);
        int n = 6 + A.Tier;
        for (int k = 0; k < n; k++)
        {
            double off = (k - (n - 1) / 2.0) * 1.9;
            double x = cx + sx * off, z = cz + sz * off;
            if (A.CanStand(x, z)) A.Spawn("risen_warrior", x, z, false, SpawnStyle.Rise);
        }
        Hold(0.6);
    }

    void Pilum()
    {
        var (dx, dz, d) = ToPlayer();
        double len = Math.Min(22, d + 6);
        Hold(1.0);
        Lane(E.X, E.Z, E.X + dx * len, E.Z + dz * len, 1.3, 1.0, 1.6, "Pilum");
    }

    /// <summary>The testudo: a ring of shields round him; then the century charges out in columns.</summary>
    void Testudo(Enemy e)
    {
        A.Bark(e.X, e.Z, "\"Testudo!\"", "The Barrow Lord");
        Ring("risen_warrior", 8, e.X, e.Z, 3.6, SpawnStyle.Rise);
        Hold(6, () =>
        {
            var (dx, dz, _) = ToPlayer();
            double a0 = Math.Atan2(dz, dx);
            int cols = E.Hp > E.MaxHp * 0.55 ? 3 : 2;
            for (int k = 0; k < cols; k++)
            {
                double a = a0 + (k - (cols - 1) / 2.0) * 0.55;
                Lane(E.X, E.Z, E.X + Math.Cos(a) * 18, E.Z + Math.Sin(a) * 18, 2.2, 1.3, 1.5, "Charge of the century");
            }
            Hold(1.3);
        });
    }

    /// <summary>He falls and does not die: stand over him three seconds to lay him down,
    /// or he rises with a quarter of his life and fights on, quicker.</summary>
    void StartLay(Enemy e)
    {
        laying = true;
        layT = 0;
        layHeld = 0;
        e.TakenMul = 0;
        e.Hp = 1;
        Channel = "He will not lie down: stand over him";
        ChannelProgress = 0;
        A.Say("He will not lie down", "Stand over him", "danger");
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Safe, X = e.X, Z = e.Z, Radius = 3, Delay = 8, From = e, Label = "Lay him down" });
        // His dead try to drag you out of it.
        Ring("risen", 6 + A.Tier, e.X, e.Z, 9, SpawnStyle.Rise);
    }

    bool Lay(Enemy e, double dt)
    {
        e.Vx = e.Vz = 0;
        e.State = EnemyState.Casting;
        e.TakenMul = 0;
        layT += dt;
        var p = B.Player;
        if ((p.X - e.X) * (p.X - e.X) + (p.Z - e.Z) * (p.Z - e.Z) < 9) layHeld += dt * (holyT > 0 ? 2 : 1);
        if (holyT > 0) holyT -= dt;
        ChannelProgress = layHeld / 3;
        if (layHeld >= 3)
        {
            laying = false;
            Channel = null;
            e.TakenMul = 1;
            e.HpFloor = 0;
            A.Say("Laid down", null, "reward");
            B.KillEnemy(e, true, null);
            return true;
        }
        if (layT >= 8)
        {
            laying = false;
            Channel = null;
            risings++;
            e.TakenMul = 1;
            e.Hp = e.MaxHp * 0.25;
            e.State = EnemyState.Active;
            A.Say("He rises", "A quarter of his life, and quicker", "danger");
            e.Speed *= 1.2;
            gladiusT = 1;
        }
        return true;
    }

    double holyT;
    public override void OnHit(Enemy e, School school, double dmg)
    {
        if (laying && school == School.Holy) holyT = 0.5;
        base.OnHit(e, school, dmg);
    }
}

/// <summary>Grimtunnel, roused: the ground is the enemy. He cannot die before the
/// story's end, so the fight is won when he goes back down the hole. Frost stops
/// him under the ground.
///
/// The Ganger fights the same fight: a Dig foreman, the table's Lamplings' boss,
/// since the story keeps Grimtunnel and his name for the Dig Boils Over and Act 3
/// (docs/STORY_BIBLE.md, "The nights"). It wears one lamp, not his three, that
/// flares for each of the three verbs in turn and puts them all out when it breaks;
/// and it dies like anything else.</summary>
public sealed class Grimtunnel : ArenaBoss
{
    readonly bool ganger;
    public Grimtunnel(IBossArena a, bool ganger = false) : base(a)
    {
        this.ganger = ganger;
        Lit = ganger ? [true] : [true, true, true];
        lampHp = new double[Lit.Length];
    }
    public bool Ganger => ganger;
    protected override Phase[] Phases { get; } =
    [
        new("The Dig", 0.60, 15, 60),
        new("The Collapse", 0.25, 20, 60),
        new("The Boil", 0, 15, 0),
    ];
    public override School Weakness => School.Frost;
    public override string WeaknessText => ganger ? "Frost catches it under the ground" : "Frost stops him under the ground";
    protected override string HardName => "The Fall";
    protected override bool DiesAtZero => ganger;
    double underT = 5, lampT = 3, mothT = 12, boilT = 6, pickT = 2;
    int lampIx, verb;
    double dazeT;
    /// <summary>His three lamps (red, blue, green): each lit, a verb; hit while it flares to
    /// break it. The Ganger's one lamp carries all three verbs.</summary>
    public readonly bool[] Lit;
    readonly double[] lampHp;
    int flaring = -1;
    double flareT;
    /// <summary>The lamp flaring now (-1: none): hit him while it does to break it.</summary>
    public int Flaring => flaring;
    readonly System.Collections.Generic.List<(double X, double Z, int Id, int Mark)> pits = new();
    bool goingDown;
    double downT;

    static readonly string[] LampNames = ["red lamp", "blue lamp", "green lamp"];

    protected override void Enter(int phase)
    {
        // His three lamps a twelfth of him each; the Ganger's one a sixth.
        if (phase == 0) for (int i = 0; i < Lit.Length; i++) lampHp[i] = E.MaxHp * (ganger ? 0.16 : 0.08);
        if (phase == 2) { E.Speed *= 1.3; boilT = 4; }
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (goingDown) return GoDown(e, dt);
        if (!ganger && e.Hp <= 1.5 && PhaseIx == Phases.Length - 1) { StartDown(e); return true; }
        if (dazeT > 0) { dazeT -= dt; e.TakenMul = 1.5; e.Vx = e.Vz = 0; e.State = EnemyState.Stunned; e.StateT = Math.Max(e.StateT, dt * 2); return true; }
        // Under the ground he is still in reach, at half.
        e.TakenMul = under ? 0.5 : 1;
        if (flareT > 0) { flareT -= dt; if (flareT <= 0) flaring = -1; }
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        underT -= dt; lampT -= dt; mothT -= dt; boilT -= dt; pickT -= dt;
        if (mothT <= 0) { mothT = 20 * Cadence; Moths(); }
        if (PhaseIx < 2 && underT <= 0) { underT = (Hard ? 6 : 12) * Cadence; Under(e); return true; }
        if (lampT <= 0 && Lit.Any(l => l))
        {
            lampT = 7 * Cadence;
            if (ganger) { lampIx = 0; verb = (verb + 1) % 3; }
            else { for (int k = 0; k < 3; k++) { lampIx = (lampIx + 1) % 3; if (Lit[lampIx]) break; } verb = lampIx; }
            flaring = lampIx;
            Lamp(verb);
            return true;
        }
        if (PhaseIx == 2)
        {
            if (boilT <= 0) { boilT = 15 * Cadence; Boil(e); }
            if (d < 4 && pickT <= 0) { pickT = 3 * Cadence; Hold(0.9); Cone(3.6, 90, 0.9, 1.5, "Pick"); return true; }
        }
        return false;
    }

    /// <summary>His lamp flares: a verb, and while it flares, hits on him break it.</summary>
    void Lamp(int i)
    {
        flareT = 2.5;
        var p = B.Player;
        switch (i)
        {
            case 0:
                // Blasting ember: three charges lobbed round the survivor, leaving fire.
                Hold(0.6);
                for (int k = 0; k < 3; k++)
                {
                    double a = A.R() * Math.PI * 2, r = k == 0 ? 0 : 2.5 + A.R() * 2;
                    var b = Circle(p.X + Math.Cos(a) * r, p.Z + Math.Sin(a) * r, 2.2, 1.4, 1.6, k == 0 ? "Blasting ember" : "", School.Fire);
                    double bx = b.X, bz = b.Z;
                    b.After = bb => bb.SpawnZone(Side.Enemy, bx, bz, 2.0, 3, E.Damage * 0.25, School.Fire);
                }
                break;
            case 1:
                // The deep lamp: his diggers come up under the survivor.
                Hold(0.6);
                Circle(p.X, p.Z, 1.8, 1.0, 0.8, "The deep lamp");
                for (int k = 0; k < 2 + A.Tier; k++)
                {
                    double a = A.R() * Math.PI * 2;
                    double x = p.X + Math.Cos(a) * 1.5, z = p.Z + Math.Sin(a) * 1.5;
                    if (A.CanStand(x, z)) A.Spawn("lampling", x, z, false, SpawnStyle.Burrow);
                }
                break;
            default:
            {
                // Slurry: a sprayed cone that leaves slowing ground.
                Hold(1.2);
                var (dx, dz, _) = ToPlayer();
                var b = Cone(7, 60, 1.2, 1.2, "Slurry", School.Nature);
                double ex = E.X, ez = E.Z;
                b.After = bb =>
                {
                    for (int k = 1; k <= 3; k++)
                    {
                        var z = bb.SpawnZone(Side.Enemy, ex + dx * k * 2, ez + dz * k * 2, 1.7, 4, E.Damage * 0.1, School.Nature);
                        if (z != null) z.Slow = 0.45;
                    }
                };
                break;
            }
        }
    }

    /// <summary>Under: he dives, the mound runs at the survivor, and he bursts up where it stops.</summary>
    void Under(Enemy e)
    {
        var p = B.Player;
        A.Bark(e.X, e.Z, "Rocks in a barrel: something under the ground.", null);
        double tx = p.X, tz = p.Z;
        under = true;
        DashTo(tx, tz, 2.4, () =>
        {
            Circle(E.X, E.Z, 3.5, 1.2, 2.0, "He bursts up", School.Physical);
            double bx = E.X, bz = E.Z;
            Hold(1.2, () =>
            {
                under = false;
                dazeT = frostCaught ? 8 : 4;
                frostCaught = false;
                if (PhaseIx == 1) Pit(bx, bz);
            });
        });
    }
    bool frostCaught, under;

    /// <summary>A sinkhole where he burst: ground nothing can stand on, up to six (and one more a tier).</summary>
    void Pit(double x, double z)
    {
        int cap = 5 + A.Tier;
        if (pits.Count >= cap && !Soft) { var old = pits[0]; pits.RemoveAt(0); B.Collision.Remove(old.Id); B.EndMark(old.Mark); }
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, X = x, Z = z, Radius = 2.6, Delay = 1.5, From = E, Label = "The ground goes" });
        int mark = B.Mark(TelegraphKind.Wall, x, z, 2.5, 900);
        int id = B.Collision.AddCircle(x, z, 2.4, new ColliderOpts(Tag: "pit")).Id;
        pits.Add((x, z, id, mark));
    }

    void Moths()
    {
        var p = B.Player;
        A.Bark(p.X, p.Z + 2, "Lamplings flock to the light.", null);
        for (int k = 0; k < 6 + 2 * A.Tier; k++)
        {
            double a = k * Math.PI * 2 / (6 + 2 * A.Tier), r = 5 + A.R() * 2;
            double x = p.X + Math.Cos(a) * r, z = p.Z + Math.Sin(a) * r;
            if (A.CanStand(x, z)) A.Spawn("lampling", x, z, false, SpawnStyle.Burrow);
        }
    }

    /// <summary>The Dig boils: slurry wells up in a ring that runs out from him.</summary>
    void Boil(Enemy e)
    {
        A.Bark(e.X, e.Z, "The Dig boils!", null);
        double cx = e.X, cz = e.Z;
        for (int k = 0; k < 7; k++)
        {
            double inner = 1 + k * 2.4, outer = inner + 1.8;
            var b = Band(cx, cz, inner, outer, 0.9 + k * 0.5, 1.0, k == 0 ? "The Dig boils" : "", School.Nature);
            b.Slow = 0.5; b.SlowFor = 1.5;
        }
    }

    public override void OnHit(Enemy e, School school, double dmg)
    {
        // A lamp flaring takes the blows on it, and breaks.
        if (flaring >= 0 && Lit[flaring] && !goingDown)
        {
            lampHp[flaring] -= dmg;
            if (lampHp[flaring] <= 0)
            {
                Lit[flaring] = false;
                B.Events.Emit(new Ev.Announce { Title = ganger ? "Its lamp breaks" : $"His {LampNames[flaring]} breaks", Subtitle = ganger ? "Its blasting, its diggers and its slurry are done" : null, Tone = Tone.Boon });
                B.Events.Emit(new Ev.Explosion { X = e.X, Z = e.Z, Radius = 2.5, School = verb == 0 ? School.Fire : verb == 1 ? School.Frost : School.Nature, Power = 1 });
                flaring = -1;
            }
        }
        // Frost on him as he comes up: he stays dazed twice as long.
        if (school == Weakness && under) frostCaught = true;
        base.OnHit(e, school, dmg);
    }

    /// <summary>The bar's lamps, for the HUD's title.</summary>
    public string Lamps => ganger ? (Lit[0] ? "lit" : "out") : string.Join(" ", Lit.Select((l, i) => l ? LampNames[i].Split(' ')[0] : "-"));

    void StartDown(Enemy e)
    {
        goingDown = true;
        downT = 0;
        e.TakenMul = 0;
        e.Hp = 1;
        // He goes down delighted, never beaten: he is wanted below (docs/STORY_BIBLE.md,
        // "The nights"). Since C03 he cannot finish "surface-meat" at her: she smells of downstairs.
        A.Bark(e.X, e.Z, "\"Ha! Keep upstairs, surface-m— you! I'm wanted DOWNSTAIRS!\"", "Grimtunnel");
        B.Events.Emit(new Ev.Focus { X = e.X, Z = e.Z, Duration = 1.6 });
    }

    /// <summary>Back down the hole: the pits close behind him, his diggers dive, and the fight is won.</summary>
    bool GoDown(Enemy e, double dt)
    {
        downT += dt;
        e.Vx = e.Vz = 0;
        e.State = EnemyState.Casting;
        if (downT < 1.4) return true;
        ClosePits();
        double x = e.X, z = e.Z;
        foreach (var o in B.Enemies.Items)
            if (o.Alive && o != e && o.Def.Id.StartsWith("lampling") && o.State != EnemyState.Dying) B.Enemies.Release(o);
        B.Events.Emit(new Ev.Explosion { X = x, Z = z, Radius = 4, School = School.Physical, Power = 1.5 });
        B.Events.Emit(new Ev.Shake { Amount = 0.5 });
        A.Bark(x, z + 3, "\"Snib will tell Boss you said hello. Snib will NOT tell Boss.\"", "Snib");
        B.Enemies.Release(e);
        A.Won(x, z);
        return true;
    }

    protected override void OnSoft() { }
    public override void Fell(Enemy e) => ClosePits();

    /// <summary>The pits fill in behind him (arena changes end with the fight).</summary>
    void ClosePits()
    {
        foreach (var (_, _, id, mark) in pits) { B.Collision.Remove(id); B.EndMark(mark); }
        pits.Clear();
    }
}

/// <summary>The Red Hand: the boss who steals. What is your build without its best
/// piece? Storm makes his thief drop what he took.</summary>
public sealed class RedHand : ArenaBoss
{
    public RedHand(IBossArena a) : base(a) { }
    protected override Phase[] Phases { get; } =
    [
        new("The Toll", 0.65, 15, 60),
        new("The Cages", 0.30, 20, 60),
        new("The Hand", 0, 15, 0),
    ];
    public override School Weakness => School.Storm;
    public override string WeaknessText => "Storm makes his thief drop what he took";
    protected override string HardName => "Everything Owed";
    double tollT = 10, volleyT = 5, cageT = 3, maulT = 2, sweepT = 4;
    bool levy, everything;
    Enemy? thief;
    WeaponInst? taken;
    /// <summary>The footpad running with the survivor's weapon, while he runs.</summary>
    public Enemy? Thief => thief;
    readonly System.Collections.Generic.List<int> posts = new();
    double postsT;

    protected override void Enter(int phase)
    {
        if (phase == 1) cageT = 2;
        if (phase == 2) { maulT = 1.5; sweepT = 3; }
    }

    protected override bool Act(Enemy e, double dt)
    {
        if (postsT > 0) { postsT -= dt; if (postsT <= 0) { foreach (var id in posts) B.Collision.Remove(id); posts.Clear(); } }
        if (thief != null && (!thief.Alive || thief.State == EnemyState.Dying)) Recover(thief.Credit);
        // Storm on the thief: he drops what he took.
        else if (thief != null && thief.LastSchool == Weakness && thief.Hp < thief.MaxHp) { B.Enemies.Release(thief); Recover(true); }
        if (Running(e, dt)) return true;
        var (dx, dz, d) = ToPlayer();
        tollT -= dt; volleyT -= dt; cageT -= dt; maulT -= dt; sweepT -= dt;
        if ((PhaseIx == 0 || Hard) && tollT <= 0 && thief == null) { tollT = (Hard ? 10 : Soft ? 15 : 30); Toll(); return true; }
        switch (PhaseIx)
        {
            case 0:
                if (volleyT <= 0 && d > 4) { volleyT = 9 * Cadence; Volley(); return true; }
                return false;
            case 1:
                if (!levy && e.Hp < e.MaxHp * 0.5) { levy = true; Levy(); }
                if (cageT <= 0) { cageT = 20 * Cadence; Cage(); return true; }
                if (volleyT <= 0 && d > 4) { volleyT = 9 * Cadence; Volley(); return true; }
                return false;
            default:
                if (!everything && e.Hp < e.MaxHp * 0.15) { everything = true; TakeEverything(); return true; }
                if (d < 7 && maulT <= 0)
                {
                    maulT = 5 * Cadence;
                    double hx = E.X + dx * 4, hz = E.Z + dz * 4;
                    Hold(1.2);
                    Circle(hx, hz, 2.4, 1.2, 2.0, "The maul");
                    return true;
                }
                if (d < 4.5 && sweepT <= 0) { sweepT = 4 * Cadence; Hold(1.0); Cone(4.2, 160, 1.0, 1.4, "Sweep"); return true; }
                return false;
        }
    }

    /// <summary>The Toll: a red ring closes on the survivor; still in it, a footpad
    /// touches them and runs with their best weapon. It comes back in 8 s, or at
    /// once (and firing) when he is caught.</summary>
    void Toll()
    {
        var p = B.Player;
        A.Bark(E.X, E.Z, "\"Toll's due.\"", "The Red Hand");
        var ring = B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = p.X, Z = p.Z, Radius = 2.6, Delay = 1.0, From = E, Label = "The Toll" });
        double rx = p.X, rz = p.Z;
        ring.After = bb =>
        {
            var pp = bb.Player;
            if ((pp.X - rx) * (pp.X - rx) + (pp.Z - rz) * (pp.Z - rz) > 2.6 * 2.6 || pp.Iframes > 0) { bb.Events.Emit(new Ev.Bark { X = pp.X, Z = pp.Z + 2, Text = "The toll missed." }); return; }
            taken = bb.Weapons.Where(w => w.DisabledT <= 0).OrderByDescending(w => w.Rank + (w.Evolution != null ? 8 : 0)).FirstOrDefault();
            if (taken == null) return;
            taken.DisabledT = 8;
            double a = A.R() * Math.PI * 2;
            thief = A.Spawn("footpad", pp.X + Math.Cos(a) * 1.5, pp.Z + Math.Sin(a) * 1.5, true);
            if (thief != null) { thief.Tag = "toll_thief"; thief.MaxHp = thief.Hp = thief.MaxHp * 0.7; thief.Speed *= 1.3; thief.LifeT = 12; }
            bb.Events.Emit(new Ev.Announce { Title = $"{taken.Def.Name} is taken", Subtitle = "Catch the thief", Tone = Tone.Danger });
        };
        Hold(1.0);
    }

    void Recover(bool caught)
    {
        if (taken != null)
        {
            taken.DisabledT = 0;
            if (caught) taken.Timer = 0;
            B.Events.Emit(new Ev.Announce { Title = $"{taken.Def.Name} is yours again", Tone = Tone.Boon });
        }
        taken = null;
        thief = null;
    }

    void Volley()
    {
        var (dx, dz, d) = ToPlayer();
        double a0 = Math.Atan2(dz, dx);
        Hold(1.1);
        for (int k = 0; k < 5; k++)
        {
            double a = a0 + (k - 2) * 0.18;
            Lane(E.X, E.Z, E.X + Math.Cos(a) * 18, E.Z + Math.Sin(a) * 18, 1.0, 1.1, 1.2, k == 2 ? "Volley" : "");
        }
    }

    /// <summary>A cage of posts dropped round the survivor, with footpads inside: dash out first.</summary>
    void Cage()
    {
        var p = B.Player;
        double cx = p.X, cz = p.Z;
        B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, Kind = TelegraphKind.Wall, X = cx, Z = cz, Radius = 5, Delay = 1.5, From = E, Label = "A cage" });
        Hold(1.5, () =>
        {
            for (int k = 0; k < 10; k++)
            {
                double a = k * Math.PI * 2 / 10;
                posts.Add(B.Collision.AddCircle(cx + Math.Cos(a) * 5, cz + Math.Sin(a) * 5, 0.7, new ColliderOpts(Tag: "cage")).Id);
            }
            B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Ring, Kind = TelegraphKind.Wall, X = cx, Z = cz, Inner = 4.6, Radius = 5.4, Delay = 8, From = E });
            postsT = 8;
            for (int k = 0; k < 2 + A.Tier; k++)
            {
                double a = A.R() * Math.PI * 2;
                if (A.CanStand(cx + Math.Cos(a) * 2.5, cz + Math.Sin(a) * 2.5)) A.Spawn("footpad", cx + Math.Cos(a) * 2.5, cz + Math.Sin(a) * 2.5);
            }
        });
    }

    /// <summary>The Ashford levy's drill: a line of shields in step.</summary>
    void Levy()
    {
        var p = B.Player;
        A.Say("The levy", "A line of shields in step", "danger");
        double a = Math.Atan2(E.Z - p.Z, E.X - p.X);
        double cx = p.X + Math.Cos(a) * 11, cz = p.Z + Math.Sin(a) * 11, sx = -Math.Sin(a), sz = Math.Cos(a);
        for (int k = 0; k < 6 + A.Tier; k++)
        {
            double off = (k - (5 + A.Tier) / 2.0) * 2.0;
            if (A.CanStand(cx + sx * off, cz + sz * off)) A.Spawn("bruiser", cx + sx * off, cz + sz * off);
        }
    }

    /// <summary>The bell three times: every weapon stops for 6 s unless the ring is slipped.</summary>
    void TakeEverything()
    {
        var p = B.Player;
        A.Bark(E.X, E.Z, "The toll bell, three times.", "The Red Hand");
        var ring = B.Blow(new Battle.EnemyBlow { Shape = TelegraphShape.Circle, X = p.X, Z = p.Z, Radius = 4, Delay = 2, From = E, Label = "Takes everything" });
        double rx = p.X, rz = p.Z;
        ring.After = bb =>
        {
            var pp = bb.Player;
            if ((pp.X - rx) * (pp.X - rx) + (pp.Z - rz) * (pp.Z - rz) > 16 || pp.Iframes > 0) return;
            foreach (var w in bb.Weapons) w.DisabledT = Math.Max(w.DisabledT, 6);
            bb.Events.Emit(new Ev.Announce { Title = "He takes everything", Subtitle = "Six seconds with your hands alone", Tone = Tone.Danger });
        };
        Hold(2);
    }


    public override void Fell(Enemy e)
    {
        Recover(true);
        foreach (var w in B.Weapons) { w.DisabledT = 0; w.Timer = 0; }
        foreach (var id in posts) B.Collision.Remove(id);
        posts.Clear();
    }
}

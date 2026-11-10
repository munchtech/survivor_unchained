using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;
using Xunit;
using Xunit.Abstractions;

namespace SurvivorUnchained.Tests;

/// <summary>Every lamp on the P7 skills' wicks (skill_lamps.json: Heroic Leap, the Cleaver, Iron Vow, Shield Charge)
/// changes the fight (Sim/WardenWicks.cs). Data-driven: each lamp in the file runs its skill's seeded, scripted campaign
/// scene twice, its parents lit both times and itself lit the second, and the number its sentence promises must move the
/// way it promises (the table Measure: a lamp without a row, or a row that measures no change, fails). Then every lamp
/// lit at once: no exception, each scene runs out.</summary>
public sealed class WickRulesTests(ITestOutputHelper output)
{
    const double Dt = 1 / 60.0;
    static readonly string[] Skills = ["heroic_leap", "cleaver", "iron_vow", "shield_charge"];

    /// <summary>For each lamp: the scene's variant, the metric its sentence promises, and the way it must move.</summary>
    static readonly Dictionary<string, (string Variant, string Metric, int Sign)> Measure = new()
    {
        // Heroic Leap.
        ["heroic_leap.quake.1"] = ("base", "Struck", +1),          // the ring reaches 4.5 m
        ["heroic_leap.quake.2"] = ("base", "DealtTo:A", +1),       // the ring heaves again
        ["heroic_leap.quake.3"] = ("base", "DealtTo:By", +1),      // what it throws strikes what it lands on
        ["heroic_leap.quake.4"] = ("base", "MinOut", +1),          // none outside get in
        ["heroic_leap.flight.1"] = ("far", "Travel", +1),          // 13 m, not 9
        ["heroic_leap.flight.2"] = ("off", "Struck", +1),          // lands in the pack's heart
        ["heroic_leap.flight.3"] = ("walk", "Walk", +1),           // slows broken, 30% faster after
        ["heroic_leap.flight.4"] = ("hold", "Travel", +1),         // hangs, steered as far as 16 m
        ["heroic_leap.bound.1"] = ("base", "Timer", -1),           // a landing that kills 3 takes 4 s off
        ["heroic_leap.bound.2"] = ("probe", "Probe", -1),          // swings and casts 25% faster
        ["heroic_leap.bound.3"] = ("base", "Timer", -1),           // kills 5: ready at once
        ["heroic_leap.bound.4"] = ("again", "Presses", +1),        // leap on at once
        // The Cleaver.
        ["cleaver.wound.1"] = ("base", "Dealt", +1),               // every chop bleeds, 40%
        ["cleaver.wound.2"] = ("spatter", "DealtTo:By", +1),       // a bleeding death sprays bleed
        ["cleaver.wound.3"] = ("base", "DotEarly", +1),            // all of the bleed in 1.5 s
        ["cleaver.wound.4"] = ("base", "DealtEarly", +1),          // a chop tears the bleed open
        ["cleaver.weight.1"] = ("base", "OwnHeavy", +1),           // every 3rd chop heavy
        ["cleaver.weight.2"] = ("base", "LoDist", +1),             // a heavy chop throws 3 m
        ["cleaver.weight.3"] = ("base", "Spent", +1),              // 15% slower: in the campaign, its cost
        ["cleaver.weight.4"] = ("base", "Dealt", +1),              // Bonesplitter's shockwave
        ["cleaver.sweep.1"] = ("base", "Struck", +1),              // reaches 3.5 m
        ["cleaver.sweep.2"] = ("crowd", "Spent", -1),              // strikes 6: the next at once (free)
        ["cleaver.sweep.3"] = ("base", "Spent", -1),               // 25% faster: in the campaign, its cost
        ["cleaver.sweep.4"] = ("base", "HitsA", +1),               // every chop cuts twice
        // Iron Vow.
        ["iron_vow.hoard.1"] = ("base", "DealtTo:A", +1),          // stores 35%
        ["iron_vow.hoard.2"] = ("blocks", "DealtTo:A", +1),        // a block stores all of it
        ["iron_vow.hoard.3"] = ("base", "DealtTo:A", +1),          // bursts at 5 times
        ["iron_vow.hoard.4"] = ("base", "DealtTo:Ln", +1),         // a 14 m shockwave
        ["iron_vow.brace.1"] = ("base", "BurstAt", +1),            // 3.5 s
        ["iron_vow.brace.2"] = ("base", "HpLost", -1),             // cut by 70%
        ["iron_vow.brace.3"] = ("walk", "Travel", +1),             // walks at full speed
        ["iron_vow.brace.4"] = ("hold", "VowStruck", +1),          // held, the burst reaches further
        ["iron_vow.challenge.1"] = ("base", "Statused", +1),       // the burst sears
        ["iron_vow.challenge.2"] = ("base", "DealtTo:St", +1),     // blows strike their striker back
        ["iron_vow.challenge.3"] = ("base", "HpLost", -1),         // the burst mends
        ["iron_vow.challenge.4"] = ("base", "VowStruck", +1),      // the burst reaches 7 m
        // Shield Charge.
        ["shield_charge.ram.1"] = ("base", "Shield", +1),          // 25% barrier
        ["shield_charge.ram.2"] = ("base", "Shield", +1),          // a barrier for each struck
        ["shield_charge.ram.3"] = ("champ", "Dealt", +1),          // bleeds; champions harder
        ["shield_charge.ram.4"] = ("base", "DealtTo:E", +1),       // Pile Driver's slam
        ["shield_charge.drive.1"] = ("base", "Travel", +1),        // 12 m, not 8
        ["shield_charge.drive.2"] = ("base", "RideX", +1),         // the struck ride her shield
        ["shield_charge.drive.3"] = ("champ", "Travel", +1),       // no champion stops it
        ["shield_charge.drive.4"] = ("base", "DealtTo:F", +1),     // the riders hurled 10 m on
        ["shield_charge.guard.1"] = ("blows", "HpLost", -1),       // blocks from in front for 2 s
        ["shield_charge.guard.2"] = ("blows", "Timer", -1),        // each block 1 s off its wait
        ["shield_charge.guard.3"] = ("perfect", "Timer", -1),      // a perfect dash readies it
        ["shield_charge.guard.4"] = ("again", "Presses", +1),      // three runs
    };

    sealed record LampRec(string Id, string Skill, string? Parent, bool Turn, List<JsonElement> Effects);

    static List<LampRec> Lamps()
    {
        using var doc = JsonDocument.Parse(File.ReadAllText(Path.Combine(DataFiles.Dir, "content", "skill_lamps.json")));
        var list = new List<LampRec>();
        foreach (var l in doc.RootElement.GetProperty("lamps").EnumerateArray())
        {
            string skill = l.GetProperty("skill").GetString()!;
            if (!Skills.Contains(skill)) continue;
            list.Add(new LampRec(l.GetProperty("id").GetString()!, skill,
                l.TryGetProperty("parent", out var p) && p.ValueKind == JsonValueKind.String ? p.GetString() : null,
                l.TryGetProperty("turn", out var t) && t.ValueKind == JsonValueKind.True,
                l.GetProperty("effects").EnumerateArray().Select(e => e.Clone()).ToList()));
        }
        return list;
    }

    static List<LampRec> Chain(List<LampRec> all, LampRec l)
    {
        var c = new List<LampRec>();
        for (var p = l.Parent; p != null;) { var r = all.Single(x => x.Id == p); c.Insert(0, r); p = r.Parent; }
        return c;
    }

    /// <summary>Light a lamp as the game will (its rule ids with their numeric args; an evolve, the evolution).</summary>
    static void Light(Battle b, LampRec l)
    {
        foreach (var e in l.Effects)
        {
            string d = e.GetProperty("do").GetString()!;
            if (d == "evolve") { b.Evolve(l.Skill, e.GetProperty("evolution").GetString()!, chest: true); continue; }
            Assert.Equal("rule", d);
            var fx = new LampEffect { Do = LampDo.Rule, Rule = e.GetProperty("rule").GetString(), Args = new Dictionary<string, double>() };
            if (e.TryGetProperty("args", out var args))
                foreach (var a in args.EnumerateObject())
                {
                    if (a.Value.ValueKind == JsonValueKind.Number) fx.Args[a.Name] = a.Value.GetDouble();
                    else if (a.Name == "skill") fx.Skill = a.Value.GetString();
                    else if (a.Name == "status" && a.Value.TryGetProperty("kind", out var k) && fx.Rule == "skill.status")
                        fx.Status = Enum.Parse<StatusKind>(k.GetString()!, true);
                }
            b.Lamps.Add(fx);
        }
    }

    /* -------------------------------------------------------------- scenes -- */

    sealed class Scene
    {
        public Battle B = null!;
        public double X0, Z0;
        public readonly Dictionary<string, Enemy> Named = new();
        public readonly List<Enemy> Pinned = new();
        public readonly Dictionary<Enemy, (double X, double Z)> PinAt = new();
        public readonly SortedList<double, Action> Script = new();
        public readonly Dictionary<string, double> M = new();
        public double MoveX, MoveZ;
        public Func<(double X, double Z)>? Outsider;

        public Enemy Foe(string name, double dx, double dz, bool pin = true, double hp = 1e7, bool elite = false)
        {
            var e = B.SpawnEnemy("footpad", X0 + dx, Z0 + dz)!;
            e.Hp = e.MaxHp = hp;
            e.AttackT = e.RangedT = 999;
            e.Elite = elite;
            Named[name] = e;
            if (pin) { Pinned.Add(e); PinAt[e] = (e.X, e.Z); }
            return e;
        }

        public void At(double t, Action a) { while (Script.ContainsKey(t)) t += 1e-6; Script.Add(t, a); }
        public void Add(string m, double v) => M[m] = M.GetValueOrDefault(m) + v;
        public int Slot(string id) => B.Weapons.Single(w => w.Id == id).Slot;
        public WeaponInst W(string id) => B.Weapons.Single(w => w.Id == id);

        public void Press(string id, double dx, double dz)
        {
            if (id == "cleaver") B.Resolve.Set(100);
            double before = B.Resolve.Value;
            if (B.PressSkill(Slot(id), X0 + dx, Z0 + dz)) Add("Presses", 1);
            Add("Spent", before - B.Resolve.Value);
        }
    }

    static Scene Make(string skill, IEnumerable<LampRec> lit, params (string Id, int Rank)[] extra)
    {
        var skills = new List<(string, int)> { (skill, 1) };
        skills.AddRange(extra.Select(e => (e.Id, e.Rank)));
        var b = new Battle(new BattleSetup
        {
            Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
            Weapons = skills, Ability = AbilityKind.ShieldBash,
        });
        b.Calling = "warden";
        b.Lamps = new LampLoadout();
        foreach (var l in lit) Light(b, l);
        foreach (var w in b.Weapons) w.Timer = 0;
        b.Resolve.Set(100);
        return new Scene { B = b, X0 = b.Player.X, Z0 = b.Player.Z };
    }

    static Dictionary<string, double> Run(Scene s, double seconds)
    {
        var b = s.B;
        var p = b.Player;
        double sx = p.X, sz = p.Z;
        var stunned = new HashSet<int>();
        var statused = new HashSet<int>();
        var struck = new HashSet<int>();
        var ids = s.Named.ToDictionary(kv => kv.Value.Id, kv => kv.Key);
        double minOut = double.PositiveInfinity;
        var script = new Queue<KeyValuePair<double, Action>>(s.Script);
        for (double t = 0; t < seconds - 1e-9; t += Dt)
        {
            while (script.Count > 0 && script.Peek().Key <= t + 1e-9) script.Dequeue().Value();
            foreach (var e in s.Pinned) { (e.X, e.Z) = s.PinAt[e]; e.Vx = e.Vz = e.Kbx = e.Kbz = 0; }
            b.Tick(Dt, s.MoveX, s.MoveZ);
            foreach (var ev in b.Events.Drain())
            {
                if (ev is Ev.Hit h)
                {
                    s.Add("Dealt", h.Amount);
                    if (t < 1.0) s.Add("DealtEarly", h.Amount);
                    if (h.Dot && t < 2.2) s.Add("DotEarly", h.Amount);
                    if (!h.Dot) struck.Add(h.Target);
                    if (ids.TryGetValue(h.Target, out var n)) { s.Add("DealtTo:" + n, h.Amount); if (n == "A" && !h.Dot) s.Add("HitsA", 1); }
                }
                else if (ev is Ev.Cast { Heavy: true }) s.Add("OwnHeavy", 1);
                else if (ev is Ev.Brace { Phase: BracePhase.Burst } && !s.M.ContainsKey("BurstAt")) s.M["BurstAt"] = t;
                else if (ev is Ev.Leap { Phase: LeapPhase.Land }) s.Add("Leaps", 1);
            }
            foreach (var e in b.Enemies.Items)
            {
                if (!e.Alive) continue;
                if (e.Status.Has(StatusKind.Stun)) stunned.Add(e.Id);
                if (e.Status.Has(StatusKind.Bleed) || e.Status.Has(StatusKind.Sear)) statused.Add(e.Id);
            }
            if (s.Outsider != null && s.Named.TryGetValue("O", out var o) && o.Alive)
            {
                var c = s.Outsider();
                if (!double.IsNaN(c.X)) minOut = Math.Min(minOut, MathX.Dist(o.X, o.Z, c.X, c.Z));
            }
            s.Add("Shield", 0);
            s.M["Shield"] = Math.Max(s.M["Shield"], p.Shield);
        }
        s.M["Travel"] = MathX.Dist(p.X, p.Z, sx, sz);
        s.M["Struck"] = struck.Count;
        s.M["Stunned"] = stunned.Count;
        s.M["Statused"] = statused.Count;
        s.M["HpLost"] = b.MaxHp - p.Hp;
        s.M["VowStruck"] = b.VowStruck.Count;
        if (!double.IsPositiveInfinity(minOut)) s.M["MinOut"] = minOut;
        return s.M;
    }

    static Dictionary<string, double> LeapScene(string v, IEnumerable<LampRec> lit)
    {
        var s = Make("heroic_leap", lit, ("cleaver", 1));
        double lx = 8;
        s.Foe("A", lx + 1, 0);
        s.Foe("R4", lx, 4.3);
        s.Foe("T", lx, -2, pin: false);
        s.Foe("By", lx, -8);
        // Five that the landing kills ("again": one, so a kill opens the bound and restless's five don't ready it).
        int k = 0;
        foreach (var (dx, dz) in new[] { (-1.5, 0.0), (-0.8, 1.5), (-0.8, -1.4), (0.6, 1.8), (1.6, -1.2) }) s.Foe("w" + dx + dz, lx + dx, dz, hp: v == "again" && k++ > 0 ? 1e7 : 1);
        var o = s.Foe("O", lx + 7.5, 0, pin: false);
        double landAt = double.NaN;
        s.Outsider = () => !double.IsNaN(landAt) && s.B.Time >= landAt + 0.1 ? (s.X0 + lx, s.Z0) : (double.NaN, double.NaN);
        if (v == "walk") s.At(0.45, () => { s.B.Player.SlowT = 3; s.B.Player.SlowF = 0.5; });
        if (v == "hold") s.At(0.45, () => s.B.HoldSkill(s.Slot("heroic_leap"), true, s.X0 + 16, s.Z0));
        double ax = v switch { "far" or "hold" => 20, _ => lx }, az = v == "off" ? 3.6 : 0;
        s.At(0.5, () => { s.Press("heroic_leap", ax, az); landAt = s.B.Time + 0.62; });
        s.At(1.3, () => s.M["Timer"] = s.W("heroic_leap").Timer);
        if (v == "walk")
        {
            double wx = 0, wz = 0;
            s.At(1.25, () => { (wx, wz) = (s.B.Player.X, s.B.Player.Z); s.MoveX = -1; });
            s.At(2.25, () => { s.M["Walk"] = MathX.Dist(s.B.Player.X, s.B.Player.Z, wx, wz); s.MoveX = 0; });
        }
        if (v == "probe") s.At(1.4, () => { s.Press("cleaver", lx + 1, 0); s.M["Probe"] = s.W("cleaver").Timer; });
        if (v == "again") s.At(1.7, () => s.Press("heroic_leap", lx + 6, 0));
        if (v == "hold") s.At(3.0, () => s.B.HoldSkill(s.Slot("heroic_leap"), false));
        return Run(s, 4);
    }

    static Dictionary<string, double> CleaverScene(string v, IEnumerable<LampRec> lit)
    {
        var s = Make("cleaver", lit);
        s.Foe("A", 1.6, 0);
        s.Foe("Far3", 3.2, 0.3);
        var lo = s.Foe("Lo", 1.8, -0.6, pin: false);
        if (v == "spatter") { s.Foe("Vi", 2.0, 0.8, hp: 1); s.Foe("By", 4.2, 1.6); }
        if (v == "crowd") for (int i = 0; i < 7; i++) { double a = -0.9 + 0.3 * i; s.Foe("c" + i, 1.9 * Math.Cos(a), 1.9 * Math.Sin(a)); }
        foreach (var t in new[] { 0.2, 0.8, 1.4 }) s.At(t, () => s.Press("cleaver", 2, 0));
        s.At(1.47, () => s.M["LoDist"] = MathX.Dist(lo.X, lo.Z, s.B.Player.X, s.B.Player.Z));
        return Run(s, 6);
    }

    static Dictionary<string, double> VowScene(string v, IEnumerable<LampRec> lit)
    {
        var s = Make("iron_vow", lit);
        s.Foe("A", 2, 0);
        s.Foe("R6", 0, 6.5);
        s.Foe("Ln", 10, 0);
        var st = s.Foe("St", -1.5, 0);
        if (v == "hold") s.At(0.1, () => s.B.HoldSkill(s.Slot("iron_vow"), true, s.X0 + 14, s.Z0));
        s.At(0.2, () => s.Press("iron_vow", 14, 0));
        foreach (var t in new[] { 0.8, 1.2, 1.6, 2.0 })
            s.At(t, () =>
            {
                if (v == "blocks") s.B.RiposteUntil = s.B.Time + 0.05;
                s.B.HurtPlayer(30, School.Physical, "test", st);
            });
        if (v == "walk") { s.At(0.25, () => s.MoveZ = -1); s.At(2.0, () => s.MoveZ = 0); }
        if (v == "hold") s.At(4.2, () => s.B.HoldSkill(s.Slot("iron_vow"), false));
        return Run(s, 6);
    }

    static Dictionary<string, double> ChargeScene(string v, IEnumerable<LampRec> lit)
    {
        var s = Make("shield_charge", lit);
        var s1 = s.Foe("S1", 3, 0, pin: false);
        s.Foe("S2", 5, 0.4, pin: false);
        s.Foe("E", 9.5, 1.5);
        s.Foe("F", 17, 0);
        var fr = s.Foe("Fr", 30, 0);
        if (v == "champ") s.Foe("C", 3.5, -0.3, elite: true);
        double s1x = s1.X;
        s.At(0.3, () => s.Press("shield_charge", 20, 0));
        s.At(0.9, () => s.M["RideX"] = s1.X - s1x);
        if (v == "blows")
        {
            foreach (var t in new[] { 0.9, 1.1, 1.3 }) s.At(t, () => s.B.HurtPlayer(20, School.Physical, "test", fr));
            s.At(1.5, () => s.M["Timer"] = s.W("shield_charge").Timer);
        }
        if (v == "perfect")
        {
            s.At(1.0, () =>
            {
                var p = s.B.Player;
                p.Iframes = 0.3; p.DodgeWindow = 0.2; p.PerfectThisDash = false;
                s.B.HurtPlayer(10, School.Physical, "test", fr, telegraphed: true);
            });
            s.At(1.1, () => s.M["Timer"] = s.W("shield_charge").Timer);
        }
        if (v == "again") s.At(1.2, () => s.Press("shield_charge", 40, 0));
        return Run(s, 3);
    }

    static Dictionary<string, double> SceneOf(string skill, string v, IEnumerable<LampRec> lit) => skill switch
    {
        "heroic_leap" => LeapScene(v, lit),
        "cleaver" => CleaverScene(v, lit),
        "iron_vow" => VowScene(v, lit),
        _ => ChargeScene(v, lit),
    };

    /* --------------------------------------------------------------- tests -- */

    [Fact]
    public void Every_lamp_on_the_four_skills_changes_the_number_its_sentence_promises()
    {
        var all = Lamps();
        Assert.Equal(4, all.Select(l => l.Skill).Distinct().Count());
        var fails = new List<string>();
        foreach (var l in all)
        {
            if (!Measure.TryGetValue(l.Id, out var m)) { fails.Add($"{l.Id}: no row in Measure (a new lamp needs its rule and its measure)"); continue; }
            var chain = Chain(all, l);
            var off = SceneOf(l.Skill, m.Variant, chain);
            var on = SceneOf(l.Skill, m.Variant, chain.Append(l).ToList());
            double a = off.GetValueOrDefault(m.Metric), c = on.GetValueOrDefault(m.Metric);
            string line = $"{l.Id,-26} {m.Variant,-8} {m.Metric,-11} {a,10:0.###} -> {c,10:0.###}";
            output.WriteLine(line);
            if (Math.Sign(c - a) != m.Sign || Math.Abs(c - a) < 1e-6 * Math.Max(1, Math.Abs(a))) fails.Add(line);
        }
        Assert.True(fails.Count == 0, "lamps that changed nothing (or the wrong way):\n" + string.Join("\n", fails));
    }

    [Fact]
    public void Every_lamp_lit_at_once_breaks_nothing()
    {
        var all = Lamps();
        foreach (var skill in Skills)
        {
            var lit = all.Where(l => l.Skill == skill).ToList();
            foreach (var v in Measure.Where(kv => kv.Key.StartsWith(skill + ".")).Select(kv => kv.Value.Variant).Distinct())
            {
                var m = SceneOf(skill, v, lit);
                Assert.True(m.GetValueOrDefault("Presses") >= 1, $"{skill} {v}: nothing went off");
                Assert.True(m.Values.All(x => !double.IsNaN(x)), $"{skill} {v}: a NaN");
            }
        }
    }

    [Fact]
    public void Bladestorms_spin_carries_the_cleavers_lamps()
    {
        double Bleeding(bool lit)
        {
            var b = new Battle(new BattleSetup
            {
                Seed = 5, Collision = new CollisionWorld(120), Combat = true, Campaign = true, Stats = BattleTests.BaseStats(),
                Weapons = [("sunder", 1), ("cleaver", 1)], Ability = AbilityKind.ShieldBash,
            });
            b.Calling = "warden";
            b.Lamps = new LampLoadout();
            if (lit) b.Lamps.Add(new LampEffect { Do = LampDo.Rule, Rule = "cleaver.laid_open", Args = new Dictionary<string, double>() });
            var w = b.GrantUnion("bladestorm")!;
            w.Timer = 0;
            b.Resolve.Set(100);
            var p = b.Player;
            var foes = Enumerable.Range(0, 6).Select(i =>
            {
                var e = b.SpawnEnemy("footpad", p.X + 2 * Math.Cos(i), p.Z + 2 * Math.Sin(i))!;
                e.Hp = e.MaxHp = 1e7; e.AttackT = e.RangedT = 999;
                return e;
            }).ToList();
            var at = foes.Select(e => (e.X, e.Z)).ToList();
            b.HoldSkill(w.Slot, true);
            Assert.True(b.PressSkill(w.Slot, p.X + 1, p.Z));
            int bleeding = 0;
            for (int i = 0; i < 30; i++)
            {
                for (int k = 0; k < foes.Count; k++) { foes[k].X = at[k].X; foes[k].Z = at[k].Z; foes[k].Vx = foes[k].Vz = 0; }
                b.Tick(Dt, 0, 0);
            }
            foreach (var e in foes) if (e.Status.Has(StatusKind.Bleed)) bleeding++;
            return bleeding;
        }
        Assert.Equal(0, Bleeding(false));
        Assert.Equal(6, Bleeding(true));
    }
}

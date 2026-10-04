using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* Champion Signs (docs/bestiary/COUNTERS.md section 4; docs/SKILLS_DESIGN.md, "Encounters").
 *
 * A champion used to be its kind with three times the health. A Sign gives it one more
 * verb, with a tell on its body and its name, and with answers in more than one kind of
 * build. Signs never grow stronger with the tier, only more numerous; some never go
 * together. A signed champion is its own def (a copy with the verb added), so everything
 * that reads a def (the AI, the view, the bestiary) sees the Sign without being told. */

/// <summary>A Sign: its name (worn before the kind's: "Swift, Kindled Barrow Knight"), its colour
/// on the body, and what it adds.</summary>
public sealed record SignDef(string Id, string Name, (double R, double G, double B) Tint, double Glow, Func<EnemyDef, EnemyDef?> Apply);

public static class Signs
{
    static LungeSpec? Quicker(LungeSpec? l) => l == null ? null : l with { Cooldown = l.Cooldown * 0.7 };

    public static readonly SignDef[] All =
    [
        // Faster, and its run comes oftener: chill, knockback, a tree, a vault.
        new("swift", "Swift", (1.1, 1.08, 1.0), 0, d =>
        {
            var c = d.Clone();
            c.Speed *= 1.35;
            c.Lunge = Quicker(d.Lunge);
            c.Charge = Quicker(d.Charge);
            return c;
        }),
        // Shrugs off two fifths of any blow that is not a critical: crits land in full.
        new("ironbound", "Ironbound", (0.78, 0.8, 0.88), 0, d => { var c = d.Clone(); c.IronSkin = 0.4; return c; }),
        // Leaves burning ground behind it: keep moving, or stand in fire you can bear.
        new("kindled", "Kindled", (1.3, 0.85, 0.6), 0.18, d =>
            d.Trail != null ? null : With(d, c => c.Trail = new TrailSpec(0.6, 1.2, 3, 0.3, School.Fire))),
        // Its blows chill to a crawl: tenacity, a sprint, sure footing.
        new("rimed", "Rimed", (0.8, 0.95, 1.35), 0.1, d => With(d, c => c.Bite = StatusKind.Chill)),
        // Dies into a blast after a breath: a dash out, a kill at range.
        new("volatile", "Volatile", (1.35, 1.05, 0.6), 0.22, d =>
            d.Burst != null ? null : With(d, c => c.Burst = new BurstSpec(3, 1.4, 1.0, School.Fire, StatusKind.Burn))),
        // Dies into three of its people's rank and file: area.
        new("brood", "Brood", (0.95, 1.12, 0.78), 0.06, d =>
            d.Split != null ? null : With(d, c => c.Split = new SplitSpec(BroodOf(d), 3))),
        // A shield on its arm: go round it, or use what is not a projectile. Never on a guard.
        new("shielded", "Shielded", (0.92, 0.92, 0.95), 0, d =>
            d.Guard != null ? null : With(d, c => c.Guard = new GuardSpec(1.5, 0.6))),
        // Its own round it quicker and quicker to strike while it lives: kill it first.
        new("bannered", "Bannered", (1.25, 0.82, 0.8), 0.12, d =>
            d.Aura != null ? null : With(d, c => c.Aura = new AuraSpec(6, 8, 4, Haste: 1.25, Word: "Rally"))),
        // Raises two of the fallen near it, again and again: move the fight off the bodies.
        new("gravebound", "Gravebound", (0.82, 0.88, 1.15), 0.1, d =>
            d.Raise != null ? null : With(d, c => c.Raise = new RaiseSpec(8, 2, BroodOf(d), 7))),
    ];

    public static SignDef Get(string id) => All.First(s => s.Id == id);

    static EnemyDef With(EnemyDef d, Action<EnemyDef> f) { var c = d.Clone(); f(c); return c; }

    /// <summary>What a brood or a raising brings up: the people's rank and file.</summary>
    static string BroodOf(EnemyDef d) => d.Faction switch
    {
        Faction.Pack => "wolf",
        Faction.Dead => "risen",
        Faction.Lampling => "lampling",
        Faction.Kerchief => "footpad",
        _ => d.Id,
    };

    /// <summary>Pairs never worn together: a fast slower is inescapable; two "your hits do not
    /// count"; two "more of them"; a charge that ends in a blast.</summary>
    static readonly (string, string)[] Never =
    [
        ("swift", "rimed"), ("brood", "gravebound"), ("swift", "volatile"),
    ];

    /// <summary>May this kind wear this Sign beside those it already wears?</summary>
    public static bool Fits(EnemyDef d, string sign, IReadOnlyCollection<string> worn)
    {
        if (worn.Contains(sign)) return false;
        foreach (var (a, b) in Never)
            if ((sign == a && worn.Contains(b)) || (sign == b && worn.Contains(a))) return false;
        // A Swift charger that bursts, a Shielded guard: the Apply refuses what cannot be.
        if (sign == "volatile" && (d.Charge ?? d.Lunge) != null && worn.Contains("swift")) return false;
        return Get(sign).Apply(d) != null;
    }

    static readonly Dictionary<string, EnemyDef> made = new();

    /// <summary>A kind wearing these Signs, in order (made once and kept). Its id stays its
    /// kind's, so the bestiary, the drops and the kills count it as what it is.</summary>
    public static EnemyDef Wear(EnemyDef kind, IReadOnlyList<string> signs)
    {
        if (signs.Count == 0) return kind;
        string key = kind.Id + "+" + string.Join("+", signs);
        lock (made)
        {
            if (made.TryGetValue(key, out var have)) return have;
            var d = kind;
            var tint = kind.Tint ?? (1, 1, 1);
            double glow = kind.Glow ?? 0;
            foreach (var s in signs)
            {
                var sd = Get(s);
                d = sd.Apply(d) ?? d;
                tint = (tint.R * sd.Tint.R, tint.G * sd.Tint.G, tint.B * sd.Tint.B);
                glow = Math.Max(glow, sd.Glow);
            }
            if (ReferenceEquals(d, kind)) d = kind.Clone();
            d.Signs = signs.ToArray();
            d.Name = string.Join(", ", signs.Select(s => Get(s).Name)) + " " + kind.Name;
            d.Tint = tint;
            d.Glow = glow;
            made[key] = d;
            return d;
        }
    }
}

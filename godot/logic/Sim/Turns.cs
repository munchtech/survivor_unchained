using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/// <summary>A school strand's lead-ins at work: the status its hits may apply, more damage to what has it, and more
/// of its time.</summary>
public sealed record WickStatus(StatusPayload Pay, double VsStatus, double Duration);

/// <summary>
/// A skill's lit wick as numbers on the weapon (docs/design/CLASS_IDENTITY_AND_TALENTS.md 3.3): what its lead-ins
/// add and what its Turn makes of it. Built once whenever the lit lamps or the skill change (in, ranked, evolved,
/// united), so the hot path only multiplies. A weapon with no wick has none of this (null), and fights as before.
/// </summary>
public sealed class WickFx
{
    /// <summary>The lamps lit, in the order they lit.</summary>
    public string[] Lit = Array.Empty<string>();
    /// <summary>The Turns at work, and those dark for this night (the evolution or union changed what they turned).</summary>
    public List<string> Turns = new(), Dark = new();
    public double Damage = 1, Area = 1, Speed = 1, Cooldown = 1, Projectiles = 1;
    public int Chains, Bounces;
    public double VsChampion;
    public GroundSpec? Ground;
    /// <summary>A school Turn: what it became, and the status its old school's became.</summary>
    public School? School;
    public School From;
    public StatusPayload? Status;
    public List<WickStatus> Statuses = new();

    public bool TurnLit => Turns.Count > 0;
}

public static class Turns
{
    /// <summary>A status native to a school, which follows the school when a Turn converts it.</summary>
    public static StatusKind? NativeStatus(School s) => s switch
    {
        School.Fire => StatusKind.Burn, School.Frost => StatusKind.Chill, School.Holy => StatusKind.Sear,
        School.Storm => StatusKind.Shock, School.Nature => StatusKind.Poison, _ => null,
    };

    /// <summary>Does an evolution replace a shape (its own behavior, or a count or arc of its own)? Then a shape Turn
    /// has nothing left to turn, and goes dark for the night.</summary>
    public static bool ReplacesShape(Evolution? e) =>
        e != null && (e.Behavior != null || e.Set?.Projectiles != null || e.Set?.Arc != null);

    /// <summary>The weapon's own behavior, tags and school, before any Turn.</summary>
    static (WeaponBehavior B, Tag[] Tags, School S, bool Splash) Natural(WeaponInst w)
    {
        var school = w.Evolution?.School ?? w.Def.School;
        var t = new List<Tag>(w.Def.Tags);
        if (w.Evolution?.AddTags is { } add) foreach (var a in add) if (!t.Contains(a)) t.Add(a);
        if (!t.Contains(school.AsTag())) t.Add(school.AsTag());
        return (w.Behavior, t.ToArray(), school, (w.Num(s => s.Splash) ?? 0) > 0);
    }

    /// <summary>May this lit Turn work on the weapon as it is now? A union's carried Turns pass united = true: the
    /// union's weapon is its own, so only whether it suits counts.</summary>
    public static bool Works(WeaponInst w, StrandDef s, bool united = false)
    {
        var t = s.TurnDef;
        if (t.Inert) return false;
        var (b, tags, school, splash) = Natural(w);
        if (!Wicks.Suits(s, b, tags, school, splash)) return false;
        if (united) return true;
        if (s.Kind == StrandKind.Shape && ReplacesShape(w.Evolution)) return false;
        // An evolution of a school of its own has already turned it.
        if (s.Kind == StrandKind.School && w.Evolution?.School != null) return false;
        return true;
    }

    /// <summary>The numbers of lit lamps (each a strand and its place, 1-4) on a weapon.</summary>
    public static WickFx Build(WeaponInst w, IEnumerable<(StrandDef Strand, int N)> lit, IEnumerable<string>? ids = null, bool united = false)
    {
        var fx = new WickFx { Lit = ids?.ToArray() ?? Array.Empty<string>(), From = Natural(w).S };
        bool projectile = w.Def.Tags.Has(Tag.Projectile) || w.Evolution?.AddTags?.Contains(Tag.Projectile) == true;
        double dmg = 0, area = 0, speed = 0, cd = 0;
        // School lead-ins gather by strand, so each strand's status keeps its own numbers.
        var school = new Dictionary<StrandDef, (double Chance, double Vs, double Dur)>();
        foreach (var (s, n) in lit)
        {
            if (n < Wicks.PerStrand)
            {
                var l = s.LeadIns[n - 1];
                dmg += l.Damage; cd += l.Cooldown; speed += l.Speed;
                if (projectile && l.ProjectileSpeed != 0) speed += l.ProjectileSpeed; else area += l.Area;
                fx.VsChampion += l.VsChampion;
                if (l.StatusChance != 0 || l.VsStatus != 0 || l.StatusDuration != 0)
                {
                    var c = school.GetValueOrDefault(s);
                    school[s] = (c.Chance + l.StatusChance, c.Vs + l.VsStatus, c.Dur + l.StatusDuration);
                }
                continue;
            }
            var t = s.TurnDef;
            if (!Works(w, s, united)) { fx.Dark.Add(t.Id); continue; }
            fx.Turns.Add(t.Id);
            fx.Damage *= t.Damage; fx.Area *= t.Area; fx.Cooldown *= t.Cooldown; fx.Projectiles *= t.Projectiles;
            fx.Chains += t.Chains; fx.Bounces += t.Bounces;
            if (t.Ground != null) fx.Ground = t.Ground;
            if (t.School is { } sc && fx.School == null) { fx.School = sc; fx.Status = t.Status; }
        }
        fx.Damage *= 1 + dmg; fx.Area *= 1 + area; fx.Speed *= 1 + speed; fx.Cooldown *= Math.Max(0.1, 1 + cd);
        foreach (var (s, (chance, vs, dur)) in school)
            if (s.TurnDef.Status is { } st) fx.Statuses.Add(new WickStatus(st with { Chance = chance }, vs, dur));
        return fx;
    }
}

public sealed partial class Battle
{
    /// <summary>Each skill's wick, in the order it lights (Rpg/WickBook.Path: the day's plan, then Light my way).
    /// A skill not here has no wick in this fight; an empty map (a bare test fight) leaves every skill as it was.</summary>
    public Dictionary<string, string[]> WickPaths = new();
    /// <summary>Wick lamps lit by the ember tonight, for measurement and tests.</summary>
    public int WickLit;

    /// <summary>Light a weapon's wick to its rank (as it comes in, ranks up or evolves). At night each new lamp is
    /// shown (Ev.Wick). A skill with no path keeps what it has (a union's carried Turns).</summary>
    internal void Relight(WeaponInst w, bool show)
    {
        if (!WickPaths.TryGetValue(w.Id, out var path) || Wicks.Of(w.Id) == null) return;
        int had = w.Wick?.Lit.Length ?? 0;
        var ids = path.Take(Math.Min(w.Rank, path.Length)).ToArray();
        var lit = ids.Select(id => Wicks.Lamp(w.Id, id)).Where(l => l != null).Select(l => l!.Value);
        w.Wick = Turns.Build(w, lit, ids);
        if (!show || !EmberOn) return;
        for (int i = had; i < ids.Length; i++)
        {
            WickLit++;
            Events.Emit(new Ev.Wick { Skill = w.Id, Lamp = ids[i], Turn = Wicks.IsTurn(w.Id, ids[i]) });
        }
    }

    /// <summary>A union keeps each part's lit Turn while its own weapon still suits it; the rest go dark.</summary>
    internal void CarryTurns(WeaponInst into, params WeaponInst?[] parts)
    {
        var carried = new List<(StrandDef, int)>();
        foreach (var p in parts)
        {
            if (p?.Wick == null) continue;
            foreach (var id in p.Wick.Lit)
                if (Wicks.Lamp(p.Id, id) is { N: Wicks.PerStrand } l) carried.Add(l);
        }
        if (carried.Count > 0) into.Wick = Turns.Build(into, carried, united: true);
    }

    /// <summary>A wick's damage against this creature: its school strand's status on it, a champion.</summary>
    internal double WickDamageMul(Enemy e, WickFx fx)
    {
        double m = 1;
        if (fx.VsChampion != 0 && e.Elite && !e.Boss) m *= 1 + fx.VsChampion;
        foreach (var s in fx.Statuses) if (s.VsStatus != 0 && e.Status.Has(s.Pay.Kind)) m *= 1 + s.VsStatus;
        return m;
    }

    /// <summary>A school strand's chance to apply its status, on each hit of the skill.</summary>
    internal void WickStatuses(Enemy e, WickFx fx, double dmg, int depth, string? by)
    {
        foreach (var s in fx.Statuses) if (s.Pay.Chance > 0) ApplyStatus(e, s.Pay, dmg, depth, by);
    }

    /// <summary>A school strand's longer status, when the skill applies it.</summary>
    double WickDuration(StatusKind k)
    {
        if (statusWeapon?.Wick is not { } fx) return 1;
        double m = 1;
        foreach (var s in fx.Statuses) if (s.Pay.Kind == k) m *= 1 + s.Duration;
        return m;
    }
}

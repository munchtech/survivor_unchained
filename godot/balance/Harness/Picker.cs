using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Balance;

/// <summary>How a bot takes cards. Each policy is a way a player might
/// draft: the strongest-looking card now (greedy), one path held to
/// (path:ID), anything (random), or whatever comes first (first).</summary>
public abstract class Picker
{
    public abstract string Name { get; }
    /// <summary>The path it means to walk, if it means to walk one.</summary>
    public virtual PathDef? Path => null;
    public abstract int Choose(Battle b, List<Offer> offers, Rng rng);
    /// <summary>Reroll this draft rather than take any of it?</summary>
    public virtual bool Reroll(Battle b, List<Offer> offers) => false;
    /// <summary>Banish one of these for the rest of the run? Its index, or -1.</summary>
    public virtual int Banish(Battle b, List<Offer> offers) => -1;
    /// <summary>Skip this draft (where skipping is allowed)?</summary>
    public virtual bool Skip(Battle b, List<Offer> offers) => false;

    public static Picker Make(string spec) => spec switch
    {
        "first" => new FirstPicker(),
        "random" => new RandomPicker(),
        "greedy" => new GreedyPicker(null),
        _ when spec.StartsWith("path:") => new GreedyPicker(Paths.Find(spec[5..]) ?? throw new ArgumentException($"no path {spec[5..]}")),
        _ => throw new ArgumentException($"no policy {spec}"),
    };
}

sealed class FirstPicker : Picker
{
    public override string Name => "first";
    public override int Choose(Battle b, List<Offer> offers, Rng rng) => 0;
}

sealed class RandomPicker : Picker
{
    public override string Name => "random";
    public override int Choose(Battle b, List<Offer> offers, Rng rng)
    {
        // An evolution is always taken: refusing one is not a way anyone plays.
        int evo = offers.FindIndex(o => o.Kind == OfferKind.Evolve);
        return evo >= 0 ? evo : rng.Int(0, offers.Count - 1);
    }
}

/// <summary>A sensible player: values each card by what it does for the
/// build as it stands (the weapon dealing most, the passives that touch
/// what is carried, defence when hurt), with a path to hold to if it has one.</summary>
sealed class GreedyPicker(PathDef? path) : Picker
{
    public override string Name => path == null ? "greedy" : $"path:{path.Id}";
    public override PathDef? Path => path;

    public override int Choose(Battle b, List<Offer> offers, Rng rng)
    {
        int best = 0;
        double bs = double.MinValue;
        for (int i = 0; i < offers.Count; i++)
        {
            double s = Score(b, offers[i]) + rng.Next() * 6;
            if (s > bs) { bs = s; best = i; }
        }
        return best;
    }

    public override bool Reroll(Battle b, List<Offer> offers)
    {
        if (path == null || offers.Any(o => o.Kind == OfferKind.Evolve || o.Great || o.Blessing)) return false;
        // Nothing on the path, and the path still has room: look again.
        return !offers.Any(o => OnPath(o)) && b.Weapons.Count(w => path.Weapons.Contains(w.Id)) < Math.Min(4, path.Weapons.Length);
    }

    public override int Banish(Battle b, List<Offer> offers)
    {
        if (path == null) return -1;
        // A new combat skill off the path, while the arsenal still has room for the path's own.
        return offers.FindIndex(o => o.Kind == OfferKind.Weapon && !path.Weapons.Contains(o.Id) && b.Weapons.Count < Weapons.MaxWeapons - 1);
    }

    bool OnPath(Offer o) => path != null && o.Kind switch
    {
        OfferKind.Weapon or OfferKind.Rank => path.Weapons.Contains(o.Id),
        OfferKind.Boon => path.Passives.Contains(o.Id) || path.Blessings.Contains(o.Id) || path.Great.Contains(o.Id),
        OfferKind.Evolve => true,
        _ => false,
    };

    double Share(Battle b, string weapon)
    {
        double total = 0, mine = 0;
        foreach (var (k, v) in b.DamageBy)
        {
            total += v;
            if (k == weapon) mine += v;
        }
        return total <= 0 ? 1.0 / Math.Max(1, b.Weapons.Count) : mine / total;
    }

    int Carrying(Battle b, params Tag[] tags) => b.Weapons.Count(w => tags.Any(w.Tags.Contains));

    double Score(Battle b, Offer o)
    {
        double hp = b.Player.Hp / b.MaxHp;
        double s;
        switch (o.Kind)
        {
            case OfferKind.Evolve:
                s = 1000 + (path?.Capstones.Contains(o.Branch!) == true ? 100 : 0);
                break;
            case OfferKind.Weapon:
            {
                int n = b.Weapons.Count;
                s = n < 2 ? 70 : n < 4 ? 50 : 30;
                var d = Weapons.All[o.Id];
                var build = LevelUp.BuildTags(b);
                s += 4 * d.Tags.Count(build.Contains);
                if (path != null) s += path.Weapons.Contains(o.Id) ? 60 : -25;
                break;
            }
            case OfferKind.Rank:
            {
                var w = b.Weapons.First(x => x.Id == o.Id);
                s = 40 + 40 * Share(b, w.Id);
                if (o.To == Weapons.MaxRank) s += 15 + (w.Def.Evolutions.Any(e => e.Catalysts.Any(c => b.Boons.GetValueOrDefault(c) > 0)) ? 40 : 0);
                if (path != null && path.Weapons.Contains(o.Id)) s += 20;
                break;
            }
            case OfferKind.Boon when o.Great:
                s = (path?.Great.Contains(o.Id) == true ? 60 : 0) + (o.From > 0 ? 15 : 0) + GreatValue(o.Id);
                break;
            case OfferKind.Boon when o.Blessing:
            {
                var d = Boons.All[o.Id];
                var build = LevelUp.BuildTags(b);
                s = 30 + 8 * d.Tags.Count(build.Contains) + (o.From > 0 ? 10 : 0);
                if (path != null && path.Blessings.Contains(o.Id)) s += 40;
                break;
            }
            case OfferKind.Boon:
            {
                s = PassiveValue(b, o.Id, hp);
                if (path != null && path.Passives.Contains(o.Id)) s += 35;
                // A catalyst for a weapon carried and not yet evolved.
                foreach (var w in b.Weapons)
                    if (w.Evolution == null && w.Def.Evolutions.Any(e => e.Catalysts.Contains(o.Id)) && b.Boons.GetValueOrDefault(o.Id) == 0)
                        s += w.Rank >= 6 ? 45 : 20;
                if (o.From > 0) s *= 0.9;
                break;
            }
            case OfferKind.Heal: s = 5 + 40 * (1 - hp); break;
            default: s = 1; break;
        }
        return s;
    }

    /// <summary>A plain player's sense of a great blessing: none is ruled out.</summary>
    static double GreatValue(string id) => 10;

    double PassiveValue(Battle b, string id, double hp)
    {
        double crit = b.Stats.Get(Stat.CritChance);
        double defence = 18 + 40 * (1 - hp) + (b.Time > 900 ? 10 : 0);
        return id switch
        {
            "might" => 40,
            "haste" => 42,
            "duplicity" => 10 + 12 * Carrying(b, Tag.Projectile, Tag.Orbit, Tag.Chain, Tag.Melee),
            "precision" => 32,
            "ferocity" => 20 + 60 * crit,
            "expanse" => 18 + 6 * Carrying(b, Tag.Area, Tag.Zone, Tag.Nova, Tag.Aura),
            "perennial" => 8 + 7 * Carrying(b, Tag.Zone, Tag.Orbit, Tag.Summon),
            "serration" => 15 + 40 * crit + 6 * Carrying(b, Tag.Steel),
            "chilling" or "searing" => 26,
            "fleetfoot" => 15,
            "thorns" => 10,
            "vitality" or "ironhide" or "recovery" or "evasion" or "warding" => defence,
            _ => 8,
        };
    }
}

using System;
using System.Linq;
using SurvivorUnchained.Content;
using static SurvivorUnchained.Core.MathX;

namespace SurvivorUnchained.Sim;

/// <summary>(SU-072) Whose side a creature's blow is on, taken when it is thrown: a missile in flight still knows it
/// after its thrower is dead or its slot reused.</summary>
public readonly record struct Allegiance(Faction Faction, bool Ally, bool HostileToPlayer, string Credit, double? BossDamage)
{
    public static Allegiance Of(Enemy e) => new(e.Faction, e.Disposition == Disposition.Ally, e.Disposition == Disposition.Hostile || e.Provoked,
        e.SummonedBy ?? e.Def.Id, e.SummonedBy != null && Weapons.All.TryGetValue(e.SummonedBy, out var by) ? by.BossDamage : null);
}

public sealed partial class Battle
{
    static readonly Tag[] AllyBlow = [Tag.Summon, Tag.Melee, Tag.Physical], AllyShot = [Tag.Summon, Tag.Projectile];

    /// <summary>Whether a creature on side a may harm o: her allies harm what is hostile, anything hostile to her harms
    /// her allies, rival factions harm each other. One rule for choosing a target and for what a blow or missile strikes (SU-072).</summary>
    public bool MayHarm(in Allegiance a, Enemy o)
    {
        if (a.Ally) return o.Disposition != Disposition.Ally && (o.Disposition == Disposition.Hostile || o.Provoked);
        return o.Disposition == Disposition.Ally ? a.HostileToPlayer : FactionsAtWar(a.Faction, o.Faction);
    }

    /// <summary>One creature's blow on another, whatever carried it (a bite, a charge, a missile). Her allies strike for
    /// her, so theirs runs through her pipeline; a rival's is real damage, no credit, and it draws attention.</summary>
    internal void CreatureStrike(Enemy o, double dmg, School school, in Allegiance by, Enemy? from, double dirX, double dirZ, bool missile = false)
    {
        if (by.Ally)
        {
            HitEnemy(o, dmg, school, missile ? AllyShot : AllyBlow, new HitOpts { Summon = true, Knockback = 0.3, DirX = dirX, DirZ = dirZ, Credit = by.Credit,
                BossDamage = by.BossDamage, Projectile = missile, FromX = dirX, FromZ = dirZ });
            return;
        }
        o.Hp -= dmg;
        o.Flash = 1;
        Events.Emit(new Ev.Hit { X = o.X, Z = o.Z, Amount = dmg, Crit = false, School = school, Target = o.Id });
        if (from != null && o.Target != from.Id && Rng.Next() < 0.6) o.Target = from.Id;
        if (o.Hp <= 0) KillEnemy(o, false, null);
    }

    bool MayStrike(Projectile pr, in Allegiance al, Enemy o) =>
        o.Alive && o.State is not (EnemyState.Dying or EnemyState.Burrowed) && Lifetime.Of(o) != pr.OwnerLife && MayHarm(al, o);

    /// <summary>A creature's missile in flight strikes the first creature its thrower may harm that it touches (SU-072).</summary>
    bool MissileStrikesCreature(Projectile pr, in Allegiance al)
    {
        Spatial.Query(pr.X, pr.Z, pr.Radius + Math.Max(1.2, Spatial.MaxRadius), qProj);
        foreach (var id in qProj)
        {
            var o = Enemies.Items[id];
            if (!MayStrike(pr, al, o) || Dist(o.X, o.Z, pr.X, pr.Z) >= pr.Radius + o.Radius) continue;
            double l = Math.Max(1e-6, Math.Sqrt(pr.Vx * pr.Vx + pr.Vz * pr.Vz));
            CreatureStrike(o, pr.Damage, pr.School, al, Live(pr.OwnerLife), pr.Vx / l, pr.Vz / l, true);
            return true;
        }
        return false;
    }

    /// <summary>A creature's lobbed pot bursts on every creature in reach its thrower may harm (SU-072).</summary>
    void LobStrikesCreatures(Projectile pr, in Allegiance al, double r)
    {
        Spatial.Query(pr.X, pr.Z, r + Math.Max(1.2, Spatial.MaxRadius), qProj);
        var src = Live(pr.OwnerLife);
        foreach (var id in qProj.ToArray())   // (a death's hooks may query again)
        {
            var o = Enemies.Items[id];
            double d = Dist(o.X, o.Z, pr.X, pr.Z);
            if (!MayStrike(pr, al, o) || d >= r + o.Radius) continue;
            double dd = Math.Max(1e-6, d);
            CreatureStrike(o, pr.Damage, pr.School, al, src, (o.X - pr.X) / dd, (o.Z - pr.Z) / dd, true);
        }
    }
}

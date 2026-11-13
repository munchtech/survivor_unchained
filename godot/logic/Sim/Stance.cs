using System;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/* (bd-keys, docs/design/BUILD_DIRECTION.md round 8; BUILD_UNLOCKS.md level 8) The second weapon set is a stance, not a
 * second bar. She keeps the same four keys and her auto slots: in set B the stance weapon flavors every key's landed blows
 * (Content/Stances.cs StanceBlow) and its price and gift ride her numbers (StanceDef.Mods, source "stance:<id>"); nothing
 * is ever turned off, and no weapon gate reads set B. Every swap is a strike: set A's own (her calling weapon's) or set
 * B's, as she takes the set up, each on its own internal cooldown, so swapping fast swaps but does not strike.
 *
 * API for the views (bd-ui): Battle.StanceB (null: no second set yet), OnB, StanceNow, Swap(), StrikeOf(set),
 * StrikeReadyIn(set), Swaps, SwapStrikes; Ev.Swap on every swap. */
public sealed partial class Battle
{
    /// <summary>Her second weapon set's stance; null until it opens (SkillBook.StanceOf) or outside the campaign.</summary>
    public StanceDef? StanceB { get; private set; }
    /// <summary>She is in set B now.</summary>
    public bool OnB { get; private set; }
    /// <summary>The stance flavoring her keys now (null in set A).</summary>
    public StanceDef? StanceNow => OnB ? StanceB : null;
    /// <summary>Swaps made, and swap strikes fired, this fight.</summary>
    public int Swaps { get; private set; }
    public int SwapStrikes { get; private set; }

    readonly double[] strikeReady = [double.NegativeInfinity, double.NegativeInfinity];
    int stanceBlows;
    static readonly Tag[] StrikeTags = [Tag.Melee, Tag.Physical];

    /// <summary>Set B's stance (an id in data/content/stances.json; null or unknown: no second set). In set B when it
    /// changes, the old stance's numbers go and the new one's come in; with none she is back in set A.</summary>
    public void SetStance(string? id)
    {
        var next = Campaign ? Stances.Find(id) : null;
        if (next?.Id == StanceB?.Id) return;
        if (OnB && StanceB != null) Stats.RemoveSource($"stance:{StanceB.Id}");
        StanceB = next;
        if (OnB && next != null) Stats.AddAll(next.StatMods);
        if (next == null) OnB = false;
        Player.Hp = Math.Min(Player.Hp, MaxHp);
    }

    /// <summary>A set's swap strike: 0 set A's (her calling's), 1 set B's (its stance's).</summary>
    public SwapStrike? StrikeOf(int set) => set == 0 ? Stances.SetA(Calling) : StanceB?.Strike;

    /// <summary>Seconds until a set's swap strike is ready again (0: ready).</summary>
    public double StrikeReadyIn(int set) => Math.Max(0, strikeReady[set] - Time);

    /// <summary>Swap weapon sets (never a key: the dash, the Flare and the swap are outside the four). Her skills stay as
    /// they are; the stance's numbers come or go; the set she takes up strikes if its strike is ready. False when there is
    /// no second set, or she cannot act.</summary>
    public bool Swap()
    {
        if (!Combat || !Player.Alive || StanceB == null) return false;
        if (OnB) Stats.RemoveSource($"stance:{StanceB.Id}");
        else Stats.AddAll(StanceB.StatMods);
        OnB = !OnB;
        Swaps++;
        stanceBlows = 0;
        Player.Hp = Math.Min(Player.Hp, MaxHp);
        int set = OnB ? 1 : 0;
        var s = StrikeOf(set);
        bool struck = s != null && Time >= strikeReady[set];
        if (struck)
        {
            strikeReady[set] = Time + s!.Cooldown;
            SwapStrikes++;
            Strike(s, set);
        }
        Events.Emit(new Ev.Swap { Set = set, Stance = StanceNow?.Id ?? "", Strike = struck ? s!.Name : "", X = Player.X, Z = Player.Z });
        return true;
    }

    /// <summary>The strike around her: grown by her basic attack's rank (the first key's) as a skill grows with its own.</summary>
    void Strike(SwapStrike s, int set)
    {
        var p = Player;
        int rank = OnSlot(0)?.Rank ?? 1;
        double dmg = s.Damage * (1 + Content.Weapons.DamageStep * (rank - 1));
        string credit = set == 0 ? "swap" : $"swap:{StanceB?.Id}";
        foreach (var e in HostilesInRadius(p.X, p.Z, s.Radius))
        {
            double dx = e.X - p.X, dz = e.Z - p.Z, d = Math.Max(0.01, Math.Sqrt(dx * dx + dz * dz));
            double dealt = HitEnemy(e, dmg, School.Physical, StrikeTags, new HitOpts { Credit = credit, Knockback = s.Knockback, DirX = dx / d, DirZ = dz / d, Provoke = true });
            if (!e.Alive) continue;
            if (e.Boss) { if (s.Stagger > 0) AddStagger(e, s.Stagger); }
            else if (s.Stun > 0) ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 0, s.Stun), dealt, from: credit);
            if (s.Bleed != null) ApplyStatus(e, s.Bleed.Payload, dealt, from: credit);
        }
    }

    /// <summary>A key skill's blow landed in set B: the stance's flavor rides it (HitEnemy, after the blow's own payloads).</summary>
    void StanceBlow(Enemy e, WeaponInst w, double dealt)
    {
        if (StanceNow is not { } st || !e.Alive) return;
        var b = st.Blow;
        if (b.Ward > 0 && Player.BlockT > 0) Player.BlockT = Math.Max(0, Player.BlockT - b.Ward);
        if (++stanceBlows < Math.Max(1, b.Every)) return;
        stanceBlows = 0;
        string from = $"stance:{st.Id}";
        if (e.Boss) { if (b.Stagger > 0) AddStagger(e, b.Stagger); }
        else if (b.Stun > 0) ApplyStatus(e, new StatusPayload(StatusKind.Stun, 1, 0, b.Stun), dealt, from: from);
        if (b.Bleed != null) ApplyStatus(e, b.Bleed.Payload, dealt, from: from);
    }

    /// <summary>The blows a stance flavors: a key skill's (the campaign's four keys), never a status's tick or an auto's.</summary>
    bool StanceFlavors(in HitOpts o) => OnB && !o.Dot && o.Weapon is { } w && w.Slot >= 0 && w.Slot < KeyCount;
}

using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;

namespace SurvivorUnchained.Sim;

/* A story night lets the survivor get up again where a stage began, as she
 * stood when she came into it (docs/design/STORY_BOSSES.md 5.1). What she
 * built since then must go: the cards she took in the stage she fell in are
 * not hers to keep, or a fall would be a way to farm them.
 *
 * The build is kept as a journal of the verbs that made it (every weapon,
 * rank, evolution, honing, union and blessing, in order), so a checkpoint is
 * the journal so far and a few counters. Going back clears what those verbs
 * made and plays the journal again through the same verbs: whatever they do
 * (triggers, stats, discoveries, summons) is done again by them, and nothing
 * new added to a verb is forgotten by the restore. */

/// <summary>One verb of the build: W weapon (N its rank), R rank, H hone, E evolve (Arg the
/// branch, N 1 out of a chest), B blessing or passive, U union.</summary>
public readonly record struct BuildStep(char Op, string Id, string? Arg = null, int N = 0);

/// <summary>The survivor as she stood at a checkpoint: her build's journal, her ember and
/// what the draft owes and remembers, her health and what keeps her up.</summary>
public sealed class BuildSnapshot
{
    public List<BuildStep> Steps = new();
    public int EmberLevel, PendingLevels, GreatOwed, GreatExtra, Rerolls, Banishes, Ashes, Revives, DashCharges;
    public double EmberXp, EmberNext, Hp, Shield;
    public List<int> PendingBlessings = new();
    public List<string> Banned = new();
    public int DraftCards, RarePity, Skipped, Greats, SkillDrafts;
    public bool OwnShown;
    public Dictionary<string, int> CatalystWait = new();
}

public sealed partial class Battle
{
    /// <summary>The build as it was made (Checkpoint.cs).</summary>
    public readonly List<BuildStep> Built = new();
    /// <summary>Inside a verb that calls another (a union adds its weapon): only the outer one is the journal's.</summary>
    int building;

    void Journal(char op, string id, string? arg = null, int n = 0)
    {
        if (building == 0) Built.Add(new BuildStep(op, id, arg, n));
    }

    /// <summary>How she stands now, to come back to.</summary>
    public BuildSnapshot Snapshot()
    {
        var p = Player;
        var d = Drafting;
        return new BuildSnapshot
        {
            Steps = Built.ToList(),
            EmberLevel = EmberLevel, EmberXp = EmberXp, EmberNext = EmberNext,
            PendingLevels = PendingLevels, PendingBlessings = PendingBlessings.ToList(), GreatOwed = GreatOwed, GreatExtra = GreatExtra,
            Rerolls = Rerolls, Banishes = Banishes, Banned = BannedCards.ToList(),
            Hp = p.Hp, Shield = p.Shield, Ashes = p.Ashes, Revives = p.Revives, DashCharges = p.DashCharges,
            DraftCards = d.Cards, RarePity = d.RarePity, Skipped = d.Skipped, Greats = d.Greats, SkillDrafts = d.SkillDrafts, OwnShown = d.OwnShown,
            CatalystWait = new Dictionary<string, int>(d.CatalystWait),
        };
    }

    /// <summary>Back to how she stood at a checkpoint: what she built since goes, and she has
    /// the health and draft she had then. What the replay announces is not said again.</summary>
    public void Restore(BuildSnapshot s)
    {
        int said = Events.Pending.Count;
        foreach (var w in Weapons.ToList()) RemoveWeapon(w.Id);
        foreach (var id in Boons.Keys.ToList())
        {
            Stats.RemoveSource($"boon:{id}");
            Stats.RemoveSource($"syn:{id}");
            RemoveTriggers($"boon:{id}");
        }
        Boons.Clear();
        foreach (var id in Discoveries) RemoveTriggers($"disc:{id}");
        Discoveries.Clear();
        // What the blessings called up comes again with them.
        foreach (var e in Enemies.Living().Where(e => e.Disposition == Disposition.Ally).ToList()) Enemies.Release(e);
        Built.Clear();
        foreach (var st in s.Steps)
            switch (st.Op)
            {
                case 'W': AddWeapon(st.Id, st.N); break;
                case 'R': RankWeapon(st.Id); break;
                case 'H': Hone(st.Id); break;
                case 'E': Evolve(st.Id, st.Arg!, st.N == 1); break;
                case 'B': AddBoon(st.Id); break;
                case 'U': Unite(st.Id); break;
            }
        EmberLevel = s.EmberLevel; EmberXp = s.EmberXp; EmberNext = s.EmberNext;
        PendingLevels = s.PendingLevels;
        PendingBlessings.Clear(); PendingBlessings.AddRange(s.PendingBlessings);
        GreatOwed = s.GreatOwed; GreatExtra = s.GreatExtra;
        Rerolls = s.Rerolls; Banishes = s.Banishes;
        BannedCards.Clear(); BannedCards.UnionWith(s.Banned);
        var d = Drafting;
        d.Cards = s.DraftCards; d.RarePity = s.RarePity; d.Skipped = s.Skipped; d.Greats = s.Greats; d.SkillDrafts = s.SkillDrafts; d.OwnShown = s.OwnShown;
        d.Shown.Clear();
        d.CatalystWait.Clear();
        foreach (var (k, v) in s.CatalystWait) d.CatalystWait[k] = v;
        var p = Player;
        p.Alive = true;
        Over = null;
        p.Hp = Math.Min(s.Hp, MaxHp);
        p.Shield = s.Shield;
        p.Ashes = s.Ashes;
        p.Revives = s.Revives;
        // A rise spent is spent: going back to a checkpoint does not give it back.
        if (p.Rose > 0) p.Ashes = p.Revives = 0;
        p.DashCharges = s.DashCharges;
        p.BurnT = p.PoisonT = p.SlowT = 0;
        p.SlowF = 1;
        p.FellTo = null;
        Events.Since(said);
    }

    /// <summary>Pushed bodily (a living wall's shove): moved, not struck. It is not a blow, so it
    /// buys no moment of grace; armour answers what it hurts, as it answers bad ground.</summary>
    public void ShovePlayer(double dx, double dz, double metres, double damage, string source)
    {
        var p = Player;
        if (!p.Alive) return;
        double l = Math.Max(1e-6, Math.Sqrt(dx * dx + dz * dz));
        int steps = Math.Max(1, (int)Math.Ceiling(metres / 0.4));
        for (int i = 0; i < steps; i++)
        {
            p.X += dx / l * metres / steps;
            p.Z += dz / l * metres / steps;
            Collision.Resolve(ref p.X, ref p.Z, p.Radius, true);
        }
        p.HurtT = 0.25;
        if (damage > 0) HurtByGround(damage, School.Physical, 1, source);
    }
}

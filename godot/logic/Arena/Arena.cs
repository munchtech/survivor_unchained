using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Maps;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Arena;

/* The other half of the game: the ember arenas.
 *
 * The story is walked and talked through; its fights are fixed packs that
 * teach the survivor (character experience, levels). At its turns, and
 * where danger is marked in the world, the survivor is pulled into an
 * arena: a place made for one fight, seen from higher and further out, where
 * the ember starts again from nothing and burns against a horde that
 * thickens by the minute. At the half hour what rules the horde comes; kill
 * it and the fight is won. The arena does not end there: it goes on, harder
 * by the minute, for as long as the survivor cares to see how strong the
 * ember has made them, until they take the way out or fall (fallen after
 * the win, it is still won). The cards taken there do not come out; what
 * does is what was learned (skills discovered, to be learned in the world),
 * what was earned (experience for the time survived, the gold and gear
 * picked up), and how the story goes on (the fight won or lost). A story
 * fight lost can be taken again at the Wayfinder's table. */

/// <summary>One arena: where, against whom, how hard, and where the story
/// goes on afterward.</summary>
public sealed class ArenaSpec
{
    /// <summary>The fight this is: a story encounter's id, or 'table:N' for one of the Wayfinder's.</summary>
    public string Id = "";
    public string Name = "", Sub = "";
    public int Seed = 1;
    public int Tier = 1;
    public string Theme = "wood";
    public bool Night = true;
    /// <summary>Who fills it (Maps/MapOffers.Peoples).</summary>
    public string People = "pack";
    public List<string> Oaths = new();
    public double Minutes = 30;
    /// <summary>Where the story goes on: the zone and the spot the survivor was pulled from.</summary>
    public string ReturnZone = "waystation";
    public double ReturnX, ReturnZ, ReturnFacing;
    /// <summary>The story's outcome, as changes (JSON), when it is won and when it is lost.</summary>
    public string? OnWin, OnLose;
    /// <summary>A story fight (lost, it waits at the table to be taken again).</summary>
    public bool Story;

    public MapSpec Map => new() { Seed = Seed, Tier = Tier, Theme = Theme, Night = Night, Oaths = Oaths, Name = Name, Arena = true };
}

/// <summary>How an arena ended, and what came out of it.</summary>
public sealed record ArenaResult(ArenaSpec Spec, bool Won, double Seconds, int Kills, int EmberLevel, double Xp, double Gold,
    List<string> Discovered, int LevelsGained, bool Longest = false);

public static class Arenas
{
    /// <summary>The arena begun, for the zone that runs it (kept with the world, so a
    /// save made on the way in knows where it was going).</summary>
    public static void Begin(WorldState w, ArenaSpec spec) => w.Arena = spec;

    public static ArenaSpec? Current(WorldState w) => w.Arena;

    /// <summary>One of the Wayfinder's maps, as an arena: back to where the
    /// survivor stood at the table after.</summary>
    public static ArenaSpec FromTable(MapOffer o, string zone, double x, double z, double facing) => new()
    {
        Id = $"table:{o.Spec.Seed}", Name = o.Spec.Name, Sub = $"Tier {o.Spec.Tier} · held by {MapOffers.People(o.People).Name}",
        Seed = o.Spec.Seed, Tier = o.Spec.Tier, Theme = o.Spec.Theme, Night = o.Spec.Night, People = o.People, Oaths = o.Spec.Oaths.ToList(),
        ReturnZone = zone, ReturnX = x, ReturnZ = z, ReturnFacing = facing,
    };

    /// <summary>A story fight lost, to be taken again: the same fight, back to
    /// the table after. The story has already been told it was lost, so a
    /// second loss tells it nothing; a win still counts.</summary>
    public static ArenaSpec Again(ArenaSpec lost, string zone, double x, double z, double facing) => new()
    {
        Id = lost.Id, Name = lost.Name, Sub = lost.Sub, Seed = lost.Seed + 1, Tier = lost.Tier, Theme = lost.Theme, Night = lost.Night,
        People = lost.People, Oaths = lost.Oaths.ToList(), Minutes = lost.Minutes, Story = true, OnWin = lost.OnWin, OnLose = null,
        ReturnZone = zone, ReturnX = x, ReturnZ = z, ReturnFacing = facing,
    };

    /// <summary>Experience for the time survived (past the half hour too): more
    /// the harder the arena, a purse for the win.</summary>
    public static double XpFor(ArenaSpec spec, double seconds, bool won) =>
        Math.Round(seconds / 60 * 30 * (1 + 0.3 * (spec.Tier - 1)) + (won ? 300 * spec.Tier : 0));

    /// <summary>The skills a run discovered: every combat skill carried at the
    /// end (and what it evolved from), every passive taken.</summary>
    public static IEnumerable<string> Skills(Battle b) =>
        b.Weapons.Select(w => w.Id).Concat(b.Boons.Keys.Where(k => Content.Boons.All.TryGetValue(k, out var d) && d.Kind == Content.BoonKind.Passive));

    /// <summary>What rules the horde is dead: the fight is won, and the story is
    /// told so at once (the arena goes on; whatever happens in it now, it was won).</summary>
    public static void Won(Journey j, ArenaSpec spec)
    {
        var w = j.World;
        if (spec.OnWin != null) j.Apply(spec.OnWin);
        w.Rematches.RemoveAll(r => r.Id == spec.Id);
        w.Facts[$"arena.{spec.Id}"] = "won";
        w.Facts["arena.won"] = w.Fact("arena.won").Number + 1;
        w.Facts["arena.best"] = Math.Max(w.Fact("arena.best").Number, spec.Tier);
    }

    /// <summary>The arena is over (the way out taken, or the survivor fallen):
    /// they take out what they learned and earned; lost, the story is told so,
    /// and a story fight waits at the table.</summary>
    public static ArenaResult Finish(Journey j, Battle b, ArenaSpec spec, bool won)
    {
        var ch = j.Ch;
        double xp = XpFor(spec, b.Time, won);
        int levels = Character.GainXp(ch, xp);
        var fresh = new List<string>();
        foreach (var id in Skills(b))
            if (!ch.Discovered.Contains(id)) { ch.Discovered.Add(id); fresh.Add(id); }
        j.BankGold(b);
        var w = j.World;
        if (!won)
        {
            if (spec.OnLose != null) j.Apply(spec.OnLose);
            w.Rematches.RemoveAll(r => r.Id == spec.Id);
            if (spec.Story) w.Rematches.Add(spec);
            w.Facts[$"arena.{spec.Id}"] = "lost";
        }
        bool longest = b.Time / 60 > w.Fact("arena.longest").Number;
        if (longest) w.Facts["arena.longest"] = Math.Round(b.Time / 60, 2);
        w.Arena = null;
        return new ArenaResult(spec, won, b.Time, b.KillCount, b.EmberLevel, xp, b.GoldTotal, fresh, levels, longest);
    }
}

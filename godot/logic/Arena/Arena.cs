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
    /// <summary>Who comes at the half hour, if not what rules the people (a named
    /// foe of the story: Greymuzzle, Redcowl).</summary>
    public string? Boss, BossName, BossTitle;
    /// <summary>The boss is brought down and let go, not killed (Greymuzzle, when the story
    /// allows it: docs/STORY_BIBLE.md, "The nights").</summary>
    public bool Spare;

    /// <summary>The ground (always by night: the ember burns only in the dark).</summary>
    public MapSpec Map => new() { Seed = Seed, Tier = Tier, Theme = Theme, Night = true, Oaths = Oaths, Name = Name, Arena = true, People = People };
}

/// <summary>How an arena ended, and what came out of it.</summary>
public sealed record ArenaResult(ArenaSpec Spec, bool Won, double Seconds, int Kills, int EmberLevel, double Xp, double Gold,
    List<string> Discovered, int LevelsGained, bool Longest = false, string? Tome = null, string? Taught = null)
{
    /// <summary>What a tome won here may be inscribed with (the player chooses
    /// one: Arenas.Inscribe); empty if none was won.</summary>
    public List<string> TomeChoices { get; init; } = new();
    /// <summary>Evolutions and unions made here for the first time (now in the codex).</summary>
    public List<string> Recorded { get; init; } = new();
    /// <summary>What the tome was written with, once it has been.</summary>
    public string? Inscribed { get; set; }
    /// <summary>What the survivor carried out for the Waystation's hands (ember shards, the
    /// people's own), and what they spilled falling (docs/CRAFTING_DESIGN.md 6.1).</summary>
    public Dictionary<string, int> Carried { get; init; } = new();
    public Dictionary<string, int> Spilled { get; init; } = new();
}

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
        Seed = o.Spec.Seed, Tier = o.Spec.Tier, Theme = o.Spec.Theme, People = o.People, Oaths = o.Spec.Oaths.ToList(),
        ReturnZone = zone, ReturnX = x, ReturnZ = z, ReturnFacing = facing,
    };

    /// <summary>A story fight lost, to be taken again: the same fight, back to
    /// the table after. The story has already been told it was lost, so a
    /// second loss tells it nothing; a win still counts.</summary>
    public static ArenaSpec Again(ArenaSpec lost, string zone, double x, double z, double facing) => new()
    {
        Id = lost.Id, Name = lost.Name, Sub = lost.Sub, Seed = lost.Seed + 1, Tier = lost.Tier, Theme = lost.Theme,
        People = lost.People, Oaths = lost.Oaths.ToList(), Minutes = lost.Minutes, Story = true, OnWin = lost.OnWin, OnLose = null,
        Boss = lost.Boss, BossName = lost.BossName, BossTitle = lost.BossTitle,
        ReturnZone = zone, ReturnX = x, ReturnZ = z, ReturnFacing = facing,
    };

    /// <summary>Experience for the time survived (past the half hour too): more
    /// the harder the arena, a purse for the win.</summary>
    public static double XpFor(ArenaSpec spec, double seconds, bool won)
    {
        // A shorter night is the same night told quicker: its minutes before the boss count as a
        // table night's would, so a story night teaches as much (past the boss, real minutes).
        double end = spec.Minutes * 60, night = Math.Min(seconds, end) * 30 / spec.Minutes + Math.Max(0, seconds - end);
        return Math.Round(night / 60 * 30 * (1 + 0.3 * (spec.Tier - 1)) + (won ? 300 * spec.Tier : 0));
    }

    /// <summary>The skills a run discovered: every combat skill carried at the
    /// end (evolved or not), and the halves of any union made. Only combat
    /// skills can be learned by day, so only they are discovered.</summary>
    public static IEnumerable<string> Skills(Battle b) =>
        b.Weapons.SelectMany(w => Content.Unions.All.FirstOrDefault(u => u.Into == w.Id) is { } un ? new[] { un.A, un.B } : new[] { w.Id })
            .Where(id => Content.Weapons.All.TryGetValue(id, out var d) && d.Findable).Distinct();

    /// <summary>What the fight made that the codex keeps: its evolutions
    /// (evo:id) and unions (union:id), each with its recipe for the book.</summary>
    public static IEnumerable<string> Made(Battle b) =>
        b.Weapons.Select(w => w.Evolution is { } e ? $"evo:{e.Id}" : Content.Unions.All.FirstOrDefault(u => u.Into == w.Id) is { } un ? $"union:{un.Id}" : null)
            .Where(x => x != null).Select(x => x!);

    /// <summary>Write a tome won in an arena with one of its choices: the tome
    /// goes into the pack, ready to be read. Once only; false if it was not
    /// one of them (or the pack is full).</summary>
    public static bool Inscribe(Journey j, ArenaResult r, string id)
    {
        if (r.Inscribed != null || !r.TomeChoices.Contains(id) || !j.GiveItem(SkillBook.Tome(id), 1)) return false;
        r.Inscribed = id;
        return true;
    }

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
    public static ArenaResult Finish(Journey j, Battle b, ArenaSpec spec, bool won, string? killer = null)
    {
        var ch = j.Ch;
        double xp = XpFor(spec, b.Time, won);
        var fresh = new List<string>();
        foreach (var id in Skills(b))
            if (!ch.Discovered.Contains(id)) { ch.Discovered.Add(id); fresh.Add(id); }
        int levels = Character.GainXp(ch, xp);
        string? taught = levels > 0 ? j.Grew() : null;
        // A story fight won gives a tome (a table's, now and then): blank, to be
        // written with one of what burned here, the survivor's choice of up to three.
        var choices = new List<string>();
        if (won && (spec.Story || b.Rng.Next() < 0.35))
            choices = Skills(b).Where(id => SkillBook.CanLearn(ch, id))
                .OrderByDescending(id => b.Weapons.FirstOrDefault(w => w.Id == id)?.Rank ?? 8).Take(3).ToList();
        // What was made here for the first time goes in the codex, recipe and all.
        var recorded = new List<string>();
        foreach (var m in Made(b))
            if (!j.World.Codex.Contains(m)) { j.World.Codex.Add(m); recorded.Add(m); }
        foreach (var m in Made(b).Where(m => m.StartsWith("evo:")))
            if (!ch.Stats.Evolutions.Contains(m[4..])) ch.Stats.Evolutions.Add(m[4..]);
        j.BankGold(b);
        // What the night leaves in the survivor's fist, for the Waystation's hands: walked
        // out, all of it; fallen, half.
        var carry = Crafting.Night(spec.People, spec.Tier, spec.Story, b.EmberLevel, Math.Max(0, b.Time / 60 - spec.Minutes), won, !b.Player.Alive, b.ChampionsByFamily);
        j.Carry(carry, spec.Name);
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
        // The last night, for the town to talk about (docs/EXPERIENCE_AUDIT.md: Hades' house
        // reacts to every run; ours said one line). The story writes what is said of it.
        w.Facts["arena.last.people"] = spec.People;
        w.Facts["arena.last.won"] = won;
        w.Facts["arena.last.fell"] = !b.Player.Alive;
        w.Facts["arena.last.story"] = spec.Story;
        w.Facts["arena.last.tier"] = spec.Tier;
        w.Facts["arena.last.minutes"] = Math.Round(b.Time / 60, 1);
        w.Facts["arena.last.past"] = Math.Round(Math.Max(0, b.Time / 60 - spec.Minutes), 1);
        w.Facts["arena.last.day"] = w.Day;
        w.Facts["arena.last.longest"] = longest;
        w.Facts["arena.last.killer"] = !b.Player.Alive && killer != null ? killer : null;
        if (!b.Player.Alive) w.Facts["arena.fell"] = w.Fact("arena.fell").Number + 1;
        w.Facts["arena.nights"] = w.Fact("arena.nights").Number + 1;
        w.Arena = null;
        return new ArenaResult(spec, won, b.Time, b.KillCount, b.EmberLevel, xp, b.GoldTotal, fresh, levels, longest, null, taught)
        {
            TomeChoices = choices, Recorded = recorded, Carried = carry.Kept, Spilled = carry.Spilled,
        };
    }
}

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.World;

/* The world goes on without you.
 *
 * A day passes when the survivor rests. Then, in order:
 *
 *   1. scheduled consequences come due ("the survivors die on day 5 if
 *      nobody came");
 *   2. every daily rule is checked - quest escalations, the blight spreading
 *      or receding, the Kerchiefs raiding a road nobody guards - and fires if
 *      its condition holds;
 *   3. gossip moves one step along who-talks-to-whom: an event someone knows
 *      has a chance to reach each person they talk to, and when it arrives it
 *      changes how that person feels about you;
 *   4. conditions on the survivor heal (or worsen);
 *   5. whatever the survivor would notice is written into the morning
 *      report the inn gives them.
 *
 * The rules are content (data/content/rules.json), not code. */

public sealed class DailyRule
{
    public string Id = "";
    /// <summary>Checked each new day.</summary>
    public Cond When = new();
    [JsonConverter(typeof(OneOrMany<Change>))] public List<Change> Effect = new();
    /// <summary>Fire at most once.</summary>
    public bool Once;
    /// <summary>What the survivor hears about it in the morning, if anything.</summary>
    public string? Report;
}

public sealed record Heard(string Npc, string Event);
public sealed record DayReport(int Day, List<string> Lines, List<Heard> Heard);

public static class Simulation
{
    sealed class File
    {
        public List<DailyRule> Rules = new();
        public Dictionary<string, List<string>> Social = new();
        public Change CaravanSettle = new();
    }

    static File? data;
    static File D => data ??= Json.Parse<File>(Json.ReadContent("rules.json"));

    public static List<DailyRule> DailyRules => D.Rules;
    /// <summary>Who talks to whom: how news travels. The innkeeper hears everything.</summary>
    public static Dictionary<string, List<string>> Social => D.Social;
    /// <summary>When both the teamsters' fate and the cargo's are known, the quest is settled.</summary>
    public static Change CaravanSettle => D.CaravanSettle;

    public static DayReport AdvanceDay(Ctx ctx, Func<double> rng, List<DailyRule>? rules = null, Dictionary<string, List<string>>? social = null)
    {
        rules ??= DailyRules;
        social ??= Social;
        var w = ctx.World;
        w.Day++;
        w.Time = TimeOfDay.Dawn;
        var lines = new List<string>();

        // 1. What was scheduled for today.
        var due = w.Scheduled.Where(s => s.Day <= w.Day).ToList();
        w.Scheduled = w.Scheduled.Where(s => s.Day > w.Day).ToList();
        foreach (var s in due) World.Rules.Apply(s.Effect, ctx);

        // 2. The world's own agendas.
        var firedStr = w.Fact("_rules.fired").Str;
        var fired = string.IsNullOrEmpty(firedStr) ? new List<string>() : firedStr.Split(',').ToList();
        foreach (var r in rules)
        {
            if (r.Once && fired.Contains(r.Id)) continue;
            if (!World.Rules.Test(r.When, ctx)) continue;
            World.Rules.Apply(r.Effect, ctx);
            if (r.Once) fired.Add(r.Id);
            if (r.Report != null) lines.Add(r.Report);
        }
        w.Facts["_rules.fired"] = string.Join(",", fired);

        // 3. Gossip: one step along the links.
        var heard = new List<Heard>();
        var spreading = w.History.Where(h => h.Spread > 0).ToList();
        foreach (var (who, circle) in social)
        {
            var me = w.Npc(who);
            if (!me.Alive) continue;
            foreach (var ev in spreading)
            {
                if (me.Memories.Contains(ev.Id)) continue;
                bool told = circle.Any(o => w.Npc(o).Memories.Contains(ev.Id));
                double p = told ? 0.45 * ev.Spread : ev.Spread >= 2 ? 0.15 : 0;
                if (p > 0 && rng() < p && World.Rules.Witness(w, who, ev)) heard.Add(new Heard(who, ev.Id));
            }
        }

        // 4. The survivor's conditions.
        var ch = ctx.Ch;
        bool hardy = ch.Traits.Contains("iron_constitution");
        foreach (var c in ch.Conditions) c.Days -= hardy && c.Id == ConditionId.Wounded ? 2 : 1;
        var healed = ch.Conditions.Where(c => c.Days <= 0).ToList();
        ch.Conditions.RemoveAll(c => c.Days <= 0);
        foreach (var c in healed) if (c.Id == ConditionId.Wounded) lines.Add("Your wounds have closed.");
        ch.Conditions.Add(new Condition { Id = ConditionId.Rested, Days = 1 });

        return new DayReport(w.Day, lines, heard);
    }

    /// <summary>Evening falls: the time of day moves on without a full day passing.</summary>
    public static void PassTime(Ctx ctx, TimeOfDay to) => ctx.World.Time = to;
}

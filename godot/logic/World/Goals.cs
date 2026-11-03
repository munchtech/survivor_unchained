using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Core;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.World;

/* Where to go next, as data (data/content/goals.json): one entry gives the tracker its line, the
 * minimap and the full map a pin, and the screen a waypoint and an edge arrow. The pin is an
 * Interactable of the zone; the goal lives while that interactable does. The next town goal is
 * one JSON entry. */

public sealed class GoalStep { public string Text = ""; public bool Optional; }

public sealed class GoalDef
{
    public string Id = "", Zone = "", Pin = "", Title = "", Label = "", Glyph = "", Color = "#e8c070";
    /// <summary>Whether the goal exists at all (pin and line).</summary>
    public Cond? When;
    /// <summary>Whether its tracker line shows (the pin shows without it).</summary>
    public Cond? LineWhen;
    public List<GoalStep> Steps = new();
    /// <summary>The Tracked block to put the steps into, at index At; none: a block of its own.</summary>
    public string? Into;
    public int At = 1;
    public bool Edge = true;
    /// <summary>Metres: the on-screen pin hides when she is closer than this.</summary>
    public double Near = 4;
    /// <summary>Metres: the on-screen pin fades out from Fade + 2 to Fade; none: Near.</summary>
    public double? Fade;
    /// <summary>A block of its own goes to the top of the tracker (after "tonight"), not the end.</summary>
    public bool First;
}

public sealed record ActiveGoal(GoalDef Def, double X, double Z, double R, bool Line);

public static class Goals
{
    static List<GoalDef>? all;
    public static List<GoalDef> All => all ??= Json.Parse<List<GoalDef>>(Json.ReadContent("goals.json"));

    public static List<ActiveGoal> Active(IEnumerable<GoalDef> defs, Ctx ctx, string zoneId, IEnumerable<Interactable> interactables)
    {
        var o = new List<ActiveGoal>();
        var things = interactables.ToList();
        foreach (var d in defs)
        {
            if (d.Zone != zoneId || !Rules.Test(d.When, ctx)) continue;
            var pin = things.FirstOrDefault(i => i.Id == d.Pin && (i.When == null || i.When()));
            if (pin == null) continue;
            o.Add(new ActiveGoal(d, pin.X, pin.Z, pin.R, Rules.Test(d.LineWhen, ctx)));
        }
        return o;
    }

    static readonly Regex Token = new(@"\{(\w+)\}");

    public static List<Tracked> Merge(List<Tracked> list, List<ActiveGoal> active, Func<string, string?> word)
    {
        var o = new List<Tracked>(list);
        string Say(string text) => Token.Replace(text, m => word(m.Groups[1].Value) ?? m.Groups[1].Value);
        foreach (var a in active.Where(a => a.Line))
        {
            var steps = a.Def.Steps.Select(s => new Step(Say(s.Text), s.Optional)).ToList();
            int i = a.Def.Into == null ? -1 : o.FindIndex(t => t.Id == a.Def.Into);
            if (i >= 0)
            {
                var into = new List<Step>(o[i].Steps);
                into.InsertRange(Math.Clamp(a.Def.At, 0, into.Count), steps);
                o[i] = o[i] with { Steps = into };
            }
            else
            {
                var block = new Tracked(a.Def.Id, a.Def.Title, TrackTone.Main, steps);
                if (a.Def.First) o.Insert(o.FindIndex(t => t.Id == "tonight") + 1, block);
                else o.Add(block);
            }
        }
        return o;
    }
}

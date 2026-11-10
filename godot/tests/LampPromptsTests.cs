using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Ui;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>Read-only (the arena): no Lamps prompt offers an action that only gets denied.</summary>
public class LampPromptsTests
{
    static readonly string[] DenyOnly = ["Light my way", "Light", "Light it", "Light the path", "Put out", "Hold: put out", "Take it up"];

    [Theory]
    [InlineData(false, false)] [InlineData(false, true)] [InlineData(true, false)] [InlineData(true, true)]
    public void ReadOnlyHidesDeniedPrompts(bool pad, bool wide)
    {
        var rows = new List<IEnumerable<(string, string)>> { LampPrompts.HeaderRow(pad, wide, true), LampPrompts.FootRow(pad, false, true, false), LampPrompts.FootRow(pad, true, true, false) };
        rows.AddRange(LampPrompts.WideFootRows(pad, false, true, false));
        rows.AddRange(LampPrompts.WideFootRows(pad, true, true, false));
        foreach (var r in rows)
            Assert.DoesNotContain(r, p => DenyOnly.Contains(p.Item2) || p.Item2 == "Plan");
        Assert.Equal(pad ? ["Find", "Open wide"] : new[] { "Find", "Open wide" }, LampPrompts.HeaderRow(pad, false, true).Select(p => p.Item2));
        Assert.Equal(pad ? ["Home", "Open wide"] : new[] { "Home", "Find", "Open wide" }, LampPrompts.FootRow(pad, false, true, true).Select(p => p.Item2));
    }

    [Fact]
    public void ReadOnlyWickKeepsPlanWhereItWorks()
    {
        Assert.Equal(["Plan", "Light my way", "Board"], LampPrompts.FootRow(false, true, true, true).Select(p => p.Item2));
        Assert.Equal(["Board"], LampPrompts.FootRow(false, true, true, false).Select(p => p.Item2));
    }

    [Fact]
    public void NotReadOnlyRowsAreUnchanged()
    {
        Assert.Equal(["Space Light my way", "F Find", "Z Open wide"], LampPrompts.HeaderRow(false, false, false).Select(p => p.Item1 + " " + p.Item2));
        Assert.Equal(["Y Light my way", "D-pad up Find", "B Close"], LampPrompts.HeaderRow(true, true, false).Select(p => p.Item1 + " " + p.Item2));
        Assert.Equal(["Click Light", "Space Light my way", "H Home", "F Find", "Z Open wide"], LampPrompts.FootRow(false, false, false, true).Select(p => p.Item1 + " " + p.Item2));
        Assert.Equal(["A Light", "Y Light my way", "L3 Home", "R3 Open wide"], LampPrompts.FootRow(true, false, false, true).Select(p => p.Item1 + " " + p.Item2));
        Assert.Equal(["Click Plan", "Space Light my way", "Tab Board"], LampPrompts.FootRow(false, true, false, false).Select(p => p.Item1 + " " + p.Item2));
        Assert.Equal(3, LampPrompts.WideFootRows(false, true, false, false).Count);
    }
}

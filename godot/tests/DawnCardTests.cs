using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Play;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The dawn's card (N24): what the ember takes, what she keeps, in short lines and American words.</summary>
public class DawnCardTests
{
    static readonly Regex British = new(@"\b(colour|armour|honour|favour|grey|centre|metre|realise|realising|recognise|learnt|burnt|spelt|dreamt|whilst|amongst|travelled|travelling|lustre|sombre|defence|offence|odour|harbour|neighbour)\b", RegexOptions.IgnoreCase);

    [Fact]
    public void The_card_names_the_nights_skills_and_what_she_keeps()
    {
        var c = DawnCard.Build(["Ember Lance", "Cinderwake"], 5);
        Assert.Equal("The ember goes out", c.Title);
        Assert.Equal("The ember takes", c.TakesHead);
        Assert.Equal(["Ember Lance", "Cinderwake", "The Lamps' light"], c.Takes);
        Assert.Equal("You keep", c.KeepsHead);
        Assert.Equal(["Your gear", "Your gold", "Your traits", "Level 5"], c.Keeps);
        Assert.Equal("When the dark comes again, it will burn again.", c.Last);
        Assert.Equal("Click to go on", c.Go);
    }

    [Fact]
    public void A_long_night_is_counted_and_no_level_is_left_off()
    {
        var c = DawnCard.Build(["A", "B", "C", "D", "E", "F", "G"], null);
        Assert.Equal(["A", "B", "C", "And 4 more", "The Lamps' light"], c.Takes);
        Assert.True(c.Takes.Count <= DawnCard.MaxLines);
        Assert.DoesNotContain(c.Keeps, k => k.StartsWith("Level"));
        Assert.Equal(["The Lamps' light"], DawnCard.Build([], null).Takes);
    }

    [Fact]
    public void Its_lines_are_short_and_American()
    {
        var c = DawnCard.Build(["Ember Lance"], 3);
        foreach (var line in c.Takes.Concat(c.Keeps).Append(c.TakesHead).Append(c.KeepsHead))
            Assert.True(line.Split(' ').Length <= 4, line);
        foreach (var w in c.Words()) Assert.False(British.IsMatch(w), w);
    }
}

using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The credits that ship (Content/Credits.cs): made from the ledger,
/// public/assets/CREDITS.md, and never behind it. data/credits.json is what
/// the game shows; licences/CREDITS.txt goes beside the executable. Both are
/// written from the ledger with WRITE_CREDITS=1 and checked against it
/// otherwise, so an asset fetched and credited is a failing test until it is
/// credited in the game too.</summary>
public class CreditsTests
{
    static readonly string Godot = Path.GetFullPath(Path.Combine(DataFiles.Dir, ".."));
    static readonly string Ledger = Path.GetFullPath(Path.Combine(Godot, "..", "public", "assets", "CREDITS.md"));
    static readonly string Json_ = Path.Combine(DataFiles.Dir, "credits.json");
    static readonly string Txt = Path.Combine(Godot, "licences", "CREDITS.txt");

    static string Md => File.ReadAllText(Ledger);
    static CreditsBook Book => Credits.Parse(Md);
    static string Norm(string s) => s.Replace("\r\n", "\n");

    [Fact]
    public void The_shipped_credits_are_the_ledgers()
    {
        var book = Book;
        string json = Credits.Json(book), txt = Credits.Text(book);
        if (Environment.GetEnvironmentVariable("WRITE_CREDITS") == "1")
        {
            File.WriteAllText(Json_, json);
            File.WriteAllText(Txt, txt);
        }
        const string how = "the credits are behind public/assets/CREDITS.md: run WRITE_CREDITS=1 dotnet test --filter CreditsTests in godot/tests, read the diff, and commit both files";
        Assert.True(File.Exists(Json_) && Norm(File.ReadAllText(Json_)) == Norm(json), "data/credits.json: " + how);
        Assert.True(File.Exists(Txt) && Norm(File.ReadAllText(Txt)) == Norm(txt), "licences/CREDITS.txt: " + how);
    }

    [Fact]
    public void Every_link_in_the_ledger_is_credited()
    {
        // A line a fetch tool appended somewhere the credits do not read is caught here.
        var shipped = File.ReadAllText(Json_);
        var missing = Regex.Matches(Md, @"https?://[^\s,;()`]+").Select(m => m.Value.TrimEnd('.', ':')).Distinct()
            .Where(u => !shipped.Contains(u)).ToList();
        Assert.True(missing.Count == 0, "not in the credits (move its line into its section of CREDITS.md): " + string.Join(", ", missing));
    }

    [Fact]
    public void Nothing_of_the_workshop_ships()
    {
        // Paths, the fetch tools and what is under legal review stay in the ledger; data-miners read the .pck.
        foreach (var text in new[] { File.ReadAllText(Json_), File.ReadAllText(Txt) })
            foreach (var bad in new[] { "`", "->", "tools/", "godot/", "public/", "docs/", "under review", "PE-0", "CR-0", ".glb", ".py", ".mjs", "**", "personal use" })
                Assert.False(text.Contains(bad, StringComparison.OrdinalIgnoreCase), $"'{bad}' would ship in the credits");
    }

    [Fact]
    public void Each_work_under_CC_BY_has_its_creator_link_and_licence()
    {
        var by = Book.Sections.Single(s => s.Licence == "CC BY 4.0");
        var works = by.Groups.SelectMany(g => g.Entries).ToList();
        Assert.True(works.Count >= 15, $"only {works.Count} works under CC BY");
        foreach (var w in works)
        {
            Assert.NotEmpty(w.Links);
            Assert.Contains("by ", (w.Name + " " + w.Text));
        }
        var wolf = works.Single(w => w.Name == "Animated Wolf Scene");
        Assert.Equal("by Roo", wolf.Text);
        Assert.Equal(new[] { "https://sketchfab.com/roo3d", "https://sketchfab.com/3d-models/animated-wolf-scene-5d55506494e5460eaadf04370e07cd5c" }, wolf.Links);
        var mace = works.Single(w => w.Name == "Medieval Mace");
        Assert.Equal("designed by Kama Modeling; modelled and textured by Yavuz Temel", mace.Text);
        // A change on the work's own line stays with it, and the whole kind's are on its group.
        Assert.Contains(works.Single(w => w.Name == "Goblin Ghoul").Lines, l => l.StartsWith("Changes: the lamplings' hats"));
        Assert.Contains(by.Groups.Single(g => g.Title == "Weapons, from Sketchfab").Notes, n => n.StartsWith("Changes for every weapon: turned and scaled to one grip convention in code; photographed"));
        Assert.Contains("Modified: turned and scaled", Credits.Text(Book));
    }

    [Fact]
    public void The_ledger_reads_as_the_player_should()
    {
        var book = Book;
        Assert.StartsWith("Survivor Unchained is made by Munchtech.", book.Intro[0]);
        Assert.Equal(new[] { "Engine and runtime", "Typefaces", "Used under Creative Commons Attribution 4.0", "Used under service terms or model licences", "Third-party works under CC0", "Made with AI tools", "Made for the game" },
            book.Sections.Select(s => s.Short));
        var godot = book.Sections[0].Groups[0].Entries[0];
        Assert.Equal("Godot Engine", godot.Name);
        Assert.Contains("https://godotengine.org/license", godot.Links);
        // Public-domain sources are groups of the public-domain section, not sections of their own.
        var cc0 = book.Sections.Single(s => s.Short == "Third-party works under CC0");
        Assert.Contains(cc0.Groups, g => g.Title == "Poly Haven models");
        Assert.Contains(cc0.Groups, g => g.Title == "ambientCG");
        Assert.Contains(cc0.Groups, g => g.Title == "The Verge's ground" && g.Sub);
        Assert.Contains(cc0.Groups.Single(g => g.Title == "Kenney").Entries, e => e.Links.Contains("https://kenney.nl/assets/rpg-audio"));
        // The web game's own packages are not this game's.
        Assert.DoesNotContain(book.Sections, s => s.Title.Contains("web game"));
    }

    [Fact]
    public void A_line_a_fetch_tool_appends_lands_in_its_section()
    {
        var md = Md + "- \"Iron Helm\" by Smith (https://sketchfab.com/smith), CC Attribution: https://sketchfab.com/3d-models/iron-helm-0123 -> public/assets/props/helm.glb\n";
        var by = Credits.Parse(md).Sections.Single(s => s.Licence == "CC BY 4.0");
        var helm = by.Groups.Single(g => g.Title == "More from Sketchfab").Entries.Single();
        Assert.Equal("Iron Helm", helm.Name);
        Assert.Equal("https://sketchfab.com/3d-models/iron-helm-0123", helm.Links[^1]);
    }

    [Fact]
    public void The_licence_texts_ship_beside_the_game()
    {
        foreach (var (file, _) in Credits.Texts)
            Assert.True(new FileInfo(Path.Combine(Godot, "licences", file)) is { Exists: true, Length: > 500 }, file);
        // In the pack too, so the game can show them; tools/godot/export.sh copies the folder beside the executable.
        var presets = File.ReadAllText(Path.Combine(Godot, "export_presets.cfg"));
        Assert.Equal(3, Regex.Matches(presets, @"include_filter=""[^""]*licences/\*").Count);
        Assert.Contains("licences", File.ReadAllText(Path.Combine(Godot, "..", "tools", "godot", "export.sh")));
    }
}

using System;
using System.Collections;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text;
using SurvivorUnchained.Content;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The combat skills live in data/content/skills.json: the file loads
/// whole, every name in it resolves, and writing it back changes nothing (so
/// a hand edit and the writer never disagree about the format).</summary>
public class SkillsDataTests
{
    [Fact]
    public void Counts()
    {
        Assert.Equal(26, Weapons.Pool.Length);
        Assert.Equal(52, Weapons.Pool.Sum(id => Weapons.All[id].Evolutions.Length));
        Assert.Equal(9, Unions.All.Length);
        Assert.Equal(Weapons.Pool.Length + Unions.All.Length, Weapons.All.Count);
    }

    [Fact]
    public void NamesResolve()
    {
        var passives = Boons.All.Values.Where(b => b.Kind == BoonKind.Passive).Select(b => b.Id).ToHashSet();
        foreach (var w in Weapons.All.Values)
            foreach (var e in w.Evolutions)
            {
                Assert.NotEmpty(e.Catalysts);
                foreach (var c in e.Catalysts) Assert.True(passives.Contains(c), $"{w.Id}/{e.Id}: no passive '{c}'");
            }
        foreach (var u in Unions.All)
        {
            foreach (var part in new[] { u.A, u.B })
                Assert.True(Weapons.All.TryGetValue(part, out var p) && p.Findable && p.Evolutions.Length > 0, $"{u.Id}: '{part}' is not an evolving skill");
            Assert.True(Weapons.All.TryGetValue(u.Into, out var into) && !into.Findable, $"{u.Id}: '{u.Into}' is not a union weapon");
        }
        var ids = Weapons.All.Values.SelectMany(w => w.Evolutions.Select(e => e.Id).Prepend(w.Id)).ToList();
        Assert.Equal(ids.Count, ids.Distinct().Count());
    }

    [Fact]
    public void RoundTripIsStable()
    {
        var once = SkillsJson.Parse(File.ReadAllText(Path.Combine(SurvivorUnchained.Core.DataFiles.Dir, "content", "skills.json")));
        string written = SkillsJson.Write(once);
        // The writer is a fixed point (a tuning script may move a number and so a line break; that is fine).
        Assert.Equal(written, SkillsJson.Write(SkillsJson.Parse(written)));
        Assert.Equal(Dump(once), Dump(SkillsJson.Parse(written)));
        Assert.Equal(Dump(once), Dump(new SkillsFile { Skills = Weapons.All.Values.ToList(), Unions = Unions.All.ToList() }));
    }

    /// <summary>SU_SKILLS_EXPORT=PATH: the loaded defs written back out in the
    /// writer's layout (how skills.json was first made from the C# defs; now a
    /// reformat after hand edits).</summary>
    [ProbeFact("SU_SKILLS_EXPORT")]
    public void Export() =>
        File.WriteAllText(Environment.GetEnvironmentVariable("SU_SKILLS_EXPORT")!,
            SkillsJson.Write(new SkillsFile { Skills = Weapons.All.Values.ToList(), Unions = Unions.All.ToList() }));

    /// <summary>SU_SKILLS_DUMP=PATH: every field of the loaded defs, to text (the
    /// refactor's before/after check).</summary>
    [ProbeFact("SU_SKILLS_DUMP")]
    public void DumpDefs()
    {
        var sb = new StringBuilder(Dump(new SkillsFile { Skills = Weapons.All.Values.ToList(), Unions = Unions.All.ToList() }));
        sb.Append("keys ").AppendLine(string.Join(",", Weapons.All.Keys));
        sb.Append("pool ").AppendLine(string.Join(",", Weapons.Pool));
        sb.Append("unionsById ").AppendLine(string.Join(",", Unions.ById.Keys));
        File.WriteAllText(Environment.GetEnvironmentVariable("SU_SKILLS_DUMP")!, sb.ToString());
    }

    /// <summary>Every public field and property, depth first, one per line.</summary>
    public static string Dump(object root)
    {
        var sb = new StringBuilder();
        void Go(string path, object? v)
        {
            switch (v)
            {
                case null: sb.Append(path).AppendLine(" = null"); return;
                case string s: sb.Append(path).Append(" = \"").Append(s).AppendLine("\""); return;
                case double d: sb.Append(path).Append(" = ").AppendLine(d.ToString("R", CultureInfo.InvariantCulture)); return;
                case bool or int or Enum: sb.Append(path).Append(" = ").AppendLine(Convert.ToString(v, CultureInfo.InvariantCulture)); return;
                case IEnumerable list:
                    int i = 0;
                    sb.Append(path).Append(" : ").AppendLine(v.GetType().Name);
                    foreach (var x in list) Go($"{path}[{i++}]", x);
                    sb.Append(path).Append(" count ").AppendLine(i.ToString());
                    return;
            }
            var t = v.GetType();
            sb.Append(path).Append(" : ").AppendLine(t.FullName);
            foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.Instance)) Go($"{path}.{f.Name}", f.GetValue(v));
            foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
                if (p.GetIndexParameters().Length == 0 && p.Name != "EqualityContract") Go($"{path}.{p.Name}", p.GetValue(v));
        }
        Go("file", root);
        return sb.ToString();
    }
}

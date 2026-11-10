using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using SurvivorUnchained.Look;
using Xunit;

namespace SurvivorUnchained.Tests;

/// <summary>The material library (data/look/materials.json): the file reads, its rules classify, and every adopting
/// shader's CEL_* defines equal its class's numbers.</summary>
public class MaterialLibraryTests
{
    static string Root()
    {
        var d = new DirectoryInfo(AppContext.BaseDirectory);
        while (d != null && !File.Exists(Path.Combine(d.FullName, "project.godot"))) d = d.Parent;
        return d?.FullName ?? Directory.GetCurrentDirectory();
    }

    static MaterialLibrary Real() => MaterialLibrary.Parse(File.ReadAllText(Path.Combine(Root(), "data", "look", "materials.json")));

    [Fact]
    public void ClassesAreWellFormed()
    {
        var lib = Real();
        Assert.NotEmpty(lib.Classes);
        foreach (var (name, c) in lib.Classes)
        {
            Assert.False(string.IsNullOrWhiteSpace(c.From), name + " has no from");
            Assert.Equal(4, c.Cel.Band.Length);
            Assert.Equal(4, c.Cel.Mid.Length);
            Assert.Equal(4, c.Cel.Spec.Length);
            Assert.InRange(c.Cel.Ink, 0, 3);
        }
    }

    /// <summary>(B2r2) Every class measured on a board carries both colors: lit (as painted) and albedo (its light divided out).</summary>
    [Fact]
    public void MeasuredClassesCarryLitAndAlbedo()
    {
        var lib = Real();
        foreach (var (name, c) in lib.Classes)
            Assert.True((c.Mid == null) == (c.LitMid == null), $"{name}: lit {c.LitMid ?? "none"} but albedo {c.Mid ?? "none"}");
        Assert.True(lib.Classes.Values.Count(c => c.Mid != null) >= 20, "fewer than 20 classes have an albedo");
    }

    [Fact]
    public void ReferencesResolve()
    {
        var lib = Real();
        Assert.True(lib.Classes.ContainsKey(lib.Fallback), "fallback " + lib.Fallback);
        foreach (var r in lib.Assign) Assert.True(lib.Classes.ContainsKey(r.Class), "assign class " + r.Class);
        foreach (var (k, v) in lib.Shaders) Assert.True(lib.Classes.ContainsKey(v), $"shader {k} class {v}");
    }

    [Theory]
    [InlineData("res://shaders/person.gdshader", "Body", null, "folk_skin")]
    [InlineData("res://shaders/kit.gdshader", "RoundTiles", null, "roof")]
    [InlineData(null, "Stone_Own_Spruce", null, "rock")]
    [InlineData(null, "Leaves_OwnAlder", null, "foliage")]
    [InlineData(null, "Barrel_Wood", null, "plank")]
    [InlineData(null, "xyz", null, null)]
    public void ClassFor(string? shader, string? mat, string? path, string? want) =>
        Assert.Equal(want, Real().ClassFor(shader, mat, path));

    [Fact]
    public void ExcludeHerAndWater()
    {
        var lib = Real();
        Assert.True(lib.Excluded("res://shaders/heroine_skin.gdshader", null));
        Assert.True(lib.Excluded(null, "heroine_eye"));
        Assert.False(lib.Excluded("res://shaders/kit.gdshader", "Wall"));
    }

    // ---- the fallbacks test: each shader's CEL_* defines equal its class ----

    sealed class Pre
    {
        public readonly Dictionary<string, string> Defs = new();
        readonly string _root;
        public Pre(string root, string? symbol) { _root = root; if (symbol != null) Defs[symbol] = ""; }

        public void Run(string resPath)
        {
            var file = Path.Combine(_root, resPath.Substring("res://".Length).Replace('/', Path.DirectorySeparatorChar));
            var stack = new Stack<(bool Parent, bool Taken)>();
            bool active = true;
            foreach (var raw in File.ReadAllLines(file))
            {
                var line = Regex.Replace(raw, "(?<!:)//.*$", "").Trim();
                if (!line.StartsWith('#')) continue;
                var m = Regex.Match(line, @"^#\s*(\w+)\s*(.*)$");
                if (!m.Success) continue;
                string d = m.Groups[1].Value, rest = m.Groups[2].Value.Trim();
                switch (d)
                {
                    case "ifdef": active = Push(active, Defs.ContainsKey(rest), stack); break;
                    case "ifndef": active = Push(active, !Defs.ContainsKey(rest), stack); break;
                    case "if": active = Push(active, Eval(rest), stack); break;
                    case "else":
                        {
                            var t = stack.Pop(); bool a = t.Parent && !t.Taken;
                            stack.Push((t.Parent, true)); active = a; break;
                        }
                    case "endif":
                        { var t = stack.Pop(); active = t.Parent; break; }
                    case "include" when active:
                        { var im = Regex.Match(rest, "\"(res://[^\"]+)\""); if (im.Success) Run(im.Groups[1].Value); break; }
                    case "define" when active:
                        {
                            var dm = Regex.Match(rest, @"^(\w+)\s*(.*)$");
                            if (dm.Success) Defs[dm.Groups[1].Value] = dm.Groups[2].Value.Trim();
                            break;
                        }
                    case "undef" when active: Defs.Remove(rest); break;
                }
            }
        }

        static bool Push(bool parent, bool cond, Stack<(bool Parent, bool Taken)> stack)
        {
            bool take = parent && cond;
            stack.Push((parent, take));
            return take;
        }

        bool Eval(string expr) =>
            expr.Split("||").Any(or => or.Split("&&").All(t =>
            {
                t = t.Trim(); bool neg = t.StartsWith('!'); if (neg) t = t.Substring(1).Trim();
                var dm = Regex.Match(t, @"^defined\s*\(?\s*(\w+)\s*\)?$");
                bool v = dm.Success && Defs.ContainsKey(dm.Groups[1].Value);
                return neg ? !v : v;
            }));
    }

    static float[]? Nums(string? v)
    {
        if (v == null) return null;
        var ms = Regex.Matches(Regex.Replace(v, @"vec\d", ""), @"-?\d+\.?\d*(?:[eE][-+]?\d+)?");
        return ms.Select(x => float.Parse(x.Value, CultureInfo.InvariantCulture)).ToArray();
    }

    [Fact]
    public void ShaderFallbacksEqualTheirClass()
    {
        var lib = Real(); var root = Root(); var fails = new List<string>();
        foreach (var (key, cls) in lib.Shaders)
        {
            var hash = key.IndexOf('#');
            var path = hash >= 0 ? key.Substring(0, hash) : key;
            var sym = hash >= 0 ? key.Substring(hash + 1) : null;
            if (!File.Exists(Path.Combine(root, path.Substring("res://".Length).Replace('/', Path.DirectorySeparatorChar))))
            { fails.Add($"{key}: missing file"); continue; }
            var pre = new Pre(root, sym); pre.Run(path);
            var c = lib.Classes[cls];

            void Vec(string def, float[] want)
            {
                var got = pre.Defs.TryGetValue(def, out var s) ? Nums(s) : null;
                if (got == null || got.Length != want.Length || got.Zip(want).Any(p => Math.Abs(p.First - p.Second) > 1e-4))
                    fails.Add($"{key}: {def} expected [{string.Join(", ", want)}] ({cls}) found {(got == null ? "undefined" : "[" + string.Join(", ", got) + "]")}");
            }

            Vec("CEL_BAND", c.Cel.Band); Vec("CEL_MID", c.Cel.Mid); Vec("CEL_SPEC", c.Cel.Spec);
            Vec("CEL_FORM", new[] { c.Cel.Form }); Vec("CEL_NMAP", new[] { c.Cel.Nmap });
            var ink = pre.Defs.TryGetValue("CEL_INK", out var iv) ? Nums(iv) : null;
            if (ink == null || ink.Length != 1 || (int)ink[0] != c.Cel.Ink)
                fails.Add($"{key}: CEL_INK expected {c.Cel.Ink} ({cls}) found {(ink == null ? "undefined" : ink[0].ToString(CultureInfo.InvariantCulture))}");
            bool noRim = pre.Defs.ContainsKey("CEL_NO_RIM");
            if (noRim != (c.Cel.RimK == 0f))
                fails.Add($"{key}: CEL_NO_RIM {(noRim ? "defined" : "not defined")} but class {cls} rim_k is {c.Cel.RimK}");
            if (c.Edge != null) Vec("CEL_CROWD_EDGE", c.Edge);
        }
        Assert.True(fails.Count == 0, fails.Count + " mismatches:\n" + string.Join("\n", fails));
    }
}

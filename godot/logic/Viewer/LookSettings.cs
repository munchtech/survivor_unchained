using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace SurvivorUnchained.Viewer;

/// <summary>A request or live.json the viewer refuses, with why.</summary>
public sealed class LookError : Exception
{
    public LookError(string why) : base(why) { }
}

/// <summary>
/// One look viewer shot's settings (live.json, or a request in requests/ID.json; docs/tools/LOOK_VIEWER.md), and the
/// game's switches for each camera exactly as Marionette's tools/npc/game_frame.py command() builds them, so a frame
/// through the viewer and a frame through game_frame are the same run of the game. The per-frame terms game_frame's
/// hook (game_frame.gd) applies are carried here too (Off, Light, LightOnly, Global, Spot, Solo, Mods).
/// </summary>
public sealed class LookSettings
{
    /// <summary>camera -> (--npc flags, extra game args): game_frame.py CAMS.</summary>
    public static readonly IReadOnlyDictionary<string, (string Flags, string[] Extra)> Cams = new Dictionary<string, (string, string[])>
    {
        ["play"] = ("", new[] { "--idle-after", "1000000", "--seconds", "6" }),
        ["chest"] = (":swap:chest", new[] { "--close", "1", "--idle-after", "1", "--seconds", "8" }),
    };

    /// <summary>The engine terms game_frame.gd switches off each frame (game_frame.py TERMS, less the light aliases).</summary>
    public static readonly IReadOnlySet<string> Terms = new HashSet<string>
    {
        "glow", "grade", "lut", "tonemap", "exposure", "fog", "volfog", "ssao", "ssil", "ssr", "sdfgi", "ambient",
        "reflection", "taa", "msaa", "lights", "shadows", "keyshadow", "ink",
    };

    /// <summary>Light aliases -> node-path patterns (game_frame.py LIGHTS).</summary>
    public static readonly IReadOnlyDictionary<string, string[]> Lights = new Dictionary<string, string[]>
    {
        ["key"] = new[] { "atmosphere/key" }, ["celrig_key"] = new[] { "celrigkey" }, ["her"] = new[] { "survivor/@omnilight3d" },
        ["townlamps"] = new[] { "/lights/light" }, ["campfire"] = new[] { "fires/" }, ["posthead"] = new[] { "posthead_" },
        ["battlefx"] = new[] { "battlefx" }, ["close_key"] = new[] { "closekeyfolk" }, ["close_fill"] = new[] { "closefillfolk" },
        ["close_cool"] = new[] { "closecoolfolk" }, ["close_rim"] = new[] { "closerimfolk" }, ["close_bodyrim"] = new[] { "closebodyrimfolk" },
        ["close_folk"] = new[] { "closekeyfolk", "closefillfolk", "closecoolfolk", "closerimfolk", "closebodyrimfolk" },
        ["ground"] = new[] { "closegroundkey" },
    };

    /// <summary>Known shade per zone (dx,dz): game_frame.py SHADE_SPOTS.</summary>
    public static readonly IReadOnlyDictionary<string, string> ShadeSpots = new Dictionary<string, string> { ["waystation"] = "-1.0,6.0" };

    public string Id = "base";
    public string? Package;          // a package folder, or "live" (requests); null in live.json
    public string? Name;             // the package's name in the game (default: see NameFor)
    public string? Out;              // where a request's frames go
    public string Zone = "waystation", Time = "day", Spot = "sun", Size = "1920x1080", Mods = "";
    public double? Clock, Turn;
    public bool Walk, Solo;
    public List<string> CamList = new() { "play", "chest" };
    public List<string> Off = new(), Light = new(), LightOnly = new();
    public Dictionary<string, double[]> Global = new();

    static readonly Regex IdOk = new(@"^[A-Za-z0-9_.-]+$"), SpotOk = new(@"^-?[\d.]+,-?[\d.]+$"), SizeOk = new(@"^\d+x\d+$");

    public static LookSettings Parse(string json, string? defaultId = null)
    {
        JsonDocument doc;
        try { doc = JsonDocument.Parse(json); }
        catch (JsonException e) { throw new LookError($"not JSON: {e.Message}"); }
        using (doc)
        {
            if (doc.RootElement.ValueKind != JsonValueKind.Object) throw new LookError("a JSON object is needed");
            var s = new LookSettings();
            if (defaultId != null) s.Id = defaultId;
            foreach (var p in doc.RootElement.EnumerateObject())
            {
                var v = p.Value;
                switch (p.Name)
                {
                    case "id": s.Id = Str(p); break;
                    case "package": s.Package = Str(p); break;
                    case "name": s.Name = Str(p); break;
                    case "out": s.Out = Str(p); break;
                    case "zone": s.Zone = Str(p); break;
                    case "time": s.Time = Str(p); break;
                    case "spot": s.Spot = Str(p); break;
                    case "size": s.Size = Str(p); break;
                    case "mods": s.Mods = v.ValueKind == JsonValueKind.Array ? string.Join(",", List(p)) : Str(p); break;
                    case "clock": s.Clock = v.ValueKind == JsonValueKind.Null ? null : Num(p); break;
                    case "turn": s.Turn = v.ValueKind == JsonValueKind.Null ? null : Num(p); break;
                    case "walk": s.Walk = Bool(p); break;
                    case "solo": s.Solo = Bool(p); break;
                    case "cams": s.CamList = List(p); break;
                    case "off": s.Off = List(p); break;
                    case "light": s.Light = List(p); break;
                    case "light_only": s.LightOnly = List(p); break;
                    case "global":
                        if (v.ValueKind != JsonValueKind.Object) throw new LookError("global: an object of NAME: number or [numbers]");
                        foreach (var g in v.EnumerateObject())
                            s.Global[g.Name] = g.Value.ValueKind == JsonValueKind.Array ? g.Value.EnumerateArray().Select(x => x.GetDouble()).ToArray()
                                : g.Value.ValueKind == JsonValueKind.Number ? new[] { g.Value.GetDouble() } : throw new LookError($"global {g.Name}: a number or [numbers]");
                        break;
                    case "comment": case "_comment": break;
                    default: throw new LookError($"no setting {p.Name} (id package name out zone time clock cams walk turn spot off light light_only global solo mods size)");
                }
            }
            s.Check();
            return s;
        }
    }

    static string Str(JsonProperty p) => p.Value.ValueKind == JsonValueKind.String ? p.Value.GetString()! : throw new LookError($"{p.Name}: a string");
    static double Num(JsonProperty p) => p.Value.ValueKind == JsonValueKind.Number ? p.Value.GetDouble() : throw new LookError($"{p.Name}: a number");
    static bool Bool(JsonProperty p) => p.Value.ValueKind is JsonValueKind.True or JsonValueKind.False ? p.Value.GetBoolean() : throw new LookError($"{p.Name}: true or false");
    static List<string> List(JsonProperty p) => p.Value.ValueKind switch
    {
        JsonValueKind.Array => p.Value.EnumerateArray().Select(x => x.ValueKind == JsonValueKind.String ? x.GetString()!.Trim() : throw new LookError($"{p.Name}: strings")).Where(x => x != "").ToList(),
        JsonValueKind.String => p.Value.GetString()!.Split(',').Select(x => x.Trim()).Where(x => x != "").ToList(),
        _ => throw new LookError($"{p.Name}: a list or a comma string"),
    };

    void Check()
    {
        if (!IdOk.IsMatch(Id)) throw new LookError($"id {Id}: letters, digits, _ . - only");
        if (Time is not ("day" or "night")) throw new LookError($"time {Time}: day or night");
        if (!SizeOk.IsMatch(Size)) throw new LookError($"size WxH, not {Size}");
        if (CamList.Count == 0) throw new LookError("cams: at least one of play, chest");
        foreach (var c in CamList) if (!Cams.ContainsKey(c)) throw new LookError($"no camera {c} (play, chest)");
        foreach (var t in Off) if (!Terms.Contains(t) && !Lights.ContainsKey(t)) throw new LookError($"no term {t} ({string.Join(", ", Terms.Concat(Lights.Keys).OrderBy(x => x))})");
        if (Spot is not ("sun" or "shade") && !SpotOk.IsMatch(Spot)) throw new LookError($"spot {Spot}: sun, shade or dx,dz");
        if (Spot == "shade" && !ShadeSpots.ContainsKey(Zone.ToLowerInvariant()))
            throw new LookError($"spot shade in {Zone}: the viewer knows only the table's shade ({string.Join(", ", ShadeSpots.Keys)}); give dx,dz, or use game_frame.py (its ray search)");
        if (Name != null && !IdOk.IsMatch(Name)) throw new LookError($"name {Name}: letters, digits, _ . - only");
    }

    public (int W, int H) SizeWH
    {
        get { var f = Size.Split('x'); return (int.Parse(f[0], CultureInfo.InvariantCulture), int.Parse(f[1], CultureInfo.InvariantCulture)); }
    }

    /// <summary>The package's name in the game: the settings' "name", else (for a folder) the folder's name, as
    /// game_frame.py names a package folder; the live folder (named "live") takes its manifest's "name".</summary>
    public static string NameFor(string? given, string folder, string? manifestName)
    {
        if (given != null) return given;
        var leaf = System.IO.Path.GetFileName(folder.TrimEnd('/', '\\'));
        if (leaf == "live" && manifestName is { Length: > 0 } mn && IdOk.IsMatch(mn)) return mn;
        return leaf;
    }

    /// <summary>(engine terms for the per-frame hook, light patterns, game args): game_frame.py off_terms.</summary>
    public (List<string> Terms, List<string> Pats, List<string> Game) OffTerms()
    {
        var terms = new List<string>(); var pats = new List<string>(Light.Select(x => x.ToLowerInvariant())); var game = new List<string>();
        foreach (var t in Off)
        {
            if (t == "ink") game.AddRange(new[] { "--ink", "off" });
            else if (Lights.TryGetValue(t, out var ps)) pats.AddRange(ps);
            else terms.Add(t);
        }
        return (terms, pats, game);
    }

    /// <summary>The spot offset game_frame.gd is sent (dx,dz), or null for the sun (where the game stands him).</summary>
    public (double Dx, double Dz)? SpotOffset()
    {
        if (Spot == "sun") return null;
        var s = Spot == "shade" ? ShadeSpots[Zone.ToLowerInvariant()] : Spot;
        var f = s.Split(',');
        return (double.Parse(f[0], CultureInfo.InvariantCulture), double.Parse(f[1], CultureInfo.InvariantCulture));
    }

    /// <summary>The spot as game_frame.py sends it (--gf-spot), for the record.</summary>
    public string? SpotSent => Spot == "sun" ? null : Spot == "shade" ? ShadeSpots[Zone.ToLowerInvariant()] : Spot;

    /// <summary>Python's "{x:g}" for the values the tools use.</summary>
    public static string G(double x) => x.ToString("0.#####", CultureInfo.InvariantCulture);

    /// <summary>The game's user args for one camera, as game_frame.py command() puts them after "--" (its --gf-* hook
    /// args excepted: the viewer does the hook's work itself).</summary>
    public List<string> GameArgs(string cam, string name, string? overlay, string tag)
    {
        if (!Cams.TryGetValue(cam, out var c)) throw new LookError($"no camera {cam}");
        var flags = c.Flags;
        if (Walk) flags = ":walk" + flags;
        if (Turn is double t && t != 0) flags += $":turn{G(t)}";
        var (_, _, game) = OffTerms();
        var a = new List<string> { "--quick", "warden", "--sex", "female", "--nohud", "--zone", Zone, "--facing", "0", "--seed", "1", "--time", Time };
        if (Clock is double k) a.AddRange(new[] { "--clock", G(k) });
        if (overlay != null) a.AddRange(new[] { "--npc-overlay", $"{name}={overlay.Replace('\\', '/')}" });
        a.AddRange(game);
        a.AddRange(c.Extra);
        a.AddRange(new[] { "--npc", name + flags, "--npc-debug", "--shot", tag });
        return a;
    }

    /// <summary>The seconds Shots takes its frame at, for a camera.</summary>
    public static double SecondsOf(string cam) => double.Parse(Cams[cam].Extra[Array.IndexOf(Cams[cam].Extra, "--seconds") + 1], CultureInfo.InvariantCulture);

    /// <summary>game_frame.py's tag for the shot (gf_ID_CAM, dots made underscores).</summary>
    public string Tag(string cam) => $"gf_{Id}_{cam}".Replace('.', '_');

    /// <summary>The settings as the record writes them back (CAM.json).</summary>
    public Dictionary<string, object?> Record() => new()
    {
        ["id"] = Id, ["package"] = Package, ["name"] = Name, ["zone"] = Zone, ["time"] = Time, ["clock"] = Clock, ["cams"] = CamList,
        ["walk"] = Walk, ["turn"] = Turn, ["spot"] = Spot, ["off"] = Off, ["light"] = Light, ["light_only"] = LightOnly,
        ["global"] = Global, ["solo"] = Solo, ["mods"] = Mods, ["size"] = Size,
    };
}

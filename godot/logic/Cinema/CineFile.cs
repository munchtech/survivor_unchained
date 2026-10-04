using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Cinema;

/* A cinematic as data (godot/data/cinematics/<id>.json; the format is
 * docs/cinematics/shoot/README.md). It is written from its shooting script
 * (docs/cinematics/shoot/<id>.md), shot by shot, so a writer can retime it
 * without touching code: each shot has a length, a camera and its cues, and
 * every cue is timed from the start (or the end) of its own shot, so a
 * longer shot carries its cues with it. Everything here is plain C#: the
 * game plays it (src/Cinema/CinemaDirector.cs), the tests read it, and the
 * animatic is cut from the same numbers (tools/cinematics/animatic.py). */

/// <summary>One cinematic, as written.</summary>
public sealed class CineFile
{
    public string Id = "", Title = "", Script = "", Conversation = "", Zone = "";
    /// <summary>Letterbox: seconds to ease the bars in at the start (0: they are
    /// there on the first frame) and out at the end.</summary>
    public CineBars Bars = new();
    public CineSkip Skip = new();
    /// <summary>How fast the world runs under it (Battle.WorldRate; 0 holds it),
    /// and whether the zone's own director waits.</summary>
    public CineWorld World = new();
    /// <summary>Named places in the zone: [x, z], [x, z, heading] or [x, h, z, heading]
    /// (h above the ground there).</summary>
    public Dictionary<string, double[]> Marks = new();
    public Dictionary<string, CineCast> Cast = new();
    /// <summary>Whose lines are read as narration: in italics, unnamed. The voice
    /// is the node's speaker in dialogue.json, so a narration recast (Vonnra
    /// calling the survivor home, if the story lead decides it) is a change to
    /// the speaker there and to this list, and nothing else.</summary>
    public List<string> Narrators = ["narrator"];
    public List<CineShot> Shots = new();
    /// <summary>Where it leaves things: the survivor's mark, and how the game's camera takes over.</summary>
    public CineEnd End = new();

    public static CineFile Parse(string json) => Json.Parse<CineFile>(json);

    /// <summary>A cinematic by id, from the game's data.</summary>
    public static CineFile Load(string id) => Parse(DataFiles.Text($"cinematics/{id}.json"));

    /// <summary>A mark as (x, h, z, heading): h is the height above the ground.</summary>
    public (double X, double H, double Z, double Heading) Mark(string name)
    {
        if (!Marks.TryGetValue(name, out var m)) throw new KeyNotFoundException($"{Id}: no mark '{name}'");
        return m.Length switch
        {
            2 => (m[0], 0, m[1], 0),
            3 => (m[0], 0, m[1], m[2]),
            4 => (m[0], m[1], m[2], m[3]),
            _ => throw new FormatException($"{Id}: mark '{name}' has {m.Length} numbers"),
        };
    }
}

public sealed class CineBars { public double In = 0.6, Out = 0.8; }

/// <summary>Hold interact or pause this long to skip, once this far in (from
/// the first frame for a cinematic seen before).</summary>
public sealed class CineSkip { public double From = 1.5, Hold = 0.8; }

public sealed class CineWorld { public double Rate; public bool ZoneHeld = true; }

/// <summary>Someone in it: the survivor, a person, one of the dead (spawned
/// into the fight, so they are still there when play begins), a boss.</summary>
public sealed class CineCast
{
    /// <summary>survivor, npc, enemy, boss.</summary>
    public string Kind = "npc";
    /// <summary>The enemy's def, the npc's id.</summary>
    public string? Def;
    /// <summary>Where they are when it begins.</summary>
    public string? Mark;
}

public sealed class CineEnd
{
    /// <summary>The survivor's mark when play resumes (skip or not).</summary>
    public string? Her;
    /// <summary>"follow": the game's camera; the last shot's move blends into it.</summary>
    public string Camera = "follow";
}

/// <summary>Which survivors a shot or a cue is for (all of them, when unset).</summary>
public sealed class CineWhen
{
    public List<string>? Calling, Background, Hair, Sex;
    public List<string>? Facts;

    public bool Holds(CineContext c) =>
        (Calling == null || Calling.Contains(c.Calling)) && (Background == null || Background.Contains(c.Background))
        && (Hair == null || Hair.Contains(c.Hair)) && (Sex == null || Sex.Contains(c.Sex))
        && (Facts == null || Facts.All(f => f.StartsWith('!') ? !c.Facts.Contains(f[1..]) : c.Facts.Contains(f)));
}

/// <summary>The survivor it is played for.</summary>
public sealed class CineContext
{
    public string Calling = "warden", Background = "hunter", Hair = "long", Sex = "female";
    public HashSet<string> Facts = new();
}

public sealed class CineShot
{
    public string Id = "";
    /// <summary>ECU, CU, MCU, MS, MLS, LS, ELS, OTS, POV, INSERT, 2S (for people; the player ignores it).</summary>
    public string Type = "";
    public double Dur;
    /// <summary>The screen black (sound only).</summary>
    public bool Black;
    /// <summary>Keep the camera where it is (the last frame before it began).</summary>
    public bool Hold;
    /// <summary>Lines this shot must hold to the end of, plus Tail: a longer take makes a longer shot.</summary>
    public List<string>? Fit;
    public double Tail = 0.6;
    public CineCam? Cam;
    public List<CineCue> Cues = new();
    public CineWhen? When;
    /// <summary>For people: what the shot is.</summary>
    public string Note = "";
    /// <summary>The moment that stands for the shot (its board, its previs frame):
    /// seconds in; unset, 60% of the way through.</summary>
    public double? Still;
}

public sealed class CineCam
{
    public JsonElement Pos, At;
    /// <summary>Full-frame focal length (mm), as horizontal field of view.</summary>
    public double Lens = 50;
    /// <summary>Where it is sharp: metres from the lens, or a place; unset: no depth of field.</summary>
    public JsonElement Focus;
    /// <summary>How shallow: the f-number (lower is shallower).</summary>
    public double Fstop = 2.8;
    public double Roll;
    /// <summary>A hand on the camera (0..1 of the game's shake).</summary>
    public double Handheld;
    public CineMove? Move;
}

/// <summary>The camera moving within its shot, from Start to End seconds
/// (End may be "end" or "end-0.5").</summary>
public sealed class CineMove
{
    public JsonElement Pos, At, Focus, Start, End;
    /// <summary>A crane or a dolly by spline: the places it passes through, after Pos.</summary>
    public List<JsonElement>? Path;
    /// <summary>A push in (metres along the look, + toward it), instead of a new place.</summary>
    public double Push;
    public double? Lens, Roll;
    public string Ease = "inout";
    /// <summary>Ends as the game's own follow camera on the survivor's end mark.</summary>
    public bool Follow;
}

/// <summary>Something that happens at a moment of a shot. What it carries
/// depends on what it does (Do); the rest of its fields are read by name.</summary>
public sealed class CineCue
{
    /// <summary>Seconds from the shot's start, or "end-0.8" from its end.</summary>
    public JsonElement At;
    public string Do = "";
    public CineWhen? When;
    /// <summary>"apply" or "drop": whether a skip still does it (by default: what lasts, yes).</summary>
    public string? Skip;
    [JsonExtensionData] public Dictionary<string, JsonElement>? Args;

    public string? Str(string k) => Args != null && Args.TryGetValue(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    public double Num(string k, double or = 0) => Args != null && Args.TryGetValue(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : or;
    public bool Bool(string k, bool or = false) => Args != null && Args.TryGetValue(k, out var v) && v.ValueKind is JsonValueKind.True or JsonValueKind.False ? v.GetBoolean() : or;
    public bool Has(string k) => Args != null && Args.ContainsKey(k);
    public JsonElement Get(string k) => Args != null && Args.TryGetValue(k, out var v) ? v : default;
    public string Actor => Str("actor") ?? "her";

    /// <summary>What a skip still does: what lasts after the cinematic (who is where,
    /// what was spawned, lights, the air, the world's pace, the game's events).</summary>
    public bool Lasting => Skip switch
    {
        "apply" => true,
        "drop" => false,
        _ => Do is "place" or "spawn" or "world" or "light" or "lit" or "atmosphere" or "event" or "fire" or "hide" or "prints",
    };

    /// <summary>The kinds of cue the player knows (the tests hold every cue to them).</summary>
    public static readonly HashSet<string> Kinds =
    [
        "line", "music", "sfx", "place", "anim", "move", "face", "gaze", "lids", "look", "light", "lit", "fire",
        "atmosphere", "vfx", "spawn", "world", "bars", "title", "event", "fade", "hide", "wet", "hold", "prop", "prints",
    ];
}

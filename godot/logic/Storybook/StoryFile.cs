using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Storybook;

/* A storybook as data (godot/data/storybook/<id>.json; the format is
 * docs/storybook/README.md): painted plates in layers, each with its own
 * camera across them, living touches, particles, its transition in and out,
 * and cues for sound and lines. Times are seconds from the first frame of
 * black, and a plate's own times (camera, layer keys, cues) are from its
 * "at". Positions and sizes are canvas pixels: the plate's reference frame
 * as seen from the camera at rest. Plain C#: the game plays it
 * (src/Storybook), the tests read it. */

/// <summary>One storybook, as written.</summary>
public sealed class StoryFile
{
    public string Id = "", Title = "", Script = "", Conversation = "";
    /// <summary>Whether a new journey plays it (false while its plates are placeholders; --storybook &lt;id&gt; still plays it alone).</summary>
    public bool Live = true;
    /// <summary>The plate's reference frame, in pixels (16:9; the 2.39:1 bars crop it).</summary>
    public double[] Canvas = [3200, 1800];
    /// <summary>The light screen-space finish over everything: film grain and a vignette.</summary>
    public double Grain = 0.05, Vignette = 0.3;
    public StorySkip Skip = new();
    public List<StoryPlate> Plates = new();
    /// <summary>Cues at absolute times (the plates' own are from their "at").</summary>
    public List<StoryCue> Cues = new();
    /// <summary>When it is over (black after the last plate until then).</summary>
    public double End;

    public double CanvasW => Canvas.Length > 0 ? Canvas[0] : 3200;
    public double CanvasH => Canvas.Length > 1 ? Canvas[1] : 1800;

    public static StoryFile Parse(string json)
    {
        var f = Json.Parse<StoryFile>(json);
        if (f.End <= 0) f.End = f.Plates.Count > 0 ? f.Plates.Max(p => p.Until) : 0;
        return f;
    }

    /// <summary>A storybook by id, from the game's data.</summary>
    public static StoryFile Load(string id) => Parse(DataFiles.Text($"storybook/{id}.json"));

    /// <summary>What is wrong with it, said plainly (empty: it plays).</summary>
    public List<string> Problems()
    {
        var p = new List<string>();
        if (Id == "") p.Add("no id");
        if (CanvasW <= 0 || CanvasH <= 0) p.Add("canvas has no size");
        double last = double.NegativeInfinity;
        foreach (var pl in Plates)
        {
            string w = $"plate {pl.Id}";
            if (pl.At < last) p.Add($"{w} starts before the plate above it");
            last = pl.At;
            if (pl.Until <= pl.At) p.Add($"{w} ends ({pl.Until}) before it starts ({pl.At})");
            if (!StoryTransition.Kinds.Contains(pl.In.Kind)) p.Add($"{w}: no transition '{pl.In.Kind}'");
            if (pl.Out != null && pl.Out.Kind != "fade") p.Add($"{w}: out is only 'fade'");
            if (pl.In.Kind != "cut" && pl.In.Dur <= 0) p.Add($"{w}: transition {pl.In.Kind} has no length");
            if (pl.In.Dur > pl.Until - pl.At) p.Add($"{w}: its transition outlasts it");
            foreach (var l in pl.Layers)
            {
                if (l.Image == null && l.Color == null && (l.Frames == null || l.Frames.Count == 0)) p.Add($"{w} layer {l.Id}: no image, frames or color");
                if (l.Z <= 0) p.Add($"{w} layer {l.Id}: z must be above 0");
                if (!StoryLayer.Blends.Contains(l.Blend)) p.Add($"{w} layer {l.Id}: no blend '{l.Blend}'");
                foreach (var t in l.Touch ?? new())
                    if (!StoryTouch.Kinds.Contains(t.Kind)) p.Add($"{w} layer {l.Id}: no touch '{t.Kind}'");
                if ((l.Touch ?? new()).GroupBy(t => t.Kind).Any(g => g.Count() > 1)) p.Add($"{w} layer {l.Id}: a touch kind twice");
            }
            foreach (var fx in pl.Fx)
            {
                if (fx.Kind is not ("particles" or "mist")) p.Add($"{w}: no fx '{fx.Kind}'");
                if (fx.Kind == "particles" && !StoryFx.Presets.Contains(fx.Preset ?? "")) p.Add($"{w}: no particle preset '{fx.Preset}'");
            }
            foreach (var c in pl.Cues) if (!StoryCue.Kinds.Contains(c.Do)) p.Add($"{w}: no cue '{c.Do}'");
        }
        foreach (var c in Cues) if (!StoryCue.Kinds.Contains(c.Do)) p.Add($"no cue '{c.Do}'");
        if (Plates.Count > 0 && End < Plates.Max(x => x.Until)) p.Add($"ends ({End}) before its last plate");
        return p;
    }
}

/// <summary>Hold interact or pause this long to skip, once this far in (at once once seen).</summary>
public sealed class StorySkip { public double From = 1.5, Hold = 0.8; }

/// <summary>One painting in layers, with its own camera move.</summary>
public sealed class StoryPlate
{
    public string Id = "";
    /// <summary>When its transition in starts, and when it is done (the outgoing
    /// plate is drawn on until the next one's transition ends).</summary>
    public double At, Until;
    [JsonPropertyName("in")] public StoryTransition In = new();
    /// <summary>Its own way out (a fade to black over the last Dur before Until).</summary>
    [JsonPropertyName("out")] public StoryTransition? Out;
    public List<StoryCamKey> Camera = new();
    public List<StoryGradeKey>? Grade;
    public List<StoryLayer> Layers = new();
    public List<StoryFx> Fx = new();
    public List<StoryCue> Cues = new();
    public string? Note;
}

public sealed class StoryTransition
{
    public static readonly HashSet<string> Kinds = ["cut", "fade", "dissolve", "ink", "light", "waterline"];
    public string Kind = "cut";
    public double Dur;
    /// <summary>Ink and light: where the bloom starts (0..1 of the screen) and its order map
    /// (grayscale, dark first; unset: a fractal bloom from Origin).</summary>
    public double[]? Origin;
    public string? Map;
    /// <summary>The front's colour (ink: the wet rim; light: the warm glow), and how soft it is (0..1 of the order).</summary>
    public string? Edge;
    public double Soft = 0.08;
    /// <summary>Fade: the colour it dips through (black).</summary>
    public string? Color;
    /// <summary>Waterline: how much the surface line waves (0..1 of the screen's height).</summary>
    public double Wave = 0.025;
}

/// <summary>A camera key. Unset values carry on from the key before (the first's: at rest).</summary>
public sealed class StoryCamKey
{
    public double T;
    public double? X, Y, Zoom, Dolly, Rot;
    public string? Ease;
}

public sealed class StoryGradeKey
{
    public double T;
    public double? Exposure, Sat;
    public string? Tint;
    public string? Ease;
}

public sealed class StoryLayer
{
    public static readonly HashSet<string> Blends = ["mix", "add", "screen", "multiply"];
    public string Id = "";
    public string? Image;
    /// <summary>A flat card instead of an image (a placeholder), its size in canvas px
    /// (unset: the canvas), and a small label written on it.</summary>
    public string? Color, Label;
    public double[]? Size;
    /// <summary>Where its top-left sits on the canvas at rest, and image px to canvas px.</summary>
    public double[] Pos = [0, 0];
    public double Scale = 1;
    /// <summary>Its depth: 1 the reference plane; far is more (sky 6-20), near less (0.5-0.9).</summary>
    public double Z = 1;
    public string Blend = "mix";
    public double Opacity = 1;
    /// <summary>What its keys turn and scale about, in canvas px (unset: its centre).</summary>
    public double[]? Pivot;
    /// <summary>The image repeats beyond its edges (a scroll's mist band).</summary>
    public bool Repeat;
    public List<StoryLayerKey>? Keys;
    public List<StoryFrame>? Frames;
    public List<StoryTouch>? Touch;
}

public sealed class StoryLayerKey
{
    public double T;
    public double? Dx, Dy, Scale, Rot, Opacity;
    public string? Ease;
}

/// <summary>A drawn key pose, crossfaded in over Fade seconds from T.</summary>
public sealed class StoryFrame { public double T; public string Image = ""; public double Fade = 0.4; }

/// <summary>Named arguments read by name, for touches, fx and cues.</summary>
public abstract class StoryArgs
{
    [JsonExtensionData] public Dictionary<string, JsonElement>? Args;
    public bool Has(string k) => Args != null && Args.ContainsKey(k);
    public string? Str(string k) => Args != null && Args.TryGetValue(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
    public double Num(string k, double or = 0) => Args != null && Args.TryGetValue(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : or;
    public bool Bool(string k, bool or = false) => Args != null && Args.TryGetValue(k, out var v) && v.ValueKind is JsonValueKind.True or JsonValueKind.False ? v.GetBoolean() : or;
    /// <summary>A list of numbers ([x, y], [min, max]); a single number is a list of one.</summary>
    public double[]? Nums(string k)
    {
        if (Args == null || !Args.TryGetValue(k, out var v)) return null;
        if (v.ValueKind == JsonValueKind.Number) return [v.GetDouble()];
        if (v.ValueKind != JsonValueKind.Array) return null;
        return v.EnumerateArray().Where(e => e.ValueKind == JsonValueKind.Number).Select(e => e.GetDouble()).ToArray();
    }
    /// <summary>A list of points ([[x, y], ...]).</summary>
    public List<double[]> Points(string k)
    {
        var o = new List<double[]>();
        if (Args == null || !Args.TryGetValue(k, out var v) || v.ValueKind != JsonValueKind.Array) return o;
        foreach (var e in v.EnumerateArray())
            if (e.ValueKind == JsonValueKind.Array) o.Add(e.EnumerateArray().Select(x => x.GetDouble()).ToArray());
        return o;
    }
    public List<string> Strs(string k)
    {
        if (Args == null || !Args.TryGetValue(k, out var v)) return new();
        if (v.ValueKind == JsonValueKind.String) return [v.GetString()!];
        if (v.ValueKind != JsonValueKind.Array) return new();
        return v.EnumerateArray().Where(e => e.ValueKind == JsonValueKind.String).Select(e => e.GetString()!).ToList();
    }
}

/// <summary>A living touch on a layer (a shader): flicker, sway, water, ripple, reveal, scroll.</summary>
public sealed class StoryTouch : StoryArgs
{
    public static readonly HashSet<string> Kinds = ["flicker", "sway", "water", "ripple", "reveal", "scroll"];
    public string Kind = "";
}

/// <summary>Particles (a preset, tuned) or a drifting mist band, at a depth.</summary>
public sealed class StoryFx : StoryArgs
{
    public static readonly HashSet<string> Presets = ["smoke", "sparks", "motes", "bubbles", "drips", "ash", "snow"];
    public string Kind = "";
    public string? Preset;
    public double Z = 1;
}

/// <summary>Something that happens at a moment: a line, a sound, the music, the bus.</summary>
public sealed class StoryCue : StoryArgs
{
    public static readonly HashSet<string> Kinds = ["line", "sfx", "sound", "stop", "music", "bus", "say"];
    public double At;
    public string Do = "";
}

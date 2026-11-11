using System;
using System.Collections.Generic;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

public enum HitClass { Trash, Heavy, Critical, EliteKill, Finisher }

public sealed class HitStopDef
{
    public bool Enabled;
    public double CapMs;
    public Dictionary<HitClass, double> DurationMs = new();
    public CrowdDef Crowd = new();
    public ScreenDef HeadlessScreen = new();

    public sealed class CrowdDef { public int Above; public double Scale; }
    public sealed class ScreenDef { public double HalfWidth, HalfDepth; }

    public double Seconds(HitClass kind, int liveOnScreen) => !Enabled ? 0 :
        Math.Min(CapMs, DurationMs[kind] * (liveOnScreen > Crowd.Above ? Crowd.Scale : 1)) / 1000;
}

public static class HitStop
{
    static readonly Lazy<HitStopDef> file = new(() => Parse(Json.ReadContent("hit_stop.json")));
    public static HitStopDef File => file.Value;

    public static HitStopDef Parse(string json)
    {
        var d = Json.Parse<HitStopDef>(json);
        // This ceiling is a safety invariant, even when the tuning data changes.
        if (!double.IsFinite(d.CapMs) || d.CapMs <= 0 || d.CapMs > 150 || d.Crowd.Above < 0 ||
            !double.IsFinite(d.Crowd.Scale) || d.Crowd.Scale < 0 || d.Crowd.Scale > 1 ||
            !double.IsFinite(d.HeadlessScreen.HalfWidth) || d.HeadlessScreen.HalfWidth <= 0 ||
            !double.IsFinite(d.HeadlessScreen.HalfDepth) || d.HeadlessScreen.HalfDepth <= 0)
            throw new ArgumentException("Invalid hit-stop bounds");
        foreach (var kind in Enum.GetValues<HitClass>())
            if (!d.DurationMs.TryGetValue(kind, out double ms) || !double.IsFinite(ms) || ms < 0)
                throw new ArgumentException($"Invalid hit-stop duration: {kind}");
        return d;
    }
}

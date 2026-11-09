using System.Collections.Generic;
using System.Globalization;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.View;

/// <summary>
/// --act CLIP (dev only; nothing changes without it): one of her P4 clips played on her WHOLE BODY for a shot, timed by
/// ActPlan from data/anim/her_events.json. Flags: --act-at S (run seconds to the start, 1.0), --act-travel M (her root moves
/// M meters straight ahead, her facing at the start, over the clip's travel window), --act-hold S (the loop range repeats for
/// S seconds), --act-spin T (turns a second to her left while the loop plays), --act-repeat N (n acts from the first's spot
/// and facing, 1.5 s apart). The clip's place is driven per frame (fullScale; a seek where a held loop jumps back) and her
/// root and facing are set after her other drivers have had their say, so locomotion, rest, look-at and the turn to the view
/// do not move her; when the clip ends she blends back to what she was doing, where the act left her.
/// One log line per act, then the run time each event is hit.
/// </summary>
public partial class PlayerView
{
    static readonly string? ActClip = Args.Get("act");
    static bool ActOn => ActClip != null;

    ActPlan? actPlan;
    bool actInit;
    double actT0;
    int actPass = -1, actEvent;
    double actPos;
    Vector3 actBase;
    float actBaseYaw;
    bool actFading, actShown;
    List<(string Name, double Run)> actEvents = new();

    /// <summary>She is inside an act (started, not yet ended): her rest, fidgets and look-at stand aside.</summary>
    bool ActLive => actPlan != null && actPass >= 0 && actClock() <= actPlan.Start(actPlan.Repeat - 1) + actPlan.Duration + 0.25;
    double actClock() => time - actT0;

    /// <summary>Where the act has put her (null: no act has begun), for the camera and the lights to follow.</summary>
    public Vector3? ActAt => actShown ? Position : null;

    void ActLoad()
    {
        actInit = true;
        actT0 = time - 0;   // (time has run this frame's dt already: the run's clock counts from here)
        if (!own.Has(ActClip!)) { GD.PrintErr($"act: no clip '{ActClip}' in her library"); return; }
        var anim = person.Anim.GetAnimation(own.Prefix + ActClip);
        HerEvents.Beats? beats = null;
        var path = ProjectSettings.GlobalizePath("res://data/anim/her_events.json");
        if (Godot.FileAccess.FileExists(path) && HerEvents.Load(Godot.FileAccess.GetFileAsString(path)).TryGetValue(ActClip!, out var bb)) beats = bb;
        double Num(string k, double d) => double.TryParse(Args.Get(k), NumberStyles.Float, CultureInfo.InvariantCulture, out var v) ? v : d;
        actPlan = new ActPlan(anim.Length, beats, anim.LoopMode != Animation.LoopModeEnum.None, Num("act-at", 1.0), Num("act-travel", 0), Num("act-hold", 0),
            Num("act-spin", 0), (int)Num("act-repeat", 1));
        if (actPlan.Travel != 0 && actPlan.WindowWhole) GD.PrintErr($"act: {ActClip} has no takeoff/land or launch/impact in her_events.json: travelling over its whole length");
        if (actPlan.HoldIgnored) GD.PrintErr($"act: {ActClip} has no loop range and its animation does not loop: --act-hold ignored");
        if (actPlan.SpinIgnored) GD.PrintErr($"act: {ActClip} has no loop range and its animation does not loop: --act-spin ignored");
        if (beats == null) GD.Print($"act: {ActClip} has no beats in her_events.json");
    }

    /// <summary>Before the tree advances: start the clip at its time, then each frame set its place for the end of this frame.</summary>
    void ActTick(double dt)
    {
        if (!ActOn) return;
        if (!actInit) ActLoad();
        if (actPlan == null) return;
        var s = actPlan.Sample(actClock());
        if (s.Pass < 0) return;
        if (s.Pass != actPass)
        {
            actPass = s.Pass; actEvent = 0; actPos = 0; actFading = false;
            if (!actShown) { actBase = Position; actBaseYaw = Rotation.Y; actShown = true; }
            if (!FullHer(ActClip!, 1, false)) { GD.PrintErr($"act: {ActClip} would not start"); actPlan = null; return; }
            actEvents = new List<(string, double)>(actPlan.EventsRun(actPass));
            GD.Print($"act: {ActClip} at t={actPlan.Start(actPass):0.00} travel {actPlan.Travel:0.##} m over [{actPlan.Window.A:0.000}, {actPlan.Window.B:0.000}] s, " +
                     $"hold {(actPlan.Loop is { } lp ? actPlan.Passes * (lp.B - lp.A) : 0):0.##} s, spin {actPlan.Spin:0.##} t/s (pass {actPass + 1}/{actPlan.Repeat}, {actPlan.Duration:0.00} s long)");
        }
        if (s.Active)
        {
            double scale = 1;
            if (s.Clip < actPos - 1e-6)
            {
                // a held loop jumps back to its start
                tree.Set("parameters/fullSeek/seek_request", s.Clip);
            }
            else scale = System.Math.Max(0, (s.Clip - actPos) / System.Math.Max(1e-4, dt));
            actPos = s.Clip;
            tree.Set("parameters/fullScale/scale", scale);
            // (a looping animation never ends the shot by itself: let it go over its last 0.2 s)
            if (!actFading && actClock() >= actPlan.Start(actPass) + actPlan.Duration - 0.2 && full.Animation != null
                && person.Anim.GetAnimation(full.Animation)?.LoopMode != Animation.LoopModeEnum.None)
            {
                actFading = true;
                tree.Set("parameters/fullShot/request", (int)AnimationNodeOneShot.OneShotRequest.FadeOut);
            }
        }
        else tree.Set("parameters/fullScale/scale", 1.0);
        while (actEvent < actEvents.Count && actClock() >= actEvents[actEvent].Run)
        {
            GD.Print($"act: {ActClip} event {actEvents[actEvent].Name} hit at t={actEvents[actEvent].Run:0.00} (clip {actPos:0.000} s)");
            actEvent++;
        }
    }

    /// <summary>After her other drivers: her root off the fight's spot by the act's offset along its facing, her yaw turned by the act's.</summary>
    void ActApply()
    {
        if (!ActOn || actPlan == null || !actShown) return;
        var s = actPlan.Sample(actClock());
        if (s.Pass < 0) return;
        var fwd = new Vector3(Mathf.Sin(actBaseYaw), 0, Mathf.Cos(actBaseYaw));
        Position = actBase + fwd * (float)s.Ahead;
        Rotation = new Vector3(0, actBaseYaw + (float)s.Yaw, 0);
        if (carriage != null && ActLive) carriage.Aim = carriage.Bank = carriage.Tilt = carriage.HeadLevel = 0;
        aim = 0;
    }
}

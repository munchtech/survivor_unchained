using System;
using Godot;
using SurvivorUnchained.Play.Zones;

namespace SurvivorUnchained.Play;

/// <summary>
/// The close view of her in play (logic/Play/CloseUp.cs decides how near; FollowCamera.Close frames it): the wheel
/// or the right stick in town, and the idle view anywhere quiet. The wheel only brings the view nearer, her back
/// still to it; in the idle view she turns to it (CloseUp.PoseFor), her head to the lens. Close, by day her carried
/// light comes down so the sun models her face. --close C: the wheel's level set (pictures); --idle-after S: the idle view after S seconds.
/// </summary>
public partial class Game
{
    readonly CloseUp closeUp = new();
    double closeDrift;
    bool closeDrives;

    /// <summary>A new place: the close view back to play's distance at once (--close C: set, where it is safe).</summary>
    void CloseUpBegin(ZoneRuntime z)
    {
        closeUp.Reset();
        if (!z.Combat && Args.Has("close")) closeUp.Wheel(Args.Num("close", 0) / CloseUp.Step, 0, new CloseUp.Situation(true, false, false, false));
        cam.Close = 0;
        cam.Orbit = 0;
        cam.SnapClose();
        hud.Calm(false, 0);
        z.KeepClear = null;
        cam.Room = (a, b) =>
        {
            if (Battle?.Collision is not { } col) return 1;
            float dx = b.X - a.X, dz = b.Z - a.Z, len = Mathf.Sqrt(dx * dx + dz * dz);
            if (len < 0.01f) return 1;
            // (a wall's face with a hand's room before it)
            return col.Raycast(a.X, a.Z, b.X, b.Z, 0.25) is { } hit ? Mathf.Max(0, (float)hit.T * len - 0.35f) / len : 1;
        };
        cam.Ground = (x, zz) => (float)(scene?.HeightAt(x, zz) ?? 0);
    }

    /// <summary>Each frame of play.</summary>
    void UpdateCloseUp(double dt)
    {
        if (scene == null || zone == null) return;
        var s = Settings.Current;
        closeUp.IdleOn = s.IdleClose;
        closeUp.IdleAfter = Args.Has("idle-after") ? Args.Num("idle-after", 60) : s.IdleCloseAfter;
        bool taken = InCinematic || showing || scene.CameraHeld;
        bool held = taken || Mode != "play" || hudMode != null || screens.Current != null || inTransit || camSaved != null
            || zone is ArenaRun or StoryNight || zone.Ember || cam.FocusOverride != null || Battle?.Player is not { Alive: true };
        var p = Battle?.Player;
        bool moving = p != null && p.Vx * p.Vx + p.Vz * p.Vz > 0.16;
        var sit = new CloseUp.Situation(!zone.Combat, held, Battle is { } b && CloseUp.Threat(b), moving);
        scene.Player?.Calm(sit.Safe, sit.Threat);
        if (controls.Touched) { controls.Touched = false; closeUp.Input(); }
        double notches = controls.Wheel;
        controls.Wheel = 0;
        // The pad's right stick, up nearer and down back (as the figure in creation), where it is safe.
        var look = controls.Look;
        if (!held && !zone.Combat && Mathf.Abs(look.Y) > Mathf.Abs(look.X)) notches += -look.Y * 7 * dt;
        closeUp.Wheel(notches, cam.CloseShown, sit);
        float target = (float)closeUp.Update(dt, sit);
        if (spotClose is float tc) { target = tc; taken = true; }
        cam.Close = target;
        cam.CloseRate = (float)closeUp.Rate(target, cam.CloseShown);
        // The idle view drifts slowly round her, between three-quarters and her front.
        closeDrift = closeUp.Idling ? closeDrift + dt : 0;
        cam.Orbit = closeUp.Idling ? 0.3f * Mathf.Sin((float)closeDrift * 0.1f) : 0;
        if (taken) cam.SnapClose();
        HerToTheView(dt, held);
        // The idle view is a picture: the HUD steps away (back at once on any input). Near, by the wheel or idle,
        // no name floats by her head, and the town's walkers keep out of the view behind her.
        float near = cam.CloseShown;
        hud.Calm(!held && closeUp.Idling && near > 0.15f, dt);
        scene.Voices.Away = !held && (closeUp.Idling || target >= 0.5f || near >= 0.5f);
        if (!held && near > 0.3f && p != null)
            zone.KeepClear = (p.X, p.Z, -Mathf.Sin(cam.Yaw), -Mathf.Cos(cam.Yaw));
        else zone.KeepClear = null;
    }

    /// <summary>In the idle view she turns to it, her head to the lens (never for the wheel alone: the owner,
    /// 17 October); close, by day her light comes down.</summary>
    void HerToTheView(double dt, bool held)
    {
        if (scene?.Player is not { } pv || screens.Current != null) { closeDrives = false; return; }
        float near = cam.CloseShown;
        bool turn = !held && closeUp.PoseFor(false, false, false) == CloseUp.Pose.ToTheView;
        if (turn)
        {
            // (three-quarters to the lens, her shield side away: square on, the shield hid her waist and hips)
            pv.Turned = cam.Yaw + 0.6f;
            pv.Watch = cam.Camera;
        }
        else if (closeDrives) { pv.Turned = null; pv.Watch = null; }
        bool lit = !held && near > 0.05f && scene.View.Night != true;
        float day = Mathf.Clamp((near - 0.3f) / 0.4f, 0, 1);
        if (lit) pv.LampScale = Mathf.Lerp(1, CloseLampByDay, day);
        else if (closeDrives) pv.LampScale = 1;
        closeDrives = turn || lit;
        // By day the sun is behind or above her: a soft key of her own, 40 degrees off the lens on the side she
        // turns to and 25 up, on people only (layer 2), so her face is modelled, not flat.
        if (closeKey == null || !IsInstanceValid(closeKey) || closeKey.GetParent() != scene)
        {
            closeKey = new SpotLight3D { LightColor = new Color(1f, 0.95f, 0.88f), SpotAngle = 24, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = 2, LightSpecular = 0.3f, LightEnergy = 0 };
            scene.AddChild(closeKey);
        }
        float want = lit ? CloseKey * day : 0;
        closeKey.LightEnergy = Mathf.Lerp(closeKey.LightEnergy, want, 1 - Mathf.Exp(-3 * (float)dt));
        closeKey.Visible = closeKey.LightEnergy > 0.005f;
        if (closeKey.Visible)
        {
            var chest = pv.GlobalPosition + new Vector3(0, 1.55f, 0);
            float a = cam.Yaw + 0.7f, up = Mathf.DegToRad(25);
            closeKey.GlobalPosition = chest + new Vector3(Mathf.Sin(a) * Mathf.Cos(up), Mathf.Sin(up), Mathf.Cos(a) * Mathf.Cos(up)) * 2.6f;
            closeKey.LookAt(chest);
        }
    }

    SpotLight3D? closeKey;
    // --close-key E, --close-lamp L: the day key's strength and her lamp's share by day, for pictures.
    static float CloseKey => Args.Has("close-key") ? Args.Num("close-key", 0.7f) : 0.7f;
    static float CloseLampByDay => Args.Has("close-lamp") ? Args.Num("close-lamp", 0.25f) : 0.25f;
}

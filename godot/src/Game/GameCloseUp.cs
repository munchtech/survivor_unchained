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
    static readonly float CloseTurn = Args.Has("close-turn") ? (float)Args.Num("close-turn", 0.6f) : 0.6f;
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
        roomTops.Clear();
        cam.Room = (a, b) =>
        {
            if (Battle?.Collision is not { } col) return 1;
            float dx = b.X - a.X, dz = b.Z - a.Z, len = Mathf.Sqrt(dx * dx + dz * dz);
            if (len < 0.01f) return 1;
            // (a wall's face with a hand's room before it; a post seen past, a cart passed over: CameraRoom)
            var hit = col.Raycast(a.X, a.Z, b.X, b.Z, 0.25, true, (c, t) => CameraRoom.Blocks(c, t, a.Y, b.Y, RoomTop(c)));
            if (CamLog) cam.RoomHit = hit is { } h0 ? $"{h0.Collider.Id}:{h0.Collider.Kind}@{h0.Collider.X:F1},{h0.Collider.Z:F1}_r{h0.Collider.R:F2}_T{h0.T:F2}_top{RoomTop(h0.Collider):F2}" : null;
            return hit is { } h ? Mathf.Max(0, (float)h.T * len - 0.35f) / len : 1;
        };
        cam.Ground = (x, zz) => (float)(scene?.HeightAt(x, zz) ?? 0);
    }

    static readonly bool CamLog = Args.Has("camlog");
    readonly System.Collections.Generic.Dictionary<int, float?> roomTops = new();

    /// <summary>The top (world y) of what is drawn standing on a collider's footprint, looked up once (the renderer's
    /// own cull of the box over it: meshes and each copy of a multimesh there, not the ground, the grass or the
    /// living); null where nothing is drawn there.</summary>
    float? RoomTop(SurvivorUnchained.Sim.Collider c)
    {
        if (roomTops.TryGetValue(c.Id, out var known)) return known;
        float? top = null;
        var world = camera.GetWorld3D();
        if (world != null)
        {
            // (the footprint, a little inside its edge, so a neighbor's wall touching it is not counted)
            float ex = (float)c.R + 0.3f, inset = 0.1f;
            float cx = (float)c.X, cz = (float)c.Z;
            float gy = (float)(scene?.HeightAt(c.X, c.Z) ?? 0);
            var box = new Aabb(new Vector3(cx - ex, gy - 4, cz - ex), new Vector3(2 * ex, 44, 2 * ex));
            bool Over(Aabb a)
            {
                if (a.Size.Y < 0.5f || a.Size.X > 40 || a.Size.Z > 40) return false;
                if (c.Kind == SurvivorUnchained.Sim.ColliderKind.Circle)
                {
                    float qx = Mathf.Clamp(cx, a.Position.X, a.End.X), qz = Mathf.Clamp(cz, a.Position.Z, a.End.Z);
                    float r = (float)c.R - inset;
                    return (qx - cx) * (qx - cx) + (qz - cz) * (qz - cz) < r * r;
                }
                // (a box: the drawn thing's middle within it, a quarter metre's slack, in the box's own frame)
                float cos = Mathf.Cos(-(float)c.Rot), sin = Mathf.Sin(-(float)c.Rot);
                var m = a.GetCenter();
                float lx = (m.X - cx) * cos - (m.Z - cz) * sin, lz = (m.X - cx) * sin + (m.Z - cz) * cos;
                return Mathf.Abs(lx) < (float)c.Hw + 0.25f && Mathf.Abs(lz) < (float)c.Hd + 0.25f;
            }
            foreach (ulong id in RenderingServer.InstancesCullAabb(box, world.Scenario))
            {
                if (GodotObject.InstanceFromId(id) is not GeometryInstance3D g || !g.IsVisibleInTree() || g.GetParent() is Skeleton3D) continue;
                if (g is MultiMeshInstance3D mmi && mmi.Multimesh is { Mesh: { } mesh } mm)
                {
                    var local = mesh.GetAabb();
                    if (local.Size.Y < 0.5f) continue;
                    var gt = mmi.GlobalTransform;
                    int n = mm.VisibleInstanceCount >= 0 ? mm.VisibleInstanceCount : mm.InstanceCount;
                    for (int i = 0; i < n; i++)
                    {
                        var a = gt * mm.GetInstanceTransform(i) * local;
                        if (Over(a)) top = Mathf.Max(top ?? float.MinValue, a.End.Y);
                    }
                }
                else if (g is MeshInstance3D mi && mi.Mesh != null)
                {
                    var a = mi.GlobalTransform * mi.GetAabb();
                    if (Over(a)) top = Mathf.Max(top ?? float.MinValue, a.End.Y);
                }
            }
        }
        roomTops[c.Id] = top;
        return top;
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
        if (scene.Player != null && Args.Has("hairdump")) HairDump.Tick(scene.Player.Person, dt);
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
        if (scene?.Player is not { } pv || screens.Current != null)
        {
            closeDrives = false;
            if (scene?.Player is { } pv0) { pv0.LampOffHer = false; if (pv0.OwnLayer) { pv0.OwnLayer = false; scene.View.HerUnlit(false); } }
            if (scene?.Player is { } pv1 && skyShown != 1) { skyShown = 1; SurvivorUnchained.View.People.HerSkyShare(pv1.Person, 1); }
            if (scene?.Player is { } pv2 && eyesNight != 0) { eyesNight = 0; SurvivorUnchained.View.People.HerEyesNight(pv2.Person, 0); SurvivorUnchained.View.People.HerSkinHold(pv2.Person, 0); }
            if (fireFill != null && IsInstanceValid(fireFill)) fireFill.Visible = false;
            return;
        }
        float near = cam.CloseShown;
        bool turn = !held && closeUp.PoseFor(false, false, false) == CloseUp.Pose.ToTheView;
        if (turn)
        {
            // (three-quarters to the lens, her shield side away: square on, the shield hid her waist and hips)
            // (--close-turn R: pictures only, her turn from the lens in radians; -0.6 the mirror, her left side to it)
            pv.Turned = cam.Yaw + CloseTurn;
            pv.Watch = cam.Camera;
        }
        else if (closeDrives) { pv.Turned = null; pv.Watch = null; }
        // (--spots holds the close view where play would not: lit as play lights it there.)
        bool night = scene.View.Night == true, lit = (!held || spotClose != null) && near > 0.05f;
        float day = Mathf.Clamp((near - 0.3f) / 0.4f, 0, 1);
        if (lit) pv.LampScale = Mathf.Lerp(1, night ? CloseLampByNight : CloseLampByDay, day);
        else if (closeDrives) pv.LampScale = 1;
        pv.LampOffHer = lit && night && day > 0.5f && CloseLampOffHer;
        // By night the camp's fire stood behind the lens and lit both her cheeks alike: it is kept off her (her own
        // layer), and a share of it, from where it burns and flickering as it does, stays on her as her warm fill.
        bool own = pv.LampOffHer && CloseFireShare < 1;
        if (own != pv.OwnLayer) { pv.OwnLayer = own; scene.View.HerUnlit(own); }
        FireOnHer(own, pv);
        closeDrives = turn || lit;
        // By day the sun is behind or above her: a soft key of her own, 40 degrees off the lens on the side she
        // turns to and 25 up, on people only (layer 2), so her face is modelled, not flat. By night her ember's
        // warm light, 40 degrees off the lens and 30 up (from above her head and in front it lit her face flat,
        // as a flash would: E1 round 2), with the moon's cool rim from behind on her other side, so she stands
        // out from the wood behind her, not pasted on it.
        if (closeKey == null || !IsInstanceValid(closeKey) || closeKey.GetParent() != scene)
        {
            closeKey = new SpotLight3D { LightColor = new Color(1f, 0.95f, 0.88f), SpotAngle = 24, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = 2 | SurvivorUnchained.View.PlayerView.HerLayers, LightSpecular = 0.3f, LightEnergy = 0 };
            scene.AddChild(closeKey);
        }
        if (closeRim == null || !IsInstanceValid(closeRim) || closeRim.GetParent() != scene)
        {
            // (On her and people, not her hair (PlayerView.HerHairLayer): from behind it lifted her copper crown.)
            closeRim = new SpotLight3D { LightColor = new Color("#a9c4ff"), SpotAngle = 26, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = 2 | SurvivorUnchained.View.PlayerView.HerLayer, LightSpecular = CloseRimSpec, LightEnergy = 0 };
            scene.AddChild(closeRim);
        }
        // Its twin on her gear (PlayerView.HerGearLayer: weapon, armor, buckles), the same light with the sheen her skin
        // no longer takes: with the rim's sheen at 0 her axe head went flat black (judge J1, face 36).
        if (closeRimGear == null || !IsInstanceValid(closeRimGear) || closeRimGear.GetParent() != scene)
        {
            closeRimGear = new SpotLight3D { LightColor = closeRim.LightColor, SpotAngle = 26, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = SurvivorUnchained.View.PlayerView.HerGearLayer, LightSpecular = CloseRimGearSpec, LightEnergy = 0 };
            scene.AddChild(closeRimGear);
        }
        closeKey.LightColor = night ? CloseKeyColourNight : CloseKeyColourDay;
        float want = lit ? (night ? CloseKeyNight : CloseKey) * day : 0;
        closeKey.LightEnergy = Mathf.Lerp(closeKey.LightEnergy, want, 1 - Mathf.Exp(-3 * (float)dt));
        closeKey.Visible = closeKey.LightEnergy > 0.005f;
        var chest = pv.GlobalPosition + new Vector3(0, 1.55f, 0);
        if (closeKey.Visible)
        {
            // (By night: the key CloseKeyAzNight degrees off her face, on the lens's side of it. She stands turned 0.6 rad
            // from the lens, so round 2's key at 0.7 rad was 6 degrees off her face: frontal, flat, waxy.)
            float a = cam.Yaw + 0.6f - Mathf.DegToRad(night ? CloseKeyAzNight : CloseKeyAzDay), up = Mathf.DegToRad(night ? CloseKeyElNight : CloseKeyElDay);
            closeKey.GlobalPosition = chest + new Vector3(Mathf.Sin(a) * Mathf.Cos(up), Mathf.Sin(up), Mathf.Cos(a) * Mathf.Cos(up)) * 2.6f;
            closeKey.LookAt(chest);
        }
        // By day her share of the sky's light comes down in the close view (her skin only, the town as it is): the waystation's
        // grey-blue sky (hemi 0.9, env 0.8) was the largest light on her face and lay level on every plane. With it off, the
        // shade side of her jaw went 45 to 31.7 Oklab L, her forehead 74 to 68: the flat, pale, flash-lit look was the sky's.
        // (Set each frame while it is in force: her skin is made again when her look changes.)
        float sky = lit && !night ? Mathf.Lerp(1, CloseSkyDay, day) : 1;
        // (Her body from her collarbones down keeps more of it, CloseSkyBody: no key reaches the underside and inner slope of
        // her breast, lit by the sky alone; at 0.45 the pocket between her cups by the gore read as a dent (dent d2).)
        float skyBody = CloseSkyBody < 0 ? -1 : lit && !night ? Mathf.Lerp(1, CloseSkyBody, day) : 1;
        if (sky != 1 || skyShown != 1) { skyShown = sky; SurvivorUnchained.View.People.HerSkyShare(pv.Person, sky, sky == 1 ? -1 : skyBody); }
        // (her eyes by night, under the night key: the lids' shade eased and the iris lifted, People.HerEyesNight)
        float en = lit && night ? day : 0;
        if (en != 0 || eyesNight != 0) { eyesNight = en; SurvivorUnchained.View.People.HerEyesNight(pv.Person, en); SurvivorUnchained.View.People.HerSkinHold(pv.Person, en); }
        air.SetViewExposure(lit && night ? Mathf.Lerp(1, CloseExposureNight, day) : 1);
        air.SetViewHighlights(lit ? (night ? day : CloseGradeDay * day) : 0);
        float wantRim = lit && night ? CloseRimNight * day : 0;
        closeRim.LightEnergy = Mathf.Lerp(closeRim.LightEnergy, wantRim, 1 - Mathf.Exp(-3 * (float)dt));
        closeRim.Visible = closeRim.LightEnergy > 0.005f;
        if (closeRim.Visible)
        {
            // Behind her, on the side away from the key (her far cheek's), CloseRimEl degrees up.
            float a = cam.Yaw + Mathf.Pi - CloseRimAz, up = Mathf.DegToRad(CloseRimEl);
            closeRim.GlobalPosition = chest + new Vector3(Mathf.Sin(a) * Mathf.Cos(up), Mathf.Sin(up), Mathf.Cos(a) * Mathf.Cos(up)) * 2.4f;
            closeRim.LookAt(chest + new Vector3(0, 0.15f, 0));
        }
        closeRimGear.LightEnergy = closeRim.LightEnergy * CloseRimGearGain;
        closeRimGear.Visible = closeRim.Visible && closeRimGear.LightEnergy > 0.005f;
        if (closeRimGear.Visible)
        {
            // (from behind her at CloseRimGearAz off straight behind (the rim's own side by default), as low as the rim)
            float a = cam.Yaw + Mathf.Pi - CloseRimGearAz, up = Mathf.DegToRad(CloseRimEl);
            closeRimGear.GlobalPosition = chest + new Vector3(Mathf.Sin(a) * Mathf.Cos(up), Mathf.Sin(up), Mathf.Cos(a) * Mathf.Cos(up)) * 2.4f;
            closeRimGear.LookAt(chest + new Vector3(0, 0.15f, 0));
        }
        // --body-rim E (Body 20 light test, 27 Oct; the arm judge: "under the close-up's soft frontal light shallow forms barely
        // read"): a soft rim on her (people, layer 2, as the key; by night her own layer), from behind her on the
        // key's far side, aimed below her shoulders, so her arms' outline and broad planes read. 0: off, as before.
        // --body-rim-night E (by night; default the day's), --body-rim-az A (radians off straight behind her, toward the rim's
        // side), --body-rim-el D (degrees up), --body-rim-spec S, --body-rim-colour R,G,B.
        if (closeBodyRim == null || !IsInstanceValid(closeBodyRim) || closeBodyRim.GetParent() != scene)
        {
            closeBodyRim = new SpotLight3D { LightColor = BodyRimColour, SpotAngle = 30, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = 2 | SurvivorUnchained.View.PlayerView.HerLayer, LightSpecular = BodyRimSpec, LightEnergy = 0 };
            scene.AddChild(closeBodyRim);
        }
        float wantBody = lit ? (night ? BodyRimNight : BodyRimDay) * day : 0;
        closeBodyRim.LightEnergy = Mathf.Lerp(closeBodyRim.LightEnergy, wantBody, 1 - Mathf.Exp(-3 * (float)dt));
        closeBodyRim.Visible = closeBodyRim.LightEnergy > 0.005f;
        if (closeBodyRim.Visible)
        {
            float a = cam.Yaw + Mathf.Pi - BodyRimAz, up = Mathf.DegToRad(BodyRimEl);
            var arms = pv.GlobalPosition + new Vector3(0, 1.2f, 0);
            closeBodyRim.GlobalPosition = arms + new Vector3(Mathf.Sin(a) * Mathf.Cos(up), Mathf.Sin(up), Mathf.Cos(a) * Mathf.Cos(up)) * 2.4f;
            closeBodyRim.LookAt(arms);
        }
    }

    void FireOnHer(bool own, SurvivorUnchained.View.PlayerView pv)
    {
        var src = own ? scene!.View.NearestLit(pv.GlobalPosition, 12) : null;
        if (src == null) { if (fireFill != null && IsInstanceValid(fireFill)) fireFill.Visible = false; return; }
        if (fireFill == null || !IsInstanceValid(fireFill) || fireFill.GetParent() != scene)
        {
            fireFill = new OmniLight3D { Name = "CloseFireFill", ShadowEnabled = false, LightCullMask = SurvivorUnchained.View.PlayerView.HerLayers };
            scene!.AddChild(fireFill);
        }
        fireFill.GlobalPosition = src.GlobalPosition;
        fireFill.LightColor = src.LightColor;
        fireFill.LightEnergy = src.LightEnergy * CloseFireShare;
        fireFill.OmniRange = src.OmniRange;
        fireFill.OmniAttenuation = src.OmniAttenuation;
        fireFill.LightSpecular = src.LightSpecular;
        fireFill.Visible = true;
    }

    SpotLight3D? closeKey, closeRim, closeRimGear, closeBodyRim;
    static float BodyRimDay => Args.Num("body-rim", 0f);
    static float BodyRimNight => Args.Num("body-rim-night", BodyRimDay);
    static float BodyRimAz => Args.Num("body-rim-az", 0.9f);
    static float BodyRimEl => Args.Num("body-rim-el", 15f);
    static float BodyRimSpec => Args.Num("body-rim-spec", 0.2f);
    static readonly Color BodyRimColour = Args.Get("body-rim-colour") is string brc && brc.Split(',') is { Length: 3 } bc
        ? new Color(float.Parse(bc[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(bc[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(bc[2], System.Globalization.CultureInfo.InvariantCulture))
        : new Color(1f, 0.93f, 0.84f);
    float skyShown = 1;
    float eyesNight;
    OmniLight3D? fireFill;
    // --close-fire K: the camp fire's share on her in the close view by night (1: all of it, as play; judge 3 found it
    // filled her shadow side almost to her lit side). Art style round 2 (20 Oct): 0.75, rim 3, night key 2.2, under the paint grade.
    static float CloseFireShare => Args.Num("close-fire", 0.9f);   // (G1 r3: 0.9; 1.0 puts her back on the world's fire layer, crown L 47.7 vs 46.8)
    // --close-key-night E, --close-rim E, --close-lamp-night L: the night key, the moon's rim and her lamp's share by night (pictures).
    static float CloseKeyNight => Args.Num("close-key-night", 1.7f);   // (G1 r3: 2.2 to 1.7)
    // --close-key-el D: the night key's elevation (degrees).
    static float CloseKeyElNight => Args.Num("close-key-el", 18f);
    // (G1 r2: rim 3.0 to 1.0 and down from 35 degrees to 10, the key from 30 to 18: from above they lifted her copper crown
    // pinkish-tan, toward strawberry blonde (crown Oklab L 52.6, 44.9 now, her face 79.9 and 79.4: the crown to face of
    // art style r2's frame, 0.56); low, the rim's cool edge grazes her shoulders and arms.)
    static float CloseRimNight => Args.Num("close-rim", 3f);   // (G1 r3: 1.5; 3 lifted the crown to 47.9 at frame 03, at az 0.9 it fills her shade side. G1 r4: 3, off her hair (PlayerView.HerHairLayer): her far edge +4.4 to +5.1 L at hue 240, the crown 39.7 as without it)
    // --close-rim-spec S: the moon rim's sheen (Light3D.light_specular). At 0.6 it lay down the side of her neck as a broad
    // pale lavender band, plastic not skin (the owner's night close-up, 21 Oct; face 35: band Oklab L 51 C 4.3 hue -67, at 0
    // L 38.7 hue -5, her warm skin), and read as a lump on her left neck.
    static float CloseRimSpec => Args.Num("close-rim-spec", 0f);
    // --close-rim-gear-spec S: the rim's sheen on her gear (its twin on PlayerView.HerGearLayer; 0.6, the rim's before face 35).
    static float CloseRimGearSpec => Args.Num("close-rim-gear-spec", 0.6f);
    // --close-rim-gear-az R, --close-rim-gear-gain G: the gear twin's angle off straight behind her (radians, + toward her far
    // cheek as CloseRimAz) and its light against the rim's. -1.2: from behind on her weapon's side, so the axe head at her hip
    // reads as moonlit steel (mean 9 of 255 by night before, flat black; 17 by the night key alone once on her gear layer; 59
    // with the twin there); at the rim's own 0.5 it never reached the axe (face 36).
    static float CloseRimGearAz => Args.Num("close-rim-gear-az", -1.2f);
    static float CloseRimGearGain => Args.Num("close-rim-gear-gain", 1f);
    // --close-rim-el D: the rim's elevation (degrees).
    static float CloseRimEl => Args.Num("close-rim-el", 10f);
    // --close-rim-az R: the rim's angle off straight behind her (radians, toward her far cheek's side).
    static float CloseRimAz => Args.Num("close-rim-az", 0.5f);
    static float CloseLampByNight => Args.Num("close-lamp-night", 0.8f);
    // --close-lamp-on-her: by night her lamp lights her too in the close view (before E1 round 3c it did, and filled her face flat).
    static bool CloseLampOffHer => !Args.Has("close-lamp-on-her");
    // --close-exp-night X: the close view's exposure by night against play's (pictures).
    // (Round 3: 2.0 left her face pale at 187; 0.35 of a stop under it brings it to about 165.)
    static float CloseExposureNight => Args.Num("close-exp-night", 1.2f);   // (G1 r4: 1.35 to 1.2: at 1.35 a third of her lit face sat above Oklab L 85 at the tonemap's shoulder, flat and pale; earlier: x the preset's 1.5: face ~145-150 (judge 3 fix; round 3c's 1.465 left it pale at 170, the fire filling it))
    // --close-key-az D: the night key's angle off her face (degrees), toward the lens, so her far cheek falls into half
    // shade (E1 round 3: 50-60; judge 3 fix: 90, about 55 degrees off the lens on the fire's side, once the fire no longer filled her).
    // The key's colour: the ember's, saturated (1.0, 0.6, 0.35).
    static float CloseKeyAzNight => Args.Num("close-key-az", 90f);
    static readonly Color CloseKeyColourNight = new(1f, 0.6f, 0.35f);
    // --close-key E, --close-lamp L: the day key's strength and her lamp's share by day, for pictures.
    static float CloseKey => Args.Has("close-key") ? Args.Num("close-key", 0.7f) : 0.7f;
    // --close-key-az-day D, --close-key-el-day D: the day key's angle off her face toward the lens, and its elevation (degrees).
    // (Before face 34 it stood 0.7 rad off the lens, 6 degrees off her face (she turns 0.6 from it): frontal, her face flat under the town's day light.)
    // (Face 34: -30, 64 degrees off the lens on the sun's side, warmer (1, 0.8, 0.66) against the sun's yellow (lit cheek hue 65
    // against the Look's 51), with her sky share at 0.45: lit cheek 74.1 to 69.9 Oklab L (the night close-up's 69.9), shade
    // cheek 58 to 46, cheek split -16 to -24, forehead to jaw sides +18 (the night's +18.4).)
    static float CloseKeyAzDay => Args.Num("close-key-az-day", -30f);
    static float CloseKeyElDay => Args.Num("close-key-el-day", 25f);
    // --close-sky-day S: her share of the sky's light in the close view by day (1: as play).
    static float CloseSkyDay => Args.Num("close-sky-day", 0.45f);
    // --close-sky-body S: her body's share from her collarbones down (-1: as her face's, CloseSkyDay). 1, as in play (dent d2,
    // warden close-up: the pocket between her cups by the gore 49.7 to 71.0/255, the arcanist's V 60.1 to 77.4, her face
    // unchanged; before face 34's light it was 82.2 and 88.1; 1.25 gives 78.8 and 84.2).
    static float CloseSkyBody => Args.Num("close-sky-body", 1f);
    // --close-key-colour-day R,G,B: the day key's colour. --close-grade-day K: how much of the close view's own grade
    // (the night's and the Look's paint grade, Atmosphere.ViewGrade) it takes by day (0: play's; at 1 her cheek's chroma 6.5 to 6.4, so 0).
    static readonly Color CloseKeyColourDay = Args.Get("close-key-colour-day") is string kcd && kcd.Split(',') is { Length: 3 } kd
        ? new Color(float.Parse(kd[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(kd[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(kd[2], System.Globalization.CultureInfo.InvariantCulture))
        : new Color(1f, 0.8f, 0.66f);
    static float CloseGradeDay => Args.Num("close-grade-day", 0f);
    static float CloseLampByDay => Args.Has("close-lamp") ? Args.Num("close-lamp", 0.25f) : 0.25f;
}

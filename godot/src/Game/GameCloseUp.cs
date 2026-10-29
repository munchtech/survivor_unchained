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
            if (scene?.Player is { } pv0) { pv0.FolkScale = 1; pv0.PoolScale = 1; pv0.LampOffHer = false; if (pv0.OwnLayer) { pv0.OwnLayer = false; scene.View.HerUnlit(false); } }
            if (scene?.Player is { } pv1 && skyShown != 1) { skyShown = 1; SurvivorUnchained.View.People.HerSkyShare(pv1.Person, 1); }
            if (scene?.Player is { } pv2 && eyesNight != 0) { eyesNight = 0; SurvivorUnchained.View.People.HerEyesNight(pv2.Person, 0); SurvivorUnchained.View.People.HerSkinHold(pv2.Person, 0); }
            if (fireFill != null && IsInstanceValid(fireFill)) fireFill.Visible = false;
            if (closeFill != null && IsInstanceValid(closeFill)) { closeFill.LightEnergy = 0; closeFill.Visible = false; }
            if (groundKey != null && IsInstanceValid(groundKey)) groundKey.Visible = false;
            TownLampsDim(1);
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
        pv.FolkScale = FolkScaleFor(pv, night, lit ? day : 0, out float nearLamp);
        pv.PoolScale = Mathf.Lerp(1, PoolNearLamp, nearLamp);
        // (and in the town's close view by night, CloseTownPool: from her hand her pool lit the stall's awning beside her as
        // bright as her face, tnight_02; the town's lamps light its ground)
        if (night && IsTown && lit) pv.PoolScale *= Mathf.Lerp(1, CloseTownPool, day);
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
            // (Rendering 1: off her hair (PlayerView.HerHairLayer), which takes its twin, closeKeyHair, in the ember's orange at
            // CloseKeyHair of its light: at 3000K and twice the light (the exposure down) it lifted her copper toward strawberry blonde.)
            closeKey = new SpotLight3D { LightColor = new Color(1f, 0.95f, 0.88f), SpotAngle = 24, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = 2 | SurvivorUnchained.View.PlayerView.HerLayer, LightSpecular = 0.3f, LightEnergy = 0 };
            scene.AddChild(closeKey);
            // (Rendering 2, judge j1 D3 "the sword tip blazes white, the brightest thing in the frame": its twin on her gear
            // (PlayerView.HerGearLayer) with CloseKeyGearSpec of the sheen: at 0.3 the key's highlight ran up the blade clipped.)
            closeKeyGear = new SpotLight3D { SpotAngle = 24, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = SurvivorUnchained.View.PlayerView.HerGearLayer, LightSpecular = CloseKeyGearSpec, LightEnergy = 0 };
            scene.AddChild(closeKeyGear);
            closeKeyHair = new SpotLight3D { LightColor = CloseKeyHairColour, SpotAngle = 24, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = SurvivorUnchained.View.PlayerView.HerHairLayer, LightSpecular = 0.3f, LightEnergy = 0 };
            scene.AddChild(closeKeyHair);
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
        closeKey.ShadowEnabled = night && CloseKeyShadow; closeKey.LightSize = 0.15f;
        closeKeyHair!.LightColor = night ? CloseKeyHairColour : closeKey.LightColor;
        closeKeyHair.LightEnergy = closeKey.LightEnergy * (night ? CloseKeyHair : 1);
        closeKeyHair.Visible = closeKey.Visible;
        closeKeyGear!.LightColor = closeKey.LightColor; closeKeyGear.LightEnergy = closeKey.LightEnergy; closeKeyGear.Visible = closeKey.Visible;
        closeKeyGear.LightSpecular = night ? CloseKeyGearSpec : 0.3f;
        var chest = pv.GlobalPosition + new Vector3(0, 1.55f, 0);
        if (closeKey.Visible)
        {
            // (By night: the key CloseKeyAzNight degrees off her face, on the lens's side of it. She stands turned 0.6 rad
            // from the lens, so round 2's key at 0.7 rad was 6 degrees off her face: frontal, flat, waxy.)
            float a = cam.Yaw + 0.6f - Mathf.DegToRad(night ? CloseKeyAzNight : CloseKeyAzDay), up = Mathf.DegToRad(night ? CloseKeyElNight : CloseKeyElDay);
            // Rendering 1 (judge j0 B3/B6a, "a warm frontal light lights her and nothing else"): the key comes from the named
            // source's side, as the scene lights her. By night the nearest lit fire or lamp (12 m), else the moon: from where
            // it stands, so turned away from the fire her face falls into shade and the key rims her cheek. By day the sun's
            // side, held within CloseKeySunHold degrees of the lens so the sun behind her still models her face from its side.
            // (--close-key-src 0: the lens-relative key before.)
            if (KeySourceDir(night, pv) is { } toSrc)
            {
                a = Mathf.Atan2(toSrc.X, toSrc.Z);
                if (!night || CloseKeySrcLamp == null)
                {
                    float lens = cam.Yaw, d = Mathf.Wrap(a - lens, -Mathf.Pi, Mathf.Pi), hold = Mathf.DegToRad(CloseKeySunHold);
                    a = lens + Mathf.Clamp(d, -hold, hold);
                }
                // Rendering 2 (judge j1 C, lfclosedeep_01 "her face is a silhouette"): a fire behind her lights her back, not her
                // face; the key is held within CloseKeyFaceHold degrees of the way she faces, so she is never keyed from behind.
                {
                    float face = pv.GlobalRotation.Y, d = Mathf.Wrap(a - face, -Mathf.Pi, Mathf.Pi), hold = Mathf.DegToRad(CloseKeyFaceHold);
                    a = face + Mathf.Clamp(d, -hold, hold);
                }
                // Rendering 2 (judge j1 E4, tnight_02/tcloseN_00/tdawn_01 "soft front light"): in the town, by night and at dawn
                // and dusk, the key CloseKeyTownOff degrees (min,max) off the lens, on the named source's side.
                if (IsTown && (night || SurvivorUnchained.View.Atmosphere.TownLit > 0.5f) && CloseKeyTownOff is { } to)
                {
                    float lens = cam.Yaw, d = Mathf.Wrap(a - lens, -Mathf.Pi, Mathf.Pi);
                    a = lens + (d < 0 ? -1 : 1) * Mathf.Clamp(Mathf.Abs(d), Mathf.DegToRad(to.X), Mathf.DegToRad(to.Y));
                }
                // Rendering 3 (judge j2 D2, lfclose_00/01 "a flat key from near the camera axis"): out of the town by night the
                // key CloseKeyWildOff degrees (min,max) off the lens on the side she faces, then held within the face hold again,
                // so her face is modelled three-quarters and the shield in front of her takes the key grazing.
                else if (night && CloseKeyWildOff is { } wo)
                {
                    float lens = cam.Yaw, face = pv.GlobalRotation.Y, fd = Mathf.Wrap(face - lens, -Mathf.Pi, Mathf.Pi);
                    a = lens + (fd < 0 ? -1 : 1) * Mathf.Clamp(Mathf.Abs(Mathf.Wrap(a - lens, -Mathf.Pi, Mathf.Pi)), Mathf.DegToRad(wo.X), Mathf.DegToRad(wo.Y));
                    float d = Mathf.Wrap(a - face, -Mathf.Pi, Mathf.Pi), hold = Mathf.DegToRad(CloseKeyFaceHold);
                    a = face + Mathf.Clamp(d, -hold, hold);
                }
            }
            closeKey.GlobalPosition = chest + new Vector3(Mathf.Sin(a) * Mathf.Cos(up), Mathf.Sin(up), Mathf.Cos(a) * Mathf.Cos(up)) * 2.6f;
            closeKey.LookAt(chest);
            closeKeyHair!.GlobalTransform = closeKey.GlobalTransform;
            // (Rendering 3: her hair's twin stays at CloseKeyHairEl, as the key stood before: from 30 up it lifted her copper crown.)
            if (night && CloseKeyHairEl >= 0)
            {
                float hu = Mathf.DegToRad(CloseKeyHairEl);
                closeKeyHair.GlobalPosition = chest + new Vector3(Mathf.Sin(a) * Mathf.Cos(hu), Mathf.Sin(hu), Mathf.Cos(a) * Mathf.Cos(hu)) * 2.6f;
                closeKeyHair.LookAt(chest);
            }
            closeKeyGear!.GlobalTransform = closeKey.GlobalTransform;
            GroundKey(night, pv, a, closeKey.LightEnergy);
            if (CamLog) GD.Print($"closekey face={Mathf.RadToDeg(Mathf.Wrap(a - pv.GlobalRotation.Y, -Mathf.Pi, Mathf.Pi)):F0} night={night} src={(CloseKeySrcLamp != null ? CloseKeySrcLamp.Name + "@" + CloseKeySrcLamp.GlobalPosition.ToString("F1") + " E" + CloseKeySrcLamp.LightEnergy.ToString("F1") + " c" + CloseKeySrcLamp.LightColor.ToHtml(false) : "sky")} her={pv.GlobalPosition.ToString("F1")} yaw={Mathf.RadToDeg(cam.Yaw):F0} a={Mathf.RadToDeg(Mathf.Wrap(a - cam.Yaw, -Mathf.Pi, Mathf.Pi)):F0} off lens, E={closeKey.LightEnergy:F2}");
        }
        else GroundKey(night, pv, 0, 0);
        TownLampsDim(lit && night && IsTown ? Mathf.Lerp(1, CloseTownLamps, day) : 1);
        if (CamLog) FacePx(pv.Person);
        // A weak cool fill from the lens's side away from the key (by night), so the shade side reads, never black.
        if (closeFill == null || !IsInstanceValid(closeFill) || closeFill.GetParent() != scene)
        {
            closeFill = new SpotLight3D { LightColor = CloseFillColourNight, SpotAngle = 26, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = 2 | SurvivorUnchained.View.PlayerView.HerLayers, LightSpecular = 0f, LightEnergy = 0 };
            scene.AddChild(closeFill);
        }
        // (Rendering 3, judge j2 D2: CloseFillRatio on fair skin, up by CloseFillDeep of the key on the darkest, People.HerSkinDark:
        // with the key 50-60 degrees off the lens deep skin's shade side went to 8-16 of 255, near silhouette)
        float fillRatio = CloseFillRatio + CloseFillDeep * SurvivorUnchained.View.People.HerSkinDark(pv.Person);
        float wantFill = lit && night ? (CloseFillNight > 0 ? CloseFillNight : CloseKeyNight * fillRatio) * day : 0;
        closeFill.LightEnergy = Mathf.Lerp(closeFill.LightEnergy, wantFill, 1 - Mathf.Exp(-3 * (float)dt));
        closeFill.Visible = closeFill.LightEnergy > 0.005f;
        if (closeFill.Visible)
        {
            var kd = closeKey.GlobalPosition - chest;
            float ka = Mathf.Atan2(kd.X, kd.Z), side = Mathf.Wrap(ka - cam.Yaw, -Mathf.Pi, Mathf.Pi) >= 0 ? -1 : 1;
            float fa = cam.Yaw + side * Mathf.DegToRad(35), fu = Mathf.DegToRad(10);
            closeFill.GlobalPosition = chest + new Vector3(Mathf.Sin(fa) * Mathf.Cos(fu), Mathf.Sin(fu), Mathf.Cos(fa) * Mathf.Cos(fu)) * 2.6f;
            closeFill.LookAt(chest);
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
        // (Rendering 1: at dawn and dusk (Atmosphere.TownLit) the close view stops down CloseExposureDusk: the low sun left her face waxy at 185-189.)
        air.SetViewExposure(lit ? Mathf.Lerp(1, night ? CloseExposureNight : SurvivorUnchained.View.Atmosphere.TownLit > 0.5f ? CloseExposureDusk : 1, day) : 1);
        air.SetViewHighlights(lit ? (night ? day : CloseGradeDay * day) : 0);
        // (Rendering 2: the grade's skin guard (Atmosphere.SkinGuard) by night, dawn and dusk, where warm keys turned deep skin copper.)
        air.SetViewSkinGuard(lit && (night || SurvivorUnchained.View.Atmosphere.TownLit > 0.5f) ? day : 0);
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
        // (Rendering 1: the fire's own orange toward the key's 3000K on her, CloseFireWarm: its full orange turned fair skin
        // apricot and deep skin rust-red, judge j0 C2.)
        fireFill.LightColor = src.LightColor.Lerp(CloseKeyColourNight, CloseFireToKey);
        // (Rendering 3, judge j2 D5, tnight_02 "lit soft from the front": a source near the lens's line fills both her cheeks alike;
        // its share eased to CloseFireFront of it within 25 degrees of the lens, whole from 60.)
        var ts = src.GlobalPosition - pv.GlobalPosition;
        float off = Mathf.Abs(Mathf.RadToDeg(Mathf.Wrap(Mathf.Atan2(ts.X, ts.Z) - cam.Yaw, -Mathf.Pi, Mathf.Pi)));
        float front = Mathf.Lerp(CloseFireFront, 1, Mathf.SmoothStep(25, 60, off));
        fireFill.LightEnergy = (lampDim.TryGetValue(src, out var ld) && Mathf.IsEqualApprox(src.LightEnergy, ld.Set) ? ld.Base : src.LightEnergy) * CloseFireShare * front;   // (undimmed: CloseTownLamps is the world's, not hers)
        fireFill.OmniRange = src.OmniRange;
        fireFill.OmniAttenuation = src.OmniAttenuation;
        fireFill.LightSpecular = src.LightSpecular;
        fireFill.Visible = true;
    }

    double facePxAt = -1;
    /// <summary>--camlog: her eyes' place on the screen and the pixels a decimetre spans there, a few times a second (Rendering 1's face measure).</summary>
    void FacePx(SurvivorUnchained.View.People.Person who)
    {
        if (Shots.Clock - facePxAt < 0.2) return;
        facePxAt = Shots.Clock;
        var e = SurvivorUnchained.View.People.EyesOf(who);
        var c = camera.UnprojectPosition(e); var r = camera.UnprojectPosition(e + camera.GlobalBasis.X * 0.1f);
        GD.Print($"facepx t={Shots.Clock:F2} x={c.X:F0} y={c.Y:F0} s={(r - c).Length():F1}");
    }
    /// <summary>The way (level, unit) from her to the key's source: by night the nearest lit fire or lamp, else the moon;
    /// by day the sun. Null with --close-key-src 0 (the lens-relative key).</summary>
    Vector3? KeySourceDir(bool night, SurvivorUnchained.View.PlayerView pv)
    {
        CloseKeySrcLamp = null;
        if (!CloseKeySrc) return null;
        Vector3 d;
        if (night && scene!.View.NearestLit(pv.GlobalPosition, CloseKeySrcRange) is { } src)
        {
            CloseKeySrcLamp = src;
            d = src.GlobalPosition - pv.GlobalPosition;
        }
        else d = air.Key.GlobalTransform.Basis.Z;   // (a directional light shines along its -Z)
        d.Y = 0;
        return d.LengthSquared() < 0.01f ? null : d.Normalized();
    }
    OmniLight3D? CloseKeySrcLamp;
    // --close-key-src 0|1: the key from the scene's source (1, Rendering 1) or lens-relative as before (0).
    static readonly bool CloseKeySrc = Args.Num("close-key-src", 1) != 0;
    // --close-key-src-range M: how near a fire or lamp must burn to key her by night (m; beyond it the moon keys her).
    static float CloseKeySrcRange => Args.Num("close-key-src-range", 12f);
    // --close-key-sun-hold D: by day (and by moonlight) the key keeps to within D degrees of the lens on the sun's side.
    // --close-exp-dusk X: the close view's exposure at dawn and dusk against play's.
    static float CloseExposureDusk => Args.Num("close-exp-dusk", 0.85f);
    static float CloseKeySunHold => Args.Num("close-key-sun-hold", 70f);
    // --close-fire-to-key K: the fire's colour on her toward the key's (0: the fire's own orange).
    static float CloseFireToKey => Args.Num("close-fire-to-key", 1f);
    // --close-fill-night E: a weak cool fill by night from the lens's side away from the key (0: none, as before).
    static float CloseFillNight => Args.Num("close-fill-night", 0f);
    // --close-fill-ratio R (Rendering 2, judge j1 C: "a cool fill of at least 1/3 of the key on the face side"): the night fill at
    // R of the night key (0.2: at 0.33 it lit the lens-side of her face flat at the Low Ford fire; 0.2 keeps the deep face read at lfclosedeep_01) when --close-fill-night is not given.
    static float CloseFillRatio => Args.Num("close-fill-ratio", 0.25f);
    // --close-fill-deep D: the night fill's ratio up by D on the darkest skin (Rendering 3).
    static float CloseFillDeep => Args.Num("close-fill-deep", 0.6f);
    // --close-key-face-hold D: the key within D degrees of the way she faces (Rendering 2).
    static float CloseKeyFaceHold => Args.Num("close-key-face-hold", 100f);
    // --close-key-town MIN,MAX: in the town by night, dawn and dusk the key MIN-MAX degrees off the lens (Rendering 2); "off": as the source stands.
    static readonly Vector2? CloseKeyTownOff = Args.Get("close-key-town") is string ckt ? (ckt == "off" ? null : ckt.Split(',') is [var t0, var t1]
        ? new Vector2(float.Parse(t0, System.Globalization.CultureInfo.InvariantCulture), float.Parse(t1, System.Globalization.CultureInfo.InvariantCulture)) : new Vector2(50, 60)) : new Vector2(50, 60);
    bool IsTown => scene?.View.Data.Id == "waystation";

    // Rendering 2 (judge j1 E2, lfclose_00/deep_00 "still spotlit: the key lights only her, the grass beside her stays blue"): the key's
    // light on the world as well. A warm light of the key's colour on her side of the key's source, CloseGroundAt (m out level from
    // her feet, m up), on everything but people (the key lights them), with her shadow, so the ground and grass round her take the
    // fire she is keyed by. A spot from high on the key's side aimed at her feet, CloseGroundCone degrees wide with a soft edge: an
    // omni at her height on the world's layers blew her shield (the world's layer 1, her gear's too) cream-white near the lens,
    // while from above the shield's and the sword's upright faces take it grazing, the ground square on. Night only, the close view only.
    // --close-ground E (its energy per unit of the key's; 0: off), --close-ground-at OUT,UP, --close-ground-range M, --close-ground-att A,
    // --close-ground-cone D, --close-ground-shadow 0/1.
    static float CloseGround => Args.Num("close-ground", 7f);
    static float CloseGroundCone => Args.Num("close-ground-cone", 45f);
    static readonly Vector2 CloseGroundAt = Args.Get("close-ground-at") is string cga && cga.Split(',') is [var g0, var g1]
        ? new Vector2(float.Parse(g0, System.Globalization.CultureInfo.InvariantCulture), float.Parse(g1, System.Globalization.CultureInfo.InvariantCulture)) : new Vector2(2.5f, 5f);
    static float CloseGroundRange => Args.Num("close-ground-range", 12f);
    static float CloseGroundAtt => Args.Num("close-ground-att", 1f);
    static bool CloseGroundShadow => Args.Num("close-ground-shadow", 1) != 0;
    SpotLight3D? groundKey;
    void GroundKey(bool night, SurvivorUnchained.View.PlayerView pv, float a, float keyE)
    {
        // (Rendering 3, judge j2 D5: not in the town, whose lamps light its ground: from 5 m up it lit the stall's awning and post
        // over her face at tnight_02. --close-ground-town: there too.)
        bool on = night && keyE > 0.005f && CloseGround > 0 && (!IsTown || Args.Has("close-ground-town"));
        if (!on) { if (groundKey != null && IsInstanceValid(groundKey)) groundKey.Visible = false; return; }
        if (groundKey == null || !IsInstanceValid(groundKey) || groundKey.GetParent() != scene)
        {
            groundKey = new SpotLight3D { Name = "CloseGroundKey", LightSpecular = 0.2f, SpotAngleAttenuation = 0.6f, ShadowBlur = 2f,
                LightCullMask = 0xFFFFFu & ~2u & ~SurvivorUnchained.View.PlayerView.HerLayers & ~SurvivorUnchained.View.Brush.MaskLayer };
            scene!.AddChild(groundKey);
        }
        groundKey.LightColor = CloseKeyColourNight;
        groundKey.LightEnergy = keyE * CloseGround;
        groundKey.SpotRange = CloseGroundRange; groundKey.SpotAttenuation = CloseGroundAtt; groundKey.SpotAngle = CloseGroundCone;
        groundKey.ShadowEnabled = CloseGroundShadow;
        var way = new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a));
        groundKey.GlobalPosition = pv.GlobalPosition + way * CloseGroundAt.X + Vector3.Up * CloseGroundAt.Y;
        groundKey.LookAt(pv.GlobalPosition + way * 0.5f);
        groundKey.Visible = true;
    }

    // Rendering 2 (judge j1 C/E4, tnight_02: "the lamp-lit wall behind her head only about 2x under her face"): in the town's close
    // view by night its lamp lights (ZoneView's Light#) at CloseTownLamps of their light, the windows (emissive) as they are. Set
    // just before each frame is drawn, over whatever the zone gave them that frame (flicker included), and given back after.
    // --close-town-lamps K (1: as before).
    static float CloseTownLamps => Args.Num("close-town-lamps", 0.5f);
    // --close-src-lamp K: the lamps near her (CloseNearLamp), on the world, a further K in the town's close view by night (Rendering 3,
    // judge j2 D5, tnight_02 "the awning and post brighter than her face": 0.5, a stop; her own share of it, FireOnHer, undimmed).
    static float CloseSrcLampDim => Args.Num("close-src-lamp", 0.5f);
    // --close-near-lamp M: the lamps within M of her take CloseSrcLampDim (the stall's lamp on its awning and post near the lens).
    static float CloseNearLamp => Args.Num("close-near-lamp", 7f);
    readonly System.Collections.Generic.Dictionary<OmniLight3D, (float Base, float Set)> lampDim = new();
    float lampDimK = 1; bool lampDimHooked;
    void TownLampsDim(float k)
    {
        lampDimK = k;
        if (lampDimHooked || k >= 0.999f) return;
        lampDimHooked = true;
        RenderingServer.FramePreDraw += LampDimDraw;
    }
    void LampDimDraw()
    {
        if (scene == null || !IsInstanceValid(scene)) { lampDim.Clear(); return; }
        if (lampDimK >= 0.999f && lampDim.Count == 0) return;
        if (lampDim.Count == 0)
            foreach (var n in scene.View.FindChildren("Light*", "OmniLight3D", true, false))
                if (n is OmniLight3D l) lampDim[l] = (l.LightEnergy, l.LightEnergy);
        foreach (var l in System.Linq.Enumerable.ToArray(lampDim.Keys))
        {
            if (!IsInstanceValid(l)) { lampDim.Remove(l); continue; }
            var (b, set) = lampDim[l];
            // (energy not what was set last: the zone set it again this frame, the new base)
            if (!Mathf.IsEqualApprox(l.LightEnergy, set)) b = l.LightEnergy;
            bool near = lampDimK < 0.999f && scene.Player is { } pn && l.GlobalPosition.DistanceTo(pn.GlobalPosition) < CloseNearLamp;
            l.LightEnergy = b * lampDimK * (near ? CloseSrcLampDim : 1);
            lampDim[l] = (b, l.LightEnergy);
        }
        if (lampDimK >= 0.999f) lampDim.Clear();
    }
    static readonly Color CloseFillColourNight = ArgColour("close-fill-colour-night", new Color(0.72f, 0.82f, 1f));
    static Color ArgColour(string name, Color d) => Args.Get(name) is string s && s.Split(',') is { Length: 3 } p
        ? new Color(float.Parse(p[0], System.Globalization.CultureInfo.InvariantCulture), float.Parse(p[1], System.Globalization.CultureInfo.InvariantCulture), float.Parse(p[2], System.Globalization.CultureInfo.InvariantCulture))
        : d;
    // --close-key-gear-spec S: the night key's sheen on her gear (Rendering 2; 0.3 before).
    static float CloseKeyGearSpec => Args.Num("close-key-gear-spec", 0.08f);
    SpotLight3D? closeKeyGear;
    SpotLight3D? closeKey, closeKeyHair, closeRim, closeRimGear, closeBodyRim, closeFill;
    // --close-key-hair G, --close-key-hair-colour R,G,B: the key's twin on her hair by night (its light against the key's; its colour; default as the key).
    // --close-key-shadow 0|1: by night the key casts her shadows (her hair's on her hairline: without, the key from the fire's
    // low side lit the skin under her hairline as a red patch).
    static bool CloseKeyShadow => Args.Num("close-key-shadow", 0) != 0;   // (off: her gear and the camp's people cast on her face, which went black)
    static float CloseKeyHair => Args.Num("close-key-hair", 1f);
    static Color CloseKeyHairColour => ArgColour("close-key-hair-colour", CloseKeyColourNight);
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
    static float CloseFireShare => Args.Num("close-fire", 0.5f);
    // --close-fire-front K: the fire's share on her when it stands near the lens's line (Rendering 3).
    static float CloseFireFront => Args.Num("close-fire-front", 0.3f);   // (Rendering 1: 0.5, in the key's colour (CloseFireToKey): with the key from the fire's side the fire is the key; at 1.1 it lifted her copper crown to strawberry blonde. G1 r3: 0.9; 1.0 puts her back on the world's fire layer, crown L 47.7 vs 46.8)
    // --close-key-night E, --close-rim E, --close-lamp-night L: the night key, the moon's rim and her lamp's share by night (pictures).
    static float CloseKeyNight => Args.Num("close-key-night", 3.6f);   // (Rendering 1: 3.6 under the exposure's 0.72, her lit cheek where it was. G1 r3: 2.2 to 1.7)
    // --close-key-el D: the night key's elevation (degrees).
    static float CloseKeyElNight => Args.Num("close-key-el", 30f);   // (Rendering 3, judge j2 D2: 18 -> 30, the hair's twin kept at 18)
    // --close-key-hair-el D: the hair twin's elevation by night (-1: the key's).
    static float CloseKeyHairEl => Args.Num("close-key-hair-el", 18f);
    // --close-key-wild MIN,MAX: out of the town by night the key MIN-MAX degrees off the lens on her facing's side (Rendering 3); "off": none.
    // (65-75: at the judge's 50-60 her head, turned near profile to the fire, took the key 30 degrees off her nose on the lens's
    // side, and the fair face stayed flat, 2.3:1 linear at lfclose_00; 65-75 gave 2.9 there and 4.0 at lfclose_01.)
    static readonly Vector2? CloseKeyWildOff = Args.Get("close-key-wild") is string ckw ? (ckw == "off" ? null : ckw.Split(',') is [var w0, var w1]
        ? new Vector2(float.Parse(w0, System.Globalization.CultureInfo.InvariantCulture), float.Parse(w1, System.Globalization.CultureInfo.InvariantCulture)) : new Vector2(65, 75)) : new Vector2(65, 75);
    // --folk-near-lamp K: her folk light inside a town lamp's reach by night (1: as round 2); --folk-near-reach M: the reach (m; eased over its outer half).
    static float FolkNearLamp => Args.Num("folk-near-lamp", 0.5f);
    static float FolkNearReach => Args.Num("folk-near-reach", 3f);
    // --pool-near-lamp K: her pool light there (1: as round 2; 0.1: tnight_01 blown 14.5% -> 1.4%, the lantern lights the ground there).
    static float PoolNearLamp => Args.Num("pool-near-lamp", 0.1f);
    // --close-town-pool K: her pool light in the town's close view by night (Rendering 3; 1: as round 2).
    static float CloseTownPool => Args.Num("close-town-pool", 0.25f);
    /// <summary>Her folk light's share (PlayerView.FolkScale): ducked to FolkNearLamp within FolkNearReach of a town lamp by night (judge
    /// j2 D4: her ember stacked on the lantern ran her body near-white), eased over the outer half of the reach; off in the close
    /// view by night (closeDay, judge j2 D5: the close rig lights her).</summary>
    double folkLogAt = -9;
    float FolkScaleFor(SurvivorUnchained.View.PlayerView pv, bool night, float closeDay, out float nearLamp)
    {
        float k = 1; nearLamp = 0;
        if (night && IsTown && scene!.View.NearestLit(pv.GlobalPosition, 30) is { } l)
        {
            // (metres, not the lamp's range: the town's ranges run 4-13 m, and a brazier's 13 ducked her pool 3.4 m off at tnight_00)
            float r = Mathf.Min(l.OmniRange, FolkNearReach), dd = l.GlobalPosition.DistanceTo(pv.GlobalPosition);
            nearLamp = 1 - Mathf.SmoothStep(0.5f * r, r, dd);
            if (CamLog && Shots.Clock - folkLogAt > 1) GD.Print($"folk lamp {l.Name} d={dd:F1} range={l.OmniRange:F1} E={l.LightEnergy:F2} her={pv.GlobalPosition.ToString("F1")}");
            k = Mathf.Lerp(1, FolkNearLamp, nearLamp);
        }
        if (CamLog && Shots.Clock - folkLogAt > 1) { folkLogAt = Shots.Clock; GD.Print($"folk k={k:F2} close={closeDay:F2} town={IsTown} night={night}"); }
        return night ? k * (1 - closeDay) : k;
    }
    // (G1 r2: rim 3.0 to 1.0 and down from 35 degrees to 10, the key from 30 to 18: from above they lifted her copper crown
    // pinkish-tan, toward strawberry blonde (crown Oklab L 52.6, 44.9 now, her face 79.9 and 79.4: the crown to face of
    // art style r2's frame, 0.56); low, the rim's cool edge grazes her shoulders and arms.)
    static float CloseRimNight => Args.Num("close-rim", 5f);   // (Rendering 1: 5, its light on her as before under the exposure's 0.72. G1 r3: 1.5; 3 lifted the crown to 47.9 at frame 03, at az 0.9 it fills her shade side. G1 r4: 3, off her hair (PlayerView.HerHairLayer): her far edge +4.4 to +5.1 L at hue 240, the crown 39.7 as without it)
    // --close-rim-spec S: the moon rim's sheen (Light3D.light_specular). At 0.6 it lay down the side of her neck as a broad
    // pale lavender band, plastic not skin (the owner's night close-up, 21 Oct; face 35: band Oklab L 51 C 4.3 hue -67, at 0
    // L 38.7 hue -5, her warm skin), and read as a lump on her left neck.
    static float CloseRimSpec => Args.Num("close-rim-spec", 0f);
    // --close-rim-gear-spec S: the rim's sheen on her gear (its twin on PlayerView.HerGearLayer; 0.6, the rim's before face 35).
    static float CloseRimGearSpec => Args.Num("close-rim-gear-spec", 0.3f);   // (Rendering 3, judge j2 D1: 0.6 -> 0.3, the moon's pink-white glint up the blade)
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
    static float CloseExposureNight => Args.Num("close-exp-night", 0.72f);   // (Rendering 1: 0.72, her lights up as much: the background ~6x under her lit face (judge j0 B3, the owner's rule), her face no brighter. G1 r4: 1.35 to 1.2: at 1.35 a third of her lit face sat above Oklab L 85 at the tonemap's shoulder, flat and pale; earlier: x the preset's 1.5: face ~145-150 (judge 3 fix; round 3c's 1.465 left it pale at 170, the fire filling it))
    // --close-key-az D: the night key's angle off her face (degrees), toward the lens, so her far cheek falls into half
    // shade (E1 round 3: 50-60; judge 3 fix: 90, about 55 degrees off the lens on the fire's side, once the fire no longer filled her).
    // The key's colour: the ember's, saturated (1.0, 0.6, 0.35).
    static float CloseKeyAzNight => Args.Num("close-key-az", 90f);
    // (Rendering 1: about 3000K, (1, 0.71, 0.42), less orange than the ember's (1, 0.6, 0.35): judge j0 B3, fair skin apricot
    // and deep skin rust-red under it. --close-key-colour-night R,G,B.)
    static readonly Color CloseKeyColourNight = ArgColour("close-key-colour-night", new Color(1f, 0.71f, 0.42f));
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

using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Cinema;
using SurvivorUnchained.View;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Play;

/// Face 48: her light in a cinematic as the close view lights her (GameCloseUp.HerToTheView). A shot's own rigs
/// (the "rig" cue: a bare spot on people's layer, 0.4-0.8 m from her head) lit her skin, hair and metal alike, at up to
/// several times the close view's key on her face, and none of the close view's night treatment reached her double.
/// Now, whenever a shot lights her: her double's hair and metal leave people's layer for hers (PlayerView.HerHairLayer,
/// HerGearLayer); every rig takes a hair twin (the close view's hair key: held low, so a light from above or behind
/// does not lift her crown) and a gear twin at the close view's low sheen; the rigs on her face are held to the close
/// view's key on it (their ratios and directions kept); and by night, close, her eyes, skin hold, skin guard and the
/// close view's highlight grade come on. No shot is tuned by hand.
/// Round 2: when the shot frames her face close (HerCloseness), the close view's own rig keys her from the cinematic camera
/// (HerKey: key, fill, rim, twins, exposure matched; the moon, the zone's fires and any flame near her held to it on her alone).
/// --cine-her off: none of it (before frames). --cine-her-key off: round 1 (no key, the cap on).
/// --cine-her-off layers,hair,gear,spec,cap,night,eyes,guard,key,moon,fire,near: those parts off.
/// --cine-her-on hold,grade,lift,sky: parts kept off by default (Face 48 measured them worse or no better), for pictures.
/// --cine-her-cap K: the cap as K of the close view's key (exposure counted). --cine-her-hair-back S: a light from
/// behind or steeply above her keeps S of itself on her hair.
public partial class Game
{
    sealed partial class Cine
    {
        static readonly bool HerOn = Args.Get("cine-her") != "off";
        static readonly HashSet<string> HerOff = (Args.Get("cine-her-off") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).ToHashSet();
        static readonly HashSet<string> HerOnToo = (Args.Get("cine-her-on") ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).ToHashSet();
        /// <summary>Parts off unless --cine-her-on names them (Face 48 diag: the skin hold turned rig-lit skin lemon, hue 57 to 68;
        /// the close view's highlight grade moved her face little and re-grades the whole frame).</summary>
        /// (and "lift", the rigs raised to the close key: flatter, p85-p15 19 to 13 on C02 s4; "sky", her skin off the sky's light
        /// by night: under 1 L either way, the ambient is not what carries her face there)
        static readonly HashSet<string> HerOffByDefault = new() { "hold", "grade", "lift", "sky" };
        static readonly bool HerKeyArg = Args.Get("cine-her-key") != "off";
        static bool HerPart(string p) => HerOn && !HerOff.Contains(p) && (!HerOffByDefault.Contains(p) || HerOnToo.Contains(p)) && (p != "key" || HerKeyArg);
        // Her key's numbers (Face 48 round 2): --cine-her-key-gain, --cine-her-fill, --cine-her-rim, --cine-her-moon: the close
        // view's key, fill, rim and the moon on her, each times this (1: as the close view, exposure matched); --cine-her-fire F: the
        // nearest zone fire's share on her, as CloseFireShare; --cine-her-near-light N: any other light near her face (a flame,
        // a glow) kept at N of itself; --cine-her-rigs S: a shot's rigs keep S of themselves on her skin, hair and gear under her
        // key (a catchlight's sheen whole). Defaults by the numbers on C01 s3/s8, C02 s4/s8, C03 s3b (Face 48 r2): key 0.85, fill
        // 0.5, fire 0.3, rigs 0.2 put the lit cheek at 72-76, the shade at 40-51, nothing clipped; --cine-her-sky-hold K: her
        // skin's sky share, held to the close view's (exposure and the shot's hemi and env counted), times K; --cine-her-near PX:
        // her face at PX pixels per 10 cm at 1080p (or the lens within 3 m of her eyes) keys her whole, none under 2/3 of it.
        static float HerKeyGain => Args.Num("cine-her-key-gain", 0.85f);
        static float HerFillGain => Args.Num("cine-her-fill", 0.5f);
        static float HerRimGain => Args.Num("cine-her-rim", 1f);
        static float HerMoonGain => Args.Num("cine-her-moon", 1f);
        static float HerFireGain => Args.Num("cine-her-fire", 0.3f);
        static float HerNearGain => Args.Num("cine-her-near-light", 0.5f);
        static float HerRigShare => Args.Num("cine-her-rigs", 0.2f);
        static float HerSkyHold => Args.Num("cine-her-sky-hold", 1f);
        static float HerNear => Args.Num("cine-her-near", 90f);
        static float HerCap => Args.Num("cine-her-cap", 1f);
        static float HerLift => Args.Num("cine-her-lift", 2.5f);
        static float HerSky => Args.Num("cine-her-sky", 0.4f);
        static float HerHairBack => Args.Num("cine-her-hair-back", 0.35f);
        static float HerSkinSpec => Args.Num("cine-her-spec", 0.3f);
        static readonly bool HerLog = Args.Has("camlog");
        static readonly bool HerLights = Args.Has("cine-her-lights");
        int herLightsShot = -1;

        /// <summary>A shot's rig light: its authored energy (the cue's and its fade's), the light, and its twins on her hair and gear.</summary>
        sealed class Rig
        {
            public readonly SpotLight3D L; public readonly System.Text.Json.JsonElement From, Aim; public readonly int Shot;
            public float E, Spec;
            public SpotLight3D? Hair, Gear, Skin;
            /// <summary>A catchlight: narrow (8 degrees or under) and aimed at her eyes bone; its sheen stays whole on her under her key.</summary>
            public readonly bool Catch;
            public Rig(SpotLight3D l, System.Text.Json.JsonElement from, System.Text.Json.JsonElement aim, int shot, float e)
            {
                L = l; From = from; Aim = aim; Shot = shot; E = e; Spec = l.LightSpecular;
                Catch = l.SpotAngle <= 8 && aim.ValueKind == System.Text.Json.JsonValueKind.Object && aim.TryGetProperty("bone", out var b) && b.GetString() == "eyes";
            }
            public void Free() { L.QueueFree(); Hair?.QueueFree(); Gear?.QueueFree(); Skin?.QueueFree(); }
        }

        readonly List<GeometryInstance3D> herMoved = new();
        float herNightShown, herCapShown = 1, herK, herSkyShown = 1;
        SpotLight3D? herKey, herKeyHair, herKeyGear, herFill, herRim, herRimGear;
        DirectionalLight3D? herMoon;
        OmniLight3D? herFire;
        /// <summary>The other lights near her face (a lantern, a flame, a fire's glow: not the zone's), each off her for its twin.</summary>
        readonly List<(OmniLight3D Src, OmniLight3D Twin, uint Bits)> herNear = new();
        int herNearShot = -1;
        double herNearAt = -1;
        bool herMoonOff, herZoneOff;
        string herSrc = "-";
        double herLogAt = -1;

        /// <summary>Her double's hair and metal on her own layers (each frame: her look and her hair are made again as they change).</summary>
        void HerLayers(PersonView her)
        {
            if (!HerPart("layers")) return;
            void Walk(Node n)
            {
                foreach (var c in n.GetChildren())
                {
                    if (c is GeometryInstance3D gi && (gi.Layers & 2u) != 0)
                    {
                        uint to = gi is MeshInstance3D mi && her.Person.Hair.Contains(mi) ? PlayerView.HerHairLayer
                            : PlayerView.IsMetalPart(gi) ? PlayerView.HerGearLayer : 0;
                        if (to != 0) { gi.Layers = (gi.Layers & ~2u) | to; herMoved.Add(gi); }
                    }
                    Walk(c);
                }
            }
            Walk(her);
        }

        static float Lum(Color c) { var l = c.SrgbToLinear(); return 0.2126f * l.R + 0.7152f * l.G + 0.0722f * l.B; }

        /// <summary>A spot's light at a point, as Godot's renderer attenuates it (distance window and decay, the cone's edge), times its colour's luminance.</summary>
        static float SpotAt(SpotLight3D l, float energy, Vector3 p)
        {
            var d = p - l.GlobalPosition; float dist = Mathf.Max(d.Length(), 0.0001f);
            float nd = dist / Mathf.Max(l.SpotRange, 0.001f); nd *= nd; nd *= nd; nd = Mathf.Max(1 - nd, 0); nd *= nd;
            float att = nd * Mathf.Pow(dist, -l.SpotAttenuation);
            // (the cone taken as reaching her face if its edge comes within a head's width of the point: a narrow rig aimed
            // at her cheek or brow lights her face though her eyes sit outside it)
            float ang = Mathf.RadToDeg(Mathf.Acos(Mathf.Clamp((-l.GlobalBasis.Z).Normalized().Dot(d / dist), -1, 1)));
            if (ang > l.SpotAngle + Mathf.RadToDeg(Mathf.Atan2(0.12f, dist))) return 0;
            return energy * att * Lum(l.LightColor);
        }

        /// <summary>An omni's light at a point, as SpotAt (no cone).</summary>
        static float OmniAt(OmniLight3D l, float energy, Vector3 p)
        {
            float dist = Mathf.Max((p - l.GlobalPosition).Length(), 0.0001f);
            float nd = dist / Mathf.Max(l.OmniRange, 0.001f); nd *= nd; nd *= nd; nd = Mathf.Max(1 - nd, 0); nd *= nd;
            return energy * nd * Mathf.Pow(dist, -l.OmniAttenuation) * Lum(l.LightColor);
        }

        /// <summary>The close view's key on her face by night, as the rigs are measured (its key at 2.6 m, on axis, and its fill),
        /// times the close view's exposure against this frame's.</summary>
        float CloseKeyOnFace()
        {
            float d = 2.6f, nd = d / 8; nd *= nd; nd *= nd; nd = (1 - nd) * (1 - nd);
            float key = CloseKeyNight * nd * Mathf.Pow(d, -0.4f) * Lum(CloseKeyColourNight);
            float fill = (CloseFillNight > 0 ? CloseFillNight : CloseKeyNight * CloseFillRatio) * nd * Mathf.Pow(d, -0.4f) * Lum(CloseFillColourNight);
            float closeExp = (float)Atmospheres.ByName("night").Exposure * g.air.ExposureScale * CloseExposureNight;
            float now = Mathf.Max(g.air.Env.TonemapExposure, 0.01f);
            return (key + fill) * closeExp / now;
        }

        /// <summary>Each frame, after the rigs are placed: the twins, the cap, her night treatment.</summary>
        void HerLight()
        {
            PersonView? her = people.TryGetValue("her", out var hv) && IsInstanceValid(hv) && hv.IsVisibleInTree() ? hv : null;
            // (her eyes as the close view finds them, People.EyesOf: the cue's "eyes" is her head bone and 7 cm up the world, off her face when she lies down)
            Vector3? eyes = her != null ? People.EyesOf(her.Person) : null;
            if (her != null && HerOn) HerLayers(her);
            // (her key: how close the shot frames her face, 0 wide or unseen; the rigs keep HerRigShare of themselves on her skin)
            float k = her != null && eyes is Vector3 ke && HerPart("key") ? HerCloseness(her, ke) : 0;
            herK = k;
            // (the rigs on her face, measured where her eyes are, and held to the close view's key)
            float sum = 0;
            var on = new Dictionary<Rig, float>();
            foreach (var r in rigs.Values)
            {
                float f = eyes is Vector3 e ? SpotAt(r.L, r.E, e + (g.camera.GlobalPosition - e).Normalized() * 0.08f) : 0;
                on[r] = f; sum += f;
            }
            float cap = 1;
            if (HerPart("cap") && !HerPart("key") && her != null && sum > 0.001f) cap = Mathf.Min(HerPart("lift") ? HerLift : 1, HerCap * CloseKeyOnFace() / sum);
            herCapShown = cap;
            bool night = g.scene?.View.Night == true;
            foreach (var r in rigs.Values)
            {
                float kk = on[r] > 0.01f * sum ? cap : 1;
                r.L.LightEnergy = r.E * kk;
                r.L.LightSpecular = HerPart("spec") ? Mathf.Min(r.Spec, HerSkinSpec) : r.Spec;
                // Under her key the rig leaves her skin (people's layer, which in a cinematic is hers alone: the cast are on
                // CastLayer) for its skin twin, at HerRigShare of itself (a catchlight whole).
                // (a catchlight's diffuse on her face takes the share too: C01 s8's 6-degree "eyes" rig from the lens was 40% of the
                // light on her face, flat and frontal; its sheen, the catchlight in her eyes, kept whole by its specular over the share)
                float share = Mathf.Lerp(1, HerRigShare, k);
                r.L.LightCullMask = k > 0 ? PlayerView.CastLayer : 2u | PlayerView.CastLayer;
                if (k > 0)
                {
                    r.Skin ??= Twin(r, 2u, r.Spec);
                    r.Skin.GlobalTransform = r.L.GlobalTransform; r.Skin.SpotRange = r.L.SpotRange; r.Skin.SpotAngle = r.L.SpotAngle;
                    r.Skin.SpotAttenuation = r.L.SpotAttenuation; r.Skin.LightColor = r.L.LightColor;
                    r.Skin.LightSpecular = r.Catch ? Mathf.Min(r.L.LightSpecular / Mathf.Max(share, 0.05f), 16) : r.L.LightSpecular;
                    r.Skin.LightEnergy = r.L.LightEnergy * share; r.Skin.Visible = r.Skin.LightEnergy > 0.0005f;
                }
                else if (r.Skin != null) r.Skin.Visible = false;
                if (!HerPart("layers")) { r.Hair?.QueueFree(); r.Gear?.QueueFree(); r.Hair = r.Gear = null; continue; }
                r.Hair ??= Twin(r, PlayerView.HerHairLayer, r.Spec);
                r.Gear ??= Twin(r, PlayerView.HerGearLayer, HerPart("gear") ? CloseKeyGearSpec : r.Spec);
                foreach (var t in new[] { r.Hair, r.Gear })
                {
                    t.GlobalTransform = r.L.GlobalTransform; t.SpotRange = r.L.SpotRange; t.SpotAngle = r.L.SpotAngle;
                    t.SpotAttenuation = r.L.SpotAttenuation; t.LightColor = r.L.LightColor; t.LightEnergy = r.L.LightEnergy * share;
                    t.Visible = t.LightEnergy > 0.0005f;
                }
                // Her hair's twin as the close view's (CloseKeyHairEl, CloseKeyHair; its rim kept off her hair): a light above
                // her head comes down to the hair key's height at its own bearing and distance, and one from behind her or
                // steeply above keeps CineHerHairBack of itself, so the crown and the hairline are not lifted pale.
                if (HerPart("hair") && eyes is Vector3 he)
                {
                    var rel = r.L.GlobalPosition - he; float dist = rel.Length();
                    var flat = new Vector3(rel.X, 0, rel.Z); float el = Mathf.RadToDeg(Mathf.Atan2(rel.Y, flat.Length()));
                    var lens = g.camera.GlobalPosition - he; lens.Y = 0;
                    bool behind = flat.LengthSquared() > 1e-4f && lens.LengthSquared() > 1e-4f && flat.Normalized().Dot(lens.Normalized()) < -0.17f;
                    float hs = night ? CloseKeyHair : 1;
                    if (behind || el > 60) hs *= HerHairBack;
                    if (el > CloseKeyHairEl && flat.LengthSquared() > 1e-4f)
                    {
                        float hu = Mathf.DegToRad(CloseKeyHairEl);
                        var aimAt = r.L.GlobalPosition + -r.L.GlobalBasis.Z * dist;
                        r.Hair.GlobalPosition = he + flat.Normalized() * dist * Mathf.Cos(hu) + Vector3.Up * dist * Mathf.Sin(hu);
                        if (r.Hair.GlobalPosition.DistanceTo(aimAt) > 0.05f) r.Hair.LookAt(aimAt);
                    }
                    r.Hair.LightEnergy = r.L.LightEnergy * share * hs;
                    r.Hair.Visible = r.Hair.LightEnergy > 0.0005f;
                }
            }
            HerKey(her, eyes, k, night);
            // By night, close: the close view's night treatment on her. Under her key, as close as the key is on; else (round 1)
            // her eyes within 2 m of the lens, none past 4 m.
            float nk = 0;
            if (HerPart("night") && her != null && night && eyes is Vector3 ne)
                nk = HerPart("key") ? k : Mathf.Clamp((4 - g.camera.GlobalPosition.DistanceTo(ne)) / 2, 0, 1);
            if (her != null && (nk != 0 || herNightShown != 0))
            {
                People.HerEyesNight(her.Person, HerPart("eyes") ? nk : 0); People.HerSkinHold(her.Person, HerPart("hold") ? nk : 0);
                g.air.SetViewSkinGuard(HerPart("guard") ? nk : 0); g.air.SetViewHighlights(HerPart("grade") ? nk : 0);
                // (her skin's share of the sky's light by night, close, while a rig keys her: a shot's own "skin" cue rules)
                if (skinSky == 1 && !HerPart("key")) People.HerSkyShare(her.Person, HerPart("sky") && sum > 0.001f ? Mathf.Lerp(1, HerSky, nk) : 1);
            }
            herNightShown = nk;
            if (HerLights && eyes is Vector3 de && player.Shot.Index != herLightsShot && player.Local > 0.5)
            {
                // (--cine-her-lights: once a shot, every light on people's layer that reaches her eyes, with its light there)
                herLightsShot = player.Shot.Index;
                void Dump(Node n)
                {
                    foreach (var c in n.GetChildren())
                    {
                        if (c is Light3D l && l.IsVisibleInTree() && (l.LightCullMask & 2u) != 0 && l.LightEnergy > 0)
                        {
                            float at = l is SpotLight3D sl ? SpotAt(sl, sl.LightEnergy, de) : l is OmniLight3D ol ? OmniAt(ol, ol.LightEnergy, de) : l.LightEnergy * Lum(l.LightColor);
                            if (at > 0.005f) GD.Print($"herlight shot={player.Shot.Shot.Id} {l.GetPath()} {l.GetType().Name} E={l.LightEnergy:F2} at={at:F3} mask={l.LightCullMask:X} c={l.LightColor.ToHtml(false)}");
                        }
                        Dump(c);
                    }
                }
                Dump(g.GetTree().Root);
            }
            if (HerLog && eyes is Vector3 le && Shots.Clock - herLogAt >= 0.1)
            {
                herLogAt = Shots.Clock;
                var c = g.camera.UnprojectPosition(le); var rr = g.camera.UnprojectPosition(le + g.camera.GlobalBasis.X * 0.1f);
                GD.Print($"facepx t={Shots.Clock:F2} x={c.X:F0} y={c.Y:F0} s={(rr - c).Length():F1}");
                GD.Print($"cineher t={Shots.Clock:F2} shot={player.Shot.Shot.Id} local={player.Local:F2} x={c.X:F0} y={c.Y:F0} s={(rr - c).Length():F1} rigs={sum:F3} close={CloseKeyOnFace():F3} cap={cap:F2} k={k:F2} key={(herKey?.LightEnergy ?? 0):F2} fill={(herFill?.LightEnergy ?? 0):F2} rim={(herRim?.LightEnergy ?? 0):F2} moon={(herMoon?.Visible == true ? herMoon.LightEnergy : -1):F3} fire={(herFire?.Visible == true ? herFire.LightEnergy : -1):F2} keyAt={(herKey?.Visible == true && eyes is Vector3 qe ? SpotAt(herKey, herKey.LightEnergy, qe) : 0):F3} fireAt={(herFire?.Visible == true && eyes is Vector3 qf ? OmniAt(herFire, herFire.LightEnergy, qf) : 0):F3} sky={herSkyShown:F2} src={herSrc} exp={g.air.Env.TonemapExposure:F3} night={night} nk={nk:F2} lens={g.camera.GlobalPosition.DistanceTo(le):F2} "
                    + string.Join(" ", rigs.Select(kv => $"{kv.Key}={on.GetValueOrDefault(kv.Value):F3}")));
            }
        }

        /// <summary>Her head's forward (the way her face looks) and up (to her crown), in the world.</summary>
        static (Vector3 fwd, Vector3 up) HerHead(PersonView her)
        {
            var p = her.Person; int hb = p.Skeleton.FindBone("Head");
            if (hb < 0) return (her.GlobalBasis.Z.Normalized(), Vector3.Up);
            var rest = p.Skeleton.GetBoneGlobalRest(hb);
            var b = p.Skeleton.GlobalTransform.Basis * ((p.HeadPose ?? p.Skeleton.GetBoneGlobalPose(hb)) * rest.AffineInverse()).Basis;
            return ((b * Vector3.Back).Normalized(), (b * Vector3.Up).Normalized());
        }

        /// <summary>How close the shot frames her face (0 to 1): her eyes in frame, her face toward the lens (not her back
        /// or the back of her head), and her face at HerNear pixels per 10 cm at 1080p or the lens within 3 m of her eyes.</summary>
        float HerCloseness(PersonView her, Vector3 eyes)
        {
            var cam = g.camera;
            if (cam.IsPositionBehind(eyes)) return 0;
            var vp = g.GetViewport().GetVisibleRect().Size;
            var c = cam.UnprojectPosition(eyes);
            if (c.X < -0.02f * vp.X || c.X > 1.02f * vp.X || c.Y < -0.02f * vp.Y || c.Y > 1.02f * vp.Y) return 0;
            float px = (cam.UnprojectPosition(eyes + cam.GlobalBasis.X * 0.1f) - c).Length() * 1080f / Mathf.Max(vp.Y, 1);
            float near = Mathf.Max(Mathf.SmoothStep(HerNear * 2 / 3f, HerNear, px), Mathf.SmoothStep(3.6f, 3f, cam.GlobalPosition.DistanceTo(eyes)));
            var toLens = (cam.GlobalPosition - eyes).Normalized();
            float facing = Mathf.SmoothStep(-0.45f, -0.15f, HerHead(her).fwd.Dot(toLens));
            return near * facing;
        }

        static SpotLight3D HerSpot(Node at, string name, uint mask, float spec, float angle)
        {
            var l = new SpotLight3D { Name = name, SpotAngle = angle, SpotRange = 8, SpotAttenuation = 0.4f, ShadowEnabled = false, LightCullMask = mask, LightSpecular = spec, LightEnergy = 0, Visible = false };
            at.AddChild(l);
            return l;
        }

        /// <summary>Her key in a cinematic (Face 48 round 2): the close view's light on her (GameCloseUp.HerToTheView) by this
        /// frame's camera, with "where she faces" her head's forward (so it keys her lying down): the key from the nearest lit
        /// fire or lamp's side (12 m), else the moon's (by day the sun's), CloseKeyWildOff off the lens on the side she faces
        /// and held within CloseKeyFaceHold of her face, CloseKeyElNight up; its hair and gear twins; by night the cool fill
        /// 35 degrees off the lens on the far side and the moon rim behind her (off her hair) with its gear twin. Each at the
        /// close view's energy times its exposure against this frame's, so her face lands where the close view puts it
        /// whatever exposure the shot set; the moon and the sky's light on her held down to the close view's the same way
        /// (her skin only: the shot's mood stays in the world). k: HerCloseness (0: all of it off, the frame as before).
        /// By day it is the close view's day path (untested in a cinematic).</summary>
        void HerKey(PersonView? her, Vector3? eyesAt, float k, bool night)
        {
            if (her == null || eyesAt is not Vector3 e || k <= 0.001f || g.scene == null)
            {
                HerZoneBack(); HerNearBack();
                foreach (var l in new[] { herKey, herKeyHair, herKeyGear, herFill, herRim, herRimGear }) if (l != null && IsInstanceValid(l)) l.Visible = false;
                HerMoonBack();
                if (herSkyShown != 1 && her != null && skinSky == 1) People.HerSkyShare(her.Person, 1);
                herSkyShown = 1; herSrc = "-";
                return;
            }
            var scene = g.scene;
            if (herKey == null || !IsInstanceValid(herKey))
            {
                herKey = HerSpot(scene, "HerKey", 2u | PlayerView.HerLayer, 0.3f, 24);
                herKeyHair = HerSpot(scene, "HerKey_hair", PlayerView.HerHairLayer, 0.3f, 24);
                herKeyGear = HerSpot(scene, "HerKey_gear", PlayerView.HerGearLayer, CloseKeyGearSpec, 24);
                herFill = HerSpot(scene, "HerFill", 2u | PlayerView.HerLayers, 0, 26);
                herRim = HerSpot(scene, "HerRim", 2u | PlayerView.HerLayer, CloseRimSpec, 26);
                herRimGear = HerSpot(scene, "HerRim_gear", PlayerView.HerGearLayer, CloseRimGearSpec, 26);
            }
            var cam = g.camera.GlobalPosition;
            var (fwd, headUp) = HerHead(her);
            // (her frame: the world's up, or, as her face turns to the sky or the ground (lying down), her head's)
            var U = Vector3.Up.Lerp(headUp, Mathf.SmoothStep(0.55f, 0.8f, Mathf.Abs(fwd.Y))).Normalized();
            var Z0 = Vector3.Back - U * U.Dot(Vector3.Back);
            if (Z0.LengthSquared() < 1e-3f) Z0 = Vector3.Right - U * U.Dot(Vector3.Right);
            Z0 = Z0.Normalized(); var X0 = U.Cross(Z0);
            float Az(Vector3 v) => Mathf.Atan2(v.Dot(X0), v.Dot(Z0));
            Vector3 Dir(float a, float up) => (X0 * Mathf.Sin(a) + Z0 * Mathf.Cos(a)) * Mathf.Cos(up) + U * Mathf.Sin(up);
            static float W(float x) => Mathf.Wrap(x, -Mathf.Pi, Mathf.Pi);
            var center = e - U * 0.06f;
            float lens = Az(cam - e), face = Az(fwd), hold = Mathf.DegToRad(CloseKeyFaceHold);
            var lamp = night ? scene.View.NearestLit(e, CloseKeySrcRange) : null;
            var src = lamp != null ? lamp.GlobalPosition - e : g.air.Key.GlobalTransform.Basis.Z;
            herSrc = lamp != null ? lamp.Name : night ? "moon" : "sun";
            var sp = src - U * U.Dot(src);
            float a = sp.LengthSquared() > 1e-4f ? Az(sp) : lens;
            if (lamp == null) a = lens + Mathf.Clamp(W(a - lens), -Mathf.DegToRad(CloseKeySunHold), Mathf.DegToRad(CloseKeySunHold));
            a = face + Mathf.Clamp(W(a - face), -hold, hold);
            if (g.IsTown && (night || Atmosphere.TownLit > 0.5f) && CloseKeyTownOff is { } to)
            {
                float d = W(a - lens);
                a = lens + (d < 0 ? -1 : 1) * Mathf.Clamp(Mathf.Abs(d), Mathf.DegToRad(to.X), Mathf.DegToRad(to.Y));
            }
            else if (night && CloseKeyWildOff is { } wo)
            {
                float fd = W(face - lens);
                a = lens + (fd < 0 ? -1 : 1) * Mathf.Clamp(Mathf.Abs(W(a - lens)), Mathf.DegToRad(wo.X), Mathf.DegToRad(wo.Y));
                a = face + Mathf.Clamp(W(a - face), -hold, hold);
            }
            // (the close view's exposure against this frame's: her lights scaled by it, so her face lands where the close view's does)
            var pre = night ? Atmospheres.Night : Atmospheres.Day;
            float closeExp = (float)pre.Exposure * g.air.ExposureScale * (night ? CloseExposureNight : Atmosphere.TownLit > 0.5f ? CloseExposureDusk : 1);
            float m = closeExp / Mathf.Max(g.air.Env.TonemapExposure, 0.01f);
            void Place(SpotLight3D l, float az, float up, float dist, Vector3 at)
            {
                l.GlobalPosition = at + Dir(az, up) * dist;
                var to = (at - l.GlobalPosition).Normalized();
                l.LookAt(at, Mathf.Abs(to.Dot(U)) > 0.98f ? Z0 : U);
            }
            float up0 = Mathf.DegToRad(night ? CloseKeyElNight : CloseKeyElDay);
            herKey.LightColor = night ? CloseKeyColourNight : CloseKeyColourDay;
            herKey.LightEnergy = (night ? CloseKeyNight : CloseKey) * m * HerKeyGain * k;
            herKey.Visible = herKey.LightEnergy > 0.005f;
            herKey.ShadowEnabled = night && CloseKeyShadow; herKey.LightSize = 0.15f;
            Place(herKey, a, up0, 2.6f, center);
            herKeyHair!.LightColor = night ? CloseKeyHairColour : herKey.LightColor;
            herKeyHair.LightEnergy = herKey.LightEnergy * (night ? CloseKeyHair : 1); herKeyHair.Visible = herKey.Visible;
            if (night && CloseKeyHairEl >= 0) Place(herKeyHair, a, Mathf.DegToRad(CloseKeyHairEl), 2.6f, center);
            else herKeyHair.GlobalTransform = herKey.GlobalTransform;
            herKeyGear!.LightColor = herKey.LightColor; herKeyGear.LightEnergy = herKey.LightEnergy; herKeyGear.Visible = herKey.Visible;
            herKeyGear.LightSpecular = night ? CloseKeyGearSpec : 0.3f; herKeyGear.GlobalTransform = herKey.GlobalTransform;
            // (by night the cool fill on the lens's far side from the key, raised on deep skin, People.HerSkinDark)
            float fillRatio = CloseFillRatio + CloseFillDeep * People.HerSkinDark(her.Person);
            herFill!.LightColor = CloseFillColourNight;
            herFill.LightEnergy = night ? (CloseFillNight > 0 ? CloseFillNight : CloseKeyNight * fillRatio) * m * HerFillGain * k : 0;
            herFill.Visible = herFill.LightEnergy > 0.005f;
            float side = W(a - lens) >= 0 ? -1 : 1;
            Place(herFill, lens + side * Mathf.DegToRad(35), Mathf.DegToRad(10), 2.6f, center);
            herRim!.LightColor = new Color("#a9c4ff");
            herRim.LightEnergy = night ? CloseRimNight * m * HerRimGain * k : 0;
            herRim.Visible = herRim.LightEnergy > 0.005f;
            Place(herRim, lens + Mathf.Pi - CloseRimAz, Mathf.DegToRad(CloseRimEl), 2.4f, center + U * 0.15f);
            herRimGear!.LightColor = herRim.LightColor; herRimGear.LightEnergy = herRim.LightEnergy * CloseRimGearGain;
            herRimGear.Visible = herRim.Visible && herRimGear.LightEnergy > 0.005f;
            Place(herRimGear, lens + Mathf.Pi - CloseRimGearAz, Mathf.DegToRad(CloseRimEl), 2.4f, center + U * 0.15f);
            // The moon (by day the sun) on her skin: off people's layer for its twin, held down to the close view's on her.
            var key = g.air.Key;
            if (HerPart("moon"))
            {
                if (herMoon == null || !IsInstanceValid(herMoon))
                {
                    herMoon = new DirectionalLight3D { Name = "HerMoon", LightCullMask = 2u, DirectionalShadowMode = DirectionalLight3D.ShadowMode.Parallel2Splits, DirectionalShadowMaxDistance = 20 };
                    scene.AddChild(herMoon);
                }
                if (!herMoonOff) { key.LightCullMask &= ~2u; herMoonOff = true; }
                float want = (float)pre.KeyIntensity / Mathf.Pi * m * HerMoonGain;
                herMoon.GlobalTransform = key.GlobalTransform; herMoon.LightColor = key.LightColor; herMoon.LightSpecular = key.LightSpecular;
                herMoon.ShadowEnabled = key.ShadowEnabled; herMoon.ShadowBlur = key.ShadowBlur; herMoon.LightAngularDistance = key.LightAngularDistance;
                herMoon.LightEnergy = Mathf.Lerp(key.LightEnergy, Mathf.Min(key.LightEnergy, want), k);
                herMoon.Visible = key.Visible;
            }
            else HerMoonBack();
            // The zone's fires and lamps off her, as the close view keeps them (ZoneView.HerUnlit), and a share of the nearest
            // (CloseFireShare, eased near the lens's line, in the key's colour) kept on her at the close view's exposure.
            if (HerPart("fire"))
            {
                if (!herZoneOff) { scene.View.Unlit(2u | PlayerView.HerLayers, true); herZoneOff = true; }
                if (herFire == null || !IsInstanceValid(herFire))
                {
                    herFire = new OmniLight3D { Name = "HerFire", ShadowEnabled = false, LightCullMask = 2u | PlayerView.HerLayers };
                    scene.AddChild(herFire);
                }
                if (lamp != null)
                {
                    herFire.GlobalPosition = lamp.GlobalPosition;
                    herFire.LightColor = lamp.LightColor.Lerp(CloseKeyColourNight, CloseFireToKey);
                    var ts = lamp.GlobalPosition - e; ts -= U * U.Dot(ts);
                    float front = Mathf.Lerp(CloseFireFront, 1, Mathf.SmoothStep(25, 60, Mathf.Abs(Mathf.RadToDeg(W(Az(ts) - lens)))));
                    herFire.LightEnergy = lamp.LightEnergy * CloseFireShare * front * m * HerFireGain;
                    herFire.OmniRange = lamp.OmniRange; herFire.OmniAttenuation = lamp.OmniAttenuation; herFire.LightSpecular = lamp.LightSpecular;
                    herFire.Visible = true;
                }
                else herFire.Visible = false;
            }
            else HerZoneBack();
            // Every other light near her face (C02 s8: a cold flame 0.3 m off her cheek was as strong on it as her key) held the
            // same way: off her layers, its twin on them at HerNearGain of it, exposure matched. Found once a shot.
            if (HerPart("near"))
            {
                // (looked for at each shot's start and every half second: a flame lit or carried in mid-shot)
                if (herNearShot != player.Shot.Index || Shots.Clock - herNearAt >= 0.5)
                {
                    if (herNearShot != player.Shot.Index) HerNearBack();
                    herNearShot = player.Shot.Index; herNearAt = Shots.Clock;
                    void Find(Node n)
                    {
                        foreach (var c in n.GetChildren())
                        {
                            if (c is OmniLight3D o && o != herFire && o.IsVisibleInTree() && (o.LightCullMask & 2u) != 0 && OmniAt(o, o.LightEnergy, e) > 0.01f)
                            {
                                uint bits = o.LightCullMask & (2u | PlayerView.HerLayers);
                                var t = new OmniLight3D { Name = "HerNear_" + o.Name, ShadowEnabled = false, LightCullMask = bits };
                                o.LightCullMask &= ~bits;
                                scene.AddChild(t);
                                herNear.Add((o, t, bits));
                            }
                            Find(c);
                        }
                    }
                    Find(scene);
                }
                foreach (var (o, t, _) in herNear)
                {
                    if (!IsInstanceValid(o) || !IsInstanceValid(t)) continue;
                    t.GlobalPosition = o.GlobalPosition; t.LightColor = o.LightColor; t.OmniRange = o.OmniRange; t.OmniAttenuation = o.OmniAttenuation;
                    t.LightSpecular = o.LightSpecular; t.LightEnergy = o.LightEnergy * m * HerNearGain; t.Visible = o.IsVisibleInTree();
                }
            }
            else HerNearBack();
            // Her skin's share of the sky's light, held to the close view's (its exposure and its hemi and env against the shot's).
            if (skinSky == 1)
            {
                double amb = g.air.Current.HemiIntensity + g.air.Current.EnvIntensity;
                float hold0 = Mathf.Min(1, m * (float)((pre.HemiIntensity + pre.EnvIntensity) / Math.Max(amb, 1e-3))) * HerSkyHold * (night ? 1 : CloseSkyDay);
                herSkyShown = Mathf.Lerp(1, Mathf.Clamp(hold0, 0, 1), k);
                People.HerSkyShare(her.Person, herSkyShown);
            }
        }

        void HerNearBack()
        {
            foreach (var (o, t, bits) in herNear) { if (IsInstanceValid(o)) o.LightCullMask |= bits; if (IsInstanceValid(t)) t.QueueFree(); }
            herNear.Clear(); herNearShot = -1;
        }

        void HerZoneBack()
        {
            if (herZoneOff && g.scene != null) g.scene.View.Unlit(2u | PlayerView.HerLayers, false);
            herZoneOff = false;
            if (herFire != null && IsInstanceValid(herFire)) herFire.Visible = false;
        }

        void HerMoonBack()
        {
            if (herMoonOff) { g.air.Key.LightCullMask |= 2u; herMoonOff = false; }
            if (herMoon != null && IsInstanceValid(herMoon)) herMoon.Visible = false;
        }


        SpotLight3D Twin(Rig r, uint layer, float spec)
        {
            var t = new SpotLight3D { Name = r.L.Name + (layer == PlayerView.HerHairLayer ? "_hair" : layer == 2u ? "_skin" : "_gear"), ShadowEnabled = false, LightCullMask = layer, LightSpecular = spec, LightEnergy = 0 };
            g.scene!.AddChild(t);
            return t;
        }

        /// <summary>At the cinematic's end: her layers, her night treatment and the view's grade given back.</summary>
        void HerLightEnd()
        {
            HerMoonBack(); HerZoneBack(); HerNearBack();
            foreach (var l in new Light3D?[] { herKey, herKeyHair, herKeyGear, herFill, herRim, herRimGear, herMoon, herFire }) if (l != null && IsInstanceValid(l)) l.QueueFree();
            herKey = herKeyHair = herKeyGear = herFill = herRim = herRimGear = null; herMoon = null; herFire = null;
            if (herSkyShown != 1 && people.TryGetValue("her", out var hs) && IsInstanceValid(hs)) People.HerSkyShare(hs.Person, 1);
            herSkyShown = 1;
            foreach (var gi in herMoved)
                if (IsInstanceValid(gi)) gi.Layers = (gi.Layers & ~(PlayerView.HerHairLayer | PlayerView.HerGearLayer)) | 2u;
            herMoved.Clear();
            if (herNightShown != 0)
            {
                if (people.TryGetValue("her", out var hv) && IsInstanceValid(hv)) { People.HerEyesNight(hv.Person, 0); People.HerSkinHold(hv.Person, 0); People.HerSkyShare(hv.Person, 1); }
                g.air.SetViewSkinGuard(0); g.air.SetViewHighlights(0);
                herNightShown = 0;
            }
        }
    }
}

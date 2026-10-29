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
/// --cine-her off: none of it (before frames). --cine-her-off layers,hair,gear,spec,cap,night,eyes,guard: those parts off.
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
        static bool HerPart(string p) => HerOn && !HerOff.Contains(p) && (!HerOffByDefault.Contains(p) || HerOnToo.Contains(p));
        static float HerCap => Args.Num("cine-her-cap", 1f);
        static float HerLift => Args.Num("cine-her-lift", 2.5f);
        static float HerSky => Args.Num("cine-her-sky", 0.4f);
        static float HerHairBack => Args.Num("cine-her-hair-back", 0.35f);
        static float HerSkinSpec => Args.Num("cine-her-spec", 0.3f);
        static readonly bool HerLog = Args.Has("camlog");

        /// <summary>A shot's rig light: its authored energy (the cue's and its fade's), the light, and its twins on her hair and gear.</summary>
        sealed class Rig
        {
            public readonly SpotLight3D L; public readonly System.Text.Json.JsonElement From, Aim; public readonly int Shot;
            public float E, Spec;
            public SpotLight3D? Hair, Gear;
            public Rig(SpotLight3D l, System.Text.Json.JsonElement from, System.Text.Json.JsonElement aim, int shot, float e)
            { L = l; From = from; Aim = aim; Shot = shot; E = e; Spec = l.LightSpecular; }
            public void Free() { L.QueueFree(); Hair?.QueueFree(); Gear?.QueueFree(); }
        }

        readonly List<GeometryInstance3D> herMoved = new();
        float herNightShown, herCapShown = 1;
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
            // (the rigs on her face, measured where her eyes are, and held to the close view's key)
            float sum = 0;
            var on = new Dictionary<Rig, float>();
            foreach (var r in rigs.Values)
            {
                float f = eyes is Vector3 e ? SpotAt(r.L, r.E, e + (g.camera.GlobalPosition - e).Normalized() * 0.08f) : 0;
                on[r] = f; sum += f;
            }
            float cap = 1;
            if (HerPart("cap") && her != null && sum > 0.001f) cap = Mathf.Min(HerPart("lift") ? HerLift : 1, HerCap * CloseKeyOnFace() / sum);
            herCapShown = cap;
            bool night = g.scene?.View.Night == true;
            foreach (var r in rigs.Values)
            {
                float k = on[r] > 0.01f * sum ? cap : 1;
                r.L.LightEnergy = r.E * k;
                r.L.LightSpecular = HerPart("spec") ? Mathf.Min(r.Spec, HerSkinSpec) : r.Spec;
                if (!HerPart("layers")) { r.Hair?.QueueFree(); r.Gear?.QueueFree(); r.Hair = r.Gear = null; continue; }
                r.Hair ??= Twin(r, PlayerView.HerHairLayer, r.Spec);
                r.Gear ??= Twin(r, PlayerView.HerGearLayer, HerPart("gear") ? CloseKeyGearSpec : r.Spec);
                foreach (var t in new[] { r.Hair, r.Gear })
                {
                    t.GlobalTransform = r.L.GlobalTransform; t.SpotRange = r.L.SpotRange; t.SpotAngle = r.L.SpotAngle;
                    t.SpotAttenuation = r.L.SpotAttenuation; t.LightColor = r.L.LightColor; t.LightEnergy = r.L.LightEnergy;
                    t.Visible = r.L.LightEnergy > 0.0005f;
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
                    float share = night ? CloseKeyHair : 1;
                    if (behind || el > 60) share *= HerHairBack;
                    if (el > CloseKeyHairEl && flat.LengthSquared() > 1e-4f)
                    {
                        float hu = Mathf.DegToRad(CloseKeyHairEl);
                        var aimAt = r.L.GlobalPosition + -r.L.GlobalBasis.Z * dist;
                        r.Hair.GlobalPosition = he + flat.Normalized() * dist * Mathf.Cos(hu) + Vector3.Up * dist * Mathf.Sin(hu);
                        if (r.Hair.GlobalPosition.DistanceTo(aimAt) > 0.05f) r.Hair.LookAt(aimAt);
                    }
                    r.Hair.LightEnergy = r.L.LightEnergy * share;
                    r.Hair.Visible = r.Hair.LightEnergy > 0.0005f;
                }
            }
            // By night, close (her eyes within 2 m of the lens, none past 4 m): the close view's night treatment on her.
            float nk = 0;
            if (HerPart("night") && her != null && night && eyes is Vector3 ne)
                nk = Mathf.Clamp((4 - g.camera.GlobalPosition.DistanceTo(ne)) / 2, 0, 1);
            if (her != null && (nk != 0 || herNightShown != 0))
            {
                People.HerEyesNight(her.Person, HerPart("eyes") ? nk : 0); People.HerSkinHold(her.Person, HerPart("hold") ? nk : 0);
                g.air.SetViewSkinGuard(HerPart("guard") ? nk : 0); g.air.SetViewHighlights(HerPart("grade") ? nk : 0);
                // (her skin's share of the sky's light by night, close, while a rig keys her: a shot's own "skin" cue rules)
                if (skinSky == 1) People.HerSkyShare(her.Person, HerPart("sky") && sum > 0.001f ? Mathf.Lerp(1, HerSky, nk) : 1);
            }
            herNightShown = nk;
            if (HerLog && eyes is Vector3 le && Shots.Clock - herLogAt >= 0.1)
            {
                herLogAt = Shots.Clock;
                var c = g.camera.UnprojectPosition(le); var rr = g.camera.UnprojectPosition(le + g.camera.GlobalBasis.X * 0.1f);
                GD.Print($"facepx t={Shots.Clock:F2} x={c.X:F0} y={c.Y:F0} s={(rr - c).Length():F1}");
                GD.Print($"cineher t={Shots.Clock:F2} shot={player.Shot.Shot.Id} local={player.Local:F2} x={c.X:F0} y={c.Y:F0} s={(rr - c).Length():F1} rigs={sum:F3} close={CloseKeyOnFace():F3} cap={cap:F2} exp={g.air.Env.TonemapExposure:F3} night={night} nk={nk:F2} lens={g.camera.GlobalPosition.DistanceTo(le):F2} "
                    + string.Join(" ", rigs.Select(kv => $"{kv.Key}={on.GetValueOrDefault(kv.Value):F3}")));
            }
        }

        SpotLight3D Twin(Rig r, uint layer, float spec)
        {
            var t = new SpotLight3D { Name = r.L.Name + (layer == PlayerView.HerHairLayer ? "_hair" : "_gear"), ShadowEnabled = false, LightCullMask = layer, LightSpecular = spec, LightEnergy = 0 };
            g.scene!.AddChild(t);
            return t;
        }

        /// <summary>At the cinematic's end: her layers, her night treatment and the view's grade given back.</summary>
        void HerLightEnd()
        {
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

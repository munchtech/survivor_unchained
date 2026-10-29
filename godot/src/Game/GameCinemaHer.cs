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
/// --cine-her-on hold,grade,lift,sky,spec2,kick,shadehue: parts kept off by default (Face 48 measured them worse or no better; spec2, kick, shadehue are round 4 and the final judge held them back), for pictures.
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
        static readonly HashSet<string> HerOffByDefault = new() { "hold", "grade", "lift", "sky", "spec2", "kick", "shadehue" };
        static readonly bool HerKeyArg = Args.Get("cine-her-key") != "off";
        static bool HerPart(string p) => HerOn && !HerOff.Contains(p) && herOffNow?.Contains(p) != true && (!HerOffByDefault.Contains(p) || HerOnToo.Contains(p)) && (p != "key" || HerKeyArg);
        // Her key's numbers (Face 48 round 2): --cine-her-key-gain, --cine-her-fill, --cine-her-rim, --cine-her-moon: the close
        // view's key, fill, rim and the moon on her, each times this (1: as the close view, exposure matched); --cine-her-fire F: the
        // nearest zone fire's share on her, as CloseFireShare; --cine-her-near-light N: any other light near her face (a flame,
        // a glow) kept at N of itself; --cine-her-rigs S: a shot's rigs keep S of themselves on her skin, hair and gear under her
        // key (a catchlight's sheen whole). Defaults by the numbers on C01 s3/s8, C02 s4/s8, C03 s3b (Face 48 r2): key 0.85, fill
        // 0.5, fire 0.3, rigs 0.2 put the lit cheek at 72-76, the shade at 40-51, nothing clipped; --cine-her-sky-hold K: her
        // skin's sky share, held to the close view's (exposure and the shot's hemi and env counted), times K; --cine-her-near PX:
        // her face at PX pixels per 10 cm at 1080p (or the lens within 3 m of her eyes) keys her whole, none under 2/3 of it.
        static float HerKeyGain => Args.Num("cine-her-key-gain", 0.68f);
        static float HerFillGain => Args.Num("cine-her-fill", 0.36f);
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
        // Face 48 round 3 (the judge's light): --cine-her-scale off|PX: her face held to PX per 10 cm at 1080p at most in a
        // cinematic (300: pupils about 190 px apart; the lens widened about its aim). Her key from the strongest light at her
        // head (rigs, lamps, glows, fires, the moon; each by its light at her eyes, more as it comes from where she faces),
        // its colour on her skin limited (--cine-her-skin-c: a warm source's chroma at C of the close key's; --cine-her-skin-cool:
        // a cool one's at this Oklab chroma), her hair and gear in its own colour; --cine-her-side R, --cine-her-side-min M: a
        // second source at M or more of the first kept as a side light on the face's other half at R of the key; the rim narrow
        // (--cine-her-rim-az, radians off straight behind) with its hair twin (--cine-her-rim-hair); --cine-her-eye E: a sheen-only
        // light just above the lens for her catchlights; --cine-her-body B: her key on her shoulders and chest at B.
        // --cine-her-off src,side,rim2,eye,body,scale: each back to round 2.
        static float HerScale => Args.Get("cine-her-scale") == "off" ? 0 : Args.Num("cine-her-scale", 300f);
        // A shot's own her-rig knobs (Cinematics 11, C02 s4/s8: the cool fill's grey-blue where it met the warm key), from the
        // "skin" cue's "fill" (the fill's energy times F), "fillColor" (hex) and "scale" (the face-scale cap in px per 10 cm),
        // for the shot that sets them only; other shots keep the defaults above.
        float herFillK = 1, herScaleShot; Color? herFillCol; int herKnobShot = -1;
        // ("off": the parts this shot turns off, as --cine-her-off names them: C02 s4/s8, the moon and his lantern lit by the
        // shot's own rigs, the close rig's key, fill and rim off so it does not re-aim them)
        HashSet<string>? herOffShot;
        static HashSet<string>? herOffNow;
        bool HerKnobs => herKnobShot >= 0 && player.Shot.Index == herKnobShot;
        float HerScaleNow => HerKnobs && herScaleShot > 0 ? herScaleShot : HerScale;
        static float HerSkinC => Args.Num("cine-her-skin-c", 0.87f);
        static float HerSkinCool => Args.Num("cine-her-skin-cool", 0.045f);
        static float HerSideGain => Args.Num("cine-her-side", 0.38f);
        static float HerSideMin => Args.Num("cine-her-side-min", 0.4f);
        static float HerKeySide => Args.Num("cine-her-key-side", 0.88f);
        static float HerFillSide => Args.Num("cine-her-fill-side", 0.2f);
        static float HerRimAz => Args.Num("cine-her-rim-az", 0.25f);
        static float HerRim2 => Args.Num("cine-her-rim2", 0.6f);
        static float HerRimHair => Args.Num("cine-her-rim-hair", 0.5f);
        static float HerEye => Args.Num("cine-her-eye", 0.012f);
        static float HerEyeEl => Args.Num("cine-her-eye-el", 7f);
        static float HerBodyGain => Args.Num("cine-her-body", 0.6f);
        static Color HerFillColour => ArgColour("cine-her-fill-colour", new Color(0.97f, 0.96f, 1f));
        static readonly bool HerLog = Args.Has("camlog");
        static readonly bool HerLights = Args.Has("cine-her-lights");
        // Face 48 round 4 (the judge's light): --cine-her-off spec2,kick,aim,front,cap2,catchfloor: each back to round 3.
        // spec2: her key's, side light's and moon's sheen (skin and cornea) from specular-only twins in the source's own colour at
        // full chroma (their diffuse keeps the skin-safe limit; the lights tagged light_specular 0.31, which her skin and eye
        // shaders read as "no sheen" while People.HerCineSpec is on). kick: a cool kicker on the shadow side's edge (cheek, jaw,
        // ear, neck) and its hair twin: --cine-her-kick K (times the close view's rim), --cine-her-kick-az D (degrees off
        // straight behind her from the lens), --cine-her-kick-face F (at least F degrees off where she faces), --cine-her-kick-el,
        // --cine-her-kick-hair H. aim: the catchlight light swung toward her gaze by --cine-her-eye-aim A of its angle off the
        // lens (capped at --cine-her-eye-cap degrees; her gaze --cine-her-gaze-deg degrees per iris radius). front: a key
        // within --cine-her-front-min degrees of the lens swung to --cine-her-front degrees on its side, at least 20 up.
        // shadehue: Atmosphere.SetViewShadeHue (her shade's hue floor in the grade). The kicker's sheen at light_specular 2 (tagged:
        // its own cap on her skin, cine_kick_cap) so its edge carries the source's blue.
        // cap2: the light on her face (her lights at her eyes, exposure counted) held under --cine-her-face-max.
        // catchfloor: a shot's painted catchlight no lower than --cine-her-catch-floor.
        static float HerKick => Args.Num("cine-her-kick", 0.4f);
        static float HerKickAz => Args.Num("cine-her-kick-az", 20f);
        static float HerKickFace => Args.Num("cine-her-kick-face", 125f);
        static float HerKickEl => Args.Num("cine-her-kick-el", 0f);
        static float HerKickHair => Args.Num("cine-her-kick-hair", 0.6f);
        static float HerEyeAim => Args.Num("cine-her-eye-aim", 0.5f);
        static float HerEyeCap => Args.Num("cine-her-eye-cap", 20f);
        static float HerGazeDeg => Args.Num("cine-her-gaze-deg", 30f);
        static float HerFrontMin => Args.Num("cine-her-front-min", 35f);
        static float HerFront => Args.Num("cine-her-front", 47.5f);
        static float HerFaceMax => Args.Num("cine-her-face-max", 2.55f);
        static float HerFaceMin => Args.Num("cine-her-face-min", 2.4f);
        static float HerSpecGain => Args.Num("cine-her-spec-gain", 2.5f);
        static float HerFireFront => Args.Num("cine-her-fire-front", 0.35f);
        static float HerBodyAngle => Args.Num("cine-her-body-angle", 9f);
        public static float HerCatchFloor(float v) => HerPart("catchfloor") ? Mathf.Max(v, Args.Num("cine-her-catch-floor", 0.45f)) : v;
        const float HerTagSpec = 0.31f, HerTwinSpec = 12f, HerKickTag = 2f;
        SpotLight3D? herKeySpec, herSideSpec, herKick, herKickHair;
        DirectionalLight3D? herMoonSpec;
        bool herSpecOn;
        float herKeyLens, herKeyFace, herFaceLight, herEyeOff, herRigsOnFace;
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
        SpotLight3D? herSide, herSideHair, herRimHair, herEye, herBody;
        readonly HashSet<int> herClampLogged = new();
        string herSrc2 = "-";
        float herKeyOff;
        int herCandShot = -1;
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
            herOffNow = HerKnobs ? herOffShot : null;
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
            herRigsOnFace = sum * Mathf.Lerp(1, HerRigShare, k);
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
                g.air.SetViewShadeHue(HerPart("shadehue") ? nk : 0);
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
                GD.Print($"cineher t={Shots.Clock:F2} shot={player.Shot.Shot.Id} local={player.Local:F2} x={c.X:F0} y={c.Y:F0} s={(rr - c).Length():F1} rigs={sum:F3} close={CloseKeyOnFace():F3} cap={cap:F2} k={k:F2} key={(herKey?.LightEnergy ?? 0):F2} fill={(herFill?.LightEnergy ?? 0):F2} rim={(herRim?.LightEnergy ?? 0):F2} moon={(herMoon?.Visible == true ? herMoon.LightEnergy : -1):F3} fire={(herFire?.Visible == true ? herFire.LightEnergy : -1):F2} keyAt={(herKey?.Visible == true && eyes is Vector3 qe ? SpotAt(herKey, herKey.LightEnergy, qe) : 0):F3} fireAt={(herFire?.Visible == true && eyes is Vector3 qf ? OmniAt(herFire, herFire.LightEnergy, qf) : 0):F3} sky={herSkyShown:F2} src={herSrc} src2={herSrc2} keyoff={herKeyOff:F0} side={(herSide?.Visible == true ? herSide.LightEnergy : 0):F2} exp={g.air.Env.TonemapExposure:F3} keylens={herKeyLens:F0} keyface={herKeyFace:F0} facelight={herFaceLight:F3} eyeoff={herEyeOff:F1} kick={(herKick?.Visible == true ? herKick.LightEnergy : 0):F2} night={night} nk={nk:F2} lens={g.camera.GlobalPosition.DistanceTo(le):F2} "
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

        /// <summary>The face-scale cap (Face 48 round 3): with her eyes in frame and her face toward the lens, a lens that puts her
        /// face past HerScale px per 10 cm at 1080p is widened (about its aim, the frame's middle) until it does not. Returns the
        /// lens in mm (36 mm film) after it; logs each shot's first clamp.</summary>
        double HerScaleCap(double lensMm)
        {
            if (!HerPart("scale") || HerScaleNow <= 0 || !people.TryGetValue("her", out var hv) || !IsInstanceValid(hv) || !hv.IsVisibleInTree()) return lensMm;
            var cam = g.camera; var eyes = People.EyesOf(hv.Person);
            if (cam.IsPositionBehind(eyes)) return lensMm;
            var vp = g.GetViewport().GetVisibleRect().Size; var c = cam.UnprojectPosition(eyes);
            if (c.X < 0 || c.X > vp.X || c.Y < 0 || c.Y > vp.Y) return lensMm;
            if (HerHead(hv).fwd.Dot((cam.GlobalPosition - eyes).Normalized()) < -0.3f) return lensMm;
            float px = (cam.UnprojectPosition(eyes + cam.GlobalBasis.X * 0.1f) - c).Length() * 1080f / Mathf.Max(vp.Y, 1);
            if (px <= HerScaleNow) return lensMm;
            float t0 = Mathf.Tan(Mathf.DegToRad(cam.Fov) / 2), t1 = t0 * px / HerScaleNow;
            cam.Fov = Mathf.RadToDeg(2 * Mathf.Atan(t1));
            if (herClampLogged.Add(player.Shot.Index))
                GD.Print($"cine-her: shot {player.Shot.Shot.Id} lens clamp {18 / t0:F0} mm -> {18 / t1:F0} mm (face {px:F0} -> {HerScaleNow:F0} px per 10 cm)");
            return 18 / t1;
        }

        static Vector3 Ok(Color c)
        {
            var l = c.SrgbToLinear();
            float L = Mathf.Pow(Mathf.Max(0.4122214708f * l.R + 0.5363325363f * l.G + 0.0514459929f * l.B, 0), 1 / 3f);
            float M = Mathf.Pow(Mathf.Max(0.2119034982f * l.R + 0.6806995451f * l.G + 0.1073969566f * l.B, 0), 1 / 3f);
            float S = Mathf.Pow(Mathf.Max(0.0883024619f * l.R + 0.2817188376f * l.G + 0.6299787005f * l.B, 0), 1 / 3f);
            return new Vector3(0.2104542553f * L + 0.7936177850f * M - 0.0040720468f * S, 1.9779984951f * L - 2.4285922050f * M + 0.4505937099f * S, 0.0259040371f * L + 0.7827717662f * M - 0.8086757660f * S);
        }

        /// <summary>An Oklab colour as a light's: brightest channel 1.</summary>
        static Color FromOk(Vector3 o)
        {
            float l = o.X + 0.3963377774f * o.Y + 0.2158037573f * o.Z, m = o.X - 0.1055613458f * o.Y - 0.0638541728f * o.Z, s = o.X - 0.0894841775f * o.Y - 1.2914855480f * o.Z;
            l = l * l * l; m = m * m * m; s = s * s * s;
            float r = Mathf.Max(4.0767416621f * l - 3.3077115913f * m + 0.2309699292f * s, 0), gg = Mathf.Max(-1.2684380046f * l + 2.6097574011f * m - 0.3413193965f * s, 0), b = Mathf.Max(-0.0041960863f * l - 0.7034186147f * m + 1.7076147010f * s, 0);
            float mx = Mathf.Max(Mathf.Max(r, gg), Mathf.Max(b, 1e-4f));
            return new Color(r / mx, gg / mx, b / mx).LinearToSrgb();
        }

        /// <summary>A source's colour as her skin takes it (Face 48 round 3): a warm source (Oklab hue 35-115) at HerSkinC of the
        /// close key's chroma at most, any other (blue, violet, red) at HerSkinCool: her skin stays skin under a blue lamp.</summary>
        static Color SkinSafe(Color c)
        {
            var o = Ok(c); float C = new Vector2(o.Y, o.Z).Length(), h = Mathf.PosMod(Mathf.RadToDeg(Mathf.Atan2(o.Z, o.Y)), 360);
            var k = Ok(CloseKeyColourNight); float cmax = h >= 35 && h <= 115 ? new Vector2(k.Y, k.Z).Length() * HerSkinC : HerSkinCool;
            float f = C > cmax ? cmax / C : 1;
            return FromOk(new Vector3(0.9f, o.Y * f, o.Z * f));
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
                foreach (var l in new[] { herKey, herKeyHair, herKeyGear, herFill, herRim, herRimGear, herSide, herSideHair, herRimHair, herEye, herBody, herKeySpec, herSideSpec, herKick, herKickHair }) if (l != null && IsInstanceValid(l)) l.Visible = false;
                HerMoonBack(); HerSpecSplit(her, false);
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
            // (the close view's exposure against this frame's: her lights scaled by it, so her face lands where the close view's does)
            var pre = night ? Atmospheres.Night : Atmospheres.Day;
            float closeExp = (float)pre.Exposure * g.air.ExposureScale * (night ? CloseExposureNight : Atmosphere.TownLit > 0.5f ? CloseExposureDusk : 1);
            float m = closeExp / Mathf.Max(g.air.Env.TonemapExposure, 0.01f);
            // (the zone's fires and lamps off her first, as round 2 had them: the near lights are the rest)
            if (HerPart("fire") && !herZoneOff) { scene.View.Unlit(2u | PlayerView.HerLayers, true); herZoneOff = true; }
            if (HerPart("near")) HerNearFind(scene, e, m); else HerNearBack();
            // Round 3: the key from the strongest light at her head (by its light at her eyes, the more as it comes from
            // where she faces), its colour hers; a second at HerSideMin of it or more kept as a side light.
            bool srcDir = lamp == null; Color srcColour = lamp?.LightColor ?? g.air.Key.LightColor;
            Vector3? src2 = null; Color src2Colour = default; herSrc2 = "-";
            if (HerPart("src"))
            {
                var cands = new List<(Vector3 dir, bool sun, Color c, float w, float at, string name)>();
                void Add(Vector3 to, bool sun, Color c, float at, string name)
                {
                    if (at <= 0.003f || to.LengthSquared() < 1e-6f) return;
                    var d = to.Normalized(); cands.Add((sun ? d : to, sun, c, at * (0.3f + 0.7f * Mathf.Max(0, fwd.Dot(d))), at, name));
                }
                foreach (var (name, r) in rigs) if (!r.Catch) Add(r.L.GlobalPosition - e, false, r.L.LightColor, SpotAt(r.L, r.E, e), "rig:" + name);
                if (lamp != null) Add(lamp.GlobalPosition - e, false, lamp.LightColor, OmniAt(lamp, lamp.LightEnergy, e), "lamp:" + lamp.Name);
                foreach (var (o, _, _) in herNear) if (IsInstanceValid(o) && o != lamp) Add(o.GlobalPosition - e, false, o.LightColor, OmniAt(o, o.LightEnergy, e), "near:" + o.Name);
                if (g.air.Key.Visible) Add(g.air.Key.GlobalTransform.Basis.Z, true, g.air.Key.LightColor, g.air.Key.LightEnergy * Lum(g.air.Key.LightColor), night ? "moon" : "sun");
                cands.Sort((p, q) => q.w.CompareTo(p.w));
                if (HerLights && herCandShot != player.Shot.Index && player.Local > 0.5)
                {
                    herCandShot = player.Shot.Index;
                    GD.Print($"hersrc shot={player.Shot.Shot.Id} " + string.Join(" ", cands.Select(q => $"{q.name}:w={q.w:F3}:at={q.at:F3}")));
                }
                if (cands.Count > 0)
                {
                    var c0 = cands[0]; src = c0.dir; srcDir = c0.sun; srcColour = c0.c; herSrc = $"{c0.name}:{c0.w:F3}";
                    if (HerPart("side"))
                        foreach (var c1 in cands.Skip(1))
                        {
                            // (the moon itself already on her by HerMoon: a second source is a lamp, a glow or a rig)
                            if (c1.at < HerSideMin * c0.at || (c1.sun && HerPart("moon"))) continue;
                            src2 = c1.dir; src2Colour = c1.c; herSrc2 = $"{c1.name}:{c1.w:F3}"; break;
                        }
                }
            }
            var sp = src - U * U.Dot(src);
            float a = sp.LengthSquared() > 1e-4f ? Az(sp) : lens;
            if (srcDir) a = lens + Mathf.Clamp(W(a - lens), -Mathf.DegToRad(CloseKeySunHold), Mathf.DegToRad(CloseKeySunHold));
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
            void Place(SpotLight3D l, float az, float up, float dist, Vector3 at)
            {
                l.GlobalPosition = at + Dir(az, up) * dist;
                var to = (at - l.GlobalPosition).Normalized();
                l.LookAt(at, Mathf.Abs(to.Dot(U)) > 0.98f ? Z0 : U);
            }
            float up0 = Mathf.DegToRad(night ? CloseKeyElNight : CloseKeyElDay);
            // Round 4: no frontal key. A key within HerFrontMin of the lens (in 3D, its height counted) swings to HerFront off it
            // on its own side, at least 20 degrees up, so a third or more of her face falls in shade.
            var lensDir = (cam - center).Normalized();
            herKeyLens = Mathf.RadToDeg(Dir(a, up0).AngleTo(lensDir)); herKeyFace = Mathf.RadToDeg(Dir(a, up0).AngleTo(fwd));
            if (HerPart("front") && herKeyLens < HerFrontMin)
            {
                float sgn = W(a - lens) >= 0 ? 1 : -1;
                a = lens + sgn * Mathf.DegToRad(HerFront); up0 = Mathf.Max(up0, Mathf.DegToRad(20));
                herKeyLens = Mathf.RadToDeg(Dir(a, up0).AngleTo(lensDir)); herKeyFace = Mathf.RadToDeg(Dir(a, up0).AngleTo(fwd));
            }
            bool own = HerPart("src");
            bool split = own && HerPart("spec2");
            HerSpecSplit(her, split);
            var refColour = night ? CloseKeyColourNight : CloseKeyColourDay;
            herKey.LightColor = own ? SkinSafe(srcColour) : refColour;
            herKey.LightEnergy = (night ? CloseKeyNight : CloseKey) * m * HerKeyGain * k * (own ? Lum(refColour) / Mathf.Max(Lum(herKey.LightColor), 0.05f) : 1) * (src2 != null && night ? HerKeySide : 1);
            herKey.Visible = herKey.LightEnergy > 0.005f;
            herKey.ShadowEnabled = night && CloseKeyShadow; herKey.LightSize = 0.15f;
            Place(herKey, a, up0, 2.6f, center);
            herKeyOff = Mathf.RadToDeg(W(a - lens));
            herKey.LightSpecular = split ? HerTagSpec : 0.3f;
            herKeySpec = SpecTwin(scene, herKeySpec, "HerKey_spec", herKey, FromOk(Ok(srcColour)), 0.3f * HerSpecGain, split);
            // (her hair and gear in the source's own colour, as bright as the key's would be)
            var trueColour = own ? FromOk(Ok(srcColour)) : herKey.LightColor;
            float trueE = own ? herKey.LightEnergy * Mathf.Min(Lum(herKey.LightColor) / Mathf.Max(Lum(trueColour), 0.02f), 3) : herKey.LightEnergy;
            herKeyHair!.LightColor = own ? trueColour : night ? CloseKeyHairColour : herKey.LightColor;
            herKeyHair.LightEnergy = (own ? trueE : herKey.LightEnergy) * (night ? CloseKeyHair : 1); herKeyHair.Visible = herKey.Visible;
            if (night && CloseKeyHairEl >= 0) Place(herKeyHair, a, Mathf.DegToRad(CloseKeyHairEl), 2.6f, center);
            else herKeyHair.GlobalTransform = herKey.GlobalTransform;
            herKeyGear!.LightColor = trueColour; herKeyGear.LightEnergy = trueE; herKeyGear.Visible = herKey.Visible;
            herKeyGear.LightSpecular = night ? CloseKeyGearSpec : 0.3f; herKeyGear.GlobalTransform = herKey.GlobalTransform;
            // (by night the cool fill on the lens's far side from the key, raised on deep skin, People.HerSkinDark)
            float fillRatio = CloseFillRatio + CloseFillDeep * People.HerSkinDark(her.Person);
            herFill!.LightColor = HerKnobs && herFillCol is Color hfc ? hfc : own ? HerFillColour : CloseFillColourNight;
            herFill.LightEnergy = night ? (CloseFillNight > 0 ? CloseFillNight : CloseKeyNight * fillRatio) * m * HerFillGain * k * (src2 != null ? HerFillSide : 1) * (HerKnobs ? herFillK : 1) : 0;
            herFill.Visible = herFill.LightEnergy > 0.005f;
            float side = W(a - lens) >= 0 ? -1 : 1;
            Place(herFill, lens + side * Mathf.DegToRad(35), Mathf.DegToRad(10), 2.6f, center);
            herRim!.LightColor = new Color("#a9c4ff");
            bool rim2 = HerPart("rim2");
            herRim.LightEnergy = night ? CloseRimNight * m * HerRimGain * k * (rim2 ? HerRim2 : 1) : 0;
            herRim.Visible = herRim.LightEnergy > 0.005f;
            // (round 3: the rim from nearer straight behind, so it is a line on her far jaw, ear and hair, not a band)
            float rimAz = rim2 ? HerRimAz * (W(face - lens) < 0 ? -1 : 1) : CloseRimAz;
            Place(herRim, lens + Mathf.Pi - rimAz, Mathf.DegToRad(CloseRimEl), 2.4f, center + U * 0.15f);
            herRimHair ??= HerSpot(scene, "HerRim_hair", PlayerView.HerHairLayer, CloseRimSpec, 26);
            herRimHair.LightColor = herRim.LightColor; herRimHair.LightEnergy = rim2 ? herRim.LightEnergy * HerRimHair : 0;
            herRimHair.Visible = herRimHair.LightEnergy > 0.005f; herRimHair.GlobalTransform = herRim.GlobalTransform;
            // A second source (C01 s3: the moon beside her ember) on the face's other half, at HerSideGain of the key.
            herSide ??= HerSpot(scene, "HerSide", 2u | PlayerView.HerLayer, 0.3f, 24);
            herSideHair ??= HerSpot(scene, "HerSide_hair", PlayerView.HerHairLayer | PlayerView.HerGearLayer, 0.3f, 24);
            if (src2 is Vector3 && night)
            {
                herSide.LightColor = SkinSafe(src2Colour);
                herSide.LightEnergy = herKey.LightEnergy * HerSideGain * Lum(herKey.LightColor) / Mathf.Max(Lum(herSide.LightColor), 0.05f);
                float sa = face - (W(a - face) >= 0 ? 1 : -1) * Mathf.DegToRad(75);
                Place(herSide, sa, Mathf.DegToRad(20), 2.6f, center);
                herSideHair.LightColor = FromOk(Ok(src2Colour));
                herSideHair.LightEnergy = herSide.LightEnergy * Mathf.Min(Lum(herSide.LightColor) / Mathf.Max(Lum(herSideHair.LightColor), 0.02f), 3) * CloseKeyHair;
                herSideHair.GlobalTransform = herSide.GlobalTransform;
            }
            else herSide.LightEnergy = herSideHair.LightEnergy = 0;
            herSide.Visible = herSide.LightEnergy > 0.005f; herSideHair.Visible = herSideHair.LightEnergy > 0.005f;
            herSide.LightSpecular = split ? HerTagSpec : 0.3f;
            herSideSpec = SpecTwin(scene, herSideSpec, "HerSide_spec", herSide, src2 != null ? FromOk(Ok(src2Colour)) : herSide.LightColor, 0.3f * HerSpecGain, split);
            // Round 4: a kicker on the shadow side's edge (the far side from her key as the lens sees her): from behind her, cool,
            // in the coolest source's own colour (a blue lamp, a cold flame, else the moon's), and kept behind the front of her
            // temple (HerKickFace off where she faces), so it is a line on her cheek, jaw, ear and neck and her hair's edge.
            herKick ??= HerSpot(scene, "HerKick", 2u | PlayerView.HerLayer, 0.3f, 20);
            herKick.LightSpecular = split ? HerKickTag : 0.3f;
            herKickHair ??= HerSpot(scene, "HerKick_hair", PlayerView.HerHairLayer, 0.3f, 20);
            if (HerPart("kick") && night && HerKick > 0)
            {
                float ks = W(a - lens) >= 0 ? -1 : 1;
                float kaz = lens + ks * Mathf.DegToRad(180 - HerKickAz);
                float df = W(kaz - face), kf = Mathf.DegToRad(HerKickFace);
                if (Mathf.Abs(df) < kf) kaz = face + (df >= 0 ? 1 : -1) * kf;
                Place(herKick, kaz, Mathf.DegToRad(HerKickEl), 2.4f, center);
                var kc = !Warm(srcColour) ? srcColour : src2 != null && !Warm(src2Colour) ? src2Colour : new Color("#a9c4ff");
                herKick.LightColor = FromOk(Ok(kc));
                herKick.LightEnergy = CloseRimNight * m * HerKick * k * Mathf.Min(Lum(new Color("#a9c4ff")) / Mathf.Max(Lum(herKick.LightColor), 0.02f), 3);
                herKickHair.GlobalTransform = herKick.GlobalTransform; herKickHair.LightColor = herKick.LightColor;
                herKickHair.LightEnergy = herKick.LightEnergy * HerKickHair;
            }
            else herKick.LightEnergy = herKickHair.LightEnergy = 0;
            herKick.Visible = herKick.LightEnergy > 0.005f; herKickHair.Visible = herKickHair.LightEnergy > 0.005f;
            // Her catchlights: a light just above the lens, too faint to light her skin, its sheen whole on her wet eyes.
            // (its specular 15.5, which the eye shader reads as "sheen only, on the cornea": no diffuse there, its own roughness)
            herEye ??= HerSpot(scene, "HerEye", 2u | PlayerView.HerLayer, 15.5f, 4);
            if (HerPart("eye") && HerEye > 0)
            {
                var toCam = g.camera.GlobalPosition - e; float cd = toCam.Length();
                var camUp = g.camera.GlobalBasis.Y; var dir = toCam / Mathf.Max(cd, 1e-3f);
                var upPerp = (camUp - dir * dir.Dot(camUp)).Normalized(); float el = Mathf.DegToRad(HerEyeEl);
                herEyeOff = 0;
                if (HerPart("aim"))
                {
                    // (round 4: toward her gaze, so the lens's reflection off her cornea falls on the iris where she looks:
                    // her head's forward turned by her eyes' slide, HerGazeDeg per iris radius, +x to her left, +y down)
                    var gz = People.HerGaze(her.Person); var left = headUp.Cross(fwd).Normalized();
                    var gd = (fwd + left * Mathf.Tan(Mathf.DegToRad(gz.X * HerGazeDeg)) - headUp * Mathf.Tan(Mathf.DegToRad(gz.Y * HerGazeDeg))).Normalized();
                    float th = dir.AngleTo(gd), off = Mathf.Min(th * HerEyeAim, Mathf.DegToRad(HerEyeCap));
                    var ax = dir.Cross(gd);
                    if (th > 1e-3f && ax.LengthSquared() > 1e-8f) { dir = dir.Rotated(ax.Normalized(), off); upPerp = (camUp - dir * dir.Dot(camUp)).Normalized(); herEyeOff = Mathf.RadToDeg(off); }
                }
                herEye.GlobalPosition = e + (dir * Mathf.Cos(el) + upPerp * Mathf.Sin(el)) * cd;
                herEye.LookAt(e, camUp);
                herEye.SpotRange = cd + 2; herEye.LightEnergy = HerEye * k; herEye.LightSpecular = 15.5f;
                herEye.Visible = herEye.LightEnergy > 0.00005f;
            }
            else herEye.Visible = false;
            // Her key on her shoulders and chest (C01 s3: a lit face over grey-lilac skin): its colour from its side at HerBodyGain.
            herBody ??= HerSpot(scene, "HerBody", 2u | PlayerView.HerLayer, 0.3f, 14);
            if (HerPart("body") && HerBodyGain > 0)
            {
                var chest = center - U * 0.3f - fwd * 0.03f;
                // (round 4: narrowed to HerBodyAngle so it stays on her shoulders and chest: at 14 degrees it reached her eyes at
                // 60% of her key, a second frontal key on her face)
                herBody.LightColor = herKey.LightColor; herBody.SpotAngleAttenuation = 2; herBody.SpotAngle = HerPart("front") ? HerBodyAngle : 14;
                herBody.LightEnergy = herKey.LightEnergy * HerBodyGain;
                Place(herBody, a, up0 * 0.5f, 2.6f, chest);
                herBody.Visible = herBody.LightEnergy > 0.005f;
            }
            else herBody.Visible = false;
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
                herMoon.GlobalTransform = key.GlobalTransform;
                // (round 3: the moon on her skin in her skin's colour of it, as her key)
                herMoon.LightColor = HerPart("src") ? SkinSafe(key.LightColor) : key.LightColor;
                herMoon.LightSpecular = split ? HerTagSpec : key.LightSpecular;
                herMoon.ShadowEnabled = key.ShadowEnabled; herMoon.ShadowBlur = key.ShadowBlur; herMoon.LightAngularDistance = key.LightAngularDistance;
                herMoon.LightEnergy = Mathf.Lerp(key.LightEnergy, Mathf.Min(key.LightEnergy, want), k);
                herMoon.Visible = key.Visible;
                // (round 4: its sheen on her in the moon's own colour, a sheen-only twin as her key's)
                if (herMoonSpec == null || !IsInstanceValid(herMoonSpec))
                {
                    herMoonSpec = new DirectionalLight3D { Name = "HerMoon_spec", LightCullMask = 2u, DirectionalShadowMode = DirectionalLight3D.ShadowMode.Parallel2Splits, DirectionalShadowMaxDistance = 20, LightSpecular = HerTwinSpec };
                    scene.AddChild(herMoonSpec);
                }
                herMoonSpec.GlobalTransform = key.GlobalTransform; herMoonSpec.LightColor = FromOk(Ok(key.LightColor));
                herMoonSpec.ShadowEnabled = key.ShadowEnabled; herMoonSpec.ShadowBlur = key.ShadowBlur; herMoonSpec.LightAngularDistance = key.LightAngularDistance;
                herMoonSpec.LightEnergy = herMoon.LightEnergy * key.LightSpecular * HerSpecGain / HerTwinSpec * Mathf.Min(Lum(herMoon.LightColor) / Mathf.Max(Lum(herMoonSpec.LightColor), 0.02f), 3);
                herMoonSpec.Visible = split && herMoon.Visible && herMoonSpec.LightEnergy > 0;
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
                    // (round 4: a source within HerFrontMin of the lens is a frontal fill on her face: HerFireFront of it)
                    if (HerPart("front") && (lamp.GlobalPosition - center).AngleTo(cam - center) < Mathf.DegToRad(HerFrontMin)) herFire.LightEnergy *= HerFireFront;
                    herFire.OmniRange = lamp.OmniRange; herFire.OmniAttenuation = lamp.OmniAttenuation; herFire.LightSpecular = lamp.LightSpecular;
                    herFire.Visible = true;
                }
                else herFire.Visible = false;
            }
            else HerZoneBack();
            // Round 4: the light on her face (her key, side light, fire and the rigs' share at her eyes, the exposure counted)
            // held under HerFaceMax: her lit cheek no brighter than about 75 whatever the shot's lamps add.
            {
                float kA = herKey.Visible ? SpotAt(herKey, herKey.LightEnergy, e) : 0, sA = herSide.Visible ? SpotAt(herSide, herSide.LightEnergy, e) : 0;
                float fA = herFire != null && IsInstanceValid(herFire) && herFire.Visible ? OmniAt(herFire, herFire.LightEnergy, e) : 0;
                float bA = herBody.Visible ? SpotAt(herBody, herBody.LightEnergy, e) : 0;
                float mA = herMoon != null && IsInstanceValid(herMoon) && herMoon.Visible ? herMoon.LightEnergy * Lum(herMoon.LightColor) : 0;
                float nA = 0; foreach (var (_, t, _) in herNear) if (IsInstanceValid(t) && t.Visible) nA += OmniAt(t, t.LightEnergy, e);
                float ex = g.air.Env.TonemapExposure;
                float own2 = (kA + sA + fA + bA + mA) * ex, rest = (herRigsOnFace + nA + (herFill.Visible ? SpotAt(herFill, herFill.LightEnergy, e) : 0)) * ex;
                herFaceLight = own2 + rest;
                // (a band, not only a cap: the shots' own lamps and the moon put her lit cheek anywhere from 70 to 81 at the
                // same key; held between HerFaceMin and HerFaceMax, it lands at 72-75)
                if (HerPart("cap2") && HerFaceMax > 0 && own2 > 1e-4f && (herFaceLight > HerFaceMax || herFaceLight < HerFaceMin))
                {
                    float want = (herFaceLight > HerFaceMax ? HerFaceMax : HerFaceMin) - rest;
                    float f = Mathf.Clamp(want / own2, 0.6f, 1.3f);
                    foreach (var l in new Light3D?[] { herKey, herKeySpec, herSide, herSideSpec, herBody, herFire, herMoon, herMoonSpec }) if (l != null && IsInstanceValid(l)) l.LightEnergy *= f;
                    herFaceLight = own2 * f + rest;
                }
            }
            // Her skin's share of the sky's light, held to the close view's (its exposure and its hemi and env against the shot's).
            if (skinSky == 1)
            {
                double amb = g.air.Current.HemiIntensity + g.air.Current.EnvIntensity;
                float hold0 = Mathf.Min(1, m * (float)((pre.HemiIntensity + pre.EnvIntensity) / Math.Max(amb, 1e-3))) * HerSkyHold * (night ? 1 : CloseSkyDay);
                herSkyShown = Mathf.Lerp(1, Mathf.Clamp(hold0, 0, 1), k);
                People.HerSkyShare(her.Person, herSkyShown);
            }
        }

        /// <summary>Every other light near her face (C02 s8: a cold flame 0.3 m off her cheek was as strong on it as her key)
        /// held as her key is: off her layers, its twin on them at HerNearGain of it, exposure matched. Looked for at each
        /// shot's start and every half second (a flame lit or carried in mid-shot).</summary>
        void HerNearFind(Node3D scene, Vector3 e, float m)
        {
            if (herNearShot != player.Shot.Index || Shots.Clock - herNearAt >= 0.5)
            {
                if (herNearShot != player.Shot.Index) HerNearBack();
                herNearShot = player.Shot.Index; herNearAt = Shots.Clock;
                void Find(Node n)
                {
                    foreach (var c in n.GetChildren())
                    {
                        if (c is OmniLight3D o && o != herFire && !o.Name.ToString().StartsWith("Her") && o.IsVisibleInTree() && (o.LightCullMask & 2u) != 0 && OmniAt(o, o.LightEnergy, e) > 0.01f)
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
            if (herMoonSpec != null && IsInstanceValid(herMoonSpec)) herMoonSpec.Visible = false;
        }


        static bool Warm(Color c)
        {
            var o = Ok(c); float h = Mathf.PosMod(Mathf.RadToDeg(Mathf.Atan2(o.Z, o.Y)), 360);
            return new Vector2(o.Y, o.Z).Length() < 0.02f || (h >= 35 && h <= 115);
        }

        /// <summary>A light's sheen-only twin on her skin and eyes (round 4): its place, cone and shadow, the colour c at the light's
        /// luminance, at HerTwinSpec with its energy cut to match (its diffuse a fortieth of the light's: nothing).</summary>
        static SpotLight3D SpecTwin(Node at, SpotLight3D? t, string name, SpotLight3D l, Color c, float spec, bool on)
        {
            if (t == null || !IsInstanceValid(t)) t = HerSpot(at, name, l.LightCullMask, HerTwinSpec, l.SpotAngle);
            t.GlobalTransform = l.GlobalTransform; t.SpotAngle = l.SpotAngle; t.SpotRange = l.SpotRange; t.SpotAttenuation = l.SpotAttenuation;
            t.SpotAngleAttenuation = l.SpotAngleAttenuation; t.ShadowEnabled = l.ShadowEnabled; t.LightSize = l.LightSize; t.LightCullMask = l.LightCullMask;
            t.LightColor = c; t.LightSpecular = HerTwinSpec;
            t.LightEnergy = l.LightEnergy * spec / HerTwinSpec * Mathf.Min(Lum(l.LightColor) / Mathf.Max(Lum(c), 0.02f), 3);
            t.Visible = on && l.Visible && t.LightEnergy > 0.0001f;
            return t;
        }

        void HerSpecSplit(PersonView? her, bool on)
        {
            if (on == herSpecOn || her == null) return;
            herSpecOn = on; People.HerCineSpec(her.Person, on ? 1 : 0);
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
            foreach (var l in new Light3D?[] { herKey, herKeyHair, herKeyGear, herFill, herRim, herRimGear, herSide, herSideHair, herRimHair, herEye, herBody, herMoon, herFire, herKeySpec, herSideSpec, herKick, herKickHair, herMoonSpec }) if (l != null && IsInstanceValid(l)) l.QueueFree();
            herKeySpec = herSideSpec = herKick = herKickHair = null; herMoonSpec = null;
            if (herSpecOn && people.TryGetValue("her", out var hsp) && IsInstanceValid(hsp)) People.HerCineSpec(hsp.Person, 0);
            herSpecOn = false;
            herKey = herKeyHair = herKeyGear = herFill = herRim = herRimGear = herSide = herSideHair = herRimHair = herEye = herBody = null; herMoon = null; herFire = null;
            if (herSkyShown != 1 && people.TryGetValue("her", out var hs) && IsInstanceValid(hs)) People.HerSkyShare(hs.Person, 1);
            herSkyShown = 1;
            herKnobShot = -1; herFillK = 1; herScaleShot = 0; herFillCol = null; herOffShot = herOffNow = null;
            foreach (var gi in herMoved)
                if (IsInstanceValid(gi)) gi.Layers = (gi.Layers & ~(PlayerView.HerHairLayer | PlayerView.HerGearLayer)) | 2u;
            herMoved.Clear();
            if (herNightShown != 0)
            {
                if (people.TryGetValue("her", out var hv) && IsInstanceValid(hv)) { People.HerEyesNight(hv.Person, 0); People.HerSkinHold(hv.Person, 0); People.HerSkyShare(hv.Person, 1); }
                g.air.SetViewSkinGuard(0); g.air.SetViewHighlights(0); g.air.SetViewShadeHue(0);
                herNightShown = 0;
            }
        }
    }
}

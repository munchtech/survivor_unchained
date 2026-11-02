using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Her auto-attacks' shared hit kit (SKILL_VFX_STUDY §6 item 2): what every body her
/// Oathblade, Disc or Shield Bash strikes shows. Steel sparks off the body, flung
/// along the blow (one pooled spark batch, never a node per hit; capped per swing);
/// the struck rim is the crowd's own (CrowdView: Battle sets the body's Flash, the
/// VAT shader lights its rim and decays it in a few frames); and a 2 to 3 frame
/// hitstop on the first hit of a swing only (WorldScene asks FirstHitStop).
///
/// The Oathblade's sweep beats (dev only, --aa-beats): on her 3rd, 5th and 7th
/// swing a frame at +1 and +3 drawn frames and one as the first hit's hitstop
/// lands; one plain frame mid-fight (half a second after the 4th swing).
/// </summary>
public partial class BattleFx
{
    /// <summary>The Oathblade and its evolutions (skills.json oathblade: slash_steel, slash_holy, slash_blood).</summary>
    public static bool IsOath(string? art) => art is "slash_steel" or "slash_holy" or "slash_blood";

    /// <summary>The hitstop a blow asks for as the first hit of its swing (seconds; 0 none) and how long after
    /// the blow it lands: the sweep is revealed over its first 2 frames (OathReveal), so 0.03 s on, the blade
    /// has passed every body it struck and their flash, streaks, glint and rim are up when the frame holds.
    /// Her auto-attacks' arts only: the Disc and Shield Bash add theirs here.</summary>
    public static (double Len, double Delay) FirstHitStop(Ev.Hit h) =>
        h.Dot || h.ByFlare || h.Blocked ? (0, 0) : IsOath(h.Art) ? (0.042, 0.03) : (0, 0);

    /* ------------------------------------------------------- the sweep -- */

    // Her Oathblade's gold, its evolutions' hues (linear, near 1 so the tone curve keeps them a colour;
    // the white-hot lead is the shader's), and the sparks off what they strike.
    static readonly Color OathSteel = Hdr("#ffb83a", 1.15f), OathHoly = Hdr("#ffd772", 1.2f), OathBlood = Hdr("#ff2a1a", 1.15f);
    static Color OathHue(string art) => art switch { "slash_holy" => OathHoly, "slash_blood" => OathBlood, _ => OathSteel };
    static Color OathSpark(string art) => art == "slash_blood" ? Blood : art == "slash_holy" ? OathGold : Ember;

    /// <summary>The sweep's inner radius (her hand, metres), its reveal and its erosion (seconds: 2 and 4 frames).</summary>
    const float OathInner = 0.55f, OathReveal = 2 / 60f, OathErode = 4 / 60f;

    // The swing in flight (for the struck's streaks: flung on along the blade's path), and how many full kits it has thrown.
    Vector3 oathAt;
    bool oathMirror;
    int oathKits;
    /// <summary>Full kits (streaks, glint) per swing; the rest of a crowd struck get three streaks and the rim.</summary>
    const int OathKits = 6;

    /// <summary>The Oathblade's sweep: ONE gold crescent leaving her hand (0.55 m) out to the blade's reach
    /// (1.8-2.2 m), revealed along the arc over 2 frames and eaten from its tail over 4, light only, its body
    /// fine broken streaks (shaders/oath_sweep.gdshader, art/fx/oath_streaks.png); and a real gold pool of
    /// light on the ground under the middle of the arc (OathPool).</summary>
    void OathSweep(Ev.Slash e, Vector3 at, float facing, float reach, float g)
    {
        string art = e.Art ?? "";
        float rich = Mathf.Min(g, 1.35f);
        oathAt = at; oathMirror = mirror; oathKits = 0;
        var hue = OathHue(art);
        float outer = Mathf.Clamp(reach * 0.66f * (1 + 0.3f * (rich - 1)), 1.8f, 2.2f);
        OathBlades.Add(at, facing, outer, (float)e.Arc * 1.1f, mirror, OathReveal, OathErode, hue * (0.9f + 0.1f * g), OathInner / outer);
        float mr = (OathInner + outer) * 0.5f;
        double px = e.X + Math.Cos(e.Angle) * mr, pz = e.Z + Math.Sin(e.Angle) * mr;
        OathPool(V(px, Y(px, pz) + 0.3, pz), art == "slash_blood" ? new Color("#ff6a40") : new Color("#ffc25a"));
        if (AaBeats && oathSwings is 3 or 5 or 7 && GetViewport()?.GetCamera3D() is { } cam)
        {
            var sp = cam.UnprojectPosition(V(px, Y(px, pz), pz));
            var hp = cam.UnprojectPosition(at);
            GD.Print($"[aa-beats] pool s{oathSwings} screen {sp.X:F0},{sp.Y:F0} her {hp.X:F0},{hp.Y:F0}");
        }
        // The Watch's oath along the edge of a ranked Oathblade: a few gold glints that hang.
        if (e.Rank >= 5 && art != "slash_blood")
            for (int i = 0; i < 4; i++)
            {
                float a = (float)e.Angle + (float)e.Arc * (R() - 0.5f);
                var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                Sparks.Spawn(at + rim * outer * 0.95f, Vector3.Up * 0.4f, 0.5f, 0.12f, OathGold, OathGold * 0.3f, 0.02f, 0, 2, sprite: Sprites.Of("star"), spinV: 3);
            }
    }

    /* -------------------------------------------------------- the pool -- */

    /// <summary>Pooled unshadowed lights for the sweep's pool: a swing's lives 6 frames, she swings about once a second.</summary>
    const int OathPools = 3;
    /// <summary>Full for 3 frames, then fading over 3 (seconds, on the fight's clock: a hitstop holds it).</summary>
    const float PoolHold = 3 / 60f, PoolFade = 3 / 60f;
    readonly OmniLight3D?[] oathPools = new OmniLight3D?[OathPools];
    readonly float[] oathPoolAge = { 9, 9, 9 };
    readonly float[] oathPoolEnergy = new float[OathPools];
    int oathPoolNext;
    /// <summary>The pool's energy scale (dev: --aa-pool K; 0 for the before frames).</summary>
    static readonly float PoolScale = Args.Num("aa-pool", 1f);

    /// <summary>The sweep's light on the ground: an unshadowed omni 0.3 m up at the arc's middle, 2.5 m in range,
    /// about +50% on the ground under it at night, a warming of the grass by day.</summary>
    void OathPool(Vector3 at, Color hue)
    {
        int i = oathPoolNext++ % OathPools;
        if (oathPools[i] == null)
        {
            oathPools[i] = new OmniLight3D { OmniRange = 2.5f, OmniAttenuation = 1.2f, ShadowEnabled = false, LightSpecular = 0.2f, Visible = false };
            AddChild(oathPools[i]);
        }
        var l = oathPools[i]!;
        l.Position = at;
        l.LightColor = hue;
        oathPoolEnergy[i] = (Flare.Night ? 4.6f : 7f) * PoolScale;
        oathPoolAge[i] = 0;
        StepOathPool(i, 0);
    }

    void StepOathPools(float dt) { for (int i = 0; i < OathPools; i++) StepOathPool(i, dt); }

    void StepOathPool(int i, float dt)
    {
        if (oathPools[i] is not { } l) return;
        float a = oathPoolAge[i] += dt;
        float k = a < PoolHold ? 1 : Mathf.Max(0, 1 - (a - PoolHold) / PoolFade);
        l.LightEnergy = oathPoolEnergy[i] * k * k;
        l.Visible = k > 0.001f && oathPoolEnergy[i] > 0 && !Flare.HushesSwings;
    }

    /* ----------------------------------------------------- the hit kit -- */

    /// <summary>The struck rim's bodies (enemy id: until when, on the fight's clock); CrowdView.StruckRim reads it.</summary>
    readonly System.Collections.Generic.Dictionary<int, double> struckRims = new();
    /// <summary>The rim's life: 2 frames.</summary>
    const double RimLife = 2.5 / 60;
    /// <summary>(dev: --aa-norim, the beats without the rim, for an A/B)</summary>
    static readonly bool NoRim = Args.Has("aa-norim");
    bool StruckRimOn(int id) => struckRims.TryGetValue(id, out var until) && time < until;

    /// <summary>The shared hit kit at a struck body (`at`, chest height; `away` the blow's way, flat):
    /// 8-12 steel streaks (0.2-0.4 m, velocity-stretched: Sparks.P.Stretch; white-hot cooling to `spark`,
    /// 0.15-0.25 s) flung on along the blow and `path`; a 4-point contact glint (0.66-0.8 m, 3 frames); a 2-frame
    /// gold-white fresnel rim on the body (`target`, the enemy's id; the crowd's VAT shader draws it). The first
    /// body of an Oathblade swing (or any call with `first`) also gets the impact flash, a light burst for 4 frames:
    /// what the first hit's hitstop holds. `full` false (past the caller's cap, or the frame's hit budget spent)
    /// throws three streaks only. The Disc and Shield Bash pass their own `spark` hue and `path`
    /// (their callers cap their kits).</summary>
    public void HitKit(Vector3 at, Vector3 away, Color spark, float g, bool crit, bool full = true, Vector3? path = null, int target = -1, bool first = false)
    {
        Vector3 along;
        if (path is { } own) along = own;
        else
        {
            // The Oathblade's: along the blade's path at this body (the swing's tangent there), so the streaks fly on with the cut.
            first = first || oathKits == 0;
            full = full && oathKits++ < OathKits;
            var rim = at - oathAt; rim.Y = 0;
            along = rim.LengthSquared() > 0.01f ? new Vector3(-rim.Z, 0, rim.X).Normalized() * (oathMirror ? -1 : 1) : Vector3.Zero;
        }
        // (the rim on the full kits only: on all twenty a swing strikes the crowd went a field of lit ghosts)
        if (target >= 0 && full && !NoRim) struckRims[target] = time + RimLife;
        int n = full ? (crit ? 12 : 9) + (first ? 3 : 0) : 3;
        for (int i = 0; i < n; i++)
        {
            var dir = (away * (0.5f + R() * 0.9f) + along * (0.4f + R() * 1.0f) + new Vector3((R() - 0.5f) * 0.9f, 0.25f + R() * 0.6f, (R() - 0.5f) * 0.9f)).Normalized();
            float speed = 5.5f + R() * 4.5f, len = 0.2f + R() * 0.2f;
            Sparks.Spawn(new Sparks.P
            {
                At = at + new Vector3((R() - 0.5f) * 0.2f, (R() - 0.5f) * 0.35f, (R() - 0.5f) * 0.2f), V = dir * speed,
                Life = 0.15f + R() * 0.1f, Size = 0.034f, SizeEnd = 0.018f, Color = SteelWhite * 1.15f, ColorEnd = spark * 0.8f,
                Gravity = 9, Drag = 2.2f, Alpha = 1, Sprite = -1, Stretch = len / speed,
            });
        }
        if (!full) return;
        // The contact glint: a 4-point star at the body, white-gold cooling to the spark's hue, 3 frames.
        float gs = (crit ? 0.8f : 0.66f) * Mathf.Min(g, 1.2f);
        Sparks.Spawn(new Sparks.P
        {
            At = at - away * 0.15f, Life = 0.05f, Size = gs, SizeEnd = gs * 0.55f, Color = Hdr("#fff2d6", 1.7f), ColorEnd = spark * 0.35f,
            Alpha = 1, Sprite = Star4, Spin = 0.2f + R() * 0.4f, SpinV = 0.001f,
        });
        if (!first) return;
        // The impact flash on the first contact: a hot light burst, 4 frames (the hitstop holds it).
        Sparks.Spawn(new Sparks.P
        {
            At = at - away * 0.1f, Life = 0.07f, Size = 0.6f, SizeEnd = 0.8f, Color = Hdr("#ffd890", 1.1f), ColorEnd = spark * 0.12f,
            Alpha = 1, Sprite = Sprites.Range("light").First + 1 + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f,
        });
    }

    /// <summary>A dark chip puff off a struck body (for the Disc and the Bash): a solid brown-grey puff, densest at
    /// its centre (Sparks.P.Core, on the pack's solid puffs only: its last three are rings and read as grey donuts),
    /// 0.3-0.4 m, 0.25-0.35 s, drifting along `away`; `n` puffs.</summary>
    public void ChipPuff(Vector3 at, Vector3 away, int n = 2)
    {
        for (int i = 0; i < n; i++)
        {
            float s = 0.3f + R() * 0.1f;
            Smoke.Spawn(new Sparks.P
            {
                At = at + new Vector3((R() - 0.5f) * 0.15f, (R() - 0.5f) * 0.15f, (R() - 0.5f) * 0.15f),
                V = away * (0.8f + R() * 0.8f) + Vector3.Up * (0.3f + R() * 0.3f), Drag = 3,
                Life = 0.25f + R() * 0.1f, Size = s * 0.7f, SizeEnd = s, Color = new Color(0.2f, 0.17f, 0.14f), ColorEnd = new Color(0.16f, 0.14f, 0.12f),
                Alpha = 0.7f, Sprite = SolidPuff(), Core = true,
            });
        }
    }

    /// <summary>One of the pack's solid smoke puffs (its first seven; the last three are rings).</summary>
    static float SolidPuff() => Sprites.Range("smoke").First + 1 + (int)(R() * 6.99f);

    /* ---------------------------------------------------------- the disc -- */

    /// <summary>The Judgement Disc and its evolutions (skills.json judgement_disc: disc, disc_aegis, disc_reckon).</summary>
    public static bool IsDisc(string? art) => art is "disc" or "disc_aegis" or "disc_reckon";

    // Its hue: the holy palette's gold (Palette: Holy glow #ffd46a), Aegis's ward-blue, Reckoning's deeper gold.
    // Near 1, so the tone curve keeps them a colour; the white is the head's heart and rays.
    static Color DiscHue(string art) => art switch { "disc_aegis" => Hdr("#cfe0ff", 1f), "disc_reckon" => Hdr("#ffb848", 1.05f), _ => Hdr("#ffd46a", 1f) };
    static Color DiscSpark(string art) => art == "disc_aegis" ? Hdr("#9ab8ff", 1.6f) : OathGold;
    // The pool it carries over the ground: warm (Aegis's cool), a light for the first four, a glow for the rest.
    static Color DiscPoolHue(string art) => art == "disc_aegis" ? new Color("#b8ccff") : new Color("#ffc46a");

    /// <summary>At most this many discs carry a real (unshadowed) light; the rest a decal glow on the ground.</summary>
    const int DiscLights = 4;
    readonly OmniLight3D[] discLamps = new OmniLight3D[DiscLights];
    readonly System.Collections.Generic.List<Decal> discGlows = new();
    int discLit, discGlowN;
    Batch discs = null!;
    /// <summary>A 4-point star (the pack's star layer 23), the glint of a struck body.</summary>
    static int Star4 => Sprites.Range("star").First + 2 + 1;

    void DiscReady()
    {
        discs = Add(new Batch(DiscMesh(), 120, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/disc.gdshader") }));
        wedges = Add(new Batch(WedgeMesh(), 8, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/bash_wedge.gdshader") }));
        for (int i = 0; i < DiscLights; i++)
        {
            discLamps[i] = new OmniLight3D { LightEnergy = 0, OmniRange = 2.6f, OmniAttenuation = 1.3f, ShadowEnabled = false, Visible = false };
            AddChild(discLamps[i]);
        }
    }

    /// <summary>The disc's head, flat in the ground's plane round the origin, 0.26 m in radius, its mesh out to
    /// 1.6x that for its halo: UV.x 0 at the centre to 1 at the halo's edge, UV.y the angle round it (shaders/disc.gdshader).</summary>
    static ArrayMesh DiscMesh()
    {
        const int N = 64, Rings = 8;
        const float Rad = DiscRad * 1.6f, Thick = 0.012f;
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        for (int side = 0; side < 2; side++)
        {
            var n = side == 0 ? Vector3.Up : Vector3.Down;
            var lift = n * Thick;
            for (int k = 0; k < Rings; k++)
            {
                float r0 = k / (float)Rings, r1 = (k + 1) / (float)Rings;
                for (int i = 0; i < N; i++)
                {
                    float u0 = i / (float)N, u1 = (i + 1) / (float)N;
                    var d0 = new Vector3(Mathf.Cos(u0 * Mathf.Tau), 0, Mathf.Sin(u0 * Mathf.Tau));
                    var d1 = new Vector3(Mathf.Cos(u1 * Mathf.Tau), 0, Mathf.Sin(u1 * Mathf.Tau));
                    void P(Vector3 d, float r, float u) { st.SetNormal(n); st.SetUV(new Vector2(r, u)); st.AddVertex(d * r * Rad + lift); }
                    P(d0, r0, u0); P(d0, r1, u0); P(d1, r1, u1);
                    P(d0, r0, u0); P(d1, r1, u1); P(d1, r0, u1);
                }
            }
        }
        return st.Commit();
    }

    /// <summary>The disc's radius (metres, before its throw's scale).</summary>
    const float DiscRad = 0.26f;

    void DiscsBegin() { discLit = 0; discGlowN = 0; discs.Begin(); }

    void DiscsEnd()
    {
        discs.End();
        for (int i = discLit; i < DiscLights; i++) { discLamps[i].Visible = false; discLamps[i].LightEnergy = 0; }
        for (int i = discGlowN; i < discGlows.Count; i++) discGlows[i].Visible = false;
    }

    /// <summary>The Judgement Disc in flight: a spinning head (shaders/disc.gdshader: a white-hot core, a gold face
    /// smeared by its turn, a thin bright steel rim, a soft halo to 1.6x), a curved additive ribbon behind it at 90%
    /// of its width fading over 0.18 s (so it draws the bounces as a curve), and its light riding with it.</summary>
    bool DiscFlight(Projectile p, Vector3 at, double now, float g, long key)
    {
        string art = p.Art;
        float s = 1.1f * Mathf.Sqrt(g) * (art == "disc_reckon" ? 1.15f : 1);
        var hue = DiscHue(art);
        float spin = (float)(now * 16 + p.Id);
        // Leaving her hand it is held down, so it never blooms over her.
        float near = new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length();
        float off = Mathf.Lerp(0.35f, 1, Mathf.SmoothStep(0.8f, 3f, near));
        if (AaBeats && discThrows >= 2 && !discFlyShot && near > 1.8f && near < 6f) { discFlyShot = true; Shots.WantFrames("d_fly", 1); GD.Print($"[aa-beats] disc in flight t={time:F2}"); }
        // A faint dark bed under it (so the head shows over the pale dead), and the head.
        Shade(at, 1.0f * s, 0.3f);
        discs.Add(new Transform3D(new Godot.Basis(Vector3.Up, -spin).Scaled(Vector3.One * s), at), hue * off);
        // Its wake: a ribbon at 90% of the head's width, tapering and fading over 0.18 s.
        Ribbons.Feed(key, at, DiscRad * 2 * 0.9f * s, 0.18f, art == "disc_aegis" ? Hdr("#bcd4ff", 1f) : Hdr("#ffb040", 1f), 1.5f * off, Ribbons.Style.Glow);
        if (R() < 0.3f)
        {
            float a = R() * Mathf.Tau;
            var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Sparks.Spawn(at + rim * 0.33f * s, new Vector3(-rim.Z, 0, rim.X) * 3.5f + rim * 1.5f + Vector3.Up * 0.5f, 0.2f, 0.05f, Hdr("#ffe8a0", 2f), Hdr("#ff9a20", 1.4f), 0.01f, 0, 3);
        }
        // The pool: a real light for the first four, a glow on the ground for the rest.
        var ground = V(p.X, heightAt(p.X, p.Z), p.Z);
        var pool = DiscPoolHue(art);
        if (discLit < DiscLights)
        {
            var l = discLamps[discLit++];
            // (riding with the head, 0.4 m over it: it lights the bodies it passes and the ground under it)
            l.Position = at + Vector3.Up * 0.4f;
            l.LightColor = pool;
            // (squared near her: a light at her hip lit her before the disc had left her)
            l.LightEnergy = 1.6f * off * off;
            l.Visible = true;
        }
        else
        {
            if (discGlowN == discGlows.Count)
            {
                var d = new Decal { UpperFade = 0.3f, LowerFade = 0.3f, CullMask = 1, TextureEmission = glowTex, AlbedoMix = 0, NormalFade = MarkNormalFade, EmissionEnergy = 1f };
                AddChild(d);
                discGlows.Add(d);
            }
            var gd = discGlows[discGlowN++];
            gd.Position = ground;
            gd.Size = new Vector3(2.4f, 1.2f, 2.4f);
            gd.Modulate = pool * (0.45f * off);
            gd.Visible = true;
        }
        return true;
    }

    /// <summary>A body the disc strikes: the shared hit kit (HitKit: streaks flung on along the disc's way, the
    /// contact glint, the gold struck rim on the body; the impact flash on its throw's first body) and a dark
    /// chip puff (ChipPuff). No hitstop: it bounces through five bodies every 2.2 s, and a hold on its first hit
    /// stuttered under the Oathblade's own.</summary>
    void DiscStruck(Ev.Hit e, Vector3 at, Vector3 away, float g, bool rich)
    {
        string art = e.Art ?? "";
        int nth = DiscHitsOf(e.Target);
        BeatDiscHit(nth);
        HitKit(at, away, DiscSpark(art), g, e.Crit, rich, away, e.Target, first: nth == 1);
        if (rich) ChipPuff(at, away, 2);
    }

    /// <summary>Which of its throw's bodies this is (1 the first; 0 unknown): the living disc whose last hit it was.</summary>
    int DiscHitsOf(int target)
    {
        if (b0 == null) return 0;
        foreach (var p in b0.Projectiles.Living())
            if (IsDisc(p.Art) && p.Hits.Count > 0 && p.Hits[^1] == target) return p.Hits.Count;
        return 0;
    }

    /* ----------------------------------------------------- the shield bash -- */

    // Bronze-gold, dented: the shield's face catching the blow (near 1, a colour, never a white ring).
    static readonly Color BashBronze = Hdr("#e0a048", 1.25f), BashSpark = Hdr("#ffbe5a", 2.2f);
    double bashAt = -1;
    Vector3 bashFrom;
    int bashKits;
    readonly System.Collections.Generic.Dictionary<int, double> stunned = new();

    /// <summary>Shield Bash: a short heavy shove of the shield's face. A bronze-gold wedge of force driven forward
    /// over the ground across exactly what it strikes (the sim's +-1.2 rad to 3.4 m: shaders/bash_wedge.gdshader),
    /// 1.2 m across at the shield, its weight on her facing line, its front out over 4 frames on the frame's own
    /// clock (a hitstop holds the bodies, never the shove); the shield's contact glint and light; a ground plow of
    /// 30 low solid dust puffs and grit running outward. The struck get the hit kit (BashStruck) and a stun glint;
    /// the hitstop is WorldScene's (3 frames). Wide: the same, mirrored behind her.</summary>
    void ShieldBash(Ev.Ability e)
    {
        float gy = Y(e.X, e.Z);
        var her = V(e.X, gy, e.Z);
        bashAt = time; bashFrom = her; bashKits = 0;
        BeatBash();
        int sides = e.Wide ? 2 : 1;
        float reach = (float)(e.Radius > 0 ? e.Radius : 3.4);
        for (int k = 0; k < sides; k++)
        {
            float ang = (float)e.Angle + k * Mathf.Pi;
            var dir = new Vector3(Mathf.Cos(ang), 0, Mathf.Sin(ang));
            liveWedges.Add(new Wedge { At = her + Vector3.Up * 0.06f, Angle = ang, Reach = reach });
            var face = her + dir * 0.75f + Vector3.Up * 0.85f;
            // The shield's face meeting them: a white-gold glint off its boss and a short bronze light burst, 4 frames.
            Sparks.Spawn(new Sparks.P
            {
                At = face, Life = 0.07f, Size = 0.6f, SizeEnd = 0.35f, Color = Hdr("#fff2d8", 1.5f), ColorEnd = BashBronze * 0.3f,
                Alpha = 1, Sprite = Star4, Spin = 0.38f, SpinV = 0.001f,
            });
            Sparks.Spawn(new Sparks.P { At = face + dir * 0.2f, V = dir * 2f, Life = 0.07f, Size = 0.7f, SizeEnd = 1.0f, Color = BashBronze * 0.8f, ColorEnd = BashBronze * 0.1f, Alpha = 1, Sprite = Sprites.Range("light").First + 1 + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f });
            Flash(face + dir * 0.6f - Vector3.Up * 0.4f, new Color("#ffc878"), 6, 0.16f, 5);
            // The plow: low solid dust thrown outward across the cone from the shield's line, 3-5 m/s, dragged to a stop.
            for (int i = 0; i < BashPlow; i++)
            {
                float a = ang + (R() + R() - 1) * 1.2f, d = 0.7f + R() * 1.4f;
                var u = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                double x = e.X + u.X * d, z = e.Z + u.Z * d;
                float sz = 0.28f + R() * 0.18f;
                Smoke.Spawn(new Sparks.P
                {
                    At = V(x, Y(x, z) + 0.1 + R() * 0.08, z), V = u * (3 + R() * 2) + Vector3.Up * (0.15f + R() * 0.25f), Drag = 3.2f, Gravity = 0.6f,
                    Life = 0.4f + R() * 0.2f, Size = sz * 0.6f, SizeEnd = sz, Color = new Color(0.36f, 0.31f, 0.25f), ColorEnd = new Color(0.24f, 0.21f, 0.17f),
                    Alpha = 0.6f, Sprite = SolidPuff(), Core = true,
                });
            }
            // Grit: bronze-lit flecks streaking out low with the plow.
            for (int i = 0; i < 10; i++)
            {
                float a = ang + (R() + R() - 1) * 1.1f;
                var u = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                double x = e.X + u.X * (0.8f + R()), z = e.Z + u.Z * (0.8f + R());
                float sp = 4 + R() * 2;
                Sparks.Spawn(new Sparks.P
                {
                    At = V(x, Y(x, z) + 0.12, z), V = u * sp + Vector3.Up * (0.6f + R() * 0.8f), Gravity = 9, Drag = 2.5f,
                    Life = 0.25f + R() * 0.15f, Size = 0.022f, SizeEnd = 0.012f, Color = BashBronze * 0.7f, ColorEnd = BashBronze * 0.15f,
                    Alpha = 1, Sprite = -1, Stretch = 0.25f / sp,
                });
            }
        }
    }

    /// <summary>The plow's dust puffs a side.</summary>
    const int BashPlow = 30;

    /// <summary>The wedge's life, on the frame's own clock (seconds: 5 frames, its front out by the 4th).</summary>
    const float WedgeLife = 5 / 60f;
    struct Wedge { public Vector3 At; public float Angle, Reach, Age; }
    readonly System.Collections.Generic.List<Wedge> liveWedges = new();
    Batch wedges = null!;

    /// <summary>The wedge's mesh: the sim's +-1.2 rad sector from the shield (0.65 m, of a unit reach) to the reach, flat;
    /// UV.x out along it, UV.y across it (-1..1).</summary>
    static ArrayMesh WedgeMesh()
    {
        const int Na = 40, Nr = 16;
        const float Inner = 0.65f / 3.4f, Half = 1.2f;
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        void P(int i, int j)
        {
            float v = i / (float)Na * 2 - 1, u = j / (float)Nr, a = v * Half, r = Mathf.Lerp(Inner, 1, u);
            st.SetNormal(Vector3.Up); st.SetUV(new Vector2(u, v)); st.AddVertex(new Vector3(Mathf.Cos(a) * r, 0, Mathf.Sin(a) * r));
        }
        for (int i = 0; i < Na; i++)
            for (int j = 0; j < Nr; j++) { P(i, j); P(i + 1, j); P(i + 1, j + 1); P(i, j); P(i + 1, j + 1); P(i, j + 1); }
        return st.Commit();
    }

    void StepWedges()
    {
        wedges.Begin();
        float dt = frameDt > 0 ? (float)GetProcessDeltaTime() : 0;
        for (int i = liveWedges.Count - 1; i >= 0; i--)
        {
            var w = liveWedges[i];
            if (w.Age >= WedgeLife) { liveWedges.RemoveAt(i); continue; }
            wedges.Add(new Transform3D(new Godot.Basis(Vector3.Up, -w.Angle).Scaled(Vector3.One * w.Reach), w.At), BashBronze with { A = w.Age / WedgeLife });
            w.Age += dt;
            liveWedges[i] = w;
        }
        wedges.End();
    }

    /// <summary>A blow of the Bash (its hits carry no art: they land in the same step as its event, within its reach):
    /// the hit kit thrown back from her (the first body its impact flash), a chip puff, and the body marked for its
    /// stun glint. False for any other blow.</summary>
    bool BashStruck(Ev.Hit e, Vector3 at)
    {
        if (time != bashAt || e.Art != null || e.Dot) return false;
        var away = at - bashFrom; away.Y = 0;
        if (away.LengthSquared() > 3.7f * 3.7f) return false;
        away = away.LengthSquared() > 0.01f ? away.Normalized() : Vector3.Forward;
        bool full = bashKits < 8 && hitBudget-- > 0;
        HitKit(at, away, BashSpark, 1, e.Crit, full, away, e.Target, first: bashKits == 0);
        if (full) ChipPuff(at, away, 1);
        bashKits++;
        stunned[e.Target] = time + 1.5;
        if (AaBeats && bashBeat == 1 && throwLog.Count < 3 && b0 != null && b0.Enemies.Items[e.Target] is { } en)
        {
            var (x, z) = Drawn?.Of(en) ?? (en.X, en.Z);
            throwLog.Add((e.Target, x, z, time, 0));
        }
        return true;
    }

    // (dev, --aa-beats: the first bash's first three struck, their drawn place logged for 0.35 s: how far they are thrown)
    readonly System.Collections.Generic.List<(int Id, double X, double Z, double T, int N)> throwLog = new();

    void LogThrows(Battle b)
    {
        for (int i = 0; i < throwLog.Count; i++)
        {
            var (id, x0, z0, t0, n) = throwLog[i];
            if (n < 0) continue;
            var en = b.Enemies.Items[id];
            var (x, z) = Drawn?.Of(en) ?? (en.X, en.Z);
            double dx = x - x0, dz = z - z0, simd = Math.Sqrt((en.X - x0) * (en.X - x0) + (en.Z - z0) * (en.Z - z0));
            GD.Print($"[aa-throw] id={id} f={n} t={time - t0:F3} drawn={Math.Sqrt(dx * dx + dz * dz):F2} sim={simd:F2} alive={en.Alive} state={en.State} kb=({en.Kbx:F2},{en.Kbz:F2}) mass={en.Mass:F1}");
            throwLog[i] = (id, x0, z0, t0, time - t0 > 0.35 ? -1 : n + 1);
        }
    }

    /// <summary>The stun glint's size (metres).</summary>
    const float StunGlint = 0.28f;

    /// <summary>The stunned: a small dim gold 4-point glint circling over each for its stun, each twinkling
    /// on its own phase (a crowd of them all lit at once read as a field of icons).</summary>
    void StunGlints(Battle b)
    {
        StepWedges();
        if (AaBeats) LogThrows(b);
        if (stunned.Count == 0 || frameDt <= 0) return;
        System.Collections.Generic.List<int>? gone = null;
        foreach (var (id, until) in stunned)
        {
            var en = id >= 0 && id < b.Enemies.Capacity ? b.Enemies.Items[id] : null;
            if (en == null || !en.Alive || time > until || !en.Status.Has(StatusKind.Stun)) { (gone ??= new()).Add(id); continue; }
            float ph = (float)time * 5 + id * 2.3f;
            float tw = 0.3f + 0.7f * Mathf.Pow(Mathf.Max(0, Mathf.Sin(ph * 1.6f)), 2);
            var (gx, gz) = Drawn?.Of(en) ?? (en.X, en.Z);
            var over = V(gx, Y(gx, gz) + 2.05, gz) + new Vector3(Mathf.Cos(ph), 0, Mathf.Sin(ph)) * 0.2f;
            Sparks.Spawn(new Sparks.P
            {
                At = over, Life = frameDt * 1.5f, Size = StunGlint, SizeEnd = StunGlint, Color = OathGold * (0.95f * tw), ColorEnd = OathGold * (0.95f * tw),
                Alpha = 1, Sprite = Star4, Spin = 0.001f, SpinV = 0.001f,
            });
        }
        if (gone != null) foreach (var id in gone) stunned.Remove(id);
    }

    /* --------------------------------------------------------- the beats -- */

    int discThrows, bashBeat;
    bool discBeat, discHitShot, discBounceShot, discFlyShot;

    /// <summary>The Disc's beats: half a second after her 3rd throw (in flight), then that throw's
    /// first hit and its first bounce (the next frame after each, as the player sees them land).</summary>
    void BeatDiscThrow()
    {
        if (!AaBeats) return;
        discThrows++;
        if (discThrows == 3) { discBeat = true; }
        GD.Print($"[aa-beats] disc {discThrows} t={time:F2}");
    }

    void BeatDiscHit(int n)
    {
        if (!AaBeats || !discBeat || b0 == null) return;
        if (n == 1 && !discHitShot) { discHitShot = true; Shots.WantFrames("d_hit", 1); GD.Print($"[aa-beats] disc hit t={time:F2}"); }
        else if (n == 2 && discHitShot && !discBounceShot) { discBounceShot = true; Shots.WantFrames("d_bounce", 1); GD.Print($"[aa-beats] disc bounce t={time:F2}"); }
    }

    /// <summary>The Bash's beats: its first two, at +1 and +3 drawn frames.</summary>
    void BeatBash()
    {
        if (!AaBeats) return;
        bashBeat++;
        if (bashBeat <= 2) { Shots.WantFrames($"b{bashBeat}_f1", 1); Shots.WantFrames($"b{bashBeat}_f3", 3); }
        GD.Print($"[aa-beats] bash {bashBeat} t={time:F2}");
    }

    static readonly bool AaBeats = Args.Has("aa-beats");
    int oathSwings, beatHitFor;

    void BeatSwing(Ev.Slash e)
    {
        if (!AaBeats) return;
        oathSwings++;
        if (oathSwings is 3 or 5 or 7)
        {
            Shots.WantFrames($"s{oathSwings}_f1", 1);
            Shots.WantFrames($"s{oathSwings}_f3", 3);
            Shots.WantFrames($"s{oathSwings}_f6", 6);
            beatHitFor = oathSwings;
        }
        else beatHitFor = 0;
        if (oathSwings == 4) Shots.Want("mid", 0.5);
        GD.Print($"[aa-beats] swing {oathSwings} t={time:F2} angle={e.Angle:F2} arc={e.Arc:F2} reach={e.Reach:F2}");
    }

    void BeatHit(Ev.Hit e)
    {
        if (AaBeats && oathSwings == 5 && b0 != null) GD.Print($"[aa-beats] hit at dx={e.X - b0.Player.X:F2} dz={e.Z - b0.Player.Z:F2} angle={Math.Atan2(e.Z - b0.Player.Z, e.X - b0.Player.X):F2}");
        if (!AaBeats || beatHitFor == 0) return;
        // (the frame the first hit's hitstop holds: its delay is 0.03 s, two frames on)
        Shots.WantFrames($"s{beatHitFor}_hit", 2);
        beatHitFor = 0;
    }
}

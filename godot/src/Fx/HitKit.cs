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

    /// <summary>The sweep's inner radius (her hand, metres), its reveal and its erosion (seconds, real frames through a
    /// hitstop: revealed by f2, its peak; half eaten by f4, gone by f6).</summary>
    const float OathInner = 0.55f, OathReveal = 3 / 60f, OathErode = 4 / 60f;

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

    /// <summary>The struck rim's bodies (enemy id: the drawn frame it was struck on); CrowdView.StruckRim reads it.</summary>
    readonly System.Collections.Generic.Dictionary<int, long> struckRims = new();
    /// <summary>The struck look in drawn frames (r3 judge): a warm-white flash for 2 (30% then 12% blend), then a gold
    /// fresnel rim fading to nothing over 8 (on real frames: a hitstop holds the bodies, not the light).</summary>
    const int RimFlash = 2, RimFrames = 8;
    /// <summary>(dev: --aa-norim, the beats without the rim, for an A/B)</summary>
    static readonly bool NoRim = Args.Has("aa-norim");
    /// <summary>A struck body's (flash blend, rim strength) this frame; (-1, 0) when it has none. By night the rim is
    /// held to ~0.6 of the sweep's peak (Flare.Night).</summary>
    /// <summary>Struck by her auto-attacks within the struck look's frames.</summary>
    bool AaStruck(int id) => struckRims.TryGetValue(id, out var at) && Engine.GetFramesDrawn() - at < RimFrames;

    Vector2 StruckRimOn(int id)
    {
        if (!struckRims.TryGetValue(id, out var at)) return new Vector2(-1, 0);
        long age = Engine.GetFramesDrawn() - at;
        if (age < 0 || age >= RimFrames) { if (age >= RimFrames) struckRims.Remove(id); return new Vector2(-1, 0); }
        float flash = age < RimFlash ? (age == 0 ? 0.3f : 0.12f) : 0;
        float k = 1 - age / (float)RimFrames;
        return new Vector2(flash, k * k * (Flare.Night ? 0.55f : 1f));
    }

    /// <summary>The shared hit kit at a struck body (`at`, chest height; `away` the blow's way, flat):
    /// 8-12 steel streaks (0.2-0.4 m, velocity-stretched: Sparks.P.Stretch; white-hot cooling to `spark`,
    /// 0.15-0.25 s) flung on along the blow and `path`; a 4-point contact glint (0.66-0.8 m, 3 frames); a 2-frame
    /// gold-white fresnel rim on the body (`target`, the enemy's id; the crowd's VAT shader draws it). The first
    /// body of an Oathblade swing (or any call with `first`) also gets the impact flash, a light burst for 4 frames:
    /// what the first hit's hitstop holds. `full` false (past the caller's cap, or the frame's hit budget spent)
    /// throws three streaks only. The Disc and Shield Bash pass their own `spark` hue and `path`
    /// (their callers cap their kits).</summary>
    static readonly Color SparkHead = Hdr("#fff2c0", 1.9f), SparkTail = Hdr("#ff8a2a", 1.5f);

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
        // (every struck body: a tight gold rim fading over 8 frames, not the old cream ghost; the frame it was first struck)
        if (target >= 0 && !NoRim && !(struckRims.TryGetValue(target, out var was) && Engine.GetFramesDrawn() - was < RimFrames)) struckRims[target] = Engine.GetFramesDrawn();
        // The sparks (r3): on the full kits only (at most six bodies a swing; the rest of a crowd get the rim), 3-5 each:
        // 12-20 px x 2-3 px at the play camera, white-yellow head to an orange tail, flung on along the blow at 10-15 m/s
        // with drag, 4-6 frames. (They run through the hitstop on the FX's own clock: BattleFx.Update.)
        if (!full) return;
        // (the Oathblade's full kits get the chip puff too; the Disc and Bash throw their own)
        if (path == null) ChipPuff(at, away, 1);
        int n = Math.Min(5, (crit ? 5 : 3 + (int)(R() * 1.99f)) + (first ? 1 : 0));
        if (AaBeats) GD.Print($"[aa-kit] {(path == null ? $"s{oathSwings}" : time == bashAt ? $"b{bashBeat}" : "d")} sparks {n}");
        for (int i = 0; i < n; i++)
        {
            var dir = (away * (0.7f + R() * 0.6f) + along * (0.3f + R() * 0.8f) + new Vector3((R() - 0.5f) * 0.5f, 0.15f + R() * 0.35f, (R() - 0.5f) * 0.5f)).Normalized();
            float speed = 10 + R() * 5, len = 0.32f + R() * 0.16f;
            Sparks.Spawn(new Sparks.P
            {
                At = at + new Vector3((R() - 0.5f) * 0.2f, (R() - 0.5f) * 0.3f, (R() - 0.5f) * 0.2f), V = dir * speed,
                Life = (4 + R() * 2) / 60f, Size = 0.07f, SizeEnd = 0.05f, Color = SparkHead, ColorEnd = SparkTail,
                Gravity = 4, Drag = 5, Alpha = 1, Sprite = -1, Stretch = len / speed,
            });
        }
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

    /// <summary>A chip puff off a struck body (for the Disc and the Bash; r3): 1-2 solid dust puffs, densest at the centre
    /// (Sparks.P.Core, the pack's solid puffs), 18-28 px at the play camera (0.5-0.7 m), alpha 0.5, growing 1.0x to 1.6x
    /// over 10-14 frames, drifting along `away`. Not additive, and lit by hand: a sunlit dust by day, a dark one by night
    /// (the smoke batch is unshaded). Never a cloud of white specks.</summary>
    public void ChipPuff(Vector3 at, Vector3 away, int n = 2)
    {
        n = Math.Clamp(n, 1, 2);
        var dust = Flare.Night ? new Color(0.15f, 0.14f, 0.15f) : new Color(0.4f, 0.32f, 0.23f);
        for (int i = 0; i < n; i++)
        {
            float s = 0.5f + R() * 0.2f;
            Smoke.Spawn(new Sparks.P
            {
                At = at + new Vector3((R() - 0.5f) * 0.2f, -0.2f + (R() - 0.5f) * 0.2f, (R() - 0.5f) * 0.2f),
                V = away * (0.6f + R() * 0.6f) + Vector3.Up * (0.2f + R() * 0.2f), Drag = 3,
                Life = (10 + R() * 4) / 60f, Size = s, SizeEnd = s * 1.6f, Color = dust, ColorEnd = dust * 0.92f,
                Alpha = 0.5f, Sprite = SolidPuff(), Core = true, Spin = R() * Mathf.Tau,
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
        walls = Add(new Batch(WallMesh(), 8, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/bash_wall.gdshader") }));
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

    // (each disc's last drawn place and side, for its twin rails)
    readonly System.Collections.Generic.Dictionary<long, Vector3> discLast = new(), discSide = new();
    static float half2(float s) => 0.62f * s / 1.1f;

    /// <summary>The disc's radius (metres, before its throw's scale).</summary>
    const float DiscRad = 0.26f;

    void DiscsBegin() { discLit = 0; discGlowN = 0; discs.Begin(); }

    void DiscsEnd()
    {
        discs.End();
        if (discLast.Count > 64) { discLast.Clear(); discSide.Clear(); }
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
        // (r3: ~38 degrees a frame, under the 3 glint arcs' strobing rates)
        float spin = (float)(now * 40 + p.Id);
        // Leaving her hand it is held down, so it never blooms over her.
        float near = new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length();
        float off = Mathf.Lerp(0.35f, 1, Mathf.SmoothStep(0.8f, 3f, near));
        if (AaBeats && discThrows >= 1 && !discFlyShot && near > 1.8f && near < 6f) { discFlyShot = true; Shots.WantFrames("d_fly", 1); GD.Print($"[aa-beats] disc in flight t={time:F2}"); }
        if (AaBeats && discBounceShot && !discOpenShot && near > 2.5f && near < 9f && b0 != null && Clear(p.X, p.Z, Flare.Night ? 1.8 : 1.2)) { discOpenShot = true; Shots.WantFrames("d_open", 1); GD.Print($"[aa-beats] disc over open ground t={time:F2}"); }
        // A faint dark bed under it (so the head shows over the pale dead), and the head.
        Shade(at, 1.0f * s, 0.3f);
        discs.Add(new Transform3D(new Godot.Basis(Vector3.Up, -spin).Scaled(Vector3.One * s), at), hue * off);
        // Its wake (r3): twin rails off the disc's two edges (~0.68 m apart, 36-40 px at the play camera) with a faint fill
        // between them, in world space (a bounce leaves a V for ~0.1 s), tapering and fading over 0.16 s. Never one
        // stick behind a ball.
        var wake = art == "disc_aegis" ? Hdr("#bcd4ff", 1f) : Hdr("#ffb040", 1f);
        var side = Vector3.Zero;
        if (discLast.TryGetValue(key, out var was) && (at - was).LengthSquared() > 1e-5f) { var mv = (at - was).Normalized(); side = new Vector3(-mv.Z, 0, mv.X); }
        else if (discSide.TryGetValue(key, out var ws)) side = ws;
        discLast[key] = at;
        if (side != Vector3.Zero)
        {
            discSide[key] = side;
            float half = 0.34f * s / 1.1f;
            Ribbons.Feed(key * 4 + 1, at + side * half, 0.065f, 0.1f, wake, 1.7f * off, Ribbons.Style.Glow);
            Ribbons.Feed(key * 4 + 2, at - side * half, 0.065f, 0.1f, wake, 1.7f * off, Ribbons.Style.Glow);
        }
        Ribbons.Feed(key, at, half2(s), 0.12f, wake, 0.35f * off, Ribbons.Style.Glow);
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
        // The contact (r3): a 2-frame amber flare ~1.5x the halo on every hit, at the disc's side of the body.
        Sparks.Spawn(new Sparks.P
        {
            At = at - away * 0.3f, Life = 2 / 60f, Size = 1.1f, SizeEnd = 0.95f, Color = Hdr("#ffb448", 1.1f), ColorEnd = Hdr("#ff8a28", 0.6f),
            Alpha = 1, Sprite = Sprites.Range("light").First + 1 + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f,
        });
        if (rich) ChipPuff(at, away, R() < 0.5f ? 1 : 2);
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
    /// from the shield's face (0.5 m), its weight forward (100% on her facing line, ~50% at +-35 degrees, under 15% at
    /// the sides), its front out over 4 frames on the frame's own clock (a hitstop holds the bodies, never the shove)
    /// with a standing face 0.4 m tall (bash_wall.gdshader); a bronze flash at the shield on f0-f2; a brown dust
    /// plow laid at the front across +-40 degrees, drifting on (StepWedges). The struck get the hit kit (BashStruck) and a stun glint;
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
            liveWedges.Add(new Wedge { At = her + Vector3.Up * 0.06f, Angle = ang, Reach = reach, Night = Flare.Night });
            // The shove (r3): a bronze flash 0.6-0.8 m wide at the shield's face, ~0.5 m in front of her, on f0-f2.
            var face = her + dir * 0.5f + Vector3.Up * 0.55f;
            Sparks.Spawn(new Sparks.P
            {
                At = face, Life = 3 / 60f, Size = 0.75f, SizeEnd = 0.65f, Color = BashBronze * (Flare.Night ? 0.75f : 1f), ColorEnd = BashBronze * 0.3f,
                Alpha = 1, Sprite = Sprites.Range("light").First + 1 + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f,
            });
            Flash(face + dir * 0.4f - Vector3.Up * 0.2f, new Color("#ffc878"), 6, 0.16f, 5);
        }
    }

    /// <summary>The plow's dust puffs laid at the front each frame it runs (r3: a band travelling with it across +-40 degrees).</summary>
    const int BashPlow = 6;

    /// <summary>The wedge's life, on the frame's own clock (seconds: 6 frames, its front out by the 4th).</summary>
    const float WedgeLife = 6 / 60f;
    /// <summary>The wedge's mesh starts at the shield's face (metres from her, of the sim's 3.4 m reach).</summary>
    const float WedgeInner = 0.5f;
    /// <summary>Where the wedge's front is (UV share from the shield to the reach) at `p` of its life: bash_wedge.gdshader's.</summary>
    static float WedgeFront(float p) => Mathf.Lerp(0.04f, 1.08f, 1 - Mathf.Pow(1 - Mathf.Min(p, 1), 2.2f));
    struct Wedge { public Vector3 At; public float Angle, Reach, Age; public bool Night; }
    Batch walls = null!;
    readonly System.Collections.Generic.List<Wedge> liveWedges = new();
    Batch wedges = null!;

    /// <summary>The wedge's mesh: the sim's +-1.2 rad sector from the shield (0.65 m, of a unit reach) to the reach, flat;
    /// UV.x out along it, UV.y across it (-1..1).</summary>
    static ArrayMesh WedgeMesh()
    {
        const int Na = 40, Nr = 16;
        const float Inner = WedgeInner / 3.4f, Half = 1.2f;
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

    /// <summary>The wave front's standing face (r3): a vertical strip on the arc, unit radius and height, +-1.2 rad;
    /// UV.x across it (-1..1, the angle), UV.y up it (shaders/bash_wall.gdshader).</summary>
    static ArrayMesh WallMesh()
    {
        const int Na = 48;
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        void P(int i, int j)
        {
            float v = i / (float)Na * 2 - 1, a = v * 1.2f;
            st.SetNormal(new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a))); st.SetUV(new Vector2(v, j)); st.AddVertex(new Vector3(Mathf.Cos(a), j, Mathf.Sin(a)));
        }
        for (int i = 0; i < Na; i++) { P(i, 0); P(i + 1, 0); P(i + 1, 1); P(i, 0); P(i + 1, 1); P(i, 1); }
        return st.Commit();
    }

    void StepWedges()
    {
        wedges.Begin();
        walls.Begin();
        float dt = frameDt > 0 ? (float)GetProcessDeltaTime() : 0;
        for (int i = liveWedges.Count - 1; i >= 0; i--)
        {
            var w = liveWedges[i];
            if (w.Age >= WedgeLife) { liveWedges.RemoveAt(i); continue; }
            float p = w.Age / WedgeLife;
            // (its strength in the colour: lower by night, so the rim never clips to white)
            float k = w.Night ? 0.62f : 1f;
            wedges.Add(new Transform3D(new Godot.Basis(Vector3.Up, -w.Angle).Scaled(Vector3.One * w.Reach), w.At), new Color(k, k, k, p));
            // The front's standing face, 0.4 m tall, riding the front out.
            float fr = Mathf.Lerp(WedgeInner, w.Reach, Mathf.Min(1, WedgeFront(p)));
            walls.Add(new Transform3D(new Godot.Basis(Vector3.Up, -w.Angle).Scaled(new Vector3(fr, 0.42f, fr)), w.At), new Color(k, k, k, p));
            // The plow: brown dust laid at the front as it runs, across +-40 degrees, drifting on (12-20 frames).
            if (dt > 0 && p < 0.75f)
            {
                var dust = w.Night ? new Color(0.13f, 0.12f, 0.12f) : new Color(0.36f, 0.28f, 0.19f);
                for (int j = 0; j < BashPlow; j++)
                {
                    float a = w.Angle + (R() + R() - 1) * 0.7f;
                    var u = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    float d = fr * (0.92f + R() * 0.12f), sz = 0.42f + R() * 0.14f;
                    double x = w.At.X + u.X * d, z = w.At.Z + u.Z * d;
                    Smoke.Spawn(new Sparks.P
                    {
                        At = V(x, Y(x, z) + 0.22 + R() * 0.08, z), V = u * (1.4f + R() * 1.2f) + Vector3.Up * (0.1f + R() * 0.2f), Drag = 2.5f,
                        Life = (12 + R() * 8) / 60f, Size = sz, SizeEnd = sz * 1.5f, Color = dust, ColorEnd = dust * 0.9f,
                        Alpha = 0.4f + R() * 0.2f, Sprite = SolidPuff(), Core = true, Spin = R() * Mathf.Tau,
                    });
                }
            }
            w.Age += dt;
            liveWedges[i] = w;
        }
        wedges.End();
        walls.End();
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
        bool full = bashKits < 6 && hitBudget-- > 0;
        HitKit(at, away, BashSpark, 1, e.Crit, full, away, e.Target, first: bashKits == 0);
        if (full) ChipPuff(at, away, 1);
        bashKits++;
        stunned[e.Target] = time + 1.5;
        if (AaBeats && bashBeat == 1 && throwLog.Count < 3 && b0 != null && b0.Enemies.Items[e.Target] is { } en)
        {
            var (x, z) = CrowdView.Placed?.Invoke(en) ?? Drawn?.Of(en) ?? (en.X, en.Z);
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
            var (x, z) = CrowdView.Placed?.Invoke(en) ?? Drawn?.Of(en) ?? (en.X, en.Z);
            double dx = x - x0, dz = z - z0, simd = Math.Sqrt((en.X - x0) * (en.X - x0) + (en.Z - z0) * (en.Z - z0));
            GD.Print($"[aa-throw] id={id} f={n} t={time - t0:F3} drawn={Math.Sqrt(dx * dx + dz * dz):F2} sim={simd:F2} alive={en.Alive} state={en.State} kb=({en.Kbx:F2},{en.Kbz:F2}) mass={en.Mass:F1}");
            throwLog[i] = (id, x0, z0, t0, time - t0 > 0.35 ? -1 : n + 1);
        }
    }

    /// <summary>The stun glint's size (metres).</summary>
    const float StunGlint = 0.3f;
    static readonly Color StunGold = Hdr("#ffb84a", 1.5f);

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
            // (r3) A twinkle: 0.6x to 1.0x and back over ~0.4 s, each on its own phase; gold, clear of the skull (2.2 m up).
            float tw = 0.6f + 0.4f * Mathf.Pow(Mathf.Sin(((float)time / 0.4f + id * 0.37f) * Mathf.Pi), 2);
            var (gx, gz) = CrowdView.Placed?.Invoke(en) ?? Drawn?.Of(en) ?? (en.X, en.Z);
            var over = V(gx, Y(gx, gz) + 2.2, gz) + new Vector3(Mathf.Cos(ph), 0, Mathf.Sin(ph)) * 0.18f;
            Sparks.Spawn(new Sparks.P
            {
                At = over, Life = frameDt * 1.5f, Size = StunGlint * tw, SizeEnd = StunGlint * tw, Color = StunGold * (0.6f + 0.4f * tw), ColorEnd = StunGold * (0.6f + 0.4f * tw),
                Alpha = 1, Sprite = Star4, Spin = 0.001f, SpinV = 0.001f,
            });
        }
        if (gone != null) foreach (var id in gone) stunned.Remove(id);
    }

    /* --------------------------------------------------------- the beats -- */

    int discThrows, bashBeat;
    bool discBeat, discHitShot, discBounceShot, discFlyShot, discOpenShot;

    // (dev: no living body within `r` metres of (x, z))
    bool Clear(double x, double z, double r)
    {
        foreach (var en in b0!.Enemies.Items)
            if (en != null && en.Alive && (en.X - x) * (en.X - x) + (en.Z - z) * (en.Z - z) < r * r) return false;
        return true;
    }

    /// <summary>The Disc's beats: her 1st throw in flight (1.8-6 m out, while the crowd is still off her), then that throw's
    /// first hit and its first bounce (the next frame after each, as the player sees them land).</summary>
    void BeatDiscThrow()
    {
        if (!AaBeats) return;
        discThrows++;
        if (discThrows == 1) { discBeat = true; }
        GD.Print($"[aa-beats] disc {discThrows} t={time:F2}");
    }

    void BeatDiscHit(int n)
    {
        if (!AaBeats || !discBeat || b0 == null) return;
        if (n == 1 && !discHitShot) { discHitShot = true; Shots.WantFrames("d_hit", 1); GD.Print($"[aa-beats] disc hit t={time:F2}"); }
        else if (n == 2 && discHitShot && !discBounceShot) { discBounceShot = true; Shots.WantFrames("d_bounce", 1); Shots.WantFrames("d_bounce3", 4); GD.Print($"[aa-beats] disc bounce t={time:F2}"); }
    }

    /// <summary>The Bash's beats: its first two, at +1 and +3 drawn frames.</summary>
    void BeatBash()
    {
        if (!AaBeats) return;
        bashBeat++;
        if (bashBeat <= 2) { Shots.WantFrames($"b{bashBeat}_f1", 1); Shots.WantFrames($"b{bashBeat}_f3", 3); }
        if (bashBeat == 1) { Shots.WantFrames("b1_f6", 6); Shots.WantFrames("b1_f10", 10); }
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
            if (oathSwings == 5) { Shots.WantFrames("s5_f4", 4); Shots.WantFrames("s5_f8", 8); }
            beatHitFor = oathSwings;
            sweepLogFrom = Engine.GetFramesDrawn(); sweepAge = 0;
        }
        else beatHitFor = 0;
        if (oathSwings == 4) Shots.Want("mid", 0.5);
        GD.Print($"[aa-beats] swing {oathSwings} t={time:F2} angle={e.Angle:F2} arc={e.Arc:F2} reach={e.Reach:F2}");
    }

    // (dev, --aa-beats: the sweep's timeline on swings 3, 5 and 7, a line a drawn frame for 10 frames)
    long sweepLogFrom = -100;
    float sweepAge;
    void LogSweep(float dt, bool stopped)
    {
        long f = Engine.GetFramesDrawn() - sweepLogFrom;
        if (!AaBeats || f < 0 || f > 10) return;
        sweepAge += dt;
        float hd = Mathf.Min(1, sweepAge / OathReveal), er = Mathf.Clamp((sweepAge - OathReveal) / OathErode, 0, 1);
        GD.Print($"[aa-sweep] s{oathSwings} f{f} frame {Engine.GetFramesDrawn()} age {sweepAge * 60:F1}/60 head {1 - (1 - hd) * (1 - hd):F2} erode {er:F2} hitstop {(stopped ? 1 : 0)} fight-dt {frameDt * 60:F2}/60");
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

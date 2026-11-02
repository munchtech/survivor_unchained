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
    /// the blow it lands (the blade meeting the body, not the swing's first frame). Her auto-attacks' arts only:
    /// the Disc and Shield Bash add theirs here.</summary>
    public static (double Len, double Delay) FirstHitStop(Ev.Hit h) =>
        h.Dot || h.ByFlare || h.Blocked ? (0, 0) : IsOath(h.Art) ? (0.042, 0.03) : (0, 0);

    /* ------------------------------------------------------- the sweep -- */

    // Her Oathblade's gold, its evolutions' hues (linear, near 1 so the tone curve keeps them a colour;
    // the white-hot edge is the shader's), and the sparks off what they strike.
    static readonly Color OathSteel = Hdr("#ffb83a", 1.15f), OathHoly = Hdr("#ffd772", 1.2f), OathBlood = Hdr("#ff2a1a", 1.15f);
    static Color OathHue(string art) => art switch { "slash_holy" => OathHoly, "slash_blood" => OathBlood, _ => OathSteel };
    static Color OathSpark(string art) => art == "slash_blood" ? Blood : art == "slash_holy" ? OathGold : Ember;

    // The swing in flight (for the struck's sparks: flung on along the blade's path), and how many full kits it has thrown.
    Vector3 oathAt;
    bool oathMirror;
    int oathKits;
    /// <summary>Full kits (sparks and contact) per swing; the rest of a crowd struck get two sparks.</summary>
    const int OathKits = 6;

    /// <summary>The Oathblade's sweep: ONE gold crescent leaving her blade, its leading edge white-hot, light only
    /// (it lights the ground, never darkens it), gone in 6 frames; a faint gold pool on the ground under it for 3.</summary>
    void OathSweep(Ev.Slash e, Vector3 at, float facing, float reach, float g)
    {
        string art = e.Art ?? "";
        float rich = Mathf.Min(g, 1.35f);
        oathAt = at; oathMirror = mirror; oathKits = 0;
        var hue = OathHue(art);
        OathBlades.Add(at, facing, reach, (float)e.Arc * 1.1f, mirror, 0.055f, 0.045f, hue * (0.9f + 0.1f * g), 0.4f * rich);
        // The pool: under the middle of the arc, warm and faint, the decal's box shallow so it lights the ground only.
        var mid = new Vector3(Mathf.Cos((float)e.Angle), 0, Mathf.Sin((float)e.Angle)) * reach * 0.55f;
        var m = Ground(e.X + mid.X, e.Z + mid.Z, reach * 0.55f, glowTex!, hue with { A = 1 }, 0.05f, 0.9f);
        m.Decal.Size = new Vector3(reach * 1.1f, 0.6f, reach * 1.1f);
        // The Watch's oath along the edge of a ranked Oathblade: a few gold glints that hang.
        if (e.Rank >= 5 && art != "slash_blood")
            for (int i = 0; i < 4; i++)
            {
                float a = (float)e.Angle + (float)e.Arc * (R() - 0.5f);
                var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                Sparks.Spawn(at + rim * reach * 0.95f, Vector3.Up * 0.4f, 0.5f, 0.12f, OathGold, OathGold * 0.3f, 0.02f, 0, 2, sprite: Sprites.Of("star"), spinV: 3);
            }
    }

    /// <summary>The shared hit kit at a struck body (`at`, chest height; `away` the blow's way, flat):
    /// steel sparks white-hot cooling to `spark`, flung on along the blow and the blade's path, and a
    /// 3-frame contact star. `full` false (past the swing's cap, or the frame's hit budget spent) throws
    /// two sparks only. The rim is the crowd's own struck flash; the hitstop is FirstHitStop's.
    /// The Disc and Shield Bash call this with their own `spark` hue.</summary>
    public void HitKit(Vector3 at, Vector3 away, Color spark, float g, bool crit, bool full = true, Vector3? path = null)
    {
        Vector3 along;
        // The Disc and the Bash give their own path (their caller caps their kits); the Oathblade's
        // is along the blade's path at this body (the swing's tangent there), so sparks fly on with the cut.
        if (path is { } own) along = own;
        else
        {
            full = full && oathKits++ < OathKits;
            var rim = at - oathAt; rim.Y = 0;
            along = rim.LengthSquared() > 0.01f ? new Vector3(-rim.Z, 0, rim.X).Normalized() * (oathMirror ? -1 : 1) : Vector3.Zero;
        }
        int n = full ? (crit ? 9 : 6) : 2;
        for (int i = 0; i < n; i++)
        {
            var v = away * (3 + R() * 4) + along * (3 + R() * 4) + new Vector3((R() - 0.5f) * 3, 1.2f + R() * 2.5f, (R() - 0.5f) * 3);
            Sparks.Spawn(at + Vector3.Up * (R() - 0.5f) * 0.3f, v, 0.14f + R() * 0.12f, 0.035f + R() * 0.02f, SteelWhite, spark, 0.008f, 9, 2.5f);
        }
        if (full) Sparks.Spawn(at, Vector3.Zero, 0.05f, (crit ? 0.4f : 0.24f) * g, SteelWhite * 0.5f, SteelWhite * 0.1f, 0.12f, sprite: Sprites.Of("flare"), spinV: 0);
    }

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
        for (int i = 0; i < DiscLights; i++)
        {
            discLamps[i] = new OmniLight3D { LightEnergy = 0, OmniRange = 2.6f, OmniAttenuation = 1.3f, ShadowEnabled = false, Visible = false };
            AddChild(discLamps[i]);
        }
    }

    /// <summary>The disc's head, flat in the ground's plane round the origin, 0.3 m in radius:
    /// UV.x 0 at the centre to 1 at the rim, UV.y the angle round it (shaders/disc.gdshader).</summary>
    static ArrayMesh DiscMesh()
    {
        const int N = 48, Rings = 4;
        const float Rad = 0.26f, Thick = 0.012f;
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

    void DiscsBegin() { discLit = 0; discGlowN = 0; discs.Begin(); }

    void DiscsEnd()
    {
        discs.End();
        for (int i = discLit; i < DiscLights; i++) { discLamps[i].Visible = false; discLamps[i].LightEnergy = 0; }
        for (int i = discGlowN; i < discGlows.Count; i++) discGlows[i].Visible = false;
    }

    /// <summary>The Judgement Disc in flight: a small spinning white-gold head with a dark steel rim
    /// (a head the eye can track), a short warm trail, and a pool of its light on the ground under it.</summary>
    bool DiscFlight(Projectile p, Vector3 at, double now, float g, long key)
    {
        string art = p.Art;
        float s = 1.1f * Mathf.Sqrt(g) * (art == "disc_reckon" ? 1.15f : 1);
        var hue = DiscHue(art);
        float spin = (float)(now * 16 + p.Id);
        // Leaving her hand it is held down, so it never blooms over her.
        float near = new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length();
        float off = Mathf.Lerp(0.35f, 1, Mathf.SmoothStep(0.8f, 3f, near));
        // A dark soft bed under it (so the head shows over the pale dead), the head, a small hot heart.
        if (AaBeats && discThrows >= 2 && !discFlyShot && near > 1.8f && near < 6f) { discFlyShot = true; Shots.WantFrames("d_fly", 1); GD.Print($"[aa-beats] disc in flight t={time:F2}"); }
        Shade(at, 1.05f * s, 0.5f);
        discs.Add(new Transform3D(new Godot.Basis(Vector3.Up, -spin).Scaled(Vector3.One * s), at), hue * off);
        orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.26f * s), at + Vector3.Up * 0.03f), Hdr("#fff2d0", 1.3f) * off);
        // Its turn: two thin arcs whipping round just outside the rim, as the eye sees a blade spin.
        SpinArcs(at, 0.31f * s, spin * 1.6f, 0.05f * s, art == "disc_aegis" ? Hdr("#e8f2ff", 1f) : Hdr("#fff0c8", 1f), 2.2f * off);
        // Its wake: short and warm, so a thrown disc never reads as a beam.
        Ribbons.Feed(key, at, 0.26f * s, 0.11f, art == "disc_aegis" ? Hdr("#bcd4ff", 1f) : Hdr("#ffb040", 1f), 1.4f, Ribbons.Style.Glow);
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
            l.Position = ground + Vector3.Up * 0.75f;
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

    /// <summary>A body the disc strikes: a 4-point glint, the shared kit's sparks flung along the disc's
    /// own way, and a dark chip puff. No hitstop: it bounces through five bodies every 2.2 s, and a hold
    /// on its first hit stuttered under the Oathblade's own.</summary>
    void DiscStruck(Ev.Hit e, Vector3 at, Vector3 away, float g, bool rich)
    {
        string art = e.Art ?? "";
        BeatDiscHit(e);
        var hue = DiscHue(art);
        Sparks.Spawn(new Sparks.P
        {
            At = at, Life = 0.1f, Size = (e.Crit ? 0.8f : 0.6f) * g, SizeEnd = 0.3f * g, Color = Hdr("#fff6e0", 1.6f), ColorEnd = hue * 0.3f,
            Alpha = 1, Sprite = Star4, Spin = 0.001f, SpinV = 0.001f,
        });
        HitKit(at, away, DiscSpark(art), g, e.Crit, rich, Vector3.Zero);
        if (!rich) return;
        // The chip: a puff of dark grit off the body and a few dark flecks thrown on with the disc.
        Smoke.Spawn(at, away * 1.2f + Vector3.Up * 0.4f, 0.4f, 0.22f, new Color(0.05f, 0.045f, 0.04f), new Color(0.08f, 0.07f, 0.06f), 0.55f, 0, 3, 0.55f);
        for (int i = 0; i < 3; i++)
            Smoke.Spawn(at, away * (2 + R() * 2) + new Vector3((R() - 0.5f) * 1.5f, 1 + R() * 1.5f, (R() - 0.5f) * 1.5f), 0.4f, 0.045f, new Color(0.04f, 0.035f, 0.03f), null, 0.04f, 9, 0.5f, 0.9f);
    }

    /* ----------------------------------------------------- the shield bash -- */

    // Bronze-gold, dented: the shield's face catching the blow (near 1, a colour, never a white ring).
    static readonly Color BashBronze = Hdr("#e0a048", 1.25f), BashSpark = Hdr("#ffbe5a", 2.2f);
    double bashAt = -1;
    Vector3 bashFrom;
    int bashKits;
    readonly System.Collections.Generic.Dictionary<int, double> stunned = new();

    /// <summary>Shield Bash: a short heavy shove of the shield's face. A dented bronze-gold flash in
    /// front of her (not a ring round her), a low dust kick across the 2.5 m cone; the struck get the
    /// hit kit (BashStruck) and a small stun glint; the hitstop is WorldScene's (3 frames).</summary>
    void ShieldBash(Ev.Ability e)
    {
        float gy = Y(e.X, e.Z);
        var her = V(e.X, gy, e.Z);
        bashAt = time; bashFrom = her; bashKits = 0;
        BeatBash();
        int sides = e.Wide ? 2 : 1;
        for (int k = 0; k < sides; k++)
        {
            float ang = (float)e.Angle + k * Mathf.Pi;
            var dir = new Vector3(Mathf.Cos(ang), 0, Mathf.Sin(ang));
            var face = her + dir * 1.35f + Vector3.Up * 0.8f;
            // The shield's face: a squat bronze flash, a white-gold glint off its dented boss, gone in 6 frames.
            Sparks.Spawn(new Sparks.P { At = face, V = dir * 1.2f, Life = 0.1f, Size = 0.95f, SizeEnd = 1.4f, Color = BashBronze, ColorEnd = BashBronze * 0.12f, Alpha = 1, Sprite = Sprites.Range("light").First + 1 + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f });
            Sparks.Spawn(new Sparks.P
            {
                At = face + Vector3.Up * 0.12f - dir * 0.05f, Life = 0.06f, Size = 0.55f, SizeEnd = 0.3f, Color = Hdr("#fff2d8", 1.5f), ColorEnd = BashBronze * 0.3f,
                Alpha = 1, Sprite = Star4, Spin = 0.38f, SpinV = 0.001f,
            });
            // Bronze flecks off its rim, flung forward.
            for (int i = 0; i < 7; i++)
            {
                float a = ang + (R() - 0.5f) * 1.2f;
                var v = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * (4 + R() * 4) + Vector3.Up * (0.5f + R() * 1.5f);
                Sparks.Spawn(face, v, 0.12f + R() * 0.1f, 0.03f, SteelWhite * 0.8f, BashBronze, 0.008f, 9, 2.5f);
            }
            Flash(face, new Color("#ffc878"), 6, 0.16f, 5);
            // The dust kicked low across the cone, its front running out to 2.5 m.
            for (int i = 0; i < 18; i++)
            {
                float a = ang + (R() - 0.5f) * 1.5f, d = 0.5f + R() * 2.0f;
                var u = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                double x = e.X + u.X * d, z = e.Z + u.Z * d;
                Smoke.Spawn(V(x, Y(x, z) + 0.12, z), u * (1.5f + R() * 2.5f) + Vector3.Up * (0.15f + R() * 0.4f), 0.55f + R() * 0.3f, 0.4f + R() * 0.25f,
                    new Color(0.34f, 0.3f, 0.25f), new Color(0.2f, 0.18f, 0.15f), 1.2f, 0, 3, 0.55f);
            }
        }
    }

    /// <summary>A blow of the Bash (its hits carry no art: they land in the same step as its event, within its reach):
    /// the hit kit thrown back from her, and the body marked for its stun glint. False for any other blow.</summary>
    bool BashStruck(Ev.Hit e, Vector3 at)
    {
        if (time != bashAt || e.Art != null || e.Dot) return false;
        var away = at - bashFrom; away.Y = 0;
        if (away.LengthSquared() > 3.7f * 3.7f) return false;
        away = away.LengthSquared() > 0.01f ? away.Normalized() : Vector3.Forward;
        HitKit(at, away, BashSpark, 1, e.Crit, bashKits++ < 8 && hitBudget-- > 0, Vector3.Zero);
        stunned[e.Target] = time + 1.5;
        return true;
    }

    /// <summary>The stunned: a small dim gold 4-point glint circling over each for its stun, each twinkling
    /// on its own phase (a crowd of them all lit at once read as a field of icons).</summary>
    void StunGlints(Battle b)
    {
        if (stunned.Count == 0 || frameDt <= 0) return;
        System.Collections.Generic.List<int>? gone = null;
        foreach (var (id, until) in stunned)
        {
            var en = id >= 0 && id < b.Enemies.Capacity ? b.Enemies.Items[id] : null;
            if (en == null || !en.Alive || time > until || !en.Status.Has(StatusKind.Stun)) { (gone ??= new()).Add(id); continue; }
            float ph = (float)time * 5 + id * 2.3f;
            float tw = 0.3f + 0.7f * Mathf.Pow(Mathf.Max(0, Mathf.Sin(ph * 1.6f)), 2);
            var over = V(en.X, Y(en.X, en.Z) + 2.05, en.Z) + new Vector3(Mathf.Cos(ph), 0, Mathf.Sin(ph)) * 0.2f;
            Sparks.Spawn(new Sparks.P
            {
                At = over, Life = frameDt * 1.5f, Size = 0.24f, SizeEnd = 0.24f, Color = OathGold * (0.7f * tw), ColorEnd = OathGold * (0.7f * tw),
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

    void BeatDiscHit(Ev.Hit e)
    {
        if (!AaBeats || !discBeat || b0 == null) return;
        int n = 0;
        foreach (var p in b0.Projectiles.Living())
            if (IsDisc(p.Art) && p.Hits.Count > 0 && p.Hits[^1] == e.Target) { n = p.Hits.Count; break; }
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

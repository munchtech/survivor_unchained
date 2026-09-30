using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.View;

/// <summary>
/// The fight made visible (the web game's fx/combatFx.ts). The simulation
/// says what happened; this decides what it looks like, in the colour of
/// its school and scaled by how much it matters: a tick of poison is a
/// whisper, a critical a shower of sparks and a gold number, an elite's
/// death a burst of light on the ground round it, a charge a lane on the
/// floor to read the timing off. Also draws what is in the air and what
/// lies on the ground to be taken. Lights are few: a pool of them goes to
/// the brightest recent moments and fades.
/// </summary>
public partial class BattleFx : Node3D
{
    readonly Func<double, double, double> heightAt;
    public readonly Sparks Sparks = new(6000, true), Smoke = new(2500, false);
    public readonly Hits Hits = new();
    /// <summary>Blood, pools and what a burst body throws (its Level: the settings' gore).</summary>
    public readonly Gore Gore;
    public FollowCamera? Cam;
    /// <summary>A blow landed on the survivor: how hard (0..1), for the edges of the picture.</summary>
    public Action<float> OnDamageFlash = _ => { };
    public Vector3 PlayerPos;
    double time;

    readonly List<(OmniLight3D Light, float T, float Life, float Peak)> flashes = new();
    readonly List<Mark> marks = new();
    readonly Dictionary<int, Mark> keyed = new();
    readonly Dictionary<int, Mark> zoneMarks = new();
    readonly List<(MeshInstance3D Mesh, ShaderMaterial Mat, float T, float Life)> beams = new();
    readonly List<(double At, Action Fn)> pending = new();
    int nextBeam;
    bool mirror;

    // What is in the air, and what lies on the ground.
    Batch orbs = null!, steel = null!, shards = null!, rings = null!, embers = null!, coins = null!, flasks = null!, lodestones = null!, sacks = null!, chests = null!, kegs = null!, lootBeams = null!;
    /// <summary>How far above the ground the middle of a sack and a chest sits.</summary>
    float sackUp, chestUp;
    readonly Dictionary<int, float> trailAcc = new();

    static Texture2D? ringTex, discTex, laneTex;

    sealed class Mark
    {
        public required Decal Decal;
        public float T, Life, Radius;
        public bool Progress, Grow, Active;
        public Color Color;
        public Decal? Fill;
    }

    public BattleFx(Func<double, double, double> heightAt)
    {
        this.heightAt = heightAt;
        Name = "BattleFx";
        Gore = new Gore(heightAt, Smoke, Hits);
    }

    public override void _Ready()
    {
        AddChild(Sparks);
        AddChild(Smoke);
        AddChild(Hits);
        AddChild(Gore);
        for (int i = 0; i < 8; i++)
        {
            var l = new OmniLight3D { LightEnergy = 0, OmniRange = 10, OmniAttenuation = 1.6f, ShadowEnabled = false, Visible = false };
            AddChild(l);
            flashes.Add((l, 1, 1, 0));
        }
        ringTex ??= GroundTexture(0);
        discTex ??= GroundTexture(1);
        laneTex ??= GroundTexture(2);
        var beamShader = GD.Load<Shader>("res://shaders/beam.gdshader");
        for (int i = 0; i < 20; i++)
        {
            var mat = new ShaderMaterial { Shader = beamShader };
            var m = new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 1, BottomRadius = 1, Height = 1, RadialSegments = 16, CapTop = false, CapBottom = false }, MaterialOverride = mat, Visible = false, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(m);
            beams.Add((m, mat, 1, 1));
        }
        var spark = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/spark.gdshader") };
        Material Glowing(float emit, float rough = 0.35f, float metal = 0)
        {
            var m = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/glowing.gdshader") };
            m.SetShaderParameter("emit", emit);
            m.SetShaderParameter("roughness", rough);
            m.SetShaderParameter("metallic", metal);
            return m;
        }
        var beam = new ShaderMaterial { Shader = beamShader };
        beam.SetShaderParameter("energy", 1.6f);
        orbs = Add(new Batch(new QuadMesh { Size = Vector2.One }, 1400, spark));
        steel = Add(new Batch(new BoxMesh { Size = new Vector3(0.06f, 0.04f, 0.6f) }, 600, Glowing(0.25f, 0.3f, 0.7f)));
        shards = Add(new Batch(new PrismMesh { Size = new Vector3(0.14f, 0.7f, 0.14f) }, 600, Glowing(1.8f, 0.1f)));
        rings = Add(new Batch(new TorusMesh { InnerRadius = 0.36f, OuterRadius = 0.5f, Rings = 16, RingSegments = 6 }, 200, Glowing(1.2f, 0.2f, 0.8f)));
        // What lies on the ground is what the pack shows (the photographs'
        // models): an ember is the ember's crystals, lit the colour of its
        // worth; a draught, a lodestone, a sack of what was carried, a chest.
        embers = Add(new Batch(Pickup("ember", 1.25f, m => m is BaseMaterial3D { EmissionEnabled: true }), 1400, Glowing(2.6f, 0.25f)));
        var coin = new Build();
        Lathe(coin, Pts(0, -0.012f, 0.12f, -0.012f, 0.15f, -0.02f, 0.16f, -0.012f, 0.16f, 0.012f, 0.15f, 0.02f, 0.12f, 0.012f, 0, 0.012f), 16);
        coins = Add(new Batch(coin.Mesh(), 600, Glowing(0.6f, 0.3f, 0.9f)));
        flasks = Add(new Batch(Pickup("potion", 0.36f), 200, null));
        lodestones = Add(new Batch(Pickup("sigil", 0.42f), 60, null));
        var sack = Pickup("seed", 0.38f);
        sackUp = sack.GetAabb().Size.Y / 2;
        sacks = Add(new Batch(sack, 200, null, true));
        var chest = Pickup("chest", 0.55f);
        chestUp = chest.GetAabb().Size.Y / 2;
        chests = Add(new Batch(chest, 60, null, true));
        // A sapper's firepot: a keg of powder, thrown.
        kegs = Add(new Batch(Pickup("bomb", 0.34f), 60, null));
        lootBeams = Add(new Batch(new CylinderMesh { TopRadius = 0.12f, BottomRadius = 0.18f, Height = 1, RadialSegments = 10, CapTop = false, CapBottom = false }, 200, beam));
    }

    Batch Add(Batch b) { AddChild(b); return b; }

    /// <summary>An item's own model (the photographs', Ui/ItemModels) as one
    /// mesh to draw many of: its parts merged, each keeping its material (or
    /// only the parts whose material `keep` wants), centred, `size` across at
    /// its largest.</summary>
    static Mesh Pickup(string key, float size, Func<Material, bool>? keep = null)
    {
        var model = ItemModels.Make(key)?.Model;
        if (model == null) return new SphereMesh { Radius = size / 2, Height = size };
        var parts = new List<(Mesh Mesh, int Surface, Transform3D At, Material? Mat)>();
        void Walk(Node n, Transform3D at)
        {
            foreach (var c in n.GetChildren())
            {
                var t = c is Node3D n3 ? at * n3.Transform : at;
                if (c is MeshInstance3D { Mesh: { } mesh } mi)
                    for (int s = 0; s < mesh.GetSurfaceCount(); s++)
                    {
                        var mat = mi.GetSurfaceOverrideMaterial(s) ?? mi.MaterialOverride ?? mesh.SurfaceGetMaterial(s);
                        if (keep == null || (mat != null && keep(mat))) parts.Add((mesh, s, t, mat));
                    }
                Walk(c, t);
            }
        }
        Walk(model, Transform3D.Identity);
        Aabb? box = null;
        foreach (var p in parts) { var b = p.At * p.Mesh.GetAabb(); box = box?.Merge(b) ?? b; }
        var merged = new ArrayMesh();
        if (box is { } bx)
        {
            float scale = size / Mathf.Max(1e-3f, Mathf.Max(bx.Size.X, Mathf.Max(bx.Size.Y, bx.Size.Z)));
            var fit = new Transform3D(Godot.Basis.FromScale(Vector3.One * scale), -bx.GetCenter() * scale);
            foreach (var p in parts)
            {
                var st = new SurfaceTool();
                st.AppendFrom(p.Mesh, p.Surface, fit * p.At);
                if (p.Mat != null) st.SetMaterial(p.Mat);
                st.Commit(merged);
            }
        }
        model.Free();
        return merged;
    }

    void Spray(Vector3 at, Vector3 away, Color? color, float amount)
    {
        if (Gore.Level > 0) Hits.Spray(at, away, color, amount * Gore.Level);
    }

    float Y(double x, double z) => (float)heightAt(x, z);
    static Vector3 V(double x, double y, double z) => new((float)x, (float)y, (float)z);
    static float R() => Sparks.R();

    /* --------------------------------------------------------- primitives -- */

    public void Flash(Vector3 at, Color color, float peak, float life, float range = 9)
    {
        int best = 0;
        for (int i = 1; i < flashes.Count; i++) if (flashes[i].Light.LightEnergy < flashes[best].Light.LightEnergy) best = i;
        var l = flashes[best].Light;
        l.Position = at;
        l.LightColor = color;
        l.OmniRange = range;
        l.Visible = true;
        flashes[best] = (l, 0, life, peak);
    }

    public void Burst(Vector3 at, School school, int n, float speed, float up = 1.5f, float size = 0.09f, float life = 0.45f, float gravity = 6)
    {
        var pal = Palette.Of(school);
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, v = speed * (0.4f + R() * 0.8f);
            // Among the specks, a few catch the light as glints.
            bool glint = R() < 0.3f;
            Sparks.Spawn(at, new Vector3(Mathf.Cos(a) * v, up * (0.5f + R()), Mathf.Sin(a) * v), life * (0.7f + R() * 0.6f), glint ? size * 2.2f : size, pal.Core, pal.Glow, 0.01f, gravity, 3,
                sprite: glint ? Sprites.Of("star") : 0, spinV: glint ? 6 : 0);
        }
    }

    Mark Ground(double x, double z, float radius, Texture2D tex, Color color, float life, float energy = 2.5f)
    {
        Mark? m = null;
        foreach (var k in marks) if (!k.Active) { m = k; break; }
        if (m == null)
        {
            m = new Mark { Decal = new Decal { UpperFade = 0.3f, LowerFade = 0.3f, CullMask = 1 } };
            AddChild(m.Decal);
            marks.Add(m);
        }
        m.Active = true;
        m.T = 0;
        m.Life = life;
        m.Radius = radius;
        m.Color = color;
        m.Progress = m.Grow = false;
        var d = m.Decal;
        d.TextureEmission = tex;
        d.TextureAlbedo = null;
        d.EmissionEnergy = energy;
        d.Modulate = color;
        d.AlbedoMix = 0;
        d.Position = V(x, heightAt(x, z), z);
        d.Rotation = Vector3.Zero;
        d.Size = new Vector3(radius * 2, 4, radius * 2);
        d.Visible = true;
        if (m.Fill != null) m.Fill.Visible = false;
        return m;
    }

    void Ring(double x, double z, float radius, Color color, float life, bool progress = false, int? key = null)
    {
        if (key is int k && keyed.TryGetValue(k, out var old)) { old.Active = false; old.Decal.Visible = false; if (old.Fill != null) old.Fill.Visible = false; }
        var m = Ground(x, z, radius, ringTex!, color, life);
        if (progress)
        {
            m.Progress = true;
            if (m.Fill == null) { m.Fill = new Decal { UpperFade = 0.3f, LowerFade = 0.3f, CullMask = 1, TextureEmission = discTex }; AddChild(m.Fill); }
            m.Fill.Position = m.Decal.Position;
            m.Fill.Modulate = color with { A = 0.55f };
            m.Fill.EmissionEnergy = 2;
            m.Fill.Size = new Vector3(0.01f, 4, 0.01f);
            m.Fill.Visible = true;
        }
        if (key is int k2) keyed[k2] = m;
    }

    void Lane(double x0, double z0, double x1, double z1, float width, Color color, float life, int? key = null)
    {
        if (key is int k && keyed.TryGetValue(k, out var old)) { old.Active = false; old.Decal.Visible = false; }
        double dx = x1 - x0, dz = z1 - z0, len = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
        var m = Ground((x0 + x1) / 2, (z0 + z1) / 2, 1, laneTex!, color, life);
        m.Decal.Size = new Vector3(width, 4, (float)len);
        m.Decal.Rotation = new Vector3(0, (float)Math.Atan2(dx, dz), 0);
        if (key is int k2) keyed[k2] = m;
    }

    /// <summary>A ring that races out from a point and fades.</summary>
    void Nova(double x, double z, float radius, Color color, float life)
    {
        var m = Ground(x, z, radius, ringTex!, color, life, 3);
        m.Grow = true;
    }

    /// <summary>A column of light from the ground (a strike from the sky, a level gained).</summary>
    void Pillar(Vector3 at, float height, float radius, Color color, float life)
    {
        var (m, mat, _, _) = beams[nextBeam];
        m.Position = at + Vector3.Up * height / 2;
        m.Rotation = Vector3.Zero;
        m.Scale = new Vector3(radius, height, radius);
        m.Visible = true;
        mat.SetShaderParameter("color", new Vector3(color.R, color.G, color.B));
        mat.SetShaderParameter("energy", 1f);
        mat.SetShaderParameter("taper", 1f);
        beams[nextBeam] = (m, mat, 0, life);
        nextBeam = (nextBeam + 1) % beams.Count;
    }

    /// <summary>A band of light between two points (a beam, a bolt of lightning's leg).</summary>
    void Band(Vector3 a, Vector3 b, float width, Color color, float life)
    {
        var (m, mat, _, _) = beams[nextBeam];
        var d = b - a;
        float len = Mathf.Max(0.05f, d.Length());
        m.Position = (a + b) / 2;
        // The cylinder's axis (Y) along the band.
        var y = d / len;
        var x = Mathf.Abs(y.Y) < 0.99f ? y.Cross(Vector3.Up).Normalized() : Vector3.Right;
        var z = x.Cross(y);
        m.Basis = new Godot.Basis(x * width, y * len, z * width);
        m.Visible = true;
        mat.SetShaderParameter("color", new Vector3(color.R, color.G, color.B));
        mat.SetShaderParameter("energy", 1f);
        mat.SetShaderParameter("taper", 0f);
        beams[nextBeam] = (m, mat, 0, life);
        nextBeam = (nextBeam + 1) % beams.Count;
    }

    /// <summary>Soft round shapes for the ground: a ring, a disc, a lane.</summary>
    static Texture2D GroundTexture(int kind)
    {
        const int N = 128;
        var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v), a;
                if (kind == 0) a = Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.07f, 0, 1) + Mathf.Clamp(1 - r, 0, 1) * 0.12f * (r < 0.93f ? 1 : 0);
                else if (kind == 1) a = r < 0.97f ? 0.35f + 0.65f * Mathf.SmoothStep(0.6f, 0.95f, r) : Mathf.Clamp((1 - r) / 0.03f, 0, 1);
                else { float e = Mathf.Abs(u); a = (Mathf.Clamp(1 - Mathf.Abs(e - 0.88f) / 0.1f, 0, 1) + 0.22f) * Mathf.Clamp((1 - Mathf.Abs(v)) / 0.05f, 0, 1); }
                a = Mathf.Clamp(a, 0, 1);
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return ImageTexture.CreateFromImage(img);
    }

    /* ------------------------------------------------------------- events -- */

    public void Handle(IReadOnlyList<CombatEvent> events, Battle b)
    {
        foreach (var ev in events)
        {
            switch (ev)
            {
                case Ev.Hit e:
                {
                    var at = V(e.X, Y(e.X, e.Z) + 1.0, e.Z);
                    if (e.Dot)
                    {
                        if (R() < 0.35f) Hits.Text(at, ((int)Math.Round(e.Amount)).ToString(), new Color(0.85f, 0.8f, 0.72f, 0.85f), 40);
                        break;
                    }
                    if (e.Blocked) { Hits.Text(at, "blocked", new Color(0.7f, 0.75f, 0.8f), 44); Burst(at, School.Physical, 5, 3, 2, 0.06f); break; }
                    Hits.Number(at, (int)Math.Round(e.Amount), e.Crit);
                    Burst(at, e.School, e.Crit ? 10 : 4, e.Crit ? 5 : 3, size: e.Crit ? 0.12f : 0.08f);
                    if (e.Family != null)
                    {
                        var away = new Vector3((float)e.Dx, 0, (float)e.Dz);
                        if (away.LengthSquared() < 0.01f) away = Vector3.Forward;
                        Gore.Hit(at + Vector3.Up * 0.2f, e.Amount, e.MaxHp, View.Gore.Of(e.Family, e.Def ?? ""), e.Family == Family.Undead, away.Normalized(), e.Crit);
                    }
                    if (e.Crit)
                    {
                        Sparks.Spawn(at, Vector3.Zero, 0.22f, 1.1f, Palette.Of(e.School).Core, sizeEnd: 0.25f, sprite: Sprites.Of("star"), spinV: 4);
                        Cam?.AddTrauma(0.04f);
                    }
                    break;
                }
                case Ev.Kill e:
                {
                    // A reflection breaking is glass, not a body (Ability: mirror_break).
                    if (e.Def == "mirror") break;
                    float gy = Y(e.X, e.Z);
                    var pal = Palette.Of(e.School);
                    var at = V(e.X, gy + 0.9, e.Z);
                    var away = new Vector3((float)e.Dx, 0, (float)e.Dz);
                    if (away.LengthSquared() < 0.01f) away = Vector3.Forward;
                    Gore.Kill(V(e.X, gy + 0.7 * e.Scale, e.Z), (float)e.Scale, View.Gore.Of(e.Family, e.Def), e.Family == Family.Undead, e.Burst, away.Normalized());
                    Burst(at, e.School, e.Elite ? 40 : 10, e.Elite ? 7 : 4, 3, life: 0.6f);
                    for (int i = 0; i < (e.Elite ? 14 : 4); i++)
                        Sparks.Spawn(V(e.X + (R() - 0.5) * 0.6, gy + 0.5, e.Z + (R() - 0.5) * 0.6), new Vector3(0, 1.4f + R() * 1.5f, 0), 1 + R() * 0.6f, 0.07f,
                            new Color(2.4f, 1.1f, 0.3f), new Color(1.6f, 0.3f, 0.05f), 0.02f, 0, 0.8f);
                    if (e.Family == Family.Undead)
                        for (int i = 0; i < 6; i++) Smoke.Spawn(V(e.X, gy + 0.6, e.Z), new Vector3((R() - 0.5f) * 3, 2 + R() * 2, (R() - 0.5f) * 3), 0.9f, 0.2f, new Color("#d8d2c0"), gravity: 9, sprite: Sprites.Of("dirt"), spinV: 3);
                    Smoke.Spawn(V(e.X, gy + 0.3, e.Z), new Vector3(0, 0.5f, 0), 0.9f, 0.5f, new Color("#3a3430"), new Color("#1a1816"), 1.3f, alpha: 0.35f);
                    if (e.Elite || e.Boss)
                    {
                        Flash(V(e.X, gy + 1.5, e.Z), pal.Light, 16, 0.6f, 12);
                        Nova(e.X, e.Z, 5, pal.Glow, 0.45f);
                        Cam?.AddTrauma(0.35f);
                    }
                    break;
                }
                case Ev.PlayerHit e:
                {
                    var at = V(e.X, Y(e.X, e.Z) + 1.2, e.Z);
                    if (e.Dodged || e.Blocked)
                    {
                        Hits.Text(at, e.Dodged ? "dodged" : "blocked", new Color(0.8f, 0.85f, 0.95f), 44);
                        Burst(at, e.Blocked ? School.Holy : School.Physical, 12, 4);
                        break;
                    }
                    Hits.Text(at + Vector3.Up * 0.2f, ((int)Math.Round(e.Amount)).ToString(), new Color(2f, 0.35f, 0.3f), 58);
                    Spray(at, Vector3.Up, null, 0.4f);
                    Cam?.AddTrauma((float)Math.Min(0.5, 0.12 + e.Amount / 60));
                    OnDamageFlash((float)Math.Min(1, 0.35 + e.Amount / 40));
                    break;
                }
                case Ev.ShieldHit e:
                {
                    var at = V(e.X, Y(e.X, e.Z) + 1.1, e.Z);
                    Hits.Text(at + Vector3.Up * 0.3f, ((int)Math.Round(e.Absorbed)).ToString(), new Color(1.4f, 1.3f, 0.9f), 44);
                    Burst(at, School.Holy, e.Broke ? 26 : 8, e.Broke ? 6 : 3, size: e.Broke ? 0.1f : 0.07f);
                    Flash(at, Palette.Of(School.Holy).Light, e.Broke ? 8 : 3, e.Broke ? 0.4f : 0.2f, 7);
                    if (e.Broke) { Nova(e.X, e.Z, 2.2f, Palette.Of(School.Holy).Glow, 0.3f); Cam?.AddTrauma(0.12f); }
                    break;
                }
                case Ev.PlayerHeal e:
                    if (e.Amount >= 3) Hits.Text(PlayerPos + Vector3.Up * 1.6f, $"+{(int)Math.Round(e.Amount)}", new Color(0.5f, 1.8f, 0.6f), 50);
                    break;
                case Ev.Nova e:
                {
                    var pal = Palette.Of(e.School);
                    Nova(e.X, e.Z, (float)e.Radius, pal.Glow, (float)Math.Max(0.25, e.Duration));
                    if ((e.Rings ?? 1) > 0) Flash(V(e.X, Y(e.X, e.Z) + 1.3, e.Z), pal.Light, 6, 0.35f, (float)e.Radius * 2);
                    break;
                }
                case Ev.Explosion e:
                {
                    float gy = Y(e.X, e.Z), r = (float)e.Radius;
                    var pal = Palette.Of(e.School);
                    Flash(V(e.X, gy + 1.2, e.Z), pal.Light, 10 + (float)e.Power * 10, 0.35f, r * 3 + 3);
                    Nova(e.X, e.Z, r * 1.15f, pal.Glow, 0.3f);
                    int n = Math.Min(40, 10 + (int)Math.Round(r * 8));
                    for (int i = 0; i < n; i++)
                    {
                        float a = R() * Mathf.Tau, v = r * (2 + R() * 3);
                        Sparks.Spawn(V(e.X, gy + 0.6, e.Z), new Vector3(Mathf.Cos(a) * v, 2 + R() * 4, Mathf.Sin(a) * v), 0.4f + R() * 0.4f, 0.1f + R() * 0.08f, pal.Core, pal.Glow, 0.01f, 8, 2.5f);
                    }
                    Sparks.Spawn(V(e.X, gy + 0.8, e.Z), Vector3.Zero, 0.3f, r * 1.3f, pal.Core, pal.Glow, r * 2.2f, alpha: 0.9f, sprite: Sprites.Of("fire"), spinV: 1.5f);
                    if (e.School is School.Fire or School.Shadow or School.Physical)
                        for (int i = 0; i < 6; i++) Smoke.Spawn(V(e.X + (R() - 0.5) * r, gy + 0.5, e.Z + (R() - 0.5) * r), new Vector3(0, 1 + R(), 0), 1.2f, r * 0.4f, new Color("#2a2420"), new Color("#121010"), r * 0.9f, drag: 1.2f, alpha: 0.45f);
                    Cam?.AddTrauma((float)Math.Min(0.3, 0.05 + e.Power * 0.1));
                    break;
                }
                case Ev.Chain e:
                {
                    var pal = Palette.Of(e.School);
                    var p = e.Points;
                    if (p.Length < 4) break;
                    float y = Y(p[0], p[1]) + 1.0f;
                    for (int k = 0; k + 3 < p.Length; k += 2)
                    {
                        var a = V(p[k], y, p[k + 1]);
                        var bb = V(p[k + 2], y, p[k + 3]);
                        // A jag in the middle of each leg.
                        var mid = (a + bb) / 2 + new Vector3((R() - 0.5f) * 0.8f, (R() - 0.5f) * 0.5f, (R() - 0.5f) * 0.8f);
                        Band(a, mid, 0.05f, pal.Core, 0.24f);
                        Band(mid, bb, 0.05f, pal.Core, 0.24f);
                        Burst(bb, e.School, 4, 3, size: 0.06f);
                    }
                    if (e.School == School.Storm) Flash(V(p[^2], y + 1, p[^1]), pal.Light, 6, 0.2f, 8);
                    break;
                }
                case Ev.Beam e:
                {
                    var pal = Palette.Of(e.School);
                    float y = Y(e.X0, e.Z0) + 1.0f;
                    Band(V(e.X0, y, e.Z0), V(e.X1, y, e.Z1), (float)e.Width * 0.3f, pal.Glow, (float)Math.Max(0.15, e.Duration));
                    Flash(V((e.X0 + e.X1) / 2, y, (e.Z0 + e.Z1) / 2), pal.Light, 6, (float)e.Duration, 12);
                    break;
                }
                case Ev.Strike e:
                {
                    float gy = Y(e.X, e.Z);
                    var pal = Palette.Of(e.School);
                    var at = V(e.X, gy, e.Z);
                    float r = (float)e.Radius;
                    if (e.Delay > 0.05)
                    {
                        Ring(e.X, e.Z, r, pal.Glow * 0.6f, (float)e.Delay, true);
                        pending.Add((time + e.Delay, () => { Pillar(at, 16, 0.35f + r * 0.1f, pal.Core, 0.3f); Flash(at + Vector3.Up * 2, pal.Light, 8, 0.25f, 10); }));
                    }
                    else { Pillar(at, 16, 0.35f, pal.Core, 0.3f); Flash(at + Vector3.Up * 2, pal.Light, 8, 0.25f, 10); }
                    break;
                }
                case Ev.Slash e:
                {
                    var pal = Palette.Of(e.School);
                    mirror = !mirror;
                    Hits.Arc(V(e.X, Y(e.X, e.Z) + 1.0, e.Z), (float)(Math.PI / 2 - e.Angle), (float)e.Reach, 0.22f, mirror, pal.Core, pal.Glow);
                    break;
                }
                case Ev.Telegraph e:
                {
                    var col = e.Hostile ? Palette.HostileDanger : Palette.Of(School.Holy).Glow;
                    if (e.Shape == TelegraphShape.Line) Lane(e.X, e.Z, e.X1 ?? e.X, e.Z1 ?? e.Z, (float)(e.Width ?? 1), col, (float)e.Duration, e.Id);
                    else if (e.Shape == TelegraphShape.Ring) Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, false, e.Id);
                    else Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, true, e.Id);
                    break;
                }
                case Ev.Spawn e:
                {
                    float gy = Y(e.X, e.Z);
                    if (e.Style == SpawnStyle.Rise)
                    {
                        for (int i = 0; i < 10; i++) Smoke.Spawn(V(e.X + (R() - 0.5) * 0.8, gy + 0.1, e.Z + (R() - 0.5) * 0.8), new Vector3((R() - 0.5f) * 2, 1 + R() * 2, (R() - 0.5f) * 2), 0.7f, 0.2f, new Color("#3a2e22"), gravity: 6, sprite: Sprites.Of("dirt"), spinV: 2);
                        Smoke.Spawn(V(e.X, gy + 0.2, e.Z), new Vector3(0, 0.3f, 0), 1, 0.6f, new Color("#2e2620"), sizeEnd: 1.2f, alpha: 0.4f);
                        Sparks.Spawn(V(e.X, gy + 0.3, e.Z), new Vector3(0, 0.6f, 0), 0.8f, 0.5f, new Color(0.3f, 0.5f, 1.2f), sizeEnd: 0.1f, alpha: 0.35f);
                    }
                    else if (e.Style == SpawnStyle.Burrow)
                        for (int i = 0; i < 8; i++) Smoke.Spawn(V(e.X, gy + 0.1, e.Z), new Vector3((R() - 0.5f) * 3, 1.5f + R() * 2, (R() - 0.5f) * 3), 0.6f, 0.18f, new Color("#4a3a28"), gravity: 8, sprite: Sprites.Of("dirt"), spinV: 2);
                    break;
                }
                case Ev.Pickup e:
                    if (e.Kind is PickupKind.Ember or PickupKind.Gold)
                        Sparks.Spawn(PlayerPos + Vector3.Up, new Vector3(0, 1, 0), 0.3f, 0.25f, e.Kind == PickupKind.Gold ? new Color(2f, 1.5f, 0.5f) : new Color(2.2f, 1f, 0.35f), sizeEnd: 0.05f, alpha: 0.6f);
                    break;
                case Ev.LevelUp:
                {
                    var p = PlayerPos;
                    Nova(p.X, p.Z, 3.6f, Palette.Of(School.Fire).Glow, 0.5f);
                    Pillar(p, 7, 0.55f, Palette.Of(School.Holy).Core * 0.6f, 0.55f);
                    Flash(p + Vector3.Up * 2, new Color("#ffc070"), 10, 0.7f, 9);
                    for (int i = 0; i < 30; i++)
                    {
                        float a = R() * Mathf.Tau;
                        bool glint = i % 3 == 0;
                        Sparks.Spawn(p + new Vector3(Mathf.Cos(a) * 0.8f, 0.2f, Mathf.Sin(a) * 0.8f), new Vector3(Mathf.Cos(a) * 0.5f, 3 + R() * 4, Mathf.Sin(a) * 0.5f), 1.2f, glint ? 0.3f : 0.1f, new Color(2.4f, 1.9f, 1.1f), new Color(2.2f, 0.6f, 0.1f), 0.02f, 0, 1.5f,
                            sprite: glint ? Sprites.Of("star") : 0, spinV: 3);
                    }
                    break;
                }
                case Ev.Evolve or Ev.Discovery:
                {
                    var p = PlayerPos;
                    Nova(p.X, p.Z, 9, Palette.Of(School.Arcane).Glow, 0.8f);
                    Flash(p + Vector3.Up * 2, new Color("#ffe0ff"), 30, 1.2f, 18);
                    Cam?.AddTrauma(0.3f);
                    break;
                }
                case Ev.PerfectDodge e:
                {
                    // A blow slipped at the last moment: a ring of cold light
                    // cracks out from you, glints spin in the air, the word.
                    var at = V(e.X, Y(e.X, e.Z) + 1.0, e.Z);
                    Nova(e.X, e.Z, (float)SurvivorUnchained.Content.Abilities.Dash.Crack, new Color(0.9f, 1.3f, 2.2f), 0.35f);
                    Flash(at + Vector3.Up * 0.6f, new Color("#cfe4ff"), 14, 0.3f, 9);
                    for (int i = 0; i < 8; i++)
                    {
                        float a = i / 8f * Mathf.Tau;
                        Sparks.Spawn(at + new Vector3(Mathf.Cos(a) * 0.6f, 0.2f, Mathf.Sin(a) * 0.6f), new Vector3(Mathf.Cos(a) * 3, 1.2f, Mathf.Sin(a) * 3), 0.4f, 0.22f,
                            new Color(2.4f, 2.6f, 3.2f), new Color(0.4f, 0.6f, 1.6f), 0.05f, 0, 1.5f, sprite: Sprites.Of("star"), spinV: 6);
                    }
                    Hits.Text(at + Vector3.Up * 1.1f, "PERFECT", new Color(1.6f, 1.8f, 2.4f), 70);
                    Cam?.AddTrauma(0.12f);
                    break;
                }
                case Ev.Dash e:
                    for (int i = 0; i < 14; i++)
                    {
                        float t = i / 14f;
                        double x = e.X0 + (e.X1 - e.X0) * t, z = e.Z0 + (e.Z1 - e.Z0) * t;
                        Sparks.Spawn(V(x, Y(x, z) + 0.9, z), Vector3.Zero, 0.35f, 0.5f, new Color(0.5f, 0.65f, 1.3f), new Color(0.1f, 0.14f, 0.4f), 0.1f, alpha: 0.35f);
                        Smoke.Spawn(V(x, Y(x, z) + 0.15, z), new Vector3(0, 0.4f, 0), 0.6f, 0.3f, new Color("#4a4038"), sizeEnd: 0.7f, alpha: 0.35f);
                    }
                    break;
                case Ev.Ability e:
                    Ability(e, b);
                    break;
                case Ev.Status e:
                    if (e.Kind == StatusKind.Frozen)
                        for (int i = 0; i < 8; i++) Sparks.Spawn(V(e.X, Y(e.X, e.Z) + 0.8, e.Z), new Vector3((R() - 0.5f) * 2, R() * 2, (R() - 0.5f) * 2), 0.5f, 0.25f, new Color(1.6f, 2.2f, 2.6f), drag: 3, sprite: Sprites.Of("star"), spinV: 2);
                    break;
                case Ev.Shake e:
                    Cam?.AddTrauma((float)e.Amount);
                    break;
            }
        }
    }

    static readonly Color GlassCore = new(1.6f, 2.2f, 2.8f), GlassGlow = new(0.6f, 1.3f, 2.2f), EchoGlow = new(1.3f, 0.8f, 2.6f), WraithGlow = new(0.9f, 0.5f, 2.2f), Chain = new(1.5f, 1.35f, 1.1f);
    const int EchoKey = -7771;

    void Ability(Ev.Ability e, Battle b)
    {
        float gy = Y(e.X, e.Z);
        var at = V(e.X, gy, e.Z);
        var to = V(e.X1, Y(e.X1, e.Z1), e.Z1);
        switch (e.Id)
        {
            case "shield_bash":
                Hits.Arc(at + Vector3.Up * 0.9f, (float)(Math.PI / 2 - e.Angle), (float)e.Radius, 0.25f, false, Palette.Of(School.Holy).Core, Palette.Of(School.Physical).Glow);
                if (e.Wide)
                {
                    Hits.Arc(at + Vector3.Up * 0.9f, (float)(Math.PI / 2 - e.Angle + Math.PI), (float)e.Radius, 0.25f, true, Palette.Of(School.Holy).Core, Palette.Of(School.Physical).Glow);
                    Nova(e.X, e.Z, (float)e.Radius, Palette.Of(School.Holy).Glow, 0.35f);
                }
                Burst(at + new Vector3((float)Math.Cos(e.Angle) * 1.5f, 1, (float)Math.Sin(e.Angle) * 1.5f), School.Physical, 20, 6);
                Flash(at + Vector3.Up * 1.2f, new Color("#fff0d0"), 10, 0.3f);
                break;
            case "leap":
                Ring(e.X, e.Z, (float)e.Radius, Palette.HostileRim * 0.3f + Palette.Of(School.Physical).Glow, 0.42f, true);
                break;
            case "blink":
            {
                var f = Palette.Of(School.Frost);
                Nova(e.X, e.Z, 3.2f, f.Glow, 0.45f);
                Burst(at + Vector3.Up * 0.6f, School.Frost, 26, 5, 1.2f, 0.08f, 0.6f, 3);
                Flash(at + Vector3.Up * 1.2f, f.Light, 8, 0.35f);
                break;
            }
            case "sprint":
                Nova(e.X, e.Z, 2.2f, new Color(1.2f, 1.15f, 1.0f), 0.3f);
                Dust(e.X, e.Z, 14, 3.5f);
                break;
            case "mirror_step":
                // The glass forms where you stood.
                Flash(at + Vector3.Up * 1.2f, new Color(0.6f, 0.85f, 1f), 9, 0.4f);
                Shards(at + Vector3.Up * 1.1f, 18, 3.5f);
                Band(at + Vector3.Up * 1.1f, to + Vector3.Up * 1.1f, 0.06f, GlassGlow, 0.25f);
                break;
            case "mirror_break":
                Flash(at + Vector3.Up * 1.1f, new Color(0.6f, 0.85f, 1f), 10, 0.35f);
                Shards(at + Vector3.Up * 1.1f, 34, 6.5f);
                Nova(e.X, e.Z, (float)e.Radius, GlassGlow, 0.35f);
                break;
            case "mirror_strike":
                Hits.Arc(at + Vector3.Up * 0.9f, (float)(Math.PI / 2 - e.Angle), (float)e.Radius, 0.2f, false, GlassCore, GlassGlow);
                break;
            case "bull_rush":
            {
                var h = Palette.Of(School.Holy);
                Flash(at + Vector3.Up * 1.2f, h.Light, 7, 0.3f);
                Nova(e.X, e.Z, 1.8f, h.Glow * 0.8f, 0.3f);
                Dust(e.X, e.Z, 18, 4.5f);
                break;
            }
            case "wraith_walk":
                Nova(e.X, e.Z, (float)e.Radius, WraithGlow, 0.45f);
                Flash(at + Vector3.Up * 1.2f, new Color(0.6f, 0.4f, 1f), 7, 0.4f);
                Burst(at + Vector3.Up * 1, School.Shadow, 20, 2.5f, 2.5f, 0.1f, 0.8f, -1);
                break;
            case "drain":
            {
                // A thread from what is drained into the ghost.
                Band(at + Vector3.Up * 1.0f, to + Vector3.Up * 1.1f, 0.05f, WraithGlow, 0.3f);
                var sh = Palette.Of(School.Shadow);
                for (int i = 0; i < 6; i++)
                {
                    float k = R();
                    Sparks.Spawn(at.Lerp(to, k) + Vector3.Up * (1 + R() * 0.3f), (to - at).Normalized() * 3 + Vector3.Up * 0.5f, 0.35f, 0.07f, sh.Core, sh.Glow, 0.01f, drag: 2);
                }
                break;
            }
            case "cinder_trail":
                Nova(e.X, e.Z, 2.4f, Palette.Of(School.Fire).Glow, 0.4f);
                Burst(at + Vector3.Up * 0.4f, School.Fire, 24, 3.5f, 2.2f, 0.09f, 0.7f, -0.5f);
                Flash(at + Vector3.Up * 1, Palette.Of(School.Fire).Light, 8, 0.35f);
                break;
            case "grapple" or "grapple_miss":
            {
                bool miss = e.Id == "grapple_miss";
                var from = at + Vector3.Up * 1.3f;
                var end = to + Vector3.Up * (miss ? 0.4f : 1.0f);
                Band(from, end, 0.035f, Chain, miss ? 0.2f : 0.3f);
                Links(from, end);
                if (!miss) { Burst(end, School.Physical, 14, 4, 1, 0.07f, 0.35f); Flash(end, new Color("#ffe0b0"), 5, 0.2f); }
                break;
            }
            case "chain_whirl":
                Hits.Arc(at + Vector3.Up * 0.9f, 0, (float)e.Radius, 0.28f, false, Chain, Palette.Of(School.Physical).Glow);
                Hits.Arc(at + Vector3.Up * 0.9f, Mathf.Pi, (float)e.Radius, 0.28f, true, Chain, Palette.Of(School.Physical).Glow);
                Nova(e.X, e.Z, (float)e.Radius, Palette.Of(School.Physical).Glow, 0.3f);
                break;
            case "echo_step":
                Nova(e.X, e.Z, 1.6f, EchoGlow, 0.4f);
                Flash(at + Vector3.Up * 1.2f, new Color(0.75f, 0.55f, 1f), 6, 0.35f);
                Ring(e.X, e.Z, 1.1f, EchoGlow * 0.7f, (float)Math.Max(0.1, b.Art.EchoT), true, EchoKey);
                break;
            case "echo_recall":
                Ring(e.X, e.Z, 0.01f, EchoGlow, 0.01f, false, EchoKey);
                Band(to + Vector3.Up * 1.1f, at + Vector3.Up * 1.1f, 0.08f, EchoGlow, 0.3f);
                Nova(e.X, e.Z, (float)e.Radius, EchoGlow, 0.4f);
                Nova(e.X1, e.Z1, 2f, EchoGlow * 0.7f, 0.35f);
                Flash(at + Vector3.Up * 1.2f, new Color(0.75f, 0.55f, 1f), 10, 0.4f);
                Burst(at + Vector3.Up * 1, School.Arcane, 22, 3, 1.5f, 0.08f, 0.6f, 1);
                break;
            case "iron_vow":
            {
                // The vow renewed: a ring of pale gold closing round you.
                var h = Palette.Of(School.Holy);
                Nova(e.X, e.Z, 1.6f, h.Glow * 0.6f, 0.45f);
                for (int i = 0; i < 12; i++)
                {
                    float a = i * Mathf.Tau / 12;
                    var from = at + new Vector3(Mathf.Cos(a) * 1.3f, 0.3f + R() * 1.4f, Mathf.Sin(a) * 1.3f);
                    Sparks.Spawn(from, (at + Vector3.Up * 1.1f - from) * 2.2f, 0.4f, 0.07f, h.Core, h.Glow, 0.02f, drag: 1);
                }
                break;
            }
            case "vault":
                Dust(e.X, e.Z, 16, 4);
                Burst(at + Vector3.Up * 0.3f, School.Physical, 10, 3, 0.6f, 0.06f, 0.4f);
                break;
            default:
            {
                // A war cry, a ward, a vanishing: a ring from where they stand.
                var school = e.Id switch { "bulwark" => School.Holy, "smoke_bomb" => School.Shadow, "warcry" => School.Fire, _ => School.Arcane };
                Nova(e.X, e.Z, (float)Math.Max(2.4, e.Radius), Palette.Of(school).Glow, 0.4f);
                Flash(at + Vector3.Up * 1.4f, Palette.Of(school).Light, 6, 0.35f);
                break;
            }
        }
    }

    /// <summary>Glass flying: bright glints that tumble and fall.</summary>
    void Shards(Vector3 at, int n, float speed)
    {
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, v = speed * (0.3f + R() * 0.9f);
            Sparks.Spawn(at + new Vector3(R() - 0.5f, R() - 0.5f, R() - 0.5f) * 0.6f, new Vector3(Mathf.Cos(a) * v, 1 + R() * 3, Mathf.Sin(a) * v), 0.5f + R() * 0.4f,
                0.09f + R() * 0.08f, GlassCore, GlassGlow, 0.02f, 9, 1.5f, sprite: Sprites.Of("star"), spinV: 10);
        }
    }

    /// <summary>Kicked-up earth at the feet.</summary>
    void Dust(double x, double z, int n, float speed)
    {
        var at = V(x, Y(x, z) + 0.15, z);
        var pal = Palette.Of(School.Physical);
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, v = speed * (0.3f + R() * 0.7f);
            Smoke.Spawn(at, new Vector3(Mathf.Cos(a) * v, 0.4f + R() * 0.8f, Mathf.Sin(a) * v), 0.6f + R() * 0.4f, 0.35f, pal.Dim * 0.5f, pal.Dim * 0.2f, 1.1f, 0, 3, 0.5f);
        }
    }

    /// <summary>Links of a chain glinting along a line.</summary>
    void Links(Vector3 a, Vector3 b)
    {
        float len = a.DistanceTo(b);
        int n = Math.Min(24, (int)(len / 0.45f));
        for (int i = 1; i <= n; i++)
            Sparks.Spawn(a.Lerp(b, i / (float)(n + 1)), Vector3.Zero, 0.22f, 0.06f, Chain, Chain * 0.5f, 0.04f);
    }

    /* -------------------------------------------------------------- frame -- */

    public void Update(Battle b, double dt, double now)
    {
        time = now;
        float fdt = (float)dt;
        for (int i = pending.Count - 1; i >= 0; i--)
            if (pending[i].At <= now) { var fn = pending[i].Fn; pending.RemoveAt(i); fn(); }
        for (int i = 0; i < flashes.Count; i++)
        {
            var (l, t, life, peak) = flashes[i];
            if (t >= 1) continue;
            t = Mathf.Min(1, t + fdt / life);
            l.LightEnergy = peak / Mathf.Pi * (1 - t) * (1 - t);
            if (t >= 1) l.Visible = false;
            flashes[i] = (l, t, life, peak);
        }
        foreach (var m in marks)
        {
            if (!m.Active) continue;
            m.T += fdt / Mathf.Max(0.05f, m.Life);
            if (m.T >= 1) { m.Active = false; m.Decal.Visible = false; if (m.Fill != null) m.Fill.Visible = false; continue; }
            if (m.Grow)
            {
                float r = m.Radius * (0.25f + 0.75f * Mathf.Sqrt(m.T));
                m.Decal.Size = new Vector3(r * 2, 4, r * 2);
                m.Decal.Modulate = m.Color with { A = 1 - m.T };
            }
            else
            {
                // Telegraphs: steady, a quick flare at the end.
                m.Decal.Modulate = m.Color with { A = m.T > 0.85f ? 1 : 0.75f + 0.1f * Mathf.Sin((float)now * 12) };
                if (m.Progress && m.Fill != null) { float r = m.Radius * m.T; m.Fill.Size = new Vector3(r * 2, 4, r * 2); }
            }
        }
        for (int i = 0; i < beams.Count; i++)
        {
            var (m, mat, t, life) = beams[i];
            if (t >= 1) continue;
            t += fdt / life;
            mat.SetShaderParameter("alpha", Mathf.Max(0, 1 - t));
            if (t >= 1) m.Visible = false;
            beams[i] = (m, mat, t, life);
        }
        Zones(b, now);
        ArtTrails(b, fdt);
        Projectiles(b, fdt, now);
        Pickups(b, now);
        Sparks.Step(fdt);
        Smoke.Step(fdt);
        Gore.Step(fdt);
    }

    float artT;

    /// <summary>An art while it runs: wind off a sprint, wisps off a wraith,
    /// embers off a cinder run, dust before a charge, the chain on a haul.</summary>
    void ArtTrails(Battle b, float dt)
    {
        var p = b.Player;
        var a = b.Art;
        if (!p.Alive) return;
        artT -= dt;
        bool tick = artT <= 0;
        if (tick) artT = 1 / 30f;
        float gy = Y(p.X, p.Z);
        var feet = V(p.X, gy + 0.15, p.Z);
        float sp = (float)Math.Sqrt(p.Vx * p.Vx + p.Vz * p.Vz);
        var back = sp > 0.3f ? new Vector3((float)-p.Vx, 0, (float)-p.Vz) / sp : Vector3.Zero;
        if (a.SprintT > 0 && tick && sp > 1)
        {
            // Streaks of air peeling off behind.
            var side = new Vector3(back.Z, 0, -back.X) * (R() - 0.5f) * 0.9f;
            Sparks.Spawn(feet + Vector3.Up * (0.3f + R() * 1.3f) + side, back * (4 + R() * 3), 0.25f, 0.05f, new Color(1.1f, 1.1f, 1.05f), new Color(0.4f, 0.45f, 0.5f), 0.01f, drag: 3, alpha: 0.6f);
            if (R() < 0.35f) Dust(p.X, p.Z, 1, 1.2f);
        }
        if (a.WraithT > 0 && tick)
        {
            var sh = Palette.Of(School.Shadow);
            for (int i = 0; i < 2; i++)
                Sparks.Spawn(feet + new Vector3((R() - 0.5f) * 0.7f, 0.2f + R() * 1.6f, (R() - 0.5f) * 0.7f), back * 1.5f + Vector3.Up * (0.8f + R()), 0.7f, 0.1f, sh.Core, sh.Dim, 0.02f, -0.5f, 1.5f);
        }
        if (a.CinderT > 0 && tick)
        {
            var f = Palette.Of(School.Fire);
            for (int i = 0; i < 2; i++)
                Sparks.Spawn(feet + new Vector3((R() - 0.5f) * 0.5f, R() * 0.4f, (R() - 0.5f) * 0.5f), back * 1.2f + Vector3.Up * (1.2f + R() * 1.5f), 0.6f + R() * 0.4f, 0.07f, f.Core, f.Glow, 0.01f, -1.2f, 1.2f);
        }
        if (a.Rush == AbilityKind.BullRush && tick)
        {
            Dust(p.X, p.Z, 2, 2.5f);
            Sparks.Spawn(feet + Vector3.Up * 1.1f + new Vector3((float)a.RushDX, 0, (float)a.RushDZ) * 0.6f, Vector3.Up * 0.2f, 0.12f, 0.5f, Palette.Of(School.Holy).Glow * 0.5f, Palette.Of(School.Holy).Dim * 0.1f, 0.9f);
        }
        if (a.Rush == AbilityKind.Grapple && a.Hooked is { Alive: true } h)
        {
            var from = feet + Vector3.Up * 1.15f;
            var to = V(h.X, Y(h.X, h.Z) + 1.0, h.Z);
            if (tick) { Band(from, to, 0.03f, Chain, 0.06f); Links(from, to); }
        }
    }

    /// <summary>Ground left burning, blighted, hallowed: a disc for each while it lasts.</summary>
    void Zones(Battle b, double now)
    {
        var alive = new HashSet<int>();
        foreach (var z in b.Zones.Living())
        {
            alive.Add(z.Id);
            var school = Palette.OfArt(z.Art);
            var col = z.Owner == Sim.Side.Enemy ? Palette.HostileDanger * 0.6f : Palette.Of(school).Glow * 0.5f;
            // Hallowed and arcane ground is a turning circle of runes, burning
            // ground a spread of fire; the rest, and the enemy's, a glow.
            bool mine = z.Owner != Sim.Side.Enemy, runes = mine && school is School.Holy or School.Arcane;
            if (!zoneMarks.TryGetValue(z.Id, out var m) || !m.Active)
            {
                var tex = !mine ? discTex! : school switch { School.Holy => Sprites.Runes(1), School.Arcane => Sprites.Runes(0), School.Fire => Sprites.Burning, _ => discTex! };
                m = Ground(z.X, z.Z, (float)z.Radius, tex, col, 1e6f, runes ? 2.2f : 1.2f);
                zoneMarks[z.Id] = m;
            }
            m.T = 0;
            if (runes) m.Decal.Rotation = new Vector3(0, (float)(now * 0.3 + z.Id), 0);
            m.Decal.Position = V(z.X, heightAt(z.X, z.Z), z.Z);
            m.Decal.Size = new Vector3((float)z.Radius * 2, 4, (float)z.Radius * 2);
            float fade = (float)Math.Min(1, Math.Min(z.Age / 0.2, (z.Life - z.Age) / 0.4));
            m.Decal.Modulate = col with { A = Mathf.Max(0, fade) * (0.55f + 0.15f * Mathf.Sin((float)now * 3 + z.Id)) };
            if (R() < 0.3f)
            {
                float a = R() * Mathf.Tau, d = (float)z.Radius * Mathf.Sqrt(R());
                var pal = Palette.Of(school);
                double x = z.X + Mathf.Cos(a) * d, zz = z.Z + Mathf.Sin(a) * d;
                Sparks.Spawn(V(x, Y(x, zz) + 0.1, zz), new Vector3(0, 0.8f + R(), 0), 0.8f, 0.07f, z.Owner == Sim.Side.Enemy ? Palette.HostileRim : pal.Glow, pal.Dim, 0.01f, drag: 1);
            }
        }
        var gone = new List<int>();
        foreach (var (id, m) in zoneMarks) if (!alive.Contains(id)) { m.Active = false; m.Decal.Visible = false; gone.Add(id); }
        foreach (var id in gone) zoneMarks.Remove(id);
    }

    void Projectiles(Battle b, float dt, double now)
    {
        orbs.Begin(); steel.Begin(); shards.Begin(); rings.Begin(); kegs.Begin();
        foreach (var p in b.Projectiles.Living())
        {
            var art = p.Art;
            var school = p.School == School.Physical ? Palette.OfArt(art) : p.School;
            var pal = Palette.Of(school);
            bool hostile = p.Owner == Sim.Side.Enemy;
            float gy = Y(p.X, p.Z);
            var at = V(p.X, gy + p.Y, p.Z);
            float heading = Mathf.Atan2((float)p.Vx, (float)p.Vz);
            float trail = 1;
            if (art.StartsWith("dagger") || art.StartsWith("arrow") || art == "bolt_bone" || art.StartsWith("axe"))
            {
                var basis = new Godot.Basis(Vector3.Up, heading);
                if (art.StartsWith("dagger")) basis = basis * new Godot.Basis(Vector3.Right, (float)(now * 18 + p.Id));
                if (art.StartsWith("axe")) basis = new Godot.Basis(Vector3.Up, (float)(now * 14 + p.Id)) * Godot.Basis.FromScale(new Vector3(3, 1.5f, 1.2f));
                steel.Add(new Transform3D(basis, at), hostile ? new Color(0.5f, 0.42f, 0.36f) : new Color(0.75f, 0.72f, 0.68f));
                trail = 0.3f;
            }
            else if (art.StartsWith("disc") || art.StartsWith("chakram"))
            {
                float s = art.StartsWith("disc") ? 1.1f : 0.8f;
                rings.Add(new Transform3D(new Godot.Basis(Vector3.Up, (float)(now * 16)).Scaled(Vector3.One * s), at), pal.Glow * 0.5f);
                trail = 0.5f;
            }
            else if (art.StartsWith("shard") || art == "spear_ice")
            {
                float s = art == "spear_ice" ? 2.4f : 1;
                var basis = new Godot.Basis(Vector3.Up, heading) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2);
                shards.Add(new Transform3D(basis.Scaled(Vector3.One * s), at), pal.Glow * 0.6f);
                trail = 0.6f;
            }
            else if (art == "firepot")
            {
                // Tumbling end over end, its fuse alight.
                var tumble = new Godot.Basis(Vector3.Up, heading) * new Godot.Basis(Vector3.Right, (float)(now * 9 + p.Id));
                kegs.Add(new Transform3D(tumble, at), Colors.White);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.22f), at + tumble.Y * 0.2f), new Color(1.8f, 0.8f, 0.25f));
                trail = 0.6f;
            }
            else
            {
                float size = art is "mote" or "mote_cascade" or "mote_star" or "ember_seeker" ? 0.34f : art is "star" ? 1.0f : art is "cinder" or "living_flame" ? 0.7f : art.StartsWith("herd") ? 1.3f : art.StartsWith("crescent") ? 1.6f : 0.5f;
                var core = hostile ? Palette.HostileRim : pal.Core;
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * size), at), core);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * size * 2.2f), at), (hostile ? Palette.HostileDanger : pal.Glow) * 0.35f);
            }
            // A trail of its own light behind it.
            trailAcc.TryGetValue(p.Id, out var acc);
            acc += dt * 40 * trail;
            while (acc >= 1)
            {
                acc -= 1;
                Sparks.Spawn(at + new Vector3((R() - 0.5f) * 0.08f, (R() - 0.5f) * 0.08f, (R() - 0.5f) * 0.08f), Vector3.Zero, 0.25f + 0.2f * trail, 0.12f * (0.5f + trail), hostile ? Palette.HostileRim : pal.Glow, pal.Dim, 0.01f);
            }
            trailAcc[p.Id] = acc;
        }
        if (trailAcc.Count > 2000) trailAcc.Clear();
        orbs.End(); steel.End(); shards.End(); rings.End(); kegs.End();
    }

    static readonly Color[] EmberTiers = { new(2.4f, 1.0f, 0.25f), new(2.6f, 1.7f, 0.45f), new(2.8f, 2.6f, 1.6f), new(1.6f, 2.2f, 2.8f) };

    void Pickups(Battle b, double now)
    {
        embers.Begin(); coins.Begin(); flasks.Begin(); lodestones.Begin(); sacks.Begin(); chests.Begin(); lootBeams.Begin();
        foreach (var p in b.Pickups.Living())
        {
            float gy = Y(p.X, p.Z);
            float bob = Mathf.Sin((float)(now * 3 + p.Id)) * 0.08f;
            var spin = new Godot.Basis(Vector3.Up, (float)(now * 2.2 + p.Id));
            switch (p.Kind)
            {
                case PickupKind.Ember:
                {
                    int tier = Math.Clamp(p.Tier, 0, 3);
                    float s = new[] { 0.16f, 0.21f, 0.27f, 0.34f }[tier];
                    embers.Add(new Transform3D(spin.Scaled(Vector3.One * s), V(p.X, gy + 0.45 + bob, p.Z)), EmberTiers[tier] * 0.5f);
                    break;
                }
                case PickupKind.Gold:
                    coins.Add(new Transform3D(spin * new Godot.Basis(Vector3.Right, Mathf.Pi / 2), V(p.X, gy + 0.35 + bob, p.Z)), new Color(1.0f, 0.75f, 0.3f));
                    break;
                case PickupKind.Heal:
                    flasks.Add(new Transform3D(spin, V(p.X, gy + 0.35 + bob, p.Z)), Colors.White);
                    break;
                case PickupKind.Magnet:
                    lodestones.Add(new Transform3D(spin, V(p.X, gy + 0.5 + bob, p.Z)), Colors.White);
                    break;
                default:
                {
                    // Gear and what else is worth carrying, set down where it
                    // fell (not spun), and a light to find it by.
                    var col = Palette.Rarity[Math.Clamp(p.Tier, 0, Palette.Rarity.Length - 1)];
                    if (p.Kind == PickupKind.Quest) col = new Color("#ffd46a");
                    var lie = new Godot.Basis(Vector3.Up, p.Id * 2.4f);
                    if (p.Kind == PickupKind.Chest) chests.Add(new Transform3D(lie, V(p.X, gy + chestUp, p.Z)), Colors.White);
                    else sacks.Add(new Transform3D(lie, V(p.X, gy + sackUp, p.Z)), Colors.White);
                    float h = p.Kind is PickupKind.Material ? 1.4f : 3.2f;
                    lootBeams.Add(new Transform3D(Godot.Basis.Identity.Scaled(new Vector3(1, h, 1)), V(p.X, gy + h / 2, p.Z)), col);
                    break;
                }
            }
        }
        embers.End(); coins.End(); flasks.End(); lodestones.End(); sacks.End(); chests.End(); lootBeams.End();
    }
}

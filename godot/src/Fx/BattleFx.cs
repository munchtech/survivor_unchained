using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;
using SurvivorUnchained.Content;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Ui;
using LootTier = SurvivorUnchained.Rpg.LootTier;
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
    /// <summary>Filmed effects cut into atlases: blasts, flame, smoke, magic.</summary>
    public readonly Flipbooks Books = new();
    /// <summary>What blows leave on the ground: scorch, frost, cracks, sigils.</summary>
    public readonly Scars Scars = new();
    public readonly Shockwaves Waves = new();
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
    Batch shades = null!, orbs = null!, steel = null!, axes = null!, daggers = null!, shards = null!, rings = null!, chakrams = null!, embers = null!, coins = null!, flasks = null!, lodestones = null!, sacks = null!, chests = null!, kegs = null!;
    /// <summary>How far above the ground the middle of a sack and a chest sits.</summary>
    float sackUp, chestUp;
    readonly Dictionary<int, float> trailAcc = new();

    static Texture2D? ringTex, discTex, laneTex, hatchTex, dashTex, wallTex, laneFillTex;
    static readonly Dictionary<int, Texture2D> coneTex = new(), bandTex = new();

    sealed class Mark
    {
        public required Decal Decal;
        public float T, Life, Radius;
        public bool Progress, Grow, Active;
        public Color Color;
        public Decal? Fill;
        /// <summary>A lane's fill runs from its start to its end over its life: where it comes from,
        /// which way, how long.</summary>
        public Vector3 From, Along;
        public float Length;
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
        AddChild(Books);
        AddChild(Scars);
        AddChild(Waves);
        AddChild(Hits);
        AddChild(Gore);
        AddChild(Ribbons);
        AddChild(Blades);
        for (int i = 0; i < 8; i++)
        {
            var l = new OmniLight3D { LightEnergy = 0, OmniRange = 10, OmniAttenuation = 1.6f, ShadowEnabled = false, Visible = false };
            AddChild(l);
            flashes.Add((l, 1, 1, 0));
        }
        ringTex ??= GroundTexture(0);
        discTex ??= GroundTexture(1);
        laneTex ??= GroundTexture(2);
        hatchTex ??= GroundTexture(3);
        dashTex ??= GroundTexture(4);
        wallTex ??= GroundTexture(5);
        laneFillTex ??= GroundTexture(6);
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
        // What the survivor sends flying is drawn over the crowd it flies through.
        var over = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/spark_over.gdshader") };
        over.SetShaderParameter("sprites", Sprites.Array);
        // The dark under them, drawn first, so a light over the pale dead still shows.
        shades = Add(new Batch(new QuadMesh { Size = Vector2.One }, 600, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/spark_shade.gdshader"), RenderPriority = -1 }));
        orbs = Add(new Batch(new QuadMesh { Size = Vector2.One }, 1400, over));
        steel = Add(new Batch(Arrow(), 600, Glowing(0.3f, 0.35f, 0.5f)));
        // What is thrown is the weapon in hand (Arms), not a stick of light.
        axes = Add(new Batch(Weapon("viking_axe", 0.85f), 400, null));
        daggers = Add(new Batch(Weapon("dagger_b", 0.5f), 600, null));
        shards = Add(new Batch(IceLance(), 600, Crystal(0.5f, 1.8f, 0.05f, 1f)));
        rings = Add(new Batch(new TorusMesh { InnerRadius = 0.36f, OuterRadius = 0.5f, Rings = 16, RingSegments = 6 }, 200, Glowing(1.2f, 0.2f, 0.8f)));
        chakrams = Add(new Batch(ChakramMesh(), 200, new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/chakram.gdshader") }));
        // What lies on the ground is what the pack shows (the photographs'
        // models): an ember is the ember's crystals, lit the colour of its
        // worth; a draught, a lodestone, a sack of what was carried, a chest.
        // Lit by their own colour at about its strength, no more: at 2.6 times a stone was white-hot
        // in every channel and the tone curve made cream popcorn of a field of them.
        embers = Add(new Batch(Pickup("ember", 1.25f, m => m is BaseMaterial3D { EmissionEnabled: true }), 1400, Glowing(1.0f, 0.25f)));
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
    }

    Batch Add(Batch b) { AddChild(b); return b; }


    /// <summary>An item's own model (the photographs', Ui/ItemModels) as one
    /// mesh to draw many of: its parts merged, each keeping its material (or
    /// only the parts whose material `keep` wants), centred, `size` across at
    /// its largest.</summary>
    static Mesh Pickup(string key, float size, Func<Material, bool>? keep = null) => Merge(ItemModels.Make(key)?.Model, size, keep);

    /// <summary>A weapon as the survivor holds it (Arms), as one mesh, its
    /// length along +Y.</summary>
    static Mesh Weapon(string id, float size) => Merge(Arms.Make(id), size, null);

    static Mesh Merge(Node3D? model, float size, Func<Material, bool>? keep)
    {
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
        // Lights share: each one already lit dims the next, so a crowd's worth of
        // blows lights the pale dead no brighter than a few (they washed to cream).
        int lit = 0;
        foreach (var f in flashes) if (f.T < 0.5f) lit++;
        peak /= 1 + 0.6f * lit;
        // A light lit beside her lights her most of all: a champion falling at her elbow burned
        // her white through every effect's hero_clear. Her own moments (lit where she stands)
        // keep their light; the rest fade out within four metres of her.
        float near = new Vector2(at.X - PlayerPos.X, at.Z - PlayerPos.Z).Length();
        if (near > 0.4f) peak *= Mathf.Lerp(0.15f, 1, Mathf.SmoothStep(1, 4, near));
        int best = 0;
        for (int i = 1; i < flashes.Count; i++) if (flashes[i].Light.LightEnergy < flashes[best].Light.LightEnergy) best = i;
        var l = flashes[best].Light;
        l.Position = at;
        l.LightColor = color;
        l.OmniRange = range;
        l.Visible = true;
        flashes[best] = (l, 0, life, peak);
    }

    /// <summary>A chest bursting open (ChestCeremony): its light up out of it in a column, a
    /// fountain of glints, a ring thrown across the ground (never a filled disc). A richer chest
    /// throws more of each.</summary>
    public void ChestBurst(Vector3 at, Color color, int count)
    {
        float k = count >= 5 ? 1.5f : count >= 3 ? 1.2f : 1f;
        Flash(at + Vector3.Up * 1.4f, color, 12 * k, 0.7f, 10);
        // (Short and soft: the reels rise through it, and a long white column hid them and the plaque.)
        Pillar(at, 6 * k, 0.26f * k, color * 0.45f, 0.6f);
        Waves.Add(at + Vector3.Up * 0.3f, 4 * k, 0.55f, color, 0.6f);
        for (int i = 0; i < (int)(46 * k); i++)
        {
            float a = R() * Mathf.Tau, out_ = 0.4f + R() * 1.6f;
            bool glint = i % 3 == 0;
            Sparks.Spawn(at + new Vector3(Mathf.Cos(a) * 0.25f, 0.45f, Mathf.Sin(a) * 0.25f), new Vector3(Mathf.Cos(a) * out_, 4 + R() * 5 * k, Mathf.Sin(a) * out_),
                1.1f + R() * 0.8f, glint ? 0.26f : 0.09f, new Color(2.6f, 2.0f, 1.1f), new Color(2.2f, 0.7f, 0.15f), 0.02f, 4, 1.2f,
                sprite: glint ? Sprites.Of("star") : 0, spinV: 3);
        }
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
        m.Length = 0;
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
            m.Fill.Modulate = color with { A = 0.42f };
            m.Fill.EmissionEnergy = 1.4f;
            m.Fill.Size = new Vector3(0.01f, 4, 0.01f);
            m.Fill.Visible = true;
        }
        if (key is int k2) keyed[k2] = m;
    }

    /// <summary>A lane on the ground; a hostile one fills from where the blow comes to its end as it
    /// comes (as a circle fills from its heart), so a charge reads as coming and when, and never as
    /// one more line on the ground (two edges alone read as the story places' burning edge).</summary>
    void Lane(double x0, double z0, double x1, double z1, float width, Color color, float life, int? key = null, bool progress = false)
    {
        if (key is int k && keyed.TryGetValue(k, out var old)) { old.Active = false; old.Decal.Visible = false; if (old.Fill != null) old.Fill.Visible = false; }
        double dx = x1 - x0, dz = z1 - z0, len = Math.Max(0.5, Math.Sqrt(dx * dx + dz * dz));
        var m = Ground((x0 + x1) / 2, (z0 + z1) / 2, 1, laneTex!, color, life);
        m.Decal.Size = new Vector3(width, 4, (float)len);
        m.Decal.Rotation = new Vector3(0, (float)Math.Atan2(dx, dz), 0);
        if (progress)
        {
            m.Progress = true;
            m.From = V(x0, heightAt(x0, z0), z0);
            m.Along = new Vector3((float)(dx / len), 0, (float)(dz / len));
            m.Length = (float)len;
            m.Radius = width / 2;
            if (m.Fill == null) { m.Fill = new Decal { UpperFade = 0.3f, LowerFade = 0.3f, CullMask = 1 }; AddChild(m.Fill); }
            m.Fill.TextureEmission = laneFillTex;
            m.Fill.Modulate = color with { A = 0.42f };
            m.Fill.EmissionEnergy = 1.4f;
            m.Fill.Rotation = m.Decal.Rotation;
            m.Fill.Position = m.From;
            m.Fill.Size = new Vector3(width * 0.94f, 4, 0.01f);
            m.Fill.Visible = true;
        }
        if (key is int k2) keyed[k2] = m;
    }

    /// <summary>A ring that races out from a point and fades.</summary>
    /// <summary>Each school's burst, filmed (Flipbooks).</summary>
    static string BlastOf(School s) => s switch
    {
        School.Fire => "fire_blast", School.Frost => "frost_burst", School.Storm => "storm_strike", School.Nature => "nature_burst",
        School.Arcane => "arcane_burst", School.Holy => "holy_burst", School.Shadow => "shadow_burst", _ => "dust_ring",
    };

    /// <summary>A school's burst on the ground, `radius` across at its
    /// height, with what it throws up: false if there is no atlas for it
    /// yet (the caller draws what it drew before).</summary>
    /// <summary>How bright each school's burst is drawn: fire hot enough to
    /// bloom, the pale ones (frost, lightning, light) held back so their
    /// cores keep their detail rather than burning to white.</summary>
    static float GlowOf(School s) => s switch
    {
        School.Fire => 1.3f, School.Shadow => 1.6f, School.Nature => 1.35f, School.Arcane => 1.0f,
        School.Frost => 0.7f, School.Storm => 1.15f, School.Holy => 1.05f, _ => 1f,
    };

    /// <summary>What each school leaves on the ground, and for how long.</summary>
    static (string Mark, float Size, float Life, float Spin) ScarOf(School s) => s switch
    {
        School.Fire => ("scorch", 0.7f, 9, 0), School.Frost => ("frost", 0.55f, 6, 0), School.Storm => ("scorch", 0.45f, 6, 0),
        School.Holy => ("sigil", 0.75f, 1.6f, 0.5f), School.Shadow => ("blight", 0.55f, 6, 0), School.Nature => ("roots", 0.75f, 3, 0),
        School.Arcane => ("runes", 0.75f, 1.6f, -0.7f), _ => ("crack", 0.65f, 9, 0),
    };

    /// <summary>A school's blow landing on the ground, in the layers a blast
    /// is made of: a white-hot flash for a few frames, the air thrown out
    /// (a ring that bends the picture), the burst itself (filmed), what it
    /// throws (embers, shards, sparks, motes, clods), smoke or mist rising
    /// after, its light, and the mark it leaves. `radius` is the reach of the
    /// blow. A light blast (a weapon's pulse, every few seconds) is the burst
    /// and what it throws only: the flash, the light and the mark are for the
    /// blows that should stop the eye. False if the school has no filmed
    /// burst yet (the caller draws what it drew before).</summary>
    /// <summary>For finding which layer of a blast draws what: FX_LAYERS, a
    /// set of letters (f flash, w wave, b burst, d debris, s smoke, l light,
    /// m mark); unset, all of them.</summary>
    static readonly string FxLayers = System.Environment.GetEnvironmentVariable("FX_LAYERS") ?? "fwbdslm";
    static bool On(char layer) => FxLayers.Contains(layer);

    public bool Blast(double x, double z, School school, float radius, float life = 0.9f, float glow = -1, bool light = false)
    {
        if (!Flipbooks.Has(BlastOf(school))) return false;
        if (glow < 0) glow = GlowOf(school);
        float gy = Y(x, z), r = radius;
        var pal = Palette.Of(school);
        var ground = V(x, gy, z);
        // A short blow is short in every layer: its light and its dust gone with it.
        bool brief = life <= 0.65f;

        if (light)
        {
            var lt = school == School.Fire ? new Color(glow * 0.7f, glow * 0.45f, glow * 0.22f, 0.8f) : new Color(glow * 0.7f, glow * 0.7f, glow * 0.7f, 0.8f);
            Books.Spawn(BlastOf(school), ground + Vector3.Up * 0.55f, r * 1.1f, life * 0.8f, lt, flat: true, sizeEnd: r * 2.1f);
            for (int i = 0; i < 6; i++)
            {
                float a = R() * Mathf.Tau, v = r * (1 + R() * 2);
                Sparks.Spawn(ground + Vector3.Up * 0.5f, new Vector3(Mathf.Cos(a) * v, 1 + R() * 2, Mathf.Sin(a) * v), 0.4f + R() * 0.3f, 0.06f, pal.Core, pal.Glow, 0.02f, 2, 2);
            }
            return true;
        }
        // The instant: brighter than anything else in the frame, gone in a breath.
        // Fire's is yellow-hot, never white: a white instant over the pale dead read as a cream disc.
        bool fire = school == School.Fire;
        if (On('f')) Sparks.Spawn(ground + Vector3.Up * 0.9f, Vector3.Zero, 0.07f, r * (fire ? 0.3f : 0.4f), fire ? new Color(1.9f, 0.95f, 0.22f) : new Color(1.8f, 1.7f, 1.6f), pal.Glow * 0.4f, r * (fire ? 0.6f : 0.8f), alpha: fire ? 0.7f : 0.8f);
        // The air thrown out.
        if (On('w')) Waves.Add(ground + Vector3.Up * 0.35f, r * 1.7f, 0.35f, pal.Glow, school == School.Holy ? 0.6f : 1);
        // The burst, flat on the ground and above the grass.
        var tint = school == School.Frost ? new Color(glow * 0.8f, glow * 0.92f, glow * 1.15f, 1)
            // Fire's heart held to yellow (its filmed white core, tinted warm-pale, bloomed cream).
            : fire ? new Color(glow * 1.0f, glow * 0.6f, glow * 0.3f, 1) : new Color(glow, glow, glow, 1);
        if (On('b')) Books.Spawn(BlastOf(school), ground + Vector3.Up * 0.55f, r * 1.2f, life, tint, flat: true, sizeEnd: r * 2.4f);
        // What it throws.
        int n = On('d') ? Math.Min(48, 12 + (int)(r * 8)) : 0;
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, v = r * (1.5f + R() * 3.5f);
            var out_ = new Vector3(Mathf.Cos(a) * v, 0, Mathf.Sin(a) * v);
            var from = ground + Vector3.Up * 0.5f;
            switch (school)
            {
                case School.Fire:
                    Sparks.Spawn(from, out_ + Vector3.Up * (3 + R() * 5), 0.5f + R() * 0.7f, 0.06f + R() * 0.06f, new Color(2.6f, 1.2f, 0.3f), new Color(1.4f, 0.25f, 0.05f), 0.02f, 9, 1.5f);
                    break;
                case School.Frost:
                    Sparks.Spawn(from, out_ + Vector3.Up * (2 + R() * 4), 0.45f + R() * 0.4f, 0.07f + R() * 0.07f, new Color(1.3f, 1.7f, 2.2f), new Color(0.5f, 0.8f, 1.4f), 0.03f, 14, 1.2f, sprite: Sprites.Of("star"), spinV: 6);
                    break;
                case School.Storm:
                    Sparks.Spawn(from, out_ * 1.8f + Vector3.Up * (1 + R() * 3), 0.18f + R() * 0.2f, 0.05f, new Color(1.6f, 2f, 2.8f), new Color(0.6f, 0.9f, 2f), 0.01f, 4, 3);
                    break;
                case School.Holy or School.Nature or School.Arcane:
                    Sparks.Spawn(from + out_ * 0.1f, out_ * 0.25f + Vector3.Up * (1.5f + R() * 2.5f), 0.9f + R() * 0.8f, 0.07f + R() * 0.06f, pal.Core, pal.Glow, 0.02f, -0.6f, 1.6f);
                    break;
                case School.Shadow:
                    Sparks.Spawn(from, out_ * 0.6f + Vector3.Up * (1 + R() * 2), 0.6f + R() * 0.5f, 0.07f, pal.Core, pal.Dim, 0.02f, 2, 2);
                    break;
                default:
                    Smoke.Spawn(from, out_ * 0.8f + Vector3.Up * (3 + R() * 4), 0.7f + R() * 0.3f, 0.12f + R() * 0.12f, new Color("#4a3a2a"), gravity: 14, sprite: Sprites.Of("dirt"), spinV: 4);
                    break;
            }
        }
        // What hangs in the air after.
        if (!On('s')) { }
        else if (school is School.Fire or School.Physical or School.Shadow)
        {
            // Thin and soon gone: smoke that lingers hides the next fight.
            // Steel's dust is the ground's brown, not tan: tan puffs over the pale dead read as cream.
            // Fire's smoke is char-dark and soon gone: grey, lit by the blast and the lights round
            // it, it hung a pale haze over her for a second and a half.
            var smoke = school == School.Shadow ? new Color(0.5f, 0.35f, 0.7f, 0.5f) : school == School.Physical ? new Color(0.42f, 0.34f, 0.26f, 0.38f) : new Color(0.17f, 0.14f, 0.13f, 0.45f);
            for (int i = 0; i < 4; i++)
                Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r * 0.6f, 0.6f + R() * 0.4f, (R() - 0.5f) * r * 0.6f), new Vector3((R() - 0.5f) * 0.6f, 0.8f + R() * 0.6f, (R() - 0.5f) * 0.6f), brief ? 0.5f + R() * 0.15f : fire ? 0.8f + R() * 0.4f : 1.2f + R() * 0.6f, r * 0.35f, smoke, smoke * 0.6f, r * 0.8f, drag: 1.2f, alpha: smoke.A);
        }
        else if (school == School.Frost)
            for (int i = 0; i < (brief ? 1 : 3); i++)
                Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r * 0.8f, 0.4f, (R() - 0.5f) * r * 0.8f), new Vector3(0, 0.25f, 0), 1.4f, r * 0.4f, new Color(0.75f, 0.85f, 1f), new Color(0.6f, 0.7f, 0.9f), r * 0.9f, drag: 1.5f, alpha: 0.18f);
        // Its light.
        // (Fire's light halved: an orange light at full strength lit the pale dead round it cream.)
        if (On('l')) Flash(ground + Vector3.Up * 1.4f, pal.Light, (fire ? 6 : 12) * glow, brief ? 0.15f : 0.3f + r * 0.04f, fire ? r * 2.4f + 3 : r * 3 + 4);
        // And what it leaves behind.
        var (mark, size, last, spin) = ScarOf(school);
        if (On('m')) Scars.Add(mark, ground, r * size, last, spin);
        return true;
    }

    /// <summary>A strike from the sky arriving: a thin hot pillar, its
    /// school's burst on the ground, and the light of it.</summary>
    void Land(double x, double z, School school, Vector3 at, float r, Palette.Hues pal)
    {
        Pillar(at, 16, 0.18f + r * 0.05f, pal.Core, 0.18f);
        Blast(x, z, school, Mathf.Max(1.2f, r), 0.6f);
        Flash(at + Vector3.Up * 2, pal.Light, 8, 0.25f, 10);
    }

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
                // A blow coming, filling as it comes: a bright front at its edge and a sparse hatch behind
                // it, so the crowd still reads through (a solid fill hid the fight).
                else if (kind == 1) a = r < 0.97f ? 0.08f + (Mathf.PosMod((u - v) * 6f, 1f) < 0.22f ? 0.2f : 0) + 0.72f * Mathf.SmoothStep(0.8f, 0.95f, r) : Mathf.Clamp((1 - r) / 0.03f, 0, 1);
                else if (kind == 2) { float e = Mathf.Abs(u); a = (Mathf.Clamp(1 - Mathf.Abs(e - 0.88f) / 0.08f, 0, 1) + (e < 0.86f ? (Mathf.PosMod((u + v * 4) * 5f, 1f) < 0.25f ? 0.28f : 0.06f) : 0)) * Mathf.Clamp((1 - Mathf.Abs(v)) / 0.05f, 0, 1); }
                // This ground stays bad: hatched, with its edge.
                else if (kind == 3) a = r < 0.97f ? (Mathf.PosMod((u + v) * 7f, 1f) < 0.3f ? 0.38f : 0.08f) + Mathf.Clamp(1 - Mathf.Abs(r - 0.92f) / 0.05f, 0, 1) : 0;
                // Stand here: a dashed ring.
                else if (kind == 4) a = Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.06f, 0, 1) * (Mathf.PosMod(Mathf.Atan2(v, u) / Mathf.Tau * 24f, 1f) < 0.55f ? 1 : 0) + (r < 0.9f ? 0.1f : 0);
                // A lane's fill, run out along it as the blow comes: as a circle's, a bright front at
                // its leading end (both ends: the one under the foe is hidden) and only a breath behind.
                else if (kind == 6) a = Mathf.Clamp((0.9f - Mathf.Abs(u)) / 0.12f, 0, 1) * Mathf.Clamp((1 - Mathf.Abs(v)) / 0.03f, 0, 1)
                    * (0.06f + 0.8f * Mathf.SmoothStep(0.84f, 0.96f, Mathf.Abs(v)));
                // This will be solid: a hard, thick edge.
                else a = (r < 0.97f ? 0.2f : 0) + Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.09f, 0, 1);
                a = Mathf.Clamp(a, 0, 1);
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return ImageTexture.CreateFromImage(img);
    }

    /// <summary>A cone pointing along the texture's v, apex at the centre, `arc` degrees wide.</summary>
    static Texture2D ConeTexture(int arc)
    {
        if (coneTex.TryGetValue(arc, out var t)) return t;
        const int N = 192;
        float half = arc * Mathf.Pi / 360f;
        var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v), ang = Mathf.Abs(Mathf.Atan2(u, v));
                float a = 0;
                // Eased at its sides and its rim, so a wide cone has no steps along them.
                float inside = Mathf.Clamp((half - ang) * r / 0.016f + 0.5f, 0, 1) * Mathf.Clamp((0.97f - r) / 0.016f + 0.5f, 0, 1);
                if (inside > 0)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.07f, 0, 1), Mathf.Clamp(1 - Mathf.Abs(half - ang) * r / 0.05f, 0, 1));
                    a = (0.18f + 0.82f * edge) * inside;
                }
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return coneTex[arc] = ImageTexture.CreateFromImage(img);
    }

    /// <summary>A band: the ground between two circles filled, edged at both, and the
    /// inside left clear (the inside is where to stand; two rings with a wash over the
    /// whole disc said the opposite).</summary>
    static Texture2D BandTexture(int innerPct)
    {
        if (bandTex.TryGetValue(innerPct, out var t)) return t;
        const int N = 192;
        float inner = innerPct / 100f * 0.97f, outer = 0.97f;
        var img = Image.CreateEmpty(N, N, false, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float u = (x + 0.5f) / N * 2 - 1, v = (y + 0.5f) / N * 2 - 1;
                float r = Mathf.Sqrt(u * u + v * v), a = 0;
                // Its edges eased over a texel and a half, or a band ten paces across shows steps.
                float inside = Mathf.Clamp((r - inner) / 0.016f + 0.5f, 0, 1) * Mathf.Clamp((outer - r) / 0.016f + 0.5f, 0, 1);
                if (inside > 0)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - Mathf.Abs(r - inner) / 0.035f, 0, 1), Mathf.Clamp(1 - Mathf.Abs(outer - r) / 0.035f, 0, 1));
                    a = (0.3f + 0.7f * edge) * inside;
                }
                img.SetPixel(x, y, new Color(a, a, a, a));
            }
        return bandTex[innerPct] = ImageTexture.CreateFromImage(img);
    }

    void BandMark(double x, double z, double inner, float outer, Color color, float life, int? key = null)
    {
        if (key is int k && keyed.TryGetValue(k, out var old)) { old.Active = false; old.Decal.Visible = false; if (old.Fill != null) old.Fill.Visible = false; }
        int pct = (int)Math.Round(Math.Clamp(inner / Math.Max(0.01, outer), 0, 0.95) * 20) * 5;
        var m = Ground(x, z, outer, BandTexture(pct), color, life);
        if (key is int k2) keyed[k2] = m;
    }

    /// <summary>A cone on the ground from (x, z), pointing at `angle` (radians, in the plane), `radius` long.</summary>
    void ConeMark(double x, double z, float radius, double angle, double arc, Color color, float life, int? key = null)
    {
        if (key is int k && keyed.TryGetValue(k, out var old)) { old.Active = false; old.Decal.Visible = false; }
        var m = Ground(x, z, radius, ConeTexture((int)Math.Round(arc * 180 / Math.PI / 5) * 5), color, life);
        m.Decal.Rotation = new Vector3(0, (float)Math.Atan2(Math.Cos(angle), Math.Sin(angle)), 0);
        if (key is int k2) keyed[k2] = m;
    }

    /// <summary>A mark's colour lifted for its word: the ground's tint is dim by design, the word must read over a crowd.</summary>
    static Color WordColour(Color c)
    {
        var h = c with { A = 1 };
        float m = Mathf.Max(h.R, Mathf.Max(h.G, h.B));
        return m < 1.4f ? new Color(h.R / Mathf.Max(0.01f, m) * 1.4f, h.G / Mathf.Max(0.01f, m) * 1.4f, h.B / Mathf.Max(0.01f, m) * 1.4f) : h;
    }

    /* ------------------------------------------------------------- events -- */

    /// <summary>Critical bursts in the last breath (a crowd of crits is told by a few).</summary>
    double critBurstAt = -1;
    int critBursts;

    public void Handle(IReadOnlyList<CombatEvent> events, Battle b)
    {
        b0 = b;
        hitBudget = 28;
        killBudget = 6;
        rose = false;
        foreach (var ev in events)
        {
            switch (ev)
            {
                case Ev.Hit e:
                {
                    var at = V(e.X, Y(e.X, e.Z) + 1.0, e.Z);
                    if (e.Dot)
                    {
                        // Summed per body per beat like the blows, in the colour of what is doing it.
                        var dc = Palette.Of(e.School).Glow;
                        float dm = Mathf.Max(dc.R, Mathf.Max(dc.G, dc.B));
                        Hits.Tally(e.Target, at, e.Amount, e.MaxHp, false, new Color(dc.R / dm * 1.1f, dc.G / dm * 1.1f, dc.B / dm * 1.1f, 0.9f));
                        break;
                    }
                    if (e.Blocked)
                    {
                        if (time - lastBlocked > 0.35) { lastBlocked = time; Hits.Text(at, "blocked", new Color(0.7f, 0.75f, 0.8f), 44); }
                        Burst(at, School.Physical, 5, 3, 2, 0.06f);
                        break;
                    }
                    Hits.Tally(e.Target, at, e.Amount, e.MaxHp, e.Crit);
                    if (e.Art != null) Impact(e, at);
                    else Burst(at, e.School, e.Crit ? 10 : 4, e.Crit ? 5 : 3, size: e.Crit ? 0.12f : 0.08f);
                    if (e.Family != null)
                    {
                        var away = new Vector3((float)e.Dx, 0, (float)e.Dz);
                        if (away.LengthSquared() < 0.01f) away = Vector3.Forward;
                        Gore.Hit(at + Vector3.Up * 0.2f, e.Amount, e.MaxHp, View.Gore.Of(e.Family, e.Def ?? ""), e.Family == Family.Undead, away.Normalized(), e.Crit);
                    }
                    // A critical's burst: warm gold under the tone curve's knee (white-hot, a crowd of
                    // crits bloomed white round her), three at most in a breath, and small at her elbow.
                    if (e.Crit && (time - critBurstAt > 0.15 || critBursts < 3))
                    {
                        if (time - critBurstAt > 0.15) { critBurstAt = time; critBursts = 0; }
                        critBursts++;
                        double dx = e.X - b.Player.X, dz = e.Z - b.Player.Z;
                        float near = dx * dx + dz * dz < 9 ? 0.6f : 1f;
                        if (!Books.Spawn("sparks", at, 0.7f * near, 0.3f, new Color(1f, 0.8f, 0.48f) * new Color(1, 1, 1, near), sizeEnd: 1.2f * near))
                            Sparks.Spawn(at, Vector3.Zero, 0.22f * near, 1.1f, Palette.Of(e.School).Core, sizeEnd: 0.25f, sprite: Sprites.Of("star"), spinV: 4);
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
                    // A crowd cut down at once is told by its first few deaths in a frame; the
                    // rest fall with their gore alone (every death's burst of light together
                    // read as one cream blob over the crowd). What steel kills throws bone
                    // and grit, not light.
                    bool told = e.Elite || e.Boss || killBudget-- > 0;
                    if (told)
                    {
                        if (e.School == School.Physical)
                            for (int i = 0; i < (e.Elite ? 18 : 6); i++)
                                Smoke.Spawn(at, new Vector3((R() - 0.5f) * 5, 2 + R() * 3, (R() - 0.5f) * 5), 0.6f + R() * 0.3f, 0.06f + R() * 0.05f,
                                    new Color("#bfb6a2"), gravity: 12, sprite: Sprites.Of("dirt"), spinV: 6);
                        else Burst(at, e.School, e.Elite ? 30 : 7, e.Elite ? 7 : 4, 3, life: 0.5f);
                        for (int i = 0; i < (e.Elite ? 12 : 3); i++)
                            Sparks.Spawn(V(e.X + (R() - 0.5) * 0.6, gy + 0.5, e.Z + (R() - 0.5) * 0.6), new Vector3(0, 1.4f + R() * 1.5f, 0), 0.8f + R() * 0.5f, 0.06f,
                                new Color(2.2f, 0.9f, 0.25f), new Color(1.4f, 0.25f, 0.05f), 0.02f, 0, 0.8f);
                    }
                    // The dry dead's bone dust, the grey of old bone and few (pale and six to a death, every
                    // kill on the dead hung a cream cloud over the crowd, and sixty falling to one blow a
                    // snow of white specks): told by the first few too.
                    if (e.Family == Family.Undead)
                        for (int i = 0; i < (told ? 4 : 1); i++) Smoke.Spawn(V(e.X, gy + 0.6, e.Z), new Vector3((R() - 0.5f) * 3, 2 + R() * 2, (R() - 0.5f) * 3), 0.7f, 0.14f, new Color("#7e776b"), gravity: 11, sprite: Sprites.Of("dirt"), spinV: 3);
                    Smoke.Spawn(V(e.X, gy + 0.3, e.Z), new Vector3(0, 0.5f, 0), 0.9f, 0.5f, new Color("#3a3430"), new Color("#1a1816"), 1.3f, alpha: 0.35f);
                    if (e.Elite || e.Boss)
                    {
                        // A champion's fall is brief and no wider than its body's reach (the experience
                        // director's rule: about 3 m, a flash under 0.15 s, the dust down in 0.6 s, never
                        // bigger than a level-up). A boss's is the fall's (Ev.Victory): its light and rings,
                        // with no flat blast of its own under them (one fourteen metres across filled the peak).
                        // Champions falling together are told by the first: the rest burst light and
                        // small (eight full blasts at once washed the whole crowd white).
                        bool first = e.Boss || time - lastFall > 0.3;
                        if (first) lastFall = time;
                        Flash(V(e.X, gy + 1.5, e.Z), pal.Light, e.Boss ? 16 : first ? 10 : 4, e.Boss ? 0.6f : 0.15f, e.Boss ? 12 : 8);
                        if (e.Boss) Waves.Add(V(e.X, gy + 0.5, e.Z), 7, 0.5f, pal.Glow, 0.8f);
                        // (A burst's reach is its radius, its picture 2.4 times that across: at 2 it was
                        // nearly five metres of colour, the rule's three is 1.3.)
                        else if (!Blast(e.X, e.Z, e.School, first ? 1.3f : 0.9f, 0.55f, 0.8f, light: !first)) Nova(e.X, e.Z, 3, pal.Glow, 0.45f);
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
                    // Poison or burning in the survivor: a quieter number in its own colour, no shake.
                    if (e.Dot)
                    {
                        Hits.Text(at + Vector3.Up * 0.2f, ((int)Math.Round(e.Amount)).ToString(), e.School == School.Fire ? new Color(1.8f, 0.8f, 0.25f) : new Color(0.7f, 1.6f, 0.35f), 40);
                        OnDamageFlash(0.18f);
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
                case Ev.Nova e when e.Art != null && Pulse(e):
                    break;
                case Ev.Nova e:
                {
                    var pal = Palette.Of(e.School);
                    if (!Blast(e.X, e.Z, e.School, (float)e.Radius * 0.9f, (float)Math.Max(0.5, e.Duration * 1.5), 1f, light: true)) Nova(e.X, e.Z, (float)e.Radius, pal.Glow, (float)Math.Max(0.25, e.Duration));
                    if ((e.Rings ?? 1) > 0) Flash(V(e.X, Y(e.X, e.Z) + 1.3, e.Z), pal.Light, 6, 0.35f, (float)e.Radius * 2);
                    break;
                }
                case Ev.Rise e:
                    Rise(e);
                    break;
                // The rise's fire is drawn by the rise (a ring going out from her), not as a blast.
                case Ev.Explosion { School: School.Fire, Art: null } when rose:
                    break;
                case Ev.Explosion e:
                {
                    float gy = Y(e.X, e.Z), r = (float)e.Radius;
                    var pal = Palette.Of(e.School);
                    Cam?.AddTrauma((float)Math.Min(0.3, 0.05 + e.Power * 0.1));
                    if (e.School == School.Physical && e.Art == null) Slammed(e.X, e.Z, r);
                    if (Blast(e.X, e.Z, e.School, r, 0.8f + r * 0.08f)) break;
                    Flash(V(e.X, gy + 1.2, e.Z), pal.Light, 10 + (float)e.Power * 10, 0.35f, r * 3 + 3);
                    Nova(e.X, e.Z, r * 1.15f, pal.Glow, 0.3f);
                    int n = Math.Min(40, 10 + (int)Math.Round(r * 8));
                    for (int i = 0; i < n; i++)
                    {
                        float a = R() * Mathf.Tau, v = r * (2 + R() * 3);
                        Sparks.Spawn(V(e.X, gy + 0.6, e.Z), new Vector3(Mathf.Cos(a) * v, 2 + R() * 4, Mathf.Sin(a) * v), 0.4f + R() * 0.4f, 0.1f + R() * 0.08f, pal.Core, pal.Glow, 0.01f, 8, 2.5f);
                    }
                    if (!Flipbooks.Has(BlastOf(e.School))) Sparks.Spawn(V(e.X, gy + 0.8, e.Z), Vector3.Zero, 0.3f, r * 1.3f, pal.Core, pal.Glow, r * 2.2f, alpha: 0.9f, sprite: Sprites.Of("fire"), spinV: 1.5f);
                    if (e.School is School.Fire or School.Shadow or School.Physical)
                        for (int i = 0; i < 6; i++) Smoke.Spawn(V(e.X + (R() - 0.5) * r, gy + 0.5, e.Z + (R() - 0.5) * r), new Vector3(0, 1 + R(), 0), 1.2f, r * 0.4f, new Color("#2a2420"), new Color("#121010"), r * 0.9f, drag: 1.2f, alpha: 0.45f);
                    break;
                }
                case Ev.Chain e when Leap(e):
                    break;
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
                case Ev.Beam e when Lance(e):
                    break;
                case Ev.Beam e:
                {
                    var pal = Palette.Of(e.School);
                    float y = Y(e.X0, e.Z0) + 1.0f;
                    Band(V(e.X0, y, e.Z0), V(e.X1, y, e.Z1), (float)e.Width * 0.3f, pal.Glow, (float)Math.Max(0.15, e.Duration));
                    Flash(V((e.X0 + e.X1) / 2, y, (e.Z0 + e.Z1) / 2), pal.Light, 6, (float)e.Duration, 12);
                    break;
                }
                case Ev.Strike e when e.Art != null && Fall(e):
                    break;
                case Ev.Strike e:
                {
                    float gy = Y(e.X, e.Z);
                    var pal = Palette.Of(e.School);
                    var at = V(e.X, gy, e.Z);
                    float r = (float)e.Radius;
                    if (e.Delay > 0.05)
                    {
                        Ring(e.X, e.Z, r, pal.Glow * 0.6f, (float)e.Delay, true);
                        pending.Add((time + e.Delay, () => Land(e.X, e.Z, e.School, at, r, pal)));
                    }
                    else Land(e.X, e.Z, e.School, at, r, pal);
                    break;
                }
                case Ev.Muzzle e:
                    Release(e);
                    break;
                case Ev.Slash e when e.Art != null:
                    Swing(e);
                    break;
                case Ev.Slash e:
                {
                    var pal = Palette.Of(e.School);
                    mirror = !mirror;
                    Hits.Arc(V(e.X, Y(e.X, e.Z) + 1.0, e.Z), (float)(Math.PI / 2 - e.Angle), (float)e.Reach, 0.22f, mirror, pal.Core, pal.Glow);
                    break;
                }
                case Ev.Telegraph e:
                {
                    if (DigMark(e)) break;
                    var col = e.Hostile ? Palette.Telegraph(e.Kind) : e.Faction is { } pf ? People(pf) : Palette.Of(School.Holy).Glow;
                    // A crowd's marks are held near the ground's own lit value (the arena lead's rule: a
                    // stop over it at most): at full strength the Dig's lamplings' bombs burned cream
                    // rings over the dark clay. A boss's marks a little stronger.
                    // A named move (its name shown over whoever makes it) is one to read, whoever makes it:
                    // a boss's strength (the Hollow's drive was drawn at the crowd's, and read as the place's edge).
                    if (e.Hostile) { float k = e.Boss || e.Label is { Length: > 0 } ? 0.5f : 0.28f; col = new Color(col.R * k, col.G * k, col.B * k, col.A); }
                    if (!e.Hostile && e.Faction is { } rf && e.Shape == TelegraphShape.Ring) Rally(e, col);
                    else if (e.Hostile && e.Faction is { } sf && e.Kind == TelegraphKind.Ground && e.Id == -1 && e.Shape == TelegraphShape.Circle) Summoning(e, People(sf));
                    else if (e.Shape == TelegraphShape.Line) Lane(e.X, e.Z, e.X1 ?? e.X, e.Z1 ?? e.Z, (float)(e.Width ?? 1), col, (float)e.Duration, e.Id, e.Hostile && e.Kind == TelegraphKind.Blow);
                    else if (e.Shape == TelegraphShape.Cone) ConeMark(e.X, e.Z, (float)e.Radius, e.Angle ?? 0, e.Arc ?? Math.PI / 2, col, (float)e.Duration, e.Id);
                    else if (e.Shape == TelegraphShape.Ring) BandMark(e.X, e.Z, e.Inner, (float)e.Radius, col, (float)e.Duration, e.Id);
                    else if (e.Hostile && e.Kind != TelegraphKind.Blow)
                    {
                        if (keyed.TryGetValue(e.Id, out var old)) { old.Active = false; old.Decal.Visible = false; if (old.Fill != null) old.Fill.Visible = false; }
                        var tex = e.Kind == TelegraphKind.Ground ? hatchTex! : e.Kind == TelegraphKind.Safe ? dashTex! : wallTex!;
                        keyed[e.Id] = Ground(e.X, e.Z, (float)e.Radius, tex, col, (float)e.Duration);
                    }
                    else Ring(e.X, e.Z, (float)e.Radius, col, (float)e.Duration, true, e.Id);
                    // A boss's move, named over the boss for as long as its mark stands: who is doing
                    // it, where the eye already is (over the mark, it sat on the survivor's head).
                    if (e.Label is { Length: > 0 } label)
                    {
                        double lx = e.ByX ?? e.X, lz = e.ByZ ?? e.Z;
                        Hits.Word(V(lx, Y(lx, lz) + 4.4, lz), label.ToUpperInvariant(), WordColour(col), 70, (float)Math.Min(2.5, e.Duration + 0.3));
                    }
                    break;
                }
                case Ev.Break br:
                {
                    // A phase broken past its mark: the surplus as one big number.
                    // High over the boss and alone: the moves' names it would sit among are put away.
                    var at = V(br.X, Y(br.X, br.Z) + 5.2, br.Z);
                    Hits.ClearWords();
                    Hits.Word(at, $"BREAK {Math.Round(br.Amount):N0}", new Color(2.4f, 1.9f, 0.6f), 104, 2.4f);
                    Flash(at, new Color("#ffd46a"), 8, 0.5f, 9);
                    Cam?.AddTrauma(0.35f);
                    break;
                }
                case Ev.Drop d:
                    Dropped(d);
                    break;
                case Ev.Spawn e:
                {
                    float gy = Y(e.X, e.Z);
                    if (e.Style == SpawnStyle.Rise && e.Def.EndsWith("_ally", StringComparison.Ordinal)) { Raised(e); break; }
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
                    if (!Blast(p.X, p.Z, School.Holy, 2.2f, 1.1f, 0.9f)) Nova(p.X, p.Z, 3.6f, Palette.Of(School.Fire).Glow, 0.5f);
                    Pillar(p, 7, 0.3f, Palette.Of(School.Holy).Core * 0.6f, 0.45f);
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
                case Ev.Victory v:
                {
                    // The night's peak, in layers (it plays in the fall's slow motion, so it
                    // lingers): a white-gold flash that lights the field, a column of the ember
                    // leaving what ruled it, three shockwaves (rings, never a filled disc), embers rising
                    // slowly, a dark ring of dust thrown out, and the camera's biggest kick.
                    float gy = Y(v.X, v.Z);
                    var at = V(v.X, gy, v.Z);
                    var gold = new Color(2.6f, 1.9f, 1.0f);
                    Flash(at + Vector3.Up * 3, new Color("#ffe6b0"), 42, 1.8f, 28);
                    Pillar(at, 34, 1.1f, gold * 0.8f, 1.6f);
                    Pillar(at, 22, 0.35f, new Color(3, 2.8f, 2.4f), 0.9f);
                    Waves.Add(at + Vector3.Up * 0.4f, 9, 0.7f, gold, 1);
                    Waves.Add(at + Vector3.Up * 0.6f, 15, 1.1f, new Color(2.2f, 1.2f, 0.5f), 0.8f);
                    Waves.Add(at + Vector3.Up * 0.8f, 22, 1.6f, new Color(1.6f, 0.8f, 0.4f), 0.5f);
                    for (int i = 0; i < 90; i++)
                    {
                        float a = R() * Mathf.Tau, d = R() * 2.2f;
                        bool glint = i % 3 == 0;
                        Sparks.Spawn(at + new Vector3(Mathf.Cos(a) * d, 0.4f + R() * 1.5f, Mathf.Sin(a) * d), new Vector3(Mathf.Cos(a) * (0.6f + R()), 2.5f + R() * 5, Mathf.Sin(a) * (0.6f + R())),
                            1.6f + R() * 1.4f, glint ? 0.28f : 0.1f, new Color(2.6f, 1.6f, 0.5f), new Color(2.0f, 0.5f, 0.1f), 0.02f, -0.4f, 0.7f, sprite: glint ? Sprites.Of("star") : 0, spinV: 2);
                    }
                    for (int i = 0; i < 16; i++)
                    {
                        float a = i / 16f * Mathf.Tau;
                        Smoke.Spawn(at + new Vector3(Mathf.Cos(a) * 1.5f, 0.4f, Mathf.Sin(a) * 1.5f), new Vector3(Mathf.Cos(a) * 9, 0.6f, Mathf.Sin(a) * 9), 1.4f, 1.2f,
                            new Color("#3a3430"), new Color("#1a1816"), 2.4f, alpha: 0.4f);
                    }
                    Cam?.AddTrauma(0.6f);
                    break;
                }
                case Ev.Evolve { Chest: true }: break;
                case Ev.Evolve:
                {
                    // It clicked: gold light down on her and two rings thrown out across the crowd,
                    // in the world's slowed breath (WorldScene.Slow). Rings and light, never a filled
                    // disc: the pink one nine metres across hid her at her best moment.
                    var p = PlayerPos;
                    var gold = new Color(2.6f, 2.0f, 1.0f);
                    Flash(p + Vector3.Up * 2, new Color("#ffe6b0"), 24, 1.0f, 14);
                    Pillar(p, 12, 0.45f, gold * 0.75f, 1.0f);
                    Waves.Add(p + Vector3.Up * 0.4f, 6, 0.5f, gold, 0.9f);
                    Waves.Add(p + Vector3.Up * 0.6f, 10, 0.8f, new Color(2.2f, 1.3f, 0.5f), 0.6f);
                    for (int i = 0; i < 40; i++)
                    {
                        float a = R() * Mathf.Tau;
                        bool glint = i % 3 == 0;
                        Sparks.Spawn(p + new Vector3(Mathf.Cos(a) * 0.6f, 0.3f, Mathf.Sin(a) * 0.6f), new Vector3(Mathf.Cos(a) * 1.2f, 3 + R() * 5, Mathf.Sin(a) * 1.2f), 1.2f, glint ? 0.28f : 0.09f,
                            new Color(2.6f, 2.0f, 1.1f), new Color(2.2f, 0.7f, 0.15f), 0.02f, 2, 1.2f, sprite: glint ? Sprites.Of("star") : 0, spinV: 3);
                    }
                    Cam?.AddTrauma(0.3f);
                    break;
                }
                case Ev.Discovery:
                {
                    // A pair that quietly does more: a breath of light on her, no more.
                    Flash(PlayerPos + Vector3.Up * 2, new Color("#ffe0ff"), 10, 0.5f, 9);
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
                {
                    // Her dash: one streak of cold air where she went, thinning to its start, and dust
                    // kicked up at her heels (fourteen soft spots in a row read as a string of pearls).
                    var path = new Vector3[6];
                    var widths = new float[6];
                    for (int i = 0; i < 6; i++)
                    {
                        float t = i / 5f;
                        double x = e.X0 + (e.X1 - e.X0) * t, z = e.Z0 + (e.Z1 - e.Z0) * t;
                        path[i] = V(x, Y(x, z) + 0.75 + 0.15 * t, z);
                        widths[i] = Mathf.SmoothStep(0, 1, t) * (1 - 0.3f * Mathf.Max(0, t - 0.8f) / 0.2f);
                    }
                    Ribbons.Line(path, 0.55f, 0.28f, new Color(0.42f, 0.55f, 0.95f), 1.1f, Ribbons.Style.Wisp, widths);
                    for (int i = 0; i < 5; i++)
                    {
                        float t = (i + 0.5f) / 5f;
                        double x = e.X0 + (e.X1 - e.X0) * t, z = e.Z0 + (e.Z1 - e.Z0) * t;
                        Smoke.Spawn(V(x, Y(x, z) + 0.15, z), new Vector3((R() - 0.5f) * 0.6f, 0.4f, (R() - 0.5f) * 0.6f), 0.55f, 0.3f, new Color("#4a4038"), sizeEnd: 0.75f, alpha: 0.3f);
                    }
                    break;
                }
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
        frameDt = fdt;
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
                if (m.Progress && m.Fill != null && m.Length > 0)
                {
                    // A lane's fill runs out along it, its front reaching the end as the blow lands.
                    float l = Mathf.Max(0.01f, m.Length * m.T);
                    var mid = m.From + m.Along * (l / 2);
                    m.Fill.Position = new Vector3(mid.X, (float)heightAt(mid.X, mid.Z), mid.Z);
                    m.Fill.Size = new Vector3(m.Radius * 2 * 0.94f, 4, l);
                }
                else if (m.Progress && m.Fill != null) { float r = m.Radius * m.T; m.Fill.Size = new Vector3(r * 2, 4, r * 2); }
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
        bossUp = false;
        foreach (var e in b.Enemies.Living()) if (e.Boss) { bossUp = true; break; }
        Zones(b, now);
        ArtTrails(b, fdt);
        StepRise(b, fdt);
        StepDig(fdt);
        Projectiles(b, fdt, now);
        Pickups(b, now);
        StepFronts(fdt);
        Blades.Step(fdt);
        Hits.Flush(b0 is { } hb ? V(hb.Player.X, Y(hb.Player.X, hb.Player.Z) + 1.0, hb.Player.Z) : null);
        StepSpikes(fdt);
        Ribbons.Step(fdt, GetViewport()?.GetCamera3D());
        Sparks.Step(fdt);
        Books.Step(fdt);
        Scars.Step(fdt);
        Waves.Step(fdt);
        Smoke.Step(fdt);
        Gore.Step(fdt);
    }

    float artT;
    /// <summary>A boss is up: her own grounds are drawn at half (the eye goes to his marks).</summary>
    bool bossUp;

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
    readonly HashSet<int> zonesAlive = new();
    readonly List<int> zonesGone = new();

    void Zones(Battle b, double now)
    {
        var alive = zonesAlive;
        alive.Clear();
        foreach (var z in b.Zones.Living())
        {
            alive.Add(z.Id);
            if (z.Owner != Sim.Side.Enemy && SkillGround(z, now)) continue;
            var school = Palette.OfArt(z.Art);
            // The enemy's ground is the danger language's "this ground stays bad": violet and hatched,
            // held toward the ground's own lit value (red, it was her colour and loud on the Dig's clay).
            var col = z.Owner == Sim.Side.Enemy ? Palette.TeleGround * 0.28f : Palette.Of(school).Glow * 0.5f;
            // Hallowed and arcane ground is a turning circle of runes, burning
            // ground a spread of fire; the rest, and the enemy's, a glow.
            bool mine = z.Owner != Sim.Side.Enemy, runes = mine && school is School.Holy or School.Arcane;
            if (!zoneMarks.TryGetValue(z.Id, out var m) || !m.Active)
            {
                var tex = !mine ? hatchTex! : school switch { School.Holy => Premul(Sprites.Runes(0)), School.Arcane => Premul(Sprites.Runes(0)), School.Fire => Premul(Sprites.Burning), _ => discTex! };
                m = Ground(z.X, z.Z, (float)z.Radius, tex, col, 1e6f, runes ? 2.2f : 1.2f);
                zoneMarks[z.Id] = m;
            }
            m.T = 0;
            if (runes) m.Decal.Rotation = new Vector3(0, (float)(now * 0.3 + z.Id), 0);
            m.Decal.Position = V(z.X, heightAt(z.X, z.Z), z.Z);
            m.Decal.Size = new Vector3((float)z.Radius * 2, 4, (float)z.Radius * 2);
            float fade = (float)Math.Min(1, Math.Min(z.Age / 0.2, (z.Life - z.Age) / 0.4));
            // Faded in its colour (a decal's emission ignores alpha).
            m.Decal.Modulate = Dim(col, Mathf.Max(0, fade) * (0.85f + 0.15f * Mathf.Sin((float)now * 3 + z.Id)));
            if (R() < 0.3f)
            {
                float a = R() * Mathf.Tau, d = (float)z.Radius * Mathf.Sqrt(R());
                var pal = Palette.Of(school);
                double x = z.X + Mathf.Cos(a) * d, zz = z.Z + Mathf.Sin(a) * d;
                Sparks.Spawn(V(x, Y(x, zz) + 0.1, zz), new Vector3(0, 0.8f + R(), 0), 0.8f, 0.07f, z.Owner == Sim.Side.Enemy ? Palette.TeleGround * 0.6f : pal.Glow, pal.Dim, 0.01f, drag: 1);
            }
        }
        var gone = zonesGone;
        gone.Clear();
        foreach (var (id, m) in zoneMarks) if (!alive.Contains(id)) { m.Active = false; m.Decal.Visible = false; gone.Add(id); }
        foreach (var id in gone) zoneMarks.Remove(id);
        GroundsGone(alive);
    }

    void Projectiles(Battle b, float dt, double now)
    {
        shades.Begin(); orbs.Begin(); steel.Begin(); axes.Begin(); daggers.Begin(); shards.Begin(); rings.Begin(); chakrams.Begin(); kegs.Begin(); herdCrowd?.Begin();
        Buffs(b);
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
            // Lifted to head height: from above, the bodies it passes through would hide it.
            if (!hostile && Flight(p, at + Vector3.Up * 0.55f, heading, now, dt)) continue;
            if (hostile && HostileFlight(p, at + Vector3.Up * 0.3f, heading, (float)now)) continue;
            if (art.StartsWith("axe", StringComparison.Ordinal))
            {
                // Laid flat and whirling about its middle, as an axe thrown to spin.
                var basis = new Godot.Basis(Vector3.Up, -(float)(now * 16 + p.Id)) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2) * Godot.Basis.FromScale(Vector3.One * 1.3f);
                axes.Add(new Transform3D(basis, at), hostile ? new Color(0.6f, 0.5f, 0.45f) : Colors.White);
                trail = 0.45f;
            }
            else if (art.StartsWith("dagger", StringComparison.Ordinal))
            {
                // Point first along its flight, turning a little about its length.
                var basis = new Godot.Basis(Vector3.Up, heading) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2) * new Godot.Basis(Vector3.Up, (float)(now * 9 + p.Id));
                daggers.Add(new Transform3D(basis, at), hostile ? new Color(0.6f, 0.5f, 0.45f) : Colors.White);
                trail = 0.35f;
            }
            else if (art.StartsWith("arrow", StringComparison.Ordinal) || art == "bolt_bone")
            {
                var basis = new Godot.Basis(Vector3.Up, heading);
                steel.Add(new Transform3D(basis, at), hostile ? new Color(0.5f, 0.42f, 0.36f) : new Color(0.75f, 0.72f, 0.68f));
                trail = 0.3f;
            }
            else if (art.StartsWith("disc", StringComparison.Ordinal) || art.StartsWith("chakram", StringComparison.Ordinal))
            {
                float s = art.StartsWith("disc", StringComparison.Ordinal) ? 1.1f : 0.8f;
                rings.Add(new Transform3D(new Godot.Basis(Vector3.Up, (float)(now * 16)).Scaled(Vector3.One * s), at), pal.Glow * 0.5f);
                trail = 0.5f;
            }
            else if (art.StartsWith("shard", StringComparison.Ordinal) || art == "spear_ice")
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
                float size = art is "mote" or "mote_cascade" or "mote_star" or "ember_seeker" ? 0.34f : art is "star" ? 1.0f : art is "cinder" or "living_flame" ? 0.7f : art.StartsWith("herd", StringComparison.Ordinal) ? 0.6f : art.StartsWith("crescent", StringComparison.Ordinal) ? 1.0f : 0.5f;
                var core = hostile ? Palette.HostileRim : pal.Core;
                // A small hot core in a wider, faint halo: a big bright core
                // only blooms into a featureless disc that hides the fight.
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * size * 0.6f), at), core);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * size * 2f), at), (hostile ? Palette.HostileDanger : pal.Glow) * 0.18f);
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
        shades.End(); orbs.End(); steel.End(); axes.End(); daggers.End(); shards.End(); rings.End(); chakrams.End(); kegs.End(); herdCrowd?.End();
    }

    // Ember by worth, kept saturated: orange, amber, gold, a cold blue for the rare great stone, and
    // the hoard stone's deep red (Battle.Hoard). Their glow is these at about 1.3 at most: past the
    // tone curve's knee every hue folds to cream, and a field of stones read as popcorn.
    static readonly Color[] EmberTiers = { new(1.3f, 0.42f, 0.08f), new(1.3f, 0.72f, 0.14f), new(1.25f, 1.0f, 0.24f), new(0.25f, 0.62f, 1.35f), new(1.35f, 0.16f, 0.12f) };
    // (An array made for each ember on the ground every frame was most of what the effects threw away.)
    static readonly float[] EmberSizes = { 0.16f, 0.21f, 0.27f, 0.34f, 0.5f };

    void Pickups(Battle b, double now)
    {
        embers.Begin(); coins.Begin(); flasks.Begin(); lodestones.Begin(); sacks.Begin(); chests.Begin(); BeginLoot();
        foreach (var p in b.Pickups.Living())
        {
            float gy = Y(p.X, p.Z);
            float bob = Mathf.Sin((float)(now * 3 + p.Id)) * 0.08f;
            var spin = new Godot.Basis(Vector3.Up, (float)(now * 2.2 + p.Id));
            switch (p.Kind)
            {
                case PickupKind.Ember:
                {
                    int tier = Math.Clamp(p.Tier, 0, 4);
                    float s = EmberSizes[tier];
                    if (tier == 4)
                    {
                        // The hoard stone: bigger, beating like a heart, with a red beam to find it by.
                        s *= 1 + 0.12f * Mathf.Sin((float)now * 5);
                        Column(p.X, gy, p.Z, 4.5f, 0.2f, StoriedRed, 0.7f);
                    }
                    embers.Add(new Transform3D(spin.Scaled(Vector3.One * s), V(p.X, gy + 0.45 + bob, p.Z)), EmberTiers[tier]);
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
                    // What the item filter hides lies unlit and dark: the world stays honest, the eye is spared.
                    bool hidden = p.Look == Verdict.Hidden;
                    if (p.Kind == PickupKind.Chest) chests.Add(new Transform3D(lie, V(p.X, gy + chestUp, p.Z)), Colors.White);
                    else sacks.Add(new Transform3D(lie.Scaled(Vector3.One * (hidden ? 0.7f : 1f)), V(p.X, gy + sackUp, p.Z)), hidden ? new Color(0.35f, 0.33f, 0.3f) : Colors.White);
                    if (hidden) break;
                    // Loot rolled whole carries its tier (docs/design/LOOT_DESIGN.md §8.1): the light's
                    // height says how rare, its colour the band (BattleFx.Loot).
                    LootLight(p, gy, now, col);
                    break;
                }
            }
        }
        embers.End(); coins.End(); flasks.End(); lodestones.End(); sacks.End(); chests.End(); EndLoot();
    }
}

using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.View;

/// <summary>
/// What a hit looks like: a spray of blood (GPU particles), the number, and
/// the blade's arc (blood on the ground is Gore's). Pools, reused oldest
/// first.
/// </summary>
public partial class Hits : Node3D
{
    readonly List<GpuParticles3D> sprays = new();
    readonly List<(Label3D Label, float T)> numbers = new();
    readonly List<(MeshInstance3D Mesh, ShaderMaterial Mat, float T, float Life)> arcs = new();
    /// <summary>A boss's words: its moves' names and the BREAK. Their own few, held as long as
    /// the mark they name: in the numbers' pool, a fast build's hits took them in a frame.</summary>
    readonly List<(Label3D Label, float T, float Life, Vector3 At)> words = new();
    int nextSpray, nextNumber, nextArc, nextWord;
    readonly RandomNumberGenerator rng = new() { Seed = 5 };

    public override void _Ready()
    {
        var droplet = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.PerPixel, AlbedoColor = new Color("#5a0a08"), Roughness = 0.25f,
            BillboardMode = BaseMaterial3D.BillboardModeEnum.Particles, VertexColorUseAsAlbedo = true,
        };
        var dropMesh = new SphereMesh { Radius = 0.035f, Height = 0.07f, RadialSegments = 6, Rings = 3, Material = droplet };
        for (int i = 0; i < 14; i++)
        {
            var p = new ParticleProcessMaterial
            {
                Direction = Vector3.Up, Spread = 55, InitialVelocityMin = 2.2f, InitialVelocityMax = 5.5f,
                Gravity = new Vector3(0, -14, 0), ScaleMin = 0.6f, ScaleMax = 1.6f,
                Color = new Color("#6a0c0a"),
                CollisionMode = ParticleProcessMaterial.CollisionModeEnum.HideOnContact,
            };
            var g = new GpuParticles3D { Amount = 26, Lifetime = 0.9, OneShot = true, Explosiveness = 0.92f, Emitting = false, ProcessMaterial = p, DrawPass1 = dropMesh, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(g);
            sprays.Add(g);
        }
        for (int i = 0; i < 48; i++)
        {
            var l = new Label3D
            {
                Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true, FontSize = 64, OutlineSize = 14,
                PixelSize = 0.006f, Modulate = new Color(1f, 0.95f, 0.85f), OutlineModulate = new Color(0.08f, 0.03f, 0.02f), Visible = false,
                Shaded = false, RenderPriority = 10, OutlineRenderPriority = 9,
            };
            AddChild(l);
            numbers.Add((l, 1));
        }
        for (int i = 0; i < 8; i++)
        {
            var l = new Label3D
            {
                Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true, FontSize = 64, OutlineSize = 18,
                PixelSize = 0.006f, OutlineModulate = new Color(0.06f, 0.02f, 0.01f), Visible = false,
                Shaded = false, RenderPriority = 12, OutlineRenderPriority = 11,
            };
            if (UiFont() is { } font) l.Font = font;
            AddChild(l);
            words.Add((l, 1, 1, Vector3.Zero));
        }
        var shader = GD.Load<Shader>("res://shaders/slash.gdshader");
        for (int i = 0; i < 10; i++)
        {
            var mat = new ShaderMaterial { Shader = shader };
            var m = new MeshInstance3D { Mesh = ArcMesh(1.6f), MaterialOverride = mat, Visible = false, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(m);
            arcs.Add((m, mat, 1, 1));
        }
    }

    /// <summary>A flat band round a quarter circle and more, in XZ, facing +Z
    /// at its middle; scaled and turned per swing.</summary>
    static ArrayMesh ArcMesh(float arc)
    {
        const int Segs = 24;
        var verts = new List<Vector3>(); var uvs = new List<Vector2>(); var idx = new List<int>();
        for (int i = 0; i <= Segs; i++)
        {
            float u = (float)i / Segs, a = -arc / 2 + arc * u;
            float lift = Mathf.Sin(u * Mathf.Pi) * 0.25f;
            verts.Add(new Vector3(Mathf.Sin(a) * 0.4f, lift * 0.4f, Mathf.Cos(a) * 0.4f)); uvs.Add(new Vector2(u, 0));
            verts.Add(new Vector3(Mathf.Sin(a) * 1.02f, lift, Mathf.Cos(a) * 1.02f)); uvs.Add(new Vector2(u, 1));
            if (i < Segs) { int b = i * 2; idx.AddRange(new[] { b, b + 1, b + 2, b + 1, b + 3, b + 2 }); }
        }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts.ToArray();
        arrays[(int)Mesh.ArrayType.TexUV] = uvs.ToArray();
        arrays[(int)Mesh.ArrayType.Index] = idx.ToArray();
        var m = new ArrayMesh();
        m.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return m;
    }

    static readonly Color Blood = new("#6a0c0a");

    /// <summary>Blood thrown from a wound (dust from the dry dead: `color`).</summary>
    public void Spray(Vector3 at, Vector3 away, Color? color = null, float amount = 1)
    {
        var g = sprays[nextSpray++ % sprays.Count];
        g.GlobalPosition = at;
        var pm = (ParticleProcessMaterial)g.ProcessMaterial;
        pm.Direction = (away + Vector3.Up * 1.2f).Normalized();
        pm.Color = color ?? Blood;
        g.AmountRatio = Mathf.Clamp(amount, 0.2f, 1);
        g.Restart();
        g.Emitting = true;
    }

    public void Number(Vector3 at, int amount, bool crit) =>
        Text(at, crit ? $"{amount}!" : amount.ToString(), crit ? new Color(1.6f, 1.15f, 0.4f) : new Color(1, 0.94f, 0.86f), crit ? 88 : 60);

    /// <summary>The boss's words now showing put away (the BREAK is said alone).</summary>
    public void ClearWords()
    {
        for (int i = 0; i < words.Count; i++)
        {
            var (l, t, life, at) = words[i];
            if (t < 1) { l.Visible = false; words[i] = (l, 1, life, at); }
        }
    }

    /// <summary>A boss's word over its mark: steady for `life` seconds, then gone in a breath.</summary>
    public void Word(Vector3 at, string text, Color color, int size, float life)
    {
        int i = nextWord++ % words.Count;
        var l = words[i].Label;
        l.Text = text;
        l.FontSize = size;
        l.Modulate = color;
        l.GlobalPosition = at;
        l.Visible = true;
        words[i] = (l, 0, Mathf.Max(0.6f, life), at);
    }

    /// <summary>A move's name over a foe near the top of the screen is brought down to stand just
    /// under the HUD's top stack (it was printed over the clock and the kill count).</summary>
    Vector3 UnderTheBars(Vector3 p)
    {
        var cam = GetViewport()?.GetCamera3D();
        if (cam == null || cam.IsPositionBehind(p)) return p;
        var sp = cam.UnprojectPosition(p);
        float clear = SurvivorUnchained.Ui.GameHud.TopClear + 34;
        if (sp.Y >= clear) return p;
        float depth = (p - cam.GlobalPosition).Dot(-cam.GlobalTransform.Basis.Z);
        return cam.ProjectPosition(new Vector2(sp.X, clear), depth);
    }

    /// <summary>The interface's heavy face, so a move's name reads as the HUD does.</summary>
    static Font? UiFont() => SurvivorUnchained.Ui.Style.UiHeavy;

    /// <summary>A word or number that rises from where something happened and fades.</summary>
    public void Text(Vector3 at, string text, Color color, int size = 60) => Show(at, text, color, size);

    /// <summary>As Text, saying which of the pool's labels it took.</summary>
    int Show(Vector3 at, string text, Color color, int size)
    {
        int i = nextNumber++ % numbers.Count;
        Untally(i);
        var l = numbers[i].Label;
        l.Text = text;
        l.FontSize = size;
        l.Modulate = color;
        l.GlobalPosition = at + new Vector3(rng.RandfRange(-0.3f, 0.3f), 0, 0);
        l.Visible = true;
        numbers[i] = (l, 0);
        return i;
    }

    /// <summary>The blade's arc round `at`, facing `facing`, sweeping over
    /// `life` seconds.</summary>
    public void Arc(Vector3 at, float facing, float reach, float life = 0.22f, bool mirror = false, Color? core = null, Color? glow = null)
    {
        int i = nextArc++ % arcs.Count;
        var (m, mat, _, _) = arcs[i];
        static Vector3 V(Color c) => new(c.R, c.G, c.B);
        mat.SetShaderParameter("core", V(core ?? new Color(2.2f, 2.03f, 1.72f)));
        mat.SetShaderParameter("glow", V(glow ?? new Color(1.4f, 0.97f, 0.49f)));
        m.GlobalPosition = at;
        m.Basis = new Basis(Vector3.Up, facing).Scaled(new Vector3(mirror ? -reach : reach, reach, reach));
        m.Visible = true;
        mat.SetShaderParameter("head", 0f);
        mat.SetShaderParameter("seed", rng.Randf() * 100);
        arcs[i] = (m, mat, 0, life);
    }

    public override void _Process(double delta)
    {
        StepTally(delta);
        float dt = (float)delta;
        for (int i = 0; i < numbers.Count; i++)
        {
            var (l, t) = numbers[i];
            if (t >= 1) continue;
            t += dt / 0.75f;
            l.Position += Vector3.Up * dt * 1.4f * (1 - t);
            var c = l.Modulate; c.A = t < 0.7f ? 1 : 1 - (t - 0.7f) / 0.3f; l.Modulate = c;
            l.OutlineModulate = new Color(l.OutlineModulate, c.A);
            if (t >= 1) l.Visible = false;
            numbers[i] = (l, t);
        }
        for (int i = 0; i < words.Count; i++)
        {
            var (l, t, life, at) = words[i];
            if (t >= 1) continue;
            t += dt / life;
            // In quickly, a slow lift while it holds, out over its last fifth.
            float a = Mathf.Min(1, t * life / 0.12f) * (t < 0.8f ? 1 : 1 - (t - 0.8f) / 0.2f);
            l.GlobalPosition = UnderTheBars(at + Vector3.Up * 0.35f * t);
            var c = l.Modulate; c.A = a; l.Modulate = c;
            l.OutlineModulate = new Color(l.OutlineModulate, a);
            if (t >= 1) l.Visible = false;
            words[i] = (l, t, life, at);
        }
        for (int i = 0; i < arcs.Count; i++)
        {
            var (m, mat, t, life) = arcs[i];
            if (t >= 1) continue;
            t += dt / life;
            mat.SetShaderParameter("head", Mathf.Min(1.1f, t / 0.55f));
            mat.SetShaderParameter("alpha", 1 - Mathf.Max(0, (t - 0.5f) * 2));
            if (t >= 1) m.Visible = false;
            arcs[i] = (m, mat, t, life);
        }
    }
}

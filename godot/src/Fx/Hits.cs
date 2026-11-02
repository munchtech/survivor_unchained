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
    // (Names made once, not a new one every frame for the collector.)
    static readonly StringName HeadName = "head", AlphaName = "alpha";
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
                Billboard = BaseMaterial3D.BillboardModeEnum.Enabled, NoDepthTest = true, FontSize = 64, OutlineSize = NumOutline,
                PixelSize = NumPixel, Modulate = new Color(1f, 0.95f, 0.85f), OutlineModulate = new Color(0.08f, 0.03f, 0.02f), Visible = false,
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

    /// <summary>A floater that would print over a dropped item's name is lifted to stand just above it (UI note 5, 26 Oct).</summary>
    static int liftShots;
    Vector3 ClearOfNames(Vector3 at, string text, int size)
    {
        var names = SurvivorUnchained.Ui.GroundLabels.Drawn;
        var cam = GetViewport()?.GetCamera3D();
        if (names.Count == 0 || cam == null || cam.IsPositionBehind(at)) return at;
        var p = cam.UnprojectPosition(at);
        float w = Mathf.Max(50, text.Length * size * 0.4f), h = size * 0.8f;
        bool moved = false;
        for (int pass = 0; pass < 3; pass++)
        {
            var f = new Rect2(p.X - w / 2, p.Y - h / 2, w, h);
            var hit = names.Find(r => r.Grow(4).Intersects(f));
            if (hit.Size == Vector2.Zero) break;
            p.Y = hit.Position.Y - 6 - h / 2;
            moved = true;
        }
        if (!moved) return at;
        if (liftShots < 3 && Args.Has("shot")) Shots.Want($"floaterlift_{++liftShots}", 0.1);
        float depth = (at - cam.GlobalPosition).Dot(-cam.GlobalBasis.Z);
        return cam.ProjectPosition(p, depth);
    }

    /// <summary>The Drowned Girl's HUD top at screen x (1080 px): her figure's head over its span, her hair's river
    /// 880 to the first seat, 955 across the seats, 915 at the eddy; null where nothing of the HUD stands.</summary>
    public static float? HudTop(float x, float figL, float figR, float figTop, float seatL, float seatR, float keepL, float keepR, float keepTop = 875)
    {
        if (x >= figL && x <= figR) return Mathf.Min(818, figTop);
        if (x > figR && x < seatL) return 880;
        if (x >= seatL && x <= seatR) return 955;
        if (x > seatR && x < keepL) return 955;
        if (x >= keepL && x <= keepR) return keepTop;
        return null;
    }

    /// <summary>The highest (smallest y) HUD top over a span of screen x, both in 1080 design px, sampled at its ends,
    /// its middle and every 40 px between, with the live HUD (her figure's fade rect, the seats, the keeper);
    /// null where no part of the HUD stands under the span or the HUD isn't up. Shared by numbers and barks.</summary>
    public static float? HudTopOver(float x0, float x1)
    {
        if (SurvivorUnchained.Ui.LifeLamp.Live?.FadeRect is not Rect2 f) return null;
        float seatL = SurvivorUnchained.Ui.DgPanel.Rect.Position.X, seatR = SurvivorUnchained.Ui.DgPanel.Rect.End.X;
        var kr = SurvivorUnchained.Ui.DgPanel.KeeperRect; float kt = SurvivorUnchained.Ui.DgPanel.KeeperTop;
        float? top = null;
        int n = Mathf.Max(2, Mathf.CeilToInt((x1 - x0) / 40f));
        for (int i = 0; i <= n; i++)
            if (HudTop(x0 + (x1 - x0) * i / n, f.Position.X, f.End.X, f.Position.Y, seatL, seatR, kr.Position.X, kr.End.X, kt) is float t) top = top is float o ? Mathf.Min(o, t) : t;
        return top;
    }

    static int hudShots;
    const int NumOutline = 14;
    const float NumPixel = 0.006f;

    /// <summary>A number restyled (a tally's text or size grew: a crit at 80-98 from the 60 it was placed at) kept
    /// clear of the HUD again at its new size (UI 20: crits were placed as an empty 60 px box, then grew over the hair).</summary>
    void Reclear(int i)
    {
        var l = numbers[i].Label;
        if (l.Visible) l.GlobalPosition = AboveHud(l.GlobalPosition, l.Text, l.FontSize);
    }
    /// <summary>The Drowned Girl (UI 17): a number's box keeps its bottom 8 px above the HUD's top at its x.</summary>
    Vector3 AboveHud(Vector3 at, string text, int size)
    {
        var fig = SurvivorUnchained.Ui.LifeLamp.Live?.FadeRect;
        var cam = GetViewport()?.GetCamera3D();
        if (fig == null || cam == null || cam.IsPositionBehind(at)) return at;
        float k = GetViewport().GetVisibleRect().Size.Y / 1080f;
        var p = cam.UnprojectPosition(at);
        // (UI 20: the box from the label's real size on screen at its depth, its outline included: a font px is
        // PixelSize metres, so a crit's 98 at the play camera is ~2x the 60 the old guess took for every number)
        float em = (cam.UnprojectPosition(at + cam.GlobalBasis.Y * (size + 2 * NumOutline) * NumPixel) - p).Length();
        float h = em * 0.8f;
        // (the box's width is its text's: checked across all of it)
        float w = Mathf.Max(em * 0.8f, text.Length * em * 0.6f);
        float top = HudTopOver((p.X - w / 2) / k, (p.X + w / 2) / k) is float ht ? ht * k : float.MaxValue;
        if (top == float.MaxValue || p.Y + h / 2 <= top - 8) return at;
        float to = top - 8 - h / 2;
        if (hudShots++ < 12) GD.Print($"hits: number '{text}' size {size} ({h:0} px tall) at y {p.Y:0} (bottom {p.Y + h / 2:0}) lifted to {to:0}, HUD top {top:0}");
        float depth = (at - cam.GlobalPosition).Dot(-cam.GlobalBasis.Z);
        return cam.ProjectPosition(new Vector2(p.X, to), depth);
    }

    /// <summary>As Text, saying which of the pool's labels it took.</summary>
    int Show(Vector3 at, string text, Color color, int size)
    {
        int i = nextNumber++ % numbers.Count;
        Untally(i);
        var l = numbers[i].Label;
        l.Text = text;
        l.FontSize = size;
        l.Modulate = color;
        at = ClearOfNames(at + new Vector3(rng.RandfRange(-0.3f, 0.3f), 0, 0), text, size);
        at = AboveHud(at, text, size);
        l.GlobalPosition = at;
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
            mat.SetShaderParameter(HeadName, Mathf.Min(1.1f, t / 0.55f));
            mat.SetShaderParameter(AlphaName, 1 - Mathf.Max(0, (t - 0.5f) * 2));
            if (t >= 1) m.Visible = false;
            arcs[i] = (m, mat, t, life);
        }
    }
}

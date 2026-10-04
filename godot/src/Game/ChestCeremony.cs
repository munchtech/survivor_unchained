using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.Sound;
using SurvivorUnchained.Ui;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Play;

/// <summary>
/// A chest opened in a fight, as the genre's jackpot (docs/feel/SUGGESTIONS.md, S-09), staged in
/// the world rather than on a page: the world is held still round her and darkens at the edges,
/// the camera comes in, the chest swells, turns to face us and shakes with light leaking from its
/// seam; the lid is thrown back on a column of light, and what is inside comes out spinning like
/// reels that stop one by one, each landing a step further up the score's ladder. An evolution
/// lands first, in gold, held a breath longer. Then each thing flies home to its place on the bar
/// and the night goes on. Any key brings everything down at once; a second key closes it. From
/// the third ordinary chest of a night the opening runs quicker, so the twentieth still pleases.
/// </summary>
public partial class ChestCeremony : Control
{
    readonly ChestOpened c;
    readonly Battle b;
    readonly WorldScene scene;
    readonly FollowCamera cam;
    readonly GameHud hud;
    readonly Haptics haptics;
    readonly Vector3 at;
    readonly float lie;
    readonly double speed;
    readonly int count;
    readonly bool gold;

    Node3D chest = null!;
    Node3D? lid;
    OmniLight3D light = null!;
    StandardMaterial3D seamMat = null!, mouthMat = null!;
    TextureRect shade = null!;
    Control kicker = null!, hint = null!;
    readonly List<Reel> reels = new();
    readonly List<string> pool = new();
    Vector3? savedFocus;
    float savedDistance, near;

    /// <summary>The opening's own clock (quicker from the third chest), and the real one.</summary>
    double t, real;
    bool burst, skipped, closing;
    double closeAt, closeT;
    public bool Done { get; private set; }

    const double Shake = 0.55, FlyOut = 0.32, FirstReel = 0.9, NextReel = 0.35, EvoHold = 0.4, Outro = 0.4;
    static readonly Color Gilt = new("#ffd88a");

    sealed class Reel
    {
        public required ChestItem It;
        public required Medallion M;
        public required Control Plate;
        public required Shine Ring;
        public float Size;
        public double Out, Land, NextTurn;
        public bool Landed;
        public int Turn;
        public Vector2 Pos;
    }

    public ChestCeremony(ChestOpened c, Battle b, WorldScene scene, FollowCamera cam, GameHud hud, Haptics haptics)
    {
        this.c = c;
        this.b = b;
        this.scene = scene;
        this.cam = cam;
        this.hud = hud;
        this.haptics = haptics;
        count = c.Items.Count;
        at = new Vector3((float)c.X, (float)scene.HeightAt(c.X, c.Z), (float)c.Z);
        lie = c.Seed * 2.4f;
        gold = c.Items.Any(i => i.Kind == ChestItemKind.Evolution);
        speed = c.Opened >= 3 && c.Hoard == null && count < 5 ? 1.7 : 1;
        Style.Fill(this);
        MouseFilter = MouseFilterEnum.Ignore;
    }

    /// <summary>The colour a thing reads in: an evolution gold, a combat skill its school's, a
    /// passive its rarity's.</summary>
    static Color ColourOf(ChestItem it) => it.Kind switch
    {
        ChestItemKind.Evolution => Gilt,
        ChestItemKind.Rank when it.School is School s => ItemViews.SchoolColors[s],
        ChestItemKind.Gold => Style.Gold,
        _ => Style.RarityOf((int)it.Rarity),
    };

    static string DetailOf(ChestItem it) => it.Kind switch
    {
        ChestItemKind.Evolution => it.Before != null ? $"{it.Before} evolves" : "Evolution",
        ChestItemKind.Rank => it.From <= 0 ? "New" : $"Rank {it.From} to {it.To}",
        ChestItemKind.Passive => it.From <= 0 ? "New passive" : $"Rank {it.From} to {it.To}",
        _ => "Coin, and breath back",
    };

    public override void _Ready()
    {
        BuildChest();
        // The edges of the world go dark round the chest: the eye goes where the light is.
        shade = new TextureRect
        {
            ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale, MouseFilter = MouseFilterEnum.Ignore,
            Texture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(0, 0, 0, 0), new Color(0, 0, 0, 0.05f), new Color(0.02f, 0.01f, 0.03f, 0.6f), new Color(0.02f, 0.01f, 0.03f, 0.82f) }, Offsets = new[] { 0f, 0.14f, 0.42f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1f, 0.5f), Width = 256, Height = 256,
            },
            Size = new Vector2(3000, 3000), Modulate = Colors.Transparent,
        };
        AddChild(shade);
        // What the reels turn through: what she carries, and what came out.
        foreach (var w in b.Weapons) pool.Add(w.Art);
        foreach (var (id, r) in b.Boons) if (r > 0 && Content.Boons.Find(id) is { } bd) pool.Add(bd.Icon);
        foreach (var it in c.Items) pool.Add(it.Icon);
        foreach (var w in Content.Weapons.All.Values.Take(8)) pool.Add(w.Art);
        pool.RemoveAll(string.IsNullOrEmpty);
        // The reels, spinning out of the chest at the burst and stopping one by one.
        float size = count > 5 ? 88 : 104;
        double land = Shake + 0.25 + FirstReel;
        for (int i = 0; i < count; i++)
        {
            var it = c.Items[i];
            float s = it.Kind == ChestItemKind.Evolution ? size + 26 : size;
            var m = new Medallion((int)s, "", pool[i % pool.Count]) { Ring = Style.GoldDim, Ink = new Color("#e8dcc4"), Core = new Color("#1c1410"), Visible = false };
            m.Size = new Vector2(s, s);
            m.PivotOffset = new Vector2(s / 2, s / 2);
            var ring = new Shine { Size = new Vector2(s * 3, s * 3), Colour = ColourOf(it) };
            var plate = Plate(it, count > 5 ? 160 : 190);
            plate.Modulate = Colors.Transparent;
            AddChild(ring);
            AddChild(m);
            AddChild(plate);
            reels.Add(new Reel { It = it, M = m, Plate = plate, Ring = ring, Size = s, Out = Shake + i * 0.05, Land = land });
            land += NextReel + (it.Kind == ChestItemKind.Evolution ? EvoHold : 0);
        }
        string title = c.Hoard ?? (count >= 5 ? "A hoard" : count >= 3 ? "A rich chest" : "A chest");
        kicker = new Plaque(title, count >= 5 || c.Hoard != null ? 34 : 28, count >= 5 ? 120 : 80, gold ? Gilt : Style.GoldHi) { Modulate = Colors.Transparent };
        AddChild(kicker);
        hint = Style.Hint(Act.Confirm, "Skip");
        hint.Modulate = Colors.Transparent;
        AddChild(hint);
        // The camera in on it; the world held round her.
        savedFocus = cam.FocusOverride;
        savedDistance = cam.TargetDistance;
        cam.FocusOverride = at + Vector3.Up * 0.4f;
        near = Math.Min(savedDistance, count >= 5 || c.Hoard != null ? 13.5f : 12);
        cam.TargetDistance = near;
        Sfx.ChestShake(Shake / speed, Total / speed + Outro);
    }

    /// <summary>When the last reel stops, and how long the whole is held after.</summary>
    double LastLand => reels.Count > 0 ? reels[^1].Land : Shake + 0.6;
    double Total => LastLand + (count >= 5 || c.Hoard != null ? 1.8 : count >= 3 ? 1.3 : 0.9);

    static Control Plate(ChestItem it, float width)
    {
        var col = ColourOf(it);
        var v = Style.V(2);
        v.CustomMinimumSize = new Vector2(width, 0);
        v.Size = new Vector2(width, 60);
        var name = Style.Label(it.Name, Style.Display, it.Kind == ChestItemKind.Evolution ? 22 : 19, it.Kind == ChestItemKind.Evolution ? Gilt : Style.GoldHi, true, HorizontalAlignment.Center);
        name.CustomMinimumSize = new Vector2(width, 0);
        v.AddChild(name);
        var detail = Style.Label(DetailOf(it).ToUpperInvariant(), Style.UiHeavy, Style.Badge, col.Lightened(0.2f), true, HorizontalAlignment.Center);
        detail.CustomMinimumSize = new Vector2(width, 0);
        v.AddChild(detail);
        v.MouseFilter = MouseFilterEnum.Ignore;
        return v;
    }

    void BuildChest()
    {
        chest = new Node3D { Name = "OpeningChest" };
        if (ItemModels.Make("chest") is { } made)
        {
            chest.AddChild(made.Model);
            lid = made.Model.FindChild("Lid", true, false) as Node3D;
        }
        // Light leaking from the seam under the lid, then pouring out of the open mouth.
        seamMat = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = Colors.Black };
        chest.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(1.045f, 0.02f, 0.645f) }, MaterialOverride = seamMat, Position = new Vector3(0, 0.262f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        // The light inside: hottest at its heart, deep amber at the walls (a flat fill read as a card).
        mouthMat = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = Colors.Black,
            AlbedoTexture = new GradientTexture2D
            {
                Gradient = new Gradient { Colors = new[] { new Color(1f, 0.92f, 0.7f), new Color(0.95f, 0.55f, 0.18f), new Color(0.35f, 0.1f, 0.02f) }, Offsets = new[] { 0f, 0.45f, 1f } },
                Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1.05f, 0.5f), Width = 64, Height = 64,
            },
        };
        chest.AddChild(new MeshInstance3D { Mesh = new PlaneMesh { Size = new Vector2(0.94f, 0.54f) }, MaterialOverride = mouthMat, Position = new Vector3(0, 0.274f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off });
        light = new OmniLight3D { LightColor = gold ? new Color("#ffcf6a") : new Color("#ffb860"), OmniRange = 7, LightEnergy = 0, ShadowEnabled = false, Position = new Vector3(0, 0.9f, 0) };
        chest.AddChild(light);
        // On the people's layer, which the marks on the ground do not paint: a burnt patch under
        // the fight was printed across the open mouth and put its light out.
        static void Lift(Node n)
        {
            if (n is VisualInstance3D v) v.Layers = 2;
            foreach (var k in n.GetChildren()) Lift(k);
        }
        Lift(chest);
        scene.AddChild(chest);
        Place(0);
    }

    static float Smooth(double x) { x = Math.Clamp(x, 0, 1); return (float)(x * x * (3 - 2 * x)); }
    static float BackOut(double x) { x = Math.Clamp(x, 0, 1); const double s = 1.7; x -= 1; return (float)(x * x * ((s + 1) * x + s) + 1); }

    /// <summary>The chest where it lay: swelling as it is taken up, turning to face us, shaking
    /// harder until it bursts, then standing open, and at the end gone back into the light.</summary>
    void Place(double dt)
    {
        float k = (float)Math.Clamp(t / Shake, 0, 1);
        float grow = 0.55f + 0.3f * BackOut(t / 0.3);
        if (closing) grow *= 1 - Smooth(closeT / (Outro * 0.8));
        double turn = Math.Atan2(Math.Sin(cam.Yaw - lie), Math.Cos(cam.Yaw - lie));
        float yaw = lie + (float)turn * Smooth(t / 0.4);
        float wob = burst ? 0 : k * k;
        var basis = new Godot.Basis(Vector3.Up, yaw + Mathf.Sin((float)t * 41) * 0.07f * wob)
            * new Godot.Basis(Vector3.Forward, Mathf.Sin((float)t * 33 + 1) * 0.06f * wob);
        float hop = burst ? 0 : Mathf.Abs(Mathf.Sin((float)t * 21)) * 0.05f * wob;
        chest.Transform = new Transform3D(basis.Scaled(Vector3.One * Math.Max(0.001f, grow)), at + Vector3.Up * (0.27f * grow + hop));
        if (lid != null)
        {
            // Rattling against its lock, then thrown back on its hinge.
            float open = burst ? -1.95f * BackOut((t - Shake) / 0.16) : -Mathf.Abs(Mathf.Sin((float)t * 27)) * 0.14f * wob;
            lid.Rotation = new Vector3(open, 0, 0);
        }
        float leak = burst ? 0 : k * k * 3.2f * (0.8f + 0.2f * Mathf.Sin((float)t * 50));
        seamMat.AlbedoColor = new Color(1.0f, 0.75f, 0.35f) * leak;
        float pour = burst ? (closing ? 1 - Smooth(closeT / Outro) : 1) * (1.8f + 0.25f * Mathf.Sin((float)real * 6)) : 0;
        mouthMat.AlbedoColor = (gold ? new Color(1.1f, 1.0f, 0.75f) : new Color(1.1f, 0.9f, 0.7f)) * (pour * 0.75f);
        light.LightEnergy = burst ? 2.6f * (closing ? 1 - Smooth(closeT / Outro) : 1) : k * k * 2.2f;
    }

    /// <summary>A key: everything lands now; a second key, done.</summary>
    public void Skip()
    {
        if (closing || real < 0.5) return;
        if (skipped || t >= LastLand) { Close(); return; }
        skipped = true;
        if (!burst) { t = Shake; Burst(); }
        // Every reel stops at once, on one chord: the highest step, and the evolution's if there is one.
        t = Math.Max(t, LastLand - 0.001);
        foreach (var r in reels) if (!r.Landed) { r.Land = t; Landed(r, false); }
        Sfx.ChestLand(reels.Count - 1, gold);
        closeAt = real + 0.7;
    }

    void Burst()
    {
        burst = true;
        Sfx.ChestBurst(c.Hoard != null ? Math.Max(5, count) : count);
        scene.Fx.ChestBurst(at + Vector3.Up * 0.3f, gold ? new Color(2.8f, 2.2f, 1.1f) : new Color(2.6f, 1.8f, 0.8f), c.Hoard != null ? Math.Max(5, count) : count);
        cam.AddTrauma(count >= 5 || c.Hoard != null ? 0.32f : 0.2f);
        haptics.Add(count >= 5 || c.Hoard != null ? 0.7f : 0.5f, 0.3f, 0.18f);
        foreach (var r in reels) r.M.Visible = true;
    }

    void Landed(Reel r, bool sound)
    {
        r.Landed = true;
        var col = ColourOf(r.It);
        r.M.Glyph = r.It.Icon;
        r.M.Ring = col;
        r.M.Ink = col.Lightened(0.2f);
        r.M.Core = col.Darkened(0.82f);
        r.M.Lit = r.It.Kind == ChestItemKind.Evolution;
        r.M.QueueRedraw();
        r.Ring.Start();
        if (!sound) return;
        Sfx.ChestLand(reels.IndexOf(r), r.It.Kind == ChestItemKind.Evolution);
        haptics.Add(r.It.Kind == ChestItemKind.Evolution ? 0.5f : 0.1f, 0.3f, r.It.Kind == ChestItemKind.Evolution ? 0.2f : 0.04f);
        if (r.It.Kind == ChestItemKind.Evolution)
        {
            scene.Fx.Flash(at + Vector3.Up * 2, Gilt, 14, 0.8f, 12);
            cam.AddTrauma(0.18f);
        }
    }

    void Close()
    {
        if (closing) return;
        closing = true;
        closeT = 0;
        // Home: each thing flies to its place on the bar.
        foreach (var r in reels) if (!r.Landed) Landed(r, false);
        cam.FocusOverride = savedFocus;
        cam.TargetDistance = savedDistance;
    }

    public override void _Process(double delta)
    {
        if (Done) return;
        double dt = Math.Min(delta, 0.1);
        real += dt;
        if (!closing) t += dt * speed;
        else closeT += dt;
        // The world held round her, let go as it closes.
        scene.Hold = closing ? 1 - Smooth(closeT / (Outro * 0.75)) : Smooth(real / 0.15);
        if (!burst && t >= Shake) Burst();
        // In close by the burst (the camera's own easing took two seconds to get there); it eases
        // back out by itself once let go.
        if (!closing) cam.Distance = Mathf.Lerp(savedDistance, near, Smooth(real / 0.5));
        Place(dt);
        var mouth = cam.Camera.IsPositionBehind(at) ? new Vector2(960, 560) : cam.Camera.UnprojectPosition(at + Vector3.Up * 0.55f);
        // The darkness round the chest, centred on it.
        shade.Position = mouth - shade.Size / 2;
        shade.Modulate = Colors.White with { A = closing ? 1 - Smooth(closeT / Outro) : Smooth(real / 0.4) };
        // The fan of reels over the chest, kept on the screen.
        int n = reels.Count;
        float gap = n <= 5 ? 200 : Math.Min(200, 1560f / n);
        float cx = Mathf.Clamp(mouth.X, 140 + gap * (n - 1) / 2, 1780 - gap * (n - 1) / 2);
        // Clear of the top bars (a herald's or a boss's name and health sit there).
        float cy = Math.Max(390, mouth.Y - 250);
        for (int i = 0; i < n; i++)
        {
            var r = reels[i];
            float u = n > 1 ? (i - (n - 1) / 2f) / ((n - 1) / 2f) : 0;
            var home = new Vector2(cx + (i - (n - 1) / 2f) * gap, cy - 34 * (1 - u * u));
            // Out of the chest's mouth, arcing up to its place.
            float fly = BackOut((t - r.Out) / FlyOut);
            var pos = mouth.Lerp(home, fly) + Vector2.Up * 60 * Mathf.Sin(Mathf.Pi * Mathf.Clamp((float)((t - r.Out) / FlyOut), 0, 1));
            float scale = 0.3f + 0.7f * Smooth((t - r.Out) / FlyOut);
            // Spinning: the glyphs turn over fast and slow down into the landing.
            if (burst && !r.Landed && t >= r.Out)
            {
                if (t >= r.Land) Landed(r, true);
                else if (t >= r.NextTurn)
                {
                    double left = Math.Clamp((r.Land - t) / (r.Land - r.Out), 0, 1);
                    r.NextTurn = t + 0.055 + 0.22 * (1 - left) * (1 - left);
                    r.M.Glyph = pool[(i * 3 + ++r.Turn) % pool.Count];
                    r.M.QueueRedraw();
                    if (i == reels.FindIndex(x => !x.Landed)) Sfx.ChestTick(0.6 + 0.4 * left);
                }
            }
            // Landed: a kick of size that settles, and its name under it.
            if (r.Landed)
            {
                double since = t - r.Land;
                scale *= 1 + 0.32f * (float)Math.Max(0, 1 - since / 0.28) * (float)Math.Exp(-since * 3);
                r.Plate.Modulate = Colors.White with { A = Smooth(since / 0.25) };
            }
            if (closing)
            {
                // Home to its place on the bar, shrinking as it goes.
                float k = Smooth(closeT / Outro);
                pos = pos.Lerp(hud.PlaceOf(r.It.Id), k);
                scale *= 1 - 0.65f * k;
                r.Plate.Modulate = Colors.White with { A = 1 - Smooth(closeT / (Outro * 0.5)) };
                r.M.Modulate = Colors.White with { A = 1 - Smooth((closeT - Outro * 0.7) / (Outro * 0.3)) };
            }
            r.Pos = pos;
            r.M.Position = pos - new Vector2(r.Size / 2, r.Size / 2);
            r.M.Scale = Vector2.One * scale;
            r.Ring.Position = pos - r.Ring.Size / 2;
            r.Plate.Position = home + new Vector2(-r.Plate.Size.X / 2, r.Size / 2 + 10);
        }
        kicker.Position = new Vector2(cx - kicker.Size.X / 2, cy - 34 - 72 - kicker.Size.Y);
        kicker.Modulate = Colors.White with { A = closing ? 1 - Smooth(closeT / (Outro * 0.5)) : Smooth((t - Shake) / 0.3) };
        hint.Position = new Vector2(960 - hint.Size.X / 2, 1080 - 210);
        hint.Modulate = Colors.White with { A = closing ? 0 : Smooth((real - 0.5) / 0.3) * 0.8f };
        if (!closing && (t >= Total || (closeAt > 0 && real >= closeAt))) Close();
        if (closing && closeT >= Outro)
        {
            scene.Hold = 0;
            chest.QueueFree();
            Done = true;
            // An evolution out of it: crowned on the bar as it arrives, and the world slowed for a
            // breath as the new thing fires its first.
            foreach (var r in reels) if (r.It.Kind == ChestItemKind.Evolution) { hud.Crown(r.It.Id); scene.Slow(0.6); }
        }
    }

    public override void _ExitTree()
    {
        // Left early (a zone changed under it): nothing of it stays in the world.
        if (IsInstanceValid(chest) && !chest.IsQueuedForDeletion()) chest.QueueFree();
        scene.Hold = 0;
    }

    /// <summary>A ring of light thrown out from a thing as it lands.</summary>
    public partial class Shine : Control
    {
        public Color Colour = Style.Gold;
        double t = -1;

        public Shine() { MouseFilter = MouseFilterEnum.Ignore; }

        public void Start() { t = 0; QueueRedraw(); }

        public override void _Process(double delta)
        {
            if (t < 0) return;
            t += delta;
            QueueRedraw();
            if (t > 0.6) t = -1;
        }

        public override void _Draw()
        {
            if (t < 0) return;
            float k = (float)(t / 0.6);
            var c = Size / 2;
            float r = Size.X * (0.18f + 0.3f * (1 - (1 - k) * (1 - k)));
            DrawArc(c, r, 0, Mathf.Tau, 64, Colour with { A = 0.85f * (1 - k) }, 3 + 4 * (1 - k), true);
            DrawArc(c, r * 0.82f, 0, Mathf.Tau, 64, Colour.Lightened(0.4f) with { A = 0.4f * (1 - k) }, 1.5f, true);
        }
    }
}

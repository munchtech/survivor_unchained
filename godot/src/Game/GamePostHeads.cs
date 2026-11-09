using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Content;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Play;

/* (M5 r3, judge mark 5) Every lamp-post of the zone gets a lantern head that reads from the play camera: the kit's post
 * is a bare dark pier from up here. Dark, its glass holds a faint ember (lamp_posts.json lit.ember); lit, a warm flame
 * in the glass, a soft bloom round it and a soft round pool of its light on the ground (a decal, not the zone light's
 * mottled stain); kindled, sparks rise from the head and the bloom and pool swell and settle. Lit posts burn lit.color,
 * a whiter gold than her ember. A landmark post (a town square's lamp, Post.Landmark) is the same head bigger, on its
 * own tall iron pole, lit with its pool and its own light even by day. Functional: M5 owns that it reads, L1 the final
 * light (energies, the pool's size, the bloom, the zone light under it). --heads-off leaves them out (pictures). */
public partial class Game
{
    sealed class PostHead
    {
        public string Id = "";
        public Node3D Root = null!;
        public StandardMaterial3D Glass = null!, Bloom = null!;
        public MeshInstance3D BloomQ = null!;
        public Decal Pool = null!;
        public OmniLight3D? Own;
        public Vector3 Head;
        public float Scale = 1, A, Flare, PoolR;
        public bool Lit, Seen, Landmark;
    }

    readonly List<PostHead> heads = new();
    Node? headsScene;
    string? headsZone;
    static readonly bool HeadsOff = Args.Has("heads-off");

    /// <summary>Each frame: the zone's posts' heads follow their lit state (none in a film).</summary>
    void PostHeads(double dt)
    {
        string? zid = scene != null && zone != null && !HeadsOff ? zone.Id : null;
        if (zid != headsZone || scene != headsScene || (heads.Count > 0 && !IsInstanceValid(heads[0].Root))) BuildHeads(zid);
        if (heads.Count == 0) return;
        bool show = !InCinematic, night = scene!.View.Night;
        var lc = LampPosts.Lit;
        Color litC = new(lc.Color), ember = new(lc.Ember);
        var eye = camera.GlobalPosition;
        float t = (float)scene.Time;
        for (int i = 0; i < heads.Count; i++)
        {
            var h = heads[i];
            h.Root.Visible = show;
            if (!show) continue;
            bool lit = LampBook.PostLit(Journey.World, h.Id);
            if (lit && !h.Lit && h.Seen) h.Flare = 1;
            if (!h.Seen) h.A = lit ? 1 : 0;
            h.Lit = lit; h.Seen = true;
            h.A = Mathf.MoveToward(h.A, lit ? 1 : 0, (float)dt / 0.5f);
            h.Flare = Mathf.MoveToward(h.Flare, 0, (float)dt / 1.6f);
            float f = h.Flare * h.Flare * (3 - 2 * h.Flare), a = h.A;
            float breath = 1 + 0.07f * Mathf.Sin(t * 2.3f + i * 1.7f) + 0.04f * Mathf.Sin(t * 6.1f + i);
            // (the glass: an ember dark, the flame lit; brighter by night, where it is the frame's light)
            var gc = ember.Lerp(litC, a);
            float ge = Mathf.Lerp(1.6f, night ? 3.4f : 2.4f, a) * breath * (1 + 1.6f * f) * (h.Landmark ? 1.25f : 1);
            h.Glass.Emission = gc;
            h.Glass.EmissionEnergyMultiplier = ge;
            // (the bloom round the head: small and dim dark, wider lit, swelling with the kindling; drawn toward the camera so
            // the cage never cuts it)
            float bs = h.Scale * Mathf.Lerp(0.75f, 1.25f, a) * (1 + 1.2f * f);
            h.BloomQ.Scale = Vector3.One * bs;
            h.BloomQ.GlobalPosition = h.Head + (eye - h.Head).Normalized() * 0.5f * h.Scale;
            var bc = gc.SrgbToLinear() * (Mathf.Lerp(0.4f, night ? 0.6f : 0.35f, a) * breath * (1 + 1.2f * f));
            h.Bloom.AlbedoColor = new Color(bc.R, bc.G, bc.B, 1);
            // (the pool: a soft round of its light on the ground, lit only; a landmark's even by day)
            float pe = a * (night ? 0.3f : h.Landmark ? 0.16f : 0.06f) * breath * (1 + 1.2f * f);
            h.Pool.Visible = pe > 0.002f;
            h.Pool.EmissionEnergy = pe;
            // (the pool a warmer gold than the flame: lit.color alone laid a white spot on sunlit ground)
            h.Pool.Modulate = litC.Lerp(ember, 0.3f);
            float pr = h.PoolR * (1 + 0.35f * f);
            h.Pool.Size = new Vector3(pr * 2, h.Pool.Size.Y, pr * 2);
            if (h.Own != null) { h.Own.LightColor = litC; h.Own.LightEnergy = a * (night ? 2.2f : 1.4f) * breath; }
            // (the kindling's sparks: rising off the head while it flares)
            if (h.Flare > 0.25f)
                for (int k = 0; k < 2; k++)
                {
                    float rx = (GD.Randf() - 0.5f) * 0.35f * h.Scale, rz = (GD.Randf() - 0.5f) * 0.35f * h.Scale;
                    scene.Fx.Sparks.Spawn(h.Head + new Vector3(rx, 0.15f * h.Scale, rz), new Vector3(rx * 1.5f, 1.6f + 2.2f * GD.Randf(), rz * 1.5f),
                        0.8f + 0.7f * GD.Randf(), 0.05f, litC * 3.2f, ember * 1.4f, 0.015f, -0.6f, 0.8f);
                }
        }
    }

    void BuildHeads(string? zid)
    {
        foreach (var h in heads) if (IsInstanceValid(h.Root)) h.Root.QueueFree();
        heads.Clear();
        headsZone = zid; headsScene = scene;
        if (zid == null || scene == null) return;
        var lights = scene.Data.Meta.Lights;
        var iron = new StandardMaterial3D { AlbedoColor = new Color("#2a241e"), Metallic = 0.55f, Roughness = 0.55f };
        foreach (var p in LampPosts.In(zid))
        {
            float g = (float)scene.HeightAt(p.X, p.Z);
            float y = g + 2.0f;
            if (p.Light >= 0 && p.Light < lights.Count)
            {
                float ly = (float)lights[p.Light].Y;
                y = ly > g + 0.8f ? ly : g + ly;
            }
            // (where the kit hangs its own lantern (the light's glass node, on a bracket off the post), the head is drawn
            // round it: one lantern, not two)
            var at = new Vector3((float)p.X, y, (float)p.Z);
            if (p.Light >= 0 && p.Light < lights.Count && lights[p.Light].Glow.Count > 0 && scene.View.Node(lights[p.Light].Glow[0]) is { } gn && IsInstanceValid(gn))
            {
                var gp = gn.GlobalPosition;
                if (new Vector2(gp.X - at.X, gp.Z - at.Z).Length() < 2.5f && Math.Abs(gp.Y - at.Y) < 2) at = gp;
            }
            bool mark = p.Landmark > 0;
            float s = mark ? (float)p.Landmark : 1.6f;
            if (mark && p.Tall > 0) y = g + (float)p.Tall;
            var h = new PostHead { Id = p.Id, Root = new Node3D { Name = "PostHead_" + p.Id }, Scale = s, Landmark = mark, PoolR = mark ? 6.5f : 3.4f };
            scene.AddChild(h.Root);
            if (mark && p.Tall > 0) at = new Vector3((float)p.X, y, (float)p.Z);
            h.Root.GlobalPosition = at;
            y = at.Y;
            h.Head = h.Root.GlobalPosition;
            var lantern = new Node3D { Scale = Vector3.One * s };
            h.Root.AddChild(lantern);
            void Part(Mesh m, Material mat, float py, float rot = 0) =>
                lantern.AddChild(new MeshInstance3D { Mesh = m, MaterialOverride = mat, Position = new Vector3(0, py, 0), RotationDegrees = new Vector3(0, rot, 0) });
            // (a four-sided lantern: an iron cap with its ring, the glass in four bars, an iron foot on the post's top)
            h.Glass = new StandardMaterial3D { AlbedoColor = new Color("#3a2414"), Roughness = 0.35f, EmissionEnabled = true, Emission = new Color(LampPosts.Lit.Ember), EmissionEnergyMultiplier = 0.5f };
            Part(new CylinderMesh { TopRadius = 0.03f, BottomRadius = 0.12f, Height = 0.1f, RadialSegments = 4, Rings = 1 }, iron, 0.23f, 45);
            Part(new TorusMesh { InnerRadius = 0.02f, OuterRadius = 0.045f, Rings = 8, RingSegments = 6 }, iron, 0.3f);
            Part(new CylinderMesh { TopRadius = 0.135f, BottomRadius = 0.115f, Height = 0.32f, RadialSegments = 4, Rings = 1 }, h.Glass, 0.02f, 45);
            Part(new CylinderMesh { TopRadius = 0.15f, BottomRadius = 0.09f, Height = 0.07f, RadialSegments = 4, Rings = 1 }, iron, -0.175f, 45);
            for (int k = 0; k < 4; k++)
            {
                float an = Mathf.Pi / 4 + k * Mathf.Pi / 2;
                lantern.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.03f, 0.34f, 0.03f) }, MaterialOverride = iron, Position = new Vector3(Mathf.Cos(an) * 0.13f, 0.02f, Mathf.Sin(an) * 0.13f) });
            }
            if (mark)
            {
                // (its own pole, standing over the kit's post, and a light of its own: the square's lamp by day too)
                float tall = y - g - 0.21f * s;
                h.Root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.055f, BottomRadius = 0.09f, Height = tall, RadialSegments = 10 }, MaterialOverride = iron, Position = new Vector3(0, -0.21f * s - tall / 2, 0) });
                h.Root.AddChild(new MeshInstance3D { Mesh = new CylinderMesh { TopRadius = 0.14f, BottomRadius = 0.2f, Height = 0.35f, RadialSegments = 10 }, MaterialOverride = iron, Position = new Vector3(0, g - y + 0.17f, 0) });
                h.Own = new OmniLight3D { OmniRange = 9, OmniAttenuation = 1.1f, LightSpecular = 0.2f, ShadowEnabled = false, Position = new Vector3(0, -0.4f, 0) };
                h.Root.AddChild(h.Own);
            }
            h.Bloom = new StandardMaterial3D
            {
                ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                AlbedoTexture = BeaconTexture(), DisableFog = true, DisableReceiveShadows = true,
            };
            h.BloomQ = new MeshInstance3D { Mesh = new QuadMesh { Size = Vector2.One * 2 }, MaterialOverride = h.Bloom, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            h.Root.AddChild(h.BloomQ);
            h.Pool = new Decal
            {
                Size = new Vector3(h.PoolR * 2, 2, h.PoolR * 2), TextureAlbedo = PoolTexture(), TextureEmission = PoolTexture(), AlbedoMix = 0,
                EmissionEnergy = 0, UpperFade = 0.3f, LowerFade = 0.3f, Visible = false, Position = new Vector3(0, g + 0.2f - y, 0),
            };
            h.Root.AddChild(h.Pool);
            heads.Add(h);
        }
    }

    static ImageTexture? poolTex;

    /// <summary>A soft round pool: full in its middle, falling smoothly to nothing at its edge (no rim, no ring).</summary>
    static ImageTexture PoolTexture()
    {
        if (poolTex != null) return poolTex;
        const int N = 128;
        var img = Image.CreateEmpty(N, N, true, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float dx = (x + 0.5f) / N * 2 - 1, dy = (y + 0.5f) / N * 2 - 1, r = Mathf.Sqrt(dx * dx + dy * dy);
                float k = 1 - Mathf.SmoothStep(0.15f, 1f, r);
                k *= k;
                img.SetPixel(x, y, new Color(k, k, k, k));
            }
        img.GenerateMipmaps();
        return poolTex = ImageTexture.CreateFromImage(img);
    }
}

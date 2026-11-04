using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Ui;

namespace SurvivorUnchained.Play;

/* The Ford-Warden's lamp posts on this side of the screen: the pointers to the lit ones that are off screen
 * (drawn by Ui/LampPointers.cs, fed from the same camera projection as the goal arrows), each lit post's beacon
 * (its look of burning, the fight's alone), and the --lampcheck measurement. */
public partial class Game
{
    double lampCheckAt = -1;

    /// <summary>A lit post's look in the fight (H4 item 5, N8: the owner saw one lamp that refills). From the play
    /// camera, 25 m out at night, the flame in its iron is a fleck and the post a dark pier: lit, it gets a soft cold
    /// halo round the flame (drawn a little toward the camera, so the cage and the pier's top never cut it) and a pool
    /// of its light on the water and the bank round it; put out, both go at once (Snuff's frost burst covers it);
    /// relit, they flare up and settle. Only while the fight is on (Prologue.LampPosts): C02 and C03 light posts 4-6
    /// themselves, and their look is theirs.</summary>
    sealed class Beacon { public Node3D Root = null!; public MeshInstance3D Halo = null!; public StandardMaterial3D Mat = null!; public OmniLight3D Pool = null!; public bool Lit, Seen; public float A, Flare; }
    readonly List<Beacon> beacons = new();
    static ImageTexture? beaconTex;
    /// <summary>--beacon-halo R, --beacon-glow A, --beacon-pool E, --beacon-off: the halo's half size (m), its strength,
    /// the pool light's energy, and the beacons left out (pictures).</summary>
    static readonly float BeaconHalo = Args.Num("beacon-halo", 2.6f), BeaconGlow = Args.Num("beacon-glow", 0.9f), BeaconPool = Args.Num("beacon-pool", 12f);
    static readonly Color BeaconColor = new("#7ab6ff");

    /// <summary>A halo with no rim: a hot core round the flame, the lamp's glow in the air, and a faint wide breath of
    /// its light, windowed to nothing at the quad's edge.</summary>
    static ImageTexture BeaconTexture()
    {
        if (beaconTex != null) return beaconTex;
        const int N = 128;
        var img = Image.CreateEmpty(N, N, true, Image.Format.Rgba8);
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                float dx = (x + 0.5f) / N * 2 - 1, dy = (y + 0.5f) / N * 2 - 1, r2 = dx * dx + dy * dy;
                float win = r2 >= 1 ? 0 : (1 - r2) * (1 - r2);
                float a = Mathf.Min(1, 0.55f * Mathf.Exp(-r2 * 90f) + 0.3f * Mathf.Exp(-r2 * 14f) + 0.15f * Mathf.Exp(-r2 * 2.5f)) * win;
                img.SetPixel(x, y, new Color(1, 1, 1, a));
            }
        img.GenerateMipmaps();
        return beaconTex = ImageTexture.CreateFromImage(img);
    }

    Beacon NewBeacon()
    {
        var b = new Beacon { Root = new Node3D { Name = "LampBeacon" } };
        b.Mat = new StandardMaterial3D
        {
            ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
            BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
            AlbedoTexture = BeaconTexture(), DisableFog = true, DisableReceiveShadows = true,
            // (soft where it meets a body standing in it: the Warden at his post)
            ProximityFadeEnabled = true, ProximityFadeDistance = 0.8f,
        };
        b.Halo = new MeshInstance3D { Mesh = new QuadMesh { Size = Vector2.One * BeaconHalo * 2 }, MaterialOverride = b.Mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
        // (the pier and the iron kept out of it, as out of the lamp's own light: ZoneView.LampLayer)
        b.Pool = new OmniLight3D { LightColor = BeaconColor, OmniRange = 8, OmniAttenuation = 1.2f, LightSpecular = 0.25f, ShadowEnabled = false, LightCullMask = ~SurvivorUnchained.View.ZoneView.LampLayer };
        b.Root.AddChild(b.Halo);
        b.Root.AddChild(b.Pool);
        scene!.AddChild(b.Root);
        return b;
    }

    /// <summary>Each frame of play: the beacons follow the posts' lit state (none outside the fight, or in a film).</summary>
    void LampBeacons(double dt)
    {
        for (int i = beacons.Count - 1; i >= 0; i--)
            if (!IsInstanceValid(beacons[i].Root) || beacons[i].Root.GetParent() != scene) beacons.RemoveAt(i);
        var posts = zone is Zones.Prologue pro && !InCinematic && !Args.Has("beacon-off") ? pro.LampPosts.ToList() : new();
        if (posts.Count == 0)
        {
            foreach (var b in beacons) { b.A = 0; b.Seen = false; b.Root.Visible = false; }
            return;
        }
        while (beacons.Count < posts.Count) beacons.Add(NewBeacon());
        var eye = camera.GlobalPosition;
        float t = (float)(scene!.Time);
        for (int i = 0; i < posts.Count; i++)
        {
            var (x, y, z, lit) = posts[i];
            var b = beacons[i];
            // (relit in the fight: a flare; the fight's first frame comes up with no flare, C02 had them burning)
            if (lit && !b.Lit && b.Seen) b.Flare = 1;
            if (!b.Seen) b.A = lit ? 1 : 0;
            b.Lit = lit; b.Seen = true;
            b.A = Mathf.MoveToward(b.A, lit ? 1 : 0, (float)dt / (lit ? 0.35f : 0.12f));
            b.Flare = Mathf.MoveToward(b.Flare, 0, (float)dt / 1.4f);
            b.Root.Visible = b.A > 0.001f;
            if (!b.Root.Visible) continue;
            // (the flame's middle: the lamp's light hangs 0.8 m over the pier's top, the flame's foot 0.2 m over it)
            var flame = new Vector3((float)x, (float)y - 0.48f, (float)z);
            float f = b.Flare * b.Flare * (3 - 2 * b.Flare);
            float breath = 1 + 0.06f * Mathf.Sin(t * 1.9f + i * 2.1f) + 0.03f * Mathf.Sin(t * 5.3f + i);
            b.Halo.GlobalPosition = flame + (eye - flame).Normalized() * 1.2f;
            b.Halo.Scale = Vector3.One * (1 + 0.9f * f);
            var c = BeaconColor.SrgbToLinear() * (BeaconGlow * breath * (1 + 1.5f * f));
            b.Mat.AlbedoColor = new Color(c.R, c.G, c.B, b.A);
            // (its pool hangs a metre under the pier's top, over the water or the bank: a round of cold light some 5 m across)
            b.Pool.GlobalPosition = new Vector3((float)x, (float)y - 1.8f, (float)z);
            b.Pool.LightEnergy = BeaconPool * b.A * breath * (1 + 2f * f);
        }
    }

    /// <summary>A lit post whose lamp is more than 70 px outside the view (or behind the camera) gets a pointer on the
    /// edge of a rectangle 90 px in from the view's sides, kept above the hotbar and below the corner's words (as the goal arrows are).</summary>
    List<LampPointers.Pointer> PostPointers()
    {
        var o = new List<LampPointers.Pointer>();
        if (scene == null || zone is not Zones.Prologue pro) return o;
        var size = GetViewport().GetVisibleRect().Size;
        var seen = new Rect2(Vector2.Zero, size).Grow(70);
        var box = new Rect2(90, 160, size.X - 180, size.Y - 160 - 210);
        var mid = size / 2;
        int i = 0;
        foreach (var p in pro.LampPosts)
        {
            int id = i++;
            if (!p.Lit) continue;
            var w = new Vector3((float)p.X, (float)p.Y, (float)p.Z);
            bool behind = camera.IsPositionBehind(w);
            var sp = camera.UnprojectPosition(w);
            if (!behind && seen.HasPoint(sp)) continue;
            var d = sp - mid;
            if (behind) d = -d;
            if (d.LengthSquared() < 1) d = Vector2.Down;
            float tx = d.X != 0 ? ((d.X > 0 ? box.End.X : box.Position.X) - mid.X) / d.X : float.MaxValue;
            float ty = d.Y != 0 ? ((d.Y > 0 ? box.End.Y : box.Position.Y) - mid.Y) / d.Y : float.MaxValue;
            o.Add(new LampPointers.Pointer(id, mid + d * Mathf.Min(tx, ty), d.Normalized()));
        }
        return o;
    }

    /// <summary>--lampcheck: every 0.5 s of the Warden fight, how many lit posts (and posts, and she) are in the frame.</summary>
    void LampCheck(double battleTime)
    {
        if (!Args.Has("lampcheck") || zone is not Zones.Prologue pro) return;
        var posts = pro.LampPosts.ToList();
        if (posts.Count == 0) { lampCheckAt = -1; return; }
        if (lampCheckAt >= 0 && battleTime < lampCheckAt + 0.5) return;
        lampCheckAt = battleTime;
        var size = GetViewport().GetVisibleRect().Size;
        var view = new Rect2(Vector2.Zero, size).Grow(-40);
        bool In(Vector3 w) => !camera.IsPositionBehind(w) && view.HasPoint(camera.UnprojectPosition(w));
        bool InPost((double X, double Y, double Z, bool Lit) p) => In(new Vector3((float)p.X, (float)p.Y, (float)p.Z));
        int lit = posts.Count(p => p.Lit), inframe = posts.Count(p => p.Lit && InPost(p)), all = posts.Count(InPost);
        int her = In(scene!.HerDrawn + new Vector3(0, 1.1f, 0)) ? 1 : 0;
        GD.Print($"LAMPCHECK t={battleTime:0.0} lit={lit} inframe={inframe} all={all} her={her}");
    }
}

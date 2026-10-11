using System;
using System.Collections.Generic;
using Godot;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.View;

/// <summary>
/// Her own things in the cinematics, made to sit in her hands where
/// animation keyed them (tools/anim/clips/story.py, story_c04.py):
/// <list type="bullet">
/// <item>the gourd: a pilgrim's water gourd on a hemp cord wound twice round
/// her right wrist (C01: "full and corked", a strand of river weed caught in
/// the cord; C04 A: the drink). Held, she has it by its waist as Arms.Hold
/// mounts a thing, the neck out of the thumb side and its lip 9 cm up (held.py
/// SPOUT); hung, it swings on its cord from her wrist and lies on the ground
/// when she does.</item>
/// <item>its cork, passed from the gourd to her teeth and on to her left hand
/// (PersonView.Pass);</item>
/// <item>the letter that brought her home, wet through (C01): folded in her
/// left hand's pinch, or opened between both hands' pinches, unfolding as
/// they draw apart.</item>
/// </list>
/// Pinches are found from her own finger bones, not guessed offsets, so the
/// paper sits between the thumb and the forefinger whatever the hand does.
/// </summary>
public static partial class Keepsakes
{
    public static bool Is(string piece) => piece is "gourd" or "gourd_hung" or "letter" or "letter_open" || piece.StartsWith("palms:");

    /// <summary>The thing to hold, already in her skeleton (or, for what
    /// moves by itself, on top of it). ground: the ground's height at a place.</summary>
    public static Node3D Make(People.Person p, string piece, Func<float, float, float>? ground)
    {
        var sk = p.Skeleton;
        switch (piece)
        {
            case "gourd":
            {
                // In her fist, the way Arms.Hold mounts a weapon: the neck along the
                // hand's thumb side (+Z), across the fingers (+Y).
                var att = Attach(sk, "hand_r");
                var mount = new Node3D { Name = "mount:gourd" };
                var x = new Vector3(0, 1, 0);
                var y = new Vector3(0, 0, 1);
                mount.Basis = new Basis(x, y, x.Cross(y));
                mount.Position = new Vector3(-0.025f, 0.075f, 0);
                att.AddChild(mount);
                var g = Gourd();
                mount.AddChild(g);
                var cord = new WristCord(sk, g.GetNode<Node3D>("tie"), 0.02f);
                att.AddChild(cord);
                return att;
            }
            case "gourd_hung":
            {
                var root = new Node3D { Name = "gourd_hung" };
                sk.AddChild(root);
                var hung = new Hung { Name = "hung", Ground = ground };
                root.AddChild(hung);
                var g = Gourd();
                hung.AddChild(g);
                var cord = new WristCord(sk, g.GetNode<Node3D>("tie"), 0.0f);
                root.AddChild(cord);
                hung.Cord = cord;
                return root;
            }
            case var palms when palms.StartsWith("palms:"):
            {
                var light = new Palms(sk, new Color(palms["palms:".Length..]));
                sk.AddChild(light);
                return light;
            }
            case "letter":
            case "letter_open":
            {
                var l = new Letter(sk) { Name = "letter", Open = piece == "letter_open" };
                sk.AddChild(l);
                return l;
            }
        }
        throw new ArgumentException(piece);
    }

    /// <summary>A node that follows one of her bones.</summary>
    public static BoneAttachment3D Attach(Skeleton3D sk, string bone)
    {
        // Her head is "Head" in the rig; the timelines say "head", as cameras do.
        if (sk.FindBone(bone) < 0 && sk.FindBone(Capitalised(bone)) >= 0) bone = Capitalised(bone);
        var att = new BoneAttachment3D { BoneName = bone };
        sk.AddChild(att);
        // Placed now, so a thing handed to it this frame keeps where it is.
        int i = sk.FindBone(bone);
        if (i >= 0) att.GlobalTransform = sk.GlobalTransform * sk.GetBoneGlobalPose(i);
        return att;
    }

    static string Capitalised(string s) => s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s[1..];

    /// <summary>Where a pinch holds (between the pads of the thumb and the
    /// forefinger, each a little past its last joint), and the line from the
    /// forefinger's pad to the thumb's.</summary>
    public static (Vector3 At, Vector3 Across) Pinch(Skeleton3D sk, string side)
    {
        Vector3 Tip(string finger)
        {
            int j = sk.FindBone($"{finger}_03_{side}"), k = sk.FindBone($"{finger}_02_{side}");
            var a = sk.GlobalTransform * sk.GetBoneGlobalPose(j).Origin;
            var b = sk.GlobalTransform * sk.GetBoneGlobalPose(k).Origin;
            return a + (a - b).Normalized() * 0.014f;
        }
        Vector3 t = Tip("thumb"), f = Tip("index");
        return ((t + f) / 2, (t - f).Normalized());
    }

    /* ------------------------------------------------------------ the gourd -- */

    static Material? gourdSkin, hemp, cork, weed;

    /// <summary>A dried bottle gourd, oiled: a heavy round belly, a waist
    /// where the cord is tied and the hand takes it, a smaller shoulder, a
    /// short neck with its lip 9 cm above the waist, and a cork in it. Its
    /// origin is the waist, +Y the neck. Children: "cork", "tie" (where the
    /// cord leaves the waist).</summary>
    static Node3D Gourd()
    {
        var root = new Node3D { Name = "gourd" };
        gourdSkin ??= new StandardMaterial3D
        {
            AlbedoTexture = Tex(Paint(128, 256, (u, v) =>
            {
                // A dried, oiled gourd's skin: warm honey-amber, smooth, deepening toward the
                // base and the neck, in soft streaks down its length; a few dark blooms where
                // it lay on the ground as it dried, never a speckle.
                float streak = Noise(u * 7, v * 1.2f) * 0.7f + Noise(u * 22, v * 2.5f) * 0.3f;
                float ends = Mathf.Max(Mathf.Clamp((v - 0.72f) * 3, 0, 1), Mathf.Clamp((0.2f - v) * 4, 0, 1));
                float bloom = Mathf.Clamp((Noise(u * 2.5f + 7, v * 3 + 2) - 0.64f) * 2.5f, 0, 1);
                var c = new Color("#c98f45").Lerp(new Color("#8a5426"), 0.45f * (1 - streak) + 0.45f * ends);
                return c.Lerp(new Color("#5a341a"), bloom * 0.4f);
            })),
            Roughness = 0.38f, ClearcoatEnabled = true, Clearcoat = 0.6f, ClearcoatRoughness = 0.2f,
        };
        hemp ??= new StandardMaterial3D
        {
            AlbedoTexture = Tex(Paint(16, 64, (u, v) =>
            {
                // A two-ply twist: dark grooves running round the cord.
                float twist = Mathf.Abs(Mathf.Sin((v * 64 + u * 16) * Mathf.Pi / 4));
                return new Color("#8c7a5c").Darkened(0.45f * (1 - twist) + 0.15f * Noise(u * 4, v * 30));
            })),
            Roughness = 0.9f,
        };
        cork ??= new StandardMaterial3D
        {
            AlbedoTexture = Tex(Paint(64, 64, (u, v) =>
            {
                float pit = Mathf.Clamp((Noise(u * 50, v * 50) - 0.62f) * 5, 0, 1);
                return new Color("#b48c5e").Lerp(new Color("#5a4028"), pit * 0.8f + 0.15f * Noise(u * 8, v * 8));
            })),
            Roughness = 0.95f,
        };
        weed ??= new StandardMaterial3D
        {
            AlbedoColor = new Color("#2e4a1c"), Roughness = 0.35f, CullMode = BaseMaterial3D.CullModeEnum.Disabled,
            BacklightEnabled = true, Backlight = new Color("#4a6a20"),
        };
        var body = new Build();
        Lathe(body, Pts(
            0, -0.118f, 0.016f, -0.116f, 0.032f, -0.108f, 0.043f, -0.094f, 0.049f, -0.077f, 0.0495f, -0.060f, 0.045f, -0.043f,
            0.036f, -0.027f, 0.026f, -0.013f, 0.0205f, -0.003f, 0.020f, 0.004f, 0.023f, 0.014f, 0.029f, 0.027f, 0.031f, 0.038f,
            0.028f, 0.050f, 0.020f, 0.061f, 0.0135f, 0.069f, 0.0112f, 0.077f, 0.0114f, 0.084f, 0.0128f, 0.0865f, 0.0128f, 0.0895f,
            0.0115f, 0.0903f, 0.0088f, 0.0902f, 0.0086f, 0.084f), 36, textured: true,
            // A gourd is never quite true: a little lean and a flat side.
            warp: p => new Vector3(p.X + 0.0025f * Mathf.Max(0, -p.Y - 0.03f) * 30 * 0.1f, p.Y, p.Z * (p.Y < -0.02f ? 0.94f : 1)));
        root.AddChild(new MeshInstance3D { Name = "body", Mesh = body.Mesh(), MaterialOverride = gourdSkin });
        // The cord's two turns round the waist, and its knot.
        var turns = new Build();
        Tube(turns, Path(80, t =>
        {
            float a = t * Mathf.Tau * 2, r = 0.0222f;
            return new Vector3(r * Mathf.Cos(a), -0.004f + 0.0055f * t, r * Mathf.Sin(a));
        }), 0.0021f, 6);
        turns.Append(Knot(), new Transform3D(Basis.Identity, new Vector3(0.024f, 0.0f, 0)));
        root.AddChild(new MeshInstance3D { Name = "turns", Mesh = turns.Mesh(), MaterialOverride = hemp });
        root.AddChild(new Node3D { Name = "tie", Position = new Vector3(0.026f, 0.001f, 0) });
        // The cork: tapered, its top a little proud of the lip and rounded by use.
        var c = new Build();
        Lathe(c, Pts(0, 0.081f, 0.0080f, 0.081f, 0.0084f, 0.090f, 0.0094f, 0.106f, 0.0092f, 0.1095f, 0.0080f, 0.1108f, 0, 0.111f), 20, textured: true);
        root.AddChild(new MeshInstance3D { Name = "cork", Mesh = c.Mesh(), MaterialOverride = cork });
        return root;
    }

    /// <summary>A small knot: a lump of the cord's own turns.</summary>
    static Build Knot()
    {
        var k = new Build();
        Tube(k, Path(24, t =>
        {
            float a = t * Mathf.Tau * 1.5f;
            return new Vector3(0.003f * Mathf.Cos(a), 0.004f * Mathf.Sin(a * 0.66f), 0.0035f * Mathf.Sin(a));
        }), 0.0024f, 6);
        return k;
    }

    /// <summary>The cord: two turns round her right wrist at its crease, an
    /// oval a little wider than the wrist is thick, so they sit on the skin
    /// below any bracer's edge; the strand from the turns to the gourd's waist,
    /// drawn again each frame with a little sag; and the strand of river weed
    /// caught in the turns.</summary>
    public sealed partial class WristCord : Node3D
    {
        readonly Skeleton3D sk;
        readonly Node3D tie;
        readonly float sag;
        readonly int hand;
        readonly BoneAttachment3D ring;
        // In the hand's frame: the fingers run +Y, the thumb side is +Z, so the
        // wrist is wide across Z and thin across X.
        static readonly Vector3 Centre = new(0, 0.012f, 0);
        const float RX = 0.0245f, RZ = 0.0335f;
        readonly MeshInstance3D strand = new() { Name = "strand", TopLevel = true };

        static Vector3 On(float ang, float r = 0) => Centre + new Vector3((RX + r) * Mathf.Cos(ang), 0, (RZ + r) * Mathf.Sin(ang));

        public WristCord(Skeleton3D sk, Node3D tie, float sag)
        {
            this.sk = sk;
            this.tie = tie;
            this.sag = sag;
            Name = "cord";
            hand = sk.FindBone("hand_r");
            var loops = new Build();
            Tube(loops, Path(96, t =>
            {
                float ang = t * Mathf.Tau * 2;
                return On(ang, 0.0007f * Mathf.Sin(ang * 3)) + new Vector3(0, 0.0055f * t - 0.0028f, 0);
            }), 0.0022f, 6);
            // On the skeleton itself, so it follows her hand wherever the gourd is.
            ring = new BoneAttachment3D { BoneName = "hand_r", Name = "cord_turns" };
            ring.AddChild(new MeshInstance3D { Name = "loops", Mesh = loops.Mesh(), MaterialOverride = hemp });
            // River weed caught in the turns on the little-finger side, hanging off them.
            var w = new Build();
            var wp = Path(10, t => On(-1.9f, 0.003f) + new Vector3(-0.006f * t, -0.004f - 0.045f * t, -0.012f * Mathf.Sin(t * 4)));
            Ribbon(w, wp, new Vector3(1, 0, 0), t => 0.008f * (1 - 0.7f * t));
            ring.AddChild(new MeshInstance3D { Name = "weed", Mesh = w.Mesh(), MaterialOverride = weed });
            sk.AddChild(ring);
            AddChild(strand);
        }

        public override void _ExitTree()
        {
            if (IsInstanceValid(ring)) ring.QueueFree();
        }

        Transform3D Hand() => sk.GlobalTransform * sk.GetBoneGlobalPose(hand);

        /// <summary>The point of the turns nearest a place (where a strand leaves them for it).</summary>
        Vector3 Nearest(Transform3D t, Vector3 to)
        {
            Vector3 best = t * Centre;
            float d = float.MaxValue;
            for (int i = 0; i < 32; i++)
            {
                var p = t * On(i * Mathf.Tau / 32);
                float e = p.DistanceSquaredTo(to);
                if (e < d) { d = e; best = p; }
            }
            return best;
        }

        public override void _Process(double delta)
        {
            if (hand < 0) return;
            var end = tie.GlobalPosition;
            var low = Nearest(Hand(), end);
            var mid = (low + end) / 2 + Vector3.Down * sag;
            var bld = new Build();
            Tube(bld, Path(10, s => low * (1 - s) * (1 - s) + mid * 2 * s * (1 - s) + end * s * s), 0.0021f, 5);
            strand.Mesh = bld.Mesh();
            strand.MaterialOverride = hemp;
        }

        /// <summary>The lowest point of the turns, the cord hangs from it.</summary>
        public Vector3 Hang()
        {
            var t = Hand();
            return Nearest(t, t * Centre + Vector3.Down * 10);
        }
    }
    /// <summary>The gourd hanging by its cord from her wrist: a pendulum
    /// (gravity, a little air, the cord's length as a limit, the ground as a
    /// floor), turned to hang neck up along the cord, or laid on its side on
    /// the ground when the cord goes slack there.</summary>
    public sealed partial class Hung : Node3D
    {
        public Func<float, float, float>? Ground;
        public WristCord? Cord;
        const float Length = 0.15f, Belly = 0.047f;
        Vector3 bob, prev, side = Vector3.Right;
        bool started;

        public override void _Ready() => TopLevel = true;

        public override void _Process(double delta)
        {
            if (Cord == null) return;
            var anchor = Cord.Hang();
            if (!started || bob.DistanceTo(anchor) > 0.6f)
            {
                bob = prev = anchor + Vector3.Down * Length;
                started = true;
            }
            int n = Math.Clamp((int)Math.Ceiling(delta * 240), 1, 32);
            float h = (float)delta / n;
            bool grounded = false;
            for (int i = 0; i < n; i++)
            {
                var v = (bob - prev) * 0.97f;
                prev = bob;
                bob += v + Vector3.Down * 9.8f * h * h;
                var d = bob - anchor;
                if (d.Length() > Length) bob = anchor + d.Normalized() * Length;
                if (Ground != null)
                {
                    float floor = Ground(bob.X, bob.Z) + Belly;
                    if (bob.Y < floor) { bob.Y = floor; prev = prev.Lerp(bob, 0.6f); grounded = true; }
                }
            }
            var up = (anchor - bob).Normalized();
            // On the ground and slack, it lies on its side.
            if (grounded) up = new Vector3(up.X, up.Y * 0.15f, up.Z).Normalized();
            side = (side - up * side.Dot(up)).Normalized();
            if (side.LengthSquared() < 0.5f) side = up.Cross(Vector3.Forward).Normalized();
            var fwd = side.Cross(up);
            GlobalTransform = new Transform3D(new Basis(side, up, fwd), bob);
        }
    }

    /* ------------------------------------------------------------ her palms -- */

    /// <summary>The arcanist's first light (C01 shot 11): cupped in her hands, a
    /// spark that catches and fills her palms in her school's colour, lighting
    /// her face from below. It sits between her palms wherever her hands go,
    /// and grows from nothing over its first second.</summary>
    public sealed partial class Palms : Node3D
    {
        readonly Skeleton3D sk;
        readonly int left, right;
        readonly OmniLight3D light;
        readonly MeshInstance3D core;
        readonly StandardMaterial3D glow;
        float t;
        const float Grow = 1.0f;

        public Palms(Skeleton3D sk, Color c)
        {
            this.sk = sk;
            Name = "palms";
            TopLevel = true;
            left = sk.FindBone("hand_l");
            right = sk.FindBone("hand_r");
            light = new OmniLight3D { LightColor = c, OmniRange = 1.6f, LightEnergy = 0, ShadowEnabled = false, OmniAttenuation = 1.6f };
            glow = new StandardMaterial3D
            {
                ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = c.Lightened(0.55f) * new Color(1, 1, 1, 0),
                Transparency = BaseMaterial3D.TransparencyEnum.Alpha, BlendMode = BaseMaterial3D.BlendModeEnum.Add,
            };
            core = new MeshInstance3D
            {
                Mesh = new SphereMesh { Radius = 0.022f, Height = 0.044f, RadialSegments = 16, Rings = 8 }, MaterialOverride = glow,
                CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            };
            AddChild(light);
            AddChild(core);
        }

        public override void _Process(double delta)
        {
            if (left < 0 || right < 0) return;
            t += (float)delta;
            var l = sk.GlobalTransform * sk.GetBoneGlobalPose(left);
            var r = sk.GlobalTransform * sk.GetBoneGlobalPose(right);
            // Each palm's middle, a little along the fingers from the wrist; the light sits between them, in the cup.
            var at = (l.Origin + l.Basis.Y.Normalized() * 0.05f + r.Origin + r.Basis.Y.Normalized() * 0.05f) / 2 + Vector3.Up * 0.025f;
            GlobalPosition = at;
            // A spark first, catching, then the palms full: a quick flicker as it takes.
            float k = Mathf.SmoothStep(0, 1, Mathf.Clamp(t / Grow, 0, 1));
            float flicker = 1 + 0.12f * Mathf.Sin(t * 23) * Mathf.Sin(t * 7.3f) * (1 - 0.6f * k);
            light.LightEnergy = 1.8f * k * flicker;
            float s = 0.25f + 0.75f * k;
            core.Scale = Vector3.One * s;
            var c = glow.AlbedoColor;
            glow.AlbedoColor = new Color(c.R, c.G, c.B, 0.85f * Mathf.Min(1, t / 0.15f) * flicker);
        }
    }

    /// <summary>Each focus's school as a colour (the written script's: Seeking Motes
    /// violet-white, Cinderfall ember red, Rimeshard frost-white).</summary>
    public static Color School(string? item) => item switch
    {
        "ember_staff" => new Color("#ff6a2a"),
        "rime_rod" => new Color("#cfe6ff"),
        _ => new Color("#c9b6ff"),
    };
    /* ----------------------------------------------------------- the letter -- */

    static Material? paperFace, paperBack;

    /// <summary>The letter, 20 by 14 cm, folded in half and in half again
    /// with the writing inside, wet through: the ink run to blue water down
    /// the lines it was, no word left. Folded, its free edges are in her left
    /// hand's pinch and its fold stands out from the hand; open, a hand holds
    /// each side edge, the thumbs on its face, and it unfolds as they draw
    /// apart (the long fold standing out away from her until it lies flat).</summary>
    public sealed partial class Letter : MeshInstance3D
    {
        readonly Skeleton3D sk;
        public bool Open;
        const float Half = 0.10f, Tall = 0.14f;

        public Letter(Skeleton3D sk)
        {
            this.sk = sk;
            TopLevel = true;
            CastShadow = ShadowCastingSetting.On;
            if (paperFace == null)
            {
                var (face, back) = Paper();
                paperFace = PaperMat(face, BaseMaterial3D.CullModeEnum.Back);
                paperBack = PaperMat(back, BaseMaterial3D.CullModeEnum.Back);
            }
        }

        static StandardMaterial3D PaperMat(Image img, BaseMaterial3D.CullModeEnum cull) => new()
        {
            AlbedoTexture = Tex(img), Roughness = 0.5f, CullMode = cull,
            // Wet paper lets the light through.
            BacklightEnabled = true, Backlight = new Color(0.26f, 0.23f, 0.19f),
        };

        public override void _Process(double delta)
        {
            var (pl, nl) = Pinch(sk, "l");
            int handL = sk.FindBone("hand_l");
            var hand = sk.GlobalTransform * sk.GetBoneGlobalPose(handL);
            Vector3 el, er, k, up;
            float fold;
            if (!Open)
            {
                // Its two free edges together in the pinch, the fold standing out from the hand.
                var dir = pl - hand.Origin;
                dir = (dir - nl * dir.Dot(nl)).Normalized();
                el = pl - nl * 0.0009f;
                er = pl + nl * 0.0009f;
                k = dir;
                up = nl.Cross(dir).Normalized();
                if (up.Y < 0) up = -up;
                fold = 1;
            }
            else
            {
                var (pr, nr) = Pinch(sk, "r");
                var toward = (nl + nr).Normalized();
                var across = pr - pl;
                float d = across.Length();
                across = d > 1e-4f ? across / d : hand.Basis.X.Normalized();
                up = toward.Cross(across).Normalized();
                if (up.Y < 0) up = -up;
                toward = across.Cross(up).Normalized();
                // Each pinch has its edge a centimetre in; the sheet slides in them if they draw too far apart.
                float span = Mathf.Min(d + 0.016f, 2 * Half);
                var mid = (pl + pr) / 2;
                el = mid - across * span / 2;
                er = mid + across * span / 2;
                k = -toward;
                fold = 1 - Mathf.SmoothStep(0.075f, 0.17f, span);
            }
            Mesh = Shape(el, er, k, up, fold);
        }

        /// <summary>The sheet between its two side edges' midpoints (el, er),
        /// the long fold standing out along k, the short fold closed by `fold`
        /// (the bottom half up over the writing).</summary>
        static ArrayMesh Shape(Vector3 el, Vector3 er, Vector3 k, Vector3 up, float fold)
        {
            float span = el.DistanceTo(er);
            float depth = Mathf.Sqrt(Mathf.Max(0, Half * Half - span * span / 4));
            var crease = (el + er) / 2 + k * depth;
            float phi = Mathf.Pi * fold;
            var lift = -up * (Tall / 4) * fold;
            var face = new Shapes.Build();
            var back = new Shapes.Build();
            for (int side = 0; side < 2; side++)
            {
                var e = side == 0 ? el : er;
                var a = crease - e;
                a = a.LengthSquared() > 1e-8f ? a.Normalized() : k;
                var pn = (side == 0 ? a.Cross(up) : up.Cross(a)).Normalized();
                const int NS = 6, NV = 10;
                int f0 = face.P.Count, b0 = back.P.Count;
                for (int i = 0; i <= NS; i++)
                    for (int j = 0; j <= NV; j++)
                    {
                        float s = Half * i / NS, y = Tall / 2 - Tall * j / NV;
                        // Wet paper sags a little between its folds.
                        float bow = 0.003f * Mathf.Sin(Mathf.Pi * i / NS) * (1 - fold);
                        var p = e + a * s + pn * bow;
                        p += y >= 0 ? up * y : -y * (-up * Mathf.Cos(phi) + pn * Mathf.Sin(phi)) + pn * 0.0012f * (1 - Mathf.Cos(phi)) / 2;
                        p += lift;
                        var uv = new Vector2(side == 0 ? s / (2 * Half) : 1 - s / (2 * Half), j / (float)NV);
                        var n = y >= 0 ? pn : (pn * Mathf.Cos(phi) + up * Mathf.Sin(phi)).Normalized();
                        face.V(p, n, uv);
                        back.V(p, -n, uv);
                    }
                for (int i = 0; i < NS; i++)
                    for (int j = 0; j < NV; j++)
                    {
                        int q = i * (NV + 1) + j;
                        face.Quad(f0 + q, f0 + q + 1, f0 + q + NV + 2, f0 + q + NV + 1);
                        back.Quad(b0 + q, b0 + q + 1, b0 + q + NV + 2, b0 + q + NV + 1);
                    }
            }
            var mesh = face.Mesh();
            var arr = new Godot.Collections.Array();
            arr.Resize((int)Godot.Mesh.ArrayType.Max);
            arr[(int)Godot.Mesh.ArrayType.Vertex] = back.P.ToArray();
            arr[(int)Godot.Mesh.ArrayType.Normal] = back.N.ToArray();
            arr[(int)Godot.Mesh.ArrayType.TexUV] = back.U.ToArray();
            arr[(int)Godot.Mesh.ArrayType.Index] = back.I.ToArray();
            mesh.AddSurfaceFromArrays(Godot.Mesh.PrimitiveType.Triangles, arr);
            mesh.SurfaceSetMaterial(0, paperFace);
            mesh.SurfaceSetMaterial(1, paperBack);
            return mesh;
        }
    }

    /// <summary>The letter's two sides: its face, the lines of a hand run to
    /// blue water and down the sheet in streaks, tide-marked where the wet
    /// stopped, no word left; and its back, where the same shows through the
    /// wet paper, fainter. Both creased where it was folded.</summary>
    static (Image Face, Image Back) Paper()
    {
        const int W = 480, H = 336;
        var face = Image.CreateEmpty(W, H, false, Image.Format.Rgba8);
        var back = Image.CreateEmpty(W, H, false, Image.Format.Rgba8);
        // Rag paper soaked through: greyer and darker than dry, warm where it is thickest.
        var paper = new Color("#cdc1a6");
        // Iron-gall ink run to blue water: blue-black at the heart of a line, a cold wash at its edges.
        var ink = new Color("#2a3f6e");
        var wash = new Color("#5f7aa6");
        var lines = new List<float>();
        for (float v = 0.12f; v < 0.86f; v += 0.058f) lines.Add(v);
        for (int py = 0; py < H; py++)
            for (int px = 0; px < W; px++)
            {
                float u = (px + 0.5f) / W, v = (py + 0.5f) / H;
                float wet = Noise(u * 3, v * 3) * 0.6f + Noise(u * 17, v * 17) * 0.4f;
                float edge = Mathf.Min(Mathf.Min(u, 1 - u), Mathf.Min(v, 1 - v));
                var c = paper.Darkened(0.14f * wet + 0.22f * Mathf.Clamp(1 - edge * 14, 0, 1));
                // Each line of the hand is now a bleed where its words were: a dark core with
                // feathered edges, broken between words, the last line short; below it the
                // ink ran down the sheet in streaks as the water drained.
                float core = 0, bleed = 0;
                for (int i = 0; i < lines.Count; i++)
                {
                    float lv = lines[i], dv = v - lv;
                    float end = i == lines.Count - 1 ? 0.42f : 0.88f - 0.12f * Noise(i * 7.3f, 1.5f);
                    float margin = 0.09f + 0.015f * Noise(i * 3.1f, 9);
                    float inLine = Mathf.Clamp((u - margin) * 40, 0, 1) * Mathf.Clamp((end - u) * 30, 0, 1);
                    if (inLine <= 0) continue;
                    float words = Mathf.Clamp((Noise(u * 22 + i * 3, i * 1.7f) - 0.28f) * 3.2f, 0, 1) * inLine;
                    float wobble = (Noise(u * 9, i * 4.4f) - 0.5f) * 0.012f;
                    float d = dv - wobble;
                    float k = Mathf.Exp(-d * d / (2 * 0.0075f * 0.0075f));
                    float b = Mathf.Exp(-d * d / (2 * 0.02f * 0.02f));
                    float run = 0;
                    if (d > 0)
                    {
                        float len = 0.025f + 0.09f * Mathf.Pow(Noise(u * 48 + i * 11, 4.1f), 1.8f);
                        float streak = 0.4f + 0.6f * Mathf.Pow(Noise(u * 140, i * 2.3f), 1.5f);
                        run = Mathf.Clamp(1 - d / len, 0, 1) * streak;
                    }
                    core = Mathf.Max(core, words * k);
                    bleed = Mathf.Max(bleed, words * Mathf.Max(b * 0.75f, run * 0.65f));
                }
                float grain = 0.8f + 0.4f * Noise(u * 60, v * 60);
                // Tide-lines where the water stopped: a darker margin round each wet patch.
                float tide = Mathf.Clamp(1 - Mathf.Abs(Noise(u * 4 + 9, v * 4 + 2) - 0.55f) / 0.01f, 0, 1) * 0.14f;
                float fu = Mathf.Abs(u - 0.5f) * W, fv = Mathf.Abs(v - 0.5f) * H;
                float crease = Mathf.Max(Mathf.Clamp(1 - fu / 1.8f, 0, 1), Mathf.Clamp(1 - fv / 1.8f, 0, 1)) * 0.28f;
                float shine = Mathf.Max(fu is > 1.8f and < 5f ? 1 : 0, fv is > 1.8f and < 5f ? 1 : 0) * 0.05f;
                var basec = c.Darkened(tide + crease).Lightened(shine);
                var f = basec.Lerp(wash, Mathf.Clamp(bleed * grain, 0, 0.7f)).Lerp(ink, Mathf.Clamp(core * grain * 0.85f, 0, 0.8f));
                face.SetPixel(px, py, f);
                // Through the wet sheet the same shows on its back, fainter and colder.
                back.SetPixel(px, py, basec.Lerp(wash, Mathf.Clamp((bleed * 0.4f + core * 0.3f) * grain, 0, 0.35f)));
            }
        if (Args.Has("dumppaper"))
        {
            face.SavePng("res://.shots/letter_face.png");
            back.SavePng("res://.shots/letter_back.png");
        }
        return (face, back);
    }
}

using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The instrument along the foot (the owner, 5 October: "the bottom skill bar and health globes and
/// stuff need to be incredible, its a keystone of that kind of game"; "one composed group, not loose
/// pieces"). Her irons: two cuffs, one at each end, joined by a chain. The left cuff holds her life's
/// blood, the right the art in her hand, its charge rising as it readies; beside each, smaller, what
/// goes with it (the draught by her life, the dash by her art); between them the six places of what
/// fires by itself; and under those the chain itself, heating link by link as the ember gathers, a
/// lock at its middle stamped with the night's level that springs open as she rises. Mirrored about
/// the screen's middle in every part. Drawn here until UI art's iron is in (art/ui/hud/, see
/// docs/team/ui_design.md "For UI art"); every piece asks for its art by name first.
/// </summary>
public partial class Instrument : Control
{
    /* The geometry, in the HUD's 1920 by 1080 (docs/design/UI_RESEARCH.md, "The HUD"). */
    /// <summary>The vessels' glass, and the cuff's iron band round it.</summary>
    public const float R = 60, Band = 13;
    /// <summary>The vessels' middles from the screen's: mirrored either side.</summary>
    public const float Reach = 352;
    /// <summary>The vessels' middles' height, the cuffs 30 px clear of the foot (room for the lock).</summary>
    public const float VY = 1080 - 30 - (R + Band);
    /// <summary>The six places: their size, the gap between, and their tops (their middles 20 px above
    /// the vessels', so the chain and the keys have room under them).</summary>
    public const float Sock = 58, SockGap = 8, SockY = VY - 20 - Sock / 2;
    /// <summary>The draught's and the dash's glass, and their iron.</summary>
    public const float SmallR = 23, SmallBand = 6;
    /// <summary>Where the chain leaves each cuff: an eye this far below the level, on the inner side.</summary>
    public const float EyeAngle = 32;

    public static float SocksX => 960 - (6 * Sock + 5 * SockGap) / 2;
    public static float SmallY => SockY + Sock / 2;
    public static Vector2 LifeAt => new(960 - Reach, VY);
    public static Vector2 ArtAt => new(960 + Reach, VY);
    public static Vector2 DraughtAt => new(SocksX - 14 - SmallR - SmallBand, SmallY);
    public static Vector2 DashAt => new(SocksX + 6 * Sock + 5 * SockGap + 14 + SmallR + SmallBand, SmallY);
    /// <summary>The chain's ends, at the cuffs' eyes.</summary>
    public static Vector2 EyeL => LifeAt + new Vector2(Mathf.Cos(Mathf.DegToRad(EyeAngle)), Mathf.Sin(Mathf.DegToRad(EyeAngle))) * (R + Band + 2);
    public static Vector2 EyeR => new(1920 - EyeL.X, EyeL.Y);
    /// <summary>All of it on the screen, from the statuses over her life to the lock under the chain.</summary>
    public static Rect2 Bounds => new(960 - Reach - R - Band - 16, VY - R - Band - 48, 2 * (Reach + R + Band + 16), 1080 - (VY - R - Band - 48));

    public readonly Vessel Life, Art;
    public readonly Socket[] Sockets = new Socket[Content.Weapons.MaxWeapons];
    public readonly Round Draught, Dash;
    public readonly EmberChain Chain;
    /// <summary>The passives over the six places; what is on her (burning, shielded) over her life; the
    /// art's state in a word over the art.</summary>
    public readonly HBoxContainer Passives, Statuses;
    public readonly Label ArtWord;
    readonly Control lifeKey = new(), artKey = new(), draughtKey = new(), dashKey = new();

    public Instrument()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Position = Vector2.Zero;
        Size = new Vector2(1920, 1080);
        // (the chain first: its eyes and the cuffs lie over its ends)
        Chain = new EmberChain();
        AddChild(Chain);
        Life = new Vessel(true) { Position = LifeAt - Vessel.Half };
        AddChild(Life);
        Art = new Vessel(false) { Position = ArtAt - Vessel.Half };
        AddChild(Art);
        for (int i = 0; i < Sockets.Length; i++)
        {
            Sockets[i] = new Socket { Position = new Vector2(SocksX + i * (Sock + SockGap), SockY) };
            AddChild(Sockets[i]);
        }
        Draught = new Round(Round.Kind.Draught) { Position = DraughtAt - Round.Half };
        AddChild(Draught);
        Dash = new Round(Round.Kind.Dash) { Position = DashAt - Round.Half };
        AddChild(Dash);
        Passives = Style.H(6);
        Passives.Alignment = BoxContainer.AlignmentMode.Center;
        Passives.Position = new Vector2(SocksX, SockY - 34);
        Passives.Size = new Vector2(6 * Sock + 5 * SockGap, 28);
        AddChild(Passives);
        Statuses = Style.H(10);
        Statuses.Alignment = BoxContainer.AlignmentMode.Center;
        Statuses.Position = new Vector2(LifeAt.X - 150, VY - R - Band - 40);
        Statuses.Size = new Vector2(300, 30);
        AddChild(Statuses);
        ArtWord = Style.Label("", Style.UiHeavy, Style.Badge, new Color("#d8b8ff"), false, HorizontalAlignment.Center);
        ArtWord.Position = new Vector2(ArtAt.X - 150, VY - R - Band - 30);
        ArtWord.Size = new Vector2(300, 20);
        AddChild(ArtWord);
        foreach (var k in new[] { lifeKey, artKey, draughtKey, dashKey }) { k.MouseFilter = MouseFilterEnum.Ignore; AddChild(k); }
        Keys();
    }

    /// <summary>The keys, as the device in hand has them: on the art's cuff at its foot, and over the
    /// draught's and the dash's iron at theirs.</summary>
    public void Keys()
    {
        void Put(Control holder, Act a, Vector2 at)
        {
            foreach (var c in holder.GetChildren()) { holder.RemoveChild(c); c.QueueFree(); }
            var k = Style.Prompt(a);
            // Centred on its place whatever its width (a cap is as wide as its word).
            k.SetAnchorsPreset(LayoutPreset.Center);
            k.GrowHorizontal = GrowDirection.Both;
            k.GrowVertical = GrowDirection.Both;
            holder.AddChild(k);
            holder.Size = Vector2.Zero;
            holder.Position = at;
        }
        Put(artKey, Act.Ability, ArtAt + new Vector2(0, R + Band - 2));
        Put(draughtKey, Act.Ultimate, DraughtAt + new Vector2(0, SmallR + SmallBand - 1));
        Put(dashKey, Act.Dash, DashAt + new Vector2(0, SmallR + SmallBand - 1));
    }

    /// <summary>The six places' spread: by night all six from the left (the empty ones the places still to
    /// come), by day only what is carried, centred on the middle (the day has no places to promise).</summary>
    public void Lay(int shown, bool all)
    {
        int n = all ? Sockets.Length : Math.Min(shown, Sockets.Length);
        float x0 = 960 - (n * Sock + Math.Max(0, n - 1) * SockGap) / 2;
        for (int i = 0; i < Sockets.Length; i++)
        {
            Sockets[i].Visible = i < n;
            Sockets[i].Position = new Vector2(x0 + i * (Sock + SockGap), SockY);
        }
    }
}

/// <summary>A glass vessel in its iron cuff: her life (blood, its number) or the art in her hand (its
/// glyph, its charge rising as it readies, the seconds left). The liquid is the vessel shader's
/// (shaders/hud_vessel.gdshader); the cuff is UI art's (hud/cuff.png, the left cuff; mirrored for the
/// right) or drawn.</summary>
public partial class Vessel : Control
{
    public static readonly Vector2 Half = new(Instrument.R + Instrument.Band + 14, Instrument.R + Instrument.Band + 14);
    readonly bool life;
    readonly ColorRect glass;
    readonly ShaderMaterial mat;
    readonly Cuff cuff;
    readonly Control over;
    public float Level = 1, Trail = 1, Shield, Pulse, Glow;
    public string Number = "";
    public Texture2D? Glyph;
    public Color GlyphTint = Colors.White;
    float slosh, shownLevel = -1;

    public Vessel(bool life)
    {
        this.life = life;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Half * 2;
        PivotOffset = Half;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_vessel.gdshader") };
        mat.SetShaderParameter("seed", life ? 0.13f : 0.71f);
        if (!life) Liquid(new Color("#ffcf7a"), new Color("#a8460c"), new Color("#0c0907"));
        glass = new ColorRect { Material = mat, MouseFilter = MouseFilterEnum.Ignore, Position = Half - new Vector2(Instrument.R, Instrument.R), Size = new Vector2(Instrument.R * 2, Instrument.R * 2) };
        AddChild(glass);
        // UI art's glass over the liquid (its window's light caught high on the left, its rim's shade),
        // sized so its glass's edge meets the cuff's seat.
        if (UiArt.Art("hud/globe_glass.png") is { } painted)
        {
            float gs = Instrument.R * 2 / 0.91f;
            AddChild(new TextureRect { Texture = painted, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
                MouseFilter = MouseFilterEnum.Ignore, Position = Half - new Vector2(gs, gs) / 2, Size = new Vector2(gs, gs) });
            mat.SetShaderParameter("own_light", 0f);
        }
        cuff = new Cuff(Instrument.R, Instrument.Band, mirrored: !life, Half);
        AddChild(cuff);
        over = new Over(this);
        AddChild(over);
    }

    /// <summary>The liquid's colours: at its surface, at its foot, and the empty glass.</summary>
    public void Liquid(Color shallow, Color deep, Color? empty = null)
    {
        mat.SetShaderParameter("shallow", shallow);
        mat.SetShaderParameter("deep", deep);
        if (empty is Color e) mat.SetShaderParameter("empty", e);
    }

    public override void _Process(double delta)
    {
        float dt = (float)delta;
        // A sudden change (a blow, a draught, the art spent) sloshes the surface, which settles over a
        // second or so; the art's steady filling does not.
        if (shownLevel >= 0 && Math.Abs(Level - shownLevel) > 0.04f) slosh = Math.Min(1, slosh + Math.Abs(Level - shownLevel) * 4);
        shownLevel = Level;
        slosh = Mathf.MoveToward(slosh, 0, dt * 0.9f);
        mat.SetShaderParameter("level", Level);
        // (only her life leaves a trail as it falls)
        mat.SetShaderParameter("trail", life ? Math.Max(Trail, Level) : Level);
        mat.SetShaderParameter("shield", Shield);
        mat.SetShaderParameter("pulse", Pulse);
        mat.SetShaderParameter("slosh", slosh);
        mat.SetShaderParameter("glow", Glow);
        over.QueueRedraw();
    }

    /// <summary>Over the glass: the art's glyph, the number (her life, or the seconds the art has left).</summary>
    partial class Over : Control
    {
        readonly Vessel v;
        public Over(Vessel v) { this.v = v; MouseFilter = MouseFilterEnum.Ignore; Size = v.Size; }

        public override void _Draw()
        {
            var c = Size / 2;
            if (v.Glyph is { } g)
            {
                // The art's mark, edged in the dark so it reads on the empty glass and the bright charge alike.
                float s = Instrument.R * 1.1f;
                var r = new Rect2(c - new Vector2(s, s) / 2, new Vector2(s, s));
                var edge = new Color(0.05f, 0.03f, 0.02f, 0.75f * v.GlyphTint.A);
                for (int i = 0; i < 8; i++)
                {
                    var d = new Vector2(Mathf.Cos(i * Mathf.Tau / 8), Mathf.Sin(i * Mathf.Tau / 8)) * 1.6f;
                    DrawTextureRect(g, new Rect2(r.Position + d, r.Size), false, edge);
                }
                DrawTextureRect(g, r, false, v.GlyphTint);
            }
            if (v.Number == "") return;
            var f = v.life ? Style.UiHeavy : Style.Display;
            int fs = v.life ? 24 : 34;
            var ts = f.GetStringSize(v.Number, HorizontalAlignment.Left, -1, fs);
            var at = c + new Vector2(-ts.X / 2, fs * 0.36f);
            DrawStringOutline(f, at + new Vector2(0, 1), v.Number, HorizontalAlignment.Left, -1, fs, 6, new Color(0, 0, 0, 0.55f));
            DrawString(f, at, v.Number, HorizontalAlignment.Left, -1, fs, new Color("#fff4ea"));
        }
    }
}

/// <summary>The iron round a vessel: hud/cuff.png (or hud/cuff_small.png round the draught and the dash)
/// when UI art has made it, else drawn: a forged band, lit from above, its inner edge sunk where the
/// glass sits, a hinge's knuckle on its outer side and, on its inner side, the eye the chain runs from.</summary>
public partial class Cuff : Control
{
    readonly float r, band;
    readonly bool mirrored, small;

    public Cuff(float r, float band, bool mirrored, Vector2 half, bool small = false)
    {
        this.r = r; this.band = band; this.mirrored = mirrored; this.small = small;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = half * 2;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
    }

    public override void _Draw()
    {
        var c = Size / 2;
        var art = UiArt.Art(small ? "hud/cuff_small.png" : "hud/cuff.png");
        if (art != null)
        {
            var s = art.GetSize();
            if (mirrored) DrawSetTransform(c, 0, new Vector2(-1, 1)); else DrawSetTransform(c);
            DrawTexture(art, -s / 2);
            DrawSetTransform(Vector2.Zero);
            return;
        }
        float ro = r + band;
        // The hinge's knuckle on the outer side, and the eye on the inner (under the band, so the band's
        // edge runs over their roots).
        float side = mirrored ? 1 : -1;
        if (!small)
        {
            var k = c + new Vector2(side * (ro + 3), 0);
            DrawRect(new Rect2(k - new Vector2(6, 13), new Vector2(12, 26)), Iron(0.32f));
            DrawRect(new Rect2(k - new Vector2(6, 13), new Vector2(12, 26)), new Color(0, 0, 0, 0.9f), false, 1.2f);
            DrawLine(k + new Vector2(-6, -4.5f), k + new Vector2(6, -4.5f), new Color(0, 0, 0, 0.75f), 1.2f, true);
            DrawLine(k + new Vector2(-6, 4.5f), k + new Vector2(6, 4.5f), new Color(0, 0, 0, 0.75f), 1.2f, true);
            DrawLine(k + new Vector2(-5, -12), k + new Vector2(5, -12), new Color(1, 0.95f, 0.85f, 0.18f), 1, true);
            float a = Mathf.DegToRad(Instrument.EyeAngle);
            var eye = c + new Vector2(-side * Mathf.Cos(a), Mathf.Sin(a)) * (ro + 2);
            DrawArc(eye, 6.5f, 0, Mathf.Tau, 24, Iron(0.3f), 4, true);
            DrawArc(eye, 8.6f, 0, Mathf.Tau, 24, new Color(0, 0, 0, 0.8f), 1.2f, true);
        }
        Band(this, c, r, band);
        if (!small)
            // Two rivets either side of the hinge, the cuff's only ornament.
            foreach (float dy in new[] { -1f, 1f })
            {
                float a = Mathf.Pi * (mirrored ? 0 : 1) + dy * 0.42f * side;
                var p = c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * (ro - band / 2);
                DrawCircle(p, 2.4f, Iron(0.25f));
                DrawCircle(p - new Vector2(0.6f, 0.7f), 1.2f, Iron(0.85f));
            }
    }

    /// <summary>A forged band round a glass (the cuffs, the minimap's bezel): drawn as rings from its
    /// outer edge in, round in section (the light rises across its middle), lit from the upper left and
    /// dark at its foot; a dark line outside, the sunk seat the glass sits in, a hair of light high on
    /// its upper left.</summary>
    public static void Band(CanvasItem ci, Vector2 c, float r, float band)
    {
        float ro = r + band;
        int rings = (int)Math.Max(4, band * 1.5f);
        for (int i = 0; i < rings; i++)
        {
            float rr = ro - (i + 0.5f) * band / rings;
            float bulge = Mathf.Sin((i + 0.5f) / rings * Mathf.Pi);
            const int seg = 96;
            var pts = new Vector2[seg + 1];
            var cols = new Color[seg + 1];
            for (int j = 0; j <= seg; j++)
            {
                float t = j * Mathf.Tau / seg;
                var d = new Vector2(Mathf.Cos(t), Mathf.Sin(t));
                pts[j] = c + d * rr;
                float lit = Mathf.Clamp(-d.Y * 0.55f - d.X * 0.3f, -1, 1);
                cols[j] = Iron(0.16f + 0.24f * bulge + 0.32f * lit * bulge);
            }
            ci.DrawPolylineColors(pts, cols, band / rings + 0.9f, true);
        }
        ci.DrawArc(c, ro, 0, Mathf.Tau, 96, new Color(0, 0, 0, 0.85f), 1.4f, true);
        ci.DrawArc(c, r + 0.6f, 0, Mathf.Tau, 96, new Color(0, 0, 0, 0.95f), 2.2f, true);
        ci.DrawArc(c, ro - 1.3f, Mathf.Pi * 1.08f, Mathf.Pi * 1.62f, 32, new Color(1, 0.94f, 0.82f, 0.22f), 1.1f, true);
    }

    /// <summary>The iron's colour at a light (0 dark to 1 bright): a warm grey-black.</summary>
    public static Color Iron(float light) => new Color(0.16f, 0.145f, 0.13f).Lerp(new Color(0.62f, 0.58f, 0.53f), Mathf.Clamp(light, 0, 1) * 0.75f);
}

/// <summary>One of the six places for what fires by itself: its glyph in its school's colour on a dark
/// ground in a forged square socket, a shade sweeping off as it readies and a flash as it fires, and
/// its rank as eight rivets along the socket's foot, lit to its rank. At the top with what it evolves
/// with, the socket breathes gold; evolved, it is rimmed in gold. Empty, it is a quiet dark socket.
/// UI art's hud/socket.png and socket_empty.png replace the drawn iron.</summary>
public partial class Socket : Control
{
    public string Id = "";
    Texture2D? art;
    Color school;
    int rank, max = 8;
    bool evolved, ripe, filled;
    double ready = 1, lastReady = 1, flash, t, crown = -1;

    public Socket()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(Instrument.Sock, Instrument.Sock);
        PivotOffset = Size / 2;
    }

    public void Empty()
    {
        if (!filled && Id == "") return;
        filled = false; Id = ""; art = null; crown = -1; Scale = Vector2.One; Modulate = Colors.White;
        QueueRedraw();
    }

    public void Show(string id, string glyph, Color school, double ready, int rank, int max, bool evolved, bool canEvolve)
    {
        if (id != Id || !filled) { Id = id; filled = true; lastReady = ready; }
        // (drawn glyphs, one hand for the row: the painted set mixes full colour and line)
        art = Glyphs.Texture(glyph, 78, school, line: true);
        this.school = school; this.rank = rank; this.max = Math.Max(1, max); this.evolved = evolved; ripe = canEvolve;
        if (ready < lastReady - 0.4) flash = 1;
        lastReady = ready;
        this.ready = ready;
    }

    /// <summary>It has evolved: the place swells and burns gold, settling over a second.</summary>
    public void Crown() => crown = 0;

    public override void _Process(double delta)
    {
        t += delta;
        flash = Math.Max(0, flash - delta * 4);
        if (crown >= 0)
        {
            crown += delta;
            float k = (float)Math.Clamp(crown / 1.3, 0, 1), e = (1 - k) * (1 - k);
            Scale = Vector2.One * (1 + 0.45f * e * (0.75f + 0.25f * Mathf.Cos((float)crown * 18)));
            Modulate = Colors.White.Lerp(new Color(2.2f, 1.8f, 1.0f), e);
            if (crown >= 1.3) { crown = -1; Scale = Vector2.One; Modulate = Colors.White; }
        }
        QueueRedraw();
    }

    public override void _Draw()
    {
        float s = Size.X;
        var art2 = UiArt.Art(filled ? "hud/socket.png" : "hud/socket_empty.png");
        if (!filled)
        {
            // A place still to come: a dark seat with a ghost of the iron, quiet but there, so the six
            // read as one row however few are filled (empty is quiet, not gone).
            if (art2 != null) { DrawTextureRect(art2, new Rect2(Vector2.Zero, Size), false); return; }
            DrawRect(new Rect2(3, 3, s - 6, s - 6), new Color(0.03f, 0.025f, 0.035f, 0.62f));
            Frame(s, 0.3f);
            return;
        }
        // The ground the glyph sits on: near black, warmed a breath by its school.
        var ground = new Color(0.045f, 0.04f, 0.05f).Lerp(school, 0.06f) with { A = 0.94f };
        DrawRect(new Rect2(3, 3, s - 6, s - 6), ground);
        if (art2 != null) DrawTextureRect(art2, new Rect2(Vector2.Zero, Size), false);
        else Frame(s, 1f);
        // The glyph, brighter when it is ready.
        if (art != null)
        {
            float g = s * 0.66f;
            var col = ready >= 0.98 ? new Color(1.25f, 1.25f, 1.25f) : Colors.White;
            DrawTextureRect(art, new Rect2((s - g) / 2, (s - g) / 2 - 3, g, g), false, col.Lerp(new Color(2.2f, 2.0f, 1.7f), (float)flash));
        }
        // The shade that sweeps off as it readies, from the top down.
        if (ready < 0.98) DrawRect(new Rect2(3, 3, s - 6, (s - 6) * (float)(1 - ready)), new Color(0.02f, 0.015f, 0.03f, 0.6f));
        // The rank: eight rivets along the foot, lit to it.
        float y = s - 7.5f, x0 = 9, x1 = s - 9;
        for (int i = 0; i < max; i++)
        {
            float x = max == 1 ? s / 2 : x0 + i * (x1 - x0) / (max - 1);
            bool lit = i < rank;
            DrawCircle(new Vector2(x, y + 0.6f), 2.3f, new Color(0, 0, 0, 0.85f));
            DrawCircle(new Vector2(x, y), 1.8f, lit ? (evolved || ripe ? Style.EmberHi : school.Lightened(0.15f)) : new Color(0.2f, 0.18f, 0.17f));
        }
        // Ready to evolve: the rim breathes gold until the draft offers it; evolved, it is gold.
        if (evolved || ripe)
        {
            float a = evolved ? 0.9f : 0.45f + 0.4f * (0.5f + 0.5f * Mathf.Sin((float)t * 4.5f));
            DrawRect(new Rect2(1, 1, s - 2, s - 2), Style.Gold with { A = a }, false, 2);
        }
    }

    /// <summary>The socket's iron, drawn: a square ring four pixels wide, lit at the top and left, dark at
    /// the foot and right, and inside it the seat sunk the other way.</summary>
    void Frame(float s, float a)
    {
        var top = Cuff.Iron(0.75f) with { A = a };
        var foot = Cuff.Iron(0.18f) with { A = a };
        var mid = Cuff.Iron(0.42f) with { A = a };
        DrawRect(new Rect2(0, 0, s, s), new Color(0, 0, 0, 0.85f * a), false, 1.2f);
        DrawRect(new Rect2(1.5f, 1.5f, s - 3, s - 3), mid, false, 3);
        DrawLine(new Vector2(1, 1.2f), new Vector2(s - 1, 1.2f), top, 1.1f);
        DrawLine(new Vector2(1.2f, 1), new Vector2(1.2f, s - 1), top with { A = 0.6f * a }, 1.1f);
        DrawLine(new Vector2(1, s - 1.2f), new Vector2(s - 1, s - 1.2f), foot, 1.1f);
        DrawLine(new Vector2(s - 1.2f, 1), new Vector2(s - 1.2f, s - 1), foot, 1.1f);
        // The seat: dark along its top and left (in shadow), a hair of light along its foot.
        DrawLine(new Vector2(3.5f, 3.8f), new Vector2(s - 3.5f, 3.8f), new Color(0, 0, 0, 0.7f * a), 1.4f);
        DrawLine(new Vector2(3.8f, 3.5f), new Vector2(3.8f, s - 3.5f), new Color(0, 0, 0, 0.55f * a), 1.4f);
        DrawLine(new Vector2(4, s - 3.6f), new Vector2(s - 4, s - 3.6f), new Color(1, 0.92f, 0.78f, 0.12f * a), 1);
    }
}

/// <summary>The draught by her life and the dash by her art: a small glass in a small cuff. The draught
/// shows its flask and how many are left; the dash its mark and its charges as arcs round the inside of
/// its glass, the one recharging filling as it comes back.</summary>
public partial class Round : Control
{
    public enum Kind { Draught, Dash }
    public static readonly Vector2 Half = new(Instrument.SmallR + Instrument.SmallBand + 6, Instrument.SmallR + Instrument.SmallBand + 6);
    readonly Kind kind;
    readonly Cuff cuff;
    readonly Control icon;
    public int Count, Max = 2;
    public float Recharge;

    public Round(Kind kind)
    {
        this.kind = kind;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Half * 2;
        cuff = new Cuff(Instrument.SmallR, Instrument.SmallBand, kind == Kind.Dash, Half, small: true);
        // The glass first, under the iron.
        AddChild(new Glass(this));
        AddChild(cuff);
        float s = Instrument.SmallR * 1.5f;
        icon = kind == Kind.Draught ? ItemPhotos.Icon("potion", (int)s, new Color("#ff8a80")) : Glyphs.Icon("dash", (int)s, Style.Ink);
        icon.Position = Half - new Vector2(s, s) / 2;
        icon.Size = new Vector2(s, s);
        icon.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(icon);
        AddChild(new Count2(this));
    }

    public override void _Process(double delta)
    {
        // An empty draught is dimmed, not hidden: its place keeps the instrument whole.
        icon.Modulate = kind == Kind.Draught && Count <= 0 ? new Color(0.45f, 0.42f, 0.42f, 0.7f) : Colors.White;
        foreach (var c in GetChildren()) if (c is CanvasItem ci && ci != icon && ci != cuff) ci.QueueRedraw();
    }

    partial class Glass : Control
    {
        readonly Round o;
        public Glass(Round o) { this.o = o; MouseFilter = MouseFilterEnum.Ignore; Size = o.Size; }

        public override void _Draw()
        {
            var c = Size / 2;
            float r = Instrument.SmallR;
            DrawCircle(c, r, new Color(0.05f, 0.04f, 0.05f, 0.95f));
            DrawCircle(c + new Vector2(-r * 0.3f, -r * 0.4f), r * 0.45f, new Color(1, 1, 1, 0.04f));
            if (o.kind != Kind.Dash) return;
            // The charges, round the inside of the glass from the top: lit when held, the next filling.
            int n = Math.Max(1, o.Max);
            float gap = 0.22f, span = (Mathf.Tau - gap * n) / n;
            for (int i = 0; i < n; i++)
            {
                float a0 = -Mathf.Pi / 2 + gap / 2 + i * (span + gap);
                DrawArc(c, r - 3.5f, a0, a0 + span, 24, new Color(0, 0, 0, 0.6f), 4.5f, true);
                float fill = i < o.Count ? 1 : i == o.Count ? o.Recharge : 0;
                if (fill > 0) DrawArc(c, r - 3.5f, a0, a0 + span * fill, 24, i < o.Count ? new Color("#efe6d6") : new Color("#efe6d6") with { A = 0.4f }, 3, true);
            }
        }
    }

    partial class Count2 : Control
    {
        readonly Round o;
        public Count2(Round o) { this.o = o; MouseFilter = MouseFilterEnum.Ignore; Size = o.Size; }

        public override void _Draw()
        {
            if (o.kind != Kind.Draught) return;
            var f = Style.UiHeavy;
            string s = o.Count.ToString();
            var at = Size / 2 + new Vector2(Instrument.SmallR * 0.42f, Instrument.SmallR * 0.78f);
            DrawStringOutline(f, at, s, HorizontalAlignment.Left, -1, 15, 5, new Color(0, 0, 0, 0.9f));
            DrawString(f, at, s, HorizontalAlignment.Left, -1, 15, o.Count > 0 ? Colors.White : Style.BloodHi);
        }
    }
}

/// <summary>
/// The chain between the cuffs: the ember (by night) or her experience (by day) as heat along its
/// links. By night the links it has reached glow a deep red and the last few burn bright, so the eye
/// finds the leading edge; the rest hang cold. By day, steel brightened to where she has grown. At its
/// middle a lock, the level stamped on it; when the ember fills, the whole chain flares, the lock
/// springs open and swings, and the heat drains back to what carried over. UI art's links
/// (art/ui/chain/, the book's tabs' own) at four fifths of their size; hud/lock.png and lock_open.png
/// for the lock when they are made.
/// </summary>
public partial class EmberChain : Control
{
    const float LinkScale = 0.8f, Sag = 4;
    float fill, flash, swing, swingV, open;
    bool ember = true;
    int level = 1;
    readonly Glow glow;
    readonly Lock lck;

    public EmberChain()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(1920, 1080);
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        glow = new Glow(this);
        AddChild(glow);
        lck = new Lock(this);
        AddChild(lck);
    }

    /// <summary>How full (0 to 1), whether it is the ember or her experience, and the level.</summary>
    public void Set(float fill, bool ember, int level)
    {
        this.fill = Mathf.Clamp(fill, 0, 1);
        this.ember = ember;
        this.level = Math.Max(1, level);
    }

    /// <summary>A level gained: the chain flares, the lock springs and swings.</summary>
    public void Rise()
    {
        flash = 1;
        open = 1;
        swingV += 7;
    }

    public override void _Process(double delta)
    {
        float dt = (float)Math.Min(delta, 1 / 30.0);
        flash = Mathf.MoveToward(flash, 0, dt / 0.55f);
        open = Mathf.MoveToward(open, 0, dt / 0.45f);
        // The lock swings on its link and settles, a pendulum a little under its damping.
        swingV += (-60 * swing - 3.2f * swingV) * dt;
        swing += swingV * dt;
        QueueRedraw();
        glow.QueueRedraw();
        lck.QueueRedraw();
    }

    Vector2 A => Instrument.EyeL;
    Vector2 B => Instrument.EyeR;
    float Len => B.X - A.X;
    float Pitch => 17.2f * LinkScale;
    int Count => (int)Math.Floor(Len / Pitch);

    /// <summary>A point along the chain (0 at the left eye, 1 at the right), on its shallow sag.</summary>
    Vector2 At(float t) => new(Mathf.Lerp(A.X, B.X, t), Mathf.Lerp(A.Y, B.Y, t) + Sag * 4 * t * (1 - t));

    /// <summary>How hot the link at t is (0 cold to 1 white-hot): the body it has reached a deep red, the
    /// last links bright, a flare over all as she rises.</summary>
    float Heat(float t)
    {
        if (fill <= 0) return flash;
        float lead = 3.5f / Count;
        float h = t > fill - lead ? 0.75f + 0.25f * Mathf.Clamp(1 - (fill - t) / lead, 0, 1) : 0.5f;
        // The link the edge is in warms as the edge crosses it.
        h *= Mathf.Clamp((fill - t) * Count + 0.5f, 0, 1);
        return Math.Max(h, flash);
    }

    public override void _Draw()
    {
        int n = Count;
        // Face-on links first; those on edge pass through their ends and lie over them.
        for (int pass = 0; pass < 2; pass++)
            for (int k = 0; k <= n; k++)
            {
                bool face = (k & 1) == 0;
                if (face != (pass == 0)) continue;
                float t = (float)k / n;
                var at = At(t);
                float ang = Mathf.Atan2(At(Math.Min(1, t + 0.01f)).Y - At(Math.Max(0, t - 0.01f)).Y, (Math.Min(1, t + 0.01f) - Math.Max(0, t - 0.01f)) * Len);
                DrawSetTransform(at, ang, new Vector2(LinkScale, LinkScale));
                int variant = (k * 7 + 3) % 6;
                string shape = face ? "face" : "edge";
                float heat = ember ? Heat(t) : 0;
                if (ChainTabs.Sprite($"{shape}_{variant}") is { } cold)
                {
                    // By night the cold links are dulled, so the heat is what the eye finds; by day, steel
                    // brightened where she has grown, dulled beyond.
                    var tint = ember ? new Color(0.72f, 0.7f, 0.68f) : t <= fill ? new Color(1.45f, 1.5f, 1.6f) : new Color(0.62f, 0.62f, 0.66f);
                    if (!ember && flash > 0) tint = tint.Lerp(new Color(2.2f, 2.3f, 2.5f), flash);
                    DrawTexture(cold, -cold.GetSize() / 2, tint);
                    if (heat > 0 && ChainTabs.Sprite($"warm_{shape}_{variant}") is { } warm)
                        DrawTexture(warm, -warm.GetSize() / 2, Colors.White with { A = Math.Min(1, heat / 0.5f) });
                    if (heat > 0.6f && ChainTabs.Sprite($"hot_{shape}_{variant}") is { } hot)
                        DrawTexture(hot, -hot.GetSize() / 2, Colors.White with { A = (heat - 0.6f) / 0.4f });
                }
                else
                {
                    // Drawn links, until the art is there.
                    var iron = Cuff.Iron(ember ? 0.5f : t <= fill ? 0.95f : 0.4f).Lerp(ChainTabs.HeatColour(heat), heat > 0 ? 0.85f : 0);
                    if (face)
                    {
                        var pts = new Vector2[17];
                        for (int i = 0; i <= 16; i++) pts[i] = new Vector2(Mathf.Cos(i * Mathf.Tau / 16) * 13, Mathf.Sin(i * Mathf.Tau / 16) * 7.5f);
                        DrawPolyline(pts, iron, 3.4f, true);
                    }
                    else DrawLine(new Vector2(-12, 0), new Vector2(12, 0), iron.Darkened(0.12f), 4.4f, true);
                }
            }
        DrawSetTransform(Vector2.Zero);
    }

    /// <summary>The heat's light over the links, added: a soft glow along what it has reached, brightest
    /// at the leading edge, breathing as embers do; all of it as she rises.</summary>
    partial class Glow : Control
    {
        static GradientTexture2D? soft;
        readonly EmberChain c;

        public Glow(EmberChain c)
        {
            this.c = c;
            MouseFilter = MouseFilterEnum.Ignore;
            Size = c.Size;
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add };
            soft ??= new GradientTexture2D
            {
                Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
                Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.35f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.35f, 1f } },
            };
        }

        public override void _Draw()
        {
            if (!c.ember && c.flash <= 0) return;
            float now = Time.GetTicksMsec() / 1000f;
            float flick = 1 + 0.10f * Mathf.Sin(now * 23) + 0.07f * Mathf.Sin(now * 37.3f + 1.7f);
            int n = c.Count;
            for (int k = 0; k <= n; k += 2)
            {
                float t = (float)k / n;
                float h = c.ember ? c.Heat(t) : c.flash;
                if (h <= 0.02f) continue;
                var at = c.At(t);
                float r = 8 + 8 * h;
                var col = c.ember ? ChainTabs.HeatColour(h) : new Color("#cfe4ff");
                DrawTextureRect(soft!, new Rect2(at - new Vector2(r * 1.5f, r), new Vector2(r * 3, r * 2)), false, col with { A = (0.10f + 0.16f * h) * flick });
            }
        }
    }

    /// <summary>The lock at the chain's middle, hanging from it, the level stamped on its body; warm once
    /// the heat has reached it. As she rises its shackle springs open and it swings.</summary>
    partial class Lock : Control
    {
        /// <summary>A padlock's body: flat along its top, its foot rounded (28 wide, 12 to 37 down).</summary>
        static Vector2[] Body()
        {
            var pts = new List<Vector2> { new(-14, 12), new(14, 12), new(14, 28) };
            for (int i = 1; i <= 6; i++) { float a = i * Mathf.Pi / 2 / 6; pts.Add(new Vector2(5 + 9 * Mathf.Cos(a), 28 + 9 * Mathf.Sin(a))); }
            for (int i = 0; i <= 6; i++) { float a = Mathf.Pi / 2 + i * Mathf.Pi / 2 / 6; pts.Add(new Vector2(-5 + 9 * Mathf.Cos(a), 28 + 9 * Mathf.Sin(a))); }
            return pts.ToArray();
        }

        readonly EmberChain c;
        public Lock(EmberChain c) { this.c = c; MouseFilter = MouseFilterEnum.Ignore; Size = c.Size; TextureFilter = TextureFilterEnum.LinearWithMipmaps; }

        public override void _Draw()
        {
            var top = c.At(0.5f) + new Vector2(0, 2);
            DrawSetTransform(top, c.swing * 0.12f);
            float heat = c.ember ? Math.Max(c.fill >= 0.5f ? 0.45f + 0.55f * Mathf.Clamp((c.fill - 0.5f) * 2, 0, 1) : 0, c.flash) : 0;
            var art = UiArt.Art(c.open > 0.3f ? "hud/lock_open.png" : "hud/lock.png");
            if (art != null)
            {
                var s = art.GetSize();
                DrawTexture(art, new Vector2(-s.X / 2, 0));
                if (heat > 0 && UiArt.Art("hud/lock_hot.png") is { } hot) DrawTexture(hot, new Vector2(-s.X / 2, 0), Colors.White with { A = heat });
            }
            else
            {
                // The shackle: a stirrup of round iron from the link, its left leg lifting out as it springs.
                float lift = c.open * 7;
                var shackle = Cuff.Iron(0.55f).Lerp(ChainTabs.HeatColour(heat), heat * 0.8f);
                DrawArc(new Vector2(0, 9), 7.5f, Mathf.Pi, Mathf.Tau, 20, new Color(0, 0, 0, 0.8f), 5.2f, true);
                DrawArc(new Vector2(0, 9), 7.5f, Mathf.Pi, Mathf.Tau, 20, shackle, 3.4f, true);
                DrawLine(new Vector2(7.5f, 9), new Vector2(7.5f, 13), shackle, 3.4f, true);
                DrawLine(new Vector2(-7.5f, 9 - lift), new Vector2(-7.5f, 13 - lift), shackle, 3.4f, true);
                // The body: a squat block of iron, lit at its top, its edges dark.
                var lo = Cuff.Iron(0.2f).Lerp(new Color("#5a160a"), heat * 0.9f);
                var hi = Cuff.Iron(0.62f).Lerp(new Color("#c2461a"), heat * 0.9f);
                var pts = Body();
                var cols = new Color[pts.Length];
                for (int i = 0; i < pts.Length; i++) cols[i] = hi.Lerp(lo, Mathf.Clamp((pts[i].Y - 12) / 25, 0, 1));
                DrawPolygon(pts, cols);
                var outline = new Vector2[pts.Length + 1];
                pts.CopyTo(outline, 0);
                outline[^1] = pts[0];
                DrawPolyline(outline, new Color(0, 0, 0, 0.9f), 1.4f, true);
                DrawLine(new Vector2(-12.5f, 13.3f), new Vector2(12.5f, 13.3f), new Color(1, 0.94f, 0.8f, 0.28f), 1, true);
            }
            // The level, stamped: dark in the iron, the ember's colour when the heat is in it.
            string s2 = c.level.ToString();
            var f = Style.Display;
            int fs = s2.Length > 2 ? 13 : 16;
            var ts = f.GetStringSize(s2, HorizontalAlignment.Left, -1, fs);
            var at = new Vector2(-ts.X / 2, 12 + 11.5f + fs * 0.36f);
            var ink = c.ember ? new Color("#1a0e08").Lerp(Style.EmberHi, Math.Min(1, heat * 1.4f)) : new Color("#121418");
            DrawString(f, at + new Vector2(0, 1), s2, HorizontalAlignment.Left, -1, fs, new Color(1, 0.92f, 0.8f, 0.18f));
            DrawString(f, at, s2, HorizontalAlignment.Left, -1, fs, ink);
            DrawSetTransform(Vector2.Zero);
        }
    }
}

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
    public const float Sock = 58, SockGap = 6, SockY = VY - 20 - Sock / 2;
    /// <summary>The draught's and the dash's glass, and their iron.</summary>
    public const float SmallR = 23, SmallBand = 6;
    /// <summary>Where the chain leaves each cuff: an eye this far below the level, on the inner side.</summary>
    public const float EyeAngle = 32;
    /// <summary>HUD v2: the clear between the row's ends and the small glasses (22), the forged lug between a
    /// big cuff and the small glass (10, part of the cuff art, kept here so the art lines up), the sill under
    /// the row (5 tall, 6 past each end), and the key tags hung at 6 o'clock (16 tall).</summary>
    public const float SeatClear = 22, LugLen = 10, SillH = 5, SillOver = 6, TagH = 16;

    public static float SocksX => 960 - (6 * Sock + 5 * SockGap) / 2;
    public static float SmallY => SockY + Sock / 2;
    public static Vector2 LifeAt => new(960 - Reach, VY);
    public static Vector2 ArtAt => new(960 + Reach, VY);
    public static Vector2 DraughtAt => new(SocksX - SeatClear - SmallR - SmallBand, SmallY);
    public static Vector2 DashAt => new(SocksX + 6 * Sock + 5 * SockGap + SeatClear + SmallR + SmallBand, SmallY);
    /// <summary>The chain's ends: the riveted joints on the cuffs' outer edge, 32 degrees below level.</summary>
    public static Vector2 EyeL => LifeAt + JointOff;
    public static Vector2 EyeR => new(1920 - EyeL.X, EyeL.Y);
    /// <summary>HUD v2: the first link's centre from the life cuff's centre (the art's rivet at cuff image
    /// (150.0, 127.6) less the band centre (85, 87), plus the link's 4.4 px beside it); mirrored on the right.</summary>
    public static readonly Vector2 JointOff = new(69.4f, 40.6f);
    /// <summary>All of it on the screen, from the statuses over her life to the lock under the chain.</summary>
    public static Rect2 Bounds => new(960 - Reach - R - Band - 16, VY - R - Band - 48, 2 * (Reach + R + Band + 16), 1080 - (VY - R - Band - 48));

    public readonly Vessel Life, Art;
    public readonly Socket[] Sockets = new Socket[Content.Weapons.MaxWeapons];
    public readonly Round Draught, Dash;
    public readonly EmberChain Chain;
    /// <summary>The passives over the six places; what is on her (burning, shielded) over her life; the
    /// art's state in a word over the art.</summary>
    public readonly HBoxContainer Passives, Statuses;
    public readonly Label ArtWord, ArtNote;
    public readonly Sill SillStrap = new();
    readonly KeyTag draughtKey = new(Act.Draught), dashKey = new(Act.Dash), artKey = new(Act.Flare, true);
    int laidN = -1;

    public Instrument()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Position = Vector2.Zero;
        Size = new Vector2(1920, 1080);
        // (draw order: the sill and the six seats, the cuffs and small glasses, then the chain over the
        // cuffs' bands, then each cuff's front ear over the chain's first link, then the key tags)
        AddChild(SillStrap);
        Chain = new EmberChain();
        Life = new Vessel(true) { Position = LifeAt - Vessel.Half };
        AddChild(Life);
        Art = new Vessel(false) { Position = ArtAt - Vessel.Half };
        AddChild(Art);
        for (int i = 0; i < Sockets.Length; i++)
        {
            Sockets[i] = new Socket { Seat = i % 3, Position = new Vector2(SocksX + i * (Sock + SockGap), SockY) };
            AddChild(Sockets[i]);
        }
        Draught = new Round(Round.Kind.Draught) { Position = DraughtAt - Round.Half };
        AddChild(Draught);
        Dash = new Round(Round.Kind.Dash) { Position = DashAt - Round.Half };
        AddChild(Dash);
        AddChild(Chain);
        AddChild(new CuffFront(false) { Position = LifeAt - Vessel.Half });
        AddChild(new CuffFront(true) { Position = ArtAt - Vessel.Half });
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
        // A plain debug line under the Flare's slot (the dash form and the reflexes' waits) until the real HUD.
        ArtNote = Style.Label("", Style.Ui, 13, new Color("#d8c8a8"), false, HorizontalAlignment.Center);
        ArtNote.Position = new Vector2(ArtAt.X - 200, VY - R - Band - 50);
        ArtNote.Size = new Vector2(400, 18);
        AddChild(ArtNote);
        draughtKey.Place(DraughtAt.X, 989);  // plate top: the tag's hole (13, 3.6) meets the ring's (35, 64.5) under the draught's band centre
        dashKey.Place(DashAt.X, 989);
        artKey.Place(ArtAt.X, 1057);  // the ring hangs at the band's foot (1050), the plate within 1053-1073
        AddChild(draughtKey); AddChild(dashKey); AddChild(artKey);
        Keys();
        Lay(Sockets.Length, true);
    }

    /// <summary>The keys, as the device in hand has them: iron tags at 6 o'clock under the draught, the dash
    /// and the art's cuff (the life cuff has none). A tag redraws only when its key or button changed.</summary>
    public void Keys()
    {
        draughtKey.Refresh();
        dashKey.Refresh();
        artKey.Refresh();
    }

    /// <summary>A callout's spotlight: every part dimmed to dim but the one taught (keep: "art", "dash",
    /// "draught", "chain", "socket:ID"); the six places and the passives at slots' strength; the chain's
    /// heat pulsing along it (pulse).</summary>
    public void Spot(string? keep, Color dim, float slots, float pulse)
    {
        Color For(bool kept) => kept ? Colors.White : dim;
        Chain.Modulate = For(keep == "chain");
        Chain.Pulse = pulse;
        Life.Modulate = For(false);
        Art.Modulate = artKey.Modulate = For(keep == "art");
        // (the chain's callout: what stands over the chain fades with the six places, so the arrow's
        // point reads as the chain's)
        float over = keep == "chain" ? slots : 1;
        Dash.Modulate = dashKey.Modulate = For(keep == "dash") with { A = over };
        Draught.Modulate = draughtKey.Modulate = For(keep == "draught") with { A = over };
        Statuses.Modulate = For(false);
        Passives.Modulate = For(false) with { A = slots };
        foreach (var s in Sockets) s.Modulate = For(keep == "socket:" + s.Id && s.Id != "") with { A = slots };
    }

    /// <summary>Debug (--hud-pin seats=f3:h:e): the seats as shown, whatever she carries. f3 is filled at rank 3
    /// of 8, h filled and hot (can evolve), e empty (night); fewer codes than seats leaves the rest empty.</summary>
    public void PinSeats(string[] codes, bool night)
    {
        var defs = System.Linq.Enumerable.ToList(Content.Weapons.All.Values);
        int shown = 0;
        for (int i = 0; i < Sockets.Length; i++)
        {
            string c = i < codes.Length ? codes[i] : "e";
            if (c.StartsWith("e") || defs.Count == 0) { Sockets[i].Empty(); continue; }
            var d = defs[(i * 7) % defs.Count];
            bool hot = c.StartsWith("h");
            int rank = hot ? Content.Weapons.MaxRank : int.TryParse(c.AsSpan(1), out var r) ? Math.Clamp(r, 1, Content.Weapons.MaxRank) : 1;
            Sockets[i].Show(d.Id, d.Art, ItemViews.SchoolColors[d.School], 1, rank, Content.Weapons.MaxRank, false, hot);
            shown++;
        }
        Lay(shown, night);
    }

    /// <summary>The six places' spread: by night all six from the left (the empty ones the places still to
    /// come), by day only what is carried, centred on the middle (the day has no places to promise).</summary>
    public void Lay(int shown, bool all)
    {
        int n = all ? Sockets.Length : Math.Min(shown, Sockets.Length);
        if (n == laidN) return;
        laidN = n;
        SillStrap.Lay(n);
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
/// (shaders/hud_vessel.gdshader: her life in blood mode, HUD v2; the art in the first HUD's look until its
/// gold mode is made); over her blood, the glass's own light, rendered (hud/glass.png, premultiplied); the
/// cuff is UI art's (hud/cuff.png, the left cuff; mirrored for the right) or drawn. Each frame only the
/// shader's uniforms change: the number redraws when it (or its ink) does.</summary>
public partial class Vessel : Control
{
    public static readonly Vector2 Half = new(Instrument.R + Instrument.Band + 14, Instrument.R + Instrument.Band + 14);
    /// <summary>Her life's number: bone, and the low red at 30% and under (HUD v2).</summary>
    public static readonly Color Bone = new("#f2e8d6"), LowInk = new("#ff6a5a");
    static readonly StringName ULevel = "level", UTrail = "trail", UShield = "shield", UPulse = "pulse", USlosh = "slosh", UGlow = "glow";
    readonly bool life;
    readonly ColorRect glass;
    readonly ShaderMaterial mat;
    readonly Cuff cuff;
    readonly Over over;
    /// <summary>Her life: the blood's motion (HUD v2), and the cuff's inner chamfer flushed red on the
    /// heartbeat (hud/cuff_glow.png, added).</summary>
    readonly Flow? flow;
    readonly TextureRect? flush;
    /// <summary>The level and the shield (0..1 of her life). Trail is the first HUD's and unused by her blood,
    /// whose hurt film is its own. Pulse: 1 where her heartbeat may sound (the fight), 0 at peace; the beat
    /// itself is the vessel's, at 30% and under.</summary>
    public float Level = 1, Trail = 1, Shield, Pulse, Glow;
    public string Number = "";
    public Texture2D? Glyph;
    public Color GlyphTint = Colors.White;
    float slosh, shownLevel = -1, flushShown = -1;
    string drawnNumber = "";
    Texture2D? drawnGlyph;
    Color drawnTint, drawnInk, ink = Bone;

    public Vessel(bool life)
    {
        this.life = life;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Half * 2;
        PivotOffset = Half;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_vessel.gdshader") };
        mat.SetShaderParameter("seed", life ? 0.13f : 0.71f);
        mat.SetShaderParameter("mode", life ? 0 : 2);
        if (!life) Liquid(new Color("#ffcf7a"), new Color("#a8460c"), new Color("#0c0907"));
        glass = new ColorRect { Material = mat, MouseFilter = MouseFilterEnum.Ignore, Position = Half - new Vector2(Instrument.R, Instrument.R), Size = new Vector2(Instrument.R * 2, Instrument.R * 2) };
        AddChild(glass);
        if (life)
        {
            flow = new Flow(mat, true);
            Light(this, "hud/glass.png", Instrument.R + 6, Half);
        }
        // The art: UI art's first glass over the liquid (its window's light caught high on the left, its rim's
        // shade), sized so its glass's edge meets the cuff's seat.
        else if (UiArt.Art("hud/globe_glass.png") is { } painted)
        {
            float gs = Instrument.R * 2 / 0.91f;
            AddChild(new TextureRect { Texture = painted, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
                MouseFilter = MouseFilterEnum.Ignore, TextureFilter = TextureFilterEnum.LinearWithMipmaps, Position = Half - new Vector2(gs, gs) / 2, Size = new Vector2(gs, gs) });
            mat.SetShaderParameter("own_light", 0f);
        }
        cuff = new Cuff(Instrument.R, Instrument.Band, mirrored: !life, Half);
        AddChild(cuff);
        if (life && UiArt.Tex("hud/cuff_glow.png", false) is { } chamfer)
        {
            flush = new TextureRect { Texture = chamfer, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
                MouseFilter = MouseFilterEnum.Ignore, Position = new Vector2(2, 0), Size = Half * 2, TextureFilter = TextureFilterEnum.LinearWithMipmaps,
                Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add }, Modulate = Colors.Transparent };
            AddChild(flush);
        }
        over = new Over(this);
        AddChild(over);
    }

    /// <summary>A glass's rendered light (hud/glass.png, hud/glass_small.png: its window, hot spot, rim and the
    /// cuff's shadow, nothing else) laid over its liquid: premultiplied (out = under * (1 - a) + rgb), its file
    /// twice the size shown and drawn with mipmaps, r px out from the glass's middle at c.</summary>
    public static TextureRect? Light(Control parent, string art, float r, Vector2 c)
    {
        if (UiArt.Tex(art, false) is not { } tex) return null;
        var t = new TextureRect { Texture = tex, ExpandMode = TextureRect.ExpandModeEnum.IgnoreSize, StretchMode = TextureRect.StretchModeEnum.Scale,
            MouseFilter = MouseFilterEnum.Ignore, Position = c - new Vector2(r, r), Size = new Vector2(2 * r, 2 * r),
            TextureFilter = TextureFilterEnum.LinearWithMipmaps, Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.PremultAlpha } };
        parent.AddChild(t);
        return t;
    }

    /// <summary>Alegreya Sans 800 with lining tabular figures (lnum, tnum): numbers that hold still as they change.</summary>
    public static Font Figures => figures ??= new FontVariation
    {
        BaseFont = Style.UiHeavy,
        OpentypeFeatures = new Godot.Collections.Dictionary
        {
            { TextServerManager.Singleton.GetPrimaryInterface().NameToTag("lnum"), 1 },
            { TextServerManager.Singleton.GetPrimaryInterface().NameToTag("tnum"), 1 },
        },
    };
    static FontVariation? figures;

    /// <summary>The liquid's colours: at its surface, at its foot, and the empty glass (the art's).</summary>
    public void Liquid(Color shallow, Color deep, Color? empty = null)
    {
        mat.SetShaderParameter("shallow", shallow);
        mat.SetShaderParameter("deep", deep);
        if (empty is Color e) mat.SetShaderParameter("empty", e);
    }

    public override void _Process(double delta)
    {
        float dt = Math.Min((float)delta, 0.1f);
        if (flow != null)
        {
            flow.Tick(dt, Level, Shield, Pulse > 0);
            ink = flow.Low ? LowInk : Bone;
            if (flush != null && flow.Beat != flushShown)
            {
                flushShown = flow.Beat;
                flush.Modulate = new Color(0.88f, 0.16f, 0.17f, 0.9f * flushShown);
            }
        }
        else
        {
            // The art: a sudden change (the art spent) sloshes the surface, which settles over a second or so;
            // its steady filling does not.
            if (shownLevel >= 0 && Math.Abs(Level - shownLevel) > 0.04f) slosh = Math.Min(1, slosh + Math.Abs(Level - shownLevel) * 4);
            shownLevel = Level;
            slosh = Mathf.MoveToward(slosh, 0, dt * 0.9f);
            mat.SetShaderParameter(ULevel, Level);
            mat.SetShaderParameter(UTrail, Level);
            mat.SetShaderParameter(UShield, Shield);
            mat.SetShaderParameter(UPulse, Pulse);
            mat.SetShaderParameter(USlosh, slosh);
            mat.SetShaderParameter(UGlow, Glow);
        }
        if (Number != drawnNumber || Glyph != drawnGlyph || GlyphTint != drawnTint || ink != drawnInk)
        {
            drawnNumber = Number; drawnGlyph = Glyph; drawnTint = GlyphTint; drawnInk = ink;
            over.QueueRedraw();
        }
    }

    /// <summary>The blood's motion, HUD v2 (shaders/hud_vessel.gdshader, modes 0 and 1). It eases the level as
    /// drawn (a blow takes it down in about 0.1 s, healing fills it in about 0.4) and rocks the surface on a
    /// change (a damped slosh, settled in 0.8 s). For her life it also runs the hurt film down the glass (0.6 s),
    /// swirls fresh blood up on healing (a rise of 3% or more, never the slow regeneration), beats at 30% and
    /// under (every 1.1 s, 0.75 s under 15%) and rimes the shield's frost, cracking it away once (0.3 s) when the
    /// shield breaks. Each frame it sets only the uniforms that changed: at rest, none.</summary>
    public sealed class Flow
    {
        static readonly StringName[] Names = ["level", "tilt", "wave", "film_top", "film_t", "heal", "heal_t", "beat", "frost", "crack", "crack_reach"];
        /// <summary>The slosh's swing (0.46 s) and its damping (settled in 0.8 s).</summary>
        const float W = Mathf.Tau / 0.46f, Damp = 4.9f;
        readonly ShaderMaterial mat;
        readonly bool life;
        readonly float[] sent = new float[11];
        float last = -1, sx, sv, filmTop, filmT = 1, healT = 9, healA, healAcc, phase, frost, crackT = 1, crackReach;
        /// <summary>The level as drawn.</summary>
        public float Shown { get; private set; } = -1;
        /// <summary>The heartbeat now (0..1, 1 on the beat), and whether it beats.</summary>
        public float Beat { get; private set; }
        public bool Low { get; private set; }

        public Flow(ShaderMaterial mat, bool life)
        {
            this.mat = mat;
            this.life = life;
            Array.Fill(sent, float.NaN);
        }

        /// <summary>A change rocks the surface: a blow or a draught hard, a trickle hardly at all.</summary>
        public void Kick(float change)
        {
            float a = Math.Abs(change);
            if (a < 1e-5f) return;
            sv += Math.Sign(change) * Math.Min(2.2f, a * 4.7f + (a > 0.015f ? 0.35f : 0));
        }

        /// <summary>A frame: the level wanted, the shield (0..1 of her life) and whether the heartbeat may sound.
        /// ease false draws the level as given (the draught paces its own).</summary>
        public void Tick(float dt, float level, float shield = 0, bool alarm = false, bool ease = true)
        {
            level = Math.Clamp(level, 0, 1);
            if (last < 0) last = Shown = level;
            float d = level - last;
            if (life)
            {
                if (d < -0.002f)
                {
                    // A blow: the glass keeps a film of blood from where it stood (still higher if the last
                    // one's has not run down yet).
                    float still = filmT < 1 ? Mathf.Lerp(filmTop, Shown, filmT * filmT) : 0;
                    filmTop = Math.Max(Math.Max(Shown, last), still);
                    filmT = 0;
                }
                else if (d > 0.002f)
                {
                    healAcc += d;
                    if (healAcc >= 0.03f)
                    {
                        if (healT > 0.9f) healT = 0;
                        healA = Math.Min(1, Math.Max(healA, 0.45f + healAcc * 2.5f));
                    }
                }
                if (Math.Abs(d) > 0.004f) Kick(d);
            }
            healAcc = Math.Max(0, healAcc - dt * 0.05f);
            last = level;
            Shown = !ease ? level : Shown + (level - Shown) * (1 - Mathf.Exp(-(level < Shown ? 24f : 7f) * dt));
            if (Math.Abs(level - Shown) < 0.0005f) Shown = level;
            // The slosh: a damped swing, stepped finely.
            int steps = Math.Max(1, (int)Math.Ceiling(dt / 0.008f));
            for (int i = 0; i < steps; i++)
            {
                float h = dt / steps;
                sv += (-W * W * sx - 2 * Damp * sv) * h;
                sx += sv * h;
            }
            sx = Math.Clamp(sx, -0.16f, 0.16f);
            if (Math.Abs(sx) < 0.0004f && Math.Abs(sv) < 0.004f) sx = sv = 0;
            filmT = Math.Min(1, filmT + dt / 0.6f);
            healT += dt;
            if (healT > 1.4f) healA = 0;
            // The heartbeat: at 30% and under, where it may sound; its first beat lands a moment after the blow.
            bool low = life && alarm && Shown <= 0.30f && level > 0;
            float period = Shown < 0.15f ? 0.75f : 1.1f;
            if (low && !Low) phase = 0.70f;
            Low = low;
            if (low) phase = (phase + dt / period) % 1f;
            Beat = low ? HeartBeat(phase * period, period) : 0;
            // The frost: rimed as far round as the shield holds; cracked away once when it breaks.
            float sh = life ? Math.Clamp(shield, 0, 1) : 0;
            if (sh <= 0.0005f && frost > 0.01f) { crackT = 0; crackReach = frost; frost = 0; }
            else frost = Mathf.MoveToward(frost, sh, dt * 2.5f);
            crackT = Math.Min(1, crackT + dt / 0.3f);
            float he = healA * Mathf.Clamp(healT / 0.15f, 0, 1) * (1 - Mathf.SmoothStep(0.6f, 1.4f, healT));
            Set(0, Shown);
            Set(1, sx);
            Set(2, 0.3f * sv / W);
            Set(3, filmTop);
            Set(4, filmT);
            Set(5, he);
            Set(6, he > 0 ? healT : 0);
            Set(7, Beat);
            Set(8, frost);
            Set(9, crackT);
            Set(10, crackReach);
        }

        void Set(int i, float v)
        {
            if (sent[i] == v) return;
            sent[i] = v;
            mat.SetShaderParameter(Names[i], v);
        }

        /// <summary>A heart's beat s seconds into its period: a sharp rise and a softer fall, its second sound
        /// 0.2 s after the first.</summary>
        static float HeartBeat(float s, float period)
        {
            static float P(float u) => u < 0 ? Mathf.Exp(-(u / 0.035f) * (u / 0.035f)) : Mathf.Exp(-u / 0.13f);
            return Math.Min(1, P(s) + 0.6f * P(s - 0.2f) + P(s - period));
        }
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
            if (v.life) { LifeNumber(c); return; }
            var f = Style.Display;
            const int fs = 34;
            var ts = f.GetStringSize(v.Number, HorizontalAlignment.Left, -1, fs);
            var at = c + new Vector2(-ts.X / 2, fs * 0.36f);
            DrawStringOutline(f, at + new Vector2(0, 1), v.Number, HorizontalAlignment.Left, -1, fs, 6, new Color(0, 0, 0, 0.55f));
            DrawString(f, at, v.Number, HorizontalAlignment.Left, -1, fs, new Color("#fff4ea"));
        }

        /// <summary>Her life's number (HUD v2): Alegreya Sans 800, 22 px, lining tabular figures, bone (the low red
        /// at 30% and under), a soft shadow (0, 2, 4 px at 70%) and no stroke; its middle 58% of the way down the
        /// glass, on the blood's mass and out of the window's reflection.</summary>
        void LifeNumber(Vector2 c)
        {
            var f = Figures;
            const int fs = 22;
            var ts = f.GetStringSize(v.Number, HorizontalAlignment.Left, -1, fs);
            // (the figures stand 0.596 em tall on the baseline: their middle 0.293 em above it)
            var at = new Vector2(Mathf.Round(c.X - ts.X / 2), Mathf.Round(c.Y + 0.16f * Instrument.R + 0.293f * fs));
            var sh = at + new Vector2(0, 2);
            DrawStringOutline(f, sh, v.Number, HorizontalAlignment.Left, -1, fs, 8, new Color(0, 0, 0, 0.10f));
            DrawStringOutline(f, sh, v.Number, HorizontalAlignment.Left, -1, fs, 5, new Color(0, 0, 0, 0.16f));
            DrawStringOutline(f, sh, v.Number, HorizontalAlignment.Left, -1, fs, 2, new Color(0, 0, 0, 0.24f));
            DrawString(f, sh, v.Number, HorizontalAlignment.Left, -1, fs, new Color(0, 0, 0, 0.40f));
            DrawString(f, at, v.Number, HorizontalAlignment.Left, -1, fs, v.ink);
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
            // (HUD v2: the band's centre in the image, (85, 87) big and (35, 30) small, on the glass's centre;
            // the right cuff is the image flipped in x about that centre)
            var anchor = small ? new Vector2(35, 30) : new Vector2(85, 87);
            if (mirrored) DrawSetTransform(c, 0, new Vector2(-1, 1)); else DrawSetTransform(c);
            DrawTexture(art, -anchor);
            DrawSetTransform(Vector2.Zero);
            return;
        }
        float ro = r + band;
        // The hinge's knuckle on the outer side (the chain's joint is CuffFront's: a rivet, no open eye).
        float side = mirrored ? 1 : -1;
        if (!small)
        {
            var k = c + new Vector2(side * (ro + 3), 0);
            DrawRect(new Rect2(k - new Vector2(6, 13), new Vector2(12, 26)), Iron(0.32f));
            DrawRect(new Rect2(k - new Vector2(6, 13), new Vector2(12, 26)), new Color(0, 0, 0, 0.9f), false, 1.2f);
            DrawLine(k + new Vector2(-6, -4.5f), k + new Vector2(6, -4.5f), new Color(0, 0, 0, 0.75f), 1.2f, true);
            DrawLine(k + new Vector2(-6, 4.5f), k + new Vector2(6, 4.5f), new Color(0, 0, 0, 0.75f), 1.2f, true);
            DrawLine(k + new Vector2(-5, -12), k + new Vector2(5, -12), new Color(1, 0.95f, 0.85f, 0.18f), 1, true);
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
    /// <summary>HUD v2: which of the three seat castings it wears (seat index % 3, so neighbors differ).</summary>
    public int Seat;
    Texture2D? art;
    static Vector2[][]? dimples;

    /// <summary>The rank pits' centers per casting, in shown px of the 68 px seat image (hud/seat.json).</summary>
    static Vector2[][] Dimples()
    {
        if (dimples != null) return dimples;
        dimples = new Vector2[3][];
        try
        {
            var d = Json.ParseString(Godot.FileAccess.GetFileAsString(UiArt.Root + "hud/seat.json")).AsGodotDictionary()["dimples"].AsGodotDictionary();
            for (int k = 0; k < 3; k++)
            {
                var a = d[k.ToString()].AsGodotArray();
                dimples[k] = new Vector2[a.Count];
                for (int i = 0; i < a.Count; i++) { var xy = a[i].AsGodotArray(); dimples[k][i] = new Vector2((float)xy[0], (float)xy[1]); }
            }
        }
        catch (Exception) { dimples = new Vector2[3][] { Array.Empty<Vector2>(), Array.Empty<Vector2>(), Array.Empty<Vector2>() }; }
        return dimples;
    }
    Color school;
    int rank, max = 8;
    bool evolved, ripe, filled;
    double ready = 1, lastReady = 1, flash, t, crown = -1;

    public Socket()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(Instrument.Sock, Instrument.Sock);
        PivotOffset = Size / 2;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
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
        // The skill's own painting where there is one (the draft's card shows the same), else its drawn glyph.
        art = UiArt.Icon("glyph_color", glyph) ?? Glyphs.Texture(glyph, 78, school, line: true);
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
        // HUD v2: the cast seat (68 px, the 58 seat at (4, 4)); no drawn collar, floor or rivets with it.
        var seat = UiArt.Art(filled ? $"hud/seat_{Seat}.png" : $"hud/seat_empty_{Seat}.png");
        if (seat != null)
        {
            DrawTexture(seat, new Vector2(-4, -4));
            if (!filled) return;
            float heat = evolved ? 1 : ripe ? 0.45f + 0.4f * (0.5f + 0.5f * Mathf.Sin((float)t * 4.5f)) : 0;
            if (heat > 0 && UiArt.Art($"hud/seat_hot_{Seat}.png") is { } hotSeat) DrawTexture(hotSeat, new Vector2(-4, -4), Colors.White with { A = heat });
            if (art != null)
            {
                float g2 = s * 0.66f;
                var col2 = ready >= 0.98 ? new Color(1.25f, 1.25f, 1.25f) : Colors.White;
                DrawTextureRect(art, new Rect2((s - g2) / 2, (s - g2) / 2 - 3, g2, g2), false, col2.Lerp(new Color(2.2f, 2.0f, 1.7f), (float)flash));
            }
            if (ready < 0.98) DrawRect(new Rect2(3, 3, s - 6, (s - 6) * (float)(1 - ready)), new Color(0.02f, 0.015f, 0.03f, 0.6f));
            var pits = Dimples()[Seat % 3];
            for (int i = 0; i < pits.Length; i++)
            {
                var pc = pits[i] - new Vector2(4, 4);
                if (i < rank)
                {
                    DrawCircle(pc, 1.9f, new Color("#ff8a3a") with { A = 0.35f });
                    DrawCircle(pc, 1.5f, new Color("#ff8a3a") with { A = 0.85f });
                }
                else DrawCircle(pc, 1.1f, new Color(0, 0, 0, 0.55f));
            }
            return;
        }
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
    readonly Glass glassOf;
    readonly Count2 countOf;
    int countDrawn = int.MinValue;
    public int Count, Max = 2;
    public float Recharge;
    /// <summary>The dash's form (her calling's art riding it, Forms.cs): -1 none; 0..1 its wait coming round, a
    /// thin ember arc outside the glass; 1 ready: the glass warm, flames licking up off the cuff's rim and the
    /// calling's own badge (FormGlyph) at its shoulder: a look of its own, never the callouts' ring (round 2
    /// judge: the ready glow and a callout's ring were the same ember circle).</summary>
    public float Form = -1;
    /// <summary>The calling's art's glyph, the badge the ready form wears.</summary>
    public Texture2D? FormGlyph;

    public Round(Kind kind)
    {
        this.kind = kind;
        MouseFilter = MouseFilterEnum.Ignore;
        // (its flames keep licking under a callout's freeze: paused, they stood as a row of ticks, round 3 judge)
        ProcessMode = ProcessModeEnum.Always;
        Size = Half * 2;
        cuff = new Cuff(Instrument.SmallR, Instrument.SmallBand, kind == Kind.Dash, Half, small: true);
        // The glass first, under the iron.
        AddChild(glassOf = new Glass(this));
        AddChild(cuff);
        float s = Instrument.SmallR * 1.5f;
        // (HUD v2: the draught has no flask icon; its glass is the flask)
        icon = kind == Kind.Draught ? new Control() : Glyphs.Icon("dash", (int)s, Style.Ink);
        icon.Position = Half - new Vector2(s, s) / 2;
        icon.Size = new Vector2(s, s);
        icon.MouseFilter = MouseFilterEnum.Ignore;
        AddChild(icon);
        AddChild(countOf = new Count2(this));
    }

    public override void _Process(double delta)
    {
        // HUD v2: the draught's liquid is the vessel shader's (its uniforms only); its count redraws when it changes.
        if (kind == Kind.Draught)
        {
            glassOf.Tick(Math.Min((float)delta, 0.1f));
            if (Count != countDrawn) { countDrawn = Count; countOf.QueueRedraw(); }
            return;
        }
        // An empty draught is dimmed, not hidden: its place keeps the instrument whole.
        icon.Modulate = kind == Kind.Draught && Count <= 0 ? new Color(0.45f, 0.42f, 0.42f, 0.7f) : Colors.White;
        foreach (var c in GetChildren()) if (c is CanvasItem ci && ci != icon && ci != cuff) ci.QueueRedraw();
    }

    partial class Glass : Control
    {
        readonly Round o;
        /// <summary>The draught (HUD v2): its liquid, the vessel shader in draught mode under its glass's
        /// rendered light (hud/glass_small.png).</summary>
        readonly Vessel.Flow? flow;
        int had = -1;
        float lvl;
        bool draining;

        public Glass(Round o)
        {
            this.o = o;
            MouseFilter = MouseFilterEnum.Ignore;
            Size = o.Size;
            if (o.kind != Kind.Draught) return;
            float r = Instrument.SmallR;
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_vessel.gdshader") };
            mat.SetShaderParameter("mode", 1);
            mat.SetShaderParameter("seed", 0.37f);
            mat.SetShaderParameter("dry_film", 0f);
            AddChild(new ColorRect { Material = mat, MouseFilter = MouseFilterEnum.Ignore, Position = Size / 2 - new Vector2(r, r), Size = new Vector2(2 * r, 2 * r) });
            Vessel.Light(this, "hud/glass_small.png", r + 2, Size / 2);
            flow = new Vessel.Flow(mat, false);
        }

        /// <summary>The draught's level: full while one is left; drunk, it drains (0.25 s) and the next fills it
        /// (0.6 s); with none left, dark (or rising as it refills, Recharge).</summary>
        public void Tick(float dt)
        {
            if (flow == null) return;
            int n = Math.Max(0, o.Count);
            float want = n > 0 ? 1 : Math.Clamp(o.Recharge, 0, 1);
            if (had < 0) { had = n; lvl = want; }
            if (n < had) { draining = true; flow.Kick(-0.3f); }
            else if (n > had && had == 0) flow.Kick(0.15f);
            had = n;
            if (draining) { lvl = Mathf.MoveToward(lvl, 0, dt * 4); if (lvl <= 0) draining = false; }
            else lvl = Mathf.MoveToward(lvl, want, dt / 0.6f);
            flow.Tick(dt, lvl, ease: false);
        }

        public override void _Draw()
        {
            if (o.kind == Kind.Draught) return;
            var c = Size / 2;
            float r = Instrument.SmallR;
            DrawCircle(c, r, new Color(0.05f, 0.04f, 0.05f, 0.95f));
            DrawCircle(c + new Vector2(-r * 0.3f, -r * 0.4f), r * 0.45f, new Color(1, 1, 1, 0.04f));
            if (o.kind != Kind.Dash) return;
            if (o.Form >= 1)
            {
                float breath = 0.5f + 0.5f * Mathf.Sin(Time.GetTicksMsec() / 1000f * 3.2f);
                DrawCircle(c, r - 1, new Color(1f, 0.55f, 0.15f, 0.14f + 0.1f * breath));
            }
            else if (o.Form >= 0)
                DrawArc(c, r + Instrument.SmallBand + 3, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * o.Form, 48, new Color(1f, 0.6f, 0.2f, 0.45f), 2, true);
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
            if (o.kind == Kind.Dash && o.Form >= 1) { Licks(); return; }
            if (o.kind != Kind.Draught) return;
            // HUD v2: the count in the glass's lower right (Alegreya Sans 800, 16 px, lining tabular figures), bone,
            // dim with none left; a 1.5 px dark outline and a soft shadow, so it reads on the blood's bright rim.
            var f = Vessel.Figures;
            const int fs = 16;
            string s = o.Count.ToString();
            var ts = f.GetStringSize(s, HorizontalAlignment.Left, -1, fs);
            var mid = Size / 2 + new Vector2(Instrument.SmallR * 0.40f, Instrument.SmallR * 0.42f);
            var at = new Vector2(Mathf.Round(mid.X - ts.X / 2), Mathf.Round(mid.Y + 0.293f * fs));
            DrawStringOutline(f, at + new Vector2(0, 1.5f), s, HorizontalAlignment.Left, -1, fs, 7, new Color(0, 0, 0, 0.22f));
            DrawStringOutline(f, at, s, HorizontalAlignment.Left, -1, fs, 3, new Color(0, 0, 0, 0.62f));
            DrawString(f, at, s, HorizontalAlignment.Left, -1, fs, o.Count > 0 ? Vessel.Bone : new Color(0.55f, 0.51f, 0.46f));
        }

        /// <summary>The ready form: tongues of fire licking up off the top of the cuff, each on its own
        /// flicker, and the calling's badge (an iron coin, its glyph in ember) at the right shoulder.</summary>
        void Licks()
        {
            var c = Size / 2;
            float t = Time.GetTicksMsec() / 1000f;
            float r0 = Instrument.SmallR + Instrument.SmallBand - 1;
            for (int i = 0; i < 9; i++)
            {
                float u = (i - 4) / 4f;
                float a = -Mathf.Pi / 2 + u * 1.25f;
                float flick = 0.5f + 0.3f * Mathf.Sin(t * (7.1f + i * 1.3f) + i * 2.1f) + 0.2f * Mathf.Sin(t * (12.7f + i * 0.7f) + i);
                float h = (9f + 10f * flick) * (1 - 0.5f * u * u);
                float w = 0.13f * (1 - 0.3f * u * u);
                var dir = Vector2.FromAngle(a);
                var side = new Vector2(-dir.Y, dir.X);
                float sway = 2.2f * Mathf.Sin(t * (5.3f + i) + i * 1.7f);
                Vector2 Tongue(float hk) => c + dir * (r0 + h * hk) + side * sway * hk * hk;
                Vector2[] Shape(float wk, float hk)
                {
                    var b1 = c + Vector2.FromAngle(a - w * wk) * r0;
                    var b2 = c + Vector2.FromAngle(a + w * wk) * r0;
                    var m1 = c + dir * (r0 + h * hk * 0.45f) - side * (r0 * w * wk * 0.8f) + side * sway * 0.3f;
                    var m2 = c + dir * (r0 + h * hk * 0.45f) + side * (r0 * w * wk * 0.8f) + side * sway * 0.3f;
                    return [b1, m1, Tongue(hk), m2, b2];
                }
                DrawColoredPolygon(Shape(1, 1), new Color(0.95f, 0.32f, 0.06f, 0.85f));
                DrawColoredPolygon(Shape(0.55f, 0.62f), new Color(1f, 0.74f, 0.3f, 0.95f));
            }
            // The badge: the calling's own mark, so the lit dash says whose charge it is.
            if (o.FormGlyph is { } g)
            {
                var at = c + Vector2.FromAngle(-Mathf.Pi / 4) * (Instrument.SmallR + Instrument.SmallBand + 2);
                const float br = 14;
                DrawCircle(at, br + 2, new Color(0.055f, 0.04f, 0.035f, 0.95f));
                DrawArc(at, br + 1, 0, Mathf.Tau, 32, new Color(1f, 0.6f, 0.2f, 0.95f), 1.6f, true);
                DrawTextureRect(g, new Rect2(at - Vector2.One * (br - 1.5f), Vector2.One * (br - 1.5f) * 2), false, new Color(1f, 0.78f, 0.42f));
            }
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
    /// <summary>A callout points at the chain: its heat runs along all of it (0 to 1).</summary>
    public float Pulse;
    /// <summary>Debug (--hud-pin lockheat): the lock's heat held at this, 0 to 1; -1 off.</summary>
    public float PinHeat = -1;
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
    // (HUD v2: a multiple of four, so the first and last links and the middle one are all face-on)
    int Count => Math.Max(4, 4 * (int)Math.Round(Len / Pitch / 4));

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
                    var tint = ember ? new Color(0.72f, 0.7f, 0.68f) : t <= fill ? new Color(1.2f, 1.22f, 1.28f) : new Color(0.62f, 0.62f, 0.66f);
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
            float now = Time.GetTicksMsec() / 1000f;
            // (a callout's pulse: the ember's glow filling the chain from the left, its edge brightest,
            // once every 1.8 s, held full a beat, then again)
            if (c.Pulse > 0)
            {
                float fillTo = Mathf.Min(1, (now % 1.8f) / 1.3f);
                for (int k = 0; k <= c.Count; k += 2)
                {
                    float t = (float)k / c.Count;
                    if (t > fillTo) break;
                    float w = 0.3f + 0.7f * Mathf.Exp(-(fillTo - t) * 7);
                    var at = c.At(t);
                    DrawTextureRect(soft!, new Rect2(at - new Vector2(22, 14), new Vector2(44, 28)), false, ChainTabs.HeatColour(0.75f) with { A = c.Pulse * (0.08f + 0.4f * w) });
                }
            }
            if (!c.ember && c.flash <= 0) return;
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
            // (HUD v2: the art's shackle passes through the middle link, image (19, 10); that link is face-on at
            // angle 0 at t = 0.5, so the pivot is the link's centre)
            var top = c.At(0.5f) + (UiArt.Art("hud/lock.png") != null ? Vector2.Zero : new Vector2(0, 2));
            DrawSetTransform(top, c.swing * 0.12f);
            float heat = c.PinHeat >= 0 ? c.PinHeat : c.ember ? Math.Max(c.fill >= 0.5f ? 0.45f + 0.55f * Mathf.Clamp((c.fill - 0.5f) * 2, 0, 1) : 0, c.flash) : 0;
            var art = UiArt.Art(c.open > 0.3f ? "hud/lock_open.png" : "hud/lock.png");
            if (art != null)
            {
                DrawTexture(art, new Vector2(-19, -10));
                if (heat > 0 && UiArt.Art("hud/lock_hot.png") is { } hot) DrawTexture(hot, new Vector2(-19, -10), Colors.White with { A = heat });
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
            // (the art's numeral centre is image (19, 32), 5 lower when open: 22 below the pivot; the keyhole is at 31.5)
            var at = new Vector2(-ts.X / 2, art != null ? 22 + (c.open > 0.3f ? 5 : 0) + fs * 0.36f : 12 + 11.5f + fs * 0.36f);
            var ink = c.ember ? new Color("#1a0e08").Lerp(Style.EmberHi, Math.Min(1, heat * 1.4f)) : new Color("#121418");
            DrawString(f, at + new Vector2(0, 1), s2, HorizontalAlignment.Left, -1, fs, new Color(1, 0.92f, 0.8f, 0.18f));
            DrawString(f, at, s2, HorizontalAlignment.Left, -1, fs, ink);
            DrawSetTransform(Vector2.Zero);
        }
    }
}

/// <summary>HUD v2: the strap the six seats stand on, 5 px tall and 6 px past each end of the row, a rivet
/// under each gap. By day it is as long as what she carries, centered. hud/sill_N.png (N seats shown, drawn
/// at half its size: the art is rendered at 2x) when UI art has made it, else drawn plain dark iron.</summary>
public partial class Sill : Control
{
    int n = Content.Weapons.MaxWeapons, full = 6;
    Texture2D? art;

    public Sill()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
    }

    /// <summary>The row now has n seats (hidden for none); redraws only on a change. The art: sill_6 for 4 to 6
    /// seats, sill_3 for 1 to 3, its middle cut by whole pitches (64 px) to the row's length, so the rivets stay
    /// under the gaps; top-left at (row's left - 6, 985).</summary>
    public void Lay(int n)
    {
        this.n = n;
        Visible = n > 0;
        if (n <= 0) return;
        full = n > 3 ? 6 : 3;
        art = UiArt.Art($"hud/sill_{full}.png");
        float row = n * Instrument.Sock + (n - 1) * Instrument.SockGap;
        Size = art != null ? new Vector2(64 * n + 11, art.GetSize().Y / 2) : new Vector2(row + 2 * Instrument.SillOver, Instrument.SillH);
        Position = new Vector2(960 - row / 2 - Instrument.SillOver, art != null ? 985 : Instrument.SockY + Instrument.Sock);
        QueueRedraw();
    }

    public override void _Draw()
    {
        if (art != null)
        {
            // (cut at x 38, the middle of the first seat's bay: left piece, then the right piece from the cut
            // plus the seats left out; whole pitches, so the pattern runs on)
            var sz = art.GetSize();
            float cut = 38, skip = (full - n) * 64;
            DrawTextureRectRegion(art, new Rect2(0, 0, cut, sz.Y), new Rect2(0, 0, cut, sz.Y));
            DrawTextureRectRegion(art, new Rect2(cut, 0, sz.X - skip - cut, sz.Y), new Rect2(cut + skip, 0, sz.X - skip - cut, sz.Y));
            return;
        }
        DrawRect(new Rect2(Vector2.Zero, Size), new Color("#1a1714"));
        DrawRect(new Rect2(0, 0, Size.X, 1), new Color("#f2e8d6") with { A = 0.3f });
        for (int g = 0; g < n - 1; g++)
        {
            float x = Instrument.SillOver + (g + 1) * Instrument.Sock + g * Instrument.SockGap + Instrument.SockGap / 2f;
            DrawCircle(new Vector2(x, Instrument.SillH / 2f + 0.5f), 1.5f, new Color("#0c0a08"));
        }
    }
}

/// <summary>HUD v2: a key on a small stamped iron tag (16 tall; 24, 32, 40 or 52 wide) hung from a ring at
/// 6 o'clock. The key in Alegreya Sans 800 caps 14 px, bone, a 1 px dark edge; SPACE tracked 60. On a pad
/// the button sits in the same tag (Style.PadButton, scaled to fit). Redraws only when its key or button
/// changes (Refresh). hud/tag_W.png and hud/tag_ring.png (half size) when made, else a drawn plate.</summary>
public partial class KeyTag : Control
{
    readonly Act act;
    string text = "";
    string? padName;
    float w = 24, cx;
    bool built;
    Control? padView;
    static StyleBoxFlat? plate;

    readonly bool ring;

    public KeyTag(Act act, bool ring = false)
    {
        this.act = act;
        this.ring = ring;
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        Size = new Vector2(52, Instrument.TagH);
    }

    /// <summary>Hung from a ring at x, its top at y.</summary>
    public void Place(float x, float y) { cx = x; Position = new Vector2(x - Size.X / 2, y); }

    public void Refresh()
    {
        var c = Controls.Instance;
        string? pad = c != null && c.UsingPad ? System.Linq.Enumerable.FirstOrDefault(c.PadLabels(act)) : null;
        string t = pad != null ? "" : (c?.KeyLabel(act) ?? "?").ToUpperInvariant();
        if (built && t == text && pad == padName) return;
        built = true; text = t; padName = pad;
        padView?.QueueFree();
        padView = null;
        if (pad != null)
        {
            w = 32;
            padView = Style.PadButton(pad);
            AddChild(padView);
            var ps = padView.GetCombinedMinimumSize();
            float k = (Instrument.TagH - 3) / Math.Max(1, ps.Y);
            padView.Size = ps;
            padView.Scale = new Vector2(k, k);
            padView.Position = new Vector2((Size.X - ps.X * k) / 2, (Instrument.TagH - ps.Y * k) / 2);
        }
        else
        {
            w = t.Length <= 1 ? 24 : t.Length == 2 ? 32 : t.Length == 3 ? 40 : 52;
            if (t.Length > 4) w = Math.Max(w, TextWidth() + 10);
        }
        Size = new Vector2(Math.Max(52, w), Instrument.TagH);
        Place(cx, Position.Y);
        QueueRedraw();
    }

    float Track => text == "SPACE" ? 60 / 1000f * 14 : 0;

    float TextWidth()
    {
        var f = Style.UiHeavy;
        float x = 0;
        foreach (char ch in text) x += f.GetStringSize(ch.ToString(), HorizontalAlignment.Left, -1, 14).X + Track;
        return x - Track;
    }

    public override void _Draw()
    {
        float x0 = (Size.X - w) / 2;
        var tag = UiArt.Art($"hud/tag_{(int)w}.png");
        // (the art's plate is 1 px in from the image's corner; its hole is at (1 + plate/2, 3.6))
        if (tag != null) DrawTextureRect(tag, new Rect2(Size.X / 2 - 1 - w / 2, -1, tag.GetSize()), false);
        else
        {
            plate ??= new StyleBoxFlat { BgColor = new Color("#2a2420"), BorderColor = new Color("#6b5a48"), BorderWidthTop = 1, CornerRadiusTopLeft = 2, CornerRadiusTopRight = 2, CornerRadiusBottomLeft = 2, CornerRadiusBottomRight = 2 };
            DrawStyleBox(plate, new Rect2(x0, 0, w, Instrument.TagH));
        }
        // (the Q tag's own ring: image (6, 1.5) on the band's foot, 1050; the small cuffs carry theirs)
        if (this.ring && UiArt.Art("hud/tag_ring.png") is { } rg) DrawTexture(rg, new Vector2(Size.X / 2 - 6, 1048.5f - Position.Y));
        if (padName != null || text == "") return;
        var f = Style.UiHeavy;
        float x = (Size.X - TextWidth()) / 2;
        float y = (Instrument.TagH - f.GetHeight(14)) / 2 + f.GetAscent(14) + (tag != null && (int)w == 24 ? 1.5f : 0);
        foreach (char ch in text)
        {
            string s = ch.ToString();
            DrawStringOutline(f, new Vector2(x, y), s, HorizontalAlignment.Left, -1, 14, 1, new Color("#0c0a08") with { A = 0.8f });
            DrawString(f, new Vector2(x, y), s, HorizontalAlignment.Left, -1, 14, new Color("#f2e8d6"));
            x += f.GetStringSize(s, HorizontalAlignment.Left, -1, 14).X + Track;
        }
    }
}

/// <summary>HUD v2: a cuff's front ear and rivet (hud/cuff_front.png), drawn over the chain's first link with
/// the cuff's own placement, size and mirroring. Drawn without the art: a domed rivet at the joint.</summary>
public partial class CuffFront : Control
{
    readonly bool mirrored;

    public CuffFront(bool mirrored)
    {
        this.mirrored = mirrored;
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Vessel.Half * 2;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
    }

    public override void _Draw()
    {
        var c = Size / 2;
        if (UiArt.Art("hud/cuff_front.png") is { } art)
        {
            if (mirrored) DrawSetTransform(c, 0, new Vector2(-1, 1)); else DrawSetTransform(c);
            DrawTexture(art, -new Vector2(85, 87));
            DrawSetTransform(Vector2.Zero);
            return;
        }
        float a = Mathf.DegToRad(Instrument.EyeAngle);
        var p = c + new Vector2((mirrored ? -1 : 1) * Mathf.Cos(a), Mathf.Sin(a)) * (Instrument.R + Instrument.Band);
        DrawCircle(p, 3.6f, new Color(0, 0, 0, 0.85f));
        DrawCircle(p, 3f, Cuff.Iron(0.3f));
        DrawCircle(p - new Vector2(0.8f, 0.9f), 1.3f, Cuff.Iron(0.85f));
    }
}

using System;
using System.Collections.Generic;
using Godot;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The instrument along the foot (the owner, 5 October: "the bottom skill bar and health globes and
/// stuff need to be incredible, its a keystone of that kind of game"; "one composed group, not loose
/// pieces"): HUD A, "the keeper" (UI 23, the owner's pick). At the left the Drowned Girl's bronze figure lifts the
/// life orb to her lips (LifeLamp), her hair down her back to the screen's foot, a slow shine running down it; in the
/// middle its own plate (DgPanel): the flask [R] (Round, DgSmall), three seats (Socket), the level coin with the
/// experience ring (by night the ember; DgPanel.Ring, XpLight), three seats, the dash [SPACE]; at the right the keeper
/// (DgKeeper) bows over the bowl that holds the Flare [Q] (Vessel, DgGlobe: a dark glass globe filling with fire). Her
/// group draws at DgPanel.GroupScale about its outer bottom corner; the keeper's rect is final. Every place comes from the art's geo
/// (art/ui/dg_keeper/hud_a_geo.json, art/ui/lamp_life/drowned).
/// </summary>
public partial class Instrument : Control
{
    /* The callouts' ring sizes (GameTeach) and the boss bar's width (GameHud), in the HUD's 1920 by 1080. */
    /// <summary>The Flare's reach (its ring's radius is R + Band) and the distance the boss bar spans either side.</summary>
    public const float R = 60, Band = 13, Reach = 352;
    /// <summary>A skill's place (its callout ring), and the draught's and the dash's.</summary>
    public const float Sock = 58, SmallR = 23, SmallBand = 6;
    /// <summary>The key tags' height.</summary>
    public const float TagH = 16;

    /// <summary>The Flare's glass (in the keeper's bowl), the flask's and the dash's middles (DgPanel).</summary>
    public static Vector2 ArtAt => DgPanel.GlassAt;
    public static Vector2 DraughtAt => DgPanel.FlaskAt;
    public static Vector2 DashAt => DgPanel.DashAt;
    /// <summary>The coin's experience ring: what "chain" and "chain_fill" bracket in a callout (UI 23; it was the
    /// river's crest).</summary>
    public static Rect2 ChainFill => DgPanel.RingRect;
    /// <summary>The key chips' top (R and SPACE, from the geo).</summary>
    public static float DgTagTop => DgPanel.KeyR.Y;
    /// <summary>All of it on the screen, from her head to the screen's foot, her left edge to the keeper's right.</summary>
    public static Rect2 Bounds
    {
        get
        {
            float s = DgPanel.GroupScale;
            var tl = DgPanel.GirlAnchor + (LifeLamp.At - DgPanel.GirlAnchor) * s;
            float right = Math.Max(DgPanel.Rect.End.X, DgPanel.KeeperRect.End.X);
            return new Rect2(tl, new Vector2(right - tl.X, 1080 - tl.Y));
        }
    }

    public readonly LifeLamp Life;
    /// <summary>The keeper, bowed over the Flare's bowl (the right group's figure).</summary>
    public readonly DgKeeper Keeper;
    public readonly Vessel Art;
    public readonly Socket[] Sockets = new Socket[Content.Weapons.MaxWeapons];
    public readonly Round Draught, Dash;
    /// <summary>The plate in the middle (the bar).</summary>
    public readonly DgPanel Panel;
    /// <summary>The passives' beads over the plate's top line, over the seats' middle; what is on her (burning,
    /// shielded); the art's state in a word over the art.</summary>
    public readonly HBoxContainer Passives, Statuses;
    public readonly Label ArtWord, ArtNote;
    readonly KeyTag draughtKey = new(Act.Draught) { Chip = true }, dashKey = new(Act.Dash) { Chip = true }, artKey = new(Act.Flare) { Chip = true };

    public Instrument()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Position = Vector2.Zero;
        Size = new Vector2(1920, 1080);
        // (draw order, UI 23: the figures (her; the keeper, the next piece), then the plate over her hair's tail where
        // they meet, then what is live on it: the coin's ring, the seats, the flask and the dash, the beads, the key
        // chips, the numbers; the level's title and the numbers' card over everything)
        Life = new LifeLamp();
        Life.Group(DgPanel.GirlAnchor, DgPanel.GroupScale);
        AddChild(Life);
        // (the right group's figure, the keeper: under the plate, at his geo rect)
        Keeper = new DgKeeper();
        AddChild(Keeper);
        Draught = new Round(Round.Kind.Draught);
        Draught.Place(DgPanel.FlaskAt, DgPanel.FlaskScale);
        Panel = new DgPanel(Draught);
        AddChild(Panel);
        AddChild(Panel.XpRing);
        Art = new Vessel { Position = ArtAt - Vessel.Half };
        AddChild(Art);
        Keeper.Globe = Art.Globe;
        for (int i = 0; i < Sockets.Length; i++)
        {
            Sockets[i] = new Socket { Index = i };
            Sockets[i].Position = DgPanel.Seat(i) - Sockets[i].Size / 2;
            AddChild(Sockets[i]);
        }
        AddChild(Draught);
        Dash = new Round(Round.Kind.Dash);
        Dash.Place(DgPanel.DashAt, DgPanel.DashScale);
        AddChild(Dash);
        // (UI 23: the beads in a row over the plate's top line, over the seats' middle)
        Passives = Style.H(2);
        Passives.Alignment = BoxContainer.AlignmentMode.Center;
        float mid = (DgPanel.Seat(0).X + DgPanel.Seat(5).X) / 2, w = DgPanel.Seat(5).X - DgPanel.Seat(0).X + 2 * DgPanel.SeatR;
        Passives.Position = new Vector2(mid - w / 2, DgPanel.TopY - DgMeters.BeadLift - 28 - 6);
        Passives.Size = new Vector2(w, 28);
        AddChild(Passives);
        Statuses = Style.H(10);
        Statuses.Alignment = BoxContainer.AlignmentMode.Center;
        Statuses.Position = new Vector2(LegacyLifeX - 150, LegacyTop - 40);
        Statuses.Size = new Vector2(300, 30);
        AddChild(Statuses);
        ArtWord = Style.Label("", Style.UiHeavy, Style.Badge, new Color("#d8b8ff"), false, HorizontalAlignment.Center);
        ArtWord.Position = new Vector2(ArtAt.X - 150, LegacyTop - 30);
        ArtWord.Size = new Vector2(300, 20);
        AddChild(ArtWord);
        // A plain debug line under the Flare's slot (the dash form and the reflexes' waits) until the real HUD.
        ArtNote = Style.Label("", Style.Ui, 13, new Color("#d8c8a8"), false, HorizontalAlignment.Center);
        ArtNote.Position = new Vector2(ArtAt.X - 200, LegacyTop - 50);
        ArtNote.Size = new Vector2(400, 18);
        AddChild(ArtNote);
        // (UI 23: R, SPACE and Q on small dark chips at the geo's places under the flask, the dash and the keeper's
        // bowl; Q lit "Q  READY" when the Flare is full)
        draughtKey.Place(DgPanel.KeyR.X, DgPanel.KeyR.Y);
        dashKey.Place(DgPanel.KeySpace.X, DgPanel.KeySpace.Y);
        artKey.Place(DgPanel.KeyQ.X, DgPanel.KeyQ.Y);
        AddChild(draughtKey); AddChild(dashKey); AddChild(artKey);
        AddChild(Panel.Numbers);
        // (the level's title and the numbers' card, over everything on the instrument)
        AddChild(Panel.Title); AddChild(Panel.Card);
        Keys();
    }

    /// <summary>The Q chip lit "Q  READY" while the Flare is full (a change redraws it once).</summary>
    public override void _Process(double delta) => artKey.Lit = Art.Level >= 0.999f;

    /// <summary>Where the statuses and the art's word stood in the iron HUD (its life cuff's middle and its cuffs'
    /// top), kept so they show where they always have until the UI lead places them on the Drowned Girl.</summary>
    const float LegacyLifeX = 960 - Reach, LegacyTop = 1080 - 30 - 2 * (R + Band);

    /// <summary>By day (her experience) or by night (the ember): the bronze takes the day's or the
    /// night's light (Cuff.Day); a change redraws everything in the instrument once.</summary>
    public void DayNight(bool ember)
    {
        if (Cuff.Day != ember) return;
        Cuff.Day = !ember;
        Redraw(this);
    }

    static void Redraw(Node n)
    {
        if (n is CanvasItem ci) ci.QueueRedraw();
        foreach (var ch in n.GetChildren()) Redraw(ch);
    }

    /// <summary>The keys, as the device in hand has them: plates under the draught, the dash and the Flare. A tag
    /// redraws only when its key or button changed.</summary>
    public void Keys()
    {
        draughtKey.Refresh();
        dashKey.Refresh();
        artKey.Refresh();
    }

    /// <summary>A callout's spotlight: every part dimmed to dim but the one taught (keep: "art", "dash",
    /// "draught", "chain", "socket:ID"); the six places and the passives at slots' strength; the light pulsing
    /// along the river (pulse).</summary>
    public void Spot(string? keep, Color dim, float slots, float pulse)
    {
        Color For(bool kept) => kept ? Colors.White : dim;
        bool chain = keep == "chain";
        Life.Modulate = Keeper.Modulate = For(false);
        Panel.Modulate = For(false);
        // (the chain's callout: the coin's ring and its number kept, the light looping round it)
        Panel.XpRing.Modulate = Panel.Numbers.Modulate = For(chain);
        Panel.Pulse = pulse;
        Art.Modulate = artKey.Modulate = For(keep == "art");
        float over = chain ? slots : 1;
        Dash.Modulate = dashKey.Modulate = For(keep == "dash") with { A = over };
        Draught.Modulate = draughtKey.Modulate = For(keep == "draught") with { A = over };
        Statuses.Modulate = For(false);
        Passives.Modulate = For(false) with { A = slots };
        foreach (var s in Sockets) s.Modulate = For(keep == "socket:" + s.Id && s.Id != "") with { A = slots };
    }

    /// <summary>Debug (--hud-pin seats=f3:h:e): the seats as shown, whatever she carries. f3 is filled at rank 3
    /// of 8, c3 the same coming back (on cooldown), h filled and hot (can evolve), e empty; fewer codes than seats
    /// leaves the rest empty.</summary>
    public void PinSeats(string[] codes)
    {
        var defs = System.Linq.Enumerable.ToList(Content.Weapons.All.Values);
        // (every 7th skill, skipping any whose glyph's family (slash, zone...) is already shown: six different skills)
        var arts = new HashSet<string>();
        int pick = 0;
        for (int i = 0; i < Sockets.Length; i++)
        {
            string c = i < codes.Length ? codes[i] : "e";
            if (c.StartsWith("e") || defs.Count == 0) { Sockets[i].Empty(); continue; }
            var d = defs[(pick * 7) % defs.Count];
            for (int tries = 0; tries < defs.Count && !arts.Add(d.Art.Split('_')[0]); tries++) d = defs[(pick * 7 + tries + 1) % defs.Count];
            pick++;
            bool hot = c.StartsWith("h");
            int rank = hot ? Content.Weapons.MaxRank : int.TryParse(c.AsSpan(1), out var r) ? Math.Clamp(r, 1, Content.Weapons.MaxRank) : 1;
            // (c3: filled at rank 3 and coming back, a quarter, half or three quarters ready by its place)
            double ready = c.StartsWith("c") ? 0.25 + 0.25 * (i % 3) : 1;
            Sockets[i].Show(d.Id, d.Art, ItemViews.SchoolColors[d.School], ready, rank, Content.Weapons.MaxRank, false, hot, ready < 1 ? (1 - ready) * 8 : -1);
        }
    }
}

/// <summary>The Flare (UI 23, HUD A): the dark glass globe in the keeper's bowl, filling with fire as it charges
/// (DgGlobe). (The class keeps the iron HUD's name: GameHud and the callouts address the Flare as the instrument's Art
/// vessel.) Its box is the glass's bezel round DgPanel.GlassAt; the globe's quad reaches past it for its light.</summary>
public partial class Vessel : Control
{
    /// <summary>Half the Flare's box (the glass and its bezel; the glass at its middle).</summary>
    public static readonly Vector2 Half = Vector2.One * Mathf.Ceil(DgPanel.GlassOuterR);
    /// <summary>The draught's count's ink: bone.</summary>
    public static readonly Color Bone = new("#f2e8d6");
    /// <summary>The Flare's charge (0..1): the fire's level in the glass; the ready swell (1 on reaching full).</summary>
    public float Level, Ping;
    public readonly DgGlobe Globe;

    public Vessel()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = Half * 2;
        PivotOffset = Half;
        Globe = new DgGlobe();
        Globe.Position = DgGlobe.Quad.Position - (DgPanel.GlassAt - Half);
        AddChild(Globe);
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

    public override void _Process(double delta) { Globe.Level = Level; Globe.Ping = Ping; }
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
}

/// <summary>The irons' shared light and forged band (the iron HUD's cuffs are retired with it; the Drowned Girl's
/// bronze, her bar under her feet, the key tags and the minimap's bezel still take their light from here).</summary>
public partial class Cuff : Control
{
    /// <summary>By day (her experience) or by night (the ember): the irons' light, dulled by night so
    /// the heat is what the eye finds, brightened steel by day. Instrument.DayNight flips it and redraws the
    /// instrument.</summary>
    public static bool Day;
    public static Color Cold => Day ? new Color(1.2f, 1.22f, 1.28f) : new Color(0.72f, 0.70f, 0.68f);

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

/// <summary>One of the six places for what fires by itself: a well of dark river glass in the plate's baked bezel
/// (DrawRing, UI 23): its skill's gold inlay, the well filling as it readies, a flash as it fires, its rank on a
/// small chip. Ready to evolve, the well's edge breathes gold; evolved, it is rimmed in gold. Empty, a darker, empty
/// well.</summary>
public partial class Socket : Control
{
    public string Id = "";
    /// <summary>Its box across (the old ring's; it draws within DgPanel.SeatR of its middle and its rank chip).</summary>
    public const float SeatD = 78;
    /// <summary>Its place in the row: which ring and well it wears (DgRiver).</summary>
    public int Index;
    Texture2D? art;
    Color school;
    string glyphKey = "";
    int rank, max = 8;
    bool evolved, ripe, filled;
    double ready = 1, lastReady = 1, flash, t, crown = -1;

    public Socket()
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = new Vector2(SeatD, SeatD);
        PivotOffset = Size / 2;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
    }

    public void Empty()
    {
        if (!filled && Id == "") return;
        filled = false; Id = ""; art = null; crown = -1; Scale = Vector2.One; Modulate = Colors.White;
        dirty = false;
        QueueRedraw();
    }

    /// <summary>secs: the seconds left of its wait, where known (the Drowned Girl shows long waits' seconds).</summary>
    public void Show(string id, string glyph, Color school, double ready, int rank, int max, bool evolved, bool canEvolve, double secs = -1)
    {
        int ws = secs >= 0 ? (int)Math.Ceiling(secs) : -1;
        if (ws != secsShown) { secsShown = ws; dirty = true; }
        waitSecs = secs;
        if (id != Id || !filled) { Id = id; filled = true; lastReady = ready; }
        // The skill's own painting where there is one (the draft's card shows the same), else its drawn glyph.
        var newArt = UiArt.Icon("glyph_color", glyph) ?? Glyphs.Texture(glyph, 78, school, line: true);
        if (glyph != glyphKey) { glyphKey = glyph; dirty = true; }
        // (redrawn only when what it shows changes: MR4, the HUD's redraws were 3.4 ms a frame)
        if (newArt != art || school != this.school || rank != this.rank || Math.Max(1, max) != this.max || evolved != this.evolved || canEvolve != ripe || ready != this.ready) dirty = true;
        art = newArt;
        this.school = school; this.rank = rank; this.max = Math.Max(1, max); this.evolved = evolved; ripe = canEvolve;
        if (ready < lastReady - 0.4) flash = 1;
        lastReady = ready;
        this.ready = ready;
    }

    bool dirty = true;
    double waitSecs = -1;
    int secsShown = -1;

    /// <summary>It has evolved: the place swells and burns gold, settling over a second.</summary>
    public void Crown() => crown = 0;

    public override void _Process(double delta)
    {
        t += delta;
        double before = flash;
        flash = Math.Max(0, flash - delta * 4);
        if (flash != before) dirty = true;
        if (crown >= 0)
        {
            crown += delta;
            float k = (float)Math.Clamp(crown / 1.3, 0, 1), e = (1 - k) * (1 - k);
            Scale = Vector2.One * (1 + 0.45f * e * (0.75f + 0.25f * Mathf.Cos((float)crown * 18)));
            Modulate = Colors.White.Lerp(new Color(2.2f, 1.8f, 1.0f), e);
            if (crown >= 1.3) { crown = -1; Scale = Vector2.One; Modulate = Colors.White; }
        }
        // Where it breathes gold (ready to evolve, not yet evolved) it draws by the clock, so it goes on redrawing.
        if (dirty || (filled && ripe && !evolved)) { dirty = false; QueueRedraw(); }
    }

    public override void _Draw() => DrawRing();

    /// <summary>The Drowned Girl (UI 17): the seat as a hair-bound bronze ring in the river (DgRiver.Ring) round a well of
    /// dark river glass (DgRiver.Well), the glass lit faintly in the skill's element. In it the skill's gold inlay
    /// (DgGold), brighter when ready. Round 2 (the judge): coming back, the well fills from its foot, lit in the
    /// element under a dark top (DgMeters.Level: no line across it, which read as a strike-through), with a long
    /// wait's seconds in gold over it; the rank one numeral engraved on top of the ring (round 3: off the key tags'
    /// line, where it read as a keybind); ready to evolve, the ring's inner edge breathing gold (gold when evolved). An empty
    /// seat is the ring round a darker, empty well.</summary>
    void DrawRing()
    {
        var c = Size / 2;
        float hr = DgRiver.Hole(Index);
        if (hr <= 0) hr = Size.X * 0.34f;
        if (DgRiver.Well(Index) is { } well)
        {
            var ws = well.GetSize();
            DrawTextureRect(well, new Rect2(c - ws / 2, ws), false, filled ? Colors.White : new Color(0.7f, 0.7f, 0.7f));
        }
        else DrawCircle(c, hr + 1, new Color(0.03f, 0.06f, 0.065f), true, -1, true);
        bool cooling = filled && ready < 0.98;
        if (filled)
        {
            // (round 2: the element's light in the well's glass, so neighbours read apart by more than shape)
            DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * hr * 1.15f + new Vector2(0, hr * 0.25f), Vector2.One * hr * 2.3f), false, school with { A = 0.42f });
            float g = Mathf.Min(38, hr * 2 * 0.80f);
            // (piece 5: gold inlay, the line glyph's shape, DgGold; lit and warm-lit under when ready, dull bronze-gold
            // coming back; a faint share of the school's colour in the light under it so neighbours differ)
            if (glyphKey != "")
            {
                int gi = (int)Mathf.Round(g);
                var (gold, glowTex) = DgGold.Of(glyphKey, gi);
                var gr = new Rect2(c - new Vector2(gi + 2 * DgGold.Pad, gi + 2 * DgGold.Pad) / 2, new Vector2(gi + 2 * DgGold.Pad, gi + 2 * DgGold.Pad));
                bool up = ready >= 0.98;
                var warm = new Color(1f, 0.62f, 0.24f).Lerp(school, 0.45f);
                if (up || flash > 0) DrawTextureRect(glowTex, gr, false, warm with { A = (up ? 0.42f : 0) + 0.5f * (float)flash });
                var tone = (up ? Colors.White : new Color(0.66f, 0.60f, 0.52f)).Lerp(new Color(1.5f, 1.4f, 1.25f), (float)flash);
                DrawTextureRect(gold, gr, false, (tone * Colors.White.Lerp(school, 0.10f)) with { A = 1 });
            }
            else if (art != null)
            {
                var col2 = ready >= 0.98 ? new Color(1.25f, 1.25f, 1.25f) : Colors.White;
                DrawTextureRect(art, new Rect2(c - new Vector2(g, g) / 2 - new Vector2(0, 2), new Vector2(g, g)), false, col2.Lerp(new Color(2.2f, 2.0f, 1.7f), (float)flash));
            }
            // coming back (round 2): the well fills from its foot, lit in the element, dark above (DgMeters.Level)
            if (cooling) DgMeters.Level(this, c, hr + 0.5f, (float)ready, school);
        }
        // (UI 23: only the ring's inner edge, the well's rim shading, inside the plate's baked bezel)
        if (DgRiver.RingInner(Index, DgPanel.WellR) is { } ring)
        {
            var rs = ring.GetSize();
            DrawTextureRect(ring, new Rect2(c - rs / 2, rs), false);
        }
        if (filled && (evolved || ripe))
        {
            float a = evolved ? 0.9f : 0.45f + 0.4f * (0.5f + 0.5f * Mathf.Sin((float)t * 4.5f));
            DrawArc(c, hr + 0.5f, 0, Mathf.Tau, 64, Style.Gold with { A = a }, 2, true);
            DrawArc(c, hr + 2.5f, 0, Mathf.Tau, 64, Style.EmberHi with { A = a * 0.3f }, 3, true);
        }
        if (filled)
        {
            // a long wait's seconds over the well, gold (the concept's figures); short ones show only the level
            double total = waitSecs > 0 && ready < 0.98 ? waitSecs / Math.Max(0.02, 1 - ready) : 0;
            if (cooling && total >= 3.5 && waitSecs >= 1)
                DgMeters.Numeral(this, c, ((int)Math.Ceiling(waitSecs)).ToString(), 20, DgMeters.Gold, 4);
            // the rank (UI 23): a small dark chip at half past one over the bezel (DgPanel.Marks.Chip), gold-rimmed
            // when it can evolve or has
            if (rank > 0) DgPanel.Marks.Chip(this, c + DgPanel.ChipOff, rank.ToString(), evolved || ripe);
        }
    }
}

/// <summary>The draught and the dash (the Drowned Girl, piece 5): the hair-bound flask and the small ring with its
/// pearls (DgSmall). The draught's count stands beside the flask's foot, on the bronze; the dash's charges are the
/// pearls, its ready form the ring's warm well.</summary>
public partial class Round : Control
{
    public enum Kind { Draught, Dash }
    public static readonly Vector2 Half = new(Instrument.SmallR + Instrument.SmallBand + 6, Instrument.SmallR + Instrument.SmallBand + 6);
    readonly Kind kind;
    readonly DgSmall dg;
    readonly Count2 countOf;
    int countDrawn = int.MinValue;
    public int Count, Max = 2;
    public float Recharge;
    /// <summary>The dash's form (her calling's art riding it, Forms.cs): -1 none; 0..1 its wait coming round; 1
    /// ready: the dash ring's well warm (DgSmall).</summary>
    public float Form = -1;
    /// <summary>The calling's art's glyph (the iron HUD's ready badge; DgSmall shows no badge).</summary>
    public Texture2D? FormGlyph;

    /// <summary>UI 23: drawn at scale s with the flask's (or the dash ring's) middle at mid (DgPanel's geo).</summary>
    public void Place(Vector2 mid, float s)
    {
        PivotOffset = Half + new Vector2(0, kind == Kind.Draught ? DgSmall.FlaskDy : DgSmall.DashDy);
        Scale = new Vector2(s, s);
        Position = mid - PivotOffset;
    }

    public Round(Kind kind)
    {
        this.kind = kind;
        MouseFilter = MouseFilterEnum.Ignore;
        // (its well keeps breathing under a callout's freeze)
        ProcessMode = ProcessModeEnum.Always;
        Size = Half * 2;
        AddChild(dg = new DgSmall(this, kind == Kind.Dash));
        AddChild(countOf = new Count2(this));
    }

    public override void _Process(double delta)
    {
        if (kind == Kind.Draught)
        {
            dg.Tick(Math.Min((float)delta, 0.1f));
            if (Count != countDrawn) { countDrawn = Count; countOf.QueueRedraw(); }
            return;
        }
        if (HudPin.Dash is float dp) { Count = (int)dp; Recharge = dp - (int)dp; }
        // (redrawn only when what it shows changes, or while the ready dash breathes by the clock: MR4, the HUD's
        // redraws were 3.4 ms a frame)
        bool live = Form >= 1;
        if (live || !shown || Count != shownCount || Max != shownMax || Recharge != shownRecharge || Form != shownForm)
        {
            shown = true; shownCount = Count; shownMax = Max; shownRecharge = Recharge; shownForm = Form;
            foreach (var c in GetChildren()) if (c is CanvasItem ci) ci.QueueRedraw();
        }
    }

    bool shown;
    int shownCount, shownMax;
    float shownRecharge, shownForm;

    partial class Count2 : Control
    {
        readonly Round o;
        public Count2(Round o) { this.o = o; MouseFilter = MouseFilterEnum.Ignore; Size = o.Size; }

        public override void _Draw()
        {
            return;   // (UI 23: the count is on its badge, DgPanel.Marks)
#pragma warning disable CS0162
            // the count beside the flask's foot, on the bronze, as the concept has it (Alegreya Sans 800, 16 px,
            // lining tabular figures), bone, dim with none left; a dark outline and a soft shadow
            var f = Vessel.Figures;
            const int fs = 16;
            string s = o.Count.ToString();
            var ts = f.GetStringSize(s, HorizontalAlignment.Left, -1, fs);
            var mid = Size / 2 + new Vector2(23, 12);
            var at = new Vector2(Mathf.Round(mid.X - ts.X / 2), Mathf.Round(mid.Y + 0.293f * fs));
            DrawStringOutline(f, at + new Vector2(0, 1.5f), s, HorizontalAlignment.Left, -1, fs, 7, new Color(0, 0, 0, 0.22f));
            DrawStringOutline(f, at, s, HorizontalAlignment.Left, -1, fs, 3, new Color(0, 0, 0, 0.62f));
            DrawString(f, at, s, HorizontalAlignment.Left, -1, fs, o.Count > 0 ? Vessel.Bone : new Color(0.55f, 0.51f, 0.46f));
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
    float w = 24, cx, cy;
    bool built;
    Control? padView;
    static StyleBoxFlat? plate;

    readonly bool ring;
    /// <summary>UI 23 (mock7.py text_layer chip()): a small dark chip, 16 tall, radius 3, a 1 px bronze rim, the key in
    /// Alegreya Sans 800 16 tracked 0.6, bone; Place puts its top at y.</summary>
    public bool Chip;
    bool lit;
    /// <summary>UI 23 (the Flare's Q): lit, the chip reads "Q  READY", amber on a dark ember ground with a gold rim
    /// (mock7.py chip(lit)). A change redraws it once.</summary>
    public bool Lit
    {
        get => lit;
        set { if (value == lit) return; lit = value; Fit(); }
    }
    string Shown => lit && padName == null && text != "" ? text + "  READY" : text;

    public KeyTag(Act act, bool ring = false)
    {
        this.act = act;
        this.ring = ring;
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        Size = new Vector2(52, Instrument.TagH);
    }

    /// <summary>Hung at x, its plate's top at y (HUD v2: 2 lower under a small cuff, whose band's hole its link
    /// runs from; the art cuff's tag at y itself).</summary>
    /// (The art cuff's tag 3 higher, so its link runs up into a hole drilled in the band's foot, as the small
    /// cuffs' do: KeyTag draws that hole, since cuff.png is the life cuff's too, which hangs no tag.)
    public void Place(float x, float y)
    {
        cx = x; cy = y;
        // (a chip on whole px, its box and its text placed about the true middle in _Draw: the mock's round(cx - w / 2))
        Position = Chip ? new Vector2(Mathf.Floor(x - Size.X / 2), Mathf.Round(y)) : new Vector2(x - Size.X / 2, y + (ring ? -3 : 2));
    }

    float ChipTextW(string s)
    {
        float tw = 0;
        foreach (char ch in s) tw += Style.UiHeavy.GetStringSize(ch.ToString(), HorizontalAlignment.Left, -1, 16).X + 0.6f;
        return tw - 0.6f;
    }

    void Fit()
    {
        if (Chip) Size = new Vector2(Math.Max(Math.Max(52, w), Mathf.Ceil(Math.Max(18, ChipTextW(Shown) + 9)) + 4), Instrument.TagH);
        Place(cx, cy);
        QueueRedraw();
    }

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
        Fit();
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
        if (Chip && padName == null && text != "")
        {
            var cf = Style.UiHeavy;
            string label = Shown;
            float tw = ChipTextW(label);
            // (about the true middle: Place put the chip on whole px)
            float mid = cx - Position.X;
            float cw = Math.Max(18, tw + 9), cx0 = Mathf.Round(mid - cw / 2);
            var box = lit
                ? new StyleBoxFlat { BgColor = new Color(70 / 255f, 34 / 255f, 8 / 255f, 245 / 255f), BorderColor = new Color(1f, 190 / 255f, 90 / 255f), AntiAliasing = true }
                : new StyleBoxFlat { BgColor = new Color(22 / 255f, 18 / 255f, 14 / 255f, 238 / 255f), BorderColor = new Color(138 / 255f, 108 / 255f, 70 / 255f), AntiAliasing = true };
            box.SetBorderWidthAll(1); box.SetCornerRadiusAll(3);
            DrawStyleBox(box, new Rect2(cx0, 0, cw, Instrument.TagH));
            float tx = mid - tw / 2;
            float ty = Instrument.TagH / 2 + 0.5f + (cf.GetAscent(16) - cf.GetDescent(16)) / 2;
            var ink = lit ? new Color(1f, 236 / 255f, 196 / 255f) : new Color(240 / 255f, 230 / 255f, 208 / 255f);
            foreach (char ch in label)
            {
                string s = ch.ToString();
                DrawString(cf, new Vector2(tx, ty), s, HorizontalAlignment.Left, -1, 16, ink);
                tx += cf.GetStringSize(s, HorizontalAlignment.Left, -1, 16).X + 0.6f;
            }
            return;
        }
        float x0 = (Size.X - w) / 2;
        var tag = UiArt.Art($"hud/tag_{(int)w}.png");
        // (HUD v2: the art's plate at image (3, 8), its ear and the link it hangs by above it, cut at the band;
        // in the irons' light, gentler: a rubbed plate is what the eye reads the key on)
        // (HUD v2 r2: the irons' own light, darker: iron like the cuff it hangs from, not a pale steel label; the
        // darkest at which the pressed key still reads at a glance by its lit lip)
        float pl = Cuff.Day ? 0.52f : 0.63f;
        var cold = Cuff.Cold;
        if (tag != null)
        {
            // the art cuff's tag: the hole in the band's foot its link goes into (7 above the plate, on the band's
            // outer slope 3 in from its edge), dark, its lower lip catching a hair of light
            if (ring)
            {
                var hole = new Vector2(Mathf.Round(Size.X / 2) , -7);
                DrawCircle(hole + new Vector2(0.3f, 0.5f), 1.7f, new Color(0.62f, 0.6f, 0.58f, 0.22f), true, -1, true);
                DrawCircle(hole, 1.5f, new Color("#050303") with { A = 0.92f }, true, -1, true);
            }
            DrawTexture(tag, new Vector2(Mathf.Round(Size.X / 2 - w / 2) - 3, -8), new Color(cold.R * pl, cold.G * pl, cold.B * pl));
        }
        else
        {
            plate ??= new StyleBoxFlat { BgColor = new Color("#2a2420"), BorderColor = new Color("#6b5a48"), BorderWidthTop = 1, CornerRadiusTopLeft = 2, CornerRadiusTopRight = 2, CornerRadiusBottomLeft = 2, CornerRadiusBottomRight = 2 };
            DrawStyleBox(plate, new Rect2(x0, 0, w, Instrument.TagH));
        }
        if (padName != null || text == "") return;
        // The key pressed into the plate: its floor dark, a 1 px lip of light at its lower right; its caps' middle
        // on the plate's (Alegreya Sans caps stand 0.645 em)
        var f = Style.UiHeavy;
        float x = Mathf.Round((Size.X - TextWidth()) / 2);
        float y = Mathf.Round(Instrument.TagH / 2 + 0.645f * 14 / 2);
        foreach (char ch in text)
        {
            string s = ch.ToString();
            var p = new Vector2(Mathf.Round(x), y);
            DrawString(f, p + Vector2.One, s, HorizontalAlignment.Left, -1, 14, new Color("#f2e8d6") with { A = 0.55f });
            DrawString(f, p, s, HorizontalAlignment.Left, -1, 14, new Color("#0b0908") with { A = 0.95f });
            x += f.GetStringSize(s, HorizontalAlignment.Left, -1, 14).X + Track;
        }
    }
}

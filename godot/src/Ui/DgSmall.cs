using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (the game's HUD), piece 5, round 2: the draught and the dash in the relief's own language, in
/// place of the small glasses in their iron (Round).
/// The draught: a round flask of scarlet in plain glass, one highlight (round 3: the strand of hair round it read as
/// a stripe; art/ui/dg_meters/flask_full.png and flask_empty.png, tools/uiforge/dg_flask.py, shaders/hud_dg_flask.gdshader). Scarlet, brighter and
/// warmer than the life orb's garnet, so the two never read as one. While one is left it stands full; drunk, it drains
/// with a slosh (0.25 s) and the next fills it (0.6 s); with none left it stands dark. Its count beside it (Round's
/// Count2); its key hangs from its foot on the plates' line (Instrument.DgTagTop).
/// The dash: a hair-bound seat like the skills', smaller (one of the river's rings round a dark well, the dash's mark
/// in gold inlay, DgGold); its charges as pearls set in the ring's lower wrap either side of the key's link, lit when
/// held, the one coming back ringed as it fills; with none left the well fills from its foot as the skills' do
/// (DgMeters.Level). The dash form (her calling's art riding it): its wait a hair of gold round the ring's inner edge,
/// ready a warm breathing well (the old flames and badge are gone in this HUD).
/// </summary>
public partial class DgSmall : Control
{
    /// <summary>The dash's ring across (a seat's is 78), which of the river's rings it wears, its well's share of the
    /// ring (as the seats'), the hole's radius, and how far below the dash's place its middle sits (level with the
    /// seats' row).</summary>
    public const float RingD = 64, WellK = 60f / 78, HoleR = 23, DashDy = 4;
    const int RingOf = 2;
    /// <summary>The flask's middle above the draught's place.</summary>
    public const float FlaskDy = -6;
    /// <summary>The flask's drawn size.</summary>
    public static Vector2 FlaskSize => DgMeterGeo.Flask().Size;
    /// <summary>Where the dash ring is drawn (HUD px): the round's middle, DashDy below it.</summary>
    public static Vector2 DashMid => Instrument.DashAt;
    /// <summary>The dash's and the flask's callout radii as drawn (UI 23: at DgPanel's scales).</summary>
    public static float DashR => RingD / 2 * DgPanel.DashScale;
    public static float FlaskR => Math.Max(FlaskSize.X, FlaskSize.Y) / 2 * DgPanel.FlaskScale;
    /// <summary>Where the flask is drawn (HUD px): the round's middle, FlaskDy above it.</summary>
    public static Vector2 DraughtMid => Instrument.DraughtAt;
    /// <summary>The dash's glass light (it has no element): the river's cold green.</summary>
    static readonly Color Glass = new(0.55f, 0.85f, 0.80f);
    readonly Round o;
    readonly bool dash;
    readonly ShaderMaterial? fmat;
    float lvl = 1, wave;
    int had = -1;
    bool draining;
    static readonly StringName ULevel = "level", UWave = "wave";

    public DgSmall(Round o, bool dash)
    {
        this.o = o;
        this.dash = dash;
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        Size = o.Size;
        if (dash) return;
        var (fs, top, bot) = DgMeterGeo.Flask();
        fmat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_flask.gdshader") };
        if (UiArt.Tex("dg_meters/flask_full.png") is { } full && UiArt.Tex("dg_meters/flask_empty.png") is { } empty)
        {
            fmat.SetShaderParameter("full_tex", full);
            fmat.SetShaderParameter("empty_tex", empty);
        }
        else GD.PushError("DgSmall: dg_meters/flask_*.png did not load: the draught draws blank");
        fmat.SetShaderParameter("top", top);
        fmat.SetShaderParameter("bot", bot);
        // (its foot clear above the key plates' line, Instrument.DgTagTop, so R hangs from it inside the bar)
        AddChild(new ColorRect { Material = fmat, MouseFilter = MouseFilterEnum.Ignore, Size = fs, Position = Size / 2 - fs / 2 + new Vector2(0, FlaskDy) });
    }

    /// <summary>The draught's level (Round._Process, each frame).</summary>
    public void Tick(float dt)
    {
        if (fmat == null) return;
        int n = Math.Max(0, o.Count);
        float want = n > 0 ? 1 : Math.Clamp(o.Recharge, 0, 1);
        if (had < 0) { had = n; lvl = want; }
        if (n < had) { draining = true; wave = 1; }
        else if (n > had && had == 0) wave = 0.6f;
        had = n;
        if (draining) { lvl = Mathf.MoveToward(lvl, 0, dt * 4); if (lvl <= 0) draining = false; }
        else lvl = Mathf.MoveToward(lvl, want, dt / 0.6f);
        wave = Mathf.MoveToward(wave, 0, dt * 1.2f);
        fmat.SetShaderParameter(ULevel, lvl);
        fmat.SetShaderParameter(UWave, wave);
    }

    public override void _Draw()
    {
        if (!dash) return;
        // (round 2: rebuilt as a hair-bound seat like the skills', a little smaller, its middle level with theirs)
        var c = Size / 2 + new Vector2(0, DashDy);
        bool any = o.Count > 0;
        float hr = HoleR;
        if (DgRiver.Well(RingOf) is { } well)
        {
            float wd = RingD * WellK;
            DrawTextureRect(well, new Rect2(c - Vector2.One * wd / 2, Vector2.One * wd), false, any ? Colors.White : new Color(0.72f, 0.72f, 0.72f));
        }
        else DrawCircle(c, hr + 1, new Color(0.03f, 0.06f, 0.065f), true, -1, true);
        // the form ready (her calling's art riding the dash): the well warm, breathing (the old flames and badge are gone)
        float t = Time.GetTicksMsec() / 1000f;
        if (o.Form >= 1) DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * hr * 1.2f, Vector2.One * hr * 2.4f), false,
            new Color(1f, 0.55f, 0.18f, 0.30f + 0.16f * (0.5f + 0.5f * Mathf.Sin(t * 3.2f))));
        else DrawTextureRect(DgMeters.Disc, new Rect2(c - Vector2.One * hr * 1.15f + new Vector2(0, hr * 0.25f), Vector2.One * hr * 2.3f), false, Glass with { A = 0.22f });
        const int gi = 26;
        var (gold, glow) = DgGold.Of("dash", gi);
        var gr = new Rect2(c - Vector2.One * (gi / 2f + DgGold.Pad), Vector2.One * (gi + 2 * DgGold.Pad));
        if (any) DrawTextureRect(glow, gr, false, new Color(1f, 0.62f, 0.24f, o.Form >= 1 ? 0.65f : 0.42f));
        DrawTextureRect(gold, gr, false, any ? Colors.White : new Color(0.66f, 0.60f, 0.52f));
        // none left: the well fills from its foot as the next comes back (the seats' way, DgMeters.Level)
        if (!any) DgMeters.Level(this, c, hr + 0.5f, Math.Clamp(o.Recharge, 0, 1), Glass);
        if (DgRiver.Ring(RingOf) is { } ring) DrawTextureRect(ring, new Rect2(c - Vector2.One * RingD / 2, Vector2.One * RingD), false);
        // the form's wait coming round: a hair of gold on the ring's inner edge from the top
        if (o.Form >= 0 && o.Form < 1)
            DrawArc(c, hr + 1.2f, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * o.Form, 48, DgMeters.Gold with { A = 0.75f }, 1.6f, true);
        // the charges: pearls set in the ring's lower wrap either side of the key's link, lit when held, the one
        // coming back ringed as it fills; they fill from the left
        int m = Math.Clamp(o.Max, 1, 6);
        float pr = (hr + RingD / 2) / 2;
        for (int i = 0; i < m; i++)
        {
            var p = c + Vector2.FromAngle(Mathf.DegToRad(PearlDeg(i, m))) * pr;
            DrawCircle(p + new Vector2(0.5f, 0.8f), 4.6f, new Color(0, 0, 0, 0.6f), true, -1, true);
            DrawCircle(p, 4.1f, new Color(0.331f, 0.247f, 0.140f), true, -1, true);   // (UI 18: round 3's bronze grade)
            DrawCircle(p, 3.1f, new Color(0.05f, 0.045f, 0.04f), true, -1, true);
            if (i < o.Count)
            {
                DrawCircle(p, 3.0f, new Color(0.90f, 0.86f, 0.77f), true, -1, true);
                DrawCircle(p + new Vector2(0.6f, 0.8f), 1.8f, new Color(0.70f, 0.64f, 0.55f, 0.6f), true, -1, true);
                DrawCircle(p + new Vector2(-0.9f, -1f), 1.1f, new Color(1, 1, 1, 0.95f), true, -1, true);
            }
            else if (i == o.Count && o.Recharge > 0)
            {
                DrawCircle(p, 2.6f, new Color(0.90f, 0.86f, 0.77f, 0.25f + 0.35f * o.Recharge), true, -1, true);
                DrawArc(p, 4.1f, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * o.Recharge, 20, new Color(1f, 0.86f, 0.55f, 0.95f), 1.3f, true);
            }
        }
    }

    /// <summary>The i-th of m pearls' angle on the lower wrap (degrees, 0 = right, 90 = down), left to right,
    /// half on each side of the key's link at the foot (which keeps 60..120 clear).</summary>
    static float PearlDeg(int i, int m)
    {
        int left = (m + 1) / 2;
        if (i < left) return 140 + 24 * (left - 1 - i);
        return 40 - 24 * (i - left);
    }
}

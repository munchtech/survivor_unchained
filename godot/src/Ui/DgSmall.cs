using System;
using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// UI 17, The Drowned Girl (--hud drowned), piece 5: the draught and the dash in the relief's own language, in place
/// of the small glasses in their iron (Round, when LifeLamp.Drowned).
/// The draught: a round flask of scarlet bound by a lock of her bronze hair (art/ui/dg_river/flask_full.png and
/// flask_empty.png, tools/uiforge/dg_flask.py, shaders/hud_dg_flask.gdshader). Scarlet, brighter and warmer than the
/// life orb's garnet, so the two never read as one. While one is left it stands full; drunk, it drains with a slosh
/// (0.25 s) and the next fills it (0.6 s); with none left it stands dark. Its count beside it (Round's Count2).
/// The dash: a small hair-bound ring (a seat's ring, smaller) round a dark well with the dash's mark in gold inlay
/// (DgGold); its charges as pearls set under it, lit when held, the one coming back ringed as it fills; with none
/// left the well's shade and water line (as the skills' cooldown) show the next one coming. The dash form (her
/// calling's art riding it) keeps its wait's arc and its ready flames (Round).
/// </summary>
public partial class DgSmall : Control
{
    /// <summary>The dash's ring across, its well's radius, the pearls' row below its middle.</summary>
    public const float RingD = 50, WellR = 18, PearlY = 29.5f, PearlGap = 11;
    readonly Round o;
    readonly bool dash;
    readonly ShaderMaterial? fmat;
    float lvl = 1, wave;
    int had = -1;
    bool draining;
    static readonly StringName ULevel = "level", UWave = "wave";

    /// <summary>The flask's size shown and the liquid's top and foot in it (river_geo.json "flask").</summary>
    static (Vector2 Size, float Top, float Bot) FlaskGeo()
    {
        var path = $"{UiArt.Root}dg_river/river_geo.json";
        if (FileAccess.FileExists(path) && Json.ParseString(FileAccess.GetFileAsString(path)).AsGodotDictionary() is { } d
            && d.TryGetValue("flask", out var f) && f.AsGodotDictionary() is { } g)
            return (new Vector2((float)g["w"].AsDouble(), (float)g["h"].AsDouble()), (float)g["top"].AsDouble(), (float)g["bot"].AsDouble());
        return (new Vector2(47, 64), 0.44f, 0.95f);
    }

    public DgSmall(Round o, bool dash)
    {
        this.o = o;
        this.dash = dash;
        MouseFilter = MouseFilterEnum.Ignore;
        TextureFilter = TextureFilterEnum.LinearWithMipmaps;
        Size = o.Size;
        if (dash) return;
        var (fs, top, bot) = FlaskGeo();
        fmat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_flask.gdshader") };
        if (UiArt.Tex("dg_river/flask_full.png") is { } full && UiArt.Tex("dg_river/flask_empty.png") is { } empty)
        {
            fmat.SetShaderParameter("full_tex", full);
            fmat.SetShaderParameter("empty_tex", empty);
        }
        else GD.PushError("DgSmall: dg_river/flask_*.png did not load: the draught draws blank");
        fmat.SetShaderParameter("top", top);
        fmat.SetShaderParameter("bot", bot);
        // (its belly a little above the round's middle, so the key tag hangs clear under it)
        AddChild(new ColorRect { Material = fmat, MouseFilter = MouseFilterEnum.Ignore, Size = fs, Position = Size / 2 - fs / 2 + new Vector2(0, -3) });
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
        var c = Size / 2;
        bool any = o.Count > 0;
        if (DgRiver.Well(3) is { } well)
            DrawTextureRect(well, new Rect2(c - Vector2.One * (WellR + 1.5f), Vector2.One * 2 * (WellR + 1.5f)), false, any ? Colors.White : new Color(0.75f, 0.75f, 0.75f));
        else DrawCircle(c, WellR + 1, new Color(0.03f, 0.06f, 0.065f), true, -1, true);
        const int gi = 22;
        var (gold, glow) = DgGold.Of("dash", gi);
        var gr = new Rect2(c - Vector2.One * (gi / 2f + DgGold.Pad), Vector2.One * (gi + 2 * DgGold.Pad));
        if (any) DrawTextureRect(glow, gr, false, new Color(1f, 0.62f, 0.24f, 0.42f));
        DrawTextureRect(gold, gr, false, any ? Colors.White : new Color(0.62f, 0.56f, 0.48f));
        // none left: the shade from the top of the well down to what is still to come back, its edge a water line
        if (!any)
        {
            float r = WellR + 0.5f, yCut = -r + 2 * r * (1 - Math.Clamp(o.Recharge, 0, 1));
            float a0 = Mathf.Asin(Mathf.Clamp(yCut / r, -1, 1));
            var pts = new List<Vector2>();
            const int n = 32;
            for (int k = 0; k <= n; k++)
            {
                float a = a0 + (-Mathf.Pi - 2 * a0) * k / n;
                pts.Add(c + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * r);
            }
            if (pts.Count >= 3) DrawColoredPolygon(pts.ToArray(), new Color(0.015f, 0.012f, 0.02f, 0.72f));
            float half = Mathf.Sqrt(Mathf.Max(0, r * r - yCut * yCut)) - 1.5f;
            if (half > 2) DrawLine(c + new Vector2(-half, yCut), c + new Vector2(half, yCut), new Color(0.80f, 0.92f, 0.88f, 0.55f), 1.3f, true);
        }
        if (DgRiver.Ring(4) is { } ring) DrawTextureRect(ring, new Rect2(c - Vector2.One * RingD / 2, Vector2.One * RingD), false);
        // the form's wait coming round (the ready form's flames are Round's)
        if (o.Form >= 0 && o.Form < 1)
            DrawArc(c, RingD / 2 + 3, -Mathf.Pi / 2, -Mathf.Pi / 2 + Mathf.Tau * o.Form, 48, new Color(1f, 0.6f, 0.2f, 0.5f), 2, true);
        // the charges: pearls set in the bronze under the ring
        int m = Math.Max(1, o.Max);
        for (int i = 0; i < m; i++)
        {
            var p = c + new Vector2((i - (m - 1) / 2f) * PearlGap, PearlY);
            DrawCircle(p + new Vector2(0.5f, 0.8f), 4.6f, new Color(0, 0, 0, 0.6f), true, -1, true);
            DrawCircle(p, 4.1f, new Color(0.36f, 0.27f, 0.15f), true, -1, true);
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
}

using System;
using Godot;
using SurvivorUnchained.Sim;
using SurvivorUnchained.View;

namespace SurvivorUnchained.Ui;

/// <summary>M4 (docs/design/M4_HUD.md section 2): Resolve as heat rising through the Drowned Girl's hair. One quad
/// over her figure (a child of LifeLamp, so LifeLamp.Group's transform is its own), hud_dg_resolve.gdshader over
/// lamp_veins.png (tools/uiforge/dg_resolve_veins.py). ResolveMotion holds the numbers; this sends each uniform only
/// when it changes. The bands are the school's (fx_language.json; the warden's steel is "physical").</summary>
public sealed partial class ResolveVeins : ColorRect
{
    public readonly ResolveMotion Motion = new();
    readonly ShaderMaterial mat;
    readonly Color edge, core, spark;
    float sLevel = -1, sAlpha = -1, sPktG = -2, sPktK = -1, sPktW = -1, sFlare = -1, sSpentK = -1, sDrain = -1, sCool = -1,
        sShimmer = -2, sGlint = -1, sRim = -1;
    Vector2 sSpent = new(-1, -1);
    ResolveMotion.Packet sPkt = (ResolveMotion.Packet)(-1);
    static readonly StringName ULevel = "level", UAlpha = "alpha", UPktG = "pkt_g", UPktK = "pkt_k", UPktW = "pkt_w",
        UPktC = "pkt_c", UFlare = "flare", USpent = "spent", USpentK = "spent_k", UDrain = "drain", UCool = "cool",
        UShimmer = "shimmer_g", UGlint = "glint", URim = "rim";

    public ResolveVeins(Vector2 canvas, Texture2D? cold, Vector2 crown, string school = "physical")
    {
        MouseFilter = MouseFilterEnum.Ignore;
        Size = canvas;
        Visible = false;
        mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/hud_dg_resolve.gdshader") };
        Material = mat;
        if (UiArt.Tex("lamp_life/drowned/lamp_veins.png", false) is { } v)
        {
            mat.SetShaderParameter("veins", v);
            mat.SetShaderParameter("tex_px", v.GetSize());
        }
        else GD.PushError("ResolveVeins: lamp_life/drowned/lamp_veins.png did not load (unimported?): no Resolve in her hair");
        if (cold != null) mat.SetShaderParameter("cold", cold);
        mat.SetShaderParameter("canvas", canvas);
        mat.SetShaderParameter("crown", crown);
        var s = FxCel.Lang[school] ?? FxCel.Lang["physical"]!;
        edge = new Color(s.Edge.Hex); core = new Color(s.Core.Hex); spark = new Color(s.Sparks.Hex);
        mat.SetShaderParameter("c_edge", edge);
        mat.SetShaderParameter("c_mid", new Color(s.Mid.Hex));
        mat.SetShaderParameter("c_core", core);
        mat.SetShaderParameter("c_spark", spark);
        if (HudPin.Resolve is float pl) Motion.Pin(pl, HudPin.ResolveWhy ?? "");
    }

    /// <summary>A frame: dt, and her figure's fade now (LifeLamp's fig_a and its FadeTo).</summary>
    public void Tick(float dt, float figA, float fadeTo)
    {
        var m = Motion;
        m.Tick(dt);
        if (Visible != m.Shown) Visible = m.Shown;
        if (!m.Shown) return;
        Send(ULevel, m.Level, ref sLevel);
        Send(UAlpha, ResolveMotion.Alpha(figA, fadeTo), ref sAlpha);
        Send(UPktG, m.PktG, ref sPktG);
        Send(UPktK, m.PktK, ref sPktK);
        Send(UPktW, m.PktW, ref sPktW);
        if (m.PktColor != sPkt)
        {
            sPkt = m.PktColor;
            mat.SetShaderParameter(UPktC, sPkt == ResolveMotion.Packet.Edge ? edge : sPkt == ResolveMotion.Packet.Spark ? spark : core);
        }
        Send(UFlare, m.Flare, ref sFlare);
        var sp = new Vector2(m.SpentLo, m.SpentHi);
        if (sp != sSpent) { sSpent = sp; mat.SetShaderParameter(USpent, sp); }
        Send(USpentK, m.SpentK, ref sSpentK);
        Send(UDrain, m.Drain, ref sDrain);
        Send(UCool, m.Cool, ref sCool);
        Send(UShimmer, m.ShimmerG, ref sShimmer);
        Send(UGlint, m.Glint, ref sGlint);
        Send(URim, m.Rim, ref sRim);
    }

    void Send(StringName u, float v, ref float sent)
    {
        if (v == sent) return;
        sent = v;
        mat.SetShaderParameter(u, v);
    }
}

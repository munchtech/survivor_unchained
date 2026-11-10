using System;
using Godot;
using SurvivorUnchained.Sim;


namespace SurvivorUnchained.View;

/// <summary>(L1 lead 26, M4 row b) The held lamp's pool edge as a world ground mark (it left the HUD in 7d2c06467):
/// a ring of painted warm-white dabs at the pool's radius, following the ground (+5 cm), shown while a caught, lit lamp's
/// pool is somewhere she is not (<see cref="SurvivorUnchained.Ui.LampPoolEdge.Show"/>), fading over 0.2 s as she crosses the edge. One mesh,
/// one draw (shaders/lamp_pool.gdshader), drawn after the grade and occluded by the world as P7's rings are (FxAfter's
/// layer + FxWorldDepth). --lamp-pool off: none of it.</summary>
public partial class BattleFx
{
    const int LampPoolSegs = 240;
    const float LampPoolLift = 0.05f;
    static readonly bool LampPoolOn = Args.Get("lamp-pool") != "off";
    MeshInstance3D? lampPool;
    ShaderMaterial? lampPoolMat;
    float lampPoolA;
    int lampPoolLog = -1;
    double lampPoolX = double.NaN, lampPoolZ, lampPoolR;

    void LampPool(Battle b, float dt)
    {
        var l = b.HeldLamp;
        bool on = LampPoolOn && SurvivorUnchained.Ui.LampPoolEdge.Show(l, b.Player.X, b.Player.Z);
        lampPoolA = SurvivorUnchained.Ui.LampPoolEdge.Step(lampPoolA, on, dt);
        if (Args.Has("stage-log") && l != null && (int)(time * 2) != lampPoolLog) { lampPoolLog = (int)(time * 2); GD.Print($"lamp-pool lamp ({l.X:F1},{l.Z:F1}) r {l.Pool:F1} caught {l.Caught} lit {l.Lit} her ({b.Player.X:F1},{b.Player.Z:F1}) a {lampPoolA:F2}"); }
        if (lampPoolA <= 0 || l == null) { if (lampPool != null) lampPool.Visible = false; return; }
        if (lampPool == null)
        {
            lampPoolMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/lamp_pool.gdshader") };
            lampPoolMat.SetShaderParameter("fx_after", FxAfter.On ? 1f : 0f);
            lampPoolMat.SetShaderParameter("lp_seed", R() * 10);
            lampPool = new MeshInstance3D { MaterialOverride = lampPoolMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off, Name = "LampPoolEdge" };
            AddChild(lampPool);
            lampPool.GlobalTransform = Transform3D.Identity;
            if (FxAfter.On) FxAfter.Adopt(lampPool);
        }
        if (l.X != lampPoolX || l.Z != lampPoolZ || l.Pool != lampPoolR) LampPoolBuild(b, l);
        lampPool.Visible = true;
        // the fade in steps of a quarter (the board's stepped life), never a smooth ramp
        lampPoolMat!.SetShaderParameter("lp_alpha", Mathf.Ceil(lampPoolA * 4f) / 4f);
    }

    void LampPoolBuild(Battle b, LampMark l)
    {
        lampPoolX = l.X; lampPoolZ = l.Z; lampPoolR = l.Pool;
        float half = 0.13f;
        lampPoolMat!.SetShaderParameter("lp_half", half);
        lampPoolMat.SetShaderParameter("lp_circ", (float)(Math.Tau * l.Pool));
        var st = new SurfaceTool();
        st.Begin(Mesh.PrimitiveType.Triangles);
        for (int i = 0; i <= LampPoolSegs; i++)
        {
            float u = i / (float)LampPoolSegs;
            double t = u * Math.Tau, c = Math.Cos(t), s = Math.Sin(t);
            for (int k = 0; k < 2; k++)
            {
                double r = l.Pool + (k == 0 ? -half : half), x = l.X + c * r, z = l.Z + s * r;
                st.SetUV(new Vector2(u, k == 0 ? -1 : 1));
                st.SetNormal(Vector3.Up);
                st.AddVertex(new Vector3((float)x, (float)b.HeightAt(x, z) + LampPoolLift, (float)z));
            }
        }
        for (int i = 0; i < LampPoolSegs; i++)
        {
            int a = i * 2;
            st.AddIndex(a); st.AddIndex(a + 1); st.AddIndex(a + 2);
            st.AddIndex(a + 1); st.AddIndex(a + 3); st.AddIndex(a + 2);
        }
        lampPool!.Mesh = st.Commit();
    }
}

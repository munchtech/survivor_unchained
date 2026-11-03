using System.Collections.Generic;
using Godot;

namespace SurvivorUnchained.Ui;

/// <summary>
/// The Lamps' Open wide over the live world (docs/design/LAMPS_SCREEN_BRIEF.md §12 A, §16 "A's night grade"; the mock's
/// skins/a.py grade() and pools()): on its own canvas layer over the 3D and under the HUD (10) and the screens (20), a
/// back-buffer copy, the grade (shaders/ui_lamps_grade.gdshader, one full-screen pass) and the pools (one MultiMesh, an
/// instance per lit lamp in the field, reading the same copy: the world's own colors back round her lit lamps). The
/// UI above it is never graded. Amount fades it (0.35 s in, 0.2 s out).
/// </summary>
public partial class LampGrade : CanvasLayer
{
    public const int MaxPools = 160;
    readonly ShaderMaterial gradeMat, poolMat;
    readonly MultiMeshInstance2D pools = new();
    float amount;

    public LampGrade(bool night)
    {
        Layer = 9;
        AddChild(new BackBufferCopy { CopyMode = BackBufferCopy.CopyModeEnum.Viewport });
        gradeMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_grade.gdshader") };
        gradeMat.SetShaderParameter("night", night ? 1f : 0f);
        var rect = new ColorRect { Color = Colors.White, MouseFilter = Control.MouseFilterEnum.Ignore, Material = gradeMat, Size = new Vector2(1920, 1080) };
        AddChild(rect);
        poolMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/ui_lamps_pool.gdshader") };
        pools.Material = poolMat;
        var arr = new Godot.Collections.Array();
        arr.Resize((int)Mesh.ArrayType.Max);
        arr[(int)Mesh.ArrayType.Vertex] = new Vector2[] { new(-0.5f, -0.5f), new(0.5f, -0.5f), new(0.5f, 0.5f), new(-0.5f, 0.5f) };
        arr[(int)Mesh.ArrayType.TexUV] = new Vector2[] { new(0, 0), new(1, 0), new(1, 1), new(0, 1) };
        arr[(int)Mesh.ArrayType.Index] = new int[] { 0, 1, 2, 0, 2, 3 };
        var quad = new ArrayMesh();
        quad.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arr);
        pools.Multimesh = new MultiMesh
        {
            TransformFormat = MultiMesh.TransformFormatEnum.Transform2D, UseCustomData = true, Mesh = quad,
            InstanceCount = MaxPools, VisibleInstanceCount = 0,
        };
        AddChild(pools);
        Amount = 0;
    }

    /// <summary>0: the world as it is; 1: the grade and the pools at full.</summary>
    public float Amount
    {
        get => amount;
        set { amount = value; gradeMat.SetShaderParameter("amount", value); poolMat.SetShaderParameter("amount", value); }
    }

    /// <summary>The pools' field (the board's window in framebuffer px, its per-side feathers, the foot's and her knockout).</summary>
    public void Field(Vector4 win, Vector4 fe, Vector2 vp, Texture2D? hud, Texture2D? her)
    {
        poolMat.SetShaderParameter("win", win);
        poolMat.SetShaderParameter("fe", fe);
        poolMat.SetShaderParameter("vp_size", vp);
        poolMat.SetShaderParameter("knock_on", 1f);
        if (hud != null) poolMat.SetShaderParameter("knock_hud", hud);
        // (her own pool: the pools light her, as the mock's; only the foot's knockout holds them)
        gradeMat.SetShaderParameter("vp_size", vp);
    }

    /// <summary>The lit lamps on the screen (sigma 34 px; 14 at the Valley).</summary>
    public void Pools(IReadOnlyList<Vector2> at, bool valley)
    {
        float sg = valley ? 14 : 34, side = 6 * sg;
        int n = System.Math.Min(at.Count, MaxPools);
        var mm = pools.Multimesh;
        for (int i = 0; i < n; i++)
        {
            mm.SetInstanceTransform2D(i, new Transform2D(0, new Vector2(side, side), 0, at[i]));
            mm.SetInstanceCustomData(i, new Color(sg, 0, 0, 0));
        }
        mm.VisibleInstanceCount = n;
    }
}

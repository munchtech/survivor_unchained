using System;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.View;

/// <summary>
/// Her held grip's cut (M3 MR 2, item 9; the most-seen effect in the game): ONE painted stroke where the blade travels,
/// in the steel family's bands (L1's fx_stroke through shaders/fx_grip_stroke.gdshader, after the grade), and a short
/// hard star where the blade meets a foe. Under the spenders by rule: the stroke rides the blade's own reach (1.7-2.1 m,
/// not the cut's hit reach), is about 0.4 m wide at its head, and is gone 0.2 s after the contact (the grip
/// repeats every 0.7-1.4 s). Sunder's is the heavy one (wider, shorter, dust under it); the Oathblade's is longer and
/// thinner and keeps its gold pool on the ground. Called from Swing() for a held cut; at --cel off or --p7fx-off (or
/// --grip-old) Swing() draws the old crescents.
/// </summary>
public partial class BattleFx
{
    static readonly bool GripStrokeOn = FxCel.On && !P7Off && !Args.Has("grip-old");
    const string GripShader = "res://shaders/fx_grip_stroke.gdshader";
    static ArrayMesh? gripMesh;
    static readonly Color GripSpark = Hdr("#fdd171", 1.5f);

    /// <summary>The stroke's numbers by weapon: the head's half-width (a share of the blade's reach), the stroke's
    /// longest length (radians), how long the blade takes across the cut, and the star's half-size and spikes.</summary>
    readonly record struct GripLook(float Hw, float Len, float Cross, float Star, int Spikes);
    static readonly GripLook GripSunder = new(0.11f, 1.7f, 0.09f, 0.7f, 5), GripOath = new(0.085f, 1.9f, 0.07f, 0.5f, 4);
    /// <summary>After the blade has crossed: a breath whole, then a step every GripStep (core, gold, amber out).</summary>
    const float GripHold = 0.02f, GripStep = 0.035f;

    void GripCut(Ev.Slash e, Vector3 at, float facing, float reach, float g, bool oath)
    {
        if (oath && AaFxOff) return;
        var look = oath ? GripOath : GripSunder;
        // Where the blade travels: her arm and the sword, not the cut's hit reach; the middle of the cone, not all of it.
        float r = Mathf.Clamp(reach * 0.62f, 1.7f, 2.1f);
        float span = Mathf.Clamp((float)e.Arc * 0.68f, 1.5f, 2.6f);
        float maxLen = look.Len / span, cross = look.Cross, hold = cross + GripHold;
        var m = new ShaderMaterial { Shader = GD.Load<Shader>(GripShader) };
        FxCel.Apply(m, School.Physical, FxAfter.On);
        P7Brush(m, 2 * look.Hw * r / P7Px(at), 0.05f);
        // A clean cut: a wetter brush than a skill's smear (less dry at the tail, less waver at the band edges).
        m.SetShaderParameter("fx_bristle", new Vector4(Mathf.Clamp(2 * look.Hw * r / P7Px(at) / 3f, 1f, 24f), 12f, 0.3f, 0.12f));
        m.SetShaderParameter("grip_span", span);
        m.SetShaderParameter("grip_hw", look.Hw);
        var n = new MeshInstance3D
        {
            Mesh = gripMesh ??= GripGrid(56, 8), MaterialOverride = m, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            CustomAabb = new Aabb(new Vector3(-1.2f, -0.3f, -1.2f), new Vector3(2.4f, 0.9f, 2.4f)),
        };
        AddChild(n);
        // The mirror is the cut's own (its local X), before the turn: as Blades.Add.
        n.GlobalTransform = new Transform3D(new Godot.Basis(Vector3.Up, facing) * Godot.Basis.FromScale(new Vector3(mirror ? -r : r, r, r)), at);
        if (FxAfter.On) FxAfter.Adopt(n);
        var s = new P7Shape
        {
            N = n, M = m, Life = hold + 3 * GripStep,
            Step = x =>
            {
                // Born a third of the way in (the contact frame shows a stroke, not a point), fast across, then stepped out
                // from the tail: nothing fades.
                float k = Mathf.Clamp(x.Age / cross, 0, 1);
                float head = 0.34f + 0.66f * (1 - Mathf.Pow(1 - k, 2.2f));
                int gone = x.Age < hold ? 0 : Math.Min(3, (int)((x.Age - hold) / GripStep) + 1);
                x.M.SetShaderParameter("grip_head", head);
                x.M.SetShaderParameter("grip_len", Mathf.Min(maxLen, head) * (1 - 0.22f * gone));
                x.M.SetShaderParameter("grip_life", gone / 3f);
            },
        };
        p7Shapes.Add(s);
        s.Step(s);
        // A few tears of steel flung off where the cut ends.
        float aEnd = (float)e.Angle + span * 0.42f * (mirror ? -1 : 1);
        var rim = new Vector3(Mathf.Cos(aEnd), 0, Mathf.Sin(aEnd));
        var tan = new Vector3(-rim.Z, 0, rim.X) * (mirror ? -1 : 1);
        for (int i = 0; i < (oath ? 2 : 3); i++)
            Sparks.Spawn(at + rim * r * (0.85f + R() * 0.15f), tan * (5 + R() * 4) + Vector3.Up * (0.5f + R() * 1.5f), 0.12f + R() * 0.08f, 0.03f + R() * 0.012f, GripSpark, GripSpark * 0.5f, 0.01f, 7, 2.5f);
        // The contact: one hard star at the nearest body it struck, a step toward her (where the edge met it).
        if (e.Struck > 0)
        {
            var body = V(e.HitX, Y(e.HitX, e.HitZ) + 1.0, e.HitZ);
            var to = new Vector3(at.X - body.X, 0, at.Z - body.Z);
            if (to.LengthSquared() > 0.01f) body += to.Normalized() * 0.25f;
            P7Star(body, look.Star * Mathf.Min(g, 1.2f), look.Spikes, 3 / 60f, bill: true, step: 0.04f);
            if (!oath) Cam?.AddTrauma(0.03f);
        }
        float mid = (float)e.Angle;
        double tx = e.X + Mathf.Cos(mid) * r * 0.9f, tz = e.Z + Mathf.Sin(mid) * r * 0.9f;
        if (!oath)
        {
            // The heavy blade's grit where it passes nearest the ground.
            Dust(tx, tz, 4, 1.8f * g);
            Cam?.AddTrauma(0.02f);
            return;
        }
        // The Oathblade's own: its gold on the ground under the cut, the struck's streaks along its path (HitKit), and a
        // ranked blade's hanging glints.
        oathAt = at; oathMirror = mirror; oathKits = 0;
        OathPool(V(tx, Y(tx, tz) + 0.3, tz), e.Art == "slash_blood" ? new Color("#ff6a40") : new Color("#ffc25a"));
        if (e.Rank >= 5 && e.Art != "slash_blood")
            for (int i = 0; i < 3; i++)
            {
                float a = (float)e.Angle + span * (R() - 0.5f);
                var o = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                Sparks.Spawn(at + o * r * 0.95f, Vector3.Up * 0.4f, 0.25f, 0.1f, OathGold, OathGold * 0.3f, 0.02f, 0, 2, sprite: Sprites.Of("star"), spinV: 3);
            }
    }

    /// <summary>A flat grid of `along` by `across` cells in XZ, its UV 0 to 1 both ways (the shader bends it).</summary>
    static ArrayMesh GripGrid(int along, int across)
    {
        var verts = new Vector3[(along + 1) * (across + 1)];
        var uvs = new Vector2[verts.Length];
        var idx = new int[along * across * 6];
        for (int i = 0; i <= along; i++)
            for (int j = 0; j <= across; j++)
            {
                int v = i * (across + 1) + j;
                verts[v] = new Vector3(i / (float)along, 0, j / (float)across);
                uvs[v] = new Vector2(i / (float)along, j / (float)across);
            }
        int k = 0;
        for (int i = 0; i < along; i++)
            for (int j = 0; j < across; j++)
            {
                int a = i * (across + 1) + j, b = a + across + 1;
                idx[k++] = a; idx[k++] = b; idx[k++] = a + 1;
                idx[k++] = a + 1; idx[k++] = b; idx[k++] = b + 1;
            }
        var arrays = new Godot.Collections.Array();
        arrays.Resize((int)Mesh.ArrayType.Max);
        arrays[(int)Mesh.ArrayType.Vertex] = verts;
        arrays[(int)Mesh.ArrayType.TexUV] = uvs;
        arrays[(int)Mesh.ArrayType.Index] = idx;
        var mesh = new ArrayMesh();
        mesh.AddSurfaceFromArrays(Mesh.PrimitiveType.Triangles, arrays);
        return mesh;
    }
}

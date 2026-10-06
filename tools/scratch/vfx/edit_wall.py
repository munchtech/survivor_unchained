p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\src\Fx\BattleFx.Rise.cs"
s = open(p, encoding="utf-8").read()
old_fields = '''    MeshInstance3D? fireMesh;
    ShaderMaterial? fireMat;
'''
new_fields = '''    MeshInstance3D? fireMesh, wallMesh;
    ShaderMaterial? fireMat, wallMat;
    /// <summary>The wall of flame at its tallest, and how far apart its columns stand.</summary>
    const float WallHigh = 1.55f, WallColumn = 1.5f;
'''
assert old_fields in s
s = s.replace(old_fields, new_fields)
old_start = '''        fireMesh.Visible = true;
        fire = (at, r, time);
        StepFire();'''
new_start = '''        fireMesh.Visible = true;
        // The burning edge itself: filmed flame stood all the way round the front (fire_wall).
        if (wallMesh == null && Flipbooks.Has("fire_loop"))
        {
            wallMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_wall.gdshader") };
            wallMat.SetShaderParameter("atlas", GD.Load<Texture2D>("res://art/fx/fb/fire_loop.png"));
            wallMesh = new MeshInstance3D
            {
                Mesh = new CylinderMesh { TopRadius = 1, BottomRadius = 1, Height = 1, RadialSegments = 160, Rings = 1, CapTop = false, CapBottom = false },
                MaterialOverride = wallMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            };
            AddChild(wallMesh);
        }
        if (wallMesh != null && wallMat != null)
        {
            wallMat.SetShaderParameter("seed", R() * 100);
            wallMat.SetShaderParameter("tiles", Mathf.Max(6, Mathf.Round(Mathf.Tau * r / WallColumn)));
            wallMesh.Visible = true;
        }
        fire = (at, r, time);
        StepFire();'''
assert old_start in s
s = s.replace(old_start, new_start)
old_step = '''        if (fire is not var (_, _, from) || fireMesh == null || fireMat == null) return;
        float t = (float)(time - from);
        if (t > FireRun + FireDown) { fire = null; fireMesh.Visible = false; return; }
        float k = Mathf.Clamp(t / FireRun, 0, 1), ease = 1 - (1 - k) * (1 - k) * (1 - k);
        float down = Mathf.Clamp((t - FireRun) / FireDown, 0, 1);
        fireMat.SetShaderParameter("front", (0.03f + 0.97f * ease) / FireRoom);
        fireMat.SetShaderParameter("fade", 1 - down * down);
        fireMat.SetShaderParameter("cool", down);'''
new_step = '''        if (fire is not var (at, r, from) || fireMesh == null || fireMat == null) return;
        float t = (float)(time - from);
        if (t > FireRun + FireDown) { fire = null; fireMesh.Visible = false; if (wallMesh != null) wallMesh.Visible = false; return; }
        // (Combat's Battle.RiseFront is this same curve: each body catches as the front reaches it.)
        float k = Mathf.Clamp(t / FireRun, 0, 1), ease = 1 - (1 - k) * (1 - k) * (1 - k);
        float down = Mathf.Clamp((t - FireRun) / FireDown, 0, 1);
        fireMat.SetShaderParameter("front", (0.03f + 0.97f * ease) / FireRoom);
        fireMat.SetShaderParameter("fade", 1 - down * down);
        fireMat.SetShaderParameter("cool", down);
        if (wallMesh != null && wallMat != null)
        {
            // The wall rides the front, rising as it runs and standing tallest where it stops,
            // then burning down there, lower and dimmer, its tongues guttering.
            float reach = r * (0.03f + 0.97f * ease);
            float high = WallHigh * (0.45f + 0.55f * ease) * (1 - down * down * 0.85f);
            wallMesh.Position = at + Vector3.Up * (high / 2 - 0.05f);
            wallMesh.Scale = new Vector3(reach, high, reach);
            wallMat.SetShaderParameter("burn", Mathf.Min(1, t / 0.04f) * (1 - down * down));
        }'''
assert old_step in s
s = s.replace(old_step, new_step)
open(p, "w", encoding="utf-8").write(s)
print("ok")

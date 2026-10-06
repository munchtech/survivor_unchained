"""Swap the rise's sprite fire for the fire_ring shader (lines from Catch's summary to the end of Tongue)."""
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a94ac6b67f1279213\godot\src\Fx\BattleFx.Rise.cs"
src = open(p, encoding="utf-8").read()
start = src.index("    /// <summary>Cold, Then Not: the fire going out from her")
end = src.index("    /// <summary>Not Yet: the Order's answer.")
new = '''    /// <summary>Cold, Then Not: the fire going out from her as far as it burns, a ragged front
    /// of flame racing over the ground (shaders/fire_ring.gdshader), burning down where it
    /// stops, the ground left smouldering in a ring.</summary>
    void Catch(Ev.Rise e)
    {
        float gy = Y(e.X, e.Z), r = (float)Math.Max(2, e.Radius);
        var ground = V(e.X, gy, e.Z);
        // Fast, so the crowd it burns is lit as it goes (its burning lands at once).
        Waves.Add(ground + Vector3.Up * 0.4f, r * 1.1f, FireRun, RiseFire, 0.6f);
        StartFire(ground, r);
        // The ember climbing her as she gets up: a few sparks wound up round her.
        for (int i = 0; i < 18; i++)
        {
            float a = i * 0.7f, h = i / 18f;
            var from = ground + new Vector3(Mathf.Cos(a) * 0.5f, 0.1f + h * 0.4f, Mathf.Sin(a) * 0.5f);
            var round = new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a));
            Sparks.Spawn(from, round * 2f + Vector3.Up * (2.2f + h * 2), 0.5f + R() * 0.3f, 0.04f + R() * 0.02f, Ember, EmberDeep, 0.01f, -1, 0.8f);
        }
        // Embers thrown up off the wall of fire where it stops.
        int n = Math.Min(48, (int)(Mathf.Tau * r * 0.8f));
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, d = r * (0.85f + R() * 0.15f);
            double x = e.X + Mathf.Cos(a) * d, z = e.Z + Mathf.Sin(a) * d;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            pending.Add((time + FireRun * (0.7f + R() * 0.5f), () => Sparks.Spawn(V(x, Y(x, z) + 0.3, z), dir * (0.5f + R()) + Vector3.Up * (1.5f + R() * 2.5f),
                0.8f + R() * 0.8f, 0.035f + R() * 0.025f, Ember, EmberDeep, 0.01f, -0.6f, 1.2f)));
        }
        Scars.Add("scorch", ground, 1.4f, 6, 0);
        // The ring of ground it leaves smouldering, laid as the fire burns down.
        pending.Add((time + FireRun, () => Scars.Add("smoulder", ground, r * 1.05f, 7, 0)));
        // Its light low over the ground (the fire's, not hers), and soon gone.
        Flash(ground + Vector3.Up * 0.5f, new Color("#ff6a1a"), 5, 0.4f, r * 1.4f);
        Cam?.AddTrauma(0.4f);
    }

    const float FireRun = 0.3f, FireDown = 1.3f;
    /// <summary>How much of the fire square's half-width its front runs to (its tongues reach past it).</summary>
    const float FireRoom = 1.12f;
    /// <summary>Not Yet's dial: its outer ring's radius, and how high in the air it is held.</summary>
    const float Dial = 2.7f, DialUp = 1.0f;
    /// <summary>The rise's fire: where from, how far, since when; drawn on one square.</summary>
    (Vector3 At, float R, double From)? fire;
    MeshInstance3D? fireMesh;
    ShaderMaterial? fireMat;

    void StartFire(Vector3 at, float r)
    {
        if (fireMesh == null)
        {
            fireMat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_ring.gdshader") };
            fireMesh = new MeshInstance3D { Mesh = new PlaneMesh { Size = new Vector2(2, 2) }, MaterialOverride = fireMat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off };
            AddChild(fireMesh);
        }
        // Just over the ground: the dead stand in it, their feet hidden in the flame.
        fireMesh.Position = at + Vector3.Up * 0.22f;
        fireMesh.Scale = new Vector3(r * FireRoom, 1, r * FireRoom);
        fireMat!.SetShaderParameter("seed", R() * 100);
        // The front about two thirds of a metre deep, whatever its reach.
        fireMat.SetShaderParameter("width", 0.65f / (r * FireRoom));
        fireMesh.Visible = true;
        fire = (at, r, time);
        StepFire();
    }

    /// <summary>The fire's front running out (eased, as a blast's air is), then burning down
    /// where it stopped while the char behind it cools.</summary>
    void StepFire()
    {
        if (fire is not var (_, _, from) || fireMesh == null || fireMat == null) return;
        float t = (float)(time - from);
        if (t > FireRun + FireDown) { fire = null; fireMesh.Visible = false; return; }
        float k = Mathf.Clamp(t / FireRun, 0, 1), ease = 1 - (1 - k) * (1 - k) * (1 - k);
        float down = Mathf.Clamp((t - FireRun) / FireDown, 0, 1);
        fireMat.SetShaderParameter("front", (0.03f + 0.97f * ease) / FireRoom);
        fireMat.SetShaderParameter("fade", 1 - down * down);
        fireMat.SetShaderParameter("cool", down);
    }

'''
src = src[:start] + new + src[end:]
src = src.replace("        StepFire(dt);\n", "        StepFire();\n")
open(p, "w", encoding="utf-8", newline="").write(src)
print("ok", src.count("StepFire"))

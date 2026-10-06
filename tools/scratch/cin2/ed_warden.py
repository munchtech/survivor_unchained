import os
p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot\src\Actors\BossViews.cs"
s = open(p, encoding="utf-8").read()

old = '''    public double Glow { get; set; } = 1;
    const float Size = 2.6f;
'''
new = '''    public double Glow { get; set; } = 1;
    /// <summary>Whether his lamp burns (it goes out in the river in C03).</summary>
    public bool LampLit { get; set; } = true;
    /// <summary>The body, for a cinematic that moves and poses him itself.</summary>
    public PersonView Body => view;
    const float Size = 2.6f;
'''
assert old in s, "glow"
s = s.replace(old, new)

old = '''        flash = Math.Max(flash - dt * 6, e?.Flash ?? 0);
        foreach (var m in skin) m.Emission = new Color(1f, 0.8f, 0.6f) * (float)(flash * 0.25);
        double g = Glow * (pose == "sleep" ? 0.35 : 1) * (pose == "dead" ? 0 : 1);
        foreach (var m in eyes) m.EmissionEnergyMultiplier = (float)(1.2 + g * 2.4 + Math.Sin(time * 5) * g * 0.5);
        // The light is the lamp in his fist, hung a little out from the body.
        double i = g * (5 + Math.Sin(time * 3.1) * 0.8 + (pose == "channel" ? 4 + Math.Sin(time * 14) * 2 : 0));
        light.LightEnergy = (float)(i / Math.PI);
        var at = lamp.GlobalPosition;
        light.GlobalPosition = new Vector3(at.X, Mathf.Max(at.Y, (float)y + 1.2f) + 0.8f, at.Z);
        lamp.Visible = pose != "dead" || g > 0.01;
    }
'''
new = '''        flash = Math.Max(flash - dt * 6, e?.Flash ?? 0);
        foreach (var m in skin) m.Emission = new Color(1f, 0.8f, 0.6f) * (float)(flash * 0.25);
        double g = Glow * (pose == "sleep" ? 0.35 : 1) * (pose == "dead" ? 0 : 1);
        Light(g, (float)y);
        lamp.Visible = pose != "dead" || g > 0.01;
    }

    /// <summary>A cinematic's frame: the eyes and the lamp at the glow it sets,
    /// wherever the cinematic has put the body.</summary>
    public void Shine(double dt)
    {
        time += dt;
        Visible = true;
        Light(Glow, view.GlobalPosition.Y);
        lamp.Visible = LampLit;
    }

    void Light(double g, float ground)
    {
        foreach (var m in eyes) m.EmissionEnergyMultiplier = (float)(g <= 0.001 ? 0 : 1.2 + g * 2.4 + Math.Sin(time * 5) * g * 0.5);
        // The light is the lamp in his fist, hung a little out from the body.
        double i = LampLit ? g * (5 + Math.Sin(time * 3.1) * 0.8 + (pose == "channel" ? 4 + Math.Sin(time * 14) * 2 : 0)) : 0;
        light.LightEnergy = (float)(i / Math.PI);
        var at = lamp.GlobalPosition;
        light.GlobalPosition = new Vector3(at.X, Mathf.Max(at.Y, ground + 1.2f) + 0.8f, at.Z);
    }
'''
assert old in s, "update"
s = s.replace(old, new)
open(p, "w", encoding="utf-8", newline="").write(s)
print("ok")

import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a3058a45eee41d695\godot"


def edit(rel, pairs):
    p = os.path.join(G, rel)
    s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        assert s.count(old) == 1, (rel, s.count(old), old[:70])
        s = s.replace(old, new, 1)
    open(p, "w", encoding="utf-8", newline="").write(s)


edit(r"src\Actors\BossViews.cs", [
('''    readonly Node3D lamp;''', '''    readonly Node3D lamp, flame;'''),
('''        var iron = new StandardMaterial3D { AlbedoColor = new Color("#2a2622"), Metallic = 0.6f, Roughness = 0.5f };
        lamp.AddChild(new MeshInstance3D { Mesh = new BoxMesh { Size = new Vector3(0.12f, 0.16f, 0.12f), Material = iron }, Position = new Vector3(0, -0.14f, 0) });
        lamp.AddChild(new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = 0.045f, Height = 0.1f, Material = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(1.4f, 2.4f, 3.2f) } },
            Position = new Vector3(0, -0.14f, 0), CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        });''',
'''        // A lamp-iron, new black iron in the old fist: an open cage, so the flame shows.
        var iron = new StandardMaterial3D { AlbedoColor = new Color("#1e1c1a"), Metallic = 0.7f, Roughness = 0.38f };
        void Iron(Mesh m, Vector3 at) { m.SurfaceSetMaterial(0, iron); lamp.AddChild(new MeshInstance3D { Mesh = m, Position = at }); }
        Iron(new BoxMesh { Size = new Vector3(0.13f, 0.018f, 0.13f) }, new Vector3(0, -0.06f, 0));
        Iron(new BoxMesh { Size = new Vector3(0.13f, 0.02f, 0.13f) }, new Vector3(0, -0.22f, 0));
        Iron(new CylinderMesh { TopRadius = 0.02f, BottomRadius = 0.06f, Height = 0.045f, RadialSegments = 4 }, new Vector3(0, -0.03f, 0));
        foreach (var (x, z) in new[] { (-1, -1), (-1, 1), (1, -1), (1, 1) })
            Iron(new BoxMesh { Size = new Vector3(0.012f, 0.16f, 0.012f) }, new Vector3(x * 0.058f, -0.14f, z * 0.058f));
        Iron(new TorusMesh { InnerRadius = 0.022f, OuterRadius = 0.032f, Rings = 12, RingSegments = 6 }, new Vector3(0, 0.0f, 0));
        flame = new Node3D { Position = new Vector3(0, -0.15f, 0) };
        lamp.AddChild(flame);
        flame.AddChild(new MeshInstance3D
        {
            Mesh = new SphereMesh { Radius = 0.026f, Height = 0.075f, Material = new StandardMaterial3D { ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, AlbedoColor = new Color(1.4f, 2.4f, 3.2f) } },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
        });
        flame.AddChild(new MeshInstance3D
        {
            Mesh = new QuadMesh { Size = Vector2.One * 0.3f },
            CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
            MaterialOverride = new StandardMaterial3D
            {
                ShadingMode = BaseMaterial3D.ShadingModeEnum.Unshaded, Transparency = BaseMaterial3D.TransparencyEnum.Alpha,
                BlendMode = BaseMaterial3D.BlendModeEnum.Add, BillboardMode = BaseMaterial3D.BillboardModeEnum.Enabled,
                AlbedoTexture = new GradientTexture2D
                {
                    Gradient = new Gradient { Colors = [new Color(1, 1, 1, 1), new Color(1, 1, 1, 0.15f), new Color(1, 1, 1, 0)], Offsets = [0, 0.25f, 1] },
                    Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f), Width = 64, Height = 64,
                },
                AlbedoColor = new Color(0.55f, 0.8f, 1f, 0.6f),
            },
        });'''),
('''        Light(g, (float)y);
        lamp.Visible = pose != "dead" || g > 0.01;
    }''',
'''        Light(g, (float)y);
        lamp.Visible = pose != "dead" || g > 0.01;
        flame.Visible = LampLit && g > 0.01;
    }'''),
('''        Light(Glow, view.GlobalPosition.Y);
        lamp.Visible = LampLit;
    }''',
'''        Light(Glow, view.GlobalPosition.Y);
        lamp.Visible = true;
        flame.Visible = LampLit && Glow > 0.01;
    }'''),
])
print("ok")

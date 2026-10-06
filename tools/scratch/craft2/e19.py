from ed import sub
sub('src/Ui/Forge.cs', [
("""            ScaleAmountMin = 2.6f, ScaleAmountMax = 5.6f, ColorRamp = ramp, Position = local, ZIndex = 30,
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
        };""",
"""            ScaleAmountMin = 0.55f, ScaleAmountMax = 1.15f, ColorRamp = ramp, Position = local, ZIndex = 30,
            Material = new CanvasItemMaterial { BlendMode = CanvasItemMaterial.BlendModeEnum.Add },
            // Streaks, not squares: a soft spindle of light along the way each spark flies.
            Texture = Spark, ParticleFlagAlignY = true,
        };"""),
("""    /// <summary>A burst of sparks off the anvil at a point in a control (embers for a coal).</summary>""",
"""    static GradientTexture2D? spark;
    static GradientTexture2D Spark => spark ??= new GradientTexture2D
    {
        Width = 10, Height = 30, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(0.5f, 0f),
        Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.55f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.35f, 1f } },
    };

    /// <summary>A burst of sparks off the anvil at a point in a control (embers for a coal).</summary>"""),
])

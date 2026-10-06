PAIRS = [
("""                var s = chevron.GetSize() * (1.05f + 0.08f * Mathf.Sin(t * 3.2f));
                DrawCircle(p, 30, m.Color with { A = 0.16f * breath });""",
"""                var s = chevron.GetSize() * (1.4f + 0.1f * Mathf.Sin(t * 3.2f));
                // (a soft light, never a disc with an edge)
                soft ??= new GradientTexture2D
                {
                    Width = 64, Height = 64, Fill = GradientTexture2D.FillEnum.Radial, FillFrom = new Vector2(0.5f, 0.5f), FillTo = new Vector2(1, 0.5f),
                    Gradient = new Gradient { Colors = new[] { Colors.White, Colors.White with { A = 0.3f }, Colors.White with { A = 0 } }, Offsets = new[] { 0f, 0.45f, 1f } },
                };
                DrawTextureRect(soft, new Rect2(p - new Vector2(46, 46), new Vector2(92, 92)), false, m.Color with { A = 0.4f * breath });"""),
("""    public EdgeMarks() { MouseFilter = MouseFilterEnum.Ignore; }""",
"""    public EdgeMarks() { MouseFilter = MouseFilterEnum.Ignore; }

    static GradientTexture2D? soft;"""),
]

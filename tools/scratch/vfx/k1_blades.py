from ed import edit
edit(r"src\Fx\Blades.cs", [
("""        public float Span, Sweep, Drain, Age, Depth, Seed;
        public Color Hue;""",
"""        public float Span, Sweep, Drain, Age, Depth, Seed, Tail, White;
        public Color Hue;"""),
("""    /// its colour (linear, bright), `depth` how deep its smear reaches in
    /// from the edge as a share of the reach.</summary>
    public void Add(Vector3 centre, float facing, float reach, float span, bool mirror, float sweep, float drain, Color hue, float depth, float delay = 0)
    {""",
"""    /// its colour (linear, bright), `depth` how deep its smear reaches in
    /// from the edge as a share of the reach. `tail` is how much of the swing
    /// its smear trails behind the blade (a share of the span), and `white` how
    /// near white its cutting edge burns (0 its own hue, 1 white).</summary>
    public void Add(Vector3 centre, float facing, float reach, float span, bool mirror, float sweep, float drain, Color hue, float depth, float delay = 0,
        float tail = 0.75f, float white = 0.75f)
    {"""),
("""            Age = -delay, Depth = Mathf.Clamp(depth, 0.05f, 0.62f), Hue = hue, Seed = 1 + rng.Next(900),
        });""",
"""            Age = -delay, Depth = Mathf.Clamp(depth, 0.05f, 0.62f), Hue = hue, Seed = 1 + rng.Next(900),
            Tail = Mathf.Clamp(tail, 0.08f, 0.95f), White = Mathf.Clamp(white, 0, 1),
        });"""),
("""            const float Tail = 0.75f;
            float back = Mathf.Max(0, head - Tail);
            if (s.Age > s.Sweep)
            {
                float d = (s.Age - s.Sweep) / s.Drain;
                back = Mathf.Lerp(1 - Tail, 1, 1 - (1 - d) * (1 - d));
            }""",
"""            float back = Mathf.Max(0, head - s.Tail);
            if (s.Age > s.Sweep)
            {
                float d = (s.Age - s.Sweep) / s.Drain;
                back = Mathf.Lerp(1 - s.Tail, 1, 1 - (1 - d) * (1 - d));
            }"""),
("""            buffer[o + 16] = head; buffer[o + 17] = back; buffer[o + 18] = s.Span; buffer[o + 19] = s.Seed + Mathf.Clamp(left, 0.001f, 0.999f);""",
"""            // The edge's heat rides in the seed's thousands (a level of five), as the custom data is full.
            float heat = 1000 * (1 + Mathf.Round(s.White * 4));
            buffer[o + 16] = head; buffer[o + 17] = back; buffer[o + 18] = s.Span; buffer[o + 19] = heat + s.Seed + Mathf.Clamp(left, 0.001f, 0.999f);"""),
])
edit(r"shaders\blade.gdshader", [
("""// INSTANCE_CUSTOM is (head, back,
// span in radians, seed + what is left): the blade's place along the swing
// (0 the start, 1 the end), where its smear ends behind it, the angle it
// sweeps, and a seed whose fraction is how much of it is left.""",
"""// INSTANCE_CUSTOM is (head, back,
// span in radians, heat + seed + what is left): the blade's place along the swing
// (0 the start, 1 the end), where its smear ends behind it, the angle it
// sweeps, and in the last its edge's heat in thousands (1 to 5: its own hue to
// white), a seed under a thousand, and in its fraction how much of it is left."""),
("""	float seed = floor(v_custom.w), left = fract(v_custom.w);""",
"""	float packed = floor(v_custom.w), left = fract(v_custom.w);
	float level = floor(packed / 1000.0);
	float seed = packed - level * 1000.0;
	float white = clamp((level - 1.0) / 4.0, 0.0, 1.0);"""),
("""	vec3 hot = mix(hue, vec3(1.0), 0.75) * 2.4;""",
"""	vec3 hot = mix(hue, vec3(1.0), white) * 2.4;"""),
])

from ed import edit
edit(r"shaders\ribbon.gdshader", [
    ("""		// Frost: a pale core and glittering points that wink.
		vec2 cellp = vec2(along * 40.0, UV.y * 4.0);
		float h = hash(floor(cellp));
		float glint = step(0.86, h) * (0.5 + 0.5 * sin(TIME * 18.0 + h * 40.0)) * body;""",
     """		// Frost: a pale core and glittering points that wink. (Each glint a soft point in its cell:
		// lit whole, the cells read as pale squares on a wide ribbon.)
		vec2 cellp = vec2(along * 40.0, UV.y * 4.0);
		float h = hash(floor(cellp));
		vec2 f = fract(cellp) - 0.5;
		float point = exp(-dot(f, f) * 28.0);
		float glint = step(0.86, h) * point * (0.5 + 0.5 * sin(TIME * 18.0 + h * 40.0)) * body;"""),
])
edit(r"src\Fx\BattleFx.Skills.cs", [
    ("""if (ice) Ribbons.Feed(key ^ 0x55aa, at + Vector3.Up * 0.05f, 0.3f * s, 0.32f, Hdr("#3d8cff", 1f), 1.6f, Ribbons.Style.Frost);""",
     """if (ice) Ribbons.Feed(key ^ 0x55aa, at + Vector3.Up * 0.05f, 0.2f * s, 0.3f, Hdr("#3d8cff", 1f), 1.6f, Ribbons.Style.Frost);"""),
])

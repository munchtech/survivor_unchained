from ed import edit
edit(r"shaders\loot_beam.gdshader", [
    ("""			+ deep * pool(w * 0.55) * 0.4;
		veil = (g(x, w * 0.14) * 0.25 + g(x, w * 0.4) * 0.08) * fade;""",
     """			+ deep * pool(w * 0.55) * 0.4;
		// A little of the ground under its pool covered, so by night it lies warm and not pink.
		veil = (g(x, w * 0.14) * 0.25 + g(x, w * 0.4) * 0.08) * fade + pool(w * 0.55) * 0.12;"""),
])
edit(r"src\Fx\BattleFx.cs", [
    ("""                    Flash(at + Vector3.Up * 3, new Color("#ffb060"), 30, 1.6f, 24);""",
     """                    Flash(at + Vector3.Up * 3, new Color("#ff9a40"), 30, 1.6f, 24);"""),
])

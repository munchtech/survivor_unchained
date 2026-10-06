import re
W = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot"
# Shader: a seventh kind, a shaft of light of a given height (a strike from the sky, a level, an
# evolution, a chest, the night won).
p = W + r"\shaders\loot_beam.gdshader"
s = open(p, encoding="utf-8").read()
a = """	} else {
		// A plain short glow."""
b = """	} else if (kind > 6.5) {
		// A shaft: light down from the sky or up out of the ground for a moment, a hot core in a
		// glow scaled to its width, brightest at its foot.
		float w = half_w;
		float fade = rise * pow(1.0 - u, 0.9);
		light = (tint * g(x, w * 0.09) * 1.2 + mix(tint, deep, 0.5) * g(x, w * 0.28) * 0.5 + deep * g(x, w * 0.7) * 0.14) * fade
			+ deep * pool(w * 0.55) * 0.4;
		veil = (g(x, w * 0.14) * 0.25 + g(x, w * 0.4) * 0.08) * fade;
	} else {
		// A plain short glow."""
assert a in s
s = s.replace(a, b)
s = s.replace("//   6 Glow: a plain short light (Chart, Quest, the hoard stone).",
              "//   6 Glow: a plain short light (Chart, Quest, the hoard stone).\n//   7 Shaft: a moment's column of light (BattleFx.Pillar: a strike, a level, an evolution, a chest,\n//     the night won), its height given.")
open(p, "w", encoding="utf-8", newline="\n").write(s)

p = W + r"\src\Fx\BattleFx.Loot.cs"
s = open(p, encoding="utf-8").read()
reps = [
    ("    enum Lit { Rare = 1, Epic = 2, Set = 3, Pillar = 4, Strike = 5, Glow = 6 }",
     """    enum Lit { Rare = 1, Epic = 2, Set = 3, Pillar = 4, Strike = 5, Glow = 6, Shaft = 7 }

    // A moment's columns of light (Pillar): where, how tall and wide, in what colour, since when, how long.
    readonly List<(Vector3 At, float Height, float Width, Color Colour, double Born, float Life)> shafts = new();

    /// <summary>A column of light from the ground for a moment (a strike from the sky, a level gained,
    /// an evolution, a chest, the night won), drawn as loot's light is: upright on the screen, soft,
    /// held below the tone curve's knee. (On a world-upright tube, the night's 34 m column and its
    /// white core read as a huge slanted cream bar.) `radius` is its core's reach; its glow spreads
    /// four times wider.</summary>
    void Pillar(Vector3 at, float height, float radius, Color color, float life)
    {
        // Its hue kept, its brightness held to the knee.
        float top = Mathf.Max(color.R, Mathf.Max(color.G, color.B));
        var c = top > 1.1f ? new Color(color.R / top * 1.1f, color.G / top * 1.1f, color.B / top * 1.1f) : color;
        shafts.Add((at, height, Mathf.Max(0.5f, radius * 4), c, time, Mathf.Max(0.05f, life)));
    }"""),
    ("""    void EndLoot()
    {
        lootLight!.End();""",
     """    void EndLoot()
    {
        for (int i = shafts.Count - 1; i >= 0; i--)
        {
            var s = shafts[i];
            float k = (float)((time - s.Born) / s.Life);
            if (k >= 1 || k < 0) { shafts.RemoveAt(i); continue; }
            // Up fast out of the ground, then thinning away.
            float grow = Mathf.SmoothStep(0, 0.12f, k), fade = (1 - k) * (1 - k);
            Light(s.At.X, s.At.Y - 0.04f, s.At.Z, Lit.Shaft, 0, s.Width * (0.8f + 0.2f * grow), s.Height * (0.4f + 0.6f * grow), s.Colour, fade);
        }
        lootLight!.End();"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)

p = W + r"\src\Fx\BattleFx.cs"
s = open(p, encoding="utf-8").read()
start = s.index("    /// <summary>A column of light from the ground (a strike from the sky, a level gained).</summary>\n    void Pillar(")
end = s.index("    /// <summary>A band of light between two points")
s = s[:start] + s[end:]
reps = [
    ("""                    Pillar(at, 34, 1.1f, gold * 0.8f, 1.6f);
                    Pillar(at, 22, 0.35f, new Color(3, 2.8f, 2.4f), 0.9f);""",
     """                    // (One column, gold: its white core read as a cream bar.)
                    Pillar(at, 34, 1.1f, gold, 1.6f);"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")

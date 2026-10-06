p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot\src\Fx\BattleFx.Skills.cs"
s = open(p, encoding="utf-8").read()
rep = [
    ('''                // A cut across the body in the wind's colour (its blood for Razorgale).
                Sparks.Spawn(at, Vector3.Zero, 0.15f, 0.75f * g, art == "chakram_razor" ? Blood : art == "chakram_hail" ? Hdr("#bfe6ff", 1.8f) : Hdr("#e6fff2", 1.7f), null, 0.9f * g, sprite: Sprites.Of("scratch"), spinV: 0);''',
     '''                // A cut across the body in the wind's colour (its blood for Razorgale). Held low: a
                // ring of bodies cut at once at her feet summed to a pale glow at her hips.
                Sparks.Spawn(at, Vector3.Zero, 0.13f, 0.6f * g, art == "chakram_razor" ? Blood * 0.7f : art == "chakram_hail" ? Hdr("#9fd8ff", 1.15f) : Hdr("#a8f0d0", 1.1f), null, 0.75f * g, sprite: Sprites.Of("scratch"), spinV: 0);'''),
    ('''                // Gale Chakram rides the wind: a curl of air behind it.
                Ribbons.Feed(key, at, 0.5f * s, 0.16f, new Color(gust.R * 0.6f, gust.G * 0.6f, gust.B * 0.6f), razor ? 1.2f : 1f,''',
     '''                // Gale Chakram rides the wind: a thin curl of air behind it (broad and pale, it read as
                // a lance through the blade).
                Ribbons.Feed(key, at - fwd * 0.3f * s, 0.26f * s, 0.14f, new Color(gust.R * 0.45f, gust.G * 0.45f, gust.B * 0.45f), razor ? 0.9f : 0.75f,'''),
]
for a, b in rep:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")

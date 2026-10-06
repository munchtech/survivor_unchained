import io
WT = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad059388f00c19f9f\godot"
def edit(rel, pairs):
    p = WT + "\\" + rel
    s = io.open(p, encoding="utf-8", newline="").read()
    for a, b in pairs:
        assert s.count(a) == 1, (rel, a)
        s = s.replace(a, b)
    io.open(p, "w", encoding="utf-8", newline="").write(s)
edit(r"src\Fx\BattleFx.Loot.cs", [
    ("lootLamps[i] = new OmniLight3D { LightEnergy = 0, OmniRange = 7, OmniAttenuation = 1.4f, ShadowEnabled = false, Visible = false };",
     "// Low and short: at 1.4 m up with a 7 m reach, by night it warmed the ground 300 px across,\n"
     "            // lighting the clearing; this marks the spot and what stands on it (about 180 px).\n"
     "            lootLamps[i] = new OmniLight3D { LightEnergy = 0, OmniRange = 2.8f, OmniAttenuation = 1.4f, ShadowEnabled = false, Visible = false };"),
    ("var at = V(p.X, gy + 1.4, p.Z);", "var at = V(p.X, gy + 1.0, p.Z);"),
    ("lamp.LightEnergy = 1.5f * flicker", "lamp.LightEnergy = 1.1f * flicker"),
])
edit(r"shaders\loot_beam.gdshader", [
    ("+ amber * hearth * 0.5 + deep * pool(half_w * 0.75) * 0.5;", "+ amber * hearth * 0.5 + deep * pool(half_w * 0.52) * 0.5;"),
    ("* fade + pool(half_w * 0.75) * 0.14;", "* fade + pool(half_w * 0.52) * 0.14;"),
])
print("ok")

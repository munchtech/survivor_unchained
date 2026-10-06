G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-abc6bbe020c7fe287\godot"
p = G + r"\src\Fx\BattleFx.cs"
s = open(p, encoding="utf-8").read()
pairs = [
    (", kegs = null!, lootBeams = null!;", ", kegs = null!;"),
    ('''        lootBeams = Add(new Batch(new CylinderMesh { TopRadius = 0.12f, BottomRadius = 0.18f, Height = 1, RadialSegments = 10, CapTop = false, CapBottom = false }, 200, beam));
''', ""),
    ('''        var beam = new ShaderMaterial { Shader = beamShader };
        beam.SetShaderParameter("energy", 1.6f);
''', ""),
    ('''                case Ev.Spawn e:
                {''', '''                case Ev.Drop d:
                    Dropped(d);
                    break;
                case Ev.Spawn e:
                {'''),
]
for a, b in pairs:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8").write(s)
print("ok")

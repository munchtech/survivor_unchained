W = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a09c5a65f5a84319e\godot'

def edit(path, pairs):
    p = W + '\\' + path
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, s.count(a), a[:80])
        s = s.replace(a, b, 1)
    open(p, 'w', encoding='utf-8').write(s)

edit(r'src\Fx\BattleFx.cs', [
('''                float r = Mathf.Sqrt(u * u + v * v), a = 0;
                if (r >= inner && r <= outer)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - (r - inner) / 0.035f, 0, 1), Mathf.Clamp(1 - (outer - r) / 0.035f, 0, 1));
                    a = 0.3f + 0.7f * edge;
                }''',
'''                float r = Mathf.Sqrt(u * u + v * v), a = 0;
                // Its edges eased over a texel and a half, or a band ten paces across shows steps.
                float inside = Mathf.Clamp((r - inner) / 0.016f + 0.5f, 0, 1) * Mathf.Clamp((outer - r) / 0.016f + 0.5f, 0, 1);
                if (inside > 0)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - Mathf.Abs(r - inner) / 0.035f, 0, 1), Mathf.Clamp(1 - Mathf.Abs(outer - r) / 0.035f, 0, 1));
                    a = (0.3f + 0.7f * edge) * inside;
                }'''),
('''                float r = Mathf.Sqrt(u * u + v * v), ang = Mathf.Abs(Mathf.Atan2(u, v));
                float a = 0;
                if (r < 0.97f && ang <= half)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.07f, 0, 1), Mathf.Clamp(1 - (half - ang) * r / 0.05f, 0, 1));
                    a = 0.18f + 0.82f * edge;
                }''',
'''                float r = Mathf.Sqrt(u * u + v * v), ang = Mathf.Abs(Mathf.Atan2(u, v));
                float a = 0;
                // Eased at its sides and its rim, so a wide cone has no steps along them.
                float inside = Mathf.Clamp((half - ang) * r / 0.016f + 0.5f, 0, 1) * Mathf.Clamp((0.97f - r) / 0.016f + 0.5f, 0, 1);
                if (inside > 0)
                {
                    float edge = Mathf.Max(Mathf.Clamp(1 - Mathf.Abs(r - 0.9f) / 0.07f, 0, 1), Mathf.Clamp(1 - Mathf.Abs(half - ang) * r / 0.05f, 0, 1));
                    a = (0.18f + 0.82f * edge) * inside;
                }'''),
])
print("ok")

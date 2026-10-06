import os
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
def rep(path, pairs):
    p = os.path.join(G, path)
    s = open(p, encoding='utf-8').read()
    for a, b in pairs:
        assert a in s, (path, a[:70])
        s = s.replace(a, b)
    open(p, 'w', encoding='utf-8').write(s)
rep('shaders/arena_ground.gdshader', [
('		vec2 ca = w * 7.5, cb = w * 2.6;', '		vec2 ca = w * 3.6, cb = w * 1.3;'),
('''		mc *= 0.3 + 0.8 * dome;''',
'''		// Velvet, not bubbles: the domes shade the cushion gently, and a fine fibre runs
		// through it (from thirty metres up, strong round highlights read as bubble wrap).
		float fib = texture(noise_tex, w * 3.3 + 0.17).g * 0.6 + texture(noise_tex, w * 8.1 + 0.53).b * 0.4;
		mc *= (0.55 + 0.55 * smoothstep(0.15, 0.95, dome)) * (0.72 + 0.56 * fib);'''),
('''		n = normalize(mix(n, normalize(n_geo - vec3(ra.x + rb.x * 0.6, 0.0, ra.y + rb.y * 0.6) * 0.9), mo * 0.85));''',
'''		n = normalize(mix(n, normalize(n_geo - vec3(ra.x + rb.x * 0.6, 0.0, ra.y + rb.y * 0.6) * 0.5), mo * 0.5));'''),
])
rep('src/World/ArenaGround.cs', [
('new(0.11f, 1.0f, Con: 1.4f, Lift: 0.02f, Size: 1.7f)', 'new(0.11f, 1.0f, Con: 1.3f, Lift: 0.02f, Size: 1.9f)'),
])
print('ok')

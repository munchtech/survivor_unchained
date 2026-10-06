import os, sys
G = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a26767f7f9955cb56\godot"
p = os.path.join(G, 'shaders/arena_ground.gdshader')
s = open(p, encoding='utf-8').read()
a = '''		// Coals strewn outward, going out the further they lie.'''
b = '''		if (ember_dbg == 6) glow += vec3(step(pl.x, 0.0) * 2.0, clamp(px * 40.0, 0.0, 1.0) * 2.0, clamp(pl.x, 0.0, 1.0) * 2.0);
		// Coals strewn outward, going out the further they lie.'''
assert a in s
s = s.replace(a, b)
open(p, 'w', encoding='utf-8').write(s)
print('ok')

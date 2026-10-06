p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\shaders\fire_wall.gdshader"
s = open(p, encoding="utf-8").read()
reps = [
    ("uniform vec3 hot = vec3(1.0, 0.6, 0.14);\nuniform vec3 mid = vec3(0.86, 0.25, 0.03);\nuniform vec3 deep = vec3(0.34, 0.035, 0.0);",
     "uniform vec3 hot = vec3(0.95, 0.5, 0.1);\nuniform vec3 mid = vec3(0.74, 0.19, 0.022);\nuniform vec3 deep = vec3(0.3, 0.028, 0.0);"),
    ("""	float flick = 0.7 + 0.5 * fbm(vec2(xs * 3.4, u * 3.0 - t * 5.0), cells * 3.4);
	float heat = f * flick;
	vec3 col = mix(deep, mid, smoothstep(0.1, 0.5, heat));
	col = mix(col, hot, smoothstep(0.6, 1.05, heat));""",
     """	// The tall tongues burn hottest at their hearts; the low ones and the edges deep red.
	float flick = 0.65 + 0.55 * fbm(vec2(xs * 3.4, u * 3.0 - t * 5.0), cells * 3.4);
	float heat = f * mix(0.45, 1.1, pow(ridge, 1.5)) * flick;
	vec3 col = mix(deep, mid, smoothstep(0.12, 0.5, heat));
	col = mix(col, hot, smoothstep(0.58, 1.0, heat));"""),
    ("""	ALBEDO = col * a * flick * fade * clear;
	ALPHA = a * 0.42 * fade * clear;""",
     """	// Enough of what is behind is covered that flame seen along the ring, card behind card, comes
	// to its own colour and stops there, never past the knee to cream.
	ALBEDO = col * a * fade * clear;
	ALPHA = a * 0.62 * fade * clear;"""),
]
for a, b in reps:
    assert a in s, a[:70]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")

p = r"C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a191ed81e2df462cf\godot\shaders\fire_wall.gdshader"
s = open(p, encoding="utf-8").read()
reps = [
    ("uniform vec3 hot = vec3(0.95, 0.5, 0.1);\nuniform vec3 mid = vec3(0.74, 0.19, 0.022);\nuniform vec3 deep = vec3(0.3, 0.028, 0.0);",
     "// (Measured: at 0.95, 0.5, 0.1 a wide wall came out (236, 155, 88), apricot. Deeper and redder\n// still, so its body reads orange and only its hearts yellow.)\nuniform vec3 hot = vec3(0.78, 0.33, 0.05);\nuniform vec3 mid = vec3(0.5, 0.1, 0.01);\nuniform vec3 deep = vec3(0.17, 0.012, 0.0);"),
    ("""	vec3 col = mix(deep, mid, smoothstep(0.12, 0.5, heat));
	col = mix(col, hot, smoothstep(0.58, 1.0, heat));""",
     """	vec3 col = mix(deep, mid, smoothstep(0.12, 0.55, heat));
	col = mix(col, hot, smoothstep(0.7, 1.1, heat));"""),
]
for a, b in reps:
    assert a in s, a[:60]
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ok")

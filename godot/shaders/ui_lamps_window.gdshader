// The Lamps page's own backdrop in the book's panel (C; docs/design/LAMPS_SCREEN_BRIEF.md §13, Lamps fix round 1):
// the world behind, read at half resolution and blurred about 10 px at 1080 (the screen's mips 2-3, through a cubic
// B-spline so the low mip comes back smooth), then the panel's own ground laid over it at 88%, so no townsfolk read
// through the board. Its edges feather into the panel over `feather` px: no inner frame (the panel's ground is the
// board's ground).
shader_type canvas_item;

uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
uniform vec3 ground : source_color = vec3(0.110, 0.090, 0.094);
uniform float keep = 0.88;
uniform float lod = 2.5;
uniform vec2 size = vec2(852.0, 846.0);
uniform float feather = 40.0;

vec4 cubic(float v) {
	vec4 n = vec4(1.0, 2.0, 3.0, 4.0) - v;
	vec4 s = n * n * n;
	float x = s.x;
	float y = s.y - 4.0 * s.x;
	float z = s.z - 4.0 * s.y + 6.0 * s.x;
	float w = 6.0 - x - y - z;
	return vec4(x, y, z, w) * (1.0 / 6.0);
}

vec3 smooth_lod(vec2 uv, float l) {
	vec2 sz = vec2(textureSize(screen, int(l)));
	vec2 inv = 1.0 / sz;
	vec2 t = uv * sz - 0.5;
	vec2 f = fract(t);
	t -= f;
	vec4 xc = cubic(f.x);
	vec4 yc = cubic(f.y);
	vec4 c = t.xxyy + vec2(-0.5, 1.5).xyxy;
	vec4 s = vec4(xc.xz + xc.yw, yc.xz + yc.yw);
	vec4 o = (c + vec4(xc.yw, yc.yw) / s) * inv.xxyy;
	vec3 s0 = textureLod(screen, o.xz, l).rgb;
	vec3 s1 = textureLod(screen, o.yz, l).rgb;
	vec3 s2 = textureLod(screen, o.xw, l).rgb;
	vec3 s3 = textureLod(screen, o.yw, l).rgb;
	float sx = s.x / (s.x + s.y);
	float sy = s.z / (s.z + s.w);
	return mix(mix(s3, s2, sx), mix(s1, s0, sx), sy);
}

void fragment() {
	float l0 = floor(lod);
	vec3 w = mix(smooth_lod(SCREEN_UV, l0), smooth_lod(SCREEN_UV, l0 + 1.0), fract(lod));
	vec2 p = UV * size;
	float e = min(min(p.x, size.x - p.x), min(p.y, size.y - p.y));
	COLOR = vec4(mix(w, ground, keep), smoothstep(0.0, feather, e));
}

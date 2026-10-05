// Behind a full page or a side panel (Ui/Ornate.cs, Backdrop): the world as
// it is, out of focus as a lens would put it, darkened and graded into the
// house's night (cool iron in the shadows, the lamps' warmth kept in what is
// lit), so the page sits in the place the survivor stands rather than on
// flat black. Its mipmaps give the blur, read through a cubic B-spline so
// the low mips come back smooth instead of blocky (a plain bilinear read of a
// small mip is what made the old backdrop look low in definition).
shader_type canvas_item;

uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
uniform float blur = 3.0;
uniform float dim = 0.5;
uniform vec3 tint : source_color = vec3(0.95, 0.8, 0.66);
uniform vec3 shade : source_color = vec3(0.42, 0.42, 0.58);
uniform float grey = 0.55;

vec4 cubic(float v) {
	vec4 n = vec4(1.0, 2.0, 3.0, 4.0) - v;
	vec4 s = n * n * n;
	float x = s.x;
	float y = s.y - 4.0 * s.x;
	float z = s.z - 4.0 * s.y + 6.0 * s.x;
	float w = 6.0 - x - y - z;
	return vec4(x, y, z, w) * (1.0 / 6.0);
}

vec3 smooth_lod(vec2 uv, float lod) {
	vec2 size = vec2(textureSize(screen, int(lod)));
	vec2 inv = 1.0 / size;
	vec2 t = uv * size - 0.5;
	vec2 f = fract(t);
	t -= f;
	vec4 xc = cubic(f.x);
	vec4 yc = cubic(f.y);
	vec4 c = t.xxyy + vec2(-0.5, 1.5).xyxy;
	vec4 s = vec4(xc.xz + xc.yw, yc.xz + yc.yw);
	vec4 o = (c + vec4(xc.yw, yc.yw) / s) * inv.xxyy;
	vec3 s0 = textureLod(screen, o.xz, lod).rgb;
	vec3 s1 = textureLod(screen, o.yz, lod).rgb;
	vec3 s2 = textureLod(screen, o.xw, lod).rgb;
	vec3 s3 = textureLod(screen, o.yw, lod).rgb;
	float sx = s.x / (s.x + s.y);
	float sy = s.z / (s.z + s.w);
	return mix(mix(s3, s2, sx), mix(s1, s0, sx), sy);
}

void fragment() {
	// Two levels of the blur laid together: the near one keeps the shapes, the far one the
	// glow round the lights, as a lens's out-of-focus world has both.
	float l0 = floor(blur);
	vec3 c = mix(smooth_lod(SCREEN_UV, l0), smooth_lod(SCREEN_UV, l0 + 1.0), 0.5 + 0.5 * fract(blur));
	float l = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(l), grey);
	// The grade: shadows into the house's violet-black iron, light kept warm.
	float lit = smoothstep(0.08, 0.7, l);
	c *= mix(shade, tint, lit);
	COLOR = vec4(c * dim, 1.0);
}

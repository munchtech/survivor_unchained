// A dungeon's walls (src/World/DungeonWalls.cs): triplanar painted rock or roots over earth, dark toward the top, with a
// cutaway so a near wall never hides her. COLOR.r says what a vertex is: 0 the wall's face, 0.5 the top beyond it, 1 a root.
shader_type spatial;
render_mode cull_disabled;
#define CEL_INK 1
#include "res://shaders/cel.gdshaderinc"

global uniform vec4 survivor;   // her chest (xyz), w 1 while she is in the world

uniform sampler2DArray sheet : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float layer_a = 1.0;    // den: rot; ravine: face
uniform float layer_b = 2.0;    // den: roots
uniform float ravine = 0.0;
uniform float wall_h = 4.0;
uniform float tile = 5.0;

varying vec3 wpos;
varying vec3 wnrm;
varying float kind;
varying float floor_y;

void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	wnrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	kind = COLOR.r;
	floor_y = UV2.x;
}

float bayer8(ivec2 p) {
	int x = p.x & 7;
	int y = p.y & 7;
	int v = 0;
	for (int i = 2; i >= 0; i--) {
		v = (v << 2) | ((((x >> i) & 1) ^ ((y >> i) & 1)) << 1) | ((y >> i) & 1);
	}
	return (float(v) + 0.5) / 64.0;
}

vec3 tri(float layer, vec3 w) {
	vec3 b = pow(abs(wnrm), vec3(4.0));
	b /= b.x + b.y + b.z;
	return texture(sheet, vec3(wpos.zy / tile, layer)).rgb * b.x
		+ texture(sheet, vec3(wpos.xz / tile, layer)).rgb * b.y
		+ texture(sheet, vec3(wpos.xy / tile, layer)).rgb * b.z;
}

void fragment() {
	// The cutaway: what stands nearer the camera than her, over her chest on screen, is cut away (dithered at its
	// edge), keeping a 0.9 m footing so the wall still stands round her feet.
	if (survivor.w > 0.0 && wpos.y > floor_y + 0.9) {
		vec3 her_v = (VIEW_MATRIX * vec4(survivor.xyz, 1.0)).xyz;
		if (-VERTEX.z < -her_v.z - 0.5) {
			vec4 hp = PROJECTION_MATRIX * vec4(her_v, 1.0);
			vec2 ndc = hp.xy / hp.w;
			vec2 her_px = vec2(ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5) * VIEWPORT_SIZE;
			vec2 d = (FRAGCOORD.xy - her_px) / VIEWPORT_SIZE.y;
			float e = length(d / vec2(0.16, 0.22));
			if (e < 1.0 && (e < 0.75 || bayer8(ivec2(FRAGCOORD.xy)) < (1.0 - e) / 0.25)) discard;
		}
	}
	float h = max(wpos.y - floor_y, 0.0);
	vec3 col;
	if (!FRONT_FACING) {
		// The cut mass inside.
		col = vec3(0.043, 0.035, 0.031);
	} else if (kind > 0.75) {
		// A root: dark warm brown, a lit bevel along its top.
		vec3 t = tri(layer_b, wpos);
		float lum = dot(t, vec3(0.299, 0.587, 0.114));
		col = mix(vec3(0.29, 0.2, 0.15), vec3(0.29, 0.2, 0.15) * lum * 3.0, 0.5);
		col += vec3(0.29, 0.2, 0.15) * 0.9 * smoothstep(0.3, 0.8, wnrm.y);
		col *= mix(1.0, 0.0, smoothstep(0.6 * wall_h, wall_h, h)) * (1.0 - 0.35 * (1.0 - smoothstep(0.0, 0.6, h)));
	} else if (kind > 0.25) {
		// The top beyond: nearly black in the den, the rock darkened in the ravine.
		vec3 t = tri(layer_a, wpos);
		col = ravine > 0.5 ? t * vec3(0.12, 0.11, 0.14) : vec3(0.012, 0.01, 0.009);
	} else {
		vec3 t;
		if (ravine > 0.5) {
			vec3 f = tri(layer_a, wpos);
			float lum = dot(f, vec3(0.299, 0.587, 0.114));
			vec3 tinted = vec3(lum) * vec3(0.478, 0.439, 0.533) * 2.0;
			t = mix(tinted, f, 0.3);
			t += vec3(0.478, 0.439, 0.533) * 0.14 * smoothstep(0.2, 0.7, wnrm.y);
			t *= 1.0 - 0.3 * smoothstep(0.5 * wall_h, wall_h, h);
		} else {
			vec3 rot = tri(layer_a, wpos);
			vec3 roots = tri(layer_b, wpos);
			t = mix(rot, roots, 0.55);
			t *= 1.0 - smoothstep(0.6 * wall_h, wall_h, h);
		}
		col = t * (1.0 - 0.35 * (1.0 - smoothstep(0.0, 0.6, h)));
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
	CEL_FRAGMENT;
}

shader_type spatial;
// (L1 lead 22, R2INK) The hero's INTERIOR ink: the last pass of her line's chain (CelLib.LineChain), drawn on her own visible
// pixels only (depth-tested on her mesh, no depth write), so nothing lands outside her silhouette or on another actor. A
// pixel of hers takes ink where a neighbor within the width (1-2 px) is (a) another material (a step of chromaticity: her
// classes are painted as one hue per class, lit and shade differ in level only), the darker side taking the line; (b) a
// surface of hers well behind it (a limb over her body), the near side taking the line; (c) a fold (deeper than both sides).
// The hull's own pixels (its tone) never count, so the outer line stays as it is. Width: ink_px at 1080p, full up to
// fade.x px per metre, none from fade.y (a close shot draws no ink). Off with the line (cel_hero_line.w = 0).
// (demo-look lead 3, row 1: "she nearly vanishes under the roots ... needs a rim or fill from her carried light") Her RIM:
// in the den (the rig's hero_den, cel_hero_rim), a thin warm lit edge on her own pixels just inside her outer line: a pixel
// of hers within the rim's width (px at 1080p) of her silhouette, where the neighbor is the hull's own px (its tone) or a
// surface well behind her and the ground past the hull lies well behind her too (her outer edge, never a limb over her
// body), takes the rim's tone, as much as that ground is dark (cel_hero_rim2.xy: its cube-root luminance where the rim is
// full / gone, so the open floor gets none) and only where she is darker than the rim (it lightens, never darkens); edges
// facing screen-down (her feet) take cel_hero_rim2.z of it, her carried light being over her. The ink wins over the rim.
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;

global uniform vec4 cel_hero_line;
global uniform vec4 cel_hero_rim;       // rgb: the rim's tone (linear, its level in), w: its width in px at 1080p (0: off)
global uniform vec4 cel_hero_rim2;      // x, y: the ground's cube-root luminance where the rim is full / gone; z: the
                                        // share on edges facing screen-down; w: (debug) 1 paints the found edge magenta
uniform sampler2D depth_tex : hint_depth_texture, filter_nearest;
uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform float ink_px = 1.25;            // width at 1080p, px
uniform vec2 fade = vec2(120.0, 300.0); // px per metre: full ink below x, none from y (the chroma rule's fade, rig values 33-34)
uniform vec2 gap = vec2(0.05, 0.10);       // m: a neighbor this much deeper (past its own slope) starts / is a full depth edge
uniform vec2 chroma = vec2(0.04, 0.09); // chromaticity step that starts / is a full material edge
uniform float touch = 0.02;             // m: a material edge counts only between surfaces this close in depth
uniform vec2 fold = vec2(0.45, 0.9);    // a fold: depth below both sides' mean, in px of the surface (1: a right-angle crease)
uniform float floor_y = -1000.0;        // (set on every line pass; unused here)
uniform int cut_mode = 0;               // hair: as hero_line.gdshader (the strands' cut)
uniform sampler2D cut_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float cut = 0.3;
uniform float cut_bias = 0.0;

varying float v_px;
varying float v_ppm;
varying float v_rim;

void vertex() {
	bool ortho = PROJECTION_MATRIX[3][3] != 0.0;
	vec4 o = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(MODEL_MATRIX[3].xyz, 1.0));
	float ppm = PROJECTION_MATRIX[1][1] * VIEWPORT_SIZE.y * 0.5 / max(ortho ? 1.0 : o.w, 0.0001) * (1080.0 / VIEWPORT_SIZE.y);
	v_ppm = ppm;
	float near = 1.0 - smoothstep(fade.x, fade.y, ppm);
	v_px = cel_hero_line.w > 0.0 ? ink_px * (VIEWPORT_SIZE.y / 1080.0) * near : 0.0;
	v_rim = cel_hero_line.w > 0.0 ? cel_hero_rim.w * (VIEWPORT_SIZE.y / 1080.0) * near : 0.0;
	if (v_px <= 0.01 && v_rim <= 0.01) VERTEX = vec3(0.0);   // (the whole mesh collapses: nothing drawn)
}

float lin_z(sampler2D t, ivec2 q, vec2 inv, mat4 ip) {
	float d = texelFetch(t, q, 0).r;
	vec4 v = ip * vec4((vec2(q) + 0.5) * inv * 2.0 - 1.0, d, 1.0);
	return -v.z / v.w;
}
float lum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
vec3 chrom(vec3 c) { return c / (c.r + c.g + c.b + 1e-5); }

void fragment() {
	if (IN_SHADOW_PASS) discard;
	if (cut_mode > 0) {
		vec4 t = texture(cut_tex, UV, cut_bias);
		float cover = cut_mode == 2 ? (COLOR.b < 0.5 ? 0.0 : max(COLOR.a * COLOR.a, t.a * smoothstep(0.0, 0.8, COLOR.a + (t.g - 0.5) * 0.35)))
			: t.a * smoothstep(0.0, 0.012, UV.y) * COLOR.a;
		if (cover < cut) discard;
	}
	float w = v_px;
	ivec2 sz = textureSize(depth_tex, 0);
	vec2 inv = 1.0 / vec2(sz);
	ivec2 p = ivec2(FRAGCOORD.xy);
	float z0 = -VERTEX.z;
	float px_m = 1.0 / max(v_ppm * VIEWPORT_SIZE.y / 1080.0, 1.0);   // m across one px at her
	vec3 c0 = texelFetch(screen_tex, p, 0).rgb;
	vec3 k0 = chrom(c0); float l0 = lum(c0);
	vec3 ink_c = cel_hero_line.rgb;
	float ink = 0.0;
	for (int i = 0; i < 8; i++) {
		ivec2 o = i == 0 ? ivec2(1, 0) : i == 1 ? ivec2(-1, 0) : i == 2 ? ivec2(0, 1) : i == 3 ? ivec2(0, -1)
			: i == 4 ? ivec2(1, 1) : i == 5 ? ivec2(-1, 1) : i == 6 ? ivec2(1, -1) : ivec2(-1, -1);
		float zb = lin_z(depth_tex, clamp(p - o, ivec2(0), sz - 1), inv, INV_PROJECTION_MATRIX);
		float slope = abs(z0 - zb);
		float kb = length(chrom(texelFetch(screen_tex, clamp(p - o, ivec2(0), sz - 1), 0).rgb) - k0);   // (the step behind: an edge is a step, not a grade)
		for (int k = 1; k <= 2; k++) {
			if (k == 2 && i >= 4) break;
			float cov = i >= 4 ? clamp(w - 0.414, 0.0, 1.0) : clamp(w - float(k - 1), 0.0, 1.0);
			if (cov <= 0.0) continue;
			ivec2 q = clamp(p + o * k, ivec2(0), sz - 1);
			float zn = lin_z(depth_tex, q, inv, INV_PROJECTION_MATRIX);
			vec3 cn = texelFetch(screen_tex, q, 0).rgb;
			float line_n = 1.0 - smoothstep(0.02, 0.06, length(cn - ink_c) / (lum(ink_c) + 0.01) * 0.25);   // (the hull's own px)
			float g = zn - z0;
			float e_depth = k == 1 ? smoothstep(gap.x, gap.y, g - 1.5 * slope) * (1.0 - smoothstep(0.6, 1.0, g)) : 0.0;   // (r2ink_02: one px only, never a blob)
			float side = step(0.04, (lum(cn) - l0) / (lum(cn) + l0 + 1e-4));   // (lead 23: the darker side only, a hard step: both sides of a grade no longer ink)
			float e_class = smoothstep(chroma.x, chroma.y, length(chrom(cn) - k0) - 2.0 * kb) * (1.0 - smoothstep(touch, touch * 2.0, abs(g))) * side;
			float e = max(e_depth, e_class);
			if (k == 1 && i < 4) {
				float cr = (z0 - 0.5 * (zn + zb)) / px_m;
				e = max(e, smoothstep(fold.x, fold.y, cr) * step(abs(g), 0.06) * step(slope, 0.06));
			}
			ink = max(ink, e * cov * (1.0 - line_n));
		}
	}
	// her rim (the den): her outer edge within v_rim px, where the ground past her line is dark
	float rim = 0.0;
	vec3 rim_c = cel_hero_rim.rgb;
	if (v_rim > 0.01 && ink < 0.98 && lum(c0) < lum(rim_c)) {
		int hull = int(ceil(cel_hero_line.w * (VIEWPORT_SIZE.y / 1080.0)));
		for (int i = 0; i < 8; i++) {
			ivec2 o = i == 0 ? ivec2(1, 0) : i == 1 ? ivec2(-1, 0) : i == 2 ? ivec2(0, 1) : i == 3 ? ivec2(0, -1)
				: i == 4 ? ivec2(1, 1) : i == 5 ? ivec2(-1, 1) : i == 6 ? ivec2(1, -1) : ivec2(-1, -1);
			float up = -normalize(vec2(o)).y;   // (FRAGCOORD's y runs down: 1 an edge facing screen-up)
			float side = mix(cel_hero_rim2.z, 1.0, smoothstep(-1.0, 0.0, up));
			for (int k = 1; k <= 2; k++) {
				if (k == 2 && i >= 4) break;
				float cov = i >= 4 ? clamp(v_rim - 0.414, 0.0, 1.0) : clamp(v_rim - float(k - 1), 0.0, 1.0);
				if (cov <= 0.0) continue;
				ivec2 q = clamp(p + o * k, ivec2(0), sz - 1);
				float g = lin_z(depth_tex, q, inv, INV_PROJECTION_MATRIX) - z0;
				vec3 cn = texelFetch(screen_tex, q, 0).rgb;
				float line_n = 1.0 - smoothstep(0.02, 0.06, length(cn - ink_c) / (lum(ink_c) + 0.01) * 0.25);
				float outside = max(line_n, smoothstep(0.08, 0.16, g));
				ivec2 qb = clamp(p + o * (k + hull + 1), ivec2(0), sz - 1);   // (past her line: the ground beside her)
				float far = smoothstep(0.15, 0.3, lin_z(depth_tex, qb, inv, INV_PROJECTION_MATRIX) - z0);
				float lb = pow(max(lum(texelFetch(screen_tex, qb, 0).rgb), 0.0), 1.0 / 3.0);
				float dark = cel_hero_rim2.w > 0.5 ? 1.0 : 1.0 - smoothstep(cel_hero_rim2.x, cel_hero_rim2.y, lb);
				rim = max(rim, outside * far * dark * side * cov);
			}
		}
		rim *= (1.0 - ink) * (1.0 - smoothstep(0.55, 1.0, lum(c0) / max(lum(rim_c), 1e-5)));
		if (cel_hero_rim2.w > 0.5) rim_c = vec3(1.0, 0.0, 1.0);
	}
	float a = ink + rim;
	if (a < 0.02) discard;
	ALBEDO = (ink_c * ink + rim_c * rim) / a;
	ALPHA = a;
}

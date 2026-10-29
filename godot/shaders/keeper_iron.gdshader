// Old black iron out of the river: the Warden's lamp-iron (tools/assets/lamp_iron.py) and his Watch blade
// (tools/assets/watch_blade.py), LampIron.cs. A tiling mask (art/props/keeper_lamp/iron_masks.png: R rust
// blotches, G grain, B pitting height, A vertical water streaks) projected three ways in the model's own
// space, so it stays on the piece however it is scaled; the mesh's vertex colour says where the edges are
// (R: 0.5 flat, toward 1 a sharp outer edge, toward 0 a crease), which part it is (G: 1 the grip's cord)
// and a per-part random (B). Edges worn back to grey steel, rust and silt in the creases and low down,
// pitting as bump, and the whole a little wet.
shader_type spatial;
render_mode blend_mix, cull_back, depth_draw_opaque;

uniform sampler2D masks : filter_linear_mipmap_anisotropic, repeat_enable;
// Repeats of the mask per model unit.
uniform float tile = 9.0;
uniform vec3 iron = vec3(0.042, 0.040, 0.037);
uniform vec3 steel = vec3(0.30, 0.295, 0.285);
uniform vec3 rust = vec3(0.13, 0.055, 0.026);
uniform vec3 silt = vec3(0.075, 0.072, 0.058);
uniform vec3 cord = vec3(0.045, 0.034, 0.026);
uniform float wear = 1.0;
uniform float rust_k = 0.55;
uniform float silt_k = 0.6;
// Model height below which silt gathers (it fades in over silt_fade).
uniform float silt_top = -0.17;
uniform float silt_fade = 0.05;
// The pitting's depth (world metres per unit of height).
uniform float bump = 0.5;
uniform float wet = 0.35;
// Soot inside the lamp's cage (model units: the cage's inner half-width and its top and bottom): matte black where
// the flame's own light falls closest, so the inside never burns white. 0 for anything that isn't the lamp.
uniform float soot_k = 0.0;
uniform vec3 cage = vec3(0.0655, -0.0625, -0.2055);
// The lamp's own flame lighting its iron (LampIron.MakeWarden; the Warden's light leaves the lamp out, so the
// bars a few cm from it never burn white): model units, a soft Gaussian reach, the side facing the flame and the
// worn bevels brightest. 0 for anything that isn't a lit lamp (the sill lamp, the blade).
uniform float inner_k = 0.0;
uniform vec3 inner_col = vec3(0.42, 0.66, 1.0);
uniform vec3 flame_o = vec3(0.0, -0.168, 0.0);
uniform float inner_r = 0.08;

varying vec3 opos;
varying vec3 onrm;

void vertex() {
	opos = VERTEX;
	onrm = NORMAL;
}

vec4 tri(vec3 p, vec3 w) {
	// Each projection's v runs up the model's y where it can, so the streaks run down.
	return texture(masks, p.zy) * w.x + texture(masks, p.xz) * w.y + texture(masks, p.xy) * w.z;
}

void fragment() {
	vec3 w = pow(abs(normalize(onrm)), vec3(4.0));
	w /= (w.x + w.y + w.z);
	vec3 p = opos * tile + COLOR.b * 3.7;
	vec4 m = tri(p, w);
	vec4 m2 = tri(p * 0.31 + 0.5, w);
	float conv = clamp((COLOR.r - 0.5) * 2.0, 0.0, 1.0);
	float cav = clamp((0.5 - COLOR.r) * 2.0, 0.0, 1.0);
	bool is_cord = COLOR.g > 0.75;
	// Worn edges: the convex rim, broken up by grain.
	float edge = smoothstep(0.18, 0.55, conv + (m.g - 0.5) * 0.35) * wear;
	// Rust: big blotches, pulled into creases and along streaks.
	float r = smoothstep(0.58, 0.8, m2.r + cav * 0.3 + m.a * 0.12 + (m.r - 0.5) * 0.25) * rust_k;
	float low = smoothstep(silt_top, silt_top - silt_fade, opos.y);
	float up = clamp(normalize(onrm).y, 0.0, 1.0);
	float s = clamp(low * (0.5 + 0.5 * up) * smoothstep(0.3, 0.7, m2.g + cav * 0.4), 0.0, 1.0) * silt_k;
	vec3 col = iron * (0.8 + 0.45 * m.g) * (0.9 + 0.2 * m.a);
	col = mix(col, steel * (0.75 + 0.5 * m.g), edge * (1.0 - r));
	col = mix(col, rust * (0.7 + 0.6 * m.r), r);
	col = mix(col, silt * (0.8 + 0.4 * m.g), s);
	float metal = mix(0.75, 1.0, edge) * (1.0 - r * 0.85) * (1.0 - s * 0.9);
	float rough = mix(0.5 + 0.18 * (m.g - 0.5) + 0.12 * (1.0 - m.b), 0.3, edge);
	rough = mix(rough, 0.85, r);
	rough = mix(rough, 0.92, s);
	float h = m.b - r * 0.25 * m.r;
	float bk = bump * (1.0 - edge * 0.6);
	if (is_cord) {
		// The grip's cord: dark leather-brown, dull, its own grain.
		col = cord * (0.75 + 0.5 * m.g);
		metal = 0.0;
		rough = 0.78 + 0.1 * m.g;
		h = m.g;
		bk = bump * 0.6;
	}
	float inside = smoothstep(cage.x + 0.002, cage.x - 0.002, max(abs(opos.x), abs(opos.z)))
		* smoothstep(cage.y + 0.002, cage.y - 0.002, opos.y) * smoothstep(cage.z - 0.002, cage.z + 0.002, opos.y) * soot_k;
	col = mix(col, vec3(0.012, 0.011, 0.010) * (0.8 + 0.4 * m.g), inside);
	metal = mix(metal, 0.0, inside);
	rough = mix(rough, 0.95, inside);
	// Wet: darker where it isn't metal, glossier everywhere.
	col *= mix(1.0, 0.72, wet * (1.0 - metal));
	rough = mix(rough, rough * 0.55, wet);
	// Bump from the height's screen derivatives (works for any projection).
	vec3 dpdx = dFdx(VERTEX), dpdy = dFdy(VERTEX);
	float dhx = dFdx(h), dhy = dFdy(h);
	vec3 r1 = cross(dpdy, NORMAL), r2 = cross(NORMAL, dpdx);
	float det = dot(dpdx, r1);
	vec3 grad = sign(det) * (dhx * r1 + dhy * r2);
	NORMAL = normalize(abs(det) * NORMAL - bk * 0.0015 * grad);
	ALBEDO = col;
	if (inner_k > 0.0) {
		vec3 dl = flame_o - opos;
		float dd = length(dl);
		float ndl = dot(normalize(onrm), dl / max(dd, 1e-4));
		float fall = exp(-dd * dd / (inner_r * inner_r));
		float face = 0.06 + smoothstep(-0.1, 0.9, ndl);
		EMISSION = inner_col * inner_k * fall * face * (0.5 + 1.4 * edge) * (1.0 - 0.85 * inside) * (1.0 - 0.6 * r) * (0.75 + 0.5 * m.g);
	}
	METALLIC = metal;
	ROUGHNESS = clamp(rough, 0.05, 1.0);
	SPECULAR = 0.5;
}

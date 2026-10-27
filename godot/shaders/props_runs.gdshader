// (E8 later r2) The gate's masonry (the drums, the gatehouse, the curtains): OwnProps' prop material (the atlas x the
// vertex colours, its normals and ORM, as OrmMaterial3D draws them) plus, on the faces env_props.py flags (vertex
// alpha 0.5: the outer faces), what the vertices are too coarse to carry (blocks 0.4-0.7 m a triangle):
// - grime runs hanging from the crenels and from the corbels' or machicolation's foot, 0.2-0.7 m wide, 1.3-4.5 m long,
//   tapering, uneven, through the courses; 15-25% darker on screen and a little green-brown, so they read in shade
//   (A8 faces a backlit dawn sky: the old vertex runs measured a column-mean std of 6.6 -> 6.7);
// - a damp, mossy band at the foot, 0.5-1.0 m with a ragged top (r3; 0.9-1.5 m in r2).
// Per mesh (OwnProps from props.json "runs"): run_top (m), run_drop (the second row, m below it), run_len (m),
// run_k (strength), run_ring (1: "along the face" is round a drum). Same draws as the shared material.
shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_back, diffuse_burley, specular_schlick_ggx;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D orm_tex : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float normal_scale = 1.0;
// The runs' colour at full (linear multiply: about 20% darker on screen, toward green-brown) and the foot band's.
uniform vec3 run_col = vec3(0.42, 0.44, 0.33);
uniform vec3 moss_col = vec3(0.78, 0.86, 0.60);
uniform float moss_k = 1.0;
instance uniform float run_top = 10.0;
instance uniform float run_drop = 0.0;
instance uniform float run_len = 4.5;
instance uniform float run_k = 0.0;
instance uniform float run_ring = 0.0;

varying vec3 o_pos;
varying vec3 o_nrm;

float h11(float x) { return fract(sin(x * 127.1 + 311.7) * 43758.5453); }
float vn(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = h11(i.x + i.y * 57.0), b = h11(i.x + 1.0 + i.y * 57.0);
	float c = h11(i.x + (i.y + 1.0) * 57.0), d = h11(i.x + 1.0 + (i.y + 1.0) * 57.0);
	return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void vertex() {
	o_pos = VERTEX;
	o_nrm = NORMAL;
}

void fragment() {
	vec3 alb = texture(albedo_tex, UV).rgb * COLOR.rgb;
	vec3 orm = texture(orm_tex, UV).rgb;
	float rough = orm.g;
	if (COLOR.a < 0.75 && run_k > 0.0) {
		// along the face (m): round a drum its arc from the front (+z), so the seam is at the back
		float u = run_ring > 0.5 ? atan(o_pos.x, o_pos.z) * length(o_pos.xz)
			: (abs(o_nrm.z) >= abs(o_nrm.x) ? o_pos.x : o_pos.z);
		float d = run_top - o_pos.y;
		float sd = dot(MODEL_MATRIX[3].xz, vec2(0.37, 0.91));   // each piece its own runs
		const float CW = 0.55;
		float ci = floor(u / CW);
		float run = 0.0;
		for (int k = -1; k <= 1; k++) {
			float c = ci + float(k) + floor(sd * 13.0);
			float hx = h11(c), hy = h11(c + 17.3), hz = h11(c + 41.9), hw = h11(c + 73.1);
			if (hx > 0.72) continue;
			// half from the crenels, half from the corbels' foot
			float d0 = (hz < 0.5 ? 0.0 : run_drop) - 0.15 + 0.4 * fract(hz * 9.7);
			float L = run_len * (0.3 + 0.7 * hy);
			float dd = d - d0;
			if (dd < 0.0 || dd > L) continue;
			float t = dd / L;
			float w = (0.32 + 0.5 * hw) * mix(1.0, 0.45, t);
			float cx = (c - floor(sd * 13.0) + 0.3 + 0.4 * fract(hx * 7.13)) * CW + 0.06 * sin(dd * 2.1 + hy * 6.28);
			float acr = 1.0 - smoothstep(0.28 * w, 0.6 * w, abs(u - cx));
			float alg = smoothstep(0.0, 0.25, dd) * (1.0 - smoothstep(0.45, 1.0, t)) * mix(0.65, 1.0, fract(hz * 23.1));
			run = max(run, acr * alg);
		}
		run *= mix(0.6, 1.0, vn(vec2(u * 4.1, d * 1.3)));
		alb *= mix(vec3(1.0), run_col, clamp(run * run_k * 1.8, 0.0, 1.0));
		// the damp foot: a mossy band with a ragged top, smoother (wet)
		float fh = 0.75 + 0.25 * (vn(vec2(u * 0.9 + sd, 3.0)) - 0.5) * 2.0 + 0.14 * (vn(vec2(u * 4.3, 7.0)) - 0.5) * 2.0;
		float band = (1.0 - smoothstep(fh - 0.12, fh + 0.08, o_pos.y)) * mix(0.75, 1.0, vn(vec2(u * 2.7, o_pos.y * 3.1)));
		alb *= mix(vec3(1.0), moss_col, band * moss_k);
		rough = mix(rough, rough * 0.8, band);
	}
	// (E8 later r3) the footing seen from the play camera (its weathering course and the foot of the drum, up to 1.75 m):
	// lifted so the stone ring reads, not a dark collar (dawn 25 -> ~29 luma); up faces more
	if (run_k > 0.0 && run_ring > 0.5) {
		float ft = 1.0 - smoothstep(1.55, 1.8, o_pos.y);
		alb *= 1.0 + ft * mix(0.2, 0.4, smoothstep(0.3, 0.6, o_nrm.y));
	}
	ALBEDO = alb;
	ROUGHNESS = rough;
	METALLIC = 0.0;
	SPECULAR = 0.5;
	NORMAL_MAP = texture(normal_tex, UV).rgb;
	NORMAL_MAP_DEPTH = normal_scale;
}

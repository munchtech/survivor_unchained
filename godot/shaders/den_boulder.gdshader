// The den's boulders (DungeonDress.Boulders.cs): each a PAINTING of the boulder as the fixed play camera sees it
// (tools/look/den_boulders.py), drawn on a card in the boulder that faces that camera (its plane spanned by the camera's
// right and up at yaw 0, pitch 62). The card writes the painting's own depth (boulders_form.png's alpha, along the view
// from the card), so she and the pack are hidden by the stone exactly where it is painted and nowhere else; outside the
// painting's alpha it discards. The painting is already lit and shaded (its lit band, shade side, ink and moss): the room's
// light only scales it (no cel bands, no n.l from the key; a soft turn for the shafts' spots and the fungus' omnis), and it
// takes no shadow (the boulder's own hull, a separate shadow-only mesh, would shade the painting twice).
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque, shadows_disabled, specular_disabled;

uniform sampler2D paint_tex : source_color, filter_linear_mipmap;
uniform sampler2D form_tex : filter_linear_mipmap;
uniform vec4 rect = vec4(0.0, 0.0, 1.0, 1.0);   // the boulder's rect in the atlases (uv: x, y, w, h)
uniform float dmax = 2.5;                      // the depth's range (m): d = (a * 2 - 1) * dmax
uniform vec3 right_dir = vec3(1.0, 0.0, 0.0);
uniform vec3 up_dir = vec3(0.0, 0.469472, -0.882948);
uniform vec3 view_dir = vec3(0.0, -0.882948, -0.469472);
uniform float gain = 1.0;                      // the painting's albedo scale (calibrated on the den's frames)
uniform float cold_take = 0.5;                 // how much of a cold light's brightness the stone takes
uniform float spot_cap = 99.0;                 // (den r18 L3, R17 item 10) a spot or omni's light on the stone, soft-capped (99: none)
uniform float local_turn = 0.5;               // how much a spot or omni follows the painted normal (0 flat)

varying vec3 lpos;
// (den r18 lead, coordinator #15 item: a boulder hid her whole body at the play camera, s11 leg L10) the occlusion cut-out as
// den_set's occ_cut: the painted stone nearer the camera than her chest and above her knees, inside a screen disc round her,
// dithered out to occ_a of itself. occ_k 0 off (--den-boulder-occlude). Her chest is the global 'survivor' (WorldScene).
global uniform vec4 survivor;
uniform float occ_k = 0.0;
uniform float occ_a = 0.2;
uniform vec2 occ_r = vec2(0.085, 0.15);
float occ_bayer(ivec2 p) {
	int x = p.x & 7;
	int y = p.y & 7;
	int v = 0;
	for (int i = 2; i >= 0; i--) {
		v = (v << 2) | ((((x >> i) & 1) ^ ((y >> i) & 1)) << 1) | ((y >> i) & 1);
	}
	return (float(v) + 0.5) / 64.0;
}
bool occ_cut(mat4 pm, vec3 vpos, vec3 wp, vec4 frag, vec2 vsz, mat4 vm) {
	if (occ_k <= 0.0 || survivor.w <= 0.0 || wp.y < survivor.y - 0.2) return false;
	vec3 her_v = (vm * vec4(survivor.xyz, 1.0)).xyz;
	if (-vpos.z >= -her_v.z - 0.4) return false;
	vec4 hp = pm * vec4(her_v, 1.0);
	vec2 ndc = hp.xy / hp.w;
	vec2 her_px = vec2(ndc.x * 0.5 + 0.5, 0.5 - ndc.y * 0.5) * vsz;
	float d = length(frag.xy - her_px) / vsz.y;
	float hole = (1.0 - occ_a) * occ_k * (1.0 - smoothstep(occ_r.x, occ_r.y, d));
	return occ_bayer(ivec2(frag.xy)) < hole;
}

void vertex() {
	lpos = VERTEX;
}

void fragment() {
	vec2 uv = rect.xy + UV * rect.zw;
	vec4 c = texture(paint_tex, uv);
	vec4 f = texture(form_tex, uv);
	vec3 lp = lpos + view_dir * ((f.a * 2.0 - 1.0) * dmax);
	vec4 vp = VIEW_MATRIX * (MODEL_MATRIX * vec4(lp, 1.0));
	vec4 cp = PROJECTION_MATRIX * vp;
	DEPTH = cp.z / cp.w;
	if (occ_cut(PROJECTION_MATRIX, vp.xyz, (MODEL_MATRIX * vec4(lp, 1.0)).xyz, FRAGCOORD, VIEWPORT_SIZE, VIEW_MATRIX)) discard;
	LIGHT_VERTEX = vp.xyz;
	vec3 nw = normalize(right_dir * (f.r * 2.0 - 1.0) + up_dir * (f.g * 2.0 - 1.0) - view_dir * (f.b * 2.0 - 1.0));
	NORMAL = normalize((VIEW_MATRIX * (MODEL_MATRIX * vec4(nw, 0.0))).xyz);
	ALBEDO = c.rgb * gain;
	ALPHA = c.a;
	ALPHA_SCISSOR_THRESHOLD = 0.5;
	// the ink tag (cel.gdshaderinc's cel_tag): roughness 1, class 2 (no post ink: the painting carries its own)
	ROUGHNESS = 126.0 / 127.0;
}

void light() {
	float w = LIGHT_IS_DIRECTIONAL ? 1.0 : mix(1.0, max(dot(NORMAL, LIGHT), 0.0), local_turn);
	// (round 7) a cold light (the fungus' teal omnis) gives the stone its brightness only, never its colour: it read green
	vec3 lc = LIGHT_COLOR;
	float ll = dot(lc, vec3(0.299, 0.587, 0.114));
	lc = LIGHT_IS_DIRECTIONAL || lc.r >= lc.g ? lc : vec3(ll) * cold_take;
	vec3 add = lc * ATTENUATION * w / PI;
	if (!LIGHT_IS_DIRECTIONAL) {
		float al = dot(add, vec3(0.299, 0.587, 0.114)), kn = 0.5 * spot_cap;
		if (al > kn) add *= (kn + (spot_cap - kn) * tanh((al - kn) / (spot_cap - kn))) / al;
	}
	DIFFUSE_LIGHT += add;
}

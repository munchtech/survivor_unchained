// (demo-look r2 her, 16 Nov; judge 1: "her sword is a 1 px black stick") Her held steel in the den (Actors/HerSteel.cs; the
// rig's hero_den row, View/HeroDen.cs). Metal in a dark room shows the dark, so the blade is painted, not reflected: its
// metal (the piece's own metallic map) at two set tones, lit where it faces the key and shade where it turns away, one
// painted glint across the blade (a short band at a set place along the piece's long axis, only where the blade faces the
// eye), and its grip at its own albedo times a light level. No light reaches it (light() adds nothing, no ambient, no
// specular; the tones are its emission), so the den's grade lands it where the row set it. A lit render mode on purpose:
// CelLib's line goes round lit, solid materials only, and her line must go round her blade.
shader_type spatial;
render_mode cull_disabled, depth_draw_opaque, shadows_disabled, specular_disabled, ambient_light_disabled;

global uniform vec4 cel_key;            // toward the key light (world), Atmosphere
global uniform vec4 hero_steel_lit;     // the steel's lit tone (linear rgb), w: the glint's place along the piece (0-1 from its low end)
global uniform vec4 hero_steel_shade;   // the steel's shade tone (linear rgb), w: the glint's half length (share of the piece)
global uniform vec4 hero_steel_glint;   // the glint's tone (linear rgb), w: the grip's light (its albedo times this)
uniform sampler2D albedo_tex : source_color, hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 albedo : source_color = vec4(1.0);
uniform sampler2D metal_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 metal_channel = vec4(0.0, 0.0, 1.0, 0.0);   // the metallic map's channel (glTF: blue)
uniform float metallic = 1.0;
uniform vec3 axis_lo;   // the piece's long axis in its mesh's space: its two ends (HerSteel, from the mesh's box)
uniform vec3 axis_hi;
varying vec3 mp;
// (lane E lead 10, 18 Nov; judge 7: lead 9's edge-on glint lit 48% of the blade, in dashes: a flat blade faces the eye, so
// no n.v term can find its edge.) At the play camera the blade is 2 px of its own between 2 px of her line each side. So,
// on screen: each vertex moves `widen` px out from the blade's axis (its own px grow by 1 a side, her line keeps 1 px of
// its 2, her whole outline the same size), and the half of the blade on the key's side of that axis (on screen), from
// `past` px over it, is the lit edge: one clean band the length of the blade whatever it is turned to, never a dash.
const float widen = 1.0;    // px at 1080p a side
const float past = 0.9;     // px at 1080p: the lit edge's reach past the blade's axis
const float edge_k = 0.85;  // the lit edge's share of the glint's tone (over the lit/shade tone)
varying float v_side;       // px at 1080p across the blade from its axis, + toward the key (on screen)

void vertex() {
	mp = VERTEX;
	mat4 mvp = PROJECTION_MATRIX * MODELVIEW_MATRIX;
	vec4 c = mvp * vec4(VERTEX, 1.0);
	vec4 a = mvp * vec4(axis_lo, 1.0), b = mvp * vec4(axis_hi, 1.0);
	vec2 h = VIEWPORT_SIZE * 0.5;
	vec2 sa = a.xy / a.w * h, sb = b.xy / b.w * h, sc = c.xy / c.w * h;
	vec2 dir = sb - sa;
	dir = length(dir) > 0.001 ? normalize(dir) : vec2(0.0, 1.0);
	vec2 perp = vec2(-dir.y, dir.x);
	// (the key's side: the key's own direction on screen at the blade; where the blade lies along it, the screen's top)
	vec3 mid = (MODEL_MATRIX * vec4(0.5 * (axis_lo + axis_hi), 1.0)).xyz;
	vec4 k0 = PROJECTION_MATRIX * VIEW_MATRIX * vec4(mid, 1.0);
	vec4 k1 = PROJECTION_MATRIX * VIEW_MATRIX * vec4(mid + normalize(cel_key.xyz + vec3(0.0, 1e-4, 0.0)) * 0.3, 1.0);
	vec2 ks = (k1.xy / k1.w - k0.xy / k0.w) * h;
	float side = dot(perp, ks) / max(length(ks), 1e-4) + 0.35 * perp.y;
	float s1080 = VIEWPORT_SIZE.y / 1080.0;
	float d = dot(sc - sa, perp);
	float push = widen * s1080 * clamp(d / (0.25 * s1080), -1.0, 1.0);
	c.xy += perp * push / h * c.w;
	POSITION = c;
	v_side = (d + push) / s1080 * (side >= 0.0 ? 1.0 : -1.0);
}

void fragment() {
	vec3 own = texture(albedo_tex, UV).rgb * albedo.rgb;
	float metal = step(0.5, dot(texture(metal_tex, UV), metal_channel) * metallic);
	vec3 wn = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec3 wv = normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz);
	// (lit unless it turns well away: a blade two or three px wide reads as one lit steel inside its line, not as stripes)
	float lit = step(-0.25, dot(wn, normalize(cel_key.xyz + vec3(0.0, 1e-4, 0.0))));
	vec3 ax = axis_hi - axis_lo;
	float t = dot(mp - axis_lo, ax) / max(dot(ax, ax), 1e-6);
	float glint = step(abs(t - hero_steel_lit.w), hero_steel_shade.w) * step(0.3, abs(dot(wn, wv)));
	vec3 steel = mix(mix(hero_steel_shade.rgb, hero_steel_lit.rgb, lit), hero_steel_glint.rgb, glint);
	// (lead 10) the lit edge: the key's half of the blade on screen, at most of the glint's tone; the glint across stays whitest
	vec3 edge = mix(mix(hero_steel_shade.rgb, hero_steel_lit.rgb, lit), hero_steel_glint.rgb, edge_k);
	steel = mix(steel, edge, step(-past, v_side) * (1.0 - glint));
	vec3 grip = own * hero_steel_glint.w * mix(0.55, 1.0, lit);
	EMISSION = mix(grip, steel, metal);
	ALBEDO = vec3(0.0);
	METALLIC = 0.0;
	ROUGHNESS = 1.0;
	AO = 0.0;
}

void light() {
}

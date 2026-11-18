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

void vertex() {
	mp = VERTEX;
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
	// (lane E lead 9, 17 Nov; the movement judge r19: "on dark ground the drawn blade loses its edge": her dark line round a
	// dark blade on dark ground leaves nothing. Where the steel turns edge-on to the eye (its bevels, its silhouette) it
	// takes most of the glint's tone, so the blade keeps a lit edge whatever it lies on.)
	float edge = 1.0 - smoothstep(0.22, 0.42, abs(dot(wn, wv)));
	steel = mix(steel, hero_steel_glint.rgb, edge * 0.75);
	vec3 grip = own * hero_steel_glint.w * mix(0.55, 1.0, lit);
	EMISSION = mix(grip, steel, metal);
	ALBEDO = vec3(0.0);
	METALLIC = 0.0;
	ROUGHNESS = 1.0;
	AO = 0.0;
}

void light() {
}

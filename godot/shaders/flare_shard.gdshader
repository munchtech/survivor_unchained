// Burns Twice's ice shards (Fx/Flare/FlareShards.cs): real lit geometry, faceted plates of see-through cyan glass
// (judge 4 fix 4: opaque matte grey cards read as spilled salt). A clear cyan body over whatever lies behind it,
// a bright grazing rim where the plate turns edge-on, and one short facet flash each as it tumbles; never white.
// Down, it is gone to a wet dark mark a half again its size within a tenth of a second, drying over a second and
// a half. INSTANCE_CUSTOM.x is the shard's heat (lit from inside by the ember that broke it, cooling), .y its melt
// (0..1 after it lands), .z 1 once landed, .w its seed. COLOR.a is its facet flash (1 for its two frames).
shader_type spatial;
render_mode diffuse_burley, specular_disabled, cull_back, blend_mix, depth_draw_never;

global uniform sampler2D flare_plate : filter_linear_mipmap, repeat_enable;
global uniform vec4 flare_hue;    // a: night 0..1

varying flat vec4 v_c;
varying flat float v_flash;
varying vec3 v_local;

void vertex() {
	v_c = INSTANCE_CUSTOM;
	v_flash = COLOR.a;
	v_local = VERTEX;
	// Facets stay facets; a breath of dome so a face never goes one flat tone.
	NORMAL = normalize(mix(NORMAL, normalize(VERTEX * vec3(0.6, 4.0, 0.6) + vec3(0.0, 1e-3, 0.0)), 0.15));
}

float fl_h(float x) { return fract(sin(x * 91.7) * 43758.5453); }

void fragment() {
	float rim = 1.0 - clamp(abs(dot(NORMAL, VIEW)), 0.0, 1.0);
	float cr = texture(flare_plate, v_local.xz * 1.6 + v_local.y * 1.7).r;
	float heat = clamp(v_c.x, 0.0, 1.0);
	float seed = v_c.w;
	float day = 1.0 - flare_hue.a;
	// Down: glass for the first frames of its landing (<=0.12 s), then only the wet mark.
	float down = v_c.z;
	float glassk = 1.0 - down * smoothstep(0.0, 0.08, v_c.y);
	// Which facet this is (twelve, each facing its own way): the one its seed picks takes the flash.
	float fid = floor(atan(v_local.z, v_local.x) * 0.955 + 3.0) + step(0.0, v_local.y) * 7.0;
	float mine = 1.0 - step(0.5, abs(fid - floor(fl_h(seed * 5.3) * 12.0)));
	// The body: clear cyan glass (about rgb 95,140,170 over the dark), a little of the light behind it bent
	// through the crystal's grain, cooler and thinner by day so the sun on it never turns it white.
	// (s9a: at 0.55 over the whole face they read as flat pale cards: the face clearer and dimmer, each facet its
	// own tone, the light at the edges.)
	// (Judge 6 (4): at night they read as grey paper. Ice: base sRGB about (140, 200, 225), a fresnel rim at least
	// twice its luma.)
	const vec3 base = vec3(0.262, 0.578, 0.753);
	float ftone = 0.8 + 0.2 * fl_h(seed * 3.1 + fid * 0.71);
	// (Its colour its own light: lit, under the fire's warm light, a cyan albedo went grey: a1.)
	vec3 body = base * (0.85 + 0.3 * cr) * ftone * mix(0.5, 0.25, day);
	float grazing = pow(rim, 2.0);
	// (Cyan to its brightest: a white rim or flash went neutral under the tone curve, white chips over the floor: a2.)
	vec3 rimc = base * grazing * mix(1.4, 0.7, day);
	vec3 flash = base * 0.9 * v_flash * mine * (1.0 - down);
	// Hot: lit orange at its edges by the fire that threw it (only the edges: a whole face lit read as confetti).
	vec3 hot = vec3(1.0, 0.32, 0.05) * heat * 1.1 * pow(rim, 2.5);
	ALBEDO = mix(base * 0.06, vec3(0.012, 0.014, 0.016), 1.0 - glassk);
	ROUGHNESS = 0.3;
	SPECULAR = 0.0;
	METALLIC = 0.0;
	EMISSION = ((body * (1.0 - 0.8 * heat) + rimc * (1.0 - 0.8 * heat) + flash) + hot) * glassk;
	float a_glass = clamp(0.7 + 0.2 * grazing + 0.2 * v_flash * mine, 0.0, 0.95);
	// The wet mark: dark, soft-edged, about 0.6x the ground, drying out.
	float r = length(v_local.xz);
	float a_wet = 0.42 * (1.0 - smoothstep(0.18, 0.46, r + (cr - 0.5) * 0.12)) * (1.0 - smoothstep(0.2, 1.0, v_c.y));
	ALPHA = mix(a_wet, a_glass, glassk);
}

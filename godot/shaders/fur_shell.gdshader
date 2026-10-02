// Fur by shells: the piece drawn again and again, each pass a little further
// out along its normals, keeping only the strands that reach that far, so
// the surface grows a pile of hairs that thin toward their tips and catch
// the light at their edges. Each pass is one of a chain of next_pass
// materials (People.Fur), `layer` from 0 at the skin to 1 at the tips.
shader_type spatial;
render_mode cull_back, depth_draw_opaque;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float layer = 0.0;
uniform float fur_length = 0.008;
uniform float density = 260.0;
uniform float clump = 0.35;
uniform vec3 gravity = vec3(0.0, -1.0, 0.0);

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void vertex() {
	// Strands bend down a little toward their tips.
	vec3 g = (inverse(MODEL_MATRIX) * vec4(gravity, 0.0)).xyz;
	VERTEX += NORMAL * fur_length * layer + g * fur_length * 0.35 * layer * layer;
}

void fragment() {
	vec2 cell = UV * density;
	vec2 id = floor(cell);
	vec2 f = fract(cell) - 0.5;
	float h = hash(id);
	// Each strand a cone: wide at the root, a point at its own height.
	float tall = mix(0.55, 1.0, h) * mix(1.0, hash(floor(UV * density * 0.12)), clump);
	float radius = 0.5 * (1.0 - layer / max(tall, 0.001));
	if (layer > 0.0 && (layer > tall || length(f) > radius)) discard;
	vec3 c = texture(albedo_tex, UV).rgb * tint.rgb;
	// Darker at the roots (shadowed by the pile), lighter at the tips.
	ALBEDO = c * mix(0.45, 1.15, layer);
	ROUGHNESS = 0.9;
	SPECULAR = 0.25;
	BACKLIGHT = c * 0.25;
}

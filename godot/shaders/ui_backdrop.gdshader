// Behind a full page or a side panel (Ui/Ornate.cs, Backdrop): the world
// as it is, softened out of focus, darkened and warmed, so the page sits in
// the place the survivor stands rather than on flat black. Its mipmaps give
// the blur; a few taps round each point smooth their steps.
shader_type canvas_item;

uniform sampler2D screen : hint_screen_texture, filter_linear_mipmap;
uniform float blur = 3.2;
uniform float dim = 0.5;
uniform vec3 tint : source_color = vec3(1.0, 0.86, 0.72);
uniform float grey = 0.35;

void fragment() {
	vec2 px = SCREEN_PIXEL_SIZE * exp2(blur);
	vec3 c = textureLod(screen, SCREEN_UV, blur).rgb * 0.4;
	c += textureLod(screen, SCREEN_UV + vec2(px.x, 0.0), blur).rgb * 0.15;
	c += textureLod(screen, SCREEN_UV - vec2(px.x, 0.0), blur).rgb * 0.15;
	c += textureLod(screen, SCREEN_UV + vec2(0.0, px.y), blur).rgb * 0.15;
	c += textureLod(screen, SCREEN_UV - vec2(0.0, px.y), blur).rgb * 0.15;
	float l = dot(c, vec3(0.3, 0.59, 0.11));
	c = mix(c, vec3(l), grey) * tint * dim;
	COLOR = vec4(c, 1.0);
}

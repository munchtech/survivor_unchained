// UI 17, The Drowned Girl (--hud drowned), piece 5: the draught's hair-bound flask (DgSmall). Two paintings of it
// (art/ui/dg_river/flask_full.png and flask_empty.png, tools/uiforge/dg_flask.py) blended at the liquid's level:
// below it the scarlet as painted, above it the dark empty glass; a bright meniscus while it drains or refills, and
// a short slosh (wave) when it is drunk. top and bot: the liquid's top and foot as painted (0..1 of the height).
shader_type canvas_item;

uniform sampler2D full_tex : filter_linear_mipmap, repeat_disable;
uniform sampler2D empty_tex : filter_linear_mipmap, repeat_disable;
uniform float level = 1.0;
uniform float top = 0.44;
uniform float bot = 0.95;
uniform float wave = 0.0;

void fragment()
{
	vec4 tint = COLOR;
	vec4 f = texture(full_tex, UV), e = texture(empty_tex, UV);
	float y = mix(bot, top, clamp(level, 0.0, 1.0)) + wave * sin(UV.x * 16.0 + TIME * 11.0) * 0.025;
	float k = smoothstep(y - 0.008, y + 0.008, UV.y) * step(0.002, level);
	vec4 c = mix(e, f, k);
	float liq = clamp(length(f.rgb - e.rgb) * 3.0, 0.0, 1.0);
	float moving = step(level, 0.995) * step(0.002, level);
	c.rgb += liq * exp(-pow((UV.y - y) / 0.010, 2.0)) * vec3(1.0, 0.62, 0.50) * 0.7 * moving;
	COLOR = c * tint;
}

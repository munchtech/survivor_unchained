// The Lamps board's field (src/Ui/LampBoard.cs, LampKnock.cs; docs/design/LAMPS_SCREEN_BRIEF.md §16 "Edges"): the board's
// window feathered on each side (C: 48 px all round; A: y 84-124 and 900-960, none at the screen's sides), and in A the
// knockout: the HUD foot's own alpha grown 32 px soft (48 at the girl's face), and her silhouette with a 10 px feather,
// so no lamp, road, halo or label crosses them. Sampled once per fragment (both masks are prepared at half size).
uniform vec4 win = vec4(0.0, 0.0, 1920.0, 1080.0);   // the board window in framebuffer px
uniform float feather = 48.0;
uniform vec4 fe = vec4(-1.0);                          // per side (left, top, right, bottom); x < 0: feather on all four
uniform float knock_on = 0.0;
uniform vec2 vp_size = vec2(1920.0, 1080.0);
uniform sampler2D knock_hud : hint_default_white, filter_linear, repeat_disable;
uniform sampler2D knock_her : hint_default_white, filter_linear, repeat_disable;

float side_(float d, float f) { return f < 0.5 ? step(0.0, d) : smoothstep(0.0, f, d); }

float knock_mask(vec2 fc) {
	if (knock_on < 0.5) return 1.0;
	vec2 uv = fc / vp_size;
	return texture(knock_hud, uv).r * texture(knock_her, uv).r;
}

float field_mask(vec2 fc) {
	vec4 f = fe.x < 0.0 ? vec4(feather) : fe;
	return side_(fc.x - win.x, f.x) * side_(fc.y - win.y, f.y) * side_(win.z - fc.x, f.z) * side_(win.w - fc.y, f.w)
		* knock_mask(fc);
}

// Heroic Leap's Henge Turn: its standing stones (BattleFx.P7Henge, WgHengeMat), painted in the den's own boulder paint
// (art/dungeon/den/boulders_paint.png, tools/look/den_boulders.py: no new art). One boulder's fully painted inside (rect,
// in atlas uv) is laid on triplanar in the stone's own space (so the paint rides the stone as it rises and sinks),
// mirror-tiled every `metres` so no seam shows, sampled with the unfolded gradient so the folds take no mip seam. The
// room's light shades it as any stone (its lit and shade sides); `tint` lifts the painting to the den's lit rock.
shader_type spatial;
render_mode cull_back, specular_disabled;

uniform sampler2D paint_tex : source_color, filter_linear_mipmap, repeat_disable;
uniform vec4 rect = vec4(0.2915, 0.0347, 0.1602, 0.1230);
uniform float metres = 0.9;
uniform vec3 tint = vec3(1.3, 1.25, 1.2);

varying vec3 lpos;
varying vec3 lnrm;

void vertex() {
	lpos = VERTEX;
	lnrm = NORMAL;
}

vec3 paint(vec2 p) {
	vec2 q = p / metres;
	vec2 m = 1.0 - abs(1.0 - 2.0 * fract(q * 0.5));
	return textureGrad(paint_tex, rect.xy + m * rect.zw, dFdx(q) * rect.zw, dFdy(q) * rect.zw).rgb;
}

void fragment() {
	vec3 w = pow(abs(normalize(lnrm)), vec3(4.0));
	w /= (w.x + w.y + w.z);
	vec3 c = paint(lpos.zy) * w.x + paint(lpos.xz) * w.y + paint(lpos.xy) * w.z;
	ALBEDO = c * tint;
	ROUGHNESS = 1.0;
}

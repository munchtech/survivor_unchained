// hud24 r1: the keeper's fade. His body fades to fade_to as fig_a falls; a 1 screen px gold rim (0.85, #CDAE72) stays along
// his outer silhouette, crossfaded in with the fade (none at fig_a = 1): a glass statue with the threat inside it.
// The art is 2x the rect, so a screen px is 2 texels. Self modulate is not used (fig_a is the fade); Modulate still dims.
shader_type canvas_item;
uniform float fig_a = 1.0;
uniform float fade_to = 0.30;
uniform float texels_per_px = 2.0;
// hud24 r2: the rim is taken from keeper_rim.png (tools/uiforge/dg_rim_mask.py): A the art's alpha with the small holes filled,
// R where a rim may be drawn (not along the bar's frame); the body alpha stays the art's own
uniform sampler2D rim_src : filter_linear;
const vec3 RIM_GOLD = vec3(0.8039, 0.6824, 0.4471);

void fragment()
{
	vec4 c = texture(TEXTURE, UV);
	float body = c.a * fig_a;
	float k = clamp((1.0 - fig_a) / (1.0 - fade_to), 0.0, 1.0);
	float rim = 0.0;
	if (k > 0.0)
	{
		vec2 st = TEXTURE_PIXEL_SIZE * texels_per_px;
		vec4 r = texture(rim_src, UV);
		float mn = r.a;
		for (int i = 0; i < 8; i++)
		{
			float ang = float(i) * 0.785398;
			mn = min(mn, texture(rim_src, UV + vec2(cos(ang), sin(ang)) * st).a);
		}
		rim = clamp(r.a - mn, 0.0, 1.0) * step(0.5, r.a) * r.r * step(0.5, c.a) * 0.85 * k;
	}
	float oa = body * (1.0 - rim) + rim;
	vec3 pm = c.rgb * body * (1.0 - rim) + RIM_GOLD * rim;
	COLOR = vec4(oa > 0.0 ? pm / oa : vec3(0.0), oa);
}

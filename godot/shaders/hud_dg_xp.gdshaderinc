// UI 18, the Drowned Girl's experience light (the owner's pick (c): "no XP on screen until it moves").
// Included by hud_dg_orb.gdshader (her hair) and hud_dg_river.gdshader (the river). At rest xp_on is 0 and nothing here
// runs: the HUD draws exactly as without it. On a gain (Play/XpLight.cs, DgRiver.Light) a cool light runs from her hair
// to the current fraction (the eddy = full), holds, and fades: behind the front the bronze itself is lifted (its own
// hue kept) on its ridges with only a faint cool cast, her hair lifted less than the river; the front is the brightest
// line, a cool glint. A level-up lights all of her hair and the river for its moment (xp_whole). Masks are baked from
// the art (tools/uiforge/dg_xp_mask.py, art/ui/dg_river/xp_light.png: R her hair, G the ridges, B the cast, softened).
// The widgets (rings, glass, icons, keycaps, the flask, the coal) are drawn over the river and her figure: no light
// reaches them.

uniform sampler2D xp_mask : hint_default_black, filter_linear;
uniform vec2 xp_at = vec2(295.0, 822.0);      // the mask's top left on the 1080 screen
uniform vec2 xp_size = vec2(1310.0, 258.0);
uniform float xp_on = 0.0;                     // anything lit (0: at rest)
uniform float xp_front = -1000.0;              // the front, in the run coordinate s (1080 px)
uniform float xp_tail = 0.0;                   // the run's light behind the front, 0..1 (its fade)
uniform float xp_peak = 0.0;                   // the front's own light, 0..1
uniform float xp_whole = 0.0;                  // a level-up: all of it lit, 0..1
uniform vec3 xp_c = vec3(0.886, 0.831, 1.0);   // the light (night: violet white #e2d4ff; day: sky white #cfe8ff)
uniform vec3 xp_hue = vec3(0.612, 0.494, 0.878); // its hue (night #9c7ee0; day #5aa2d6)
uniform float xp_day = 0.0;

// (UI 18 judge, hair 1 and 2: on her hair the light was a change of material at a level-up (all of it pearl, pink-
// lavender by night, mint by day, clipped near white) and only a warmer bronze on a run (so it seemed to start where
// the hair meets the river). On her hair the light now turns only the strand crests toward one cool white (no pink),
// stopping short of clipping; the mid-tones keep their bronze. The crests: the mask's ridges or the bronze's own lit
// tops, whichever is more.)
const vec3 XP_COOL = vec3(0.80, 0.89, 1.0);
vec3 xp_crest(vec3 r, float k)
{
	float L = dot(r, vec3(0.2126, 0.7152, 0.0722));
	return mix(r, XP_COOL * clamp(L * 1.12 + 0.14, 0.0, 0.93), clamp(k, 0.0, 0.85));
}

// fc: the bronze as drawn; scr: the 1080 screen px; m: how much of this is hair or river (0..1); hairk: the tail's
// strength here (her hair is lifted less than the river: 0.28; the river 1)
vec3 xp_light(vec3 fc, vec2 scr, float m, float hairk)
{
	vec3 mk = texture(xp_mask, (scr - xp_at) / xp_size).rgb;
	float H = mk.g;
	float cast = mk.b;
	float s = scr.x - 500.0 + 0.5 * (clamp(scr.y, 830.0, 980.0) - 830.0);
	float d = s - xp_front;
	float tail = xp_tail / (1.0 + exp(clamp(d / 6.0, -30.0, 30.0)));
	float peak = xp_peak * exp(-(d / 20.0) * (d / 20.0));
	// the tail: the bronze brightened on its ridges, its own hue kept, a faint cool cast (held.py)
	float kt = 0.85 * tail * m * hairk;
	bool hair = hairk < 0.99;
	float cr = hair ? max(smoothstep(0.30, 0.85, H), smoothstep(0.45, 0.78, dot(fc, vec3(0.2126, 0.7152, 0.0722)))) : 0.0;
	vec3 r = fc * (1.0 + 1.3 * kt * (0.5 + H)) + (hair ? vec3(0.0) : xp_hue * (kt * cast * 0.25));
	// her hair: the run's cool crest light from the nape, as the river's (its lift above stays the lesser); the front
	// and a level-up the same crest light, never the violet front's glint or cast (it read pink-lavender on her)
	if (hair) return xp_crest(r, max(0.85 * tail, max(peak, 0.9 * xp_whole)) * m * cr);
	// the front: the cool light itself, brightest on the ridges
	float kp = 2.3 * peak * m;
	r += xp_c * (kp * (1.05 * H + 0.10)) + xp_hue * (kp * cast * 1.15 * 0.35);
	// a level-up: her hair and the river lit at once (dir_c.py's level-up)
	float kw = 0.30 * xp_whole * m;
	r += xp_c * (kw * (1.05 * H + 0.10)) * mix(1.1, 1.0, xp_day) + xp_hue * (kw * cast * 1.15 * mix(0.40, 0.30, xp_day));
	return r;
}

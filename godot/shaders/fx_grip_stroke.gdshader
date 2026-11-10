// Her held grip's cut (src/Fx/BattleFx.Grip.cs; the pure parts: logic/Look/GripPaint.cs): the STROKE her blade lays and
// the hot edge her blade keeps between a chain's cuts. Steel family (fx_mid gold, fx_edge amber; the white is the
// stroke's own, grip_white), drawn after the grade (FxCel.Apply): hard cel edges, no soft alpha, no glow.
// Mode 0, the stroke, TAKE 7 (P7 lead 9): ONE brush stroke of paint, one mesh, one material, one draw.
//   UV.x = metres along the LAID path (anchored where each rib was laid: the fill never swims), grip_tail_u at the
//   drawn tail, grip_total at the blade now, more past it (the cap). UV.y = 0 at the guard, 1 on the tip's path, more
//   past it (the margin, then the throw's sheet). UV2 = (the rib's limit where the path turns on screen, the rib's
//   PRESS: laid with the rib, raised once where the blade crossed the bodies, never moved). COLOR = (whiteness / 2.5,
//   the contact's raise on this rib as a share).
//   (i) THE CAP: past the blade's line the paint runs on along the path's tangent to a convex nose near the tip's path
//   (grip_cap), its edge the bristles' tips (grip_rag: hashed, each tip rounded); from the nose the leading edge sweeps
//   BACK behind the blade's line to the inner edge on a concave curve: a fang. The blade's line is never an edge.
//   (ii) the width at a rib is grip_head x its press: it stays where it was laid. (iii) THE FILL: bristle lanes across
//   the width, each its own value (2-3 close ones, in streaks along the sweep), its own threshold on the rib's
//   whiteness (so the white's, the gold's and the amber's ends are tines along the sweep, never a line across), its
//   own start (the tail's comb), and as the stroke leaves its own dry gaps along the WHOLE length (grip_leave.y).
//   Leaving (grip_leave.x): the whole stroke thins toward the tip's path, the gold along the inner edge, and the
//   cap's inner edge retreats (the head closes to a point). (iv) THE SPLAY AND THE THROW: spikes rooted on the pressed
//   ribs' outer edge (grip_spike: the fanned tines, then the streaks thrown out to the cut's reach), the same paint.
// Mode 2, the hot edge (a quad on the blade facing the camera; UV.x 0 guard to 1 tip, UV.y pixels across; COLOR.r 1:
//   the tip's glint, UV -1..1): a core line grip_size.x px wide, stepping out gold, then amber (grip_thin 1, 2).
shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
#include "res://shaders/fx_cel.gdshaderinc"

uniform int grip_mode = 0;
uniform float grip_total = 1.0;   // the laid path's metres at the blade now
uniform float grip_tail_u = 0.0;  // the laid path's metres at the drawn tail
uniform float grip_blade = 1.0;   // the blade's length guard to tip (m)
uniform float grip_head = 0.6;    // the stroke's width at press 1 (a share of the blade, in from the tip's path)
uniform vec2 grip_point = vec2(0.5, 1.2);                // the tail: its first metres run to a point, the power
uniform vec4 grip_cap = vec4(0.7, 0.24, 0.55, 0.45);     // the cap, in stroke widths: its length past the blade's line, the nose's place across, how far behind the blade's line the inner edge starts, the outer corner's round-off (share of the length)
uniform vec2 grip_cap2 = vec2(0.6, 1.2);                 // the cap's inner curve's power (under 1: concave), the inner edge's further retreat at the shed's end (widths)
uniform vec3 grip_rag = vec3(5.0, 0.03, 0.6);            // the cap's bristle tips: a bristle (px across), the tips' variation (m), a tip's rounding (share of the bristle)
uniform float grip_thin = 0.0;    // mode 2: 0 hot, 1, 2 stepping out
uniform float grip_px = 0.012;    // a pixel here (m)
uniform float grip_seed = 0.0;
uniform vec2 grip_size = vec2(1.5, 0.5);
uniform float grip_narrow = 0.2;  // leaving: the stroke's width at the shed's end (share of its own)
uniform vec2 grip_leave = vec2(0.0, 0.0);                // leaving: the shed (0 whole, 1 its end), the dry gaps' share of each lane
uniform vec4 grip_fill = vec4(11.0, 0.93, 0.85, 0.3);    // the fill: bristle lanes across, the two darker values, the comb (a lane starts at its own whiteness up to this)
uniform vec4 grip_streak = vec4(0.35, 0.9, 0.3, 0.8);    // a value streak's length (m: least, most), a dry gap's cell (m: least, most)
uniform vec4 grip_tine = vec4(0.3, 0.25, 0.34, 0.68);    // a lane's own threshold (+-), its slant across the lane; the whiteness at which amber turns gold, gold turns white
uniform vec2 grip_shedw = vec2(0.3, 0.75);               // leaving: whiteness added along the tip's path, taken along the inner edge
uniform float grip_out = 0.1;     // the pressed ribs' outer edge, past the tip's path (a share of the blade at the raise's most)
uniform vec3 grip_white = vec3(1.0, 0.92, 0.72);         // the stroke's own white (grip.white.day / night; linear, as fx_core is)
uniform float grip_spike[48];     // the spikes on the pressed section's outer edge, 4 each: the root's place (m along), its half width (m along), its length out (m), its slant (m along per m out)
uniform int grip_spike_n = 0;
uniform int grip_tine_n = 0;      // the first of them are the splay's tines; the rest the thrown streaks
uniform vec2 grip_throw = vec2(0.55, 0.85);              // a thrown streak: white to this share of its length, gold to this, amber after

float grip_in(float edge, float x) { return 1.0 - fx_hard(edge, x, 0.0); }

// The cap's outline (logic/Look/GripPaint.cs CapFront, line for line): how far AHEAD of the blade's line the paint runs
// at a across (0 the tip's path, 1 the inner edge), in stroke widths: convex to the nose, concave from it back to
// behind the blade's line at the inner edge.
float grip_front(float a, float shed) {
	float an = grip_cap.y, back = grip_cap.z + grip_cap2.y * shed;
	if (a <= an) {
		float x = 1.0 - clamp(a / max(an, 1e-4), 0.0, 1.0);
		return grip_cap.x * (1.0 - grip_cap.w * x * x);
	}
	return grip_cap.x - (grip_cap.x + back) * pow(clamp((a - an) / max(1.0 - an, 1e-4), 0.0, 1.0), grip_cap2.x);
}

// One bristle lane's paint (li: the lane, ll: 0..1 across it) at u m of the laid path: its color and its cover.
// f = a pixel of (the whiteness, the lanes, the across); fu = a pixel of u.
vec4 grip_lane(float li, float ll, float u, float a, float white, float shed, float dry, vec3 f, float fu) {
	float h1 = fx_hash(vec2(li + 3.1, grip_seed)), h2 = fx_hash(vec2(li + 17.7, grip_seed)), h3 = fx_hash(vec2(li + 29.3, grip_seed));
	// its own threshold on the rib's whiteness, slanted across the lane: the colors end in tines along the sweep.
	// Leaving: the white runs on along the tip's path, the gold lies along the inner edge.
	float w = white + grip_tine.x * (2.0 * h1 - 1.0) + grip_tine.y * (ll - 0.5) + shed * mix(grip_shedw.x, -grip_shedw.y, a);
	float fw = f.x + abs(grip_tine.y) * f.y + shed * (grip_shedw.x + grip_shedw.y) * f.z;
	vec3 c = mix(fx_edge, fx_mid, clamp((w - grip_tine.z) / fw + 0.5, 0.0, 1.0));
	c = mix(c, grip_white, clamp((w - grip_tine.w) / fw + 0.5, 0.0, 1.0));
	// 2-3 close values in streaks along the sweep, anchored where they were laid
	float sl = mix(grip_streak.x, grip_streak.y, h2);
	float tone = fx_hash(vec2(li + 41.9, floor((u + 5.0 * h3) / sl + 0.3 * (ll - 0.5)) + grip_seed));
	c *= tone < 0.4 ? 1.0 : tone < 0.75 ? grip_fill.y : grip_fill.z;
	// the comb: each lane starts at its own whiteness (the lane on the tip's path whole: the comma's point)
	float st = li < 0.5 ? -1.0 : grip_fill.w * h3;
	float cov = clamp((white - st) / f.x + 0.5, 0.0, 1.0);
	// leaving: dry-brush gaps along the whole length (a value noise along the lane, anchored where it was laid)
	if (dry > 0.0) {
		float cl = mix(grip_streak.z, grip_streak.w, h2);
		float x = (u + 9.0 * h1) / cl + 0.5 * (ll - 0.5), i = floor(x), t = x - i;
		t = t * t * (3.0 - 2.0 * t);
		float nz = mix(fx_hash(vec2(li + 53.0, i + grip_seed)), fx_hash(vec2(li + 53.0, i + 1.0 + grip_seed)), t);
		cov *= clamp((nz - dry) / max(1.5 * fu / cl, 1e-5) + 0.5, 0.0, 1.0);
	}
	return vec4(c, cov);
}

vec4 grip_trail(vec2 uv, vec2 lay, vec2 rib) {
	float u = uv.x, sb = grip_total - u;   // metres behind the blade's line (negative: the cap, past it)
	float white = rib.x * 2.5, shed = grip_leave.x, dry = grip_leave.y;
	float thin = mix(1.0, grip_narrow, shed);
	// the tail: the first metres from the drawn tail run to a point (the brush landing; a short stroke: its whole length)
	float tw = pow(clamp((u - grip_tail_u) / max(min(grip_point.x, 1.25 * (grip_total - grip_tail_u)), 1e-3), 0.0, 1.0), grip_point.y);
	float po = grip_out * rib.y;           // the pressed ribs' outer edge splays out past the tip's path
	float vm = 1.0 - uv.y + po;            // shares of the blade in from the stroke's outer edge (negative: past it)
	// (lay.x: the rib's own limit where the path turns on screen: the stroke pinches inside the turn, never over itself)
	float wide = max(min(min(grip_head * lay.y * thin * tw, 0.98), lay.x) + po, 1e-4);
	float fv = max(fwidth(uv.y), 1e-5), fu = max(fwidth(u), 1e-5);
	float cov = 0.0;
	vec3 col = grip_white;
	if (vm > -fv) {
		float a = clamp(vm / wide, 0.0, 1.0), wm = wide * grip_blade;
		// the cap: the leading edge, the bristles' tips on it (each its own length, its end rounded)
		float lead = sb + grip_front(a, shed) * wm;   // metres inside the leading edge
		float bw = grip_rag.x * grip_px, bx = vm * grip_blade / bw, bi = floor(bx), bl = 2.0 * (bx - bi) - 1.0;
		float rag = grip_rag.y * (2.0 * fx_hash(vec2(bi + 61.7, grip_seed)) - 1.0) - grip_rag.z * bw * (1.0 - sqrt(max(1.0 - bl * bl, 0.0)));
		float front = clamp((lead + rag) / max(fwidth(lead), 1e-5) + 0.5, 0.0, 1.0);
		float edge = clamp(vm / fv + 0.5, 0.0, 1.0) * clamp((wide - vm) / fv + 0.5, 0.0, 1.0) * clamp(wide / fv, 0.0, 1.0);
		// the fill: bristle lanes of uneven width across, each its own paint; two lanes blended over their border's pixel
		float ln = grip_fill.x * a + 0.45 * sin(6.2832 * (2.3 * a + fx_hash(vec2(7.7, grip_seed))));
		float li = floor(ln), ll = ln - li;
		vec3 f = vec3(max(fwidth(white), 1e-5), max(fwidth(ln), 1e-5), max(fwidth(a), 1e-5));
		vec4 p0 = grip_lane(li, ll, u, a, white, shed, dry, f, fu);
		float dpx = min(ll, 1.0 - ll) / f.y;
		if (dpx < 0.5) {
			vec4 p1 = grip_lane(ll < 0.5 ? li - 1.0 : li + 1.0, ll < 0.5 ? 1.0 : 0.0, u, a, white, shed, dry, f, fu);
			float k = 0.5 - dpx, ca = mix(p0.a, p1.a, k);
			p0 = vec4(mix(p0.rgb * p0.a, p1.rgb * p1.a, k) / max(ca, 1e-4), ca);
		}
		col = p0.rgb;
		cov = p0.a * edge * front * step(grip_tail_u, u);
	}
	// the splay and the throw: spikes rooted on the pressed section's outer edge, each run out to a point
	if (grip_spike_n > 0 && vm < fv) {
		float o = max(-vm * grip_blade, 0.0), sp = 0.0, far = 0.0;
		for (int i = 0; i < grip_spike_n; i++) {
			float len = grip_spike[i * 4 + 2];
			if (o >= len) continue;
			float x = o / len;
			float c = clamp((grip_spike[i * 4 + 1] * pow(1.0 - x, 0.7) - abs(u - grip_spike[i * 4] - grip_spike[i * 4 + 3] * o)) / fu + 0.5, 0.0, 1.0);
			if (c > sp) { sp = c; far = i < grip_tine_n ? 0.0 : x; }
		}
		if (sp > cov) {
			col = far < grip_throw.x ? grip_white : far < grip_throw.y ? fx_mid : fx_edge;
			cov = sp;
		}
	}
	return vec4(col, cov);
}

vec4 grip_edge(vec2 uv, float glint) {
	int st = int(grip_thin + 0.5);
	vec3 c = st == 0 ? fx_core : st == 1 ? fx_mid : fx_edge;
	if (glint > 0.5) {
		// the tip's glint: a small four-point star, long along the blade; only while the edge is hot
		vec2 q = abs(uv);
		float sd = pow(q.x, 0.62) + pow(q.y, 0.62) - 1.0;
		return vec4(c, st == 0 ? grip_in(0.0, sd) : 0.0);
	}
	// the line: a little finer toward the guard, thinner by the step
	float hw = 0.5 * grip_size.x * mix(0.7, 1.0, clamp(uv.x, 0.0, 1.0)) * (st == 0 ? 1.0 : st == 1 ? 0.7 : 0.45);
	float cov = grip_in(hw, abs(uv.y)) * step(0.0, uv.x) * step(uv.x, 1.0);
	return vec4(c, cov);
}

void fragment() {
	vec4 c = grip_mode == 0 ? grip_trail(UV, UV2, COLOR.rg) : grip_edge(UV, COLOR.r);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}

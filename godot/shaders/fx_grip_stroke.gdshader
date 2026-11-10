// Her held grip's cut (src/Fx/BattleFx.Grip.cs; the pure parts: logic/Look/GripPaint.cs): the STROKE her blade lays and
// the hot edge her blade keeps between a chain's cuts. Steel family (fx_mid gold, fx_edge amber; the white is the
// stroke's own, grip_white), drawn after the grade (FxCel.Apply): hard cel edges, no soft alpha, no glow.
// Mode 0, the stroke, TAKE 10 (P7 lead 10; take 7's laying, lead 9; take 10: the press by streak, the warm gold, the grooves, the flicks): ONE brush stroke of paint, one mesh, one material, one draw.
//   UV.x = metres along the LAID path (anchored where each rib was laid: the fill never swims), grip_tail_u at the
//   drawn tail, grip_total at the blade now, more past it (the cap). UV.y = 0 at the guard, 1 on the tip's path, more
//   past it (the margin, then the throw's sheet). UV2 = (the rib's limit where the path turns on screen, the rib's
//   PRESS: laid with the rib, raised once where the blade crossed the bodies, never moved). COLOR = (whiteness / 2.5,
//   the contact's raise on this rib as a share).
//   (i) THE CAP: past the blade's line the paint runs on along the path's tangent to a convex nose near the tip's path
//   (grip_cap), its edge the bristles' tips (grip_rag: hashed, each tip rounded); from the nose the leading edge sweeps
//   BACK behind the blade's line to the inner edge on a concave curve: a fang. The blade's line is never an edge.
//   (ii) the width at a rib is grip_head x its press: it stays where it was laid. (iii) THE FILL (take 8): bristle
//   lanes across the width, each its own paint in streaks along the sweep: three values (the stroke's white,
//   grip_val1, grip_val2: hard ends, hard borders), the innermost lane GOLD (grip_gold: the kit's warm gold, a narrow
//   band on the inner edge, its border stepping a lane in and out), its own threshold on the whiteness (the tail's
//   amber and gold end in tines), its own start (the tail's comb). THE BRISTLES' GROOVES (grip_groove): hair lines of
//   the deepest value along stretches of the lanes' borders (the white reads as brushed), opening into thin dry gaps
//   in the tail half from the middle of the life (grip_leave.z); gaps along the whole length as it leaves
//   (grip_leave.y). THE PRESS (grip_stamp, asked at each half streak's centre: no line across the stroke) is more
//   paint, not another hue: its lanes split in two and take a little more of the deeper values. The head is LOADED:
//   white for grip_loaded m behind the blade whatever was laid (the stroke's first frame is a white comma).
//   Leaving (grip_leave.x): the whole stroke thins toward the tip's path, the gold along the inner edge, and the
//   cap's inner edge retreats (the head closes to a point). (iv) THE SPLAY AND THE THROW: on the contact's frame a
//   tine or two on the pressed ribs' outer edge (grip_spike, pixels wide), and the thrown FLICKS: each its own thin
//   ribbon along a smooth curve (grip_flick), fanned over the pressed span, white then gold, run to a point; shed,
//   its near end leaves the root and it breaks into a few dashes along the same line (grip_fly).
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
uniform vec3 grip_leave = vec3(0.0, 0.0, 0.0);           // leaving: the shed (0 whole, 1 its end), the dry gaps' share of each lane, of the gapped lanes at the tail (none past the middle)
uniform vec4 grip_fill = vec4(8.0, 0.5, 0.8, 0.3);       // the fill: bristle lanes across, a lane's share at the full white, up to the second value, the comb (a lane starts at its own whiteness up to this)
uniform vec3 grip_val1 = vec3(0.95, 0.74, 0.4);          // the second value (linear)
uniform vec3 grip_val2 = vec3(0.86, 0.6, 0.25);          // the third, the deepest (linear)
uniform vec3 grip_gold = vec3(0.12, 1.25, 0.3);          // the inner edge's gold band: its share of the width, the light gold's green and blue (x fx_mid's: a warm gold, never lemon), the next lane's share in gold
uniform vec2 grip_dense = vec2(0.15, 0.12);              // the press: the values' shares shift by this at the raise's most; a lane splits in two from this raise (+0.3 x its own number)
uniform vec4 grip_stamp = vec4(0.0, 0.32, 0.45, 0.0);    // the contact: its place (m along the laid path), its reach toward the head, toward the tail (m), its size now (share of the most; 0: none)
uniform vec4 grip_groove = vec4(1.3, 0.5, 2.0, 0.45);    // the bristles' grooves on the lanes' borders: a groove's width (px), the share of a border's length grooved, a dry gap's width (px), the groove's color (the deepest value toward the gold)
uniform float grip_loaded = 0.35; // the loaded head: white this many metres behind the blade's line
uniform vec4 grip_streak = vec4(0.35, 0.9, 0.3, 0.8);    // a value streak's length (m: least, most), a dry gap's cell (m: least, most)
uniform vec4 grip_tine = vec4(0.3, 0.25, 0.34, 0.68);    // a lane's own threshold (+-), its slant across the lane; the whiteness at which amber turns gold, gold turns white
uniform vec2 grip_shedw = vec2(0.3, 0.75);               // leaving: whiteness added along the tip's path, taken along the inner edge
uniform float grip_out = 0.03;    // the pressed ribs' outer edge, past the tip's path (a share of the blade at the raise's most)
uniform vec3 grip_white = vec3(1.0, 0.92, 0.72);         // the stroke's own white (grip.white.day / night; linear, as fx_core is)
uniform float grip_spike[48];     // the splay's tines on the pressed section's outer edge, 4 each: the root's place (m along), its half width at the root (PIXELS), its length out (m), its lean (m along per m out)
uniform int grip_spike_n = 0;
uniform vec3 grip_fly = vec3(0.0, 1.0, 0.35);            // a thrown flick now: its near end's place (share of its length), its dashes' share, a dash's cell (m)
uniform float grip_throw_gold = 0.7;                     // a thrown streak is white to this share of its length, gold after

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

// The press at uc m of the laid path, 0..1: where the contact was stamped (the fill asks it at a streak's CENTRE, so a
// whole streak is pressed or not: its ends are the streaks' own slanted ends, never a line across the stroke).
float grip_pressed(float uc) {
	float t = (uc - grip_stamp.x) / max(uc > grip_stamp.x ? grip_stamp.y : grip_stamp.z, 1e-3);
	return grip_stamp.w * clamp(1.0 - t * t, 0.0, 1.0);
}

// One bristle lane's paint (li: the lane, ll: 0..1 across it) at u m of the laid path: its color and its cover.
// wh = (the whiteness for the colors, the LAID whiteness for the comb), shed = the leaving, dr = (the dry gaps' share
// for every lane, the grooves' open share here); f = a pixel of (the whiteness, the lanes, the across); fu = a pixel of u.
vec4 grip_lane(float li, float ll, float u, float a, vec2 wh, float shed, vec2 dr, vec3 f, float fu) {
	float h1 = fx_hash(vec2(li + 3.1, grip_seed)), h2 = fx_hash(vec2(li + 17.7, grip_seed)), h3 = fx_hash(vec2(li + 29.3, grip_seed));
	// its own threshold on the whiteness, slanted across the lane: the tail's colors end in tines along the sweep.
	// Leaving: the white runs on along the tip's path, the gold lies along the inner edge.
	float w = wh.x + grip_tine.x * (2.0 * h1 - 1.0) + grip_tine.y * (ll - 0.5) + shed * mix(grip_shedw.x, -grip_shedw.y, a);
	float fw = f.x + abs(grip_tine.y) * f.y + shed * (grip_shedw.x + grip_shedw.y) * f.z;
	// its paint: streaks along the sweep, anchored where they were laid, each one of three values (hard ends, slanted
	// across the lane). THE PRESS is asked per HALF streak at its centre: a pressed half splits in two finer lanes,
	// each its own value, the deeper values taking a little more of it. Unpressed, the two halves are one streak.
	float hl = 0.5 * mix(grip_streak.x, grip_streak.y, h2);
	float ci = floor((u + 5.0 * h3) / hl + 0.6 * (ll - 0.5));
	float pressed = grip_pressed((ci + 0.5) * hl - 5.0 * h3);
	bool split = pressed > grip_dense.y + 0.3 * h1;
	float tone = split ? fx_hash(vec2(li + 49.2 + 7.3 * floor(2.0 * ll), ci + grip_seed)) : fx_hash(vec2(li + 41.9, floor(0.5 * ci) + grip_seed));
	float k0 = grip_fill.y - grip_dense.x * pressed, k1 = grip_fill.z - 0.8 * grip_dense.x * pressed;
	vec3 top = tone < k0 ? grip_white : tone < k1 ? grip_val1 : grip_val2;
	// the inner edge's gold band: the innermost lane is gold (the kit's warm gold, lighter in some streaks), the lane
	// beside it gold in some of its streaks (the band's border steps in and out along the sweep: bristles, not a hem)
	float lc = (li + 0.5) / grip_fill.x, edge_at = 1.0 - grip_gold.x;
	vec3 gold2 = fx_mid * vec3(1.0, grip_gold.y, grip_gold.y);
	bool gold = lc > edge_at || (lc + 1.0 / grip_fill.x > edge_at && tone > 1.0 - grip_gold.z);
	if (gold) top = fract(tone * 7.0) < 0.35 ? gold2 : fx_mid;
	// the comb: each lane starts at its own LAID whiteness (the lane on the tip's path whole: the comma's point)
	float st = li < 0.5 ? -1.0 : grip_fill.w * h3;
	float cov = clamp((wh.y - st) / f.x + 0.5, 0.0, 1.0);
	// THE BRISTLES' GROOVES: along stretches of a lane's border the paint is thin: a hair line of the deepest value
	// (in the white: the bristles read), and in the tail half from the middle of the life the stretch's middle opens
	// into a dry gap (the ground through). A value noise along the border, anchored where it was laid: pointed ends.
	if (li > 0.5) {
		float cl = mix(grip_streak.z, grip_streak.w, h1);
		float x = (u + 9.0 * h1) / cl, i = floor(x), t = x - i;
		t = t * t * (3.0 - 2.0 * t);
		float nz = mix(fx_hash(vec2(li + 53.0, i + grip_seed)), fx_hash(vec2(li + 53.0, i + 1.0 + grip_seed)), t);
		float fn = max(1.5 * fu / cl, 1e-5);
		float on = clamp((grip_groove.y - nz) / fn + 0.5, 0.0, 1.0);
		float open = clamp((grip_groove.y * dr.y - nz) / fn + 0.5, 0.0, 1.0);
		float line = clamp(grip_groove.x - ll / f.y + 0.5, 0.0, 1.0), gap = clamp(grip_groove.z - ll / f.y + 0.5, 0.0, 1.0);
		if (!gold) top = mix(top, mix(grip_val2, gold2, grip_groove.w), on * line);
		cov *= 1.0 - open * gap;
	}
	vec3 c = mix(fx_edge, fx_mid, clamp((w - grip_tine.z) / fw + 0.5, 0.0, 1.0));
	c = mix(c, top, clamp((w - grip_tine.w) / fw + 0.5, 0.0, 1.0));
	// leaving: dry-brush gaps open along the whole length of every lane (a value noise along the lane)
	if (dr.x > 0.0) {
		float cl = mix(grip_streak.z, grip_streak.w, h2);
		float x = (u + 9.0 * h2) / cl + 0.5 * (ll - 0.5), i = floor(x), t = x - i;
		t = t * t * (3.0 - 2.0 * t);
		float nz = mix(fx_hash(vec2(li + 67.0, i + grip_seed)), fx_hash(vec2(li + 67.0, i + 1.0 + grip_seed)), t);
		cov *= clamp((nz - dr.x) / max(1.5 * fu / cl, 1e-5) + 0.5, 0.0, 1.0);
	}
	return vec4(c, cov);
}

vec4 grip_trail(vec2 uv, vec2 lay, vec2 rib) {
	float u = uv.x, sb = grip_total - u;   // metres behind the blade's line (negative: the cap, past it)
	float wl = rib.x * 2.5, shed = grip_leave.x, span = max(grip_total - grip_tail_u, 1e-3);
	// the loaded head: white behind the blade whatever was laid there (the first frames: a white comma)
	float white = max(wl, 1.15 * (1.0 - sb / max(grip_loaded, 1e-3)));
	float thin = mix(1.0, grip_narrow, shed);
	// the tail: the first metres from the drawn tail run to a point (the brush landing; a short stroke: its whole length)
	float tw = pow(clamp((u - grip_tail_u) / max(min(grip_point.x, 1.25 * span), 1e-3), 0.0, 1.0), grip_point.y);
	vec2 dr = vec2(grip_leave.y, grip_leave.z * clamp(1.0 - (u - grip_tail_u) / (0.5 * span), 0.0, 1.0));
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
		// the fill: bristle lanes of uneven width across, each its own paint; two lanes meet on their border's pixel
		float ln = grip_fill.x * a + 0.45 * sin(6.2832 * (2.3 * a + fx_hash(vec2(7.7, grip_seed))));
		float li = floor(ln), ll = ln - li;
		vec3 f = vec3(max(fwidth(white), 1e-5), max(fwidth(ln), 1e-5), max(fwidth(a), 1e-5));
		vec2 wh = vec2(white, wl);
		vec4 p0 = grip_lane(li, ll, u, a, wh, shed, dr, f, fu);
		float dpx = min(ll, 1.0 - ll) / f.y;
		if (dpx < 0.5) {
			vec4 p1 = grip_lane(ll < 0.5 ? li - 1.0 : li + 1.0, ll < 0.5 ? 1.0 : 0.0, u, a, wh, shed, dr, f, fu);
			float k = 0.5 - dpx, ca = mix(p0.a, p1.a, k);
			p0 = vec4(mix(p0.rgb * p0.a, p1.rgb * p1.a, k) / max(ca, 1e-4), ca);
		}
		col = p0.rgb;
		cov = p0.a * edge * front * step(grip_tail_u, u);
	}
	// the splay: a few short tines rooted on the pressed section's outer edge, hair lines in pixels
	if (grip_spike_n > 0 && vm < fv) {
		float o = max(-vm * grip_blade, 0.0), fo = max(fv * grip_blade, 1e-5), sp = 0.0;
		for (int i = 0; i < grip_spike_n; i++) {
			float len = grip_spike[i * 4 + 2];
			if (len <= 1e-4 || o >= len) continue;
			// its width: the root's, run toward a point but never under a pixel (a dim hair reads dark)
			float wpx = max(grip_spike[i * 4 + 1] * (1.0 - o / len), 0.6);
			float du = u - grip_spike[i * 4] - grip_spike[i * 4 + 3] * o;
			sp = max(sp, clamp(wpx - abs(du) / fu + 0.5, 0.0, 1.0) * clamp((len - o) / fo, 0.0, 1.0));
		}
		if (sp > cov) { col = grip_white; cov = sp; }
	}
	return vec4(col, cov);
}

// A THROWN FLICK (take 10): its own thin ribbon in the stroke's mesh, laid along a smooth curve from its root on the
// pressed section's outer edge out toward the cut's reach (BattleFx.Grip.cs GripFlicks: the curve is GEOMETRY, so it
// cannot kink; take 8 drew it in a fanned sheet of quads and the fan's triangles broke every line into a zigzag).
// uv = (metres along it, 50 + pixels across it), st = (its length (m), its number), wroot = its half width at the
// root (px). It runs to a point; shed, its near end leaves the root (grip_fly.x) and it breaks into a few dashes
// along the same line (grip_fly.y, .z). White, then the warm gold toward its end.
vec4 grip_flick(vec2 uv, vec2 st, float wroot) {
	float o = uv.x, len = max(st.x, 1e-3), x = o / len, d = abs(uv.y - 50.0), near = grip_fly.x;
	if (x <= near || x >= 1.0) return vec4(0.0);
	float fo = max(fwidth(o), 1e-5), xx = (x - near) / max(1.0 - near, 1e-3), hs = fx_hash(vec2(st.y + 71.3, grip_seed));
	float wpx = max(wroot * pow(1.0 - xx, 0.7), 0.55);
	if (near > 0.0) wpx *= clamp(xx * 6.0, 0.0, 1.0);
	float c = clamp(wpx - d + 0.5, 0.0, 1.0) * clamp((len - o) / fo, 0.0, 1.0) * clamp((o - near * len) / fo, 0.0, 1.0);
	if (grip_fly.y < 0.999) {
		// each dash its own length, more gap toward the end; the first stretch whole
		float q = o / grip_fly.z + 7.0 * hs, ci = floor(q), t = q - ci;
		float dd = mix(1.0, grip_fly.y * (0.6 + 0.8 * fx_hash(vec2(ci + 13.7, hs + grip_seed))), smoothstep(0.05, 0.4, xx));
		c *= clamp((dd - t) * grip_fly.z / fo + 0.5, 0.0, 1.0);
	}
	return vec4(x < grip_throw_gold ? grip_white : fx_mid * vec3(1.0, grip_gold.y, grip_gold.y), c);
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
	vec4 c = grip_mode != 0 ? grip_edge(UV, COLOR.r) : UV.y > 20.0 ? grip_flick(UV, UV2, COLOR.r * 4.0) : grip_trail(UV, UV2, COLOR.rg);
	if (c.a < 0.004) discard;
	ALBEDO = fx_out(c.rgb, c.a);
	ALPHA = c.a;
}

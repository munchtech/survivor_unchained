// The Lamps board's motion (docs/design/LAMPS_SCREEN_BRIEF.md §11; src/Ui/LampMotion.cs, LampBoard.cs): a few uniforms
// and each instance's own event time, so the board animates with no per-frame instance writes. Times are LampMotion's
// clock (now); NO_EV (-1e4) is "none". The open: a lamp fades in over 0.10 s after stagger x its distance from her
// hearth over open_r (the radial stagger, 0.25 s in all); the halos bloom last (0.20-0.35 s). The close: all out over
// 0.2 s, no stagger. still: reduce-motion (the flicker, the breathing and the running fuse stilled, the stagger instant).
uniform float now = 0.0;
uniform float open_t0 = -10000.0;
uniform float close_t0 = 1000000.0;   // (none: far ahead)
uniform vec2 hearth = vec2(0.0);
uniform float open_r = 1000.0;
uniform float stagger = 0.15;
uniform float still = 0.0;

const float RUN = 0.16;      // the flame along the road from the lit neighbor
const float CATCH = 0.12;    // the lamp catches: x0.85 to 1, a bloom
const float HALO_GROW = 0.3;
const float GUTTER = 0.18;
const float DRAIN = 0.2;

float ease_out(float u) { u = clamp(u, 0.0, 1.0); return 1.0 - (1.0 - u) * (1.0 - u) * (1.0 - u); }
float close_out() { return 1.0 - clamp((now - close_t0) / 0.2, 0.0, 1.0); }
// a board point's open alpha (d: its distance from the hearth, px)
float open_in(float d) { return clamp((now - open_t0 - stagger * clamp(d / max(open_r, 1.0), 0.0, 1.0)) / 0.10, 0.0, 1.0); }
float halo_open() { return clamp((now - open_t0 - 0.20) / 0.15, 0.0, 1.0); }
// the lit lamps' luma at rest: ±4%, each its own phase (seed); stilled, each its fixed offset as before
float flicker(float seed) {
	if (still > 0.5) return 1.0 + (seed - 0.5) * 0.08;
	float t = TIME;
	return 1.0 + 0.04 * (0.62 * sin(6.2831853 * (1.30 * t + seed)) + 0.38 * sin(6.2831853 * (2.70 * t + seed * 1.73)));
}

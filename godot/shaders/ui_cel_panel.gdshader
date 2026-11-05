// The UI language's panel (L1 B6; docs/design/LOOK_BIBLE.md rule 12; data/look/ui_language.json "panel", set by
// tools_scenes/ui_panel.gd): a dark painted field in a bronze frame, as targets 08 and 11 draw one. From the outside in:
// the ink line, the frame's one highlight band, its flat bronze body, a shade step, the inner ink line, then the field
// (its middle color falling to its deep color at the edges, a soft brushed grain); square corner plates with chamfered
// corners and a rivet; one optional gold line across the field. Flat painted blocks, no gradients but the field's.
// On a test panel only (the UI lead owns every element's look): never set on a live screen.
shader_type canvas_item;

uniform vec2 size_px = vec2(1208.0, 838.0);
uniform vec3 field : source_color = vec3(0.176, 0.129, 0.133);
uniform vec3 field_deep : source_color = vec3(0.161, 0.114, 0.118);
uniform vec3 frame : source_color = vec3(0.451, 0.227, 0.176);
uniform vec3 frame_hi : source_color = vec3(0.773, 0.396, 0.208);
uniform vec3 ink : source_color = vec3(0.035, 0.035, 0.063);
uniform float frame_px = 16.1;
uniform float line_px = 2.9;
uniform float corner_px = 57.4;
uniform float band = 0.214;
uniform float grain = 0.054;
// the gold line: its color, its height from the top (px; 0 = none), its weight (px)
uniform vec3 gold : source_color = vec3(0.851, 0.710, 0.416);
uniform float gold_y = 0.0;
uniform float gold_px = 2.0;

float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vnoise(vec2 p) {
	vec2 i = floor(p), f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}
// a hard, antialiased step at d = 0 (inside where d < 0)
float cov(float d) { return clamp(0.5 - d, 0.0, 1.0); }

// past an edge at 0, antialiased over a pixel
float past(float x) { return clamp(x + 0.5, 0.0, 1.0); }

// the frame's color at `d` px in from its outer edge: ink, the highlight band, the bronze body, a shade step, ink
vec3 frame_at(float d, float fw) {
	float hb = max(1.0, band * fw);
	vec3 c = ink;
	c = mix(c, frame_hi, past(d - line_px));
	c = mix(c, frame, past(d - line_px - hb));
	c = mix(c, frame * 0.72, past(d - (fw - line_px - 1.5)));
	c = mix(c, ink, past(d - (fw - line_px)));
	return c;
}

void fragment() {
	vec2 p = UV * size_px;
	// the distance in from the panel's nearest edge
	vec2 e = min(p, size_px - p);
	float d = min(e.x, e.y);
	float fw = frame_px;
	// the field: middle to deep by the distance from the edge, a brushed grain (long strokes, mostly across)
	float vig = smoothstep(0.0, 0.35 * min(size_px.x, size_px.y), d - fw);
	vec3 col = mix(field_deep, field, vig);
	// broad diagonal brush strokes (11's field: L 0.25-0.30, its L10-L90 span is `grain`)
	vec2 sp = mat2(vec2(0.866, 0.5), vec2(-0.5, 0.866)) * p;
	float g = vnoise(sp * vec2(0.006, 0.03)) * 0.65 + vnoise(sp * vec2(0.015, 0.08) + 7.0) * 0.35;
	col *= 1.0 + (g - 0.5) * grain * 12.0;
	if (gold_y > 0.0) {
		float gy = abs(p.y - gold_y) - gold_px * 0.5;
		float fade = smoothstep(fw + 40.0, fw + 140.0, min(p.x, size_px.x - p.x));
		col = mix(col, gold, cov(gy) * fade);
	}
	// the frame band
	if (d < fw + 1.0) col = mix(frame_at(d, fw), col, clamp(d - fw + 0.5, 0.0, 1.0));
	// the corner brackets: an L of two arms along the edges, corner_px long, inked, highlit on its outer edges, a rivet
	vec2 q = min(p, size_px - p);
	if (q.x < corner_px + 2.0 && q.y < corner_px + 2.0) {
		vec2 r = q - vec2(corner_px * 0.5);
		// an L bracket: two arms frame_px + 6 wide along the edges, corner_px long, the outer corner chamfered
		float aw = fw + 6.0;
		float arm = min(max(q.x - corner_px, q.y - aw), max(q.y - corner_px, q.x - aw));
		float cut = (q.x + q.y) - corner_px * 0.22;
		float sd = max(max(arm, -q.x), max(-q.y, -cut * 0.7071));
		vec3 pc = frame;
		float din = -sd;
		pc = mix(frame_hi, pc, past(din - line_px - max(1.0, band * fw)));
		// the shade on its inner (lower right) half
		pc = mix(pc, frame * 0.72, past(din - aw * 0.5));
		// the rivet
		r = q - vec2(aw * 0.5);
		float rv = length(r) - aw * 0.26;
		pc = mix(pc, ink, cov(rv));
		pc = mix(pc, frame_hi, cov(length(r + vec2(aw * 0.07)) - aw * 0.12));
		pc = mix(ink, pc, past(din - line_px));
		col = mix(col, pc, cov(sd));
	}
	COLOR = vec4(col, 1.0);
}

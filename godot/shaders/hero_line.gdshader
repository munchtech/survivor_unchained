shader_type spatial;
// (L1 lead 20, HER5) The hero's LINE: a hull round a hero-scale figure in her lit pool (the rig's hero_pool, values 8 and 9;
// CelLib.HeroLine hangs it on every mesh of hers as the overlay's passes). One pass draws the mesh once more in ONE dark
// tone, moved `dir` x the rig's width in SCREEN pixels and set back from the eye, so only what sticks out past her own
// surface shows: the passes together (six directions) widen her silhouette by the same px all round. No normals are read:
// a thin shell (her shield, cloth, hair cards) has the same normals front and back and a push along them shrinks or
// slides it. The width is a share of the frame's height (px at 1080p), so in a close view the line stays as thin.
// Off (cel_hero_line.w = 0: no row, a camera rig): every vertex leaves the frame, nothing is drawn.
render_mode unshaded, cull_disabled, shadows_disabled;

global uniform vec4 cel_hero_line;      // rgb: the line's tone (linear), w: its width in px at 1080p (0: off)
uniform vec2 dir = vec2(1.0, 0.0);      // this pass's shift on screen, a unit vector
uniform float back = 0.15;              // how far behind her surface the hull sits, m along the eye's ray: a part of hers
                                        // nearer than this to what is behind it draws no line between them
uniform float floor_y = -1000.0;        // her foot's height: the hull never sinks under the floor she stands on
uniform float lift = 0.012;             // the hull's least height over that floor, m
uniform float near_px = 0.0;            // (hair cards: the hull is the card's whole quad) px per metre from which the
                                        // line thins to nothing in a close view; 0: never
// (L1 lead 22, HAIRLINE) Hair: CelLib hangs a chain on each OPAQUE hair surface (never the blended cap or fine hairs) with
// that surface's own cut, so the hull is the strands as drawn, not the card's whole quad: 1 a card (heroine_hair.gdshaderinc,
// not the cap: its atlas's alpha by its root's fade and the vertex alpha), 2 a braid's rope on the cap (vertex blue 0.5 up).
uniform int cut_mode = 0;               // 0: no cut (a solid mesh)
uniform sampler2D cut_tex : hint_default_white, filter_linear_mipmap, repeat_enable;   // the surface's strands atlas
uniform float cut = 0.3;                // the cover the hull counts from (CelLib.LineHairCut: the fringe past the core)
uniform float cut_bias = 0.0;           // its mip bias (strand_bias)

void vertex() {
	float px = cel_hero_line.w;
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	bool ortho = PROJECTION_MATRIX[3][3] != 0.0;
	vec3 ray = ortho ? -INV_VIEW_MATRIX[2].xyz : normalize(w - CAMERA_POSITION_WORLD);
	float b = back;
	if (ray.y < -0.001) b = min(b, (w.y - floor_y - lift) / -ray.y);
	w += ray * max(b, 0.0);
	vec4 clip = PROJECTION_MATRIX * (VIEW_MATRIX * vec4(w, 1.0));
	if (near_px > 0.0) {
		float ppm = PROJECTION_MATRIX[1][1] * VIEWPORT_SIZE.y * 0.5 / max(ortho ? 1.0 : clip.w, 0.0001);
		px *= 1.0 - smoothstep(near_px, near_px * 2.0, ppm);
	}
	clip.xy += dir * (px * (VIEWPORT_SIZE.y / 1080.0) * 2.0) / VIEWPORT_SIZE * clip.w;
	POSITION = px > 0.0 ? clip : vec4(3.0, 3.0, -1.0, 1.0);
}

void fragment() {
	if (IN_SHADOW_PASS) discard;
	if (cut_mode > 0) {
		vec4 t = texture(cut_tex, UV, cut_bias);
		float cover;
		if (cut_mode == 2) {
			if (COLOR.b < 0.5) discard;
			cover = max(COLOR.a * COLOR.a, t.a * smoothstep(0.0, 0.8, COLOR.a + (t.g - 0.5) * 0.35));
		} else {
			cover = t.a * smoothstep(0.0, 0.012, UV.y) * COLOR.a;
		}
		if (cover < cut) discard;
	}
	ALBEDO = cel_hero_line.rgb;
}

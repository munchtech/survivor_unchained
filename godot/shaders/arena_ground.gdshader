// An ember arena's ground (View/ArenaGround.cs): the place's own seven
// photoscanned materials (art/arena/PLACE: two for the ground itself, four it
// paints over them, one for steep faces), mixed by the arena's two paints
// (Maps/ArenaGen.cs), their edges frayed by noise and decided by height, each
// sampled twice and turned along a slow noise so no tile repeats on screen.
// Over them: standing water that holds the moon, ground trodden flat, the
// ember's char with its cracks glowing, and the dark past the ring.
//
// For the fight's sake the ground is held in a value range below everything
// that moves on it (g_tone, g_sat), and the ember's glow keeps to the char.
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#define NL 7
#define FACE 6

uniform sampler2D noise_tex : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D splat : filter_linear_mipmap, repeat_disable;
uniform sampler2D splat2 : filter_linear_mipmap, repeat_disable;
// R moss, G the slurry's light, B foxfire, A open to the sky.
uniform sampler2D splat3 : filter_linear_mipmap, repeat_disable;
uniform vec3 moss_color : source_color = vec3(0.05, 0.1, 0.02);
// The slurry the Dig cooks: "warm, faintly glowing", a sick yellow-green.
uniform vec3 slurry : source_color = vec3(0.52, 0.62, 0.16);
uniform float slurry_glow = 0.0;
// Foxfire (splat3 B): the cold light rotting wood gives off.
uniform vec3 fox_color : source_color = vec3(0.55, 0.85, 0.6);
uniform float fox_glow = 0.0;
uniform sampler2DArray g_alb : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_nor : filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2DArray g_arh : filter_linear_mipmap_anisotropic, repeat_enable;
uniform float g_scale[NL];
// Each photograph brought to the value the place asks of it (its mean albedo
// over what it was shot at), and how much of its colour it keeps: all kept
// below the living (View/ArenaGround.cs).
uniform float g_tone[NL];
uniform float g_sat[NL];
// Each photograph's own contrast pushed (1 as shot) about its mean luminance
// (g_mean): from thirty metres up a scan's grain averages away, and the
// ground reads as asphalt unless its lights and darks are pulled apart.
uniform float g_con[NL];
uniform float g_mean[NL];
// How high each material lies (metres over the bare ground) and how much
// its own photographed height swells it: summed, they make the ground's
// macro relief, whose slopes light the edges between materials, so moss
// stands up off the earth and a pool lies sunk in it rather than painted on.
uniform float g_lift[NL];
uniform float g_bump[NL];
uniform float relief = 1.0;
uniform float zone_size = 300.0;
// Moonlight through a canopy, in pools (the Hollow).
uniform float dapple = 0.0;
uniform vec3 ember : source_color = vec3(1.0, 0.35, 0.13);
uniform float ember_glow = 1.0;
// Water's colour in the low places (a stream's slurry sheen).
uniform vec3 wet_tint : source_color = vec3(0.55, 0.55, 0.52);
// The night sky as standing water gives it back (no reflection probe sees
// it from the arena's camera; without it, water reads as a hole).
uniform vec3 sheen : source_color = vec3(0.2, 0.27, 0.4);
uniform float sheen_amount = 0.06;

// Where the lip burns: metres outside the walkable edge. Just past where she
// can stand, so it marks the edge without ever lying under the fight.
uniform float lip_at = 1.8;
// How hot the lip burns: a story place's edge is its banks, and its lip burns low (a glow
// in the char, no white thread round every bank).
uniform float lip_glow = 1.0;
// How far in from the edge the ground is heat-killed (metres): a story place is small.
uniform float scorch_reach = 11.0;

varying vec3 w_pos;
varying vec3 w_nrm;
varying float w_in;
varying float w_inn;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	// How far inside the ring this vertex is (1 well in, 0 well out), and in metres.
	w_in = COLOR.r;
	w_inn = CUSTOM0.r;
}

vec2 hash2(vec2 p) {
	p = vec2(dot(p, vec2(127.1, 311.7)), dot(p, vec2(269.5, 183.3)));
	return fract(sin(p) * 43758.5453);
}

// Burnt ground splits into plates: the distance to the nearest plate's border
// (half the gap between the nearest two cells' points, never below nothing:
// the exact border's search went wrong under the warp and filled whole plates
// as border, which lit as flat orange blobs), and that plate's own hash.
vec3 plates(vec2 x) {
	vec2 n = floor(x), f = fract(x);
	float d1 = 8.0, d2 = 8.0;
	vec2 id = n;
	for (int j = -1; j <= 1; j++)
		for (int i = -1; i <= 1; i++) {
			vec2 g = vec2(float(i), float(j));
			vec2 r = g + hash2(n + g) - f;
			float d = length(r);
			if (d < d1) { d2 = d1; d1 = d; id = n + g; }
			else if (d < d2) d2 = d;
		}
	return vec3((d2 - d1) * 0.5, hash2(id));
}

vec2 g_uv(int i, vec3 p, vec3 n, out mat3 tbn) {
	if (i == FACE) {
		vec2 h = normalize(n.xz + vec2(1e-4, 0.0));
		vec3 t = vec3(-h.y, 0.0, h.x);
		tbn = mat3(t, vec3(0.0, -1.0, 0.0), n);
		return vec2(dot(p.xz, vec2(-h.y, h.x)), p.y) * g_scale[i];
	}
	vec3 t = normalize(vec3(1.0, 0.0, 0.0) - n * n.x);
	tbn = mat3(t, cross(n, t), n);
	return p.xz * g_scale[i];
}

// No tile repeats on screen (Inigo Quilez's "texture repetition", third
// way): a slow noise picks, patch by patch, one of eight offsets into the
// photograph, and two neighbouring picks are blended where the noise
// crosses between them. Offsets only, so the normals need no turning; the
// gradients are the unshifted uv's, so the mip level never jumps at a seam.
struct Pick { vec2 a; vec2 b; float t; vec2 dx; vec2 dy; };

Pick pick(vec2 uv, vec2 w, int i) {
	Pick p;
	float k = texture(noise_tex, w * 0.09 + vec2(float(i) * 0.137, float(i) * 0.291)).r;
	float l = k * 8.0;
	float ia = floor(l);
	p.a = sin(vec2(3.0, 7.0) * ia);
	p.b = sin(vec2(3.0, 7.0) * (ia + 1.0));
	p.t = smoothstep(0.25, 0.75, fract(l));
	p.dx = dFdx(uv);
	p.dy = dFdy(uv);
	return p;
}

vec4 tex2(sampler2DArray s, vec2 uv, int i, Pick p) {
	vec4 a = textureGrad(s, vec3(uv + p.a, float(i)), p.dx, p.dy);
	vec4 b = textureGrad(s, vec3(uv + p.b, float(i)), p.dx, p.dy);
	return mix(a, b, p.t);
}

vec3 nor2(vec2 uv, int i, Pick p) {
	return normalize(tex2(g_nor, uv, i, p).xyz * 2.0 - 1.0);
}

void fragment() {
	vec2 w = w_pos.xz;
	vec4 nL = texture(noise_tex, w * 0.011);
	vec4 nM = texture(noise_tex, w * 0.061 + 0.37);
	vec4 nF = texture(noise_tex, w * 0.29 + 0.71);
	vec2 suv = (w + zone_size * 0.5) / zone_size;
	vec4 sp = texture(splat, suv);
	vec4 s2 = texture(splat2, suv);
	vec3 n_geo = normalize(w_nrm);

	// The ground's two materials, in the patches the paint asks for.
	float b2 = smoothstep(0.3, 0.7, s2.a + (nM.b - 0.5) * 0.5 + (nF.g - 0.5) * 0.15);
	float gw[NL] = float[](1.0 - b2, b2, 0.0, 0.0, 0.0, 0.0, 0.0);
	// The four painted over them, each taking its share from what is under it.
	float wp[4] = float[](
		smoothstep(0.35, 0.65, sp.r + (nM.b - 0.5) * 0.4 + (nF.g - 0.5) * 0.12),
		smoothstep(0.35, 0.65, sp.g + (nM.g - 0.5) * 0.4 + (nF.b - 0.5) * 0.12),
		smoothstep(0.35, 0.65, sp.b + (nM.r - 0.5) * 0.4 + (nF.r - 0.5) * 0.12),
		smoothstep(0.35, 0.65, sp.a + (nM.a - 0.5) * 0.4 + (nF.g - 0.5) * 0.12));
	for (int l = 0; l < 4; l++) {
		for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wp[l];
		gw[2 + l] += wp[l];
	}
	float slope = 1.0 - clamp(n_geo.y, 0.0, 1.0);
	float wr = smoothstep(0.32, 0.52, slope + (nM.b - 0.5) * 0.15);
	for (int k = 0; k < NL; k++) gw[k] *= 1.0 - wr;
	gw[FACE] += wr;

	// Heights decide at the edges: the taller material shows. Decided on the
	// heights seen a few mips up, so an edge follows clumps of stones, not
	// each stone: from thirty metres a stone is three pixels, and an edge
	// cut stone by stone reads as a pixelated one.
	const float BLEND_DEPTH = 0.22;
	float hs[NL];
	vec4 arhs[NL];
	float best = 0.0;
	for (int k = 0; k < NL; k++) {
		hs[k] = -1.0;
		if (gw[k] < 0.003) continue;
		mat3 tbn;
		vec2 uv = g_uv(k, w_pos, n_geo, tbn);
		Pick pk = pick(uv, w, k);
		arhs[k] = tex2(g_arh, uv, k, pk);
		Pick coarse = pk;
		coarse.dx *= 12.0;
		coarse.dy *= 12.0;
		float hb = tex2(g_arh, uv, k, coarse).b;
		hs[k] = gw[k] + mix(arhs[k].b, hb, 0.75) * BLEND_DEPTH;
		best = max(best, hs[k]);
	}
	float tot = 0.0;
	for (int k = 0; k < NL; k++) {
		gw[k] = hs[k] < 0.0 ? 0.0 : max(hs[k] - best + BLEND_DEPTH, 0.0);
		tot += gw[k];
	}
	vec3 albedo = vec3(0.0);
	vec3 n_w = vec3(0.0);
	float rough = 0.0, ao = 0.0, hgt = 0.0, H = 0.0;
	for (int k = 0; k < NL; k++) {
		float wk = gw[k] / tot;
		if (wk < 0.004) continue;
		mat3 tbn;
		vec2 uv = g_uv(k, w_pos, n_geo, tbn);
		Pick p = pick(uv, w, k);
		vec4 arh = arhs[k];
		vec3 a = tex2(g_alb, uv, k, p).rgb;
		float la = dot(a, vec3(0.2126, 0.7152, 0.0722));
		a *= pow(max(la, 1e-4) / g_mean[k], g_con[k] - 1.0);
		a = mix(vec3(dot(a, vec3(0.2126, 0.7152, 0.0722))), a, g_sat[k]);
		albedo += a * g_tone[k] * wk;
		H += wk * (g_lift[k] + (arh.b - 0.5) * g_bump[k]);
		n_w += tbn * nor2(uv, k, p) * wk;
		rough += arh.g * wk;
		ao += arh.r * wk;
		hgt += arh.b * wk;
	}
	vec3 n = normalize(n_w);

	// Slow variation over tens of metres, so a field is never one colour.
	albedo *= 0.78 + 0.3 * nL.r;
	albedo = mix(albedo, albedo * vec3(1.04, 1.0, 0.9), smoothstep(0.55, 0.8, nL.b) * 0.4);

	// Moss grows in clumps, each a little dome: lit on top, dark in the
	// creases between, its own green from yellow to deep. Domes at two sizes
	// (a hand, a forearm) read as moss from thirty metres up; a flat green
	// reads as paint. The clumps break its edge, and it takes the hollows first.
	vec4 s3 = texture(splat3, suv);
	float mo = 0.0;
	if (s3.r > 0.02) {
		vec2 ca = w * 7.5, cb = w * 2.6;
		vec2 ia = floor(ca), fa = fract(ca), ib = floor(cb), fb = fract(cb);
		float da = 8.0, db = 8.0;
		vec2 ra = vec2(0.0), rb = vec2(0.0), ha = vec2(0.0), hb = vec2(0.0);
		for (int j = -1; j <= 1; j++)
			for (int i = -1; i <= 1; i++) {
				vec2 g = vec2(float(i), float(j));
				vec2 pa = hash2(ia + g), pb = hash2(ib + g + 31.0);
				vec2 qa = g + pa - fa, qb = g + pb - fb;
				float a2 = dot(qa, qa), b2 = dot(qb, qb);
				if (a2 < da) { da = a2; ra = qa; ha = pa; }
				if (b2 < db) { db = b2; rb = qb; hb = pb; }
			}
		float dome = (1.0 - clamp(da, 0.0, 1.0)) * 0.6 + (1.0 - clamp(db, 0.0, 1.0)) * 0.4;
		mo = smoothstep(0.45, 0.6, s3.r + (nM.g - 0.5) * 0.28 + (dome - 0.55) * 0.35 + (0.5 - hgt) * 0.12);
		vec3 mc = moss_color * mix(vec3(1.25, 1.1, 0.6), vec3(0.8, 1.0, 0.95), hb.x) * (0.75 + 0.5 * ha.y);
		mc *= 0.3 + 0.8 * dome;
		albedo = mix(albedo, mc, mo);
		rough = mix(rough, 0.95, mo);
		// A cushion stands a hand high, each dome a little higher.
		H = mix(H, H + 0.05 + 0.06 * dome, mo);
		// The domes' slopes, toward the light and away from it.
		n = normalize(mix(n, normalize(n_geo - vec3(ra.x + rb.x * 0.6, 0.0, ra.y + rb.y * 0.6) * 0.9), mo * 0.85));
	}

	// Trodden flat: darker, smoother.
	float trod = s2.b * (0.8 + 0.4 * nF.r);
	albedo *= 1.0 - 0.22 * trod;
	rough = mix(rough, rough * 0.85, trod);
	H -= 0.03 * trod;

	// Standing water: in the low parts of the material first, then over it;
	// dark, near mirror-smooth, flat, holding the moon.
	float wet = clamp(s2.r * 1.25 - hgt * 0.45 + (nM.g - 0.5) * 0.25, 0.0, 1.0);
	float pool = smoothstep(0.45, 0.75, wet);
	albedo *= mix(1.0, 0.55, smoothstep(0.0, 0.5, wet));
	albedo = mix(albedo, albedo * wet_tint * 1.4, pool);
	rough = mix(rough, 0.06, pool);
	rough = mix(rough, rough * 0.55, smoothstep(0.1, 0.45, wet));
	// Standing water lies level, whatever the ground under it does (a level face holds the
	// moon in one place; a tilted one slides a white streak down the bank).
	n = normalize(mix(n, vec3(0.0, 1.0, 0.0), pool * 0.92));
	// Water lies level, below its banks.
	H = mix(H, -0.06, pool);

	// The macro relief's slopes, from how the height changes pixel to pixel
	// (Mikkelsen's bump mapping by derivatives), tilting the ground's normal.
	vec3 dpx = dFdx(w_pos), dpy = dFdy(w_pos);
	float hx = dFdx(H) * relief, hy = dFdy(H) * relief;
	vec3 r1 = cross(dpy, n_geo), r2 = cross(n_geo, dpx);
	float det = dot(dpx, r1);
	vec3 grad = sign(det) * (hx * r1 + hy * r2);
	vec3 nb = normalize(abs(det) * n_geo - grad);
	n = normalize(n + (nb - n_geo));

	// The scar's lip. Coming out from the fight: the ground heat-killed, browned
	// and greyed; then the char, black, split into plates with grey ash lying
	// in drifts; then, just past where she can stand, one thin burning line,
	// wandering and broken like the edge of a burning page, a few veins of it
	// creeping back into the char and coals strewn outward as it cools into
	// the dark. Only the line and its veins glow: the ring frames the fight
	// and marks its edge, and never reads as a field of fire or an amber
	// telegraph.
	float ch = s2.g;
	float inn = w_inn + (nM.r - 0.5) * 2.2 + (nF.g - 0.5) * 0.25;
	float scorch = 1.0 - smoothstep(2.0 * scorch_reach / 11.0, scorch_reach, inn + (nL.g - 0.5) * 7.0 * scorch_reach / 11.0);
	float lum0 = dot(albedo, vec3(0.2126, 0.7152, 0.0722));
	albedo = mix(albedo, vec3(lum0) * vec3(1.05, 0.9, 0.74) * 0.72, scorch * 0.8);
	float charred = smoothstep(0.15, 0.6, ch + (nF.b - 0.5) * 0.3);
	vec3 glow = vec3(0.0);
	float breathe = 0.65 + 0.35 * sin(TIME * 0.9 + nL.r * 9.0) * sin(TIME * 0.37 + nM.b * 5.0);
	// (Sampled and differentiated before the branch: neither is defined inside one.)
	float px = max(fwidth(w.x), fwidth(w.y)) * 0.62;
	float n_on = texture(noise_tex, w * 0.045 + 0.13).g;
	float n_vein = texture(noise_tex, w * 0.21 + 0.57).r;
	// Metres to the lip's line, true: the noise that makes it wander also
	// flattens its slope in places, and a line drawn on the raw value swells
	// there into pools. Divided by its slope, it keeps its width.
	float d = inn + lip_at;
	mat2 jw = mat2(dFdx(w), dFdy(w));
	vec2 gd = vec2(dFdx(d), dFdy(d));
	float dslope = abs(determinant(jw)) > 1e-9 ? length(inverse(transpose(jw)) * gd) : 1.0;
	float dl = d / clamp(dslope, 0.2, 3.0);
	if (charred > 0.001 || inn < 3.0) {
		// Plates about a metre and a half across, their borders split dark.
		vec3 pl = plates(w * 0.62 + (nM.ba - 0.5) * 0.8);
		float seam = 1.0 - smoothstep(0.0, max(0.035, px * 1.2), pl.x);
		// The ground burned where it lay: its own grain kept (the turf's tussocks,
		// the road's stones, black), each plate a shade of its own, and ash
		// drifted grey across them by the wind in broad soft drifts.
		float grain = clamp(lum0 * 11.0, 0.35, 1.6);
		float ash = smoothstep(0.5, 0.82, nM.a * 0.65 + nL.b * 0.35) * (1.0 - hgt * 0.4);
		vec3 coal = vec3(0.02, 0.017, 0.015) * grain * (0.85 + 0.3 * pl.y);
		// Ash: grey, broken by the ground's own grain and the plates' seams, never a flat
		// sheet (under the ring's red lights a flat pale drift reads as orange paint).
		float abreak = smoothstep(0.3, 0.7, nF.r * 0.6 + pl.y * 0.4);
		coal = mix(coal, vec3(0.045, 0.044, 0.042) * grain * (0.6 + 0.5 * abreak), ash * 0.6);
		coal *= 1.0 - seam * 0.45;
		albedo = mix(albedo, coal, charred * 0.94);
		rough = mix(rough, mix(0.9, 0.98, ash), charred);
		// The line: a white-hot thread a few fingers wide in a red breath,
		// broken where the noise along it dips.
		float on = smoothstep(0.32, 0.55, n_on + (nF.r - 0.5) * 0.2);
		float core = 0.035 + 0.05 * nF.b;
		float line = (1.0 - smoothstep(core * 0.5, core + px * 0.7, abs(dl))) * on;
		float halo = exp(-abs(dl) / 0.22) * on;
		// Veins: plate seams lit near the line, a metre in and a few out, sparse.
		float near = exp(-max(d, 0.0) * 1.8) * exp(min(d, 0.0) * 0.5);
		float vein = (1.0 - smoothstep(0.0, max(0.018, px), pl.x)) * near
			* smoothstep(0.5, 0.72, n_vein + (pl.y - 0.5) * 0.4);
		// Coals strewn outward, going out the further they lie.
		vec2 cg = floor(w * 1.7);
		vec2 ch2 = hash2(cg + 7.3);
		float cd = length(fract(w * 1.7) - 0.25 - ch2 * 0.5);
		float spark = step(0.88, hash2(cg + 1.9).x) * (1.0 - smoothstep(0.03, 0.08 + px, cd / 1.7))
			* (1.0 - smoothstep(-1.0, 0.0, d)) * exp(min(d, 0.0) * 0.35);
		float flick = 0.6 + 0.4 * sin(TIME * (1.5 + ch2.x * 2.0) + ch2.y * 30.0);
		vec3 white = mix(ember, vec3(1.0, 0.85, 0.55), 0.55);
		glow += (white * line * 2.4 * lip_glow * lip_glow + ember * (halo * 0.5 * lip_glow + vein * 0.9 + spark * 1.4 * flick)) * breathe * ember_glow;
	}
	// A hotter place than the ring (a pit's mouth, char past 0.85) glows whole.
	float hot = smoothstep(0.87, 1.0, ch);
	float crack = pow(1.0 - abs(nF.r * 2.0 - 1.0), 28.0);
	glow += ember * hot * (0.5 + 0.8 * crack) * breathe * ember_glow;

	// Moon through the leaves, in pools.
	if (dapple > 0.0) {
		float leaves = texture(noise_tex, w * 0.022 + vec2(TIME * 0.002, TIME * 0.0012)).g * 0.75 + texture(noise_tex, w * 0.09 - vec2(TIME * 0.004, 0.0)).b * 0.25;
		// In a clearing (splat3 A) the moon comes down whole: a pool of it, the canopy's
		// shade all round.
		albedo *= mix(mix(1.0, mix(0.45, 1.4, smoothstep(0.4, 0.62, leaves)), dapple), 1.35, s3.a);
	}

	// Past the ring the night closes in: the place goes on, darker.
	float past = 1.0 - smoothstep(0.0, 1.0, w_in);
	albedo *= 1.0 - 0.6 * past;

	ALBEDO = albedo;
	ROUGHNESS = clamp(rough, 0.04, 1.0);
	AO = mix(1.0, ao, 0.85);
	AO_LIGHT_AFFECT = 0.25;
	SPECULAR = mix(0.35, 0.6, pool);
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	// Standing water gives the sky back, broken by the wind on it.
	float ripple = texture(noise_tex, w * 0.35 + vec2(TIME * 0.02, -TIME * 0.013)).g;
	glow += sheen * sheen_amount * pool * (0.55 + 0.9 * ripple) * (1.0 - charred);
	// The slurry's own light, faint, swirling slowly in it.
	float swirl = texture(noise_tex, w * 0.16 + vec2(TIME * 0.006, -TIME * 0.009)).r;
	// Drawn out in threads and curls, not laid flat: a flat sheet of it reads as paint.
	float rn = texture(noise_tex, w * 0.23 + vec2(TIME * 0.008, -TIME * 0.011) + swirl * 0.35).r;
	float thr = pow(1.0 - abs(rn * 2.0 - 1.0), 10.0) * (0.35 + 0.65 * smoothstep(0.4, 0.7, swirl));
	glow += slurry * slurry_glow * s3.g * smoothstep(0.3, 0.8, wet) * (0.05 + 1.4 * thr) * (1.0 - charred);
	// Foxfire: specks of cold light on rotting wood and roots, a few in a cluster, each
	// breathing slowly on its own; from thirty metres up, a faint scatter of pale green
	// stars along the banks' feet.
	if (s3.b > 0.02) {
		vec2 fc = floor(w * 4.0);
		vec2 fh = hash2(fc + 3.7);
		float fd = length(fract(w * 4.0) - 0.2 - fh * 0.6);
		float speck = step(0.62, hash2(fc + 8.1).x) * (1.0 - smoothstep(0.04, 0.12 + px * 4.0, fd));
		float clump = smoothstep(0.45, 0.7, nM.r * 0.6 + nF.b * 0.4);
		float pulse = 0.55 + 0.45 * sin(TIME * (0.4 + fh.x * 0.5) + fh.y * 20.0);
		glow += fox_color * fox_glow * speck * clump * pulse * smoothstep(0.1, 0.6, s3.b);
	}
	EMISSION = glow;
}

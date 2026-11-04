// An ember arena's value masses (H2 R2 round 2, bible rules 5 and 6), shared by its ground
// (arena_ground.gdshader) and the leaves lying on it (arena_leaves.gdshader), so a leaf sits in
// the same mass as the litter under it. A ground photograph tiles every two or three metres and
// cannot carry masses five to thirty metres across: they are authored here, relative to the
// arena's shape (inn: metres inside its ring), never world noise alone, so the board H1 lays on
// the floor (walls, cover, lamps) sits on a floor that reads as one: the fighting floor a lighter,
// warm-ready mass in two or three soft plateaus, the banks toward the ring a step darker.
// np: the noise at w * 0.0085 + (0.41, 0.17) (its G: blobs fifteen to thirty metres across);
// nl: the ground's slow noise at w * 0.011. Returns the albedo's multiplier.
vec3 arena_mass(float inn, vec4 np, vec4 nl) {
	// The banks: the last dozen metres in, a step darker, the step's edge wandering a few metres.
	float floor_in = smoothstep(4.0, 16.0, inn + (nl.b - 0.5) * 9.0 + (np.r - 0.5) * 6.0);
	// The floor's plateaus: three values, soft edged, the lighter ones gathering toward the middle.
	float t = np.g + 0.2 * smoothstep(12.0, 50.0, inn) - 0.1;
	float lv = smoothstep(0.36, 0.5, t) + smoothstep(0.56, 0.7, t);
	// (Centred under 1, 0.93 on the middle plateau, 0.8 on the dark one: lighter overall, the ember's pool lost its key over the floor.)
	// (r2 w5: the dark plateau 0.74 and the light ones drawn further to the middle, where she fights: 09's key had
	// dropped to 1.92 under the bible's 2.0 once the leaves stopped being black chips on the moonlit litter.)
	float v = mix(0.8, 1.0, floor_in) * mix(0.74, 1.06, lv * 0.5 * floor_in);
	// The lighter plateaus a touch warm: ready for the ember's pool and the lamps.
	vec3 warm = mix(vec3(1.0), vec3(1.035, 1.0, 0.94), lv * 0.5 * floor_in);
	return v * warm;
}

// A surface cut to what covers it (hair's strands, lashes) by a threshold that
// moves every frame (src/Game/MotionClock.cs counts the frames), so a temporal
// smoothing (FSR 2, TAA) sums the frames' cuts into the true coverage: soft where
// the alpha is soft, and still. Godot's own hashed alpha keeps one threshold for
// each point of the surface: noise that stands still, which FSR 2 cannot average
// away and TAA only blurs; alpha to coverage needs MSAA.
global uniform float motion_frame;

// The threshold at this pixel this frame: interleaved gradient noise (an even
// scatter in any one frame), moved on by the golden ratio each frame (so each
// pixel runs evenly through 0..1 over the frames).
float coverage_cut(vec2 frag) {
	float ign = fract(52.9829189 * fract(dot(frag, vec2(0.06711056, 0.00583715))));
	return fract(ign + motion_frame * 0.61803398875);
}

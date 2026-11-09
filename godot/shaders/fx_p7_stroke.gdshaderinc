// The painted stroke (P7, 9 Nov): every P7 light shape draws through p7_stroke, which is now L1's primitive
// fx_stroke (fx_cel.gdshaderinc, fx-lang@a278b6482: three bands across the width, the dry-brush edge, the life curve;
// read its header). This wrapper only adapts P7's conventions:
//   across  -1..1 where |across| = 1 is the stroke's outer edge at its head (P7's shapes were sized so); fx_stroke's
//           head half-width is fx_stroke_shape.x, so across is scaled by it.
//   life    stepped per sample here (0, 1/3, 2/3, 1 -> whole, core gone, gold gone, dead), as FX_LANGUAGE §4 asks of
//           the caller.
// Per material: fx_stroke_seed (each instance its own bristles) and fx_bristle.x (about one bristle per 2-4 px of the
// stroke's width at the play camera), set by BattleFx.P7Brush. The stand-in body it replaced is in git history
// (456025e87..f465d3e95); its p7_sw / p7_sseed are gone (the wedge's taper is fx_stroke_shape.z, the seed
// fx_stroke_seed).
// Needs fx_cel.gdshaderinc included first.

vec4 p7_stroke(float across, float along, float life) {
	float lf = floor(clamp(life, 0.0, 1.0) * 3.0 + 1e-4) / 3.0;
	return fx_stroke(across * fx_stroke_shape.x, along, lf);
}

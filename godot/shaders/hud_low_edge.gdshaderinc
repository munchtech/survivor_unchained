// HUD "her life" low-life edge (hud_low_edge.gdshader multiplies, hud_low_edge_glow.gdshader adds): the shared falloff.
uniform float strength = 0.0;   // HeartPulse.EdgeStrength: 0 off, 0.3 at 30%, 1 at none
uniform float beat = 0.0;       // the heartbeat now, 0..1 (1 on the beat)

float edge_a(vec2 uv)
{
	vec2 q = abs(uv - 0.5) * 2.0;           // 0 at the middle, 1 at the edges
	float d = pow(pow(q.x, 4.0) + pow(q.y, 4.0), 0.25);
	float s = clamp(strength, 0.0, 1.0);
	// its inner edge creeps in with strength and on the beat, never past 0.70
	float start = mix(0.86, 0.70, s * (0.75 + 0.25 * beat));
	float ramp = smoothstep(start, 1.12, d);
	return clamp(ramp * s * (0.62 + 0.35 * beat), 0.0, 0.9);
}

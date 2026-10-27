// HUD variant "her life" (--hud-life her, HerLight.cs): at 30% of her life and under, the screen's edges darken
// to a deep blood red that beats with her heart (HeartPulse: the sound's own pacing). Subtle at 30%, stronger
// toward none; it never reaches into the middle 70% of the screen (a rounded square, |x| and |y| under 0.70 of
// the half-screen stay clear). One full-screen quad, a few ALU ops.
shader_type canvas_item;
render_mode blend_mix;

uniform float strength = 0.0;   // HeartPulse.EdgeStrength: 0 off, 0.3 at 30%, 1 at none
uniform float beat = 0.0;       // the heartbeat now, 0..1 (1 on the beat)
uniform vec4 blood : source_color = vec4(0.38, 0.03, 0.02, 1.0);

void fragment()
{
	vec2 q = abs(UV - 0.5) * 2.0;           // 0 at the middle, 1 at the edges
	float d = pow(pow(q.x, 4.0) + pow(q.y, 4.0), 0.25);
	float s = clamp(strength, 0.0, 1.0);
	// its inner edge creeps in with strength and on the beat, never past 0.70
	float start = mix(0.86, 0.70, s * (0.75 + 0.25 * beat));
	float ramp = smoothstep(start, 1.12, d);
	float a = ramp * s * (0.62 + 0.35 * beat);
	if (a <= 0.002) discard;
	COLOR = vec4(blood.rgb, clamp(a, 0.0, 0.88));
}

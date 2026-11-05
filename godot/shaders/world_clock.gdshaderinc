// The world's own clock (H7, FLARE_LOOK §1.2: in a Flare's stop the world truly holds, not crawls).
// Every world material (ground, terrain, grass, kit, water, fire, mist, the crowd) animates on
// WORLD_TIME, not the engine's TIME: src/Game/MotionClock.cs advances it each draw by the frame's
// step times the world's rate (FlareFx.WorldRate in a Flare, 1 outside one). Her, her hair and
// cloth, the Flare's own shaders, the marks and the UI keep TIME and stay alive.
// The motion vectors' look back at last frame (motion.gdshaderinc) takes last draw's world time.
#ifndef WORLD_CLOCK_INC
#define WORLD_CLOCK_INC
#include "res://shaders/motion.gdshaderinc"
global uniform float world_time;
global uniform float world_time_was;
float world_clock(float time) {
	return last_frame(time) ? world_time_was : world_time;
}
#define WORLD_TIME world_clock(TIME)
#endif

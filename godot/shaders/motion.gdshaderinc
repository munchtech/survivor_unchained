// Where a point was last frame, for the motion vectors the temporal smoothing
// follows. Godot runs a material's vertex stage a second time to know how each
// point moved, with last frame's TIME, transform and skinning, but with this
// frame's uniforms. A shape moved by values code sets each frame (her hair's
// swing) takes last frame's values, given beside this frame's, in that run:
// its TIME is the earlier, below `motion_then` (src/Game/MotionClock.cs).
global uniform float motion_then;

// True in the run that looks back at last frame (pass it TIME).
bool last_frame(float time) {
	return time < motion_then;
}

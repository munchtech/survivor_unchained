extends SceneTree
# Each resource the game loaded (in its order, from a --verbose log), timed one by one.
# Dependencies load with what needs them, so each time includes what it brought in.
const LIST := "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/perf2/load_list.txt"
const OUT := "C:/Users/munch/AppData/Local/Temp/claude/C--Users-munch-Desktop-wowsurvivors/f1b9be14-0826-4f47-8004-f1d371f2c6a3/scratchpad/perf2/load_times.txt"
var frame := 0
func _process(_d):
	frame += 1
	if frame != 5:
		return false
	var f := FileAccess.open(LIST, FileAccess.READ)
	var out := FileAccess.open(OUT, FileAccess.WRITE)
	var total := 0
	while not f.eof_reached():
		var p := f.get_line().strip_edges()
		if p == "" or p.ends_with(".cs") or p.begins_with("res://.godot") or p.ends_with(".tscn"):
			continue
		if ResourceLoader.has_cached(p):
			continue
		var t := Time.get_ticks_usec()
		var r = load(p)
		var dt := Time.get_ticks_usec() - t
		total += dt
		out.store_line("%d\t%s" % [dt / 1000, p])
	out.store_line("%d\tTOTAL" % [total / 1000])
	out.close()
	quit()
	return false

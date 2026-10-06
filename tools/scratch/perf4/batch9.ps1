# Batch 9 (one Godot turn), after merging the integration branch: the import
# (her rebuilt outfits, new icons); the dense fight before and after the names
# made once (garbage by type; the draft's first showing with the frames read
# at start); loot's ground labels and her outfits flipped; the town entered
# again with its people's models kept.
$ScratchDir = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf4"
$TreeDir = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a0eb8c612c94d4aa5"
$TurnScript = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$TurnHolder = "performance: import, names, loot labels, her outfits, town re-entry"
$GodotConsole = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
$BinDir = "$TreeDir\godot\.godot\mono\temp\bin\Debug"
python $TurnScript take godot $TurnHolder --wait 30
if ($LASTEXITCODE -ne 0) { "NO TURN"; exit 1 }
try {
    $clock = [Diagnostics.Stopwatch]::StartNew()
    & $GodotConsole --headless --path "$TreeDir\godot" --import *> "$ScratchDir\import9.log"
    "import: exit $LASTEXITCODE, $([int]$clock.Elapsed.TotalSeconds) s"
    python "$TreeDir\tools\perf\run.py" dense --repeat 2 --wait 0 --tag names --builds "lab=$ScratchDir\dll_lab,sn=$ScratchDir\dll_sn" -- --perf-allocs 2>&1 | Select-String "^dense \(|interface's frames|perf dense_names.* done|draftui [1-9]|young GC|paused [1-9]|perf alloc .*(StringName|WeakReference|Collections.Array|String$|Vector3\[\]|DisplayClass)"
    "dense done: $([int]$clock.Elapsed.TotalSeconds) s"
    Copy-Item "$ScratchDir\dll_sn\SurvivorUnchained.*" $BinDir -Force
    python "$TreeDir\tools\perf\run.py" dense --wait 0 --tag labflip -- --perf-flip labels 2>&1 | Select-String "perf dense_labflip done"
    python "$TreeDir\tools\perf\flip.py" dense_labflip
    python "$TreeDir\tools\perf\run.py" dense --wait 0 --tag herflip -- --perf-flip her 2>&1 | Select-String "perf dense_herflip done"
    python "$TreeDir\tools\perf\flip.py" dense_herflip
    "flips done: $([int]$clock.Elapsed.TotalSeconds) s"
    python "$TreeDir\tools\perf\run.py" hub --repeat 2 --wait 0 --tag hops3 --builds "lab=$ScratchDir\dll_lab,kit=$ScratchDir\dll_kit" -- --perf-warm 34 --perf-for 2 --travel "verge@6,waystation@14,verge@22,waystation@30" 2>&1 | Select-String "^hub \(|its textures|its people|built in"
    "BATCH RAN: $([int]$clock.Elapsed.TotalSeconds) s"
}
finally {
    python $TurnScript give godot $TurnHolder
}

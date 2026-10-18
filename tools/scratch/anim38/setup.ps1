$W = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a6b5a13d0be70144d"
Set-Location $W
Move-Item "$W\godot\assets" "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\43e8c2e6-36a3-4fd7-8ca4-39c475e24666\scratchpad\a38\assets.placeholder"
cmd /c mklink /J "$W\godot\assets" "$W\public\assets"
git -C $W update-index --skip-worktree godot/assets
robocopy "C:\Users\munch\Desktop\survivorsunchained\godot\.godot" "$W\godot\.godot" /E /NFL /NDL /NJH /NP /R:1 /W:1 | Select-Object -Last 8
python "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\43e8c2e6-36a3-4fd7-8ca4-39c475e24666\scratchpad\a38\sidecars.py"
Set-Location "$W\godot"
dotnet build 2>&1 | Select-Object -Last 3
"SETUP DONE"

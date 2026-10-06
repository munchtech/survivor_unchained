# v7 in one go: every face rewrapped, then the whole build (build_v7.ps1), then the shots and sheets (one godot turn).
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face4'
& "$sc\presets_wrap.ps1" -ids heroine, highborn, vixen, doe, sunborn, moonlit, saffron, wildling, hardwon, fey 2>&1 | Select-String "wrap exit"
& "$sc\build_v7.ps1"


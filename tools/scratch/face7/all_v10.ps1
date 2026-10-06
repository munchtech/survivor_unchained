# v10's whole check, in godot turns one after another: the game clay after the normals, the Look shots of every
# face, the white rig, and the book and play zoom.
$sc = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\face7'
& "$sc\gclay.ps1" -tag g1
& "$sc\shots_v8.ps1" -tag v10 -nocal
& "$sc\shots_white.ps1" -tag v10
& "$sc\shots_book.ps1" -tag bk1
"all v10 done $(Get-Date -Format HH:mm)"

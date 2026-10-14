# Shipped rig: dark irises with the halved pattern; ears at 40; neck lengths by the neck's scale (front, profile, 40).
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$runs = @()
$runs += "nk-1.5_t40|own|--turn 40 --neck-cm -1.5"
& "$SC\look_ab.ps1" -tag t7 -runs $runs
"T6 DONE $(Get-Date -Format HH:mm)"

# k16: play facings (which faces the camera), and the jaw-edge rim with the light through her off
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($d in '0', '90', '180', '270') { $runs += "pf$d|raw|--quick warden --sex female --zone waystation --time day --cam 12 --facing $d" }
foreach ($f in 'doe', 'sunborn') { $runs += "rim_$f|$f|", "rimb0_$f|$f|--skin-set *:backlight=0", "rimsc0_$f|$f|--skin-set *:scatter=0" }
& "$SC\look.ps1" -tag k16 -secs 10 -runs $runs
"K16 DONE $(Get-Date -Format HH:mm)"

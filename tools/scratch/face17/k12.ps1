# k12: key shadow size and height on the bright jaws
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'vixen', 'fey', 'own') { $runs += "s15_$f|$f|--key-shadow 0.15", "up_$f|$f|--key-at 0.55,1.6" }
& "$SC\look.ps1" -tag k12 -secs 10 -runs $runs
"K12 DONE $(Get-Date -Format HH:mm)"

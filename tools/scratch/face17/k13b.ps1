# k13: all ten, soft_tone 0.5 grey (the jaw fit; k8_t is soft 1)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|--skin-set *:soft_tone=0.5/0.5/0.5" }
& "$SC\look.ps1" -tag k13 -secs 10 -runs $runs
"K13 DONE $(Get-Date -Format HH:mm)"

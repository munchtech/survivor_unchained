# k8: all ten, trims k7: -3 cm (s_) and today (t_)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "s_$f|$f|--neck-cm -3", "t_$f|$f|" }
& "$SC\look.ps1" -tag k8 -secs 10 -runs $runs
"K8 DONE $(Get-Date -Format HH:mm)"

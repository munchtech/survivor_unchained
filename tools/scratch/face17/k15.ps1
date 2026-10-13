# k15: trims k14; -3 (s_), today (t_), today soft 0.5 grey (h_)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "s_$f|$f|--neck-cm -3", "t_$f|$f|", "h_$f|$f|--soft-tone 0.5,0.5,0.5" }
& "$SC\look.ps1" -tag k15 -secs 10 -runs $runs
"K15 DONE $(Get-Date -Format HH:mm)"

# k7: all ten at -3 cm with the fitted lifts (for the chroma trims)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|--neck-cm -3" }
& "$SC\look.ps1" -tag k7 -secs 10 -runs $runs
"K7 DONE $(Get-Date -Format HH:mm)"

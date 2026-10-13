# r6b: BodyK 1 with the shade tint by her soft lamps (fill and bounce show her paint's own colour), all ten, for trims.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|" }
& "$SC\look.ps1" -tag r6b -secs 10 -runs $runs
"R6B DONE $(Get-Date -Format HH:mm)"

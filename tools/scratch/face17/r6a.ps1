# r6a: BodyK and the shade gate. Own and Highborn: k 0.5 untinted (shipped), k 1 untinted, k 1 with the shade tint by
# each lamp's own light (default gate 0.8-1.6), the same not held to down-facing, k 1 with the old ndl gate.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'own', 'highborn') {
    $runs += "${f}_k05|$f|--body-k 0.5 --shade-tint off", "${f}_k1|$f|--body-k 1 --shade-tint off", "${f}_k1L|$f|--body-k 1",
        "${f}_k1Lall|$f|--body-k 1 --shade-down off", "${f}_k1N|$f|--body-k 1 --shade-tint ndl"
}
& "$SC\look.ps1" -tag r6a -secs 10 -runs $runs
"R6A DONE $(Get-Date -Format HH:mm)"

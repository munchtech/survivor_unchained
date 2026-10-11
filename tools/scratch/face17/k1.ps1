# k1: the key's cone falloff (SpotAttenuation 0.4 darkens 3-4 degrees off its axis: the lit neck?)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @("own_a04|own|", "own_a1|own|--key-atten 1", "own_a2|own|--key-atten 2", "saffron_a1|saffron|--key-atten 1", "saffron_a2|saffron|--key-atten 2")
& "$SC\look.ps1" -tag k1 -secs 10 -runs $runs
"K1 DONE $(Get-Date -Format HH:mm)"

# k2: the lit neck at -3 cm (are the samples on different anatomy?)
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @("own_n3|own|--neck-cm -3", "saffron_n3|saffron|--neck-cm -3", "doe_n3|doe|--neck-cm -3", "vixen_n3|vixen|--neck-cm -3")
& "$SC\look.ps1" -tag k2 -secs 10 -runs $runs
"K2 DONE $(Get-Date -Format HH:mm)"

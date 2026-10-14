# k3: body_lift and the key cone at -3 and today
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @("own_c35|own|--neck-cm -3 --key-cone 35", "own_l13|own|--neck-cm -3 --body-lift 1.3", "own_l13_0|own|--body-lift 1.3", "saffron_l13|saffron|--neck-cm -3 --body-lift 1.3", "doe_l13|doe|--neck-cm -3 --body-lift 1.3", "vixen_l13|vixen|--neck-cm -3 --body-lift 1.3")
& "$SC\look.ps1" -tag k3 -secs 10 -runs $runs
"K3 DONE $(Get-Date -Format HH:mm)"

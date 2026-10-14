# k4: the key-only body lift
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @("own_l16|own|--neck-cm -3 --body-lift 1.6", "own_l13|own|--neck-cm -3 --body-lift 1.3", "saffron_l16|saffron|--neck-cm -3 --body-lift 1.6", "doe_l16|doe|--neck-cm -3 --body-lift 1.6", "vixen_l16|vixen|--neck-cm -3 --body-lift 1.6", "own_l16_0|own|--body-lift 1.6", "play_l1|raw|--quick warden --sex female --zone waystation --time day --cam 12", "play_l16|raw|--quick warden --sex female --zone waystation --time day --cam 12 --body-lift 1.6")
& "$SC\look.ps1" -tag k4 -secs 10 -runs $runs
"K4 DONE $(Get-Date -Format HH:mm)"

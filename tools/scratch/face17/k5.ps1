# k5: the lift gated by facing
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @("own_g1|own|--neck-cm -3 --body-lift 1.6", "own_g2|own|--neck-cm -3 --body-lift 1.6 --skin-set *:lift_from=-0.15,lift_to=0.15", "vixen_g1|vixen|--neck-cm -3 --body-lift 1.6", "vixen_g2|vixen|--neck-cm -3 --body-lift 1.6 --skin-set *:lift_from=-0.15,lift_to=0.15", "own_g1_0|own|--body-lift 1.6")
& "$SC\look.ps1" -tag k5 -secs 10 -runs $runs
"K5 DONE $(Get-Date -Format HH:mm)"

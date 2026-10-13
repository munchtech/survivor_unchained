# Face 20: is her lower face short, or her head pitched? Own at the Look's front shot, head turned -8..+8 deg.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
foreach ($d in '-10', '-12', '-14') { & "$SC\look.ps1" -tag "hp$d" -secs 10 -runs @("own|own|--head-pitch $d") }
"PITCH2 DONE $(Get-Date -Format HH:mm)"

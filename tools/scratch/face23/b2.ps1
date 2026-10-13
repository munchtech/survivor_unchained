# Skin r12 batch 2: item 1 with the head left as r11 (fk.b gates the graft and body only); hardwon re-shot.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @("own|own|", "fey|fey|", "highborn|highborn|", "own_full|own|--zoom 0", "hardwon|hardwon|--skin-set *:edge_neck=0")
& "$SC\look.ps1" -tag b2 -secs 10 -runs $runs
"B2 DONE $(Get-Date -Format HH:mm)"

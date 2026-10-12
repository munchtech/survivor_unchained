# Skin r12 batch 1: r11 re-shot on the rebuilt body (edge_neck=0), item 1 (edge_tone kept to her neck), and own's
# debug views for (a): the lamps' light by kind (dbg 0.5), her maps (dbg 4), the rim lamp off, the edge lamp off.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$D = '--look-ambient 0 --tonemap linear --grade off --skin-set'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') { $runs += "$f|$f|--skin-set *:edge_neck=0" }
$runs += "own_full|own|--zoom 0 --skin-set *:edge_neck=0", "g_own_full|own|--zoom 0", "g_own|own|", "g_fey|fey|"
$runs += "dbg_own|own|$D *:dbg_gate=0.5", "map_own|own|$D *:dbg_gate=4", "norim_own|own|--rig 1.3,0.22,0.8,0", "noedge_own|own|--rig 1.3,0.22,0,0.55"
& "$SC\look.ps1" -tag b1 -secs 10 -runs $runs
"B1 DONE $(Get-Date -Format HH:mm)"

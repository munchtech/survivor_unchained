# k18: the jaw-edge rim: the terminator's per-channel reach
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @()
foreach ($f in 'doe', 'sunborn') { $runs += "ta_$f|$f|--skin-set *:terminator=0.2/0.15/0.1", "tb_$f|$f|--skin-set *:terminator=0.32/0.25/0.2", "tc_$f|$f|--skin-set *:terminator=0.24/0.19/0.15" }
& "$SC\look.ps1" -tag k18 -secs 10 -runs $runs
"K18 DONE $(Get-Date -Format HH:mm)"

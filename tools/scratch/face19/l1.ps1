# Face 19, batch l1: the lit neck's lift refit on a band at both lengths (lamps behind her take none, fade from -0.45,
# edge lamp at 1.3 m by default), and the ears at 40 degrees with a marker paint (heroine ear/cheek masks).
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$MK = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f19\ear_marker.png'
$runs = @()
foreach ($f in 'own', 'highborn', 'doe', 'sunborn', 'vixen', 'moonlit', 'saffron', 'wildling', 'hardwon', 'fey') {
    $runs += "a3_$f|$f|--neck-cm -3 --body-lift 1", "b3_$f|$f|--neck-cm -3 --body-lift 1.6", "a0_$f|$f|--body-lift 1", "b0_$f|$f|--body-lift 1.6"
    $runs += "e_$f|$f|--turn 40", "m_$f|$f|--turn 40 --head-paint $MK"
}
& "$SC\look.ps1" -tag l1 -secs 10 -runs $runs
"L1 DONE $(Get-Date -Format HH:mm)"

# Skin solver r10, batch a: which term greys/cools her far neck (own at the Look, r9 pose), and her body in the full frame.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @(
  "own|own|", "norim|own|--rig 1.3,0.22,0.8,0", "noedge|own|--rig 1.3,0.22,0,0.55", "bk0|own|--body-k 0",
  "noamb|own|--look-ambient 0", "nobl|own|--skin-set *:backlight=0", "norimt|own|--skin-set *:rim=0", "white|own|--rig-white",
  "full|own|--zoom 0", "full_bk0|own|--zoom 0 --body-k 0")
& "$SC\look.ps1" -tag s10a -secs 10 -runs $runs
"S10A DONE $(Get-Date -Format HH:mm)"

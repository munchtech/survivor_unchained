# The nape fleck at -3 cm: hair off, key shadow off.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$runs = @("nk-3_p|own|--zoom 0.55 --turn 90 --neck-cm -3", "nk-3_p_nohair|own|--zoom 0.55 --turn 90 --neck-cm -3 --hair none", "nk-3_p_noshadow|own|--zoom 0.55 --turn 90 --neck-cm -3 --key-shadow off")
& "$SC\look_ab.ps1" -tag t8 -runs $runs
"T8 DONE"

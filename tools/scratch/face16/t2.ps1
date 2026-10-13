# Irises after one Look gain pass; the light-through-skin term kept to her ears and nose (thin_map): fronts and profiles.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\181eef02-779f-45de-b419-31a949a4d27e\scratchpad\f13'
$runs = @("own_t80|own|--turn 80", "highborn_t80|highborn|--turn 80", "sunborn_t80|sunborn|--turn 80", "own|own|", "highborn|highborn|")
foreach ($f in 'doe', 'sunborn', 'moonlit', 'saffron') { $runs += "$f|$f|" }
& "$SC\look_ab.ps1" -tag t2 -import -runs $runs
"T2 DONE $(Get-Date -Format HH:mm)"

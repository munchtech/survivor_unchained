# k17: the jaw-edge rim: face_tone off (the face mask's edge?), the terminator wider
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @("ft1_doe|doe|--skin-set skin_head:face_tone=1/1/1", "ao0_doe|doe|--skin-set skin_head:ao_light=0")
& "$SC\look.ps1" -tag k17 -secs 10 -runs $runs
"K17 DONE $(Get-Date -Format HH:mm)"

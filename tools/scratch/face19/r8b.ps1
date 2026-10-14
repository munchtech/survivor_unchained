# r8b: Sunborn's under-jaw chroma taken down (heroine_jaw_tone.py sunborn 0.72); Vixen, Moonlit, Fey soft tones back to
# their fits, and their shaded body (under the bust, the inner arm) beside own's, for j6's "not yellow" check.
$SC = 'C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-survivorsunchained\91211d34-e079-4956-a2a0-7b52c04594a8\scratchpad\f18'
$runs = @('sunborn|sunborn|', 'sunborn_t40|sunborn|--turn 40', 'vixen|vixen|', 'moonlit|moonlit|', 'fey|fey|')
foreach ($f in 'own', 'vixen', 'moonlit', 'fey', 'highborn') { $runs += "bust_$f|$f|--zoom 0.55", "bustx_$f|$f|--zoom 0.55 --soft-tone 1,1,1" }
& "$SC\look.ps1" -tag r8b -import -secs 10 -runs $runs
"R8B DONE $(Get-Date -Format HH:mm)"

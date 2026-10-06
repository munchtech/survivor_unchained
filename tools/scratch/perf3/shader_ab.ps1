param([string[]]$Variants = @("orig", "new"), [string[]]$Scenarios = @("dense"), [int]$Repeat = 3, [string]$Tag = "g", [string]$Extra = "")
# Perf runs of the grass shader variants, interleaved (orig, new, orig, new...)
# so a busy GPU weighs on both alike. Ends with the 'new' shader in place.
$S = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad\perf3"
$W = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-a56abaf3a104be675"
foreach ($r in 1..$Repeat) {
    foreach ($v in $Variants) {
        python "$S\shader_variants.py" use $v | Out-Null
        foreach ($sc in $Scenarios) {
            $args = @("$W\tools\perf\run.py", $sc, "--tag", "$Tag$v$r", "--wait", "0")
            if ($Extra -ne "") { $args += @("--") + $Extra.Split(" ") }
            python @args 2>&1 | Select-String -Pattern "GPU before|^ *(run|$sc)" | ForEach-Object { $_.Line }
        }
    }
}
python "$S\shader_variants.py" use new | Out-Null
"AB DONE"

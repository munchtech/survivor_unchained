$turn = "C:/Users/munch/Desktop/survivorsunchained/tools/turn.py"
$job = "ui art: three item icons repainted"
$scr = "C:\Users\munch\AppData\Local\Temp\claude\C--Users-munch-Desktop-wowsurvivors\f1b9be14-0826-4f47-8004-f1d371f2c6a3\scratchpad"
$deadline = (Get-Date).AddMinutes(90)
while ((Get-Date) -lt $deadline) {
    python $turn take gpu $job
    if ($LASTEXITCODE -eq 0) {
        "took the gpu turn at $(Get-Date)"
        try { python "$scr\uiart_paint3.py" } finally { python $turn give gpu $job; "gave it back at $(Get-Date)" }
        exit 0
    }
    Start-Sleep -Seconds 60
}
"no turn within 90 minutes"
exit 1

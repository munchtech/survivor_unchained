# Wait until there is room in memory, then import the project; retry a crashed import.
$wt = "C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-aa9c11f1e40170a4d"
$g = "C:\Users\munch\Desktop\Godot_v4.5.1-stable_mono_win64\Godot_v4.5.1-stable_mono_win64_console.exe"
for ($try = 1; $try -le 6; $try++) {
    while ($true) {
        $os = Get-CimInstance Win32_OperatingSystem
        $free = $os.FreeVirtualMemory / 1MB
        if ($free -gt 12) { break }
        Start-Sleep 20
    }
    $t = Get-Date
    & $g --headless --path "$wt\godot" --import *> "$env:TEMP\su_import_w.log"
    $code = $LASTEXITCODE
    $crash = Select-String -Path "$env:TEMP\su_import_w.log" -Pattern "CrashHandlerException" -Quiet
    "try $try exit $code crash $crash took $((Get-Date) - $t)"
    if (-not $crash) { break }
}

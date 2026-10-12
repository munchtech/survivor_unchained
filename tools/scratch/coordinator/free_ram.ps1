# Pause the PC's background apps to give RAM and VRAM to game work, and bring them back after.
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/free_ram.ps1 status
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/free_ram.ps1 pause [-Browser]
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/free_ram.ps1 resume
# pause closes the apps in $Pausable (Chrome only with -Browser) and records what it closed;
# resume reopens exactly those. Pause also clears leftovers nothing needs back: monitor tails older
# than 12 hours from finished sessions, and the idle C# compiler server (only when no build or test runs).
# Never touched: Defender, the firewall, Windows services, L-Connect (fan curves), NVIDIA, audio,
# Claude, Godot, Blender, Python/ComfyUI. Add an app to $Pausable only if it isn't one of those.
param([ValidateSet('status', 'pause', 'resume')][string]$Mode = 'status', [switch]$Browser)
$ErrorActionPreference = 'Continue'
$state = Join-Path $env:LOCALAPPDATA 'SurvivorUnchained\paused_apps.json'

# name = process name; start = how to reopen it (empty: the path it ran from)
$Pausable = @(
    @{ name = 'Discord'; start = "$env:LOCALAPPDATA\Discord\Update.exe|--processStart Discord.exe" }
    @{ name = 'ShareX'; start = '' }
)  # DisplayFusion is left out: Windows denies closing it without admin rights
if ($Browser) { $Pausable += @{ name = 'chrome'; start = '' } }

function Show-Free {
    $os = Get-CimInstance Win32_OperatingSystem
    $v = (& nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>$null) -split ','
    $line = 'RAM free {0:N1} of {1:N1} GB' -f ($os.FreePhysicalMemory / 1MB), ($os.TotalVisibleMemorySize / 1MB)
    if ($v.Count -eq 2) { $line += ' | VRAM free {0:N1} of {1:N1} GB' -f (($v[1] - $v[0]) / 1KB), ($v[1] / 1KB) }
    $line
}
function Get-StaleTails {
    Get-CimInstance Win32_Process -Filter "Name='tail.exe'" |
        Where-Object { $_.CommandLine -match 'Temp/claude' -and $_.CreationDate -lt (Get-Date).AddHours(-12) }
}

if ($Mode -eq 'status') {
    Show-Free
    foreach ($n in @($Pausable.name) + 'chrome' | Select-Object -Unique) {
        $ps = @(Get-Process -Name $n -ErrorAction SilentlyContinue)
        if ($ps.Count) { '  {0,-14} {1,5:N2} GB  pausable{2}' -f $n, (($ps | Measure-Object WorkingSet64 -Sum).Sum / 1GB), $(if ($n -eq 'chrome' -and -not $Browser) { ' with -Browser' }) }
    }
    $t = @(Get-StaleTails); if ($t.Count) { "  $($t.Count) stale monitor tails from finished sessions" }
    if (Test-Path $state) { "Paused now: $((Get-Content $state -Raw | ConvertFrom-Json).name -join ', '). Run resume to bring them back." }
    return
}

if ($Mode -eq 'pause') {
    'Before: ' + (Show-Free)
    $closed = @(); if (Test-Path $state) { $closed = @(Get-Content $state -Raw | ConvertFrom-Json) }
    foreach ($a in $Pausable) {
        $ps = @(Get-Process -Name $a.name -ErrorAction SilentlyContinue)
        if (-not $ps.Count) { continue }
        $path = ($ps | Where-Object { $_.Path } | Select-Object -First 1).Path
        $start = if ($a.start) { $a.start } else { $path }
        $ps | ForEach-Object { [void]$_.CloseMainWindow() }      # let it save (Chrome keeps its tabs)
        Start-Sleep -Seconds 3
        # Tray apps (Discord, DisplayFusion) only hide on close, and Discord's main process respawns
        # its children, so end the whole tree with taskkill and wait for it to go.
        $err = ''
        for ($i = 0; $i -lt 10 -and (Get-Process -Name $a.name -ErrorAction SilentlyContinue); $i++) {
            $err = (& taskkill /F /T /IM "$($a.name).exe" 2>&1 | Out-String).Trim()
            Start-Sleep -Seconds 1
        }
        if (Get-Process -Name $a.name -ErrorAction SilentlyContinue) { "  could not close $($a.name): $err"; continue }
        if ($start -and -not ($closed | Where-Object { $_.name -eq $a.name })) { $closed += [pscustomobject]@{ name = $a.name; start = $start } }
        "  paused $($a.name)"
    }
    $t = @(Get-StaleTails); $t | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if ($t.Count) { "  cleared $($t.Count) stale monitor tails" }
    $busy = Get-CimInstance Win32_Process -Filter "Name='dotnet.exe'" | Where-Object { $_.CommandLine -match '\b(build|test|run|msbuild|vstest)\b' }
    if (-not $busy) { & dotnet build-server shutdown *> $null; '  stopped the idle C# compiler server (it restarts on the next build)' }
    if ($closed.Count) { New-Item -ItemType Directory -Force (Split-Path $state) | Out-Null; ConvertTo-Json @($closed) | Set-Content -Encoding utf8 $state }
    Start-Sleep -Seconds 2
    'After:  ' + (Show-Free)
    return
}

if ($Mode -eq 'resume') {
    if (-not (Test-Path $state)) { 'Nothing paused.'; return }
    foreach ($a in @(Get-Content $state -Raw | ConvertFrom-Json)) {
        if (Get-Process -Name $a.name -ErrorAction SilentlyContinue) { "  $($a.name) already running"; continue }
        $exe, $arg = $a.start -split '\|', 2
        if (-not (Test-Path -LiteralPath $exe)) { "  can't find $exe for $($a.name); open it by hand"; continue }
        if ($arg) { Start-Process -FilePath $exe -ArgumentList $arg } else { Start-Process -FilePath $exe }
        "  reopened $($a.name)"
    }
    Remove-Item $state
}

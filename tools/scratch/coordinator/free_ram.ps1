# Pause the PC's background apps to give RAM and VRAM to game work, and bring them back after.
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/free_ram.ps1 status
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/free_ram.ps1 pause [-Browser]
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/scratch/coordinator/free_ram.ps1 resume
# pause records each app's command line and whether it ran as admin; resume reopens it the same way.
# An app that really runs as admin is closed and reopened through Windows' admin prompt (none of the
# current list does: Discord's launcher drops the shortcut's admin flag). Pause also clears leftovers
# nothing needs back: monitor tails older than 12 hours from finished sessions, and the idle C# compiler server.
# Never touched: Defender, the firewall, Windows services, L-Connect (fan curves), NVIDIA, audio,
# Claude, Godot, Blender, Python/ComfyUI. Add an app to $Pausable only if it isn't one of those.
param([ValidateSet('status', 'pause', 'resume')][string]$Mode = 'status', [switch]$Browser)
$ErrorActionPreference = 'Continue'
$dir = Join-Path $env:LOCALAPPDATA 'SurvivorUnchained'
$state = Join-Path $dir 'paused_apps.json'

# name = process name; start = how to reopen it, "exe|args" (empty: the command line it ran with)
$Pausable = @(
    @{ name = 'Discord'; start = "$env:LOCALAPPDATA\Discord\Update.exe|--processStart Discord.exe" }  # app-x.y.z path changes on update
    @{ name = 'ShareX'; start = '' }
)  # DisplayFusion is left out: it guards itself, and Windows refuses to close it
if ($Browser) { $Pausable += @{ name = 'chrome'; start = '' } }

Add-Type -Namespace SU -Name Tok -MemberDefinition @'
[DllImport("kernel32.dll")] static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
[DllImport("advapi32.dll")] static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
[DllImport("advapi32.dll")] static extern bool GetTokenInformation(IntPtr token, int cls, out int value, int len, out int ret);
[DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
// 1 = runs as admin, 0 = normal, -1 = can't tell
public static int Elevated(int pid) {
    IntPtr p = OpenProcess(0x1000, false, pid); if (p == IntPtr.Zero) return -1;
    IntPtr t; int v = -1, r;
    if (OpenProcessToken(p, 8, out t)) { if (!GetTokenInformation(t, 20, out v, 4, out r)) v = -1; CloseHandle(t); }
    CloseHandle(p); return v;
}
'@
$iAmAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

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
# The app's top process (its parent isn't the same app): its command line, split into exe and args.
function Get-MainProcess($name) {
    $all = @(Get-CimInstance Win32_Process -Filter "Name='$name.exe'")
    $ids = $all.ProcessId
    $main = $all | Where-Object { $ids -notcontains $_.ParentProcessId } | Select-Object -First 1
    if (-not $main) { return $null }
    $cl = "$($main.CommandLine)".Trim()
    if ($cl -match '^"([^"]+)"\s*(.*)$' -or $cl -match '^(\S+)\s*(.*)$') { $exe, $arg = $Matches[1], $Matches[2] } else { $exe, $arg = $main.ExecutablePath, '' }
    if (-not $exe) { $exe = $main.ExecutablePath }
    [pscustomobject]@{ id = $main.ProcessId; start = "$exe|$arg"; admin = ([SU.Tok]::Elevated($main.ProcessId) -ne 0) }  # unreadable token: it's admin and we aren't
}

if ($Mode -eq 'status') {
    Show-Free
    foreach ($n in @($Pausable.name) + 'chrome' | Select-Object -Unique) {
        $ps = @(Get-Process -Name $n -ErrorAction SilentlyContinue)
        if (-not $ps.Count) { continue }
        $m = Get-MainProcess $n
        '  {0,-14} {1,5:N2} GB  {2}{3}' -f $n, (($ps | Measure-Object WorkingSet64 -Sum).Sum / 1GB), $(if ($m.admin) { 'admin, ' }), $(if ($n -eq 'chrome' -and -not $Browser) { 'pausable with -Browser' } else { 'pausable' })
    }
    $t = @(Get-StaleTails); if ($t.Count) { "  $($t.Count) stale monitor tails from finished sessions" }
    if (Test-Path $state) { "Paused now: $((Get-Content $state -Raw | ConvertFrom-Json).name -join ', '). Run resume to bring them back." }
    return
}

if ($Mode -eq 'pause') {
    'Before: ' + (Show-Free)
    $closed = @(); if (Test-Path $state) { $j = Get-Content $state -Raw | ConvertFrom-Json; $closed = @($j) }  # 5.1 hands the JSON array back as one item unless assigned first
    foreach ($a in $Pausable) {
        $m = Get-MainProcess $a.name
        if (-not $m) { "  $($a.name) isn't running"; continue }
        $start = if ($a.start) { $a.start } else { $m.start }
        if (-not ($start -split '\|')[0]) { "  can't tell how to reopen $($a.name), so it stays open"; continue }
        Get-Process -Name $a.name -ErrorAction SilentlyContinue | ForEach-Object { [void]$_.CloseMainWindow() }  # let it save (Chrome keeps its tabs)
        Start-Sleep -Seconds 3
        # Tray apps (Discord, ShareX) only hide on close, and Discord's main process respawns
        # its children, so end the whole tree with taskkill and wait for it to go.
        $err = ''
        for ($i = 0; $i -lt 10 -and (Get-Process -Name $a.name -ErrorAction SilentlyContinue); $i++) {
            if ($m.admin -and -not $iAmAdmin) {   # an admin app needs an admin taskkill: Windows asks once
                try { Start-Process taskkill -ArgumentList "/F /T /IM $($a.name).exe" -Verb RunAs -WindowStyle Hidden -Wait -ErrorAction Stop } catch { $err = 'admin prompt declined'; break }
            } else { $err = (& taskkill /F /T /IM "$($a.name).exe" 2>&1 | Select-String 'Reason' | Select-Object -Last 1 | Out-String).Trim() }
            Start-Sleep -Seconds 1
        }
        if (Get-Process -Name $a.name -ErrorAction SilentlyContinue) { "  could not close $($a.name): $err"; continue }
        $closed = @($closed | Where-Object { $_.name -ne $a.name }) + [pscustomobject]@{ name = $a.name; start = $start; admin = $m.admin }
        "  paused $($a.name)$(if ($m.admin) { ' (was admin)' })"
    }
    $t = @(Get-StaleTails); $t | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    if ($t.Count) { "  cleared $($t.Count) stale monitor tails" }
    $busy = Get-CimInstance Win32_Process -Filter "Name='dotnet.exe'" | Where-Object { $_.CommandLine -match '\b(build|test|run|msbuild|vstest)\b' }
    if (-not $busy) { & dotnet build-server shutdown *> $null; '  stopped the idle C# compiler server (it restarts on the next build)' }
    if ($closed.Count) { New-Item -ItemType Directory -Force $dir | Out-Null; ConvertTo-Json @($closed) | Set-Content -Encoding utf8 $state }
    Start-Sleep -Seconds 2
    'After:  ' + (Show-Free)
    return
}

if ($Mode -eq 'resume') {
    if (-not (Test-Path $state)) { 'Nothing paused.'; return }
    $left = @()
    $j = Get-Content $state -Raw | ConvertFrom-Json
    foreach ($a in @($j)) {
        if (Get-Process -Name $a.name -ErrorAction SilentlyContinue) { "  $($a.name) already running"; continue }
        $exe, $arg = $a.start -split '\|', 2
        if (-not (Test-Path -LiteralPath $exe)) { "  can't find $exe for $($a.name); open it by hand"; continue }
        $p = @{ FilePath = $exe; WorkingDirectory = (Split-Path $exe); WindowStyle = 'Normal' }  # not the hidden style of the window that runs us
        if ($arg) { $p.ArgumentList = $arg }
        try {
            if ($a.admin -and -not $iAmAdmin) { Start-Process @p -Verb RunAs -ErrorAction Stop }   # Windows asks for admin
            else { Start-Process @p -ErrorAction Stop }
            "  reopened $($a.name)$(if ($a.admin) { ' as admin' })"
        } catch { "  could not reopen $($a.name): $($_.Exception.Message)"; $left += $a }
    }
    Start-Sleep -Seconds 3
    if ($left.Count) { ConvertTo-Json @($left) | Set-Content -Encoding utf8 $state } else { Remove-Item $state }
}

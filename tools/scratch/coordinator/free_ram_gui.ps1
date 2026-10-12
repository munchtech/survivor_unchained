# A small window for free_ram.ps1: one button to pause or resume, a Chrome checkbox, live RAM and VRAM.
#   powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File tools/scratch/coordinator/free_ram_gui.ps1
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$script = Join-Path $PSScriptRoot 'free_ram.ps1'
$state = Join-Path $env:LOCALAPPDATA 'SurvivorUnchained\paused_apps.json'

$form = New-Object System.Windows.Forms.Form -Property @{
    Text = 'Free RAM for game work'; ClientSize = '360,300'; FormBorderStyle = 'FixedSingle'
    MaximizeBox = $false; StartPosition = 'CenterScreen'; Font = New-Object System.Drawing.Font('Segoe UI', 10)
}
$mem = New-Object System.Windows.Forms.Label -Property @{ Location = '16,14'; Size = '330,44'; Font = New-Object System.Drawing.Font('Segoe UI', 11) }
$btn = New-Object System.Windows.Forms.Button -Property @{ Location = '16,64'; Size = '328,56'; Font = New-Object System.Drawing.Font('Segoe UI', 13, [System.Drawing.FontStyle]::Bold) }
$chk = New-Object System.Windows.Forms.CheckBox -Property @{ Location = '18,128'; Size = '320,26'; Text = 'Also close Chrome (it reopens your tabs)' }
$log = New-Object System.Windows.Forms.TextBox -Property @{ Location = '16,160'; Size = '328,126'; Multiline = $true; ReadOnly = $true; ScrollBars = 'Vertical'; Font = New-Object System.Drawing.Font('Consolas', 9) }
$form.Controls.AddRange(@($mem, $btn, $chk, $log))

function Update-View {
    $os = Get-CimInstance Win32_OperatingSystem
    $text = 'RAM free  {0:N1} of {1:N0} GB' -f ($os.FreePhysicalMemory / 1MB), ($os.TotalVisibleMemorySize / 1MB)
    $v = (& nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>$null) -split ','
    if ($v.Count -eq 2) { $text += "`nVRAM free {0:N1} of {1:N0} GB" -f (($v[1] - $v[0]) / 1KB), ($v[1] / 1KB) }
    $mem.Text = $text
    if (Test-Path $state) {
        $btn.Text = 'Paused: click to resume'; $btn.BackColor = [System.Drawing.Color]::FromArgb(255, 214, 150); $chk.Enabled = $false
    } else {
        $btn.Text = 'Normal: click to pause'; $btn.BackColor = [System.Drawing.Color]::FromArgb(170, 225, 170); $chk.Enabled = $true
    }
}

$btn.Add_Click({
    $btn.Enabled = $false; $form.UseWaitCursor = $true; $log.Text = 'Working...'; $form.Refresh()
    $args2 = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $script)
    $args2 += if (Test-Path $state) { 'resume' } else { 'pause' }
    if ($chk.Checked -and $args2[-1] -eq 'pause') { $args2 += '-Browser' }
    $out = & powershell @args2 2>&1 | Out-String
    $log.Text = ($out.Trim() -replace "`r?`n", "`r`n")
    $btn.Enabled = $true; $form.UseWaitCursor = $false; Update-View
})

$timer = New-Object System.Windows.Forms.Timer -Property @{ Interval = 10000 }
$timer.Add_Tick({ if ($form.WindowState -ne 'Minimized') { Update-View } })  # no polling while minimized
$form.Add_Shown({ Update-View; $timer.Start() })
[void]$form.ShowDialog()
$timer.Dispose()

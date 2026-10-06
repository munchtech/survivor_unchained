param([string]$Exe, [string]$Out, [string[]]$GameArgs = @(), [string]$Steps)
# Runs an exported build and plays a script of steps against its window by
# posted messages (no focus taken, the owner's mouse and keys untouched):
#   wait:S        wait S seconds
#   key:NAME      press and release a key (Return, Escape, W, A, S, D, Space, E, Down, Up)
#   hold:NAME:S   hold a key S seconds
#   shot:TAG      copy the window from the screen (raised topmost) to $Out.TAG.png
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class U {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint f);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
$keys = @{ Return = @(0x0D, 0x1C); Escape = @(0x1B, 0x01); W = @(0x57, 0x11); A = @(0x41, 0x1E); S = @(0x53, 0x1F); D = @(0x44, 0x20); Space = @(0x20, 0x39); E = @(0x45, 0x12); Down = @(0x28, 0x50); Up = @(0x26, 0x48); Tab = @(0x09, 0x0F) }
function Down($h, $k) { $v = $keys[$k]; [void][U]::PostMessage($h, 0x100, [IntPtr]$v[0], [IntPtr](1 -bor ($v[1] -shl 16))) }
function Up($h, $k) { $v = $keys[$k]; [void][U]::PostMessage($h, 0x101, [IntPtr]$v[0], [IntPtr]([int64](1 -bor ($v[1] -shl 16) -bor (1 -shl 30)) -bor 0x80000000L)) }
function Grab($h, $file) {
  [void][U]::SetWindowPos($h, [IntPtr](-1), 0, 0, 0, 0, 0x41)
  Start-Sleep -Milliseconds 800
  $r = New-Object U+RECT
  [void][U]::GetWindowRect($h, [ref]$r)
  $bmp = New-Object System.Drawing.Bitmap ($r.R - $r.L), ($r.B - $r.T)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
  $bmp.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
  [void][U]::SetWindowPos($h, [IntPtr](-2), 0, 0, 0, 0, 0x43)
  "captured $file"
}
$p = Start-Process -FilePath $Exe -ArgumentList $GameArgs -PassThru -RedirectStandardOutput "$Out.log" -RedirectStandardError "$Out.err"
$h = [IntPtr]::Zero
foreach ($i in 1..60) { Start-Sleep -Seconds 1; $p.Refresh(); if ($p.MainWindowHandle -ne [IntPtr]::Zero) { $h = $p.MainWindowHandle; break } }
if ($h -eq [IntPtr]::Zero) { "no window"; if (!$p.HasExited) { $p.Kill() }; exit 1 }
foreach ($s in $Steps.Split(",")) {
  $a = $s.Split(":")
  switch ($a[0]) {
    "wait" { Start-Sleep -Seconds ([double]$a[1]) }
    "key" { Down $h $a[1]; Start-Sleep -Milliseconds 120; Up $h $a[1]; Start-Sleep -Milliseconds 400 }
    "hold" { Down $h $a[1]; $end = (Get-Date).AddSeconds([double]$a[2]); while ((Get-Date) -lt $end) { Start-Sleep -Milliseconds 200 }; Up $h $a[1] }
    "shot" { Grab $h "$Out.$($a[1]).png" }
  }
  if ($p.HasExited) { "exited early with $($p.ExitCode)"; break }
}
if (!$p.HasExited) { [void]$p.CloseMainWindow(); if (!$p.WaitForExit(20000)) { $p.Kill(); "killed" } else { "closed, exit $($p.ExitCode)" } }

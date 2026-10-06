param([string]$Exe, [string]$Out, [int]$Wait = 30, [string[]]$GameArgs = @(), [string[]]$Keys = @())
# Runs an exported build, copies its window from the screen after $Wait
# seconds (DWM composes Vulkan windows, so a screen copy sees them where
# PrintWindow gives black), then closes it. -Keys sends keystrokes first
# (SendKeys syntax), a second apart, with a capture after each.
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class W {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint f);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@
function Grab($h, $file) {
  [void][W]::SetWindowPos($h, [IntPtr](-1), 0, 0, 0, 0, 0x41)
  [void][W]::SetForegroundWindow($h)
  Start-Sleep -Milliseconds 800
  $r = New-Object W+RECT
  [void][W]::GetWindowRect($h, [ref]$r)
  $bmp = New-Object System.Drawing.Bitmap ($r.R - $r.L), ($r.B - $r.T)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
  $bmp.Save($file, [System.Drawing.Imaging.ImageFormat]::Png)
  "captured $file $($bmp.Width)x$($bmp.Height) at $($r.L),$($r.T)"
}
$p = Start-Process -FilePath $Exe -ArgumentList $GameArgs -PassThru -RedirectStandardOutput "$Out.log" -RedirectStandardError "$Out.err"
Start-Sleep -Seconds $Wait
$p.Refresh()
$h = $p.MainWindowHandle
if ($h -eq [IntPtr]::Zero) { "no window; exited=$($p.HasExited)"; if (!$p.HasExited) { $p.Kill() }; exit 1 }
Grab $h "$Out.png"
$i = 0
foreach ($k in $Keys) {
  $i++
  [void][W]::SetForegroundWindow($h)
  [System.Windows.Forms.SendKeys]::SendWait($k)
  Start-Sleep -Seconds 3
  Grab $h "$Out.k$i.png"
}
[void]$p.CloseMainWindow()
if (!$p.WaitForExit(15000)) { $p.Kill(); "killed" } else { "exited" }


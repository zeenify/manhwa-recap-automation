param(
  [Parameter(Mandatory=$true)][string]$PathsRaw,
  [int]$TimeoutMs = 20000
)
# Same as drive_dialog.ps1 but feeds MULTIPLE quoted paths (Windows dialog
# multi-select syntax) into the native Open dialog in one shot.
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinM {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindow(string cls, string title);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
}
"@
$deadline = (Get-Date).AddMilliseconds($TimeoutMs)
$h = [IntPtr]::Zero
while ((Get-Date) -lt $deadline) {
  $h = [WinM]::FindWindow("#32770", "Open")
  if ($h -eq [IntPtr]::Zero) { $h = [WinM]::FindWindow("#32770", $null) }
  if ($h -ne [IntPtr]::Zero -and [WinM]::IsWindowVisible($h)) { break }
  $h = [IntPtr]::Zero
  Start-Sleep -Milliseconds 300
}
if ($h -eq [IntPtr]::Zero) { Write-Output "NO_DIALOG"; exit 1 }
$wsh = New-Object -ComObject WScript.Shell
$null = $wsh.AppActivate("Open")
Start-Sleep -Milliseconds 700
[WinM]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 700
$Paths = $PathsRaw -split '\|'
$quoted = ($Paths | ForEach-Object { '"' + $_ + '"' }) -join " "
Set-Clipboard -Value $quoted
[System.Windows.Forms.SendKeys]::SendWait("%n")
Start-Sleep -Milliseconds 400
[System.Windows.Forms.SendKeys]::SendWait("^a")
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait("^v")
Start-Sleep -Milliseconds 800
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
Start-Sleep -Milliseconds 2500
$still = [WinM]::FindWindow("#32770", "Open")
if ($still -ne [IntPtr]::Zero -and [WinM]::IsWindowVisible($still)) { Write-Output "DIALOG_STILL_OPEN" } else { Write-Output "DONE" }

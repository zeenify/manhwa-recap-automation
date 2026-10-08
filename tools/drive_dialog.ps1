param(
  [Parameter(Mandatory=$true)][string]$Path,
  [int]$TimeoutMs = 20000
)
# Drives the native Windows "Open" file dialog (class #32770) to select $Path.
# Computer Use is unavailable this session, so this replaces only the OS-dialog
# step of the documented upload flow. Finds the dialog as a WINDOW (dialogs are
# not a process's MainWindow, so Get-Process cannot see them).
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win {
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr FindWindow(string cls, string title);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
}
"@
$deadline = (Get-Date).AddMilliseconds($TimeoutMs)
$h = [IntPtr]::Zero
while ((Get-Date) -lt $deadline) {
  $h = [Win]::FindWindow("#32770", "Open")
  if ($h -eq [IntPtr]::Zero) { $h = [Win]::FindWindow("#32770", $null) }
  if ($h -ne [IntPtr]::Zero -and [Win]::IsWindowVisible($h)) { break }
  $h = [IntPtr]::Zero
  Start-Sleep -Milliseconds 300
}
if ($h -eq [IntPtr]::Zero) { Write-Output "NO_DIALOG"; exit 1 }
$wsh = New-Object -ComObject WScript.Shell
# two focus paths: title activation (reliable across processes) then hwnd
$null = $wsh.AppActivate("Open")
Start-Sleep -Milliseconds 700
[Win]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 700
Set-Clipboard -Value $Path
[System.Windows.Forms.SendKeys]::SendWait("%n")   # Alt+N focuses the File name field
Start-Sleep -Milliseconds 400
[System.Windows.Forms.SendKeys]::SendWait("^a")
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait("^v")
Start-Sleep -Milliseconds 700
[System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
Start-Sleep -Milliseconds 1500
$still = [Win]::FindWindow("#32770", "Open")
if ($still -ne [IntPtr]::Zero -and [Win]::IsWindowVisible($still)) { Write-Output "DIALOG_STILL_OPEN" } else { Write-Output "DONE" }

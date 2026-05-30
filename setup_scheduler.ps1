# Run this script once to register a daily 9pm task in Windows Task Scheduler.
# Open PowerShell as Administrator and run:
#   .\setup_scheduler.ps1

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe  = (Get-Command python).Source
$MainScript = Join-Path $ScriptDir "main.py"
$TaskName   = "BloombergTranscripts"

$Action  = New-ScheduledTaskAction -Execute $PythonExe -Argument "`"$MainScript`"" -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Daily -At "21:00"
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun:$false

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -RunLevel Limited `
    -Force

Write-Host "Task '$TaskName' registered. It will run daily at 9:00 PM."
Write-Host "To run it immediately for testing: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "To remove it: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"

<#
  Install the Altera USB-Blaster driver that ships inside Quartus.

  YOU run this, not Claude: it needs administrator rights and Windows may ask
  you to trust the driver publisher. Right-click Windows PowerShell ->
  "Run as administrator", then:

      cd C:\Users\Alex\Documents\GitHub\LycoChip
      powershell -ExecutionPolicy Bypass -File tools\windows\install-usb-blaster-driver.ps1

  Plug the board in (USB-Blaster connected, board powered) before running it.

  It shows you what it found and asks before changing anything. It does NOT
  touch Core Isolation / Memory integrity -- see the note it prints if the
  driver refuses to load.
#>
#Requires -RunAsAdministrator
$ErrorActionPreference = 'Stop'

function Find-QuartusRoot {
    if ($env:QUARTUS_ROOTDIR -and (Test-Path (Join-Path $env:QUARTUS_ROOTDIR 'bin64\quartus_sh.exe'))) {
        return (Resolve-Path $env:QUARTUS_ROOTDIR).Path
    }
    $c = Get-ChildItem 'C:\intelFPGA_lite\*\quartus', 'C:\altera_lite\*\quartus', 'C:\intelFPGA\*\quartus' `
            -Directory -ErrorAction SilentlyContinue |
         Where-Object { Test-Path (Join-Path $_.FullName 'bin64\quartus_sh.exe') }
    $pick = $c | Where-Object { $_.FullName -match '\\20\.1\\' } | Select-Object -First 1
    if (-not $pick) { $pick = $c | Sort-Object FullName | Select-Object -Last 1 }
    if ($pick) { return $pick.FullName }
    return $null
}

function Show-Blaster {
    $d = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
         Where-Object { $_.InstanceId -match 'VID_09FB' }
    if ($d) { $d | Format-Table Status, Class, FriendlyName, InstanceId -AutoSize | Out-String -Width 200 | Write-Host }
    else    { Write-Host '  (no device with Altera vendor ID 09FB is plugged in)' }
}

$root = Find-QuartusRoot
if (-not $root) { throw 'No Quartus install found. Install Quartus Prime Lite first.' }
Write-Host "Quartus: $root"

$drv = Join-Path $root 'drivers\usb-blaster'
if (-not (Test-Path $drv)) { throw "No driver folder at $drv -- list $root\drivers and pick the usb-blaster one by hand." }
$infs = Get-ChildItem $drv -Recurse -Filter *.inf
if (-not $infs) { throw "No .inf files under $drv" }
Write-Host "`nDriver .inf files found:"
$infs | ForEach-Object { Write-Host "  $($_.FullName)" }

Write-Host "`nUSB-Blaster before:"
Show-Blaster

$hvci = (Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' -ErrorAction SilentlyContinue).Enabled
Write-Host ("Core Isolation / Memory integrity: " + $(if ($hvci -eq 1) { 'ON' } else { 'off or not configured' }))

$ans = Read-Host "`nInstall these drivers with pnputil? (y/N)"
if ($ans -notmatch '^[yY]') { Write-Host 'Nothing changed.'; exit 0 }

foreach ($i in $infs) {
    Write-Host "`n> pnputil /add-driver `"$($i.FullName)`" /install"
    & pnputil.exe /add-driver $i.FullName /install
}

# The JTAG server is what jtagconfig and quartus_pgm talk to. On Windows it
# runs as a service; installing it needs admin, which is why it is here.
$js = Join-Path $root 'bin64\jtagserver.exe'
if (Test-Path $js) {
    Write-Host "`n> jtagserver --install / --start"
    & $js --install 2>&1 | Write-Host
    & $js --start   2>&1 | Write-Host
}

Write-Host "`nUSB-Blaster after (unplug and replug if it still shows an error):"
Show-Blaster

Write-Host "`n> jtagconfig"
& (Join-Path $root 'bin64\jtagconfig.exe') 2>&1 | Write-Host

Write-Host @"

What good looks like: jtagconfig lists 'USB-Blaster [USB-0]' and under it
'020F10DD   EP3C(10|5)/EP4CE(10|6)'. That IDCODE is the chip answering.

If the device shows an error (Code 39 or 52) and Memory integrity is ON:
Windows is refusing the old, unsigned-for-HVCI driver. The options are a
decision for you, not a fix to apply blindly:
  - turn Memory integrity off (Settings > Privacy & security > Windows
    Security > Device security > Core isolation) and reboot -- this weakens
    a real kernel protection on this PC;
  - try the USB-Blaster driver from a newer Quartus Programmer release;
  - or bypass the Altera driver: openFPGALoader (in OSS CAD Suite) with a
    WinUSB driver via Zadig, loading the .svf exactly as the Mac does.
"@

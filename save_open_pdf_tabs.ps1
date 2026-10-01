$ErrorActionPreference = "Stop"

Add-Type -AssemblyName Microsoft.VisualBasic
Add-Type -AssemblyName System.Windows.Forms

$rawCount = [Microsoft.VisualBasic.Interaction]::InputBox(
    "How many PDF tabs are already open?`r`n`r`n请输入已经打开的 PDF 标签页数量。",
    "ChipSeeker - Save Open PDF Tabs",
    "1"
)

if ([string]::IsNullOrWhiteSpace($rawCount)) {
    exit 0
}

$count = 0
if (-not [int]::TryParse($rawCount, [ref]$count) -or $count -lt 1 -or $count -gt 200) {
    [System.Windows.Forms.MessageBox]::Show(
        "Please enter a number from 1 to 200.`r`n请输入 1 到 200 之间的数字。",
        "ChipSeeker Downloader",
        "OK",
        "Warning"
    ) | Out-Null
    exit 1
}

[System.Windows.Forms.MessageBox]::Show(
    "After closing this message, click the first PDF tab within 5 seconds.`r`n`r`nThe script will save and close each PDF tab in turn.`r`n`r`n关闭本提示后，请在 5 秒内点击任意一个待下载的 PDF 标签页。脚本会依次保存并关闭这些 PDF 标签页。",
    "ChipSeeker - Ready",
    "OK",
    "Information"
) | Out-Null

$shell = New-Object -ComObject WScript.Shell
Start-Sleep -Seconds 5

for ($index = 1; $index -le $count; $index++) {
    Write-Host "[$index/$count] Saving the active PDF tab..."
    $shell.SendKeys("^s")
    Start-Sleep -Milliseconds 2200
    $shell.SendKeys("{ENTER}")
    Start-Sleep -Milliseconds 2600
    $shell.SendKeys("^w")
    Start-Sleep -Milliseconds 900
}

[System.Windows.Forms.MessageBox]::Show(
    "Finished processing $count PDF tabs.`r`n已处理 $count 个 PDF 标签页。",
    "ChipSeeker Downloader",
    "OK",
    "Information"
) | Out-Null

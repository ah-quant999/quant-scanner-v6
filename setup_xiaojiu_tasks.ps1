# setup_xiaojiu_tasks.ps1 - 小九（单位电脑）定时任务设置
# 使用方法：右键 → 以管理员身份运行 PowerShell → .\setup_xiaojiu_tasks.ps1

$wd = "E:\workspace\workspace\stock-scanner"
$py = "C:\Users\HH20210606\AppData\Local\Programs\Python\Python312\python.exe"

# 如果 Python 路径或工作目录不同，请修改上面两行

Write-Output "=== 九宝量化 小九定时任务设置 ==="
Write-Output "工作目录: $wd"
Write-Output "Python路径: $py"
Write-Output ""

# 检查路径是否存在
if (-not (Test-Path $wd)) {
    Write-Output "❌ 工作目录不存在: $wd"
    Write-Output "   请修改脚本中的 `$wd` 变量"
    exit 1
}

$tasks = @(
    @{Name="九宝量化-晨间速报"; Time="07:30"; Mode="pre_brief"},
    @{Name="九宝量化-盘前"; Time="09:15"; Mode="pre_market"},
    @{Name="九宝量化-盘中快速"; Time="09:45"; Mode="morning_scan"},
    @{Name="九宝量化-盘中三卡"; Time="10:30"; Mode="morning_plus"},
    @{Name="九宝量化-午间报告"; Time="11:45"; Mode="morning_report"},
    @{Name="九宝量化-午后1"; Time="13:30"; Mode="afternoon"},
    @{Name="九宝量化-午后2"; Time="14:30"; Mode="afternoon"},
    @{Name="九宝量化-收盘前"; Time="15:20"; Mode="afternoon"},
    @{Name="九宝量化-收盘全量"; Time="19:30"; Mode="close"},
    @{Name="九宝量化-审核备份"; Time="21:00"; Mode="backup"}
)

$success = 0
$failed = 0

foreach ($task in $tasks) {
    try {
        $act = New-ScheduledTaskAction -Execute $py -Argument "batch_update.py $($task.Mode)" -WorkingDirectory $wd
        $trig = New-ScheduledTaskTrigger -Daily -At $task.Time
        $set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        
        Register-ScheduledTask -TaskName $task.Name -Trigger $trig -Action $act -Settings $set -Description "$($task.Time) $($task.Mode)" -Force
        
        Write-Output "✅ $($task.Name) ($($task.Time))"
        $success++
    }
    catch {
        Write-Output "❌ $($task.Name) 创建失败: $_"
        $failed++
    }
}

Write-Output ""
Write-Output "=== 创建完成 ==="
Write-Output "成功: $success  失败: $failed"
Write-Output ""

Write-Output "=== 当前所有九宝任务 ==="
Get-ScheduledTask -TaskName '*九宝量化*' | Select-Object TaskName,State,NextRunTime | Format-Table

Write-Output ""
Write-Output "如果 State 不是 Ready，请打开'任务计划程序'检查。"

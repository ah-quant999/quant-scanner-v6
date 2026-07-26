<#
================================================================================
 heartbeat_deploy_check.ps1 — 云端部署心跳监控(督促部署)
 
 用途：检测 GitHub Pages 上次部署时长，超阈则强制 dispatch cloud_intraday
 所属系统：九宝量化v6.0 自动化兜底层
 依赖：git credential helper（取 PAT）、GitHub API（公开+鉴权）
 调用者：WorkBuddy 自动化"心跳监控-督促云端部署"
 
 修复清单 v2 (2026-07-21):
   P0 - 周一用 68h 阈值覆盖周末
   P0 - 用 cloud_intraday.yml 文件名代替硬编码 workflow ID
   P1 - 调用 check_trading_day.py 判断真实交易日(含节假日)
   P1 - dispatch 前查运行中 workflow（幂等保护）
   P1 - PAT 空值降级处理
   P2 - dispatch 后 5s 确认 run 被创建
   P2 - 08:00~09:00 跳过 dispatch（本地 09:20 独家部署）
   P2 - 静默结束输出日志行

 修复清单 v3 (2026-07-23) — 真·一劳永逸闭环:
   核心 - 检测到 gh-pages 陈旧后【立即本地自愈部署】(deploy_now.py --force，走 SSH 已验证可靠)
          取代旧版"只 dispatch 云端等它跑"的被动模式，闭环自己部署最新数据
   核心 - 本地部署前/后 git ls-remote 比对 SHA，确认 gh-pages 真刷新才算成功
   核心 - 云端 dispatch 降级为【兜底】：仅当本地部署失败且非 08:00~09:00 冲突窗口才触发
   核心 - 08:00~09:00 若已严重陈旧(≥20h) 仍本地自愈，但不 dispatch 云端(避免与09:20冲突)
   环境 - PowerShell 子进程默认 PATH 无 git → 启动时注入 PortableGit(candidates 回退)
   环境 - PowerShell 子进程默认 GBK 编码 → 设 PYTHONUTF8=1 让 deploy_now.py/open() 走 UTF-8
   修复 - gh-pages 提交带 +08:00 偏移导致时区双重+8(算出"未来时间")→ 改用 [DateTimeOffset]
================================================================================
#>

# ---------- 常量 ----------
$REPO_OWNER = "ah-quant999"
$REPO_NAME = "quant-scanner-v6"
$WORKFLOW_FILE = "cloud_intraday.yml"          # 用文件名 > 硬编码ID
$GHP_API = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/commits/gh-pages?per_page=1"
$DISPATCH_API = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$WORKFLOW_FILE/dispatches"
$RUNS_API = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/runs?event=workflow_dispatch&per_page=1"
$RUNNING_API = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$WORKFLOW_FILE/runs?status=in_progress&per_page=1"
$CHECK_TRADE_PY = "E:\workspace\stock-scanner\repo-temp\check_trading_day.py"
$DEPLOY_PY = "E:\workspace\stock-scanner\repo-temp\deploy_now.py"
$PYTHON = "C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe"

# ---------- 环境修复 A：PowerShell 子进程默认 PATH 无 git，补上（多候选回退） ----------
# 不注入则 git credential fill(PAT) 与 deploy_now.py(本地自愈) 均会 'git 不是命令' 静默失败
$gitCandidates = @(
    "E:\workbuddy-data\vendor\PortableGit\mingw64\bin",
    "C:\Program Files\Git\cmd",
    "C:\Program Files\Git\bin",
    "C:\Program Files (x86)\Git\cmd"
)
foreach ($cand in $gitCandidates) {
    if (Test-Path "$cand\git.exe") {
        if ($env:PATH -notlike "*$cand*") { $env:PATH = "$cand;$env:PATH" }
        Write-Output "已注入 git PATH: $cand"
        break
    }
}

# ---------- 环境修复 B：强制 Python UTF-8 模式 ----------
# PowerShell 子进程默认文件编码是 GBK(cp936)，deploy_now.py/update_data_v2.py 里 open() 不带
# encoding 会 UnicodeDecodeError 崩溃。PYTHONUTF8=1 让其默认 UTF-8，与 Git Bash 行为一致。
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

# ---------- 步骤1：交易日判断 ----------
Write-Output "=== 心跳监控-督促云端部署 v3 (本地自愈闭环) ==="
Write-Output "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') (北京时间)"

# 走 check_trading_day.py 判断真实交易日
$tradeCheck = & $PYTHON $CHECK_TRADE_PY 2>$null | Select-Object -Last 1
if ($tradeCheck -ne "TRADE") {
    Write-Output "非交易日（$tradeCheck），静默结束。"
    exit 0
}
Write-Output "交易日 ✅"

# ---------- 步骤2：查 gh-pages 最新部署时间 ----------
try {
    $r = Invoke-RestMethod -Uri $GHP_API -Headers @{"Accept"="application/vnd.github.v3+json"} -ErrorAction Stop
    # ⚠️ 修复时区双重+8 bug：API 返回的 committer.date 已含 +08:00 偏移(deploy_now.py 在本机 Beijing 提交)
    # 用 [DateTimeOffset] 解析再取 UtcDateTime，避免 Parse 二次加时区导致算出"未来时间"
    $lastDeployUtc = [DateTimeOffset]::Parse($r.commit.committer.date).UtcDateTime
    $lastDeployBj = $lastDeployUtc.AddHours(8)
    $nowBj = [DateTime]::UtcNow.AddHours(8)
    $hoursElapsed = [Math]::Round(($nowBj - $lastDeployBj).TotalHours, 1)
    Write-Output "gh-pages 最新部署: $($lastDeployBj.ToString('yyyy-MM-dd HH:mm:ss')) (北京时间)"
    Write-Output "距今: ${hoursElapsed}小时"
} catch {
    Write-Output "🔴 获取 gh-pages 部署时间失败: $_"
    exit 1
}

# ---------- 步骤3：计算阈值 ----------
$dayOfWeek = [int]$nowBj.DayOfWeek  # 0=周日, 1=周一, ..., 6=周六
$bjHour = $nowBj.Hour
$shouldDispatch = $false
$cloudDispatchAllowed = $true      # 本地自愈优先；仅在非 08:00~09:00 冲突窗口才允许云端 dispatch
$skipReason = ""

# 3a: 周一特殊处理 —— 用 68h 覆盖整个周末
if ($dayOfWeek -eq 1) {
    if ($hoursElapsed -ge 68) {
        $shouldDispatch = $true
        Write-Output "周一检测，${hoursElapsed}h ≥ 68h 周末阈值 → 准备 dispatch"
    } else {
        $skipReason = "周一 ${hoursElapsed}h < 68h 周末阈值，静默"
    }
}
# 3b: 08:00~09:00 —— 若已严重陈旧则本地立即自愈（不 dispatch 云端，避免与 09:20 冲突）
elseif ($bjHour -ge 8 -and $bjHour -lt 9) {
    if ($hoursElapsed -ge 20) {
        $shouldDispatch = $true
        $cloudDispatchAllowed = $false
        Write-Output "08:00~09:00 但已陈旧 ${hoursElapsed}h≥20h → 本地立即自愈（不 dispatch 云端）"
    } else {
        $skipReason = "08:00~09:00 窗口且未严重陈旧，等待本地 09:20 独家部署"
    }
}
# 3c: 交易时段 09:00~16:30
elseif ($bjHour -ge 9 -and $bjHour -lt 16 -or ($bjHour -eq 16 -and $nowBj.Minute -le 30)) {
    if ($hoursElapsed -ge 4) {
        $shouldDispatch = $true
        Write-Output "交易时段内，${hoursElapsed}h ≥ 4h → 准备 dispatch"
    } else {
        $skipReason = "交易时段内 ${hoursElapsed}h < 4h，云端 cron 会自己跑"
    }
}
# 3d: 盘后~次日盘前
else {
    if ($hoursElapsed -ge 20) {
        $shouldDispatch = $true
        Write-Output "盘后时段，${hoursElapsed}h ≥ 20h → 准备 dispatch"
    } else {
        $skipReason = "盘后 ${hoursElapsed}h < 20h，未超阈值"
    }
}

if (-not $shouldDispatch) {
    Write-Output "✅ 心跳检查正常：gh-pages 距现在 ${hoursElapsed}h，$skipReason"
    exit 0
}

# ---------- 步骤4：本地自愈部署（真·一劳永逸核心） ----------
# 检测到陈旧 → 立即用本机最新数据部署（deploy_now.py 走 SSH，已验证可靠）
# 比 dispatch 云端更快更稳，且本地双机数据本就保持新鲜，无需等待云端
#
# 🔒 新数据闸门（用户铁律：兜底=没新数据就不动，绝不回退到旧数据）：
#   取本地 data/ 最新提交时间，若它不晚于 gh-pages 当前部署时间 → 本地也没有比线上更新的数据
#   → 跳过本地部署（不动旧数据），转云端实时抓取兜底（云端抓实时行情，仍是新数据，不会回退）
try {
    $localDataEpoch = 0
    $le = (git -c http.version=HTTP/1.1 log -1 --format=%ct -- data/ 2>$null)
    if ($le -match '^\d+$') { $localDataEpoch = [int]$le }
    $localDeployAllowed = $true
    if ($localDataEpoch -gt 0) {
        $localDataBj = [DateTimeOffset]::FromUnixTimeSeconds($localDataEpoch).UtcDateTime.AddHours(8)
        if ($localDataBj -le $lastDeployBj) {
            Write-Output "🔒 新数据闸门：本地 data/ 最新更新 $($localDataBj.ToString('yyyy-MM-dd HH:mm')) 不晚于线上部署 $($lastDeployBj.ToString('yyyy-MM-dd HH:mm'))"
            Write-Output "   → 本地无更新数据，跳过本地部署（绝不回退旧数据），转云端实时抓取兜底"
            $localDeployAllowed = $false
        }
    }
} catch {
    Write-Output "⚠️ 新数据闸门检查异常（git log 失败），放行本地部署尝试"
    $localDeployAllowed = $true
}

if ($localDeployAllowed) {
    Write-Output "🔧 启动本地自愈部署（deploy_now.py --force）..."

    # 部署前记录 gh-pages SHA，用于事后校验
    try {
        $preSha = ((git -c http.version=HTTP/1.1 ls-remote origin gh-pages 2>$null) -split "\s+")[0]
    } catch { $preSha = "" }

    $deployOk = $false
    try {
        $deployOut = & $PYTHON $DEPLOY_PY --force 2>&1
        $deployExit = $LASTEXITCODE
        $deployOut | ForEach-Object { Write-Output "  [deploy] $_" }
        if ($deployExit -eq 0) {
            Start-Sleep -Seconds 3
            $postSha = ((git -c http.version=HTTP/1.1 ls-remote origin gh-pages 2>$null) -split "\s+")[0]
            if ($postSha -and $postSha -ne $preSha) {
                $preShort = if ($preSha.Length -ge 8) { $preSha.Substring(0,8) } else { $preSha }
                $postShort = if ($postSha.Length -ge 8) { $postSha.Substring(0,8) } else { $postSha }
                Write-Output "✅ 本地自愈部署成功：gh-pages $preShort → $postShort 已刷新"
                $deployOk = $true
            } else {
                Write-Output "⚠️ 本地部署退出0但 gh-pages SHA 未变化（$postSha），转云端 dispatch 兜底"
            }
        } else {
            Write-Output "⚠️ 本地部署返回非零($deployExit)，转云端 dispatch 兜底"
        }
    } catch {
        Write-Output "⚠️ 本地部署异常: $_，转云端 dispatch 兜底"
    }

    if ($deployOk) {
        Write-Output ""
        Write-Output "🎉 真·一劳永逸：检测到陈旧后已立即本地部署最新数据，无需等待云端。"
        exit 0
    }
} else {
    # ========== 新数据闸门触发：本地 data/ 也不比线上新 → 立即诊断 + 汇报 ==========
    Write-Output ""
    Write-Output "🔴 🔴 🔴 诊断报告：gh-pages 已陈旧 ${hoursElapsed}h，但本地 data/ 也无更新数据"
    Write-Output "   gh-pages 最后部署: $($lastDeployBj.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Output "   本地 data/ 最新:    $($localDataBj.ToString('yyyy-MM-dd HH:mm:ss'))"
    Write-Output ""

    # 诊断 A：查本机最近自动化心跳（_heartbeat.log）
    $hbLog = "E:\workspace\stock-scanner\repo-temp\_heartbeat.log"
    if (Test-Path $hbLog) {
        $recentLines = Get-Content $hbLog -Tail 10 -Encoding UTF8
        Write-Output "--- 最近 10 条心跳记录 ---"
        foreach ($line in $recentLines) { Write-Output "  $line" }
        Write-Output ""
    } else {
        Write-Output "⚠️ _heartbeat.log 不存在（$hbLog）"
        Write-Output ""
    }

    # 诊断 B：查 origin/main 最近提交（看云端是否在推数据）
    try {
        $mainLog = (git -c http.version=HTTP/1.1 log --oneline -5 --format="%h %ai %s" origin/main 2>$null)
        if ($mainLog) {
            Write-Output "--- origin/main 最近 5 条提交 ---"
            $mainLog | ForEach-Object { Write-Output "  $_" }
            Write-Output ""
        }
    } catch { Write-Output "⚠️ git log origin/main 失败: $_`n" }

    # 诊断 C：查 cloud_intraday workflow 最近运行状态
    try {
        $wfApi = "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/actions/workflows/$WORKFLOW_FILE/runs?per_page=3"
        $wfRuns = Invoke-RestMethod -Uri $wfApi -Headers @{"Accept"="application/vnd.github.v3+json"} -ErrorAction SilentlyContinue
        if ($wfRuns.total_count -gt 0) {
            Write-Output "--- cloud_intraday 最近 $($wfRuns.workflow_runs.Count) 次运行 ---"
            foreach ($run in $wfRuns.workflow_runs) {
                $runDt = [DateTimeOffset]::Parse($run.created_at).UtcDateTime.AddHours(8).ToString('MM-dd HH:mm')
                $statusIcon = switch ($run.conclusion) { 'success' {'✅'}; 'failure'{'❌'}; 'cancelled'{'⏹️'}; default {'⏳'}}
                Write-Output "  [$statusIcon] Run#$($run.id) $runDt ($($run.event)) conclusion=$($run.conclusion)"
            }
            Write-Output ""
        }
    } catch { Write-Output "⚠️ 查询 workflow 运行状态失败: $_`n" }

    # 汇报结论 + 决策（按窗口区分：08:00~09:00 不 dispatch，等 09:20 本地独家部署）
    if ($cloudDispatchAllowed) {
        $nextAction = "将立即尝试云端 dispatch 触发实时行情抓取部署；若云端也失败 → 需人工介入排查双机自动化 / GitHub Actions 日志。"
    } else {
        $nextAction = "当前 08:00~09:00 窗口不 dispatch 云端（避免与本地 09:20 独家盘前部署冲突）→ 等待 09:20 部署；若届时仍陈旧，说明双机盘前任务也故障，需人工介入。"
    }
    $diagSummary = @"
📋 诊断结论：
  gh-pages 陈旧 ${hoursElapsed}h + 本地 data/ 同样陈旧 = 双机+云端数据管道可能同时停滞。
  本地不会推送旧数据（铁律）。
  下一步：$nextAction
"@
    Write-Output $diagSummary

    Write-Output "ℹ️ 本地部署已跳过（闸门），进入步骤5 决策..."
}

# ---------- 步骤5：取 PAT（仅本地部署失败时走云端兜底） ----------
# ⚠️ v2 修复: PowerShell 无 printf 命令，改用 here-string 传 stdin
if (-not $cloudDispatchAllowed) {
    Write-Output "ℹ️ 当前窗口不允许云端 dispatch（避免与本地 09:20 冲突），本地自愈已失败 → 等待 09:20 独家部署兜底"
    exit 1
}
try {
    $credInput = @"
protocol=https
host=github.com
"@
    $credLines = ($credInput | git credential fill) -split "`n"
    $tok = ""
    foreach ($line in $credLines) {
        if ($line -match '^password=(.+)$') {
            $tok = $matches[1]
            break
        }
    }
    if ([string]::IsNullOrEmpty($tok)) {
        Write-Output "🔴 PAT 获取失败（git credential 返回空），本地+云端均无法部署！请人工介入。"
        exit 1
    }
    Write-Output "PAT 获取成功 ✅"
} catch {
    Write-Output "🔴 PAT 获取异常: $_"
    exit 1
}

# ---------- 步骤6：dispatch 前查运行中 workflow（幂等保护） ----------
try {
    $running = Invoke-RestMethod -Uri $RUNNING_API -Headers @{
        "Accept" = "application/vnd.github.v3+json"
        "Authorization" = "Bearer $tok"
    } -ErrorAction Stop
    if ($running.total_count -gt 0) {
        $runId = $running.workflow_runs[0].id
        Write-Output "ℹ️ 已有运行中的 cloud_intraday workflow（Run ID: $runId），跳过 dispatch（幂等保护）"
        exit 0
    }
    Write-Output "无运行中的 workflow ✅"
} catch {
    Write-Output "⚠️ 查询运行中 workflow 失败: $_（继续 dispatch）"
}

# ---------- 步骤7：触发 workflow_dispatch ----------
try {
    $body = '{"ref":"main"}'
    $responseCode = (Invoke-WebRequest -Uri $DISPATCH_API -Method Post `
        -Headers @{
            "Accept" = "application/vnd.github+json"
            "Authorization" = "Bearer $tok"
        } `
        -Body $body -ContentType "application/json" `
        -UseBasicParsing -ErrorAction Stop).StatusCode
    
    if ($responseCode -ne 204) {
        Write-Output "🔴 dispatch 返回 HTTP $responseCode，云端兜底触发失败！本地自愈也已失败，需人工介入。"
        exit 1
    }
    Write-Output "dispatch 请求成功（HTTP 204）✅"
} catch {
    Write-Output "🔴 dispatch 请求异常: $_"
    exit 1
}

# ---------- 步骤8：dispatch 后确认 ----------
Start-Sleep -Seconds 5
try {
    $confirm = Invoke-RestMethod -Uri $RUNS_API -Headers @{
        "Accept" = "application/vnd.github.v3+json"
        "Authorization" = "Bearer $tok"
    } -ErrorAction Stop
    if ($confirm.total_count -gt 0) {
        $newRunId = $confirm.workflow_runs[0].id
        $newRunUrl = $confirm.workflow_runs[0].html_url
        Write-Output "✅ dispatch 确认成功，新 Run ID: $newRunId"
        Write-Output "   链接: $newRunUrl"
    } else {
        Write-Output "⚠️ dispatch 返回 204 但未检测到新 run，可能 workflow 被禁用"
    }
} catch {
    Write-Output "⚠️ dispatch 后确认失败: $_（可能请求超时，请手动复查）"
}

# ---------- 输出最终告警 ----------
$alertMsg = @"

⚠️ 云端已超过 ${hoursElapsed} 小时未部署。
优先尝试了本地自愈部署（deploy_now.py）但失败，已强制触发 ${WORKFLOW_FILE} 重新部署（dispatch）兜底。
请 5 分钟后复查 gh-pages build-stamp 是否刷新；若仍未更新，说明 GitHub Actions 调度/运行本身故障，需登 GitHub 查 Actions 日志。
Run ID: ${newRunId}
"@
Write-Output $alertMsg

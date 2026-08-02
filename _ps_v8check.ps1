Set-Location E:\workspace\quant-scanner-v8
$env:PATH = 'E:\.workbuddy\vendor\PortableGit\mingw64\bin;' + $env:PATH
$env:GIT_PAGER = 'cat'
# 看每个 8 点后 commit 改动文件及概览
& git --no-pager log --since=2026-08-02T08:00 --reverse --stat --pretty=format:'===%h %ad %s===' --date=iso | Out-String

$env:Path = "C:\Program Files\Git\bin;C:\Program Files\Git\cmd;" + $env:Path
Set-Location 'E:\workspace\stock-scanner\repo-temp'
& 'C:\Users\Administrator\AppData\Local\Microsoft\WindowsApps\python.exe' 'E:\workspace\stock-scanner\repo-temp\deploy_now.py' --force
#!/usr/bin/env bash
# 午后 fetch 并行运行器（带网络容错重试）
set -u
cd /e/workspace/stock-scanner/repo-temp || exit 1
PY=C:/Users/Administrator/AppData/Local/Microsoft/WindowsApps/python.exe
mkdir -p logs

NET_RE="DNS|502|NameResolution|ConnectionError|URLError|Timeout|网络|timed out|getaddrinfo|RemoteDisconnected"

run_fetch() {
  local name="$1"; shift
  local log="logs/${name}.log"
  for attempt in 1 2; do
    "$@" > "$log" 2>&1
    local code=$?
    if [ $code -eq 0 ]; then
      echo "[$name] OK (attempt $attempt)"
      return 0
    fi
    if grep -qiE "$NET_RE" "$log" && [ $attempt -eq 1 ]; then
      echo "[$name] network error, retry after 30s"
      sleep 30
      continue
    fi
    echo "[$name] FAILED (attempt $attempt) exit=$code"
    return 1
  done
}

run_fetch fetch_up_down_stats  "$PY" fetch_up_down_stats.py & \
run_fetch fetch_nt_data        "$PY" fetch_nt_data.py & \
run_fetch fetch_sector_fund_flow "$PY" fetch_sector_fund_flow.py & \
run_fetch fetch_etf_subscription "$PY" fetch_etf_subscription.py & \
run_fetch fetch_market_alerts  "$PY" fetch_market_alerts.py & \
run_fetch fetch_sh_sz_history  "$PY" fetch_sh_sz_history.py & \
run_fetch fetch_margin         "$PY" fetch_margin.py & \
wait
echo "ALL FETCH DONE"

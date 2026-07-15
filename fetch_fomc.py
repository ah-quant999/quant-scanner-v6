#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOMC 美联储议息数据采集
从 akshare 宏观数据接口拉取最近一次 FOMC 会议概要
若 akshare 数据滞后，用已知日程推算下次会议日期
"""
import json
import os
import sys
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(PROJECT_ROOT, "data", "fomc_summary.json")

# 2026 年 FOMC 会议日程（官方公布）
FOMC_2026_DATES = [
    "2026-01-28", "2026-03-18", "2026-05-06",
    "2026-06-17", "2026-07-29", "2026-09-23",
    "2026-11-04", "2026-12-16"
]

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def _is_nan(v):
    if v is None:
        return True
    try:
        import math
        if isinstance(v, float) and math.isnan(v):
            return True
    except:
        pass
    if str(v).lower() in ('nan', 'none', 'null', ''):
        return True
    return False

def _find_next_meeting(today_str):
    """根据官方日程返回下一个/当前会议日期"""
    for d in FOMC_2026_DATES:
        if d >= today_str:
            return d
    return FOMC_2026_DATES[-1]

def fetch_fomc():
    """获取 FOMC 最新数据"""
    try:
        import akshare as ak
        import pandas as pd
        # 美联储利率决议历史
        df = ak.macro_bank_usa_interest_rate()
        if df is None or len(df) == 0:
            log("未获取到美联储利率数据")
            return None
        
        # 找最近一条有效利率记录
        last_rate = None
        last_rate_date = None
        for idx in reversed(range(len(df))):
            row = df.iloc[idx]
            val = row.get('今值')
            if not _is_nan(val):
                last_rate = val
                last_rate_date = str(row.get('日期', ''))
                break
        
        # 最新一行（可能含 NaN）
        latest = df.iloc[-1]
        meeting_date_raw = str(latest.get('日期', ''))
        meeting_date = meeting_date_raw.replace('年', '-').replace('月', '-').replace('日', '')
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        next_meeting = _find_next_meeting(today_str)
        
        result = {
            "meeting_date": meeting_date,
            "next_meeting_date": next_meeting,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": ""
        }
        
        if last_rate is not None:
            result["summary"] = f"当前利率 {last_rate}%（上次有效决议 {last_rate_date}），下次会议 {next_meeting}"
            result["last_rate"] = last_rate
            result["last_rate_date"] = last_rate_date
        else:
            result["summary"] = f"下次 FOMC 会议 {next_meeting}"
        
        log(f"最新FOMC: {result['summary']}")
        return result
        
    except Exception as e:
        log(f"FOMC数据获取失败: {e}")
        return None

def main():
    log("=" * 40)
    log("FOMC 数据采集")
    
    data = fetch_fomc()
    if data and data["summary"]:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f"✅ 已保存: {DATA_FILE}")
    else:
        log("⚠️ 未获取到有效FOMC数据，保留现有文件")

if __name__ == "__main__":
    from fetch_logger import record_success, record_failure
    try:
        main()
        record_success(__file__)
    except Exception as e:
        record_failure(__file__, str(e))
        raise

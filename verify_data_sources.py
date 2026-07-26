#!/usr/bin/env python3
"""
数据源验证脚本 — 对比本地JSON与官网数据
验证：north_fund / main_stock / sector_fund_flow / herding_data
"""
import json
import os
import sys
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(name):
    path = os.path.join(DATA_DIR, name)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_freshness(data, name, max_hours=48):
    """检查数据新鲜度"""
    update_time = data.get("update_time", "")
    if not update_time:
        return f"  ⚠️  {name}: 无 update_time"
    
    try:
        # 尝试解析时间
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"]:
            try:
                dt = datetime.strptime(update_time.strip(), fmt)
                hours_ago = (datetime.now() - dt).total_seconds() / 3600
                if hours_ago > max_hours:
                    return f"  ❌ {name}: 数据过期 {hours_ago:.1f} 小时 (update_time={update_time})"
                else:
                    return f"  ✅ {name}: 数据新鲜 ({hours_ago:.1f} 小时前)"
            except ValueError:
                continue
        return f"  ⚠️  {name}: 无法解析 update_time={update_time}"
    except Exception as e:
        return f"  ⚠️  {name}: 时间解析异常 {e}"

def verify_north_fund_locally(data):
    """本地验证 north_fund.json 数据合理性"""
    issues = []
    
    # 检查关键字段
    if not data.get("south_flow") and not data.get("north_info"):
        issues.append("  无 south_flow 或 north_info 数据")
    
    # 检查 south_individual（南向资金个股）
    south_ind = data.get("south_individual", {})
    if south_ind and "stocks" in south_ind:
        stocks = south_ind["stocks"]
        if len(stocks) > 0:
            # 检查第一只股票的关键字段
            s = stocks[0]
            required = ["code", "name", "change_pct", "south_flow"]
            missing = [f for f in required if f not in s]
            if missing:
                issues.append(f"  south_individual.stocks[0] 缺字段: {missing}")
    
    # 检查日期合理性
    data_date = data.get("data_date", "")
    if data_date:
        try:
            dt = datetime.strptime(data_date, "%Y-%m-%d")
            if dt > datetime.now():
                issues.append(f"  data_date 在未来: {data_date}")
        except:
            issues.append(f"  data_date 格式异常: {data_date}")
    
    return issues

def verify_main_stock_locally(data):
    """本地验证 main_stock.json 数据合理性"""
    issues = []
    
    top_in = data.get("top_main_in", [])
    top_out = data.get("top_main_out", [])
    
    if len(top_in) == 0:
        issues.append("  top_main_in 为空")
    else:
        # 检查第一只股票
        s = top_in[0]
        required = ["code", "name", "net_in"]
        missing = [f for f in required if f not in s]
        if missing:
            issues.append(f"  top_main_in[0] 缺字段: {missing}")
        
        # 检查 net_in 合理性
        if "net_in" in s:
            val = s["net_in"]
            if abs(val) > 1000:  # 超过1000亿不合理
                issues.append(f"  top_main_in[0].net_in 异常: {val}")
    
    if len(top_out) == 0:
        issues.append("  top_main_out 为空")
    
    return issues

def verify_sector_fund_locally(data):
    """本地验证 sector_fund_flow.json 数据合理性"""
    issues = []
    
    sectors_in = data.get("sectors_in", [])
    sectors_out = data.get("sectors_out", [])
    
    if len(sectors_in) == 0:
        issues.append("  sectors_in 为空")
    if len(sectors_out) == 0:
        issues.append("  sectors_out 为空")
    
    # 检查板块名称非空
    if sectors_in:
        empty_names = [s for s in sectors_in if not s.get("name")]
        if empty_names:
            issues.append(f"  sectors_in 有 {len(empty_names)} 个空名称")
    
    return issues

def verify_herding_locally(data):
    """本地验证 herding_data.json 数据合理性"""
    issues = []
    
    if not isinstance(data, dict):
        issues.append("  herding_data.json 根不是dict")
        return issues
    
    clusters = data.get("clusters", 0)
    high_prob = data.get("high_prob", 0)
    
    if clusters == 0 and high_prob == 0:
        issues.append("  clusters=0 且 high_prob=0（可能是空数据）")
    
    return issues

def main():
    print("=" * 60)
    print("数据源验证（本地合理性检查 + 新鲜度检查）")
    print("=" * 60)
    
    all_passed = True
    
    # 验证文件列表
    files = [
        ("north_fund.json", verify_north_fund_locally),
        ("main_stock.json", verify_main_stock_locally),
        ("sector_fund_flow.json", verify_sector_fund_locally),
        ("herding_data.json", verify_herding_locally),
    ]
    
    for fname, verify_func in files:
        print(f"\n📋 验证 {fname}:")
        data = load_json(fname)
        
        if data is None:
            print(f"  ❌ 文件不存在")
            all_passed = False
            continue
        
        # 新鲜度检查
        freshness = check_freshness(data, fname)
        print(freshness)
        if "❌" in freshness:
            all_passed = False
        
        # 本地合理性检查
        issues = verify_func(data)
        if issues:
            for issue in issues:
                print(issue)
                all_passed = False
        else:
            print(f"  ✅ 数据合理性检查通过")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有数据验证通过")
    else:
        print("⚠️  发现数据问题，请检查上述异常")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

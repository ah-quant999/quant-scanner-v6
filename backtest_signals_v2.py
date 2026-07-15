#!/usr/bin/env python3
"""
核心信号历史回测脚本 v2
使用 akshare 获取真实历史价格，计算信号准确率
"""
import json
import os
import sys
import glob
from datetime import datetime, timedelta

# 尝试导入 pandas
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("⚠️ pandas 未安装，将使用简化模式")

def load_historical_scans():
    """加载 backup 目录中的历史扫描结果"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backup_dirs = sorted(glob.glob(os.path.join(script_dir, "backup_*")))
    
    scans = []
    for d in backup_dirs:
        path = os.path.join(d, "data", "scan_result.json")
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_source_dir"] = d
                scans.append(data)
        except Exception as e:
            print(f"  ⚠️ 加载失败 {path}: {e}")
    
    return scans

def extract_signals(scan_data):
    """提取有信号的股票（signal_count >= 2）"""
    results = scan_data.get("all_results", [])
    signals = []
    
    for stock in results:
        signal_count = stock.get("signal_count", 0)
        if signal_count >= 2:
            signals.append({
                "code": stock.get("code"),
                "name": stock.get("name"),
                "market": stock.get("market", "sh"),
                "signal_count": signal_count,
                "signals": get_signal_names(stock),
                "close_at_signal": stock.get("close"),
                "scan_time": scan_data.get("scan_time"),
            })
    
    return signals

def get_signal_names(stock):
    """获取具体信号名称"""
    names = []
    for key in ["金钻_黄柱", "金钻_起涨", "三线共振", "三足鼎立", "上涨趋势", "缠论买_日K"]:
        if stock.get(key):
            names.append(key)
    return names

def fetch_price_akshare(code, market, start_date, end_date):
    """使用 akshare 获取历史价格"""
    try:
        import akshare as ak
        import pandas as pd
        
        # 转换代码格式（akshare 需要不带前缀的代码）
        if market == "sh":
            # 上海：600XXX, 688XXX
            ak_code = code
        else:
            # 深圳：000XXX, 002XXX, 300XXX, 301XXX
            ak_code = code
        
        # 获取历史日线数据
        df = ak.stock_zh_a_hist(
            symbol=ak_code,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq"  # 前复权
        )
        
        if df is None or df.empty:
            return None
        
        # akshare 返回列名：日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
        # 重命名以便使用
        df = df.rename(columns={
            "日期": "date",
            "收盘": "close",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        })
        
        return df
        
    except Exception as e:
        return None

def calculate_signal_accuracy(signals_list):
    """计算信号准确率"""
    print(f"\n📊 回测 {len(signals_list)} 只信号股票...")
    
    results = {
        "total": len(signals_list),
        "with_price_data": 0,
        "future_1d": {"up": 0, "down": 0, "flat": 0},
        "future_3d": {"up": 0, "down": 0, "flat": 0},
        "future_5d": {"up": 0, "down": 0, "flat": 0},
        "details": [],
    }
    
    for i, signal in enumerate(signals_list):
        code = signal["code"]
        market = signal.get("market", "sh")
        scan_time = signal.get("scan_time", "")
        
        # 解析扫描时间
        try:
            if isinstance(scan_time, str):
                scan_dt = datetime.strptime(scan_time[:19], "%Y-%m-%d %H:%M:%S")
            else:
                scan_dt = datetime.now() - timedelta(days=7)  # 默认7天前
        except:
            scan_dt = datetime.now() - timedelta(days=7)
        
        # 获取扫描后1/3/5天的日期
        dates_to_check = []
        for day_offset in [1, 3, 5]:
            future_dt = scan_dt + timedelta(days=day_offset)
            # 跳过周末
            while future_dt.weekday() >= 5:  # 5=Saturday, 6=Sunday
                future_dt += timedelta(days=1)
            dates_to_check.append((day_offset, future_dt))
        
        # 获取历史价格
        start_date = scan_dt - timedelta(days=10)
        end_date = scan_dt + timedelta(days=10)
        
        df = fetch_price_akshare(code, market, start_date, end_date)
        
        if df is None or df.empty:
            results["details"].append({
                "code": code,
                "name": signal["name"],
                "price_data": "N/A",
            })
            continue
        
        results["with_price_data"] += 1
        
        # 找到扫描日的收盘价
        scan_date_str = scan_dt.strftime("%Y-%m-%d")
        df["date"] = pd.to_datetime(df["date"])
        scan_row = df[df["date"] == pd.Timestamp(scan_date_str)]
        
        if scan_row.empty:
            # 扫描日可能是非交易日，找最近交易日
            scan_row = df[df["date"] <= pd.Timestamp(scan_date_str)].tail(1)
        
        if scan_row.empty:
            continue
        
        price_at_signal = scan_row.iloc[-1]["close"]
        
        # 检查未来N天的涨跌
        for day_offset, future_dt in dates_to_check:
            future_date_str = future_dt.strftime("%Y-%m-%d")
            future_row = df[df["date"] >= pd.Timestamp(future_date_str)].head(1)
            
            if future_row.empty:
                continue
            
            future_price = future_row.iloc[0]["close"]
            return_pct = (future_price - price_at_signal) / price_at_signal * 100
            
            key = f"future_{day_offset}d"
            if return_pct > 0.5:
                results[key]["up"] += 1
            elif return_pct < -0.5:
                results[key]["down"] += 1
            else:
                results[key]["flat"] += 1
            
            results["details"].append({
                "code": code,
                "name": signal["name"],
                "signal_count": signal["signal_count"],
                "price_at_signal": price_at_signal,
                f"price_{day_offset}d": future_price,
                f"return_{day_offset}d": return_pct,
            })
    
    return results

def print_backtest_results(results):
    """打印回测结果"""
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    
    total = results["total"]
    with_data = results["with_price_data"]
    
    print(f"\n总信号股票数: {total}")
    print(f"成功获取价格数据: {with_data} ({with_data/total*100:.1f}%)")
    
    for day in [1, 3, 5]:
        key = f"future_{day}d"
        up = results[key]["up"]
        down = results[key]["down"]
        flat = results[key]["flat"]
        total_check = up + down + flat
        
        if total_check == 0:
            print(f"\n未来{day}天: 无数据")
            continue
        
        accuracy = up / total_check * 100
        print(f"\n未来{day}天收益率:")
        print(f"  上涨: {up} ({up/total_check*100:.1f}%)")
        print(f"  下跌: {down} ({down/total_check*100:.1f}%)")
        print(f"  平盘: {flat} ({flat/total_check*100:.1f}%)")
        print(f"  准确率(上涨概率): {accuracy:.1f}%")
    
    print("\n" + "=" * 60)
    
    # 判断信号是否有价值
    for day in [1, 3, 5]:
        key = f"future_{day}d"
        up = results[key]["up"]
        total_check = up + results[key]["down"] + results[key]["flat"]
        
        if total_check == 0:
            continue
        
        accuracy = up / total_check * 100
        if accuracy > 55:
            print(f"✅ 未来{day}天准确率 {accuracy:.1f}% — 信号有价值!")
        elif accuracy > 50:
            print(f"⚠️  未来{day}天准确率 {accuracy:.1f}% — 信号略有价值")
        else:
            print(f"❌ 未来{day}天准确率 {accuracy:.1f}% — 信号无价值!")

def main():
    print("=" * 60)
    print("核心信号历史回测 v2")
    print("=" * 60)
    
    # 加载历史扫描
    print("\n📊 加载历史扫描数据...")
    scans = load_historical_scans()
    print(f"  加载了 {len(scans)} 个历史扫描结果")
    
    if len(scans) == 0:
        print("  ❌ 无历史数据，无法回测")
        return False
    
    # 提取所有信号
    print("\n📊 提取有信号的股票...")
    all_signals = []
    for scan in scans:
        signals = extract_signals(scan)
        all_signals.extend(signals)
    
    # 去重
    seen = set()
    unique_signals = []
    for s in all_signals:
        key = s["code"]
        if key not in seen:
            seen.add(key)
            unique_signals.append(s)
    
    print(f"  共有 {len(unique_signals)} 只股票有信号（去重后）")
    
    if len(unique_signals) == 0:
        print("  ❌ 无信号股票，无法回测")
        return False
    
    # 运行回测
    try:
        import pandas as pd
        results = calculate_signal_accuracy(unique_signals)
        print_backtest_results(results)
        
        # 保存详细结果
        output_path = os.path.join(os.path.dirname(__file__), "backtest_result.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n✅ 详细结果已保存: {output_path}")
        
    except ImportError:
        print("\n⚠️  需要安装 pandas: pip install pandas")
        print("  将使用简化模式（不计算收益率）")
        # 简化模式：只输出信号列表
        output = {
            "total": len(unique_signals),
            "signals": unique_signals[:50],
        }
        output_path = os.path.join(os.path.dirname(__file__), "backtest_signals_list.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"✅ 信号列表已保存: {output_path}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

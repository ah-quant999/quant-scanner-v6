#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
is_trading_day.py — A股交易日判断（周末 + 法定假日 + 调休补班）

判断今天（或指定日期）是否为 A股交易日。非交易日 = 周末（除非调休补班）
或沪深交易所公告的法定休市日。

用法（命令行）：
  python is_trading_day.py            # 判断今天
  python is_trading_day.py 2026-10-02 # 判断指定日期 YYYY-MM-DD
  → 输出 TRADING / CLOSED <原因>，交易日 exit 0，休市 exit 1

作为模块：
  from is_trading_day import is_trading_day
  if not is_trading_day():
      print("非交易日，跳过"); sys.exit(0)

──────────────────────────────────────────────────────────
⚠️ 数据来源与维护义务（每年必须更新！）
  休市区间：上海证券交易所 2026 年休市安排公告
    https://www.sse.com.cn/disclosure/dealinstruc/closed/
    （2025-12-22 发布，证监办发〔2025〕130号）
  补班开市日：国务院办公厅关于 2026 年部分节假日安排的通知
    https://www.gov.cn/zhengce/content/202511/content_7047090.htm
  （2026 补班开市：1/4、2/14、2/28、5/9、9/20、10/10 共 6 个周末上班日）
  每年 12 月交易所/国务院发布新一年安排后，必须同步更新下方
  HOLIDAY_RANGES 与 MAKEUP_TRADING_DAYS，否则会误跳过真交易日或误跑休市日。
"""
import sys
import datetime

# 2026 A股休市区间（闭区间，含跨周末连休的整段闭市日）
# 来源：上交所 2026 年休市安排公告（已与上交所/国务院官方公告核对）
HOLIDAY_RANGES = [
    ("01-01", "01-03"),  # 元旦：1/1(四)-1/3(六)，1/4(日)为补班开市见下
    ("02-15", "02-23"),  # 春节：2/15(日)-2/23(一)，2/14/2/28 补班开市见下
    ("04-04", "04-06"),  # 清明：4/4(六)-4/6(一)
    ("05-01", "05-05"),  # 劳动：5/1(五)-5/5(二)，5/9(六)补班开市见下
    ("06-19", "06-21"),  # 端午：6/19(五)-6/21(日)
    ("09-25", "09-27"),  # 中秋：9/25(五)-9/27(日)，9/20(日)补班开市见下
    ("10-01", "10-07"),  # 国庆：10/1(四)-10/7(三)，10/10(六)补班开市见下
]

# 2026 调休补班开市日（周末但 A股开市）—— 必须放行，否则误丢数据
# 来源：国务院办公厅 2026 年节假日安排通知（证监办发〔2025〕130号）
MAKEUP_TRADING_DAYS = {
    datetime.date(2026, 1, 4),
    datetime.date(2026, 2, 14),
    datetime.date(2026, 2, 28),
    datetime.date(2026, 5, 9),
    datetime.date(2026, 9, 20),
    datetime.date(2026, 10, 10),
}


def _in_holiday(d: datetime.date) -> bool:
    key = (d.month, d.day)
    for start, end in HOLIDAY_RANGES:
        sm, sd = map(int, start.split("-"))
        em, ed = map(int, end.split("-"))
        if (sm, sd) <= key <= (em, ed):
            return True
    return False


def is_holiday(date: datetime.date = None) -> bool:
    """返回 True 表示该日期落在 A股法定休市区间内（含假期内的周末，如国庆周六 10/3）。

    设计要点：
      - 补班开市日（周末但开市）→ 返回 False（不是休市）。
      - 纯周末（不在法定假期内）→ 返回 False，由调用方按"周末"逻辑处理，
        不要把普通周六误判成法定假日。
    用途：batch_update 守卫需区分"周六 T+1 放行"与"周六但法定假日应跳过"。
    """
    d = date or datetime.date.today()
    if d in MAKEUP_TRADING_DAYS:
        return False
    return _in_holiday(d)


def is_trading_day(date: datetime.date = None) -> bool:
    """返回 True=交易日（应跑），False=休市（应跳过）。

    date 缺省为今天。补班开市日（周末上班）视为交易日。
    """
    d = date or datetime.date.today()
    if d in MAKEUP_TRADING_DAYS:
        return True
    if d.weekday() >= 5:  # 5=周六, 6=周日（且非补班）
        return False
    if _in_holiday(d):
        return False
    return True


def closed_reason(date: datetime.date = None) -> str:
    """返回休市原因字符串（'周末' / '法定假日' / '' 表示交易日）。"""
    d = date or datetime.date.today()
    if is_trading_day(d):
        return ""
    if d.weekday() >= 5:
        return "周末"
    return "法定假日"


def main():
    if len(sys.argv) > 1:
        try:
            d = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
        except ValueError:
            print("日期格式错误，应为 YYYY-MM-DD")
            return 2
    else:
        d = datetime.date.today()
    if is_trading_day(d):
        print("TRADING %s" % d.isoformat())
        return 0
    print("CLOSED %s (%s)" % (d.isoformat(), closed_reason(d)))
    return 1


if __name__ == "__main__":
    sys.exit(main())


function getLatestPredictTime() {
  var times = [];
  if (HERRING_DATA && HERRING_DATA.update_time) times.push(HERRING_DATA.update_time);
  if (window.LHB_DATA && window.LHB_DATA.update_time) times.push(window.LHB_DATA.update_time);
  if (MAIN_STOCK_DATA && MAIN_STOCK_DATA.update_time) times.push(MAIN_STOCK_DATA.update_time);
  if (!times.length) return '';
  times.sort();
  return times[times.length - 1];
}

// ===== 板块强度追踪 =====
window.SECTOR_RS = {
"update_time": "2026-07-01 19:28",
"sectors": [
{
"name": "航天装备Ⅱ",
"pct_day": 2.18,
"pct_5d": 12.58,
"pct_20d": 8.5,
"pct_52w": 109.63,
"relative_5d": 11.69,
"relative_20d": 7.61
},
{
"name": "电子化学品Ⅱ",
"pct_day": -0.77,
"pct_5d": 10.89,
"pct_20d": 50.07,
"pct_52w": 209.4,
"relative_5d": 10.0,
"relative_20d": 49.18
},
{
"name": "养殖业",
"pct_day": 6.41,
"pct_5d": 10.89,
"pct_20d": -1.54,
"pct_52w": -13.94,
"relative_5d": 10.0,
"relative_20d": -2.43
},
{
"name": "工程咨询服务Ⅱ",
"pct_day": 4.64,
"pct_5d": 10.29,
"pct_20d": 16.47,
"pct_52w": 30.19,
"relative_5d": 9.4,
"relative_20d": 15.58
},
{
"name": "半导体",
"pct_day": -1.95,
"pct_5d": 10.0,
"pct_20d": 39.22,
"pct_52w": 184.32,
"relative_5d": 9.11,
"relative_20d": 38.33
},
{
"name": "光学光电子",
"pct_day": 0.02,
"pct_5d": 9.45,
"pct_20d": 25.52,
"pct_52w": 71.99,
"relative_5d": 8.56,
"relative_20d": 24.63
},
{
"name": "玻璃玻纤",
"pct_day": -2.66,
"pct_5d": 4.75,
"pct_20d": 48.09,
"pct_52w": 302.34,
"relative_5d": 3.86,
"relative_20d": 47.2
},
{
"name": "其他电子Ⅱ",
"pct_day": -1.81,
"pct_5d": -2.52,
"pct_20d": 18.52,
"pct_52w": 102.92,
"relative_5d": -3.41,
"relative_20d": 17.63
},
{
"name": "小金属",
"pct_day": -0.7,
"pct_5d": -1.85,
"pct_20d": 18.46,
"pct_52w": 158.85,
"relative_5d": -2.74,
"relative_20d": 17.57
},
{
"name": "通信设备",
"pct_day": -4.3,
"pct_5d": -5.91,
"pct_20d": 6.64,
"pct_52w": 277.79,
"relative_5d": -6.8,
"relative_20d": 5.75
},
{
"name": "元件",
"pct_day": -3.21,
"pct_5d": -0.09,
"pct_20d": 15.0,
"pct_52w": 249.81,
"relative_5d": -0.98,
"relative_20d": 14.11
}
],
"strong_5d": [
{
"name": "航天装备Ⅱ",
"pct_day": 2.18,
"pct_5d": 12.58,
"pct_20d": 8.5,
"pct_52w": 109.63,
"relative_5d": 11.69,
"relative_20d": 7.61
},
{
"name": "电子化学品Ⅱ",
"pct_day": -0.77,
"pct_5d": 10.89,
"pct_20d": 50.07,
"pct_52w": 209.4,
"relative_5d": 10.0,
"relative_20d": 49.18
},
{
"name": "养殖业",
"pct_day": 6.41,
"pct_5d": 10.89,
"pct_20d": -1.54,
"pct_52w": -13.94,
"relative_5d": 10.0,
"relative_20d": -2.43
},
{
"name": "工程咨询服务Ⅱ",
"pct_day": 4.64,
"pct_5d": 10.29,
"pct_20d": 16.47,
"pct_52w": 30.19,
"relative_5d": 9.4,
"relative_20d": 15.58
},
{
"name": "半导体",
"pct_day": -1.95,
"pct_5d": 10.0,
"pct_20d": 39.22,
"pct_52w": 184.32,
"relative_5d": 9.11,
"relative_20d": 38.33
},
{
"name": "光学光电子",
"pct_day": 0.02,
"pct_5d": 9.45,
"pct_20d": 25.52,
"pct_52w": 71.99,
"relative_5d": 8.56,
"relative_20d": 24.63
},
{
"name": "玻璃玻纤",
"pct_day": -2.66,
"pct_5d": 4.75,
"pct_20d": 48.09,
"pct_52w": 302.34,
"relative_5d": 3.86,
"relative_20d": 47.2
},
{
"name": "元件",
"pct_day": -3.21,
"pct_5d": -0.09,
"pct_20d": 15.0,
"pct_52w": 249.81,
"relative_5d": -0.98,
"relative_20d": 14.11
},
{
"name": "小金属",
"pct_day": -0.7,
"pct_5d": -1.85,
"pct_20d": 18.46,
"pct_52w": 158.85,
"relative_5d": -2.74,
"relative_20d": 17.57
},
{
"name": "其他电子Ⅱ",
"pct_day": -1.81,
"pct_5d": -2.52,
"pct_20d": 18.52,
"pct_52w": 102.92,
"relative_5d": -3.41,
"relative_20d": 17.63
}
],
"strong_20d": [
{
"name": "电子化学品Ⅱ",
"pct_day": -0.77,
"pct_5d": 10.89,
"pct_20d": 50.07,
"pct_52w": 209.4,
"relative_5d": 10.0,
"relative_20d": 49.18
},
{
"name": "玻璃玻纤",
"pct_day": -2.66,
"pct_5d": 4.75,
"pct_20d": 48.09,
"pct_52w": 302.34,
"relative_5d": 3.86,
"relative_20d": 47.2
},
{
"name": "半导体",
"pct_day": -1.95,
"pct_5d": 10.0,
"pct_20d": 39.22,
"pct_52w": 184.32,
"relative_5d": 9.11,
"relative_20d": 38.33
},
{
"name": "光学光电子",
"pct_day": 0.02,
"pct_5d": 9.45,
"pct_20d": 25.52,
"pct_52w": 71.99,
"relative_5d": 8.56,
"relative_20d": 24.63
},
{
"name": "其他电子Ⅱ",
"pct_day": -1.81,
"pct_5d": -2.52,
"pct_20d": 18.52,
"pct_52w": 102.92,
"relative_5d": -3.41,
"relative_20d": 17.63
},
{
"name": "小金属",
"pct_day": -0.7,
"pct_5d": -1.85,
"pct_20d": 18.46,
"pct_52w": 158.85,
"relative_5d": -2.74,
"relative_20d": 17.57
},
{
"name": "工程咨询服务Ⅱ",
"pct_day": 4.64,
"pct_5d": 10.29,
"pct_20d": 16.47,
"pct_52w": 30.19,
"relative_5d": 9.4,
"relative_20d": 15.58
},
{
"name": "元件",
"pct_day": -3.21,
"pct_5d": -0.09,
"pct_20d": 15.0,
"pct_52w": 249.81,
"relative_5d": -0.98,
"relative_20d": 14.11
},
{
"name": "航天装备Ⅱ",
"pct_day": 2.18,
"pct_5d": 12.58,
"pct_20d": 8.5,
"pct_52w": 109.63,
"relative_5d": 11.69,
"relative_20d": 7.61
},
{
"name": "通信设备",
"pct_day": -4.3,
"pct_5d": -5.91,
"pct_20d": 6.64,
"pct_52w": 277.79,
"relative_5d": -6.8,
"relative_20d": 5.75
}
],
"strong_52w": [
{
"name": "玻璃玻纤",
"pct_day": -2.66,
"pct_5d": 4.75,
"pct_20d": 48.09,
"pct_52w": 302.34,
"relative_5d": 3.86,
"relative_20d": 47.2
},
{
"name": "通信设备",
"pct_day": -4.3,
"pct_5d": -5.91,
"pct_20d": 6.64,
"pct_52w": 277.79,
"relative_5d": -6.8,
"relative_20d": 5.75
},
{
"name": "元件",
"pct_day": -3.21,
"pct_5d": -0.09,
"pct_20d": 15.0,
"pct_52w": 249.81,
"relative_5d": -0.98,
"relative_20d": 14.11
},
{
"name": "电子化学品Ⅱ",
"pct_day": -0.77,
"pct_5d": 10.89,
"pct_20d": 50.07,
"pct_52w": 209.4,
"relative_5d": 10.0,
"relative_20d": 49.18
},
{
"name": "半导体",
"pct_day": -1.95,
"pct_5d": 10.0,
"pct_20d": 39.22,
"pct_52w": 184.32,
"relative_5d": 9.11,
"relative_20d": 38.33
},
{
"name": "小金属",
"pct_day": -0.7,
"pct_5d": -1.85,
"pct_20d": 18.46,
"pct_52w": 158.85,
"relative_5d": -2.74,
"relative_20d": 17.57
},
{
"name": "航天装备Ⅱ",
"pct_day": 2.18,
"pct_5d": 12.58,
"pct_20d": 8.5,
"pct_52w": 109.63,
"relative_5d": 11.69,
"relative_20d": 7.61
},
{
"name": "其他电子Ⅱ",
"pct_day": -1.81,
"pct_5d": -2.52,
"pct_20d": 18.52,
"pct_52w": 102.92,
"relative_5d": -3.41,
"relative_20d": 17.63
},
{
"name": "光学光电子",
"pct_day": 0.02,
"pct_5d": 9.45,
"pct_20d": 25.52,
"pct_52w": 71.99,
"relative_5d": 8.56,
"relative_20d": 24.63
},
{
"name": "工程咨询服务Ⅱ",
"pct_day": 4.64,
"pct_5d": 10.29,
"pct_20d": 16.47,
"pct_52w": 30.19,
"relative_5d": 9.4,
"relative_20d": 15.58
}
],
"weak_5d": [
{
"name": "通信设备",
"pct_day": -4.3,
"pct_5d": -5.91,
"pct_20d": 6.64,
"pct_52w": 277.79,
"relative_5d": -6.8,
"relative_20d": 5.75
},
{
"name": "其他电子Ⅱ",
"pct_day": -1.81,
"pct_5d": -2.52,
"pct_20d": 18.52,
"pct_52w": 102.92,
"relative_5d": -3.41,
"relative_20d": 17.63
},
{
"name": "小金属",
"pct_day": -0.7,
"pct_5d": -1.85,
"pct_20d": 18.46,
"pct_52w": 158.85,
"relative_5d": -2.74,
"relative_20d": 17.57
},
{
"name": "元件",
"pct_day": -3.21,
"pct_5d": -0.09,
"pct_20d": 15.0,
"pct_52w": 249.81,
"relative_5d": -0.98,
"relative_20d": 14.11
},
{
"name": "玻璃玻纤",
"pct_day": -2.66,
"pct_5d": 4.75,
"pct_20d": 48.09,
"pct_52w": 302.34,
"relative_5d": 3.86,
"relative_20d": 47.2
},
{
"name": "光学光电子",
"pct_day": 0.02,
"pct_5d": 9.45,
"pct_20d": 25.52,
"pct_52w": 71.99,
"relative_5d": 8.56,
"relative_20d": 24.63
},
{
"name": "半导体",
"pct_day": -1.95,
"pct_5d": 10.0,
"pct_20d": 39.22,
"pct_52w": 184.32,
"relative_5d": 9.11,
"relative_20d": 38.33
},
{
"name": "工程咨询服务Ⅱ",
"pct_day": 4.64,
"pct_5d": 10.29,
"pct_20d": 16.47,
"pct_52w": 30.19,
"relative_5d": 9.4,
"relative_20d": 15.58
},
{
"name": "电子化学品Ⅱ",
"pct_day": -0.77,
"pct_5d": 10.89,
"pct_20d": 50.07,
"pct_52w": 209.4,
"relative_5d": 10.0,
"relative_20d": 49.18
},
{
"name": "养殖业",
"pct_day": 6.41,
"pct_5d": 10.89,
"pct_20d": -1.54,
"pct_52w": -13.94,
"relative_5d": 10.0,
"relative_20d": -2.43
}
],
"strong_relative_5d": [
{
"name": "航天装备Ⅱ",
"pct_day": 2.18,
"pct_5d": 12.58,
"pct_20d": 8.5,
"pct_52w": 109.63,
"relative_5d": 11.69,
"relative_20d": 7.61
},
{
"name": "电子化学品Ⅱ",
"pct_day": -0.77,
"pct_5d": 10.89,
"pct_20d": 50.07,
"pct_52w": 209.4,
"relative_5d": 10.0,
"relative_20d": 49.18
},
{
"name": "养殖业",
"pct_day": 6.41,
"pct_5d": 10.89,
"pct_20d": -1.54,
"pct_52w": -13.94,
"relative_5d": 10.0,
"relative_20d": -2.43
},
{
"name": "工程咨询服务Ⅱ",
"pct_day": 4.64,
"pct_5d": 10.29,
"pct_20d": 16.47,
"pct_52w": 30.19,
"relative_5d": 9.4,
"relative_20d": 15.58
},
{
"name": "半导体",
"pct_day": -1.95,
"pct_5d": 10.0,
"pct_20d": 39.22,
"pct_52w": 184.32,
"relative_5d": 9.11,
"relative_20d": 38.33
},
{
"name": "光学光电子",
"pct_day": 0.02,
"pct_5d": 9.45,
"pct_20d": 25.52,
"pct_52w": 71.99,
"relative_5d": 8.56,
"relative_20d": 24.63
},
{
"name": "玻璃玻纤",
"pct_day": -2.66,
"pct_5d": 4.75,
"pct_20d": 48.09,
"pct_52w": 302.34,
"relative_5d": 3.86,
"relative_20d": 47.2
},
{
"name": "元件",
"pct_day": -3.21,
"pct_5d": -0.09,
"pct_20d": 15.0,
"pct_52w": 249.81,
"relative_5d": -0.98,
"relative_20d": 14.11
},
{
"name": "小金属",
"pct_day": -0.7,
"pct_5d": -1.85,
"pct_20d": 18.46,
"pct_52w": 158.85,
"relative_5d": -2.74,
"relative_20d": 17.57
},
{
"name": "其他电子Ⅱ",
"pct_day": -1.81,
"pct_5d": -2.52,
"pct_20d": 18.52,
"pct_52w": 102.92,
"relative_5d": -3.41,
"relative_20d": 17.63
}
],
"strong_relative_20d": [
{
"name": "电子化学品Ⅱ",
"pct_day": -0.77,
"pct_5d": 10.89,
"pct_20d": 50.07,
"pct_52w": 209.4,
"relative_5d": 10.0,
"relative_20d": 49.18
},
{
"name": "玻璃玻纤",
"pct_day": -2.66,
"pct_5d": 4.75,
"pct_20d": 48.09,
"pct_52w": 302.34,
"relative_5d": 3.86,
"relative_20d": 47.2
},
{
"name": "半导体",
"pct_day": -1.95,
"pct_5d": 10.0,
"pct_20d": 39.22,
"pct_52w": 184.32,
"relative_5d": 9.11,
"relative_20d": 38.33
},
{
"name": "光学光电子",
"pct_day": 0.02,
"pct_5d": 9.45,
"pct_20d": 25.52,
"pct_52w": 71.99,
"relative_5d": 8.56,
"relative_20d": 24.63
},
{
"name": "其他电子Ⅱ",
"pct_day": -1.81,
"pct_5d": -2.52,
"pct_20d": 18.52,
"pct_52w": 102.92,
"relative_5d": -3.41,
"relative_20d": 17.63
},
{
"name": "小金属",
"pct_day": -0.7,
"pct_5d": -1.85,
"pct_20d": 18.46,
"pct_52w": 158.85,
"relative_5d": -2.74,
"relative_20d": 17.57
},
{
"name": "工程咨询服务Ⅱ",
"pct_day": 4.64,
"pct_5d": 10.29,
"pct_20d": 16.47,
"pct_52w": 30.19,
"relative_5d": 9.4,
"relative_20d": 15.58
},
{
"name": "元件",
"pct_day": -3.21,
"pct_5d": -0.09,
"pct_20d": 15.0,
"pct_52w": 249.81,
"relative_5d": -0.98,
"relative_20d": 14.11
},
{
"name": "航天装备Ⅱ",
"pct_day": 2.18,
"pct_5d": 12.58,
"pct_20d": 8.5,
"pct_52w": 109.63,
"relative_5d": 11.69,
"relative_20d": 7.61
},
{
"name": "通信设备",
"pct_day": -4.3,
"pct_5d": -5.91,
"pct_20d": 6.64,
"pct_52w": 277.79,
"relative_5d": -6.8,
"relative_20d": 5.75
}
],
"anti_drop": [
{
"name": "养殖业",
"pct_day": 6.41,
"pct_5d": 10.89,
"pct_20d": -1.54,
"pct_52w": -13.94,
"relative_5d": 10.0,
"relative_20d": -2.43
}
],
"index": {
"name": "沪深300",
"pct_5d": 0.89,
"pct_20d": 0.89
}
};// ===== 打新价值评分 =====
window.IPO_DATA = {
"update_time": "2026-07-01 19:31:55",
"eligible_count": 1,
"summary": "1只需谨慎参与。建议谨慎观望。",
"stocks": [
{
"code": "301583",
"name": "托伦斯",
"apply_code": "301583",
"issue_price": 22.6,
"issue_pe": 32.9,
"industry_pe": 47.9,
"pe_discount": 31.3,
"lottery_rate": 0,
"board": "创业板",
"industry": "待确认",
"apply_date": "20260701",
"score": 58,
"recommend": "谨慎参与",
"tag_color": "#f57f17",
"bg_color": "#fffde7",
"highlights": [
"发行价适中",
"首日预估收益2,100+"
]
}
]
};window.W52_HIGH = {
"update_time": "2026-07-01 19:45",
"total": 308,
"top_gainers": [
{
"code": "001399",
"name": "惠科股份",
"pct_chg": 21.21
},
{
"code": "300345",
"name": "华民股份",
"pct_chg": 20.03
},
{
"code": "300873",
"name": "海晨股份",
"pct_chg": 20.02
},
{
"code": "300607",
"name": "拓斯达",
"pct_chg": 20.01
},
{
"code": "300121",
"name": "阳谷华泰",
"pct_chg": 20.0
},
{
"code": "300487",
"name": "蓝晓科技",
"pct_chg": 20.0
},
{
"code": "300518",
"name": "新迅达",
"pct_chg": 20.0
},
{
"code": "300852",
"name": "四会富仕",
"pct_chg": 20.0
},
{
"code": "300481",
"name": "濮阳惠成",
"pct_chg": 19.98
},
{
"code": "300539",
"name": "横河精密",
"pct_chg": 19.98
},
{
"code": "300720",
"name": "海川智能",
"pct_chg": 14.66
},
{
"code": "300560",
"name": "中富通",
"pct_chg": 14.65
},
{
"code": "300566",
"name": "激智科技",
"pct_chg": 14.32
},
{
"code": "300540",
"name": "蜀道装备",
"pct_chg": 14.01
},
{
"code": "300840",
"name": "酷特智能",
"pct_chg": 13.19
}
],
"top_sectors": [],
"stocks": [
{
"code": "000004",
"name": "国华退",
"pct_chg": 8.82,
"price": 0.37,
"prev_high": 0.34,
"prev_high_date": "2026-06-30",
"turnover": 9.11
},
{
"code": "000012",
"name": "南玻A",
"pct_chg": 1.74,
"price": 5.25,
"prev_high": 5.16,
"prev_high_date": "2026-06-30",
"turnover": 10.66
},
{
"code": "000048",
"name": "京基智农",
"pct_chg": 1.86,
"price": 22.5,
"prev_high": 22.31,
"prev_high_date": "2026-06-25",
"turnover": 3.98
},
{
"code": "000100",
"name": "TCL科技",
"pct_chg": 5.16,
"price": 6.12,
"prev_high": 5.82,
"prev_high_date": "2026-06-30",
"turnover": 13.62
},
{
"code": "000404",
"name": "长虹华意",
"pct_chg": 5.47,
"price": 8.29,
"prev_high": 8.06,
"prev_high_date": "2026-06-29",
"turnover": 6.45
},
{
"code": "000417",
"name": "合百集团",
"pct_chg": 2.86,
"price": 9.0,
"prev_high": 8.75,
"prev_high_date": "2026-06-30",
"turnover": 10.9
},
{
"code": "000422",
"name": "湖北宜化",
"pct_chg": 7.12,
"price": 15.05,
"prev_high": 14.38,
"prev_high_date": "2026-06-25",
"turnover": 7.35
},
{
"code": "000521",
"name": "长虹美菱",
"pct_chg": 9.95,
"price": 5.97,
"prev_high": 5.68,
"prev_high_date": "2026-06-15",
"turnover": 6.63
},
{
"code": "000551",
"name": "创元科技",
"pct_chg": 1.79,
"price": 21.0,
"prev_high": 20.63,
"prev_high_date": "2026-06-30",
"turnover": 12.03
},
{
"code": "000566",
"name": "海南海药",
"pct_chg": 10.02,
"price": 5.49,
"prev_high": 4.99,
"prev_high_date": "2026-06-30",
"turnover": 16.0
},
{
"code": "000609",
"name": "*ST中迪",
"pct_chg": 5.0,
"price": 13.43,
"prev_high": 13.03,
"prev_high_date": "2026-06-05",
"turnover": 3.83
},
{
"code": "000620",
"name": "盈新发展",
"pct_chg": 10.0,
"price": 3.85,
"prev_high": 3.5,
"prev_high_date": "2026-06-30",
"turnover": 17.99
},
{
"code": "000623",
"name": "吉林敖东",
"pct_chg": 5.53,
"price": 18.71,
"prev_high": 18.39,
"prev_high_date": "2026-06-22",
"turnover": 2.39
},
{
"code": "000629",
"name": "钒钛股份",
"pct_chg": 6.29,
"price": 3.55,
"prev_high": 3.45,
"prev_high_date": "2026-06-01",
"turnover": 5.08
},
{
"code": "000685",
"name": "中山公用",
"pct_chg": 4.66,
"price": 11.68,
"prev_high": 11.57,
"prev_high_date": "2026-06-22",
"turnover": 2.56
},
{
"code": "000686",
"name": "东北证券",
"pct_chg": 4.17,
"price": 8.75,
"prev_high": 8.73,
"prev_high_date": "2026-06-25",
"turnover": 2.6
},
{
"code": "000725",
"name": "京东方A",
"pct_chg": 1.04,
"price": 8.77,
"prev_high": 8.68,
"prev_high_date": "2026-06-30",
"turnover": 13.08
},
{
"code": "000728",
"name": "国元证券",
"pct_chg": 4.54,
"price": 7.83,
"prev_high": 7.66,
"prev_high_date": "2026-06-26",
"turnover": 2.18
},
{
"code": "000733",
"name": "振华科技",
"pct_chg": 9.99,
"price": 62.3,
"prev_high": 60.52,
"prev_high_date": "2026-06-25",
"turnover": 2.46
},
{
"code": "000739",
"name": "普洛药业",
"pct_chg": 3.18,
"price": 17.19,
"prev_high": 17.03,
"prev_high_date": "2026-06-29",
"turnover": 1.45
},
{
"code": "000750",
"name": "国海证券",
"pct_chg": 4.89,
"price": 3.86,
"prev_high": 3.85,
"prev_high_date": "2026-06-25",
"turnover": 2.0
},
{
"code": "000756",
"name": "新华制药",
"pct_chg": 3.88,
"price": 14.72,
"prev_high": 14.19,
"prev_high_date": "2026-06-24",
"turnover": 7.71
},
{
"code": "000776",
"name": "广发证券",
"pct_chg": 6.24,
"price": 24.86,
"prev_high": 23.4,
"prev_high_date": "2026-06-30",
"turnover": 3.3
},
{
"code": "000779",
"name": "甘咨询",
"pct_chg": 1.93,
"price": 7.94,
"prev_high": 7.79,
"prev_high_date": "2026-06-30",
"turnover": 2.14
},
{
"code": "000782",
"name": "恒申新材",
"pct_chg": 6.44,
"price": 8.6,
"prev_high": 8.08,
"prev_high_date": "2026-06-30",
"turnover": 8.59
},
{
"code": "000783",
"name": "长江证券",
"pct_chg": 8.1,
"price": 10.54,
"prev_high": 10.15,
"prev_high_date": "2026-06-25",
"turnover": 7.9
},
{
"code": "000810",
"name": "创维数字",
"pct_chg": 1.06,
"price": 13.39,
"prev_high": 13.25,
"prev_high_date": "2026-06-30",
"turnover": 3.11
},
{
"code": "000818",
"name": "航锦科技",
"pct_chg": 2.27,
"price": 14.85,
"prev_high": 14.81,
"prev_high_date": "2026-06-25",
"turnover": 11.68
},
{
"code": "000925",
"name": "众合科技",
"pct_chg": 9.96,
"price": 10.27,
"prev_high": 9.52,
"prev_high_date": "2026-06-26",
"turnover": 16.71
},
{
"code": "000938",
"name": "紫光股份",
"pct_chg": 3.71,
"price": 29.93,
"prev_high": 28.86,
"prev_high_date": "2026-06-30",
"turnover": 11.86
},
{
"code": "000963",
"name": "华东医药",
"pct_chg": 5.16,
"price": 29.57,
"prev_high": 29.13,
"prev_high_date": "2026-06-11",
"turnover": 2.01
},
{
"code": "000970",
"name": "中科三环",
"pct_chg": 1.98,
"price": 15.49,
"prev_high": 15.19,
"prev_high_date": "2026-06-30",
"turnover": 10.63
},
{
"code": "001229",
"name": "魅视科技",
"pct_chg": 1.71,
"price": 36.94,
"prev_high": 36.32,
"prev_high_date": "2026-06-30",
"turnover": 21.0
},
{
"code": "001237",
"name": "惠康科技",
"pct_chg": 2.02,
"price": 73.17,
"prev_high": 72.35,
"prev_high_date": "2026-06-01",
"turnover": 35.18
},
{
"code": "001256",
"name": "炜冈科技",
"pct_chg": 10.0,
"price": 30.02,
"prev_high": 27.29,
"prev_high_date": "2026-06-30",
"turnover": 3.1
},
{
"code": "001270",
"name": "铖昌科技",
"pct_chg": 1.93,
"price": 159.0,
"prev_high": 155.99,
"prev_high_date": "2026-06-30",
"turnover": 7.11
},
{
"code": "001324",
"name": "长青科技",
"pct_chg": 8.81,
"price": 20.0,
"prev_high": 19.31,
"prev_high_date": "2026-06-01",
"turnover": 4.3
},
{
"code": "001331",
"name": "胜通能源",
"pct_chg": 10.0,
"price": 62.02,
"prev_high": 56.38,
"prev_high_date": "2026-06-30",
"turnover": 5.04
},
{
"code": "001358",
"name": "兴欣新材",
"pct_chg": 5.34,
"price": 27.22,
"prev_high": 26.05,
"prev_high_date": "2026-06-16",
"turnover": 12.8
},
{
"code": "001390",
"name": "古麒绒材",
"pct_chg": 0.94,
"price": 20.3,
"prev_high": 20.11,
"prev_high_date": "2026-06-30",
"turnover": 2.57
},
{
"code": "001399",
"name": "惠科股份",
"pct_chg": 21.21,
"price": 46.28,
"prev_high": 42.0,
"prev_high_date": "2026-06-26",
"turnover": 51.05
},
{
"code": "002020",
"name": "京新药业",
"pct_chg": 6.72,
"price": 13.33,
"prev_high": 13.12,
"prev_high_date": "2026-06-01",
"turnover": 3.85
},
{
"code": "002025",
"name": "航天电器",
"pct_chg": 5.22,
"price": 80.2,
"prev_high": 76.22,
"prev_high_date": "2026-06-30",
"turnover": 8.64
},
{
"code": "002038",
"name": "双鹭药业",
"pct_chg": 5.9,
"price": 6.28,
"prev_high": 5.93,
"prev_high_date": "2026-06-30",
"turnover": 9.66
},
{
"code": "002056",
"name": "横店东磁",
"pct_chg": 0.92,
"price": 30.76,
"prev_high": 30.52,
"prev_high_date": "2026-06-26",
"turnover": 4.93
},
{
"code": "002068",
"name": "黑猫股份",
"pct_chg": 1.86,
"price": 15.31,
"prev_high": 15.03,
"prev_high_date": "2026-06-30",
"turnover": 8.02
},
{
"code": "002106",
"name": "莱宝高科",
"pct_chg": 3.02,
"price": 18.05,
"prev_high": 17.52,
"prev_high_date": "2026-06-30",
"turnover": 16.69
},
{
"code": "002119",
"name": "康强电子",
"pct_chg": 0.7,
"price": 40.2,
"prev_high": 39.92,
"prev_high_date": "2026-06-30",
"turnover": 24.17
},
{
"code": "002120",
"name": "韵达股份",
"pct_chg": 8.18,
"price": 6.88,
"prev_high": 6.78,
"prev_high_date": "2026-06-01",
"turnover": 3.65
},
{
"code": "002167",
"name": "东方锆业",
"pct_chg": 10.01,
"price": 24.28,
"prev_high": 22.77,
"prev_high_date": "2026-06-25",
"turnover": 21.82
},
{
"code": "002182",
"name": "宝武镁业",
"pct_chg": 1.99,
"price": 15.88,
"prev_high": 15.57,
"prev_high_date": "2026-06-30",
"turnover": 7.28
},
{
"code": "002189",
"name": "中光学",
"pct_chg": 0.85,
"price": 22.55,
"prev_high": 22.36,
"prev_high_date": "2026-06-30",
"turnover": 2.96
},
{
"code": "002192",
"name": "融捷股份",
"pct_chg": 5.32,
"price": 94.16,
"prev_high": 93.39,
"prev_high_date": "2026-06-24",
"turnover": 13.84
},
{
"code": "002202",
"name": "金风科技",
"pct_chg": 3.18,
"price": 24.66,
"prev_high": 23.9,
"prev_high_date": "2026-06-30",
"turnover": 9.61
},
{
"code": "002211",
"name": "ST宏达",
"pct_chg": 3.32,
"price": 4.05,
"prev_high": 3.99,
"prev_high_date": "2026-06-24",
"turnover": 2.7
},
{
"code": "002225",
"name": "濮耐股份",
"pct_chg": 3.38,
"price": 4.89,
"prev_high": 4.73,
"prev_high_date": "2026-06-30",
"turnover": 10.24
},
{
"code": "002273",
"name": "水晶光电",
"pct_chg": 10.01,
"price": 39.03,
"prev_high": 37.18,
"prev_high_date": "2026-06-04",
"turnover": 1.08
},
{
"code": "002293",
"name": "罗莱生活",
"pct_chg": 7.79,
"price": 10.66,
"prev_high": 10.34,
"prev_high_date": "2026-06-15",
"turnover": 1.83
},
{
"code": "002294",
"name": "信立泰",
"pct_chg": 7.24,
"price": 34.2,
"prev_high": 32.99,
"prev_high_date": "2026-06-02",
"turnover": 4.27
},
{
"code": "002303",
"name": "美盈森",
"pct_chg": 0.0,
"price": 4.3,
"prev_high": 4.3,
"prev_high_date": "2026-06-30",
"turnover": 8.03
},
{
"code": "002317",
"name": "众生药业",
"pct_chg": 8.71,
"price": 26.71,
"prev_high": 24.85,
"prev_high_date": "2026-06-29",
"turnover": 10.1
},
{
"code": "002326",
"name": "永太科技",
"pct_chg": 10.02,
"price": 26.02,
"prev_high": 25.48,
"prev_high_date": "2026-06-25",
"turnover": 7.22
},
{
"code": "002338",
"name": "奥普光电",
"pct_chg": 0.87,
"price": 57.7,
"prev_high": 57.2,
"prev_high_date": "2026-06-30",
"turnover": 4.29
},
{
"code": "002354",
"name": "天娱数科",
"pct_chg": 1.07,
"price": 9.4,
"prev_high": 9.3,
"prev_high_date": "2026-06-30",
"turnover": 32.33
},
{
"code": "002367",
"name": "康力电梯",
"pct_chg": 2.17,
"price": 7.06,
"prev_high": 6.91,
"prev_high_date": "2026-06-30",
"turnover": 3.51
},
{
"code": "002371",
"name": "北方华创",
"pct_chg": 5.74,
"price": 935.36,
"prev_high": 884.56,
"prev_high_date": "2026-06-30",
"turnover": 2.02
},
{
"code": "002386",
"name": "天原股份",
"pct_chg": 2.74,
"price": 6.37,
"prev_high": 6.2,
"prev_high_date": "2026-06-30",
"turnover": 3.4
},
{
"code": "002402",
"name": "和而泰",
"pct_chg": 3.99,
"price": 26.86,
"prev_high": 26.44,
"prev_high_date": "2026-06-01",
"turnover": 11.41
},
{
"code": "002407",
"name": "多氟多",
"pct_chg": 9.99,
"price": 55.25,
"prev_high": 50.23,
"prev_high_date": "2026-06-30",
"turnover": 6.57
},
{
"code": "002409",
"name": "雅克科技",
"pct_chg": 5.16,
"price": 236.09,
"prev_high": 224.5,
"prev_high_date": "2026-06-30",
"turnover": 14.12
},
{
"code": "002422",
"name": "科伦药业",
"pct_chg": 8.9,
"price": 41.95,
"prev_high": 39.16,
"prev_high_date": "2026-06-29",
"turnover": 3.86
},
{
"code": "002430",
"name": "杭氧股份",
"pct_chg": 4.33,
"price": 32.3,
"prev_high": 30.96,
"prev_high_date": "2026-06-30",
"turnover": 5.21
},
{
"code": "002458",
"name": "益生股份",
"pct_chg": 10.04,
"price": 8.55,
"prev_high": 8.39,
"prev_high_date": "2026-06-01",
"turnover": 8.55
},
{
"code": "002468",
"name": "申通快递",
"pct_chg": 10.03,
"price": 16.02,
"prev_high": 15.03,
"prev_high_date": "2026-06-01",
"turnover": 3.07
},
{
"code": "002485",
"name": "ST雪发",
"pct_chg": 2.63,
"price": 5.86,
"prev_high": 5.71,
"prev_high_date": "2026-06-30",
"turnover": 2.86
},
{
"code": "002500",
"name": "山西证券",
"pct_chg": 4.07,
"price": 5.37,
"prev_high": 5.31,
"prev_high_date": "2026-06-25",
"turnover": 1.54
},
{
"code": "002549",
"name": "凯美特气",
"pct_chg": 6.08,
"price": 22.33,
"prev_high": 21.05,
"prev_high_date": "2026-06-30",
"turnover": 18.2
},
{
"code": "002550",
"name": "千红制药",
"pct_chg": 9.66,
"price": 6.81,
"prev_high": 6.51,
"prev_high_date": "2026-06-24",
"turnover": 7.28
},
{
"code": "002558",
"name": "巨人网络",
"pct_chg": 2.0,
"price": 28.11,
"prev_high": 27.73,
"prev_high_date": "2026-06-25",
"turnover": 6.24
},
{
"code": "002559",
"name": "亚威股份",
"pct_chg": 9.99,
"price": 13.98,
"prev_high": 13.0,
"prev_high_date": "2026-06-29",
"turnover": 4.1
},
{
"code": "002628",
"name": "成都路桥",
"pct_chg": 1.31,
"price": 5.42,
"prev_high": 5.35,
"prev_high_date": "2026-06-30",
"turnover": 7.85
},
{
"code": "002631",
"name": "德尔未来",
"pct_chg": 1.68,
"price": 11.48,
"prev_high": 11.29,
"prev_high_date": "2026-06-30",
"turnover": 10.79
},
{
"code": "002635",
"name": "安洁科技",
"pct_chg": 10.02,
"price": 22.5,
"prev_high": 20.45,
"prev_high_date": "2026-06-30",
"turnover": 1.45
},
{
"code": "002643",
"name": "万润股份",
"pct_chg": 4.15,
"price": 21.82,
"prev_high": 20.95,
"prev_high_date": "2026-06-30",
"turnover": 6.36
},
{
"code": "002653",
"name": "海思科",
"pct_chg": 9.98,
"price": 72.96,
"prev_high": 66.34,
"prev_high_date": "2026-06-30",
"turnover": 4.19
},
{
"code": "002687",
"name": "乔治白",
"pct_chg": 3.63,
"price": 5.43,
"prev_high": 5.24,
"prev_high_date": "2026-06-30",
"turnover": 11.37
},
{
"code": "002698",
"name": "博实股份",
"pct_chg": 10.03,
"price": 13.28,
"prev_high": 12.8,
"prev_high_date": "2026-06-08",
"turnover": 4.85
},
{
"code": "002728",
"name": "特一药业",
"pct_chg": 5.03,
"price": 9.61,
"prev_high": 9.15,
"prev_high_date": "2026-06-30",
"turnover": 11.08
},
{
"code": "002738",
"name": "中矿资源",
"pct_chg": 10.0,
"price": 64.89,
"prev_high": 62.84,
"prev_high_date": "2026-06-22",
"turnover": 2.77
},
{
"code": "002747",
"name": "埃斯顿",
"pct_chg": 9.99,
"price": 41.06,
"prev_high": 38.25,
"prev_high_date": "2026-06-23",
"turnover": 6.92
},
{
"code": "002755",
"name": "奥赛康",
"pct_chg": 6.61,
"price": 14.52,
"prev_high": 14.21,
"prev_high_date": "2026-06-01",
"turnover": 1.9
},
{
"code": "002773",
"name": "康弘药业",
"pct_chg": 8.07,
"price": 22.1,
"prev_high": 20.94,
"prev_high_date": "2026-06-04",
"turnover": 2.86
},
{
"code": "002774",
"name": "快意电梯",
"pct_chg": 2.11,
"price": 14.51,
"prev_high": 14.21,
"prev_high_date": "2026-06-30",
"turnover": 3.53
},
{
"code": "002785",
"name": "万里石",
"pct_chg": 3.32,
"price": 45.78,
"prev_high": 44.5,
"prev_high_date": "2026-06-25",
"turnover": 4.03
},
{
"code": "002787",
"name": "华源控股",
"pct_chg": 4.97,
"price": 33.8,
"prev_high": 32.47,
"prev_high_date": "2026-06-26",
"turnover": 10.71
},
{
"code": "002808",
"name": "恒久退",
"pct_chg": 9.52,
"price": 0.23,
"prev_high": 0.21,
"prev_high_date": "2026-06-30",
"turnover": 4.68
},
{
"code": "002822",
"name": "ST中装",
"pct_chg": 5.0,
"price": 3.36,
"prev_high": 3.2,
"prev_high_date": "2026-06-30",
"turnover": 1.1
},
{
"code": "002828",
"name": "贝肯能源",
"pct_chg": 3.97,
"price": 10.99,
"prev_high": 10.59,
"prev_high_date": "2026-06-29",
"turnover": 11.45
},
{
"code": "002830",
"name": "名雕股份",
"pct_chg": 4.45,
"price": 18.06,
"prev_high": 17.77,
"prev_high_date": "2026-06-23",
"turnover": 14.74
},
{
"code": "002845",
"name": "同兴达",
"pct_chg": 0.12,
"price": 16.42,
"prev_high": 16.4,
"prev_high_date": "2026-06-30",
"turnover": 10.99
},
{
"code": "002860",
"name": "星帅尔",
"pct_chg": 2.33,
"price": 14.93,
"prev_high": 14.59,
"prev_high_date": "2026-06-30",
"turnover": 6.26
},
{
"code": "002861",
"name": "瀛通通讯",
"pct_chg": 5.79,
"price": 23.57,
"prev_high": 22.28,
"prev_high_date": "2026-06-30",
"turnover": 5.85
},
{
"code": "002871",
"name": "伟隆股份",
"pct_chg": 4.12,
"price": 23.23,
"prev_high": 22.46,
"prev_high_date": "2026-06-02",
"turnover": 9.01
},
{
"code": "002907",
"name": "华森制药",
"pct_chg": 6.41,
"price": 14.12,
"prev_high": 13.84,
"prev_high_date": "2026-06-29",
"turnover": 3.74
},
{
"code": "002921",
"name": "联诚精密",
"pct_chg": 8.7,
"price": 29.72,
"prev_high": 27.34,
"prev_high_date": "2026-06-30",
"turnover": 13.4
},
{
"code": "002925",
"name": "盈趣科技",
"pct_chg": 2.51,
"price": 25.28,
"prev_high": 25.0,
"prev_high_date": "2026-06-26",
"turnover": 3.76
},
{
"code": "002929",
"name": "润建股份",
"pct_chg": 10.0,
"price": 73.57,
"prev_high": 70.5,
"prev_high_date": "2026-06-01",
"turnover": 18.96
},
{
"code": "002935",
"name": "天奥电子",
"pct_chg": 4.92,
"price": 23.02,
"prev_high": 22.24,
"prev_high_date": "2026-06-15",
"turnover": 4.91
},
{
"code": "002979",
"name": "雷赛智能",
"pct_chg": 3.05,
"price": 57.48,
"prev_high": 55.96,
"prev_high_date": "2026-06-17",
"turnover": 9.75
},
{
"code": "002983",
"name": "芯瑞达",
"pct_chg": 1.12,
"price": 27.99,
"prev_high": 27.68,
"prev_high_date": "2026-06-30",
"turnover": 9.0
},
{
"code": "300005",
"name": "探路者",
"pct_chg": 8.1,
"price": 24.43,
"prev_high": 23.21,
"prev_high_date": "2026-06-26",
"turnover": 7.41
},
{
"code": "300012",
"name": "华测检测",
"pct_chg": 8.51,
"price": 15.04,
"prev_high": 14.6,
"prev_high_date": "2026-06-22",
"turnover": 4.05
},
{
"code": "300019",
"name": "硅宝科技",
"pct_chg": 2.2,
"price": 19.48,
"prev_high": 19.06,
"prev_high_date": "2026-06-30",
"turnover": 5.47
},
{
"code": "300037",
"name": "新宙邦",
"pct_chg": 0.75,
"price": 93.55,
"prev_high": 92.85,
"prev_high_date": "2026-06-30",
"turnover": 6.9
},
{
"code": "300059",
"name": "东方财富",
"pct_chg": 5.25,
"price": 21.45,
"prev_high": 21.11,
"prev_high_date": "2026-06-25",
"turnover": 7.11
},
{
"code": "300065",
"name": "海兰信",
"pct_chg": 1.03,
"price": 22.54,
"prev_high": 22.31,
"prev_high_date": "2026-06-30",
"turnover": 9.18
},
{
"code": "300083",
"name": "创世纪",
"pct_chg": 0.29,
"price": 13.66,
"prev_high": 13.62,
"prev_high_date": "2026-06-30",
"turnover": 8.55
},
{
"code": "300121",
"name": "阳谷华泰",
"pct_chg": 20.0,
"price": 15.12,
"prev_high": 13.56,
"prev_high_date": "2026-06-11",
"turnover": 23.73
},
{
"code": "300142",
"name": "沃森生物",
"pct_chg": 2.77,
"price": 13.35,
"prev_high": 12.99,
"prev_high_date": "2026-06-30",
"turnover": 6.21
},
{
"code": "300149",
"name": "睿智医药",
"pct_chg": 3.77,
"price": 9.9,
"prev_high": 9.86,
"prev_high_date": "2026-06-29",
"turnover": 12.45
},
{
"code": "300181",
"name": "佐力药业",
"pct_chg": 2.06,
"price": 14.39,
"prev_high": 14.19,
"prev_high_date": "2026-06-01",
"turnover": 3.38
},
{
"code": "300192",
"name": "科德教育",
"pct_chg": 6.68,
"price": 17.41,
"prev_high": 17.3,
"prev_high_date": "2026-06-16",
"turnover": 5.29
},
{
"code": "300199",
"name": "翰宇药业",
"pct_chg": 8.38,
"price": 23.93,
"prev_high": 23.03,
"prev_high_date": "2026-06-15",
"turnover": 10.44
},
{
"code": "300204",
"name": "舒泰神",
"pct_chg": 5.8,
"price": 25.16,
"prev_high": 24.96,
"prev_high_date": "2026-06-03",
"turnover": 15.74
},
{
"code": "300223",
"name": "北京君正",
"pct_chg": 4.08,
"price": 259.05,
"prev_high": 248.9,
"prev_high_date": "2026-06-30",
"turnover": 13.89
},
{
"code": "300234",
"name": "开尔新材",
"pct_chg": 0.08,
"price": 11.73,
"prev_high": 11.72,
"prev_high_date": "2026-06-30",
"turnover": 6.13
},
{
"code": "300238",
"name": "冠昊生物",
"pct_chg": 4.74,
"price": 12.15,
"prev_high": 12.0,
"prev_high_date": "2026-06-01",
"turnover": 4.04
},
{
"code": "300244",
"name": "迪安诊断",
"pct_chg": 9.39,
"price": 20.5,
"prev_high": 19.83,
"prev_high_date": "2026-06-25",
"turnover": 12.16
},
{
"code": "300260",
"name": "新莱应材",
"pct_chg": 3.4,
"price": 103.88,
"prev_high": 103.6,
"prev_high_date": "2026-06-29",
"turnover": 10.51
},
{
"code": "300263",
"name": "隆华科技",
"pct_chg": 2.52,
"price": 16.71,
"prev_high": 16.63,
"prev_high_date": "2026-06-17",
"turnover": 14.77
},
{
"code": "300269",
"name": "联建光电",
"pct_chg": 11.98,
"price": 6.17,
"prev_high": 5.51,
"prev_high_date": "2026-06-30",
"turnover": 24.05
},
{
"code": "300270",
"name": "中威电子",
"pct_chg": 9.76,
"price": 14.28,
"prev_high": 13.02,
"prev_high_date": "2026-06-03",
"turnover": 23.16
},
{
"code": "300316",
"name": "晶盛机电",
"pct_chg": 0.18,
"price": 60.51,
"prev_high": 60.4,
"prev_high_date": "2026-06-30",
"turnover": 4.16
},
{
"code": "300323",
"name": "华灿光电",
"pct_chg": 8.53,
"price": 22.14,
"prev_high": 20.4,
"prev_high_date": "2026-06-30",
"turnover": 15.35
},
{
"code": "300327",
"name": "中颖电子",
"pct_chg": 7.68,
"price": 34.51,
"prev_high": 32.58,
"prev_high_date": "2026-06-25",
"turnover": 16.59
},
{
"code": "300345",
"name": "华民股份",
"pct_chg": 20.03,
"price": 7.01,
"prev_high": 6.42,
"prev_high_date": "2026-06-11",
"turnover": 20.59
},
{
"code": "300354",
"name": "东华测试",
"pct_chg": 10.69,
"price": 37.5,
"prev_high": 35.41,
"prev_high_date": "2026-06-18",
"turnover": 11.09
},
{
"code": "300357",
"name": "我武生物",
"pct_chg": 5.02,
"price": 24.49,
"prev_high": 23.62,
"prev_high_date": "2026-06-29",
"turnover": 3.55
},
{
"code": "300358",
"name": "楚天科技",
"pct_chg": 5.38,
"price": 8.43,
"prev_high": 8.38,
"prev_high_date": "2026-06-01",
"turnover": 4.7
},
{
"code": "300383",
"name": "光环新网",
"pct_chg": 10.69,
"price": 13.77,
"prev_high": 13.53,
"prev_high_date": "2026-06-02",
"turnover": 9.26
},
{
"code": "300408",
"name": "三环集团",
"pct_chg": 2.13,
"price": 170.46,
"prev_high": 166.9,
"prev_high_date": "2026-06-30",
"turnover": 3.96
},
{
"code": "300416",
"name": "苏试试验",
"pct_chg": 7.36,
"price": 21.88,
"prev_high": 20.38,
"prev_high_date": "2026-06-30",
"turnover": 9.79
},
{
"code": "300429",
"name": "强力新材",
"pct_chg": 0.0,
"price": 17.72,
"prev_high": 17.72,
"prev_high_date": "2026-06-30",
"turnover": 12.8
},
{
"code": "300434",
"name": "金石亚药",
"pct_chg": 2.58,
"price": 11.52,
"prev_high": 11.23,
"prev_high_date": "2026-06-30",
"turnover": 14.15
},
{
"code": "300436",
"name": "广生堂",
"pct_chg": 4.58,
"price": 112.57,
"prev_high": 107.64,
"prev_high_date": "2026-06-30",
"turnover": 12.43
},
{
"code": "300440",
"name": "运达科技",
"pct_chg": 2.58,
"price": 21.88,
"prev_high": 21.36,
"prev_high_date": "2026-06-26",
"turnover": 3.61
},
{
"code": "300442",
"name": "润泽科技",
"pct_chg": 8.41,
"price": 90.06,
"prev_high": 86.0,
"prev_high_date": "2026-06-22",
"turnover": 5.61
},
{
"code": "300460",
"name": "ST惠伦",
"pct_chg": 7.5,
"price": 10.61,
"prev_high": 9.87,
"prev_high_date": "2026-06-30",
"turnover": 5.28
},
{
"code": "300469",
"name": "信息发展",
"pct_chg": 6.9,
"price": 56.24,
"prev_high": 56.09,
"prev_high_date": "2026-06-05",
"turnover": 4.9
},
{
"code": "300480",
"name": "光力科技",
"pct_chg": 5.08,
"price": 44.85,
"prev_high": 42.68,
"prev_high_date": "2026-06-30",
"turnover": 17.09
},
{
"code": "300481",
"name": "濮阳惠成",
"pct_chg": 19.98,
"price": 22.82,
"prev_high": 19.36,
"prev_high_date": "2026-06-17",
"turnover": 18.36
},
{
"code": "300485",
"name": "赛升药业",
"pct_chg": 3.68,
"price": 9.86,
"prev_high": 9.7,
"prev_high_date": "2026-06-23",
"turnover": 8.22
},
{
"code": "300487",
"name": "蓝晓科技",
"pct_chg": 20.0,
"price": 70.62,
"prev_high": 62.0,
"prev_high_date": "2026-06-22",
"turnover": 6.39
},
{
"code": "300488",
"name": "恒锋工具",
"pct_chg": 2.11,
"price": 47.82,
"prev_high": 47.79,
"prev_high_date": "2026-06-17",
"turnover": 7.8
},
{
"code": "300497",
"name": "富祥股份",
"pct_chg": 5.33,
"price": 23.34,
"prev_high": 22.5,
"prev_high_date": "2026-06-25",
"turnover": 21.04
},
{
"code": "300503",
"name": "昊志机电",
"pct_chg": 9.95,
"price": 101.48,
"prev_high": 92.3,
"prev_high_date": "2026-06-30",
"turnover": 21.4
},
{
"code": "300518",
"name": "新迅达",
"pct_chg": 20.0,
"price": 39.66,
"prev_high": 33.05,
"prev_high_date": "2026-06-30",
"turnover": 6.77
},
{
"code": "300537",
"name": "广信材料",
"pct_chg": 4.97,
"price": 35.27,
"prev_high": 33.6,
"prev_high_date": "2026-06-30",
"turnover": 27.28
},
{
"code": "300539",
"name": "横河精密",
"pct_chg": 19.98,
"price": 24.44,
"prev_high": 24.14,
"prev_high_date": "2026-06-01",
"turnover": 5.95
},
{
"code": "300540",
"name": "蜀道装备",
"pct_chg": 14.01,
"price": 43.21,
"prev_high": 37.9,
"prev_high_date": "2026-06-30",
"turnover": 21.36
},
{
"code": "300557",
"name": "理工光科",
"pct_chg": 5.98,
"price": 36.49,
"prev_high": 35.73,
"prev_high_date": "2026-06-25",
"turnover": 7.94
},
{
"code": "300558",
"name": "贝达药业",
"pct_chg": 4.43,
"price": 67.95,
"prev_high": 65.07,
"prev_high_date": "2026-06-30",
"turnover": 7.11
},
{
"code": "300560",
"name": "中富通",
"pct_chg": 14.65,
"price": 21.84,
"prev_high": 20.55,
"prev_high_date": "2026-06-22",
"turnover": 18.85
},
{
"code": "300562",
"name": "乐心医疗",
"pct_chg": 6.59,
"price": 14.4,
"prev_high": 13.51,
"prev_high_date": "2026-06-30",
"turnover": 12.98
},
{
"code": "300566",
"name": "激智科技",
"pct_chg": 14.32,
"price": 42.24,
"prev_high": 36.95,
"prev_high_date": "2026-06-30",
"turnover": 21.33
},
{
"code": "300573",
"name": "兴齐眼药",
"pct_chg": 4.66,
"price": 42.66,
"prev_high": 41.47,
"prev_high_date": "2026-06-29",
"turnover": 5.22
},
{
"code": "300592",
"name": "华凯易佰",
"pct_chg": 4.35,
"price": 18.47,
"prev_high": 17.7,
"prev_high_date": "2026-06-30",
"turnover": 8.35
},
{
"code": "300596",
"name": "利安隆",
"pct_chg": 3.85,
"price": 54.5,
"prev_high": 52.48,
"prev_high_date": "2026-06-30",
"turnover": 5.34
},
{
"code": "300607",
"name": "拓斯达",
"pct_chg": 20.01,
"price": 49.48,
"prev_high": 41.23,
"prev_high_date": "2026-06-30",
"turnover": 15.02
},
{
"code": "300666",
"name": "江丰电子",
"pct_chg": 6.98,
"price": 394.33,
"prev_high": 382.48,
"prev_high_date": "2026-06-29",
"turnover": 11.49
},
{
"code": "300670",
"name": "大烨智能",
"pct_chg": 0.42,
"price": 7.09,
"prev_high": 7.06,
"prev_high_date": "2026-06-30",
"turnover": 10.62
},
{
"code": "300671",
"name": "富满微",
"pct_chg": 6.48,
"price": 91.74,
"prev_high": 86.16,
"prev_high_date": "2026-06-30",
"turnover": 18.23
},
{
"code": "300676",
"name": "华大基因",
"pct_chg": 5.11,
"price": 36.85,
"prev_high": 36.58,
"prev_high_date": "2026-06-22",
"turnover": 2.41
},
{
"code": "300689",
"name": "澄天伟业",
"pct_chg": 0.88,
"price": 70.8,
"prev_high": 70.18,
"prev_high_date": "2026-06-30",
"turnover": 3.31
},
{
"code": "300717",
"name": "华信新材",
"pct_chg": 3.8,
"price": 22.11,
"prev_high": 22.0,
"prev_high_date": "2026-06-26",
"turnover": 8.7
},
{
"code": "300720",
"name": "海川智能",
"pct_chg": 14.66,
"price": 110.3,
"prev_high": 96.2,
"prev_high_date": "2026-06-30",
"turnover": 12.76
},
{
"code": "300725",
"name": "药石科技",
"pct_chg": 3.5,
"price": 37.88,
"prev_high": 36.6,
"prev_high_date": "2026-06-30",
"turnover": 7.86
},
{
"code": "300727",
"name": "润禾材料",
"pct_chg": 3.63,
"price": 38.78,
"prev_high": 38.44,
"prev_high_date": "2026-06-26",
"turnover": 9.13
},
{
"code": "300739",
"name": "明阳电路",
"pct_chg": 2.45,
"price": 36.0,
"prev_high": 35.14,
"prev_high_date": "2026-06-30",
"turnover": 9.6
},
{
"code": "300751",
"name": "迈为股份",
"pct_chg": 8.51,
"price": 306.5,
"prev_high": 282.46,
"prev_high_date": "2026-06-30",
"turnover": 10.61
},
{
"code": "300759",
"name": "康龙化成",
"pct_chg": 3.6,
"price": 29.97,
"prev_high": 28.93,
"prev_high_date": "2026-06-30",
"turnover": 6.65
},
{
"code": "300762",
"name": "上海瀚讯",
"pct_chg": 0.15,
"price": 45.72,
"prev_high": 45.65,
"prev_high_date": "2026-06-30",
"turnover": 7.77
},
{
"code": "300765",
"name": "石药创新",
"pct_chg": 12.93,
"price": 30.75,
"prev_high": 27.7,
"prev_high_date": "2026-06-29",
"turnover": 1.88
},
{
"code": "300780",
"name": "德恩精工",
"pct_chg": 0.12,
"price": 34.1,
"prev_high": 34.06,
"prev_high_date": "2026-06-30",
"turnover": 8.93
},
{
"code": "300786",
"name": "国林科技",
"pct_chg": 1.04,
"price": 25.33,
"prev_high": 25.07,
"prev_high_date": "2026-06-30",
"turnover": 13.15
},
{
"code": "300801",
"name": "泰和科技",
"pct_chg": 9.75,
"price": 35.45,
"prev_high": 33.59,
"prev_high_date": "2026-06-29",
"turnover": 18.44
},
{
"code": "300821",
"name": "东岳硅材",
"pct_chg": 7.64,
"price": 22.13,
"prev_high": 20.9,
"prev_high_date": "2026-06-22",
"turnover": 11.06
},
{
"code": "300840",
"name": "酷特智能",
"pct_chg": 13.19,
"price": 23.35,
"prev_high": 22.83,
"prev_high_date": "2026-06-01",
"turnover": 8.36
},
{
"code": "300841",
"name": "康华生物",
"pct_chg": 2.99,
"price": 48.98,
"prev_high": 48.16,
"prev_high_date": "2026-06-22",
"turnover": 2.77
},
{
"code": "300843",
"name": "胜蓝股份",
"pct_chg": 2.08,
"price": 159.5,
"prev_high": 156.25,
"prev_high_date": "2026-06-30",
"turnover": 6.12
},
{
"code": "300852",
"name": "四会富仕",
"pct_chg": 20.0,
"price": 83.09,
"prev_high": 69.24,
"prev_high_date": "2026-06-30",
"turnover": 13.89
},
{
"code": "300873",
"name": "海晨股份",
"pct_chg": 20.02,
"price": 28.72,
"prev_high": 23.89,
"prev_high_date": "2026-06-30",
"turnover": 23.5
},
{
"code": "300900",
"name": "广联航空",
"pct_chg": 1.09,
"price": 38.99,
"prev_high": 38.57,
"prev_high_date": "2026-06-30",
"turnover": 9.93
},
{
"code": "300907",
"name": "康平科技",
"pct_chg": 1.27,
"price": 56.71,
"prev_high": 56.51,
"prev_high_date": "2026-06-25",
"turnover": 5.37
},
{
"code": "300932",
"name": "三友联众",
"pct_chg": 0.38,
"price": 10.64,
"prev_high": 10.6,
"prev_high_date": "2026-06-30",
"turnover": 12.19
},
{
"code": "300938",
"name": "信测标准",
"pct_chg": 5.39,
"price": 52.57,
"prev_high": 52.51,
"prev_high_date": "2026-06-26",
"turnover": 6.62
},
{
"code": "300980",
"name": "祥源新材",
"pct_chg": 6.56,
"price": 31.34,
"prev_high": 29.41,
"prev_high_date": "2026-06-30",
"turnover": 17.76
},
{
"code": "300985",
"name": "致远新能",
"pct_chg": 4.08,
"price": 40.07,
"prev_high": 38.5,
"prev_high_date": "2026-06-30",
"turnover": 3.39
},
{
"code": "600030",
"name": "中信证券",
"pct_chg": 2.58,
"price": 29.47,
"prev_high": 28.98,
"prev_high_date": "2026-06-25",
"turnover": 3.52
},
{
"code": "600061",
"name": "国投资本",
"pct_chg": 3.75,
"price": 6.64,
"prev_high": 6.63,
"prev_high_date": "2026-06-25",
"turnover": 1.16
}
],
"note": "数据来源：权威公开网站（含机构评级与板块分析）"
};window.ANALYST_RATINGS = {
"update_time": "2026-07-01 19:45",
"upgrades": [],
"downgrades": [],
"new_coverage": [],
"hot_stocks": [
{
"code": "688003",
"name": "天准科技",
"rating": "增持",
"institution": "爱建证券",
"report_count_1m": 1,
"date": "2026-06-16"
},
{
"code": "300263",
"name": "隆华科技",
"rating": "买入",
"institution": "中邮证券",
"report_count_1m": 1,
"date": "2026-06-18"
},
{
"code": "688300",
"name": "联瑞新材",
"rating": "",
"institution": "西南证券",
"report_count_1m": 1,
"date": "2026-06-15"
},
{
"code": "688233",
"name": "神工股份",
"rating": "增持",
"institution": "国信证券",
"report_count_1m": 1,
"date": "2026-06-16"
},
{
"code": "600276",
"name": "恒瑞医药",
"rating": "买入",
"institution": "西南证券",
"report_count_1m": 1,
"date": "2026-07-01"
},
{
"code": "600030",
"name": "中信证券",
"rating": "买入",
"institution": "华源证券",
"report_count_1m": 1,
"date": "2026-06-02"
},
{
"code": "300759",
"name": "康龙化成",
"rating": "买入",
"institution": "长城国瑞证券",
"report_count_1m": 1,
"date": "2026-07-01"
}
],
"latest_reports": [
{
"code": "600276",
"name": "恒瑞医药",
"title": "研发能力再得验证，创新成果加速落地",
"rating": "买入",
"institution": "西南证券",
"date": "2026-07-01"
},
{
"code": "300759",
"name": "康龙化成",
"title": "一体化CXO平台持续深化 小分子CDMO商业化能力逐步验证",
"rating": "买入",
"institution": "长城国瑞证券",
"date": "2026-07-01"
}
],
"note": "数据来源：权威公开投行研报网站"
"rating_summary": {
"买入": 2
}
};window.POLICY_DENSITY = {
"update_time": "2026-07-01 19:46",
"density": 0.0,
"level": "低",
"signals": [],
"summary": "",
"note": "数据来源：多源新闻聚合（权威新闻+财经媒体）",
"hits": {},
"total_score": 0
};// ===== 资金抱团预判 =====
window.HERRING_DATA = {
"update_time": "2026-07-01 19:31:49",
"current_clusters": [
{
"rank": 1,
"medal": "🥇",
"sector": "证券",
"amount": 135.42,
"unit": "亿",
"direction": "流入",
"leader": "天风证券",
"pct": 4.82
},
{
"rank": 2,
"medal": "🥈",
"sector": "化学制药",
"amount": 49.28,
"unit": "亿",
"direction": "流入",
"leader": "汇宇制药",
"pct": 5.64
},
{
"rank": 3,
"medal": "🥉",
"sector": "软件开发",
"amount": 37.66,
"unit": "亿",
"direction": "流入",
"leader": "汇金科技",
"pct": 2.99
}
],
"high_prob": [
{
"sector": "期货概念",
"net": 120.11,
"unit": "亿",
"leader": "朗源股份",
"pct": 4.41
},
{
"sector": "互联网金融",
"net": 97.63,
"unit": "亿",
"leader": "*ST同辉",
"pct": 3.52
},
{
"sector": "证金持股",
"net": 96.7,
"unit": "亿",
"leader": "友阿股份",
"pct": 2.13
},
{
"sector": "AI应用",
"net": 87.54,
"unit": "亿",
"leader": "汇金科技",
"pct": 2.7
},
{
"sector": "创新药",
"net": 74.26,
"unit": "亿",
"leader": "汇宇制药",
"pct": 4.71
}
],
"cautious": [
{
"sector": "通信设备",
"reason": "主力净流出-219.82亿"
},
{
"sector": "元件",
"reason": "主力净流出-126.73亿"
},
{
"sector": "消费电子",
"reason": "主力净流出-92.56亿"
}
],
"catalysts": [],
"broker_views": [],
"industry_flow": {
"inflow": [
{
"name": "证券",
"net": 135.42,
"pct": 4.82,
"leader": "天风证券"
},
{
"name": "化学制药",
"net": 49.28,
"pct": 5.64,
"leader": "汇宇制药"
},
{
"name": "软件开发",
"net": 37.66,
"pct": 2.99,
"leader": "汇金科技"
},
{
"name": "保险",
"net": 31.49,
"pct": 7.09,
"leader": "中国人寿"
},
{
"name": "通信服务",
"net": 17.83,
"pct": 2.76,
"leader": "中富通"
}
],
"outflow": [
{
"name": "通信设备",
"net": -219.82,
"pct": -0.43,
"leader": "星网锐捷"
},
{
"name": "元件",
"net": -126.73,
"pct": -1.26,
"leader": "四会富仕"
},
{
"name": "消费电子",
"net": -92.56,
"pct": -0.17,
"leader": "安洁科技"
},
{
"name": "半导体",
"net": -90.58,
"pct": -0.5,
"leader": "格科微"
},
{
"name": "自动化设备",
"net": -56.42,
"pct": 1.38,
"leader": "拓斯达"
}
]
},
"concept_flow": {
"inflow": [
{
"name": "期货概念",
"net": 120.11,
"pct": 4.41,
"leader": "朗源股份"
},
{
"name": "互联网金融",
"net": 97.63,
"pct": 3.52,
"leader": "*ST同辉"
},
{
"name": "证金持股",
"net": 96.7,
"pct": 2.13,
"leader": "友阿股份"
},
{
"name": "AI应用",
"net": 87.54,
"pct": 2.7,
"leader": "汇金科技"
},
{
"name": "创新药",
"net": 74.26,
"pct": 4.71,
"leader": "汇宇制药"
},
{
"name": "互联网保险",
"net": 67.81,
"pct": 5.34,
"leader": "金证股份"
},
{
"name": "AIGC概念",
"net": 58.97,
"pct": 2.43,
"leader": "飞利信"
},
{
"name": "京津冀一体化",
"net": 51.61,
"pct": 2.66,
"leader": "*ST同辉"
},
{
"name": "区块链",
"net": 42.31,
"pct": 2.44,
"leader": "汇金科技"
},
{
"name": "仿制药一致性评价",
"net": 33.66,
"pct": 4.8,
"leader": "汇宇制药"
}
],
"outflow": [
{
"name": "芯片概念",
"net": -594.47,
"pct": 0.69,
"leader": "惠科股份"
},
{
"name": "数据中心(AIDC)",
"net": -560.29,
"pct": 0.66,
"leader": "*ST同辉"
},
{
"name": "5G",
"net": -533.0,
"pct": 0.02,
"leader": "四会富仕"
},
{
"name": "共封装光学(CPO)",
"net": -508.05,
"pct": -1.22,
"leader": "四会富仕"
},
{
"name": "新能源汽车",
"net": -443.02,
"pct": 0.87,
"leader": "海晨股份"
}
]
}
};var MAIN_STOCK_DATA = window.MAIN_STOCK_DATA = {
"update_time": "2026-07-01 16:12",
"data_available": false,
"top_main_in": [],
"top_main_out": []
};window.MAIN_WEEK_DATA = {
"update_time": "2026-07-01 19:29:04",
"source": "自算-行业资金流历史5日累计",
"type": "week",
"buy_top5": [
{
"name": "深股通",
"net": 1310.83,
"unit": "亿",
"pct": 0
},
{
"name": "芯片概念",
"net": 1217.06,
"unit": "亿",
"pct": 0
},
{
"name": "数据中心(AIDC)",
"net": 1166.99,
"unit": "亿",
"pct": 0
},
{
"name": "融资融券",
"net": 973.53,
"unit": "亿",
"pct": 0
},
{
"name": "5G",
"net": 972.39,
"unit": "亿",
"pct": 0
}
],
"sell_top5": [
{
"name": "农业",
"net": -30.1,
"unit": "亿",
"pct": 0
},
{
"name": "地产",
"net": -20.7,
"unit": "亿",
"pct": 0
},
{
"name": "电力",
"net": -18.37,
"unit": "亿",
"pct": 0
},
{
"name": "AI算力",
"net": -16.8,
"unit": "亿",
"pct": 0
},
{
"name": "银行概念",
"net": -15.73,
"unit": "亿",
"pct": 0
}
],
"available": true
};var MAHORO_COVERAGE = window.MAHORO_COVERAGE = {
"_update_time": "2026-07-01 19:26:06",
"09866": "bullish",
"02338": "bullish",
"09660": "bullish",
"01177": "bullish",
"01109": "bearish",
"01908": "bearish",
"01030": "bearish",
"300274": "neutral",
"000333": "bullish",
"300124": "bullish",
"002747": "bullish",
"002714": "bullish"
};window.SUSPENSION_ALERT = {
"update_time": "2026-07-01 19:28:09",
"suspended": [
{
"code": "200706",
"name": "瓦轴B",
"days": 121,
"reason": "刊登重要公告"
},
{
"code": "920305",
"name": "*ST云创",
"days": 62,
"reason": "刊登重要公告"
},
{
"code": "688121",
"name": "卓然股份",
"days": 56,
"reason": "未如期刊登定期报告"
},
{
"code": "002731",
"name": "ST萃华",
"days": 56,
"reason": "未如期刊登定期报告"
},
{
"code": "603137",
"name": "恒尚节能",
"days": 15,
"reason": "拟筹划重大资产重组"
},
{
"code": "603789",
"name": "ST星农",
"days": 7,
"reason": "刊登重要公告"
},
{
"code": "000524",
"name": "岭南控股",
"days": 7,
"reason": "刊登重要公告"
},
{
"code": "603001",
"name": "奥康国际",
"days": 6,
"reason": "刊登重要公告"
}
],
"near_trigger": [
{
"code": "300518",
"name": "新迅达",
"pct": 20.0,
"gap": 0
},
{
"code": "688106",
"name": "金宏气体",
"pct": 20.0,
"gap": 0
},
{
"code": "300607",
"name": "拓斯达",
"pct": 20.0,
"gap": 0
},
{
"code": "688571",
"name": "杭华股份",
"pct": 20.0,
"gap": 0
},
{
"code": "300539",
"name": "横河精密",
"pct": 20.0,
"gap": 0.0
},
{
"code": "301279",
"name": "金道科技",
"pct": 20.0,
"gap": 0
},
{
"code": "300561",
"name": "汇金科技",
"pct": 20.0,
"gap": 0.0
},
{
"code": "300487",
"name": "蓝晓科技",
"pct": 20.0,
"gap": 0
}
]
};window.NORTH_FUND_DATA = {
"update_time": "2026-06-30 11:42:31",
"data_date": null,
"south_flow": {
"total": 54.45,
"unit": "亿",
"direction": "流入",
"sh_net": 30.01,
"sz_net": 24.44
},
"south_week": {
"total": 44.05,
"unit": "亿",
"direction": "流入",
"days": 5,
"date_range": "2026-06-23 — 2026-06-29"
},
"south_history": [
{
"date": "2026-05-15",
"net_buy": 249.55
},
{
"date": "2026-05-18",
"net_buy": -78.76
},
{
"date": "2026-05-19",
"net_buy": 12.66
},
{
"date": "2026-05-20",
"net_buy": 57.08
},
{
"date": "2026-05-21",
"net_buy": -61.05
},
{
"date": "2026-05-22",
"net_buy": -64.94
},
{
"date": "2026-05-26",
"net_buy": -9.68
},
{
"date": "2026-05-27",
"net_buy": -77.17
},
{
"date": "2026-05-28",
"net_buy": 76.09
},
{
"date": "2026-05-29",
"net_buy": 18.84
},
{
"date": "2026-06-01",
"net_buy": 46.57
},
{
"date": "2026-06-02",
"net_buy": 22.23
},
{
"date": "2026-06-03",
"net_buy": 186.82
},
{
"date": "2026-06-04",
"net_buy": -3.15
},
{
"date": "2026-06-05",
"net_buy": -24.26
},
{
"date": "2026-06-08",
"net_buy": 113.18
},
{
"date": "2026-06-09",
"net_buy": -86.14
},
{
"date": "2026-06-10",
"net_buy": 82.43
},
{
"date": "2026-06-11",
"net_buy": -27.54
},
{
"date": "2026-06-12",
"net_buy": -39.42
},
{
"date": "2026-06-15",
"net_buy": 21.1
},
{
"date": "2026-06-16",
"net_buy": 34.63
},
{
"date": "2026-06-17",
"net_buy": -32.22
},
{
"date": "2026-06-18",
"net_buy": -67.92
},
{
"date": "2026-06-22",
"net_buy": -58.2
},
{
"date": "2026-06-23",
"net_buy": 103.71
},
{
"date": "2026-06-24",
"net_buy": 157.51
},
{
"date": "2026-06-25",
"net_buy": -88.74
},
{
"date": "2026-06-26",
"net_buy": -25.04
},
{
"date": "2026-06-29",
"net_buy": -103.39
}
],
"south_individual": null,
"north_info": {
"note": "北向净买额自2024年5月起不再披露（港交所新规），仅保留成交总额参考",
"last_available": "2024-08-16",
"date": "2026-06-30",
"status": "北向净买额已停更(2024.5起港交所新规)，仅保留南向资金数据"
},
"data_available": true,
"data_source": "权威公开数据源"
};if ((!window.LHB_DATA || !window.LHB_DATA.stocks || !window.LHB_DATA.stocks.length)) window.LHB_DATA = {"date":"20260612","update_time":"2026-06-15 00:44:53","summary":{"纯共振":6,"标X":27,"不达标":54,"总计":87}};
function getCatalystStatus(dateStr) {
  var today = new Date();
  var todayStr = today.getFullYear() + '-' + ('0'+(today.getMonth()+1)).slice(-2) + '-' + ('0'+today.getDate()).slice(-2);
  var todayDate = new Date(todayStr);
  var year = today.getFullYear();

  // 格式: "6.12-14" (日期范围)
  var rangeMatch = dateStr.match(/^(\d{1,2})\.(\d{1,2})-(\d{1,2})$/);
  if (rangeMatch) {
    var m = parseInt(rangeMatch[1]);
    var start = new Date(year, m-1, parseInt(rangeMatch[2]));
    var end = new Date(year, m-1, parseInt(rangeMatch[3]));
    if (todayDate >= start && todayDate <= end) return '进行中';
    if (todayDate < start) { var d = Math.floor((start - todayDate) / 86400000); return d <= 1 ? '明天开始' : d + '天后'; }
    return '已落地';
  }

  // 格式: "6.18" (单日)
  var singleMatch = dateStr.match(/^(\d{1,2})\.(\d{1,2})$/);
  if (singleMatch) {
    var m = parseInt(singleMatch[1]);
    var d = parseInt(singleMatch[2]);
    var eventDate = new Date(year, m-1, d);
    var diff = Math.floor((eventDate - todayDate) / 86400000);
    if (diff === 0) return '今日';
    if (diff === 1) return '明天';
    if (diff > 1) return diff + '天后';
    return '已落地';
  }

  // 格式: "6.12起" (持续中)
  if (dateStr.indexOf('起') !== -1) {
    return '持续中';
  }

  // 格式: "6月下旬" / "6月中旬" / "6月上旬"
  var xm = dateStr.match(/^(\d{1,2})月(上|中|下)旬$/);
  if (xm) {
    var m = parseInt(xm[1]);
    var period = xm[2];
    var startDay, endDay;
    if (period === '上') { startDay = 1; endDay = 10; }
    else if (period === '中') { startDay = 11; endDay = 20; }
    else { startDay = 21; endDay = 30; }
    var start = new Date(year, m-1, startDay);
    var end = new Date(year, m-1, endDay);
    if (todayDate >= start && todayDate <= end) return '进行中';
    if (todayDate < start) return '即将';
    return '已落地';
  }

  return '已落地';
}

// ===== 主力资金抱团监控 (HERRING_DATA + MAIN_STOCK_DATA + SECTOR_FUND_FLOW 合并) =====
function renderHerdingMain() {
  var hd = HERRING_DATA || {};
  var ms = MAIN_STOCK_DATA || {};
  var sf = window.SECTOR_FUND_FLOW || {};
  var con = document.getElementById('herdingMainContent');
  var timeEl = document.getElementById('herdingMainTime');
  if (!con) return;

  // 数据新鲜度检查（HERRING_DATA超过2天未更新 → 视为过期）
  var now = new Date();
  var hdUpdate = hd.update_time ? new Date(hd.update_time.replace(' ', 'T')) : null;
  var hdAgeDays = hdUpdate ? (now - hdUpdate) / 86400000 : 999;
  var hdStale = hdAgeDays > 2;
  // 个股主力资金新鲜度检查（fetcher挂掉，数据可能过期）
  var msUpdate = ms.update_time ? new Date(ms.update_time.replace(' ', 'T')) : null;
  var msAgeDays = msUpdate ? (now - msUpdate) / 86400000 : 999;
  var msStale = msAgeDays > 2;

  var latestTime = hd.update_time || ms.update_time || '';
  if (!latestTime) { con.innerHTML = '<div style="color:#999;text-align:center;padding:10px;">暂无主力数据，盘后更新</div>'; return; }
  if (timeEl) {
    var ft = fmtDataTime(latestTime);
    timeEl.textContent = '更新于 ' + ft.text;
  }
  var h = '';

  // 顶部总结语句（直接拼入 h）
  var summaryEl2 = true;
  var clusters = hd.current_clusters || [];
  var hdSummary = '';
  if (clusters.length >= 2) {
    var topClust = clusters[0];
    var inflowCnt = clusters.filter(function(c){ return c.direction === '流入'; }).length;
    hdSummary = '🔥 ' + (topClust.sector) + '资金' + topClust.direction + '居首（' + (topClust.amount?topClust.amount.toFixed(1):'?') + topClust.unit + '），' + inflowCnt + '/' + clusters.length + '板块获流入，主力抱团方向集中度' + (inflowCnt>=3?'高':'中') + '。';
  } else if (hdStale) {
    hdSummary = '📭 抱团数据过期，以下为历史参考方向，待更新后再做判断。';
  } else {
    hdSummary = '📊 主力资金方向分散，暂无明确抱团信号，持续观察。';
  }
  h += '<div style="font-weight:700;font-size:13px;color:#333;text-align:left;padding:8px 12px;margin-bottom:10px;background:linear-gradient(90deg,#ede7f6,#fff);border-left:4px solid #4527a0;border-radius:0 6px 6px 0;">' + hdSummary + '</div>';

  // 数据过期警告
  if (hdStale && hdUpdate) {
    h += '<div style="background:#fff3e0;border:1px solid #ffcc80;border-radius:6px;padding:8px 14px;margin-bottom:10px;font-size:12px;color:#e65100;">';
    h += '⚠️ 资金抱团预判数据已过期 ' + Math.floor(hdAgeDays) + ' 天（上次更新：' + ft.text + '），以下方向预判可能不准。板块资金实况数据正常。';
    h += '</div>';
  }

  // ═══ 区块一：方向预判 ═══
  h += '<div style="background:linear-gradient(135deg,#fff3e0,#ffe0b2);color:#e65100;padding:10px 16px;font-size:14px;font-weight:700;border-radius:6px;margin-bottom:10px;">🔥 抱团监控方向预判</div>';

  // 当前抱团（仅数据新鲜时显示）
  if (!hdStale && hd.current_clusters && hd.current_clusters.length) {
    h += '<div style="margin-bottom:10px;font-size:12px;color:#555;line-height:1.6;">';
    h += '<b>当前抱团：</b>';
    hd.current_clusters.forEach(function(c,i){
      var amt = c.amount >= 1 ? c.amount.toFixed(2) + c.unit : (c.amount * 10000).toFixed(0) + '万';
      var sep = i < hd.current_clusters.length - 1 ? ' · ' : '';
      h += (c.medal||'') + '<b style="color:#c62828;">' + c.sector + '</b> ' + amt + sep;
    });
    h += '</div>';
  }

  // 概念资金接力（仅数据新鲜时显示）
  if (!hdStale && hd.high_prob && hd.high_prob.length) {
    h += '<div style="margin-bottom:10px;">';
    h += '<div style="font-size:12px;font-weight:600;color:#e65100;margin-bottom:6px;">🔥 概念资金接力方向</div>';
    h += '<div style="font-size:12px;color:#555;line-height:2;">';
    hd.high_prob.slice(0, 8).forEach(function(p, i){
      var netStr = '+'+p.net+p.unit;
      var c = '#c62828';
      if (i === 0) c = '#b71c1c';
      else if (i < 3) c = '#c62828';
      else c = '#e65100';
      h += '<span style="font-weight:700;color:'+c+';">'+(i+1)+'. '+p.sector+'</span> <b style="color:'+c+';">'+netStr+'</b>';
      if (p.leader) h += ' <span style="color:#888;font-size:11px;">领涨:'+p.leader+'</span>';
      h += (i < Math.min(hd.high_prob.length, 8) - 1 ? '  ·  ' : '');
    });
    h += '</div></div>';
  }

  // 谨慎方向（仅数据新鲜时显示）
  if (!hdStale && hd.cautious && hd.cautious.length) {
    h += '<div style="margin-bottom:8px;padding:6px 14px;background:#fff5f5;border:2px solid #e57373;border-radius:20px;font-size:12px;">';
    h += '<b style="color:#c62828;">⚠ 谨慎：</b><span style="font-size:10px;color:#aaa;margin-left:4px;">[主力资金]</span>';
    hd.cautious.forEach(function(c,i){
      h += c.sector + '（' + c.reason + '）' + (i < hd.cautious.length - 1 ? ' · ' : '');
    });
    h += '</div>';
  }

  // 催化剂（仅数据新鲜时显示）
  if (!hdStale && hd.catalysts && hd.catalysts.length) {
    var sorted = hd.catalysts.slice().sort(function(a,b){ return (a.date||'').localeCompare(b.date||''); });
    var ongoing = [], upcoming = [];
    sorted.forEach(function(c){
      var st = c.status || getCatalystStatus(c.date);
      if (st === '已落地') return;
      var ds = (c.date || '').replace(/^\d{4}-/, '');
      if (st === '进行中' || st === '持续中' || st === '今日' || st === '明日') ongoing.push({item: c, status: st, dateLabel: ds});
      else upcoming.push({item: c, status: st, dateLabel: ds});
    });
    if (ongoing.length || upcoming.length) {
      h += '<div style="margin-bottom:10px;display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12px;">';
      h += '<div><b style="color:#42a5f5;">进行中</b>';
      if (ongoing.length) {
        ongoing.forEach(function(o){ h += '<div style="padding:3px 6px;background:#e3f2fd;border-radius:3px;margin-top:2px;">'+o.item.event+' <span style="font-size:10px;color:#888;">'+o.dateLabel+'</span></div>'; });
      } else { h += '<div style="color:#999;font-size:11px;">暂无</div>'; }
      h += '</div>';
      h += '<div><b style="color:#e65100;">预告</b>';
      if (upcoming.length) {
        upcoming.forEach(function(o){ h += '<div style="padding:3px 6px;background:#fff3e0;border-radius:3px;margin-top:2px;">'+o.item.event+' <span style="font-size:10px;color:#888;">'+o.dateLabel+'</span></div>'; });
      } else { h += '<div style="color:#999;font-size:11px;">暂无</div>'; }
      h += '</div></div>';
    }
  }

  // ═══ 区块二：个股当日（上）→ 板块当日+本周（下） ═══
  var mw = window.MAIN_WEEK_DATA || {};
  var hasWeek = mw.available && (mw.buy_top5 && mw.buy_top5.length || mw.sell_top5 && mw.sell_top5.length);

  // ═══ 上：个股主力动向（当日）—— 仅数据新鲜时显示 ═══
  if (!msStale && (ms.top_main_in && ms.top_main_in.length || ms.top_main_out && ms.top_main_out.length)) {
  h += '<div style="font-size:15px;font-weight:700;color:#1a1a2e;margin:10px 0 8px 0;padding-bottom:4px;border-bottom:1px solid #e0e0e0;">个股主力动向（当日）</div>';
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px;">';
  // 净买入
  h += '<div style="background:#fff5f5;border-radius:8px;padding:10px;">';
  h += '<div style="font-size:12px;font-weight:600;color:#c62828;margin-bottom:6px;">净买入 TOP10</div>';
  if (ms.top_main_in && ms.top_main_in.length) {
    var in10 = ms.top_main_in.slice(0,10);
    var inLeft = in10.slice(0,5), inRight = in10.slice(5,10);
    h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:3px 8px;font-size:12px;">';
    for (var col=0; col<2; col++) {
      var colData = col===0 ? inLeft : inRight;
      h += '<div>';
      colData.forEach(function(x,i){
        var idx = col*5 + i + 1;
        var dayBg = ''; var dayStyle = '';
        if (x.day_count >= 3) { dayBg = 'background:#c62828;color:#fff;'; dayStyle = 'padding:1px 4px;border-radius:3px;'; }
        else if (x.day_count >= 2) dayStyle = 'padding:1px 3px;';
        var dayTag = x.day_count >= 2 ? '<span style="font-size:10px;'+dayBg+'margin-left:3px;'+dayStyle+'">连'+x.day_count+'日</span>' : '';
        h += '<div style="padding:2px 0;">'+idx+' '+x.name+' <span style="color:#c62828;font-weight:700;">+'+x.net_in+x.unit+'</span>'+dayTag+'</div>';
      });
      h += '</div>';
    }
    h += '</div>';
  } else { h += '<span style="color:#999;font-size:12px;">暂无</span>'; }
  h += '</div>';
  // 净卖出
  h += '<div style="background:#f5fff5;border-radius:8px;padding:10px;">';
  h += '<div style="font-size:12px;font-weight:600;color:#2e7d32;margin-bottom:6px;">净卖出 TOP10</div>';
  if (ms.top_main_out && ms.top_main_out.length) {
    var out10 = ms.top_main_out.slice(0,10);
    var outLeft = out10.slice(0,5), outRight = out10.slice(5,10);
    h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:3px 8px;font-size:12px;">';
    for (var col=0; col<2; col++) {
      var colData = col===0 ? outLeft : outRight;
      h += '<div>';
      colData.forEach(function(x,i){
        var idx = col*5 + i + 1;
        var dayBg = ''; var dayStyle = '';
        if (x.day_count >= 3) { dayBg = 'background:#2e7d32;color:#fff;'; dayStyle = 'padding:1px 4px;border-radius:3px;'; }
        else if (x.day_count >= 2) dayStyle = 'padding:1px 3px;';
        var dayTag = x.day_count >= 2 ? '<span style="font-size:10px;'+dayBg+'margin-left:3px;'+dayStyle+'">连'+x.day_count+'日</span>' : '';
        h += '<div style="padding:2px 0;">'+idx+' '+x.name+' <span style="color:#2e7d32;font-weight:700;">-'+x.net_out+x.unit+'</span>'+dayTag+'</div>';
      });
      h += '</div>';
    }
    h += '</div>';
  } else { h += '<span style="color:#999;font-size:12px;">暂无</span>'; }
  h += '</div>';
  h += '</div>'; // end 个股当日 grid
  } // end 个股主力动向 (仅在数据新鲜时显示)

  // ═══ 下：板块资金实况（当日 + 本周 左右并排）═══
  var sfTimeHtml = '';
  if (sf.update_time) { var sft = fmtDataTime(sf.update_time); sfTimeHtml = ' <span style=\"font-size:11px;color:#888;font-weight:400;\">更新于 ' + sft.text + '（盘中实时）</span>'; }
  h += '<div style=\"font-size:15px;font-weight:700;color:#1a1a2e;margin:10px 0 8px 0;padding-bottom:4px;border-bottom:1px solid #e0e0e0;\">板块资金实况 <span style=\"font-size:10px;color:#aaa;font-weight:400;\">[板块总资金]</span>' + sfTimeHtml + '</div>';
  h += '<div style="display:grid;grid-template-columns:' + (hasWeek ? '1fr 1fr' : '1fr') + ';gap:10px;margin-bottom:12px;">';

  // 当日 — 左流入 右流出 并排
  h += '<div>';
  h += '<div style="font-size:14px;font-weight:700;color:#42a5f5;margin-bottom:6px;">当日</div>';
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
  // 左：流入 TOP10（红底）
  h += '<div style="background:#fff5f5;border-radius:8px;padding:8px;">';
  h += '<div style="font-size:12px;font-weight:600;color:#c62828;margin-bottom:4px;">🔴 流入 TOP10</div>';
  if (sf.top_list && sf.top_list.length) {
    var inSectors = sf.top_list.filter(function(x){return x.net>0;}).slice(0,10);
    if (inSectors.length) {
      h += '<div style="font-size:11px;line-height:1.85">';
      for (var i=0; i<inSectors.length; i++) {
        var inBg = ''; var inDs = '';
        if (inSectors[i].consecutive_days >= 3) { inBg = 'background:#c62828;color:#fff;'; inDs = 'padding:1px 4px;border-radius:3px;'; }
        else if (inSectors[i].consecutive_days >= 2) inDs = 'padding:1px 3px;';
        var inDayTag = inSectors[i].consecutive_days >= 2 ? '<span style="font-size:10px;'+inBg+'margin-left:3px;'+inDs+'">连'+inSectors[i].consecutive_days+'日</span>' : '';
        h += '<div style="padding:1px 0;">'+(i+1)+' '+inSectors[i].name+' <span style="color:#c62828;font-weight:700;">+'+inSectors[i].net.toFixed(1)+'亿</span>'+inDayTag+'</div>';
      }
      h += '</div>';
    } else { h += '<span style="color:#999;font-size:11px;">暂无</span>'; }
  } else { h += '<span style="color:#999;font-size:11px;">暂无</span>'; }
  h += '</div>';
  // 右：流出 TOP10（绿底）
  h += '<div style="background:#f5fff5;border-radius:8px;padding:8px;">';
  h += '<div style="font-size:12px;font-weight:600;color:#2e7d32;margin-bottom:4px;">🟢 流出 TOP10</div>';
  if (sf.top_list && sf.top_list.length) {
    var outSectors = sf.top_list.filter(function(x){return x.net<0;}).reverse().slice(0,10);
    if (outSectors.length) {
      h += '<div style="font-size:11px;line-height:1.85">';
      for (var i=0; i<outSectors.length; i++) {
        var outBg = ''; var outDs = '';
        if (outSectors[i].consecutive_days >= 3) { outBg = 'background:#2e7d32;color:#fff;'; outDs = 'padding:1px 4px;border-radius:3px;'; }
        else if (outSectors[i].consecutive_days >= 2) outDs = 'padding:1px 3px;';
        var outDayTag = outSectors[i].consecutive_days >= 2 ? '<span style="font-size:10px;'+outBg+'margin-left:3px;'+outDs+'">连'+outSectors[i].consecutive_days+'日</span>' : '';
        h += '<div style="padding:1px 0;">'+(i+1)+' '+outSectors[i].name+' <span style="color:#2e7d32;font-weight:700;">'+outSectors[i].net.toFixed(1)+'亿</span>'+outDayTag+'</div>';
      }
      h += '</div>';
    } else { h += '<span style="color:#999;font-size:11px;">暂无</span>'; }
  } else { h += '<span style="color:#999;font-size:11px;">暂无</span>'; }
  h += '</div>';
  h += '</div>'; // end 当日 left-right grid
  h += '</div>'; // close 当日

  // 本周（仅当数据可用时显示）— 左流入 右流出 并排
  if (hasWeek) {
  h += '<div>';
  h += '<div style="font-size:14px;font-weight:700;color:#42a5f5;margin-bottom:6px;">近5日</div>';
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
  // 左：流入 TOP10
  h += '<div style="background:#fff5f5;border-radius:8px;padding:8px;">';
  h += '<div style="font-size:12px;font-weight:600;color:#c62828;margin-bottom:4px;">🔴 流入 TOP10</div>';
  if (hasWeek && mw.buy_top5 && mw.buy_top5.length) {
    var wkIn = mw.buy_top5.slice(0,10);
    h += '<div style="font-size:11px;line-height:1.85">';
    for (var i=0; i<wkIn.length; i++) {
      var wBg = ''; var wDs = '';
      if (wkIn[i].week_count >= 3) { wBg = 'background:#c62828;color:#fff;'; wDs = 'padding:1px 4px;border-radius:3px;'; }
      else if (wkIn[i].week_count >= 2) wDs = 'padding:1px 3px;';
      var wTag = wkIn[i].week_count >= 2 ? '<span style="font-size:10px;'+wBg+'margin-left:3px;'+wDs+'">连'+wkIn[i].week_count+'周</span>' : '';
      h += '<div style="padding:1px 0;">'+(i+1)+' '+wkIn[i].name+' <span style="color:#c62828;font-weight:700;">+'+wkIn[i].net+wkIn[i].unit+'</span>'+wTag+'</div>';
    }
    h += '</div>';
  } else { h += '<span style="color:#999;font-size:11px;">暂无</span>'; }
  h += '</div>';
  // 右：流出 TOP10
  h += '<div style="background:#f5fff5;border-radius:8px;padding:8px;">';
  h += '<div style="font-size:12px;font-weight:600;color:#2e7d32;margin-bottom:4px;">🟢 流出 TOP10</div>';
  if (hasWeek && mw.sell_top5 && mw.sell_top5.length) {
    var wkOut = mw.sell_top5.slice(0,10);
    h += '<div style="font-size:11px;line-height:1.85">';
    for (var i=0; i<wkOut.length; i++) {
      var wBg2 = ''; var wDs2 = '';
      if (wkOut[i].week_count >= 3) { wBg2 = 'background:#2e7d32;color:#fff;'; wDs2 = 'padding:1px 4px;border-radius:3px;'; }
      else if (wkOut[i].week_count >= 2) wDs2 = 'padding:1px 3px;';
      var wTag2 = wkOut[i].week_count >= 2 ? '<span style="font-size:10px;'+wBg2+'margin-left:3px;'+wDs2+'">连'+wkOut[i].week_count+'周</span>' : '';
      h += '<div style="padding:1px 0;">'+(i+1)+' '+wkOut[i].name+' <span style="color:#2e7d32;font-weight:700;">'+wkOut[i].net+wkOut[i].unit+'</span>'+wTag2+'</div>';
    }
    h += '</div>';
  } else { h += '<span style="color:#999;font-size:11px;">暂无</span>'; }
  h += '</div>';
  h += '</div>'; // end 本周 left-right grid
  h += '</div>'; // close 本周
  } // end 本周 (仅在有数据时显示)
  h += '</div>'; // end 板块当日+本周 grid

  con.innerHTML = h;
}

// ===== 机游共振·龙虎榜 =====
function renderLhbPredict() {
  var d = window.LHB_DATA || {};
  var con = document.getElementById('lhbPredictContent');
  var timeEl = document.getElementById('lhbPredictTime');
  if (!con) return;
  var stocks = d.stocks || [];
  if (!stocks.length) { con.innerHTML = '<div style="color:#999;text-align:center;padding:10px;">暂无龙虎榜数据</div>'; return; }
  if (timeEl) {
    var ft = fmtDataTime(d.update_time || d.scan_time || '');
    timeEl.textContent = '更新于 ' + ft.text;
  }

  // 三分组：机构独买 / 机游共振 / 游资独买（严格互斥）
  var instStocks = stocks.filter(function(s){ return (s.inst_net_万||0) > 8000 && (s.yz_net_万||0) <= 8000; });
  var yzStocks = stocks.filter(function(s){ return (s.yz_net_万||0) > 8000 && (s.inst_net_万||0) <= 8000; });
  var resonance = stocks.filter(function(s){ return s.category === '纯共振'; });

  function formatNet(val_wan) {
    var yi = val_wan / 10000;
    return '+' + yi.toFixed(2) + '亿';
  }

  // 只取游资别名标签（红底红字），机构/北向/量化/未识别不显示
  function yzBadge(seats) {
    if (!seats) return '';
    var badges = [];
    var seen = {};
    Object.keys(seats).forEach(function(t){
      var d = seats[t];
      var aliases = d.aliases || [];
      aliases.forEach(function(a){
        if (!seen[a]) {
          seen[a] = true;
          badges.push('<span style="font-size:11px;background:#fce4ec;color:#c62828;padding:1px 4px;border-radius:2px;margin-left:2px;">'+a+'</span>');
        }
      });
    });
    return badges.join('');
  }

  function renderBlock(stocks, netFn, title, bg, color, emoji, showYz, footer) {
    var b = '';
    var maxShow = 10;
    var sorted = stocks.slice().sort(function(a,b){ return netFn(b) - netFn(a); });
    b += '<div style="background:'+bg+';border-radius:10px;padding:10px;min-height:100px;">';
    b += '<div style="font-size:14px;font-weight:700;color:'+color+';margin-bottom:6px;"><span style="font-size:20px;">'+emoji+'</span> '+title+' <b>'+sorted.length+'只</b></div>';
    if (sorted.length) {
      b += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 6px;">';
      sorted.slice(0, maxShow).forEach(function(s){
        var net = netFn(s);
        var dayTag = '';
        if (s.consecutive_days && s.consecutive_days >= 2) {
          dayTag = ' <span style="font-size:12px;font-weight:700;color:#fff;background:'+color+';padding:2px 5px;border-radius:3px;">连'+s.consecutive_days+'日</span>';
        }
        var sBadge = showYz ? yzBadge(s.seats) : '';
        b += '<div style="font-size:13px;color:#333;display:flex;justify-content:space-between;align-items:center;padding:2px 0;">';
        b += '<span>' + s.name + sBadge + dayTag + '</span>';
        b += '<b style="font-size:12px;color:'+color+';white-space:nowrap;">' + formatNet(net) + '</b>';
        b += '</div>';
      });
      b += '</div>';
    } else {
      b += '<div style="font-size:12px;color:#999;">暂无</div>';
    }
    if (footer) { b += footer; }
    b += '</div>';
    return b;
  }

  var h = '';

  // 机构净卖数据（供买入区块底部展示）
  var it = window.INST_TRADE || null;
  var sellFooter = '';
  if (it && it.top_sell && it.top_sell.length) {
    sellFooter = '<div style="margin-top:6px;padding-top:6px;border-top:1px solid #90caf9;">' +
      '<div style="font-size:14px;font-weight:700;color:#2e7d32;margin-bottom:6px;">机构净卖出top5</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 6px;">' +
      it.top_sell.slice(0,5).map(function(s){
        return '<div style="font-size:13px;color:#333;display:flex;justify-content:space-between;align-items:center;padding:2px 0;">' +
          '<span>' + s.name + '</span>' +
          '<b style="font-size:12px;color:#2e7d32;white-space:nowrap;">' + (s.net_amt / 100000000).toFixed(2) + '亿</b>' +
          '</div>';
      }).join('') +
      '</div></div>';
  }

  // 三色块
  h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:10px;">';
  // 左：机构净买入（底部含净卖出top5）
  h += renderBlock(instStocks, function(s){ return s.inst_net_万; }, '机构净买入', '#e3f2fd', '#1565c0', '🏦', false, sellFooter);
  // 中：机游共振（显示游资别名）
  h += renderBlock(resonance, function(s){ return (s.inst_net_万||0) + (s.yz_net_万||0); }, '机游共振', '#fff8e1', '#f57f17', '⚡', true);
  // 右：游资净买入（显示游资别名）
  h += renderBlock(yzStocks, function(s){ return s.yz_net_万; }, '游资净买入', '#fce4ec', '#c62828', '🔥', true);
  h += '</div>';

  // 顶部总结语句（直接拼入 h）
  var totalInst = instStocks.reduce(function(s,x){return s+(x.inst_net_万||0);},0);
  var totalYZ = yzStocks.reduce(function(s,x){return s+(x.yz_net_万||0);},0);
  var totalRes = resonance.reduce(function(s,x){return s+(x.inst_net_万||0)+(x.yz_net_万||0);},0);
  var topInst = instStocks.length ? instStocks[0].name : '';
  var topRes = resonance.length ? resonance[0].name : '';
  var lhbSummary = '';
  if (instStocks.length + resonance.length > 3) {
    lhbSummary = '💰 机构主导：' + (totalInst/10000).toFixed(2) + '亿净买入 | ⚡ 机游共振：' + resonance.length + '只 | ' + (topRes||topInst) + '领衔，机构+游资合力做多信号强。';
  } else if (yzStocks.length > instStocks.length && yzStocks.length >= 2) {
    lhbSummary = '🔥 游资活跃：' + yzStocks.length + '只游资净买入，短线情绪偏高。';
  } else {
    lhbSummary = '📊 龙虎榜信号分散，机构净买入' + instStocks.length + '只、机游共振' + resonance.length + '只，等待方向明朗。';
  }
  h = '<div style="font-weight:700;font-size:13px;color:#333;text-align:left;padding:8px 12px;margin-bottom:10px;background:linear-gradient(90deg,#e0f2f1,#fff);border-left:4px solid #a5d6a7;border-radius:0 6px 6px 0;">' + lhbSummary + '</div>' + h;

  // 底部辅助信息
  var others = stocks.filter(function(s){ return s.category !== '纯共振' && (s.inst_net_万||0) <= 8000 && (s.yz_net_万||0) <= 8000; });
  if (others.length) {
    h += '<div style="font-size:12px;color:#999;text-align:center;">另有 ' + others.length + ' 只不达标（未达到0.8亿门槛），暂不展示</div>';
  }

  con.innerHTML = h;
}

// renderMainStock 已合并至 renderHerdingMain

// ===== 北向资金监控 v4 (方向预判+板块+个股+策略) =====
function renderNorthFund() {
  var d = window.NORTH_FUND_DATA || {};
  var con = document.getElementById('northFundContent');
  var timeEl = document.getElementById('northFundTime');
  if (!con) return;

  var sf = d.south_flow || {};
  var sw = d.south_week || {};
  var sh = d.south_history || [];
  var ni = d.north_info || {};
  var si = d.south_individual || null;

  if (!d.update_time && sf.total === 0 && !d.data_available) {
    con.innerHTML = '<div style="color:#999;text-align:center;padding:10px;">暂无资金数据，盘后更新</div>';
    return;
  }

  if (timeEl && d.update_time) {
    var ft = fmtDataTime(d.update_time);
    timeEl.textContent = '更新于 ' + ft.text;
  }

  var h = '';

  // ── 操作建议（卡片顶部，色块上方）──
  var advice = '';
  if (sf.direction === '流入' && sw.direction === '流入' && sh && sh.slice(-5).filter(function(p){return p.net_buy > 0;}).length >= 4) {
    advice = '💡 南向连续多日流入，港股中线机会明确';
  } else if (sf.direction === '流出' && sw.direction === '流出') {
    advice = '💡 南向日周双流出，港股暂观望';
  } else if (sf.direction === '流出' && sw.direction === '流入') {
    advice = '💡 日内流出但本周仍净流入，维持仓位';
  } else {
    advice = '💡 维持当前港股仓位，关注次日方向';
  }
  h += '<div style="font-size:12px;color:#555;line-height:1.6;padding:6px 10px;background:#fafafa;border-radius:6px;margin-bottom:10px;border-left:3px solid #ffe082;">' + advice + '</div>';

  // ── 南向资金（港股通→港股）核心指标 + 分析融合 ──
  var sfDir = sf.direction === '流出' ? '-' : (sf.direction === '流入' ? '+' : '');
  var sfColor = sf.direction === '流出' ? '#2e7d32' : '#c62828';
  var sfVerdict = sf.direction === '流入' ? (sf.total > 50 ? '大幅加仓' : '温和买入') : (Math.abs(sf.total) > 50 ? '短线减仓' : '短线谨慎');
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:10px;">';
  h += '<div style="background:' + (sf.direction === '流出' ? '#e8f5e9' : '#ffebee') + ';border-radius:8px;padding:12px;text-align:center;">';
  h += '<div style="font-size:11px;color:#888;margin-bottom:4px;">🇭🇰 南向当日净买额 <span style="font-size:10px;color:'+sfColor+';">· '+sfVerdict+'</span></div>';
  h += '<div style="font-size:22px;font-weight:700;color:' + sfColor + ';">' + sfDir + (sf.total || '--') + '<span style="font-size:12px;font-weight:400;">亿</span></div>';
  h += '<div style="font-size:10px;color:#999;margin-top:2px;">沪 ' + (sf.sh_net > 0 ? '+' : '') + (sf.sh_net || '--') + '亿 · 深 ' + (sf.sz_net > 0 ? '+' : '') + (sf.sz_net || '--') + '亿</div>';
  h += '</div>';

  var swDir = sw.direction === '流出' ? '-' : (sw.direction === '流入' ? '+' : '');
  var swColor = sw.direction === '流出' ? '#2e7d32' : '#c62828';
  var swVerdict = sw.direction === '流入' ? '中期看多港股' : '中期偏谨慎';
  h += '<div style="background:' + (sw.direction === '流出' ? '#e8f5e9' : '#ffebee') + ';border-radius:8px;padding:12px;text-align:center;">';
  h += '<div style="font-size:11px;color:#888;margin-bottom:4px;">本周累计净买额 <span style="font-size:10px;color:'+swColor+';">· '+swVerdict+'</span></div>';
  h += '<div style="font-size:22px;font-weight:700;color:' + swColor + ';">' + swDir + (sw.total || '--') + '<span style="font-size:12px;font-weight:400;">亿</span></div>';
  if (sw.days) h += '<div style="font-size:10px;color:#999;margin-top:2px;">' + sw.date_range + ' · ' + sw.days + '日</div>';
  h += '</div></div>';

  // ── 30日趋势迷你图 ──
  if (sh.length >= 5) {
    var totalBuy = sh.reduce(function(s,p){return s + (p.net_buy||0);}, 0);
    var totalStr = totalBuy >= 0 ? ('累计净买入 <b style="color:#c62828;">+' + totalBuy.toFixed(1) + '亿</b>') : ('累计净卖出 <b style="color:#2e7d32;">' + totalBuy.toFixed(1) + '亿</b>');
    h += '<div style="margin-bottom:8px;font-size:11px;color:#888;">📈 南向近' + sh.length + '日净买额趋势 — ' + totalStr + '</div>';
    h += '<div style="display:flex;align-items:flex-end;gap:3px;height:50px;padding:4px 0;margin-bottom:4px;">';
    var maxAbs = 0;
    sh.forEach(function(p) { if (Math.abs(p.net_buy) > maxAbs) maxAbs = Math.abs(p.net_buy); });
    maxAbs = Math.max(maxAbs, 10);
    sh.forEach(function(p) {
      var barH = Math.abs(p.net_buy) / maxAbs * 40;
      var barColor = p.net_buy >= 0 ? '#c62828' : '#2e7d32';
      var valText = (p.net_buy > 0 ? '+' : '') + p.net_buy.toFixed(1);
      h += '<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;position:relative;">';
      h += '<span style="font-size:8px;color:' + barColor + ';margin-bottom:1px;">' + valText + '</span>';
      h += '<div style="width:100%;max-width:20px;height:' + Math.max(barH, 1) + 'px;background:' + barColor + ';border-radius:2px 2px 0 0;" title="' + p.date + ': ' + valText + '亿"></div>';
      h += '</div>';
    });
    h += '</div>';
    h += '<div style="display:flex;justify-content:space-between;font-size:9px;color:#aaa;">';
    sh.forEach(function(p) {
      h += '<span style="flex:1;text-align:center;">' + p.date.slice(5) + '</span>';
    });
    h += '</div>';
  }

  // ── 南向个股明细（流入/流出TOP5） ──
  if (si && (si.top_buy && si.top_buy.length > 0 || si.top_sell && si.top_sell.length > 0)) {
    h += '<div style="margin-top:10px;">';
    if (si.top_buy && si.top_buy.length > 0) {
      h += '<div style="font-size:11px;font-weight:700;color:#c62828;margin-bottom:4px;">🔴 流入TOP5</div>';
      h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 8px;">';
      si.top_buy.forEach(function(s) {
        h += '<div style="font-size:12px;color:#333;display:flex;justify-content:space-between;padding:1px 0;">';
        h += '<span>' + s.name + '</span>';
        h += '<b style="color:#c62822;font-size:11px;white-space:nowrap;">+' + s.net_buy.toFixed(1) + '亿</b>';
        h += '</div>';
      });
      h += '</div>';
    }
    if (si.top_sell && si.top_sell.length > 0) {
      h += '<div style="font-size:11px;font-weight:700;color:#2e7d32;margin-bottom:4px;margin-top:6px;">🟢 流出TOP5</div>';
      h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 8px;">';
      si.top_sell.forEach(function(s) {
        h += '<div style="font-size:12px;color:#333;display:flex;justify-content:space-between;padding:1px 0;">';
        h += '<span>' + s.name + '</span>';
        h += '<b style="color:#2e7d32;font-size:11px;white-space:nowrap;">' + s.net_buy.toFixed(1) + '亿</b>';
        h += '</div>';
      });
      h += '</div>';
    }
    h += '</div>';
  }

  <!-- 北向停更公告 -->
  h += '<div style="margin-top:12px;background:#fff3e0;border:1px solid #ffe0b2;border-radius:8px;padding:10px 12px;font-size:11px;color:#e65100;line-height:1.6;">';
  h += '<b>⚠️ 北向资金净买额已停更</b><br>';
  h += ni.status || ni.note || '自2024年5月起港交所不再披露沪深股通实时买入/卖出金额，北向净买额数据不可用。';
  if (ni.last_available) h += '<br>最后可用日期：' + ni.last_available;
  h += '</div>';

  con.innerHTML = h;
}

// 南向资金智能分析
function buildSouthFlowAnalysis(sf, sw, sh, si) {
  var items = [];
  
  // 1. 当日方向判断
  if (sf.direction && sf.total) {
    var dayVerdict = '';
    if (sf.direction === '流入' && sf.total > 50) dayVerdict = '当日大幅净买入' + sf.total + '亿，南向积极加仓港股';
    else if (sf.direction === '流入') dayVerdict = '当日净买入' + sf.total + '亿，南向温和买入';
    else if (sf.direction === '流出' && Math.abs(sf.total) > 50) dayVerdict = '当日大幅净卖出' + Math.abs(sf.total) + '亿，南向短线减仓';
    else dayVerdict = '当日净卖出' + Math.abs(sf.total) + '亿，南向短线谨慎';
    items.push('📊 ' + dayVerdict);
  }
  
  // 2. 本周方向
  if (sw.direction && sw.total) {
    var weekVerdict = sw.direction === '流入' ? '本周累计净买入' + sw.total + '亿，中期看多港股' : '本周累计净卖出' + Math.abs(sw.total) + '亿，中期偏谨慎';
    items.push('📅 ' + weekVerdict);
  }
  
  // 3. 趋势（从历史数据看近5日方向）
  if (sh && sh.length >= 5) {
    var recent5 = sh.slice(-5);
    var upDays = recent5.filter(function(p){return p.net_buy > 0;}).length;
    var total5 = recent5.reduce(function(s,p){return s + (p.net_buy||0);}, 0);
    if (upDays >= 4) items.push('🔥 近5日' + upDays + '天净流入，南向持续加仓');
    else if (upDays <= 1) items.push('❄️ 近5日仅' + upDays + '天净流入，南向偏谨慎');
    else if (total5 > 100) items.push('📈 近5日累计净流入' + total5.toFixed(0) + '亿');
    else if (total5 < -100) items.push('📉 近5日累计净流出' + Math.abs(total5).toFixed(0) + '亿');
  }
  
  // 4. 个股流向
  if (si && si.top_buy && si.top_buy.length) {
    items.push('🔴 买入聚焦：' + si.top_buy.slice(0,3).map(function(s){return s.name;}).join('、'));
  }
  
  // 5. 操作建议
  if (sf.direction === '流入' && sw.direction === '流入' && sh && sh.slice(-5).filter(function(p){return p.net_buy > 0;}).length >= 4) {
    items.push('💡 <b>建议：</b>南向连续多日流入，港股中线机会明确，关注南向重仓的科技/高股息标的');
  } else if (sf.direction === '流出' && sw.direction === '流出') {
    items.push('💡 <b>建议：</b>南向日周双流出，港股暂观望，等待资金回流信号');
  } else if (sf.direction === '流出' && sw.direction === '流入') {
    items.push('💡 <b>建议：</b>日内流出但本周仍净流入，属短期波动，维持港股仓位不变');
  } else {
    items.push('💡 <b>建议：</b>维持当前港股仓位，关注次日方向确认');
  }
  
  return items.join('<br>');
} /* buildSouthFlowAnalysis 已废弃，分析逻辑已融入色块 */

// ===== 金股池异动停牌 =====
function renderSuspensionAlert() {
  var card = document.getElementById('suspensionCard');
  if (!card) return;
  var sa = window.SUSPENSION_ALERT || {};
  var suspended = sa.suspended || [];
  var near = sa.near_trigger || [];

  // ⚡ 金股池限定：只展示金股池内的停牌/异动标的
  var gpCodes = {};
  if (window.GOLD_POOL && window.GOLD_POOL.stocks) {
    for (var k in window.GOLD_POOL.stocks) {
      var s = window.GOLD_POOL.stocks[k];
      if (s && s.code) gpCodes[s.code] = true;
    }
  }
  suspended = suspended.filter(function(s) { return gpCodes[s.code]; });
  near = near.filter(function(s) { return gpCodes[s.code]; });

  if (!suspended.length && !near.length) {
    card.style.display = 'block';
    var timeEl2 = document.getElementById('suspensionTime');
    if (timeEl2 && sa.update_time) {
      var ft2 = fmtDataTime(sa.update_time);
      timeEl2.textContent = '更新于 ' + ft2.text;
    }
    var listEl3 = document.getElementById('suspensionList');
    if (listEl3) listEl3.innerHTML = '<div style="text-align:center;padding:30px;color:#999;font-size:14px;">✅ 暂无停牌/预警标的</div>';
    return;
  }
  card.style.display = 'block';

  // 时间
  var timeEl = document.getElementById('suspensionTime');
  if (timeEl && sa.update_time) {
    var ft = fmtDataTime(sa.update_time);
    timeEl.textContent = '更新于 ' + ft.text;
  }

  // 停牌列表（两列）
  var sCount = document.getElementById('suspCount');
  var sList = document.getElementById('suspList');
  if (sCount) sCount.textContent = suspended.length;
  if (sList) {
    var showSuspended = suspended.slice(0, 10);
    if (showSuspended.length) {
      var pairs = [];
      for (var i = 0; i < showSuspended.length; i += 2) {
        var left = '<span style="font-weight:600;">' + showSuspended[i].name + '</span> <span style="font-size:10px;color:#c62828;background:#ffebee;padding:1px 5px;border-radius:3px;">' + showSuspended[i].days + '天</span>';
        var right = '';
        if (i + 1 < showSuspended.length) {
          right = '<span style="font-weight:600;">' + showSuspended[i+1].name + '</span> <span style="font-size:10px;color:#c62828;background:#ffebee;padding:1px 5px;border-radius:3px;">' + showSuspended[i+1].days + '天</span>';
        }
        pairs.push('<div style="display:grid;grid-template-columns:1fr 1fr;gap:3px 8px;">' +
          '<span>' + left + '</span>' +
          '<span>' + right + '</span>' +
          '</div>');
      }
      sList.innerHTML = pairs.join('');
    } else {
      sList.innerHTML = '暂无';
    }
  }

  // 近触发（两列）
  var nCount = document.getElementById('nearCount');
  var nList = document.getElementById('nearList');
  if (nCount) nCount.textContent = near.length;
  if (nList) {
    var showNear = near.slice(0, 10);
    if (showNear.length) {
      var npairs = [];
      for (var i = 0; i < showNear.length; i += 2) {
        var gapClass = showNear[i].gap > 0 && showNear[i].gap <= 5 ? 'color:#c62828;background:#ffebee;' : 'color:#888;background:#f5f5f5;';
        var left = '<span style="font-weight:600;">' + showNear[i].name + '</span> <span style="font-size:11px;">' + showNear[i].pct + '%</span>';
        if (showNear[i].gap > 0) left += ' <span style="font-size:10px;' + gapClass + 'padding:1px 5px;border-radius:3px;">距' + showNear[i].gap + '%</span>';
        var right = '';
        if (i + 1 < showNear.length) {
          var gapClass2 = showNear[i+1].gap > 0 && showNear[i+1].gap <= 5 ? 'color:#c62828;background:#ffebee;' : 'color:#888;background:#f5f5f5;';
          right = '<span style="font-weight:600;">' + showNear[i+1].name + '</span> <span style="font-size:11px;">' + showNear[i+1].pct + '%</span>';
          if (showNear[i+1].gap > 0) right += ' <span style="font-size:10px;' + gapClass2 + 'padding:1px 5px;border-radius:3px;">距' + showNear[i+1].gap + '%</span>';
        }
        npairs.push('<div style="display:grid;grid-template-columns:1fr 1fr;gap:3px 8px;">' +
          '<span>' + left + '</span>' +
          '<span>' + right + '</span>' +
          '</div>');
      }
      nList.innerHTML = npairs.join('');
    } else {
      nList.innerHTML = '暂无';
    }
  }
}

// ===== 打新价值评分卡（申购+上市首日+追踪） =====
function renderIpoScore() {
  var card = document.getElementById('ipoScoreCard');
  if (!card) return;
  var d = window.IPO_DATA || {};
  var stocks = d.stocks || [];

  card.style.display = 'block';

  // 按状态分组
  var applying = stocks.filter(function(s) { return s.status === 'applying'; });
  var listed = stocks.filter(function(s) { return s.status === 'listed_today'; });
  var tracking = stocks.filter(function(s) { return s.status === 'tracking'; });

  if (!stocks.length) {
    // 无新股时：紧凑一行
    card.style.padding = '6px 14px';
    var headerEl = card.querySelector('div[style*="border-bottom"]');
    if (headerEl) { headerEl.style.borderBottom = 'none'; headerEl.style.padding = '0'; }
    var bodyWrap = card.querySelector('div[style*="padding:10px"]');
    if (bodyWrap) bodyWrap.style.display = 'none';
    var timeEl2 = document.getElementById('ipoScoreTime');
    var timeStr = '';
    if (timeEl2 && d.update_time) { var ft2 = fmtDataTime(d.update_time); timeStr = '更新于 ' + ft2.text; }
    var titleSpan = card.querySelector('div[style*="border-bottom"] span');
    if (titleSpan) {
      titleSpan.innerHTML = '<span style="font-size:14px;font-weight:700;color:#880e4f;">🚀 打新研判</span> <span style="font-size:11px;font-weight:400;color:#999;">申购·上市</span> <span style="font-size:11px;color:#aaa;margin-left:4px;">' + timeStr + '</span> <span style="font-size:11px;color:#bbb;margin-left:auto;">📭 近期无新股</span>';
      if (timeEl2) timeEl2.textContent = '';
    }
    return;
  }

  // 有新股时恢复正常
  card.style.padding = '';
  var headerEl = card.querySelector('div[style*="border-bottom"]');
  if (headerEl) { headerEl.style.borderBottom = ''; headerEl.style.padding = ''; }
  var bodyWrap = card.querySelector('div[style*="padding:10px"]');
  if (bodyWrap) bodyWrap.style.display = '';

  // 更新时间
  var timeEl = document.getElementById('ipoScoreTime');
  if (timeEl && d.update_time) {
    var ft = fmtDataTime(d.update_time);
    timeEl.textContent = '更新于 ' + ft.text;
  }

  // 卡片标题动态切换
  var titleSpan = card.querySelector('div[style*="border-bottom"] span');
  var tid = document.getElementById('ipoTitleSpan');
  var titleHtml = '<span id="ipoTitleSpan" style="font-size:14px;font-weight:700;color:#880e4f;">🚀 打新研判</span>';
  if (applying.length > 0) {
    titleHtml += ' <span style="font-size:11px;font-weight:400;color:#2e7d32;">🔔 ' + applying.length + '只可申购</span>';
  }
  if (listed.length > 0) {
    titleHtml += ' <span style="font-size:11px;font-weight:400;color:#1565c0;">📈 ' + listed.length + '只上市</span>';
  }
  if (tracking.length > 0) {
    titleHtml += ' <span style="font-size:11px;font-weight:400;color:#e65100;">📊 ' + tracking.length + '只追踪</span>';
  }
  if (titleSpan) titleSpan.innerHTML = titleHtml;

  var countEl = document.getElementById('ipoCount');
  if (countEl) countEl.textContent = stocks.length;

  var listEl = document.getElementById('ipoStockList');
  if (listEl) {
    var h = '';
    // ── 合并排序：申购期的在前，其次上市首日，其次追踪 ──
    var ordered = [].concat(applying, listed, tracking);
    for (var i = 0; i < ordered.length; i++) {
      var s = ordered[i];
      var sc = s.score || 0;
      var st = s.status || '';
      var isApplying = st === 'applying';
      var isListed = st === 'listed_today';
      var isTracking = st === 'tracking';

      var stars = isApplying ? (sc >= 80 ? '⭐⭐⭐' : sc >= 65 ? '⭐⭐' : '⭐')  : isListed ? '🔥' : '📊';
      var tagColor = s.tag_color || (isApplying ? (sc >= 65 ? '#2e7d32' : '#e65100') : '#1565c0');
      var tagBg = s.bg_color || (isApplying ? '#e8f5e9' : '#e3f2fd');
      var borderColor = tagColor.replace('2e7d32','4caf50').replace('e65100','ff9800').replace('1565c0','42a5f5');

      var highs = s.highlights || [];
      var highStr = highs.length ? highs.join(' · ') : '数据待补充';

      h += '<div style="background:#fff;border:1px solid ' + borderColor + ';border-radius:10px;padding:12px 14px;';
      h += 'border-left:4px solid ' + tagColor + ';">';
      h += '<div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-bottom:6px;">';
      h += '<div style="display:flex;align-items:center;gap:4px;"><span style="font-weight:700;font-size:14px;color:#333;">' + stars + ' ' + s.name + '</span>';
      h += '<span style="font-size:11px;color:#999;">' + s.code + '</span></div>';
      h += '<span style="font-weight:700;font-size:12px;background:' + tagBg + ';color:' + tagColor + ';padding:1px 8px;border-radius:10px;">' + (s.recommend || '—') + '</span>';
      h += '</div>';
      h += '<div style="font-size:12px;color:#666;line-height:1.6;">' + highStr + '</div>';

      var dims = [];
      if (s.issue_price) dims.push('发行价 <b>¥' + s.issue_price + '</b>');
      if (s.board) dims.push(s.board);
      if (isApplying) {
        if (s.pe_discount !== undefined) dims.push('PE折价 <b style="color:' + (s.pe_discount > 20 ? '#2e7d32' : '#f57f17') + '">' + s.pe_discount + '%</b>');
        if (s.issue_pe) dims.push('发行PE <b>' + s.issue_pe + '</b>');
        if (s.industry_pe && s.industry_pe > 0) dims.push('行业PE <b>' + s.industry_pe + '</b>');
        if (s.apply_date) {
          var ad = s.apply_date, adStr = ad.substring(0,4) + '.' + ad.substring(4,6) + '.' + ad.substring(6,8);
          var today = new Date().toISOString().substring(0,10).replace(/-/g,'');
          dims.push(ad === today ? '📅 今日申购' : '📅 ' + adStr + '申购');
        }
      } else {
        // 已上市/追踪：显示收益率
        if (s.change_pct !== undefined) dims.push('涨幅 <b style="color:' + (s.change_pct > 0 ? '#c62828' : '#2e7d32') + '">' + (s.change_pct > 0 ? '+' : '') + s.change_pct + '%</b>');
        if (s.turnover) dims.push('换手率 <b>' + s.turnover + '%</b>');
        if (s.total_return !== undefined && !isListed) dims.push('较发行 <b style="color:' + (s.total_return > 0 ? '#c62828' : '#2e7d32') + '">' + (s.total_return > 0 ? '+' : '') + s.total_return + '%</b>');
        if (s.listing_date) {
          var ld = s.listing_date, ldStr = ld.substring(0,4) + '.' + ld.substring(4,6) + '.' + ld.substring(6,8);
          var today = new Date().toISOString().substring(0,10).replace(/-/g,'');
          dims.push(ld === today ? '📅 今日上市' : '📅 ' + ldStr + '上市');
        }
      }
      if (dims.length) {
        h += '<div style="font-size:11px;color:#999;margin-top:6px;">' + dims.join(' · ') + '</div>';
      }

      // 分析文字
      var analysis = '';
      if (isListed) {
        analysis = '📈 <b>上市首日</b> · ' + (s.board||'') + ' · 发行价¥' + (s.issue_price||'?') + (s.total_return ? ' · 较发行+' + s.total_return + '%' : '');
      } else if (isTracking) {
        if (s.total_return > 50) {
          analysis = '🔴 <b>强势上涨' + s.total_return + '%</b>，可考虑追入但注意获利盘风险。' + (s.turnover ? '换手率' + s.turnover + '%' + (s.turnover > 50 ? '偏高，建议等缩量' : '正常') : '');
        } else if (s.total_return > 0) {
          analysis = '🟡 <b>温和上涨' + s.total_return + '%</b>，建议等回调5%-10%再介入。' + (s.turnover ? '换手率' + s.turnover + '%' : '');
        } else {
          analysis = '🟢 <b>已破发或偏弱</b>，不建议追入。关注后续是否能止跌企稳。';
        }
      } else if (isApplying) {
        if (sc >= 80) {
          analysis = '🟢 PE折价' + (s.pe_discount||0) + '%显著，' + s.board + '新股首日破发概率极低' + (s.pe_discount > 25 ? '，估值安全垫充足' : '') + '。建议顶格申购。';
        } else if (sc >= 65) {
          analysis = '🟡 估值折价适中，具备一定安全边际，可适量参与。';
        } else if (sc >= 50) {
          analysis = '🟠 估值优势不明显，仅建议风险承受能力较强的投资者少量参与。';
        } else {
          analysis = '🔴 估值偏高或风险较大，破发概率偏高，不建议申购。';
        }
      }
      h += '<div style="font-size:11px;color:#5d4037;background:#fafafa;border-radius:6px;padding:6px 10px;margin-top:6px;line-height:1.6;">' + analysis + '</div>';
      h += '</div>';
    }
    listEl.innerHTML = h;
  }

  var judgmentEl = document.getElementById('ipoJudgment');
  if (judgmentEl && d.summary) {
    var appCount = applying.length, listCount = listed.length, trackCount = tracking.length;
    var avgScore = 0;
    if (applying.length > 0) {
      var totalS = 0; applying.forEach(function(s) { totalS += s.score || 0; });
      avgScore = Math.round(totalS / applying.length);
    }
    var verdict = appCount > 0 && avgScore >= 75 ? '整体打新价值较高，建议积极参与' :
                   appCount > 0 && avgScore >= 60 ? '整体可选择性参与' :
                   appCount > 0 ? '整体风险偏高，谨慎参与' :
                   '无待申购新股，关注已上市追踪';
    var summaryText = d.summary || '';
    if (summaryText.indexOf('打新研判') === 0) summaryText = summaryText.replace('打新研判：', '').replace('打新研判', '');
    judgmentEl.innerHTML = '<div style="margin-bottom:4px;">💡 <b>' + summaryText + '</b></div>' +
      (appCount > 0 ? '<div style="color:#888;font-size:11px;margin-top:4px;">📊 申购评分 ' + avgScore + '/100 | ' + verdict + '</div>' : '');
  }
}

// ===== 🎯 精选预判信号卡片 =====
function renderSelectedSignals() {
  var card = document.getElementById('selectedSignalsCard');
  if (!card) return;
  var w52 = window.W52_HIGH || {};
  var an = window.ANALYST_RATINGS || {};
  var pd = window.POLICY_DENSITY || {};
  var hasData = (w52.total || 0) > 0 || (an.hot_stocks || []).length > 0 || (pd.density || 0) > 0;
  if (!hasData) { card.style.display = 'none'; return; }
  card.style.display = 'block';

  // 更新时间
  var timeEl = document.getElementById('selectedSignalsTime');
  if (timeEl) {
    var t = w52.update_time || an.update_time || pd.update_time || '';
    if (t) { var ft = fmtDataTime(t); timeEl.textContent = '更新于 ' + ft.text; }
  }

  // 52周新高
  var el52 = document.getElementById('sig52wNum');
  var el52Label = document.getElementById('sig52wLabel');
  if (el52) el52.innerHTML = (w52.total || 0) + '<span style="font-size:14px;color:#999;">只</span>';
  if (el52Label) {
    var n52 = w52.total || 0;
    if (n52 >= 150) { el52Label.textContent = '市场热度极高'; el52Label.style.color = '#c62828'; el52Label.style.fontWeight = '600'; }
    else if (n52 >= 100) { el52Label.textContent = '强势股活跃'; el52Label.style.color = '#e65100'; el52Label.style.fontWeight = '600'; }
    else if (n52 >= 50) { el52Label.textContent = '结构性行情'; el52Label.style.color = '#333'; el52Label.style.fontWeight = '600'; }
    else if (n52 > 0) { el52Label.textContent = '局部热点'; el52Label.style.color = '#888'; el52Label.style.fontWeight = '600'; }
    else { el52Label.textContent = ''; }
  }
  var el52Sec = document.getElementById('sig52wSector');
  if (el52Sec) el52Sec.style.display = 'none';
  // 简要分析
  var el52Desc = document.getElementById('sig52wDesc');
  if (el52Desc) {
    var w52Total = w52.total || 0;
    if (w52Total >= 150) el52Desc.textContent = w52Total + '只创新高，市场热度极高';
    else if (w52Total >= 100) el52Desc.textContent = w52Total + '只创新高，强势股活跃';
    else if (w52Total >= 50) el52Desc.textContent = w52Total + '只创新高，结构性行情';
    else if (w52Total > 0) el52Desc.textContent = w52Total + '只创新高，局部热点';
    else el52Desc.textContent = '';
  }

  // 新高占比（A股总数约5500只，相对位置）
  var el52Ratio = document.getElementById('sig52wRatio');
  if (el52Ratio) {
    var n52r = w52.total || 0;
    // A股总数：优先取 STOCK_LIST 中 6位代码
    var totalA = 0;
    try {
      var sl = window.STOCK_LIST;
      if (Array.isArray(sl)) {
        for (var i = 0; i < sl.length; i++) {
          var c = (sl[i] && sl[i].code) || '';
          if (/^\d{6}$/.test(c)) totalA++;
        }
      }
    } catch(e) {}
    if (totalA === 0) totalA = 5500; // 兜底
    var pct = (n52r / totalA) * 100;
    var zone;
    if (pct < 1)       zone = {txt:'极度弱势区', c:'#c62828'};
    else if (pct < 3)  zone = {txt:'温和活跃区', c:'#666'};
    else if (pct < 5)  zone = {txt:'健康偏强区', c:'#2e7d32'};
    else if (pct < 10) zone = {txt:'强势主升区', c:'#e65100'};
    else if (pct < 15) zone = {txt:'亢奋警戒区', c:'#c62828'};
    else               zone = {txt:'⚠️ 极度贪婪', c:'#c62828'};
    el52Ratio.innerHTML = '占比 ' + pct.toFixed(1) + '% / <span style="color:' + zone.c + ';font-weight:600;">' + zone.txt + '</span>';
  }

  // 分析师转向
  var upgrades = an.upgrades || [], hot = an.hot_stocks || [];
  var elUp = document.getElementById('sigAnalystUp');
  var upCount = hot.filter(function(s){ return (s.rating||'').indexOf('买入')>-1 || (s.rating||'').indexOf('增持')>-1; }).length;
  if (elUp) elUp.innerHTML = (upCount > 0 ? '<span style="color:#c62828;">' + upCount + '</span>' : upCount) + '<span style="font-size:16px;color:#999;">只</span>';
  var elSub = document.getElementById('sigAnalystSub');
  if (elSub && hot.length) {
    elSub.textContent = hot.slice(0, 2).map(function(s){return s.name;}).join(' · ');
  } else if (elSub) { elSub.textContent = '最新研报覆盖中'; }

  // 政策密度
  var elScore = document.getElementById('sigPolicyScore');
  if (elScore) elScore.textContent = pd.density || '--';
  var elLevel = document.getElementById('sigPolicyLevel');
  if (elLevel) elLevel.textContent = '政策面 ' + (pd.level === '高' ? '🔥 高度密集' : pd.level === '中' ? '📊 温和活跃' : '🌊 相对平静');

  // ═══ 综合分析 ═══
  var analysisEl = document.getElementById('selectedSignalsAnalysis');
  if (analysisEl) {
    analysisEl.innerHTML = generateSelectedSignalsAnalysis(w52.total || 0, upCount, pd);
  }
}

// 精选预判信号分析
function generateSelectedSignalsAnalysis(w52Total, analystUp, policyDensity) {
  var items = [];

  // 52周新高 vs 分析师转向 关系判断
  // 注：这里的"共振"是通用词，指新高活跃度与机构动向同向，**不是**"机游共振·龙虎榜"专有概念
  if (w52Total >= 100 && analystUp === 0) {
    items.push('⚡ <b>强势股独立行情：</b>52周新高活跃（' + w52Total + '只）但分析师无上调评级（' + analystUp + '只），机构观望中。短线可追强势股但需快进快出，警惕基本面支撑不足的高位股回调。');
  } else if (w52Total >= 100 && analystUp >= 5) {
    items.push('📊 <b>强势股+机构动向同向：</b>52周新高活跃（' + w52Total + '只）且分析师上调评级增加（' + analystUp + '只），多空双方均偏多。创新高个股+被上调评级的标的建议重点关注。');
  } else if (w52Total >= 30 && w52Total < 100 && analystUp >= 3) {
    items.push('📈 <b>温和偏多：</b>52周新高温和（' + w52Total + '只，活跃度一般），叠加分析师有限跟进（' + analystUp + '只），属于结构性行情。关注创新高前列板块和被调整个股重叠的方向。');
  } else if (w52Total < 30 && analystUp >= 5) {
    items.push('🔍 <b>机构悄悄布局：</b>分析师密集上调（' + analystUp + '只）但新高数少（' + w52Total + '只），说明机构在低位埋伏。可跟踪被上调评级的标的，等待价格确认后跟进。');
  } else if (w52Total >= 30 && w52Total < 100 && analystUp === 0) {
    items.push('🟡 <b>游资主导行情：</b>52周新高温和（' + w52Total + '只）但无分析师上调（' + analystUp + '只），缺乏机构背书，市场由超短资金驱动。参与需严格止损，不恋战。');
  } else if (w52Total < 30 && analystUp < 5) {
    items.push('🌫️ <b>信号清淡：</b>新高（' + w52Total + '只）与机构动向（' + analystUp + '只）均不明显，市场缺乏明确主线，多看少动。');
  } else {
    items.push('🌫️ <b>信号混合：</b>新高' + w52Total + '只/分析师上调' + analystUp + '只，组合未落入明确区间，建议结合其他信号综合判断。');
  }

  // 政策密度解读
  var pd = policyDensity || {};
  if (pd.density > 5) {
    items.push('🏛️ <b>政策窗口期：</b>政策信号高度密集（密度' + pd.density + '），关注政策驱动的板块机会。');
  } else if (pd.density > 2) {
    items.push('📋 <b>政策适度活跃：</b>关注政策涉及板块，适度参与。');
  }
  
  return '<b>📊 判断：</b>' + items.join('<br>');
}

// ===== 预判总览 =====
function renderPredictSummary() {
  var con = document.getElementById('summaryContent');
  var timeEl = document.getElementById('summaryTime');
  if (!con) return;
  var hd = HERRING_DATA || {};
  var lhb = window.LHB_DATA || {};
  var ms = MAIN_STOCK_DATA || {};
  var nf = window.NORTH_FUND_DATA || {};
  var sf = window.SECTOR_FUND_FLOW || {};

  if (!hd.update_time && (!lhb.stocks || !lhb.stocks.length) && !ms.update_time && !(nf.net_flow && nf.net_flow.total > 0)) {
    con.innerHTML = '<span style="color:#999;">暂无预判数据，等待收盘后自动更新</span>';
    return;
  }

  var latestTime = getLatestPredictTime() || hd.update_time || (lhb.scan_time || ms.update_time || nf.update_time || '');
  if (timeEl && latestTime) {
    var ft = fmtDataTime(latestTime);
    timeEl.textContent = '更新于 ' + ft.text;
  }

  var h = '';

  // 提取核心数据（供下方关注列表使用）
  var pureLhb = (lhb.stocks && lhb.stocks.length) ? lhb.stocks.filter(function(s){return s.category==='纯共振';}) : [];

  // ═══ 核心关注 ═══
  var alerts = [];

  // 龙虎榜信号
  if (pureLhb.length) {
    var lhbSum = 0;
    pureLhb.forEach(function(s){ lhbSum += (s.inst_net_万||0) + (s.yz_net_万||0); });
    var lhbMsg = '<b style="color:#1565c0;">机游共振</b>：'+pureLhb.length+'只纯共振';
    if (lhb.pure_sector_top && lhb.pure_sectors) {
      var topSec = lhb.pure_sector_top;
      var topCnt = lhb.pure_sectors[topSec] || 1;
      if (topCnt >= 2) {
        lhbMsg += '（' + topSec + ' ' + topCnt + '只领衔';
        if (lhb.pure_sector_count > 2) lhbMsg += '，跨' + lhb.pure_sector_count + '板块';
        lhbMsg += '）';
      } else if (lhb.pure_sector_count >= 3) {
        lhbMsg += '（跨' + lhb.pure_sector_count + '板块分散）';
      }
    }
    lhbMsg += '，净买'+(lhbSum/10000).toFixed(2)+'亿，短线博弈活跃';
    alerts.push(lhbMsg);
  }

  // 主力抱团（含接力）
  if (hd.current_clusters && hd.current_clusters.length) {
    var clusterNames = hd.current_clusters.map(function(c){return c.sector + ' ' + c.amount.toFixed(1) + c.unit;}).join('、');
    var alertHtml = '<b style="color:#6a1b9a;">主力抱团</b>：'+clusterNames;
    if (hd.high_prob && hd.high_prob.length) {
      var hpItems = hd.high_prob.map(function(p){
        var tagColor = p.tag==='机构共识'?'#ba68c8':p.tag==='事件驱动'?'#e65100':p.tag==='蓄力中'?'#00838f':'#c62828';
        return '<span style="color:'+tagColor+';font-weight:500;">'+p.tag+'→'+p.sector+'</span>';
      });
      alertHtml += '<br><span style="font-size:11px;color:#666;">'+hpItems.join(' &nbsp;·&nbsp; ')+'</span>';
    }
    alerts.push(alertHtml);
  }

  // 谨慎
  if (hd.cautious && hd.cautious.length) {
    var cNames = hd.cautious.map(function(c){return c.sector+'('+c.reason+')';}).join(' · ');
    alerts.push('<b style="color:#e65100;">谨慎</b>：'+cNames);
  }

  if (alerts.length) {
    h += '<div style="padding:10px 12px;background:#f3e5f5;border-radius:8px;border-left:3px solid #ce93d8;font-size:12px;color:#555;line-height:1.8;">';
    alerts.forEach(function(a){ h += '<div>• '+a+'</div>'; });
    h += '</div>';
  } else {
    h += '<div style="font-size:12px;color:#999;text-align:center;">各维度信号不足，建议观望等待</div>';
  }

  con.innerHTML = h;
}

// ===== A股+宏观现状预判（五维评分卡）=====
function renderMacroOverview(){
  // ── 数据提取 ──
  var fib = window.SH_FIB || {};
  var macro = window.MACRO_DATA || {};
  var fomc = window.FOMC_SUMMARY || {};
  var cffex = window.CFFEX_HOLDINGS || {};
  var sf = window.SECTOR_FUND_FLOW || {};

  // 技术面数据
  var declineDays = (fib.current && fib.current.days_down) || 0;
  var declinePct = (fib.current && fib.current.total_pct) || 0;
  var nextWindow = '';
  var nextWindowDays = 99;
  if (fib.windows) {
    for (var i = 0; i < fib.windows.length; i++) {
      var w = fib.windows[i];
      if (w.status === 'future' && w.days_left < nextWindowDays) {
        nextWindow = w.name + '(' + w.date + ')';
        nextWindowDays = w.days_left;
      }
    }
  }

  // 宏观数据
  var pmi = ((macro.economy||{}).pmi||{}).value || null;
  var spread = ((macro.monetary||{}).cn_us_spread||{}).value || null;
  var socialFin = ((macro.economy||{}).social_financing||{}).change_pct || null;
  var lpr1y = ((macro.monetary||{}).lpr||{}).lpr_1y || null;

  // 全球数据
  var vix = ((macro.global_macro||{}).vix||{}).value || null;
  var dxy = ((macro.global_macro||{}).dxy||{}).value || null;
  var gold = (((macro.global_macro||{}).commodities||{}).gold||{}).value || null;
  var fomcLabel = fomc.summary || '';

  // 两融（从MARGIN_DATA取最近一条）
  var margin = window.MARGIN_DATA || {};
  var rzLatest = 0;
  if (margin.sh && margin.sh.length) {
    var lastSh = margin.sh[margin.sh.length - 1];
    rzLatest = lastSh.rz_balance || 0;
  }

  // 中信期货
  var cffexNet = cffex.net_total || 0;
  var cffexAbs = Math.abs(cffexNet);

  // 板块资金
  var sfIn = (sf.summary||{}).in_count || 0;
  var sfOut = (sf.summary||{}).out_count || 0;

  // ── 评分逻辑 ──
  function scoreDim(name, icon, score, color, detail) {
    return '<div style="font-size:22px;margin-bottom:2px;">'+icon+'</div>'+
      '<div style="font-size:28px;font-weight:800;color:'+color+';margin-bottom:2px;">'+score+'</div>'+
      '<div style="font-size:11px;font-weight:600;color:#444;margin-bottom:4px;">'+name+'</div>'+
      '<div style="font-size:10px;color:#888;line-height:1.5;">'+detail+'</div>';
  }

  // 颜色函数
  function sc(n){ return n>=7?'#2e7d32':n>=5?'#e65100':n>=3?'#ef6c00':'#c62828'; }

  // 1. 技术面评分
  var techScore = 5, techDetail = [];
  if (declineDays >= 30) { techScore -= 2; techDetail.push('回调'+declineDays+'天'); }
  else if (declineDays >= 15) { techScore -= 1; techDetail.push('回调'+declineDays+'天'); }
  if (declinePct <= -5) { techScore -= 2; techDetail.push('累计'+(declinePct).toFixed(1)+'%'); }
  else if (declinePct <= -3) { techScore -= 1; }
  if (nextWindowDays <= 5) { techDetail.push('窗口临近:'+nextWindow); }
  else if (nextWindowDays <= 10) { techDetail.push('窗口:'+nextWindow); }
  if (techDetail.length === 0) techDetail.push('震荡整理');
  techScore = Math.max(1, Math.min(10, techScore));

  // 2. 资金面评分
  var fundScore = 5, fundDetail = [];
  if (rzLatest >= 15000) { fundScore += 2; fundDetail.push('两融≥1.5万亿'); }
  else if (rzLatest >= 14500) { fundScore += 1; fundDetail.push('两融回升'); }
  if (sfIn > sfOut) { fundScore += 1; fundDetail.push('板块流入>流出'); }
  else if (sfOut > sfIn) { fundScore -= 1; fundDetail.push('板块流出>流入'); }
  if (sfIn >= 8) { fundScore += 1; fundDetail.push('多板块流入'); }
  fundScore = Math.max(1, Math.min(10, fundScore));

  // 3. 宏观面评分
  var macroScore = 5, macroDetail = [];
  if (pmi !== null && pmi < 50) { macroScore -= 2; macroDetail.push('PMI '+pmi+'线下'); }
  if (spread !== null && spread < -2) { macroScore -= 2; macroDetail.push('利差倒挂'+spread.toFixed(1)+'%'); }
  else if (spread !== null && spread < -1) { macroScore -= 1; }
  if (socialFin !== null && socialFin < 0) { macroScore -= 1; macroDetail.push('社融萎缩'); }
  if (lpr1y && lpr1y <= 3.0) { macroScore += 1; } // 低利率利好
  macroScore = Math.max(1, Math.min(10, macroScore));

  // 4. 机构面评分
  var instScore = 5, instDetail = [];
  if (cffexNet < -8000) { instScore -= 2; instDetail.push('净空'+cffexAbs+'手'); }
  else if (cffexNet < -3000) { instScore -= 1; instDetail.push('净空'+cffexAbs+'手'); }
  else if (cffexNet > 3000) { instScore += 1; instDetail.push('净多'+cffexAbs+'手'); }
  if (fomcLabel.indexOf('转鹰')>-1 || fomcLabel.indexOf('加息')>-1) { instScore -= 1; instDetail.push('FOMC转鹰'); }
  instScore = Math.max(1, Math.min(10, instScore));

  // 5. 全球面评分
  var globalScore = 5, globalDetail = [];
  if (vix !== null && vix < 18) { globalScore += 1; globalDetail.push('VIX低('+vix+')'); }
  else if (vix !== null && vix > 25) { globalScore -= 2; globalDetail.push('VIX高('+vix+')'); }
  if (gold && gold > 4000) { globalScore += 1; globalDetail.push('金价新高'); }
  if (fomcLabel.indexOf('维持')>-1 && fomcLabel.indexOf('不变')>-1) { globalScore += 1; }
  globalScore = Math.max(1, Math.min(10, globalScore));

  // ── 渲染 ──
  var elTech = document.getElementById('scoreTech');
  var elFund = document.getElementById('scoreFund');
  var elMacro = document.getElementById('scoreMacro');
  var elInst = document.getElementById('scoreInst');
  var elGlobal = document.getElementById('scoreGlobal');

  if (!elTech) return;

  elTech.innerHTML = scoreDim('技术面','📉',techScore,sc(techScore),techDetail.join(' · '));
  elFund.innerHTML = scoreDim('资金面','💰',fundScore,sc(fundScore),fundDetail.join(' · '));
  elMacro.innerHTML = scoreDim('宏观面','🌍',macroScore,sc(macroScore),macroDetail.join(' · '));
  elInst.innerHTML = scoreDim('机构面','🏦',instScore,sc(instScore),instDetail.join(' · '));
  elGlobal.innerHTML = scoreDim('全球面','🌐',globalScore,sc(globalScore),globalDetail.join(' · '));

  // 更新时间标签
  var timeEl2 = document.getElementById('macroScoreTime');
  if (timeEl2) {
    var latestMacroTime = fib.update_time || macro.update_time || sf.update_time || '';
    if (latestMacroTime) {
      var ft2 = fmtDataTime(latestMacroTime);
      timeEl2.textContent = '更新于 ' + ft2.text;
    }
  }

  // ── 五维综合评判：标题条幅下方总览 ──
  var avgScore = Math.round((techScore+fundScore+macroScore+instScore+globalScore)/5);
  var sentimentWord = avgScore >= 7 ? '偏多' : avgScore >= 5 ? '震荡' : '偏空';
  var sentimentColor = avgScore >= 7 ? '#c62828' : avgScore >= 5 ? '#ff9800' : '#2e7d32';

  // 综合结论（只算行业板块，避免概念重叠虚高）
  var sfIndIn2 = (sf.sectors_in||[]).filter(function(s){return s.type==='行业';});
  var sfIndOut2 = (sf.sectors_out||[]).filter(function(s){return s.type==='行业';});
  var sfTotalIn = sfIndIn2.reduce(function(s,x){return s+(x.net||0);},0);
  var sfTotalOut = sfIndOut2.reduce(function(s,x){return s+Math.abs(x.net||0);},0);
  var lhbStocks = (window.LHB_DATA||{}).stocks||[];
  var pureRes = lhbStocks.filter(function(s){return s.category==='纯共振';});
  var instBuy = lhbStocks.filter(function(s){return (s.inst_net_万||0)>8000 && (s.yz_net_万||0)<=8000;});

  var finalWord = '';
  if (avgScore >= 7 && sfTotalIn > sfTotalOut && pureRes.length >= 2) {
    finalWord = '🟢 资金+机构+技术面共振偏多，可适当参与。';
  } else if (avgScore >= 5) {
    finalWord = '🟡 多空分歧，资金偏多但宏观承压，轻仓等待方向。';
  } else {
    finalWord = '🔴 偏空信号为主，建议减仓观望。';
  }

  // 标题条幅下方的总结栏
  var elBar = document.getElementById('macroVerdictBar');
  if (elBar) {
    elBar.innerHTML = '<span style="color:#f57f17;">五维综合评判：</span><b style="color:' + sentimentColor + ';">' + avgScore + '/10 → ' + sentimentWord + '</b> <span style="color:#888;font-weight:500;">' + finalWord + '</span>';
  }
}

// ===== 资金流向追踪（短线5日 / 中线20日 / 长线60日）=====
function renderTrendFlow(){
  // 已合并到 renderSectorFundFlow + generateSectorRotationAnalysis
  // 原卡片已隐藏，此处静默返回
}

// ===== 板块强度追踪 =====
function renderSectorRS(){
  var rs = window.SECTOR_RS || {};
  function renderTop(list, elId, pctKey) {
    var el = document.getElementById(elId);
    if (!el) return;
    if (!list || !list.length) { el.innerHTML = '<span style="color:#999;">暂无数据</span>'; return; }
    var h = '';
    for (var i = 0; i < Math.min(list.length, 5); i++) {
      var x = list[i];
      var pct = x[pctKey];
      var sign = pct > 0 ? '+' : '';
      h += '<span>' + (i+1) + '. ' + x.name + '</span> <span style="font-weight:600;">' + sign + pct.toFixed(1) + '%</span><br>';
    }
    el.innerHTML = h || '<span style="color:#999;">暂无数据</span>';
  }
  renderTop(rs.strong_5d, 'rs5dTop', 'pct_5d');
  renderTop(rs.strong_20d, 'rs20dTop', 'pct_20d');
  renderTop(rs.strong_52w, 'rs52wTop', 'pct_52w');

  // 顶部总结语句
  var summaryEl = document.getElementById('sectorRSSummary');
  if (summaryEl) {
    var s5 = rs.strong_5d || [], s20 = rs.strong_20d || [], s52 = rs.strong_52w || [];
    if (!s5.length && !s20.length) {
      summaryEl.textContent = '📊 板块强度数据暂未生成，等待盘后更新。';
    } else {
      var top5 = s5[0] || null, top20 = s20[0] || null;
      var hotWord = top5 ? top5.name + '+' + top5.pct_5d.toFixed(1) + '%' : '';
      var trendWord = top20 ? top20.name + '+' + top20.pct_20d.toFixed(1) + '%' : '';
      if (hotWord && trendWord) {
        summaryEl.textContent = '🔥 短线热点：' + hotWord + '领涨5日 | 📊 中期主线：' + trendWord + '领涨20日 | 短线追热/中线跟趋势两大策略并行。';
      } else if (hotWord) {
        summaryEl.textContent = '🔥 短线热点：' + hotWord + '领涨5日，关注追涨动能持续性。';
      } else if (trendWord) {
        summaryEl.textContent = '📊 中期主线：' + trendWord + '领涨20日，中线趋势稳固。';
      } else {
        summaryEl.textContent = '📊 各周期板块强度分化，暂无明显主线。';
      }
    }
  }

  var timeEl = document.getElementById('sectorRSTime');
  if (timeEl && rs.update_time) {
    var ft = fmtDataTime(rs.update_time);
    timeEl.textContent = '更新于 ' + ft.text;
  }
}

// ===== 板块资金轮动（预判信号页） =====
// ===== 板块资金轮动+涨停热力联动（预判信号页） =====
// ===== 板块资金轮动（预判信号页） =====
function renderSectorRotation() {
  var card = document.getElementById('sectorRotationCard');
  var contentEl = document.getElementById('sectorRotationContent');
  if (!card || !contentEl) return;

  var data = window.SECTOR_FUND_FLOW || {};
  if (!data.sectors_in || !data.sectors_in.length) { card.style.display = 'none'; return; }

  var timeEl = document.getElementById('sectorRotationTime');
  if (timeEl && data.update_time) {
    var ft = fmtDataTime(data.update_time);
    timeEl.textContent = '更新于 ' + ft.text;
  }

  generateSectorRotationAnalysis(data, contentEl);
  if (contentEl.innerHTML) { card.style.display = 'block'; }

  // ── 5日/20日/60日 仅流入TOP5 三框（机游共振风格）──
  function buildFlowCardIn(title, icon, bg, color, key) {
    var netK = key.replace('trend_','net_');
    var inList = (data[key] || []).filter(function(x){return x[netK] > 0;}).slice(0, 5);
    var card = '<div style="background:' + bg + ';border-radius:10px;padding:10px;min-height:100px;">';
    card += '<div style="font-size:14px;font-weight:700;color:' + color + ';margin-bottom:6px;">' + icon + ' ' + title + '</div>';
    if (!inList.length) {
      card += '<div style="font-size:12px;color:#999;padding:8px 0;">暂无数据</div>';
    } else {
      inList.forEach(function(x){
        card += '<div style="font-size:13px;color:#333;display:flex;justify-content:space-between;align-items:center;padding:2px 0;">' +
          '<span>' + x.name + '</span>' +
          '<b style="font-size:12px;color:#c62828;white-space:nowrap;">+' + x[netK].toFixed(1) + '亿</b></div>';
      });
    }
    card += '</div>';
    return card;
  }

  var cards = [];
  cards.push(buildFlowCardIn('5日累计', '📅', '#e3f2fd', '#1565c0', 'trend_5d'));
  cards.push(buildFlowCardIn('20日累计', '📊', '#e8f5e9', '#2e7d32', 'trend_20d'));
  cards.push(buildFlowCardIn('60日累计', '📈', '#fff3e0', '#e65100', 'trend_60d'));
  if (cards.length) {
    contentEl.innerHTML += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:10px;">' + cards.join('') + '</div>';
  }
}

// ===== 🧬 多维80+推荐 =====
function renderTop10Daily() {
  var card = document.getElementById('top10DailyCard');
  var contentEl = document.getElementById('top10Content');
  if (!card || !contentEl) return;

  var data = window.TOP10_DAILY || {};
  var top10 = data.top10 || [];
  if (!top10.length) { card.style.display = 'none'; return; }

  card.style.display = 'block';

  // 设置更新时间
  var timeEl = document.getElementById('top10DailyTime');
  if (timeEl && data.update_time) {
    var ft = fmtDataTime(data.update_time);
    timeEl.textContent = '更新于 ' + ft.text;
  }

  function buildBlock(s, rank) {
    var bg, border;
    if (rank <= 3) { bg = '#f3e5f5'; border = '#4527a0'; }
    else if (rank <= 5) { bg = '#ede7f6'; border = '#5e35b1'; }
    else if (rank <= 8) { bg = '#f5f5f5'; border = '#7e57c2'; }
    else { bg = '#fafafa'; border = '#b39ddb'; }

    var sigs = '';
    if (s.signals.chan) sigs += '<span style="color:#b71c1c;font-size:11px;font-weight:700;" title="缠论买">C</span>';
    if (s.signals.jinzuan) sigs += '<span style="color:#ff8f00;font-size:11px;font-weight:700;" title="金钻">J</span>';
    if (s.signals.jigou) sigs += '<span style="color:#1565c0;font-size:11px;font-weight:700;" title="机构变红">I</span>';
    if (s.signals.trend) sigs += '<span style="color:#2e7d32;font-size:11px;font-weight:700;" title="上涨趋势">T</span>';

    return '<div style="background:' + bg + ';border-left:3px solid ' + border + ';border-radius:0 8px 8px 0;padding:10px 12px;display:flex;flex-direction:column;gap:4px;min-width:0;">' +
      '<div style="display:flex;align-items:center;justify-content:space-between;">' +
        '<span style="font-size:10px;font-weight:700;color:' + border + ';background:' + (rank <= 3 ? '#e1bee7' : '#e0e0e0') + ';border-radius:4px;padding:1px 6px;line-height:1.4;">#' + rank + '</span>' +
        '<span style="font-weight:700;font-size:22px;color:' + border + ';">' + s.total_score + '</span>' +
      '</div>' +
      '<div style="font-size:13px;font-weight:700;color:#333;line-height:1.3;">' + s.name + ' <span style="font-size:10px;color:#999;">' + s.code + '</span></div>' +
    '</div>';
  }

  var row1 = top10.filter(function(s){ return s.total_score >= 80; }).slice(0, 5);
  var row2 = top10.filter(function(s){ return s.total_score >= 80; }).slice(5, 10);

  var h = '<div style="display:flex;flex-direction:column;gap:10px;">';
  h += '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;">';
  row1.forEach(function(s, i) { h += buildBlock(s, s.rank); });
  h += '</div>';
  if (row2.length) {
    h += '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;">';
    row2.forEach(function(s, i) { h += buildBlock(s, s.rank); });
    h += '</div>';
  }
  h += '</div>';

  contentEl.innerHTML = h;
}

// ===== 🔥 涨停联动（预判信号页） =====
function renderLimitUpHeatmap() {
  var card = document.getElementById('limitUpHeatCard');
  var contentEl = document.getElementById('limitUpHeatContent');
  var analysisEl = document.getElementById('limitUpHeatAnalysis');
  if (!card || !contentEl) return;

  var data = window.LIMIT_UP_HEATMAP || null;
  if (!data || !data.dates || !data.sectors) { card.style.display = 'none'; return; }

  var timeEl = document.getElementById('limitUpHeatTime');
  if (timeEl && data.update_time) {
    var ft = fmtDataTime(data.update_time);
    timeEl.textContent = '更新于 ' + ft.text;
  }

  function isIgnite(sectorData, idx) {
    if (idx === 0) return sectorData[0] >= 2;
    return sectorData[idx] >= 2 && sectorData[idx - 1] === 0;
  }

  var sorted = data.sectors.slice().sort(function(a,b){
    return b.data.reduce(function(s,n){return s+n;},0) - a.data.reduce(function(s,n){return s+n;},0);
  });

  var h = '<table style="width:100%;border-collapse:collapse;font-size:11px;min-width:500px;">';
  h += '<thead><tr><th style="padding:4px 6px;text-align:left;font-weight:500;color:#888;border-bottom:2px solid #e0e0e0;">板块</th>';
  for (var di = 0; di < data.dates.length; di++) {
    h += '<th style="padding:4px 2px;text-align:center;font-weight:400;color:#aaa;font-size:10px;border-bottom:2px solid #e0e0e0;">' + data.dates[di].split('/').pop() + '</th>';
  }
  h += '<th style="padding:4px 4px;text-align:center;font-weight:500;color:#e65100;border-bottom:2px solid #e0e0e0;">合</th>';
  h += '<th style="padding:4px 6px;text-align:center;font-weight:400;color:#888;font-size:10px;border-bottom:2px solid #e0e0e0;">势</th></tr></thead><tbody>';

  for (var s = 0; s < sorted.length; s++) {
    var sector = sorted[s];
    var total = sector.data.reduce(function(sum,n){return sum+n;},0);
    h += '<tr><td style="padding:4px 6px;font-weight:600;color:#333;white-space:nowrap;">'+sector.name+'</td>';
    for (var j=0;j<sector.data.length;j++){
      var val=sector.data[j];
      var ignite=isIgnite(sector.data,j)?' style="box-shadow:inset 0 0 0 2px #ff9800;border-radius:3px;"':'';
      var bg=val>=8?'#e53935':val>=5?'#ef9a9a':val>=3?'#ffcdd2':val>=2?'#ffebee':val>=1?'#fff5f5':'transparent';
      var cl=val>=4?'#fff':val>=1?'#c62828':'#ccc';
      h+='<td style="padding:3px 2px;text-align:center;background:'+bg+';color:'+cl+';font-weight:500;"'+ignite+'>'+(val===0?'·':val)+'</td>';
    }
    h+='<td style="padding:3px 4px;text-align:center;color:#e65100;font-weight:700;">'+total+'</td>';
    var r3=sector.data.slice(-3).reduce(function(s,n){return s+n;},0);
    var p3=sector.data.slice(-6,-3).reduce(function(s,n){return s+n;},0);
    var tr=r3>p3*1.5?'↑':r3<p3*0.5?'↓':r3>=p3?'→':'↘';
    h+='<td style="padding:3px;text-align:center;color:'+(tr==='↑'?'#c62828':tr==='↓'?'#2e7d32':'#999')+';font-size:12px;">'+tr+'</td></tr>';
  }
  h+='</tbody></table>';
  h+='<div style="display:flex;gap:10px;font-size:10px;color:#999;margin-top:8px;flex-wrap:wrap;align-items:center;">';
  h+='<span style="font-weight:500;color:#555;">热度→</span>';
  h+='<span style="background:#fff5f5;padding:2px 6px;border-radius:3px;border:1px solid #eee;">1</span>';
  h+='<span style="background:#ffebee;padding:2px 6px;border-radius:3px;">2</span>';
  h+='<span style="background:#ffcdd2;padding:2px 6px;border-radius:3px;">3-4</span>';
  h+='<span style="background:#ef9a9a;color:#fff;padding:2px 6px;border-radius:3px;">5-7</span>';
  h+='<span style="background:#e53935;color:#fff;padding:2px 6px;border-radius:3px;">≥8</span>';
  h+='<span style="color:#ccc;">|</span><span style="border:2px solid #ff9800;padding:1px 6px;border-radius:3px;">启动日</span></div>';
  contentEl.innerHTML = h;
  card.style.display = 'block';

  if (!analysisEl) return;
  var analysis=[];
  var sustained=[];for(var si=0;si<sorted.length;si++){var sd=sorted[si].data;var streak=0,ms=0;
    for(var di2=0;di2<sd.length;di2++){if(sd[di2]>=3){streak++;if(streak>ms)ms=streak;}else streak=0;}
    if(ms>=2)sustained.push({name:sorted[si].name,days:ms});}
  if(sustained.length)analysis.push('🔥 <b>持续热点：</b>'+sustained.map(function(x){return x.name+'(连'+x.days+'天)';}).join('、'));
  var ni=[];for(var si2=0;si2<sorted.length;si2++){var sd2=sorted[si2].data;
    if(sd2.slice(0,sd2.length-3).reduce(function(s,n){return s+n;},0)<=1&&sd2.slice(-3).reduce(function(s,n){return s+n;},0)>=4)ni.push(sorted[si2].name);}
  if(ni.length)analysis.push('⚡ <b>新启动：</b>'+ni.join('、')+' — 前期沉寂近期爆发');
  var cl=[];for(var si3=0;si3<sorted.length;si3++){var sd3=sorted[si3].data;var h=Math.ceil(sd3.length/2);
    if(sd3.slice(0,h).reduce(function(s,n){return s+n;},0)>=8&&sd3.slice(h).reduce(function(s,n){return s+n;},0)<=2)cl.push(sorted[si3].name);}
  if(cl.length)analysis.push('❄️ <b>热度消退：</b>'+cl.join('、')+' — 前期热闹近期熄火');
  var ti=data.dates.length-1,tt=sorted.slice().sort(function(a,b){return b.data[ti]-a.data[ti];}).slice(0,3);
  if(tt[0].data[ti]>0)analysis.push('📊 <b>今日最强：</b>'+tt.map(function(x){return x.name+' '+x.data[ti]+'只涨停';}).join('、'));
  var td=sorted.reduce(function(s,sec){return s+sec.data[ti];},0);
  var pd=sorted.reduce(function(s,sec){return s+sec.data[Math.max(0,ti-3)];},0);
  analysis.push('💡 <b>全局：</b>'+(td>pd*1.2?'涨停效应扩大，短线情绪升温':td<pd*0.8?'涨停效应收缩，情绪降温':'涨停效应平稳')+'（当日'+td+'只 vs 3日前'+pd+'只）');
  analysisEl.innerHTML=analysis.map(function(a){return '<div style="line-height:1.7;">'+a+'</div>';}).join('');
  analysisEl.style.display='block';
}

// ===== 系统健康看板 =====
// 分类：live=活数据, scan=核心扫描, signal=信号排名, fund=资金流向, monitor=数据监控, alert=事件预警, macro=宏观外部
// 频率：0=盘前 1=盘中实时 2=盘后更新 3=T+1盘后更新 4=周度 5=月度 6=停更
var FREQ_ORDER = ['盘前','盘中实时','盘后更新','T+1盘后','周度','月度','停更'];
var HEALTH_SOURCES = [
  // ── 盘前 ──
  {label:'全量扫描(盘前)',    icon:'🔴', ts:function(){return (window.SCAN_DATA||{}).scan_time},        maxDays:0,  note:'每日盘前自动运行',             cat:'scan',  freq:0},
  {label:'金股池',            icon:'⭐', ts:function(){return ((window.GOLD_POOL||{}).update_time||(window.SCAN_DATA||{}).scan_time)}, maxDays:30, note:'历史累积池，每日增量', cat:'scan',  freq:0},
  {label:'金股信号',          icon:'🔴', ts:function(){return (window.GOLD_POOL_DATA||{}).update_time},  maxDays:2,  note:'扫描时计算',               cat:'scan',  freq:0},
  {label:'EMA多周期趋势',     icon:'📊', ts:function(){return (window.SCAN_DATA||{}).scan_time},          maxDays:2,  note:'扫描时计算(需≥100日K线)',     cat:'scan',  freq:0},
  {label:'观澜台研报提取',    icon:'📰', ts:function(){return (window.RECOMMEND||{}).update_time||(window.MAHORO_COVERAGE||{})._update_time}, maxDays:2, note:'知识星球研报→自动推股池', cat:'live',  freq:0},
  {label:'国际投行信号',   icon:'📡', ts:function(){return (window.MAHORO_COVERAGE||{})._update_time||''}, maxDays:1, note:'投行评级信号自动化推送', cat:'live',  freq:0},
  {label:'双机同步检查',      icon:'🔄', ts:function(){return new Date().toISOString()}, maxDays:0, note:'部署前版本标记+冲突清理', cat:'monitor',freq:0},
  // ── 盘中实时 ──
  {label:'盘中监控扫描',      icon:'🟡', ts:function(){return (window.WATCH_DATA||{}).scan_time},        maxDays:0,  note:'盘中定时扫描',               cat:'scan',  freq:1},
  {label:'概念涨跌榜',        icon:'📈', ts:function(){return (window.CONCEPT_RANKING||{}).update_time}, maxDays:0,  note:'盘中实时',                 cat:'signal',freq:1},
  {label:'市场异动速览',      icon:'⚡', ts:function(){return (window.MARKET_ALERTS||{}).update_time},   maxDays:0,  note:'盘中实时',                 cat:'signal',freq:1},
  {label:'板块资金流向',      icon:'🚀', ts:function(){return (window.SECTOR_FUND_FLOW||{}).update_time},maxDays:0,  note:'盘中实时',                 cat:'fund',  freq:1},
  {label:'ETF资金估算',       icon:'💰', ts:function(){return (window.NT_DATA||{}).update_time},          maxDays:0,  note:'盘中实时',                 cat:'fund',  freq:1},
  {label:'涨跌+成交额历史',   icon:'📊', ts:function(){return (window.SH_SZ_HISTORY||{}).update_time},   maxDays:0,  note:'盘中实时',                 cat:'monitor',freq:1},
  // ── 盘后更新 ──
  {label:'三线共振追踪',      icon:'📡', ts:function(){return (window.SCAN_DATA||{}).scan_time},        maxDays:2,  note:'追踪股价格每日刷新',         cat:'scan',  freq:2},
  {label:'斐波那契窗口',      icon:'📐', ts:function(){return (window.SH_FIB||{}).update_time},           maxDays:2,  note:'盘后更新',                 cat:'monitor',freq:2},
  {label:'资金流向追踪(5/20/60日)',icon:'💸', ts:function(){return (window.SECTOR_FUND_FLOW||{}).update_time},maxDays:1, note:'盘后更新',                 cat:'fund',  freq:2},
  {label:'投行信号覆盖',      icon:'📰', ts:function(){return ((window.MAHORO_COVERAGE||{})._update_time||'')}, maxDays:1, note:'盘后更新',             cat:'alert', freq:2},
  {label:'停牌预警',          icon:'⛔', ts:function(){return (window.SUSPENSION_ALERT||{}).update_time},maxDays:2,  note:'盘后更新',                 cat:'alert', freq:2},
  {label:'宏观数据',          icon:'🌍', ts:function(){return (window.MACRO_DATA||{}).update_time},       maxDays:1,  note:'盘后更新',                 cat:'macro', freq:2},
  // ── T+1盘后更新 ──
  {label:'龙虎榜',            icon:'🐉', ts:function(){return (window.LHB_DATA||{}).update_time},        maxDays:2,  note:'T+1-盘后更新',             cat:'signal',freq:3},
  {label:'机构买卖统计',      icon:'🏦', ts:function(){return (window.INST_TRADE||{}).update_time},      maxDays:5,  note:'T+1-盘后更新',             cat:'signal',freq:3},
  {label:'资金抱团预判',      icon:'🔥', ts:function(){return (HERRING_DATA||{}).update_time},            maxDays:2,  note:'T+1-盘后更新',             cat:'fund',  freq:3},
  {label:'沪深港通资金(北/南向)', icon:'🌏', ts:function(){return (window.NORTH_FUND_DATA||{}).update_time}, maxDays:7,  note:'每周五19:30更新',         cat:'fund',  freq:5},
  {label:'两融数据',          icon:'📊', ts:function(){return (window.MARGIN_DATA||{}).update_time},     maxDays:2,  note:'T+1-盘后更新',             cat:'monitor',freq:3},
  {label:'ETF份额',           icon:'📋', ts:function(){return (window.ETF_SUBSCRIPTION||{}).update_time},maxDays:5,  note:'T+1-盘后更新',             cat:'monitor',freq:3},
  {label:'中信期货持仓',      icon:'📊', ts:function(){return (window.CFFEX_HOLDINGS||{}).update_time},  maxDays:5,  note:'T+1-盘后更新',             cat:'monitor',freq:3},
  // ── 月度 ──
  {label:'FOMC速览',          icon:'🏛️', ts:function(){return (window.FOMC_SUMMARY||{}).update_time},   maxDays:45, note:'会议日期(7/28下次)',         cat:'alert', freq:5},
  // ── 停更 ──
  {label:'主力个股动向(停更)',icon:'💪', ts:function(){return (MAIN_STOCK_DATA||{}).update_time},         maxDays:999,note:'数据源已停更，离线中',       cat:'macro', freq:6},
  {label:'北向资金(停更)',    icon:'🌏', ts:function(){return (window.NORTH_FUND_DATA||{}).update_time}, maxDays:999,note:'数据源已停更，离线中',       cat:'macro', freq:6},
  // ── 精选预判 ──
  {label:'52周新高',           icon:'📈', ts:function(){return (window.W52_HIGH||{}).update_time},       maxDays:2,  note:'创52周新高个股及板块归属',    cat:'signal',freq:2},
  {label:'分析师评级转向',      icon:'📋', ts:function(){return (window.ANALYST_RATINGS||{}).update_time},maxDays:3,  note:'评级上调/下调/覆盖变化',       cat:'signal',freq:3},
  {label:'政策信号密度',        icon:'🏛️', ts:function(){return (window.POLICY_DENSITY||{}).update_time},  maxDays:3,  note:'政策关键词密度指数(0-100)',    cat:'macro', freq:2},
];

// ===== 页面卡片清单（用于健康看板全部视图的可视性检查）=====
var PAGE_CARDS = [
  // ===== 总览页 =====
  {page:'📋 总览', card:'📅 重要日历',       check:function(){return !!document.getElementById('calendarGrid') && document.getElementById('calendarGrid').innerHTML.length > 0;}},
  {page:'📋 总览', card:'🧠 AI市场速览',      check:function(){return !!document.getElementById('aiSummaryContent') && document.getElementById('aiSummaryContent').innerHTML.length > 200;}},
  {page:'📋 总览', card:'🚀 打新研判',        check:function(){return !!(window.IPO_DATA&&window.IPO_DATA.update_time);}},
  {page:'📋 总览', card:'📊 ETF资金流向',     check:function(){var el=document.getElementById('ntEtfFlowCard'); return el && el.style.display !== 'none';}},
  {page:'📋 总览', card:'💰 板块资金流向',    check:function(){var el=document.getElementById('sectorFundFlowCard'); return el && el.style.display !== 'none';}},
  {page:'📋 总览', card:'📈 股指期货升贴水',  check:function(){var el=document.getElementById('cffexCard'); return el && el.style.display !== 'none';}},
  {page:'📋 总览', card:'📊 概念涨跌排名',    check:function(){var el=document.getElementById('conceptRankingCard'); return el && el.style.display !== 'none';}},
  {page:'📋 总览', card:'⏸️ 金股池停牌',    check:function(){return !!(window.SUSPENSION_ALERT&&window.SUSPENSION_ALERT.update_time);}},
  // ===== 数据监控页 =====
  {page:'📈 数据监控', card:'📊 涨跌+成交额历史', check:function(){return (window.SH_SZ_HISTORY||{}).update_time ? true : false;}},
  {page:'📈 数据监控', card:'📉 斐波那契窗口',    check:function(){return (window.SH_FIB||{}).update_time ? true : false;}},
  {page:'📈 数据监控', card:'📊 两融余额',        check:function(){return (window.MARGIN_DATA||{}).update_time ? true : false;}},
  {page:'📈 数据监控', card:'📊 ETF申赎',         check:function(){return (window.ETF_SUBSCRIPTION||{}).update_time ? true : false;}},
  {page:'📈 数据监控', card:'📊 宏观观测',        check:function(){return (window.MACRO_DATA||{}).update_time ? true : false;}},
  {page:'📈 数据监控', card:'⚠️ 异常数据提醒',    check:function(){return !!(window.MARKET_ALERTS&&window.MARKET_ALERTS.update_time);}},
  {page:'📈 数据监控', card:'🚨 CN危机监测',    check:function(){return !!(window.MACRO_DATA&&window.MACRO_DATA.indicator_status);}},
  {page:'📈 数据监控', card:'🌍 全球危机监测',    check:function(){return !!(window.MACRO_DATA&&(window.MACRO_DATA.global_macro||{}).vix);}},
  // ===== 预判信号页 =====
  {page:'🔮 预判信号', card:'📊 一眼结论',        check:function(){var el=document.getElementById('summaryOverview'); return el && el.style.display !== 'none';}},
  {page:'🔮 预判信号', card:'🎯 精选预判信号',    check:function(){var el=document.getElementById('selectedSignalsCard'); return el && el.style.display !== 'none';}},
  {page:'🔮 预判信号', card:'🔥 涨停联动',        check:function(){var el=document.getElementById('limitUpHeatCard'); return el && el.style.display !== 'none';}},
  {page:'🔮 预判信号', card:'📊 板块资金轮动',    check:function(){var el=document.getElementById('sectorRotationContent'); return el && el.innerHTML.length > 100;}},
  {page:'🔮 预判信号', card:'🐉 龙虎榜监控',      check:function(){return !!(window.LHB_DATA&&window.LHB_DATA.update_time);}},
  {page:'🔮 预判信号', card:'🌏 南向资金',        check:function(){return !!(window.NORTH_FUND_DATA&&window.NORTH_FUND_DATA.update_time);}},
  // ===== 金股观测页 =====
  {page:'⭐ 金股观测', card:'🌟 个股强烈关注',    check:function(){var el=document.getElementById('goldTable'); return el && el.innerHTML.length > 50;}},
  {page:'⭐ 金股观测', card:'🧬 多维80+推荐',    check:function(){var el=document.getElementById('top10Content'); return el && el.innerHTML.length > 100;}},
  {page:'⭐ 金股观测', card:'📊 今日信号速报',    check:function(){var el=document.getElementById('signalHighlightCard'); return el && el.style.display !== 'none';}},
  {page:'⭐ 金股观测', card:'📊 金股池构成',      check:function(){var el=document.getElementById('poolCompCard'); return el && el.style.display !== 'none';}},
  // ===== 竞彩娱乐页 =====
  {page:'🎰 竞彩娱乐', card:'⚽ 世界杯',          check:function(){return !!(window.WORLD_CUP&&window.WORLD_CUP.groups);}},
  {page:'🎰 竞彩娱乐', card:'🎲 彩票概率',        check:function(){return !!document.getElementById('lotteryCard');}},
  // ===== 健康看板页 =====
  {page:'🔐 健康看板', card:'🩺 系统健康表格',   check:function(){return !!document.getElementById('healthDashboard');}},
  {page:'🔐 健康看板', card:'⏱️ F窗口+缠论',     check:function(){var el=document.getElementById('shFibChanlunSection'); return el && el.style.display !== 'none';}},
  {page:'🔐 健康看板', card:'🧠 五维评分卡',      check:function(){var el=document.getElementById('macroScoreCard'); return el && el.style.display !== 'none';}},
  {page:'🔐 健康看板', card:'🚨 CN危机监测',     check:function(){var el=document.getElementById('crisisSection'); return el && el.style.display !== 'none';}},
  {page:'🔐 健康看板', card:'🌍 全球危机监测',    check:function(){var el=document.getElementById('globalCrisisSection'); return el && el.style.display !== 'none';}},
  {page:'🔐 健康看板', card:'🐑 羊群效应',        check:function(){var el=document.getElementById('herdingCard'); return el && el.style.display !== 'none';}},
];

// ===== 暂未上架面板 =====
function toggleUnlistedPanel() {
  var panel = document.getElementById('unlistedPanel');
  var btn = document.getElementById('btnShelfUnlisted');
  var dashboard = document.getElementById('healthDashboard');
  if (!panel || !btn) return;
  var isShown = panel.style.display !== 'none';
  if (isShown) {
    panel.style.display = 'none';
    if (dashboard) dashboard.style.display = '';
    btn.style.background = '#fafafa';
    btn.style.color = '#9e9e9e';
    btn.style.borderColor = '#bdbdbd';
  } else {
    panel.style.display = 'block';
    if (dashboard) dashboard.style.display = 'none';
    btn.style.background = '#7b1fa2';
    btn.style.color = '#fff';
    btn.style.borderColor = '#7b1fa2';
    moveCardsToShelf();
  }
}

var _unlistedCardsMoved = false;
function moveCardsToShelf() {
  if (_unlistedCardsMoved) return;
  var panel = document.getElementById('unlistedPanel');
  if (!panel) return;
  // 移动已隐藏的卡片到暂未上架（顺序：板块资金实况 → F窗口+缠论 → 五维评分 → CN危机监测 → 全球危机监测）
  var cardIds = ['herdingCard', 'shFibChanlunSection', 'macroScoreCard', 'crisisSection', 'globalCrisisSection'];
  cardIds.forEach(function(id) {
    var card = document.getElementById(id);
    if (card) { card.style.display = ''; panel.appendChild(card); }
  });
  _unlistedCardsMoved = true;
}

function renderHealthDashboard(cat){
  cat = cat || 'all';
  var el = document.getElementById('healthDashboard');
  if(!el) return;

  // 更新 sub-tab 按钮样式
  var tabs = document.querySelectorAll('.health-sub-tab');
  for(var i=0;i<tabs.length;i++){
    var t = tabs[i];
    if(t.getAttribute('data-cat')===cat){
      t.style.background='#1976d2'; t.style.color='#fff'; t.style.border='1px solid #1976d2';
    } else {
      t.style.background='#fff'; t.style.color='#333'; t.style.border='1px solid #e0e0e0';
    }
  }

  function fmtAgo(ts){
    if(!ts) return {text:'未知',stale:true,days:999};
    var d = new Date(ts.replace(' ','T'));
    if(isNaN(d.getTime())) return {text:ts,stale:false,days:0};
    var now = new Date();
    var diff = now - d;
    var mins = Math.floor(diff/60000);
    var hours = Math.floor(diff/3600000);
    var days = Math.floor(diff/86400000);
    if(mins<1) return {text:'刚刚',stale:false,days:0};
    if(mins<60) return {text:mins+'分钟前',stale:false,days:0};
    if(hours<24) return {text:hours+'小时前',stale:false,days:0};
    return {text:days+'天前',stale:true,days:days};
  }

  function fmtTime(ts){
    if(!ts) return '--';
    return ts.replace('2026-','').replace('-','/').substring(0,16);
  }

  function row(s){
    var fa = fmtAgo(s.ts());
    var isStale = fa.days > s.maxDays;
    var freqLabel = FREQ_ORDER[s.freq] || '';
    var freqColor = s.freq===6 ? '#999' : s.freq===0 ? '#c62828' : s.freq===1 ? '#e65100' : s.freq===2 ? '#1565c0' : s.freq===3 ? '#7b1fa2' : '#888';
    var r = '<tr style="border-bottom:1px solid #f0f0f0;">';
    r += '<td style="padding:8px 12px;font-weight:500;">'+s.icon+' '+s.label+'</td>';
    r += '<td style="padding:8px 12px;font-size:11px;color:'+freqColor+';font-weight:600;white-space:nowrap;">'+freqLabel+'</td>';
    r += '<td style="padding:8px 12px;color:'+(isStale?'#c62828':'#2e7d32')+';font-weight:'+(isStale?'700':'400')+';">'+fmtTime(s.ts())+'</td>';
    r += '<td style="padding:8px 12px;'+(isStale?'color:#c62828;font-weight:700;':'color:#888')+'">'+fa.text+(isStale?' ⚠️':' ✓')+'</td>';
    r += '<td style="padding:8px 12px;font-size:11px;color:#888;">'+s.note+'</td>';
    r += '</tr>';
    return r;
  }

  // 按频率排序：盘前→盘中实时→盘后更新→T+1盘后→周度→月度→停更
  // 同频率内按新鲜度降序
  var list = cat==='all' ? HEALTH_SOURCES.slice() : HEALTH_SOURCES.filter(function(s){return s.cat===cat});
  list.sort(function(a, b){
    var fa=a.freq!==undefined?a.freq:99, fb=b.freq!==undefined?b.freq:99;
    if(fa!==fb) return fa-fb;
    return fmtAgo(a.ts()).days - fmtAgo(b.ts()).days;
  });

  var rows = '<table style="width:100%;border-collapse:collapse;table-layout:fixed;">';
  rows += '<tr style="background:#f8f9fa;"><th style="padding:8px 12px;text-align:left;width:22%;">数据源</th><th style="padding:8px 12px;text-align:left;width:9%;">频率</th><th style="padding:8px 12px;text-align:left;width:17%;">最后更新</th><th style="padding:8px 12px;text-align:left;width:12%;">状态</th><th style="padding:8px 12px;text-align:left;width:40%;">说明</th></tr>';

  var currentFreq = -1;
  for(var i=0;i<list.length;i++){
    var s = list[i];
    // 全部视图下显示频率分组头
    if(cat==='all' && s.freq !== currentFreq && s.freq !== undefined){
      currentFreq = s.freq;
      var freqName = FREQ_ORDER[s.freq] || '';
      var hdrBg = s.freq===6 ? '#f5f5f5' : s.freq===0 ? '#fff3e0' : s.freq===1 ? '#fff8e1' : '#e3f2fd';
      rows += '<tr style="background:'+hdrBg+';"><td colspan="5" style="padding:6px 12px;font-weight:700;font-size:12px;color:#333;border-top:2px solid #e0e0e0;">📌 '+freqName+'</td></tr>';
    }
    rows += row(s);
  }
  rows += '</table>';

  // 全部视图下：追加页面卡片可视性清单
  if (cat === 'all') {
    rows += '<div style="margin-top:16px;">';
    rows += '<div style="font-weight:700;font-size:14px;color:#1a237e;margin-bottom:8px;padding:6px 12px;background:#e8eaf6;border-radius:6px;">📋 页面卡片可视性状态（每页应有卡片）</div>';
    rows += '<table style="width:100%;border-collapse:collapse;table-layout:fixed;font-size:12px;">';
    rows += '<tr style="background:#f8f9fa;"><th style="padding:6px 8px;text-align:left;width:15%;">页面</th><th style="padding:6px 8px;text-align:left;width:20%;">卡片</th><th style="padding:6px 8px;text-align:center;width:10%;">可见</th><th style="padding:6px 8px;text-align:left;width:55%;">检查项</th></tr>';

    var pageGroups = {};
    for (var i = 0; i < PAGE_CARDS.length; i++) {
      var pc = PAGE_CARDS[i];
      if (!pageGroups[pc.page]) pageGroups[pc.page] = [];
      pageGroups[pc.page].push(pc);
    }

    var pageOrder = Object.keys(pageGroups);
    var rowIdx = 0;
    for (var pi = 0; pi < pageOrder.length; pi++) {
      var pn = pageOrder[pi];
      var cards = pageGroups[pn];
      var allOK = true;
      for (var ci = 0; ci < cards.length; ci++) {
        try {
          if (!cards[ci].check()) { allOK = false; break; }
        } catch(e) { allOK = false; break; }
      }
      for (var ci = 0; ci < cards.length; ci++) {
        var pc = cards[ci];
        var ok = false;
        try { ok = pc.check(); } catch(e) { ok = false; }
        var bg = rowIdx % 2 === 0 ? '#fff' : '#fafafa';
        var icon = ok ? '✅' : '❌';
        var color = ok ? '#2e7d32' : '#c62828';
        var checkDesc = ok ? '数据显示正常' : '数据空或卡片隐藏';
        rows += '<tr style="background:' + bg + ';">';
        if (ci === 0) {
          rows += '<td style="padding:6px 8px;font-weight:700;color:#1a237e;" rowspan="' + cards.length + '">' + pn + '</td>';
        }
        rows += '<td style="padding:6px 8px;font-weight:500;">' + pc.card + '</td>';
        rows += '<td style="padding:6px 8px;text-align:center;color:' + color + ';font-weight:700;">' + icon + '</td>';
        rows += '<td style="padding:6px 8px;font-size:11px;color:' + (ok ? '#666' : '#c62828') + ';">' + checkDesc + '</td>';
        rows += '</tr>';
        rowIdx++;
      }
    }
    rows += '</table></div>';
  }

  el.innerHTML = rows;
}

// ===== 2026世界杯胜率分析 =====
function renderWorldcup(){
  var el = document.getElementById('worldcupContent');
  if(!el) return;
  var d = window.WORLD_CUP || null;
  if(!d || !d.groups) {
    el.innerHTML = '<div style="text-align:center;padding:40px;color:#999;">⚽ 等待数据...</div>';
    return;
  }

  // 辅助函数
  function pts(t){ return t.w*3 + t.d; }
  function gd(t){ return t.gf - t.ga; }
  function winRate(t){ var p=t.w+t.d+t.l||1; return Math.round((t.w*100+t.d*33)/p); }

  function wcCard(title, content){
    return '<div style="background:#f8f9fa;border-radius:8px;padding:14px;margin-bottom:10px;border:1px solid #e0e0e0;">'+
      '<div style="font-weight:700;font-size:14px;color:#1a2a4a;margin-bottom:8px;border-left:3px solid #ff6b35;padding-left:8px;">'+title+'</div>'+
      '<div style="font-size:12px;line-height:1.9;">'+content+'</div></div>';
  }

  var h = '';

  // 更新时间和比赛日
  var wft = d.update_time ? fmtDataTime(d.update_time) : null;
  h += '<div style="font-size:12px;color:#999;margin-bottom:14px;">数据更新：' + (wft ? wft.text : (d.update_time||'')) + ' · ' + (d.matchday||'') + ' <span style="color:#bbb;">· 每日 07:30 更新</span></div>';

  // 休息日/赛程提示
  if (d.status_note) {
    h += '<div style="background:#fff3e0;border:1px solid #ffe0b2;border-radius:6px;padding:8px 12px;margin-bottom:12px;font-size:12px;color:#e65100;">📢 ' + d.status_note + '</div>';
  }

  // 1. 夺冠概率 TOP8
  var odds = d.odds || [];
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">';
  h += wcCard('🏆 夺冠概率 TOP8（Monte Carlo 模拟）', (function(){
    var r = '';
    odds.slice(0,8).forEach(function(o,i){
      var w = i===0?100:(o.prob/odds[0].prob*80).toFixed(0);
      var c = i<3?'#ffd700':i<6?'#e67e22':'#3498db';
      r += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'+
        '<span style="font-size:12px;width:16px;">#'+(i+1)+'</span>'+
        '<span style="flex:1;min-width:60px;font-weight:600;">'+o.n+'</span>'+
        '<span style="font-weight:800;color:'+c+';width:36px;text-align:right;">'+o.prob+'%</span>'+
        '<div style="flex:1;height:6px;background:#e0e0e0;border-radius:3px;"><div style="height:100%;width:'+w+'%;background:'+c+';border-radius:3px;"></div></div></div>';
    }); return r;
  })());

  // 2. 小组赛胜率榜
  var allTeams = d.all_teams || [];
  h += wcCard('📊 小组赛胜率榜（全部48队）', (function(){
    var sorted = allTeams.slice().sort(function(a,b){return winRate(b)-winRate(a);});
    var r = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:2px 10px;font-size:11px;">';
    sorted.slice(0,24).forEach(function(t,i){
      var wr = winRate(t);
      r += '<div style="display:flex;justify-content:space-between;padding:1px 0;">'+
        '<span>'+(i+1)+'. '+t.n+'</span><span style="font-weight:600;color:'+(wr>=75?'#c62828':wr>=50?'#e65100':'#666')+';">'+wr+'%</span></div>';
    }); return r+'</div>';
  })());
  h += '</div>';

  // 2.5 晋级概率预测 (Monte Carlo)
  var qualProbs = d.qual_probs || {};
  h += wcCard('🎲 晋级概率预测（Monte Carlo 5000次模拟）', (function(){
    var r = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:4px;">';
    Object.keys(qualProbs).sort().forEach(function(gid){
      var probs = qualProbs[gid];
      var sorted = Object.entries(probs).sort(function(a,b){return b[1]-a[1];});
      r += '<div style="background:#fff;border-radius:4px;padding:5px 6px;">';
      r += '<div style="font-weight:700;font-size:12px;color:#1a2a4a;margin-bottom:3px;">组 '+gid+'</div>';
      sorted.forEach(function(pair){
        var name = pair[0], prob = pair[1];
        var barColor = prob>=90?'#c62828':prob>=50?'#e67e22':prob>=20?'#3498db':'#b0bec5';
        r += '<div style="display:flex;align-items:center;gap:3px;margin-bottom:2px;font-size:11px;">'+
          '<span style="width:46px;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'+name+'</span>'+
          '<div style="width:50px;height:5px;background:#e0e0e0;border-radius:2px;flex-shrink:0;">'+
          '<div style="height:100%;width:'+Math.max(5,prob)+'%;background:'+barColor+';border-radius:2px;"></div></div>'+
          '<span style="font-weight:700;color:'+barColor+';">'+prob+'%</span></div>';
      });
      r += '</div>';
    });
    return r+'</div>';
  })());

  // 2.6 加权净胜球效率
  var adjEff = d.adj_eff || {};
  h += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">';
  h += wcCard('⚖️ 加权进攻效率 TOP10（进球×对手强度）', (function(){
    var sorted_at = allTeams.slice().sort(function(a,b){
      return (b.adj_gf||b.gf) - (a.adj_gf||a.gf);
    }).slice(0,10);
    var r = '';
    sorted_at.forEach(function(t,i){
      var raw = t.gf||0, adj = (t.adj_gf||0).toFixed(1);
      r += '<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:12px;">'+
        '<span>'+(i+1)+'. '+t.n+'</span>'+
        '<span style="color:#888;">原始'+raw+'球 → <span style="font-weight:600;color:#c62828;">加权'+adj+'</span></span></div>';
    }); return r;
  })());
  h += wcCard('🛡️ 加权防守效率 TOP10（失球÷对手强度）', (function(){
    var sorted_dt = allTeams.slice().sort(function(a,b){
      return (a.adj_ga||a.ga) - (b.adj_ga||b.ga);
    }).slice(0,10);
    var r = '';
    sorted_dt.forEach(function(t,i){
      var raw = t.ga||0, adj = (t.adj_ga||0).toFixed(1);
      r += '<div style="display:flex;justify-content:space-between;padding:2px 0;font-size:12px;">'+
        '<span>'+(i+1)+'. '+t.n+'</span>'+
        '<span style="color:#888;">原始'+raw+'球 → <span style="font-weight:600;color:#2e7d32;">加权'+adj+'</span></span></div>';
    }); return r;
  })());
  h += '</div>';

  // 3. 地区对比
  h += wcCard('🌍 各洲足联表现对比', (function(){
    var regions = {};
    var regionNames = {'UEFA':'欧洲','CONMEBOL':'南美','AFC':'亚洲','CAF':'非洲','CONCACAF':'北美','OFC':'大洋洲'};
    allTeams.forEach(function(t){
      var reg = t.region || '?';
      if(!regions[reg]) regions[reg] = [];
      regions[reg].push(t);
    });
    var regionData = Object.keys(regionNames).map(function(k){
      var list = regions[k] || [];
      var total = list.length || 1;
      var totalPts = list.reduce(function(s,t){return s+pts(t);},0);
      return {k:k, name:regionNames[k], n:list.length, avg:(totalPts/total).toFixed(1)};
    }).sort(function(a,b){return b.avg-a.avg;});
    var r = '<div style="display:grid;grid-template-columns:repeat(6,1fr);gap:4px;font-size:10px;">';
    regionData.forEach(function(d){
      r += '<div style="background:#fff;border-radius:4px;padding:4px 6px;text-align:center;">'+
        '<div style="font-weight:700;">'+d.name+'</div>'+
        '<div style="font-size:11px;">'+d.n+'队</div>'+
        '<div style="color:#e65100;">均'+d.avg+'分</div></div>';
    }); return r+'</div>';
  })());

  // 5. 小组积分榜
  var groups = d.groups || [];
  h += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;">';
  groups.forEach(function(g){
    var sorted = g.teams.slice().sort(function(a,b){ return pts(b)-pts(a) || gd(b)-gd(a) || b.gf-a.gf; });
    h += '<div style="background:#f8f9fa;border-radius:6px;padding:8px 10px;">';
    h += '<div style="font-weight:700;font-size:13px;color:#1a2a4a;margin-bottom:6px;text-align:center;">组 '+g.id+'</div>';
    sorted.forEach(function(t,i){
      var bg = i<2?'#e8f5e9':'';
      h += '<div style="padding:3px 0;font-size:11px;'+(bg?'background:'+bg+';border-radius:3px;padding-left:4px;':'')+'display:flex;justify-content:space-between;">';
      h += '<span>'+(i<2?'⬆':'')+t.name+'</span>';
      h += '<span style="color:#888;">'+t.w+'/'+t.d+'/'+t.l+' '+pts(t)+'分 '+(gd(t)>=0?'+':'')+gd(t)+'</span>';
      h += '</div>';
    });
    h += '</div>';
  });
  h += '</div>';

  // 6. 赛程表（实时数据驱动，已结束场次显示比分）
  var results = d.results || [];
  // 按日期分组
  var resultsByDate = {};
  results.forEach(function(m){
    var dd = m.d;
    if (!resultsByDate[dd]) resultsByDate[dd] = [];
    resultsByDate[dd].push(m);
  });
  
  h += wcCard('📅 赛程表（已结束场次标红比分）', (function(){
    var r = '';
    // 淘汰赛 — 决赛排最前，按日期倒序
    r += '<div style="font-weight:700;font-size:15px;color:#333;margin-bottom:6px;">🏆 淘汰赛阶段</div>';
    var knockout = d.knockout || [];
    var knockoutByDate = {};
    knockout.forEach(function(m){
      var dd = m.date;
      if (!knockoutByDate[dd]) knockoutByDate[dd] = [];
      knockoutByDate[dd].push(m);
    });
    var koDateOrder = Object.keys(knockoutByDate).sort(function(a,b){
      var months = {'Jun':6,'Jul':7};
      var ma = a.split(' '), mb = b.split(' ');
      return (months[mb[0]]||0)*100 + (parseInt(mb[1])||0) - (months[ma[0]]||0)*100 - (parseInt(ma[1])||0);
    });
    koDateOrder.forEach(function(dd){
      var matches = knockoutByDate[dd];
      r += '<div style="display:flex;gap:8px;padding:3px 0;font-size:13px;border-bottom:1px solid #f0f0f0;">';
      r += '<span style="color:#888;min-width:70px;font-weight:600;">'+dd+'</span>';
      r += '<span>';
      matches.forEach(function(m, mi){
        if (mi > 0) r += '、';
        r += '<span style="color:#666;font-size:12px;margin-right:3px;">['+m.round+']</span>' + m.home + ' vs ' + m.away;
        if (m.score) r += ' <b style="color:#c62828;font-size:14px;">'+m.score+'</b>';
        r += ' <span style="color:#999;font-size:12px;">— '+m.venue+'</span>';
      });
      r += '</span></div>';
    });
    // 小组赛 — 日期倒序
    r += '<div style="margin-top:10px;">';
    r += '<div style="font-weight:700;font-size:15px;color:#333;margin:10px 0 6px;">⚽ 小组赛阶段</div>';
    var dateOrder = Object.keys(resultsByDate).sort(function(a,b){
      var months = {'Jun':6,'Jul':7};
      var ma = a.split(' '), mb = b.split(' ');
      return (months[mb[0]]||0)*100 + (parseInt(mb[1])||0) - (months[ma[0]]||0)*100 - (parseInt(ma[1])||0);
    });
    dateOrder.forEach(function(dd){
      var matches = resultsByDate[dd];
      r += '<div style="display:flex;gap:8px;padding:3px 0;font-size:13px;border-bottom:1px solid #f0f0f0;">';
      r += '<span style="color:#888;min-width:70px;font-weight:600;">'+dd+'</span>';
      r += '<span>';
      matches.forEach(function(m, mi){
        if (mi > 0) r += '、';
        r += m.h + ' vs ' + m.a;
        if (m.s) r += ' <b style="color:#c62828;font-size:14px;">'+m.s+'</b>';
      });
      r += '</span></div>';
    });
    r += '</div>';
    return r;
  })());

  el.innerHTML = h;
}

// ===== 数字彩票概率计算器 =====
function renderLottery() {
  var el = document.getElementById('lotteryContent');
  if (!el) return;

  function C(n, k) { if (k > n || k < 0) return 0; var r = 1; for (var i = 1; i <= k; i++) r = r * (n - i + 1) / i; return Math.round(r); }
  function fmtOdds(n) { if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'; return (n / 10000).toFixed(0) + '万'; }

  // 双色球：33选6 × 16选1
  var ssq = [
    { name: '一等奖', cond: '6+1', count: 1, bonus: '浮动(500-1000万)' },
    { name: '二等奖', cond: '6+0', count: 15, bonus: '浮动(10-50万)' },
    { name: '三等奖', cond: '5+1', count: C(6, 5) * C(27, 1), bonus: '3000元' },
    { name: '四等奖', cond: '5+0/4+1', count: C(6, 5) * C(27, 1) * 15 + C(6, 4) * C(27, 2), bonus: '200元' },
    { name: '五等奖', cond: '4+0/3+1', count: C(6, 4) * C(27, 2) * 15 + C(6, 3) * C(27, 3), bonus: '10元' },
    { name: '六等奖', cond: '2+1/1+1/0+1', count: C(6, 2) * C(27, 4) + C(6, 1) * C(27, 5) + C(27, 6), bonus: '5元' },
  ];
  var ssqBase = C(33, 6) * C(16, 1);  // 17721088

  // 大乐透：35选5 × 12选2
  var dlt = [
    { name: '一等奖', cond: '5+2', count: 1, bonus: '浮动(封顶1000万)' },
    { name: '二等奖', cond: '5+1', count: C(2, 1) * C(10, 1), bonus: '浮动(约20万)' },
    { name: '三等奖', cond: '5+0', count: C(10, 2), bonus: '10000元' },
    { name: '四等奖', cond: '4+2', count: C(5, 4) * C(30, 1), bonus: '3000元' },
    { name: '五等奖', cond: '4+1', count: C(5, 4) * C(30, 1) * C(2, 1) * C(10, 1), bonus: '300元' },
    { name: '六等奖', cond: '3+2', count: C(5, 3) * C(30, 2), bonus: '200元' },
    { name: '七等奖', cond: '4+0', count: C(5, 4) * C(30, 1) * C(10, 2), bonus: '100元' },
    { name: '八等奖', cond: '3+1/2+2', count: C(5, 3) * C(30, 2) * C(2, 1) * C(10, 1) + C(5, 2) * C(30, 3), bonus: '15元' },
    { name: '九等奖', cond: '3+0/2+1/1+2/0+2', count: C(5, 3) * C(30, 2) * C(10, 2) + C(5, 2) * C(30, 3) * C(2, 1) * C(10, 1) + C(5, 1) * C(30, 4) + C(30, 5), bonus: '5元' },
  ];
  var dltBase = C(35, 5) * C(12, 2);  // 21425712

  // 期望回报
  var ssqFixed = { 三等奖: 3000, 四等奖: 200, 五等奖: 10, 六等奖: 5 };
  var dltFixed = { 三等奖: 10000, 四等奖: 3000, 五等奖: 300, 六等奖: 200, 七等奖: 100, 八等奖: 15, 九等奖: 5 };
  function expected(rules, base, fixed) {
    var t = 0;
    rules.forEach(function(r) {
      var b = fixed[r.name] || (r.name.indexOf('一') === 0 ? 5000000 : 100000);
      t += b * r.count / base;
    });
    return t;
  }
  var ssqER = expected(ssq, ssqBase, ssqFixed);
  var dltER = expected(dlt, dltBase, dltFixed);

  var h = '';

  // ===== 推荐结论卡片 =====
  var ssqReturnPct = (ssqER / 2 * 100).toFixed(1);
  var dltReturnPct = (dltER / 2 * 100).toFixed(1);
  var better = ssqER > dltER ? '双色球' : '大乐透';
  var betterER = (ssqER > dltER ? ssqER : dltER).toFixed(2);
  var worseER = (ssqER > dltER ? dltER : ssqER).toFixed(2);
  var betterRP = ssqER > dltER ? ssqReturnPct : dltReturnPct;
  var worseRP = ssqER > dltER ? dltReturnPct : ssqReturnPct;
  var yearLoss = (312 - ssqER * 156).toFixed(0);
  var monthLoss = (26 - ssqER * 13).toFixed(0);

  h += '<div style="background:linear-gradient(135deg,#e3f2fd,#bbdefb);border:2px solid #1976d2;border-radius:12px;padding:16px 20px;margin-bottom:16px;">';
  h += '<div style="font-size:15px;font-weight:900;color:#0d47a1;margin-bottom:10px;">📋 AI测算结论</div>';
  h += '<div style="font-size:12px;line-height:2;color:#333;">';
  h += '<b style="color:#c62828;">1. 两者均为负期望值博弈</b> — 长期必亏，数学上没有"赢钱"可能<br>';
  h += '<b style="color:#e65100;">2. 若非要二选一：买 <span style="font-size:16px;background:#e8f5e9;padding:2px 8px;border-radius:4px;">🔴 ' + better + '</span></b> — 期望回报 ¥' + betterER + ' vs ¥' + worseER + '，回本率 ' + betterRP + '% vs ' + worseRP + '%<br>';
  h += '<b style="color:#2e7d32;">3. 推荐玩法：2元单注，不追加不复式</b> — 复式/追加倍数只会同步放大投入和亏损期望，不改变负期望值本质<br>';
  h += '<b style="color:#6a1b9a;">4. 预算建议：每月不超过 26元（每周3次×2元×4周+2元缓冲）</b> — 月度期望亏损约 ¥' + monthLoss + '，年度约 ¥' + yearLoss + '<br>';
  h += '<b style="color:#424242;">5. 正确心态：</b>把2元理解成"买2分钟白日梦"的娱乐消费，而不是投资。中奖是意外，不中是常态。';
  h += '</div></div>';

  // 核心对比表
  h += '<table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:16px;">';
  h += '<tr style="background:#1a2a3a;color:#ff9800;"><th style="padding:6px 10px;">指标</th><th style="text-align:center;padding:6px 10px;">🔴 双色球</th><th style="text-align:center;padding:6px 10px;">🟡 大乐透</th></tr>';
  h += '<tr><td style="padding:6px 10px;">单注价格</td><td style="text-align:center;">2元</td><td style="text-align:center;">2元</td></tr>';
  h += '<tr><td style="padding:6px 10px;">头奖概率</td><td style="text-align:center;color:#c62828;">1/' + fmtOdds(ssqBase) + '</td><td style="text-align:center;color:#c62828;">1/' + fmtOdds(dltBase) + '</td></tr>';
  h += '<tr><td style="padding:6px 10px;">任一中奖概率</td><td style="text-align:center;">6.71%</td><td style="text-align:center;">6.67%</td></tr>';
  h += '<tr><td style="padding:6px 10px;">单注期望回报</td><td style="text-align:center;color:#c62828;">¥' + ssqER.toFixed(2) + '</td><td style="text-align:center;color:#c62828;">¥' + dltER.toFixed(2) + '</td></tr>';
  h += '<tr><td style="padding:6px 10px;">回本率</td><td style="text-align:center;">' + ssqReturnPct + '%</td><td style="text-align:center;">' + dltReturnPct + '%</td></tr>';
  h += '</table>';

  // 各等奖概率
  function prizeTable(title, rules, base) {
    var t = '<div style="margin-bottom:12px;"><b style="font-size:13px;">' + title + '</b>';
    t += '<table style="width:100%;border-collapse:collapse;font-size:11px;margin-top:6px;">';
    t += '<tr style="background:#1a2a3a;color:#ff9800;"><th style="padding:4px 8px;">奖项</th><th style="padding:4px 8px;">条件</th><th style="text-align:right;padding:4px 8px;">概率</th><th style="text-align:right;padding:4px 8px;">1/</th><th style="padding:4px 8px;">奖金</th></tr>';
    rules.forEach(function(r, i) {
      var p = r.count / base;
      var c = i < 3 ? '#ff9800' : '#888';
      t += '<tr><td style="padding:3px 8px;color:' + c + ';">' + r.name + '</td><td style="padding:3px 8px;color:#888;">' + r.cond + '</td><td style="text-align:right;padding:3px 8px;font-size:10px;">' + (p * 100).toFixed(8) + '%</td><td style="text-align:right;padding:3px 8px;">' + Math.round(base / r.count).toLocaleString() + '</td><td style="padding:3px 8px;">' + r.bonus + '</td></tr>';
    });
    t += '</table></div>';
    return t;
  }
  h += prizeTable('🔴 双色球 各等奖概率 (33选6 + 16选1)', ssq, ssqBase);
  h += prizeTable('🟡 大乐透 各等奖概率 (35选5 + 12选2)', dlt, dltBase);

  // 趣味对比
  var dailySSQ = 312 - ssqER * 156;
  var dailyDLT = 312 - dltER * 156;
  h += '<div style="background:linear-gradient(135deg,#fffde7,#fff8e1);border:1px solid #ffe082;border-radius:10px;padding:12px 16px;font-size:12px;line-height:1.8;margin-top:12px;">';
  h += '<b style="color:#e65100;">🎲 趣味概率对照</b><br>';
  h += '• 双色球头奖 ≈ 一个人在同一年被雷劈中3次的概率<br>';
  h += '• 大乐透头奖 ≈ 连续抛24次硬币全部正面的概率<br>';
  h += '• 双色球中六等奖(5元)概率 5.9% — 买17注约能中小奖一次，但净亏29元<br>';
  h += '• 复式投注(如7+1)多花14元，只增加6种组合，中奖概率从1/1772万提升到7/1772万，几乎无意义<br>';
  h += '• 年预算156元(每周3注)：双色球期望亏损¥' + dailySSQ.toFixed(0) + '，大乐透期望亏损¥' + dailyDLT.toFixed(0);
  h += '</div>';

  el.innerHTML = h;
}


// ===== 自动渲染（容错模式：单个函数失败不影响后续）=====
try { renderPredictSummary(); } catch(e) { console.log('renderPredictSummary error:', e.message); }
try { renderSelectedSignals(); } catch(e) { console.log('renderSelectedSignals error:', e.message); }
try { renderMacroOverview(); } catch(e) { console.log('renderMacroOverview error:', e.message); }
try { renderTrendFlow(); } catch(e) { console.log('renderTrendFlow error:', e.message); }
try { renderSectorRS(); } catch(e) { console.log('renderSectorRS error:', e.message); }
try { renderSectorRotation(); } catch(e) { console.log('renderSectorRotation error:', e.message); }
try { renderTop10Daily(); } catch(e) { console.log('renderTop10Daily error:', e.message); }
try { renderLimitUpHeatmap(); } catch(e) { console.log('renderLimitUpHeatmap error:', e.message); }
try { renderHealthDashboard(); } catch(e) { console.log('renderHealthDashboard error:', e.message); }
try { renderWorldcup(); } catch(e) { console.log('renderWorldcup error:', e.message); }
try { renderLottery(); } catch(e) { console.log('renderLottery error:', e.message); }
if (HERRING_DATA && HERRING_DATA.update_time) try { renderHerdingMain(); } catch(e) { console.log('renderHerdingMain error:', e.message); }
if (window.LHB_DATA) try { renderLhbPredict(); } catch(e) { console.log('renderLhbPredict error:', e.message); }
if (window.NORTH_FUND_DATA && window.NORTH_FUND_DATA.update_time) try { renderNorthFund(); } catch(e) { console.log('renderNorthFund error:', e.message); }
try { renderSuspensionAlert(); } catch(e) { console.log('renderSuspensionAlert error:', e.message); }
try { renderIpoScore(); } catch(e) { console.log('renderIpoScore error:', e.message); }

function renderVolatilityCard() {
  var d = window.VOLATILITY_WATCH_DATA || {};
  var card = document.getElementById('volatilityCard');
  if (!card) return;
  card.style.display = 'block';
  var body = document.getElementById('volBody');
  if (!body) return;
  var tEl = document.getElementById('volTime');
  if (tEl) tEl.textContent = fmtCardTime(d, 'update_time');

  // 空数据：框架 + 暂无数据（不隐藏，不造假）
  if (!d.available || !d.indices || !d.indices.length) {
    body.innerHTML = '<div style="text-align:center;padding:14px;color:#888;font-size:12px;">📉 波动率数据暂不可用（指数日K未取到），不展示估算值。</div>'
      + (d.note ? '<div style="font-size:10px;color:#bbb;margin-top:6px;line-height:1.5;">' + d.note + '</div>' : '');
    return;
  }

  var c = d.composite || {};
  var up = '#c62828', down = '#2e7d32';  // 涨红跌绿
  var h = '';

  // 复合信号横幅
  var rc = c.regime_color || '#888';
  h += '<div style="background:' + rc + ';color:#fff;border-radius:8px;padding:10px 12px;margin-bottom:10px;line-height:1.6;">';
  h += '<div style="font-size:16px;font-weight:800;">' + (c.regime || '—') + '</div>';
  if (c.signal_summary) h += '<div style="font-size:11px;opacity:0.96;margin-top:3px;">' + c.signal_summary + '</div>';
  if (c.hypothesis) h += '<div style="font-size:11px;margin-top:5px;font-weight:600;">' + c.hypothesis + '</div>';
  h += '</div>';

  // 今日实录
  if (c.today_note) {
    h += '<div style="font-size:12px;color:#444;background:#f8f9fa;border-left:3px solid #90a4ae;padding:6px 9px;border-radius:4px;margin-bottom:10px;line-height:1.6;">' + c.today_note + '</div>';
  }

  // 关键指标条
  h += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px;">';
  h += volStat('平均20日波动', (c.avg_vol_20d != null ? c.avg_vol_20d.toFixed(1) + '%' : '—'), '#333');
  h += volStat('短端5日波动', (c.avg_vol_5d != null ? c.avg_vol_5d.toFixed(1) + '%' : '—'), '#333');
  var svl = c.vol_short_vs_long_pct;
  h += volStat('短端vs长端', (svl != null ? (svl >= 0 ? '+' : '') + svl.toFixed(1) + '%' : '—'), svl < 0 ? '#2e7d32' : '#c62828');
  h += volStat('指数20日均收益', (c.idx_20d_avg_ret != null ? (c.idx_20d_avg_ret >= 0 ? '+' : '') + c.idx_20d_avg_ret.toFixed(1) + '%' : '—'), c.idx_20d_avg_ret >= 0 ? '#c62828' : '#2e7d32');
  h += '</div>';

  // 逐指数明细表
  h += '<table style="width:100%;font-size:11px;border-collapse:collapse;">';
  h += '<thead><tr style="background:#f5f5f5;color:#666;">'
      + '<th style="padding:4px 3px;text-align:left;">指数</th>'
      + '<th style="padding:4px 3px;text-align:right;">收盘</th>'
      + '<th style="padding:4px 3px;text-align:right;">今日</th>'
      + '<th style="padding:4px 3px;text-align:right;">20日波动</th>'
      + '<th style="padding:4px 3px;text-align:right;">趋势</th>'
      + '<th style="padding:4px 3px;text-align:right;">分位</th>'
      + '<th style="padding:4px 3px;text-align:right;">20日收益</th>'
      + '</tr></thead><tbody>';
  d.indices.forEach(function(m){
    var tcol = m.vol_trend_pct < 0 ? '#2e7d32' : '#c62828';  // 波动降=绿(好)
    var rcol = m.today_pct >= 0 ? '#c62828' : '#2e7d32';     // 涨红跌绿
    var r20 = m.ret_20d >= 0 ? '#c62828' : '#2e7d32';
    h += '<tr style="border-bottom:1px solid #f0f0f0;">'
      + '<td style="padding:4px 3px;font-weight:600;">' + m.name + '</td>'
      + '<td style="padding:4px 3px;text-align:right;color:#888;">' + m.close + '</td>'
      + '<td style="padding:4px 3px;text-align:right;color:' + rcol + ';font-weight:600;">' + (m.today_pct >= 0 ? '+' : '') + m.today_pct.toFixed(2) + '%</td>'
      + '<td style="padding:4px 3px;text-align:right;">' + m.vol_20d.toFixed(1) + '%</td>'
      + '<td style="padding:4px 3px;text-align:right;color:' + tcol + ';font-weight:600;">' + (m.vol_trend_pct >= 0 ? '+' : '') + m.vol_trend_pct.toFixed(1) + '%</td>'
      + '<td style="padding:4px 3px;text-align:right;color:#888;">' + m.vol_pctile.toFixed(0) + '%</td>'
      + '<td style="padding:4px 3px;text-align:right;color:' + r20 + ';">' + (m.ret_20d >= 0 ? '+' : '') + m.ret_20d.toFixed(1) + '%</td>'
      + '</tr>';
  });
  h += '</tbody></table>';

  if (d.note) h += '<div style="font-size:10px;color:#bbb;margin-top:8px;line-height:1.5;">' + d.note + '</div>';
  body.innerHTML = h;
}
function volStat(label, val, color){
  return '<div style="flex:1;min-width:84px;background:#fafafa;border-radius:6px;padding:6px 8px;text-align:center;">'
    + '<div style="font-size:14px;font-weight:700;color:' + color + ';">' + val + '</div>'
    + '<div style="font-size:10px;color:#999;margin-top:2px;">' + label + '</div></div>';
}


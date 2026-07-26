# -*- coding: utf-8 -*-
"""驾驶舱四项升级（2026-07-25，主人拍板：风格不变·浅色马卡龙）
1. 顶部「今日结论」执行摘要一句话（真实数据计算，不编造）
2. ② 最强赛道压缩为 TOP5 表格（当日/5日净流入+连续+占比+共振池关联股），8列多周期折叠
3. 新增 🛰️ 早期信号雷达（B档早期信号 + 三重选股，带触发标签）
4. ③ 共振候选每行加 机构/龙虎榜/技术 三列强度 + 🔶三方共振橙标
附带修复：rsList 未定义 ReferenceError（②旧代码删定义漏删引用 → 整个驾驶舱渲染中断）
"""
import io, os, sys

FILES = [
    "index_master.html",
    "index.html",
    "standalone/overview.html",
    "standalone/predict.html",
    "standalone/gold.html",
    "standalone/health.html",
    "standalone/query.html",
    "standalone/shmonitor.html",
]

# ---------- P1: 顶部执行摘要（插在 出手信号灯计算之后、顶部双卡之前） ----------
P1_OLD = """  else { light='\U0001F7E2 绿灯 · 可操作'; lightColor='#2e7d32'; lightBg='#f1f8e9'; lightText='环境平稳，按下方驾驶舱执行选股'; }
  // 顶部双卡：宏观环境（左） + 短期波动结构（右），双卡均按各自状态上色背景（红绿并置强化警觉）"""
P1_NEW = """  else { light='\U0001F7E2 绿灯 · 可操作'; lightColor='#2e7d32'; lightBg='#f1f8e9'; lightText='环境平稳，按下方驾驶舱执行选股'; }
  // \U0001F4CC 今日结论：一句话执行摘要（2026-07-25 扣子式改造·全部来自真实数据，无一编造）
  var _sffS = window.SECTOR_FUND_FLOW || {};
  var _inS = (_sffS.sectors_in||[]).slice().sort(function(a,b){return (b.net||0)-(a.net||0);});
  var _t10S = (window.TOP10_DAILY||{}).top10 || [];
  var _s80S = _t10S.filter(function(s){return s.total_score>=80;});
  var sumTxt = '';
  if(_inS.length){ sumTxt += _inS.length+' 个赛道当日资金净流入，<b>'+_inS[0].name+'</b> <span style="color:#c62828;font-weight:700;">+'+_inS[0].net+'亿</span>领衔'+(_inS[0].consecutive_days?('（连续'+_inS[0].consecutive_days+'天）'):'')+'；'; }
  else { sumTxt += '当日无板块资金净流入；'; }
  sumTxt += '共振≥80分 <b style="color:#c62828;">'+_s80S.length+'</b> 只；';
  sumTxt += light.indexOf('\U0001F534')>=0 ? '<b style="color:#c62828;">建议观望，不开新仓</b>' : (light.indexOf('\U0001F7E1')>=0 ? '<b style="color:#e65100;">建议轻仓低吸，严格止损</b>' : '<b style="color:#2e7d32;">环境平稳，可按计划执行</b>');
  h += '<div style="background:#fff;border-radius:10px;padding:10px 16px;margin-bottom:14px;box-shadow:0 1px 4px rgba(0,0,0,.05);border-left:4px solid '+lightColor+';font-size:13px;line-height:1.8;color:#444;">\U0001F4CC <b>今日结论</b>：'+sumTxt+'</div>';
  // 顶部双卡：宏观环境（左） + 短期波动结构（右），双卡均按各自状态上色背景（红绿并置强化警觉）"""

# ---------- P2: ② 最强赛道压缩 + 周期折叠 ----------
P2_OLD = """  // ② 最强赛道 TOP6
  var sff = window.SECTOR_FUND_FLOW || {};
  var srs = window.SECTOR_RS || {};
  var inList = (sff.sectors_in||[]).slice().sort(function(a,b){return (b.net||0)-(a.net||0);}).slice(0,6);
  // 板块涨幅多周期（B方案：老实显示涨幅%，按涨幅排序；字段来自 fetch_sector_rs.py 扩展后的 sectors）
  var sectorsAll = (srs.sectors||[]);
  function topSectorList(field, label){
    var arr = sectorsAll.slice().filter(function(x){return x[field]!=null;}).sort(function(a,b){return b[field]-a[field];}).slice(0,5);
    return arr.map(function(x,i){var p=x[field]; return (i+1)+'. '+x.name+' <span style="color:'+(p>=0?'#c62828':'#2e7d32')+';font-weight:600;">'+(p>0?'+':'')+p+'%</span>';});
  }
  var s2 = '<div style="display:flex;gap:10px;flex-wrap:wrap;">';
  s2 += cockpitMiniCol('\U0001F4B0 资金流入 TOP6 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 当日</span>', inList.map(function(x,i){return (i+1)+'. '+x.name+' <span style="color:#c62828;font-weight:600;">+'+(x.net)+'亿</span>'+(x.consecutive_days?' <span style="color:#888;font-size:10px;">('+x.consecutive_days+'天)</span>':'');}));
  s2 += cockpitMiniCol('\U0001F4C8 板块涨幅 TOP5 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 5日</span>', topSectorList('pct_5d'));
  s2 += cockpitMiniCol('\U0001F4C8 板块涨幅 TOP5 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 20日</span>', topSectorList('pct_20d'));
  s2 += cockpitMiniCol('\U0001F4C8 板块涨幅 TOP5 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 30日</span>', topSectorList('pct_30d'));
  s2 += cockpitMiniCol('\U0001F4C8 板块涨幅 TOP5 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 60日</span>', topSectorList('pct_60d'));
  s2 += cockpitMiniCol('\U0001F4C8 板块涨幅 TOP5 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 90日</span>', topSectorList('pct_90d'));
  s2 += cockpitMiniCol('\U0001F4C8 板块涨幅 TOP5 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 180日</span>', topSectorList('pct_180d'));
  s2 += cockpitMiniCol('\U0001F4C8 板块涨幅 TOP5 <span style="font-size:10px;font-weight:400;color:#999;margin-left:2px;">· 52周</span>', topSectorList('pct_52w'));
  s2 += '</div>';
  h += cockpitBlock('② 最强赛道', s2, '#fce4d6', '#bf6b3a');"""
P2_NEW = """  // ② 最强赛道 TOP5（2026-07-25 压缩改版：资金主导表格 + 多周期涨幅折叠）
  var sff = window.SECTOR_FUND_FLOW || {};
  var srs = window.SECTOR_RS || {};
  var inListAll = (sff.sectors_in||[]).slice().sort(function(a,b){return (b.net||0)-(a.net||0);});
  var inList = inListAll.slice(0,6);
  var secTop5 = inListAll.slice(0,5);
  var inSum = 0; inListAll.forEach(function(x){ inSum += (x.net||0); });
  // 共振池关联股：赛道名与共振股板块互含匹配；无匹配老实显示 —（不编造）
  var _t10ForSec = (window.TOP10_DAILY||{}).top10 || [];
  function secMatchStocks(secName){
    var hits = [];
    _t10ForSec.forEach(function(s){
      var secs = (s.sectors&&s.sectors.length)?s.sectors:[];
      for(var i=0;i<secs.length;i++){
        if(secs[i] && (secs[i].indexOf(secName)>=0 || secName.indexOf(secs[i])>=0)){ hits.push(s.name); break; }
      }
    });
    return hits.slice(0,2);
  }
  var s2 = '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
  s2 += '<tr style="color:#999;font-size:11px;text-align:left;"><th style="padding:4px 6px;font-weight:600;">赛道</th><th style="padding:4px 6px;font-weight:600;">当日净流入</th><th style="padding:4px 6px;font-weight:600;">5日净流入</th><th style="padding:4px 6px;font-weight:600;">连续</th><th style="padding:4px 6px;font-weight:600;" title="占当日全部净流入板块合计的比例">当日占比</th><th style="padding:4px 6px;font-weight:600;">共振池关联股</th></tr>';
  secTop5.forEach(function(x,i){
    var share = inSum>0 ? Math.round((x.net||0)/inSum*100) : 0;
    var rec = secMatchStocks(x.name);
    var n5 = x.net_5d;
    s2 += '<tr style="border-top:1px solid #f5f5f5;">'
      + '<td style="padding:5px 6px;font-weight:700;color:#333;">'+(i+1)+'. '+x.name+'</td>'
      + '<td style="padding:5px 6px;color:#c62828;font-weight:700;">+'+x.net+'亿</td>'
      + '<td style="padding:5px 6px;color:'+(n5!=null&&n5<0?'#2e7d32':'#c62828')+';font-weight:600;">'+(n5!=null?((n5>0?'+':'')+n5+'亿'):'—')+'</td>'
      + '<td style="padding:5px 6px;color:#888;">'+(x.consecutive_days?x.consecutive_days+'天':'—')+'</td>'
      + '<td style="padding:5px 6px;"><span style="display:inline-block;background:#f0e6ff;color:#5e4b7a;border-radius:4px;padding:1px 7px;font-weight:600;">'+share+'%</span></td>'
      + '<td style="padding:5px 6px;color:#1565c0;">'+(rec.length?rec.join('、'):'<span style="color:#bbb;">—</span>')+'</td>'
      + '</tr>';
  });
  s2 += '</table>';
  // 多周期涨幅（默认折叠，点按钮展开；字段来自 fetch_sector_rs.py）
  var sectorsAll = (srs.sectors||[]);
  function topSectorList(field, label){
    var arr = sectorsAll.slice().filter(function(x){return x[field]!=null;}).sort(function(a,b){return b[field]-a[field];}).slice(0,5);
    return arr.map(function(x,i){var p=x[field]; return (i+1)+'. '+x.name+' <span style="color:'+(p>=0?'#c62828':'#2e7d32')+';font-weight:600;">'+(p>0?'+':'')+p+'%</span>';});
  }
  var s2More = '<div style="display:flex;gap:10px;flex-wrap:wrap;">';
  s2More += cockpitMiniCol('\U0001F4C8 涨幅 TOP5 · 5日', topSectorList('pct_5d'));
  s2More += cockpitMiniCol('\U0001F4C8 涨幅 TOP5 · 20日', topSectorList('pct_20d'));
  s2More += cockpitMiniCol('\U0001F4C8 涨幅 TOP5 · 30日', topSectorList('pct_30d'));
  s2More += cockpitMiniCol('\U0001F4C8 涨幅 TOP5 · 60日', topSectorList('pct_60d'));
  s2More += cockpitMiniCol('\U0001F4C8 涨幅 TOP5 · 90日', topSectorList('pct_90d'));
  s2More += cockpitMiniCol('\U0001F4C8 涨幅 TOP5 · 180日', topSectorList('pct_180d'));
  s2More += cockpitMiniCol('\U0001F4C8 涨幅 TOP5 · 52周', topSectorList('pct_52w'));
  s2More += '</div>';
  s2 += '<div style="margin-top:8px;"><button onclick="var d=document.getElementById(&quot;cockpitSectorMore&quot;);var open=d.style.display===&quot;none&quot;;d.style.display=open?&quot;&quot;:&quot;none&quot;;this.innerHTML=open?&quot;收起多周期涨幅 ▴&quot;:&quot;展开多周期涨幅 ▾&quot;;" style="padding:4px 12px;border-radius:6px;font-size:11px;cursor:pointer;border:1px solid #e8d9c5;background:#fdf6ee;color:#bf6b3a;">展开多周期涨幅 ▾</button></div>';
  s2 += '<div id="cockpitSectorMore" style="display:none;margin-top:8px;">'+s2More+'</div>';
  h += cockpitBlock('② 最强赛道 TOP5', s2, '#fce4d6', '#bf6b3a');
  // \U0001F6F0 早期信号雷达（苗头阶段：B档早期信号 + 三重选股，异步填充）
  h += cockpitBlock('\U0001F6F0 早期信号雷达（苗头阶段 · 信号未确认，仅供跟踪）', '<div id="cockpitEarlyRadar" style="font-size:12px;color:#999;">加载早期信号...</div>', '#ffe0b2', '#e65100');"""

# ---------- P3: 修复 rsList 未定义（驾驶舱渲染中断的致命 bug） ----------
P3_OLD = """  inList.concat(rsList).forEach(function(x){ strongSet[x.name]=1; });"""
P3_NEW = """  // 2026-07-25 修：rsList 定义早已随「板块RS TOP3」列删除，此处引用漏删 → ReferenceError 中断整个驾驶舱渲染
  inList.forEach(function(x){ strongSet[x.name]=1; });"""

# ---------- P4: ④ 之后把 lhb/mahoro 命中集挂到 __COCKPIT_DATA 供③三列强度用 ----------
P4_OLD = """  h += cockpitBlock('④ 机构/投行/龙虎榜验证', sigHtml, '#b3d4fc', '#1565c0');"""
P4_NEW = """  h += cockpitBlock('④ 机构/投行/龙虎榜验证', sigHtml, '#b3d4fc', '#1565c0');
  // 2026-07-25 三列强度：把命中集挂到 __COCKPIT_DATA 供 renderCockpitResonance 使用
  if(__COCKPIT_DATA){ __COCKPIT_DATA.lhbCodes = lhbCodes; __COCKPIT_DATA.mahoroCodes = mahoroCodes; }"""

# ---------- P5: ③ 共振行加 机构/龙虎榜/技术 三列强度 + 三方共振橙标 ----------
P5_OLD = """    var planBadge = '<span style="font-size:10px;color:#c62828;margin-left:4px;">止盈 <b>'+tp+'</b></span><span style="font-size:10px;color:#2e7d32;margin-left:4px;">止损 <b>'+sl+'</b></span>';
    h += '<div style="display:flex;align-items:center;gap:8px;font-size:12px;border-bottom:1px solid #f0f0f0;padding:4px 0;">'
      + '<span style="font-weight:700;min-width:80px;">'+s.name+'</span>'
      + '<span style="color:#c62828;font-weight:700;">'+s.total_score+'</span>'
      + '<span style="color:#7b1fa2;font-size:10px;">'+secTxt+'</span>'
      + (s.signals?('<span style="color:#888;font-size:10px;">'+(s.signals.chan?'C':'')+(s.signals.jinzuan?'J':'')+(s.signals.jigou?'I':'')+(s.signals.trend?'T':'')+'</span>'):'')
      + winBadge
      + planBadge
      + '</div>';"""
P5_NEW = """    var planBadge = '<span style="font-size:10px;color:#c62828;margin-left:4px;">止盈 <b>'+tp+'</b></span><span style="font-size:10px;color:#2e7d32;margin-left:4px;">止损 <b>'+sl+'</b></span>';
    // 2026-07-25 三列强度：机构 / 龙虎榜(游资) / 技术 —— 全部来自评分分项与命中集，无编造；北向已停披露不展示
    var _lhbC = __COCKPIT_DATA.lhbCodes || {};
    var _mhC = __COCKPIT_DATA.mahoroCodes || {};
    var instV = s.score_inst||0;
    var techV = (s.score_base||0)+(s.score_enhance||0);
    var lhbHit = !!_lhbC[s.code];
    var mhHit = !!_mhC[s.code];
    var tripleHit = (instV>0 && lhbHit && (s.sig_count||0)>=2);
    var strengthBadge = '<span style="font-size:10px;background:'+(instV>0?'#fdecea':'#f5f5f5')+';color:'+(instV>0?'#c62828':'#999')+';border-radius:4px;padding:1px 6px;">机构'+(instV>0?'+'+instV:'—')+'</span>'
      + '<span style="font-size:10px;background:'+(lhbHit?'#fdecea':'#f5f5f5')+';color:'+(lhbHit?'#c62828':'#999')+';border-radius:4px;padding:1px 6px;margin-left:3px;">龙虎榜'+(lhbHit?'✓':'—')+'</span>'
      + '<span style="font-size:10px;background:#e8f4fd;color:#1565c0;border-radius:4px;padding:1px 6px;margin-left:3px;">技术'+techV+'</span>'
      + (mhHit?'<span style="font-size:10px;background:#ede7f6;color:#5e35b1;border-radius:4px;padding:1px 6px;margin-left:3px;">投行✓</span>':'')
      + (tripleHit?'<span style="font-size:10px;background:#fff3e0;color:#e65100;border:1px solid #ffcc80;border-radius:4px;padding:1px 6px;margin-left:3px;font-weight:700;">\U0001F536三方共振</span>':'');
    h += '<div style="display:flex;align-items:center;gap:8px;font-size:12px;border-bottom:1px solid #f0f0f0;padding:4px 0;flex-wrap:wrap;">'
      + '<span style="font-weight:700;min-width:80px;">'+s.name+'</span>'
      + '<span style="color:#c62828;font-weight:700;">'+s.total_score+'</span>'
      + '<span style="color:#7b1fa2;font-size:10px;">'+secTxt+'</span>'
      + strengthBadge
      + winBadge
      + planBadge
      + '</div>';"""

# ---------- P6: 早期信号雷达渲染函数 + 接入 tier 推荐 fetch 回调 ----------
P6_OLD = """  }).then(function(d){
    con.innerHTML = buildCockpitTierRecommendAlimiHTML(d);
  }).catch(function(e){
    var errMsg = (e && e.message) ? e.message : String(e);
    con.innerHTML = '<div style="padding:10px 14px;font-size:11px;color:#b71c1c;background:#fff;border-radius:10px;border:1px solid #ffcdd2;line-height:1.6;">\u26A0\uFE0F 驾驶舱精选加载失败：<code style="font-size:10px;background:#fff5f5;padding:1px 4px;border-radius:3px;">'+errMsg+'</code></div>';
  });
}"""
P6_NEW = """  }).then(function(d){
    con.innerHTML = buildCockpitTierRecommendAlimiHTML(d);
    try{ renderCockpitEarlyRadar(d); }catch(e){}
  }).catch(function(e){
    var errMsg = (e && e.message) ? e.message : String(e);
    con.innerHTML = '<div style="padding:10px 14px;font-size:11px;color:#b71c1c;background:#fff;border-radius:10px;border:1px solid #ffcdd2;line-height:1.6;">\u26A0\uFE0F 驾驶舱精选加载失败：<code style="font-size:10px;background:#fff5f5;padding:1px 4px;border-radius:3px;">'+errMsg+'</code></div>';
    try{ renderCockpitEarlyRadar(null); }catch(e2){}
  });
}
// \U0001F6F0 早期信号雷达（2026-07-25 新增：B档早期信号 + 三重选股苗头，带触发标签；数据不可得则如实显示暂无）
function renderCockpitEarlyRadar(d){
  var el = document.getElementById('cockpitEarlyRadar');
  if(!el) return;
  var items = {}; var order = [];
  if(d && d.tier_b && d.tier_b.length){
    d.tier_b.slice().sort(function(a,b){return (b.total_score||0)-(a.total_score||0);}).slice(0,6).forEach(function(c){
      if(!items[c.code]){ order.push(c.code); }
      items[c.code] = { name:c.name, tags:[c.early||'早期信号'], rsi:c.rsi, ret20:c.ret20 };
    });
  }
  var exp = window.EXPERIMENT_DATA || {};
  var tObj = exp.triple_select || exp.triple || exp;
  var tLists = (tObj && tObj.lists) || {};
  [['金钻起涨','\U0001F31F金钻起涨'],['主力进场','\U0001F3E6主力进场'],['三重选股','\U0001F52E三重共振']].forEach(function(pair){
    (tLists[pair[0]]||[]).slice(0,6).forEach(function(x){
      if(items[x.code]){ if(items[x.code].tags.indexOf(pair[1])<0) items[x.code].tags.push(pair[1]); }
      else if(order.length<8){ order.push(x.code); items[x.code]={name:x.name,tags:[pair[1]]}; }
    });
  });
  if(!order.length){ el.innerHTML = '<div style="font-size:12px;color:#999;">今日暂无早期信号（B档与三重选股均无输出）</div>'; return; }
  var hh = '<div style="display:flex;gap:8px;flex-wrap:wrap;">';
  order.slice(0,8).forEach(function(code){
    var it = items[code];
    hh += '<div style="background:#fff8f0;border:1px solid #ffe0b2;border-radius:8px;padding:6px 10px;min-width:140px;">';
    hh += '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;"><span style="font-weight:700;font-size:13px;color:#5d4037;">'+it.name+'</span><span style="font-size:10px;color:#999;">'+code+'</span></div>';
    hh += '<div style="margin-top:3px;display:flex;gap:4px;flex-wrap:wrap;">'+it.tags.map(function(t){return '<span style="font-size:10px;background:#fff3e0;color:#e65100;border-radius:4px;padding:1px 6px;font-weight:600;">'+t+'</span>';}).join('')+'</div>';
    if(it.rsi!=null || it.ret20!=null){
      hh += '<div style="font-size:10px;color:#888;margin-top:3px;">'+(it.rsi!=null?('RSI '+it.rsi):'')+(it.ret20!=null?(' · 20日'+(it.ret20>=0?'+':'')+it.ret20+'%'):'')+'</div>';
    }
    hh += '</div>';
  });
  hh += '</div>';
  el.innerHTML = hh;
}"""

PATCHES = [
    ("P1 今日结论摘要", P1_OLD, P1_NEW),
    ("P2 ②赛道压缩+雷达占位", P2_OLD, P2_NEW),
    ("P3 rsList修复", P3_OLD, P3_NEW),
    ("P4 命中集挂载", P4_OLD, P4_NEW),
    ("P5 ③三列强度", P5_OLD, P5_NEW),
    ("P6 早期雷达函数", P6_OLD, P6_NEW),
]

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    total_fail = 0
    for rel in FILES:
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            print(f"[SKIP] {rel} 不存在")
            continue
        with io.open(p, encoding="utf-8") as f:
            src = f.read()
        applied, missed = [], []
        for name, old, new in PATCHES:
            cnt = src.count(old)
            if cnt == 1:
                src = src.replace(old, new)
                applied.append(name)
            elif cnt == 0:
                missed.append(name + "(0处)")
            else:
                missed.append(name + f"({cnt}处,跳过防误替换)")
        if applied:
            with io.open(p, "w", encoding="utf-8", newline="") as f:
                f.write(src)
        status = "OK" if not missed else "PARTIAL"
        if missed:
            total_fail += 1
        print(f"[{status}] {rel}: 应用 {len(applied)}/{len(PATCHES)}" + (f"; 未命中: {', '.join(missed)}" if missed else ""))
    sys.exit(1 if total_fail else 0)

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""2026-07-25 审计修复：③共振候选股 renderCockpitResonance 三个逻辑问题
  R1 副标题加 id（供动态更新）
  R2 list70 随赛道过滤 + 保存全量 + 动态更新副标题计数
  R3 无≥80 时不再提前 return 吞掉 70-79 观察区（改 if/else 包裹）
  R4 R3 的闭合括号（else 分支）
"""
import sys

FILES = [
    "index_master.html",
    "standalone/overview.html",
    "standalone/predict.html",
    "standalone/gold.html",
    "standalone/health.html",
    "standalone/query.html",
    "standalone/shmonitor.html",
]

# ---- R1: 副标题加 id ----
R1_OLD = ("'<div style=\"font-size:12px;color:#666;margin-bottom:4px;\">≥80："
          "<b style=\"color:#2e7d32;\">'+s80.length+'</b> 只详细显示；70-79："
          "<b style=\"color:#bf6b3a;\">'+s70.length+'</b> 只仅计数观察</div>' + filterBtns")
R1_NEW = ("'<div id=\"cockpitResoSummary\" style=\"font-size:12px;color:#666;margin-bottom:4px;\">≥80："
          "<b style=\"color:#2e7d32;\">'+s80.length+'</b> 只详细显示；70-79："
          "<b style=\"color:#bf6b3a;\">'+s70.length+'</b> 只仅计数观察</div>' + filterBtns")

# ---- R2: list70 随过滤 + 全量 + 副标题联动 ----
R2_OLD = """  var list = top10.filter(function(s){return s.total_score>=80;});
  var list70 = top10.filter(function(s){return s.total_score>=70 && s.total_score<80;});
  if(cockpitResonanceFilter!=='all'){
    if(cockpitResonanceFilter==='__other__'){
      list = list.filter(function(s){ var secs=sectorOf(s); var hit=false; secs.forEach(function(x){ if(strongSet[x]) hit=true; }); return !hit; });
    } else {
      list = list.filter(function(s){ return sectorOf(s).indexOf(cockpitResonanceFilter)>=0; });
    }
  }"""
R2_NEW = """  var listAll80 = top10.filter(function(s){return s.total_score>=80;});
  var listAll70 = top10.filter(function(s){return s.total_score>=70 && s.total_score<80;});
  var list = listAll80.slice();
  var list70 = listAll70.slice();
  if(cockpitResonanceFilter!=='all'){
    var _secFilter = function(s){
      if(cockpitResonanceFilter==='__other__'){ var secs=sectorOf(s); var hit=false; secs.forEach(function(x){ if(strongSet[x]) hit=true; }); return !hit; }
      return sectorOf(s).indexOf(cockpitResonanceFilter)>=0;
    };
    list = list.filter(_secFilter);
    list70 = list70.filter(_secFilter);
  }
  // 2026-07-25 审计修复：③副标题计数随赛道过滤联动（避免与详细列表数量不符）
  var _sumEl = document.getElementById('cockpitResoSummary');
  if(_sumEl){
    if(cockpitResonanceFilter==='all'){
      _sumEl.innerHTML = '≥80：<b style="color:#2e7d32;">'+listAll80.length+'</b> 只详细显示；70-79：<b style="color:#bf6b3a;">'+listAll70.length+'</b> 只仅计数观察';
    } else {
      _sumEl.innerHTML = '本赛道 ≥80：<b style="color:#2e7d32;">'+list.length+'</b> 只 / 70-79：<b style="color:#bf6b3a;">'+list70.length+'</b> 只（全市场 ≥80:'+listAll80.length+' · 70-79:'+listAll70.length+'）';
    }
  }"""

# ---- R3: 无≥80 不提前 return（改 if 包裹）----
R3_OLD = """  if(!list.length){ el.innerHTML = '<div style="font-size:12px;color:#999;padding:6px 0;">该赛道暂无 ≥80 共振股</div>'; return; }
  var h = '<div style="display:flex;flex-direction:column;gap:6px;">';"""
R3_NEW = """  var h = '';
  if(list.length){
  h += '<div style="display:flex;flex-direction:column;gap:6px;">';"""

# ---- R4: R3 的 else 闭合 ----
R4_OLD = """  });
  h += '</div>';
  if(list70.length){"""
R4_NEW = """  });
  h += '</div>';
  } else { h += '<div style="font-size:12px;color:#999;padding:6px 0;">该赛道暂无 ≥80 共振股</div>'; }
  if(list70.length){"""

PATCHES = [("R1", R1_OLD, R1_NEW), ("R2", R2_OLD, R2_NEW),
           ("R3", R3_OLD, R3_NEW), ("R4", R4_OLD, R4_NEW)]

fail = 0
for f in FILES:
    with open(f, "r", encoding="utf-8") as fh:
        src = fh.read()
    orig = src
    report = []
    for name, old, new in PATCHES:
        n = src.count(old)
        if n != 1:
            report.append(f"{name}=MISS({n})")
            fail += 1
            continue
        src = src.replace(old, new)
        report.append(f"{name}=OK")
    if src != orig:
        with open(f, "w", encoding="utf-8") as fh:
            fh.write(src)
    print(f"{f}: {' '.join(report)}")

print("=== DONE, fail=%d ===" % fail)
sys.exit(1 if fail else 0)

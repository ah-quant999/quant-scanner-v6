#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026-07-25 驾驶舱二次精修：
1. 多周期涨幅默认展开，去掉折叠按钮
2. 共振候选股仅 ≥80 分详细显示，标题/副标题备注；70-79 只保留计数+ compact 观察区
"""
import os, re

TARGETS = [
    "index_master.html",
    "standalone/overview.html",
    "standalone/predict.html",
    "standalone/gold.html",
    "standalone/health.html",
    "standalone/query.html",
    "standalone/shmonitor.html",
]

PATCHES = [
    # P1: 注释改默认展开
    (
        "sector_more_comment",
        "  // 多周期涨幅（默认折叠，点按钮展开；字段来自 fetch_sector_rs.py）",
        "  // 多周期涨幅（默认展开；字段来自 fetch_sector_rs.py）",
    ),
    # P2: 删除折叠按钮
    (
        "sector_more_button",
        """  s2 += '<div style="margin-top:8px;"><button onclick="var d=document.getElementById(&quot;cockpitSectorMore&quot;);var open=d.style.display===&quot;none&quot;;d.style.display=open?&quot;&quot;:&quot;none&quot;;this.innerHTML=open?&quot;收起多周期涨幅 ▴&quot;:&quot;展开多周期涨幅 ▾&quot;;" style="padding:4px 12px;border-radius:6px;font-size:11px;cursor:pointer;border:1px solid #e8d9c5;background:#fdf6ee;color:#bf6b3a;">展开多周期涨幅 ▾</button></div>';
  s2 += '<div id="cockpitSectorMore" style="display:none;margin-top:8px;">'+s2More+'</div>';""",
        """  s2 += '<div id="cockpitSectorMore" style="display:block;margin-top:10px;">'+s2More+'</div>';""",
    ),
    # P3: 标题备注
    (
        "resonance_title",
        "  h += cockpitBlock('③ 共振候选股（≥70/≥80 · 赛道过滤 · 止盈止损）<span id=\"cockpitResonanceWinRate\" style=\"font-size:12px;color:#888;font-weight:400;margin-left:8px;\"></span>',",
        "  h += cockpitBlock('③ 共振候选股（仅 ≥80 分详细显示 · 赛道过滤）<span id=\"cockpitResonanceWinRate\" style=\"font-size:12px;color:#888;font-weight:400;margin-left:8px;\"></span>',",
    ),
    # P4: 副标题备注
    (
        "resonance_subtitle",
        "    '<div style=\"font-size:12px;color:#666;margin-bottom:4px;\">≥80：<b style=\"color:#2e7d32;\">'+s80.length+'</b> 只　·　70-79：<b style=\"color:#bf6b3a;\">'+s70.length+'</b> 只　·　全部：'+top10.length+' 只</div>' + filterBtns + '<div id=\"cockpitResonance\"></div>' + planHtml,",
        "    '<div style=\"font-size:12px;color:#666;margin-bottom:4px;\">≥80：<b style=\"color:#2e7d32;\">'+s80.length+'</b> 只详细显示；70-79：<b style=\"color:#bf6b3a;\">'+s70.length+'</b> 只仅计数观察</div>' + filterBtns + '<div id=\"cockpitResonance\"></div>' + planHtml,",
    ),
    # P5: 渲染函数过滤条件从 >=70 改为 >=80，并给 70-79 加 compact 观察区
    (
        "resonance_filter",
        "  var list = top10.filter(function(s){return s.total_score>=70;});",
        """  var list = top10.filter(function(s){return s.total_score>=80;});
  var list70 = top10.filter(function(s){return s.total_score>=70 && s.total_score<80;});""",
    ),
    # P6: 空状态文案
    (
        "resonance_empty",
        "  if(!list.length){ el.innerHTML = '<div style=\"font-size:12px;color:#999;padding:6px 0;\">该赛道暂无 ≥70 共振股</div>'; return; }",
        "  if(!list.length){ el.innerHTML = '<div style=\"font-size:12px;color:#999;padding:6px 0;\">该赛道暂无 ≥80 共振股</div>'; return; }",
    ),
    # P7: 在详细列表末尾加 70-79 观察区
    (
        "resonance_close",
        """  h += '</div>';
  el.innerHTML = h;
}""",
        """  h += '</div>';
  if(list70.length){
    h += '<div style=\"font-size:11px;color:#888;margin-top:8px;border-top:1px dashed #e0e0e0;padding-top:8px;\">70-79分观察区（共'+list70.length+'只，仅列名+分数，不展开详细信号）：' +
      list70.slice(0,12).map(function(s){ return '<span style=\"margin-right:10px;\">'+s.name+' <b>'+s.total_score+'</b></span>'; }).join('') +
      (list70.length>12?' <span style=\"color:#bbb;\">等</span>':'') + '</div>';
  }
  el.innerHTML = h;
}""",
    ),
]

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    for fname in TARGETS:
        path = os.path.join(root, fname)
        if not os.path.exists(path):
            print(f"SKIP (missing): {fname}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        applied = 0
        for name, old, new in PATCHES:
            cnt = src.count(old)
            if cnt == 1:
                src = src.replace(old, new)
                applied += 1
                print(f"  OK {name} in {fname}")
            elif cnt == 0:
                # maybe already patched
                if new in src:
                    print(f"  SKIP {name} in {fname} (already patched)")
                else:
                    print(f"  MISS {name} in {fname}")
            else:
                print(f"  MULTI {name} in {fname}: {cnt}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
        print(f"{fname}: {applied}/{len(PATCHES)} patches applied")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补做 P7：70-79 观察区（仅 renderCockpitResonance 末尾，用前序 strengthBadge 上下文定位）"""
import os

TARGETS = [
    "index_master.html",
    "standalone/overview.html",
    "standalone/predict.html",
    "standalone/gold.html",
    "standalone/health.html",
    "standalone/query.html",
    "standalone/shmonitor.html",
]

OLD = """      + strengthBadge
      + winBadge
      + planBadge
      + '</div>';
  });
  h += '</div>';
  el.innerHTML = h;
}"""

NEW = """      + strengthBadge
      + winBadge
      + planBadge
      + '</div>';
  });
  h += '</div>';
  if(list70.length){
    h += '<div style="font-size:11px;color:#888;margin-top:8px;border-top:1px dashed #e0e0e0;padding-top:8px;">70-79分观察区（共'+list70.length+'只，仅列名+分数，不展开详细信号）：' +
      list70.slice(0,12).map(function(s){ return '<span style="margin-right:10px;">'+s.name+' <b>'+s.total_score+'</b></span>'; }).join('') +
      (list70.length>12?' <span style="color:#bbb;">等</span>':'') + '</div>';
  }
  el.innerHTML = h;
}"""

def main():
    root = os.path.dirname(os.path.abspath(__file__))
    for fname in TARGETS:
        path = os.path.join(root, fname)
        if not os.path.exists(path):
            print(f"SKIP {fname}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            src = f.read()
        cnt = src.count(OLD)
        if cnt == 1:
            src = src.replace(OLD, NEW)
            print(f"OK {fname}")
        elif cnt == 0:
            if NEW in src:
                print(f"SKIP {fname} (already patched)")
            else:
                print(f"MISS {fname}")
        else:
            print(f"MULTI {fname}: {cnt}")
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""extract_standalone_final.py - stub
独立页已由 extract_panels_v6.py 生成，此处仅做占位。
"""
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
standalone_dir = os.path.join(BASE, 'standalone')
os.makedirs(standalone_dir, exist_ok=True)

# 检查关键文件是否存在，不存在则创建最小占位
placeholders = ['triple_resonance.html', 'worldcup.html', 'guide.html']
for fname in placeholders:
    fpath = os.path.join(standalone_dir, fname)
    if not os.path.exists(fpath):
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(f'<!-- placeholder: {fname} -->\n<html><body>占位页，请运行 extract_panels_v6.py 重新生成</body></html>\n')
        print(f"  [placeholder] {fname}")

print("[extract_standalone_final] ✓ 完成（stub）")
sys.exit(0)

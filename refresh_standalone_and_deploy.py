"""
独立页面自动更新 + 部署脚本
用法:
  python refresh_standalone_and_deploy.py           # 完整流程（更新数据+重新生成+部署）
  python refresh_standalone_and_deploy.py --skip-data  # 跳过数据更新，只重新生成页面并部署
  python refresh_standalone_and_deploy.py --skip-deploy  # 只重新生成页面，不部署

流程：
  1. 运行 update_data_v2.py 注入最新数据到 dist/index.html
  2. 运行 extract_panels_v6.py 重新生成8个主面板独立页
  3. 运行 extract_standalone_final.py 重新生成逻辑详解页
  4. 复制 standalone/ → dist/standalone/
  5. 运行 deploy_now.py --force 部署到 GitHub Pages
"""
import os
import sys
import subprocess
import argparse
import json
import shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))

def log(msg):
    now = datetime.now().strftime('%H:%M:%S')
    print(f"[{now}] {msg}")

def run_cmd(cmd, check=True):
    """运行命令，返回 (success, output)"""
    log(f"▶ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        log(f"  ❌ 失败 (exit {r.returncode}): {r.stderr[-300:]}")
        if check:
            raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{r.stderr[-500:]}")
        return False, r.stderr
    else:
        # 打印最后几行输出
        out = r.stdout.strip().split('\n')[-3:]
        for line in out:
            if line.strip():
                log(f"  {line}")
        return True, r.stdout

def step1_update_data():
    """步骤1：注入最新数据到 dist/index.html"""
    log("=" * 50)
    log("步骤1: 更新 dist/index.html 数据注入")
    log("=" * 50)
    ok, _ = run_cmd([sys.executable, 'update_data_v2.py'])
    return ok

def step2_extract_panels():
    """步骤2：重新生成8个主面板独立页"""
    log("=" * 50)
    log("步骤2: 重新生成主面板独立页 (extract_panels_v6.py)")
    log("=" * 50)
    ok, _ = run_cmd([sys.executable, 'extract_panels_v6.py'])
    return ok

def step3_extract_static():
    """步骤3：重新生成逻辑详解页（纯静态，预渲染JS内容）"""
    log("=" * 50)
    log("步骤3: 重新生成逻辑详解页")
    log("=" * 50)
    ok, _ = run_cmd([sys.executable, 'extract_standalone_final.py'])
    return ok

def step3b_build_crisis_radar():
    """步骤3b：重新生成危机雷达独立页 (build_crisis_radar.py)"""
    log("=" * 50)
    log("步骤3b: 重新生成危机雷达独立页 (build_crisis_radar.py)")
    log("=" * 50)
    # 数据缺失不致命：build 脚本自带兜底；失败仅告警不中止
    ok, _ = run_cmd([sys.executable, 'build_crisis_radar.py'], check=False)
    if not ok:
        log("  ⚠️ 危机雷达页生成失败（不中止，沿用旧页）")
    return True

def step3c_build_market_signal():
    """步骤3c：重新生成市场面信号独立页 (build_market_signal.py)。
    生成器已与线上手工精修版逐字节幂等（含 guide.html#数据监控 锚点），
    每次部署自动刷新数据，不会覆盖手工改动。数据缺失不致命，失败仅告警不中止。"""
    log("=" * 50)
    log("步骤3c: 重新生成市场面信号独立页 (build_market_signal.py)")
    log("=" * 50)
    ok, _ = run_cmd([sys.executable, 'build_market_signal.py'], check=False)
    if not ok:
        log("  ⚠️ 市场面信号页生成失败（不中止，沿用旧页）")
    return True

def step4_copy_to_dist():
    """步骤4：复制 standalone/ → dist/standalone/"""
    log("=" * 50)
    log("步骤4: 复制 standalone/ → dist/standalone/")
    log("=" * 50)
    src = os.path.join(BASE, 'standalone')
    dst = os.path.join(BASE, 'dist', 'standalone')
    
    if not os.path.exists(src):
        log(f"  ❌ 源目录不存在: {src}")
        return False
    
    os.makedirs(dst, exist_ok=True)
    
    count = 0
    for fname in os.listdir(src):
        if fname.endswith('.html'):
            s = os.path.join(src, fname)
            d = os.path.join(dst, fname)
            shutil.copy2(s, d)
            size = os.path.getsize(d) // 1024
            log(f"  ✓ {fname} ({size}KB)")
            count += 1
    
    log(f"  共复制 {count} 个文件")
    return True

def step5_deploy():
    """步骤5：部署到 GitHub Pages"""
    log("=" * 50)
    log("步骤5: 部署到 GitHub Pages")
    log("=" * 50)
    ok, out = run_cmd([sys.executable, 'deploy_now.py', '--force'])
    return ok

def verify_standalone():
    """验证独立页面数据完整性"""
    log("=" * 50)
    log("验证: 检查独立页面数据完整性")
    log("=" * 50)
    
    issues = []
    
    # 检查 guide.html 是否有内容
    gu_path = os.path.join(BASE, 'standalone', 'guide.html')
    if os.path.exists(gu_path):
        size = os.path.getsize(gu_path)
        if size < 10000:
            issues.append(f"⚠️ guide.html 太小 ({size} bytes)，可能内容为空")
        else:
            log(f"  ✓ guide.html: {size//1024}KB")
    
    if issues:
        log("验证发现以下问题：")
        for issue in issues:
            log(f"  {issue}")
        return False
    else:
        log("✅ 所有独立页面验证通过")
        return True

def main():
    parser = argparse.ArgumentParser(description='独立页面自动更新+部署')
    parser.add_argument('--skip-data', action='store_true', help='跳过数据更新（dist/index.html 已是最新时使用）')
    parser.add_argument('--skip-deploy', action='store_true', help='只重新生成页面，不部署')
    parser.add_argument('--verify-only', action='store_true', help='只验证，不重新生成')
    args = parser.parse_args()
    
    log("🚀 开始独立页面自动更新流程")
    log(f"   跳过数据更新: {args.skip_data}")
    log(f"   跳过部署: {args.skip_deploy}")
    log(f"   仅验证: {args.verify_only}")
    
    if args.verify_only:
        verify_standalone()
        return
    
    success = True
    
    # 步骤1：更新数据注入
    if not args.skip_data:
        if not step1_update_data():
            log("❌ 数据注入失败，中止")
            return
    else:
        log("⏭️  跳过数据更新")
    
    # 步骤2：重新生成主面板页
    if not step2_extract_panels():
        log("❌ 主面板页生成失败，中止")
        return
    
    # 步骤3：重新生成静态页
    if not step3_extract_static():
        log("❌ 静态页生成失败，中止")
        return
    
    # 步骤3b：重新生成危机雷达独立页
    step3b_build_crisis_radar()

    # 步骤3c：重新生成市场面信号独立页
    step3c_build_market_signal()
    
    # 验证
    if not verify_standalone():
        log("⚠️ 验证未通过，但继续部署...")
    
    # 步骤4：复制到 dist/
    if not step4_copy_to_dist():
        log("❌ 复制失败，中止")
        return
    
    # 步骤5：部署
    if not args.skip_deploy:
        if not step5_deploy():
            log("❌ 部署失败")
            success = False
    else:
        log("⏭️  跳过部署")
        log(f"   独立页面已生成在: {os.path.join(BASE, 'standalone')}")
        log(f"   请手动运行: python deploy_now.py --force")
    
    log("=" * 50)
    if success:
        log("✅ 独立页面自动更新流程完成！")
        log(f"   线上地址: <ADDRESS_REMOVED>")
    else:
        log("⚠️  流程完成，但部署失败，请检查错误信息")
    log("=" * 50)

if __name__ == '__main__':
    main()

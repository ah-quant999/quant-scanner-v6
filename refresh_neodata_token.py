# -*- coding: utf-8 -*-
"""
refresh_neodata_token.py — 刷新本地 neodata 金融数据凭证

用途：
    把从 connect_cloud_service 拿到的 tempToken 写入 repo-temp/.neodata_token，
    并立即打一次真实接口验证是否有效。供自动化(本机 AI)在每天抓取前调用，
    避免 neodata 三脚本(fetch_52w_high / fetch_sector_fund_flow / fetch_sector_rs)
    因 token 过期(约 23h)静默 401 失效。

数据去向：
    - 写 E:/workspace/stock-scanner/repo-temp/.neodata_token  (已被 .gitignore 忽略，不会进仓库)
    - 格式: {"token": "<tempToken>", "saved_at": <unix秒>}

依赖：仅 Python 标准库。token 通过 --token-file 传入(文件仅含 tempToken 一行)，
      严禁在命令行内联明文 token(防 shell 历史/进程列表泄露)。

用法(自动化里)：
    python refresh_neodata_token.py --token-file E:/Temp/.neotok_tmp
退出码：0=成功且验证通过；1=参数/写文件失败；2=验证接口返回鉴权失败。
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(HERE, ".neodata_token")
NEODATA_URL = "https://copilot.tencent.com/agenttool/v1/neodata"


def load_token_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def save_token(token):
    data = {"token": token, "saved_at": int(time.time())}
    tmp = TOKEN_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, TOKEN_FILE)  # 原子替换，避免写到一半被读取
    return data


def validate(token):
    body = json.dumps({
        "query": "贵州茅台最新收盘价",
        "channel": "neodata",
        "sub_channel": "workbuddy",
    }).encode("utf-8")
    req = urllib.request.Request(NEODATA_URL, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        d = json.loads(resp.read().decode("utf-8", "replace"))
        if resp.status == 200 and d.get("suc"):
            recall = d.get("data", {}).get("apiData", {}).get("apiRecall", [])
            return True, f"HTTP 200 | suc=True | 召回 {len(recall)} 块"
        return False, f"HTTP {resp.status} | suc={d.get('suc')} | msg={d.get('msg')}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code} | {e.read().decode('utf-8','replace')[:160]}"
    except Exception as e:
        return False, f"请求异常: {repr(e)[:160]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-file", required=True,
                    help="含 tempToken 的文件路径(文件仅一行 token，不内联明文)")
    args = ap.parse_args()

    try:
        token = load_token_from_file(args.token_file)
    except Exception as e:
        print(f"❌ 读取 token 文件失败: {e}")
        return 1
    if not token or not token.startswith("tk_"):
        print(f"❌ token 格式异常(应以 tk_ 开头): {token[:8]}...")
        return 1

    try:
        save_token(token)
    except Exception as e:
        print(f"❌ 写入 .neodata_token 失败: {e}")
        return 1
    print(f"✅ 已写入 .neodata_token (token 长度 {len(token)}, saved_at={int(time.time())})")

    ok, msg = validate(token)
    if ok:
        print(f"✅ 验证通过: {msg}")
        return 0
    print(f"❌ 验证失败: {msg}")
    return 2


if __name__ == "__main__":
    sys.exit(main())

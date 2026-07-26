#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_neodata_to_gh_secret.py
=== 把本机 .neodata_token 推送到 GitHub Secrets NEODATA_TOKEN ===
供云端 GitHub Actions 工作流在 fetch 前注入到 data/.neodata_token 用。

首次使用步骤：
  1. 浏览器到 https://github.com/settings/tokens 创建一个 PAT (classic)
     - 勾选 `repo` scope
     - 复制生成的 token (ghp_xxxx 开头)
  2. 写入本机 .gh_pat 文件（gitignored），仅一行：
     echo "ghp_xxxxxxxxxxxx" > repo-temp/.gh_pat
  3. 手动跑一次：python sync_neodata_to_gh_secret.py
     → 会自动获取 repo public key、加密 token、PUT 到 GitHub API
     → 验证：浏览器打开 https://github.com/ah-quant999/quant-scanner-v6/settings/secrets/actions
       应看到 NEODATA_TOKEN 已设置

后续：automation-1784084629462 (17:25) 会自动调用此脚本，本机有 token 就推。

依赖：pynacl (pip install pynacl)；GitHub PAT 通过 GH_PAT 环境变量 / .gh_pat 文件 / git credential manager 获取
"""

import os
import sys
import json
import base64
import subprocess
import datetime
import urllib.request
import urllib.error

REPO = "ah-quant999/quant-scanner-v6"
SECRET_NAME = "NEODATA_TOKEN"
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".neodata_token")
PAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gh_pat")
ROOT = os.path.dirname(os.path.abspath(__file__))
OPS_STATUS_FILE = os.path.join(ROOT, "data", ".ops_status.json")


def _get_pat_from_git_credential():
    """兜底：从 git credential manager 取 github.com 的 PAT（ghp_/gho_ 等）。

    双机适配：阿狸咪机 credential fill 可能挂死，故仅在 env / .gh_pat 都缺失时才调用，
    且设 20s 超时避免阻塞自动化。
    """
    try:
        payload = "protocol=https\nhost=github.com\n\n"
        proc = subprocess.run(
            ["git", "credential", "fill"],
            input=payload, capture_output=True, text=True, timeout=20,
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.startswith("password="):
                    return line[len("password="):].strip()
    except Exception:
        pass
    return ""


def get_pat():
    """获取 GitHub PAT（优先级：GH_PAT 环境变量 > .gh_pat 文件 > git credential manager）"""
    pat = os.environ.get("GH_PAT", "").strip()
    if pat:
        return pat
    if os.path.exists(PAT_FILE):
        with open(PAT_FILE, encoding="utf-8") as f:
            return f.read().strip()
    pat = _get_pat_from_git_credential()
    if pat:
        return pat
    print(f"❌ 找不到 {PAT_FILE}，未设置 GH_PAT，且 git credential 也无 github.com 凭据")
    print(f"   创建 PAT: https://github.com/settings/tokens （需要 repo scope）")
    print(f"   保存: echo 'ghp_xxxx' > {PAT_FILE}")
    sys.exit(1)


def get_local_token():
    """读取本机 .neodata_token"""
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ 找不到 {TOKEN_FILE}，请先跑 17:25 自动化取 token")
        sys.exit(1)
    with open(TOKEN_FILE, encoding="utf-8") as f:
        return f.read().strip()


def update_ops_status(updates):
    """更新 data/.ops_status.json，merge 现有字段而不是覆盖。

    用途：sync_neodata_to_gh_secret.py 17:25 刷新 token 后立即调用，
    把 neodata_valid_until / neodata_updated 同步给运维卡片，
    防止 09:30~17:31 期间一直误报"令牌已过期"。

    与 fetch_neodata_daily.py 内同名函数逻辑一致，保持单一职责。
    """
    os.makedirs(os.path.dirname(OPS_STATUS_FILE), exist_ok=True)
    cur = {}
    if os.path.exists(OPS_STATUS_FILE):
        try:
            cur = json.load(open(OPS_STATUS_FILE, encoding="utf-8"))
        except Exception:
            cur = {}
    cur.update(updates)
    cur["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(OPS_STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(cur, f, ensure_ascii=False, indent=2)
    print(f"📝 已同步 ops_status.json: {list(updates.keys())}")


def gh_api(method, path, pat, body=None):
    """调用 GitHub API"""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {pat}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "stock-scanner-sync-script")
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, data=data, timeout=15) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        return e.code, json.loads(raw) if raw else {}


def encrypt_secret(public_key_b64, secret_value):
    """用 repo public key 加密 secret（libsodium sealed box）"""
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.ciphers.aead import AES
    import hashlib

    # 解码公钥
    pub_bytes = base64.b64decode(public_key_b64)
    # GitHub 用的是 libsodium sealed box（curve25519xsalsa20poly1305）
    # cryptography 库没有 sealed box 原生支持，但提供了等价的实现
    # 实际 GitHub 文档: https://docs.github.com/en/rest/actions/secrets
    # 加密方式: PyNaCl 的 Box 或 sealed box
    # cryptography 不直接支持，但可以手写 sealed_box 等价
    # —— 退而求其次：安装 PyNaCl 替代
    raise NotImplementedError("需要 PyNaCl (libsodium binding)")


def main():
    pat = get_pat()
    token_json = get_local_token()
    # 验证 token JSON 格式
    try:
        tk = json.loads(token_json)
        token_value = tk.get("token", "")
        if not token_value.startswith("tk_"):
            print(f"⚠️ token 格式异常（不是 tk_ 开头）: {token_value[:20]}...")
    except Exception as e:
        print(f"❌ .neodata_token JSON 解析失败: {e}")
        sys.exit(1)

    # 1. 获取 repo public key
    print("🔑 获取 repo public key...")
    status, pub = gh_api("GET", f"/repos/{REPO}/actions/secrets/public-key", pat)
    if status != 200:
        print(f"❌ 获取 public key 失败: HTTP {status} {pub}")
        sys.exit(1)
    key_id = pub["key_id"]
    public_key = pub["key"]

    # 2. 加密 token（用 PyNaCl）
    try:
        from nacl import encoding, public
    except ImportError:
        print("❌ 缺 PyNaCl 库，请安装: pip install pynacl")
        sys.exit(1)
    # GitHub 返回的 public_key 是 base64 字符串，要先解码为 32 字节 raw key
    pk_raw = base64.b64decode(public_key)
    pk = public.PublicKey(pk_raw)
    sealed_box = public.SealedBox(pk)
    encrypted = sealed_box.encrypt(token_json.encode("utf-8"))
    encrypted_b64 = base64.b64encode(encrypted).decode("utf-8")

    # 3. PUT 到 GitHub API
    print(f"📤 推送到 GitHub Secret {SECRET_NAME}...")
    status, resp = gh_api("PUT", f"/repos/{REPO}/actions/secrets/{SECRET_NAME}", pat, {
        "encrypted_value": encrypted_b64,
        "key_id": key_id,
    })
    if status in (201, 204):
        print(f"✅ 推送成功 (HTTP {status})")
        print(f"   验证: https://github.com/{REPO}/settings/secrets/actions")
    else:
        # 2026-07-23 修复：原为 sys.exit(1)，导致 GitHub 不可达（如当日 17:25 网络超时）
        # 时本地 .ops_status.json 的 neodata 字段陈旧 → 审计 step7 误报 mismatch，
        # 且阻断后续本地 ops 更新与部署。Secret 推送失败是「云端 workflow 用不到新 token」
        # 这一个问题，不应牵连本地运维状态更新（独立本地操作，与 GitHub Secret 可达性无关）。
        print(f"⚠️ 推送失败: HTTP {status} {resp}（继续本地 ops 更新与部署，不影响本机）")

    # 4. 同步写 ops_status.json（防止运维卡片 09:30~17:31 误报"令牌已过期"）
    #    字段与 fetch_neodata_daily.py 保持一致：valid_until = saved_at + 24h
    try:
        tk = json.loads(token_json)
        saved_at = int(tk.get("saved_at", 0))
        if saved_at:
            valid_until_dt = datetime.datetime.fromtimestamp(saved_at) + datetime.timedelta(hours=24)
            update_ops_status({
                "neodata_status": "ok",
                "neodata_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "neodata_valid_until": valid_until_dt.strftime("%Y-%m-%d %H:%M:%S"),
            })
    except Exception as e:
        # ops_status 同步失败不应阻断 secret 推送（已成功），只警告
        print(f"⚠️ 同步 ops_status.json 失败（不影响 secret 推送）: {e}")

    # 5. 立即重新生成 dist/ 并部署，让前端 ops_status 卡片拿到最新 neodata_valid_until
    #    否则前端读的是旧 HTML 内嵌的 OPS_STATUS，会继续误报"令牌已过期"
    try:
        import subprocess as _sp
        _ud = os.path.join(ROOT, "update_data_v2.py")
        if os.path.exists(_ud):
            print("🔄 刷新 dist/ 数据（注入新 ops_status）...")
            _r = _sp.run([sys.executable, _ud, "--fast"], capture_output=True, text=True, timeout=120)
            if _r.returncode == 0:
                print("✅ dist/ 已刷新")
                # 尝试部署
                _dp = os.path.join(ROOT, "deploy_now.py")
                if os.path.exists(_dp):
                    print("🚀 部署到 GitHub Pages...")
                    _r2 = _sp.run([sys.executable, _dp, "--force"], capture_output=True, text=True, timeout=300)
                    if _r2.returncode == 0:
                        print("✅ 部署成功，运维卡片将立即更新")
                    else:
                        print(f"⚠️ 部署退出码 {_r2.returncode}（secret 已推送，可稍后手动部署）")
                        if _r2.stderr.strip():
                            print(f"   stderr: {_r2.stderr.strip()[-200:]}")
            else:
                print(f"⚠️ update_data_v2.py 退出码 {_r.returncode}: {_r.stderr.strip()[-150:]}")
        else:
            print(f"⚠️ 未找到 update_data_v2.py，跳过 dist 刷新（请手动跑 update_data_v2.py --fast + deploy）")
    except Exception as e:
        print(f"⚠️ 自动刷新 dist/ 失败（不影响 secret 推送）: {e}")


if __name__ == "__main__":
    main()

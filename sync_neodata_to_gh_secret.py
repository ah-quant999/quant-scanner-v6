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

依赖：cryptography (pip install cryptography)
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error

REPO = "ah-quant999/quant-scanner-v6"
SECRET_NAME = "NEODATA_TOKEN"
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".neodata_token")
PAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gh_pat")


def get_pat():
    """获取 GitHub PAT（优先级：env > .gh_pat 文件）"""
    pat = os.environ.get("GH_PAT", "").strip()
    if pat:
        return pat
    if not os.path.exists(PAT_FILE):
        print(f"❌ 找不到 {PAT_FILE}，也未设置 GH_PAT 环境变量")
        print(f"   创建 PAT: https://github.com/settings/tokens （需要 repo scope）")
        print(f"   保存: echo 'ghp_xxxx' > {PAT_FILE}")
        sys.exit(1)
    with open(PAT_FILE, encoding="utf-8") as f:
        return f.read().strip()


def get_local_token():
    """读取本机 .neodata_token"""
    if not os.path.exists(TOKEN_FILE):
        print(f"❌ 找不到 {TOKEN_FILE}，请先跑 17:25 自动化取 token")
        sys.exit(1)
    with open(TOKEN_FILE, encoding="utf-8") as f:
        return f.read().strip()


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
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


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
        print(f"❌ 推送失败: HTTP {status} {resp}")
        sys.exit(1)


if __name__ == "__main__":
    main()

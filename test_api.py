# -*- coding: utf-8 -*-
"""
最小测试：能不能调通智谱 API，以及哪个模型名字能用

运行方法（在 patent-innovation 文件夹里打开终端）：
    python test_api.py
"""
import requests
from config import ZHIPU_API_KEY

URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# 依次尝试这些模型名，看哪个能用（免费的排在前面）
CANDIDATES = [
    "glm-4-flash",
    "glm-4-flash-250414",
    "glm-4.5-flash",
    "glm-4-air",
    "glm-4-plus",
]

print("=" * 62)
print("第 1 步：检查密钥")
print("=" * 62)
if "在这里" in ZHIPU_API_KEY or len(ZHIPU_API_KEY) < 20:
    print("❌ config.py 里还没有填密钥")
    print("   打开 config.py，把 ZHIPU_API_KEY 换成你的完整密钥")
    raise SystemExit
print(f"  ✅ 密钥长度 {len(ZHIPU_API_KEY)} 位，开头是 {ZHIPU_API_KEY[:8]}...")
print()

print("=" * 62)
print("第 2 步：依次试各个模型")
print("=" * 62)
ok = []
for m in CANDIDATES:
    print(f"  {m:<24} ", end="", flush=True)
    try:
        r = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {ZHIPU_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": m,
                "messages": [{"role": "user", "content": "只回复两个字：通了"}],
                "temperature": 0.1,
            },
            timeout=60,
        )
        if r.status_code == 200:
            d = r.json()
            txt = d["choices"][0]["message"]["content"].strip()
            usage = d.get("usage", {})
            print(f"✅ 成功！ 回复「{txt}」  token={usage.get('total_tokens')}")
            ok.append(m)
        else:
            try:
                msg = r.json().get("error", {}).get("message", r.text[:100])
            except Exception:
                msg = r.text[:100]
            print(f"❌ HTTP {r.status_code}  {msg}")
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")

print()
print("=" * 62)
if ok:
    print("🎉 可用的模型：")
    for m in ok:
        print("     ", m)
    print()
    print(f"👉 把 config.py 里的 ZHIPU_MODEL 改成：\"{ok[0]}\"")
else:
    print("❌ 全部失败。可能原因：")
    print("   1. 密钥填错（注意引号里不要有空格或换行）")
    print("   2. 账号还没实名认证")
    print("   3. 模型名变了 → 去 https://bigmodel.cn/pricing 看免费模型叫什么")
print("=" * 62)

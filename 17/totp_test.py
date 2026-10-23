# 測試用：讀旁邊 .env 的 GITHUB_TOTP_SECRET，持續顯示目前的 6 位數驗證碼。
# 用法：python3 totp_test.py        （按 Ctrl+C 結束）
# 拿它跟手機驗證 App 上 GitHub 那一筆比對，兩邊要一模一樣。
import os
import sys
import time

import pyotp

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
secret = ""
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("GITHUB_TOTP_SECRET="):
                secret = line.split("=", 1)[1].strip().strip('"').strip("'")
secret = secret.replace(" ", "").upper()
if not secret:
    sys.exit("找不到 GITHUB_TOTP_SECRET，請確認旁邊有 .env（檔名就是 .env）")

totp = pyotp.TOTP(secret)
print("按 Ctrl+C 結束\n")
try:
    while True:
        left = 30 - int(time.time() % 30)
        print(f"\r驗證碼：{totp.now()}   （剩 {left:2d} 秒換下一組）", end="", flush=True)
        time.sleep(1)
except KeyboardInterrupt:
    print()

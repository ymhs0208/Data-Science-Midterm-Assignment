import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 讓 CSV 等輸出檔存在此資料夾

import csv
import time
import requests
from dotenv import load_dotenv  # 用來讀取 .env 檔的工具

# 把同資料夾裡 .env 的內容載入進來，這樣 API Key 就不用寫死在程式裡
load_dotenv()

url = "https://www.googleapis.com/books/v1/volumes"
filename = "pythonbook.csv"

# 從 .env 取出名叫 API_KEY 的那一行的值
api_key = os.getenv("API_KEY")
if not api_key:
    # 如果沒讀到，直接停下來並提醒，免得送出沒有金鑰的請求
    raise SystemExit("找不到 API_KEY，請確認 .env 裡有寫 API_KEY=你的金鑰")

with open(filename, mode="w", newline="", encoding="utf-8-sig") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["ID", "書名", "作者", "出版日期", "頁數"])

    for page in range(2):
        start_index = page * 10
        url_params = {
            "q": "Python",
            "maxResults": 10,
            "projection": "full",  # 改為 full 才能完整取得 pageCount (頁數)
            "startIndex": start_index,
            "key": api_key,
        }

        response = requests.get(url, params=url_params)

        if response.status_code == 200:
            data = response.json()
            items = data.get("items", [])

            for item in items:
                volume_info = item.get("volumeInfo", {})

                book_id = item.get("id", "")
                title = volume_info.get("title", "")
                authors = ", ".join(volume_info.get("authors", []))
                published_date = volume_info.get("publishedDate", "")
                # 若無頁數資料則預設填入 "未知" 或維持空字串
                page_count = volume_info.get("pageCount", "未知")

                writer.writerow(
                    [book_id, title, authors, published_date, page_count]
                )

            print(
                f"第 {page + 1} 頁寫入成功（startIndex={start_index}，共 {len(items)} 筆）"
            )
        else:
            print(f"第 {page + 1} 頁抓取失敗，HTTP 狀態碼: {response.status_code}")

        time.sleep(1)

print(f"\n資料已更新並存入 {filename}")

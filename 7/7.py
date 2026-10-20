import csv
import time
import requests

url = "https://www.googleapis.com/books/v1/volumes"
filename = "pythonbook.csv"
api_key = "填入api"

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

import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests


def scrape_atmovies_new():
    # 開眼電影網 本週新片網址
    url = "http://www.atmovies.com.tw/movie/new/"

    # 設定 Request Headers 模擬瀏覽器造訪，避免被伺服器阻擋
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        # 1. 發送 GET 請求取得網頁原始碼
        response = requests.get(url, headers=headers, timeout=10)
        # 確保編碼正確處理繁體中文字元 (開眼通常為 utf-8)
        response.encoding = "utf-8"

        # 檢查 HTTP 狀態碼是否正常 (200 OK)
        if response.status_code != 200:
            print(f"網頁請求失敗，狀態碼：{response.status_code}")
            return

        # 2. 使用 BeautifulSoup 與 html.parser 解析 HTML 內容
        soup = BeautifulSoup(response.text, "html.parser")

        # 3. 定位電影項目
        # 開眼新片列表中，每部電影的標題區塊通常包含在 class 為 'filmTitle' 的 div/header 內
        film_titles = soup.find_all("div", class_="filmTitle")

        if not film_titles:
            # 備用選擇器：若結構微調，嘗試抓取包含 /movie/ 連結的標題結構
            film_titles = soup.select(".filmListUL li, ul.filmList2 li")

        print(f"=== 開眼電影網 本週新片 (共抓取到 {len(film_titles)} 部) ===\n")

        for index, item in enumerate(film_titles, start=1):
            # 提取標題與電影詳細頁網址
            title_tag = item.find("a")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            relative_url = title_tag.get("href", "")
            # 使用 urljoin 自動將相對路徑轉換為完整網址
            full_url = urljoin(url, relative_url)

            # 提取電影簡介與片長：通常位於標題同層的父容器或相鄰兄弟節點中
            parent_container = item.parent
            container_text = parent_container.get_text(separator="\n")

            # 抓取片長 (透過正規表達式匹配「片長：XX分」)
            runtime_match = re.search(r"片長：\s*(\d+)\s*分", container_text)
            runtime = f"{runtime_match.group(1)} 分鐘" if runtime_match else "未標註片長"

            # 抓取簡介內容 (嘗試鎖定描述區塊 class 或抓取非標題的段落文字)
            desc_tag = parent_container.find(
                ["div", "p"], class_=lambda c: c and "desc" in c.lower()
            )
            if desc_tag:
                content = desc_tag.get_text(strip=True)
            else:
                # 若無特定 class，過濾掉標題與片長相關字樣取得乾淨簡介
                lines = [
                    line.strip()
                    for line in container_text.splitlines()
                    if line.strip()
                    and title not in line
                    and "片長" not in line
                    and "上映日期" not in line
                    and "上映廳數" not in line
                    and "評分" not in line
                ]
                content = lines[0] if lines else "暫無簡介"

            # 輸出每部電影的完整資訊
            print(f"[{index}] 電影名稱：{title}")
            print(f"    片長資訊：{runtime}")
            print(f"    電影網址：{full_url}")
            print(f"    劇情簡介：{content}")
            print("-" * 60)

    except requests.exceptions.RequestException as e:
        print(f"網路連線或請求發生錯誤：{e}")


if __name__ == "__main__":
    scrape_atmovies_new()
import os
import urllib3
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests

# 關閉因 verify=False 產生的 InsecureRequestWarning 警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def download_enterovirus_data():
    dataset_url = "https://data.gov.tw/dataset/14590"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    print(f"正在造訪資料集頁面：{dataset_url}")

    try:
        # 加入 verify=False 略過政府網站在 Python 環境下的 SSL 憑證驗證問題
        res = requests.get(
            dataset_url, headers=headers, timeout=15, verify=False
        )
        res.raise_for_status()

        soup = BeautifulSoup(res.text, "html.parser")
        csv_download_url = None

        # 尋找頁面中含有 CSV 的下載連結
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            text = a_tag.get_text(strip=True)
            if "CSV" in text or "csv" in href.lower() or "download" in href:
                csv_download_url = urljoin(dataset_url, href)
                break

        if not csv_download_url:
            print("頁面未直接解析到 CSV 標籤，啟用備用直接下載節點...")
            csv_download_url = (
                "https://od.cdc.gov.tw/eic/NHI_EnteroviralInfection.csv"
            )

        print(f"取得 CSV 下載網址：{csv_download_url}")

        # 下載檔案時同樣加上 verify=False
        file_res = requests.get(
            csv_download_url,
            headers=headers,
            stream=True,
            timeout=30,
            verify=False,
        )
        file_res.raise_for_status()

        # 寫入本地 CSV
        target_filename = "NHI_EnteroviralInfection.csv"
        with open(target_filename, "wb") as f:
            for chunk in file_res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        file_size_kb = os.path.getsize(target_filename) / 1024
        print(f"✅ 成功儲存至本地：{target_filename}")
        print(f"檔案大小約為：{file_size_kb:.2f} KB")

    except requests.exceptions.RequestException as e:
        print(f"下載或連線失敗：{e}")


if __name__ == "__main__":
    download_enterovirus_data()

if __name__ == "__main__":
    download_enterovirus_data()
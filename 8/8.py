import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 讓 CSV 等輸出檔存在此資料夾

import requests                 # 匯入 requests 套件，用於發送 HTTP 網路請求取得網頁內容
from bs4 import BeautifulSoup   # 匯入 BeautifulSoup 套件，用於解析 HTML 網頁原始碼
import csv                      # 匯入 csv 套件，用於將整理好的電影資料寫入 CSV 檔案
import re                       # 匯入 re (正規表達式) 套件，用於清理多餘空白與擷取上映日期

# 定義清理文字的輔助函式：把換行符號 (\n, \r, \t) 與多餘的連續空白全部壓成單一空白，避免 CSV 跑版
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# ==========================================
# 1. 設定目標網址與發送請求
# ==========================================
# 設定開眼電影網「本週新片 / 近期上映」的目標網址
url = "http://www.atmovies.com.tw/movie/new/"

# 設定網站主網域，用來幫待會抓到的相對路徑網址補齊開頭
base_domain = "http://www.atmovies.com.tw"

# 設定 HTTP 請求標頭 (User-Agent)，偽裝成一般使用者的 Chrome 瀏覽器
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# 發送 GET 請求取得網頁內容
response = requests.get(url, headers=headers)
# 開眼電影網使用 utf-8 編碼，明確指定以防止中文電影名稱變成亂碼
response.encoding = "utf-8"

# ==========================================
# 2. 解析 HTML 內容與擷取電影資料
# ==========================================
# 將網頁 HTML 原始碼交給 BeautifulSoup 進行解析
soup = BeautifulSoup(response.text, "html.parser")

# 建立一個空串列，用來存放所有抓取並整理好的電影資料
movie_list = []

# 開眼電影網的每部新片區塊通常包在 <article class="filmListAll"> 或 <div class="filmTitle"> 中
# 我們直接尋找所有 class 為 "filmTitle" 的區塊（每個區塊代表一部電影的標題連結）
title_blocks = soup.select(".filmTitle")

# 使用迴圈逐一處理每一部電影
for title_block in title_blocks:
    # --- (1) 抓取「電影名稱」與「連結網址」 ---
    # 在 filmTitle 區塊中尋找 <a> 超連結標籤
    a_tag = title_block.find("a")
    if not a_tag:
        continue  # 若找不到超連結則跳過該筆
        
    # 取得電影名稱，並使用 clean_text() 清除多餘空白與換行
    movie_name = clean_text(a_tag.text)
    
    # 取得 <a> 標籤中的 href 屬性 (例如：/movie/fAen12345678/)
    raw_link = a_tag.get("href", "").strip()
    # 如果網址是相對路徑 (以 "/" 開頭)，則在前面補上主網域 base_domain，變成完整可點擊的網址
    if raw_link.startswith("/"):
        movie_link = base_domain + raw_link
    else:
        movie_link = raw_link

    # --- (2) 抓取「上映時間」 ---
    # 往上一層 (parent) 找到整部電影的完整資訊區塊，以便尋找裡面的上映日期
    movie_container = title_block.parent
    
    # 預設上映時間為「未提供」
    release_date = "未提供"
    
    # 開眼電影網的上映日期通常放在 class="runtime" 的區塊內，文字格式如：「上映日期：2024/05/15」
    if movie_container:
        # 使用正規表達式在該部電影的區塊文字中搜尋「上映日期：YYYY/MM/DD」或類似格式
        date_match = re.search(r'上映日期[：:]\s*([0-9/\-]+)', movie_container.text)
        if date_match:
            # 取出配對到的純日期部分 (例如 2024/05/15)，讓 CSV 欄位更乾淨整齊
            release_date = date_match.group(1).strip()
        else:
            # 備用方案：若格式不同，尋找包含「上映日期」字樣的 <li> 或 <div> 標籤
            runtime_tag = movie_container.select_one(".runtime")
            if runtime_tag:
                release_date = clean_text(runtime_tag.text)

    # 將整理好的「電影名稱、上映時間、連結網址」打包成串列，加入總清單 movie_list 中
    movie_list.append([movie_name, release_date, movie_link])
    
    # 同時在終端機印出抓到的內容，滿足題目「列出...」的要求並方便即時檢查
    print(f"電影：{movie_name} | 上映時間：{release_date} | 網址：{movie_link}")

# ==========================================
# 3. 將資料整齊儲存至 movies.csv
# ==========================================
# 開啟 (或建立) movies.csv 檔案：
# mode="w" 代表寫入模式
# newline="" 防止 Windows 在寫入 CSV 時每行之間多出空白行
# encoding="utf-8-sig" 加入 BOM 標記，確保用 Excel 直接雙擊打開時繁體中文不會亂碼
with open("movies.csv", mode="w", newline="", encoding="utf-8-sig") as file:
    # 建立 CSV 寫入器，設定 quoting=csv.QUOTE_ALL 強制幫每個欄位加上雙引號，防止特殊符號導致欄位錯位
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    
    # 寫入第一列：依照題目要求的欄位標題順序
    writer.writerow(["電影名稱", "上映時間", "連結網址"])
    
    # 將 movie_list 中所有的電影資料一次寫入檔案
    writer.writerows(movie_list)

# 印出完成提示訊息
print(f"\n成功抓取共 {len(movie_list)} 部近期上映強片，並已整齊儲存至 movies.csv！")
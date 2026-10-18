import requests                 # 匯入 requests 套件，用來發送 HTTP 網路請求取得網頁內容
from bs4 import BeautifulSoup   # 匯入 BeautifulSoup 套件，用來解析 HTML 網頁原始碼
import csv                      # 匯入 csv 套件，用來將整理好的資料寫入 CSV 檔案
import re                       # 匯入 re (正規表達式) 套件，用來清理雜亂文字與精簡博客來網址

# 定義一個清理文字的輔助函式：把換行符號 (\n, \r, \t) 與多餘的連續空白全部替換成單一空白，避免 CSV 跑版
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# ==========================================
# 1. 設定目標網址與發送請求
# ==========================================
# 設定博客來搜尋關鍵字為「演算法」的目標網址
url = "https://search.books.com.tw/search/query/key/演算法/cat/all"

# 設定 HTTP 標頭 (User-Agent)，偽裝成一般使用者的 Chrome 瀏覽器，避免被博客來伺服器阻擋
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 發送 GET 請求到目標網址，並帶入偽裝標頭
response = requests.get(url, headers=headers)
# 指定回應內容的編碼為 utf-8，確保中文字不會變成亂碼
response.encoding = "utf-8"

# ==========================================
# 2. 解析 HTML 內容與清理資料
# ==========================================
# 將取得的 HTML 原始碼交給 BeautifulSoup，使用內建的 html.parser 解析器
soup = BeautifulSoup(response.text, "html.parser")

# 選取所有書籍項目的區塊 (博客來搜尋結果每一本書通常包在 class="table-td" 的 div 中)
books = soup.select("div.table-td")
# 如果沒抓到任何東西 (代表網頁可能改版或為不同版型)，改用備用的選擇器 tbody tr
if not books:
    books = soup.select("tbody tr")

# 建立一個空串列，用來儲存所有整理乾淨的書籍資料
book_list = []

# 使用迴圈逐一處理每一個書籍區塊
for book in books:
    # --- (1) 抓取並整理「書名」與「網址」 ---
    # 在當前書籍區塊中，尋找 h4 標籤底下的 a (超連結) 標籤
    title_tag = book.select_one("h4 a")
    # 如果這個區塊裡面沒有書名連結 (可能是空白格或廣告)，就跳過換下一筆
    if not title_tag:
        continue
    
    # 取得書名文字，並呼叫 clean_text() 清除可能造成 CSV 斷行的換行符號與多餘空白
    title = clean_text(title_tag.text)
    
    # 取得 a 標籤中的 href (網址連結) 屬性，若無則預設為空字串
    raw_link = title_tag.get("href", "").strip()
    # 如果網址是以 "//" 開頭的相對協定網址，在前面補上 "https:"
    if raw_link.startswith("//"):
        raw_link = "https:" + raw_link
        
    # 【整理重點】博客來搜尋結果原本的跳轉網址非常長又亂 (含有一堆追蹤碼)
    # 這裡用正規表達式抓出網址中 "/item/商品編號/" 的部分，轉換成乾淨的官方短網址！
    match = re.search(r'/item/([A-Za-z0-9]+)/', raw_link)
    if match:
        # 轉成乾淨的短網址，例如：https://www.books.com.tw/products/0010987654
        link = f"https://www.books.com.tw/products/{match.group(1)}"
    else:
        # 若網址結構特殊沒配對到，則保留補齊 https 後的原網址
        link = raw_link

    # --- (2) 抓取並整理「作者」 ---
    # 尋找 p.author 底下的所有 a 標籤 (因為一本書可能有多位作者或譯者)
    author_tags = book.select("p.author a")
    if author_tags:
        # 將每位作者的名字清理乾淨後，改用中文頓號「、」串接起來
        # (避免使用半形逗號 "," 減少與 CSV 分隔符號混淆的視覺雜亂感)
        authors = "、".join([clean_text(a.text) for a in author_tags if clean_text(a.text)])
    else:
        # 若沒有作者標籤，填入預設文字
        authors = "無作者資訊"

    # --- (3) 抓取並整理「書價」 ---
    # 博客來的價格在 ul.price 的 li 裡面，通常寫「79 折 450 元」，其中數字都包在 <b> 標籤內
    price_tags = book.select("ul.price li b")
    if price_tags:
        # 取出最後一個 <b> 標籤的文字 (即實際售價數字)，並改成純數字或加上「元」
        price = clean_text(price_tags[-1].text) + " 元"
    else:
        price = "無價格資訊"

    # 將整理乾淨的「書名、網址、作者、書價」打包成一個小串列，放進總清單 book_list 中
    book_list.append([title, link, authors, price])

# ==========================================
# 3. 將資料整齊存入 booklist.csv
# ==========================================
# 開啟 (或建立) booklist.csv 檔案：
# mode="w" 代表寫入模式
# newline="" 可以防止 Windows 系統在寫入 CSV 時每行之間多出一行空白列
# encoding="utf-8-sig" 會在檔案開頭加入 BOM 標記，讓 Excel 打開時能正確識別繁體中文不亂碼
with open("booklist.csv", mode="w", newline="", encoding="utf-8-sig") as file:
    # 建立 CSV 寫入器，並設定 quoting=csv.QUOTE_ALL (強制幫每個欄位加上雙引號保護，徹底防止書名含逗號或特殊符號導致欄位錯位)
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    
    # 寫入第一列：CSV 的欄位標題
    writer.writerow(["書名", "網址", "作者", "書價"])
    
    # 將 book_list 中所有的書籍資料一次寫入檔案
    writer.writerows(book_list)

# 在終端機印出完成訊息與成功抓取的筆數
print(f"成功抓取 {len(book_list)} 筆書籍資料，並已整齊存入 booklist.csv！")
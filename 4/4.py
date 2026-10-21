from playwright.sync_api import sync_playwright  # 匯入 Playwright 同步 API，用來啟動真實瀏覽器繞過防爬蟲與等待動態載入
from bs4 import BeautifulSoup                    # 匯入 BeautifulSoup 套件，用來解析 HTML 網頁原始碼
import csv                                       # 匯入 csv 套件，用來將整理好的資料寫入 CSV 檔案
import re                                        # 匯入 re (正規表達式) 套件，用來清理雜亂文字與精簡博客來網址

# 定義一個清理文字的輔助函式：把換行符號 (\n, \r, \t) 與多餘的連續空白全部替換成單一空白，避免 CSV 跑版
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

# 設定博客來搜尋關鍵字為「演算法」的目標網址
url = "https://search.books.com.tw/search/query/key/演算法/cat/all"

# ==========================================
# 1. 使用 Playwright 開啟瀏覽器取得渲染後的 HTML
# ==========================================
# 使用 with 語句啟動 Playwright 控制器，確保區塊結束後自動釋放系統資源
with sync_playwright() as p:
    # 啟動 Chromium (Chrome 核心) 瀏覽器
    # headless=False 代表「顯示瀏覽器視窗」，這樣最像真人操作，最不容易被 Cloudflare 防火牆阻擋
    # (若確認環境穩定想在背景隱藏執行，可將 False 改為 True)
    browser = p.chromium.launch(headless=False)
    
    # 建立一個全新的瀏覽器獨立環境 (Context)，並設定 User-Agent 偽裝成一般的 Windows Chrome 瀏覽器
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    
    # 在瀏覽器中開啟一個新的分頁 (相當於按新分頁按鈕)
    page = context.new_page()
    
    print("正在開啟網頁並等待資料載入...")
    # 在新分頁中前往目標網址 (同時間瀏覽器會自動執行網頁內的 JavaScript)
    page.goto(url)
    
    # 【關鍵步驟】等待網頁上的書籍區塊 (div.table-td 或 tbody tr) 實際被 JavaScript 載入並顯示出來
    # timeout=15000 代表最多等待 15000 毫秒 (15 秒)
    try:
        page.wait_for_selector("div.table-td, tbody tr", timeout=15000)
    except Exception:
        # 如果超過 15 秒還沒出現，印出提示訊息 (通常代表網路太慢、跳出真人勾選驗證，或網頁改版)
        print("等待逾時，可能遇到真人驗證或選擇器已變更。")
        
    # 取得已經由瀏覽器執行完 JavaScript、包含完整書籍資料的最終 HTML 原始碼
    html_content = page.content()
    
    # 抓取完原始碼後，關閉瀏覽器視窗
    browser.close()

# ==========================================
# 2. 解析 HTML 內容與清理資料
# ==========================================
# 將從瀏覽器取得的完整 HTML 原始碼交給 BeautifulSoup，使用內建的 html.parser 解析器
soup = BeautifulSoup(html_content, "html.parser")

# 選取所有書籍項目的區塊 (博客來搜尋結果每一本書通常包在 class="table-td" 的 div 中)
books = soup.select("div.table-td")
# 如果沒抓到任何東西 (代表網頁可能為表格版型)，改用備用的選擇器 tbody tr
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
    
    # 取得 a 標籤中的 href (網址連結) 屬性，若無則預設為空字串並去除前後空白
    raw_link = title_tag.get("href", "").strip()
    # 如果網址是以 "//" 開頭的相對協定網址，在前面補上 "https:" 變成完整網址
    if raw_link.startswith("//"):
        raw_link = "https:" + raw_link
        
    # 【整理重點】博客來搜尋結果原本的跳轉網址非常長又亂 (含有一堆追蹤碼)
    # 這裡用正規表達式抓出網址中 "/item/商品編號/" 的部分，轉換成乾淨的官方短網址！
    match = re.search(r'/item/([A-Za-z0-9]+)/', raw_link)
    if match:
        # match.group(1) 就是括號內抓到的商品編號，轉成乾淨的短網址，例如：https://www.books.com.tw/products/0010987654
        link = f"https://www.books.com.tw/products/{match.group(1)}"
    else:
        # 若網址結構特殊沒配對到，則保留補齊 https 後的原網址
        link = raw_link

    # --- (2) 抓取並整理「作者」 ---
    # 尋找 p.author 底下的所有 a 標籤 (因為一本書可能有多位作者、譯者或繪者)
    author_tags = book.select("p.author a")
    if author_tags:
        # 使用串列生成式將每位作者的名字清理乾淨，過濾掉空字串後，改用中文頓號「、」串接起來
        # (避免使用半形逗號 "," 減少與 CSV 分隔符號混淆的視覺雜亂感)
        authors = "、".join([clean_text(a.text) for a in author_tags if clean_text(a.text)])
    else:
        # 若沒有作者標籤，填入預設文字
        authors = "無作者資訊"

    # --- (3) 抓取並整理「書價」 ---
    # 博客來的價格在 ul.price 的 li 裡面，通常寫「79 折 450 元」，其中數字都包在 <b> 標籤內
    price_tags = book.select("ul.price li b")
    if price_tags:
        # 取出最後一個 [-1] 的 <b> 標籤文字 (即實際售價數字)，清理乾淨後在後方加上「 元」
        price = clean_text(price_tags[-1].text) + " 元"
    else:
        # 若沒有價格標籤，填入預設文字
        price = "無價格資訊"

    # 將整理乾淨的「書名、網址、作者、書價」打包成一個小串列，放進總清單 book_list 中
    book_list.append([title, link, authors, price])

# ==========================================
# 3. 將資料整齊存入 booklist.csv
# ==========================================
# 開啟 (或建立) booklist.csv 檔案：
# mode="w" 代表寫入模式 (若檔案已存在會覆蓋重寫)
# newline="" 可以防止 Windows 系統在寫入 CSV 時每行之間多出一行空白列
# encoding="utf-8-sig" 會在檔案開頭加入 BOM 標記，讓 Excel 點兩下打開時能正確識別繁體中文不亂碼
with open("booklist.csv", mode="w", newline="", encoding="utf-8-sig") as file:
    # 建立 CSV 寫入器，並設定 quoting=csv.QUOTE_ALL (強制幫每個欄位加上雙引號保護，徹底防止書名含逗號或特殊符號導致欄位錯位)
    writer = csv.writer(file, quoting=csv.QUOTE_ALL)
    
    # 寫入第一列：CSV 的欄位標題
    writer.writerow(["書名", "網址", "作者", "書價"])
    
    # 將 book_list 中所有的書籍資料一次寫入檔案
    writer.writerows(book_list)

# 在終端機印出完成訊息與成功抓取的筆數
print(f"成功抓取 {len(book_list)} 筆書籍資料，並已整齊存入 booklist.csv！")

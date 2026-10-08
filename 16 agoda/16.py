# ============================================================
# 第 16 題：爬 Agoda「台中」的飯店名稱與價格，存成 CSV
#
# 整體流程（白話版）：
#   1. 用程式打開一個 Chrome 瀏覽器（Selenium 就是幫我們「遙控瀏覽器」的工具）
#   2. 到 Agoda 首頁，在搜尋框輸入「台中」，按搜尋
#   3. 進到結果頁後，一邊慢慢往下捲、一邊把看到的飯店記下來
#   4. 捲到沒有新飯店了，就把記下來的資料寫進 agoda_result.csv
# ============================================================

import csv    # 用來把資料寫成 .csv 表格檔（Excel 可以直接開）
import time   # 用來讓程式「暫停幾秒」，等網頁載入
from datetime import date, timedelta  # 用來算「明天」的日期

# 下面這幾個都是 Selenium 的工具，各自的用途：
from selenium import webdriver                       # 遙控瀏覽器的主角
from selenium.webdriver import ActionChains          # 模擬「按鍵盤/滑鼠」的連續動作
from selenium.webdriver.common.by import By          # 告訴 Selenium「用什麼方式找網頁上的東西」
from selenium.webdriver.common.keys import Keys      # 代表鍵盤上的按鍵（Enter、ESC、方向鍵…）
from selenium.webdriver.support import expected_conditions as EC  # 「等到某件事發生」的條件
from selenium.webdriver.support.ui import WebDriverWait           # 「最多等多久」的計時器

# ---------------- 可以自己調整的設定 ----------------
URL = "https://www.agoda.com/zh-tw/"   # Agoda 繁體中文首頁
KEYWORD = "台中"                        # 要搜尋的地點，想爬別的城市改這裡
OUTPUT = "agoda_result.csv"            # 結果要存成的檔名

# 入住日自動設成「明天」。
# 如果寫死成某個日期，過了那天網頁就會說「日期已過」或查不到價格，
# 所以每次執行都用今天算出明天，隨時跑都能用。
# .isoformat() 會把日期變成 "2026-10-09" 這種格式，剛好是網址要的格式。
CHECK_IN = (date.today() + timedelta(days=1)).isoformat()

# 備用網址：有時候 Agoda 發現我們是用程式在操作，首頁的搜尋鈕按了不會跳到結果頁。
# 這時就直接用「已經搜尋好台中」的結果頁網址，等於幫它手動搜尋完。
#   city=12080  → 台中市在 Agoda 的代號
#   checkIn     → 入住日期
#   los=1       → 住 1 晚（length of stay）
#   rooms=1     → 1 間房
#   adults=2    → 2 位大人
FALLBACK_URL = f"https://www.agoda.com/zh-tw/search?city=12080&checkIn={CHECK_IN}&los=1&rooms=1&adults=2"


def search_city(driver, wait):
    """在首頁的搜尋框輸入「台中」，選好地點，然後按下搜尋鈕。
    （就是把人類會做的那幾個動作，一步一步用程式做一遍）"""

    # 等到搜尋框「出現而且可以點」才繼續，不然網頁還沒載完就去點會報錯。
    # 這裡寫兩個選擇器用逗號隔開，意思是「找到其中任何一個就行」，
    # 因為 Agoda 不同版本的搜尋框標記不太一樣。
    box = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "input[data-selenium='textInput'], input#textInput")))
    box.click()                # 先點一下搜尋框，讓游標進去
    box.clear()                # 清掉裡面可能預設的文字（例如上次搜尋的城市）
    box.send_keys(KEYWORD)     # 打字：輸入「台中」

    # 打完字後，Agoda 需要一點時間去查，才會跳出下方的地點建議清單。
    # 所以先等 2 秒，等清單出來。
    time.sleep(2)
    box.send_keys(Keys.ARROW_DOWN)  # 按鍵盤「↓」，選到建議清單的第一個（台中市）
    box.send_keys(Keys.ENTER)       # 按 Enter 確定選擇
    time.sleep(1)

    # 選完地點後，網頁會自動彈出日曆讓你選日期，而日曆會蓋住下面的搜尋鈕。
    # 我們不用選日期（用預設的就好），所以按 ESC 把日曆關掉。
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    time.sleep(1)

    # 等搜尋鈕可以點，然後點下去。
    search_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button[data-element-name='search-button']")))
    # 這裡不用一般的 search_btn.click()，而是叫瀏覽器直接執行一段 JavaScript 去點。
    # 原因：一般點擊如果按鈕上面蓋了彈出視窗，會點不到而報錯；
    # 用 JavaScript 點就算被蓋住也能點到。
    driver.execute_script("arguments[0].click();", search_btn)


def parse_visible(driver, seen):
    """把「現在網頁上已經載入的飯店」讀出來，記到 seen 這個字典裡。

    seen 長這樣：{ 飯店編號: (飯店名, 價格), ... }
    用字典的好處：同一間飯店重複讀到，只會記一次，不會變兩筆。

    為什麼用「飯店編號」而不是「飯店名」當依據？
    因為真的有不同的飯店取一樣的名字（例如連鎖飯店的不同分店）。
    如果用名字判斷，第二間會被誤認成「讀過了」而漏掉。
    每間飯店在網頁裡都有獨一無二的編號 data-hotelid，用它最準。

    回傳值：這一輪「新增」了幾間（捲動時用來判斷還有沒有新東西）。"""
    before = len(seen)  # 先記住讀之前有幾間，最後相減就知道新增幾間

    # 每間飯店在網頁上是一張「卡片」，找出目前所有的卡片
    cards = driver.find_elements(By.CSS_SELECTOR, "li[data-selenium='hotel-item']")
    for card in cards:
        hotel_id = card.get_attribute("data-hotelid")  # 讀這張卡片的飯店編號
        # 沒有編號（不是正常的飯店卡片），或已經記過了 → 跳過這張
        if not hotel_id or hotel_id in seen:
            continue

        # 讀飯店名稱。如果卡片還在載入、名字還沒出現，會找不到而報錯，
        # 這時不要硬記，直接跳過；等下一輪捲動時它載入好了，就會被讀到。
        try:
            name = card.find_element(By.CSS_SELECTOR, "[data-selenium='hotel-name']").text.strip()
        except Exception:
            continue
        if not name:   # 名字是空的也代表還沒載入好
            continue

        # 讀價格。有些飯店可能已滿房或沒報價，找不到價格就標「無價格」，
        # 這樣這間飯店還是會留在結果裡，不會整間消失。
        try:
            price = card.find_element(By.CSS_SELECTOR, "[data-selenium='display-price']").text.strip()
        except Exception:
            price = "無價格"

        seen[hotel_id] = (name, price)  # 記下來

    return len(seen) - before


def scrape_all(driver, max_idle=8, max_rounds=300):
    """一邊往下捲、一邊記錄飯店，直到沒有新飯店為止。回傳 [(飯店名, 價格), ...]

    參數：
      max_idle   連續幾輪都沒有新飯店，就當作到底了、可以停（預設 8 輪）。
                 不設 1 輪就停，是因為網頁偶爾會卡一下才載入下一批，太快放棄會漏。
      max_rounds 最多捲幾輪，只是保險，避免網頁出問題時程式永遠停不下來。

    這個頁面的特性（我們實際測試出來的，台中大約 98 間）：
    1. 網頁是「捲到哪裡，才把那裡的飯店內容填進去」。每往下捲一屏，只會多出約 2 間。
       所以一定要「慢慢捲」；如果一次直接跳到最底，中間的飯店卡片會是空的、沒內容。
    2. 飯店資料不會因為捲過去就消失，所以「全部捲完再一次讀」和「邊捲邊讀」都抓得到。
       這裡選邊捲邊讀，好處是中途就算出錯或被中斷，已經讀到的不會白費。
    3. 頁面最底下有「下一頁」和「查看更多民宿」按鈕，絕對不能按。
       按了就會離開這頁的飯店清單（之前資料抓不齊，就是因為誤按了它們）。"""
    seen = {}   # 已經記下來的飯店
    idle = 0    # 目前已經「連續幾輪沒有新飯店」

    for _ in range(max_rounds):
        new = parse_visible(driver, seen)  # 讀目前畫面上有的飯店
        print(f"目前累計 {len(seen)} 間（本輪新增 {new}）")  # 印出進度，方便看程式有沒有在動

        if new:
            idle = 0                # 這輪有新飯店 → 重新計算「沒新東西」的次數
        else:
            idle += 1               # 這輪沒新飯店 → 閒置次數 +1
            if idle >= max_idle:    # 連續太多輪都沒有 → 應該是全部讀完了，跳出迴圈
                break

        # 往下捲「0.8 個螢幕高度」。故意不捲滿一屏，這樣上一次捲到的內容
        # 和這次會有一點重疊，不會有卡片剛好被跳過。
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
        time.sleep(1.5)  # 給網頁 1.5 秒把新捲到的飯店內容填進去，再進下一輪

    return list(seen.values())  # 只拿 (飯店名, 價格) 的部分，編號不需要寫進檔案


def main():
    """主程式：把上面的步驟串起來。"""

    # ---- 準備瀏覽器 ----
    # 網站可以偵測「這個瀏覽器是不是被程式遙控的」，偵測到可能就擋你。
    # 下面兩行設定是把這些「被遙控」的記號藏起來，降低被擋的機率。
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)  # 打開 Chrome（新版 Selenium 會自動下載需要的驅動程式）
    driver.maximize_window()                    # 視窗最大化，一屏看到的飯店比較多

    # try ... finally 的意思：不管中間有沒有出錯，最後 finally 裡的事一定會做。
    try:
        driver.get(URL)  # 前往 Agoda 首頁
        # 建立一個「最多等 20 秒」的計時器。之後用 wait.until(...) 等網頁元素出現，
        # 網頁慢的時候不會太早放棄，真的 20 秒都沒出現才報錯。
        wait = WebDriverWait(driver, 20)
        search_city(driver, wait)  # 輸入台中、按搜尋

        # 按完搜尋後等 3 秒。Agoda 有時會把結果開在「新分頁」，
        # 如果開了新分頁（分頁數大於 1），就要把程式的操作對象切到最新那一個，
        # 不然程式還停在舊分頁，什麼都抓不到。
        time.sleep(3)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        # 檢查現在的網址有沒有 "/search"（結果頁的網址都有）。
        # 沒有的話代表搜尋鈕沒真的跳轉，就改用前面準備的備用網址直接進結果頁。
        if "/search" not in driver.current_url:
            print("搜尋鈕未跳轉，改用搜尋結果網址")
            driver.get(FALLBACK_URL)

        # 等到至少有一間飯店的名字出現在網頁上，才代表結果真的載入了，可以開始爬。
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-selenium='hotel-name']")))

        rows = scrape_all(driver)  # 開始邊捲邊記錄，拿回所有飯店
    finally:
        # 中途出錯也一定要把瀏覽器關掉，不然會留下一堆沒關的 Chrome 視窗。
        driver.quit()

    # ---- 寫入 CSV 檔 ----
    # "w"             → 寫入模式（舊檔案會被新的蓋掉）
    # newline=""      → 避免 Windows 上每一行中間多出一個空白行
    # utf-8-sig       → 在檔案開頭加一個小標記，Excel 才會知道這是 UTF-8，
    #                   不然直接雙擊開檔，中文會變成亂碼
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["飯店名", "價格"])  # 第一列：欄位標題
        writer.writerows(rows)              # 後面每一列：一間飯店
    print(f"已儲存 {len(rows)} 筆資料至 {OUTPUT}")


# 只有「直接執行這個檔案」時才會跑 main()；
# 如果是被別的程式 import 進去用，就不會自動開始爬。
if __name__ == "__main__":
    main()

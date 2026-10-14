# ============================================================
# PTT 八卦版 (Gossiping) 爬蟲：抓文章列表的「網址、標題、作者」存成 CSV
#
# 為什麼需要處理 cookie？
#   八卦版有「18 歲分級」限制，第一次進去會先跳出「你是否已滿 18 歲」的頁面，
#   要按「我已滿18歲」才進得去。
#   PTT 判斷你有沒有按過，是看瀏覽器裡有沒有一張叫 over18、值為 1 的 cookie。
#
#   cookie = 網站發給瀏覽器的「通行證」，瀏覽器之後每次開網頁都出示它，
#            網站就知道你是誰、做過什麼，不用再問一次。
#
# 這支程式有「兩層」方法通過 18 歲分級（第 2、3 步）：
#   方法一：用 Selenium 找到「我已滿18歲」按鈕，自己點下去（跟人一樣操作）
#   方法二：如果按鈕點不到，就直接把 over18=1 這張 cookie「塞」進瀏覽器，
#           PTT 看到通行證就以為你按過了，不會再擋。
#
# 流程：開八卦版 → 通過 18 歲分級 → 等文章列表 → 抓資料 → 印出 → 存 CSV
# ============================================================

from selenium import webdriver
from selenium.webdriver.common.by import By                       # 指定用什麼方式找網頁上的東西
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait           # 「最多等多久」的計時器
from selenium.webdriver.support import expected_conditions as EC  # 「等到某件事發生」的條件
from selenium.common.exceptions import TimeoutException           # 「等太久還是沒出現」的錯誤
import csv    # 把資料寫成 CSV 檔
import time   # 讓程式暫停幾秒


# ============================================================
# 基本設定
# ============================================================

# 要爬的網址：八卦版的最新一頁
URL = "https://www.ptt.cc/bbs/Gossiping/index.html"

print("=" * 60)
print("PTT Gossiping 爬蟲")
print("=" * 60)


# ============================================================
# 建立 Chrome WebDriver
# ============================================================

options = Options()

# 如果不想看到 Chrome 視窗，可以取消下面這行的註解（headless = 在背景偷偷跑，不開視窗）
# options.add_argument("--headless=new")

options.add_argument("--window-size=1400,900")   # 視窗大小，太小的話有些內容不會顯示
# 把「瀏覽器正受自動程式控制」這個特徵藏起來，網站比較不會把我們當成機器人擋掉
options.add_argument("--disable-blink-features=AutomationControlled")

# Selenium 4.6+ 通常會自動處理 ChromeDriver
driver = webdriver.Chrome(options=options)

# 之後用 wait.until(...) 最多等 15 秒，網頁慢也不會太早放棄
wait = WebDriverWait(driver, 15)


try:

    # ========================================================
    # 1. 開啟 PTT 八卦版
    # ========================================================

    print("開啟 PTT Gossiping...")
    driver.get(URL)   # 打開網址。第一次來的話，PTT 會把我們導到 18 歲分級頁

    time.sleep(2)     # 等 2 秒，讓頁面跳轉和載入完成

    print("目前網址：")
    print(driver.current_url)

    print()


    # ========================================================
    # 2. 處理 18 歲分級問題（方法一：點按鈕）
    # ========================================================

    # 怎麼知道被擋住了？看網址：被擋時網址會變成 .../ask/over18?from=...
    if "over18" in driver.current_url or "ask/over18" in driver.current_url:

        print("偵測到 18 歲分級頁面")
        print("準備確認已滿 18 歲...")

        try:
            # 等「我已滿18歲」按鈕出現而且可以點，最多等 15 秒。
            # 下面三種寫法是用逗號並列的「找法」，只要有一種找得到就算數。
            button = wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button.btn-big, "
                        "input[value*='滿18'], "
                        "a.btn-big"
                    )
                )
            )

            print("找到 18 歲確認按鈕")
            button.click()   # 點下去，PTT 就會發給瀏覽器 over18=1 的 cookie

        except TimeoutException:

            # 上面的找法等了 15 秒都找不到（PTT 可能改了按鈕的寫法），
            # 改用「按鈕上的文字」去找：任何文字含「我已滿18歲」「滿18歲」「進入」的元素
            print("使用備用方式尋找 18 歲確認按鈕...")

            elements = driver.find_elements(
                By.XPATH,
                "//*[contains(text(),'我已滿18歲') "
                "or contains(text(),'滿18歲') "
                "or contains(text(),'進入')]"
            )

            clicked = False

            for element in elements:

                try:

                    if element.is_displayed():   # 只點「看得到」的，隱藏的點了會出錯
                        print("找到按鈕：", element.text)
                        element.click()
                        clicked = True
                        break

                except Exception:
                    pass

            if not clicked:
                print("找不到 18 歲按鈕。")
                print("請檢查目前頁面：")
                print(driver.current_url)

        time.sleep(3)   # 點完等 3 秒，讓頁面跳轉到八卦版


    # ========================================================
    # 3. 如果仍然在分級頁，使用 cookie（方法二：直接塞通行證）
    # ========================================================

    # 再檢查一次網址：如果點按鈕之後還是停在分級頁，代表方法一失敗，改用塞 cookie。

    if "over18" in driver.current_url or "ask/over18" in driver.current_url:

        print("按鈕處理失敗，設定 over18 cookie...")

        try:
            # add_cookie = 把一張 cookie 塞進瀏覽器。
            # 注意：瀏覽器規定只能幫「目前所在的網站」加 cookie，
            # 這時候我們已經停在 ptt.cc 的頁面上（分級頁），所以可以加。
            driver.add_cookie({
                "name": "over18",     # cookie 的名字：PTT 就是看這個名字
                "value": "1",         # cookie 的內容：1 = 已滿 18 歲
                "domain": ".ptt.cc",  # 這張 cookie 屬於哪個網站（前面的點代表 ptt.cc 底下所有網址都適用）
                "path": "/"           # 整個網站都適用
            })

            print("已設定 over18=1")

            # 塞完 cookie 要「重新載入」八卦版，PTT 這次才會看到通行證、放我們進去
            driver.get(URL)

            time.sleep(3)

        except Exception as e:
            print("Cookie 設定失敗：", e)


    # ========================================================
    # 4. 確認已經進入 Gossiping
    # ========================================================

    # 印出網址確認：成功的話會是 .../bbs/Gossiping/index.html，不再有 over18

    print()
    print("目前網址：")
    print(driver.current_url)

    print()


    # ========================================================
    # 5. 列出網站 Title（瀏覽器分頁上顯示的標題）
    # ========================================================

    print("=" * 60)
    print("網站 Title")
    print("=" * 60)

    print(driver.title)

    print()


    # ========================================================
    # 6. 等待文章列表
    # ========================================================

    # PTT 每一列文章都包在 <div class="r-ent"> 裡，所以等它出現，就代表列表載入好了
    try:

        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.r-ent")
            )
        )

    except TimeoutException:

        print("等待文章列表逾時。")
        print("目前網址：", driver.current_url)

        # 印出部分網頁內容方便除錯（看看是不是還停在分級頁，或被擋了）
        print(driver.page_source[:2000])

        raise SystemExit   # 沒有文章可抓，直接結束程式


    # ========================================================
    # 7. 找出所有文章
    # ========================================================

    # find_elements（有 s）會把「所有」符合的 r-ent 找出來，回傳一個清單

    articles = driver.find_elements(
        By.CSS_SELECTOR,
        "div.r-ent"
    )

    print("=" * 60)
    print("文章列表")
    print("=" * 60)

    print("共找到：", len(articles), "筆")
    print()


    data = []   # 準備一個空清單，抓到的每一篇文章之後都放進來


    # ========================================================
    # 8. 逐筆抓取
    # ========================================================

    # 一篇一篇處理。外面包 try，這樣某一篇出錯也不會讓整個程式停掉
    for article in articles:

        try:

            # ------------------------------------------------
            # 標題
            # ------------------------------------------------

            title_element = article.find_element(
                By.CSS_SELECTOR,
                "div.title"
            )

            title = title_element.text.strip()   # strip() 去掉前後多餘的空白、換行


            # ------------------------------------------------
            # 如果文章已被刪除
            # ------------------------------------------------

            # continue = 跳過這一篇，直接處理下一篇
            if not title:
                continue

            if title == "(本文已被刪除)":
                continue


            # ------------------------------------------------
            # 文章網址
            # ------------------------------------------------

            try:

                link_element = article.find_element(
                    By.CSS_SELECTOR,
                    "div.title a"
                )

                href = link_element.get_attribute("href")   # 取得連結的網址

            except Exception:

                continue


            # ------------------------------------------------
            # 作者
            # ------------------------------------------------

            try:

                author_element = article.find_element(
                    By.CSS_SELECTOR,
                    "div.meta .author"
                )

                author = author_element.text.strip()

            except Exception:

                author = "N/A"


            # ------------------------------------------------
            # 轉成 PTT 相對網址（把開頭的 https://www.ptt.cc 拿掉，只留 /bbs/... 這一段）
            # ------------------------------------------------

            if href.startswith("https://www.ptt.cc"):
                href = href.replace(
                    "https://www.ptt.cc",
                    ""
                )

            elif href.startswith("http://www.ptt.cc"):
                href = href.replace(
                    "http://www.ptt.cc",
                    ""
                )


            # ------------------------------------------------
            # 存資料
            # ------------------------------------------------

            # 一篇文章用一個「字典」存：名字 → 內容
            item = {
                "網址": href,
                "標題": title,
                "作者": author
            }

            data.append(item)


        except Exception as e:

            print("某篇文章抓取失敗：", e)
            continue


    # ========================================================
    # 9. 印出結果（enumerate 的 1 是讓編號從 1 開始，不是從 0）
    # ========================================================

    print()

    for i, item in enumerate(data, 1):

        print("-" * 60)

        print(f"第 {i} 筆")

        print("網址：")
        print(item["網址"])

        print("標題：")
        print(item["標題"])

        print("作者：")
        print(item["作者"])

        print()


    # ========================================================
    # 10. 儲存 CSV
    # ========================================================

    # encoding="utf-8-sig"：讓 Excel 打開時中文不會變亂碼
    # newline=""：避免在 Windows 上每一行中間多出一個空行

    filename = "ptt_gossiping.csv"

    print("=" * 60)
    print("儲存 CSV")
    print("=" * 60)

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as csvfile:

        fieldnames = [
            "網址",
            "標題",
            "作者"
        ]

        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames
        )

        writer.writeheader()       # 先寫第一列：欄位名稱（網址、標題、作者）

        writer.writerows(data)     # 再把所有文章一次寫進去


    print("完成！")
    print("共儲存：", len(data), "筆")
    print("檔案：", filename)


finally:

    # ========================================================
    # 11. 關閉瀏覽器
    # ========================================================

    # finally：不管上面有沒有出錯，最後一定會執行這裡，避免留下沒關的 Chrome 視窗

    print()
    print("關閉瀏覽器...")

    driver.quit()

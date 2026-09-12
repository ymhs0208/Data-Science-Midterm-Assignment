from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# ==============================
# momo 網址
# ==============================
url = "https://www.momoshop.com.tw/main/Main.jsp?cid=memb&oid=back2hp&mdiv=1099800000-bt_0_150_01-bt_0_150_01_e1&ctype=B"


# ==============================
# Chrome 設定
# ==============================
options = Options()

# 如果想看到瀏覽器操作畫面，不要加 headless
options.add_argument("--start-maximized")

# 避免部分網站因自動化瀏覽器而出現問題
options.add_argument("--disable-blink-features=AutomationControlled")

options.add_argument(
    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)


# ==============================
# 開啟 Chrome
# ==============================
print("=" * 60)
print("開始開啟 momo")
print("=" * 60)

driver = webdriver.Chrome(options=options)

try:

    driver.get(url)

    print("已開啟 momo，等待網頁載入...")

    # 最多等待 30 秒
    wait = WebDriverWait(driver, 30)

    # 等待 body 出現
    wait.until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # 再等一下，讓 JavaScript 載入完成
    time.sleep(5)

    print("網頁載入完成")
    print("目前網址：")
    print(driver.current_url)

    # ==================================================
    # 找 momo 搜尋框
    # ==================================================

    search_box = None

    # momo 網頁版本可能不同，因此準備多個 selector
    selectors = [
        (By.ID, "keyword"),
        (By.NAME, "keyword"),
        (By.NAME, "search"),
        (By.CSS_SELECTOR, "input[type='text']"),
        (By.CSS_SELECTOR, "input[placeholder*='搜尋']"),
        (By.CSS_SELECTOR, "input[placeholder*='找商品']"),
        (By.XPATH, "//input[contains(@placeholder,'搜尋')]"),
        (By.XPATH, "//input[contains(@placeholder,'商品')]"),
    ]

    for by, selector in selectors:

        try:

            element = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((by, selector))
            )

            if element.is_displayed():

                search_box = element

                print("找到搜尋框：", selector)

                break

        except:
            pass


    # ==================================================
    # 如果找不到搜尋框
    # ==================================================

    if search_box is None:

        print()
        print("找不到搜尋框。")
        print("可能是 momo 網頁版本改變，或需要等待更久。")

        # 先把目前頁面存下來方便檢查
        with open(
            "NBA_test.html",
            "w",
            encoding="utf-8-sig"
        ) as f:

            f.write(driver.page_source)

        print("目前頁面已儲存成 NBA_test.html")

        input("請按 Enter 關閉瀏覽器...")

    else:

        # ==================================================
        # 輸入 nba
        # ==================================================

        print("開始輸入：nba")

        search_box.click()

        search_box.clear()

        search_box.send_keys("nba")

        print("已輸入 nba")

        # ==================================================
        # 按 Enter 搜尋
        # ==================================================

        search_box.send_keys(Keys.ENTER)

        print("已按下 Enter，等待搜尋結果...")

        # 等待網址或頁面變化
        time.sleep(8)

        print()
        print("搜尋完成")
        print("搜尋後網址：")
        print(driver.current_url)

        # ==================================================
        # 儲存 HTML
        # ==================================================

        html = driver.page_source

        with open(
            "NBA_test.html",
            "w",
            encoding="utf-8-sig"
        ) as f:

            f.write(html)

        print()
        print("=" * 60)
        print("成功！")
        print("檔案：NBA_test.html")
        print("編碼：UTF-8-SIG")
        print("HTML 字數：", len(html))
        print("=" * 60)

        # 保留瀏覽器讓你確認
        input("請確認瀏覽器畫面，完成後按 Enter 關閉...")


finally:

    driver.quit()

    print("Chrome 已關閉")

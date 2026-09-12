from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import csv
import time


# ============================================================
# 基本設定
# ============================================================

URL = "https://www.ptt.cc/bbs/Gossiping/index.html"

print("=" * 60)
print("PTT Gossiping 爬蟲")
print("=" * 60)


# ============================================================
# 建立 Chrome WebDriver
# ============================================================

options = Options()

# 如果不想看到 Chrome 視窗，可以取消下面這行的註解
# options.add_argument("--headless=new")

options.add_argument("--window-size=1400,900")
options.add_argument("--disable-blink-features=AutomationControlled")

# Selenium 4.6+ 通常會自動處理 ChromeDriver
driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 15)


try:

    # ========================================================
    # 1. 開啟 PTT 八卦版
    # ========================================================

    print("開啟 PTT Gossiping...")
    driver.get(URL)

    time.sleep(2)

    print("目前網址：")
    print(driver.current_url)

    print()


    # ========================================================
    # 2. 處理 18 歲分級問題
    # ========================================================

    if "over18" in driver.current_url or "ask/over18" in driver.current_url:

        print("偵測到 18 歲分級頁面")
        print("準備確認已滿 18 歲...")

        try:
            # PTT 的「我已滿18歲」按鈕
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
            button.click()

        except TimeoutException:

            # 如果上面的 selector 找不到，
            # 嘗試找頁面上所有按鈕 / 連結
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

                    if element.is_displayed():
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

        time.sleep(3)


    # ========================================================
    # 3. 如果仍然在分級頁，使用 cookie
    # ========================================================

    if "over18" in driver.current_url or "ask/over18" in driver.current_url:

        print("按鈕處理失敗，設定 over18 cookie...")

        try:
            driver.add_cookie({
                "name": "over18",
                "value": "1",
                "domain": ".ptt.cc",
                "path": "/"
            })

            print("已設定 over18=1")

            driver.get(URL)

            time.sleep(3)

        except Exception as e:
            print("Cookie 設定失敗：", e)


    # ========================================================
    # 4. 確認已經進入 Gossiping
    # ========================================================

    print()
    print("目前網址：")
    print(driver.current_url)

    print()


    # ========================================================
    # 5. 列出網站 Title
    # ========================================================

    print("=" * 60)
    print("網站 Title")
    print("=" * 60)

    print(driver.title)

    print()


    # ========================================================
    # 6. 等待文章列表
    # ========================================================

    try:

        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.r-ent")
            )
        )

    except TimeoutException:

        print("等待文章列表逾時。")
        print("目前網址：", driver.current_url)

        # 印出部分網頁內容方便除錯
        print(driver.page_source[:2000])

        raise SystemExit


    # ========================================================
    # 7. 找出所有文章
    # ========================================================

    articles = driver.find_elements(
        By.CSS_SELECTOR,
        "div.r-ent"
    )

    print("=" * 60)
    print("文章列表")
    print("=" * 60)

    print("共找到：", len(articles), "筆")
    print()


    data = []


    # ========================================================
    # 8. 逐筆抓取
    # ========================================================

    for article in articles:

        try:

            # ------------------------------------------------
            # 標題
            # ------------------------------------------------

            title_element = article.find_element(
                By.CSS_SELECTOR,
                "div.title"
            )

            title = title_element.text.strip()


            # ------------------------------------------------
            # 如果文章已被刪除
            # ------------------------------------------------

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

                href = link_element.get_attribute("href")

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
            # 轉成 PTT 相對網址
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
    # 9. 印出結果
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

        writer.writeheader()

        writer.writerows(data)


    print("完成！")
    print("共儲存：", len(data), "筆")
    print("檔案：", filename)


finally:

    # ========================================================
    # 11. 關閉瀏覽器
    # ========================================================

    print()
    print("關閉瀏覽器...")

    driver.quit()

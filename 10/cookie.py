
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
COOKIE_URL = "https://www.ptt.cc/"

FILENAME = "ptt_gossiping.csv"

print("=" * 60)
print("PTT Gossiping 爬蟲")
print("=" * 60)


# ============================================================
# 建立 Chrome WebDriver
# ============================================================

options = Options()

# 不顯示 Chrome 視窗時，取消下行註解
# options.add_argument("--headless=new")

options.add_argument("--window-size=1400,900")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)


try:

    # ========================================================
    # 1. 開啟 PTT 網站
    # ========================================================

    print("開啟 PTT 網站...")
    driver.get(COOKIE_URL)

    wait.until(
        EC.presence_of_element_located(
            (By.TAG_NAME, "body")
        )
    )

    print("目前網址：", driver.current_url)


    # ========================================================
    # 2. 注入 over18 Cookie
    # ========================================================

    print("\n設定 over18 Cookie...")

    driver.add_cookie({
        "name": "over18",
        "value": "1",
        "domain": "www.ptt.cc",
        "path": "/"
    })

    print("Cookie 設定完成")


    # ========================================================
    # 3. 進入 PTT 八卦版
    # ========================================================

    print("\n開啟 PTT Gossiping...")
    driver.get(URL)

    time.sleep(2)

    print("目前網址：", driver.current_url)
    print("網站 Title：", driver.title)


    # ========================================================
    # 4. 等待文章列表
    # ========================================================

    print("\n等待文章列表...")

    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div.r-ent")
            )
        )

    except TimeoutException:

        print("等待文章列表逾時。")
        print("目前網址：", driver.current_url)
        print("網頁內容：")
        print(driver.page_source[:2000])

        raise


    # ========================================================
    # 5. 抓取文章資料
    # ========================================================

    articles = driver.find_elements(
        By.CSS_SELECTOR,
        "div.r-ent"
    )

    print("\n" + "=" * 60)
    print("文章列表")
    print("=" * 60)

    print("找到文章區塊：", len(articles), "筆")

    data = []

    for article in articles:

        try:

            # 取得標題
            title_element = article.find_element(
                By.CSS_SELECTOR,
                "div.title"
            )

            title = title_element.text.strip()

            # 略過空標題及已刪除文章
            if not title:
                continue

            if title == "(本文已被刪除)":
                continue

            # 取得文章網址
            try:
                link_element = article.find_element(
                    By.CSS_SELECTOR,
                    "div.title a"
                )

                href = link_element.get_attribute("href")

            except Exception:
                continue

            if not href:
                continue

            # 取得作者
            try:
                author_element = article.find_element(
                    By.CSS_SELECTOR,
                    "div.meta .author"
                )

                author = author_element.text.strip()

            except Exception:
                author = "N/A"

            # 轉成相對網址
            if href.startswith("https://www.ptt.cc"):
                href = href.replace(
                    "https://www.ptt.cc",
                    "",
                    1
                )

            elif href.startswith("http://www.ptt.cc"):
                href = href.replace(
                    "http://www.ptt.cc",
                    "",
                    1
                )

            # 儲存資料
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
    # 6. 印出抓取結果
    # ========================================================

    print("\n" + "=" * 60)
    print("抓取結果")
    print("=" * 60)

    for i, item in enumerate(data, 1):

        print("-" * 60)
        print(f"第 {i} 筆")
        print("網址：", item["網址"])
        print("標題：", item["標題"])
        print("作者：", item["作者"])


    # ========================================================
    # 7. 匯出 CSV
    # ========================================================

    print("\n" + "=" * 60)
    print("儲存 CSV")
    print("=" * 60)

    with open(
        FILENAME,
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
    print("檔案：", FILENAME)


except TimeoutException:
    print("\n頁面載入失敗，請檢查網路或 PTT 網站狀態。")

except Exception as e:
    print("\n程式執行發生錯誤：", e)

finally:

    # ========================================================
    # 8. 關閉瀏覽器
    # ========================================================

    print("\n關閉瀏覽器...")
    driver.quit()
    print("程式結束")

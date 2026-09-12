from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import csv
import time


# ============================================================
# HoopsHype NBA 球員薪資
# ============================================================

url = "https://hoopshype.com/salaries/players/"


# ============================================================
# Selenium 設定
# ============================================================

options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

options.add_argument(
    "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)


# ============================================================
# 開啟 Chrome
# ============================================================

driver = webdriver.Chrome(options=options)

try:

    print("=" * 60)
    print("HoopsHype NBA 球員薪資")
    print("=" * 60)

    driver.get(url)

    print("正在載入網頁...")

    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script(
            "return document.readyState"
        ) == "complete"
    )

    time.sleep(5)

    print("網頁載入完成")


    # ========================================================
    # Selenium 取得 HTML
    # ========================================================

    html = driver.page_source


    # ========================================================
    # BeautifulSoup
    # ========================================================

    soup = BeautifulSoup(html, "html.parser")


    # ========================================================
    # 找薪資表格
    # ========================================================

    tables = soup.find_all("table")

    print("找到表格：", len(tables), "個")


    salary_table = None

    for table in tables:

        text = table.get_text(" ", strip=True)

        if "Stephen Curry" in text:

            salary_table = table

            break


    if salary_table is None:

        print("找不到薪資表格")

        with open(
            "debug.html",
            "w",
            encoding="utf-8-sig"
        ) as f:

            f.write(html)

        input("請按 Enter 結束")

        exit()


    print("成功找到薪資表格")


    # ========================================================
    # 取得所有 tr
    # ========================================================

    rows = salary_table.find_all("tr")


    # ========================================================
    # 建立正確欄位名稱
    # ========================================================

    headers = [
        "排名",
        "球員",
        "2025/26",
        "2026/27",
        "2027/28",
        "2028/29"
    ]


    # ========================================================
    # 抓取所有球員
    # ========================================================

    all_data = []


    for row in rows:

        cells = row.find_all(["td", "th"])

        if len(cells) < 2:
            continue


        data = []

        for cell in cells:

            text = cell.get_text(
                " ",
                strip=True
            )

            data.append(text)


        # ====================================================
        # 只保留 6 欄
        # ====================================================

        if len(data) >= 6:

            data = data[:6]

        else:

            while len(data) < 6:

                data.append("-")


        # ====================================================
        # 排除表頭
        # ====================================================

        if data[0] == "Rk":
            continue

        if data[0] == "Rank":
            continue

        if data[1].lower() == "player":
            continue


        # ====================================================
        # 確定是球員資料
        # ====================================================

        if data[1]:

            all_data.append(data)


    # ========================================================
    # 顯示抓到幾筆
    # ========================================================

    print()
    print("=" * 60)
    print("共抓到", len(all_data), "筆球員資料")
    print("=" * 60)


    # ========================================================
    # 顯示前 10 筆
    # ========================================================

    for i, row in enumerate(all_data[:10], 1):

        print(
            i,
            row
        )


    # ========================================================
    # 儲存 all_play.csv
    # ========================================================

    with open(
        "all_play.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.writer(f)

        # 寫入正確欄位名稱
        writer.writerow(headers)

        # 寫入所有球員
        writer.writerows(all_data)


    print()
    print("已完成：all_play.csv")


    # ========================================================
    # 前 3 名
    # ========================================================

    top3 = all_data[:3]


    # ========================================================
    # highest.csv
    #
    # 注意：
    # HoopsHype 薪資表沒有背號欄位
    # 因此背號先以 N/A 表示
    # ========================================================

    with open(
        "highest.csv",
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "名字",
            "背號",
            "薪資"
        ])


        for row in top3:

            name = row[1]

            salary = row[2]

            writer.writerow([
                name,
                "N/A",
                salary
            ])


    # ========================================================
    # 顯示前三名
    # ========================================================

    print()
    print("=" * 60)
    print("前 3 位高薪球員")
    print("=" * 60)


    for i, row in enumerate(top3, 1):

        print(
            f"{i}. "
            f"{row[1]} | "
            f"薪資：{row[2]}"
        )


    # ========================================================
    # 完成
    # ========================================================

    print()
    print("=" * 60)
    print("完成！")
    print("=" * 60)

    print("all_play.csv → 所有球員薪資")
    print("highest.csv → 前 3 位高薪球員")

    print()
    print("CSV 使用 UTF-8-SIG 編碼")


    input("\n按 Enter 關閉瀏覽器...")


finally:

    driver.quit()

    print("Chrome 已關閉")

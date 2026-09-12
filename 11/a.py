from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import csv
import time


# ==========================================
# Chrome 設定
# ==========================================

options = Options()

# 如果想看到 Chrome 視窗，就不要加 headless
# options.add_argument("--headless")

options.add_argument("--window-size=1400,1000")


driver = webdriver.Chrome(
    options=options
)


# ==========================================
# 開啟網站
# ==========================================

url = "https://fchart.github.io/ML/nba_items.html"

driver.get(url)


# 等待網頁載入
time.sleep(2)


# ==========================================
# 顯示標題
# ==========================================

print("=" * 60)
print("NBA 商品資料")
print("=" * 60)


# ==========================================
# 找表格
# ==========================================

try:

    table = WebDriverWait(
        driver,
        10
    ).until(
        EC.presence_of_element_located(
            (By.TAG_NAME, "table")
        )
    )

except:

    print("找不到 table")

    driver.quit()

    exit()


# ==========================================
# 抓目前頁面的所有資料
# ==========================================

def get_table_data():

    rows = table.find_elements(
        By.TAG_NAME,
        "tr"
    )

    data = []

    for row in rows:

        cells = row.find_elements(
            By.CSS_SELECTOR,
            "th, td"
        )

        row_data = []

        for cell in cells:

            text = cell.text.strip()

            row_data.append(text)


        if row_data:

            data.append(row_data)


    return data


# ==========================================
# 分頁處理
# ==========================================

page_number = 1


while True:

    # 等待目前頁面更新
    time.sleep(1)


    # --------------------------------------
    # 抓資料
    # --------------------------------------

    data = get_table_data()


    print()
    print(
        f"第 {page_number} 頁"
    )


    # --------------------------------------
    # 顯示資料
    # --------------------------------------

    for row in data:

        print(row)


    # --------------------------------------
    # 儲存 CSV
    # --------------------------------------

    filename = (
        f"NBA_Products{page_number}.csv"
    )


    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.writer(file)

        writer.writerows(data)


    # --------------------------------------
    # 要求 2
    # --------------------------------------

    print(
        f"儲存頁面: {page_number}"
    )


    # ======================================
    # 找「下一頁」
    # ======================================

    buttons = driver.find_elements(
        By.TAG_NAME,
        "button"
    )


    next_button = None


    for button in buttons:

        text = button.text.strip()


        if (
            "下一頁" in text
            or "Next" in text
            or ">" == text
        ):

            next_button = button

            break


    # ======================================
    # 如果沒有下一頁
    # ======================================

    if next_button is None:

        print()
        print("沒有下一頁")

        break


    # ======================================
    # 如果下一頁不能按
    # ======================================

    if not next_button.is_enabled():

        print()
        print("已經是最後一頁")

        break


    # ======================================
    # 點下一頁
    # ======================================

    try:

        next_button.click()

        page_number += 1

        time.sleep(1)

    except:

        print()
        print("無法點擊下一頁")

        break


# ==========================================
# 結束
# ==========================================

driver.quit()


print()
print("=" * 60)
print("全部 NBA 商品資料抓取完成！")
print("=" * 60)

import csv
import time
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.agoda.com/zh-tw/"
KEYWORD = "台中"
OUTPUT = "agoda_result.csv"
# 入住日自動取「明天」，住 1 晚，所以任何時候執行都不會用到過期日期
CHECK_IN = (date.today() + timedelta(days=1)).isoformat()
# Agoda 偵測到自動化瀏覽器時，首頁搜尋鈕有時按了不會跳轉；
# 這時直接用台中市(city=12080)的搜尋結果網址，等於手動幫它搜尋好
# los=住幾晚、rooms=房間數、adults=大人人數
FALLBACK_URL = f"https://www.agoda.com/zh-tw/search?city=12080&checkIn={CHECK_IN}&los=1&rooms=1&adults=2"


def search_city(driver, wait):
    """在首頁輸入「台中」並送出搜尋"""
    box = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "input[data-selenium='textInput'], input#textInput")))
    box.click()
    box.clear()
    box.send_keys(KEYWORD)
    # 輸入文字後 Agoda 要一點時間才會跳出建議清單，等清單出來再用方向鍵選第一個（台中市）
    time.sleep(2)
    box.send_keys(Keys.ARROW_DOWN)
    box.send_keys(Keys.ENTER)
    time.sleep(1)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()  # 選完地點後日曆會自動彈出並擋住搜尋鈕，按 ESC 關掉
    time.sleep(1)
    search_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button[data-element-name='search-button']")))
    driver.execute_script("arguments[0].click();", search_btn)  # 用 JS 直接點，即使按鈕被其他浮層蓋住也點得到


def parse_visible(driver, seen):
    """把畫面上目前看得到的飯店讀出來，放進 seen（用飯店名當 key，同一間不會重複）。
    回傳這一輪「新增」了幾間。"""
    before = len(seen)
    cards = driver.find_elements(By.CSS_SELECTOR, "li[data-selenium='hotel-item'], ol.hotel-list-container > li")
    for card in cards:
        try:
            name = card.find_element(By.CSS_SELECTOR, "[data-selenium='hotel-name']").text.strip()
        except Exception:
            continue  # 找不到飯店名稱的卡片（例如廣告區塊）直接略過
        if not name or name in seen:
            continue
        try:
            price = card.find_element(By.CSS_SELECTOR, "[data-selenium='display-price']").text.strip()
        except Exception:
            price = "無價格"
        seen[name] = price
    return len(seen) - before


def click_more(driver):
    """如果頁面底部有「載入更多 / 下一頁」按鈕就按下去，有按到回傳 True。"""
    # Agoda 不同版本的按鈕長得不一樣（文字、id、aria-label），每種都試，哪個存在就按哪個
    xpaths = [
        "//button[contains(., '載入更多') or contains(., '顯示更多') or contains(., '查看更多')]",
        "//*[@id='paginationNext' or @data-selenium='pagination-next-btn']",
        "//button[contains(@aria-label, '下一頁') or contains(@aria-label, 'Next')]",
    ]
    for xp in xpaths:
        for btn in driver.find_elements(By.XPATH, xp):
            try:
                if btn.is_displayed() and btn.is_enabled():
                    # 先把按鈕捲到畫面中間，不然可能被固定在頂部/底部的橫幅擋住
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", btn)
                    return True
            except Exception:
                continue
    return False


def scrape_all(driver, max_idle=5, max_rounds=300):
    """一邊捲動一邊收集，直到連續 max_idle 輪都沒有新飯店才停。
    原本的問題：只捲 12 次、最後才一次讀取，所以只拿到約 30 筆；
    而且網站為了省資源會把捲過去的卡片從畫面移除，最後一次讀就會漏掉。
    現在改成「每捲一下就先讀一次並記下來」，就不會漏。"""
    seen = {}
    idle = 0
    for _ in range(max_rounds):
        new = parse_visible(driver, seen)
        print(f"目前累計 {len(seen)} 間（本輪新增 {new}）")
        if new:
            idle = 0
        else:
            # 沒有新資料：先試著按「載入更多/下一頁」，按不到才算閒置一次
            if click_more(driver):
                time.sleep(3)  # 等新一批飯店載入
                idle = 0
                continue
            idle += 1
            if idle >= max_idle:
                break
        # 往下捲一屏；每次只捲一點，才不會跳過中間的卡片
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
        time.sleep(1.5)
        # 捲到底就稍微往上抖一下，觸發網站繼續載入
        at_bottom = driver.execute_script(
            "return window.innerHeight + window.scrollY >= document.body.scrollHeight - 50;")
        if at_bottom:
            driver.execute_script("window.scrollBy(0, -400);")
            time.sleep(0.8)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
    return list(seen.items())


def main():
    """流程：開瀏覽器 → 搜尋台中 → 一路捲動收集飯店 → 存成 CSV"""
    # 下面兩行是把「自動化」的標記藏起來，避免被 Agoda 當成機器人擋掉
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)  # Selenium 4.6+ 會自動下載對應 chromedriver
    driver.maximize_window()
    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)  # 之後 wait.until 最多等 20 秒，網頁慢時不會太早放棄
        search_city(driver, wait)

        # Agoda 有時會把搜尋結果開在新分頁，所以要把操作對象切到最新的分頁
        time.sleep(3)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        if "/search" not in driver.current_url:
            print("搜尋鈕未跳轉，改用搜尋結果網址")
            driver.get(FALLBACK_URL)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-selenium='hotel-name']")))
        rows = scrape_all(driver)
    finally:
        driver.quit()  # 中途出錯也要關掉，否則會留下一堆殘留的 Chrome 視窗

    # utf-8-sig 會在檔頭加標記，Excel 才不會把中文顯示成亂碼
    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["飯店名", "價格"])
        writer.writerows(rows)
    print(f"已儲存 {len(rows)} 筆資料至 {OUTPUT}")


if __name__ == "__main__":
    main()

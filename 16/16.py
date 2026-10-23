# ============================================================
# 第 16 題：爬 Agoda「台中」的飯店名稱與價格，存成 CSV
#
# 整體流程：
#   1. 打開 Chrome，到 Agoda 首頁，輸入「台中」並點選地點
#   2. 優先「點搜尋按鈕」進結果頁；按鈕點不動就依序換三種點法
#      （滑鼠點擊 → Enter 鍵 → JS 點擊）
#   3. 三種點法都失敗，才改用備用的「搜尋結果網址」直接進結果頁
#   4. 進到結果頁後慢慢往下捲、邊捲邊記錄飯店，最後寫進 CSV
# ============================================================

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 讓 CSV 輸出存在此資料夾

import csv
import time
from datetime import date, timedelta  # 用來算「明天」的日期
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.agoda.com/zh-tw/"
KEYWORD = "台中"
OUTPUT = "agoda_result.csv"

# 入住日自動設成「明天」，寫死日期的話過了那天網頁會說日期已過。
CHECK_IN = (date.today() + timedelta(days=1)).isoformat()

# 備用網址：萬一搜尋鈕怎麼點都不跳轉，就直接用「已經搜尋好台中」的結果頁網址。
#   city=12080 → 台中市在 Agoda 的代號
#   checkIn    → 入住日期
#   los=1      → 住 1 晚
#   rooms=1    → 1 間房
#   adults=2   → 2 位大人
FALLBACK_URL = f"https://www.agoda.com/zh-tw/search?city=12080&checkIn={CHECK_IN}&los=1&rooms=1&adults=2"

# 日曆彈出時按鈕名稱會變成 search-button-sticky，所以用「開頭是」來比對
SEARCH_BTN = "button[data-element-name^='search-button']"


def on_result_page(driver):
    """目前（或任何一個分頁）是不是已經在結果頁？是的話切到那個分頁並回傳 True。
    Agoda 有時會把結果開在新分頁，所以每個分頁都要看。"""
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        # 只認飯店結果頁 /zh-tw/search；按搜尋鈕時 Agoda 還會順便開
        # 「活動體驗」分頁（/activities/search），那個不能算。
        if urlparse(driver.current_url).path.rstrip("/").endswith("/zh-tw/search"):
            return True
    return False


def wait_result_page(driver, seconds=8):
    """最多等 seconds 秒，看按下去後有沒有跳到結果頁。"""
    end = time.time() + seconds
    while time.time() < end:
        if on_result_page(driver):
            return True
        time.sleep(0.5)
    return False


def click_search(driver, wait):
    """按下搜尋鈕，並確認真的跳到結果頁。
    依序嘗試三種點法，哪一種成功就停：
      1. 滑鼠真實點擊（ActionChains，最像真人）
      2. 在搜尋框按 Enter
      3. JavaScript 點擊（就算被蓋住也點得到）
    三種都沒跳轉就丟出 RuntimeError，由 main() 決定改走備用網址。"""
    # 日曆彈出時會蓋住按鈕，「可點擊」的判斷會一直不過，所以只等它存在；
    # 被蓋住時滑鼠點擊會失敗，下面會自動換 JS 點擊。
    btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, SEARCH_BTN)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
    time.sleep(0.5)

    def real_click():
        ActionChains(driver).move_to_element(btn).pause(0.3).click().perform()

    def press_enter():
        box = driver.find_element(By.CSS_SELECTOR, "input[data-selenium='textInput'], input#textInput")
        box.send_keys(Keys.ENTER)

    def js_click():
        driver.execute_script("arguments[0].click();", btn)

    for name, action in (("滑鼠點擊", real_click), ("Enter 鍵", press_enter), ("JS 點擊", js_click)):
        try:
            action()
        except Exception as e:
            print(f"{name}失敗：{type(e).__name__}")
            continue
        if wait_result_page(driver):
            print(f"用「{name}」成功跳到結果頁")
            return
        print(f"「{name}」沒有跳轉，換下一種")

    raise RuntimeError("搜尋按鈕三種點法都沒跳到結果頁")


def search_city(driver, wait):
    """在首頁搜尋框輸入「台中」、選好地點，再按搜尋鈕。"""
    box = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "input[data-selenium='textInput'], input#textInput")))
    box.click()
    box.clear()
    box.send_keys(KEYWORD)

    # 等建議清單出現，直接「點」第一項（台中市, 台灣 城市）。
    # 不用方向鍵：按 ↓ 會跳過第一項選到第二項，搜尋就送不出去。
    # 清單會隨打字更新，不能盲點第一項（會點到逢甲之類的別項），
    # 所以等到「台中市, 台灣」這個「城市」選項出現，才點它。
    # 清單重新渲染時，剛找到的選項可能馬上過期（StaleElementReference），
    # 所以「找 + 點」包在一起，過期就重來。
    def click_city_option(d):
        try:
            for li in d.find_elements(By.CSS_SELECTOR, "[data-selenium='autocompletePanel'] li[role='option']"):
                text = li.text.replace("\n", " ")
                if text.startswith(f"{KEYWORD}市, 台灣") and "城市" in text and li.is_displayed():
                    li.click()
                    return True
        except StaleElementReferenceException:
            pass
        return False

    wait.until(click_city_option)
    time.sleep(2)   # 選完會彈出日曆（日期用預設值，不用管它）

    chosen = driver.find_element(
        By.CSS_SELECTOR, "input[data-selenium='textInput'], input#textInput").get_attribute("value")
    if not chosen.startswith(KEYWORD):
        raise RuntimeError(f"選到的地點不是{KEYWORD}，而是：{chosen}")

    click_search(driver, wait)


def parse_visible(driver, seen):
    """讀出目前網頁上已載入的飯店，記到 seen：{飯店編號: (飯店名, 價格)}。
    用 data-hotelid 當依據，避免同名分店被當成同一間。回傳本輪新增幾間。"""
    before = len(seen)

    cards = driver.find_elements(By.CSS_SELECTOR, "li[data-selenium='hotel-item']")
    for card in cards:
        hotel_id = card.get_attribute("data-hotelid")
        if not hotel_id or hotel_id in seen:
            continue

        try:
            name = card.find_element(By.CSS_SELECTOR, "[data-selenium='hotel-name']").text.strip()
        except Exception:
            continue
        if not name:
            continue

        try:
            price = card.find_element(By.CSS_SELECTOR, "[data-selenium='display-price']").text.strip()
        except Exception:
            price = "無價格"

        seen[hotel_id] = (name, price)

    return len(seen) - before


def scrape_all(driver, max_idle=8, max_rounds=300):
    """慢慢往下捲、邊捲邊記錄，連續 max_idle 輪沒新飯店就停。
    注意：頁面底部的「下一頁」「查看更多民宿」不能按，按了會離開清單。"""
    seen = {}
    idle = 0

    for _ in range(max_rounds):
        new = parse_visible(driver, seen)
        print(f"目前累計 {len(seen)} 間（本輪新增 {new}）")

        if new:
            idle = 0
        else:
            idle += 1
            if idle >= max_idle:
                break

        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
        time.sleep(1.5)

    return list(seen.values())


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)
        try:
            search_city(driver, wait)   # 內含點按鈕並確認跳轉
        except RuntimeError as e:
            # 按鈕三種點法都沒跳轉（或地點沒選對）→ 改用備用的結果頁網址
            print(f"{e}，改用搜尋結果網址")
            driver.switch_to.window(driver.window_handles[0])
            driver.get(FALLBACK_URL)

        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-selenium='hotel-name']")))

        rows = scrape_all(driver)
    finally:
        driver.quit()

    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["飯店名", "價格"])
        writer.writerows(rows)
    print(f"已儲存 {len(rows)} 筆資料至 {OUTPUT}")


if __name__ == "__main__":
    main()

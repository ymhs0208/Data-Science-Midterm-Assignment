import csv
import time

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URL = "https://www.agoda.com/zh-tw/"
KEYWORD = "台中"
OUTPUT = "agoda_result.csv"
# Agoda 偵測到自動化瀏覽器時，首頁搜尋鈕不會跳轉，改用台中市(city=12080)的搜尋結果網址
FALLBACK_URL = "https://www.agoda.com/zh-tw/search?city=12080&checkIn=2026-10-10&los=1&rooms=1&adults=2"


def search_city(driver, wait):
    """在首頁輸入「台中」並送出搜尋"""
    box = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "input[data-selenium='textInput'], input#textInput")))
    box.click()
    box.clear()
    box.send_keys(KEYWORD)
    # 等待自動完成選單出現後選第一筆
    time.sleep(2)
    box.send_keys(Keys.ARROW_DOWN)
    box.send_keys(Keys.ENTER)
    time.sleep(1)
    ActionChains(driver).send_keys(Keys.ESCAPE).perform()  # 關閉自動彈出的日曆
    time.sleep(1)
    search_btn = wait.until(EC.element_to_be_clickable(
        (By.CSS_SELECTOR, "button[data-element-name='search-button']")))
    driver.execute_script("arguments[0].click();", search_btn)  # 避開彈出視窗遮擋


def scroll_to_load(driver, rounds=12):
    """逐步向下捲動，讓更多飯店載入"""
    for _ in range(rounds):
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(1.5)


def parse_results(driver):
    """回傳 [(飯店名, 價格), ...]"""
    rows = []
    cards = driver.find_elements(By.CSS_SELECTOR, "li[data-selenium='hotel-item'], ol.hotel-list-container > li")
    for card in cards:
        try:
            name = card.find_element(By.CSS_SELECTOR, "[data-selenium='hotel-name']").text.strip()
        except Exception:
            continue
        try:
            price = card.find_element(By.CSS_SELECTOR, "[data-selenium='display-price']").text.strip()
        except Exception:
            price = "無價格"
        rows.append((name, price))
    return rows


def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=options)  # Selenium 4.6+ 會自動下載對應 chromedriver
    driver.maximize_window()
    try:
        driver.get(URL)
        wait = WebDriverWait(driver, 20)
        search_city(driver, wait)

        # 搜尋後可能在新分頁開啟結果
        time.sleep(3)
        if len(driver.window_handles) > 1:
            driver.switch_to.window(driver.window_handles[-1])

        if "/search" not in driver.current_url:
            print("搜尋鈕未跳轉，改用搜尋結果網址")
            driver.get(FALLBACK_URL)
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "[data-selenium='hotel-name']")))
        scroll_to_load(driver)
        rows = parse_results(driver)
    finally:
        driver.quit()

    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["飯店名", "價格"])
        writer.writerows(rows)
    print(f"已儲存 {len(rows)} 筆資料至 {OUTPUT}")


if __name__ == "__main__":
    main()

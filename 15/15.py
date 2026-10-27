
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 讓 CSV 等輸出檔存在此資料夾

import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


def search_xpath_and_export():

    # ==========================================
    # 1. 初始化 WebDriver
    # ==========================================

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()

    # 保留原本的瀏覽器設定
    options.add_experimental_option(
        "excludeSwitches", ["enable-automation"]
    )
    options.add_experimental_option(
        "useAutomationExtension", False
    )
    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )
    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    driver.maximize_window()

    # 設定語言標頭
    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {
            "headers": {
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8"
            }
        }
    )

    extracted_data = []
    seen_links = set()
    page_number = 1
    max_pages = 30

    try:

        # ======================================
        # 2. 開啟 Google 並搜尋 xpath
        # ======================================

        driver.get("https://www.google.com")

        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.NAME, "q")
            )
        )

        search_box.send_keys("xpath")
        search_box.send_keys(Keys.RETURN)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "search")
            )
        )

        time.sleep(2)

        # ======================================
        # 3. 開始抓取每一頁
        # ======================================

        while page_number <= max_pages:

            print()
            print("=" * 60)
            print(f"正在抓取第 {page_number} 頁")
            print("=" * 60)

            # 若 Google 要求驗證，停止自動抓取
            if (
                "sorry" in driver.current_url.lower()
                or "recaptcha" in driver.page_source.lower()
            ):
                print("Google 要求驗證，停止抓取")
                break

            page_count = 0

            # ==================================
            # 4. 抓取目前已載入的資料
            # ==================================

            def get_results():

                nonlocal page_count

                # 策略 1：直接尋找包含 h3 的 a
                links_with_h3 = driver.find_elements(
                    By.XPATH,
                    "//a[descendant::h3]"
                )

                # 策略 2：若沒找到，從 h3 往上找 a
                if not links_with_h3:

                    h3_list = driver.find_elements(
                        By.XPATH, "//h3"
                    )

                    for h3 in h3_list:

                        try:
                            title = h3.text.strip()

                            if not title:
                                continue

                            parent_a = h3.find_element(
                                By.XPATH,
                                "./ancestor::a"
                            )

                            link = parent_a.get_attribute("href")

                            if (
                                link
                                and link.startswith("http")
                                and link not in seen_links
                            ):

                                seen_links.add(link)

                                extracted_data.append({
                                    "標題": title,
                                    "超連結": link
                                })

                                page_count += 1

                        except Exception:
                            continue

                else:

                    for a in links_with_h3:

                        try:
                            h3 = a.find_element(
                                By.XPATH, ".//h3"
                            )

                            title = h3.text.strip()
                            link = a.get_attribute("href")

                            if (
                                title
                                and link
                                and link.startswith("http")
                                and link not in seen_links
                            ):

                                seen_links.add(link)

                                extracted_data.append({
                                    "標題": title,
                                    "超連結": link
                                })

                                page_count += 1

                                print(f"{title}")
                                print(f"連結：{link}\n")

                        except Exception:
                            continue

            # 先抓目前頁面
            get_results()

            # ==================================
            # 5. 滾動頁面載入資料
            # ==================================

            print("開始滾動頁面載入資料...")

            for _ in range(3):

                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )

                time.sleep(2)

                # 每次滾動後重新抓取
                get_results()

            print(f"第 {page_number} 頁新增 {page_count} 筆")

            # ==================================
            # 6. 尋找更多搜尋結果 / 下一頁
            # ==================================

            more_btn_xpath = (
                "//a[@id='pnnext']"
                " | //a[@aria-label='Next page']"
                " | //a[@aria-label='下一頁']"
                " | //a[.//span[contains(text(),'下一頁')]]"
                " | //a[.//span[contains(text(),'Next')]]"
                " | //a[.//span[contains(text(),'更多搜尋結果')]]"
                " | //a[.//span[contains(text(),'More results')]]"
                " | //div[@role='button'][.//span[contains(text(),'更多搜尋結果')]]"
            )

            more_btns = driver.find_elements(
                By.XPATH,
                more_btn_xpath
            )

            next_button = None

            for btn in more_btns:

                if btn.is_displayed() and btn.is_enabled():
                    next_button = btn
                    break

            # 沒有下一頁
            if next_button is None:

                print("沒有更多搜尋結果")
                break

            # ==================================
            # 7. 點擊下一頁
            # ==================================

            try:

                old_url = driver.current_url

                old_links = {
                    a.get_attribute("href")
                    for a in driver.find_elements(
                        By.XPATH, "//a[descendant::h3]"
                    )
                }

                driver.execute_script(
                    "arguments[0].scrollIntoView(true);",
                    next_button
                )

                time.sleep(1)

                next_button.click()

                print("成功點擊下一頁！")

                # 等待網址改變或出現新的搜尋結果
                def has_new_results(d):

                    if d.current_url != old_url:
                        return True

                    new_links = {
                        a.get_attribute("href")
                        for a in d.find_elements(
                            By.XPATH, "//a[descendant::h3]"
                        )
                    }

                    return bool(new_links - old_links)

                try:

                    WebDriverWait(driver, 15).until(
                        has_new_results
                    )

                except TimeoutException:

                    print("沒有偵測到新資料，停止翻頁")
                    break

                page_number += 1

                time.sleep(3)

            except Exception as e:

                print("無法點擊下一頁：", e)
                break

    except Exception as e:

        print("執行過程中發生錯誤：", e)

    finally:

        # ======================================
        # 8. 儲存所有資料
        # ======================================

        csv_filename = "xpath.csv"

        with open(
            csv_filename,
            mode="w",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=["標題", "超連結"]
            )

            writer.writeheader()
            writer.writerows(extracted_data)

        print()
        print("=" * 60)
        print(f"總共抓取 {len(extracted_data)} 筆搜尋結果")
        print(f"資料已成功寫入 {csv_filename}")
        print("=" * 60)

        driver.quit()


if __name__ == "__main__":
    search_xpath_and_export()

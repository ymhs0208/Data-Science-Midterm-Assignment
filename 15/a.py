import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def search_xpath_and_export():
    # 1. 要求 1：初始化 WebDriver
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # 關閉自動化旗標，防止 Google 阻擋
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    try:
        # 前往 Google 首頁
        driver.get("https://www.google.com")
        
        # 2. 要求 2：搜尋列中輸入 "xpath"
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.send_keys("xpath")
        search_box.send_keys(Keys.RETURN)
        
        # 等待搜尋結果主要區域載入
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        time.sleep(2)

        # 要求 2：滾動滑鼠載入資料
        print("開始滾動頁面加載資料...")
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # 要求 3：按下「更多搜尋結果」按鈕 (如果有出現)
        try:
            more_btn_xpath = "//a[.//span[contains(text(),'更多') or contains(text(),'More')]] | //div[@role='button'][.//span[contains(text(),'更多') or contains(text(),'More')]]"
            more_btns = driver.find_elements(By.XPATH, more_btn_xpath)
            
            for btn in more_btns:
                if btn.is_displayed():
                    driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", btn)
                    print("成功點擊「更多搜尋結果」按鈕！")
                    time.sleep(3)
                    break
        except Exception as e:
            print("未發現或點擊「更多搜尋結果」按鈕失敗：", e)

        # 再次滾動確保載入完整
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # 3. 關鍵改進：使用多重 XPath/策略 擷取資料 (要求 2 & 要求 3)
        extracted_data = []
        seen_links = set()

        # 策略 1：使用最普遍的祖先 XPath 定位
        links_with_h3 = driver.find_elements(By.XPATH, "//a[descendant::h3]")
        
        # 若策略 1 沒抓到，切換為 策略 2：全局找 <h3> 向上找 <a>
        if not links_with_h3:
            h3_list = driver.find_elements(By.XPATH, "//h3")
            for h3 in h3_list:
                try:
                    title = h3.text.strip()
                    if not title:
                        continue
                    parent_a = h3.find_element(By.XPATH, "./ancestor::a")
                    link = parent_a.get_attribute("href")
                    if link and link.startswith("http") and link not in seen_links:
                        seen_links.add(link)
                        extracted_data.append({"標題": title, "超連結": link})
                except Exception:
                    continue
        else:
            for a in links_with_h3:
                try:
                    h3 = a.find_element(By.XPATH, ".//h3")
                    title = h3.text.strip()
                    link = a.get_attribute("href")
                    if title and link and link.startswith("http") and link not in seen_links:
                        seen_links.add(link)
                        extracted_data.append({"標題": title, "超連結": link})
                except Exception:
                    continue

        # 要求 2：列印出本頁資訊
        print(f"\n================ 搜尋結果（共 {len(extracted_data)} 筆） ================")
        for idx, item in enumerate(extracted_data, start=1):
            print(f"{idx}. {item['標題']}")
            print(f"   連結: {item['超連結']}\n")

        # 4. 要求 3：存入 xpath.csv 中
        csv_filename = "xpath.csv"
        with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["標題", "超連結"])
            writer.writeheader()
            writer.writerows(extracted_data)

        print(f"所有資料已成功寫入 `{csv_filename}`！")

    except Exception as e:
        print("執行過程中發生錯誤：", e)

    finally:
        driver.quit()

if __name__ == "__main__":
    search_xpath_and_export()
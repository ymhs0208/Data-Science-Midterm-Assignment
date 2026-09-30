import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def search_steam_recommendations():
    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    
    # 關閉自動化測試旗標，減少被 Google 阻擋的機率
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=service, options=options)
    results_data = []

    try:
        driver.get("https://www.google.com")
        
        # 定位搜尋框
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.send_keys("Steam 遊戲推薦")
        search_box.send_keys(Keys.RETURN)
        
        # 等待搜尋結果區塊載入
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "search"))
        )
        time.sleep(3)

        # 【關鍵修正】：先定位所有 <h3> 標題，再向上尋找父層的 <a> 超連結
        h3_elements = driver.find_elements(By.TAG_NAME, "h3")
        
        for h3 in h3_elements:
            title = h3.text.strip()
            if not title:
                continue
                
            try:
                # 尋找 <h3> 上層最近的 <a> 標籤
                parent_a = h3.find_element(By.XPATH, "./ancestor::a")
                link = parent_a.get_attribute("href")
                
                if link and link.startswith("http"):
                    results_data.append({"標題": title, "超連結": link})
            except Exception:
                # 若 <h3> 外層沒有 <a> 則跳過（可能為 Google 的模組化組件或小工具）
                continue

        # 輸出結果
        print(f"成功擷取 {len(results_data)} 筆搜尋結果：\n")
        for idx, res in enumerate(results_data, start=1):
            print(f"{idx}. {res['標題']}")
            print(f"   {res['超連結']}\n")

        # 存入 CSV
        csv_filename = "steam_games.csv"
        with open(csv_filename, mode="w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["標題", "超連結"])
            writer.writeheader()
            writer.writerows(results_data)
            
        print(f"資料已成功存入 `{csv_filename}` 檔案中！")

    except Exception as e:
        print("發生錯誤：", e)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    search_steam_recommendations()
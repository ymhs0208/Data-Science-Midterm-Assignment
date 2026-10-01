import os
from getpass import getpass

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# 帳號密碼不寫在程式裡：優先讀環境變數，否則執行時輸入
username = os.environ.get("GITHUB_USER") or input("GitHub 帳號或 Email: ")
password = os.environ.get("GITHUB_PASS") or getpass("GitHub 密碼: ")

driver = webdriver.Chrome()  # Selenium 4 會自動下載對應的 chromedriver
wait = WebDriverWait(driver, 15)


def grab(title_text):
    """用標題文字找到區塊，回傳標題與整個區塊的文字"""
    heading = wait.until(EC.presence_of_element_located(
        (By.XPATH, f"//*[contains(normalize-space(.), '{title_text}') and not(*[contains(normalize-space(.), '{title_text}')])]")))
    # 往上找包含標題與說明的區塊（最多 3 層）
    block = heading
    for _ in range(3):
        parent = block.find_element(By.XPATH, "..")
        if len(parent.text.strip()) > len(heading.text.strip()):
            block = parent
            break
        block = parent
    return heading.text.strip(), block.text.strip()


try:
    # 要求 1：自動登入
    driver.get("https://github.com/login")
    wait.until(EC.presence_of_element_located((By.ID, "login_field"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.NAME, "commit").click()

    # 若出現驗證碼 / 2FA，請在瀏覽器手動完成，最多等 2 分鐘
    if "/login" in driver.current_url or "sessions" in driver.current_url:
        print("若瀏覽器要求驗證碼或 2FA，請手動完成...")
        try:
            WebDriverWait(driver, 120).until(
                lambda d: "/login" not in d.current_url and "sessions" not in d.current_url)
        except TimeoutException:
            raise SystemExit("登入失敗：帳號密碼錯誤或驗證逾時")

    driver.get("https://github.com/")

    # 要求 2：1 號視窗 (Create your first project)
    try:
        title, text = grab("Create your first project")
        print("=== 1 號視窗 ===")
        print(text)
    except TimeoutException:
        print("找不到 1 號視窗（此帳號可能已有 repository，不會顯示）")
        # 存下首頁文字與 HTML，方便檢查實際畫面長什麼樣
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        driver.save_screenshot("dashboard.png")
        print("頁面文字前 800 字：")
        print(driver.find_element(By.TAG_NAME, "body").text[:800])

    # 要求 3：2 號視窗 (Updates to your homepage feed)
    try:
        title, text = grab("Updates to your homepage feed")
        print("\n=== 2 號視窗 ===")
        print(text)
    except TimeoutException:
        print("找不到 2 號視窗（可能已被關閉或不顯示）")
finally:
    driver.quit()

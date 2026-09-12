GitHub README.md 爬蟲作業
一、作業名稱

使用 Selenium 與 WebDriver 抓取 GitHub Repository 的 README.md 資料。

二、作業目的

本作業使用 Python 的 Selenium 套件搭配 WebDriver，自動開啟 GitHub 網頁並取得指定 Repository 的 README.md 內容。

透過 Selenium 可以模擬使用者操作瀏覽器，例如：

開啟 GitHub
搜尋 Repository
點擊 Repository
開啟 README.md
讀取網頁上的文字資料
擷取 README.md 的內容
三、使用工具

本作業使用以下工具：

Python 3
Selenium
Google Chrome
Chrome WebDriver
Visual Studio Code
四、作業要求
使用 Selenium 與 WebDriver。
開啟 GitHub 網站。
搜尋指定 Repository。
進入 Repository。
找到 README.md。
擷取 README.md 的資料。
顯示 Repository 名稱。
顯示 Repository 網址。
顯示 README.md 內容。
將抓取結果儲存成 CSV 檔案。
五、程式執行流程

程式執行流程如下：

啟動 Python
    ↓
啟動 Chrome WebDriver
    ↓
開啟 GitHub
    ↓
搜尋 Repository
    ↓
進入 Repository
    ↓
尋找 README.md
    ↓
取得 README.md 內容
    ↓
顯示抓取結果
    ↓
儲存 github_readme.csv
    ↓
關閉瀏覽器

六、Python 程式碼
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time


# ==============================
# GitHub Repository 設定
# ==============================

repo_url = "https://github.com/SeleniumHQ/selenium"


# ==============================
# Chrome 設定
# ==============================

options = Options()

# 如果需要看到瀏覽器操作過程，不要使用 headless
# options.add_argument("--headless")

options.add_argument("--start-maximized")


# ==============================
# 啟動 WebDriver
# ==============================

driver = webdriver.Chrome(options=options)

try:

    # ==============================
    # 開啟 GitHub Repository
    # ==============================

    print("=" * 60)
    print("GitHub README.md 爬蟲")
    print("=" * 60)

    print("\n開啟 GitHub Repository...")
    driver.get(repo_url)

    wait = WebDriverWait(driver, 15)

    # 等待網頁載入
    time.sleep(3)

    # ==============================
    # 取得 Repository 名稱
    # ==============================

    repository_name = "Selenium"

    try:
        title = driver.title
        print("\n網頁標題：")
        print(title)
    except:
        pass

    # ==============================
    # 尋找 README
    # ==============================

    print("\n尋找 README.md...")

    readme = None

    possible_selectors = [
        "article.markdown-body",
        "div.markdown-body",
        "[data-testid='readme']",
        ".Box-body.markdown-body"
    ]

    for selector in possible_selectors:

        try:

            readme = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, selector)
                )
            )

            if readme:
                break

        except:
            continue


    # ==============================
    # 取得 README 內容
    # ==============================

    if readme:

        readme_text = readme.text.strip()

        print("\n" + "=" * 60)
        print("Repository")
        print("=" * 60)

        print(repository_name)

        print("\n" + "=" * 60)
        print("Repository URL")
        print("=" * 60)

        print(repo_url)

        print("\n" + "=" * 60)
        print("README.md")
        print("=" * 60)

        print(readme_text)


        # ==============================
        # 儲存 CSV
        # ==============================

        csv_file = "github_readme.csv"

        with open(
            csv_file,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "Repository",
                "Repository網址",
                "README.md內容"
            ])

            writer.writerow([
                repository_name,
                repo_url,
                readme_text
            ])

        print("\n" + "=" * 60)
        print("資料儲存完成")
        print("=" * 60)

        print("檔案：", csv_file)


    else:

        print("\n找不到 README.md")
        print("可能是 GitHub 網頁版面改變。")


finally:

    # ==============================
    # 關閉瀏覽器
    # ==============================

    time.sleep(2)

    driver.quit()

    print("\n瀏覽器已關閉。")

七、CSV 檔案

程式執行完成後會產生：

github_readme.csv


CSV 欄位如下：

Repository
Repository網址
README.md內容


例如：

Repository,Repository網址,README.md內容
Selenium,https://github.com/SeleniumHQ/selenium,......


程式使用：

encoding="utf-8-sig"


儲存 CSV，因此使用 Excel 開啟時可以避免中文亂碼問題。

八、使用的 Selenium 技術

本程式使用 Selenium 的：

webdriver.Chrome()


啟動 Chrome。

使用：

driver.get(repo_url)


開啟 GitHub Repository。

使用：

By.CSS_SELECTOR


尋找 README.md 的 HTML 元素。

使用：

WebDriverWait


等待網頁內容載入完成。

最後使用：

driver.quit()


關閉瀏覽器。

九、執行結果

執行 Python 程式後，Terminal 會顯示：

============================================================
GitHub README.md 爬蟲
============================================================

開啟 GitHub Repository...

尋找 README.md...

============================================================
Repository
============================================================

Selenium

============================================================
Repository URL
============================================================

https://github.com/SeleniumHQ/selenium

============================================================
README.md
============================================================

README.md 的內容會顯示在這裡

============================================================
資料儲存完成
============================================================

檔案： github_readme.csv

瀏覽器已關閉。

十、作業截圖
1. GitHub Repository 截圖

在瀏覽器開啟 GitHub Repository 後截圖。

截圖內容應包含：

GitHub Repository
README.md

2. Selenium 執行畫面

執行 Python 程式後，截取 Chrome 自動操作的畫面。

3. Terminal 執行結果

截取 VS Code Terminal：

GitHub README.md 爬蟲
Repository
Repository URL
README.md
資料儲存完成

4. CSV 結果

開啟：

github_readme.csv


截取 CSV 資料內容。

十一、遇到的問題
問題一：找不到 Selenium

如果出現：

ModuleNotFoundError: No module named 'selenium'


可以使用：

python3 -m pip install selenium


安裝 Selenium。

問題二：Pylance 顯示無法解析 selenium

確認 VS Code 使用的 Python Interpreter 與安裝 Selenium 的 Python 相同。

可以在 Terminal 執行：

python3 -c "import selenium; print(selenium.__version__)"


如果看到版本號，例如：

4.36.0


代表 Selenium 已經安裝成功。

問題三：CSV 中文亂碼

本程式使用：

encoding="utf-8-sig"


可以讓 Excel 開啟 CSV 時較不容易出現中文亂碼。

十二、心得

透過本次作業，我學習到如何使用 Selenium 與 WebDriver 自動控制 Chrome 瀏覽器。

與一般使用 requests 抓取 HTML 不同，Selenium 可以處理需要 JavaScript 載入的動態網頁，也可以模擬使用者點擊、輸入及瀏覽網頁。

本次實作中，我利用 Selenium 開啟 GitHub Repository，找到 README.md，取得其中的文字內容，最後再將資料儲存成 CSV 檔案。

透過這次實作，可以了解 Selenium 在動態網站資料擷取上的使用方式。

十三、結論

本作業成功使用 Python、Selenium 及 WebDriver 完成 GitHub README.md 資料擷取。

完成項目包括：

使用 Selenium
使用 WebDriver
開啟 GitHub
取得 Repository
擷取 README.md
顯示 README.md 內容
儲存 CSV
使用 UTF-8-SIG 避免中文亂碼

因此完成本題的 Selenium 動態網站資料擷取要求。

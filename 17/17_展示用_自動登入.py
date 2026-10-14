# ============================================================
# 第 17 題【展示用】：自動登入 GitHub，然後抓首頁上的兩個視窗文字

#ls "/Users/nasa/資料科學/17 github/chrome_profile/Default"

# ⚠ 這一份「不要交出去」，旁邊的 chrome_profile 資料夾也不要交或上傳。
#    資料夾和 cookie 裡存的是你的登入憑證，拿到的人不用密碼就能進你的 GitHub。
#    交作業請用 17_作業用.py。
#
# 這支程式怎麼做到「免輸入驗證碼」：
#   程式會把 Chrome 的資料存在旁邊的 chrome_profile 資料夾。
#   第一次執行時，你手動輸入一次驗證碼；之後 Chrome 會自己記得登入狀態，
#   再執行就直接是登入的，不用再輸入帳號、密碼、驗證碼。
#
# 名詞白話解釋：
#   cookie  = 網站發給瀏覽器的「通行證」。登入成功後 GitHub 會發一張，
#             瀏覽器之後每次開網頁都出示它，網站就知道你是誰、不用再登入。
#             Chrome 會自動把它存進 chrome_profile 資料夾。
#   驗證碼  = GitHub 發現你用「新的瀏覽器」登入，會寄 email 確認是不是本人。
#             只要帶著有效的通行證（cookie），就不會被問。
# ============================================================

import os                      # 讀環境變數、組合資料夾路徑
import time                    # 讓程式暫停幾秒
from getpass import getpass    # 輸入密碼時，畫面上不會顯示出密碼

from selenium import webdriver                              # 遙控瀏覽器的主角
from selenium.common.exceptions import TimeoutException     # 「等太久還是沒出現」的錯誤
from selenium.webdriver.common.by import By                 # 告訴 Selenium 用什麼方式找網頁上的東西
from selenium.webdriver.support import expected_conditions as EC   # 「等到某件事發生」的條件
from selenium.webdriver.support.ui import WebDriverWait            # 「最多等多久」的計時器

# ---------------- 準備瀏覽器 ----------------

# 決定「Chrome 資料夾」要放哪裡：就放在這支程式的旁邊，取名 chrome_profile。
# __file__ 是這支程式檔案的位置。用它來算路徑的好處是：
# 不管你從哪個資料夾執行程式，都會用到同一個 chrome_profile，不會到處產生新資料夾。
# 資料夾不存在的話，Chrome 會自動建立。
PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")

options = webdriver.ChromeOptions()   # 準備一份「開 Chrome 的設定單」

# 設定一：叫 Chrome 把自己的資料（包含登入 cookie）存到 PROFILE_DIR。
# 沒有這行的話，Selenium 每次都開一個「全新、什麼都不記得」的 Chrome，
# 所以每次都要重新登入、重新收驗證碼。
# 注意：同一時間只能有一個 Chrome 在用這個資料夾，
# 如果上一次的視窗還沒關，這次會開不起來，請先把它關掉。
options.add_argument(f"--user-data-dir={PROFILE_DIR}")

# 設定二：把「Chrome 目前正受到自動測試軟體控制」的黃色提示列藏起來，
# 展示的時候畫面比較乾淨。
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(options=options)   # 照著設定單打開 Chrome
driver.maximize_window()                     # 視窗最大化，頁面內容才看得到比較多
wait = WebDriverWait(driver, 15)             # 之後用 wait.until(...) 最多等 15 秒，網頁慢也不會太早放棄


def grab(title_text):
    """找到「標題文字是 title_text」的那個視窗，回傳 (標題, 整個視窗的文字)。

    為什麼要這麼做？我們只知道視窗的標題（例如 "GitHub for beginners on YouTube"），
    但想要的是「標題底下整塊內容」（標題 + 說明文字 + 按鈕文字）。
    所以做法是：先找到標題，再一層一層往「外面」找，直到找到把說明文字也包進去的那一層。"""

    # 第一步：找標題。下面這串 XPath 的意思是：
    #   「找一個元素，它的文字包含 title_text，而且它裡面的子元素沒有再包含這段文字」
    # 後半句是為了找到「最裡面那一層」。如果沒有這個條件，
    # 會找到包著整個網頁的大外框（因為整個網頁的文字當然也包含標題）。
    heading = wait.until(EC.presence_of_element_located(
        (By.XPATH, f"//*[contains(normalize-space(.), '{title_text}') and not(*[contains(normalize-space(.), '{title_text}')])]")))

    # 取得元素文字的小工具。用 textContent 的原因：
    # 有時候元素還在載入或被摺疊起來，一般的 .text 會讀到空白，textContent 讀得到。
    # split() 再 join 是把多餘的換行、空格整理成單純的一個空格。
    def full_text(el):
        return " ".join((el.get_attribute("textContent") or "").split())

    # 第二步：往外找。網頁的元素是一層包一層的，像俄羅斯娃娃。
    # 從標題開始，每次往外跳一層（".." 的意思就是「上一層」），最多跳 6 層。
    block = heading
    for _ in range(6):
        parent = block.find_element(By.XPATH, "..")
        # 如果上一層的文字比標題還多，代表這一層把說明文字也包進來了 → 就是我們要的區塊
        if len(full_text(parent)) > len(full_text(heading)):
            block = parent
            break
        # 還是只有標題而已，再往外跳一層繼續找
        block = parent
    # 優先用 .text（保留原本的換行，印出來比較好看）；讀不到才用 textContent 備用
    return full_text(heading), block.text.strip() or full_text(block)


def login_if_needed():
    """確認現在是登入狀態；還沒登入才走「輸入帳密」的流程。

    情況一：Chrome 記得上次的登入 → 直接略過，不用做任何事
    情況二：Chrome 不記得（例如第一次執行）→ 自動填帳號密碼，驗證碼請你手動輸入"""

    # 怎麼知道有沒有登入？故意先跑去「登入頁」看看：
    #   - 已經登入的人去登入頁，GitHub 會直接把你帶回首頁，網址就不會有 /login 了
    #   - 還沒登入的人，會停在登入頁，網址還是有 /login
    # 這個方法比去猜「首頁長什麼樣」可靠得多。
    driver.get("https://github.com/login")
    if "/login" not in driver.current_url:
        print("偵測到已登入（Chrome 記住了上次的登入狀態）")
        return

    # ---- 走到這裡，代表真的還沒登入，要自動填帳號密碼 ----
    # 帳號密碼一樣先讀環境變數，沒有的話才問你（輸入密碼時畫面不會顯示）
    username = os.environ.get("GITHUB_USER") or input("GitHub 帳號或 Email: ")
    password = os.environ.get("GITHUB_PASS") or getpass("GitHub 密碼: ")

    # 等帳號欄位出現（id 是 login_field），把帳號打進去
    wait.until(EC.presence_of_element_located((By.ID, "login_field"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)   # 密碼欄位，打入密碼
    driver.find_element(By.NAME, "commit").click()               # 按下綠色的 Sign in 按鈕

    # 按完登入後，GitHub 可能會要你輸入 email 驗證碼。這個程式沒辦法替你收信，
    # 所以請你自己在瀏覽器裡輸入。程式在這裡等，最多等 180 秒（3 分鐘）。
    print("若瀏覽器要求 email 驗證碼，請手動輸入（只需要這一次）...")
    try:
        # 每隔一小段時間檢查一次網址：
        # 網址不再有 /login 和 sessions，就代表你驗證成功、已經登入了，可以繼續。
        WebDriverWait(driver, 180).until(
            lambda d: "/login" not in d.current_url and "sessions" not in d.current_url)
    except TimeoutException:
        # 等了 3 分鐘網址還是沒變 → 可能密碼打錯，或你沒有輸入驗證碼 → 直接結束程式
        raise SystemExit("登入失敗：帳號密碼錯誤或驗證逾時")


# ============================================================
# 主程式從這裡開始
# try ... finally 的意思：不管中間有沒有出錯，最後 finally 裡的事一定會做
# （這裡是「把瀏覽器關掉」，避免出錯時留下一堆沒關的 Chrome 視窗）
# ============================================================
try:
    # ---------- 步驟一：登入 ----------
    login_if_needed()    # 檢查有沒有登入，沒有才輸入帳密
    driver.get("https://github.com/")   # 登入完成，前往 GitHub 首頁

    # ---------- 步驟二：抓 1 號視窗 (Create your first code project) ----------
    try:
        title, text = grab("Create your first code project")
        print("=== 1 號視窗 ===")
        print(text)
    except TimeoutException:
        # 找不到不代表程式壞掉：這個視窗只有「還沒建立過任何 repository」的帳號才會顯示。
        # 找不到時，順便把當下的網頁存下來，之後可以打開檢查實際畫面長什麼樣。
        print("找不到 1 號視窗（此帳號可能已有 repository，不會顯示）")
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)           # 存整個網頁的原始碼
        driver.save_screenshot("dashboard.png")   # 存一張螢幕截圖
        print("頁面文字前 800 字：")
        print(driver.find_element(By.TAG_NAME, "body").text[:800])   # 印出網頁開頭的文字，看個大概

    # ---------- 步驟三：抓 2 號視窗（改抓 Playlist 卡片） ----------
    # 老師截圖裡的 Updates to your homepage feed 公告，新版首頁已經沒有了，
    # 所以改抓畫面上同位置、標題是 "GitHub for beginners on YouTube" 的卡片。
    try:
        title, text = grab("GitHub for beginners on YouTube")
        print("\n=== 2 號視窗 (Playlist) ===")
        print(text)
    except TimeoutException:
        # 這張卡片右上角有 X，被關掉之後就不會再顯示
        print("找不到 2 號視窗（Playlist 可能已被關閉或不顯示）")

    time.sleep(5)   # 展示用：多停 5 秒，讓觀眾看清楚最後的畫面，再關掉瀏覽器
finally:
    # 關閉瀏覽器。登入狀態已經存在 chrome_profile 資料夾裡，關掉不會消失，
    # 下次執行還是會記得。
    driver.quit()

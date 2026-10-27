# ============================================================
# 第 17 題【2FA 版】：用 2FA 密鑰自動算驗證碼，全自動登入 GitHub，
#                    然後抓首頁上的兩個視窗文字
#
# ⚠ 這一份要搭配旁邊的 .env 檔使用。.env 裡放的是 2FA 密鑰，
#    「.env 不要交出去、不要上傳、不要截圖」。
#    這支程式檔本身沒有任何帳號密碼，可以放心交。
#
# 事前準備（只需要做一次）：
#   1. pip install selenium pyotp
#   2. 到 GitHub：Settings → Password and authentication
#      → Two-factor authentication → Authenticator app
#      設定時畫面上有一串「setup key（密鑰）」，把它填進 .env 的 GITHUB_TOTP_SECRET
#   3. 打開 .env，填入 GITHUB_TOTP_SECRET
#
# 執行時的流程：
#   1. 終端機會問你帳號、密碼（密碼輸入時畫面不會顯示）
#   2. 輸入完，Chrome 視窗才會打開
#   3. 程式自動填帳號密碼，並用 2FA 密鑰自動算驗證碼填入
#
# 這支程式怎麼自動輸入驗證碼：
#   手機上的驗證 App（Google Authenticator 之類）每 30 秒換一組 6 位數字，
#   它是用「密鑰」加上「現在時間」算出來的。
#   pyotp 這個套件做的是一模一樣的計算，所以程式也能算出同一組數字，
#   不用你看手機、不用你手動輸入。
# ============================================================

import os                      # 讀環境變數、組合檔案路徑
import time                    # 讓程式暫停幾秒
from getpass import getpass    # 輸入密碼時，畫面上不會顯示出密碼

from selenium import webdriver                              # 遙控瀏覽器的主角
from selenium.common.exceptions import (
    TimeoutException,                # 「等太久還是沒出現」的錯誤
    StaleElementReferenceException,  # 「抓到的元素已經因為換頁而失效」的錯誤
)
from selenium.webdriver.common.by import By                 # 告訴 Selenium 用什麼方式找網頁上的東西
from selenium.webdriver.common.keys import Keys             # 模擬鍵盤按鍵（例如 Enter）
from selenium.webdriver.support import expected_conditions as EC   # 「等到某件事發生」的條件
from selenium.webdriver.support.ui import WebDriverWait            # 「最多等多久」的計時器

try:
    import pyotp   # 用 2FA 密鑰算出 6 位數驗證碼的套件
except ImportError:
    raise SystemExit("還沒安裝 pyotp，請先在終端機執行：pip install pyotp")


# ---------------- 讀取 .env 設定檔 ----------------

def load_env(path):
    """讀 .env 檔，把裡面「名字=值」的每一行放進環境變數。

    .env 檔長這樣：
        GITHUB_TOTP_SECRET=2FA密鑰
    以 # 開頭的是註解，會略過。
    如果電腦的環境變數已經設過同名的，就以電腦的為主，不會被 .env 蓋掉。"""
    if not os.path.exists(path):
        return   # 沒有 .env 也沒關係，後面會直接報錯提醒
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue   # 空行、註解、格式不對的行，都略過
            name, value = line.split("=", 1)       # 只切第一個 =，值裡面有 = 也不會壞
            os.environ.setdefault(name.strip(), value.strip().strip('"').strip("'"))


# .env 放在這支程式的旁邊。用 __file__ 算路徑，不管從哪個資料夾執行都找得到。
load_env(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# 2FA 密鑰從 .env 讀。
# GitHub 顯示的密鑰常常中間有空格、是小寫；統一去掉空格、轉大寫，才能被正確計算
totp_secret = os.environ.get("GITHUB_TOTP_SECRET", "").replace(" ", "").upper()
if not totp_secret:
    raise SystemExit("請先打開旁邊的 .env，填入 GITHUB_TOTP_SECRET（GitHub 2FA 的 setup key）")

# 帳號、密碼：在終端機輸入。
# 這一步一定要在「打開 Chrome」之前，所以你輸入完，瀏覽器視窗才會出現。
# `A or B` 的意思：A 有值就用 A，沒有才用 B。
# 所以如果你之後想省事，把 GITHUB_USER / GITHUB_PASS 設成環境變數也行，就不會再問。
username = os.environ.get("GITHUB_USER") or input("GitHub 帳號或 Email: ")
password = os.environ.get("GITHUB_PASS") or getpass("GitHub 密碼（輸入時不會顯示）: ")
print("開始自動登入...")


# ---------------- 準備瀏覽器 ----------------

options = webdriver.ChromeOptions()
# 關掉 Chrome 自己的「要不要儲存密碼 / passkey」彈窗
options.add_experimental_option("prefs", {
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False,
})
options.add_argument("--disable-save-password-bubble")
driver = webdriver.Chrome(options=options)   # 打開 Chrome（新版 Selenium 會自動下載需要的驅動程式）
driver.maximize_window()              # 視窗最大化，頁面內容才看得到比較多
wait = WebDriverWait(driver, 30)      # 之後用 wait.until(...) 最多等 30 秒，網路慢也不會太早放棄


def wait_page_loaded():
    """等到網頁完全載入完成，再多緩衝 1 秒（網路慢時，避免抓得太快）。"""
    WebDriverWait(driver, 30).until(
        lambda d: d.execute_script("return document.readyState") == "complete")
    time.sleep(1)


def dismiss_save_prompt():
    """如果 GitHub 跳出「要不要儲存 passkey」的提示，自動點 Ask me later。沒有出現就略過。"""
    try:
        btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
            (By.XPATH, "//*[self::button or self::a or self::summary][contains(normalize-space(.), 'Ask me later')]")))
        btn.click()
        print("已自動點擊 Ask me later")
        time.sleep(1)
    except TimeoutException:
        pass   # 沒有彈窗，不是錯誤


def grab(title_text):
    """找到「標題文字是 title_text」的那個視窗，回傳 (標題, 整個視窗的文字)。

    為什麼要這麼做？我們只知道視窗的標題（例如 "GitHub for beginners on YouTube"），
    但想要的是「標題底下整塊內容」（標題 + 說明文字 + 按鈕文字）。
    所以做法是：先找到標題，再一層一層往「外面」找，直到找到把說明文字也包進去的那一層。"""

    # 第一步：找標題。XPath 的意思是
    #   「找一個元素，它的文字包含 title_text，而且它裡面的子元素沒有再包含這段文字」
    # 後半句是為了找到「最裡面那一層」，不然會抓到包著整個網頁的大外框。
    heading = wait.until(EC.presence_of_element_located(
        (By.XPATH, f"//*[contains(normalize-space(.), '{title_text}') and not(*[contains(normalize-space(.), '{title_text}')])]")))

    # 取得元素文字的小工具。用 textContent 的原因：
    # 有時候元素還在載入或被摺疊起來，一般的 .text 會讀到空白，textContent 讀得到。
    # split() 再 join 是把多餘的換行、空格整理成單純的一個空格。
    def full_text(el):
        return " ".join((el.get_attribute("textContent") or "").split())

    # 第二步：往外找。網頁的元素是一層包一層的，像俄羅斯娃娃。
    # 從標題開始每次往外跳一層（".." 就是「上一層」），最多跳 6 層。
    block = heading
    for _ in range(6):
        parent = block.find_element(By.XPATH, "..")
        # 如果上一層的文字比標題多，代表這一層把說明文字也包進來了 → 就是我們要的區塊
        if len(full_text(parent)) > len(full_text(heading)):
            block = parent
            break
        block = parent   # 還是只有標題而已，再往外跳一層繼續找
    # 等這個區塊「真的顯示出來」而且文字穩定（連續 1.5 秒都沒變）才抓，
    # 避免網路慢、卡片還在載入（轉圈）時就抓到不完整的內容。
    # 這裡只用 .text（只會讀到看得見的文字、保留換行），不用 textContent 備用。
    # 順便把區塊捲到畫面中間，讓你在瀏覽器上看得到程式抓的是哪一塊
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", block)
    last, stable_since = None, time.time()
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            current = block.text.strip() if block.is_displayed() else ""
        except StaleElementReferenceException:
            current = ""   # 頁面剛重繪，元素失效了，下一輪再試
        if current != last:
            last, stable_since = current, time.time()
        elif current and time.time() - stable_since >= 1.5:
            return full_text(heading), current
        time.sleep(0.3)
    raise TimeoutException(f"視窗「{title_text}」一直沒有穩定顯示")


def still_logging_in(d):
    """網址還在登入相關頁面（登入頁、2FA 驗證頁）就回傳 True。"""
    url = d.current_url
    return "/login" in url or "sessions" in url or "two-factor" in url


def fresh_totp_code():
    """算出「現在這一刻」的 6 位數驗證碼。

    驗證碼每 30 秒換一次。如果這一組只剩不到 3 秒就過期，
    等你填進去、按下送出時可能已經失效，所以先等它換下一組再算。"""
    totp = pyotp.TOTP(totp_secret)
    seconds_left = 30 - (time.time() % 30)   # 這一組驗證碼還剩幾秒
    if seconds_left < 3:
        time.sleep(seconds_left + 1)         # 等下一組出來
    return totp.now()


def login():
    """自動登入：填帳號密碼 → 如果要 2FA，自動算驗證碼填進去。"""

    # ---- 第一步：填帳號、密碼 ----
    driver.get("https://github.com/login")
    wait.until(EC.presence_of_element_located((By.ID, "login_field"))).send_keys(username)
    driver.find_element(By.ID, "password").send_keys(password)   # 密碼欄位，打入密碼
    driver.find_element(By.NAME, "commit").click()               # 按下綠色的 Sign in 按鈕

    # ---- 第二步：如果被要求輸入驗證碼，自動算出來填進去 ----
    # 登入成功的話，網址會離開 /login 和 sessions；
    # 如果帳號有開 2FA，會停在 two-factor 頁面等你輸入驗證碼。
    if "two-factor" in driver.current_url or still_logging_in(driver):
        try:
            # 找驗證碼的輸入框。GitHub 的驗證碼欄位 id 是 app_totp（驗證 App）或 otp（其他驗證碼）。
            code_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#app_totp, #otp, input[name='app_totp'], input[name='otp']")))
            code_box.send_keys(fresh_totp_code())   # 把算出來的 6 位數打進去
            # GitHub 在輸入滿 6 碼的那一刻會「自動送出」並換頁，
            # 這時候原本抓到的輸入框就失效了，再對它按 Enter 會出現 StaleElementReferenceException。
            # 所以：還在原頁面就按 Enter 送出；已經自動換頁就略過，不是錯誤。
            try:
                code_box.send_keys(Keys.ENTER)
            except StaleElementReferenceException:
                pass   # 頁面已經自動送出並換頁了，不用再按
        except TimeoutException:
            # 10 秒內沒看到驗證碼欄位：可能是密碼打錯，也可能是 GitHub 要你做別的驗證
            print("沒有出現驗證碼欄位，請看瀏覽器畫面；若要手動處理，30 秒內完成...")

    # ---- 第三步：確認登入成功 ----
    # 每隔一小段時間檢查一次網址：離開登入相關頁面，就代表登入成功了。
    try:
        WebDriverWait(driver, 60).until(lambda d: not still_logging_in(d))
    except TimeoutException:
        # 等了一分鐘還是沒離開 → 可能是帳號、密碼、2FA 密鑰有一個填錯 → 直接結束程式
        raise SystemExit("登入失敗：請檢查 .env 裡的帳號、密碼、2FA 密鑰是否正確")
    # 網址離開登入頁不代表真的登入了（例如被 GitHub 暫時封鎖時也會跳走），
    # 所以再確認頁面裡有「已登入的使用者名稱」。
    dismiss_save_prompt()   # 登入後可能跳出「儲存 passkey」的詢問
    driver.get("https://github.com/")
    wait_page_loaded()
    user_meta = driver.find_elements(By.CSS_SELECTOR, "meta[name='user-login']")
    if not user_meta or not user_meta[0].get_attribute("content"):
        raise SystemExit("登入失敗：網頁顯示尚未登入（可能被 GitHub 暫時封鎖，或 2FA 密鑰不對），請稍後再試")
    print("登入成功")


# ============================================================
# 主程式從這裡開始
# try ... finally 的意思：不管中間有沒有出錯，最後 finally 裡的事一定會做
# （這裡是「把瀏覽器關掉」，避免出錯時留下一堆沒關的 Chrome 視窗）
# ============================================================
try:
    # ---------- 要求 1：自動登入 ----------
    login()
    driver.get("https://github.com/")   # 登入完成，前往 GitHub 首頁
    wait_page_loaded()
    dismiss_save_prompt()               # 首頁若又跳出詢問，也一併關掉
    time.sleep(3)                       # 網路慢時，多給首頁的卡片一點載入時間

    # ---------- 要求 2：1 號視窗（左側的 No repositories found） ----------
    try:
        title, text = grab("No repositories found")
        print("=== 1 號視窗 ===")
        print(text)
    except TimeoutException:
        # 這個視窗只有「還沒建立過任何 repository」的帳號才會顯示，找不到不是程式壞掉。
        # 順便把當下的網頁存下來，之後可以打開檢查實際畫面長什麼樣。
        print("找不到 1 號視窗（此帳號可能已有 repository，左側不會顯示 No repositories found）")
        with open("dashboard.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)           # 存整個網頁的原始碼
        driver.save_screenshot("dashboard.png")   # 存一張螢幕截圖
        print("頁面文字前 800 字：")
        print(driver.find_element(By.TAG_NAME, "body").text[:800])   # 印出網頁開頭的文字，看個大概

    # ---------- 要求 3：2 號視窗（改抓 Playlist 卡片） ----------
    # 老師截圖裡的 Updates to your homepage feed 公告，新版首頁已經沒有了，
    # 所以改抓畫面上同位置、標題是 "GitHub for beginners on YouTube" 的卡片。
    try:
        title, text = grab("GitHub for beginners on YouTube")
        print("\n=== 2 號視窗 (Playlist) ===")
        print(text)
    except TimeoutException:
        # 這張卡片右上角有 X，被關掉之後就不會再顯示
        print("找不到 2 號視窗（Playlist 可能已被關閉或不顯示）")

    time.sleep(2)   # 完成後停 2 秒，再關掉瀏覽器
finally:
    driver.quit()   # 關閉瀏覽器

import time

from selenium import webdriver

URL = "https://news.google.com/home?hl=zh-TW&gl=TW&ceid=TW:zh-Hant"

# 區塊標題（依頁面出現順序），遇到其他標題（如「為你精選」）則停止收集
SECTIONS = ["焦點新聞", "地方新聞", "您的主題", "更多新聞"]

# 在頁面上依 DOM 順序走訪標題與新聞連結，把每則新聞歸到它前面最近的區塊
JS = """
const names = arguments[0];
const nodes = document.querySelectorAll('h1, h2, h3, a.gPFEn, a.JtKRv');
const result = {};
let current = null;
for (const n of nodes) {
    if (n.tagName === 'A') {
        const t = n.innerText.trim();
        if (current && t && !result[current].includes(t)) result[current].push(t);
    } else {
        const t = n.innerText.trim();
        if (names.includes(t)) { current = t; result[t] = result[t] || []; }
        else if (n.tagName !== 'H3' || !current || current !== '您的主題') {
            // 非已知區塊的標題（例如「為你精選」、「焦點提要」）
            current = null;
        }
        // 「您的主題」底下的 h3（台灣、國際...）是子主題，仍算在您的主題內
    }
}
return result;
"""

print("啟動 Chrome...")
driver = webdriver.Chrome()
driver.set_window_size(1400, 1000)
try:
    print("載入 Google 新聞，約需 15 秒...")
    driver.get(URL)
    time.sleep(5)
    # 捲動頁面，讓下方區塊載入
    for _ in range(8):
        driver.execute_script("window.scrollBy(0, 2500)")
        time.sleep(1)

    data = driver.execute_script(JS, SECTIONS)

    focus = ["焦點新聞", "地方新聞"]
    print("焦點提要：", focus)
    for name in SECTIONS:
        titles = data.get(name, [])
        print(f"\n{name}：({len(titles)} 則)")
        for t in titles:
            print("  -", t)
finally:
    driver.quit()

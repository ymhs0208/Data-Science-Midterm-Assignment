import csv  # Python 內建函式庫：用於讀寫 CSV 檔案
from urllib.parse import (  # 用於將相對路徑轉換為完整的絕對 URL
    urljoin,
)
from bs4 import (  # 第三方解析工具：用於從 HTML 中搜尋與提取資料
    BeautifulSoup,
)
import requests  # 第三方網路請求工具：用於發送 HTTP GET 請求取得網頁

# 設定 HTTP 請求標頭（偽裝成一般 Chrome 瀏覽器，避免被網站阻擋或識別為爬蟲）
headers = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
}

# 建立 Session 物件維持連線狀態，並套用預設的 Request Headers
session = requests.Session()
session.headers.update(headers)

# ==========================================
# 步驟 0：從題目指定網址出發
# ==========================================
start_url = 'http://www.atmovies.com.tw/movie/new/'
print(f'正在訪問起始網址: {start_url}...')

# 向起始網址發送 GET 請求
res_start = session.get(start_url)
# 設定文字編碼為 utf-8，確保中文字元解析正常不亂碼
res_start.encoding = 'utf-8'
# 使用 BeautifulSoup 解析 HTML 網頁結構
soup_start = BeautifulSoup(res_start.text, 'html.parser')

# ==========================================
# 要求 1：在選單中找出「票房排行榜」的超連結
# ==========================================
boxoffice_link = None
# 遍歷頁面中所有帶有 href 屬性的超連結 <a> 標籤
for a in soup_start.find_all('a', href=True):
  # 檢查超連結文字是否包含「票房排行榜」
  if '票房排行榜' in a.get_text():
    # 使用 urljoin 將抓到的相對路徑轉換為完整網址
    boxoffice_link = urljoin(start_url, a['href'])
    break

# 防呆機制：若網頁結構異動未抓到文字，則帶入開眼電影票房排行榜首頁
if not boxoffice_link:
  boxoffice_link = 'https://app2.atmovies.com.tw/boxoffice/'

print(f'找到「票房排行榜」連結: {boxoffice_link}')

# ==========================================
# 要求 2：訪問票房排行榜頁面，並尋找「台北週末」區塊的 more 連結
# ==========================================
res_boxoffice = session.get(boxoffice_link)
res_boxoffice.encoding = 'utf-8'
soup_boxoffice = BeautifulSoup(res_boxoffice.text, 'html.parser')

more_link = None
# 遍歷票房排行榜首頁的所有超連結
for a in soup_boxoffice.find_all('a', href=True):
  # 尋找文字為「more」且網址路徑中含有「twweekend」（代表台北週末排行榜）的連結
  if 'more' in a.get_text(strip=True).lower() and 'twweekend' in a['href']:
    more_link = urljoin(boxoffice_link, a['href'])
    break

# 防呆機制：若未抓到 more 連結，帶入完整的台北週末排行榜網址
if not more_link:
  more_link = 'https://app2.atmovies.com.tw/boxoffice/twweekend/'

print(f'找到 more 連結: {more_link}')

# ==========================================
# 要求 3：進入 more 完整榜單頁面，擷取前 20 筆資料
# ==========================================
res_more = session.get(more_link)
res_more.encoding = 'utf-8'
soup_more = BeautifulSoup(res_more.text, 'html.parser')

movies_data = []  # 建立空清單，用於存放爬取到的電影資料字典

# 尋找頁面中所有的表格列 <tr> 標籤
for tr in soup_more.find_all('tr'):
  # 找出該列中所有的欄位標籤（包含 td 與 th）
  tds = tr.find_all(['td', 'th'])
  # 擷取每個欄位的文字內容並去除頭尾空白字元
  row = [td.get_text(strip=True) for td in tds]

  # 判斷是否為有效資料列：第一欄存在且純數字（代表排行 1, 2, 3...）
  if row and row[0].isdigit():
    rank = row[0]  # 第一欄：排名
    title = row[1]  # 第二欄：片名
    this_week = row[2]  # 第三欄：本週票房
    total = row[3]  # 第四欄：累計票房

    # 將抓取到的資料組成字典加入清單
    movies_data.append({
        '排名': rank,
        '片名': title,
        '本週票房': this_week,
        '累計票房': total,
    })

    # 符合題目要求：抓滿前 20 筆就中斷迴圈停止抓取
    if len(movies_data) == 20:
      break

# ==========================================
# 終端機格式化印出預覽（對齊欄位）
# ==========================================
print('\n【台北週末票房排行榜 TOP 20】')
print(f"{'排名':<5} {'片名':<35} {'本週票房':<12} {'累計票房':<12}")
print('-' * 70)
for m in movies_data:
  # 限制片名預覽長度最長顯示 30 字，避免長片名導致排版錯位
  print(
      f"{m['排名']:<5} {m['片名'][:30]:<35} {m['本週票房']:<12}"
      f" {m['累計票房']:<12}"
  )

# ==========================================
# 將資料寫入 CSV 檔案
# ==========================================
csv_file = 'Taipei_movies.csv'

# 開啟/建立檔案：
# - newline=''：防止在 Windows 系統寫入時出現多餘的空行
# - encoding='utf-8-sig'：加入 BOM 標記，確保微軟 Excel 開啟不會產生中文亂碼
with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
  # 定義 CSV 欄位名稱標頭
  fieldnames = ['排名', '片名', '本週票房', '累計票房']
  writer = csv.DictWriter(f, fieldnames=fieldnames)

  writer.writeheader()  # 寫入第一列表頭
  writer.writerows(movies_data)  # 寫入前 20 筆電影資料

print(f'\n已成功抓取 {len(movies_data)} 筆資料並寫入 {csv_file}！')
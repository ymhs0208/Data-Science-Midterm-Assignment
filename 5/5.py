import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # 讓 CSV 等輸出檔存在此資料夾

import csv  # Python 內建函式庫：用於讀寫 CSV 檔案
import unicodedata  # 內建：判斷全形/半形字元寬度，用於中英文對齊
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


def get_soup(url):
  """發送 GET 請求並回傳解析後的 BeautifulSoup 物件。"""
  res = session.get(url)
  res.encoding = 'utf-8'  # 確保中文字元解析正常不亂碼
  return BeautifulSoup(res.text, 'html.parser')


def clean(text):
  """將多餘的換行、空白壓成單一空白。"""
  return ' '.join(text.split())


def display_width(text):
  """計算字串在終端機的顯示寬度（全形字佔 2 格）。"""
  return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)


def pad(text, width, align='left'):
  """依顯示寬度補空白，讓中英文混排時欄位仍然對齊。"""
  space = ' ' * max(width - display_width(text), 0)
  return space + text if align == 'right' else text + space


def fit(text, width):
  """片名過長時依顯示寬度截斷並加上省略號。"""
  if display_width(text) <= width:
    return text
  out = ''
  for c in text:
    if display_width(out + c) > width - 1:
      break
    out += c
  return out + '…'


def print_table(rows, title_width=52):
  """格式化印出排行榜：排名 / 片名 / 本週票房 / 累計票房（單位：萬新台幣）。"""
  line = '-' * (6 + title_width + 2 + 12 + 2 + 12)
  print(
      pad('排名', 6) + pad('片名', title_width + 2)
      + pad('本週票房', 12, 'right') + '  ' + pad('累計票房', 12, 'right')
  )
  print(line)
  for m in rows:
    print(
        pad(m['排名'], 6) + pad(fit(m['片名'], title_width), title_width + 2)
        + pad(m['本週票房'], 12, 'right') + '  '
        + pad(m['累計票房'], 12, 'right')
    )


# ==========================================
# 步驟 0：從題目指定網址出發
# ==========================================
start_url = 'http://www.atmovies.com.tw/movie/new/'
print(f'正在訪問起始網址: {start_url}')
soup_start = get_soup(start_url)

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
# 要求 2：票房排行榜首頁的「台北週末票房」前 5 名（排名、片名、票房）
# ==========================================
soup_boxoffice = get_soup(boxoffice_link)

more_a = None
# 尋找文字為「more」且網址路徑中含有「twweekend」（代表台北週末排行榜）的連結
for a in soup_boxoffice.find_all('a', href=True):
  if 'more' in a.get_text(strip=True).lower() and 'twweekend' in a['href']:
    more_a = a
    break

# 防呆機制：若未抓到 more 連結，帶入完整的台北週末排行榜網址
if more_a:
  more_link = urljoin(boxoffice_link, more_a['href'])
else:
  more_link = 'https://app2.atmovies.com.tw/boxoffice/twweekend/'

print(f'找到 more 連結: {more_link}')

top5 = []
if more_a:
  # more 連結所在的表格就是台北排行榜；原始 HTML 的 <TR> 沒有關閉，
  # 因此不依賴列，改為依序讀取該表格內所有 <td>，每 3 格為一部電影
  cells = [clean(td.get_text()) for td in more_a.find_parent('table').find_all('td')]
  for i, cell in enumerate(cells):
    if cell.isdigit() and i + 2 < len(cells):
      top5.append({
          '排名': cell,
          '片名': cells[i + 1],
          '本週票房': cells[i + 2].replace('萬台幣', '').lstrip('$'),
      })

print('\n【台北週末票房排行榜（首頁前 5 名，單位：萬新台幣）】')
print(f"{pad('排名', 6)}{pad('片名', 54)}{pad('本週票房', 12, 'right')}")
print('-' * 72)
for m in top5:
  print(
      f"{pad(m['排名'], 6)}{pad(fit(m['片名'], 52), 54)}"
      f"{pad(m['本週票房'], 12, 'right')}"
  )

# ==========================================
# 要求 3：按下 more，進入完整榜單頁面，擷取前 20 筆資料
# ==========================================
soup_more = get_soup(more_link)

# 每部電影在 HTML 中拆成兩段（<TR> 未關閉，無法用列判斷）：
#   第 1 段：<td><b>排名</b></td><td>片名</td>
#   第 2 段：<td>&nbsp;</td><td>佔比%</td><td>本週票房</td><td>累計票房</td>...
# 所以改為依序掃描 <td>：遇到「<b>數字</b>」就往後取對應欄位。
tds = soup_more.find_all('td')
movies_data = []  # 建立空清單，用於存放爬取到的電影資料字典

for i, td in enumerate(tds):
  rank = clean(td.get_text())
  # 排名欄的特徵：內含 <b> 標籤且文字為純數字
  if td.find('b') is None or not rank.isdigit() or i + 5 >= len(tds):
    continue

  movies_data.append({
      '排名': rank,
      '片名': clean(tds[i + 1].get_text()),
      # tds[i + 2] 是空白欄、tds[i + 3] 是票房佔比（%），略過
      '本週票房': clean(tds[i + 4].get_text()).lstrip('$'),
      '累計票房': clean(tds[i + 5].get_text()).lstrip('$'),
  })

  # 符合題目要求：抓滿前 20 筆就中斷迴圈停止抓取
  if len(movies_data) == 20:
    break

print('\n【台北週末票房排行榜 TOP 20（單位：萬新台幣）】')
print_table(movies_data)

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

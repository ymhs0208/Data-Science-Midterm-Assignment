import requests                 # 匯入 requests 套件，用於發送 HTTP 網路請求
from bs4 import BeautifulSoup   # 匯入 BeautifulSoup 套件，用於解析 HTML 網頁結構
import csv                      # 匯入 csv 套件，用於將抓取到的資料寫入 CSV 檔案
import time                     # 匯入 time 套件，用於設定延遲時間，避免請求過快被網站封鎖

# 1. 定義要抓取的三支 NBA 球隊縮寫清單
teams = ["CLE", "HOU", "GSW"]

# 2. 定義目標網址模板，其中的 {0} 會在迴圈中替換成各球隊的縮寫
base_url = "https://www.basketball-reference.com/teams/{0}/2024.html"

# 設定 HTTP 請求標頭 (User-Agent)，偽裝成一般使用者的 Chrome 瀏覽器，降低被阻擋的機率
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

# 建立一個空串列，用來存放所有球隊的球員資料
all_players = []

# 3. 使用迴圈依序處理每一支球隊
for team in teams:
    # 使用 .format(team) 將網址中的 {0} 替換成目前的球隊代碼 (例如 CLE)
    url = base_url.format(team)
    print(f"正在抓取 {team} 的球員資料，網址：{url}")
    
    # 發送 GET 請求取得網頁內容
    response = requests.get(url, headers=headers)
    # 設定網頁編碼為 utf-8，確保特殊字元或外國球員姓名不會變成亂碼
    response.encoding = "utf-8"
    
    # 檢查請求是否成功 (狀態碼 200 代表成功)
    if response.status_code != 200:
        print(f"無法取得 {team} 網頁，狀態碼：{response.status_code} (若為 403 代表被防爬蟲擋住，請改用下方 Selenium 方法)")
        continue
    
    # 將網頁原始碼交給 BeautifulSoup 進行解析
    soup = BeautifulSoup(response.text, "html.parser")
    
    # 找到 id 為 "roster" (球員名單) 的表格 (<table>)
    roster_table = soup.find("table", id="roster")
    
    # 如果找不到該表格，則跳過這支球隊
    if not roster_table:
        print(f"找不到 {team} 的球員名單表格！")
        continue
        
    # 找到表格中的 <tbody> (資料本體區塊)，並抓取裡面所有的資料列 (<tr>)
    rows = roster_table.find("tbody").find_all("tr")
    
    # 4. 逐列解析每一位球員的各項數據
    for row in rows:
        # (1) 抓取「背號」：在該列中尋找 data-stat="number" 的 <th> 標籤
        num_tag = row.find("th", {"data-stat": "number"})
        number = num_tag.text.strip() if num_tag else ""
        
        # (2) 抓取「姓名」：尋找 data-stat="player" 的 <td> 標籤
        # 注意：有些雙向合約球員名字後面會帶有 "(TW)"，若只需純姓名可進一步用 .replace("(TW)", "").strip() 清理
        player_tag = row.find("td", {"data-stat": "player"})
        name = player_tag.text.strip() if player_tag else ""
        
        # (3) 抓取「位置」：尋找 data-stat="pos" 的 <td> 標籤
        pos_tag = row.find("td", {"data-stat": "pos"})
        pos = pos_tag.text.strip() if pos_tag else ""
        
        # (4) 抓取「體重」：尋找 data-stat="weight" 的 <td> 標籤
        weight_tag = row.find("td", {"data-stat": "weight"})
        weight = weight_tag.text.strip() if weight_tag else ""
        
        # (5) 抓取「生日」：尋找 data-stat="birth_date" 的 <td> 標籤
        birth_tag = row.find("td", {"data-stat": "birth_date"})
        birth_date = birth_tag.text.strip() if birth_tag else ""
        
        # (6) 抓取「經驗」：尋找 data-stat="years_experience" 的 <td> 標籤 (R 代表新秀 Rookie)
        exp_tag = row.find("td", {"data-stat": "years_experience"})
        experience = exp_tag.text.strip() if exp_tag else ""
        
        # (7) 抓取「大學」：尋找 data-stat="college" 的 <td> 標籤
        college_tag = row.find("td", {"data-stat": "college"})
        college = college_tag.text.strip() if college_tag else ""
        
        # 將這名球員的 8 項資料整理成一個串列，並加入 all_players 總清單中
        all_players.append([
            team,        # 球隊 (CLE / HOU / GSW)
            number,      # 背號
            name,        # 姓名
            pos,         # 位置
            weight,      # 體重
            birth_date,  # 生日
            experience,  # 經驗
            college      # 大學
        ])
        
    # 每抓完一支球隊暫停 3 秒，遵守爬蟲禮儀並避免觸發網站的頻率限制
    time.sleep(3)

# 5. 將所有抓取到的球員資料寫入 players.csv 檔案中
# 使用 utf-8-sig 編碼，確保使用 Excel 開啟 CSV 時中文標題與特殊外文字母不會亂碼
with open("players.csv", mode="w", newline="", encoding="utf-8-sig") as file:
    # 建立 CSV 寫入器物件
    writer = csv.writer(file)
    
    # 寫入第一列：欄位標題 (依照題目要求的順序)
    writer.writerow(["球隊", "背號", "姓名", "位置", "體重", "生日", "經驗", "大學"])
    
    # 將所有球員資料一次寫入 CSV
    writer.writerows(all_players)

print(f"成功抓取共 {len(all_players)} 位球員資料，並已儲存至 players.csv！")
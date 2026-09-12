# Python 網頁爬蟲期中作業

 ## 一、期中作業要求

 ### 繳交方式

 期中作業需繳交：

 - Word
- PPT（報告）

 ### Word 報告內容

 Word 必須包含：

 1. 題目
2. Python 程式碼
3. 程式執行完成截圖
4. 執行結果截圖
5. CSV 或其他輸出檔案結果截圖（若題目有要求）

---

 ## 二、爬蟲技術與配分

 ### 要求 1：使用 Requests 抓取資料

 - 共 2 題
- 20 分

 ### 要求 2：使用 BeautifulSoup 抓取資料

 - 共 2 題
- 30 分

 ### 要求 3：使用 Selenium 抓取動態網站資料

 - 共 2 題
- 50 分

---

 # 三、題目

 ## 1.（易）抓取電影資訊

 網址：

 http://www.atmovies.com.tw/movie/new/

 ### 要求

 抓取本週新片電影資料，包括：

 - 電影標題
- 電影內容
- 片長
- 電影網址

---

 ## 2.（中）抓取台灣銀行牌告匯率

 網址：

 https://rate.bot.com.tw/xrt?Lang=zh-TW

 ### 要求

 1. 抓取台銀牌價最新掛牌資料。
2. 將資料存入：

```
bank.csv
```

---

 ## 3.（中）抓取政府資料開放平台

 網址：

 https://data.gov.tw/

 ### 要求

 1. 抓取「健保門診及住院就診人次統計-腸病毒」資料。
2. 將資料儲存至：

```
NHI_EnteroviralInfection.csv
```

---

 ## 4.（中）抓取博客來書籍資料

 網址：

 https://search.books.com.tw/search/query/key/{0}/cat/all

 ### 要求

 1. `{0}` 設定為：

```
演算法
```

 2. 抓取書籍資料。
3. 將資料存入：

```
booklist.csv
```

 ### CSV 內容

 必須包含：

```
書名
網址
作者
書價
```

---

 ## 5.（難）抓取電影票房排行榜

 網址：

 http://www.atmovies.com.tw/movie/new/

 ### 要求

 1. 按票房排行榜。
2. 列出台北排行榜。
3. 列出：
   - 排名
   - 片名
   - 票房
4. 按下「More」後取得本頁排行。
5. 本頁共 20 筆資料。
6. 儲存至：

```
Taipei_movies.csv
```

 ### CSV 內容

```
排名
片名
本週票房
累計票房
```

---

 ## 6.（難）抓取 NBA 球員資料

 網址：

 https://www.basketball-reference.com/teams/{0}/2024.html

 ### 要求

 抓取以下三支球隊：

```
CLE
HOU
GSW
```

 ### 資料內容

 必須包含：

```
球隊
背號
姓名
位置
體重
生日
經驗
大學
```

 ### 輸出檔案

```
players.csv
```

---

 ## 7.（難）使用 Google Books API 抓取書籍資料

 API：

 https://www.googleapis.com/books/v1/volumes

 ### 要求

 使用以下參數：

```
import requests

url = "https://www.googleapis.com/books/v1/volumes"

url_params = {
    'q': 'Python',
    'maxResults': 10,
    'projection': 'lite'
}

r = requests.get(url, params=url_params)

print(r.json())
```

 ### 資料要求

 1. 使用 Google Books API。
2. 將第一頁資料存入：

```
pythonbook.csv
```

 3. 進入下一頁。
4. 再將第二頁資料存入：

```
pythonbook.csv
```

 5. 共取得兩頁資料。

---

 ## 8.（難）抓取近期上映強片電影

 網址：

 http://www.atmovies.com.tw/movie/new/

 ### 要求

 1. 列出所有近期上映強片電影。
2. 列出：
   - 電影名稱
   - 上映時間
   - 連結網址
3. 將資料儲存至：

```
movies.csv
```

---

 ## 9.（中）使用 Selenium 抓取 Google 新聞

 網站：

 Google 新聞

 ### 要求

 使用 Selenium 完成以下需求。

 ### 焦點提要

 列出：

```
焦點新聞
地方新聞
```

 ### 焦點新聞

 列出所有包含的新聞標題。

 ### 地方新聞

 列出所有包含的新聞標題。

 ### 您的主題

 列出所有包含的新聞標題。

 ### 更多新聞

 列出所有包含的新聞標題。

---

 ## 10.（中）使用 Selenium 抓取 PTT Gossiping

 網址：

 https://www.ptt.cc/bbs/Gossiping/index.html

 ### 要求

 1. 使用 Selenium 解決網站分級問題。
2. 列出網站 Title。

 例如：

```
批踢踢實業坊
```

 3. 列出該網站文章列表。

 ### 文章資料

 每筆資料包括：

```
網址
標題
作者
```

 ### 範例

```
/bbs/Gossiping/M.1704514524.A.426.html
Re: [新聞] 國三車禍台積電副理下車搖燈示警被撞身亡
topahot9303

/bbs/Gossiping/M.1704514550.A.7F5.html
[問卦] 有沒有從小培養性別刻板印象的卦
D122

/bbs/Gossiping/M.1704514568.A.7DB.html
[新聞] 薛瑞元遭爆密會綠營高層 侯友宜：串證、
ciqinz

/bbs/Gossiping/M.1704514570.A.573.html
[問卦] 今天小寒因該喝什麼湯暖身體？
ME13
```

---

 ## 11.（難）抓取 NBA 商品資料

 網址：

 https://fchart.github.io/ML/nba\_items.html

 ### 要求

 1. 列出「所有」NBA 商品資料。
2. 每存完一個 CSV 檔，就印出該頁編號。

 例如：

```
儲存頁面: 1
儲存頁面: 2
儲存頁面: 3
```

 3. 不同分頁必須儲存成不同 CSV 檔案。
4. CSV 檔案名稱格式：

```
NBA_Products1.csv
NBA_Products2.csv
NBA_Products3.csv
...
```

 5. CSV 開啟時不能出現中文亂碼。

---

 ## 12.（難）使用 Selenium 搜尋 Google 的 Steam 遊戲推薦

 ### 要求

 從 Google 搜尋：

```
Steam 遊戲推薦
```

 ### 使用工具

 - Selenium
- WebDriver

 ### 資料要求

 1. 列出搜尋結果。
2. 列出搜尋結果的超連結。
3. 將資料儲存至 CSV 檔案。

---

 ## 13.（中）抓取 momo 搜尋頁

 網址：

 https://www.momoshop.com.tw/main/Main.jsp?cid=memb&oid=back2hp&mdiv=1099800000-bt\_0\_150\_01-bt\_0\_150\_01\_e1&ctype=B

 ### 要求

 1. 自動輸入：

```
nba
```

 2. 將結果網頁儲存成：

```
NBA_test.html
```

---

 ## 14.（難）抓取 NBA 球員薪水

 網址：

 https://hoopshype.com/salaries/players

 ### 要求

 使用：

 - Selenium
- BeautifulSoup

 ### 要求一

 抓取前 3 位高薪球員的基本資料。

 包括：

```
名字
背號
薪資
```

 儲存至：

```
highest.csv
```

 ### 要求二

 抓取本頁表格所有內容。

 儲存至：

```
all_play.csv
```

---

 ## 15.（難）使用 Google 搜尋 XPath

 網址：

 https://www.google.com

 ### 要求

 1. 使用 WebDriver。
2. 在 Google 搜尋列輸入：

```
xpath
```

 3. 使用 XPath 提取搜尋結果。
4. 滾動滑鼠取得全部資料。
5. 列印本頁資訊。
6. 按下「更多結果」。
7. 取得更多搜尋資訊。
8. 將結果儲存至：

```
xpath.csv
```

---

 ## 16.（難）抓取 Agoda 搜尋資料

 網址：

 https://www.agoda.com/zh-tw/

 ### 要求

 1. 輸入：

```
台中
```

 2. 抓取搜尋結果頁面。
3. 將資料存入：

```
agoda_result.csv
```

 ### CSV 內容

 包括：

```
飯店名
價格
```

 ### 加分

 使用：

 - Selenium
- WebDriver

 自動輸入：

```
台中
```

 並將結果加入 CSV。

---

 ## 17.（難）抓取 GitHub README.md 資料

 網站：

 https://github.com/

 ### 要求

 1. 使用 Selenium。
2. 使用 WebDriver。
3. 自動操作 GitHub。
4. 搜尋指定 Repository。
5. 進入 Repository。
6. 找到 `README.md`。
7. 抓取 README.md 的內容。
8. 列出 Repository 資料。
9. 列出 README.md 資料。
10. 將抓取結果儲存至 CSV。

 ### 建議資料

```
Repository
Repository網址
README.md內容
```

 ### 輸出檔案

```
github_readme.csv
```

---

 # 四、作業報告格式

 ## Word

 Word 報告應包含：

 ### 1\. 題目

 完整列出所選題目的內容與要求。

 ### 2\. 使用工具

 說明使用：

```
Python
Requests
BeautifulSoup
Selenium
WebDriver
```

 ### 3\. 程式碼

 貼上完整 Python 程式碼。

 ### 4\. 程式執行畫面

 放入 Terminal 執行結果截圖。

 ### 5\. 網頁操作截圖

 放入爬蟲程式執行時的網頁畫面。

 ### 6\. 輸出結果

 放入 CSV、HTML 或其他輸出檔案的結果截圖。

---

 # 五、PPT 報告

 PPT 建議包含：

 1. 封面
2. 作業題目
3. 使用技術
4. 程式流程
5. 程式碼重點
6. 網頁爬蟲結果
7. CSV 結果
8. 執行畫面
9. 問題與解決方法
10. 心得
11. 結論

---

 # 六、使用技術分類

 | 題號 | 題目 | 難度 | 主要技術 |
| --- | --- | --- | --- |
| 1 | 電影新片 | 易 | Requests / BeautifulSoup |
| 2 | 台銀牌告 | 中 | Requests / BeautifulSoup |
| 3 | 政府資料開放平台 | 中 | Requests / BeautifulSoup |
| 4 | 博客來書籍 | 中 | Requests / BeautifulSoup |
| 5 | 電影票房 | 難 | Selenium / BeautifulSoup |
| 6 | NBA 球員 | 難 | Requests / BeautifulSoup |
| 7 | Google Books API | 難 | Requests |
| 8 | 近期上映強片 | 難 | Requests / BeautifulSoup |
| 9 | Google 新聞 | 中 | Selenium |
| 10 | PTT Gossiping | 中 | Selenium |
| 11 | NBA 商品 | 難 | Requests / BeautifulSoup |
| 12 | Steam 遊戲推薦 | 難 | Selenium |
| 13 | momo 搜尋 | 中 | Selenium |
| 14 | NBA 球員薪資 | 難 | Selenium + BeautifulSoup |
| 15 | Google XPath | 難 | Selenium |
| 16 | Agoda | 難 | Selenium |
| 17 | GitHub README.md | 難 | Selenium |

---

 # 七、檔案命名整理

 各題要求的輸出檔案：

```
bank.csv
NHI_EnteroviralInfection.csv
booklist.csv
Taipei_movies.csv
players.csv
pythonbook.csv
movies.csv
NBA_Products1.csv
NBA_Products2.csv
NBA_Products3.csv
...
xpath.csv
agoda_result.csv
highest.csv
all_play.csv
github_readme.csv
NBA_test.html
```

---

 # 八、完成檢查表

 - [ ] 已選擇符合要求的題目
- [ ] Requests 題目至少 2 題
- [ ] BeautifulSoup 題目至少 2 題
- [ ] Selenium 題目至少 2 題
- [ ] Python 程式可以正常執行
- [ ] 已完成資料抓取
- [ ] CSV 可以正常開啟
- [ ] CSV 中文沒有亂碼
- [ ] Word 已放入題目
- [ ] Word 已放入完整程式碼
- [ ] Word 已放入執行截圖
- [ ] Word 已放入結果截圖
- [ ] PPT 已完成報告
- [ ] PPT 已加入程式執行結果
- [ ] PPT 已加入爬蟲結果

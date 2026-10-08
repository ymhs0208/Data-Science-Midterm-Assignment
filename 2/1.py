import pandas as pd
import requests
from bs4 import BeautifulSoup

url = "https://rate.bot.com.tw/xrt?Lang=zh-TW"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    )
}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

table = soup.find("table", {"title": "牌告匯率"})
rows = table.find("tbody").find_all("tr")

data = []
for row in rows:
  currency = (
      row.find("div", class_="visible-phone print_hide")
      .text.strip()
      .replace("\n", "")
  )
  tds = row.find_all("td")
  cash_buy = tds[1].text.strip()
  cash_sell = tds[2].text.strip()
  spot_buy = tds[3].text.strip()
  spot_sell = tds[4].text.strip()

  data.append({
      "幣別": currency,
      "現金買入": cash_buy,
      "現金賣出": cash_sell,
      "即期買入": spot_buy,
      "即期賣出": spot_sell,
  })

df = pd.DataFrame(data)
df.to_csv("bank.csv", index=False, encoding="utf-8-sig")
print("bank.csv 下載完成！")
import pandas as pd
import bs4
import httpx


url = "https://ru.wikipedia.org/wiki/Список_городов_России"
page = httpx.get(url)
soup = bs4.BeautifulSoup(page.content, "html.parser")

tables = soup.find_all("table")
table = tables[0]

df = pd.read_html(str(table))[0]
df = df[["Город", "Регион", "Федеральный округ"]]
df = df.rename(columns={"Город": "city", "Регион": "region", "Федеральный округ": "fed_dist"})

f_o = df[["fed_dist"]].drop_duplicates().reset_index(drop=True)
f_o["id"] = f_o.index + 1

f_o.to_csv("districts.csv", index=False)

regions = df[["region", "fed_dist"]].drop_duplicates().reset_index(drop=True)
regions = regions.merge(f_o, on="fed_dist", how="left")
regions = regions.rename(columns={"id": "fed_id"})
regions = regions.drop(columns=["fed_dist"])
regions["id"] = regions.index + 1

regions.to_csv("regions.csv", index=False)

city = df[["city", "region", "fed_dist"]].drop_duplicates().reset_index(drop=True)
city = city.merge(regions, on="region", how="left")
city = city.rename(columns={"id": "region_id"})
city = city.drop(columns=["region", "fed_dist"])
city["id"] = city.index + 1

city.to_csv("cities.csv", index=False)

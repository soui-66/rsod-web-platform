import random
import time
from fake_useragent import UserAgent
import requests
from lxml import etree
import pandas as pd


class SteamSpider:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.session()
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Cookie': 'browserid=2814215431655073515; timezoneOffset=28800,0; _ga_SNYKG5G01T=GS1.1.1685343114.1.1.1685343133.0.0.0; _ga_ZG5GHM9QF2=GS1.1.1685343145.1.1.1685343234.0.0.0; ak_bmsc=DADF68D88BB5F961C62B7EE97FB54B7C~000000000000000000000000000000~YAAQKdo4fRvXz5KIAQAAWMiglBToQcU3vHjgpXqX36DDGUr0wOxtA1S8tCHBJ84PFvcY56py9vdPkPz5fJAmuYhJ++C8ts9iCwd656QJuXXMgI248NGHoE/x8guTWZP6Bo4xE3Xq9PX3/bvFU6Z+694y2xTu02dQtJVwsYV+LG3r0Kzo/PIHps4u1WiUK4hyC/2N4Y3wVNZa9E0RK6CBAt9bwWhVfd4yXZuJDrZcStHod6RHdKc0CIBBvom7t+vU5KNTtY01+G5QtpVxAbotTtB6qI8LzZ5lbOGtPIKlwf/lMBdglYkwVIsgk0ZKlxX7WHVTRg806/tFJYaSFes3EneYONri6PdjoDck36Jeo0e2LCbxYo6Sb2G6RHUzfkmA4nN431uF; steamLoginSecure=76561198274291976%7C%7CeyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0.eyAiaXNzIjogInI6MENEMF8yMURBOTI4MF82M0EwOCIsICJzdWIiOiAiNzY1NjExOTgyNzQyOTE5NzYiLCAiYXVkIjogWyAid2ViIiBdLCAiZXhwIjogMTY4NjIwNzk5MiwgIm5iZiI6IDE2Nzc0ODA3NDQsICJpYXQiOiAxNjg2MTIwNzQ0LCAianRpIjogIjBEMTBfMjJBOTU0RTNfRUI3OEYiLCAib2F0IjogMTY3Mjg4NTEyNiwgInJ0X2V4cCI6IDE2OTEyNDExMjgsICJwZXIiOiAwLCAiaXBfc3ViamVjdCI6ICIxMDMuMTcwLjI2LjQxIiwgImlwX2NvbmZpcm1lciI6ICIxMDMuMTcwLjI2LjQxIiB9.7rDETf66d-YJ4IvcQ6BIK_OOHUpBSYgnYrk0oC_MZ3v18I6V61iBkDOINT5S8hyZHu7wuUWmqOzJ4sZaRb9eAQ; sessionid=95da73a4ff7c020af38a7917; deep_dive_carousel_method=default; _ga=GA1.2.1570816889.1668782694; _gid=GA1.2.974329537.1686120752; steamCountry=JP%7C016ff88b16ac42ed14827c84a40dea72; deep_dive_carousel_focused_app=992300; recentapps=%7B%22730%22%3A1686121771%2C%221774880%22%3A1686121697%2C%221593350%22%3A1685343142%2C%221371630%22%3A1685343111%7D; app_impressions=570@1_7_7_7000_150_1|952060@1_7_7_7000_150_1|2231010@1_7_7_7000_150_1|381210@1_7_7_7000_150_2|1794470@1_7_7_7000_150_2|2179300@1_7_7_7000_150_2|568220@1_7_7_7000_150_2|1367080@1_7_7_7000_150_1|1364780@1_7_7_7000_150_1|1172470@1_7_7_7000_150_1|578080@1_7_7_7000_150_1|730@1_7_7_7000_150_1|1174180@1_7_7_7000_150_1|359550@1_7_7_7000_150_1|1938090@1_7_7_7000_150_1',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': self.ua.random,
        }
        self.session.headers = self.headers

    def load_cookies(self, file_path='./cookie.txt'):
        manual_cookies = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            cookies_txt = f.read().split(';')
            for item in cookies_txt:
                name, value = item.strip().split('=', 1)
                manual_cookies[name] = value
        cookies_jar = requests.utils.cookiejar_from_dict(manual_cookies, cookiejar=None, overwrite=True)
        self.session.cookies = cookies_jar

    @staticmethod
    def parse_data(req):
        page = etree.HTML(req.text)
        items = page.xpath('//*[@id="search_resultsRows"]/a')
        data = []
        for item in items[:5]:
            data.append([
                '&'.join(item.xpath('./@href')),
                '&'.join(item.xpath('./div[2]/div[1]/span/text()')),
                '&'.join(item.xpath('./div[2]/div[2]/text()')),
                '&'.join(item.xpath('./div[2]/div[1]/div/span/@class')),
                '&'.join(item.xpath('./div[2]/div[3]/span/@data-tooltip-html')),
                '&'.join(item.xpath('./div[2]/div[4]/div[1]/span/text()')),
                '&'.join(item.xpath('./div[2]/div[4]/div[2]/span/strike/text()')),
                '&'.join(item.xpath('./div[2]/div[4]/div[2]/text()')),
            ])
        return data

    def get_data(self, url):
        try:
            req = self.session.get(url)
            req.raise_for_status()
            return self.parse_data(req)
        except requests.HTTPError as e:
            print(f"Failed to get data from {url}. Error: {e}")
            return []

    def scrape_pages(self, start_page, end_page):
        dataframes = []
        for i in range(start_page, end_page+1):
            url = f'https://store.steampowered.com/search/?sort_by=_ASC&force_infinite=1&supportedlang=schinese&snr=1_7_7_7000_7&filter=topsellers&page={i}'
            data = self.get_data(url)
            print(f"第{i}页数据采集完成,共有{len(data)}条信息")
            if data:
                df = pd.DataFrame(data, columns=['game_link', 'game_name', 'game_date', 'game_platform', 'game_comment', 'game_discord', 'original_price', 'game_price'])
                dataframes.append(df)
            time.sleep(random.randint(1,5))
        return pd.concat(dataframes, axis=0)

    def run(self, start_page=1, end_page=4, save_path='./test.csv'):
        self.load_cookies()
        dfs = self.scrape_pages(start_page, end_page)
        dfs.to_csv(save_path, index=False, encoding='utf-8')
        print(f"All data saved to {save_path}")


if __name__ == '__main__':
    spider = SteamSpider()
    spider.run()

import datetime
from collections import namedtuple
import bs4
import requests
import urllib.parse
import csv

InnerBlock = namedtuple('Block', 'title,engcapacity,price,currency,date,url')


class Block(InnerBlock):
    def __str__(self):
        return f'{self.title}\t{self.engcapacity}\t{self.price} {self.currency}\t{self.date}\t{self.url}'


class AvitoParser:

    def __init__(self, proxy):
        self.proxy = proxy
        self.proxy_succeed = False
        self.proxy_success = {}
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'Accept-Language': 'ru',
        }

    def check_html(self, file):
        line = file.find("Доступ с вашего IP-адреса временно ограничен")
        return line != 1

    def get_page(self, page: int = None):
        params = {
            'radius': 100,
            'user': 1,
            'pmax': 500000,
            'pmin': 50000,
            'f': 'ASgBAQECAkTyCrCKAZ4SoLgCAUDwChSsigEDRfgCGHsiZnJvbSI6ODk4LCJ0byI6NDA1MjQyfbwVGXsiZnJvbSI6MTU3ODYsInRvIjoxNTgzMX2~FRl7ImZyb20iOjE1NDgzLCJ0byI6MTU1MjR9'
        }
        if page and page > 1:
            params['p'] = page

        url = 'https://www.avito.ru/ufa/avtomobili/levyy_rul-ASgCAQICAUDwChSsigE'
        if len(self.proxy) != 0 and self.proxy_succeed == False:
            for p in self.proxy:
                try:
                    print('ставлю прокси по %s' % p)
                    self.proxy_success = {'http': '%s' % p, 'https': '%s' % p}
                    r = self.session.get(
                        url, params=params, proxies=self.proxy_success)
                    if self.check_html(r.text):
                        print("Прокси не работает. Retry")
                        continue
                    else:
                        self.proxy_succeed = True
                        return r.text
                except Exception as e:
                    print("proxy doesn't work. Retry"+str(e))
                    continue
        elif self.proxy_succeed == True:
            r = self.session.get(url, params=params,
                                 proxies=self.proxy_success)
            return r.text
        else:
            r = self.session.get(url, params=params)
            return r.text

    def get_pagination_limit(self):
        text = self.get_page()
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('a.pagination-page')
        last_button = container[-1]
        href = last_button.get('href')
        if not href:
            return 1
        r = urllib.parse.urlparse(href)
        params = urllib.parse.parse_qs(r.query)
        print(params)
        return int(params['p'][0])

    def parse_block(self, item):
        # Block with url
        url_block = item.select_one('a.snippet-link')
        # print(url_block)
        href = url_block.get('href')
        if href:
            url = 'https://www.avito.ru'+href
        else:
            url = None

        # Selecting block with Name
        title_block = item.select_one('h3.snippet-title span')
        title = title_block.string.strip()

        # engine capacity block
        cap = item.select_one('div.specific-params.specific-params_block')
        engcapacity = cap.string.strip().split(', ')[1]
        # Block with name and currency
        price_block = item.select_one(
            'span.snippet-price').get_text('\n').strip()
        price_block = list(price_block.rsplit(' ', maxsplit=1))
        if len(price_block) == 2:
            price, currency = price_block
        else:
            price, currency = None, None
            print('Проблема со считыванием цены и валюты: ', price_block)

        # Datetime block
        date = None
        date_block = item.select_one('div.snippet-date-info')
        absolute_date = date_block.get('data-tooltip')
        if (absolute_date == ''):
            absolute_date = date_block.get_text().strip()
        date = self.parse_date(item=absolute_date)
        return Block(
            url=url,
            title=title,
            price=price,
            currency=currency,
            date=date,
            engcapacity=engcapacity,
        )

    def get_blocks(self, page=1):
        text = self.get_page(page=page)
        soup = bs4.BeautifulSoup(text, 'lxml')

        # CSS container selector selection
        container = soup.select(
            'div.snippet-horizontal.item.item_table.clearfix.js-catalog-item-enum.item-with-contact.js-item-extended')
        for item in container:
            block = self.parse_block(item=item)

            print(block)

    def get_blocks_to_csv(self, page=1):
        text = self.get_page(page=page)
        soup = bs4.BeautifulSoup(text, 'lxml')

        # CSS selector selection
        container = soup.select(
            'div.snippet-horizontal.item.item_table.clearfix.js-catalog-item-enum.item-with-contact.js-item-extended')
        with open('avito.csv', 'a', encoding='utf8') as f:
            writer = csv.writer(f)
            for item in container:
                block = self.parse_block(item=item)
                writer.writerow((block))

    @staticmethod
    def parse_date(item):
        params = item.split(' ')
        if len(params) == 3:
            day, month_ru, time = params
            day = int(day)
            months_map = {
                'января': 1,
                'февраля': 2,
                'марта': 3,
                'апреля': 4,
                'мая': 5,
                'июня': 6,
                'июля': 7,
                'августа': 8,
                'сентября': 9,
                'октября': 10,
                'ноября': 11,
                'декабря': 12,
            }
            month = months_map.get(month_ru)
            if not month:
                print("Не можем определить месяц: ", item)
                return
            today = datetime.datetime.today()
            time = datetime.datetime.strptime(time, '%H:%M')
            return datetime.datetime(day=day, month=month, year=today.year, hour=time.hour, minute=time.minute)
        else:
            print("Не могу разобрать формат: ", item)
            return

        print('sss')

    def parse_all(self):
        limit = self.get_pagination_limit()
        print(f'Всего страниц: {limit}')

        for i in range(1, limit+1):
            # self.get_blocks(page=i)
            self.get_blocks_to_csv(page=i)



def main():
    proxy = []
    with open("proxy.txt", "r") as myfile:
        try:
            data = myfile.readlines()
            for each in data:
                proxy.append(each.replace('\n', '').replace('\r', ''))
        except:
            pass
    p = AvitoParser(proxy=proxy)
    p.parse_all()
    print('Работа закончена!')


if __name__ == "__main__":
    main()

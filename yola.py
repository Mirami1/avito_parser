from utils import Parser, Block
import time
import bs4
import requests
import urllib.parse
import csv
from datetime import timedelta, datetime
import re
from dateutil.relativedelta import relativedelta
class YolaRuParser(Parser):

    def __init__(self, proxy=[]):
        super(YolaRuParser, self).__init__(proxy=proxy)
        self.ready_url=None
    def check_html(self, file):
        line = file.find("Доступ с вашего IP-адреса временно ограничен")
        return line != 1

    def set_up(self, url):
        self.url = url

    def get_page(self, page: int = 1):
        params = {
            'yearMin': 2005,
            'yearMax': 2019,
            'priceMin': 50000,
            'priceMax': 500000,
            'mileageMax': 100000,
            'carState':'notBroken',
            'wheelTypes%5B0%5D':1,
            'pts':3,
            'sellers':1,
            'page':1,
        }
        if page and page > 1:
            params['page']=page
        
        if len(self.proxy) != 0 and self.proxy_succeed == False:
            for p in self.proxy:
                try:
                    print('ставлю прокси по %s' % p)
                    self.proxy_success = {'http': '%s' % p, 'https': '%s' % p}
                    r = self.session.get(
                        self.url, params=params, proxies=self.proxy_success)
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
            r = self.session.get(self.url, params=params,
                                 proxies=self.proxy_success)
            return r.text
        else:
            r = self.session.get(self.url, params=params)
            if page==1:
                self.ready_url=r.url
            return r.text
        
        

    def get_pagination_limit(self):
        text = self.get_page()
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select_one('div.Paginator_total__oFW1n').get_text().split(' ')
        page=int(container[1])
        return page

    def parse_block(self, item):
        
        urlblock=item.select_one('a[data-target="serp-snippet-title"]')
        url = urlblock.get('href')

        # Selecting block with Name

        title = urlblock.get('title').strip()

        # engine transmission power block
        transmission=item.select_one('div[data-target-id="serp-snippet-gear-type"]').get_text()
        power=item.select_one('div[data-target-id="serp-snippet-engine-power"]').get_text()
        engcapacity = item.select_one('div[data-target-id="serp-snippet-engine-vol-type"]').get_text().split(', ')[0].replace(',','')
        

        

        # Block with price
        price= item.select_one(
            'div[data-target="serp-snippet-price"]').get_text('\n').strip()
        currency='₽'
       


        # Datetime block
        date = None
        date_block = item.select_one('div[data-target="serp-snippet-actual-date"]').get_text()
        date = self.parse_date(item=date_block)
        return Block(
            url=url,
            title=title,
            price=price,
            currency=currency,
            date=date,
            engcapacity=engcapacity,
            transmission=transmission,
            power=power
        )

    def get_blocks(self, page=1,file=0):
        text = self.get_page(page=page)
        soup = bs4.BeautifulSoup(text, 'lxml')

        # CSS container selector selection
        container=soup.select('article[data-target=serp-snippet]')
        if(file):
             with open('yola_ru.csv', 'a', encoding='utf8') as f:
                writer = csv.writer(f)
                for item in container:
                    block = self.parse_block(item=item)
                    writer.writerow((block))
        else:
            for item in container:
                block = self.parse_block(item=item)
                print(block)

    @staticmethod
    def parse_date(item):
        if 'минут назад' in item or 'минуты назад' in item or 'минуту назад' in item:
            params = item.split(' ')
            minuts=int(params[1])
            today = datetime.now()-timedelta(minutes=minuts)
            return today.strftime("%Y-%m-%d %I:%M")
        if 'день назад' in item:
            today = datetime.now()-timedelta(days=1)
            return today.strftime("%Y-%m-%d")
        if 'дня назад' in item or 'дней назад' in item:
            params = item.split(' ')
            day=int(params[1])
            today = datetime.now()-timedelta(days=day)
            return today.strftime("%Y-%m-%d")
        if 'час назад' in item:
            today = datetime.now()-timedelta(hours=1)
            return today.strftime("%Y-%m-%d %I:%M")
        if 'часа назад' in item or 'часов назад' in item:
            params = item.split(' ')
            hour=int(params[1])
            today = datetime.now()-timedelta(hours=hour)
            return today.strftime("%Y-%m-%d %I:%M")
        if 'месяц назад' in item:
            today = datetime.now()-relativedelta(months=1)
            return today.strftime("%Y-%m-%d")
        elif 'месяца назад' or 'месяцев назад' in item:
            params = item.split(' ')
            month=int(params[1])
            today=datetime.now()-relativedelta(months=month)
            return today.strftime("%Y-%m-%d")          
        else:
            print("Не могу разобрать формат: ", item)
            return


    def parse_all(self):
        limit = self.get_pagination_limit()
        print(self.ready_url)
        print(f'Всего страниц: {limit}')

        for i in range(1, limit+1):
            self.get_blocks(page=i,file=1)
            print("Страница",i)
        
        
       


def main():
    proxy = []
    with open("proxy.txt", "a+") as myfile:
        try:
            data = myfile.readlines()
            for each in data:
                proxy.append(each.replace('\n', '').replace('\r', ''))
        except:
            pass
    p = YolaRuParser(proxy=proxy)
    p.set_up(url='https://auto.youla.ru/ufa/cars/used/')
    p.parse_all()
    print('Работа закончена!')
    


if __name__ == "__main__":
    main()
from utils import Parser, Block
import time
import bs4
import requests
import urllib.parse
import csv
from datetime import timedelta, datetime
import re
class DromRuParser(Parser):

    def __init__(self, proxy=[]):
        super(DromRuParser, self).__init__(proxy=proxy)
        self.page=1

    def check_html(self, file):
        line = file.find("Доступ с вашего IP-адреса временно ограничен")
        return line != 1

    def set_up(self, url):
        self.url = url

    def get_page(self, page: int = 1):
        params = {
            'minyear': 2005,
            'maxyear': 2019,
            'minprice': 50000,
            'maxprice': 500000,
            'maxprobeg': 100000,
            'mv': 1.6,
            'damaged':'2',
            'pts':'2',
            'unsold':'1',
            'isOwnerSells':'1',
            'seller_group': 'PRIVATE',
            'owners_count_group': 'LESS_THAN_TWO',
            'steering_wheel': 'LEFT',
            'distance': '100',
        }
        if page and page > 1:
            self.page=page
        
        url=self.url+str(page)+'/'
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
            r = self.session.get(url, params=params,
                                 proxies=self.proxy_success)
            return r.text
        else:
            r = self.session.get(url, params=params)
            return r.text

    def get_pagination_limit(self):
        text = self.get_page()
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('a.css-grspv8.ena3a8q0')
        last_button = container[-1]
        href = last_button.get('href')
        if not href:
            return 1
        r = urllib.parse.urlparse(href)
        page=re.findall('\d+',r.path)
        params = urllib.parse.parse_qs(r.query)
        print(page[0])
        return int(page[0])

    def parse_block(self, item):
        
        url = item.get('href')

        # Selecting block with Name
        title_block = item.select_one('span[data-ftid=bull_title]')
        title = title_block.string.strip()

        # engine transmission power block
        cap = item.select('span.css-xyj9u2.e162wx9x0')
        s=cap[0].get_text().split(' ')
        engcapacity = s[0]+s[1]
        transmission=cap[2].get_text().replace(',','')
        power=s[2].replace('(', '')+" "+s[3].replace('),', '')

        

        # Block with price
        price= item.select_one(
            'span[data-ftid=bull_price]').get_text('\n').strip()
        currency='₽'
       


        # Datetime block
        date = None
        date_block = item.select_one('div[data-ftid=bull_date]').get_text()
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
        container=soup.select('div.css-10ib5jr.e93r9u20')
        container = container[0].select(
            'a.css-sew97f.erw2ohd2')
        if(file):
             with open('drom_ru.csv', 'a', encoding='utf8') as f:
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
        if 'часа назад' in item or 'часов назад' in item:
            params = item.split(' ')
            hour=int(params[0])
            today = datetime.now()-timedelta(hours=hour)
            return today.strftime("%Y-%m-%d %I:%M")
        elif 'сегодня' or 'час назад' in item:
            today=datetime.now()
            return today.strftime("%Y-%m-%d")          
        params = item.split(' ')
        if len(params) == 2:
            day, month_ru = params
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
            return datetime(day=day, month=month,year=datetime.now().year).strftime("%Y-%m-%d")  
        else:
            print("Не могу разобрать формат: ", item)
            return

        print('sss')

    def parse_all(self):
        limit = self.get_pagination_limit()
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
    p = DromRuParser(proxy=proxy)
    p.set_up(url='https://ufa.drom.ru/auto/all/page')
    p.parse_all()
    print('Работа закончена!')
    


if __name__ == "__main__":
    main()
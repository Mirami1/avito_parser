from utils import Parser, Block
import time
import bs4
import requests
import urllib.parse
import csv
import datetime
import json
class AutoRuParser(Parser):
# using json file from site, not from site itself
    def __init__(self, proxy=[]):
        super(AutoRuParser, self).__init__(proxy=proxy)
        self.HEADERS = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Length': '277',
            'content-type': 'application/json',
            'Cookie': '_csrf_token=ba2a2c72516632b7eaeaedf0ff563aac63b8ed104b02faa4; autoru_sid=a%3Ag5f1b2aaa2mrst99er3d525ru8bunsuq.9bfe18fca55ec59820fe7d3c467df400%7C1595615914490.604800.d9VfKO1O4syxXWbe4JFgeQ.nCFHGFhmM0bGE0RBm26wFhC-YkNvS9EymRz_J0RodLI; autoruuid=g5f1b2aaa2mrst99er3d525ru8bunsuq.9bfe18fca55ec59820fe7d3c467df400; suid=202ca01b7e93bca6c04dde580b17be28.ce9ad3ca28b66f15b5112f0f1bf1f716; from=direct; yuidcs=1; X-Vertis-DC=sas; crookie=p8jEV20ajVHcZzaZtbDwxRlu/gm/3ZttShonJWdc1CoBbItZ3qsO9ingjgo8gM4pjOiofSUZC8f6BKzwAlBIbD4kdS0=; cmtchd=MTU5NTYxNTAyODQzNw==; gids=172; bltsr=1; yuidlt=1; yandexuid=4037150261581187515; my=YwA%3D; counter_ga_all7=2; gradius=200; listing_view_session={%22sort_offers%22:%22fresh_relevance_1-DESC%22}; listing_view=%7B%22version%22%3A1%7D; from_lifetime=1595637374278',
            'Host': 'auto.ru',
            'origin': 'https://auto.ru',
            'Referer': '',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
            'x-client-app-version': '202007.24.093900',
            'x-client-date': '1595636518287',
            'x-csrf-token': 'ba2a2c72516632b7eaeaedf0ff563aac63b8ed104b02faa4',
            'x-page-request-id': '535f7d1e82f92fd2fad1b8e4f08c7aa2',
            'x-requested-with': 'fetch'
        }
    def set_up(self, url):
        self.url = url
    
    

    def check_html(self, file):
        line = file.find(
            "Продолжая использование данного сайта, я соглашаюсь с тем, что обработка моих данных будет осуществляться в соответствии с законодательством Российской Федерации.")
        return line != -1

    def get_page(self, page: int = None):
        params = {
            'year_from': 2005,
            'year_to': 2019,
            'price_from': 50000,
            'price_to': 500000,
            'km_age_to': 100000,
            'seller_group': 'PRIVATE',
            'owners_count_group': 'LESS_THAN_TWO',
            'steering_wheel': 'LEFT',
            'geo_radius': '100',
            'page': '1'
        }
        if page and page > 1:
            params['page'] = page
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
            self.HEADERS['Referer'] = r.url
            # URL to get json file
            url_to_json = 'https://auto.ru/-/ajax/desktop/listing/'
            resp = self.session.post(
                url_to_json, json=params, headers=self.HEADERS)
            data = resp.json()
            if page==1:
                print(r.url)
            return r.text, data['offers']

    def get_pagination_limit(self):
        text = self.get_page()[0]
        soup = bs4.BeautifulSoup(text, 'lxml')
        container = soup.select('a.Button')
        last_button = container[-3]
        href = last_button.get('href')
        if not href:
            return 1
        r = urllib.parse.urlparse(href)
        params = urllib.parse.parse_qs(r.query)
        print(params)
        return int(params['page'][0])

    def parse_block(self, data):

        url = 'https://auto.ru/cars/used/sale/'+data['vehicle_info']['mark_info']['code'].lower(
        )+'/' + data['vehicle_info']['model_info']['code'].lower()+'/'+data['saleId']

        # title of car
        title = data['vehicle_info']['mark_info']['name'] + \
            ' ' + data['vehicle_info']['model_info']['name']
        if 'name' in data['vehicle_info']['super_gen']:
            title = title + ' '+data['vehicle_info']['super_gen']['name']
        if 'notice' in data['vehicle_info']['configuration']:
            title = title + ' '+data['vehicle_info']['configuration']['notice']

        # engine capacity transmission
        cap = data['lk_summary'].replace('\xa0', ' ').split(' ')

        engcapacity = cap[0]
        power = cap[2].replace('(', '')+' '+cap[3].replace('),', '')
        transmission = cap[1]

        # getting price
        price, currency = data['price_info']['RUR'], '₽'

        # data of publicity
        date = data['additional_info']['hot_info']['start_time'].replace(
            'T', ' ').replace('Z', '')
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

    def get_blocks(self, page=1, file=0):
        data = self.get_page(page=page)[1]
        
        if(file):
            with open('avto_ru.csv', 'a', encoding='utf8') as f:
                writer = csv.writer(f)
                for item in range(0, len(data)):
                    block = self.parse_block(data=data[item])
                    writer.writerow((block))
                return 'Ok'
        else:
            for item in range(0, len(data)):
                block = self.parse_block( data=data[item])
                print(block)

    def parse_all(self):
        limit = self.get_pagination_limit()
        print(f'Всего страниц: {limit}')

        for i in range(1, limit+1):
           
            self.get_blocks(page=i, file=1)
            print("Страница", i)


def main():
    proxy = []
    with open("proxy.txt", "r") as myfile:
        try:
            data = myfile.readlines()
            for each in data:
                proxy.append(each.replace('\n', '').replace('\r', ''))
        except:
            pass
    p = AutoRuParser(proxy=proxy)
    p.set_up(url='https://auto.ru/ufa/cars/all/')
    p.parse_all()
    print('Работа закончена!')


if __name__ == "__main__":
    main()

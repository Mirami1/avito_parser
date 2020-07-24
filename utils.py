from collections import namedtuple
import requests

InnerBlock = namedtuple('Block', 'title,engcapacity,transmission,power,price,currency,date,url')


class Block(InnerBlock):
    def __str__(self):
        return f'{self.title}\t{self.engcapacity}\t{self.transmission}\t{self.power}\t{self.price} {self.currency}\t{self.date}\t{self.url}'


class Parser:
    def __init__(self, proxy=[]):
        self.proxy = proxy
        self.proxy_succeed = False
        self.proxy_success = {}
        self.session = requests.Session()
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
            'Accept-Language': 'ru',
        }
        self.url=None
    
    def set_up(self):
        pass
    def check_html(self):
        pass
    def get_page(self):
        pass
    def get_pagination_limit(self):
        pass
    def parse_block(self, item):
        pass
    def get_blocks(self):
        pass
    def parse_date(self):
        pass
    def parse_all(self):
        pass
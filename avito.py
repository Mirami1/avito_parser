from utils import Parser,Block
import time 
import bs4
import requests
import urllib.parse
import csv
import datetime
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class AvitoParser(Parser):

    
    def set_up(self, url):
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get(url)
        driver.find_element_by_link_text('Авто').click()
        driver.implicitly_wait(10)
        
        driver.find_element_by_xpath("//a[@class='rubricator-list-item-link-12kOm' and @data-marker='category[1000014]/link']").click()
        
        
        wait =  WebDriverWait(driver, 30)
        elem = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@class='input-input-25uCh' and @placeholder='Цена от']")))
        
        time.sleep(5)
        driver.find_element_by_xpath("//input[@class='input-input-25uCh' and @placeholder='Цена от']").send_keys('50000')
        driver.find_element_by_xpath("//input[@class='input-input-25uCh' and @placeholder='до, руб.']").send_keys('500000')
        elem=driver.find_element_by_xpath("//input[@class='suggest-input-3p8yi' and @placeholder='от 1960']").send_keys(' ')
        elem=driver.find_element_by_xpath("//ul[@class='suggest-suggests-bMAdj']").find_elements_by_xpath(".//*")
        for li in elem:
            if(li.get_attribute('data-marker')=='suggest(15)'):
                li.click()
                break
        elem=driver.find_element_by_xpath("//input[@class='suggest-input-3p8yi' and @placeholder='до 2020']").send_keys(' ')
        elem=driver.find_element_by_xpath("//ul[@class='suggest-suggests-bMAdj']").find_elements_by_xpath(".//*")
        for li in elem:
            if(li.get_attribute('data-marker')=='suggest(1)'):
                li.click()
                break
        elem=driver.find_element_by_xpath("//input[@class='suggest-input-3p8yi' and @placeholder='от 0,0']").send_keys(' ')
        elem=driver.find_element_by_xpath("//ul[@class='suggest-suggests-bMAdj']").find_elements_by_xpath(".//*")
        for li in elem:
            if(li.get_attribute('data-marker')=='suggest(11)'):
                li.click()
                break
        elem=driver.find_element_by_xpath("//input[@class='suggest-input-3p8yi' and @placeholder='до 500+']").send_keys(' ')
        elem=driver.find_element_by_xpath("//ul[@class='suggest-suggests-bMAdj']").find_elements_by_xpath(".//*")
        for li in elem:
            if(li.get_attribute('data-marker')=='suggest(41)'):
                li.click()
                break
       
        driver.find_element_by_xpath("//span[@data-marker='params[696](8854-radio)/text']").click()
        driver.find_element_by_xpath("//span[@data-marker='params[697](8856)/text']").click()
      
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.find_element_by_xpath("//input[@data-marker='params[1167](19984)/input']").click()
        driver.find_element_by_xpath("//label[@data-marker='user(1)' and @tabindex='1']").click()
        driver.find_element_by_xpath("//div[@data-marker='search-form/radius']").click()
        elem=driver.find_element_by_xpath("//div[@data-marker='popup-location/radius-list']").find_elements_by_xpath(".//*")
        for li in elem:
            if(li.get_attribute('data-marker')=='popup-location/radius-item-100'):
                li.click()
                break
        driver.find_element_by_xpath("//button[@data-marker='popup-location/save-button']").click()
        print(driver.current_url)
        self.url=driver.current_url

   

    def check_html(self, file):
        line = file.find("Доступ с вашего IP-адреса временно ограничен")
        return line != 1

    def get_page(self, page: int = None):
        r = urllib.parse.urlparse(self.url)
        params = urllib.parse.parse_qs(r.query)
        go=urllib.parse.urljoin('https://www.avito.ru',r.path)
        if page and page > 1:
            params['p'] = page
        if len(self.proxy) != 0 and self.proxy_succeed == False:
            for p in self.proxy:
                try:
                    print('ставлю прокси по %s' % p)
                    self.proxy_success = {'http': '%s' % p, 'https': '%s' % p}
                    r = self.session.get(
                        go, params=params, proxies=self.proxy_success)
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
            r = self.session.get(go, params=params,
                                 proxies=self.proxy_success)
            return r.text
        else:
            r = self.session.get(go, params=params)
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
        s=cap.string.strip().split(', ')[1].split(' ')
        engcapacity = s[0]
        transmission=s[1]
        power=s[2].replace('(', '')+" "+s[3].replace(')', '')

        

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
            transmission=transmission,
            power=power
        )

    def get_blocks(self, page=1,file=0):
        text = self.get_page(page=page)
        soup = bs4.BeautifulSoup(text, 'lxml')

        # CSS container selector selection
        container = soup.select(
            'div.snippet-horizontal.item.item_table.clearfix.js-catalog-item-enum.item-with-contact.js-item-extended')
        if(file):
             with open('avito.csv', 'a', encoding='utf8') as f:
                writer = csv.writer(f)
                for item in container:
                    block = self.parse_block(item=item)
                    writer.writerow((block))
        else:
            for item in container:
                block = self.parse_block(item=item)
                print(block)

    """def get_blocks_to_csv(self, page=1):
        text = self.get_page(page=page)
        soup = bs4.BeautifulSoup(text, 'lxml')

        # CSS selector selection
        container = soup.select(
            'div.snippet-horizontal.item.item_table.clearfix.js-catalog-item-enum.item-with-contact.js-item-extended')
        with open('avito.csv', 'a', encoding='utf8') as f:
            writer = csv.writer(f)
            for item in container:
                block = self.parse_block(item=item)
                writer.writerow((block))"""

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
    p = AvitoParser(proxy=proxy)
    p.set_up(url='https://www.avito.ru/ufa')
    p.parse_all()
    print('Работа закончена!')
    
    #p.set_up('https://www.avito.ru')



if __name__ == "__main__":
    main()

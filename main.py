from avito import AvitoParser
from auto_ru import AutoRuParser
from drom_ru import DromRuParser
from yola import YolaRuParser
def main():
    proxy = []
    with open("proxy.txt", "a+") as myfile:
        try:
            data = myfile.readlines()
            for each in data:
                proxy.append(each.replace('\n', '').replace('\r', ''))
        except:
            pass
    print('Avito!')
    p = AvitoParser(proxy=proxy)
    p.set_up(url='https://www.avito.ru/ufa')
    p.parse_all()
    print('Работа закончена!')
    
    print('AutoRu!')
    p = AutoRuParser(proxy=proxy)
    p.set_up(url='https://auto.ru/ufa/cars/all/')
    p.parse_all()
    print('Работа закончена!')

    print('DromRu!')
    p = DromRuParser(proxy=proxy)
    p.set_up(url='https://ufa.drom.ru/auto/all/page')
    p.parse_all()
    print('Работа закончена!')

    print('YolaRu!')
    p = YolaRuParser(proxy=proxy)
    p.set_up(url='https://auto.youla.ru/ufa/cars/used/')
    p.parse_all()
    print('Работа закончена!')


if __name__ == "__main__":
    main()

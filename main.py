from avito import AvitoParser
from auto_ru import AutoRuParser
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


if __name__ == "__main__":
    main()

from avito import AvitoParser
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

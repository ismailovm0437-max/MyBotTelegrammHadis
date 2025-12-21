
import requests
from bs4 import BeautifulSoup

response = requests.get("https://isnad.link/book/sahih-al-buhari") #!выполняем запрос на сервер 
page = BeautifulSoup(response.text,'html5lib') #! ПАРСИНГ ОТВЕТА УДАЛЕННОГО СЕРВЕРА ,указываем процессор библиотеку html5lib


pageTitle = page.find('div', class_="has-text-centered")  # ? метод find  позволяет извлечь первый элемент из HTML  возровщает только первое совпадение
print(pageTitle.string) #? этот метод позволяет выводит текст без тегов
print('')

# ? метод.find_all позволяет найти все указанные элелменты на сайте
pageParagraphs = page.find_all('span', class_='hadeeth-num')


#* выводим все найденные элементы 
#! ЕСЛИ У ССЫЛКИ НЕТ ПРЯМОГО СОДЕРЖИМОГО ТО ИСПОЛЬЗУЕМ МЕТОД .text и .get_text
if len(pageParagraphs) >= 5:
	#* выводим содержимое (без тегов) найденных ссылок  
	for i in range(5):
	  print(pageParagraphs[i].get_text() or pageParagraphs[i].text)
print("")


pageItemporp= page.find_all(itemprop= 'sameAs') #? itemprop= 'sameAs' используется в микроразметке страниц извлекмаем ее

#* вывод значения "href" всех найденных элементов
for item in pageItemporp:
    print(item['href'])
print("")



pageMeta =  page.find('div').find_all('meta')

for meta in pageMeta:
    print(meta['content'])
    


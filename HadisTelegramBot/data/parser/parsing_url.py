from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from parsing_title_book import page

# Получаем все внутренние ссылки
internalLinks = [
    a.get('href') for a in page.find_all('a')
    if a.get('href') and a.get('href').startswith('/')
]

# Выводим ссылки по порядку с нумерацией
print("Найдено внутренних ссылок:", len(internalLinks))
print("\nСписок внутренних ссылок:")
for i, link in enumerate(internalLinks, 1):
    print(f"{i}. {link}")

# data/parser/filtered_hadith_links.py
from parsing_title_book import page
from urllib.parse import urljoin
import re

def filter_hadith_links():
    """Фильтрует ваши внутренние ссылки чтобы найти именно хадисы"""
    
    # Ваш оригинальный код
    internalLinks = [
        a.get('href') for a in page.find_all('a')
        if a.get('href') and a.get('href').startswith('/')
    ]
    
    print(f"🔗 Ваш код нашел внутренних ссылок: {len(internalLinks)}")
    
    # ФИЛЬТРУЕМ чтобы оставить только ссылки на хадисы
    hadith_links = []
    
    for href in internalLinks:
        # Признаки ссылки на хадис
        is_book_link = '/book/' in href
        has_numbers = re.search(r'\d+', href)
        is_long_path = len(href.split('/')) > 3  # /book/sahih-al-buhari/12
        
        if is_book_link and (has_numbers or is_long_path):
            full_url = urljoin("https://isnad.link", href)
            
            # Найдем текст ссылки
            link_element = page.find('a', href=href)
            link_text = link_element.get_text().strip() if link_element else "Без текста"
            
            hadith_links.append({
                'url': full_url,
                'text': link_text,
                'href': href
            })
    
    print(f"🎯 После фильтрации осталось ссылок на хадисы: {len(hadith_links)}")
    
    # Покажем результаты
    print("\n📋 Ссылки на хадисы:")
    for i, link in enumerate(hadith_links[:15], 1):
        print(f"{i}. {link['text']}")
        print(f"   → {link['url']}")
    
    return hadith_links

# Запуск
if __name__ == "__main__":
    hadith_links = filter_hadith_links()
    
    # Если нашли ссылки - проанализируем первую
    if hadith_links:
        print(f"\n🔍 Проверим первую ссылку: {hadith_links[0]['url']}")
        
        import requests
        from bs4 import BeautifulSoup
        
        resp = requests.get(hadith_links[0]['url'])
        soup = BeautifulSoup(resp.text, 'html5lib')
        
        # Быстрый анализ страницы
        print("📄 Заголовок страницы:", soup.find('title').get_text() if soup.find('title') else "Не найден")
        
        # Поиск текста похожего на хадисы
        paragraphs = soup.find_all(['p', 'div'])
        hadith_like_texts = []
        
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text) > 100 and re.search(r'сказал|передал', text, re.IGNORECASE):
                hadith_like_texts.append(text[:150] + "...")
        
        print(f"📖 Найдено текстов похожих на хадисы: {len(hadith_like_texts)}")
        
        if hadith_like_texts:
            print("Пример текста:")
            print(hadith_like_texts[0])
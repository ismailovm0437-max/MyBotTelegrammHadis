
import requests
from bs4 import BeautifulSoup
import re 
import json

def analiz_hadisa():
    url = "https://isnad.link/book/sahih-al-buhari/1-kniga-nachalo-otkrovenij-hadisy-1-7"
    print(f"Анализирую данную страницу с хадисами ")
    
    response= requests.get(url)
    page=BeautifulSoup(response.text,'html5lib')
    
    
    with open("analiz_proverka_hadis.html",'w',encoding='utf=8') as f :
        f.write(page.prettify())
    print("Страница сохранена в analiz_proverka_hadis.html")
    
    
    print(f"Заголовок : {page.find('title').get_text() if page.find('title') else "Не найдено"}")

    elements_teg= page.find_all(['p','div','li','article','section'])
    print(f"Общее колличество элементов на странице: {len(elements_teg)}")
    
    hadis_keep=[]
    
    for i , elem in enumerate(elements_teg):
        text=elem.get_text().strip()
        classes= elem.get('class',[])
        
        poisk_po_keywords=(
            re.search(r"\b\d+\.?\b",text) and
            re.search(r'(сказал|передал|сообщил).*?(пророк|посланник|Аллах)', text, re.IGNORECASE) and
            len(text) > 50 and len(text) < 2000
        )
        
        poisk_po_claseses= any (keyword in str (classes).lower() for keyword in
                                ['hadis','text','number','isnad','matn'])
        
        
        if poisk_po_keywords or poisk_po_claseses:
            hadis_keep.append({
                'element': elem.name,
                'classes': classes,
                'text_lenght':len(text),
                'text_preview':text[:100]+('...' if len(text)>100 else 'Текст не соответсвует'),
                'full_text':text,
                'html': str(elem)[:200]+'...'
            })
    
    print("АНАЛИЗ ХАДИСОВ")
    print('='* 60)
    
    for i , hadith in enumerate(hadis_keep[:5],1):
        print(f"Хадис")
        print(f"Элемент :{hadith['element']}")
        print(f"Классы :{hadith['classes']}")
        print(f"Длинна :{hadith['text_lenght']}")
        print(f"Текст :{hadith['text_preview']}")
        
        text = hadith['full_text']
        if re.search(r'\b\d+\.?\b', text):
            numbers = re.findall(r'\b\d+\.?\b', text)
            print(f"Номера в тексте {numbers}")
            
        if re.search(r"сказал|передал",text,re.IGNORECASE):
            print(f"Содержит иснад")
        
    
    with open("hadis_pars.json",'w', encoding='utf=8') as f:
        json.dump(hadis_keep,f,ensure_ascii=False,indent=2)
    print(f"  Рузультат сохранен  ")
    return hadis_keep




if __name__=="__main__":
    hadith= analiz_hadisa()
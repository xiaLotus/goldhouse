from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
import os
import re
import time


ua = UserAgent()
headers = {
    'user-agent': ua.random,
}

def get_novel_page(title):
    with open(f'{title.replace("/", "_").replace("?", "")}.txt', 'r', encoding='utf-8') as file:
        lines = file.read().split('\n')
        for i, chapter_link in enumerate(lines, start=1):
            if chapter_link.strip():
                chapter_title, chapter_url = chapter_link.strip().split(" - ", 1)
                chapter_title = chapter_title.strip().split(" ")[0]
                request = requests.get(chapter_url, headers = headers, timeout = 5)
                request = request.text
                request.encode('utf-8')
                soup = BeautifulSoup(request, 'html.parser')
                path = f"{title}/{chapter_title}.txt"
                content_div = soup.find('div', style='font-size: 20px; line-height: 30px; word-wrap: break-word; table-layout: fixed; word-break: break-all; width: 750px; margin: 0 auto; text-indent: 2em;')

                path = f"{title}/{chapter_title}.txt"
                with open(f'{path}', 'w', encoding='utf-8') as file:
                    for content in content_div:
                        content = content.get_text().strip()
                        if '請記住本站域名:' in content or '黃金屋' in content:
                            content = ''  
                        file.write(content + '\n')

                with open(f'{path}', 'r', encoding = 'utf-8') as file:
                    original_text = file.read()

                lines = original_text.split('\n')
                for i, line in enumerate(lines):
                    if f'{title}' in line:
                        lines = lines[i:]
                        break

                result_text = '\n'.join(lines)
                with open(f'{path}', 'w', encoding='utf-8') as file:
                    file.write(result_text)

                with open(f'{path}', 'r', encoding = 'utf-8') as file:
                    original_text = file.read()

                origin_text = re.sub(r'^\s*(人在大唐已被退學[\s\S]*)', r'\1', original_text)
                origin_text = re.sub(r'\n\s*\n', '\n', origin_text)
                lines = original_text.split('\n')
                result_text = '\n'.join(lines)
                with open(f'{path}', 'w', encoding='utf-8') as file:
                    file.write(result_text)
                print(path, ' ok')
                time.sleep(1.5)


# 爬取目錄
def get_catalog(url, book_nums):
    request = requests.get(url, headers = headers)
    request = request.text
    request.encode('utf-8')
    soup = BeautifulSoup(request, 'html.parser')
    try:
        with open(f'{book_nums}.txt', 'w', encoding = 'utf-8') as file:
            file.write(soup.prettify())
    except Exception as e:
        print(str(e))

# 爬取章節(導出章節.txt)
def get_chapter(book_nums):
    with open(f'{book_nums}.txt', 'r', encoding = 'utf-8') as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    # 書名(title)
    title = soup.find('title').text.strip()
    title = title.split('/')[0].strip()
    print(title)


    if not os.path.exists(title):
        os.makedirs(title)
    
    chapter_elements = soup.find_all('td')
    for chapter_element in chapter_elements:
        link_element = chapter_element.find('a')

        if link_element:
            chapter_url = link_element['href'].strip()
            chapter_url = 'https://tw.hjwzw.com' + chapter_url
            chapter_title = link_element.get_text().strip()
            chapter_url_title = f"{chapter_title} - {chapter_url}\n"
            with open(f'{title}.txt', 'a', encoding = 'utf-8') as file:
                file.write(chapter_url_title)
    # 存放 chapter_title + url
    new_lines = []
    with open(f'{title}.txt', 'r', encoding = 'utf-8') as file:
        lines = file.readlines()

    for line in lines:
        if 'https://tw.hjwzw.com/Book/Read/' in line:
            new_lines.append(line)

    with open(f'{title}.txt', 'w', encoding = 'utf-8') as file:
        file.writelines(new_lines)
    os.remove(f'{book_nums}.txt')
    return title


if __name__ == '__main__':
    start = time.time()
    book_nums = str(input())
    url = f'https://tw.hjwzw.com/Book/Chapter/{book_nums}'
    get_catalog(url, book_nums)
    title = get_chapter(book_nums)
    get_novel_page(title)
    end = time.time()
    f = f"執行時間: %f 秒" %(end - start)
    print(f)
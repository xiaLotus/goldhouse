from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
import os
import re
import time
import asyncio
import aiohttp

semaphore = asyncio.Semaphore(5) 

async def get_novel_page(title, chapter_link, headers):
    if '-' in chapter_link:
        chapter_title, chapter_url = chapter_link.strip().split(" - ", 1)
        chapter_title = chapter_title.strip().split(" ")[0]
        chapter_title = chapter_title.replace('/', '').replace('?', '')
    else:
        print(f"無法解析章節連結：{chapter_link}，重複檢查無效，開始打包")
        return
    
    # chapter_title, chapter_url = chapter_link.strip().split(" - ", 1)
    # chapter_title = chapter_title.strip().split(" ")[0]

    async with aiohttp.ClientSession() as session:
        try:
            async with semaphore:
                async with session.get(chapter_url, headers=headers, timeout=20) as response:
                    if response.status == 200:
                        request_text = await response.text()
                    else:
                        print(f"找不到章節: {chapter_url}")
                        # 紀錄在另一個txt內
                        with open('unprocessed_chapters.txt', 'a', encoding='utf-8') as unprocessed_file:
                            unprocessed_file.write(f"{chapter_link}\n")
                        return
                    
        except asyncio.exceptions.LimitOverrunError as e:
            print(f"Error fetching chapter: {chapter_title}. Error: {str(e)}")
            # 把章節和url紀錄回去，等下一個round回來再爬一次
            with open('unprocessed_chapters.txt', 'a', encoding='utf-8') as unprocessed_file:
                unprocessed_file.write(f"{chapter_link}\n")
            return
        

    soup = BeautifulSoup(request_text, 'html.parser')
    path = f"{title}/{chapter_title}.txt"
    content_div = soup.find('div', style='font-size: 20px; line-height: 30px; word-wrap: break-word; table-layout: fixed; word-break: break-all; width: 750px; margin: 0 auto; text-indent: 2em;')

    with open(f'{path}', 'w', encoding='utf-8') as file:
        if content_div:
            for content in content_div:
                content = content.get_text().strip()
                if '請記住本站域名:' in content or '黃金屋' in content:
                    content = ''  
                file.write(content + '\n')
        else:
            file.write('Chapter content not found')
            with open('unprocessed_chapters.txt', 'a', encoding='utf-8') as unprocessed_file:
                unprocessed_file.write(f"{chapter_link}\n")
            return

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

    origin_text = re.sub(r'^\s*('+ re.escape(title) + r'[\s\S]*)', r'\1', original_text)
    origin_text = re.sub(r'\n\s*\n', '\n', origin_text)
    lines = original_text.split('\n')
    result_text = '\n'.join(lines)
    with open(f'{path}', 'w', encoding='utf-8') as file:
        file.write(result_text)
    print(path, ' ok')

# 處理未通過的章節，可以註解
async def process_unprocessed_chapters(title, headers):
    with open('unprocessed_chapters.txt', 'r', encoding='utf-8') as unprocessed_file:
        unprocessed_chapter_links = unprocessed_file.readlines()

    for chapter_link in unprocessed_chapter_links:
        chapter_link = chapter_link.strip()
        await get_novel_page(title, chapter_link, headers)

# 存好目錄，如
# 第一章 這人是個傻子 - https://tw.hjwzw.com/Book/Read/44549,20633992
# 第二章 求賢若渴 - https://tw.hjwzw.com/Book/Read/44549,20633993
async def get_catalog(url, book_nums, headers):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers, timeout = 20) as response:
            html_content = await response.text()

    soup = BeautifulSoup(html_content, 'html.parser')
    title = soup.find('title').text.strip().split('/')[0].strip()

    if not os.path.exists(title):
        os.makedirs(title)

    chapter_elements = soup.find_all('td')
    chapter_links = []
    for chapter_element in chapter_elements:
        link_element = chapter_element.find('a')
        if link_element:
            chapter_url = link_element['href'].strip()
            chapter_url = 'https://tw.hjwzw.com' + chapter_url
            chapter_title = link_element.get_text().strip()
            chapter_url_title = f"{chapter_title} - {chapter_url}\n"
            chapter_links.append(chapter_url_title)

    with open(f'{title}.txt', 'w', encoding='utf-8') as file:
        file.writelines(chapter_links)
    new_lines = []
    with open(f'{title}.txt', 'r', encoding = 'utf-8') as file:
        lines = file.readlines()

    for line in lines:
        if 'https://tw.hjwzw.com/Book/Read/' in line:
            new_lines.append(line)

    with open(f'{title}.txt', 'w', encoding = 'utf-8') as file:
        file.writelines(new_lines)
    return title

async def main():
    ua = UserAgent()
    headers = {
        'user-agent': ua.random,
    }

    book_nums = input("請輸入書號： ")
    url = f'https://tw.hjwzw.com/Book/Chapter/{book_nums}'
    title = await get_catalog(url, book_nums, headers)
    print(f'目錄已獲取，書名為：{title}')
    # 這邊生產{title}.txt

    # chapter_links = []
    with open(f'{title}.txt', 'r', encoding = 'utf-8') as file:
        lines = file.readlines()
    
    tasks = [get_novel_page(title, chapter_link, headers) for chapter_link in lines]
    await asyncio.gather(*tasks)

    await process_unprocessed_chapters(title, headers)
    os.remove(f"{title}.txt")
    os.remove(f"unprocessed_chapters.txt")

if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f"執行時間: {end - start:.2f} 秒")

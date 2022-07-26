import re
import aiohttp
import asyncio
from time import time
from bs4 import BeautifulSoup
from fake_useragent import UserAgent


class AsyncUzhits:
    def __init__(self):
        self.url = "https://uzhits.net/"
        self.headers = {
            'Accept': '*/*',
            'Connection': 'keep-alive',
            "User-Agent": UserAgent().random
        }
    
    async def start(self):
        self.s = aiohttp.ClientSession()
    
    
    async def getPage(self, url: str, data=None):
        if not url.startswith('https://uzhits.net/'):
            url = self.url + url
        try:
            resp: aiohttp.ClientResponse = await self.s.get(url, params=data, headers=self.headers)
            if resp.status != 200:
                return print(f"Bunday sahifa mavjud emas!\n {url}")
            txt = await resp.text()
            return BeautifulSoup(txt, 'html.parser')
        except Exception as e:
            return print(e)
    
    async def dl(self, music_url: str) -> str:
        bs = await self.getPage(music_url)
        if bs is not None and bs:
            a = bs.find('a', attrs={'class': "fbtn fdl"})
            return a['href']
        return print("Sahifani yuklab bo'lmadi")
            
    async def get_musics(self, query: str, search_start: int = 1, result_from: int = 1):
        bs = await self.getPage(self.url + 'index.php', {
            'do': 'search',
            'subaction': 'search',
            'full_search': 0,
            'search_start': search_start,
            'result_from': result_from,
            'story': query
        } )
        if bs is not None:
            content = bs.find('div', attrs={'id': "dle-content"})
            result = []
            for div in content.find_all('div', attrs={'class': "track-item fx-row fx-middle js-item"}):
                div2 = div.find('div', attrs={'class': "track-desc fx-1"})
                a = div2.find('a')
                result.append((a.text, a['href']))
            return result
    
    async def search_n(self, query):
        bs = await self.getPage(self.url + 'index.php', {
            'do': 'search',
            'subaction': 'search',
            'full_search': 0,
            'search_start': 0,
            'result_from': 1,
            'story': query
        } )
        if bs is not None:
            content = bs.find('main', attrs={'class': "content"})
            # print(content)
            berrors = content.find('div', attrs={'class': 'berrors'})
            found_text = "По Вашему запросу найдено"
            not_found_text = "К сожалению, поиск по сайту не дал никаких результатов. Попробуйте изменить или сократить Ваш запрос."
            if not_found_text in berrors.text.strip():
                return print("Ushbu so'rov bo'yicha birorta ma'lumot topilmadi. Boshqatdan urinib ko'ring")
            # print("Hozircha nimadir borga o'xshayapti")
            elif found_text in berrors.text.strip():
                txt = berrors.text.strip()
                n = int(re.search(r"найдено ([0-9]+) ответов", txt).group(1))
                return n
    
    async def search(self, query):
        n = await self.search_n(query)
        if n is not None and n:
            print(f"\"{query}\" qidiruvi bo'yicha {n} ta natija topildi")
            result = []
            for i in range(n // 10):
                result += await self.get_musics(query, i+1, i*10+1)
            return result
                
        print("Na borga o'xshaydi na yo'qga")
    
    async def close(self):
        return await self.s.close()
           

async def main():
    u = AsyncUzhits()
    await u.start()
    print(await u.dl("https://uzhits.net/yosh-ijodkorlar/45394-doxxim-telbalarcha.html"))
    # inp = input("Qaysi musiqani qidirmoqchisiz: ")
    inp = 'muhabbat'
    result = await u.search(inp)
    if result is not None:
        print(f"\"{inp}\" qidiruvi bo'yicha natijalar: jami", len(result), "ta")
        for i, music in enumerate(result):
            name, link = music
            print(f"{i+1})", name, "  ->  ", link)
    
    await u.close()
                
if __name__ == '__main__':
    
    loop = asyncio.get_event_loop()
    start_time = time()
    loop.run_until_complete(main())
    end_time = time()
    print(end_time - start_time)
    loop.close()


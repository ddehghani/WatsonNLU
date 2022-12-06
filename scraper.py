import asyncio
import aiohttp
from bs4 import BeautifulSoup
from util import *
from watson import WatsonNLU

API_KEY = 'YlZZ1p6TYqzpemeX5-sdCjtTJJOwblN1VtueSqW8bEwg'
NLU_URL = 'https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/fa369057-a844-4eb1-a183-b9c1c88a1ca1'
nlu = WatsonNLU(apikey = API_KEY, url = NLU_URL)

async def fetch_and_parse_url(url: str, client: aiohttp.ClientSession, parser: callable, **kwargs):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13.0; rv:107.0) Gecko/20100101 Firefox/107.0'}
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        resp = await client.get(url=url, headers=headers, timeout = timeout)
        resp.raise_for_status() # if response is not 200 raise an exception
        html = await resp.text()
    except Exception as e:
        # print(f"An error accurred while retriving the url: {url}")
        # print(e)
        return None
    else:
        # if no exception occured during fetching, parse it 
        return await parser(url, html, **kwargs)
       
async def scrap_links(url: str, html: str, **kwargs):
    same_domain_only = kwargs.get('same_domain_only')
    kwargs.pop('same_domain_only', None) # **kwargs will be passed to BS4 so internal kwargs will be removed
    found = set()
    parsed_html = BeautifulSoup(html, 'html.parser')
    link_tags = parsed_html.find_all('a', **kwargs)
    links = (link_tag.get('href') for link_tag in link_tags if 'href' in link_tag.attrs)
    for link in links:
        link = get_absolute_url(link, url)
        if not same_domain_only or is_same_domain(link, url):
           found.add(link)
    return found

def process_articles(*args, **kwargs):
    return asyncio.run(process_articles_async(*args, **kwargs))

async def process_articles_async(articles: dict[str, list]) -> dict[str, list]:
    process_articles = {}
    for news_agency, links in articles.items():
        async with aiohttp.ClientSession() as client:
            tasks = [fetch_and_parse_url(link, client, filter_and_analyze) for link in links]
            print(f'About to asynchronously process {len(tasks)} links')
            analyzed_links = await asyncio.gather(*tasks)
            keywords = {}
            for kwlist in analyzed_links:
                if kwlist:
                    for kw in kwlist:
                        kwtext = kw.get('text')
                        del kw['text']
                        if kwtext not in keywords:
                            keywords[kwtext] = kw
                        elif "emotion" in keywords[kwtext]:
                            keywords[kwtext]['count'] += kw['count']
                            keywords[kwtext]['emotion'] = weighted_average_emotion(keywords[kwtext]['emotion'], keywords[kwtext]['count'], kw['emotion'], kw['count'])
            process_articles[news_agency] = keywords
    return process_articles

async def filter_and_analyze(url: str, html: str, **kwargs) -> str:
    parsed_html = BeautifulSoup(html, 'html.parser')
    if url.startswith("https://www.infowars.com/"):
        p_tags = parsed_html.findAll('p', **kwargs)
        article_text = ""
        for p_tag in p_tags:
            if p_tag:
                article_text += p_tag.get_text(strip=True)
        return await nlu.analyze_text(text = article_text)
    else:
        article = parsed_html.find('article', **kwargs)
        return await nlu.analyze_text(text = article.get_text(strip=True)) if article else None

def deep_search_for_links_sync(*args, **kwargs) -> list[str]:
    return asyncio.run(deep_search_for_links(*args, **kwargs))

async def deep_search_for_links(*, source_url: str, already_extracted_links: dict[str, bool] = None, depth: int = 1, max_links: int = 0, same_domain_only = False, **kwargs) -> list[str]:
    # first call
    if not already_extracted_links:
        already_extracted_links = {source_url: False}
    
    # base case
    if depth == 0 or (max_links != 0 and len(already_extracted_links) > max_links): # limiting total number of articles
        print(len(already_extracted_links))
        return [link for link in already_extracted_links]
    
    # fetch and search all the links that have not yet been scrapped 
    new_urls = []
    async with aiohttp.ClientSession() as client:
        tasks = []
        for url, visited in already_extracted_links.items():
            if not visited:
                already_extracted_links[url] = True
                tasks.append(fetch_and_parse_url(url, client, scrap_links, same_domain_only = True, **kwargs))
        print(f'About to asynchronously scrap {len(tasks)} links')
        new_links = await asyncio.gather(*tasks)
        # then add any newly found link to already__extracted_links and mark them as not visited
        for linkset in new_links:
            if linkset:
                for link in linkset:
                    if link not in already_extracted_links:
                        already_extracted_links[link] = False        
    # recuursive step
    return await deep_search_for_links(source_url = None, 
                            already_extracted_links = already_extracted_links, 
                            depth = depth - 1, 
                            max_links = max_links,
                            **kwargs)

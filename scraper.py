import asyncio
import aiohttp
from bs4 import BeautifulSoup
from util import *


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

def filter_articles_sync(*args, **kwargs):
    return asyncio.run(filter_articles(*args, **kwargs))

async def filter_articles(articles: dict[str, list]) -> dict[str, list]:
    filtered_articles = {}
    for news_agency, links in articles.items():
        async with aiohttp.ClientSession() as client:
            tasks = [fetch_and_parse_url(link, client, filters, filter_for = 'article') for link in links]
            print(f'About to asynchronously filter {len(tasks)} links')
            new_links = await asyncio.gather(*tasks)
            filtered_articles[news_agency] = [link for link in new_links if link]
    return filtered_articles


async def filters(url: str, html: str, **kwargs) -> str:
    parsed_html = BeautifulSoup(html, 'html.parser')
    if filter_for := kwargs.get('filter_for'):
        del kwargs["filter_for"] # dont pass this to bs4.find()
        tag = parsed_html.find(filter_for, **kwargs)
    return url if tag is not None else None # if filter_for param is not set return false

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


# async def worker(session):
#     async with session.get(URL) as response:
#         await response.read()


# async def run(worker, *argv):
#     async with g_thread_limit:
#         await worker(*argv)


# async def main():
#     g_thread_limit = asyncio.Semaphore(MAXTHREAD)
#     async with aiohttp.ClientSession() as session:
#         await asyncio.gather(*[run(worker, session) for _ in range(MAXREQ)])


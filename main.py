# from ibm_watson import NaturalLanguageUnderstandingV1
# from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
# from ibm_watson.natural_language_understanding_v1 import Features, EmotionOptions
# from ibm_watson import ApiException
from ast import arg
import json
from bs4 import BeautifulSoup
import re
import asyncio
import aiohttp
import argparse

API_KEY = 'zts4dI59s4kAm3gdMjreP6gzEfz2dJt_26RqvS_LKlA0'
URL = 'https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/7bc06708-aa50-4cd7-bf65-cb2a535ab49a'
SOURCE_URL = 'https://blog.feedspot.com/usa_news_websites/' # a weblog containing the list of 100 most popular new aggencies in US

async def main(args):
    news_links = read_as_json(args.newsLinkFile)
    articles = read_as_json(args.articlesFile)
    if not articles:
        if not news_links:
            print("No news links file provided or it couldn't be read. Extracting news links.")
            # scrap for external links from SOURCE_URL
            news_links_list = await deep_search_for_links(source_url = SOURCE_URL, depth = 1, class_ = 'ext') # depth 1 means only links in source url will be returned 
            news_links_list.remove('https://blog.feedspot.com/usa_news_websites/') # this was tagged as 'ext' for some reason, had to remove it
            news_links = { 'links' : news_links_list}
            print(f'Total news website links extracted from {get_domain(SOURCE_URL)}: {len(news_links["links"])}')
            # save result as a json file
            save_as_json('NewsAgencies.json', news_links)
        # extract articles
        print("No article file provided or it couldn't be read. Extracting articles.")
        articles = {}
        for index, news_website in enumerate(news_links['links']):
            if news_website not in ['https://www.seattletimes.com/', 'https://atlantaintownpaper.com/']: # problematic links
                print(f'{news_website = }')
                articles[news_website] = await deep_search_for_links(source_url = news_website, depth = 2, same_domain_only = True)
                print(f'Progress: {(index + 1) * 100 / len(news_links["links"]):0.2f}%')
        save_as_json('articles.json', articles)
    
    # use articles here
    # we should check if articles are in fact articles and then save then on a json
    print(sum([len(v) for k, v in articles.items()]))

def save_as_json(filename: str, data: dict):
    json_object = json.dumps(data, indent=4)
    with open(filename, 'w') as outfile:
        outfile.write(json_object)

def read_as_json(filename: str) -> dict:
    try:
        with open(filename, 'r') as openfile:
            json_object = json.load(openfile)
    except Exception:
        return None
    else:
        return json_object

async def fetch_and_parse_url(url: str, client: aiohttp.ClientSession, same_domain_only = False, **kwargs):
    # **kwargs will be passed to BS4 for more flexible scrapping
    found = set()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        resp = await client.get(url=url, headers=headers)
        resp.raise_for_status() # if response is not 200 raise an exception
        html = await resp.text()
    except Exception as e:
        print('oops')
        print(e)
        return found
    else:
        # if not exception occured during fetching, parse it and find all links
        parsed_html = BeautifulSoup(html, 'html.parser')
        link_tags = parsed_html.find_all('a', **kwargs)
        links = (link_tag.get('href') for link_tag in link_tags if 'href' in link_tag.attrs)
        for link in links:
            if same_domain_only:
                link = is_same_domain(link, url)
            if link:
                found.add(link)
        return found

async def deep_search_for_links(*, source_url: str, already_extracted_links: dict[str, bool] = None, depth: int = 1, same_domain_only = False, **kwargs) -> list[str]:
    # base case
    if depth == 0:
        return [link for link in already_extracted_links]
    # first call
    if not already_extracted_links:
        already_extracted_links = {source_url: False}
    
    # fetch and search all the links that have not yet been scrapped 
    new_urls = []
    async with aiohttp.ClientSession() as client:
        tasks = []
        for url, visited in already_extracted_links.items():
            if not visited:
                already_extracted_links[url] = True
                tasks.append(fetch_and_parse_url(url, client, same_domain_only, **kwargs))
        print(f'About to asynchronously scrap {len(tasks)} links')
        new_links = await asyncio.gather(*tasks)
        # then add any newly found link to already__extracted_links and mark them as not visited
        for linkset in new_links:
            for link in linkset:
                if link not in already_extracted_links:
                    already_extracted_links[link] = False        
    # recuursive step
    return await deep_search_for_links(source_url = None, 
                            already_extracted_links = already_extracted_links, 
                            depth = depth - 1, 
                            **kwargs)

def get_domain(source_url: str) -> str:
    return re.split('(?<!/)/(?!/)', source_url)[0]

def is_same_domain(link:str, source_url:str) -> str:
    if link.startswith('http') and get_domain(link) == get_domain(source_url):
        return link
    if link.startswith('/'):
        return get_domain(source_url) + link
    return None

def profile(args):
    import cProfile, pstats
    with cProfile.Profile() as pr:
        asyncio.run(main(args))
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename='profile.prof')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog = 'Link Extractor',
                    description = 'Extracts links from news websites to find their articles')
    parser.add_argument('-nlf', '--newsLinkFile') 
    parser.add_argument('-af', '--articlesFile')
    parser.add_argument('-p', '--profile', action='store_true')
    args = parser.parse_args()
    if args.profile:
        profile(args)
    else:
        asyncio.run(main(args))
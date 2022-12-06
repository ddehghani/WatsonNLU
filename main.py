import argparse
from util import *
from scraper import *
from watson import WatsonNLU
from datapresentation import present_results

API_KEY = 'YlZZ1p6TYqzpemeX5-sdCjtTJJOwblN1VtueSqW8bEwg'
NLU_URL = 'https://api.us-south.natural-language-understanding.watson.cloud.ibm.com/instances/fa369057-a844-4eb1-a183-b9c1c88a1ca1'
NEWS_SOURCE_URL = 'https://blog.feedspot.com/usa_news_websites/' # a weblog containing the list of 100 most popular new aggencies in US

def main(args):
    news_links = read_as_json(args.newsLinkFile)
    articles = read_as_json(args.articlesFile)
    processed_articles = read_as_json(args.processedArticlesFile)
    
    if not articles and not processed_articles:
        if not news_links:
            print("No news links file provided or it couldn't be read. Extracting news links.")
            # scrap for external links from NEWS_SOURCE_URL
            news_links = {'links' : deep_search_for_links_sync(source_url = NEWS_SOURCE_URL, depth = 1, class_ = 'ext')}  
            print(f'Total news website links extracted from {get_domain(NEWS_SOURCE_URL)}: {len(news_links["links"])}')
            save_as_json('NewsAgencies.json', news_links) # save result as a json file
        
        # extract articles
        print("No article file provided or it couldn't be read. Extracting articles.")
        articles = {}
        for index, news_website in enumerate(news_links['links']):
            if news_website:
                print(f'{news_website = }')
                articles[news_website] = deep_search_for_links_sync(source_url = news_website, depth = 10, max_links = 500, same_domain_only = True)
                print(f'Progress: {(index + 1) * 100 / len(news_links["links"]):0.2f}%')
        save_as_json('articles.json', articles)
    
    # check articles for 
    if not processed_articles:
        processed_articles = process_articles(articles)
        save_as_json('processed_articles.json', processed_articles)
    
    present_results(processed_articles)

def profile(args):
    import cProfile, pstats
    with cProfile.Profile() as pr:
        main(args)
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename='profile.prof')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
                    prog = 'Link Extractor',
                    description = 'Extracts links from news websites to find their articles')
    parser.add_argument('-nlf', '--newsLinkFile') 
    parser.add_argument('-af', '--articlesFile')
    parser.add_argument('-paf', '--processedArticlesFile')
    parser.add_argument('-p', '--profile', action='store_true')
    args = parser.parse_args()
    if args.profile:
        profile(args)
    else:
        main(args)
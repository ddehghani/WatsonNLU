import json
import asyncio
from ibm_watson import NaturalLanguageUnderstandingV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, CategoriesOptions, EmotionOptions

class WatsonNLU:
    def __init__(self, *, apikey: str, url: str):
        self.counter = 0
        self.authenticator = IAMAuthenticator(apikey)
        self.nlu = NaturalLanguageUnderstandingV1(version='2022-04-07', authenticator = self.authenticator)
        self.nlu.set_service_url(url)

    def analyze(self, articles: dict) -> dict:
        return asyncio.run(self.analyze_async(articles))
    
    async def analyze_async(self, articles: dict) -> dict:
        new_articles = dict()
        for news_agency, articles in articles.items():
            tasks = [self.analyze_single_url(article) for article in articles]
            print(f'About to analyze {len(tasks)} links')
            results = await asyncio.gather(*tasks)
            average_emotion = {'sadness': 0, 'joy': 0, 'fear': 0, 'disgust': 0, 'anger': 0}
            total = 0
            for result in results:
                if result:
                    total += 1
                    for emotion in ['sadness', 'joy', 'fear', 'disgust', 'anger']:
                        average_emotion[emotion] += result[emotion] 
            for emotion in ['sadness', 'joy', 'fear', 'disgust', 'anger']:
                average_emotion[emotion] /= total
            new_articles[news_agency] = average_emotion
        return new_articles

    async def analyze_single_url(self, url: str):
        try:
            response = self.nlu.analyze( url=url,
            features=Features(emotion = EmotionOptions())).get_result()
            # print(json.dumps(response, indent=2))
            print(f'done{self.counter}')
            self.counter += 1
            return response.get('emotion').get('document').get('emotion')
        except ApiException as ex:
            return None
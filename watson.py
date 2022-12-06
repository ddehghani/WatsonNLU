import json
import asyncio
from ibm_watson import NaturalLanguageUnderstandingV1, ApiException
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, EmotionOptions, KeywordsOptions

class WatsonNLU:
    def __init__(self, *, apikey: str, url: str):
        self.counter = 0
        self.authenticator = IAMAuthenticator(apikey)
        self.nlu = NaturalLanguageUnderstandingV1(version='2022-04-07', authenticator = self.authenticator)
        self.nlu.set_service_url(url)
    
    async def analyze_text(self, text: str):
        try:
            response = self.nlu.analyze( text = text, features=Features(keywords=KeywordsOptions(emotion=True,limit=2))).get_result()
            self.counter += 1
            if self.counter % 100 == 0:
                print(f"{self.counter} html files were proccessed with watson NLU")
            return response.get('keywords')
        except ApiException as ex:
            return None

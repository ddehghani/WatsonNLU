from sklearn.metrics.pairwise import pairwise_distances, cosine_similarity
import pandas as pd
import numpy as np
from util import weighted_average_emotion
import matplotlib.pyplot as plt

def present_results(processed_articles: dict) -> None:
    # for keyword in findSimilarKeywords(processed_articles):
    keys = [" "]
    keywordSpecificData = {}
    for news_agency, keywords in processed_articles.items():
        newsagencyData = processed_articles[news_agency]
        emotion = {}
        count = 0
        #print(f"==============================================>{news_agency} with {len(keywords)} total keys" )
        for kw in keywords:
            if any(key.lower() in kw.lower() for key in keys) and "emotion" in newsagencyData[kw].keys():
                #print(kw)
                if count != 0 :
                    emotion = weighted_average_emotion(emotion, count, newsagencyData[kw]["emotion"], newsagencyData[kw]["count"])
                else:
                    emotion = newsagencyData[kw]["emotion"]
                count += newsagencyData[kw]["count"]

        keywordSpecificData[news_agency] = emotion
    
    df = pd.DataFrame.from_dict(data = keywordSpecificData, orient='index',columns=['sadness', 'joy', 'fear', 'disgust', 'anger'])
    normalized_df=(df-df.min())/(df.max()-df.min())
    print(df)
    print(normalized_df)
    # calculate similarities
    print(cosine_similarity(normalized_df))

    plt.rcParams['savefig.dpi'] = 600

    fig, axes = plt.subplots(3)
    fig.patch.set_visible(False)
    axes[0].axis('off')
    axes[0].axis('tight')
    axes[1].axis('off')
    axes[1].axis('tight')
    axes[2].axis('off')
    axes[2].axis('tight')


    axes[0].table(cellText=df.values, rowLabels= ['Reuters', 'ABCnews', 'Washington Post', 'Fox News', 'OAN news'], colLabels=df.columns, loc='center')
    axes[1].table(cellText=normalized_df.values, rowLabels= ['Reuters', 'ABCnews', 'Washington Post', 'Fox News', 'OAN news'], colLabels=df.columns, loc='center')
    axes[2].table(cellText=cosine_similarity(normalized_df), rowLabels= ['Reuters', 'ABCnews', 'Washington Post', 'Fox News', 'OAN news'], colLabels=['Reuters', 'ABCnews', 'Washington Post', 'Fox News', 'OAN news'], loc='center')
    fig.tight_layout()
    plt.show()

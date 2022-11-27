from sklearn.metrics.pairwise import pairwise_distances, cosine_similarity
import pandas as pd
import numpy as np

def present_results(processed_articles: dict) -> None:
    df = pd.DataFrame.from_dict(data = processed_articles, orient='index',columns=['sadness', 'joy', 'fear', 'disgust', 'anger'])
    normalized_df=(df-df.min())/(df.max()-df.min())
    print(df)
    print(normalized_df)
    # calculate similarities
    print(cosine_similarity(normalized_df))

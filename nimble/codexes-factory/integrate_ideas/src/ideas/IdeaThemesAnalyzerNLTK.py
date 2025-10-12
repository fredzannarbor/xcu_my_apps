#  Copyright (c) 2023. Fred Zimmerman.  Personal or educational use only.  All commercial and enterprise use must be licensed, contact wfz@nimblebooks.com

from collections import Counter

import matplotlib.pyplot as plt
import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from wordcloud import WordCloud


class IdeaAnalysisNLTK:
    def __init__(self, filepath):
        self.data = pd.read_csv(filepath)
        nltk.download('punkt')
        nltk.download('stopwords')
        self.stopwords = set(stopwords.words('english'))

    def get_top_items(self, n=10):
        return self.data.sort_values(by='OpenAI Sentiment', ascending=False).head(n)

    def analyze_ideas(self, ideas):
        all_ideas_tokens = [word_tokenize(idea.lower()) for idea in ideas]
        all_ideas_tokens_flat = [item for sublist in all_ideas_tokens for item in sublist]
        filtered_all_ideas_tokens = [word for word in all_ideas_tokens_flat if
                                     word not in self.stopwords and word.isalpha()]
        bi_grams = [(filtered_all_ideas_tokens[i], filtered_all_ideas_tokens[i + 1]) for i in
                    range(len(filtered_all_ideas_tokens) - 1)]
        common_elements = Counter(filtered_all_ideas_tokens).most_common(10)
        common_bi_grams = Counter(bi_grams).most_common(10)
        return common_elements, common_bi_grams

    def generate_wordcloud(self, data, title):
        wc = WordCloud(width=400, height=200, background_color='white', colormap='viridis',
                       contour_width=2, contour_color='blue').generate_from_frequencies(data)
        plt.figure(figsize=(6, 3))
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.title(title)
        plt.show()

    def display_analysis(self, n=10):
        top_items = self.get_top_items(n)
        common_elements, common_bi_grams = self.analyze_ideas(top_items['Idea'])

        common_elements_dict = dict(common_elements)
        common_bi_grams_dict = {" ".join(k): v for k, v in common_bi_grams}

        self.generate_wordcloud(common_elements_dict, "Top 10 Terms")
        self.generate_wordcloud(common_bi_grams_dict, "Top 10 Bi-grams")

# Displaying the analysis for demonstration purposes would be redundant since the results will be similar to before.
# However, the code is ready for you to use in your environment with NLTK!

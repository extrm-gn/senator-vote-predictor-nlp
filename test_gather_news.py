import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('API_KEY')
GNEWS_API_KEY = os.getenv('GNEWS_API_KEY')

"""
url = ('https://newsapi.org/v2/everything?'
       'q=Philippines Election&'
       'from=2025-01-10&'
       'sortBy=popularity&'
       f'apiKey={API_KEY}')

response = requests.get(url)

articles = response.json()['articles']

for key, value in enumerate(articles):
       print(value.keys())

"""

import json
# https://docs.python.org/3/library/urllib.request.html#module-urllib.request
# This library will be used to fetch the API.
import urllib.request

query = "Benhur Abalos".replace(" ", "%20")
url = f"https://gnews.io/api/v4/search?q={query}&lang=en&country=ph&max=3&apikey={GNEWS_API_KEY}"

with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode("utf-8"))
    articles = data["articles"]

    for i in range(len(articles)):
        # articles[i].title
        print(f"Title: {articles[i]['title']}")
        # articles[i].description
        print(f"Description: {articles[i]['description']}")
        print(f"Content: {articles[i]['content']}")
        # You can replace {property} below with any of the article properties returned by the API.
        # articles[i].{property}
        # print(f"{articles[i]['{property}']}")

        # Delete this line to display all the articles returned by the request. Currently only the first article is displayed.
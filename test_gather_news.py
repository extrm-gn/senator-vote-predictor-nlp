import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('API_KEY')

url = ('https://newsapi.org/v2/everything?'
       'q=Philippines Election&'
       'from=2025-01-10&'
       'sortBy=popularity&'
       f'apiKey={API_KEY}')

response = requests.get(url)

print(response.json())
import pandas as pd
import torch
from transformers import BertTokenizer, BertForSequenceClassification, pipeline
import spacy

# Load BERT for Sentiment Analysis (BERT base uncased)
sentiment_model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)
sentiment_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Sentiment analysis pipeline using Hugging Face
sentiment_classifier = pipeline('sentiment-analysis', model=sentiment_model, tokenizer=sentiment_tokenizer)

# Load SpaCy model for Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")

# df_new = pd.read_csv("/kaggle/input/trial-csv4/political_comments_sentiment.csv")
df_new = pd.read_csv("output.csv")

# Function to get sentiment analysis using BERT
def get_sentiment(text):
    sentiment = sentiment_classifier(text)
    return sentiment[0]['label'], sentiment[0]['score']

# Function to get Named Entity Recognition using SpaCy
def get_ner(text):
    doc = nlp(text)
    return [(entity.text, entity.label_) for entity in doc.ents]

# Apply sentiment analysis and NER to each comment_text
df_new['sentiment_label'], df_new['sentiment_score'] = zip(*df_new['concatenated_text'].apply(get_sentiment))
df_new['named_entities'] = df_new['concatenated_text'].apply(get_ner)

# Display the DataFrame with sentiment analysis and NER results
df_new.tail(20)
df_new.to_csv('labeled_data.csv')

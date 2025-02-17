# labeling.py

import pandas as pd
import numpy as np
import torch
from transformers import BertTokenizer, BertForSequenceClassification, pipeline
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import pickle

# Load BERT for Sentiment Analysis
sentiment_model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)
sentiment_tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
sentiment_classifier = pipeline('sentiment-analysis', model=sentiment_model, tokenizer=sentiment_tokenizer, truncation=True)

# Load SpaCy for Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")

# Load dataset
df = pd.read_csv("/kaggle/input/trial-csv14/output.csv")

# Function for sentiment analysis
def get_sentiment(text):
    sentiment = sentiment_classifier(text)
    return sentiment[0]['label'], sentiment[0]['score']

# Function for Named Entity Recognition
def get_ner(text):
    doc = nlp(text)
    return [(entity.text, entity.label_) for entity in doc.ents]

# Apply sentiment analysis and NER
df['sentiment_label'], df['sentiment_score'] = zip(*df['concatenated_text'].apply(get_sentiment))
df['named_entities'] = df['concatenated_text'].apply(get_ner)

# Handle missing values
df['translated_comment_text'] = df['translated_comment_text'].fillna('')
df['named_entities'] = df['named_entities'].apply(lambda x: x if isinstance(x, list) else [])

# Preprocess text data (TF-IDF)
vectorizer = TfidfVectorizer(stop_words='english', max_features=2200)
tfidf_matrix = vectorizer.fit_transform(df['translated_comment_text'])

# Extract features
df['num_named_entities'] = df['named_entities'].apply(lambda x: len(x) if isinstance(x, list) else 0)
sentiment_scores = df['sentiment_score'].values.reshape(-1, 1)
tfidf_dense = tfidf_matrix.toarray()

# One-hot encode the 'label' column
label_encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
label_features = label_encoder.fit_transform(df[['label']])

# Combine all features
combined_features = np.hstack((tfidf_dense, sentiment_scores, df[['num_named_entities']].values, label_features))

# Normalize features
scaler = StandardScaler()
combined_features_scaled = scaler.fit_transform(combined_features)

# Apply PCA
pca = PCA(n_components=50)
reduced_features = pca.fit_transform(combined_features_scaled)

# Perform clustering
n_clusters = 22
kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=100, max_iter=300)
df['cluster'] = kmeans.fit_predict(reduced_features)

# Evaluate clustering
silhouette_avg = silhouette_score(reduced_features, df['cluster'])
print(f"Silhouette Score: {silhouette_avg:.3f}")

# Save processed data and models
df.to_csv("processed_data.csv", index=False)
with open("models.pkl", "wb") as f:
    pickle.dump({"vectorizer": vectorizer, "scaler": scaler, "pca": pca, "kmeans": kmeans, "label_encoder": label_encoder}, f)

print("✅ Data processing complete. Saved processed data and models.")

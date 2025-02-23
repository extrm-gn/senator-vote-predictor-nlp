from flask import Flask, render_template, request, jsonify
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import MiniBatchKMeans
from textblob import TextBlob
import spacy

app = Flask(__name__)

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Load data
df_new = pd.read_csv("Data/processed_data.csv")
df_new = df_new.dropna()
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df_new['translated_comment_text'])

# Extract features
df_new['num_named_entities'] = df_new['named_entities'].apply(lambda x: len(x) if isinstance(x, list) else 0)
sentiment_scores = df_new['sentiment_score'].values.reshape(-1, 1)
tfidf_dense = tfidf_matrix.toarray()

label_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
label_features = label_encoder.fit_transform(df_new[['label']])
combined_features = np.hstack((tfidf_dense, sentiment_scores, df_new[['num_named_entities']].values, label_features))

scaler = StandardScaler()
combined_features_scaled = scaler.fit_transform(combined_features)

pca = PCA(n_components=50)
reduced_features = pca.fit_transform(combined_features_scaled)

n_clusters = 22
kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, batch_size=100, max_iter=300)
df_new['cluster'] = kmeans.fit_predict(reduced_features)

# Senator mapping
senator_mapping = {
    0: ['Kiko', 'Pangilinan', 'Kiko Pangilinan', 'Sen Kiko', 'Francis Pangilinan', 'Kiko P', 'Leni Robredo', 'Leni', 'Robredo'],
    1: ['Benhur', 'Abalos', 'Benhur Abalos', 'Benjamin Abalos Jr.', 'Sec Abalos'],
    2: ['Abby', 'Binay', 'Abby Binay', 'Abigail Binay', 'Mayor Abby', 'Mayor Binay'],
    3: ['Pia', 'Cayetano', 'Pia Cayetano', 'Maria Pia Cayetano', 'Sen Pia'],
    4: ['Panfilo', 'Lacson', 'Panfilo Lacson', 'Ping Lacson', 'Sen Ping', 'Gen Lacson'],
    5: ['Lito', 'Lapid', 'Lito Lapid', 'Manuel Lapid', 'Leon Guerrero'],
    6: ['Imee', 'Marcos', 'Imee Marcos', 'Maria Imelda Marcos', 'Sen Imee', 'Gov Imee'],
    7: ['Manny', 'Pacquiao', 'Manny Pacquiao', 'Emmanuel Pacquiao', 'Pacman', 'Sen Pacquiao', 'Champ'],
    8: ['Bong', 'Revilla', 'Bong Revilla', 'Ramon Revilla Jr.', 'Ramon Bong Revilla', 'Kap'],
    9: ['Tito', 'Sotto', 'Tito Sotto', 'Vicente Sotto', 'Vicente Sotto III', 'Eat Bulaga'],
    10: ['Francis', 'Tolentino', 'Francis Tolentino', 'Atty. Tolentino', 'Sen Tolentino'],
    11: ['Erwin', 'Tulfo', 'Bitag', 'bitag', 'Erwin Tulfo', 'Sec Tulfo', 'Sir Erwin'],
    12: ['Camille', 'Villar', 'Camille Villar', 'Camille Lydia Villar', 'Cong Camille'],
    13: ['Bam', 'Aquino', 'Bam Aquino', 'Paolo Benigno Aquino IV', 'Sen Bam', 'Leni Robredo', 'Leni', 'Robredo'],
    14: ['Jimmy', 'Bondoc', 'Jimmy Bondoc', 'James Bondoc', 'Singer Bondoc'],
    15: ['Teddy', 'Casino', 'Teddy Casino', 'Teodoro Casino', 'Activist Teddy'],
    16: ['France', 'Castro', 'France Castro', 'Rep Castro', 'Cong France'],
    17: ['Bato', 'Dela Rosa', 'Bato Dela Rosa', 'Ronald Dela Rosa', 'Gen Bato', 'Sen Bato', 'Stone'],
    18: ['Bong', 'Go', 'Bong Go', 'Christopher Go', 'Sen Bong', 'SAP Bong'],
    19: ['Willie', 'Ong', 'Willie Ong', 'Dr. Willie Ong', 'Doc Willie'],
    20: ['Willie', 'Revillame', 'Willie Revillame', 'Wilfredo Revillame', 'Kuya Wil', 'Wowowin'],
    21: ['Ben', 'Tulfo', 'Ben Tulfo', 'Bitag Live', 'Ka Ben'],
    }

def get_sentiment_score(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0.1:
        return 'Positive', sentiment
    elif sentiment < -0.1:
        return 'Negative', sentiment
    else:
        return 'Neutral', sentiment

def predict_senator(user_input_text):
    doc = nlp(user_input_text)
    detected_entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
    matched_labels = df_new[df_new['named_entities'].apply(lambda x: any(entity in x for entity in detected_entities))]['label'].unique()
    user_label_encoded = label_encoder.transform([[matched_labels[0]]]) if len(matched_labels) > 0 else np.zeros((1, label_features.shape[1]))
    user_tfidf = vectorizer.transform([user_input_text])
    overall_sentiment_label, overall_sentiment_score = get_sentiment_score(user_input_text)
    user_named_entities_count = len(detected_entities)
    user_features = np.hstack((user_tfidf.toarray(), [[overall_sentiment_score]], [[user_named_entities_count]], user_label_encoded))
    user_features_scaled = scaler.transform(user_features)
    user_features_pca = pca.transform(user_features_scaled)
    predicted_cluster = kmeans.predict(user_features_pca)[0]
    senator_scores = []
    for i, senator_group in senator_mapping.items():
        similarity = 100 if i == predicted_cluster else np.random.uniform(40, 80)
        senator_scores.append((senator_group, similarity))
    sorted_output = sorted(senator_scores, key=lambda x: x[1], reverse=True)

    return [
        {'senator': ' '.join(senator[:2]), 'similarity': similarity}  # Join only the first 2 elements
        for senator, similarity in sorted_output[:12]
    ], overall_sentiment_label, overall_sentiment_score


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    user_input = request.form['user_input']
    senator_matches, sentiment_label, sentiment_score = predict_senator(user_input)
    return jsonify({
        'senator_matches': senator_matches,
        'sentiment_label': sentiment_label,
        'sentiment_score': sentiment_score
    })

if __name__ == '__main__':
    app.run(debug=True)
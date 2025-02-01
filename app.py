import pandas as pd
import numpy as np
import spacy
import pickle
from textblob import TextBlob
from flask import Flask, render_template, request, jsonify

# Load preprocessed dataset and models
df = pd.read_csv(
    "C:/Users/J-CHENNY/PycharmProjects/senator-vote-predictor-nlp/dagster_pipeline/Data/processed_data.csv")
with open("C:/Users/J-CHENNY/PycharmProjects/senator-vote-predictor-nlp/dagster_pipeline/Data/models.pkl", "rb") as f:
    models = pickle.load(f)

vectorizer = models["vectorizer"]
scaler = models["scaler"]
pca = models["pca"]
kmeans = models["kmeans"]
label_encoder = models["label_encoder"]

# Load SpaCy for NER
nlp = spacy.load("en_core_web_sm")

# Senator mapping
senator_mapping = {
    0: ['Kiko Pangilinan', 'Bam Aquino'],
    1: ['Benhur Abalos'],
    2: ['Abby Binay'],
    3: ['Pia Cayetano'],
    4: ['Panfilo Lacson', 'Manny Pacquiao'],
    5: ['Lito Lapid'],
    6: ['Imee Marcos'],
    7: ['Manny Pacquiao'],
    8: ['Bong Revilla'],
    9: ['Tito Sotto'],
    10: ['Francis Tolentino'],
    11: ['Erwin Tulfo'],
    12: ['Camille Villar'],
    13: ['Bam Aquino'],
    14: ['Jimmy Bondoc'],
    15: ['Teddy Casino'],
    16: ['France Castro'],
    17: ['Bato Dela Rosa'],
    18: ['Bong Go'],
    19: ['Willie Ong'],
    20: ['Willie Revillame'],
    21: ['Ben Tulfo'],
}


# Function to get sentiment score
def get_sentiment_score(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0.1:
        return 'Positive', sentiment
    elif sentiment < -0.1:
        return 'Negative', sentiment
    else:
        return 'Neutral', sentiment


# Function to predict senator
def predict_senator(user_input_text):
    # NER on user input
    doc = nlp(user_input_text)
    detected_entities = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]

    # Preprocess user input
    user_tfidf = vectorizer.transform([user_input_text])

    # Get expected feature size
    expected_tfidf_size = vectorizer.get_feature_names_out().shape[0]
    actual_tfidf_size = user_tfidf.shape[1]

    # Fix dimension mismatch by padding zeros if needed
    if actual_tfidf_size < expected_tfidf_size:
        padding = np.zeros((1, expected_tfidf_size - actual_tfidf_size))
        user_tfidf = np.hstack((user_tfidf.toarray(), padding))
    else:
        user_tfidf = user_tfidf.toarray()

    # Set mock values for missing columns
    user_sentiment_score = 0.7
    user_named_entities_count = len(detected_entities)

    # Ensure OneHotEncoder handles unknown labels
    if len(detected_entities) > 0:
        user_label_encoded = label_encoder.transform([[detected_entities[0]]])
    else:
        user_label_encoded = np.zeros((1, label_encoder.categories_[0].shape[0]))  # Zero vector for unknown labels

    # Combine user input features
    user_features = np.hstack((
        user_tfidf,
        np.array([[user_sentiment_score]]),
        np.array([[user_named_entities_count]]),
        user_label_encoded
    ))

    # Fix feature mismatch before scaling
    expected_feature_count = scaler.n_features_in_
    actual_feature_count = user_features.shape[1]

    if actual_feature_count < expected_feature_count:
        padding = np.zeros((1, expected_feature_count - actual_feature_count))
        user_features = np.hstack((user_features, padding))

    # Normalize and apply PCA
    user_features_scaled = scaler.transform(user_features)
    user_features_pca = pca.transform(user_features_scaled)

    # Predict cluster
    predicted_cluster = kmeans.predict(user_features_pca)[0]

    # Calculate distances and similarities
    distances = kmeans.transform(user_features_pca)[0]
    max_distance, min_distance = np.max(distances), np.min(distances)
    similarity_percentages = 100 * (1 - (distances - min_distance) / (max_distance - min_distance))

    # Get senator similarity scores
    sorted_output = sorted([(senator_mapping[i], similarity_percentages[i]) for i in range(len(senator_mapping))],
                           key=lambda x: x[1], reverse=True)

    # Get overall sentiment
    overall_sentiment_label, overall_sentiment_score = get_sentiment_score(user_input_text)

    return overall_sentiment_label, overall_sentiment_score, sorted_output


# Flask routes
app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    user_input_text = request.form['user_input']
    sentiment_label, sentiment_score, prediction = predict_senator(user_input_text)

    # Prepare response data
    response = {
        'sentiment_label': sentiment_label,
        'sentiment_score': sentiment_score,
        'senator_matches': []
    }

    for senator_group, similarity in prediction[:12]:  # Top 12 senators
        for senator in senator_group:
            response['senator_matches'].append({'senator': senator, 'similarity': similarity})

    # Return predictions as a JSON response
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)

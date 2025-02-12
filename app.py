from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import spacy
import pickle
from textblob import TextBlob

app = Flask(__name__)

# Load preprocessed dataset and models
df = pd.read_csv("C:/Users/J-CHENNY/PycharmProjects/senator-vote-predictor-nlp/dagster_pipeline/Data/processed_data.csv")
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
    14: ['Jimmy', 'Bondoc', 'Jimmy Bondoc', 'James Bondoc', 'Singer Bondoc','Sara', 'Duterte', 'Sarah', 'Sara Duterte'],
    15: ['Teddy', 'Casino', 'Teddy Casino', 'Teodoro Casino', 'Activist Teddy'],
    16: ['France', 'Castro', 'France Castro', 'Rep Castro', 'Cong France'],
    17: ['Bato', 'Dela Rosa', 'Bato Dela Rosa', 'Ronald Dela Rosa', 'Gen Bato', 'Sen Bato', 'Stone', 'Sara', 'Duterte', 'Sarah', 'Sara Duterte'],
    18: ['Bong', 'Go', 'Bong Go', 'Christopher Go', 'Sen Bong', 'SAP Bong','Sara', 'Duterte', 'Sarah', 'Sara Duterte'],
    19: ['Willie', 'Ong', 'Willie Ong', 'Dr. Willie Ong', 'Doc Willie'],
    20: ['Willie', 'Revillame', 'Willie Revillame', 'Wilfredo Revillame', 'Kuya Wil', 'Wowowin'],
    21: ['Ben', 'Tulfo', 'Ben Tulfo', 'Bitag Live', 'Ka Ben'],
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
    sorted_output = sorted([(senator_mapping[i], similarity_percentages[i]) for i in range(len(senator_mapping))], key=lambda x: x[1], reverse=True)

    # Get overall sentiment
    overall_sentiment_label, overall_sentiment_score = get_sentiment_score(user_input_text)

    # Prepare results
    results = {
        "senator_matches": [{"senator": " ".join(senator), "similarity": similarity} for senator, similarity in sorted_output[:21]],
        "sentiment_label": overall_sentiment_label,
        "sentiment_score": overall_sentiment_score
    }

    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    user_input = request.form['user_input']
    result = predict_senator(user_input)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)

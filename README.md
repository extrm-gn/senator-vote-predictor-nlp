# 🏛️ Senator Election Prediction Using YouTube Comments

## 📌 Overview
🔗 **Live Demo:** [Senator Vote Predictor](https://senator-vote-predictor.onrender.com)
This project leverages YouTube comments to predict likely elected senators using Natural Language Processing (NLP) and machine learning techniques. The system extracts, processes, and analyzes user opinions to gauge political trends and forecast election outcomes.

## 🚀 Technologies Used
- 🐍 **Python**: Core programming language for data processing and modeling.
- 📺 **YouTube API**: Fetching comments from YouTube videos.
- 🗄️ **PostgreSQL**: Storing structured data following Kimball’s Data Warehousing principles.
- 🧠 **BERT**: Sentiment analysis and Named Entity Recognition (NER).
- 📉 **PCA (Principal Component Analysis)**: Dimensionality reduction.
- 🎯 **K-Means Clustering**: Grouping sentiment patterns.

## 🎯 Features
- ✅ **Automated Data Pipeline**: Extracts, cleans, and stores YouTube comments in a structured format.
- 📊 **Sentiment Analysis & NER**: Uses BERT-based NLP to analyze voter sentiments and extract named entities.
- 🔍 **Election Prediction**: PCA and K-Means clustering help identify patterns and predict 12 likely senators.
- ⚡ **Scalable Architecture**: Optimized for real-time trend analysis and efficient data processing.

## 🛠️ Installation
```bash
# Clone this repository
git clone https://github.com/your-username/senator-election-prediction.git

# Navigate to the project directory
cd senator-election-prediction

# Install dependencies
pip install -r requirements.txt
```

1. Set up **PostgreSQL** and configure connection settings.
2. Obtain **YouTube API** credentials and update the configuration.

## 📌 Usage
```bash
# Run the data extraction script
python fetch_comments.py

# Perform sentiment analysis and clustering
python analyze_sentiments.py

# Generate election predictions
python predict_senators.py
```

## 🔮 Future Enhancements
- 🤖 Implement deep learning-based sentiment analysis for higher accuracy.
- 🌍 Expand data sources beyond YouTube (e.g., Twitter, news articles).
- 📈 Integrate a real-time dashboard for visualizing trends.

## 🤝 Contributing
Contributions are welcome! Feel free to **open an issue** or **submit a pull request**.

## 📜 License
This project is licensed under the **MIT License**.

---

👤 **Author:** Marc Linus D. Rosales 
🔗 **GitHub:** [extrm-gn](https://github.com/extrm-gn)

